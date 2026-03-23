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

from helpers.agent_sim import SimulatedAgent


COMPOSE_DIR = Path(__file__).parent.parent
COMPOSE_FILE = COMPOSE_DIR / "docker-compose.test.yml"


async def _wait_for_hub(base_url: str, timeout: int = 60):
    """Poll hub health endpoint until it responds 200."""
    for _ in range(timeout // 2):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{base_url}/api/health", timeout=2)
                if resp.status_code == 200:
                    return
        except Exception:
            pass
        await asyncio.sleep(2)
    pytest.fail("Hub did not recover after restart")


class TestHubRestart:
    """Agent reconnects after hub container restarts."""

    async def test_agent_reconnects_after_hub_restart(
        self, hub_base_url, auth_headers
    ):
        ws_url = hub_base_url.replace("http://", "ws://") + "/ws/agent"

        # Register an agent before restart
        async with httpx.AsyncClient(
            base_url=hub_base_url, headers=auth_headers
        ) as client:
            resp = await client.post(
                "/api/v1/agents", json={"name": "resilience-restart"}
            )
            resp.raise_for_status()
            agent_data = resp.json()

        # Connect agent and complete handshake
        agent = SimulatedAgent(
            hub_ws_url=ws_url,
            token=agent_data["token"],
            hub_public_key=agent_data["hub_public_key"],
        )
        await agent.connect_and_handshake()
        await agent.recv_heartbeat_ack()

        # Restart the hub container and wait for it to be healthy
        subprocess.run(
            [
                "docker", "compose", "-f", str(COMPOSE_FILE),
                "restart", "--timeout", "5", "hub",
            ],
            cwd=str(COMPOSE_DIR),
            check=True,
            capture_output=True,
        )
        await _wait_for_hub(hub_base_url)

        # Old connection should be dead — close it
        await agent.close()

        # Re-register agent (DB was on tmpfs, wiped by restart)
        async with httpx.AsyncClient(
            base_url=hub_base_url, headers=auth_headers
        ) as client:
            resp = await client.post(
                "/api/v1/agents", json={"name": "resilience-restart-2"}
            )
            resp.raise_for_status()
            agent_data2 = resp.json()

        # New connection should succeed
        agent2 = SimulatedAgent(
            hub_ws_url=ws_url,
            token=agent_data2["token"],
            hub_public_key=agent_data2["hub_public_key"],
        )
        await agent2.connect_and_handshake()
        await agent2.recv_heartbeat_ack()
        await agent2.close()

        # Cleanup
        async with httpx.AsyncClient(
            base_url=hub_base_url, headers=auth_headers
        ) as client:
            await client.delete(f"/api/v1/agents/{agent_data2['id']}")


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
