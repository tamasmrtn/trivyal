"""Docker API-based container misconfiguration detection."""

import asyncio
import logging

from .docker_socket import _docker

logger = logging.getLogger(__name__)

DANGEROUS_CAPS = {"SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "ALL"}


def _check_container(container: dict) -> list[dict]:
    """Run misconfig checks against a single container inspect dict."""
    findings = []
    host_config = container.get("HostConfig", {})

    # PRIV_001: Privileged mode
    if host_config.get("Privileged"):
        findings.append(
            {
                "check_id": "PRIV_001",
                "severity": "HIGH",
                "title": "Container running in privileged mode",
                "fix_guideline": "Remove 'privileged: true' from the container definition.",
            }
        )

    # CAP_001: Dangerous capabilities
    cap_add = host_config.get("CapAdd") or []
    dangerous = DANGEROUS_CAPS.intersection(c.upper() for c in cap_add)
    if dangerous:
        caps_str = ", ".join(sorted(dangerous))
        findings.append(
            {
                "check_id": "CAP_001",
                "severity": "HIGH",
                "title": "Container has dangerous capabilities",
                "fix_guideline": f"Remove capabilities: {caps_str}.",
            }
        )

    # NET_001: Host network mode
    if host_config.get("NetworkMode") == "host":
        findings.append(
            {
                "check_id": "NET_001",
                "severity": "MEDIUM",
                "title": "Container using host network mode",
                "fix_guideline": "Use a dedicated Docker network instead of 'network_mode: host'.",
            }
        )

    # PRIV_002: Missing no-new-privileges
    security_opt = host_config.get("SecurityOpt") or []
    has_no_new_privs = any("no-new-privileges" in opt for opt in security_opt)
    if not has_no_new_privs:
        findings.append(
            {
                "check_id": "PRIV_002",
                "severity": "MEDIUM",
                "title": "Container missing no-new-privileges security option",
                "fix_guideline": "Add 'security_opt: [no-new-privileges:true]' to the container definition.",
            }
        )

    return findings


def _scan_all_containers() -> list[dict]:
    """Scan all running containers for misconfigs (sync)."""
    results = []
    for summary in _docker.containers():
        container_id = summary["Id"]
        full = _docker.container_inspect(container_id)
        findings = _check_container(full)
        if not findings:
            continue
        names = summary.get("Names", [])
        container_name = names[0].lstrip("/") if names else container_id[:12]
        results.append(
            {
                "container_id": container_id,
                "container_name": container_name,
                "image_name": summary.get("Image", ""),
                "findings": findings,
            }
        )
    return results


async def run_misconfig_checks() -> list[dict]:
    """Async wrapper for container misconfig scanning."""
    return await asyncio.to_thread(_scan_all_containers)
