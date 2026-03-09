"""Processes incoming scan results from agents."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.db.models import (
    Container,
    Finding,
    FindingStatus,
    ScanResult,
    Severity,
    _now,
)


async def process_scan_result(
    session: AsyncSession,
    agent_id: str,
    scan_data: dict,
    container_name: str | None = None,
) -> ScanResult:
    """Ingest a Trivy scan result: upsert containers, create scan record, upsert findings."""
    now = _now()

    raw_image_name = scan_data.get("ArtifactName", "unknown")
    if ":" in raw_image_name:
        image_name, image_tag = raw_image_name.rsplit(":", 1)
    else:
        image_name, image_tag = raw_image_name, None
    image_digest = scan_data.get("Metadata", {}).get("RepoDigests", [None])[0] if scan_data.get("Metadata") else None

    # Get or create container — SELECT first (handles NULL container_name correctly
    # via IS NULL), then INSERT only if not found. SQLite's on_conflict_do_nothing
    # cannot be used here because NULL != NULL in UNIQUE indexes, so a NULL
    # container_name would bypass the conflict check and create duplicate rows.
    container = (
        await session.execute(
            select(Container).where(
                Container.agent_id == agent_id,
                Container.container_name == container_name,
                Container.image_name == image_name,
            )
        )
    ).scalar_one_or_none()
    if container is None:
        container = Container(
            agent_id=agent_id,
            image_name=image_name,
            image_tag=image_tag,
            image_digest=image_digest,
            container_name=container_name,
        )
        session.add(container)
        await session.flush()
    container.last_scanned = now
    container.image_tag = image_tag
    container.image_digest = image_digest or container.image_digest

    # Create scan result
    severity_counts = {s: 0 for s in Severity}
    trivy_results = scan_data.get("Results", [])

    findings: list[Finding] = []
    for result_block in trivy_results:
        for vuln in result_block.get("Vulnerabilities", []):
            sev = vuln.get("Severity", "UNKNOWN").upper()
            if sev not in Severity.__members__:
                sev = "UNKNOWN"
            severity_counts[Severity(sev)] += 1
            findings.append(
                Finding(
                    cve_id=vuln.get("VulnerabilityID", "UNKNOWN"),
                    package_name=vuln.get("PkgName", "unknown"),
                    installed_version=vuln.get("InstalledVersion", "unknown"),
                    fixed_version=vuln.get("FixedVersion"),
                    severity=Severity(sev),
                    description=vuln.get("Description") or None,
                    first_seen=now,
                    last_seen=now,
                )
            )

    scan_result = ScanResult(
        container_id=container.id,
        agent_id=agent_id,
        scanned_at=now,
        trivy_raw=scan_data,
        critical_count=severity_counts[Severity.CRITICAL],
        high_count=severity_counts[Severity.HIGH],
        medium_count=severity_counts[Severity.MEDIUM],
        low_count=severity_counts[Severity.LOW],
        unknown_count=severity_counts[Severity.UNKNOWN],
    )
    session.add(scan_result)
    await session.flush()

    # Attach findings to the scan result
    current_keys: set[tuple[str, str]] = set()
    for finding in findings:
        finding.scan_result_id = scan_result.id
        current_keys.add((finding.cve_id, finding.package_name))
        # Check for existing active finding with the same CVE+package on this container
        existing_stmt = (
            select(Finding)
            .join(ScanResult)
            .where(
                ScanResult.container_id == container.id,
                Finding.cve_id == finding.cve_id,
                Finding.package_name == finding.package_name,
                Finding.status == FindingStatus.ACTIVE,
            )
        )
        existing = (await session.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            existing.last_seen = now
            existing.scan_result_id = scan_result.id
            if finding.description:
                existing.description = finding.description
            session.add(existing)
        else:
            session.add(finding)

    # Mark previously active findings absent from this scan as fixed
    all_active_stmt = (
        select(Finding)
        .join(ScanResult)
        .where(
            ScanResult.container_id == container.id,
            Finding.status == FindingStatus.ACTIVE,
        )
    )
    all_active = (await session.execute(all_active_stmt)).scalars().all()
    for active in all_active:
        if (active.cve_id, active.package_name) not in current_keys:
            active.status = FindingStatus.FIXED
            active.last_seen = now
            session.add(active)

    await session.commit()
    await session.refresh(scan_result)
    return scan_result
