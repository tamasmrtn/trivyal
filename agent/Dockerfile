# agent/Dockerfile

# ── Stage 1: Extract Trivy binary ────────────────────────────────────────────
FROM aquasec/trivy:latest AS trivy-source
# Nothing to run — we only need the binary at /usr/local/bin/trivy


# ── Stage 2: Install Python dependencies ─────────────────────────────────────
FROM python:3.14-alpine AS python-builder

# uv is a build tool — it belongs here, not in the runtime image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY agent/pyproject.toml agent/uv.lock ./
COPY agent/src ./src

RUN uv sync --frozen --no-dev --no-editable
# Result: /app/.venv contains all dependencies + the installed trivyal_agent package


# ── Stage 3: Runtime ─────────────────────────────────────────────────────────
FROM python:3.14-alpine AS agent

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    TRIVY_CACHE_DIR=/app/data/trivy-cache

# Copy the Trivy binary from its dedicated stage
COPY --from=trivy-source /usr/local/bin/trivy /usr/local/bin/trivy

WORKDIR /app

# Copy only the populated virtualenv — uv itself is not copied
COPY --from=python-builder /app/.venv /app/.venv

# Create non-root group that matches the host Docker socket GID at runtime.
# Default 999 covers most Debian/Ubuntu hosts; override via group_add in compose.
RUN apk upgrade --no-cache && \
    apk add --no-cache su-exec && \
    addgroup -S trivyal && \
    adduser -S -G trivyal -H trivyal && \
    mkdir -p /app/data && \
    chown -R trivyal:trivyal /app/data

COPY agent/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --interval=60s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:8100/health || exit 1

# Entrypoint runs as root to fix bind-mount ownership, then drops to trivyal
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "trivyal_agent.main"]
