# agent/Dockerfile

# ── Stage 1: Extract Trivy binary ────────────────────────────────────────────
FROM aquasec/trivy:0.69.3 AS trivy-source
# Nothing to run — we only need the binary at /usr/local/bin/trivy


# ── Stage 2: Install Python dependencies ─────────────────────────────────────
FROM python:3.14-alpine AS python-builder

# uv is a build tool — it belongs here, not in the runtime image
COPY --from=ghcr.io/astral-sh/uv:0.11.2-python3.14-trixie-slim /usr/local/bin/uv /usr/local/bin/uv

WORKDIR /app

COPY agent/pyproject.toml agent/uv.lock ./
COPY agent/src ./src

RUN uv sync --frozen --no-dev --no-editable
# Result: /app/.venv contains all dependencies + the installed trivyal_agent package


# ── Stage 3: Runtime ─────────────────────────────────────────────────────────
FROM python:3.14-alpine AS agent

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    PATH="/app/.venv/bin:$PATH" \
    TRIVY_CACHE_DIR=/app/data/trivy-cache

# Copy the Trivy binary from its dedicated stage
COPY --from=trivy-source /usr/local/bin/trivy /usr/local/bin/trivy

WORKDIR /app

# Copy only the populated virtualenv — uv itself is not copied
COPY --from=python-builder /app/.venv /app/.venv

RUN pip uninstall -y pip && \
    apk upgrade --no-cache && \
    addgroup -S trivyal && \
    adduser -S -G trivyal -H trivyal && \
    mkdir -p /app/data && \
    chown -R trivyal:trivyal /app/data

HEALTHCHECK --interval=60s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:${TRIVYAL_HEALTH_PORT:-8100}/health || exit 1

USER trivyal

CMD ["python", "-m", "trivyal_agent.main"]
