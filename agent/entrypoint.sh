#!/bin/sh
set -e

# Ensure the data directory is owned by the trivyal user.
# This handles the case where a host bind-mount is created by Docker as root.
chown -R trivyal:trivyal /app/data

# Ensure trivyal can access the Docker socket.
# group_add in docker-compose adds the GID to the init process but su-exec replaces
# supplementary groups from /etc/group, losing any dynamically-added GIDs.
# We detect the socket GID at runtime and add trivyal to the matching group.
DOCKER_SOCK=/var/run/docker.sock
if [ -S "$DOCKER_SOCK" ]; then
    SOCK_GID=$(stat -c '%g' "$DOCKER_SOCK")
    if ! getent group "$SOCK_GID" > /dev/null 2>&1; then
        addgroup -S -g "$SOCK_GID" docker-host
    fi
    GROUP_NAME=$(getent group "$SOCK_GID" | cut -d: -f1)
    addgroup trivyal "$GROUP_NAME" 2>/dev/null || true
fi

exec su-exec trivyal "$@"
