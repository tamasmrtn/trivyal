"""Tests for agent CRUD endpoints."""


class TestListAgents:
    async def test_returns_empty_list_when_no_agents(self, client, auth_header):
        response = await client.get("/api/v1/agents", headers=auth_header)
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []
        assert body["total"] == 0

    async def test_requires_auth(self, client):
        response = await client.get("/api/v1/agents")
        assert response.status_code in (401, 403)

    async def test_returns_registered_agents(self, client, auth_header):
        await client.post("/api/v1/agents", json={"name": "server-1"}, headers=auth_header)
        response = await client.get("/api/v1/agents", headers=auth_header)
        assert len(response.json()["data"]) == 1


class TestRegisterAgent:
    async def test_creates_agent_and_returns_token(self, client, auth_header):
        response = await client.post("/api/v1/agents", json={"name": "server-1"}, headers=auth_header)
        assert response.status_code == 201
        body = response.json()
        assert "token" in body
        assert "hub_public_key" in body
        assert body["name"] == "server-1"

    async def test_rejects_duplicate_name(self, client, auth_header):
        payload = {"name": "server-1"}
        await client.post("/api/v1/agents", json=payload, headers=auth_header)
        response = await client.post("/api/v1/agents", json=payload, headers=auth_header)
        assert response.status_code == 409


class TestGetAgent:
    async def test_returns_agent_detail(self, client, auth_header):
        create_resp = await client.post("/api/v1/agents", json={"name": "server-1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/agents/{agent_id}", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["name"] == "server-1"

    async def test_returns_404_for_unknown_id(self, client, auth_header):
        response = await client.get("/api/v1/agents/nonexistent", headers=auth_header)
        assert response.status_code == 404


class TestDeleteAgent:
    async def test_removes_agent(self, client, auth_header):
        create_resp = await client.post("/api/v1/agents", json={"name": "server-1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/agents/{agent_id}", headers=auth_header)
        assert response.status_code == 204

        list_resp = await client.get("/api/v1/agents", headers=auth_header)
        assert list_resp.json()["total"] == 0

    async def test_returns_404_for_unknown_id(self, client, auth_header):
        response = await client.delete("/api/v1/agents/nonexistent", headers=auth_header)
        assert response.status_code == 404
