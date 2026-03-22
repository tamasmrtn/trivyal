"""Finding and risk acceptance endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import Container, Finding, FindingStatus, RiskAcceptance, ScanResult, Severity
from trivyal_hub.db.session import get_session
from trivyal_hub.schemas.common import PaginatedResponse
from trivyal_hub.schemas.findings import (
    FindingResponse,
    FindingUpdate,
    RiskAcceptanceCreate,
    RiskAcceptanceResponse,
)

router = APIRouter(prefix="/findings", tags=["findings"], dependencies=[Depends(require_auth)])

_SORT_COLUMNS: dict = {
    "severity": Finding.severity,
    "status": Finding.status,
    "cve_id": Finding.cve_id,
    "package_name": Finding.package_name,
    "first_seen": Finding.first_seen,
    "last_seen": Finding.last_seen,
    "container": Container.image_name,
}


def _to_response(finding: Finding, container_name: str | None, image_name: str | None) -> FindingResponse:
    return FindingResponse(
        id=finding.id,
        scan_result_id=finding.scan_result_id,
        cve_id=finding.cve_id,
        package_name=finding.package_name,
        installed_version=finding.installed_version,
        fixed_version=finding.fixed_version,
        severity=finding.severity,
        description=finding.description,
        status=finding.status,
        container_name=container_name or image_name,
        first_seen=finding.first_seen,
        last_seen=finding.last_seen,
    )


async def _fetch_one(session: AsyncSession, finding_id: str):
    """Fetch a single finding joined with its container name and image name."""
    return (
        await session.execute(
            select(Finding, Container.container_name, Container.image_name)
            .join(ScanResult, Finding.scan_result_id == ScanResult.id)
            .join(Container, ScanResult.container_id == Container.id)
            .where(Finding.id == finding_id)
        )
    ).first()


@router.get("", response_model=PaginatedResponse[FindingResponse])
async def list_findings(
    severity: Severity | None = None,
    finding_status: FindingStatus | None = Query(None, alias="status"),
    agent_id: str | None = None,
    container_id: str | None = None,
    cve_id: str | None = None,
    package: str | None = None,
    image_name: str | None = None,
    image_tag: str | None = None,
    fixable: bool | None = None,
    sort_by: str = Query(
        "first_seen",
        pattern="^(severity|status|cve_id|package_name|first_seen|last_seen|container)$",
    ),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = (
        select(Finding, Container.container_name, Container.image_name)
        .join(ScanResult, Finding.scan_result_id == ScanResult.id)
        .join(Container, ScanResult.container_id == Container.id)
    )
    count_q = (
        select(func.count())
        .select_from(Finding)
        .join(ScanResult, Finding.scan_result_id == ScanResult.id)
        .join(Container, ScanResult.container_id == Container.id)
    )

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
    if agent_id:
        query = query.where(ScanResult.agent_id == agent_id)
        count_q = count_q.where(ScanResult.agent_id == agent_id)
    if container_id:
        query = query.where(ScanResult.container_id == container_id)
        count_q = count_q.where(ScanResult.container_id == container_id)
    if image_name:
        query = query.where(Container.image_name == image_name)
        count_q = count_q.where(Container.image_name == image_name)
    if image_tag:
        query = query.where(Container.image_tag == image_tag)
        count_q = count_q.where(Container.image_tag == image_tag)
    if fixable:
        fixable_cond = Finding.fixed_version.isnot(None) & (Finding.fixed_version != "")
        query = query.where(fixable_cond)
        count_q = count_q.where(fixable_cond)

    sort_col = _SORT_COLUMNS.get(sort_by, Finding.first_seen)
    query = query.order_by(sort_col.asc() if sort_dir == "asc" else sort_col.desc())

    total = (await session.execute(count_q)).scalar_one()
    rows = (await session.execute(query.offset((page - 1) * page_size).limit(page_size))).all()

    return PaginatedResponse(
        data=[_to_response(finding, cname, iname) for finding, cname, iname in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    session: AsyncSession = Depends(get_session),
):
    row = await _fetch_one(session, finding_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    finding, cname, iname = row
    return _to_response(finding, cname, iname)


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

    row = await _fetch_one(session, finding_id)
    finding, cname, iname = row  # type: ignore[misc]
    return _to_response(finding, cname, iname)


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


@router.get("/{finding_id}/acceptances", response_model=list[RiskAcceptanceResponse])
async def list_acceptances(
    finding_id: str,
    session: AsyncSession = Depends(get_session),
):
    finding = await session.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    results = (
        (
            await session.execute(
                select(RiskAcceptance)
                .where(RiskAcceptance.finding_id == finding_id)
                .order_by(RiskAcceptance.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [RiskAcceptanceResponse.model_validate(a, from_attributes=True) for a in results]


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
