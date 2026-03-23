"""Session-scoped fixtures for integration tests.

The hub is started via pytest-docker (docker-compose.test.yml) and is shared
across the entire test session. Each test that registers an agent uses the
`registered_agent` fixture, which deletes the agent (and all cascade data) on
teardown — ensuring full isolation between tests.
"""

import hashlib
from pathlib import Path

import httpx
import pytest
import requests


# ── Integration test secret — must match docker-compose.test.yml ─────────────

_SECRET_KEY = "integration-test-secret-key-32x!"
_ADMIN_PASSWORD = "testpassword"
_HUB_PORT = 18099


# ── Docker fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def docker_compose_file():
    """Point pytest-docker at our test compose file (relative to this conftest)."""
    return [str(Path(__file__).parent / "docker-compose.test.yml")]


@pytest.fixture(scope="session")
def docker_compose_project_name():
    return "trivyal-integration"


def _is_hub_healthy(url: str) -> bool:
    try:
        return requests.get(url, timeout=2).status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def hub_base_url(docker_ip, docker_services):
    """Block until the hub /api/health returns 200, then return the base URL."""
    port = docker_services.port_for("hub", 8099)
    url = f"http://{docker_ip}:{port}"
    docker_services.wait_until_responsive(
        timeout=120.0,
        pause=2.0,
        check=lambda: _is_hub_healthy(f"{url}/api/health"),
    )
    return url


# ── Auth ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def auth_token():
    """Derive the admin token directly from the known secret key (no HTTP needed)."""
    return hashlib.sha256(f"admin:{_SECRET_KEY}".encode()).hexdigest()


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ── HTTP client ───────────────────────────────────────────────────────────────


@pytest.fixture
async def hub(hub_base_url, auth_headers):
    """Authenticated async HTTPX client pointed at the real hub."""
    async with httpx.AsyncClient(base_url=hub_base_url, headers=auth_headers) as client:
        yield client


@pytest.fixture
async def hub_anon(hub_base_url):
    """Unauthenticated async HTTPX client (for testing auth enforcement)."""
    async with httpx.AsyncClient(base_url=hub_base_url) as client:
        yield client


# ── Agent helpers ─────────────────────────────────────────────────────────────


@pytest.fixture
async def registered_agent(hub):
    """Register a uniquely-named agent; delete it (and all cascade data) on teardown."""
    import uuid

    name = f"test-{uuid.uuid4().hex[:8]}"
    resp = await hub.post("/api/v1/agents", json={"name": name})
    resp.raise_for_status()
    body = resp.json()
    yield body
    # Cleanup — cascades containers → scan_results → findings
    try:
        await hub.delete(f"/api/v1/agents/{body['id']}")
    except httpx.ConnectError:
        pass  # hub may be unreachable (e.g. after resilience test restart)


@pytest.fixture
async def connected_agent(hub_base_url, registered_agent):
    """SimulatedAgent that has completed the WebSocket handshake with the hub."""
    from helpers.agent_sim import SimulatedAgent

    ws_url = hub_base_url.replace("http://", "ws://") + "/ws/agent"
    agent = SimulatedAgent(
        hub_ws_url=ws_url,
        token=registered_agent["token"],
        hub_public_key=registered_agent["hub_public_key"],
    )
    await agent.connect_and_handshake()
    yield agent
    await agent.close()
