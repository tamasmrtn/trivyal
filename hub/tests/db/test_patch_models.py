"""Tests for PatchRequest and RestartRequest models."""

from trivyal_hub.db.models import (
    Agent,
    Container,
    PatchRequest,
    PatchStatus,
    RestartRequest,
    RestartStatus,
)


class TestCreatePatchRequest:
    async def test_round_trip(self, session):
        agent = Agent(name="a1", token_hash="h")
        session.add(agent)
        await session.flush()

        container = Container(agent_id=agent.id, image_name="nginx")
        session.add(container)
        await session.flush()

        pr = PatchRequest(agent_id=agent.id, container_id=container.id, image_name="nginx")
        session.add(pr)
        await session.commit()

        loaded = await session.get(PatchRequest, pr.id)
        assert loaded is not None
        assert loaded.image_name == "nginx"
        assert loaded.status == PatchStatus.PENDING
        assert loaded.requested_at is not None

    async def test_stores_log_lines(self, session):
        agent = Agent(name="a2", token_hash="h")
        session.add(agent)
        await session.flush()

        container = Container(agent_id=agent.id, image_name="redis")
        session.add(container)
        await session.flush()

        pr = PatchRequest(
            agent_id=agent.id,
            container_id=container.id,
            image_name="redis",
            log_lines=["line1", "line2"],
        )
        session.add(pr)
        await session.commit()

        loaded = await session.get(PatchRequest, pr.id)
        assert loaded.log_lines == ["line1", "line2"]


class TestPatchRestartRelationship:
    async def test_restart_linked_to_patch(self, session):
        agent = Agent(name="a3", token_hash="h")
        session.add(agent)
        await session.flush()

        container = Container(agent_id=agent.id, image_name="alpine")
        session.add(container)
        await session.flush()

        pr = PatchRequest(agent_id=agent.id, container_id=container.id, image_name="alpine")
        session.add(pr)
        await session.flush()

        rr = RestartRequest(
            patch_request_id=pr.id,
            container_id=container.id,
        )
        session.add(rr)
        await session.commit()

        loaded = await session.get(RestartRequest, rr.id)
        assert loaded is not None
        assert loaded.status == RestartStatus.PENDING
        assert loaded.patch_request_id == pr.id

    async def test_cascade_delete(self, session):
        agent = Agent(name="a4", token_hash="h")
        session.add(agent)
        await session.flush()

        container = Container(agent_id=agent.id, image_name="postgres")
        session.add(container)
        await session.flush()

        pr = PatchRequest(agent_id=agent.id, container_id=container.id, image_name="postgres")
        session.add(pr)
        await session.flush()

        rr = RestartRequest(patch_request_id=pr.id, container_id=container.id)
        session.add(rr)
        await session.commit()

        await session.delete(pr)
        await session.commit()

        loaded = await session.get(RestartRequest, rr.id)
        assert loaded is None
