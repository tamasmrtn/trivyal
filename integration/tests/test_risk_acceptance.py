"""
Integration tests for the risk acceptance sub-resource.

Coverage:
- Create risk acceptance → finding status becomes "accepted"
- List acceptances for finding → returns the created acceptance
- Acceptance body contains reason, accepted_by, expires_at, created_at
- Revoke acceptance → finding status reverts to "active"
- Revoked acceptance no longer in list
- Create acceptance on unknown finding → 404
- Revoke unknown acceptance → 404
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from helpers.trivy_fixtures import SCAN_V1


@pytest.fixture
async def seeded_finding(hub, registered_agent, connected_agent):
    """Trigger a scan and return a finding ID (CVE-2024-9000 / CRITICAL)."""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
        tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
    await asyncio.sleep(0.5)

    r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
    return r.json()["data"][0]["id"]


class TestCreateAcceptance:
    async def test_creates_acceptance_and_changes_finding_status(self, hub, seeded_finding):
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        r = await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "Mitigated by WAF", "expires_at": expires},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["reason"] == "Mitigated by WAF"
        assert body["finding_id"] == seeded_finding
        assert "accepted_by" in body
        assert "created_at" in body

        # Finding status should now be "accepted"
        finding_r = await hub.get(f"/api/v1/findings/{seeded_finding}")
        assert finding_r.json()["status"] == "accepted"

    async def test_acceptance_without_expiry(self, hub, seeded_finding):
        r = await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "No fix available", "expires_at": None},
        )
        assert r.status_code == 201
        assert r.json()["expires_at"] is None

    async def test_unknown_finding_returns_404(self, hub):
        r = await hub.post(
            "/api/v1/findings/nonexistent0000000000000000000000000/acceptances",
            json={"reason": "Test"},
        )
        assert r.status_code == 404


class TestListAcceptances:
    async def test_lists_created_acceptance(self, hub, seeded_finding):
        await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "Listed reason"},
        )
        r = await hub.get(f"/api/v1/findings/{seeded_finding}/acceptances")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        assert any(a["reason"] == "Listed reason" for a in items)

    async def test_empty_list_before_any_acceptance(self, hub, seeded_finding):
        r = await hub.get(f"/api/v1/findings/{seeded_finding}/acceptances")
        assert r.status_code == 200
        assert r.json() == []

    async def test_unknown_finding_returns_404(self, hub):
        r = await hub.get("/api/v1/findings/nonexistent0000000000000000000000000/acceptances")
        assert r.status_code == 404


class TestRevokeAcceptance:
    async def test_revoke_reverts_finding_to_active(self, hub, seeded_finding):
        # Create acceptance
        create_r = await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "Temporary"},
        )
        acceptance_id = create_r.json()["id"]

        # Revoke
        del_r = await hub.delete(f"/api/v1/findings/{seeded_finding}/acceptances/{acceptance_id}")
        assert del_r.status_code == 204

        # Finding should be active again
        finding_r = await hub.get(f"/api/v1/findings/{seeded_finding}")
        assert finding_r.json()["status"] == "active"

    async def test_revoked_acceptance_not_in_list(self, hub, seeded_finding):
        create_r = await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "To revoke"},
        )
        acceptance_id = create_r.json()["id"]
        await hub.delete(f"/api/v1/findings/{seeded_finding}/acceptances/{acceptance_id}")

        list_r = await hub.get(f"/api/v1/findings/{seeded_finding}/acceptances")
        ids = [a["id"] for a in list_r.json()]
        assert acceptance_id not in ids

    async def test_unknown_acceptance_returns_404(self, hub, seeded_finding):
        r = await hub.delete(
            f"/api/v1/findings/{seeded_finding}/acceptances/nonexistent00000000000000000000000"
        )
        assert r.status_code == 404
