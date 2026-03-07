"""Misconfiguration finding and risk acceptance endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import (
    Container,
    MisconfigFinding,
    MisconfigStatus,
    RiskAcceptance,
    Severity,
)
from trivyal_hub.db.session import get_session
from trivyal_hub.schemas.common import PaginatedResponse
from trivyal_hub.schemas.findings import RiskAcceptanceCreate, RiskAcceptanceResponse
from trivyal_hub.schemas.misconfigs import MisconfigFindingResponse, MisconfigFindingUpdate

router = APIRouter(prefix="/misconfigs", tags=["misconfigs"], dependencies=[Depends(require_auth)])

_SORT_COLUMNS: dict = {
    "severity": MisconfigFinding.severity,
    "check_id": MisconfigFinding.check_id,
    "status": MisconfigFinding.status,
    "first_seen": MisconfigFinding.first_seen,
    "last_seen": MisconfigFinding.last_seen,
    "container": Container.container_name,
}


def _to_response(
    finding: MisconfigFinding,
    container_name: str | None,
    image_name: str | None,
) -> MisconfigFindingResponse:
    return MisconfigFindingResponse(
        id=finding.id,
        container_id=finding.container_id,
        container_name=container_name,
        image_name=image_name,
        check_id=finding.check_id,
        severity=finding.severity,
        title=finding.title,
        fix_guideline=finding.fix_guideline,
        status=finding.status,
        first_seen=finding.first_seen,
        last_seen=finding.last_seen,
    )


async def _fetch_one(session: AsyncSession, finding_id: str):
    return (
        await session.execute(
            select(MisconfigFinding, Container.container_name, Container.image_name)
            .join(Container, MisconfigFinding.container_id == Container.id)
            .where(MisconfigFinding.id == finding_id)
        )
    ).first()


@router.get("", response_model=PaginatedResponse[MisconfigFindingResponse])
async def list_misconfigs(
    severity: Severity | None = None,
    misconfig_status: MisconfigStatus | None = Query(None, alias="status"),
    agent_id: str | None = None,
    container_id: str | None = None,
    check_id: str | None = None,
    sort_by: str = Query(
        "first_seen",
        pattern="^(severity|check_id|status|first_seen|last_seen|container)$",
    ),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = select(MisconfigFinding, Container.container_name, Container.image_name).join(
        Container, MisconfigFinding.container_id == Container.id
    )
    count_q = (
        select(func.count())
        .select_from(MisconfigFinding)
        .join(Container, MisconfigFinding.container_id == Container.id)
    )

    if severity:
        query = query.where(MisconfigFinding.severity == severity)
        count_q = count_q.where(MisconfigFinding.severity == severity)
    if misconfig_status:
        query = query.where(MisconfigFinding.status == misconfig_status)
        count_q = count_q.where(MisconfigFinding.status == misconfig_status)
    if check_id:
        query = query.where(MisconfigFinding.check_id == check_id)
        count_q = count_q.where(MisconfigFinding.check_id == check_id)
    if agent_id:
        query = query.where(Container.agent_id == agent_id)
        count_q = count_q.where(Container.agent_id == agent_id)
    if container_id:
        query = query.where(MisconfigFinding.container_id == container_id)
        count_q = count_q.where(MisconfigFinding.container_id == container_id)

    sort_col = _SORT_COLUMNS.get(sort_by, MisconfigFinding.first_seen)
    query = query.order_by(sort_col.asc() if sort_dir == "asc" else sort_col.desc())

    total = (await session.execute(count_q)).scalar_one()
    rows = (await session.execute(query.offset((page - 1) * page_size).limit(page_size))).all()

    return PaginatedResponse(
        data=[_to_response(f, cname, iname) for f, cname, iname in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{finding_id}", response_model=MisconfigFindingResponse)
async def get_misconfig(
    finding_id: str,
    session: AsyncSession = Depends(get_session),
):
    row = await _fetch_one(session, finding_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Misconfig finding not found")
    finding, cname, iname = row
    return _to_response(finding, cname, iname)


@router.patch("/{finding_id}", response_model=MisconfigFindingResponse)
async def update_misconfig(
    finding_id: str,
    body: MisconfigFindingUpdate,
    session: AsyncSession = Depends(get_session),
):
    finding = await session.get(MisconfigFinding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Misconfig finding not found")
    finding.status = body.status
    session.add(finding)
    await session.commit()

    row = await _fetch_one(session, finding_id)
    finding, cname, iname = row  # type: ignore[misc]
    return _to_response(finding, cname, iname)


@router.post(
    "/{finding_id}/acceptances",
    response_model=RiskAcceptanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_misconfig_acceptance(
    finding_id: str,
    body: RiskAcceptanceCreate,
    session: AsyncSession = Depends(get_session),
):
    finding = await session.get(MisconfigFinding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Misconfig finding not found")

    acceptance = RiskAcceptance(
        misconfig_finding_id=finding_id,
        reason=body.reason,
        expires_at=body.expires_at,
    )
    session.add(acceptance)

    finding.status = MisconfigStatus.ACCEPTED
    session.add(finding)

    await session.commit()
    await session.refresh(acceptance)
    return RiskAcceptanceResponse(
        id=acceptance.id,
        finding_id=acceptance.misconfig_finding_id or "",
        reason=acceptance.reason,
        accepted_by=acceptance.accepted_by,
        expires_at=acceptance.expires_at,
        created_at=acceptance.created_at,
    )


@router.delete(
    "/{finding_id}/acceptances/{acceptance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_misconfig_acceptance(
    finding_id: str,
    acceptance_id: str,
    session: AsyncSession = Depends(get_session),
):
    acceptance = await session.get(RiskAcceptance, acceptance_id)
    if not acceptance or acceptance.misconfig_finding_id != finding_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceptance not found")

    finding = await session.get(MisconfigFinding, finding_id)
    if finding:
        finding.status = MisconfigStatus.ACTIVE
        session.add(finding)

    await session.delete(acceptance)
    await session.commit()
