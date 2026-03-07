"""Tests for core/misconfig_runner.py."""

from unittest.mock import MagicMock, patch

from trivyal_agent.core.misconfig_runner import _check_container, run_misconfig_checks


def _make_container(host_config=None, tags=None, name="test-container", container_id="abc123"):
    mock = MagicMock()
    mock.attrs = {"HostConfig": host_config or {}}
    mock.name = name
    mock.id = container_id
    mock_image = MagicMock()
    mock_image.tags = tags or ["test:latest"]
    mock_image.id = "sha256:abc"
    mock.image = mock_image
    return mock


class TestCheckContainer:
    def test_detects_privileged_mode(self):
        container = _make_container(host_config={"Privileged": True})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "PRIV_001" in check_ids
        priv = next(f for f in findings if f["check_id"] == "PRIV_001")
        assert priv["severity"] == "HIGH"

    def test_detects_dangerous_capabilities(self):
        container = _make_container(host_config={"CapAdd": ["SYS_ADMIN", "NET_RAW"]})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "CAP_001" in check_ids
        cap = next(f for f in findings if f["check_id"] == "CAP_001")
        assert "SYS_ADMIN" in cap["fix_guideline"]

    def test_detects_all_capability(self):
        container = _make_container(host_config={"CapAdd": ["ALL"]})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "CAP_001" in check_ids

    def test_ignores_safe_capabilities(self):
        container = _make_container(host_config={"CapAdd": ["NET_RAW", "CHOWN"]})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "CAP_001" not in check_ids

    def test_detects_host_network(self):
        container = _make_container(host_config={"NetworkMode": "host"})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "NET_001" in check_ids
        net = next(f for f in findings if f["check_id"] == "NET_001")
        assert net["severity"] == "MEDIUM"

    def test_ignores_bridge_network(self):
        container = _make_container(host_config={"NetworkMode": "bridge"})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "NET_001" not in check_ids

    def test_detects_missing_no_new_privileges(self):
        container = _make_container(host_config={})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "PRIV_002" in check_ids

    def test_no_priv002_when_no_new_privileges_set(self):
        container = _make_container(host_config={"SecurityOpt": ["no-new-privileges:true"]})
        findings = _check_container(container)
        check_ids = [f["check_id"] for f in findings]
        assert "PRIV_002" not in check_ids

    def test_clean_container_only_has_priv002(self):
        container = _make_container(host_config={"Privileged": False, "NetworkMode": "bridge"})
        findings = _check_container(container)
        # Only PRIV_002 (missing no-new-privileges)
        assert len(findings) == 1
        assert findings[0]["check_id"] == "PRIV_002"

    def test_fully_secure_container_has_no_findings(self):
        container = _make_container(
            host_config={
                "Privileged": False,
                "NetworkMode": "bridge",
                "SecurityOpt": ["no-new-privileges:true"],
            }
        )
        findings = _check_container(container)
        assert findings == []

    def test_multiple_issues_detected(self):
        container = _make_container(
            host_config={
                "Privileged": True,
                "CapAdd": ["SYS_ADMIN"],
                "NetworkMode": "host",
            }
        )
        findings = _check_container(container)
        check_ids = {f["check_id"] for f in findings}
        assert check_ids == {"PRIV_001", "CAP_001", "NET_001", "PRIV_002"}


class TestRunMisconfigChecks:
    async def test_returns_results_for_misconfigured_containers(self):
        mock_container = _make_container(
            host_config={"Privileged": True},
            tags=["nginx:latest"],
            name="my-nginx",
            container_id="abc123",
        )
        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]

        with patch("trivyal_agent.core.misconfig_runner.docker") as mock_docker:
            mock_docker.from_env.return_value = mock_client
            results = await run_misconfig_checks()

        assert len(results) == 1
        assert results[0]["container_id"] == "abc123"
        assert results[0]["container_name"] == "my-nginx"
        assert results[0]["image_name"] == "nginx:latest"
        assert any(f["check_id"] == "PRIV_001" for f in results[0]["findings"])

    async def test_skips_clean_containers_with_no_new_privs(self):
        mock_container = _make_container(
            host_config={
                "Privileged": False,
                "NetworkMode": "bridge",
                "SecurityOpt": ["no-new-privileges:true"],
            },
            tags=["nginx:latest"],
        )
        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]

        with patch("trivyal_agent.core.misconfig_runner.docker") as mock_docker:
            mock_docker.from_env.return_value = mock_client
            results = await run_misconfig_checks()

        assert results == []

    async def test_returns_empty_for_no_containers(self):
        mock_client = MagicMock()
        mock_client.containers.list.return_value = []

        with patch("trivyal_agent.core.misconfig_runner.docker") as mock_docker:
            mock_docker.from_env.return_value = mock_client
            results = await run_misconfig_checks()

        assert results == []
