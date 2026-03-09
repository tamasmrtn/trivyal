"""
Integration tests: vulnerability findings are auto-marked FIXED when absent
from a subsequent scan.

Coverage:
- Finding present in scan 1 but absent from scan 2 → status becomes "fixed"
- Finding still present in scan 2 → status stays "active"
- All findings absent from scan 2 (empty scan) → all become "fixed"
"""

import asyncio

import pytest

from helpers.trivy_fixtures import SCAN_V1, SCAN_V1_PARTIAL


@pytest.fixture
async def scan_v1(hub, registered_agent, connected_agent):
    """Trigger SCAN_V1 (openssl CRITICAL + libexpat1 HIGH) and wait for ingestion."""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
        tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
    await asyncio.sleep(0.5)


class TestFindingFixedStatus:
    async def test_absent_finding_becomes_fixed(self, hub, scan_v1, connected_agent):
        """libexpat1 is in scan 1 but absent from scan 2 — must become fixed."""
        # Send a second scan result without waiting for a trigger (unsolicited push)
        await connected_agent.send_scan_result(SCAN_V1_PARTIAL)
        await asyncio.sleep(0.5)

        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9001"})
        assert r.status_code == 200
        findings = r.json()["data"]
        assert len(findings) == 1
        assert findings[0]["status"] == "fixed"

    async def test_present_finding_stays_active(self, hub, scan_v1, connected_agent):
        """openssl is in both scan 1 and scan 2 — must stay active."""
        await connected_agent.send_scan_result(SCAN_V1_PARTIAL)
        await asyncio.sleep(0.5)

        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
        assert r.status_code == 200
        findings = r.json()["data"]
        assert len(findings) == 1
        assert findings[0]["status"] == "active"

    async def test_empty_scan_marks_all_findings_fixed(self, hub, scan_v1, connected_agent):
        """An empty scan result must mark all previously active findings as fixed."""
        empty_scan = {**SCAN_V1, "Results": []}
        await connected_agent.send_scan_result(empty_scan)
        await asyncio.sleep(0.5)

        r = await hub.get("/api/v1/findings", params={"status": "active"})
        assert r.status_code == 200
        assert r.json()["total"] == 0

        r = await hub.get("/api/v1/findings", params={"status": "fixed"})
        assert r.status_code == 200
        assert r.json()["total"] == 2
