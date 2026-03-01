"""Tests for the auth endpoint."""

from trivyal_hub.config import settings
from trivyal_hub.core.auth import generate_admin_token


class TestLogin:
    async def test_valid_credentials_return_token(self, client):
        response = await client.post(
            "/api/v1/auth/token",
            json={
                "username": "admin",
                "password": settings.admin_password.get_secret_value(),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"] == generate_admin_token(settings.secret_key.get_secret_value())

    async def test_wrong_password_returns_401(self, client):
        response = await client.post(
            "/api/v1/auth/token",
            json={
                "username": "admin",
                "password": "wrong",
            },
        )
        assert response.status_code == 401

    async def test_wrong_username_returns_401(self, client):
        response = await client.post(
            "/api/v1/auth/token",
            json={
                "username": "nobody",
                "password": settings.admin_password.get_secret_value(),
            },
        )
        assert response.status_code == 401
