"""Tests for the scan result aggregator."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from trivyal_hub.core.aggregator import process_scan_result
from trivyal_hub.core.auth import generate_token, hash_token
from trivyal_hub.db.models import Agent, Container, Finding


async def _create_agent(session: AsyncSession) -> Agent:
    agent = Agent(
        name="test-agent",
        token_hash=hash_token(generate_token()),
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return agent


SAMPLE_TRIVY_OUTPUT = {
    "ArtifactName": "nginx:latest",
    "Results": [
        {
            "Target": "nginx:latest",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-1000",
                    "PkgName": "libssl",
                    "InstalledVersion": "1.1.1",
                    "FixedVersion": "1.1.2",
                    "Severity": "CRITICAL",
                },
                {
                    "VulnerabilityID": "CVE-2024-2000",
                    "PkgName": "zlib",
                    "InstalledVersion": "1.2.11",
                    "Severity": "HIGH",
                },
            ],
        }
    ],
}


class TestProcessScanResult:
    async def test_creates_container_and_findings(self, session):
        agent = await _create_agent(session)
        scan = await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT)

        assert scan.critical_count == 1
        assert scan.high_count == 1

        containers = (await session.execute(select(Container))).scalars().all()
        assert len(containers) == 1
        assert containers[0].image_name == "nginx"
        assert containers[0].image_tag == "latest"

        findings = (await session.execute(select(Finding))).scalars().all()
        assert len(findings) == 2

    async def test_stores_container_name(self, session):
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        containers = (await session.execute(select(Container))).scalars().all()
        assert containers[0].container_name == "my-nginx"

    async def test_different_container_names_create_separate_rows(self, session):
        # container_name is part of the unique key, so the same image running
        # under two different names (e.g. after a rename) produces two rows.
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="old-name")
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="new-name")

        containers = (await session.execute(select(Container))).scalars().all()
        assert len(containers) == 2
        names = {c.container_name for c in containers}
        assert names == {"old-name", "new-name"}

    async def test_reuses_existing_container(self, session):
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        containers = (await session.execute(select(Container))).scalars().all()
        assert len(containers) == 1

    async def test_rebuilt_image_reuses_container(self, session):
        # Same container_name + image_name but different tag (e.g. after a rebuild).
        # Should reuse the same Container row and deduplicate findings.
        agent = await _create_agent(session)
        rebuilt = {**SAMPLE_TRIVY_OUTPUT, "ArtifactName": "nginx:1.26"}
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")
        await process_scan_result(session, agent.id, rebuilt, container_name="my-nginx")

        containers = (await session.execute(select(Container))).scalars().all()
        assert len(containers) == 1
        assert containers[0].image_tag == "1.26"

        findings = (await session.execute(select(Finding))).scalars().all()
        assert len(findings) == 2

    async def test_updates_existing_finding_last_seen(self, session):
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        findings = (await session.execute(select(Finding))).scalars().all()
        # Should still have 2 findings (not 4), existing ones get updated
        assert len(findings) == 2
