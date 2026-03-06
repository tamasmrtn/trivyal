# Trivyal — Architecture Document

> A lightweight, Beszel-style container vulnerability scanner with a hub-agent model, powered by Trivy.

---

## 1. Overview

Trivyal is a self-hosted vulnerability management tool designed for small homelab and multi-server Docker environments. It follows the same hub-agent pattern as Beszel: a lightweight agent runs on each host, scans local containers with Trivy, and ships results to a central hub that aggregates and displays everything in a single UI.

---

## 2. Feature Set

### Hub
- Dashboard showing all connected agents and their status (online / offline / scanning)
- Aggregated vulnerability view across all hosts — filterable by severity (Critical, High, Medium, Low, Unknown)
- Per-host and per-container drill-down view
- Finding timeline — tracks when CVEs appeared and when they were resolved
- Diff view between scans — highlights new findings and fixed findings
- Risk acceptance — mark a finding as accepted with a reason and expiry date
- False positive flagging per finding
- Scan history — full log of every scan run per host
- Notification support — webhook (Slack, Discord, Ntfy) on new Critical/High findings
- Agent management UI — add, remove, and view agents; copy-paste Docker Compose snippet for quick agent deploy
- Dark mode UI (default dark, toggleable)
- Single admin user with token-based API access

### Agent
- Automatic discovery of all running containers via Docker socket
- Trivy image scan per container on a configurable schedule (default: nightly)
- On-demand scan trigger from hub
- Ships results to hub via authenticated WebSocket connection
- Caches last scan results locally for resilience if hub is temporarily unreachable
- Self-reports host metadata (hostname, Docker version, OS, agent version)
- Lightweight — runs as a single Docker container, mounts Docker socket read-only

### Security
- Mutual authentication between hub and agent (token + fingerprint, modelled on Beszel)
- All communication over WebSocket (WSS in production)
- Agent is locked to the machine it registered on via a machine fingerprint
- Hub generates a registration token per agent; token is only valid for initial handshake

---

## 3. Hub-Agent Registration Flow

Modelled closely on Beszel's WebSocket + mutual auth approach:

```
User                    Hub                         Agent
 │                       │                            │
 │  1. Add Agent in UI   │                            │
 │──────────────────────►│                            │
 │                       │                            │
 │  2. Hub generates:    │                            │
 │     - registration    │                            │
 │       token           │                            │
 │     - Ed25519 keypair │                            │
 │       (hub pub key    │                            │
 │        shown in UI)   │                            │
 │                       │                            │
 │  3. User deploys      │                            │
 │     agent with:       │                            │
 │     TOKEN=xxx         │                            │
 │     KEY=<hub pub key> │                            │
 │     HUB_URL=xxx       │──────────────────────────►│
 │                       │                            │
 │                       │  4. Agent opens WebSocket  │
 │                       │◄──────────────────────────│
 │                       │     (sends TOKEN in header)│
 │                       │                            │
 │                       │  5. Hub verifies token,    │
 │                       │     signs challenge with   │
 │                       │     private key, sends back│
 │                       │────────────────────────── ►│
 │                       │                            │
 │                       │  6. Agent verifies sig     │
 │                       │     against stored hub     │
 │                       │     public key             │
 │                       │                            │
 │                       │  7. Agent sends machine    │
 │                       │◄──────────────────────────│
 │                       │     fingerprint            │
 │                       │     (hash of /etc/machine-id)
 │                       │                            │
 │                       │  8. Hub stores fingerprint,│
 │                       │     marks agent as active  │
 │                       │                            │
 │  9. Agent appears     │                            │
 │     online in UI      │                            │
 │◄──────────────────────│                            │
```

After initial registration, the agent reconnects using the same token + fingerprint pair. The fingerprint locks the agent to the original machine — a stolen token cannot be used from a different host.

## 3.1 On-Demand Scan Trigger Flow

Once an agent is connected, the hub can initiate a scan at any time via the REST API. The REST call is the entry point; the actual work is done over the existing WebSocket connection.

