"""Thin stdlib HTTP client over the Docker Unix socket.

All methods are synchronous — callers wrap them in asyncio.to_thread().
To add a new Docker API endpoint, add a method here and call self._get().
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


class DockerSocket:
    """Synchronous Docker Engine API client over a Unix socket.

    Extension points — add methods here as needed:
      def images(self) -> list[dict]:
          return self._get("/images/json")

      def image_inspect(self, image_id: str) -> dict:
          return self._get(f"/images/{image_id}/json")

      def container_stats(self, container_id: str) -> dict:
          return self._get(f"/containers/{container_id}/stats?stream=0")

      def container_top(self, container_id: str) -> dict:
          return self._get(f"/containers/{container_id}/top")
    """

    def __init__(self, path: str = "/var/run/docker.sock") -> None:
        self._path = path

    def _get(self, endpoint: str) -> Any:
        conn = _UnixHTTPConnection(self._path)
        try:
            conn.request("GET", endpoint, headers={"Host": "localhost"})
            resp = conn.getresponse()
            return json.loads(resp.read())
        finally:
            conn.close()

    def version(self) -> dict:
        return self._get("/version")

    def containers(self, all: bool = False) -> list[dict]:
        qs = "?all=1" if all else ""
        return self._get(f"/containers/json{qs}")

    def container_inspect(self, container_id: str) -> dict:
        return self._get(f"/containers/{container_id}/json")


_docker = DockerSocket()
