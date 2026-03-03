"""Scan history endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import Agent, AgentStatus, Container, ScanResult
from trivyal_hub.db.session import get_session
from trivyal_hub.schemas.common import PaginatedResponse
from trivyal_hub.schemas.scans import ScanResultDetail, ScanResultResponse, ScanTriggerResponse
from trivyal_hub.ws.manager import manager

router = APIRouter(tags=["scans"], dependencies=[Depends(require_auth)])


def _to_scan_response(
    scan: ScanResult,
    agent_name: str | None,
    container_name: str | None,
    image_name: str | None,
) -> ScanResultResponse:
    return ScanResultResponse(
        id=scan.id,
        container_id=scan.container_id,
        agent_id=scan.agent_id,
        agent_name=agent_name,
        container_name=container_name or image_name,
        scanned_at=scan.scanned_at,
        critical_count=scan.critical_count,
        high_count=scan.high_count,
        medium_count=scan.medium_count,
        low_count=scan.low_count,
        unknown_count=scan.unknown_count,
    )


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

    query = (
        select(ScanResult, Agent.name, Container.container_name, Container.image_name)
        .join(Agent, ScanResult.agent_id == Agent.id)
        .join(Container, ScanResult.container_id == Container.id)
        .where(ScanResult.agent_id == agent_id)
        .order_by(ScanResult.scanned_at.desc())
    )
    count_q = select(func.count()).select_from(ScanResult).where(ScanResult.agent_id == agent_id)

    total = (await session.execute(count_q)).scalar_one()
    rows = (await session.execute(query.offset((page - 1) * page_size).limit(page_size))).all()

    return PaginatedResponse(
        data=[_to_scan_response(scan, agent_name, cname, iname) for scan, agent_name, cname, iname in rows],
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
    query = (
        select(ScanResult, Agent.name, Container.container_name, Container.image_name)
        .join(Agent, ScanResult.agent_id == Agent.id)
        .join(Container, ScanResult.container_id == Container.id)
        .order_by(ScanResult.scanned_at.desc())
    )
    count_q = select(func.count()).select_from(ScanResult)

    total = (await session.execute(count_q)).scalar_one()
    rows = (await session.execute(query.offset((page - 1) * page_size).limit(page_size))).all()

    return PaginatedResponse(
        data=[_to_scan_response(scan, agent_name, cname, iname) for scan, agent_name, cname, iname in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/scans/{scan_id}", response_model=ScanResultDetail)
async def get_scan(
    scan_id: str,
    session: AsyncSession = Depends(get_session),
):
    row = (
        await session.execute(
            select(ScanResult, Agent.name, Container.container_name, Container.image_name)
            .join(Agent, ScanResult.agent_id == Agent.id)
            .join(Container, ScanResult.container_id == Container.id)
            .where(ScanResult.id == scan_id)
        )
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    scan, agent_name, cname, iname = row
    return ScanResultDetail(
        **_to_scan_response(scan, agent_name, cname, iname).model_dump(),
        trivy_raw=scan.trivy_raw,
    )
