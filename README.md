<p align="center">
  <img src="docs/trivyal-logo-with-name.jpeg" alt="Trivyal" width="280" />
</p>

<p align="center">A lightweight, self-hosted container vulnerability scanner with a hub-agent model, powered by <a href="https://github.com/aquasecurity/trivy">Trivy</a>.</p>

Trivyal is designed for homelabs and small multi-server Docker environments. A lightweight agent runs on each host, scans local containers with Trivy, and ships results to a central hub that aggregates and displays everything in a single UI.

---

## Features

### Hub
- Dashboard showing all connected agents and their status (online / offline / scanning)
- Aggregated vulnerability view across all hosts — filterable by severity (Critical, High, Medium, Low, Unknown)
- Per-host and per-container drill-down
- Finding timeline — tracks when CVEs appeared and when they were resolved
- Diff view between scans — highlights new and fixed findings
- Risk acceptance — mark a finding as accepted with a reason and expiry date
- False positive flagging per finding
- Full scan history log per host
- Webhook notifications (Slack, Discord, Ntfy) on new Critical/High findings
- Agent management UI — add, remove, and view agents; copy-paste Docker Compose snippet for quick deploy
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
│  │  - Notification sender  │    │
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
| Hub database | SQLite via SQLModel |
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
3. On the agent host, clone the repository and create a `.env`:

```env
TRIVYAL_HUB_URL=ws://<hub-host>:8099
AGENT_TOKEN=<token from UI>
AGENT_HUB_KEY=<hub public key from UI>
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
| `TRIVYAL_HOST` | no | `0.0.0.0` | Interface to bind. |
| `TRIVYAL_PORT` | no | `8099` | Port to listen on. |
| `TRIVYAL_STATIC_DIR` | no | `/app/static` | Directory containing the built React UI. Present automatically in Docker; not used in dev. |

### Agent

| Variable | Required | Default | Description |
|---|---|---|---|
| `TRIVYAL_HUB_URL` | **yes** | `ws://localhost:8099` | WebSocket URL of the hub. Use `wss://` in production. |
| `TRIVYAL_TOKEN` | **yes** | — | Registration token generated in the hub UI (Agents → Add Agent). |
| `TRIVYAL_KEY` | **yes** | — | Hub Ed25519 public key shown alongside the token in the hub UI. |
| `TRIVYAL_SCAN_SCHEDULE` | no | `0 2 * * *` | Cron expression for scheduled scans (default: nightly at 02:00). |
| `TRIVYAL_DATA_DIR` | no | `/app/data` | Directory for the local scan result cache. |
| `TRIVYAL_HEARTBEAT_INTERVAL` | no | `30` | Seconds between heartbeat messages sent to the hub. |
| `TRIVYAL_RECONNECT_DELAY` | no | `10` | Seconds to wait before reconnecting after a dropped connection. |

### Docker Compose

| Variable | Default | Description |
|---|---|---|
| `AGENT_TOKEN` | — | Passed as `TRIVYAL_TOKEN` to the co-located agent in `docker-compose.hub.yml`. |
| `AGENT_HUB_KEY` | — | Passed as `TRIVYAL_KEY` to the co-located agent in `docker-compose.hub.yml`. |

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for non-trivial changes so we can discuss the approach first.

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

This installs [pre-commit](https://pre-commit.com/) as a uv tool and sets up git hooks for linting (ruff), formatting, security scanning (bandit), and lockfile validation. To run all hooks manually:

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
make test          # all services
make test-hub
make test-agent
make test-ui
```

---

## License

MIT
