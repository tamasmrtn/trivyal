"""Tests for sidecar_client — HTTP client for the patcher sidecar."""

from unittest.mock import MagicMock, patch

from trivyal_agent.core.sidecar_client import SidecarClient


class TestSidecarHealth:
    def test_returns_true_on_200(self):
        mock_resp = MagicMock()
        mock_resp.status = 200

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_resp

        with patch("trivyal_agent.core.sidecar_client.http.client.HTTPConnection", return_value=mock_conn):
            client = SidecarClient("http://localhost:8101")
            assert client.health() is True

    def test_returns_false_on_connection_error(self):
        with patch(
            "trivyal_agent.core.sidecar_client.http.client.HTTPConnection",
            side_effect=Exception("Connection refused"),
        ):
            client = SidecarClient("http://localhost:8101")
            assert client.health() is False


class TestSidecarPatch:
    def test_parses_ndjson_response(self):
        lines = [b'{"type":"log","line":"Patching..."}\n', b'{"type":"result","status":"completed"}\n']

        mock_resp = MagicMock()
        mock_resp.__iter__ = MagicMock(return_value=iter(lines))

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_resp

        with patch("trivyal_agent.core.sidecar_client.http.client.HTTPConnection", return_value=mock_conn):
            client = SidecarClient("http://localhost:8101")
            events = client.patch("nginx:1.25", {}, "nginx:1.25-patched")

        assert len(events) == 2
        assert events[0]["type"] == "log"
        assert events[1]["status"] == "completed"


class TestSidecarRestart:
    def test_returns_result_dict(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"status":"completed","new_container_id":"abc"}'

        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_resp

        with patch("trivyal_agent.core.sidecar_client.http.client.HTTPConnection", return_value=mock_conn):
            client = SidecarClient("http://localhost:8101")
            result = client.restart("old-id", "nginx:patched")

        assert result["status"] == "completed"
        assert result["new_container_id"] == "abc"
