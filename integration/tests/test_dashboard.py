"""
Integration tests for the dashboard summary endpoint.

Coverage:
- Summary returns correct response shape
- Severity counts are non-negative integers
- Agent status counts appear after registering an agent
- CRITICAL/HIGH counts appear after ingesting a scan
- Summary only counts ACTIVE findings (not accepted/false_positive)

Note: because integration tests share a database, we assert on *relative* changes
(≥ some value) rather than exact totals, to stay robust in any test ordering.
"""

import asyncio

import pytest

from helpers.trivy_fixtures import SCAN_V1


class TestDashboardSummary:
    async def test_returns_correct_shape(self, hub):
        r = await hub.get("/api/v1/dashboard/summary")
        assert r.status_code == 200
        body = r.json()
        assert "severity_counts" in body
        assert "agent_status_counts" in body
        assert "total_findings" in body
        assert "total_agents" in body

    async def test_severity_counts_shape(self, hub):
        r = await hub.get("/api/v1/dashboard/summary")
        sev = r.json()["severity_counts"]
        for key in ("critical", "high", "medium", "low", "unknown"):
            assert key in sev
            assert isinstance(sev[key], int)
            assert sev[key] >= 0

    async def test_agent_status_counts_shape(self, hub):
        r = await hub.get("/api/v1/dashboard/summary")
        agent_counts = r.json()["agent_status_counts"]
        for key in ("online", "offline", "scanning"):
            assert key in agent_counts
            assert isinstance(agent_counts[key], int)
            assert agent_counts[key] >= 0

    async def test_offline_agent_counted(self, hub, registered_agent):
        r = await hub.get("/api/v1/dashboard/summary")
        body = r.json()
        assert body["total_agents"] >= 1
        assert body["agent_status_counts"]["offline"] >= 1

    async def test_online_agent_counted(self, hub, registered_agent, connected_agent):
        r = await hub.get("/api/v1/dashboard/summary")
        body = r.json()
        assert body["agent_status_counts"]["online"] >= 1

    async def test_severity_counts_after_scan(self, hub, registered_agent, connected_agent):
        agent_id = registered_agent["id"]
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{agent_id}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
        await asyncio.sleep(0.5)

        r = await hub.get("/api/v1/dashboard/summary")
        sev = r.json()["severity_counts"]
        assert sev["critical"] >= 1
        assert sev["high"] >= 1

    async def test_accepted_findings_not_in_severity_counts(self, hub, registered_agent, connected_agent):
        """Accepted findings should not appear in the active severity counts."""
        agent_id = registered_agent["id"]
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{agent_id}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
        await asyncio.sleep(0.5)

        # Accept all CRITICAL findings
        findings_r = await hub.get("/api/v1/findings", params={"severity": "CRITICAL", "status": "active"})
        before_critical = r_summary = (await hub.get("/api/v1/dashboard/summary")).json()["severity_counts"]["critical"]

        for f in findings_r.json()["data"]:
            await hub.post(f"/api/v1/findings/{f['id']}/acceptances", json={"reason": "Dashboard test"})

        r = await hub.get("/api/v1/dashboard/summary")
        after_critical = r.json()["severity_counts"]["critical"]
        assert after_critical < before_critical
