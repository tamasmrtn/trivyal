#!/bin/sh
# Ensure the data directory is owned by the trivyal user.
# This handles the case where a host bind-mount is created by Docker as root.
chown -R trivyal:trivyal /app/data
exec gosu trivyal "$@"
