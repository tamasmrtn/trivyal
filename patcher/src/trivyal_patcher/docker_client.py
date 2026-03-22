"""Synchronous Docker Engine API client over a Unix socket.

Reuses the pattern from agent/src/trivyal_agent/core/docker_socket.py but adds
write operations needed for container restarts.
"""

import http.client
import json
import socket
from typing import Any


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str) -> None:
        super().__init__("localhost")
        self._socket_path = socket_path

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self._socket_path)


class DockerClient:
    """Docker Engine API client with read and write operations."""

    def __init__(self, socket_path: str = "/var/run/docker.sock") -> None:
        self._path = socket_path

    def _request(self, method: str, endpoint: str, body: dict | None = None) -> Any:
        conn = _UnixHTTPConnection(self._path)
        try:
            headers = {"Host": "localhost"}
            data = None
            if body is not None:
                data = json.dumps(body).encode()
                headers["Content-Type"] = "application/json"
            conn.request(method, endpoint, body=data, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status >= 400:
                detail = raw.decode(errors="replace")
                msg = f"Docker API {method} {endpoint} returned {resp.status}: {detail}"
                raise RuntimeError(msg)
            if not raw:
                return {}
            return json.loads(raw)
        finally:
            conn.close()

    def _get(self, endpoint: str) -> Any:
        return self._request("GET", endpoint)

    def _post(self, endpoint: str, body: dict | None = None) -> Any:
        return self._request("POST", endpoint, body)

    def _delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)

    def container_inspect(self, container_id: str) -> dict:
        return self._get(f"/containers/{container_id}/json")

    def container_stop(self, container_id: str, timeout: int = 10) -> None:
        self._post(f"/containers/{container_id}/stop?t={timeout}")

    def container_remove(self, container_id: str) -> None:
        self._delete(f"/containers/{container_id}")

    def container_create(self, name: str, config: dict) -> str:
        result = self._post(f"/containers/create?name={name}", config)
        return result["Id"]

    def container_start(self, container_id: str) -> None:
        self._post(f"/containers/{container_id}/start")

    def has_anonymous_volumes(self, container_id: str) -> bool:
        """Check if a container has anonymous (unnamed) volumes."""
        inspect = self.container_inspect(container_id)
        mounts = inspect.get("Mounts", [])
        return any(m.get("Name") and not m.get("Source", "").startswith("/") for m in mounts if m.get("Type") == "volume" and "/" not in m.get("Name", "/"))
