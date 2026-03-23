"""
Load tests — verify hub handles concurrent agents and large scan payloads.

These tests are marked with @pytest.mark.load and are excluded from regular
CI runs. They run only in the nightly workflow or via `make test-load`.
"""

import asyncio
import uuid

import pytest

from helpers.agent_sim import SimulatedAgent
from helpers.trivy_fixtures import make_large_scan


pytestmark = pytest.mark.load


class TestMultiAgentLoad:
    """Hub handles multiple concurrent agents sending scan results."""

    async def test_ten_agents_simultaneous_scan(self, hub, hub_base_url):
        """Register 10 agents, connect all, send scans concurrently."""
        ws_url = hub_base_url.replace("http://", "ws://") + "/ws/agent"
        agents = []

        try:
            # Register and connect 10 agents
            for i in range(10):
                name = f"load-{uuid.uuid4().hex[:8]}"
                resp = await hub.post("/api/v1/agents", json={"name": name})
                resp.raise_for_status()
                data = resp.json()

                sim = SimulatedAgent(
                    hub_ws_url=ws_url,
                    token=data["token"],
                    hub_public_key=data["hub_public_key"],
                )
                await sim.connect_and_handshake()
                agents.append((data, sim))

            # Each agent sends a scan result concurrently
            scan_data = make_large_scan(1)[0]  # 1 container per agent
            await asyncio.gather(
                *(sim.send_scan_result(scan_data) for _, sim in agents)
            )

            # Allow hub to process all results
            await asyncio.sleep(5)

            # Verify dashboard reflects all agents
            resp = await hub.get("/api/v1/dashboard/summary")
            resp.raise_for_status()
            dashboard = resp.json()
            online_count = dashboard["agent_status_counts"].get("online", 0)
            assert online_count >= 10, f"Expected 10 online agents, got {online_count}"

        finally:
            for data, sim in agents:
                await sim.close()
                await hub.delete(f"/api/v1/agents/{data['id']}")

    async def test_hundred_containers_per_agent(
        self, hub, hub_base_url, registered_agent
    ):
        """Single agent sends scan results for 100 different containers."""
        ws_url = hub_base_url.replace("http://", "ws://") + "/ws/agent"
        agent = SimulatedAgent(
            hub_ws_url=ws_url,
            token=registered_agent["token"],
            hub_public_key=registered_agent["hub_public_key"],
        )
        await agent.connect_and_handshake()

        try:
            # Send 100 scan results (each for a different image)
            scans = make_large_scan(100)
            for scan in scans:
                await agent.send_scan_result(scan)

            # Allow hub to process
            await asyncio.sleep(10)

            # Verify findings were created
            resp = await hub.get(
                "/api/v1/findings",
                params={"page_size": 1},
            )
            resp.raise_for_status()
            total = resp.json()["total"]
            # 100 containers * 2 vulns each = 200 findings
            assert total >= 200, f"Expected >= 200 findings, got {total}"

        finally:
            await agent.close()
