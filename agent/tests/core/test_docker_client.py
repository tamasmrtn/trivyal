"""Tests for core/docker_client.py."""

from unittest.mock import patch

from trivyal_agent.core import docker_client as _module
from trivyal_agent.core.docker_client import collect_host_metadata, list_running_images


class TestListRunningImages:
    async def test_returns_image_and_container_name(self):
        containers = [{"Id": "abc123", "Image": "nginx:latest", "Names": ["/my-nginx"]}]
        with patch.object(_module._docker, "containers", return_value=containers):
            result = await list_running_images()
        assert result == [{"image_name": "nginx:latest", "container_name": "my-nginx"}]

    async def test_strips_leading_slash_from_name(self):
        containers = [{"Id": "abc123", "Image": "redis:7", "Names": ["/redis"]}]
        with patch.object(_module._docker, "containers", return_value=containers):
            result = await list_running_images()
        assert result == [{"image_name": "redis:7", "container_name": "redis"}]

    async def test_falls_back_to_truncated_id_when_no_names(self):
        containers = [{"Id": "deadbeef1234", "Image": "alpine:3", "Names": []}]
        with patch.object(_module._docker, "containers", return_value=containers):
            result = await list_running_images()
        assert result == [{"image_name": "alpine:3", "container_name": "deadbeef1234"}]

    async def test_returns_empty_list_when_no_containers(self):
        with patch.object(_module._docker, "containers", return_value=[]):
            result = await list_running_images()
        assert result == []


class TestCollectHostMetadata:
    async def test_returns_expected_keys(self):
        with patch.object(_module._docker, "version", return_value={"Version": "24.0.0"}):
            metadata = await collect_host_metadata()

        assert "hostname" in metadata
        assert "os" in metadata
        assert "docker_version" in metadata
        assert "agent_pid" in metadata
        assert metadata["docker_version"] == "24.0.0"

    async def test_docker_version_fallback_on_error(self):
        with patch.object(_module._docker, "version", side_effect=Exception("Docker not available")):
            metadata = await collect_host_metadata()

        assert metadata["docker_version"] == "unknown"
