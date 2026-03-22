"""Lightweight HTTP client for the patcher sidecar.

Uses stdlib http.client over TCP, matching the Docker socket pattern.
All methods are synchronous — callers wrap them in asyncio.to_thread().
"""

import http.client
import json
import logging
from collections.abc import Callable
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SidecarClient:
    """HTTP client for the trivyal-patcher sidecar."""

    def __init__(self, url: str) -> None:
        parsed = urlparse(url)
        self._host = parsed.hostname or "localhost"
        self._port = parsed.port or 8101

    def _conn(self, timeout: float | None = 10) -> http.client.HTTPConnection:
        return http.client.HTTPConnection(self._host, self._port, timeout=timeout)

    def health(self) -> bool:
        """Check if the sidecar is reachable."""
        try:
            conn = self._conn(timeout=5)
            conn.request("GET", "/health")
            resp = conn.getresponse()
            conn.close()
            return resp.status == 200
        except Exception:
            return False

    def patch(
        self,
        image: str,
        trivy_report: dict,
        patched_tag: str,
        on_event: Callable[[dict], None] | None = None,
    ) -> list[dict]:
        """POST /patch — read streaming NDJSON response line by line.

        Calls on_event(event) for each event as it arrives (useful for
        forwarding log lines in real time from a background thread).
        Returns the full list of events after Copa finishes.
        """
        body = json.dumps(
            {
                "image": image,
                "trivy_report": trivy_report,
                "patched_tag": patched_tag,
            }
        ).encode()

        conn = self._conn(timeout=None)
        conn.request(
            "POST",
            "/patch",
            body=body,
            headers={
                "Content-Type": "application/json",
            },
        )
        resp = conn.getresponse()

        if resp.status != 200:
            error = resp.read().decode(errors="replace")
            conn.close()
            raise RuntimeError(f"Patcher returned {resp.status}: {error}")

        events: list[dict] = []
        for line in resp:
            text = line.decode(errors="replace").strip()
            if text:
                event = json.loads(text)
                if on_event:
                    on_event(event)
                events.append(event)

        conn.close()
        return events

    def restart(self, container_id: str, image: str) -> dict:
        """POST /restart — returns result dict."""
        body = json.dumps(
            {
                "container_id": container_id,
                "image": image,
            }
        ).encode()

        conn = self._conn()
        conn.request(
            "POST",
            "/restart",
            body=body,
            headers={
                "Content-Type": "application/json",
            },
        )
        resp = conn.getresponse()
        result = json.loads(resp.read())
        conn.close()
        return result
