"""Tests for expire_stale_acceptances."""

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from trivyal_hub.core.acceptance_expiry import expire_stale_acceptances
from trivyal_hub.db.models import (
    Agent,
    Container,
    Finding,
    FindingStatus,
    MisconfigFinding,
    MisconfigStatus,
    RiskAcceptance,
    ScanResult,
    Severity,
    _now,
)


async def _seed_finding(session: AsyncSession) -> Finding:
    agent = Agent(name="agent-finding", token_hash="hash")
    session.add(agent)
    await session.flush()

    container = Container(agent_id=agent.id, image_name="test:latest")
    session.add(container)
    await session.flush()

    scan = ScanResult(container_id=container.id, agent_id=agent.id)
    session.add(scan)
    await session.flush()

    finding = Finding(
        scan_result_id=scan.id,
        cve_id="CVE-2024-0001",
        package_name="openssl",
        installed_version="1.1.1",
        severity=Severity.CRITICAL,
        status=FindingStatus.ACCEPTED,
    )
    session.add(finding)
    await session.commit()
    await session.refresh(finding)
    return finding


async def _seed_misconfig(session: AsyncSession) -> MisconfigFinding:
    agent = Agent(name="agent-misconfig", token_hash="hash")
    session.add(agent)
    await session.flush()

    container = Container(agent_id=agent.id, image_name="test:latest")
    session.add(container)
    await session.flush()

    misconfig = MisconfigFinding(
        container_id=container.id,
        check_id="AVD-DS-001",
        severity=Severity.HIGH,
        title="Test misconfig",
        fix_guideline="Fix it",
        status=MisconfigStatus.ACCEPTED,
    )
    session.add(misconfig)
    await session.commit()
    await session.refresh(misconfig)
    return misconfig


class TestExpireStaleAcceptances:
    async def test_no_acceptances(self, session: AsyncSession):
        count = await expire_stale_acceptances(session)
        assert count == 0

    async def test_permanent_acceptance_unchanged(self, session: AsyncSession):
        finding = await _seed_finding(session)
        session.add(RiskAcceptance(finding_id=finding.id, reason="permanent", expires_at=None))
        await session.commit()

        count = await expire_stale_acceptances(session)

        assert count == 0
        await session.refresh(finding)
        assert finding.status == FindingStatus.ACCEPTED

    async def test_future_acceptance_unchanged(self, session: AsyncSession):
        finding = await _seed_finding(session)
        session.add(RiskAcceptance(finding_id=finding.id, reason="future", expires_at=_now() + timedelta(hours=1)))
        await session.commit()

        count = await expire_stale_acceptances(session)

        assert count == 0
        await session.refresh(finding)
        assert finding.status == FindingStatus.ACCEPTED

    async def test_expired_finding_acceptance_reverts_to_active(self, session: AsyncSession):
        finding = await _seed_finding(session)
        acceptance = RiskAcceptance(finding_id=finding.id, reason="expired", expires_at=_now() - timedelta(hours=1))
        session.add(acceptance)
        await session.commit()
        acceptance_id = acceptance.id

        count = await expire_stale_acceptances(session)

        assert count == 1
        await session.refresh(finding)
        assert finding.status == FindingStatus.ACTIVE
        assert await session.get(RiskAcceptance, acceptance_id) is None

    async def test_expired_misconfig_acceptance_reverts_to_active(self, session: AsyncSession):
        misconfig = await _seed_misconfig(session)
        acceptance = RiskAcceptance(
            misconfig_finding_id=misconfig.id, reason="expired", expires_at=_now() - timedelta(hours=1)
        )
        session.add(acceptance)
        await session.commit()
        acceptance_id = acceptance.id

        count = await expire_stale_acceptances(session)

        assert count == 1
        await session.refresh(misconfig)
        assert misconfig.status == MisconfigStatus.ACTIVE
        assert await session.get(RiskAcceptance, acceptance_id) is None

    async def test_multiple_expired_acceptances(self, session: AsyncSession):
        finding = await _seed_finding(session)
        misconfig = await _seed_misconfig(session)
        session.add(RiskAcceptance(finding_id=finding.id, reason="r1", expires_at=_now() - timedelta(hours=1)))
        session.add(
            RiskAcceptance(misconfig_finding_id=misconfig.id, reason="r2", expires_at=_now() - timedelta(hours=1))
        )
        await session.commit()

        count = await expire_stale_acceptances(session)

        assert count == 2
        await session.refresh(finding)
        await session.refresh(misconfig)
        assert finding.status == FindingStatus.ACTIVE
        assert misconfig.status == MisconfigStatus.ACTIVE

    async def test_mixed_expired_and_valid_acceptances(self, session: AsyncSession):
        finding = await _seed_finding(session)
        session.add(RiskAcceptance(finding_id=finding.id, reason="expired", expires_at=_now() - timedelta(hours=1)))

        misconfig = await _seed_misconfig(session)
        session.add(
            RiskAcceptance(misconfig_finding_id=misconfig.id, reason="valid", expires_at=_now() + timedelta(hours=1))
        )
        await session.commit()

        count = await expire_stale_acceptances(session)

        assert count == 1
        await session.refresh(finding)
        await session.refresh(misconfig)
        assert finding.status == FindingStatus.ACTIVE
        assert misconfig.status == MisconfigStatus.ACCEPTED
