"""Tests for the settings endpoint."""

import pytest


class TestGetSettings:
    async def test_returns_defaults(self, client, auth_header):
        response = await client.get("/api/v1/settings", headers=auth_header)
        assert response.status_code == 200
        body = response.json()
        assert body["webhook_url"] is None
        assert body["notify_on_critical"] is True


class TestUpdateSettings:
    async def test_updates_webhook_url(self, client, auth_header):
        response = await client.patch(
            "/api/v1/settings",
            json={"webhook_url": "https://hooks.slack.com/test", "webhook_type": "slack"},
            headers=auth_header,
        )
        assert response.status_code == 200
        assert response.json()["webhook_url"] == "https://hooks.slack.com/test"
        assert response.json()["webhook_type"] == "slack"

    async def test_partial_update_preserves_other_fields(self, client, auth_header):
        # Set initial values
        await client.patch(
            "/api/v1/settings",
            json={"webhook_url": "https://example.com", "notify_on_critical": False},
            headers=auth_header,
        )

        # Update only one field
        response = await client.patch(
            "/api/v1/settings",
            json={"webhook_url": "https://new.com"},
            headers=auth_header,
        )
        body = response.json()
        assert body["webhook_url"] == "https://new.com"
        assert body["notify_on_critical"] is False  # preserved
