"""Tests for finding and risk acceptance endpoints."""

from sqlalchemy.ext.asyncio import AsyncSession
from trivyal_hub.db.models import Container, Finding, ScanResult, Severity


async def _seed_finding(session: AsyncSession, agent_id: str) -> Finding:
    """Create a container, scan result, and finding for testing."""
    container = Container(agent_id=agent_id, image_name="test:latest")
    session.add(container)
    await session.flush()

    scan = ScanResult(container_id=container.id, agent_id=agent_id)
    session.add(scan)
    await session.flush()

    finding = Finding(
        scan_result_id=scan.id,
        cve_id="CVE-2024-0001",
        package_name="openssl",
        installed_version="1.1.1",
        fixed_version="1.1.2",
        severity=Severity.CRITICAL,
    )
    session.add(finding)
    await session.commit()
    await session.refresh(finding)
    return finding


class TestListFindings:
    async def test_returns_empty_list(self, client, auth_header):
        response = await client.get("/api/v1/findings", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_requires_auth(self, client):
        response = await client.get("/api/v1/findings")
        assert response.status_code in (401, 403)

    async def test_returns_seeded_findings(self, client, auth_header, session):
        # Create agent first
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_finding(session, agent_id)

        response = await client.get("/api/v1/findings", headers=auth_header)
        assert response.json()["total"] == 1

    async def test_filter_by_severity(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_finding(session, agent_id)

        response = await client.get("/api/v1/findings?severity=CRITICAL", headers=auth_header)
        assert response.json()["total"] == 1

        response = await client.get("/api/v1/findings?severity=LOW", headers=auth_header)
        assert response.json()["total"] == 0


class TestGetFinding:
    async def test_returns_404_for_unknown(self, client, auth_header):
        response = await client.get("/api/v1/findings/bad-id", headers=auth_header)
        assert response.status_code == 404


class TestUpdateFinding:
    async def test_updates_status(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        finding = await _seed_finding(session, agent_id)

        response = await client.patch(
            f"/api/v1/findings/{finding.id}",
            json={"status": "false_positive"},
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "false_positive"


class TestRiskAcceptance:
    async def test_create_and_revoke(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        finding = await _seed_finding(session, agent_id)

        # Create acceptance
        resp = await client.post(
            f"/api/v1/findings/{finding.id}/acceptances",
            json={"reason": "Risk accepted for testing"},
            headers=auth_header,
        )
        assert resp.status_code == 201
        acceptance_id = resp.json()["id"]

        # Verify finding status changed
        f_resp = await client.get(f"/api/v1/findings/{finding.id}", headers=auth_header)
        assert f_resp.json()["status"] == "accepted"

        # Revoke acceptance
        del_resp = await client.delete(
            f"/api/v1/findings/{finding.id}/acceptances/{acceptance_id}",
            headers=auth_header,
        )
        assert del_resp.status_code == 204

        # Verify finding status reverted
        f_resp2 = await client.get(f"/api/v1/findings/{finding.id}", headers=auth_header)
        assert f_resp2.json()["status"] == "active"
