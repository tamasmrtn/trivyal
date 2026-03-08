"""
Integration tests for the concurrent reconnect path.

These tests stress the three races fixed in hub/ws/manager.py:

1. disconnect() identity guard
   ws1's finally block calls disconnect(agent_id, ws1).  Without the identity
   check, it would evict ws2 if ws2 had already registered — leaving no active
   WebSocket.  Observable symptom: agent becomes offline immediately after
   reconnect even though ws2 is still open.

2. connect() store-before-close invariant
   ws2 is stored in active *before* old.close() is called.  If the order were
   reversed and old.close() raised, ws2 might never be stored.  Hub must
   survive even if old.close() fails.

3. RuntimeError handling on ws1's receive_json()
   Starlette sets ws1.application_state = DISCONNECTED *synchronously* inside
   close(), before the actual network frame is sent.  If ws1 resumes from a DB
   await (e.g. session.commit) and then calls receive_json(), it gets
   RuntimeError instead of WebSocketDisconnect.  handle_connection must catch
   it and still run the finally block.
"""

import asyncio

import pytest
import websockets.exceptions

from helpers.agent_sim import SimulatedAgent
from helpers.trivy_fixtures import SCAN_V1


def _make_agent(hub_base_url: str, registered_agent: dict) -> SimulatedAgent:
    ws_url = hub_base_url.replace("http://", "ws://") + "/ws/agent"
    return SimulatedAgent(
        hub_ws_url=ws_url,
        token=registered_agent["token"],
        hub_public_key=registered_agent["hub_public_key"],
    )


class TestSupersededConnection:
    """ws1 is replaced by ws2 — verify ws1 is cleanly evicted."""

    async def test_superseded_ws_receives_close_4000(
        self, hub_base_url, registered_agent
    ):
        """Hub closes ws1 with code 4000 when ws2 connects for the same agent."""
        ws1 = _make_agent(hub_base_url, registered_agent)
        ws2 = _make_agent(hub_base_url, registered_agent)

        await ws1.connect_and_handshake()
        await ws2.connect_and_handshake()

        # ws1 should receive a close frame from the hub
        with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
            await asyncio.wait_for(ws1._ws.recv(), timeout=5.0)

        assert exc_info.value.rcvd is not None
        assert exc_info.value.rcvd.code == 4000, (
            f"Expected close code 4000 (Superseded), got {exc_info.value.rcvd.code}"
        )

        await ws2.close()

    async def test_agent_remains_online_after_reconnect(
        self, hub, hub_base_url, registered_agent
    ):
        """ws1's finally block must not evict ws2 from active (identity guard).

        Without the identity check in disconnect(), ws1's finally block would
        call disconnect(agent_id) and pop ws2 — the agent would then appear
        offline even though ws2 is still open.
        """
        ws1 = _make_agent(hub_base_url, registered_agent)
        ws2 = _make_agent(hub_base_url, registered_agent)

        await ws1.connect_and_handshake()
        await ws2.connect_and_handshake()

        # Wait for ws1's handle_connection to finish (finally block runs,
        # agent.status = OFFLINE written — which must then be overridden by ws2
        # being in active, or the finally block must not run at all because ws2
        # marked the agent ONLINE after ws1's OFFLINE).
        #
        # The correct behaviour: ws1 finally writes OFFLINE, but ws2 is already
        # ONLINE (written after connect()) — so the net result is ONLINE.
        await asyncio.sleep(0.8)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "online", (
            "Agent must be online (ws2 active). "
            "If offline, ws1's finally block incorrectly evicted ws2."
        )

        await ws2.close()

    async def test_ws2_is_functional_after_reconnect(
        self, hub_base_url, registered_agent
    ):
        """ws2 can exchange heartbeats with the hub after ws1 is superseded.

        Proves that ws2 is correctly registered in ConnectionManager.active
        and can receive hub-originated messages.
        """
        ws1 = _make_agent(hub_base_url, registered_agent)
        ws2 = _make_agent(hub_base_url, registered_agent)

        await ws1.connect_and_handshake()
        await ws2.connect_and_handshake()

        # Let ws1's finally block complete
        await asyncio.sleep(0.5)

        # ws2 must still have a live, functional connection
        await ws2.recv_heartbeat_ack()

        await ws2.close()


