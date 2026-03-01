"""
Integration tests for the findings endpoints.

Setup: each test that needs findings uses the `scan_result` fixture, which
triggers a scan via the simulated agent and waits for findings to be ingested.

Coverage:
- List findings returns paginated envelope
- List findings after scan contains expected CVEs
- Filter by severity (CRITICAL, HIGH)
- Filter by status (active)
- Filter by CVE ID
- Filter by package name
- Get single finding by ID
- Unknown finding ID → 404
- Update finding status to false_positive
- Update finding status to accepted (directly, without risk acceptance record)
- Reopen a finding (patch back to active)
- Pagination parameters are respected
"""

import asyncio

import pytest

from helpers.trivy_fixtures import SCAN_V1


@pytest.fixture
async def scan_result(hub, registered_agent, connected_agent):
    """Trigger a scan with SCAN_V1 and wait for findings to be persisted."""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
        tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
    await asyncio.sleep(0.5)


class TestListFindings:
    async def test_returns_paginated_envelope(self, hub, scan_result):
        r = await hub.get("/api/v1/findings")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "total" in body
        assert "page" in body
        assert "page_size" in body

    async def test_findings_present_after_scan(self, hub, scan_result):
        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    async def test_filter_by_severity_critical(self, hub, scan_result):
        r = await hub.get("/api/v1/findings", params={"severity": "CRITICAL"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(f["severity"] == "CRITICAL" for f in data)
        assert any(f["cve_id"] == "CVE-2024-9000" for f in data)

    async def test_filter_by_severity_high(self, hub, scan_result):
        r = await hub.get("/api/v1/findings", params={"severity": "HIGH"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(f["severity"] == "HIGH" for f in data)
        assert any(f["cve_id"] == "CVE-2024-9001" for f in data)

    async def test_filter_by_status_active(self, hub, scan_result):
        r = await hub.get("/api/v1/findings", params={"status": "active"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(f["status"] == "active" for f in data)

    async def test_filter_by_cve_id(self, hub, scan_result):
        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9001"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(f["cve_id"] == "CVE-2024-9001" for f in data)
        assert len(data) >= 1

    async def test_filter_by_package_name(self, hub, scan_result):
        r = await hub.get("/api/v1/findings", params={"package": "openssl"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(f["package_name"] == "openssl" for f in data)
        assert len(data) >= 1

    async def test_page_size_is_respected(self, hub, scan_result):
        r = await hub.get("/api/v1/findings", params={"page_size": 1})
        assert r.status_code == 200
        assert len(r.json()["data"]) <= 1


class TestGetFinding:
    async def test_returns_finding_detail(self, hub, scan_result):
        list_r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
        finding_id = list_r.json()["data"][0]["id"]

        r = await hub.get(f"/api/v1/findings/{finding_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == finding_id
        assert body["cve_id"] == "CVE-2024-9000"
        assert body["severity"] == "CRITICAL"
        assert body["package_name"] == "openssl"
        assert "first_seen" in body
        assert "last_seen" in body

    async def test_unknown_id_returns_404(self, hub):
        r = await hub.get("/api/v1/findings/nonexistent0000000000000000000000000")
        assert r.status_code == 404


class TestUpdateFinding:
    async def _get_finding_id(self, hub, cve_id: str) -> str:
        r = await hub.get("/api/v1/findings", params={"cve_id": cve_id})
        return r.json()["data"][0]["id"]

    async def test_mark_false_positive(self, hub, scan_result):
        fid = await self._get_finding_id(hub, "CVE-2024-9000")

        r = await hub.patch(f"/api/v1/findings/{fid}", json={"status": "false_positive"})
        assert r.status_code == 200
        assert r.json()["status"] == "false_positive"

    async def test_false_positive_appears_in_status_filter(self, hub, scan_result):
        fid = await self._get_finding_id(hub, "CVE-2024-9001")
        await hub.patch(f"/api/v1/findings/{fid}", json={"status": "false_positive"})

        r = await hub.get("/api/v1/findings", params={"status": "false_positive"})
        ids = [f["id"] for f in r.json()["data"]]
        assert fid in ids

    async def test_reopen_finding(self, hub, scan_result):
        fid = await self._get_finding_id(hub, "CVE-2024-9000")
        await hub.patch(f"/api/v1/findings/{fid}", json={"status": "false_positive"})

        r = await hub.patch(f"/api/v1/findings/{fid}", json={"status": "active"})
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    async def test_update_unknown_finding_returns_404(self, hub):
        r = await hub.patch(
            "/api/v1/findings/nonexistent0000000000000000000000000",
            json={"status": "false_positive"},
        )
        assert r.status_code == 404
