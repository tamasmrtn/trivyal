"""Tests for core/docker_client.py."""

from unittest.mock import MagicMock, patch

from trivyal_agent.core.docker_client import collect_host_metadata, list_running_images


class TestListRunningImages:
    async def test_returns_image_and_container_name(self):
        mock_image = MagicMock()
        mock_image.tags = ["nginx:latest"]
        mock_container = MagicMock()
        mock_container.image = mock_image
        mock_container.name = "my-nginx"

        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]

        with patch("trivyal_agent.core.docker_client.docker") as mock_docker:
            mock_docker.from_env.return_value = mock_client
            result = await list_running_images()

        assert result == [{"image_name": "nginx:latest", "container_name": "my-nginx"}]

    async def test_uses_image_id_when_no_tags(self):
        mock_image = MagicMock()
        mock_image.tags = []
        mock_image.id = "sha256:abc123"
        mock_container = MagicMock()
        mock_container.image = mock_image
        mock_container.name = "untagged-container"

        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]

        with patch("trivyal_agent.core.docker_client.docker") as mock_docker:
            mock_docker.from_env.return_value = mock_client
            result = await list_running_images()

        assert result == [{"image_name": "sha256:abc123", "container_name": "untagged-container"}]

    async def test_returns_empty_list_when_no_containers(self):
        mock_client = MagicMock()
        mock_client.containers.list.return_value = []

        with patch("trivyal_agent.core.docker_client.docker") as mock_docker:
            mock_docker.from_env.return_value = mock_client
            result = await list_running_images()

        assert result == []


class TestCollectHostMetadata:
    async def test_returns_expected_keys(self):
        mock_client = MagicMock()
        mock_client.version.return_value = {"Version": "24.0.0"}

        with patch("trivyal_agent.core.docker_client.docker") as mock_docker:
            mock_docker.from_env.return_value = mock_client
            metadata = await collect_host_metadata()

        assert "hostname" in metadata
        assert "os" in metadata
        assert "docker_version" in metadata
        assert "agent_pid" in metadata
        assert metadata["docker_version"] == "24.0.0"

    async def test_docker_version_fallback_on_error(self):
        with patch("trivyal_agent.core.docker_client.docker") as mock_docker:
            mock_docker.from_env.side_effect = Exception("Docker not available")
            metadata = await collect_host_metadata()

        assert metadata["docker_version"] == "unknown"
