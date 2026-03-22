"""Tests for container_ops — restart flow and anonymous volume detection."""

from unittest.mock import MagicMock

from trivyal_patcher.container_ops import restart_container


class TestRestartContainer:
    def test_successful_restart(self):
        docker = MagicMock()
        docker.has_anonymous_volumes.return_value = False
        docker.container_inspect.return_value = {
            "Name": "/my-nginx",
            "Config": {"Image": "nginx:1.25"},
            "HostConfig": {"NetworkMode": "bridge"},
            "NetworkingConfig": {},
        }
        docker.container_create.return_value = "new-id-123"

        result = restart_container(docker, "old-id", "nginx:1.25-patched")

        assert result["status"] == "completed"
        assert result["new_container_id"] == "new-id-123"
        docker.container_stop.assert_called_once_with("old-id")
        docker.container_remove.assert_called_once_with("old-id")
        docker.container_start.assert_called_once_with("new-id-123")

    def test_blocked_by_anonymous_volumes(self):
        docker = MagicMock()
        docker.has_anonymous_volumes.return_value = True

        result = restart_container(docker, "cid", "nginx:patched")

        assert result["status"] == "blocked"
        assert "anonymous volumes" in result["reason"]
        docker.container_stop.assert_not_called()
