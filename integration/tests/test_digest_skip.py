"""
Integration tests for the image-digest skip optimization.

When the agent determines that an image's digest is unchanged since the last
scan, it skips re-scanning and sends no scan_result for that image.

These tests verify the hub's observable behaviour across three paths:

1. Image unchanged → agent skips → hub scan history stays flat, findings unchanged
2. Image changed  → agent re-scans → hub records a new scan, findings reflect latest
3. Cache stale (max_scan_age exceeded) → agent forces rescan despite unchanged digest
   → hub records a new scan, newly-published CVEs appear as active findings
"""

import asyncio

import pytest

from helpers.trivy_fixtures import SCAN_V1, SCAN_V1_PLUS_NEW, SCAN_V2


class TestUnchangedImageSkip:
    """Agent sends one scan result then deliberately sends nothing on the next
    cycle — simulating the digest-match path (OPT-3 skip).
    """

    @pytest.fixture
    async def initial_scan(self, hub, registered_agent, connected_agent):
        """Trigger one scan and wait for hub to ingest the result."""
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
        await asyncio.sleep(0.5)

    async def test_scan_count_stays_at_one_when_no_rescan(
        self, hub, registered_agent, connected_agent, initial_scan
    ):
        """If the agent skips the second cycle (no scan_result sent), the hub
        must still have exactly one scan record for this agent.
        """
        # Simulate a second scan trigger where the agent decides to skip
        # (digest unchanged) — the agent receives the trigger but does not
        # send back a scan_result.
        trigger_task = asyncio.create_task(
            hub.post(f"/api/v1/agents/{registered_agent['id']}/scans")
        )
        await connected_agent.recv_scan_trigger(timeout=10.0)
        # Agent deliberately does NOT call send_scan_result here (digest match)
        await trigger_task
        await asyncio.sleep(0.5)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}/scans")
        assert r.status_code == 200
        assert r.json()["total"] == 1, (
            "Scan count must remain 1 when the agent skips re-scanning "
            "(no scan_result sent for unchanged image)"
        )

    async def test_findings_preserved_when_no_rescan(
        self, hub, registered_agent, connected_agent, initial_scan
    ):
        """Findings from the initial scan must remain active when the agent
        skips the second cycle.
        """
        # Second cycle: agent skips
        trigger_task = asyncio.create_task(
            hub.post(f"/api/v1/agents/{registered_agent['id']}/scans")
        )
        await connected_agent.recv_scan_trigger(timeout=10.0)
        await trigger_task
        await asyncio.sleep(0.5)

        r = await hub.get("/api/v1/findings", params={"status": "active"})
        assert r.status_code == 200
        assert r.json()["total"] >= 2, (
            "Findings from the first scan must stay active when the agent "
            "does not send a second scan_result"
        )


class TestChangedImageRescan:
    """Agent sends a second scan result after detecting a digest change — the
    hub must record a new scan and update findings accordingly.
    """

    async def _do_scan(self, hub, agent_id, connected_agent, scan_data):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{agent_id}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(scan_data))
        await asyncio.sleep(0.5)

    async def test_scan_count_grows_after_rescan(
        self, hub, registered_agent, connected_agent
    ):
        """Two scan results sent (simulating digest change) → hub must have
        two scan records for this agent.
        """
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V2)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}/scans")
        assert r.status_code == 200
        assert r.json()["total"] == 2, (
            "Hub must record a new scan every time the agent sends a scan_result "
            "(i.e. when the digest has changed)"
        )

    async def test_findings_updated_after_rescan(
        self, hub, registered_agent, connected_agent
    ):
        """After re-scanning with a different payload, findings from the first
        scan that are absent from the second must be marked fixed, and new
        findings from the second scan must be active.

        SCAN_V1  → CVE-2024-9000 (CRITICAL) + CVE-2024-9001 (HIGH)
        SCAN_V2  → CVE-2024-9002 (MEDIUM) only

        After re-scan: CVE-2024-9000 and CVE-2024-9001 become fixed,
                       CVE-2024-9002 becomes active.
        """
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V2)

        # Old findings must be fixed
        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9000"})
        assert r.json()["data"][0]["status"] == "fixed"

        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9001"})
        assert r.json()["data"][0]["status"] == "fixed"

        # New finding from the re-scan must be active
        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2024-9002"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 1
        assert data[0]["status"] == "active"


class TestStaleCacheRescan:
    """Agent forces a rescan because the cache exceeded max_scan_age_days, even
    though the image digest has not changed since the last scan.

    From the hub's perspective this looks identical to any other rescan — it
    receives a second scan_result for the same image.  The key scenario being
    validated is that newly-published CVEs (discovered by a fresh Trivy DB run)
    actually reach the hub when they should.

    SCAN_V1          → CVE-2024-9000 (CRITICAL) + CVE-2024-9001 (HIGH)
    SCAN_V1_PLUS_NEW → same two CVEs + CVE-2025-1000 (CRITICAL, newly published)
    """

    async def _do_scan(self, hub, agent_id, connected_agent, scan_data):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(hub.post(f"/api/v1/agents/{agent_id}/scans"))
            tg.create_task(connected_agent.handle_scan_trigger_and_respond(scan_data))
        await asyncio.sleep(0.5)

    async def test_scan_count_grows_after_stale_rescan(
        self, hub, registered_agent, connected_agent
    ):
        """Hub must record a second scan when the agent re-scans due to a stale
        cache, even though the image digest is unchanged.
        """
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)
        # Stale-cache path: agent rescans the same image (same digest) because
        # max_scan_age_days was exceeded — it sends a second scan_result.
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1_PLUS_NEW)

        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}/scans")
        assert r.status_code == 200
        assert r.json()["total"] == 2, (
            "Hub must record a new scan for every scan_result received, "
            "including stale-cache forced rescans"
        )

    async def test_existing_findings_remain_active_after_stale_rescan(
        self, hub, registered_agent, connected_agent
    ):
        """CVEs present in both the original and stale rescan must stay active."""
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1_PLUS_NEW)

        for cve_id in ("CVE-2024-9000", "CVE-2024-9001"):
            r = await hub.get("/api/v1/findings", params={"cve_id": cve_id})
            assert r.status_code == 200
            assert r.json()["data"][0]["status"] == "active", (
                f"{cve_id} must remain active after stale-cache rescan"
            )

    async def test_newly_published_cve_is_active_after_stale_rescan(
        self, hub, registered_agent, connected_agent
    ):
        """The core purpose of the stale-cache feature: a CVE that was not in
        the original scan but appears in the fresh Trivy run (because the
        vulnerability DB was updated) must be recorded as active.
        """
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1)
        await self._do_scan(hub, registered_agent["id"], connected_agent, SCAN_V1_PLUS_NEW)

        r = await hub.get("/api/v1/findings", params={"cve_id": "CVE-2025-1000"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 1, "Newly-published CVE must appear exactly once"
        assert data[0]["status"] == "active", (
            "CVE-2025-1000 must be active — it was only discovered on the "
            "stale-cache-triggered rescan after the vulnerability DB was updated"
        )
