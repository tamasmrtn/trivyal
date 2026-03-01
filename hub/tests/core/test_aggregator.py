"""Tests for the scan result aggregator."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from trivyal_hub.core.aggregator import process_scan_result
from trivyal_hub.db.models import Agent, Container, Finding, ScanResult
from trivyal_hub.core.auth import generate_keypair, generate_token, hash_token


async def _create_agent(session: AsyncSession) -> Agent:
    pub, priv = generate_keypair()
    agent = Agent(
        name="test-agent",
        token_hash=hash_token(generate_token()),
        public_key=pub,
        private_key=priv,
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
        assert containers[0].image_name == "nginx:latest"

        findings = (await session.execute(select(Finding))).scalars().all()
        assert len(findings) == 2

    async def test_reuses_existing_container(self, session):
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT)

        containers = (await session.execute(select(Container))).scalars().all()
        assert len(containers) == 1

    async def test_updates_existing_finding_last_seen(self, session):
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT)
        scan2 = await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT)

        findings = (await session.execute(select(Finding))).scalars().all()
        # Should still have 2 findings (not 4), existing ones get updated
        assert len(findings) == 2
