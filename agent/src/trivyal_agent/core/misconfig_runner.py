"""Docker API-based container misconfiguration detection."""

import asyncio
import logging
from typing import Any

from .docker_socket import _docker
from .misconfig_rules import RULES, Rule, RuleType

logger = logging.getLogger(__name__)


def _resolve_field(container: dict, dotpath: str, default: Any = None) -> Any:
    """Resolve a dot-separated path against the container inspect dict."""
    obj: Any = container
    for key in dotpath.split("."):
        if not isinstance(obj, dict):
            return default
        obj = obj.get(key)
        if obj is None:
            return default
    return obj


def _finding(rule: Rule, detail: str = "") -> dict:
    """Build the output dict for a triggered rule."""
    guideline = rule.fix_guideline.format(detail=detail) if detail else rule.fix_guideline
    return {
        "check_id": rule.check_id,
        "severity": str(rule.severity),
        "title": rule.title,
        "fix_guideline": guideline,
    }


def _match_mount_source(source: str, paths: list[str]) -> bool:
    """Check if a bind-mount source matches any of the given paths (prefix-aware)."""
    return any(source == path or source.startswith(path + "/") for path in paths)


def _evaluate_rule(rule: Rule, container: dict) -> dict | None:
    """Evaluate a single rule against a container. Returns finding dict or None."""
    raw = _resolve_field(container, rule.field)

    match rule.rule_type:
        case RuleType.FIELD_TRUTHY:
            if not raw:
                return None

        case RuleType.FIELD_EQUALS:
            effective = raw if raw is not None else (0 if rule.value == 0 else None)
            if effective != rule.value:
                return None

        case RuleType.FIELD_ABSENT:
            if raw:
                return None

        case RuleType.LIST_MISSING_SUBSTR:
            items = raw or []
            if any(rule.value in item for item in items):
                return None

        case RuleType.SET_INTERSECTION:
            items = raw or []
            matched = rule.value.intersection(v.upper() for v in items)
            if not matched:
                return None
            return _finding(rule, detail=", ".join(sorted(matched)))

        case RuleType.MOUNT_PATH:
            binds = raw or []
            sources = [b.split(":")[0] for b in binds]
            matched = [s for s in sources if _match_mount_source(s, rule.value)]
            if not matched:
                return None
            return _finding(rule, detail=", ".join(sorted(matched)))

    return _finding(rule)


def _check_container(container: dict) -> list[dict]:
    """Run all misconfig rules against a single container inspect dict."""
    findings = []
    for rule in RULES:
        result = _evaluate_rule(rule, container)
        if result is not None:
            findings.append(result)
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
