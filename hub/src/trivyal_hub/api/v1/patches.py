"""Patch and restart endpoints."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.core.log_buffer import log_buffer
from trivyal_hub.core.patch_coordinator import (
    create_patch_request,
    create_restart_request,
    trigger_patch,
    trigger_restart,
)
from trivyal_hub.db.models import (
    Agent,
    PatchRequest,
    PatchStatus,
    RestartRequest,
)
from trivyal_hub.db.session import get_session
from trivyal_hub.schemas.common import PaginatedResponse
from trivyal_hub.schemas.patches import (
    PatchCreateRequest,
    PatchResponse,
    PatchSummary,
    RestartResponse,
)
from trivyal_hub.ws.manager import manager

router = APIRouter(tags=["patches"], dependencies=[Depends(require_auth)])


def _to_restart_response(rr: RestartRequest) -> RestartResponse:
    return RestartResponse(
        id=rr.id,
        patch_request_id=rr.patch_request_id,
        container_id=rr.container_id,
        status=rr.status,
        block_reason=rr.block_reason,
        error_message=rr.error_message,
        requested_at=rr.requested_at,
        completed_at=rr.completed_at,
        reverted_at=rr.reverted_at,
    )


def _to_patch_response(pr: PatchRequest, restarts: list[RestartRequest] | None = None) -> PatchResponse:
    return PatchResponse(
        id=pr.id,
        agent_id=pr.agent_id,
        container_id=pr.container_id,
        image_name=pr.image_name,
        patched_tag=pr.patched_tag,
        status=pr.status,
        original_finding_count=pr.original_finding_count,
        patched_finding_count=pr.patched_finding_count,
        error_message=pr.error_message,
        requested_at=pr.requested_at,
        completed_at=pr.completed_at,
        restarts=[_to_restart_response(rr) for rr in (restarts or [])],
    )


@router.post("/patches", response_model=PatchResponse, status_code=status.HTTP_201_CREATED)
async def create_patch(
    body: PatchCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, body.agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    if body.agent_id not in manager.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent is not connected")

    patching = (agent.host_metadata or {}).get("patching_available", False)
    if not patching:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent does not have patching available",
        )

    pr = await create_patch_request(session, body.agent_id, body.container_id, body.image_name)
    sent = await trigger_patch(manager, session, pr)
    if not sent:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed to send patch trigger to agent")

    await session.refresh(pr)
    return _to_patch_response(pr)


@router.get("/patches", response_model=PaginatedResponse[PatchResponse])
async def list_patches(
    status_filter: PatchStatus | None = Query(None, alias="status"),
    agent_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = select(PatchRequest).order_by(PatchRequest.requested_at.desc())
    count_q = select(func.count()).select_from(PatchRequest)

    if status_filter:
        query = query.where(PatchRequest.status == status_filter)
        count_q = count_q.where(PatchRequest.status == status_filter)
    if agent_id:
        query = query.where(PatchRequest.agent_id == agent_id)
        count_q = count_q.where(PatchRequest.agent_id == agent_id)

    total = (await session.execute(count_q)).scalar_one()
    rows = (await session.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return PaginatedResponse(
        data=[_to_patch_response(pr) for pr in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/patches/{patch_id}", response_model=PatchResponse)
async def get_patch(
    patch_id: str,
    session: AsyncSession = Depends(get_session),
):
    pr = await session.get(PatchRequest, patch_id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patch not found")

    restarts = (
        (await session.execute(select(RestartRequest).where(RestartRequest.patch_request_id == patch_id)))
        .scalars()
        .all()
    )

    return _to_patch_response(pr, restarts)


@router.get("/patches/{patch_id}/logs")
async def stream_patch_logs(
    patch_id: str,
    session: AsyncSession = Depends(get_session),
):
    pr = await session.get(PatchRequest, patch_id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patch not found")

    queue = log_buffer.subscribe(patch_id)

    async def event_stream():
        while True:
            try:
                line = await asyncio.wait_for(queue.get(), timeout=60.0)
            except TimeoutError:
                yield ":\n\n"  # SSE keepalive
                continue
            if line is None:
                break
            yield f"data: {line}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post(
    "/patches/{patch_id}/restart",
    response_model=RestartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_container_restart(
    patch_id: str,
    session: AsyncSession = Depends(get_session),
):
    pr = await session.get(PatchRequest, patch_id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patch not found")

    if pr.status != PatchStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patch must be completed before restarting",
        )

    rr = await create_restart_request(session, pr.id, pr.container_id)
    sent = await trigger_restart(manager, session, rr, pr)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to send restart trigger to agent",
        )

    await session.refresh(rr)
    return _to_restart_response(rr)


@router.get("/restarts/{restart_id}", response_model=RestartResponse)
async def get_restart(
    restart_id: str,
    session: AsyncSession = Depends(get_session),
):
    rr = await session.get(RestartRequest, restart_id)
    if not rr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restart not found")
    return _to_restart_response(rr)


@router.get("/dashboard/patch-summary", response_model=PatchSummary)
async def get_patch_summary(
    session: AsyncSession = Depends(get_session),
):
    total_patched = (
        await session.execute(
            select(func.count()).select_from(PatchRequest).where(PatchRequest.status == PatchStatus.COMPLETED)
        )
    ).scalar_one()

    # Sum of (original - patched) for completed patches
    rows = (
        await session.execute(
            select(PatchRequest.original_finding_count, PatchRequest.patched_finding_count).where(
                PatchRequest.status == PatchStatus.COMPLETED
            )
        )
    ).all()
    findings_resolved = sum((orig or 0) - (patched or 0) for orig, patched in rows if orig is not None)

    # Check if any agent has patching_available
    agents = (await session.execute(select(Agent))).scalars().all()
    patching_available = any((a.host_metadata or {}).get("patching_available", False) for a in agents)

    return PatchSummary(
        total_patched=total_patched,
        findings_resolved=max(findings_resolved, 0),
        patching_available=patching_available,
    )
