"""Tests for insights analytics endpoints."""

from datetime import UTC, datetime, timedelta

from trivyal_hub.db.models import Container, Finding, FindingStatus, ScanResult, Severity


def _agent_id(client_fixture):
    """Helper: returns a create-agent coroutine result for reuse."""
    return None  # used inline below


def _make_finding(scan_id, cve_id, severity, status=FindingStatus.ACTIVE, days_ago=0):
    ts = datetime.now(UTC) - timedelta(days=days_ago)
    return Finding(
        scan_result_id=scan_id,
        cve_id=cve_id,
        package_name="pkg",
        installed_version="1.0",
        severity=severity,
        status=status,
        first_seen=ts,
        last_seen=ts,
    )


class TestInsightsSummary:
    async def test_empty_db(self, client, auth_header):
        r = await client.get("/api/v1/insights/summary", headers=auth_header)
        assert r.status_code == 200
        body = r.json()
        assert body["active_findings"] == 0
        assert body["critical_high"] == 0
        assert body["new_in_period"] == 0
        assert body["fix_rate"] == 0.0

    async def test_counts_active_findings(self, client, auth_header, session):
        reg = await client.post("/api/v1/agents", json={"name": "a1"}, headers=auth_header)
        agent_id = reg.json()["id"]

        container = Container(agent_id=agent_id, image_name="img:latest")
        session.add(container)
        await session.flush()
        scan = ScanResult(container_id=container.id, agent_id=agent_id)
        session.add(scan)
        await session.flush()

        session.add(_make_finding(scan.id, "CVE-2024-0001", Severity.CRITICAL))
        session.add(_make_finding(scan.id, "CVE-2024-0002", Severity.HIGH))
        session.add(_make_finding(scan.id, "CVE-2024-0003", Severity.MEDIUM))
        await session.commit()

        r = await client.get("/api/v1/insights/summary", headers=auth_header)
        body = r.json()
        assert body["active_findings"] == 3
        assert body["critical_high"] == 2
        assert body["new_in_period"] == 3

    async def test_fix_rate(self, client, auth_header, session):
        reg = await client.post("/api/v1/agents", json={"name": "a2"}, headers=auth_header)
        agent_id = reg.json()["id"]
        container = Container(agent_id=agent_id, image_name="img:latest")
        session.add(container)
        await session.flush()
        scan = ScanResult(container_id=container.id, agent_id=agent_id)
        session.add(scan)
        await session.flush()

        # 1 active, 1 fixed — fix rate should be 50%
        session.add(_make_finding(scan.id, "CVE-A", Severity.HIGH))
        session.add(_make_finding(scan.id, "CVE-B", Severity.HIGH, status=FindingStatus.FIXED))
        await session.commit()

        r = await client.get("/api/v1/insights/summary", headers=auth_header)
        body = r.json()
        assert body["fix_rate"] == 50.0


class TestInsightsTrend:
    async def test_empty_db(self, client, auth_header):
        r = await client.get("/api/v1/insights/trend?window=7", headers=auth_header)
        assert r.status_code == 200
        body = r.json()
        assert len(body["days"]) == 8  # 7 days + today
        assert body["scan_events"] == []
        assert body["days"][0]["critical"] == 0

    async def test_finding_appears_in_trend(self, client, auth_header, session):
        reg = await client.post("/api/v1/agents", json={"name": "a3"}, headers=auth_header)
        agent_id = reg.json()["id"]
        container = Container(agent_id=agent_id, image_name="img:latest")
        session.add(container)
        await session.flush()
        scan = ScanResult(container_id=container.id, agent_id=agent_id)
        session.add(scan)
        await session.flush()

        session.add(_make_finding(scan.id, "CVE-2024-0001", Severity.CRITICAL))
        await session.commit()

        r = await client.get("/api/v1/insights/trend?window=7", headers=auth_header)
        body = r.json()
        # Today's entry should have 1 critical
        today_entry = body["days"][-1]
        assert today_entry["critical"] == 1

    async def test_scan_events_included(self, client, auth_header, session):
        reg = await client.post("/api/v1/agents", json={"name": "a4"}, headers=auth_header)
        agent_id = reg.json()["id"]
        container = Container(agent_id=agent_id, image_name="img:latest")
        session.add(container)
        await session.flush()
        scan = ScanResult(container_id=container.id, agent_id=agent_id)
        session.add(scan)
        await session.commit()

        r = await client.get("/api/v1/insights/trend?window=7", headers=auth_header)
        body = r.json()
        assert len(body["scan_events"]) == 1


class TestInsightsAgentsTrend:
    async def test_empty_db(self, client, auth_header):
        r = await client.get("/api/v1/insights/agents/trend?window=7", headers=auth_header)
        assert r.status_code == 200
        body = r.json()
        assert body["agents"] == []
        assert body["scan_events"] == []

    async def test_agent_trend(self, client, auth_header, session):
        reg = await client.post("/api/v1/agents", json={"name": "a5"}, headers=auth_header)
        agent_id = reg.json()["id"]
        container = Container(agent_id=agent_id, image_name="img:latest")
        session.add(container)
        await session.flush()
        scan = ScanResult(container_id=container.id, agent_id=agent_id)
        session.add(scan)
        await session.flush()

        session.add(_make_finding(scan.id, "CVE-2024-0001", Severity.HIGH))
        await session.commit()

        r = await client.get("/api/v1/insights/agents/trend?window=7", headers=auth_header)
        body = r.json()
        assert len(body["agents"]) == 1
        assert body["agents"][0]["name"] == "a5"
        today_point = body["agents"][0]["days"][-1]
        assert today_point["total"] == 1


class TestInsightsTopCves:
    async def test_empty_db(self, client, auth_header):
        r = await client.get("/api/v1/insights/top-cves", headers=auth_header)
        assert r.status_code == 200
        assert r.json() == []

    async def test_returns_top_cves(self, client, auth_header, session):
        reg = await client.post("/api/v1/agents", json={"name": "a6"}, headers=auth_header)
        agent_id = reg.json()["id"]

        # Two containers with the same CVE
        c1 = Container(agent_id=agent_id, image_name="img1:latest")
        c2 = Container(agent_id=agent_id, image_name="img2:latest")
        session.add(c1)
        session.add(c2)
        await session.flush()

        s1 = ScanResult(container_id=c1.id, agent_id=agent_id)
        s2 = ScanResult(container_id=c2.id, agent_id=agent_id)
        session.add(s1)
        session.add(s2)
        await session.flush()

        session.add(_make_finding(s1.id, "CVE-WIDE", Severity.CRITICAL))
        session.add(_make_finding(s2.id, "CVE-WIDE", Severity.CRITICAL))
        session.add(_make_finding(s1.id, "CVE-NARROW", Severity.HIGH))
        await session.commit()

        r = await client.get("/api/v1/insights/top-cves", headers=auth_header)
        body = r.json()
        assert len(body) == 2
        # CVE-WIDE affects 2 containers, should be first
        assert body[0]["cve_id"] == "CVE-WIDE"
        assert body[0]["containers"] == 2
        assert body[0]["agents"] == 1
