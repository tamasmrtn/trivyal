"""Declarative misconfiguration rules for container inspection."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RuleType(StrEnum):
    """Determines which checker function evaluates the rule."""

    FIELD_TRUTHY = "field_truthy"
    FIELD_EQUALS = "field_equals"
    FIELD_ABSENT = "field_absent"
    LIST_MISSING_SUBSTR = "list_missing_substr"
    SET_INTERSECTION = "set_intersection"
    MOUNT_PATH = "mount_path"


class Rule(BaseModel):
    """A single misconfiguration check.

    Attributes:
        check_id: Unique identifier (e.g. "PRIV_001").
        severity: Finding severity level.
        title: Human-readable one-liner.
        fix_guideline: Remediation advice; may contain ``{detail}`` placeholder.
        rule_type: Determines evaluation logic.
        field: Dot-path into the container inspect dict (e.g. "HostConfig.Privileged").
        value: Comparison operand — meaning depends on ``rule_type``.
    """

    check_id: str
    severity: Severity
    title: str
    fix_guideline: str
    rule_type: RuleType
    field: str
    value: Any = None


RULES: list[Rule] = [
    # ── Privilege escalation ────────────────────────────────────────────
    Rule(
        check_id="PRIV_001",
        severity=Severity.HIGH,
        title="Container running in privileged mode",
        fix_guideline="Remove 'privileged: true' from the container definition.",
        rule_type=RuleType.FIELD_TRUTHY,
        field="HostConfig.Privileged",
    ),
    Rule(
        check_id="PRIV_002",
        severity=Severity.MEDIUM,
        title="Container missing no-new-privileges security option",
        fix_guideline="Add 'security_opt: [no-new-privileges:true]' to the container definition.",
        rule_type=RuleType.LIST_MISSING_SUBSTR,
        field="HostConfig.SecurityOpt",
        value="no-new-privileges",
    ),
    # ── Capabilities ────────────────────────────────────────────────────
    Rule(
        check_id="CAP_001",
        severity=Severity.HIGH,
        title="Container has dangerous capabilities",
        fix_guideline="Remove capabilities: {detail}.",
        rule_type=RuleType.SET_INTERSECTION,
        field="HostConfig.CapAdd",
        value={"SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "ALL"},
    ),
    # ── Network ─────────────────────────────────────────────────────────
    Rule(
        check_id="NET_001",
        severity=Severity.MEDIUM,
        title="Container using host network mode",
        fix_guideline="Use a dedicated Docker network instead of 'network_mode: host'.",
        rule_type=RuleType.FIELD_EQUALS,
        field="HostConfig.NetworkMode",
        value="host",
    ),
    # ── Namespaces ──────────────────────────────────────────────────────
    Rule(
        check_id="NS_001",
        severity=Severity.HIGH,
        title="Container using host PID namespace",
        fix_guideline="Remove 'pid: host' from the container definition.",
        rule_type=RuleType.FIELD_EQUALS,
        field="HostConfig.PidMode",
        value="host",
    ),
    Rule(
        check_id="NS_002",
        severity=Severity.MEDIUM,
        title="Container using host IPC namespace",
        fix_guideline="Remove 'ipc: host' from the container definition.",
        rule_type=RuleType.FIELD_EQUALS,
        field="HostConfig.IpcMode",
        value="host",
    ),
    # ── Mounts & filesystem ─────────────────────────────────────────────
    Rule(
        check_id="MNT_001",
        severity=Severity.HIGH,
        title="Docker socket mounted in container",
        fix_guideline="Remove the /var/run/docker.sock bind mount.",
        rule_type=RuleType.MOUNT_PATH,
        field="HostConfig.Binds",
        value=["/var/run/docker.sock"],
    ),
    Rule(
        check_id="MNT_002",
        severity=Severity.HIGH,
        title="Sensitive host directory mounted",
        fix_guideline="Remove bind mount for sensitive host path: {detail}.",
        rule_type=RuleType.MOUNT_PATH,
        field="HostConfig.Binds",
        value=["/", "/etc", "/proc", "/sys", "/dev", "/boot", "/usr"],
    ),
    Rule(
        check_id="MNT_003",
        severity=Severity.MEDIUM,
        title="Container filesystem is writable",
        fix_guideline="Set 'read_only: true' in the container definition.",
        rule_type=RuleType.FIELD_ABSENT,
        field="HostConfig.ReadonlyRootfs",
    ),
    # ── Resource limits ─────────────────────────────────────────────────
    Rule(
        check_id="RES_001",
        severity=Severity.MEDIUM,
        title="Container has no memory limit",
        fix_guideline="Set a memory limit (e.g., 'mem_limit: 512m') in the container definition.",
        rule_type=RuleType.FIELD_EQUALS,
        field="HostConfig.Memory",
        value=0,
    ),
    Rule(
        check_id="RES_002",
        severity=Severity.MEDIUM,
        title="Container has no PID limit",
        fix_guideline="Set 'pids_limit: 4096' (or appropriate value) in the container definition.",
        rule_type=RuleType.FIELD_EQUALS,
        field="HostConfig.PidsLimit",
        value=0,
    ),
    Rule(
        check_id="RES_003",
        severity=Severity.HIGH,
        title="OOM killer is disabled",
        fix_guideline="Remove 'oom_kill_disable: true' — a container without OOM protection can hang your entire host.",
        rule_type=RuleType.FIELD_TRUTHY,
        field="HostConfig.OomKillDisable",
    ),
    Rule(
        check_id="RES_004",
        severity=Severity.LOW,
        title="Container has no CPU limit",
        fix_guideline="Set 'cpus: 2.0' (or appropriate value) in the container definition to prevent CPU starvation.",
        rule_type=RuleType.FIELD_EQUALS,
        field="HostConfig.CpuQuota",
        value=0,
    ),
    # ── Capabilities (cont.) ───────────────────────────────────────────
    Rule(
        check_id="CAP_002",
        severity=Severity.MEDIUM,
        title="Container does not drop all default capabilities",
        fix_guideline="Add 'cap_drop: [ALL]' and only add back specific capabilities you need with cap_add.",
        rule_type=RuleType.LIST_MISSING_SUBSTR,
        field="HostConfig.CapDrop",
        value="ALL",
    ),
    # ── Identity ───────────────────────────────────────────────────────
    Rule(
        check_id="USR_001",
        severity=Severity.LOW,
        title="Container is running as root user",
        fix_guideline="Add 'user: \"1000:1000\"' (or another non-root UID) to the container definition.",
        rule_type=RuleType.FIELD_ABSENT,
        field="Config.User",
    ),
    # ── Network (cont.) ───────────────────────────────────────────────
    Rule(
        check_id="NET_002",
        severity=Severity.MEDIUM,
        title="Container publishes all exposed ports",
        fix_guideline="Replace '-P' / 'publish_all_ports: true' with explicit port mappings in the 'ports:' section.",
        rule_type=RuleType.FIELD_TRUTHY,
        field="HostConfig.PublishAllPorts",
    ),
    # ── Namespaces (cont.) ─────────────────────────────────────────────
    Rule(
        check_id="NS_003",
        severity=Severity.LOW,
        title="Container shares host UTS namespace",
        fix_guideline="Remove 'uts: host' from the container definition unless hostname sharing is required.",
        rule_type=RuleType.FIELD_EQUALS,
        field="HostConfig.UTSMode",
        value="host",
    ),
    # ── Observability / reliability ────────────────────────────────────
    Rule(
        check_id="LOG_001",
        severity=Severity.LOW,
        title="Container has no log size limit",
        fix_guideline='Add \'logging: { options: { max-size: "10m", max-file: "3" } }\' to prevent disk exhaustion.',
        rule_type=RuleType.FIELD_ABSENT,
        field="HostConfig.LogConfig.Config.max-size",
    ),
    Rule(
        check_id="LIFE_001",
        severity=Severity.LOW,
        title="Container has no restart policy",
        fix_guideline="Add 'restart: unless-stopped' to ensure the container recovers from crashes and host reboots.",
        rule_type=RuleType.FIELD_ABSENT,
        field="HostConfig.RestartPolicy.Name",
    ),
]
