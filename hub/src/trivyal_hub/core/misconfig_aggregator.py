"""Processes incoming misconfig results from agents."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.db.models import (
    Container,
    MisconfigFinding,
    MisconfigStatus,
    Severity,
    _now,
)


async def process_misconfig_result(
    session: AsyncSession,
    agent_id: str,
    data: dict,
) -> list[MisconfigFinding]:
    """Ingest a misconfig_result message: upsert container, upsert misconfig findings."""
    now = _now()

    image_name = data.get("image_name", "unknown")
    container_name = data.get("container_name")
    raw_findings = data.get("findings", [])

    # Split image_name into name and tag
    if ":" in image_name:
        name_part, tag_part = image_name.rsplit(":", 1)
    else:
        name_part = image_name
        tag_part = None

    # Get or create container — SELECT first (handles NULL container_name correctly
    # via IS NULL), then INSERT only if not found.
    container = (
        await session.execute(
            select(Container).where(
                Container.agent_id == agent_id,
                Container.image_name == name_part,
                Container.image_tag == tag_part,
                Container.container_name == container_name,
            )
        )
    ).scalar_one_or_none()
    if container is None:
        container = Container(
            agent_id=agent_id,
            image_name=name_part,
            image_tag=tag_part,
            container_name=container_name,
        )
        session.add(container)
        await session.flush()

    # Track which check_ids are present in this scan
    current_check_ids: set[str] = set()
    created_or_updated: list[MisconfigFinding] = []

    for finding_data in raw_findings:
        check_id = finding_data.get("check_id", "")
        sev = finding_data.get("severity", "MEDIUM").upper()
        if sev not in Severity.__members__:
            sev = "MEDIUM"
        current_check_ids.add(check_id)

        # Look for any non-fixed finding with same (container_id, check_id).
        # Checking only ACTIVE would create duplicates when a finding is ACCEPTED.
        existing_stmt = select(MisconfigFinding).where(
            MisconfigFinding.container_id == container.id,
            MisconfigFinding.check_id == check_id,
            MisconfigFinding.status != MisconfigStatus.FIXED,
        )
        existing = (await session.execute(existing_stmt)).scalar_one_or_none()

        if existing:
            existing.last_seen = now
            session.add(existing)
            created_or_updated.append(existing)
        else:
            new_finding = MisconfigFinding(
                container_id=container.id,
                check_id=check_id,
                severity=Severity(sev),
                title=finding_data.get("title", ""),
                fix_guideline=finding_data.get("fix_guideline", ""),
                first_seen=now,
                last_seen=now,
            )
            session.add(new_finding)
            created_or_updated.append(new_finding)

    # Mark previously active findings absent from this scan as fixed
    all_active_stmt = select(MisconfigFinding).where(
        MisconfigFinding.container_id == container.id,
        MisconfigFinding.status == MisconfigStatus.ACTIVE,
    )
    all_active = (await session.execute(all_active_stmt)).scalars().all()
    for active in all_active:
        if active.check_id not in current_check_ids:
            active.status = MisconfigStatus.FIXED
            active.last_seen = now
            session.add(active)

    await session.commit()
    for f in created_or_updated:
        await session.refresh(f)
    return created_or_updated
