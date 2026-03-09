"""Tests for the misconfig result aggregator."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from trivyal_hub.core.auth import generate_token, hash_token
from trivyal_hub.core.misconfig_aggregator import process_misconfig_result
from trivyal_hub.db.models import Agent, Container, MisconfigFinding, MisconfigStatus


async def _create_agent(session: AsyncSession) -> Agent:
    agent = Agent(
        name="test-agent",
        token_hash=hash_token(generate_token()),
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


SAMPLE_MISCONFIG_DATA = {
    "container_id": "docker-abc123",
    "container_name": "my-plex",
    "image_name": "linuxserver/plex:latest",
    "findings": [
        {
            "check_id": "PRIV_001",
            "severity": "HIGH",
            "title": "Container running in privileged mode",
            "fix_guideline": "Remove 'privileged: true' from the container definition.",
        },
        {
            "check_id": "NET_001",
            "severity": "MEDIUM",
            "title": "Container using host network mode",
            "fix_guideline": "Use a dedicated Docker network instead of 'network_mode: host'.",
        },
    ],
}


class TestProcessMisconfigResult:
    async def test_creates_container_and_findings(self, session):
        agent = await _create_agent(session)
        findings = await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)

        assert len(findings) == 2

        containers = (await session.execute(select(Container))).scalars().all()
        assert len(containers) == 1
        assert containers[0].image_name == "linuxserver/plex"
        assert containers[0].image_tag == "latest"
        assert containers[0].container_name == "my-plex"

        misconfigs = (await session.execute(select(MisconfigFinding))).scalars().all()
        assert len(misconfigs) == 2
        check_ids = {m.check_id for m in misconfigs}
        assert check_ids == {"PRIV_001", "NET_001"}

    async def test_updates_existing_finding_last_seen(self, session):
        agent = await _create_agent(session)
        first_findings = await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)
        first_last_seen = first_findings[0].last_seen

        await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)

        misconfigs = (await session.execute(select(MisconfigFinding))).scalars().all()
        assert len(misconfigs) == 2  # Not 4

        for m in misconfigs:
            assert m.last_seen >= first_last_seen

    async def test_reuses_existing_container(self, session):
        agent = await _create_agent(session)
        await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)
        await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)

        containers = (await session.execute(select(Container))).scalars().all()
        assert len(containers) == 1

    async def test_marks_absent_findings_as_fixed(self, session):
        agent = await _create_agent(session)
        await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)

        # Second scan with only NET_001 (PRIV_001 removed)
        partial_data = {
            **SAMPLE_MISCONFIG_DATA,
            "findings": [SAMPLE_MISCONFIG_DATA["findings"][1]],
        }
        await process_misconfig_result(session, agent.id, partial_data)

        misconfigs = (await session.execute(select(MisconfigFinding))).scalars().all()
        priv = next(m for m in misconfigs if m.check_id == "PRIV_001")
        net = next(m for m in misconfigs if m.check_id == "NET_001")
        assert priv.status == MisconfigStatus.FIXED
        assert net.status == MisconfigStatus.ACTIVE

    async def test_empty_findings_marks_all_fixed(self, session):
        agent = await _create_agent(session)
        await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)

        empty_data = {**SAMPLE_MISCONFIG_DATA, "findings": []}
        await process_misconfig_result(session, agent.id, empty_data)

        misconfigs = (await session.execute(select(MisconfigFinding))).scalars().all()
        assert all(m.status == MisconfigStatus.FIXED for m in misconfigs)

    async def test_no_duplicate_when_finding_is_accepted(self, session):
        """Regression: accepted finding + new scan should not create a duplicate ACTIVE row."""
        agent = await _create_agent(session)
        await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)

        # Simulate user accepting one finding
        net = (
            await session.execute(select(MisconfigFinding).where(MisconfigFinding.check_id == "NET_001"))
        ).scalar_one()
        net.status = MisconfigStatus.ACCEPTED
        session.add(net)
        await session.commit()

        # Next scan with same findings — must not create a new ACTIVE NET_001
        await process_misconfig_result(session, agent.id, SAMPLE_MISCONFIG_DATA)

        all_misconfigs = (await session.execute(select(MisconfigFinding))).scalars().all()
        net_findings = [m for m in all_misconfigs if m.check_id == "NET_001"]
        assert len(net_findings) == 1
        assert net_findings[0].status == MisconfigStatus.ACCEPTED

    async def test_handles_image_name_without_tag(self, session):
        agent = await _create_agent(session)
        data = {
            **SAMPLE_MISCONFIG_DATA,
            "image_name": "nginx",
        }
        await process_misconfig_result(session, agent.id, data)

        containers = (await session.execute(select(Container))).scalars().all()
        assert containers[0].image_name == "nginx"
        assert containers[0].image_tag is None
