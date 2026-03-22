"""Orchestration logic for Copa patching and container restarts."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.core.log_buffer import log_buffer
from trivyal_hub.db.models import (
    Container,
    Finding,
    FindingStatus,
    PatchRequest,
    PatchStatus,
    RestartRequest,
    RestartStatus,
    ScanResult,
    _now,
)

logger = logging.getLogger(__name__)


async def create_patch_request(
    session: AsyncSession,
    agent_id: str,
    container_id: str,
    image_name: str,
) -> PatchRequest:
    pr = PatchRequest(
        agent_id=agent_id,
        container_id=container_id,
        image_name=image_name,
    )
    session.add(pr)
    await session.commit()
    await session.refresh(pr)
    return pr


async def trigger_patch(manager, session: AsyncSession, patch_request: PatchRequest) -> bool:
    """Look up latest scan for the container and send patch_trigger via WebSocket."""
    # Find the latest scan result with trivy_raw
    scan = (
        await session.execute(
            select(ScanResult)
            .where(ScanResult.container_id == patch_request.container_id)
            .order_by(ScanResult.scanned_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if not scan or not scan.trivy_raw:
        logger.warning("No scan data for container %s — cannot trigger patch", patch_request.container_id)
        patch_request.status = PatchStatus.FAILED
        patch_request.error_message = "No scan data available. Run a scan first, then retry."
        session.add(patch_request)
        await session.commit()
        return False

    trivy_report = scan.trivy_raw

    # Build the full image reference Copa needs (e.g. "nginx:1.23.0")
    container = await session.get(Container, patch_request.container_id)
    if container and container.image_tag:
        full_image = f"{patch_request.image_name}:{container.image_tag}"
    else:
        full_image = patch_request.image_name

    # Count fixable OS-level findings for this container
    fixable = (
        (
            await session.execute(
                select(Finding)
                .join(ScanResult)
                .where(
                    ScanResult.container_id == patch_request.container_id,
                    Finding.status == FindingStatus.ACTIVE,
                    Finding.fixed_version.isnot(None),
                    Finding.fixed_version != "",
                )
            )
        )
        .scalars()
        .all()
    )
    patch_request.original_finding_count = len(fixable)

    patched_tag = f"{patch_request.image_name}:trivyal-patched"

    payload = {
        "type": "patch_trigger",
        "request_id": patch_request.id,
        "image": full_image,
        "trivy_report": trivy_report,
        "patched_tag": patched_tag,
    }

    sent = await manager.send_patch_trigger(patch_request.agent_id, payload)
    if sent:
        patch_request.status = PatchStatus.RUNNING
        session.add(patch_request)
        await session.commit()
    return sent


async def handle_patch_log(session: AsyncSession, request_id: str, line: str) -> None:
    await log_buffer.publish(request_id, line)


async def handle_patch_result(
    session: AsyncSession,
    request_id: str,
    status: str,
    patched_tag: str | None = None,
    error: str | None = None,
) -> None:
    pr = await session.get(PatchRequest, request_id)
    if not pr:
        logger.warning("Received patch result for unknown request %s", request_id)
        return

    pr.status = PatchStatus(status)
    pr.completed_at = _now()
    if patched_tag:
        pr.patched_tag = patched_tag
    if error:
        pr.error_message = error
    session.add(pr)
    await session.commit()
    await log_buffer.complete(request_id)


async def create_restart_request(
    session: AsyncSession,
    patch_request_id: str,
    container_id: str,
) -> RestartRequest:
    rr = RestartRequest(
        patch_request_id=patch_request_id,
        container_id=container_id,
    )
    session.add(rr)
    await session.commit()
    await session.refresh(rr)
    return rr


async def trigger_restart(
    manager,
    session: AsyncSession,
    restart_request: RestartRequest,
    patch_request: PatchRequest,
) -> bool:
    if not patch_request.patched_tag:
        restart_request.status = RestartStatus.FAILED
        restart_request.error_message = "No patched tag available"
        session.add(restart_request)
        await session.commit()
        return False

    container = await session.get(Container, restart_request.container_id)
    docker_container_ref = (container.container_name if container else None) or restart_request.container_id

    payload = {
        "type": "restart_trigger",
        "request_id": restart_request.id,
        "container_id": docker_container_ref,
        "image": patch_request.patched_tag,
    }

    sent = await manager.send_restart_trigger(patch_request.agent_id, payload)
    if sent:
        restart_request.status = RestartStatus.RUNNING
        session.add(restart_request)
        await session.commit()
    return sent


async def handle_restart_result(
    session: AsyncSession,
    request_id: str,
    status: str,
    new_container_id: str | None = None,
    error: str | None = None,
    block_reason: str | None = None,
) -> None:
    rr = await session.get(RestartRequest, request_id)
    if not rr:
        logger.warning("Received restart result for unknown request %s", request_id)
        return

    rr.status = RestartStatus(status)
    rr.completed_at = _now()
    if error:
        rr.error_message = error
    if block_reason:
        rr.block_reason = block_reason
    session.add(rr)
    await session.commit()
