# AI Infrastructure

*A personal AI infrastructure built around Claude Desktop and the Model Context Protocol (MCP).*

---

## Vision

This project aims to build a modular, extensible personal AI infrastructure.

Instead of integrating every service directly, the system follows an **MCP First** architecture, where new capabilities are added through standardized MCP services.

Claude Desktop acts as the unified AI entry point, while MCP Hub serves as the central integration layer.

---

## Design Principles

- **MCP First** – Prefer adding new capabilities through MCP.
- **Modular** – Every service should be independently replaceable.
- **Documentation First** – Keep documentation synchronized with implementation.
- **Infrastructure as Code** – Deploy everything with Docker Compose.
- **Extensible** – New services should integrate without changing the overall architecture.

---

## Architecture

```
Internet
    │
Cloudflare
    │
Caddy
    │
Docker Compose
    │
MCP Hub
 ├── Filesystem MCP
 ├── GitHub MCP
 ├── Ombre MCP
 ├── ntfy MCP
 ├── Browser MCP
 └── Future MCP Services
```

---

## Repository Structure

| File | Purpose |
|---|---|
| README.md | Project overview |
| PROJECT_STATE.md | Current project status |
| ARCHITECTURE.md | System architecture |
| ROADMAP.md | Development roadmap |

| Directory | Purpose |
|---|---|
| `docs/` | MCP documentation, development conventions |
| `tasks/` | Development tasks |
| `docker/` | Docker configurations |
| `scripts/` | Utility scripts |

---

## Development Workflow

1. Read `PROJECT_STATE.md`
2. Check the current task.
3. Implement the required changes.
4. Update documentation.
5. Commit changes.

---

## Current Status

See [`PROJECT_STATE.md`](PROJECT_STATE.md) for the latest project progress.

---

## Roadmap

- **Phase 0** – Project Bootstrap
- **Phase 1** – Infrastructure
- **Phase 2** – MCP Platform
- **Phase 3** – Core MCP Services
- **Phase 4** – Operations
- **Phase 5** – Automation
- **Phase 6** – Production

---

## License

MIT License
