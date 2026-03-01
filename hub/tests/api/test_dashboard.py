"""Tests for the dashboard summary endpoint."""

from trivyal_hub.db.models import Container, Finding, ScanResult, Severity


class TestDashboardSummary:
    async def test_returns_zeros_when_empty(self, client, auth_header):
        response = await client.get("/api/v1/dashboard/summary", headers=auth_header)
        assert response.status_code == 200
        body = response.json()
        assert body["total_findings"] == 0
        assert body["total_agents"] == 0
        assert body["severity_counts"]["critical"] == 0

    async def test_counts_agents_and_findings(self, client, auth_header, session):
        # Register an agent
        create_resp = await client.post("/api/v1/agents", json={"name": "s1"}, headers=auth_header)
        agent_id = create_resp.json()["id"]

        # Seed a finding
        container = Container(agent_id=agent_id, image_name="test:latest")
        session.add(container)
        await session.flush()
        scan = ScanResult(container_id=container.id, agent_id=agent_id)
        session.add(scan)
        await session.flush()
        finding = Finding(
            scan_result_id=scan.id,
            cve_id="CVE-2024-0001",
            package_name="openssl",
            installed_version="1.0",
            severity=Severity.HIGH,
        )
        session.add(finding)
        await session.commit()

        response = await client.get("/api/v1/dashboard/summary", headers=auth_header)
        body = response.json()
        assert body["total_agents"] == 1
        assert body["total_findings"] == 1
        assert body["severity_counts"]["high"] == 1
