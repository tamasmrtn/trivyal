"""Tests for scan endpoints."""

from unittest.mock import AsyncMock, patch

from trivyal_hub.db.models import Container, ScanResult


class TestTriggerScan:
    async def test_returns_202_with_job_id_when_agent_connected(self, client, auth_header):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        with patch("trivyal_hub.api.v1.scans.manager.send_scan_trigger", new=AsyncMock(return_value=True)):
            response = await client.post(f"/api/v1/agents/{agent_id}/scans", headers=auth_header)

        assert response.status_code == 202
        assert "job_id" in response.json()

    async def test_returns_409_when_agent_not_connected(self, client, auth_header):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        with patch("trivyal_hub.api.v1.scans.manager.send_scan_trigger", new=AsyncMock(return_value=False)):
            response = await client.post(f"/api/v1/agents/{agent_id}/scans", headers=auth_header)

        assert response.status_code == 409

    async def test_returns_404_for_unknown_agent(self, client, auth_header):
        response = await client.post("/api/v1/agents/bad-id/scans", headers=auth_header)
        assert response.status_code == 404


class TestListAgentScans:
    async def test_returns_empty_list(self, client, auth_header):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/agents/{agent_id}/scans", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_returns_404_for_unknown_agent(self, client, auth_header):
        response = await client.get("/api/v1/agents/bad-id/scans", headers=auth_header)
        assert response.status_code == 404


class TestListAllScans:
    async def test_returns_empty_list(self, client, auth_header):
        response = await client.get("/api/v1/scans", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["data"] == []


class TestGetScan:
    async def test_returns_404_for_unknown_scan(self, client, auth_header):
        response = await client.get("/api/v1/scans/bad-id", headers=auth_header)
        assert response.status_code == 404

    async def test_returns_scan_detail(self, client, auth_header, session):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        container = Container(agent_id=agent_id, image_name="nginx:latest")
        session.add(container)
        await session.flush()

        scan = ScanResult(
            container_id=container.id,
            agent_id=agent_id,
            critical_count=1,
            high_count=2,
            trivy_raw={"Results": []},
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)

        response = await client.get(f"/api/v1/scans/{scan.id}", headers=auth_header)
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == scan.id
        assert body["agent_id"] == agent_id
        assert body["critical_count"] == 1
        assert body["high_count"] == 2
        assert body["trivy_raw"] == {"Results": []}
