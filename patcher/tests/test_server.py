"""Tests for the patcher HTTP server."""

import json
from unittest.mock import patch

import pytest
from trivyal_patcher.server import create_app


@pytest.fixture
def client(aiohttp_client):
    app = create_app()
    return aiohttp_client(app)


class TestHealth:
    async def test_returns_ok(self, client):
        c = await client
        resp = await c.get("/health")
        assert resp.status == 200
        body = await resp.json()
        assert body["status"] == "ok"


class TestPatchEndpoint:
    async def test_returns_400_without_required_fields(self, client):
        c = await client
        resp = await c.post("/patch", json={"image": "nginx"})
        assert resp.status == 400

    async def test_streams_ndjson_events(self, client):
        async def mock_copa(image, report, tag):
            yield {"type": "log", "line": "Patching..."}
            yield {"type": "result", "status": "completed", "patched_tag": tag}

        c = await client
        with patch("trivyal_patcher.server.run_copa", mock_copa):
            resp = await c.post(
                "/patch",
                json={"image": "nginx:1.25", "trivy_report": {"Results": []}, "patched_tag": "nginx:1.25-patched"},
            )

        assert resp.status == 200
        text = await resp.text()
        lines = [json.loads(l) for l in text.strip().split("\n")]
        assert lines[0]["type"] == "log"
        assert lines[1]["type"] == "result"
        assert lines[1]["status"] == "completed"


class TestRestartEndpoint:
    async def test_returns_400_without_required_fields(self, client):
        c = await client
        resp = await c.post("/restart", json={"container_id": "abc"})
        assert resp.status == 400

    async def test_successful_restart(self, client):
        c = await client
        with patch(
            "trivyal_patcher.server.restart_container",
            return_value={"status": "completed", "new_container_id": "new-123"},
        ):
            resp = await c.post(
                "/restart",
                json={"container_id": "old-123", "image": "nginx:patched"},
            )

        assert resp.status == 200
        body = await resp.json()
        assert body["status"] == "completed"
