"""Tests for the scan result aggregator."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from trivyal_hub.core.aggregator import process_scan_result
from trivyal_hub.core.auth import generate_token, hash_token
from trivyal_hub.db.models import Agent, Container, Finding, FindingStatus


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

    async def test_marks_absent_finding_as_fixed(self, session):
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        # Second scan with only CVE-2024-1000/libssl (CVE-2024-2000/zlib removed)
        partial_output = {
            **SAMPLE_TRIVY_OUTPUT,
            "Results": [
                {
                    "Target": "nginx:latest",
                    "Vulnerabilities": [SAMPLE_TRIVY_OUTPUT["Results"][0]["Vulnerabilities"][0]],
                }
            ],
        }
        await process_scan_result(session, agent.id, partial_output, container_name="my-nginx")

        findings = (await session.execute(select(Finding))).scalars().all()
        libssl = next(f for f in findings if f.package_name == "libssl")
        zlib = next(f for f in findings if f.package_name == "zlib")
        assert libssl.status == FindingStatus.ACTIVE
        assert zlib.status == FindingStatus.FIXED

    async def test_empty_scan_marks_all_findings_fixed(self, session):
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        empty_output = {**SAMPLE_TRIVY_OUTPUT, "Results": []}
        await process_scan_result(session, agent.id, empty_output, container_name="my-nginx")

        findings = (await session.execute(select(Finding))).scalars().all()
        assert all(f.status == FindingStatus.FIXED for f in findings)

    async def test_does_not_fix_accepted_findings(self, session):
        """User-accepted findings must not be auto-reset to FIXED by reconciliation."""
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        # User accepts the zlib finding
        zlib = (await session.execute(select(Finding).where(Finding.package_name == "zlib"))).scalar_one()
        zlib.status = FindingStatus.ACCEPTED
        session.add(zlib)
        await session.commit()

        # Next scan still includes zlib — ACCEPTED status must be preserved
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        await session.refresh(zlib)
        assert zlib.status == FindingStatus.ACCEPTED

    async def test_fixed_finding_does_not_resurface_as_active(self, session):
        """A finding that was FIXED must not prevent a new ACTIVE row if it reappears."""
        agent = await _create_agent(session)
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        # Scan 2: zlib disappears → FIXED
        partial_output = {
            **SAMPLE_TRIVY_OUTPUT,
            "Results": [
                {
                    "Target": "nginx:latest",
                    "Vulnerabilities": [SAMPLE_TRIVY_OUTPUT["Results"][0]["Vulnerabilities"][0]],
                }
            ],
        }
        await process_scan_result(session, agent.id, partial_output, container_name="my-nginx")

        # Scan 3: zlib reappears → new ACTIVE finding
        await process_scan_result(session, agent.id, SAMPLE_TRIVY_OUTPUT, container_name="my-nginx")

        zlib_findings = (await session.execute(select(Finding).where(Finding.package_name == "zlib"))).scalars().all()
        active = [f for f in zlib_findings if f.status == FindingStatus.ACTIVE]
        fixed = [f for f in zlib_findings if f.status == FindingStatus.FIXED]
        assert len(active) == 1
        assert len(fixed) == 1
