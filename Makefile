.PHONY: init init-hub init-agent init-ui \
        test test-hub test-agent test-ui \
        dev-hub dev-agent dev-ui

# ── Init ──────────────────────────────────────────────────────────────────────

init: init-hub init-agent init-ui

init-hub:
	cd hub && uv sync

init-agent:
	cd agent && uv sync

init-ui:
	cd ui && npm install

# ── Tests ─────────────────────────────────────────────────────────────────────

test: test-hub test-agent test-ui

test-hub:
	cd hub && uv run pytest tests/ -vv

test-agent:
	cd agent && uv run pytest tests/ -vv

test-ui:
	cd ui && npm run test:run

# ── Dev ───────────────────────────────────────────────────────────────────────

dev-hub:
	cd hub && uv run fastapi dev src/trivyal_hub/main.py

dev-agent:
	cd agent && uv run python -m trivyal_agent.main

dev-ui:
	cd ui && npm run dev
