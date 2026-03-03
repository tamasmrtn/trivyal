"""Discover running containers via the Docker socket."""

import asyncio
import logging
import os
import platform
import socket

import docker  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def _list_running_containers() -> list[dict]:
    """Return image name and container name for all running containers (sync)."""
    client = docker.from_env()
    containers = client.containers.list()
    result = []
    for container in containers:
        image_tag = container.image.tags[0] if container.image.tags else container.image.id
        result.append({"image_name": image_tag, "container_name": container.name})
    client.close()
    return result


async def list_running_images() -> list[dict]:
    """Async wrapper — runs the Docker SDK call in a thread pool executor."""
    return await asyncio.to_thread(_list_running_containers)


def _get_docker_version() -> str:
    """Return the Docker server version string (sync)."""
    try:
        client = docker.from_env()
        version = client.version().get("Version", "unknown")
        client.close()
        return version
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
