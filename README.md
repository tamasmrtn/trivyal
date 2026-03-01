# Trivyal

A lightweight, self-hosted container vulnerability scanner with a hub-agent model, powered by [Trivy](https://github.com/aquasecurity/trivy).

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

### Deploy the Hub

Create a `docker-compose.hub.yml` on your hub server:

```yaml
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

  trivyal-agent:                    # optional: monitor the hub server itself
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

```bash
docker compose -f docker-compose.hub.yml up -d
```

Open `http://<hub-host>:8099` in your browser and log in with the admin credentials.

### Add an Agent

1. Go to **Agents** in the UI and click **Add Agent**.
2. Copy the generated `TOKEN` and `KEY` values shown.
3. On each agent host, create a `docker-compose.agent.yml`:

```yaml
services:
  trivyal-agent:
    image: trivyal/agent:latest
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./agent_data:/app/data
    environment:
      HUB_URL: "ws://<hub-host>:8099"
      TOKEN: "<generated in UI>"
      KEY: "<hub public key from UI>"
      SCAN_SCHEDULE: "0 2 * * *"   # cron, default nightly at 2am
```

```bash
docker compose -f docker-compose.agent.yml up -d
```

The agent will appear online in the hub UI within a few seconds. Scans run on the configured schedule, or you can trigger one immediately from the hub.

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

**Install all dependencies:**
```bash
make init
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
