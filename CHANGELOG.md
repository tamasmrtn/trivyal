# Changelog

## [0.2.0] - 2026-03-03

### Breaking changes

- **Hub database schema**: `Agent` table no longer stores `public_key` / `private_key`; these have moved to a new singleton `HubSettings` table. Fresh deployment or manual migration required when upgrading from v0.1.0.

### Features

- Insights analytics page at `/insights` — summary cards, vulnerability trend, new-vs-resolved, per-agent trend, top CVEs table, severity donut; time window selector (7d / 30d / 90d); powered by four new hub endpoints under `/api/v1/insights/`
- Container names are now captured by the agent, stored on the `Container` model, surfaced in scan and finding API responses, and displayed in the Scan History table
- New `GET /api/v1/hub/public-key` endpoint exposing the hub's Ed25519 public key
- Severity, finding status, and agent status badges redesigned to a ghost/tinted style

### Bug fixes

- Hub now uses a single Ed25519 keypair (stored in `HubSettings`) for all agent challenge-response handshakes; previously a new keypair was generated per agent registration, causing authentication failures on hub restart

### Dependencies

- Bumped Node.js (CI) 22 → 24, Vite 6 → 7, `@vitejs/plugin-react` 4 → 5, `jsdom` 26 → 28, `globals` 15 → 17, `tailwind-merge` 2 → 3

---

## [0.1.0] - 2026-03-02

Initial release.

- Hub service: FastAPI + SQLite, agent management, vulnerability aggregation, webhook notifications
- Agent service: Docker container discovery, Trivy scanning, scheduled and on-demand scans
- UI: React dashboard with findings, agents, and scan history
- Ed25519 challenge-response authentication between hub and agents
- Docker Compose deployment for hub and agent
