# hub/Dockerfile
# checkov:skip=CKV_DOCKER_2: healthcheck is defined in docker-compose.hub.yml

# ── Stage 1: Build the React UI ──────────────────────────────────────────────
FROM node:24-alpine AS ui-builder

WORKDIR /ui

# Install deps first so this layer is cached as long as package files don't change
COPY ui/package.json ui/package-lock.json ./
RUN npm ci

COPY ui/ .
RUN npm run build
# Output lives in /ui/dist


# ── Stage 2: Install Python dependencies ─────────────────────────────────────
FROM python:3.14-alpine AS python-builder

# uv is a build tool — it belongs here, not in the runtime image
COPY --from=ghcr.io/astral-sh/uv:0.11.3-python3.14-trixie-slim /usr/local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Copy manifests first so dep install is cached independently of source changes
COPY hub/pyproject.toml hub/uv.lock ./
# Source is needed so uv can build and install the trivyal_hub wheel
COPY hub/src ./src

# --frozen: use the lockfile as-is
# --no-dev: skip test/lint dependencies
# --no-editable: build a proper wheel so src/ is not needed at runtime
RUN uv sync --frozen --no-dev --no-editable
# Result: /app/.venv contains all dependencies + the installed trivyal_hub package


# ── Stage 3: Runtime ─────────────────────────────────────────────────────────
FROM python:3.14-alpine AS hub

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    # Activate the venv by prepending it to PATH — no `uv run` needed
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy only the populated virtualenv — uv itself is not copied
COPY --from=python-builder /app/.venv /app/.venv

# Copy the compiled UI for FastAPI to serve as static files
COPY --from=ui-builder /ui/dist ./static

RUN pip uninstall -y pip && \
    apk upgrade --no-cache && \
    addgroup -S trivyal && \
    adduser -S -G trivyal -H trivyal && \
    mkdir -p /app/data && \
    chown -R trivyal:trivyal /app/data

EXPOSE 8099

USER trivyal

CMD ["uvicorn", "trivyal_hub.main:app", \
     "--host", "0.0.0.0", "--port", "8099", \
     "--no-access-log"]
