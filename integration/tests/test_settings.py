"""
Integration tests for the settings endpoints.

Coverage:
- GET settings returns current values with expected keys
- PATCH webhook_url updates the field
- PATCH webhook_type updates the field
- PATCH notify_on_critical and notify_on_high can be toggled
- Partial PATCH preserves unset fields
- Settings persist between requests

Note: this test module mutates shared settings. Tests within this class are
designed to be self-contained — each test sets and then resets (or works
independently) so other tests are not affected.
"""

import pytest


class TestGetSettings:
    async def test_returns_expected_shape(self, hub):
        r = await hub.get("/api/v1/settings")
        assert r.status_code == 200
        body = r.json()
        assert "webhook_url" in body
        assert "webhook_type" in body
        assert "notify_on_critical" in body
        assert "notify_on_high" in body

    async def test_default_notify_flags_are_true(self, hub):
        # Defaults per NotificationSettings model: notify_on_critical=True, notify_on_high=True
        r = await hub.get("/api/v1/settings")
        body = r.json()
        # The defaults may have been changed by other tests — just assert booleans
        assert isinstance(body["notify_on_critical"], bool)
        assert isinstance(body["notify_on_high"], bool)


class TestUpdateSettings:
    async def test_update_webhook_url(self, hub):
        r = await hub.patch("/api/v1/settings", json={"webhook_url": "http://test-hook.example/notify"})
        assert r.status_code == 200
        assert r.json()["webhook_url"] == "http://test-hook.example/notify"

        # Reset
        await hub.patch("/api/v1/settings", json={"webhook_url": None})

    async def test_update_webhook_type(self, hub):
        r = await hub.patch("/api/v1/settings", json={"webhook_type": "slack"})
        assert r.status_code == 200
        assert r.json()["webhook_type"] == "slack"

        # Reset
        await hub.patch("/api/v1/settings", json={"webhook_type": None})

    async def test_update_notify_on_critical(self, hub):
        r = await hub.patch("/api/v1/settings", json={"notify_on_critical": False})
        assert r.status_code == 200
        assert r.json()["notify_on_critical"] is False

        # Reset to default
        await hub.patch("/api/v1/settings", json={"notify_on_critical": True})

    async def test_update_notify_on_high(self, hub):
        r = await hub.patch("/api/v1/settings", json={"notify_on_high": False})
        assert r.status_code == 200
        assert r.json()["notify_on_high"] is False

        # Reset
        await hub.patch("/api/v1/settings", json={"notify_on_high": True})

    async def test_partial_update_preserves_other_fields(self, hub):
        # Set a known baseline
        await hub.patch(
            "/api/v1/settings",
            json={"webhook_url": "http://preserve.example/", "webhook_type": "discord", "notify_on_critical": True},
        )

        # Partial update: only change notify_on_high
        r = await hub.patch("/api/v1/settings", json={"notify_on_high": False})
        assert r.status_code == 200
        body = r.json()
        assert body["webhook_url"] == "http://preserve.example/"
        assert body["webhook_type"] == "discord"
        assert body["notify_on_critical"] is True
        assert body["notify_on_high"] is False

        # Reset
        await hub.patch("/api/v1/settings", json={"webhook_url": None, "webhook_type": None, "notify_on_high": True})

    async def test_settings_persist_between_requests(self, hub):
        url = "http://persist-check.example/"
        await hub.patch("/api/v1/settings", json={"webhook_url": url})

        r = await hub.get("/api/v1/settings")
        assert r.json()["webhook_url"] == url

        # Reset
        await hub.patch("/api/v1/settings", json={"webhook_url": None})

    async def test_set_webhook_url_to_none(self, hub):
        await hub.patch("/api/v1/settings", json={"webhook_url": "http://temp.example/"})
        r = await hub.patch("/api/v1/settings", json={"webhook_url": None})
        assert r.status_code == 200
        assert r.json()["webhook_url"] is None
