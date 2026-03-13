"""Discover running containers and collect host metadata via the Docker socket."""

import asyncio
import logging
import os
import platform
import socket

from .docker_socket import _docker

logger = logging.getLogger(__name__)


def _list_running_containers() -> list[dict]:
    """Return image name, container name, and image digest for all running containers (sync)."""
    result = []
    for c in _docker.containers():
        image_name = c.get("Image", "")
        names = c.get("Names", [])
        container_name = names[0].lstrip("/") if names else c["Id"][:12]
        try:
            inspect = _docker.container_inspect(c["Id"])
            image_digest = inspect.get("Image", "")
        except Exception:
            image_digest = ""
        result.append({"image_name": image_name, "container_name": container_name, "image_digest": image_digest})
    return result


async def list_running_images() -> list[dict]:
    """Async wrapper — runs the Docker socket call in a thread pool executor."""
    return await asyncio.to_thread(_list_running_containers)


def _get_docker_version() -> str:
    """Return the Docker server version string (sync)."""
    try:
        return _docker.version().get("Version", "unknown")
    except Exception:
        return "unknown"


async def collect_host_metadata() -> dict:
    """Collect host metadata to report to the hub."""
    docker_version = await asyncio.to_thread(_get_docker_version)
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "docker_version": docker_version,
        "agent_pid": os.getpid(),
    }
