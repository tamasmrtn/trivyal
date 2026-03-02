# Changelog

## [0.1.0] - 2026-03-02

Initial release.

- Hub service: FastAPI + SQLite, agent management, vulnerability aggregation, webhook notifications
- Agent service: Docker container discovery, Trivy scanning, scheduled and on-demand scans
- UI: React dashboard with findings, agents, and scan history
- Ed25519 challenge-response authentication between hub and agents
- Docker Compose deployment for hub and agent