```
User                    Hub                         Agent
 │                       │                            │
 │  1. Click "Scan Now"  │                            │
 │     in Agents UI      │                            │
 │──────────────────────►│                            │
 │                       │                            │
 │   POST /api/v1/        │                            │
 │   agents/{id}/scans   │                            │
 │                       │                            │
 │                       │  2. Hub looks up agent     │
 │                       │     in DB (404 if missing) │
 │                       │                            │
 │                       │  3. Hub sends over WS:     │
 │                       │     {type: scan_trigger}   │
 │                       │────────────────────────── ►│
 │                       │   (409 if not connected)   │
 │                       │                            │
 │  4. 202 Accepted       │  5. Agent runs scan cycle  │
 │◄──────────────────────│     (discovers containers, │
 │  { job_id }           │     invokes Trivy per image)│
 │                       │                            │
 │                       │  6. Agent sends results    │
 │                       │◄──────────────────────────│
 │                       │     {type: scan_result,    │
 │                       │      data: <trivy JSON>}   │
 │                       │                            │
 │                       │  7. Hub stores ScanResult  │
 │                       │     + Findings in DB;      │
 │                       │     agent status → online  │
```

**Error cases:**
- `404 Not Found` — agent ID does not exist in the database.
- `409 Conflict` — agent exists but is not currently connected via WebSocket (offline or scanning).

The trigger is fire-and-forget from the REST perspective: the `202 Accepted` response confirms the message was delivered to the agent over the WebSocket. There is no long-polling or callback — the UI can poll the scan history endpoint to see new results appear.

---

## 4. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| **Hub backend** | Python 3.14 + FastAPI | Async, lightweight, great WebSocket support |
| **Hub database** | SQLite via SQLModel + Alembic | Zero-config, sufficient for homelab scale; Alembic runs migrations automatically at startup |
| **Hub frontend** | React + shadcn/ui + Tailwind CSS | Excellent built-in dark mode, same UI library family Beszel uses (shadcn-svelte), polished components |
| **Agent** | Python 3.14 | Matches hub, easy to containerise, simple Docker SDK |
| **Package management** | uv | Fast, reliable Python package and project manager; replaces pip + venv; lockfile-based reproducible installs |
| **Scanner** | Trivy (CLI, invoked by agent) | Best-in-class container scanning |
| **Auth** | Ed25519 keypair + token (PyNaCl) | Lightweight, same approach as Beszel |
| **Communication** | WebSocket (hub acts as server, agent connects) | Persistent connection, low overhead, allows hub-initiated scan triggers |
| **Containerisation** | Docker Compose (hub + agent each have their own image) | Simple self-hosted deployment |

### Why uv?
uv replaces `pip`, `venv`, and `requirements.txt` with a single fast tool. Each service (`hub/`, `agent/`) has a `pyproject.toml` (PEP 517/518 compliant) and a `uv.lock` lockfile for fully reproducible builds. The `src/` layout enforces proper package installation and avoids import path ambiguity.

### Why React + shadcn/ui?
Beszel uses SvelteKit + shadcn-svelte. Since Trivyal's backend is Python (not Go), the frontend is fully decoupled anyway, making React the more practical choice — larger ecosystem, more contributors, same shadcn design system. shadcn/ui ships with full dark mode support via Tailwind's `dark:` variant and a built-in theme toggle.

---

## 5. Architecture Diagram

