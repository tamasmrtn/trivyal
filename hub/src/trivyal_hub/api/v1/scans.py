"""Scan history endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import Agent, AgentStatus, ScanResult
from trivyal_hub.db.session import get_session
from trivyal_hub.schemas.common import PaginatedResponse
from trivyal_hub.schemas.scans import ScanResultDetail, ScanResultResponse, ScanTriggerResponse
from trivyal_hub.ws.manager import manager

router = APIRouter(tags=["scans"], dependencies=[Depends(require_auth)])


@router.post(
    "/agents/{agent_id}/scans",
    response_model=ScanTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_scan(
    agent_id: str,
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    sent = await manager.send_scan_trigger(agent_id)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent is not connected",
        )

    agent.status = AgentStatus.SCANNING
    session.add(agent)
    await session.commit()

    return ScanTriggerResponse(job_id=uuid4().hex)


@router.get("/agents/{agent_id}/scans", response_model=PaginatedResponse[ScanResultResponse])
async def list_agent_scans(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    query = select(ScanResult).where(ScanResult.agent_id == agent_id).order_by(ScanResult.scanned_at.desc())
    count_q = select(func.count()).select_from(ScanResult).where(ScanResult.agent_id == agent_id)

    total = (await session.execute(count_q)).scalar_one()
    results = (await session.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return PaginatedResponse(
        data=[ScanResultResponse.model_validate(r, from_attributes=True) for r in results],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/scans", response_model=PaginatedResponse[ScanResultResponse])
async def list_all_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = select(ScanResult).order_by(ScanResult.scanned_at.desc())
    count_q = select(func.count()).select_from(ScanResult)

    total = (await session.execute(count_q)).scalar_one()
    results = (await session.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return PaginatedResponse(
        data=[ScanResultResponse.model_validate(r, from_attributes=True) for r in results],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/scans/{scan_id}", response_model=ScanResultDetail)
async def get_scan(
    scan_id: str,
    session: AsyncSession = Depends(get_session),
):
    scan = await session.get(ScanResult, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return ScanResultDetail.model_validate(scan, from_attributes=True)
