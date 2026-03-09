"""Tests for core/docker_socket.py."""

import contextlib
import json
import socket
from unittest.mock import MagicMock, patch

from trivyal_agent.core.docker_socket import DockerSocket, _UnixHTTPConnection


class TestUnixHTTPConnection:
    def test_connect_uses_af_unix_socket(self):
        conn = _UnixHTTPConnection("/var/run/docker.sock")
        mock_sock = MagicMock()
        with patch("trivyal_agent.core.docker_socket.socket") as mock_socket_module:
            mock_socket_module.AF_UNIX = socket.AF_UNIX
            mock_socket_module.SOCK_STREAM = socket.SOCK_STREAM
            mock_socket_module.socket.return_value = mock_sock
            conn.connect()
        mock_socket_module.socket.assert_called_once_with(socket.AF_UNIX, socket.SOCK_STREAM)
        mock_sock.connect.assert_called_once_with("/var/run/docker.sock")

    def test_connect_stores_socket(self):
        conn = _UnixHTTPConnection("/var/run/docker.sock")
        mock_sock = MagicMock()
        with patch("socket.socket", return_value=mock_sock):
            conn.connect()
        assert conn.sock is mock_sock


class TestDockerSocketGet:
    def _make_response(self, body: bytes, status: int = 200):
        """Return a mock HTTPResponse that reads the given body."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.status = status
        return mock_resp

    def test_get_parses_json_response(self):
        payload = {"Version": "24.0.0"}
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = self._make_response(json.dumps(payload).encode())

        with patch(
            "trivyal_agent.core.docker_socket._UnixHTTPConnection",
            return_value=mock_conn,
        ):
            client = DockerSocket("/var/run/docker.sock")
            result = client._get("/version")

        assert result == payload
        mock_conn.request.assert_called_once_with("GET", "/version", headers={"Host": "localhost"})

    def test_get_closes_connection_on_success(self):
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = self._make_response(b"[]")

        with patch(
            "trivyal_agent.core.docker_socket._UnixHTTPConnection",
            return_value=mock_conn,
        ):
            DockerSocket()._get("/containers/json")

        mock_conn.close.assert_called_once()

    def test_get_closes_connection_on_error(self):
        mock_conn = MagicMock()
        mock_conn.request.side_effect = OSError("connection refused")

        with (
            patch(
                "trivyal_agent.core.docker_socket._UnixHTTPConnection",
                return_value=mock_conn,
            ),
            contextlib.suppress(OSError),
        ):
            DockerSocket()._get("/version")

        mock_conn.close.assert_called_once()


class TestDockerSocketEndpoints:
    def _client_with(self, payload):
        """Return a DockerSocket whose _get() returns payload."""
        client = DockerSocket()
        client._get = MagicMock(return_value=payload)
        return client

    def test_version_calls_version_endpoint(self):
        client = self._client_with({"Version": "24.0.0"})
        result = client.version()
        client._get.assert_called_once_with("/version")
        assert result == {"Version": "24.0.0"}

    def test_containers_no_all_flag(self):
        client = self._client_with([])
        client.containers()
        client._get.assert_called_once_with("/containers/json")

    def test_containers_with_all_flag(self):
        client = self._client_with([])
        client.containers(all=True)
        client._get.assert_called_once_with("/containers/json?all=1")

    def test_container_inspect_builds_correct_path(self):
        client = self._client_with({})
        client.container_inspect("abc123")
        client._get.assert_called_once_with("/containers/abc123/json")
