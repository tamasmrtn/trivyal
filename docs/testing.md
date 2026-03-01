# Trivyal — Testing Guide

---

## Python (hub & agent)

**Stack:** `pytest` + `pytest-asyncio` + `httpx` (async test client for FastAPI)

Run tests from the service directory:

```bash
cd hub   # or cd agent
uv run pytest
uv run pytest -v                  # verbose
uv run pytest tests/api/          # single folder
uv run pytest -k "test_create"    # filter by name
```

### Project config

Each service declares test dependencies in its `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "httpx",
]
```

### conftest.py

Shared fixtures live in `tests/conftest.py`. Keep it minimal — only what every test needs.

```python
# hub/tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from trivyal_hub.main import app
from trivyal_hub.db.session import get_session

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def client(session):
    app.dependency_overrides[get_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

### Test structure — use classes

Group related tests into a class per resource or behaviour. A class shares setup via `setup_method` or fixtures, and keeps related assertions together.

```python
# hub/tests/api/test_agents.py
import pytest

class TestListAgents:
    async def test_returns_empty_list_when_no_agents(self, client):
        response = await client.get("/api/v1/agents")
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_returns_registered_agents(self, client, session):
        # arrange: insert an agent via the DB session
        ...
        response = await client.get("/api/v1/agents")
        assert len(response.json()["data"]) == 1


class TestRegisterAgent:
    async def test_creates_agent_and_returns_token(self, client):
        response = await client.post("/api/v1/agents", json={"name": "server-1"})
        assert response.status_code == 201
        body = response.json()
        assert "token" in body
        assert "hub_public_key" in body

    async def test_rejects_duplicate_name(self, client):
        payload = {"name": "server-1"}
        await client.post("/api/v1/agents", json=payload)
        response = await client.post("/api/v1/agents", json=payload)
        assert response.status_code == 409


class TestDeleteAgent:
    async def test_removes_agent(self, client, session):
        ...

    async def test_returns_404_for_unknown_id(self, client):
        response = await client.delete("/api/v1/agents/nonexistent-id")
        assert response.status_code == 404
```

```python
# hub/tests/core/test_auth.py
import pytest
from trivyal_hub.core.auth import generate_token, hash_token, verify_token

class TestTokenGeneration:
    def test_generates_url_safe_string(self):
        token = generate_token()
        assert len(token) > 0
        assert " " not in token

    def test_tokens_are_unique(self):
        assert generate_token() != generate_token()


class TestTokenVerification:
    def test_correct_token_verifies(self):
        token = generate_token()
        token_hash = hash_token(token)
        assert verify_token(token, token_hash) is True

    def test_wrong_token_fails(self):
        token_hash = hash_token(generate_token())
        assert verify_token("wrong", token_hash) is False
```

### Naming conventions

| What | Convention |
|---|---|
| Test files | `test_<module>.py` |
| Test classes | `Test<Resource><Action>` (e.g. `TestRegisterAgent`) |
| Test methods | `test_<condition>_<expected>` (e.g. `test_missing_name_returns_422`) |

---

## React / UI

**Stack:** `vitest` + `@testing-library/react` + `@testing-library/user-event`

```bash
cd ui
npm test          # watch mode
npm run test:run  # single pass (CI)
```

### Config

```ts
// vite.config.ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
})
```

```ts
// tests/setup.ts
import "@testing-library/jest-dom"
```

### Example

```tsx
// tests/components/SeverityBadge.test.tsx
import { render, screen } from "@testing-library/react"
import { SeverityBadge } from "@/components/common/SeverityBadge"

describe("SeverityBadge", () => {
  it("renders the severity label", () => {
    render(<SeverityBadge severity="CRITICAL" />)
    expect(screen.getByText("CRITICAL")).toBeInTheDocument()
  })

  it("applies a distinct style for critical severity", () => {
    render(<SeverityBadge severity="CRITICAL" />)
    expect(screen.getByText("CRITICAL")).toHaveClass("bg-red-600")
  })
})
```

---

## What to test

Focus on behaviour, not implementation details.

| Layer | Test | Skip |
|---|---|---|
| API routes | status codes, response shape, auth enforcement | internal FastAPI wiring |
| Core logic | pure functions (token gen, fingerprint, aggregation) | I/O-heavy paths without mocking |
| UI components | renders correctly, responds to user interaction | CSS details, third-party component internals |

Keep test files short. If a test class grows beyond ~10 methods, split it into narrower classes.
