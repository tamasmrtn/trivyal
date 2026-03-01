"""Tests for the health endpoint."""


class TestHealth:
    async def test_returns_ok(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
