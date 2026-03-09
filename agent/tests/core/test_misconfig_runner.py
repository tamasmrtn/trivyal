"""Tests for core/misconfig_runner.py."""

from unittest.mock import patch

from trivyal_agent.core import misconfig_runner as _module
from trivyal_agent.core.misconfig_runner import _check_container, run_misconfig_checks


def _inspect(host_config=None, container_id="abc123"):
    """Build a minimal container inspect dict (mirrors GET /containers/{id}/json)."""
    return {"Id": container_id, "HostConfig": host_config or {}}


def _summary(container_id="abc123", image="test:latest", name="test-container"):
    """Build a minimal container list entry (mirrors GET /containers/json)."""
    return {"Id": container_id, "Image": image, "Names": [f"/{name}"]}


class TestCheckContainer:
    def test_detects_privileged_mode(self):
        findings = _check_container(_inspect(host_config={"Privileged": True}))
        check_ids = [f["check_id"] for f in findings]
        assert "PRIV_001" in check_ids
        priv = next(f for f in findings if f["check_id"] == "PRIV_001")
        assert priv["severity"] == "HIGH"

    def test_detects_dangerous_capabilities(self):
        findings = _check_container(_inspect(host_config={"CapAdd": ["SYS_ADMIN", "NET_RAW"]}))
        check_ids = [f["check_id"] for f in findings]
        assert "CAP_001" in check_ids
        cap = next(f for f in findings if f["check_id"] == "CAP_001")
        assert "SYS_ADMIN" in cap["fix_guideline"]

    def test_detects_all_capability(self):
        findings = _check_container(_inspect(host_config={"CapAdd": ["ALL"]}))
        assert "CAP_001" in [f["check_id"] for f in findings]

    def test_ignores_safe_capabilities(self):
        findings = _check_container(_inspect(host_config={"CapAdd": ["NET_RAW", "CHOWN"]}))
        assert "CAP_001" not in [f["check_id"] for f in findings]

    def test_detects_host_network(self):
        findings = _check_container(_inspect(host_config={"NetworkMode": "host"}))
        check_ids = [f["check_id"] for f in findings]
        assert "NET_001" in check_ids
        net = next(f for f in findings if f["check_id"] == "NET_001")
        assert net["severity"] == "MEDIUM"

    def test_ignores_bridge_network(self):
        findings = _check_container(_inspect(host_config={"NetworkMode": "bridge"}))
        assert "NET_001" not in [f["check_id"] for f in findings]

    def test_detects_missing_no_new_privileges(self):
        findings = _check_container(_inspect(host_config={}))
        assert "PRIV_002" in [f["check_id"] for f in findings]

    def test_no_priv002_when_no_new_privileges_set(self):
        findings = _check_container(_inspect(host_config={"SecurityOpt": ["no-new-privileges:true"]}))
        assert "PRIV_002" not in [f["check_id"] for f in findings]

    def test_clean_container_only_has_priv002(self):
        findings = _check_container(_inspect(host_config={"Privileged": False, "NetworkMode": "bridge"}))
        assert len(findings) == 1
        assert findings[0]["check_id"] == "PRIV_002"

    def test_fully_secure_container_has_no_findings(self):
        findings = _check_container(
            _inspect(
                host_config={
                    "Privileged": False,
                    "NetworkMode": "bridge",
                    "SecurityOpt": ["no-new-privileges:true"],
                }
            )
        )
        assert findings == []

    def test_multiple_issues_detected(self):
        findings = _check_container(
            _inspect(
                host_config={
                    "Privileged": True,
                    "CapAdd": ["SYS_ADMIN"],
                    "NetworkMode": "host",
                }
            )
        )
        assert {f["check_id"] for f in findings} == {"PRIV_001", "CAP_001", "NET_001", "PRIV_002"}


class TestRunMisconfigChecks:
    async def test_returns_results_for_misconfigured_containers(self):
        summary = _summary(container_id="abc123", image="nginx:latest", name="my-nginx")
        full = _inspect(host_config={"Privileged": True}, container_id="abc123")

        with (
            patch.object(_module._docker, "containers", return_value=[summary]),
            patch.object(_module._docker, "container_inspect", return_value=full),
        ):
            results = await run_misconfig_checks()

        assert len(results) == 1
        assert results[0]["container_id"] == "abc123"
        assert results[0]["container_name"] == "my-nginx"
        assert results[0]["image_name"] == "nginx:latest"
        assert any(f["check_id"] == "PRIV_001" for f in results[0]["findings"])

    async def test_skips_clean_containers_with_no_new_privs(self):
        summary = _summary(image="nginx:latest")
        full = _inspect(
            host_config={
                "Privileged": False,
                "NetworkMode": "bridge",
                "SecurityOpt": ["no-new-privileges:true"],
            }
        )

        with (
            patch.object(_module._docker, "containers", return_value=[summary]),
            patch.object(_module._docker, "container_inspect", return_value=full),
        ):
            results = await run_misconfig_checks()

        assert results == []

    async def test_returns_empty_for_no_containers(self):
        with patch.object(_module._docker, "containers", return_value=[]):
            results = await run_misconfig_checks()
        assert results == []

    async def test_calls_inspect_per_container(self):
        """Verifies that full inspect (not list attrs) is used for HostConfig checks."""
        summary = _summary(container_id="abc123")
        # inspect returns Privileged=True; the list summary has no HostConfig
        full = _inspect(host_config={"Privileged": True}, container_id="abc123")

        with (
            patch.object(_module._docker, "containers", return_value=[summary]),
            patch.object(_module._docker, "container_inspect", return_value=full) as mock_inspect,
        ):
            results = await run_misconfig_checks()

        mock_inspect.assert_called_once_with("abc123")
        assert any(f["check_id"] == "PRIV_001" for f in results[0]["findings"])
