"""Tests for misconfiguration API endpoints."""

from sqlalchemy.ext.asyncio import AsyncSession
from trivyal_hub.db.models import Container, MisconfigFinding, Severity


async def _seed_misconfig(session: AsyncSession, agent_id: str) -> MisconfigFinding:
    """Create a container and misconfig finding for testing."""
    container = Container(agent_id=agent_id, image_name="linuxserver/plex", image_tag="latest")
    session.add(container)
    await session.flush()

    finding = MisconfigFinding(
        container_id=container.id,
        check_id="PRIV_001",
        severity=Severity.HIGH,
        title="Container running in privileged mode",
        fix_guideline="Remove 'privileged: true' from the container definition.",
    )
    session.add(finding)
    await session.commit()
    await session.refresh(finding)
    return finding


async def _seed_multiple_misconfigs(session: AsyncSession, agent_id: str) -> list[MisconfigFinding]:
    """Create multiple misconfig findings with different severities."""
    container = Container(agent_id=agent_id, image_name="linuxserver/sonarr", container_name="sonarr")
    session.add(container)
    await session.flush()

    findings = []
    for check_id, sev, title in [
        ("PRIV_001", Severity.HIGH, "Privileged mode"),
        ("CAP_001", Severity.HIGH, "Dangerous capabilities"),
        ("NET_001", Severity.MEDIUM, "Host network mode"),
        ("PRIV_002", Severity.MEDIUM, "Missing no-new-privileges"),
    ]:
        f = MisconfigFinding(
            container_id=container.id,
            check_id=check_id,
            severity=sev,
            title=title,
            fix_guideline=f"Fix {check_id}",
        )
        session.add(f)
        findings.append(f)

    await session.commit()
    for f in findings:
        await session.refresh(f)
    return findings


class TestListMisconfigs:
    async def test_returns_empty_list(self, client, auth_header):
        response = await client.get("/api/v1/misconfigs", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_requires_auth(self, client):
        response = await client.get("/api/v1/misconfigs")
        assert response.status_code in (401, 403)

    async def test_returns_seeded_misconfigs(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_misconfig(session, agent_id)

        response = await client.get("/api/v1/misconfigs", headers=auth_header)
        assert response.json()["total"] == 1
        data = response.json()["data"][0]
        assert data["check_id"] == "PRIV_001"
        assert data["severity"] == "HIGH"
        assert data["image_name"] == "linuxserver/plex"

    async def test_filter_by_severity(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_multiple_misconfigs(session, agent_id)

        response = await client.get("/api/v1/misconfigs?severity=HIGH", headers=auth_header)
        assert response.json()["total"] == 2

        response = await client.get("/api/v1/misconfigs?severity=MEDIUM", headers=auth_header)
        assert response.json()["total"] == 2

    async def test_filter_by_status(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_misconfig(session, agent_id)

        response = await client.get("/api/v1/misconfigs?status=active", headers=auth_header)
        assert response.json()["total"] == 1

        response = await client.get("/api/v1/misconfigs?status=fixed", headers=auth_header)
        assert response.json()["total"] == 0

    async def test_filter_by_agent_id(self, client, auth_header, session):
        resp1 = await client.post("/api/v1/agents", json={"name": "a1"}, headers=auth_header)
        resp2 = await client.post("/api/v1/agents", json={"name": "a2"}, headers=auth_header)
        agent1 = resp1.json()["id"]
        agent2 = resp2.json()["id"]
        await _seed_misconfig(session, agent1)

        response = await client.get(f"/api/v1/misconfigs?agent_id={agent1}", headers=auth_header)
        assert response.json()["total"] == 1

        response = await client.get(f"/api/v1/misconfigs?agent_id={agent2}", headers=auth_header)
        assert response.json()["total"] == 0

    async def test_filter_by_container_id(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        finding = await _seed_misconfig(session, agent_id)

        response = await client.get(f"/api/v1/misconfigs?container_id={finding.container_id}", headers=auth_header)
        assert response.json()["total"] == 1

        response = await client.get("/api/v1/misconfigs?container_id=bad-id", headers=auth_header)
        assert response.json()["total"] == 0

    async def test_filter_by_check_id(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        await _seed_multiple_misconfigs(session, agent_id)

        response = await client.get("/api/v1/misconfigs?check_id=PRIV_001", headers=auth_header)
        assert response.json()["total"] == 1


class TestGetMisconfig:
    async def test_returns_404_for_unknown(self, client, auth_header):
        response = await client.get("/api/v1/misconfigs/bad-id", headers=auth_header)
        assert response.status_code == 404

    async def test_returns_finding(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        finding = await _seed_misconfig(session, agent_id)

        response = await client.get(f"/api/v1/misconfigs/{finding.id}", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["check_id"] == "PRIV_001"


class TestUpdateMisconfig:
    async def test_updates_status(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        finding = await _seed_misconfig(session, agent_id)

        response = await client.patch(
            f"/api/v1/misconfigs/{finding.id}",
            json={"status": "false_positive"},
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "false_positive"

    async def test_returns_404_for_unknown(self, client, auth_header):
        response = await client.patch(
            "/api/v1/misconfigs/bad-id",
            json={"status": "accepted"},
            headers=auth_header,
        )
        assert response.status_code == 404


class TestMisconfigAcceptance:
    async def test_create_and_revoke(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        finding = await _seed_misconfig(session, agent_id)

        # Create acceptance
        resp = await client.post(
            f"/api/v1/misconfigs/{finding.id}/acceptances",
            json={"reason": "Required for GPU passthrough"},
            headers=auth_header,
        )
        assert resp.status_code == 201
        acceptance_id = resp.json()["id"]

        # Verify finding status changed
        f_resp = await client.get(f"/api/v1/misconfigs/{finding.id}", headers=auth_header)
        assert f_resp.json()["status"] == "accepted"

        # Revoke acceptance
        del_resp = await client.delete(
            f"/api/v1/misconfigs/{finding.id}/acceptances/{acceptance_id}",
            headers=auth_header,
        )
        assert del_resp.status_code == 204

        # Verify finding status reverted
        f_resp2 = await client.get(f"/api/v1/misconfigs/{finding.id}", headers=auth_header)
        assert f_resp2.json()["status"] == "active"

    async def test_returns_404_for_unknown_finding(self, client, auth_header):
        resp = await client.post(
            "/api/v1/misconfigs/bad-id/acceptances",
            json={"reason": "test"},
            headers=auth_header,
        )
        assert resp.status_code == 404

    async def test_revoke_unknown_acceptance_returns_404(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]
        finding = await _seed_misconfig(session, agent_id)

        resp = await client.delete(
            f"/api/v1/misconfigs/{finding.id}/acceptances/bad-id",
            headers=auth_header,
        )
        assert resp.status_code == 404
