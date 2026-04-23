"""Tests for the WebSocket ConnectionManager.

Covers the three bug-prone paths discovered in the fix:

1. disconnect() identity guard — ws1's finally block must not evict ws2.
2. connect() store-before-close — new ws is registered even if old.close() raises.
3. send_scan_trigger() failure cleanup — broken ws removed from active so the next
   receive_json() in handle_connection doesn't see application_state=DISCONNECTED.
4. handle_connection RuntimeError handling — Starlette sets application_state=
   DISCONNECTED synchronously inside close(), so receive_json() raises RuntimeError
   instead of WebSocketDisconnect when the race fires; handle_connection must survive.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import WebSocketDisconnect
from sqlmodel import select
from trivyal_hub.core.auth import generate_token, hash_token
from trivyal_hub.db.models import Agent, AgentStatus, Finding, FindingStatus
from trivyal_hub.ws.manager import ConnectionManager


class TestDisconnect:
    def test_removes_matching_ws(self):
        manager = ConnectionManager()
        ws = MagicMock()
        manager.active["agent-1"] = ws

        manager.disconnect("agent-1", ws)

        assert "agent-1" not in manager.active

    def test_does_not_evict_replacement_ws(self):
        """ws1's finally-block disconnect(agent_id, ws1) must not remove ws2.

        Race: ws2 arrives and calls connect(), which stores ws2 in active.
        ws1's handle_connection is still running (awaiting a DB operation) and
        eventually reaches its finally block.  Without the identity check,
        disconnect() would pop ws2 — leaving the agent with no active WebSocket.
        """
        manager = ConnectionManager()
        ws1, ws2 = MagicMock(), MagicMock()
        manager.active["agent-1"] = ws2  # ws2 is already registered

        manager.disconnect("agent-1", ws1)  # stale cleanup from ws1's finally

        assert manager.active.get("agent-1") is ws2

    def test_noop_when_agent_absent(self):
        manager = ConnectionManager()
        manager.disconnect("nonexistent", MagicMock())  # must not raise


class TestConnect:
    async def test_stores_new_ws_in_active(self):
        manager = ConnectionManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        manager.active["agent-1"] = ws1

        await manager.connect("agent-1", ws2)

        assert manager.active["agent-1"] is ws2

    async def test_closes_old_ws_on_reconnect(self):
        manager = ConnectionManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        manager.active["agent-1"] = ws1

        await manager.connect("agent-1", ws2)

        ws1.close.assert_called_once_with(code=4000, reason="Superseded by new connection")

    async def test_new_ws_registered_even_if_old_close_raises(self):
        """Network may already be gone when we close the superseded connection.
        The new ws must be in active regardless.
        """
        manager = ConnectionManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        ws1.close = AsyncMock(side_effect=Exception("network gone"))
        manager.active["agent-1"] = ws1

        await manager.connect("agent-1", ws2)

        assert manager.active["agent-1"] is ws2


class TestSendScanTrigger:
    async def test_returns_true_and_sends_message(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.active["agent-1"] = ws

        result = await manager.send_scan_trigger("agent-1")

        assert result is True
        ws.send_json.assert_called_once_with({"type": "scan_trigger"})

    async def test_returns_false_when_agent_not_connected(self):
        manager = ConnectionManager()

        assert await manager.send_scan_trigger("nonexistent") is False

    async def test_removes_ws_from_active_on_send_failure(self):
        """Starlette's send() sets application_state=DISCONNECTED synchronously
        before raising.  If we leave the broken ws in active, the concurrent
        receive_json() in handle_connection will see DISCONNECTED and raise
        RuntimeError instead of WebSocketDisconnect.  Removing the ws here
        prevents that silent state corruption.
        """
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.send_json = AsyncMock(side_effect=Exception("connection lost"))
        manager.active["agent-1"] = ws

        result = await manager.send_scan_trigger("agent-1")

        assert result is False
        assert "agent-1" not in manager.active


class TestHandleConnection:
    """Integration-style tests for the full handle_connection lifecycle."""

    def _mock_agent(self, agent_id="agent-1", name="test-agent"):
        agent = MagicMock()
        agent.id = agent_id
        agent.name = name
        agent.fingerprint = None
        agent.status = None
        agent.last_seen = None
        return agent

    def _mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()  # synchronous
        return session

    async def test_runtimeerror_exits_cleanly_and_marks_agent_offline(self):
        """Regression test for the application_state race.

        Starlette sets ws.application_state=DISCONNECTED *synchronously* inside
        close(), before the actual network send.  If connect() closes ws1 while
        ws1 is awaiting a DB operation, ws1 resumes and calls receive_json() on
        an already-DISCONNECTED socket → RuntimeError.  handle_connection must
        catch it and still run the finally block so the agent is marked OFFLINE.
        """
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.receive_json = AsyncMock(
            side_effect=RuntimeError("WebSocket is not connected. Need to call 'accept' first.")
        )
        session = self._mock_session()
        agent = self._mock_agent()

        with patch.object(manager, "authenticate", new=AsyncMock(return_value=agent)):
            await manager.handle_connection(ws, session)

        # finally block committed at least once (agent marked OFFLINE)
        session.commit.assert_called()
        assert agent.status == AgentStatus.OFFLINE

    async def test_websocket_disconnect_exits_cleanly_and_marks_agent_offline(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.receive_json = AsyncMock(side_effect=WebSocketDisconnect(code=1001))
        session = self._mock_session()
        agent = self._mock_agent()

        with patch.object(manager, "authenticate", new=AsyncMock(return_value=agent)):
            await manager.handle_connection(ws, session)

        session.commit.assert_called()
        assert agent.status == AgentStatus.OFFLINE

    async def test_failed_auth_closes_connection_and_does_not_enter_loop(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        session = self._mock_session()

        with patch.object(manager, "authenticate", new=AsyncMock(return_value=None)):
            await manager.handle_connection(ws, session)

        ws.close.assert_called_once_with(code=4001, reason="Authentication failed")
        ws.receive_json.assert_not_called()

    async def test_stale_ws_finally_does_not_evict_current_ws(self):
        """Full-path regression for the disconnect() identity guard.

        ws2 arrives while ws1's handle_connection is still running (simulated by
        overwriting active[agent_id]=ws2 inside the patched connect).  When ws1
        finishes and its finally block calls disconnect(agent_id, ws1), ws2 must
        remain untouched in active.
        """
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.receive_json = AsyncMock(side_effect=RuntimeError("WebSocket is not connected"))
        session = self._mock_session()
        agent = self._mock_agent()

        original_connect = manager.connect

        async def _connect_then_supersede(agent_id, ws):
            await original_connect(agent_id, ws)
            # Simulate ws2 arriving and registering while ws1 is mid-processing.
            manager.active[agent_id] = ws2

        with (
            patch.object(manager, "authenticate", new=AsyncMock(return_value=agent)),
            patch.object(manager, "connect", side_effect=_connect_then_supersede),
        ):
            await manager.handle_connection(ws1, session)

        # ws1's finally must NOT have evicted ws2
        assert manager.active.get("agent-1") is ws2
        # ws1's finally must NOT have written OFFLINE — ws2 owns the agent now
        assert agent.status != AgentStatus.OFFLINE


class TestRateLimit:
    def test_allows_under_threshold(self):
        manager = ConnectionManager()
        for _ in range(4):
            manager.record_auth_failure("10.0.0.1")
        assert manager.is_rate_limited("10.0.0.1") is False

    def test_blocks_after_threshold(self):
        manager = ConnectionManager()
        for _ in range(5):
            manager.record_auth_failure("10.0.0.1")
        assert manager.is_rate_limited("10.0.0.1") is True

    def test_resets_after_window_expires(self):
        manager = ConnectionManager()
        # Record failures "in the past" by inserting old timestamps
        old_time = time.monotonic() - 120  # 2 minutes ago
        manager._auth_failures["10.0.0.1"] = [old_time] * 10

        assert manager.is_rate_limited("10.0.0.1") is False

    def test_different_ips_tracked_independently(self):
        manager = ConnectionManager()
        for _ in range(5):
            manager.record_auth_failure("10.0.0.1")
        assert manager.is_rate_limited("10.0.0.1") is True
        assert manager.is_rate_limited("10.0.0.2") is False

    async def test_rate_limited_connection_closed_immediately(self):
        manager = ConnectionManager()
        for _ in range(5):
            manager.record_auth_failure("10.0.0.1")

        ws = AsyncMock()
        ws.client = MagicMock()
        ws.client.host = "10.0.0.1"
        session = AsyncMock()
        session.add = MagicMock()

        await manager.handle_connection(ws, session)

        ws.close.assert_called_once_with(code=4004, reason="Rate limited")


class TestMonitorAgents:
    """Heartbeat timeout monitor — closes stale agent connections."""

    async def test_closes_stale_connection(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.active["agent-1"] = ws
        manager.last_seen["agent-1"] = time.monotonic() - 100  # 100s ago

        # Run one iteration of the monitor logic directly
        await manager._monitor_agents_once()

        ws.close.assert_called_once_with(code=4002, reason="Heartbeat timeout")

    async def test_leaves_fresh_connection_alone(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.active["agent-1"] = ws
        manager.last_seen["agent-1"] = time.monotonic()  # just now

        await manager._monitor_agents_once()

        ws.close.assert_not_called()

    async def test_survives_close_error(self):
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws1.close = AsyncMock(side_effect=Exception("already closed"))
        ws2 = AsyncMock()
        manager.active["agent-1"] = ws1
        manager.active["agent-2"] = ws2
        manager.last_seen["agent-1"] = time.monotonic() - 100
        manager.last_seen["agent-2"] = time.monotonic() - 100

        # Should not raise, and ws2 should still be closed
        await manager._monitor_agents_once()

        ws1.close.assert_called_once()
        ws2.close.assert_called_once()

    async def test_connect_updates_last_seen(self):
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect("agent-1", ws)

        assert "agent-1" in manager.last_seen

    async def test_disconnect_removes_last_seen(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.active["agent-1"] = ws
        manager.last_seen["agent-1"] = time.monotonic()

        manager.disconnect("agent-1", ws)

        assert "agent-1" not in manager.last_seen


class TestReadTimeout:
    """WebSocket read timeout — silent agent detected and marked OFFLINE."""

    def _mock_agent(self, agent_id="agent-1", name="test-agent"):
        agent = MagicMock()
        agent.id = agent_id
        agent.name = name
        agent.fingerprint = None
        agent.status = None
        agent.last_seen = None
        return agent

    def _mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        return session

    async def test_timeout_marks_agent_offline(self):
        """If receive_json blocks beyond heartbeat_timeout the agent is marked OFFLINE."""
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.receive_json = AsyncMock(side_effect=TimeoutError)
        session = self._mock_session()
        agent = self._mock_agent()

        with patch.object(manager, "authenticate", new=AsyncMock(return_value=agent)):
            await manager.handle_connection(ws, session)

        session.commit.assert_called()
        assert agent.status == AgentStatus.OFFLINE


_SCAN_RESULT_1 = {
    "ArtifactName": "nginx:latest",
    "Results": [
        {
            "Target": "nginx:latest",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-1000",
                    "PkgName": "libssl",
                    "InstalledVersion": "1.1.1",
                    "Severity": "CRITICAL",
                },
                {
                    "VulnerabilityID": "CVE-2024-2000",
                    "PkgName": "zlib",
                    "InstalledVersion": "1.2.11",
                    "Severity": "HIGH",
                },
            ],
        }
    ],
}

_SCAN_RESULT_2 = {
    "ArtifactName": "nginx:latest",
    "Results": [
        {
            "Target": "nginx:latest",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-1000",
                    "PkgName": "libssl",
                    "InstalledVersion": "1.1.1",
                    "Severity": "CRITICAL",
                },
            ],
        }
    ],
}


class TestScanResultFIXEDIntegration:
    """Integration tests: two sequential scan_result messages through handle_connection.

    Exercises process_scan_result via the full WebSocket lifecycle so that the
    FIXED reconciliation logic is covered end-to-end (WS → aggregator → DB).
    """

    async def _create_agent(self, session) -> Agent:
        agent = Agent(name="ws-test-agent", token_hash=hash_token(generate_token()))
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        return agent

    async def test_absent_finding_marked_fixed_via_ws(self, session):
        """A finding present in scan 1 but absent from scan 2 must become FIXED."""
        manager = ConnectionManager()
        real_agent = await self._create_agent(session)

        ws = AsyncMock()
        ws.receive_json = AsyncMock(
            side_effect=[
                {"type": "scan_result", "data": _SCAN_RESULT_1, "container_name": "my-nginx"},
                {"type": "scan_result", "data": _SCAN_RESULT_2, "container_name": "my-nginx"},
                WebSocketDisconnect(code=1000),
            ]
        )

        with patch.object(manager, "authenticate", new=AsyncMock(return_value=real_agent)):
            await manager.handle_connection(ws, session)

        findings = (await session.execute(select(Finding))).scalars().all()
        libssl = next(f for f in findings if f.package_name == "libssl")
        zlib = next(f for f in findings if f.package_name == "zlib")
        assert libssl.status == FindingStatus.ACTIVE
        assert zlib.status == FindingStatus.FIXED

    async def test_empty_scan_marks_all_findings_fixed_via_ws(self, session):
        """An empty scan result should mark all previously active findings as FIXED."""
        manager = ConnectionManager()
        real_agent = await self._create_agent(session)

        empty_scan = {**_SCAN_RESULT_1, "Results": []}
        ws = AsyncMock()
        ws.receive_json = AsyncMock(
            side_effect=[
                {"type": "scan_result", "data": _SCAN_RESULT_1, "container_name": "my-nginx"},
                {"type": "scan_result", "data": empty_scan, "container_name": "my-nginx"},
                WebSocketDisconnect(code=1000),
            ]
        )

        with patch.object(manager, "authenticate", new=AsyncMock(return_value=real_agent)):
            await manager.handle_connection(ws, session)

        findings = (await session.execute(select(Finding))).scalars().all()
        assert len(findings) == 2
        assert all(f.status == FindingStatus.FIXED for f in findings)
