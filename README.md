<p align="center">
  <img src="docs/trivyal-logo-no-bg.png" alt="Trivyal" width="280" />
</p>

<p align="center">A lightweight, self-hosted container vulnerability scanner with a hub-agent model, powered by <a href="https://github.com/aquasecurity/trivy">Trivy</a>.</p>

Trivyal is designed for homelabs and small multi-server Docker environments. A lightweight agent runs on each host, scans local containers with Trivy, and ships results to a central hub that aggregates and displays everything in a single UI.

---

## Alternatives

**[Harbor](https://goharbor.io/)** is a CNCF-graduated container registry with built-in vulnerability scanning, image signing, and role-based access control. Use it if you need a private registry — the scanning is a bonus that comes with it. It operates at the registry level (scanning images on push), not the runtime level, so it won't catch containers running images that were pushed before a new CVE was disclosed.

**[DefectDojo](https://www.defectdojo.org/)** is a full DevSecOps vulnerability management platform. It ingests findings from many scanners (including Trivy), deduplicates them, tracks remediation, generates reports, and integrates with issue trackers and CI pipelines. Use it when you need a centralised security programme across multiple teams, products, and scanner types — it is a significant operational investment to run.

**Use Trivyal instead when** you run a homelab or a small multi-server Docker environment and want a single lightweight tool that tells you what vulnerabilities are running on your hosts right now — no registry, no pipeline, no dedicated security team required. Trivyal focuses on one thing: discovering what is actually running via the Docker socket, scanning it with Trivy, and surfacing new findings to you.

---

## Features

### Hub
- Dashboard showing all connected agents and their status (online / offline / scanning)
- **Priorities page** — unified action signal split into two sections:
  - *Fix Today* — Docker configuration issues (privileged containers, host network, missing resource limits, etc.) with severity and status filters
  - *Update When You Can* — image-centric CVE view grouped by image, showing fixable CVE counts and per-severity breakdowns
- Aggregated vulnerability view across all hosts — filterable by severity, status, and fixable CVEs
- Per-host and per-container drill-down
- Finding timeline — tracks when CVEs appeared and when they were resolved
- Auto-marks vulnerability findings as **FIXED** when absent from a subsequent scan
- Diff view between scans — highlights new and fixed findings
- Risk acceptance — mark a finding as accepted with a reason and expiry date; automatically re-activates when the acceptance expires
- False positive flagging per finding
- Full scan history log per host
- Agent management UI — add, remove, and view agents; copy-paste Docker Compose snippet for quick deploy
- Dark mode UI (default dark, toggleable)
- Single admin user with token-based API access

### Agent
- Automatic discovery of all running containers via Docker socket
- Trivy image scan per container on a configurable schedule (default: nightly)
- **Digest-based scan skipping** — unchanged images are skipped entirely; forced rescan after a configurable number of days regardless
- **Docker configuration scanning** — inspects each container via the Docker API and flags misconfigurations (privileged mode, host network/PID/IPC, missing read-only root filesystem, missing resource limits, sensitive volume mounts)
- On-demand scan trigger from hub
- Ships results to hub via authenticated WebSocket connection
- Caches last scan results locally for resilience if hub is temporarily unreachable
- Self-reports host metadata (hostname, Docker version, OS, agent version)
- Lightweight — runs as a single Docker container, mounts Docker socket read-only

---

## Architecture

Trivyal uses a hub-agent model. The hub is the central server that aggregates scan results and serves the UI. Agents run on each Docker host, perform scans, and connect back to the hub over a persistent, authenticated WebSocket connection.

```
┌─────────────────────────────────┐       ┌──────────────────────────────────┐
│           Hub Server            │       │          Agent Host               │
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
│  └──────────┬──────────────┘    │
│             │                   │
│  ┌──────────▼──────────────┐    │
│  │       SQLite DB         │    │
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

### Tech Stack

| Layer | Choice |
|---|---|
| Hub backend | Python 3.14 + FastAPI |
| Hub database | SQLite via SQLModel + Alembic |
| Hub frontend | React + shadcn/ui + Tailwind CSS |
| Agent | Python 3.14 |
| Package management | uv |
| Scanner | Trivy (CLI, invoked by agent) |
| Auth | Ed25519 keypair + token (PyNaCl) |
| Communication | WebSocket (persistent, allows hub-initiated scan triggers) |
| Containerisation | Docker Compose |

### Registration Flow

When you add an agent in the UI, the hub generates a registration token and an Ed25519 keypair. You deploy the agent with the token, hub URL, and hub public key. On first connect, the hub verifies the token and the agent verifies the hub's identity via a signed challenge. After the handshake, the agent's machine fingerprint (derived from `/etc/machine-id`) is stored — locking that token to the original host.

---

## Getting Started

### Prerequisites

- Docker and Docker Compose on all hosts
- The hub host must be reachable by all agent hosts over TCP (default port `8099`)

### 1. Deploy the Hub

On the hub host, clone the repository and create your `.env`:

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
TRIVYAL_SECRET_KEY=<output of: openssl rand -hex 32>
TRIVYAL_ADMIN_PASSWORD=<your admin password>
```

Build and start the hub:

```bash
docker compose -f docker-compose.hub.yml up --build -d
```

Open `http://<hub-host>:8099` in your browser and log in with your admin credentials.

### 2. Add an Agent

1. Go to **Agents** in the UI and click **Add Agent**.
2. Copy the **Token** and **Hub Public Key** shown in the dialog.
3. On the agent host, clone the repository and set the required variables:

```env
TRIVYAL_HUB_URL=ws://<hub-host>:8099
TRIVYAL_TOKEN=<token from UI>
TRIVYAL_KEY=<hub public key from UI>
DOCKER_GID=<output of: stat -c '%g' /var/run/docker.sock>
```

4. Build and start the agent:

```bash
docker compose -f docker-compose.agent.yml up --build -d
```

The agent will appear online in the hub UI within a few seconds. Scans run on the configured schedule (default: nightly at 02:00), or you can trigger one immediately from the **Agents** page.

---

## Environment Variables

All variables use the `TRIVYAL_` prefix and are read from the environment or a `.env` file. Copy `.env.example` to get started.

### Hub

| Variable | Required | Default | Description |
|---|---|---|---|
| `TRIVYAL_SECRET_KEY` | **yes** | — | Long random string for signing tokens. Generate with `openssl rand -hex 32`. |
| `TRIVYAL_ADMIN_PASSWORD` | no | `admin` | Password for the web UI admin login. Change this. |
| `TRIVYAL_DATA_DIR` | no | `/app/data` | Directory where the SQLite database is stored. |
| `TRIVYAL_DATABASE_URL` | no | derived | Full SQLite connection URL. Overrides `TRIVYAL_DATA_DIR` if set. |
| `TRIVYAL_TZ` | no | `UTC` | Timezone for all hub timestamps (e.g. `Europe/London`). |
| `TRIVYAL_HOST` | no | `0.0.0.0` | Interface to bind. |
| `TRIVYAL_PORT` | no | `8099` | Port to listen on. |
| `TRIVYAL_ACCEPTANCE_EXPIRY_INTERVAL` | no | `3600` | Seconds between risk-acceptance expiry sweeps. |
| `TRIVYAL_STATIC_DIR` | no | `/app/static` | Directory containing the built React UI. Present automatically in Docker; not used in dev. |

### Agent

| Variable | Required | Default | Description |
|---|---|---|---|
| `TRIVYAL_HUB_URL` | **yes** | `ws://localhost:8099` | WebSocket URL of the hub. Use `wss://` in production. |
| `TRIVYAL_TOKEN` | **yes** | — | Registration token generated in the hub UI (Agents → Add Agent). |
| `TRIVYAL_KEY` | **yes** | — | Hub Ed25519 public key shown alongside the token in the hub UI. |
| `TRIVYAL_SCAN_SCHEDULE` | no | `0 2 * * *` | Cron expression for scheduled scans (default: nightly at 02:00). |
| `TRIVYAL_MAX_SCAN_AGE_DAYS` | no | `3` | Force a full rescan after this many days even if the image digest is unchanged. |
| `TRIVYAL_DATA_DIR` | no | `/app/data` | Directory for the local scan result cache. |
| `TRIVYAL_HEARTBEAT_INTERVAL` | no | `30` | Seconds between heartbeat messages sent to the hub. |
| `TRIVYAL_RECONNECT_DELAY` | no | `10` | Seconds to wait before reconnecting after a dropped connection. |

### Docker Compose

| Variable | Default | Description |
|---|---|---|
| `AGENT_TOKEN` | — | Passed as `TRIVYAL_TOKEN` to the co-located agent in `docker-compose.hub.yml`. |
| `AGENT_HUB_KEY` | — | Passed as `TRIVYAL_KEY` to the co-located agent in `docker-compose.hub.yml`. |
| `DOCKER_GID` | `999` | GID of `/var/run/docker.sock` on the agent host. Get it with `stat -c '%g' /var/run/docker.sock`. |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for setup instructions and guidelines. Please open an issue before submitting a pull request for non-trivial changes so we can discuss the approach first.

### Development Setup

This repository uses [uv](https://docs.astral.sh/uv/) for Python dependency management.

```
trivyal/
├── hub/      # Hub service (FastAPI) — uv project
├── agent/    # Agent service (Python) — uv project
├── ui/       # React frontend (Vite + TypeScript)
└── docs/     # Architecture and guides
```

**Install all dependencies (including pre-commit hooks):**
```bash
make init
```

This installs [pre-commit](https://pre-commit.com/) as a uv tool and sets up git hooks for linting (ruff), formatting, security scanning (bandit, pip-audit, npm audit), and lockfile validation. To run all hooks manually:

```bash
make lint
```

**Run a service in dev mode:**
```bash
make dev-hub
make dev-agent
make dev-ui
```

**Run tests:**
```bash
make test              # all unit tests (hub + agent + ui)
make test-hub
make test-agent
make test-ui
make test-integration  # requires Docker
make test-e2e          # E2E browser tests (requires Docker + Playwright)
make test-load         # load tests (requires Docker, slow)
```

---

## Inspiration

The hub-agent model and overall UX philosophy were inspired by [Beszel](https://github.com/henrygd/beszel), a lightweight server monitoring tool. Use it!

---

## License

MIT
