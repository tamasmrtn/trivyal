# Trivyal — Architecture Document

> A lightweight, Beszel-style container vulnerability scanner and patcher with a hub-agent model, powered by Trivy and Copa.

---

## 1. Overview

Trivyal is a self-hosted vulnerability management tool designed for small homelab and multi-server Docker environments. It follows the same hub-agent pattern as Beszel: a lightweight agent runs on each host, scans local containers with Trivy, and ships results to a central hub that aggregates and displays everything in a single UI. An optional patcher sidecar enables in-place OS-level vulnerability remediation using Copa, without rebuilding images or touching a registry.

---

## 2. Feature Set

### Hub
- Dashboard showing all connected agents and their status (online / offline / scanning)
- **Priorities page** — unified action signal split into two sections:
  - *Fix Today* — Docker configuration issues (privileged containers, host network, missing resource limits, etc.) with severity and status filters
  - *Update When You Can* — image-centric CVE view grouped by image, showing fixable CVE counts and per-severity breakdowns
  - **One-click patching** — "Patch" button on images with fixable CVEs; streams Copa output live in a terminal dialog
- **Patches page** — full history of patch and restart operations with status tracking
- **Patch coordinator** — orchestrates the patch lifecycle: creates `PatchRequest`, sends `patch_trigger` via WebSocket, streams logs via SSE, handles `patch_result` and `restart_result` messages
- **Revert detection** — when a subsequent scan shows the image no longer matches the patched tag, the aggregator marks the associated `RestartRequest` as reverted
- Aggregated vulnerability view across all hosts — filterable by severity, status, and fixable CVEs
- Per-host and per-container drill-down view
- Finding timeline — tracks when CVEs appeared and when they were resolved
- Diff view between scans — highlights new findings and fixed findings
- Risk acceptance — mark a finding as accepted with a reason and expiry date; revoke acceptance; false positive flagging
- Scan history — full log of every scan run per host
- Agent management UI — add, remove, and view agents; copy-paste Docker Compose snippet for quick agent deploy
- Dark mode UI (default dark, toggleable)
- Single admin user with token-based API access

### Agent
- Automatic discovery of all running containers via Docker socket
- Trivy image scan per container on a configurable schedule (default: nightly)
- **Docker configuration scanning** — inspects each container via the Docker API and flags misconfigurations: privileged mode, host network/PID/IPC namespaces, missing read-only root filesystem, missing CPU/memory limits, sensitive volume mounts
- On-demand scan trigger from hub
- **Patcher sidecar integration** — discovers the sidecar via `TRIVYAL_PATCH_SIDECAR_URL`, reports `patching_available` in host metadata, and forwards `patch_trigger` / `restart_trigger` messages to the sidecar. Streams patch logs back to the hub in real time.
- Ships both Trivy scan results and misconfig results to hub via authenticated WebSocket connection
- Caches last scan results locally for resilience if hub is temporarily unreachable
- Self-reports host metadata (hostname, Docker version, OS, agent version, patching availability)
- Lightweight — runs as a single Docker container, mounts Docker socket read-only

