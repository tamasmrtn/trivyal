"""
Integration tests for misconfiguration endpoints.

Setup: misconfig findings are seeded by sending a `misconfig_result` message
directly over the WebSocket (no scan trigger required — the hub handles the
message type independently of the CVE scan flow).

Coverage:
- Misconfig result ingested via WebSocket (misconfig_result message)
- List misconfigs: empty, after ingest, response shape
- Filter by severity, status, check_id, agent_id
- Get single misconfig by ID, 404 for unknown
- Update status (false_positive)
- Risk acceptance: create changes status to accepted, revoke reverts to active
- Fixed lifecycle: findings absent from a second scan become status=fixed
"""

import asyncio

import pytest

from helpers.trivy_fixtures import MISCONFIG_CLEAN, MISCONFIG_V1


@pytest.fixture
async def misconfig_result(connected_agent):
    """Send MISCONFIG_V1 via the simulated agent and wait for hub to persist."""
    await connected_agent.send_misconfig_result(MISCONFIG_V1)
    await asyncio.sleep(0.5)


class TestListMisconfigs:
    async def test_returns_empty_list(self, hub):
        r = await hub.get("/api/v1/misconfigs")
        assert r.status_code == 200
        assert r.json()["data"] == []
        assert r.json()["total"] == 0

    async def test_requires_auth(self, hub_anon):
        r = await hub_anon.get("/api/v1/misconfigs")
        assert r.status_code in (401, 403)

    async def test_returns_misconfigs_after_ingest(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs")
        assert r.status_code == 200
        assert r.json()["total"] >= 2

    async def test_response_has_expected_fields(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs")
        item = r.json()["data"][0]
        for field in ("id", "check_id", "severity", "status", "image_name", "title", "first_seen", "last_seen"):
            assert field in item, f"Missing field: {field}"

    async def test_image_name_is_correct(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs")
        # image_name stored without tag ("linuxserver/plex")
        assert all(item["image_name"] == "linuxserver/plex" for item in r.json()["data"])

    async def test_filter_by_severity_high(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs", params={"severity": "HIGH"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) >= 1
        assert all(f["severity"] == "HIGH" for f in data)
        assert any(f["check_id"] == "PRIV_001" for f in data)

    async def test_filter_by_severity_medium(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs", params={"severity": "MEDIUM"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) >= 1
        assert all(f["severity"] == "MEDIUM" for f in data)
        assert any(f["check_id"] == "NET_001" for f in data)

    async def test_filter_by_status_active(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs", params={"status": "active"})
        assert r.status_code == 200
        assert r.json()["total"] >= 2
        assert all(f["status"] == "active" for f in r.json()["data"])

    async def test_filter_by_status_fixed_returns_empty(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs", params={"status": "fixed"})
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_filter_by_check_id(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs", params={"check_id": "PRIV_001"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) >= 1
        assert all(f["check_id"] == "PRIV_001" for f in data)

    async def test_filter_by_agent_id(self, hub, registered_agent, misconfig_result):
        r = await hub.get("/api/v1/misconfigs", params={"agent_id": registered_agent["id"]})
        assert r.status_code == 200
        assert r.json()["total"] >= 2

    async def test_filter_by_wrong_agent_id_returns_empty(self, hub, misconfig_result):
        r = await hub.get("/api/v1/misconfigs", params={"agent_id": "nonexistent000000000000000000000000"})
        assert r.status_code == 200
        assert r.json()["total"] == 0


class TestGetMisconfig:
    async def test_unknown_id_returns_404(self, hub):
        r = await hub.get("/api/v1/misconfigs/nonexistent000000000000000000000000")
        assert r.status_code == 404

    async def test_returns_misconfig_detail(self, hub, misconfig_result):
        list_r = await hub.get("/api/v1/misconfigs", params={"check_id": "PRIV_001"})
        finding_id = list_r.json()["data"][0]["id"]

        r = await hub.get(f"/api/v1/misconfigs/{finding_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == finding_id
        assert body["check_id"] == "PRIV_001"
        assert body["severity"] == "HIGH"
        assert body["status"] == "active"
        assert body["image_name"] == "linuxserver/plex"
        assert body["container_name"] == "plex"


class TestUpdateMisconfig:
    async def _get_finding_id(self, hub, check_id: str) -> str:
        r = await hub.get("/api/v1/misconfigs", params={"check_id": check_id})
        return r.json()["data"][0]["id"]

    async def test_mark_false_positive(self, hub, misconfig_result):
        fid = await self._get_finding_id(hub, "PRIV_001")

        r = await hub.patch(f"/api/v1/misconfigs/{fid}", json={"status": "false_positive"})
        assert r.status_code == 200
        assert r.json()["status"] == "false_positive"

    async def test_false_positive_appears_in_status_filter(self, hub, misconfig_result):
        fid = await self._get_finding_id(hub, "PRIV_001")
        await hub.patch(f"/api/v1/misconfigs/{fid}", json={"status": "false_positive"})

        r = await hub.get("/api/v1/misconfigs", params={"status": "false_positive"})
        ids = [f["id"] for f in r.json()["data"]]
        assert fid in ids

    async def test_update_unknown_misconfig_returns_404(self, hub):
        r = await hub.patch(
            "/api/v1/misconfigs/nonexistent000000000000000000000000",
            json={"status": "false_positive"},
        )
        assert r.status_code == 404


class TestMisconfigAcceptance:
    async def _get_finding_id(self, hub, check_id: str) -> str:
        r = await hub.get("/api/v1/misconfigs", params={"check_id": check_id})
        return r.json()["data"][0]["id"]

    async def test_create_acceptance_returns_201(self, hub, misconfig_result):
        fid = await self._get_finding_id(hub, "PRIV_001")

        r = await hub.post(
            f"/api/v1/misconfigs/{fid}/acceptances",
            json={"reason": "Required for GPU passthrough"},
        )
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["reason"] == "Required for GPU passthrough"

    async def test_create_acceptance_changes_status_to_accepted(self, hub, misconfig_result):
        fid = await self._get_finding_id(hub, "PRIV_001")
        await hub.post(f"/api/v1/misconfigs/{fid}/acceptances", json={"reason": "GPU passthrough"})

        r = await hub.get(f"/api/v1/misconfigs/{fid}")
        assert r.json()["status"] == "accepted"

    async def test_revoke_acceptance_restores_active(self, hub, misconfig_result):
        fid = await self._get_finding_id(hub, "NET_001")
        acc_r = await hub.post(
            f"/api/v1/misconfigs/{fid}/acceptances",
            json={"reason": "Home network setup"},
        )
        acceptance_id = acc_r.json()["id"]

        del_r = await hub.delete(f"/api/v1/misconfigs/{fid}/acceptances/{acceptance_id}")
        assert del_r.status_code == 204

        r = await hub.get(f"/api/v1/misconfigs/{fid}")
        assert r.json()["status"] == "active"

    async def test_unknown_finding_returns_404(self, hub):
        r = await hub.post(
            "/api/v1/misconfigs/nonexistent000000000000000000000000/acceptances",
            json={"reason": "test"},
        )
        assert r.status_code == 404

    async def test_revoke_unknown_acceptance_returns_404(self, hub, misconfig_result):
        fid = await self._get_finding_id(hub, "PRIV_001")
        r = await hub.delete(f"/api/v1/misconfigs/{fid}/acceptances/nonexistent000000000000000000000000")
        assert r.status_code == 404


class TestMisconfigFixedLifecycle:
    async def test_misconfig_marked_fixed_when_absent_from_second_scan(
        self, hub, connected_agent
    ):
        """PRIV_001 and NET_001 appear in scan 1; absent in MISCONFIG_CLEAN → fixed."""
        await connected_agent.send_misconfig_result(MISCONFIG_V1)
        await asyncio.sleep(0.5)

        # Verify both are active
        r = await hub.get("/api/v1/misconfigs", params={"status": "active"})
        assert r.json()["total"] >= 2

        # Second scan for the same container with no findings
        await connected_agent.send_misconfig_result(MISCONFIG_CLEAN)
        await asyncio.sleep(0.5)

        r = await hub.get("/api/v1/misconfigs", params={"status": "fixed"})
        fixed_check_ids = {f["check_id"] for f in r.json()["data"]}
        assert "PRIV_001" in fixed_check_ids
        assert "NET_001" in fixed_check_ids

    async def test_second_scan_with_same_findings_keeps_them_active(
        self, hub, connected_agent
    ):
        """Re-sending MISCONFIG_V1 should keep existing findings active (not re-create or fix)."""
        await connected_agent.send_misconfig_result(MISCONFIG_V1)
        await asyncio.sleep(0.5)

        await connected_agent.send_misconfig_result(MISCONFIG_V1)
        await asyncio.sleep(0.5)

        r = await hub.get("/api/v1/misconfigs", params={"status": "active"})
        active_check_ids = {f["check_id"] for f in r.json()["data"]}
        assert "PRIV_001" in active_check_ids
        assert "NET_001" in active_check_ids

        # No duplicates — still exactly 2 active for this check_id
        r_priv = await hub.get("/api/v1/misconfigs", params={"check_id": "PRIV_001", "status": "active"})
        assert r_priv.json()["total"] == 1