```
┌─────────────────────────────────┐       ┌──────────────────────────────────┐
│           Server 2 (Hub)        │       │          Server 1 (Agent)        │
│                                 │       │                                  │
│  ┌─────────────────────────┐    │       │  ┌───────────────────────────┐   │
│  │      React UI           │    │       │  │      Trivyal Agent        │   │
│  │  (shadcn/ui dark mode)  │    │       │  │      (Python)             │   │
│  └──────────┬──────────────┘    │       │  │                           │   │
│             │ HTTP              │       │  │  - Docker socket listener │   │
│  ┌──────────▼──────────────┐    │       │  │  - Trivy runner           │   │
│  │      FastAPI Hub        │    │       │  │  - Result cache           │   │
│  │      (Python)           │◄───┼───────┼──│  - WebSocket client       │   │
│  │                         │    │  WSS  │  └───────────┬───────────────┘   │
│  │  - Agent manager        │    │       │              │                   │
│  │  - Scan aggregator      │    │       │   /var/run/docker.sock (ro)      │
│  │  - Auth / token mgmt    │    │       └──────────────────────────────────┘
│  │  - Notification sender  │    │
│  └──────────┬──────────────┘    │       ┌──────────────────────────────────┐
│             │                   │       │          Server 1 (Agent)        │
│  ┌──────────▼──────────────┐    │       │  (same pattern, second host)     │
│  │       SQLite DB         │    │       └──────────────────────────────────┘
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

---

## 6. Data Model (simplified)

```
Agent
├── id
├── name
├── token_hash
├── fingerprint
├── public_key (hub's key sent to this agent)
├── status (online | offline | scanning)
├── last_seen
└── host_metadata (JSON: hostname, OS, Docker version)

Container
├── id
├── agent_id (FK)
├── image_name
├── image_digest
└── last_scanned

ScanResult
├── id
├── container_id (FK)
├── scanned_at
├── trivy_raw (JSON blob)
└── finding_count (by severity, denormalised for speed)

Finding
├── id
├── scan_result_id (FK)
├── cve_id
├── package_name
├── installed_version
├── fixed_version
├── severity
├── description        # CVE description sourced from Trivy output (NVD/OSV)
├── status (active | fixed | accepted | false_positive)
├── first_seen
└── last_seen

RiskAcceptance
├── id
├── finding_id (FK)
├── reason
├── accepted_by
├── expires_at
└── created_at
```

---

## 7. API Surface (Hub)

All REST endpoints are versioned under `/api/v1/`. The WebSocket endpoint and health check are unversioned.

**Conventions:**
- List endpoints support `?page=` / `?page_size=` (default 50, max 200) and return a `{ data: [], total, page, page_size }` envelope.
- Mutation endpoints return the updated resource on success.
- Errors return `{ detail: string, code: string }` with appropriate HTTP status codes.
- `PATCH` uses partial JSON bodies (only include fields being changed).
- Async operations (e.g. scan triggers) return `202 Accepted` with a `{ job_id }` body.
- Auth header: `Authorization: Bearer <token>` on all `/api/v1/` routes.

```
# Health (no auth required)
GET    /api/health                         # liveness + readiness check

# Auth
POST   /api/v1/auth/token                  # login → returns { access_token, token_type }

# Agents
GET    /api/v1/agents                      # list agents (filterable: ?status=online|offline|scanning)
POST   /api/v1/agents                      # register agent → returns { id, token, hub_public_key }
GET    /api/v1/agents/{id}                 # get agent detail
DELETE /api/v1/agents/{id}                 # remove agent

# Scans (agent sub-resource)
POST   /api/v1/agents/{id}/scans           # trigger on-demand scan → 202 Accepted { job_id }
GET    /api/v1/agents/{id}/scans           # scan history for a specific agent

# Scans (global)
GET    /api/v1/scans                       # scan history across all agents (paginated)
GET    /api/v1/scans/{id}                  # scan detail + full Trivy output

# Findings
GET    /api/v1/findings                    # all findings (filterable: ?severity=&status=&agent_id=&cve_id=&package=&container_id=; sortable: ?sort_by=severity|status|cve_id|package_name|container|first_seen|last_seen&sort_dir=asc|desc)
GET    /api/v1/findings/{id}               # single finding detail
PATCH  /api/v1/findings/{id}               # update status (accept | false_positive | reopen)

# Risk Acceptances (finding sub-resource)
POST   /api/v1/findings/{id}/acceptances   # create risk acceptance { reason, expires_at }
DELETE /api/v1/findings/{id}/acceptances/{acceptance_id}  # revoke acceptance

# Dashboard
GET    /api/v1/dashboard/summary           # severity counts + agent status counts

# Insights
GET    /api/v1/insights/summary            # aggregate counts for the time window: active_findings, critical_high, new_in_period, fix_rate — ?window=<days> (7 | 30 | 90)
GET    /api/v1/insights/trend              # daily severity breakdown + new/resolved delta — ?window=<days>
GET    /api/v1/insights/agents/trend       # per-agent daily total findings — ?window=<days>
GET    /api/v1/insights/top-cves           # most-widespread CVEs ranked by container/agent count — ?window=<days>

# Settings
GET    /api/v1/settings                    # current notification + schedule config
PATCH  /api/v1/settings                    # update settings (webhooks, scan schedule)

# WebSocket (agent transport — not versioned)
WS     /ws/agent                           # agent connection endpoint (token in header)
```

---

## 8. Directory Structure

Python services use the `src/` layout (PEP 517 standard): source lives under `src/<package>/` so the package is never importable without installation, preventing accidental relative-import bugs. Each service is an independent uv project with its own `pyproject.toml` and `uv.lock`. Tests live in a top-level `tests/` directory per service, mirroring the `src/` tree.

The React frontend follows a feature-based organisation: shared primitives live in `components/` and `lib/`, while each product feature owns its own slice of components, hooks, and types under `features/`.

```
trivyal/
│
├── hub/                                    # Hub service (uv project)
│   ├── alembic.ini                         # Alembic config (developer CLI)
│   ├── src/
│   │   └── trivyal_hub/
│   │       ├── __init__.py
│   │       ├── main.py                     # FastAPI app factory + lifespan
│   │       ├── config.py                   # Settings via pydantic-settings
│   │       ├── api/
│   │       │   └── v1/
│   │       │       ├── __init__.py         # APIRouter for /api/v1
│   │       │       ├── agents.py
│   │       │       ├── findings.py
│   │       │       ├── scans.py
│   │       │       ├── dashboard.py
│   │       │       └── settings.py
│   │       ├── core/                       # Business logic (no FastAPI deps)
│   │       │   ├── auth.py                 # Token + Ed25519 key management
│   │       │   ├── aggregator.py           # Processes incoming scan results
│   │       │   ├── notifier.py             # Webhook notifications
│   │       │   └── scheduler.py           # Periodic tasks (cleanup, etc.)
│   │       ├── db/
│   │       │   ├── models.py               # SQLModel table definitions
│   │       │   ├── session.py              # Async engine + session factory
│   │       │   └── migrations/             # Alembic env.py + revision scripts
│   │       │       └── versions/           # Migration files (0001_initial_schema.py, …)
│   │       ├── schemas/                    # Pydantic request/response models
│   │       │   ├── agents.py
│   │       │   ├── findings.py
│   │       │   └── scans.py
│   │       └── ws/
│   │           └── manager.py             # WebSocket agent connection manager
│   ├── tests/
│   │   ├── conftest.py                     # Shared fixtures (test DB, async client)
│   │   ├── api/
│   │   │   ├── test_agents.py
│   │   │   ├── test_findings.py
│   │   │   └── test_scans.py
│   │   ├── core/
│   │   │   ├── test_auth.py
│   │   │   └── test_aggregator.py
│   │   └── ws/
│   │       └── test_manager.py
│   ├── pyproject.toml                      # uv project config + dependencies
│   ├── uv.lock
│   └── Dockerfile
│
├── agent/                                  # Agent service (uv project)
│   ├── src/
│   │   └── trivyal_agent/
│   │       ├── __init__.py
│   │       ├── main.py                     # Agent entrypoint
│   │       ├── config.py                   # Settings via pydantic-settings
│   │       ├── core/
│   │       │   ├── auth.py                 # Fingerprint + token logic
│   │       │   ├── docker_client.py        # Discover running containers
│   │       │   ├── trivy_runner.py         # Invoke Trivy, parse output
│   │       │   ├── cache.py                # Local result cache (JSON on disk)
│   │       │   └── scheduler.py           # Cron-style scan schedule
│   │       └── ws/
│   │           └── client.py               # WebSocket connection to hub
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── core/
│   │   │   ├── test_auth.py
│   │   │   ├── test_docker_client.py
│   │   │   └── test_trivy_runner.py
│   │   └── ws/
│   │       └── test_client.py
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile
│
├── ui/                                     # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── main.tsx                        # App entry, router setup
│   │   ├── components/
│   │   │   ├── ui/                         # Auto-generated shadcn/ui primitives
│   │   │   └── common/                     # Shared app-level components
│   │   │       ├── SeverityBadge.tsx
│   │   │       ├── ScanTimeline.tsx
│   │   │       └── PageLayout.tsx
│   │   ├── features/                       # Feature slices (co-locate components + hooks)
│   │   │   ├── agents/
│   │   │   │   ├── components/
│   │   │   │   │   ├── AgentCard.tsx
│   │   │   │   │   └── AgentTable.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   └── useAgents.ts
│   │   │   │   └── index.ts
│   │   │   ├── findings/
│   │   │   │   ├── components/
│   │   │   │   │   ├── FindingsTable.tsx
│   │   │   │   │   └── RiskAcceptanceForm.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   └── useFindings.ts
│   │   │   │   └── index.ts
│   │   │   ├── dashboard/
│   │   │   │   ├── components/
│   │   │   │   │   └── SummaryCards.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   └── useDashboard.ts
│   │   │   │   └── index.ts
│   │   │   └── insights/
│   │   │       ├── components/
│   │   │       │   ├── InsightsSummaryCards.tsx  # 4 KPI cards (active, crit+high, new, fix rate)
│   │   │       │   ├── VulnerabilityTrendChart.tsx  # severity line chart + scan event markers
│   │   │       │   ├── NewVsResolvedChart.tsx    # diverging bar chart (new red / resolved green)
│   │   │       │   ├── AgentTrendChart.tsx       # per-agent trend lines (8-colour palette)
│   │   │       │   ├── SeverityDonutChart.tsx    # donut with centre total + legend
│   │   │       │   └── TopCvesTable.tsx          # top CVEs ranked by container/agent spread
│   │   │       ├── hooks/
│   │   │       │   └── useInsights.ts            # parallel fetch of all 4 insights endpoints
│   │   │       └── index.ts
│   │   ├── pages/                          # Route-level page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Agents.tsx
│   │   │   ├── Findings.tsx
│   │   │   ├── FindingDetail.tsx
│   │   │   ├── Insights.tsx
│   │   │   ├── ScanHistory.tsx
│   │   │   └── Settings.tsx
│   │   ├── lib/
│   │   │   ├── api/                        # Typed API client (one file per resource)
│   │   │   │   ├── client.ts               # Axios/fetch base, auth header injection
│   │   │   │   ├── agents.ts
│   │   │   │   ├── findings.ts
│   │   │   │   ├── insights.ts
│   │   │   │   ├── scans.ts
│   │   │   │   └── types.ts                # Shared API response types
│   │   │   └── utils.ts
│   │   └── store/                          # Global client state (Zustand)
│   │       └── auth.ts
│   ├── tests/
│   │   ├── components/
│   │   │   └── SeverityBadge.test.tsx
│   │   └── features/
│   │       └── findings/
│   │           └── FindingsTable.test.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.hub.yml                  # Deploy hub (with local agent optional)
├── docker-compose.agent.yml                # Deploy agent-only on remote host
└── docs/
    ├── architecture.md                     # This document
    └── getting-started.md
```

---

## 9. Deployment

### Hub server (Server 2)
```yaml
# docker-compose.hub.yml
services:
  trivyal-hub:
    image: trivyal/hub:latest
    ports:
      - "8099:8099"
    volumes:
      - ./data:/app/data
    environment:
      SECRET_KEY: "change-me"
      DATA_DIR: /app/data

  trivyal-agent:                    # optional: monitor the hub server too
    image: trivyal/agent:latest
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./agent_data:/app/data
    environment:
      HUB_URL: "ws://localhost:8099"
      TOKEN: "<generated in UI>"
      KEY: "<hub public key from UI>"
```

### Agent-only server (Server 1)
```yaml
# docker-compose.agent.yml
services:
  trivyal-agent:
    image: trivyal/agent:latest
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./agent_data:/app/data
    environment:
      HUB_URL: "ws://server2:8099"
      TOKEN: "<generated in UI>"
      KEY: "<hub public key from UI>"
      SCAN_SCHEDULE: "0 2 * * *"   # cron, default nightly 2am
```

---

## 10. UI Pages

| Page | Description |
|---|---|
| **Dashboard** | Summary cards (total CVEs by severity), agent status grid, recent findings feed |
| **Agents** | List of registered agents, status, last scan time, add/remove agent, copy deploy snippet |
| **Findings** | Full findings table with filters (severity, status, agent, CVE ID, package) and sortable columns (severity, status, CVE ID, package, container, first seen, last seen); includes a **Container** column showing the originating container; bulk accept |
| **Insights** | Time-windowed analytics (7 / 30 / 90 days): KPI summary cards (active findings, critical+high count, new this period, fix rate); severity trend line chart with scan-event markers; new-vs-resolved diverging bar chart; per-agent trend lines; severity donut chart; top CVEs table ranked by container and agent spread |
| **Scan History** | Timeline of scans per agent/container, diff view (new / fixed per scan) |
| **Finding Detail** | Single CVE detail — CVE description (sourced from Trivy/NVD), affected containers, fix version, NVD link, risk acceptance form |
| **Settings** | Notification webhooks, scan schedule override, theme toggle |
