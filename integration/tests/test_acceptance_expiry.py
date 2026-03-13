"""
Integration tests for automatic risk acceptance expiry.

The hub runs an expiry sweep every TRIVYAL_ACCEPTANCE_EXPIRY_INTERVAL seconds
(set to 2s in docker-compose.test.yml).  Tests create acceptances with
`expires_at` in the past, then poll until the hub reverts the finding status
back to "active" — or assert that future/permanent acceptances are untouched.

Coverage:
- Expired CVE finding acceptance → finding reverts to "active"
- Expired misconfig acceptance → misconfig reverts to "active"
- Acceptance with no expiry → finding remains "accepted"
- Acceptance with future expiry → finding remains "accepted"
- Expired acceptance row is deleted (no longer in list endpoint)
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from helpers.trivy_fixtures import MISCONFIG_V1, SCAN_V1

_POLL_INTERVAL = 0.5  # seconds between status checks
_POLL_TIMEOUT = 10.0  # seconds to wait for expiry loop to fire


async def _poll_finding_status(hub, finding_id: str, expected: str) -> bool:
    """Poll GET /findings/{id} until status matches expected or timeout."""
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        r = await hub.get(f"/api/v1/findings/{finding_id}")
        if r.json()["status"] == expected:
            return True
        await asyncio.sleep(_POLL_INTERVAL)
    return False


async def _poll_misconfig_status(hub, misconfig_id: str, expected: str) -> bool:
    """Poll GET /misconfigs/{id} until status matches expected or timeout."""
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        r = await hub.get(f"/api/v1/misconfigs/{misconfig_id}")
        if r.json()["status"] == expected:
            return True
        await asyncio.sleep(_POLL_INTERVAL)
    return False


@pytest.fixture
async def seeded_finding(hub, registered_agent, connected_agent):
    """Trigger a scan via the simulated agent and return the CVE-2024-9000 finding ID."""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
        tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
    await asyncio.sleep(0.5)

    r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
    return r.json()["data"][0]["id"]


@pytest.fixture
async def seeded_misconfig(hub, connected_agent):
    """Send MISCONFIG_V1 via the simulated agent and return the PRIV_001 misconfig ID."""
    await connected_agent.send_misconfig_result(MISCONFIG_V1)
    await asyncio.sleep(0.5)

    r = await hub.get("/api/v1/misconfigs", params={"check_id": "PRIV_001"})
    return r.json()["data"][0]["id"]


class TestExpiredFindingAcceptance:
    async def test_expired_acceptance_reverts_finding_to_active(self, hub, seeded_finding):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        r = await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "Will expire", "expires_at": past},
        )
        assert r.status_code == 201
        acceptance_id = r.json()["id"]

        # Finding should immediately be accepted
        status_r = await hub.get(f"/api/v1/findings/{seeded_finding}")
        assert status_r.json()["status"] == "accepted"

        # Wait for the expiry loop to revert it
        reverted = await _poll_finding_status(hub, seeded_finding, "active")
        assert reverted, "Finding did not revert to 'active' within timeout"

        # Acceptance row should be gone
        list_r = await hub.get(f"/api/v1/findings/{seeded_finding}/acceptances")
        ids = [a["id"] for a in list_r.json()]
        assert acceptance_id not in ids

    async def test_permanent_acceptance_not_expired(self, hub, seeded_finding):
        r = await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "Permanent — no expiry", "expires_at": None},
        )
        assert r.status_code == 201

        # Wait longer than the expiry interval to confirm nothing changes
        await asyncio.sleep(5)

        status_r = await hub.get(f"/api/v1/findings/{seeded_finding}")
        assert status_r.json()["status"] == "accepted"

    async def test_future_acceptance_not_expired(self, hub, seeded_finding):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        r = await hub.post(
            f"/api/v1/findings/{seeded_finding}/acceptances",
            json={"reason": "Not yet expired", "expires_at": future},
        )
        assert r.status_code == 201

        await asyncio.sleep(5)

        status_r = await hub.get(f"/api/v1/findings/{seeded_finding}")
        assert status_r.json()["status"] == "accepted"


class TestExpiredMisconfigAcceptance:
    async def test_expired_acceptance_reverts_misconfig_to_active(self, hub, seeded_misconfig):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        r = await hub.post(
            f"/api/v1/misconfigs/{seeded_misconfig}/acceptances",
            json={"reason": "Will expire", "expires_at": past},
        )
        assert r.status_code == 201

        status_r = await hub.get(f"/api/v1/misconfigs/{seeded_misconfig}")
        assert status_r.json()["status"] == "accepted"

        reverted = await _poll_misconfig_status(hub, seeded_misconfig, "active")
        assert reverted, "Misconfig did not revert to 'active' within timeout"
