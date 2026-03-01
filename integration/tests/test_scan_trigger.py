"""
Integration tests for the on-demand scan trigger and result ingestion.

This is the most important integration test — it exercises the full
hub → agent (WebSocket) → hub (REST) round-trip.

Coverage:
- Trigger scan → 202 Accepted with job_id
- Agent receives scan_trigger message
- Agent sends back scan_result → hub ingests findings
- Findings appear via GET /api/v1/findings after scan
- Scan record appears via GET /api/v1/agents/{id}/scans
- Trigger on offline agent → 409
- Trigger on unknown agent → 404
- Agent status lifecycle: online → scanning → online
"""

import asyncio

import pytest

from helpers.trivy_fixtures import SCAN_CLEAN, SCAN_V1


class TestTriggerScan:
    async def test_returns_202_with_job_id(self, hub, registered_agent, connected_agent):
        async with asyncio.TaskGroup() as tg:
            trigger = tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond())

        resp = trigger.result()
        assert resp.status_code == 202
        body = resp.json()
        assert "job_id" in body
        assert len(body["job_id"]) > 0

    async def test_offline_agent_returns_409(self, hub, registered_agent):
        # registered_agent has no connected WS → should be offline
        r = await hub.post(f"/api/v1/agents/{registered_agent['id']}/scans")
        assert r.status_code == 409

    async def test_unknown_agent_returns_404(self, hub):
        r = await hub.post("/api/v1/agents/nonexistent000000000000000000000000/scans")
        assert r.status_code == 404

    async def test_agent_receives_scan_trigger(self, hub, registered_agent, connected_agent):
        """The simulated agent correctly receives the scan_trigger message."""
        await hub.post(f"/api/v1/agents/{registered_agent['id']}/scans")
        # handle_scan_trigger_and_respond waits for the trigger then replies
        await connected_agent.handle_scan_trigger_and_respond()  # would raise on wrong msg type


class TestScanResultIngestion:
    async def _do_scan(self, hub, agent_id, connected_agent, scan_data=None):
        """Trigger a scan and wait for findings to be ingested."""
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{agent_id}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(scan_data))
        # Allow the hub to persist results before assertions
        await asyncio.sleep(0.5)

    async def test_findings_appear_after_scan(self, hub, registered_agent, connected_agent):
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)

        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
        assert r.status_code == 200
        findings = r.json()["data"]
        assert any(f["cve_id"] == "CVE-2024-9000" for f in findings)

    async def test_both_findings_from_scan_are_ingested(self, hub, registered_agent, connected_agent):
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)

        critical_r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
        high_r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9001"})

        assert any(f["severity"] == "CRITICAL" for f in critical_r.json()["data"])
        assert any(f["severity"] == "HIGH" for f in high_r.json()["data"])

    async def test_scan_record_created(self, hub, registered_agent, connected_agent):
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}/scans")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    async def test_scan_record_has_severity_counts(self, hub, registered_agent, connected_agent):
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}/scans")
        scans = r.json()["data"]
        assert len(scans) >= 1
        scan = scans[0]
        assert scan["critical_count"] == 1
        assert scan["high_count"] == 1

    async def test_empty_scan_creates_no_findings(self, hub, registered_agent, connected_agent):
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_CLEAN)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}/scans")
        scans = r.json()["data"]
        assert len(scans) >= 1
        scan = scans[0]
        assert scan["critical_count"] == 0
        assert scan["high_count"] == 0
        assert scan["medium_count"] == 0


class TestAgentStatusLifecycle:
    async def test_agent_is_online_before_scan(self, hub, registered_agent, connected_agent):
        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "online"

    async def test_agent_is_online_after_scan_completes(self, hub, registered_agent, connected_agent):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond())
        await asyncio.sleep(0.5)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.json()["status"] == "online"
