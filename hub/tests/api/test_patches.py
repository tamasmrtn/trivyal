"""Tests for patch endpoints."""

from unittest.mock import AsyncMock, patch

from trivyal_hub.db.models import Agent, Container, PatchRequest, PatchStatus


async def _create_agent_and_container(client, auth_header, session):
    """Helper to create an agent with patching enabled and a container."""
    resp = await client.post("/api/v1/agents", json={"name": "p1"}, headers=auth_header)
    agent_id = resp.json()["id"]

    # Set host_metadata with patching_available
    from sqlmodel import select

    agent = (await session.execute(select(Agent).where(Agent.id == agent_id))).scalar_one()
    agent.host_metadata = {"patching_available": True}
    session.add(agent)

    container = Container(agent_id=agent_id, image_name="nginx")
    session.add(container)
    await session.commit()
    await session.refresh(container)

    return agent_id, container.id


class TestCreatePatch:
    async def test_returns_201_when_agent_connected_with_patching(self, client, auth_header, session):
        agent_id, container_id = await _create_agent_and_container(client, auth_header, session)

        with (
            patch("trivyal_hub.api.v1.patches.manager.active", {agent_id: AsyncMock()}),
            patch("trivyal_hub.api.v1.patches.trigger_patch", new=AsyncMock(return_value=True)),
        ):
            resp = await client.post(
                "/api/v1/patches",
                json={"agent_id": agent_id, "container_id": container_id, "image_name": "nginx"},
                headers=auth_header,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["image_name"] == "nginx"
        assert data["status"] in ("pending", "running")

    async def test_returns_404_for_unknown_agent(self, client, auth_header):
        resp = await client.post(
            "/api/v1/patches",
            json={"agent_id": "bad-id", "container_id": "cid", "image_name": "nginx"},
            headers=auth_header,
        )
        assert resp.status_code == 404

    async def test_returns_409_for_disconnected_agent(self, client, auth_header, session):
        agent_id, container_id = await _create_agent_and_container(client, auth_header, session)

        with patch("trivyal_hub.api.v1.patches.manager.active", {}):
            resp = await client.post(
                "/api/v1/patches",
                json={"agent_id": agent_id, "container_id": container_id, "image_name": "nginx"},
                headers=auth_header,
            )

        assert resp.status_code == 409


class TestListPatches:
    async def test_returns_empty_list(self, client, auth_header):
        resp = await client.get("/api/v1/patches", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    async def test_returns_patches(self, client, auth_header, session):
        agent_id, container_id = await _create_agent_and_container(client, auth_header, session)

        pr = PatchRequest(agent_id=agent_id, container_id=container_id, image_name="nginx")
        session.add(pr)
        await session.commit()

        resp = await client.get("/api/v1/patches", headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    async def test_filters_by_status(self, client, auth_header, session):
        agent_id, container_id = await _create_agent_and_container(client, auth_header, session)

        pr = PatchRequest(
            agent_id=agent_id, container_id=container_id, image_name="nginx", status=PatchStatus.COMPLETED
        )
        session.add(pr)
        await session.commit()

        resp = await client.get("/api/v1/patches?status=pending", headers=auth_header)
        assert resp.json()["total"] == 0

        resp = await client.get("/api/v1/patches?status=completed", headers=auth_header)
        assert resp.json()["total"] == 1


class TestGetPatch:
    async def test_returns_patch_with_restarts(self, client, auth_header, session):
        agent_id, container_id = await _create_agent_and_container(client, auth_header, session)

        pr = PatchRequest(agent_id=agent_id, container_id=container_id, image_name="nginx")
        session.add(pr)
        await session.commit()

        resp = await client.get(f"/api/v1/patches/{pr.id}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert data["image_name"] == "nginx"
        assert data["restarts"] == []

    async def test_returns_404_for_unknown_patch(self, client, auth_header):
        resp = await client.get("/api/v1/patches/bad-id", headers=auth_header)
        assert resp.status_code == 404


class TestTriggerRestart:
    async def test_returns_202_when_patch_completed(self, client, auth_header, session):
        agent_id, container_id = await _create_agent_and_container(client, auth_header, session)

        pr = PatchRequest(
            agent_id=agent_id,
            container_id=container_id,
            image_name="nginx",
            status=PatchStatus.COMPLETED,
            patched_tag="nginx:trivyal-patched",
        )
        session.add(pr)
        await session.commit()

        with (
            patch("trivyal_hub.api.v1.patches.manager.active", {agent_id: AsyncMock()}),
            patch("trivyal_hub.api.v1.patches.trigger_restart", new=AsyncMock(return_value=True)),
        ):
            resp = await client.post(f"/api/v1/patches/{pr.id}/restart", headers=auth_header)

        assert resp.status_code == 202

    async def test_returns_400_when_patch_not_completed(self, client, auth_header, session):
        agent_id, container_id = await _create_agent_and_container(client, auth_header, session)

        pr = PatchRequest(
            agent_id=agent_id,
            container_id=container_id,
            image_name="nginx",
            status=PatchStatus.RUNNING,
        )
        session.add(pr)
        await session.commit()

        resp = await client.post(f"/api/v1/patches/{pr.id}/restart", headers=auth_header)
        assert resp.status_code == 400
