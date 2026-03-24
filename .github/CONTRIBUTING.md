# Contributing to Trivyal

Thanks for your interest in contributing to Trivyal! Whether it's a bug fix, a new feature, or improved documentation, your help is appreciated.

## Before you start

For non-trivial changes, please **open an issue first** so we can discuss the approach. This avoids wasted effort if the change doesn't align with the project's direction. Bug fixes and small improvements can go straight to a pull request.

## Development setup

This repository uses [uv](https://docs.astral.sh/uv/) for Python dependency management and npm for the UI.

```
trivyal/
├── hub/      # Hub service (FastAPI) — uv project
├── agent/    # Agent service (Python) — uv project
├── ui/       # React frontend (Vite + TypeScript)
└── docs/     # Architecture and guides
```

Install all dependencies and pre-commit hooks:

```bash
make init
```

## Running locally

```bash
make dev-hub     # FastAPI dev server on :8099
make dev-agent   # Run agent directly
make dev-ui      # Vite dev server with hot reload
```

## Testing

```bash
make test              # All unit tests (hub + agent + ui)
make test-hub          # Hub tests only
make test-agent        # Agent tests only
make test-ui           # UI tests only
make test-integration  # Integration tests (requires Docker)
make test-e2e          # E2E browser tests (requires Docker + Playwright)
```

Coverage thresholds are enforced in CI. Run `make test-hub-cov`, `make test-agent-cov`, or `make test-ui-cov` to check coverage locally before pushing.

## Linting

```bash
make lint   # Runs pre-commit hooks on all files
```

This runs ruff, eslint, prettier, bandit, checkov, pip-audit, and npm audit.

**Gotcha:** `ruff format` (targeting py314) strips parentheses from `except (A, B):` into `except A, B:`, but `check-ast` uses Python 3.13 which rejects that syntax. Avoid multi-exception clauses — use `except Exception:` instead.

## Commit messages

Use conventional commit style in imperative mood:

```
type(scope): short description

fix(hub): prevent duplicate findings on rescan
feat(agent): add configurable scan schedule
chore(deps): update FastAPI to v0.115
test(ui): add missing dashboard hook tests
```

Common types: `feat`, `fix`, `chore`, `test`, `refactor`, `docs`.

**Note:** Pre-commit hooks auto-fix files on commit. If a hook modifies files, the commit will fail — re-stage the changed files and commit again.

## Pull requests

- Fill in the [PR template](pull_request_template.md) — it's lightweight
- Keep PRs focused on a single concern
- Make sure `make test` and `make lint` pass before pushing
- Link the related issue in the PR description

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Please read it before participating.
