"""Webhook notification sender for new Critical/High findings."""

import logging

import httpx

logger = logging.getLogger(__name__)


async def send_webhook(
    webhook_url: str,
    webhook_type: str | None,
    findings: list[dict],
) -> bool:
    """Send a webhook notification about new findings. Returns True on success."""
    if not webhook_url:
        return False

    payload = _format_payload(webhook_type, findings)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            return True
    except httpx.HTTPError:
        logger.exception("Failed to send webhook to %s", webhook_url)
        return False


def _format_payload(webhook_type: str | None, findings: list[dict]) -> dict:
    count = len(findings)
    summary = f"Trivyal: {count} new critical/high finding(s) detected"

    formatters = {
        "slack": {"text": summary},
        "discord": {"content": summary},
        "ntfy": {"topic": "trivyal", "title": "New Vulnerabilities", "message": summary},
    }
    return formatters.get(webhook_type, {"summary": summary, "count": count, "findings": findings})
