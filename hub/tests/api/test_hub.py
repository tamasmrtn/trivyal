"""Tests for hub-level endpoints."""


class TestGetPublicKey:
    async def test_returns_public_key(self, client, auth_header):
        response = await client.get("/api/v1/hub/public-key", headers=auth_header)
        assert response.status_code == 200
        body = response.json()
        assert "public_key" in body
        assert len(body["public_key"]) > 0

    async def test_public_key_is_stable_across_calls(self, client, auth_header):
        r1 = await client.get("/api/v1/hub/public-key", headers=auth_header)
        r2 = await client.get("/api/v1/hub/public-key", headers=auth_header)
        assert r1.json()["public_key"] == r2.json()["public_key"]

    async def test_public_key_matches_registration_response(self, client, auth_header):
        hub_resp = await client.get("/api/v1/hub/public-key", headers=auth_header)
        reg_resp = await client.post("/api/v1/agents", json={"name": "server-1"}, headers=auth_header)
        assert hub_resp.json()["public_key"] == reg_resp.json()["hub_public_key"]

    async def test_requires_auth(self, client):
        response = await client.get("/api/v1/hub/public-key")
        assert response.status_code in (401, 403)