class TestRapidReconnectStorm:
    """Multiple reconnects in quick succession — only the last ws survives."""

    async def test_last_agent_is_online_after_storm(
        self, hub, hub_base_url, registered_agent
    ):
        """N rapid reconnects: only the last ws stays active; agent is online."""
        agents = [_make_agent(hub_base_url, registered_agent) for _ in range(5)]

        for agent in agents:
            await agent.connect_and_handshake()

        # Let all displaced handle_connection finally blocks settle
        await asyncio.sleep(1.2)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "online", (
            "Agent must be online after rapid reconnect storm. "
            "If offline, a stale disconnect() call evicted the last ws."
        )

        await agents[-1].close()

    async def test_last_agent_can_heartbeat_after_storm(
        self, hub_base_url, registered_agent
    ):
        """The last ws is fully functional (not just 'online' in the DB)."""
        agents = [_make_agent(hub_base_url, registered_agent) for _ in range(5)]

        for agent in agents:
            await agent.connect_and_handshake()

        await asyncio.sleep(1.0)

        # Last ws must be live in ConnectionManager.active
        await agents[-1].recv_heartbeat_ack()

        await agents[-1].close()

    async def test_hub_does_not_crash_during_storm(
        self, hub, hub_base_url, registered_agent
    ):
        """Hub remains healthy and returns 200 on /api/health during rapid reconnects."""
        agents = [_make_agent(hub_base_url, registered_agent) for _ in range(8)]

        async def _connect_all():
            for agent in agents:
                await agent.connect_and_handshake()

        # Run reconnects concurrently with health polling
        async def _poll_health():
            for _ in range(10):
                r = await hub.get("/api/health")
                assert r.status_code == 200
                await asyncio.sleep(0.05)

        await asyncio.gather(_connect_all(), _poll_health())

        await asyncio.sleep(0.5)
        await agents[-1].close()


class TestRuntimeErrorRace:
    """Reconnect while ws1 is mid-processing — the application_state race."""

    async def test_reconnect_during_scan_result_processing(
        self, hub, hub_base_url, registered_agent
    ):
        """Hub survives RuntimeError on ws1's receive_json() after ws2 connects.

        ws1 sends a scan_result (which triggers await session.commit() inside
        handle_connection).  ws2 connects concurrently: the hub calls ws1.close(),
        which sets ws1.application_state=DISCONNECTED synchronously.  When ws1
        resumes from the DB await and calls receive_json(), it gets RuntimeError.
        handle_connection must catch it and run the finally block.

        Verified by: agent is online (ws2 is in active) and ws2 can heartbeat.
        """
        ws1 = _make_agent(hub_base_url, registered_agent)
        ws2 = _make_agent(hub_base_url, registered_agent)

        await ws1.connect_and_handshake()

        # Send a scan_result — this triggers DB writes in the hub (yield points).
        # We do NOT await for the hub to finish processing it; instead we race
        # ws2's connect() against ws1's session.commit().
        await ws1.send_scan_result(SCAN_V1)

        # Connect ws2 immediately — aims to hit ws1 mid-commit
        await ws2.connect_and_handshake()

        # Allow both handle_connections to settle (ws1 → RuntimeError or
        # WebSocketDisconnect, ws2 → normal receive loop)
        await asyncio.sleep(0.8)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "online", (
            "Hub must survive RuntimeError from ws1 and keep ws2 active. "
            "If offline, handle_connection did not catch RuntimeError correctly."
        )

        # Confirm ws2 has a working connection (not just a stale DB row)
        await ws2.recv_heartbeat_ack()

        await ws2.close()

    async def test_agent_goes_offline_after_all_connections_close(
        self, hub, hub_base_url, registered_agent
    ):
        """After the last ws closes, the agent is offline — finally block ran.

        Sanity check: the RuntimeError path must still reach the finally block
        and mark the agent OFFLINE when there is no surviving ws.
        """
        ws1 = _make_agent(hub_base_url, registered_agent)
        ws2 = _make_agent(hub_base_url, registered_agent)

        await ws1.connect_and_handshake()
        await ws2.connect_and_handshake()

        # Let ws1's finally block complete
        await asyncio.sleep(0.5)

        # Now close the last surviving connection
        await ws2.close()
        await asyncio.sleep(0.5)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "offline", (
            "Agent must be offline after all connections close. "
            "If online, ws2's finally block did not run."
        )
