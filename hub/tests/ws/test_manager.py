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

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import WebSocketDisconnect
from trivyal_hub.db.models import AgentStatus
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
