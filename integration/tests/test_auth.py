"""
Integration tests for authentication.

Coverage:
- Valid login returns access_token
- Wrong password returns 401
- Wrong username returns 401
- Unauthenticated requests to /api/v1/* return 401
- /api/health is accessible without auth
"""

import pytest


class TestHealth:
    async def test_health_requires_no_auth(self, hub_anon):
        r = await hub_anon.get("/api/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestLogin:
    async def test_valid_credentials_return_token(self, hub_base_url):
        import httpx

        async with httpx.AsyncClient(base_url=hub_base_url) as c:
            r = await c.post(
                "/api/v1/auth/token",
                json={"username": "admin", "password": "testpassword"},
            )
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 0

    async def test_wrong_password_returns_401(self, hub_base_url):
        import httpx

        async with httpx.AsyncClient(base_url=hub_base_url) as c:
            r = await c.post(
                "/api/v1/auth/token",
                json={"username": "admin", "password": "wrongpassword"},
            )
        assert r.status_code == 401

    async def test_wrong_username_returns_401(self, hub_base_url):
        import httpx

        async with httpx.AsyncClient(base_url=hub_base_url) as c:
            r = await c.post(
                "/api/v1/auth/token",
                json={"username": "notadmin", "password": "testpassword"},
            )
        assert r.status_code == 401


class TestAuthEnforcement:
    async def test_agents_endpoint_requires_auth(self, hub_anon):
        r = await hub_anon.get("/api/v1/agents")
        assert r.status_code == 401

    async def test_findings_endpoint_requires_auth(self, hub_anon):
        r = await hub_anon.get("/api/v1/findings")
        assert r.status_code == 401

    async def test_scans_endpoint_requires_auth(self, hub_anon):
        r = await hub_anon.get("/api/v1/scans")
        assert r.status_code == 401

    async def test_dashboard_endpoint_requires_auth(self, hub_anon):
        r = await hub_anon.get("/api/v1/dashboard/summary")
        assert r.status_code == 401

    async def test_settings_endpoint_requires_auth(self, hub_anon):
        r = await hub_anon.get("/api/v1/settings")
        assert r.status_code == 401

    async def test_invalid_token_returns_401(self, hub_base_url):
        import httpx

        async with httpx.AsyncClient(
            base_url=hub_base_url,
            headers={"Authorization": "Bearer not-a-real-token"},
        ) as c:
            r = await c.get("/api/v1/agents")
        assert r.status_code == 401
