"""
Integration tests for the images endpoint.

Images are populated by ingesting scan results via the WebSocket. The images
endpoint aggregates Container records with their active Finding counts.

Coverage:
- Empty list when no scan data exists
- Returns image with correct name, tag, severity breakdown, and CVE counts
- fixable_cves count is correct (only findings with a FixedVersion)
- fixable filter returns only images with at least one fixable CVE
- Agents list is included in each image response
- Sort by image_name (asc/desc) across two images
- Sort by fixable_cves (desc) prioritises the more-fixable image
- Pagination parameters are respected
"""

import asyncio

import pytest

from helpers.trivy_fixtures import SCAN_REDIS, SCAN_V1


@pytest.fixture
async def scan_result(hub, registered_agent, connected_agent):
    """Trigger a scan with SCAN_V1 (nginx:1.27) and wait for persistence."""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
        tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
    await asyncio.sleep(0.5)


@pytest.fixture
async def two_image_scans(hub, registered_agent, connected_agent):
    """Seed two images: nginx (CRITICAL+HIGH fixable) and redis (MEDIUM unfixable)."""
    # First scan: nginx:1.27
    async with asyncio.TaskGroup() as tg:
        tg.create_task(hub.post(f"/api/v1/agents/{registered_agent['id']}/scans"))
        tg.create_task(connected_agent.handle_scan_trigger_and_respond(SCAN_V1))
    await asyncio.sleep(0.3)

    # Second scan: redis:7.0 (sent directly — hub handles scan_result without a trigger)
    await connected_agent.send_scan_result(SCAN_REDIS)
    await asyncio.sleep(0.5)


class TestListImages:
    async def test_returns_empty_list(self, hub):
        r = await hub.get("/api/v1/images")
        assert r.status_code == 200
        assert r.json()["data"] == []
        assert r.json()["total"] == 0

    async def test_requires_auth(self, hub_anon):
        r = await hub_anon.get("/api/v1/images")
        assert r.status_code in (401, 403)

    async def test_returns_image_after_scan(self, hub, scan_result):
        r = await hub.get("/api/v1/images")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    async def test_image_name_and_tag(self, hub, scan_result):
        r = await hub.get("/api/v1/images")
        images = r.json()["data"]
        nginx = next((i for i in images if i["image_name"] == "nginx"), None)
        assert nginx is not None
        assert nginx["image_tag"] == "1.27"

    async def test_image_severity_breakdown(self, hub, scan_result):
        r = await hub.get("/api/v1/images")
        nginx = next(i for i in r.json()["data"] if i["image_name"] == "nginx")
        breakdown = nginx["severity_breakdown"]
        assert breakdown["critical"] >= 1
        assert breakdown["high"] >= 1

    async def test_image_cve_counts(self, hub, scan_result):
        r = await hub.get("/api/v1/images")
        nginx = next(i for i in r.json()["data"] if i["image_name"] == "nginx")
        # SCAN_V1 has 2 CVEs, both with FixedVersion
        assert nginx["total_cves"] >= 2
        assert nginx["fixable_cves"] >= 2

    async def test_image_includes_agent_info(self, hub, registered_agent, scan_result):
        r = await hub.get("/api/v1/images")
        nginx = next(i for i in r.json()["data"] if i["image_name"] == "nginx")
        agent_ids = [a["id"] for a in nginx["agents"]]
        assert registered_agent["id"] in agent_ids

    async def test_image_response_has_expected_fields(self, hub, scan_result):
        r = await hub.get("/api/v1/images")
        img = r.json()["data"][0]
        for field in ("image_name", "total_cves", "fixable_cves", "severity_breakdown", "agents", "container_count"):
            assert field in img, f"Missing field: {field}"


class TestFixableFilter:
    async def test_fixable_filter_returns_only_images_with_fixable_cves(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"fixable": "true"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert all(img["fixable_cves"] > 0 for img in data)
        # nginx has fixable CVEs; redis does not
        names = {img["image_name"] for img in data}
        assert "nginx" in names
        assert "redis" not in names

    async def test_no_fixable_filter_returns_all_images(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images")
        assert r.status_code == 200
        names = {img["image_name"] for img in r.json()["data"]}
        assert "nginx" in names
        assert "redis" in names


class TestImageSort:
    async def test_sort_by_image_name_asc(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"sort_by": "image_name", "sort_dir": "asc"})
        assert r.status_code == 200
        names = [img["image_name"] for img in r.json()["data"]]
        # "nginx" < "redis" alphabetically
        assert names.index("nginx") < names.index("redis")

    async def test_sort_by_image_name_desc(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"sort_by": "image_name", "sort_dir": "desc"})
        assert r.status_code == 200
        names = [img["image_name"] for img in r.json()["data"]]
        assert names.index("redis") < names.index("nginx")

    async def test_sort_by_fixable_cves_desc(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"sort_by": "fixable_cves", "sort_dir": "desc"})
        assert r.status_code == 200
        data = r.json()["data"]
        # nginx (2 fixable) should come before redis (0 fixable)
        names = [img["image_name"] for img in data]
        assert names.index("nginx") < names.index("redis")

    async def test_sort_by_total_cves_desc(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"sort_by": "total_cves", "sort_dir": "desc"})
        assert r.status_code == 200
        data = r.json()["data"]
        # nginx (2 CVEs) > redis (1 CVE)
        names = [img["image_name"] for img in data]
        assert names.index("nginx") < names.index("redis")


class TestImagePagination:
    async def test_page_size_is_respected(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"page_size": 1, "page": 1})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 2
        assert len(body["data"]) == 1

    async def test_second_page_returns_remaining_image(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"page_size": 1, "page": 2})
        assert r.status_code == 200
        assert len(r.json()["data"]) == 1

    async def test_out_of_range_page_returns_empty(self, hub, two_image_scans):
        r = await hub.get("/api/v1/images", params={"page_size": 50, "page": 99})
        assert r.status_code == 200
        assert r.json()["data"] == []
