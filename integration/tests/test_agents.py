"""
Integration tests for agent management.

Coverage:
- Register agent → returns id, token, hub_public_key
- Duplicate name → 409
- List agents (paginated envelope)
- Filter agents by status
- Get agent by ID
- Unknown agent ID → 404
- Delete agent
- Delete unknown agent → 404
"""

import pytest


class TestRegisterAgent:
    async def test_creates_agent_returns_token_and_key(self, hub):
        import uuid

        name = f"reg-{uuid.uuid4().hex[:8]}"
        r = await hub.post("/api/v1/agents", json={"name": name})
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == name
        assert len(body["id"]) > 0
        assert len(body["token"]) > 0
        assert len(body["hub_public_key"]) > 0
        # Cleanup
        await hub.delete(f"/api/v1/agents/{body['id']}")

    async def test_duplicate_name_returns_409(self, registered_agent, hub):
        r = await hub.post("/api/v1/agents", json={"name": registered_agent["name"]})
        assert r.status_code == 409

    async def test_token_is_url_safe(self, registered_agent):
        token = registered_agent["token"]
        assert " " not in token
        assert len(token) > 0

    async def test_hub_public_key_is_base64(self, registered_agent):
        import base64

        key = registered_agent["hub_public_key"]
        # Should decode without error and be 32 bytes (Ed25519 verify key)
        raw = base64.b64decode(key)
        assert len(raw) == 32


class TestListAgents:
    async def test_returns_paginated_envelope(self, hub):
        r = await hub.get("/api/v1/agents")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "total" in body
        assert "page" in body
        assert "page_size" in body

    async def test_registered_agent_appears_in_list(self, hub, registered_agent):
        r = await hub.get("/api/v1/agents")
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()["data"]]
        assert registered_agent["id"] in ids

    async def test_filter_by_status_offline(self, hub, registered_agent):
        # Newly registered agents start offline
        r = await hub.get("/api/v1/agents", params={"status": "offline"})
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()["data"]]
        assert registered_agent["id"] in ids

    async def test_filter_by_status_online_excludes_offline_agent(self, hub, registered_agent):
        r = await hub.get("/api/v1/agents", params={"status": "online"})
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()["data"]]
        assert registered_agent["id"] not in ids


class TestGetAgent:
    async def test_returns_agent_detail(self, hub, registered_agent):
        r = await hub.get(f"/api/v1/agents/{registered_agent['id']}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == registered_agent["id"]
        assert body["name"] == registered_agent["name"]
        assert body["status"] == "offline"

    async def test_unknown_id_returns_404(self, hub):
        r = await hub.get("/api/v1/agents/nonexistent000000000000000000000000")
        assert r.status_code == 404


class TestDeleteAgent:
    async def test_removes_agent(self, hub):
        import uuid

        name = f"del-{uuid.uuid4().hex[:8]}"
        create_r = await hub.post("/api/v1/agents", json={"name": name})
        agent_id = create_r.json()["id"]

        del_r = await hub.delete(f"/api/v1/agents/{agent_id}")
        assert del_r.status_code == 204

        get_r = await hub.get(f"/api/v1/agents/{agent_id}")
        assert get_r.status_code == 404

    async def test_unknown_id_returns_404(self, hub):
        r = await hub.delete("/api/v1/agents/nonexistent000000000000000000000000")
        assert r.status_code == 404
