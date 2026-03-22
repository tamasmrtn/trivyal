"""Tests for the images API endpoint."""

from trivyal_hub.db.models import Container, Finding, ScanResult, Severity


async def _seed_image_with_findings(session, agent_id, image_name="nginx", image_tag="latest", fixable=True):
    """Create a container with scan results and findings."""
    container = Container(agent_id=agent_id, image_name=image_name, image_tag=image_tag)
    session.add(container)
    await session.flush()

    scan = ScanResult(container_id=container.id, agent_id=agent_id)
    session.add(scan)
    await session.flush()

    findings = []
    for cve_id, sev, fixed_ver in [
        ("CVE-2024-0001", Severity.CRITICAL, "1.1.2" if fixable else None),
        ("CVE-2024-0002", Severity.HIGH, "2.0.1" if fixable else None),
        ("CVE-2024-0003", Severity.MEDIUM, None),
    ]:
        f = Finding(
            scan_result_id=scan.id,
            cve_id=cve_id,
            package_name="libssl",
            installed_version="1.0",
            fixed_version=fixed_ver,
            severity=sev,
        )
        session.add(f)
        findings.append(f)

    await session.commit()
    return container, findings


class TestListImages:
    async def test_returns_empty_list(self, client, auth_header):
        response = await client.get("/api/v1/images", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_requires_auth(self, client):
        response = await client.get("/api/v1/images")
        assert response.status_code in (401, 403)

    async def test_returns_images_with_counts(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_image_with_findings(session, agent_id)

        response = await client.get("/api/v1/images", headers=auth_header)
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        img = data[0]
        assert img["image_name"] == "nginx"
        assert img["image_tag"] == "latest"
        assert img["total_cves"] == 3
        assert img["fixable_cves"] == 2
        assert img["container_count"] == 1
        assert img["severity_breakdown"]["critical"] == 1
        assert img["severity_breakdown"]["high"] == 1
        assert img["severity_breakdown"]["medium"] == 1

    async def test_fixable_filter(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_image_with_findings(session, agent_id, image_name="fixable-img", fixable=True)
        await _seed_image_with_findings(session, agent_id, image_name="unfixable-img", fixable=False)

        # Without filter: both images
        resp = await client.get("/api/v1/images", headers=auth_header)
        assert resp.json()["total"] == 2

        # With fixable=true: only the fixable image
        resp = await client.get("/api/v1/images?fixable=true", headers=auth_header)
        assert resp.json()["total"] == 1
        assert resp.json()["data"][0]["image_name"] == "fixable-img"

    async def test_sort_by_fixable_cves_desc(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_image_with_findings(session, agent_id, image_name="img-a", fixable=True)
        await _seed_image_with_findings(session, agent_id, image_name="img-b", fixable=False)

        resp = await client.get("/api/v1/images?sort_by=fixable_cves&sort_dir=desc", headers=auth_header)
        data = resp.json()["data"]
        assert data[0]["image_name"] == "img-a"  # More fixable CVEs first

    async def test_sort_by_image_name(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_image_with_findings(session, agent_id, image_name="zulu")
        await _seed_image_with_findings(session, agent_id, image_name="alpha")

        resp = await client.get("/api/v1/images?sort_by=image_name&sort_dir=asc", headers=auth_header)
        data = resp.json()["data"]
        assert data[0]["image_name"] == "alpha"
        assert data[1]["image_name"] == "zulu"

    async def test_pagination(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        for i in range(5):
            await _seed_image_with_findings(session, agent_id, image_name=f"img-{i}")

        resp = await client.get("/api/v1/images?page_size=2&page=1", headers=auth_header)
        assert resp.json()["total"] == 5
        assert len(resp.json()["data"]) == 2

        resp = await client.get("/api/v1/images?page_size=2&page=3", headers=auth_header)
        assert len(resp.json()["data"]) == 1

    async def test_groups_by_image_name_and_tag(self, client, auth_header, session):
        """Different tags of the same image should appear as separate rows."""
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_image_with_findings(session, agent_id, image_name="postgres", image_tag="14", fixable=True)
        await _seed_image_with_findings(session, agent_id, image_name="postgres", image_tag="15", fixable=True)
        await _seed_image_with_findings(session, agent_id, image_name="postgres", image_tag="16", fixable=False)

        resp = await client.get("/api/v1/images", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 3

        tags = {item["image_tag"] for item in data}
        assert tags == {"14", "15", "16"}

        # Each row should have its own CVE counts (not aggregated across tags)
        for item in data:
            assert item["image_name"] == "postgres"
            assert item["total_cves"] == 3
            assert item["container_count"] == 1

    async def test_same_image_tag_across_agents(self, client, auth_header, session):
        """Same image:tag on multiple agents should be one row with both agents listed."""
        resp1 = await client.post("/api/v1/agents", json={"name": "server1"}, headers=auth_header)
        resp2 = await client.post("/api/v1/agents", json={"name": "server2"}, headers=auth_header)
        agent1 = resp1.json()["id"]
        agent2 = resp2.json()["id"]
        await _seed_image_with_findings(session, agent1, image_name="redis", image_tag="7")
        await _seed_image_with_findings(session, agent2, image_name="redis", image_tag="7")

        resp = await client.get("/api/v1/images", headers=auth_header)
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["container_count"] == 2
        agent_names = {a["name"] for a in data[0]["agents"]}
        assert agent_names == {"server1", "server2"}

    async def test_includes_agent_info(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "server1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_image_with_findings(session, agent_id)

        resp = await client.get("/api/v1/images", headers=auth_header)
        agents = resp.json()["data"][0]["agents"]
        assert len(agents) == 1
        assert agents[0]["name"] == "server1"
