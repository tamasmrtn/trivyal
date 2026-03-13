"""Expiry enforcement for time-limited risk acceptances."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.db.models import (
    Finding,
    FindingStatus,
    MisconfigFinding,
    MisconfigStatus,
    RiskAcceptance,
    _now,
)


async def expire_stale_acceptances(session: AsyncSession) -> int:
    """Revert findings whose risk acceptance has passed its expiry date.

    Mirrors the revoke-acceptance API: finding status → ACTIVE, acceptance row deleted.
    Returns the number of acceptances expired.
    """
    now = _now()
    stmt = select(RiskAcceptance).where(
        RiskAcceptance.expires_at.isnot(None),
        RiskAcceptance.expires_at < now,
    )
    expired = (await session.execute(stmt)).scalars().all()

    for acceptance in expired:
        if acceptance.finding_id:
            finding = await session.get(Finding, acceptance.finding_id)
            if finding:
                finding.status = FindingStatus.ACTIVE
                session.add(finding)
        elif acceptance.misconfig_finding_id:
            misconfig = await session.get(MisconfigFinding, acceptance.misconfig_finding_id)
            if misconfig:
                misconfig.status = MisconfigStatus.ACTIVE
                session.add(misconfig)
        await session.delete(acceptance)

    if expired:
        await session.commit()

    return len(expired)
