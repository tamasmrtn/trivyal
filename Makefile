.PHONY: init init-hub init-agent init-ui init-hooks init-integration \
        test test-hub test-agent test-ui test-integration \
        dev-hub dev-agent dev-ui lint \
        scan-hub scan-agent

# ── Init ──────────────────────────────────────────────────────────────────────

init: init-hub init-agent init-ui init-hooks init-integration

init-hub:
	cd hub && uv sync

init-agent:
	cd agent && uv sync

init-ui:
	cd ui && npm install

init-hooks:
	uv tool install pre-commit
	pre-commit install

init-integration:
	cd integration && uv sync

# ── Lint ──────────────────────────────────────────────────────────────────────

lint:
	pre-commit run --all-files

# ── Tests ─────────────────────────────────────────────────────────────────────

test: test-hub test-agent test-ui

test-hub:
	cd hub && uv run pytest tests/ -vv

test-agent:
	cd agent && uv run pytest tests/ -vv

test-ui:
	cd ui && npm run test:run

test-integration:
	cd integration && docker compose -f docker-compose.test.yml up --build --wait -d
	cd integration && uv run pytest tests/ -v --tb=short; \
	  EXIT=$$?; \
	  docker compose -f docker-compose.test.yml down -v; \
	  exit $$EXIT

# ── Dev ───────────────────────────────────────────────────────────────────────

dev-hub:
	@mkdir -p hub/data
	cd hub && TRIVYAL_DATA_DIR=data uv run fastapi dev --port 8099 src/trivyal_hub/main.py

dev-agent:
	cd agent && uv run python -m trivyal_agent.main

dev-ui:
	cd ui && npm run dev

# ── Scan ──────────────────────────────────────────────────────────────────────

scan-hub:
	docker build -t trivyal-hub:scan -f hub/Dockerfile .
	docker run --rm \
	  -v /var/run/docker.sock:/var/run/docker.sock \
	  -v "$(PWD)/.trivyignore":/.trivyignore \
	  aquasec/trivy:latest image \
	  --ignorefile /.trivyignore \
	  --severity CRITICAL,HIGH \
	  --ignore-unfixed \
	  trivyal-hub:scan

scan-agent:
	docker build -t trivyal-agent:scan -f agent/Dockerfile .
	docker run --rm \
	  -v /var/run/docker.sock:/var/run/docker.sock \
	  -v "$(PWD)/.trivyignore":/.trivyignore \
	  aquasec/trivy:latest image \
	  --ignorefile /.trivyignore \
	  --severity CRITICAL,HIGH \
	  --ignore-unfixed \
	  trivyal-agent:scan

# ── Migrate db ──────────────────────────────────────────────────────────────────────

migrate:
	cd hub && TRIVYAL_DATABASE_URL=sqlite+aiosqlite:///dev.db uv run alembic upgrade head
	cd hub && TRIVYAL_DATABASE_URL=sqlite+aiosqlite:///dev.db uv run alembic revision --autogenerate