### Patcher Sidecar
- Standalone Python HTTP server (`aiohttp.web`) running alongside the agent
- **`POST /patch`** — invokes Copa to patch OS-level packages in a container image. Streams NDJSON log lines as Copa runs. Requires a Trivy JSON report (the hub sends the latest `trivy_raw` from `ScanResult`) and a target tag for the patched image.
- **`POST /restart`** — stops the old container, inspects its full config (ports, volumes, env, labels, network), recreates it with the patched image, and starts it. Blocks if the container has anonymous volumes (data would be lost).
- **`GET /health`** — liveness check; agent polls this to determine `patching_available`
- Needs Docker socket with write access + the Copa binary (both provided in the Dockerfile via a multi-stage build from `ghcr.io/project-copacetic/copacetic`)
- Uses stdlib `http.client` over Unix socket for Docker Engine API calls (same pattern as the agent's `docker_socket.py`)

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
 │                       │◄──────────────────────────│
 │                       │     {type: misconfig_result│
 │                       │      data: <check JSON>}   │
 │                       │                            │
 │                       │  7. Hub stores ScanResult  │
 │                       │     + Findings +           │
 │                       │     MisconfigFindings;     │
 │                       │     agent status → online  │
```

**Error cases:**
- `404 Not Found` — agent ID does not exist in the database.
- `409 Conflict` — agent exists but is not currently connected via WebSocket (offline or scanning).

The trigger is fire-and-forget from the REST perspective: the `202 Accepted` response confirms the message was delivered to the agent over the WebSocket. There is no long-polling or callback — the UI can poll the scan history endpoint to see new results appear.

## 3.2 Patch + Restart Flow

The hub orchestrates patching via the agent, which proxies to the patcher sidecar. The UI subscribes to an SSE stream to display Copa build logs in real time.

```
User                    Hub                         Agent              Patcher Sidecar
 │                       │                            │                     │
 │  1. Click "Patch"     │                            │                     │
 │     in Priorities UI  │                            │                     │
 │──────────────────────►│                            │                     │
 │                       │                            │                     │
 │   POST /api/v1/       │                            │                     │
 │   patches             │                            │                     │
 │   {agent_id,          │                            │                     │
 │    container_id,      │                            │                     │
 │    image_name}        │                            │                     │
 │                       │                            │                     │
 │                       │  2. Hub creates             │                     │
 │                       │     PatchRequest (PENDING), │                     │
 │                       │     looks up latest         │                     │
 │                       │     trivy_raw for container │                     │
 │                       │                            │                     │
 │                       │  3. Hub sends over WS:     │                     │
 │                       │     {type: patch_trigger,   │                     │
 │                       │      request_id, image,     │                     │
 │                       │      trivy_report,          │                     │
 │                       │      patched_tag}           │                     │
 │                       │───────────────────────────►│                     │
 │                       │                            │                     │
 │  4. 201 Created       │                            │  5. Agent POSTs     │
 │◄──────────────────────│                            │     to sidecar      │
 │  { id, status }       │                            │     /patch          │
 │                       │                            │────────────────────►│
 │                       │                            │                     │
 │  5. UI subscribes to  │                            │  6. Copa runs,      │
 │     SSE: GET          │                            │     streams NDJSON  │
 │     /patches/{id}/logs│                            │◄────────────────────│
 │◄──────────────────────│                            │                     │
 │                       │  7. Agent forwards each    │                     │
 │                       │     log line as:            │                     │
 │                       │     {type: patch_log,       │                     │
 │                       │      request_id, line}      │                     │
 │                       │◄───────────────────────────│                     │
 │                       │                            │                     │
 │  (SSE log lines) ◄───│  8. Hub publishes to       │                     │
 │                       │     LogBuffer → SSE        │                     │
 │                       │                            │                     │
 │                       │  9. Agent sends:           │                     │
 │                       │     {type: patch_result,    │                     │
 │                       │      request_id, status,    │                     │
 │                       │      patched_tag}           │                     │
 │                       │◄───────────────────────────│                     │
 │                       │                            │                     │
 │                       │  10. Hub updates            │                     │
 │                       │      PatchRequest →         │                     │
 │                       │      COMPLETED, stores      │                     │
 │                       │      patched_tag + logs     │                     │
 │                       │                            │                     │
 │  11. Click "Restart"  │                            │                     │
 │──────────────────────►│                            │                     │
 │   POST /patches/      │                            │                     │
 │   {id}/restart        │                            │                     │
 │                       │  12. Hub creates            │                     │
 │                       │      RestartRequest,        │                     │
 │                       │      sends restart_trigger  │                     │
 │                       │───────────────────────────►│                     │
 │                       │                            │  13. Sidecar stops, │
 │                       │                            │      recreates, and │
 │                       │                            │      starts container│
 │                       │                            │────────────────────►│
 │                       │                            │◄────────────────────│
 │                       │  14. Agent sends:          │                     │
 │                       │      {type: restart_result} │                     │
 │                       │◄───────────────────────────│                     │
```

**Error cases:**
- `404 Not Found` — agent or container does not exist.
- `409 Conflict` — agent is not connected, or does not have `patching_available` in its host metadata.
- `400 Bad Request` — restart requested but patch is not in `completed` status.

**Revert detection:** On each subsequent scan, the aggregator compares the incoming `ArtifactName` against the `patched_tag` stored on any completed `RestartRequest` for that container. If they don't match, the restart is marked as reverted (`reverted_at` is set). This surfaces in the Patches page UI.

---

## 4. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| **Hub backend** | Python 3.14 + FastAPI | Async, lightweight, great WebSocket support |
| **Hub database** | SQLite via SQLModel + Alembic | Zero-config, sufficient for homelab scale; Alembic runs migrations automatically at startup |
| **Hub frontend** | React + shadcn/ui + Tailwind CSS | Excellent built-in dark mode, same UI library family Beszel uses (shadcn-svelte), polished components |
| **Agent** | Python 3.14 | Matches hub, easy to containerise; talks to Docker Engine API directly over Unix socket via stdlib `http.client` (no third-party dependency) |
| **Patcher sidecar** | Python 3.14 + aiohttp | Lightweight HTTP server; streams NDJSON from Copa subprocess; uses stdlib `http.client` for Docker Engine API (same pattern as agent) |
| **Package management** | uv | Fast, reliable Python package and project manager; replaces pip + venv; lockfile-based reproducible installs |
| **Scanner** | Trivy (CLI, invoked by agent) | Best-in-class container scanning |
| **Patcher** | Copa (CLI, invoked by patcher sidecar) | Patches OS-level packages in container images without rebuilding; works with Trivy reports directly |
| **Auth** | Ed25519 keypair + token (PyNaCl) | Lightweight, same approach as Beszel |
| **Communication** | WebSocket (hub acts as server, agent connects) | Persistent connection, low overhead, allows hub-initiated scan triggers and patch commands |
| **Containerisation** | Docker Compose (hub + agent + optional patcher sidecar) | Simple self-hosted deployment |

### Why uv?
uv replaces `pip`, `venv`, and `requirements.txt` with a single fast tool. Each service (`hub/`, `agent/`, `patcher/`) has a `pyproject.toml` (PEP 517/518 compliant) and a `uv.lock` lockfile for fully reproducible builds. The `src/` layout enforces proper package installation and avoids import path ambiguity.

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
│  │                         │    │  WSS  │  │  - Sidecar proxy          │   │
│  │  - Agent manager        │    │       │  └───────────┬───────────┬───┘   │
│  │  - Scan aggregator      │    │       │              │           │ HTTP  │
│  │  - Patch coordinator    │    │       │              │   ┌───────▼─────┐ │
│  │  - Auth / token mgmt    │    │       │              │   │   Patcher   │ │
│  │  - Risk acceptance mgmt │    │       │              │   │  Sidecar    │ │
│  └──────────┬──────────────┘    │       │              │   │ (Copa+Docker│ │
│             │                   │       │              │   │  write)     │ │
│  ┌──────────▼──────────────┐    │       │              │   └──────┬──────┘ │
│  │       SQLite DB         │    │       │              │          │        │
│  └─────────────────────────┘    │       │   /var/run/docker.sock (ro + rw) │
└─────────────────────────────────┘       └──────────────────────────────────┘
                                          ┌──────────────────────────────────┐
                                          │   Server N (Agent + Patcher)     │
                                          │   (same pattern, additional host)│
                                          └──────────────────────────────────┘
```

The agent mounts the Docker socket read-only for container discovery and scanning. The patcher sidecar mounts it read-write for stop/create/start operations. The agent communicates with the patcher over HTTP on the Docker network (default `http://trivyal-patcher:8101`).

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
├── image_tag
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

MisconfigFinding
├── id
├── container_id (FK)
├── agent_id (FK)
├── check_id            # e.g. PRIV_001, HOST_NET
├── severity (CRITICAL | HIGH | MEDIUM | LOW | INFO)
├── title
├── fix_guideline
├── status (active | fixed | accepted | false_positive)
├── first_seen
└── last_seen

PatchRequest
├── id
├── agent_id (FK)
├── container_id (FK)
├── image_name
├── patched_tag          # e.g. nginx:1.25-trivyal-patched
├── status (pending | running | completed | failed)
├── original_finding_count
├── patched_finding_count
├── log_lines (JSON)     # Copa build output, persisted after completion
├── error_message
├── requested_at
└── completed_at

RestartRequest
├── id
├── patch_request_id (FK)
├── container_id (FK)
├── status (pending | running | completed | failed | blocked)
├── block_reason         # e.g. "container has anonymous volumes"
├── error_message
├── requested_at
├── completed_at
└── reverted_at          # set by aggregator when patched image is rolled back
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
GET    /api/v1/findings                    # all findings (filterable: ?severity=&status=&agent_id=&cve_id=&package=&container_id=&fixable=&image_name=; sortable: ?sort_by=severity|status|cve_id|package_name|container|first_seen|last_seen&sort_dir=asc|desc)
GET    /api/v1/findings/{id}               # single finding detail
PATCH  /api/v1/findings/{id}               # update status (accept | false_positive | reopen)

# Risk Acceptances (finding sub-resource)
POST   /api/v1/findings/{id}/acceptances   # create risk acceptance { reason, expires_at }
DELETE /api/v1/findings/{id}/acceptances/{acceptance_id}  # revoke acceptance

# Misconfigurations
GET    /api/v1/misconfigurations           # all misconfig findings (filterable: ?severity=&status=&agent_id=&sort_by=&sort_dir=&page=&page_size=)
GET    /api/v1/misconfigurations/{id}      # single misconfig detail
PATCH  /api/v1/misconfigurations/{id}      # update status (accept | false_positive | reopen)
POST   /api/v1/misconfigurations/{id}/acceptances   # create risk acceptance
DELETE /api/v1/misconfigurations/{id}/acceptances/{acceptance_id}  # revoke acceptance

# Images
GET    /api/v1/images                      # image-centric CVE summary (filterable: ?agent_id=&fixable=; sortable: ?sort_by=fixable_count|name&sort_dir=asc|desc)

# Dashboard
GET    /api/v1/dashboard/summary           # severity counts + agent status counts + misconfig active count + fixable CVE count — ?fixable=true
GET    /api/v1/dashboard/patch-summary     # patch stats: total_patched, findings_resolved, patching_available

# Patches
POST   /api/v1/patches                     # create + trigger patch → 201 { id, status }
GET    /api/v1/patches                     # list patches (filterable: ?status=&agent_id=; paginated)
GET    /api/v1/patches/{id}                # patch detail with nested restarts list
GET    /api/v1/patches/{id}/logs           # SSE stream of Copa build logs (text/event-stream)
POST   /api/v1/patches/{id}/restart        # trigger container restart → 202 { id, status }
GET    /api/v1/restarts/{id}               # restart detail

# Insights
GET    /api/v1/insights/summary            # aggregate counts for the time window — ?window=<days> (7 | 30 | 90) &fixable=true
GET    /api/v1/insights/trend              # daily severity breakdown + new/resolved delta — ?window=<days>
GET    /api/v1/insights/agents/trend       # per-agent daily total findings — ?window=<days>
GET    /api/v1/insights/top-cves           # most-widespread CVEs ranked by container/agent count — ?window=<days>

# WebSocket (agent transport — not versioned)
WS     /ws/agent                           # agent connection endpoint (token in header)
```

---

## 8. Directory Structure

Python services use the `src/` layout (PEP 517 standard): source lives under `src/<package>/` so the package is never importable without installation, preventing accidental relative-import bugs. Each service (`hub/`, `agent/`, `patcher/`) is an independent uv project with its own `pyproject.toml` and `uv.lock`. Tests live in a top-level `tests/` directory per service, mirroring the `src/` tree.

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
│   │       │       ├── patches.py          # Patch + restart CRUD, SSE log stream
│   │       │       ├── dashboard.py
│   │       │       ├── insights.py
│   │       │       ├── misconfigurations.py
│   │       │       └── images.py
│   │       ├── core/                       # Business logic (no FastAPI deps)
│   │       │   ├── auth.py                 # Token + Ed25519 key management
│   │       │   ├── aggregator.py           # Processes Trivy results + revert detection
│   │       │   ├── misconfig_aggregator.py # Processes incoming misconfig results
│   │       │   ├── patch_coordinator.py    # Patch lifecycle orchestration
│   │       │   ├── log_buffer.py           # In-memory log buffer for SSE streaming
│   │       │   └── scheduler.py           # Periodic tasks (cleanup, etc.)
│   │       ├── db/
│   │       │   ├── models.py               # SQLModel table definitions
│   │       │   ├── session.py              # Async engine + session factory
│   │       │   └── migrations/             # Alembic env.py + revision scripts
│   │       │       └── versions/           # 0001_initial_schema.py, 0002_priorities_feature.py, …
│   │       ├── schemas/                    # Pydantic request/response models
│   │       │   ├── agents.py
│   │       │   ├── findings.py
│   │       │   ├── misconfigs.py
│   │       │   ├── images.py
│   │       │   ├── patches.py
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
│   │       │   ├── docker_socket.py        # Thin stdlib HTTP client over Docker Unix socket
│   │       │   ├── docker_client.py        # Discover running containers (uses docker_socket)
│   │       │   ├── trivy_runner.py         # Invoke Trivy, parse output
│   │       │   ├── misconfig_runner.py     # Docker API misconfig checks (uses docker_socket)
│   │       │   ├── sidecar_client.py        # HTTP client for patcher sidecar
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
├── patcher/                                # Copa patcher sidecar (uv project)
│   ├── src/
│   │   └── trivyal_patcher/
│   │       ├── __init__.py
│   │       ├── main.py                     # Entry point (aiohttp.web.run_app)
│   │       ├── config.py                   # Settings: port, docker_socket, copa_binary
│   │       ├── server.py                   # HTTP server: /health, /patch, /restart
│   │       ├── copa_runner.py              # Copa subprocess wrapper, yields NDJSON
│   │       ├── container_ops.py            # Container restart logic
│   │       └── docker_client.py            # Stdlib HTTP-over-Unix-socket (write ops)
│   ├── tests/
│   │   ├── test_copa_runner.py
│   │   ├── test_container_ops.py
│   │   └── test_server.py
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile                          # Multi-stage: Copa from ghcr.io + Python runtime
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
│   │   │   │   │   ├── SummaryCards.tsx
│   │   │   │   │   └── PatchSummaryCard.tsx   # patch stats card (patched count, findings resolved)
│   │   │   │   ├── hooks/
│   │   │   │   │   └── useDashboard.ts
│   │   │   │   └── index.ts
│   │   │   ├── insights/
│   │   │   │   ├── components/
│   │   │   │   │   ├── InsightsSummaryCards.tsx  # 4 KPI cards (active, crit+high, new, fix rate)
│   │   │   │   │   ├── VulnerabilityTrendChart.tsx  # severity line chart + scan event markers
│   │   │   │   │   ├── NewVsResolvedChart.tsx    # diverging bar chart (new red / resolved green)
│   │   │   │   │   ├── AgentTrendChart.tsx       # per-agent trend lines (8-colour palette)
│   │   │   │   │   ├── SeverityDonutChart.tsx    # donut with centre total + legend
│   │   │   │   │   └── TopCvesTable.tsx          # top CVEs ranked by container/agent spread
│   │   │   │   ├── hooks/
│   │   │   │   │   └── useInsights.ts            # parallel fetch of all 4 insights endpoints
│   │   │   │   └── index.ts
│   │   │   └── priorities/
│   │   │       ├── components/
│   │   │       │   ├── FixTodaySection.tsx        # misconfig findings table with filters
│   │   │       │   ├── UpdateWhenYouCanSection.tsx # image CVE table with fixable counts
│   │   │       │   ├── MisconfigStatusBadge.tsx   # status badge (active/fixed/accepted/false_positive)
│   │   │       │   ├── MisconfigDetailDialog.tsx  # detail dialog with accept/false_positive actions
│   │   │       │   └── PatchDialog.tsx            # Copa patch dialog with live log stream
│   │   │       ├── hooks/
│   │   │       │   ├── useMisconfigs.ts           # paginated misconfig hook
│   │   │       │   └── useImages.ts               # image CVE summary hook
│   │   │       └── index.ts
│   │   ├── pages/                          # Route-level page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Agents.tsx
│   │   │   ├── Findings.tsx
│   │   │   ├── FindingDetail.tsx
│   │   │   ├── Insights.tsx
│   │   │   ├── Patches.tsx                 # Patch history table with status badges
│   │   │   ├── Priorities.tsx
│   │   │   └── ScanHistory.tsx
│   │   ├── lib/
│   │   │   ├── api/                        # Typed API client (one file per resource)
│   │   │   │   ├── client.ts               # Axios/fetch base, auth header injection
│   │   │   │   ├── agents.ts
│   │   │   │   ├── findings.ts
│   │   │   │   ├── insights.ts
│   │   │   │   ├── misconfigs.ts
│   │   │   │   ├── images.ts
│   │   │   │   ├── patches.ts             # Patch API + SSE log subscription
│   │   │   │   ├── dashboard.ts
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
      PATCH_SIDECAR_URL: "http://trivyal-patcher:8101"  # optional: enable patching

  trivyal-patcher:                  # optional: enables in-place patching
    image: trivyal/patcher:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # read-write for container ops
```

---

## 10. UI Pages

| Page | Description |
|---|---|
| **Dashboard** | Summary cards (total CVEs by severity, fixable CVE count, active misconfigs), agent status grid; *Fixable only* toggle to filter to CVEs with upstream fixes available |
| **Priorities** | Unified action signal: *Fix Today* shows Docker configuration issues (filterable by severity and status, clickable rows open a detail dialog with accept/false_positive actions); *Update When You Can* shows images grouped by name with fixable CVE counts and severity breakdowns, "Patch" button per image (when agent has patching enabled), rows link to Findings filtered by image |
| **Patches** | History of all patch and restart operations. Table shows image, agent, status badge (pending/running/completed/failed), finding count delta, and timestamps. Status badges: Patched (blue), Applied (green), Reverted (amber), Failed (red) |
| **Agents** | List of registered agents, status, last scan time, add/remove agent, copy deploy snippet |
| **Findings** | Full findings table with filters (severity, status, agent, CVE ID, package, fixable, image name) and sortable columns; *Fixable only* toggle; image name badge when filtered from Priorities |
| **Insights** | Time-windowed analytics (7 / 30 / 90 days): KPI summary cards (active findings, critical+high count, new this period, fix rate); *Fixable only* toggle; severity trend line chart with scan-event markers; new-vs-resolved diverging bar chart; per-agent trend lines; severity donut chart; top CVEs table ranked by container and agent spread |
| **Scan History** | Timeline of scans per agent/container, diff view (new / fixed per scan) |
| **Finding Detail** | Single CVE detail — CVE description (sourced from Trivy/NVD), affected containers, fix version, NVD link, risk acceptance form |
