"""
Integration tests for the hub–agent WebSocket protocol.

Coverage:
- Full handshake completes without error
- Hub challenge carries a valid Ed25519 signature (SimulatedAgent verifies it)
- Agent appears online in the REST API after handshake
- Agent appears offline after disconnect
- Connection with wrong token is rejected by the hub
- Heartbeat → heartbeat_ack round-trip works
"""

import asyncio
import json

import pytest
import websockets


class TestHandshake:
    async def test_full_handshake_succeeds(self, connected_agent):
        # connect_and_handshake() raises on protocol/signature error — reaching here means OK.
        assert connected_agent._ws is not None

    async def test_agent_status_is_online_after_connect(self, hub, registered_agent, connected_agent):
        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.status_code == 200
        assert r.json()["status"] == "online"

    async def test_agent_status_is_offline_after_disconnect(self, hub, registered_agent, connected_agent):
        await connected_agent.close()
        # Give the hub a moment to process the disconnect
        await asyncio.sleep(0.5)
        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "offline"

    async def test_invalid_token_connection_is_rejected(self, hub_base_url):
        """Hub should close the connection when token doesn't match any agent."""
        with pytest.raises(Exception):
            # The hub closes the WebSocket with code 4001 on auth failure.
            # websockets will raise ConnectionClosedError or similar.
            ws = await websockets.connect(
                hub_base_url.replace("http://", "ws://") + "/ws/agent",
                additional_headers={"Authorization": "Bearer totally-invalid-token"},
            )
            # Hub closes the connection; reading will raise
            await asyncio.wait_for(ws.recv(), timeout=5.0)

    async def test_missing_token_connection_is_rejected(self, hub_base_url):
        """Hub rejects connections with no Authorization header."""
        with pytest.raises(Exception):
            ws = await websockets.connect(
                hub_base_url.replace("http://", "ws://") + "/ws/agent",
            )
            await asyncio.wait_for(ws.recv(), timeout=5.0)


class TestHeartbeat:
    async def test_heartbeat_receives_ack(self, connected_agent):
        await connected_agent.recv_heartbeat_ack()

    async def test_multiple_heartbeats_work(self, connected_agent):
        await connected_agent.recv_heartbeat_ack()
        await connected_agent.recv_heartbeat_ack()

    async def test_heartbeat_keeps_agent_online(self, hub, registered_agent, connected_agent):
        await connected_agent.recv_heartbeat_ack()
        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "online"
