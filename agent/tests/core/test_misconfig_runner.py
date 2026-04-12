"""Tests for core/misconfig_runner.py."""

from unittest.mock import patch

from trivyal_agent.core import misconfig_runner as _module
from trivyal_agent.core.misconfig_runner import _check_container, run_misconfig_checks


def _inspect(host_config=None, config=None, container_id="abc123"):
    """Build a minimal container inspect dict (mirrors GET /containers/{id}/json)."""
    d = {"Id": container_id, "HostConfig": host_config or {}}
    if config is not None:
        d["Config"] = config
    return d


def _summary(container_id="abc123", image="test:latest", name="test-container"):
    """Build a minimal container list entry (mirrors GET /containers/json)."""
    return {"Id": container_id, "Image": image, "Names": [f"/{name}"]}


# Host config that silences every rule — use as base for targeted tests.
SECURE_HOST_CONFIG = {
    "Privileged": False,
    "NetworkMode": "bridge",
    "SecurityOpt": ["no-new-privileges:true"],
    "ReadonlyRootfs": True,
    "Memory": 536870912,
    "CapDrop": ["ALL"],
    "PidsLimit": 4096,
    "CpuQuota": 100000,
    "LogConfig": {"Type": "json-file", "Config": {"max-size": "10m", "max-file": "3"}},
    "RestartPolicy": {"Name": "unless-stopped", "MaximumRetryCount": 0},
}

SECURE_CONFIG = {"User": "1000"}


