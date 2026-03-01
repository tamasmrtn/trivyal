"""
Integration tests for scan history endpoints.

Coverage:
- List scans for a specific agent (per-agent sub-resource)
- Unknown agent → 404
- Global scan list (across all agents)
- Get scan detail by ID (includes trivy_raw)
- Unknown scan → 404
- Multiple scans accumulate in history
- Scan record shape: id, container_id, agent_id, scanned_at, severity counts
"""

import asyncio

import pytest

from helpers.trivy_fixtures import SCAN_CLEAN, SCAN_V1, SCAN_V2


@pytest.fixture
async def one_scan(hub, registered_agent, connected_agent):
    """Perform one scan; returns the agent_id."""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
        tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
    await asyncio.sleep(0.5)
    return registered_agent["id"]


class TestListAgentScans:
    async def test_returns_paginated_envelope(self, hub, one_scan):
        r = await hub.get(f"/api/v1/agents/{one_scan}/scans")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "total" in body

    async def test_scan_appears_after_trigger(self, hub, one_scan):
        r = await hub.get(f"/api/v1/agents/{one_scan}/scans")
        assert r.json()["total"] >= 1

    async def test_scan_record_has_expected_shape(self, hub, one_scan):
        r = await hub.get(f"/api/v1/agents/{one_scan}/scans")
        scan = r.json()["data"][0]
        assert "id" in scan
        assert "container_id" in scan
        assert "agent_id" in scan
        assert "scanned_at" in scan
        assert "critical_count" in scan
        assert "high_count" in scan
        assert scan["agent_id"] == one_scan

    async def test_scan_severity_counts_match_payload(self, hub, one_scan):
        r = await hub.get(f"/api/v1/agents/{one_scan}/scans")
        scan = r.json()["data"][0]
        # SCAN_V1 has 1 CRITICAL + 1 HIGH
        assert scan["critical_count"] == 1
        assert scan["high_count"] == 1
        assert scan["medium_count"] == 0

    async def test_unknown_agent_returns_404(self, hub):
        r = await hub.get("/api/v1/agents/nonexistent000000000000000000000000/scans")
        assert r.status_code == 404

    async def test_multiple_scans_accumulate(self, hub, registered_agent, connected_agent):
        agent_id = registered_agent["id"]
        # First scan
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{agent_id}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
        await asyncio.sleep(0.5)

        # Second scan
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{agent_id}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V2))
        await asyncio.sleep(0.5)

        r = await hub.get(f"/api/v1/agents/{agent_id}/scans")
        assert r.json()["total"] >= 2


class TestGlobalScans:
    async def test_returns_paginated_envelope(self, hub, one_scan):
        r = await hub.get("/api/v1/scans")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "total" in body

    async def test_scan_appears_in_global_list(self, hub, one_scan):
        r = await hub.get("/api/v1/scans")
        assert r.json()["total"] >= 1

    async def test_global_list_has_correct_shape(self, hub, one_scan):
        r = await hub.get("/api/v1/scans")
        scan = r.json()["data"][0]
        assert "id" in scan
        assert "agent_id" in scan
        assert "scanned_at" in scan


class TestGetScan:
    async def test_returns_scan_detail_with_raw_json(self, hub, one_scan):
        list_r = await hub.get(f"/api/v1/agents/{one_scan}/scans")
        scan_id = list_r.json()["data"][0]["id"]

        r = await hub.get(f"/api/v1/scans/{scan_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == scan_id
        # Detail endpoint includes trivy_raw
        assert "trivy_raw" in body
        assert body["trivy_raw"] is not None

    async def test_trivy_raw_matches_original_payload(self, hub, one_scan):
        list_r = await hub.get(f"/api/v1/agents/{one_scan}/scans")
        scan_id = list_r.json()["data"][0]["id"]

        r = await hub.get(f"/api/v1/scans/{scan_id}")
        trivy_raw = r.json()["trivy_raw"]
        assert trivy_raw["ArtifactName"] == SCAN_V1["ArtifactName"]

    async def test_unknown_scan_returns_404(self, hub):
        r = await hub.get("/api/v1/scans/nonexistent000000000000000000000000")
        assert r.status_code == 404
