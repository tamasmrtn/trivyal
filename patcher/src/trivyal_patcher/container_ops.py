"""Container restart operations — stop, recreate, start with patched image."""

import logging

from trivyal_patcher.docker_client import DockerClient

logger = logging.getLogger(__name__)


def restart_container(docker: DockerClient, container_id: str, new_image: str) -> dict:
    """Restart a container with a new image. Synchronous — call via to_thread."""
    # Check for anonymous volumes that would be lost
    if docker.has_anonymous_volumes(container_id):
        return {
            "status": "blocked",
            "reason": "Container has anonymous volumes that would be lost on restart",
        }

    # Inspect the current container to capture its config
    inspect = docker.container_inspect(container_id)
    config = inspect.get("Config", {})
    host_config = inspect.get("HostConfig", {})
    networking = inspect.get("NetworkingConfig", {})
    name = inspect.get("Name", "").lstrip("/")

    # Build the create payload
    create_config = {
        **config,
        "Image": new_image,
        "HostConfig": host_config,
        "NetworkingConfig": networking,
    }
    # Remove runtime-only fields that aren't valid for create
    for key in ("Id", "Created", "State", "Path", "Args"):
        create_config.pop(key, None)

    logger.info("Stopping container %s (%s)", name, container_id)
    docker.container_stop(container_id)
    docker.container_remove(container_id)

    logger.info("Creating new container %s with image %s", name, new_image)
    new_id = docker.container_create(name, create_config)
    docker.container_start(new_id)

    logger.info("Container %s restarted as %s", name, new_id)
    return {
        "status": "completed",
        "new_container_id": new_id,
    }
