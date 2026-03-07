"""Tests for fixable filter on findings, dashboard, and insights endpoints."""

from trivyal_hub.db.models import Container, Finding, MisconfigFinding, ScanResult, Severity


async def _seed_findings_with_fixable(session, agent_id):
    """Create findings with and without fixed_version."""
    container = Container(agent_id=agent_id, image_name="nginx", image_tag="latest")
    session.add(container)
    await session.flush()

    scan = ScanResult(container_id=container.id, agent_id=agent_id)
    session.add(scan)
    await session.flush()

    # Fixable finding (has fixed_version)
    fixable = Finding(
        scan_result_id=scan.id,
        cve_id="CVE-2024-0001",
        package_name="libssl",
        installed_version="1.0",
        fixed_version="1.1",
        severity=Severity.CRITICAL,
    )
    session.add(fixable)

    # Unfixable finding (no fixed_version)
    unfixable = Finding(
        scan_result_id=scan.id,
        cve_id="CVE-2024-0002",
        package_name="zlib",
        installed_version="1.2",
        fixed_version=None,
        severity=Severity.HIGH,
    )
    session.add(unfixable)

    # Empty string fixed_version (should be treated as unfixable)
    empty_fix = Finding(
        scan_result_id=scan.id,
        cve_id="CVE-2024-0003",
        package_name="curl",
        installed_version="7.0",
        fixed_version="",
        severity=Severity.MEDIUM,
    )
    session.add(empty_fix)

    await session.commit()
    return container


class TestFindingsFixableFilter:
    async def test_without_filter_returns_all(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/findings", headers=auth_header)
        assert resp.json()["total"] == 3

    async def test_fixable_filter_returns_only_fixable(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/findings?fixable=true", headers=auth_header)
        assert resp.json()["total"] == 1
        assert resp.json()["data"][0]["cve_id"] == "CVE-2024-0001"

    async def test_fixable_with_image_name_filter(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/findings?fixable=true&image_name=nginx", headers=auth_header)
        assert resp.json()["total"] == 1

        resp = await client.get("/api/v1/findings?fixable=true&image_name=nonexistent", headers=auth_header)
        assert resp.json()["total"] == 0


class TestDashboardFixableFilter:
    async def test_summary_includes_fixable_cves_and_misconfig(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/dashboard/summary", headers=auth_header)
        body = resp.json()
        assert body["fixable_cves"] == 1
        assert "misconfig" in body
        assert body["misconfig"]["total_active"] == 0
        assert body["total_findings"] == 3

    async def test_fixable_toggle_scopes_severity_counts(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/dashboard/summary?fixable=true", headers=auth_header)
        body = resp.json()
        # Only 1 fixable finding (CRITICAL)
        assert body["severity_counts"]["critical"] == 1
        assert body["severity_counts"]["high"] == 0
        assert body["severity_counts"]["medium"] == 0
        assert body["total_findings"] == 1
        # fixable_cves is always unscoped
        assert body["fixable_cves"] == 1

    async def test_misconfig_counts_in_summary(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        container = Container(agent_id=agent_id, image_name="plex")
        session.add(container)
        await session.flush()
        for check_id, sev in [("PRIV_001", Severity.HIGH), ("NET_001", Severity.MEDIUM)]:
            session.add(
                MisconfigFinding(
                    container_id=container.id,
                    check_id=check_id,
                    severity=sev,
                    title=f"Test {check_id}",
                    fix_guideline="Fix it",
                )
            )
        await session.commit()

        resp = await client.get("/api/v1/dashboard/summary", headers=auth_header)
        misconfig = resp.json()["misconfig"]
        assert misconfig["high"] == 1
        assert misconfig["medium"] == 1
        assert misconfig["total_active"] == 2


class TestInsightsFixableFilter:
    async def test_summary_with_fixable(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/insights/summary?fixable=true", headers=auth_header)
        assert resp.status_code == 200
        body = resp.json()
        assert body["active_findings"] == 1

    async def test_trend_with_fixable(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/insights/trend?fixable=true&window=7", headers=auth_header)
        assert resp.status_code == 200

    async def test_agents_trend_with_fixable(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/insights/agents/trend?fixable=true&window=7", headers=auth_header)
        assert resp.status_code == 200

    async def test_top_cves_with_fixable(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_findings_with_fixable(session, agent_id)

        resp = await client.get("/api/v1/insights/top-cves?fixable=true&window=30", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        # Only fixable CVEs should appear
        cve_ids = [c["cve_id"] for c in data]
        assert "CVE-2024-0001" in cve_ids
        assert "CVE-2024-0002" not in cve_ids
