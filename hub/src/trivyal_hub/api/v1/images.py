"""Image-centric aggregation endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.api.deps import require_auth
from trivyal_hub.db.models import Agent, Container, Finding, FindingStatus, ScanResult, Severity
from trivyal_hub.db.session import get_session
from trivyal_hub.schemas.common import PaginatedResponse
from trivyal_hub.schemas.images import AgentRef, ImageResponse, SeverityBreakdown

router = APIRouter(prefix="/images", tags=["images"], dependencies=[Depends(require_auth)])


@router.get("", response_model=PaginatedResponse[ImageResponse])
async def list_images(
    agent_id: str | None = None,
    fixable: bool | None = None,
    sort_by: str = Query(
        "fixable_cves",
        pattern="^(fixable_cves|total_cves|image_name|last_scanned)$",
    ),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    # Fetch all containers with their agents
    container_q = select(Container, Agent.id, Agent.name).join(Agent, Container.agent_id == Agent.id)
    if agent_id:
        container_q = container_q.where(Container.agent_id == agent_id)
    container_rows = (await session.execute(container_q)).all()

    # Group containers by image_name
    image_groups: dict[str, dict] = {}
    for container, aid, aname in container_rows:
        key = container.image_name
        if key not in image_groups:
            image_groups[key] = {
                "image_name": container.image_name,
                "image_tag": container.image_tag,
                "image_digest": container.image_digest,
                "container_ids": [],
                "agents": {},
                "last_scanned": container.last_scanned,
            }
        group = image_groups[key]
        group["container_ids"].append(container.id)
        group["agents"][aid] = aname
        if container.last_scanned and (group["last_scanned"] is None or container.last_scanned > group["last_scanned"]):
            group["last_scanned"] = container.last_scanned
        if container.image_tag:
            group["image_tag"] = container.image_tag
        if container.image_digest:
            group["image_digest"] = container.image_digest

    # Get active finding counts per container
    all_container_ids = []
    for group in image_groups.values():
        all_container_ids.extend(group["container_ids"])

    findings_q = (
        select(
            ScanResult.container_id,
            Finding.severity,
            Finding.fixed_version,
        )
        .join(Finding, Finding.scan_result_id == ScanResult.id)
        .where(Finding.status == FindingStatus.ACTIVE)
    )
    if all_container_ids:
        findings_q = findings_q.where(ScanResult.container_id.in_(all_container_ids))
    finding_rows = (await session.execute(findings_q)).all()

    # Aggregate findings per image
    container_to_image: dict[str, str] = {}
    for group in image_groups.values():
        for cid in group["container_ids"]:
            container_to_image[cid] = group["image_name"]

    image_findings: dict[str, dict] = {}
    for cid, sev, fixed_version in finding_rows:
        img = container_to_image.get(cid)
        if not img:
            continue
        if img not in image_findings:
            image_findings[img] = {"total": 0, "fixable": 0, "severity": {s: 0 for s in Severity}}
        image_findings[img]["total"] += 1
        image_findings[img]["severity"][sev] += 1
        if fixed_version:
            image_findings[img]["fixable"] += 1

    # Build response
    results: list[ImageResponse] = []
    for key, group in image_groups.items():
        stats = image_findings.get(key, {"total": 0, "fixable": 0, "severity": {s: 0 for s in Severity}})

        if fixable and stats["fixable"] == 0:
            continue

        sev = stats["severity"]
        results.append(
            ImageResponse(
                image_name=group["image_name"],
                image_tag=group["image_tag"],
                image_digest=group["image_digest"],
                container_count=len(group["container_ids"]),
                agents=[AgentRef(id=aid, name=aname) for aid, aname in group["agents"].items()],
                total_cves=stats["total"],
                fixable_cves=stats["fixable"],
                severity_breakdown=SeverityBreakdown(
                    critical=sev.get(Severity.CRITICAL, 0),
                    high=sev.get(Severity.HIGH, 0),
                    medium=sev.get(Severity.MEDIUM, 0),
                    low=sev.get(Severity.LOW, 0),
                    unknown=sev.get(Severity.UNKNOWN, 0),
                ),
                last_scanned=group["last_scanned"],
            )
        )

    # Sort
    sort_keys = {
        "fixable_cves": lambda x: x.fixable_cves,
        "total_cves": lambda x: x.total_cves,
        "image_name": lambda x: x.image_name,
        "last_scanned": lambda x: x.last_scanned or "",
    }
    sort_fn = sort_keys.get(sort_by, sort_keys["fixable_cves"])
    results.sort(key=sort_fn, reverse=(sort_dir == "desc"))

    # Paginate
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = results[start:end]

    return PaginatedResponse(
        data=paginated,
        total=total,
        page=page,
        page_size=page_size,
    )
