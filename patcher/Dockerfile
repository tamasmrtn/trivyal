# patcher/Dockerfile

# ── Stage 1: Download Copa binary from GitHub Releases ───────────────────────
FROM alpine:3.23 AS copa-downloader

ARG COPA_VERSION=0.13.0

RUN apk add --no-cache curl

# TARGETARCH is set by BuildKit (amd64 or arm64) — matches Copa's asset naming
ARG TARGETARCH=amd64
RUN curl -fsSL \
    "https://github.com/project-copacetic/copacetic/releases/download/v${COPA_VERSION}/copa_${COPA_VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar -xz -C /usr/local/bin copa


# ── Stage 2: Install Python dependencies ─────────────────────────────────────
FROM python:3.14-alpine AS python-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY patcher/pyproject.toml patcher/uv.lock ./
COPY patcher/src ./src

RUN uv sync --frozen --no-dev --no-editable


# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM python:3.14-alpine AS patcher

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    PATH="/app/.venv/bin:$PATH" \
    HOME="/home/trivyal" \
    DOCKER_CONFIG="/tmp/.docker"

# Copa binary
COPY --from=copa-downloader /usr/local/bin/copa /usr/local/bin/copa

WORKDIR /app

COPY --from=python-builder /app/.venv /app/.venv

RUN pip uninstall -y pip && \
    apk upgrade --no-cache && \
    addgroup -S trivyal && \
    adduser -S -G trivyal -h /home/trivyal trivyal && \
    mkdir -p /home/trivyal && \
    chown trivyal:trivyal /home/trivyal

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8101/health || exit 1

USER trivyal

EXPOSE 8101

CMD ["python", "-m", "trivyal_patcher.main"]
