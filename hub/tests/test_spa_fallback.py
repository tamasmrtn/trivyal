"""Tests for SPA fallback routing."""

import pytest
from httpx import ASGITransport, AsyncClient
from trivyal_hub.main import SPAStaticFiles, app


@pytest.fixture
def spa_app(tmp_path):
    """Mount SPAStaticFiles with a temp dir containing index.html and a real asset."""
    (tmp_path / "index.html").write_text("<!doctype html><title>Trivyal</title>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('ok')")

    # Replace any existing UI mount, then restore after the test
    original_routes = list(app.routes)
    app.mount("/", SPAStaticFiles(directory=tmp_path, html=True), name="ui")
    yield app
    app.routes.clear()
    app.routes.extend(original_routes)


@pytest.fixture
async def spa_client(spa_app):
    async with AsyncClient(
        transport=ASGITransport(app=spa_app),
        base_url="http://test",
    ) as c:
        yield c


class TestSPAFallback:
    async def test_root_serves_index(self, spa_client):
        resp = await spa_client.get("/")
        assert resp.status_code == 200
        assert "Trivyal" in resp.text

    async def test_spa_route_serves_index(self, spa_client):
        resp = await spa_client.get("/priorities")
        assert resp.status_code == 200
        assert "Trivyal" in resp.text

    async def test_nested_spa_route_serves_index(self, spa_client):
        resp = await spa_client.get("/findings/abc-123")
        assert resp.status_code == 200
        assert "Trivyal" in resp.text

    async def test_real_asset_served_directly(self, spa_client):
        resp = await spa_client.get("/assets/app.js")
        assert resp.status_code == 200
        assert "console.log" in resp.text

    async def test_api_routes_not_affected(self, spa_client):
        resp = await spa_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