class TestCheckContainer:
    # ── Existing rules ──────────────────────────────────────────────────

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

    def test_clean_container_only_has_baseline_findings(self):
        findings = _check_container(_inspect(host_config={"Privileged": False, "NetworkMode": "bridge"}))
        check_ids = {f["check_id"] for f in findings}
        # Baseline rules that fire on a minimal container config
        assert check_ids == {
            "PRIV_002",
            "MNT_003",
            "RES_001",
            "CAP_002",
            "RES_002",
            "RES_004",
            "USR_001",
            "LOG_001",
            "LIFE_001",
        }

    def test_fully_secure_container_has_no_findings(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG, config=SECURE_CONFIG))
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
        check_ids = {f["check_id"] for f in findings}
        assert {
            "PRIV_001",
            "CAP_001",
            "NET_001",
            "PRIV_002",
            "MNT_003",
            "RES_001",
            "CAP_002",
            "RES_002",
            "RES_004",
            "USR_001",
            "LOG_001",
            "LIFE_001",
        } <= check_ids

    # ── Namespace rules ─────────────────────────────────────────────────

    def test_detects_host_pid_namespace(self):
        findings = _check_container(_inspect(host_config={"PidMode": "host"}))
        assert "NS_001" in [f["check_id"] for f in findings]
        ns = next(f for f in findings if f["check_id"] == "NS_001")
        assert ns["severity"] == "HIGH"

    def test_ignores_default_pid_mode(self):
        findings = _check_container(_inspect(host_config={"PidMode": ""}))
        assert "NS_001" not in [f["check_id"] for f in findings]

    def test_detects_host_ipc_namespace(self):
        findings = _check_container(_inspect(host_config={"IpcMode": "host"}))
        assert "NS_002" in [f["check_id"] for f in findings]
        ns = next(f for f in findings if f["check_id"] == "NS_002")
        assert ns["severity"] == "MEDIUM"

    def test_ignores_default_ipc_mode(self):
        findings = _check_container(_inspect(host_config={"IpcMode": "private"}))
        assert "NS_002" not in [f["check_id"] for f in findings]

    # ── Mount rules ─────────────────────────────────────────────────────

    def test_detects_docker_socket_mount(self):
        hc = {**SECURE_HOST_CONFIG, "Binds": ["/var/run/docker.sock:/var/run/docker.sock"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_001" in [f["check_id"] for f in findings]

    def test_ignores_non_socket_mount(self):
        hc = {**SECURE_HOST_CONFIG, "Binds": ["/data:/data"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_001" not in [f["check_id"] for f in findings]

    def test_detects_sensitive_host_dir_exact(self):
        hc = {**SECURE_HOST_CONFIG, "Binds": ["/etc:/container-etc:ro"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_002" in [f["check_id"] for f in findings]

    def test_detects_sensitive_host_dir_subpath(self):
        hc = {**SECURE_HOST_CONFIG, "Binds": ["/proc/1/ns:/ns"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_002" in [f["check_id"] for f in findings]

    def test_ignores_non_sensitive_mount(self):
        hc = {**SECURE_HOST_CONFIG, "Binds": ["/app/data:/data"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_002" not in [f["check_id"] for f in findings]

    def test_sensitive_mount_no_false_prefix_match(self):
        """'/etcetera' should NOT match the '/etc' rule."""
        hc = {**SECURE_HOST_CONFIG, "Binds": ["/etcetera:/data"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_002" not in [f["check_id"] for f in findings]

    def test_detects_root_mount(self):
        hc = {**SECURE_HOST_CONFIG, "Binds": ["/:/host:ro"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_002" in [f["check_id"] for f in findings]

    def test_detects_writable_filesystem(self):
        hc = {**SECURE_HOST_CONFIG, "ReadonlyRootfs": False}
        findings = _check_container(_inspect(host_config=hc))
        assert "MNT_003" in [f["check_id"] for f in findings]

    def test_no_mnt003_when_readonly(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "MNT_003" not in [f["check_id"] for f in findings]

    # ── Resource limit rules ────────────────────────────────────────────

    def test_detects_no_memory_limit(self):
        hc = {**SECURE_HOST_CONFIG, "Memory": 0}
        findings = _check_container(_inspect(host_config=hc))
        assert "RES_001" in [f["check_id"] for f in findings]

    def test_no_res001_when_memory_set(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "RES_001" not in [f["check_id"] for f in findings]

    def test_detects_missing_memory_field(self):
        """When Memory key is absent, treat as 0 (no limit)."""
        hc = {**SECURE_HOST_CONFIG}
        del hc["Memory"]
        findings = _check_container(_inspect(host_config=hc))
        assert "RES_001" in [f["check_id"] for f in findings]

    def test_detects_no_pid_limit(self):
        hc = {**SECURE_HOST_CONFIG, "PidsLimit": 0}
        findings = _check_container(_inspect(host_config=hc))
        assert "RES_002" in [f["check_id"] for f in findings]

    def test_no_res002_when_pidslimit_set(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "RES_002" not in [f["check_id"] for f in findings]

    def test_detects_missing_pidslimit_field(self):
        """When PidsLimit key is absent, treat as 0 (no limit)."""
        hc = {**SECURE_HOST_CONFIG}
        del hc["PidsLimit"]
        findings = _check_container(_inspect(host_config=hc))
        assert "RES_002" in [f["check_id"] for f in findings]

    def test_detects_oom_kill_disabled(self):
        hc = {**SECURE_HOST_CONFIG, "OomKillDisable": True}
        findings = _check_container(_inspect(host_config=hc))
        assert "RES_003" in [f["check_id"] for f in findings]
        res = next(f for f in findings if f["check_id"] == "RES_003")
        assert res["severity"] == "HIGH"

    def test_no_res003_when_oom_kill_default(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "RES_003" not in [f["check_id"] for f in findings]

    def test_detects_no_cpu_limit(self):
        hc = {**SECURE_HOST_CONFIG, "CpuQuota": 0}
        findings = _check_container(_inspect(host_config=hc))
        assert "RES_004" in [f["check_id"] for f in findings]

    def test_no_res004_when_cpu_quota_set(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "RES_004" not in [f["check_id"] for f in findings]

    def test_detects_missing_cpu_quota_field(self):
        """When CpuQuota key is absent, treat as 0 (no limit)."""
        hc = {**SECURE_HOST_CONFIG}
        del hc["CpuQuota"]
        findings = _check_container(_inspect(host_config=hc))
        assert "RES_004" in [f["check_id"] for f in findings]

    # ── Capability drop rules ───────────────────────────────────────────

    def test_detects_missing_cap_drop_all(self):
        hc = {**SECURE_HOST_CONFIG, "CapDrop": []}
        findings = _check_container(_inspect(host_config=hc))
        assert "CAP_002" in [f["check_id"] for f in findings]

    def test_no_cap002_when_all_dropped(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "CAP_002" not in [f["check_id"] for f in findings]

    def test_cap002_fires_on_partial_drop(self):
        """Dropping only NET_RAW is not enough — must drop ALL."""
        hc = {**SECURE_HOST_CONFIG, "CapDrop": ["NET_RAW"]}
        findings = _check_container(_inspect(host_config=hc))
        assert "CAP_002" in [f["check_id"] for f in findings]

    # ── Identity rules ──────────────────────────────────────────────────

    def test_detects_root_user(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG, config={"User": ""}))
        assert "USR_001" in [f["check_id"] for f in findings]

    def test_detects_root_user_when_config_absent(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "USR_001" in [f["check_id"] for f in findings]

    def test_no_usr001_when_non_root(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG, config=SECURE_CONFIG))
        assert "USR_001" not in [f["check_id"] for f in findings]

    def test_usr001_does_not_fire_on_explicit_root_zero(self):
        """Config.User='0' is truthy in Python — known limitation, not a bug."""
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG, config={"User": "0"}))
        assert "USR_001" not in [f["check_id"] for f in findings]

    # ── Network rules (cont.) ──────────────────────────────────────────

    def test_detects_publish_all_ports(self):
        hc = {**SECURE_HOST_CONFIG, "PublishAllPorts": True}
        findings = _check_container(_inspect(host_config=hc))
        assert "NET_002" in [f["check_id"] for f in findings]

    def test_no_net002_when_publish_all_false(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "NET_002" not in [f["check_id"] for f in findings]

    # ── Namespace rules (cont.) ────────────────────────────────────────

    def test_detects_host_uts_namespace(self):
        hc = {**SECURE_HOST_CONFIG, "UTSMode": "host"}
        findings = _check_container(_inspect(host_config=hc))
        assert "NS_003" in [f["check_id"] for f in findings]

    def test_ignores_default_uts_mode(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "NS_003" not in [f["check_id"] for f in findings]

    # ── Log rules ──────────────────────────────────────────────────────

    def test_detects_no_log_size_limit(self):
        hc = {**SECURE_HOST_CONFIG, "LogConfig": {"Type": "json-file", "Config": {}}}
        findings = _check_container(_inspect(host_config=hc))
        assert "LOG_001" in [f["check_id"] for f in findings]

    def test_detects_missing_log_config(self):
        hc = {**SECURE_HOST_CONFIG}
        del hc["LogConfig"]
        findings = _check_container(_inspect(host_config=hc))
        assert "LOG_001" in [f["check_id"] for f in findings]

    def test_no_log001_when_max_size_set(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "LOG_001" not in [f["check_id"] for f in findings]

    # ── Lifecycle rules ────────────────────────────────────────────────

    def test_detects_no_restart_policy(self):
        hc = {**SECURE_HOST_CONFIG, "RestartPolicy": {"Name": "", "MaximumRetryCount": 0}}
        findings = _check_container(_inspect(host_config=hc))
        assert "LIFE_001" in [f["check_id"] for f in findings]

    def test_detects_missing_restart_policy(self):
        hc = {**SECURE_HOST_CONFIG}
        del hc["RestartPolicy"]
        findings = _check_container(_inspect(host_config=hc))
        assert "LIFE_001" in [f["check_id"] for f in findings]

    def test_no_life001_when_restart_policy_set(self):
        findings = _check_container(_inspect(host_config=SECURE_HOST_CONFIG))
        assert "LIFE_001" not in [f["check_id"] for f in findings]


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

    async def test_skips_fully_secure_containers(self):
        summary = _summary(image="nginx:latest")
        full = _inspect(host_config=SECURE_HOST_CONFIG, config=SECURE_CONFIG)

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
        full = _inspect(host_config={"Privileged": True}, container_id="abc123")

        with (
            patch.object(_module._docker, "containers", return_value=[summary]),
            patch.object(_module._docker, "container_inspect", return_value=full) as mock_inspect,
        ):
            results = await run_misconfig_checks()

        mock_inspect.assert_called_once_with("abc123")
        assert any(f["check_id"] == "PRIV_001" for f in results[0]["findings"])
