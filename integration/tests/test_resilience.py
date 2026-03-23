"""
Resilience tests — verify hub and agent behavior under adverse conditions.

These tests exercise reconnection after hub restart and agent offline detection
when heartbeats stop.
"""

import asyncio
import subprocess
from pathlib import Path

import httpx
import pytest
import websockets

from helpers.agent_sim import SimulatedAgent


COMPOSE_DIR = Path(__file__).parent.parent
COMPOSE_FILE = COMPOSE_DIR / "docker-compose.test.yml"


class TestHubRestart:
    """Agent reconnects after hub container restarts."""

    async def test_agent_reconnects_after_hub_restart(
        self, hub_base_url, registered_agent
    ):
        ws_url = hub_base_url.replace("http://", "ws://") + "/ws/agent"

        # Connect agent and complete handshake
        agent = SimulatedAgent(
            hub_ws_url=ws_url,
            token=registered_agent["token"],
            hub_public_key=registered_agent["hub_public_key"],
        )
        await agent.connect_and_handshake()
        await agent.recv_heartbeat_ack()

        # Restart the hub container
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "restart", "hub"],
            cwd=str(COMPOSE_DIR),
            check=True,
            capture_output=True,
        )

        # Wait for hub to be healthy again
        for _ in range(30):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{hub_base_url}/api/health", timeout=2)
                    if resp.status_code == 200:
                        break
            except Exception:
                pass
            await asyncio.sleep(2)
        else:
            pytest.fail("Hub did not recover after restart")

        # Old connection should be dead — close it
        await agent.close()

        # New connection should succeed
        agent2 = SimulatedAgent(
            hub_ws_url=ws_url,
            token=registered_agent["token"],
            hub_public_key=registered_agent["hub_public_key"],
        )
        await agent2.connect_and_handshake()
        await agent2.recv_heartbeat_ack()
        await agent2.close()


class TestExtendedDisconnect:
    """Hub marks agent offline when heartbeats stop."""

    async def test_agent_marked_offline_after_disconnect(
        self, hub, hub_base_url, registered_agent
    ):
        ws_url = hub_base_url.replace("http://", "ws://") + "/ws/agent"

        # Connect and verify online status
        agent = SimulatedAgent(
            hub_ws_url=ws_url,
            token=registered_agent["token"],
            hub_public_key=registered_agent["hub_public_key"],
        )
        await agent.connect_and_handshake()
        await agent.recv_heartbeat_ack()

        resp = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert resp.json()["status"] == "online"

        # Abruptly close WebSocket (simulating network failure)
        await agent.close()

        # Give hub time to detect the disconnect
        await asyncio.sleep(2)

        resp = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert resp.json()["status"] == "offline"
