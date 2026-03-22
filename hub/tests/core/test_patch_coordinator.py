"""Tests for patch_coordinator — orchestration logic."""

from unittest.mock import AsyncMock

from trivyal_hub.core.patch_coordinator import (
    create_patch_request,
    create_restart_request,
    handle_patch_result,
    handle_restart_result,
    trigger_patch,
    trigger_restart,
)
from trivyal_hub.db.models import (
    Agent,
    Container,
    PatchRequest,
    PatchStatus,
    RestartRequest,
    RestartStatus,
)


async def _setup(session):
    agent = Agent(name="test-agent", token_hash="h")
    session.add(agent)
    await session.flush()

    container = Container(agent_id=agent.id, image_name="nginx")
    session.add(container)
    await session.flush()
    return agent, container


class TestCreatePatchRequest:
    async def test_creates_with_pending_status(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")
        assert pr.status == PatchStatus.PENDING
        assert pr.image_name == "nginx"


class TestTriggerPatch:
    async def test_sends_trigger_and_updates_status(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")

        mock_manager = AsyncMock()
        mock_manager.send_patch_trigger = AsyncMock(return_value=True)

        result = await trigger_patch(mock_manager, session, pr)
        assert result is True
        assert pr.status == PatchStatus.RUNNING
        mock_manager.send_patch_trigger.assert_called_once()

    async def test_returns_false_when_agent_disconnected(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")

        mock_manager = AsyncMock()
        mock_manager.send_patch_trigger = AsyncMock(return_value=False)

        result = await trigger_patch(mock_manager, session, pr)
        assert result is False
        assert pr.status == PatchStatus.PENDING


class TestHandlePatchResult:
    async def test_updates_status_to_completed(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")

        await handle_patch_result(session, pr.id, "completed", patched_tag="nginx:trivyal-patched")

        loaded = await session.get(PatchRequest, pr.id)
        assert loaded.status == PatchStatus.COMPLETED
        assert loaded.patched_tag == "nginx:trivyal-patched"
        assert loaded.completed_at is not None

    async def test_updates_status_to_failed_with_error(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")

        await handle_patch_result(session, pr.id, "failed", error="Copa crashed")

        loaded = await session.get(PatchRequest, pr.id)
        assert loaded.status == PatchStatus.FAILED
        assert loaded.error_message == "Copa crashed"


class TestCreateRestartRequest:
    async def test_creates_with_pending_status(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")
        rr = await create_restart_request(session, pr.id, container.id)
        assert rr.status == RestartStatus.PENDING


class TestTriggerRestart:
    async def test_sends_trigger_and_updates_status(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")
        pr.patched_tag = "nginx:trivyal-patched"
        session.add(pr)
        await session.commit()

        rr = await create_restart_request(session, pr.id, container.id)

        mock_manager = AsyncMock()
        mock_manager.send_restart_trigger = AsyncMock(return_value=True)

        result = await trigger_restart(mock_manager, session, rr, pr)
        assert result is True
        assert rr.status == RestartStatus.RUNNING


class TestHandleRestartResult:
    async def test_updates_status_to_completed(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")
        rr = await create_restart_request(session, pr.id, container.id)

        await handle_restart_result(session, rr.id, "completed", new_container_id="new-id")

        loaded = await session.get(RestartRequest, rr.id)
        assert loaded.status == RestartStatus.COMPLETED
        assert loaded.completed_at is not None

    async def test_updates_blocked_with_reason(self, session):
        agent, container = await _setup(session)
        pr = await create_patch_request(session, agent.id, container.id, "nginx")
        rr = await create_restart_request(session, pr.id, container.id)

        await handle_restart_result(session, rr.id, "blocked", block_reason="anonymous volumes")

        loaded = await session.get(RestartRequest, rr.id)
        assert loaded.status == RestartStatus.BLOCKED
        assert loaded.block_reason == "anonymous volumes"
