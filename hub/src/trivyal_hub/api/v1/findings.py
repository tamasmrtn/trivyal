"""Finding and risk acceptance endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import Finding, FindingStatus, RiskAcceptance, Severity
from trivyal_hub.db.session import get_session
from trivyal_hub.schemas.common import PaginatedResponse
from trivyal_hub.schemas.findings import (
    FindingResponse,
    FindingUpdate,
    RiskAcceptanceCreate,
    RiskAcceptanceResponse,
)

router = APIRouter(prefix="/findings", tags=["findings"], dependencies=[Depends(require_auth)])


@router.get("", response_model=PaginatedResponse[FindingResponse])
async def list_findings(
    severity: Severity | None = None,
    finding_status: FindingStatus | None = Query(None, alias="status"),
    agent_id: str | None = None,
    cve_id: str | None = None,
    package: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = select(Finding)
    count_q = select(func.count()).select_from(Finding)

    if severity:
        query = query.where(Finding.severity == severity)
        count_q = count_q.where(Finding.severity == severity)
    if finding_status:
        query = query.where(Finding.status == finding_status)
        count_q = count_q.where(Finding.status == finding_status)
    if cve_id:
        query = query.where(Finding.cve_id == cve_id)
        count_q = count_q.where(Finding.cve_id == cve_id)
    if package:
        query = query.where(Finding.package_name == package)
        count_q = count_q.where(Finding.package_name == package)

    total = (await session.execute(count_q)).scalar_one()
    results = (
        await session.execute(query.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return PaginatedResponse(
        data=[FindingResponse.model_validate(f, from_attributes=True) for f in results],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    session: AsyncSession = Depends(get_session),
):
    finding = await session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return FindingResponse.model_validate(finding, from_attributes=True)


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    body: FindingUpdate,
    session: AsyncSession = Depends(get_session),
):
    finding = await session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    finding.status = body.status
    session.add(finding)
    await session.commit()
    await session.refresh(finding)
    return FindingResponse.model_validate(finding, from_attributes=True)


@router.post(
    "/{finding_id}/acceptances",
    response_model=RiskAcceptanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_acceptance(
    finding_id: str,
    body: RiskAcceptanceCreate,
    session: AsyncSession = Depends(get_session),
):
    finding = await session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    acceptance = RiskAcceptance(
        finding_id=finding_id,
        reason=body.reason,
        expires_at=body.expires_at,
    )
    session.add(acceptance)

    finding.status = FindingStatus.ACCEPTED
    session.add(finding)

    await session.commit()
    await session.refresh(acceptance)
    return RiskAcceptanceResponse.model_validate(acceptance, from_attributes=True)


@router.delete(
    "/{finding_id}/acceptances/{acceptance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_acceptance(
    finding_id: str,
    acceptance_id: str,
    session: AsyncSession = Depends(get_session),
):
    acceptance = await session.get(RiskAcceptance, acceptance_id)
    if not acceptance or acceptance.finding_id != finding_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceptance not found")

    finding = await session.get(Finding, finding_id)
    if finding:
        finding.status = FindingStatus.ACTIVE
        session.add(finding)

    await session.delete(acceptance)
    await session.commit()
