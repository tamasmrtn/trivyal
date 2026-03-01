"""Tests for scan endpoints."""


class TestTriggerScan:
    async def test_returns_202_with_job_id(self, client, auth_header):
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        response = await client.post(f"/api/v1/agents/{agent_id}/scans", headers=auth_header)
        assert response.status_code == 202
        assert "job_id" in response.json()

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
