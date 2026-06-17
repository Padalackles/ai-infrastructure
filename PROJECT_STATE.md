# Project State

**Status:** 🟡 In Progress  
**Version:** v0.1.0  
**Last Updated:** 2026-06-17

---

## Project Goal

Build a personal AI infrastructure centered on **Claude Desktop + MCP Hub**.

**Design Principles:**

- **MCP First** — every new capability should preferably be added through MCP.
- **Docker Compose** for deployment.
- **Caddy** as reverse proxy.
- **Cloudflare** for external access.
- **Modular architecture** — swap or extend components without rewiring the whole system.

---

## Current Phase

**Phase 0 — Project Bootstrap**

---

## Current Task

Create the project structure and core documentation.

**Current priorities:**

- [x] README.md
- [x] PROJECT_STATE.md
- [ ] ARCHITECTURE.md
- [ ] ROADMAP.md
- [ ] docs/MCP.md

---

## Completed

- Defined overall project vision.
- Switched architecture from "Docker-centric" to "MCP-first".
- Decided Claude Desktop will be the unified AI entry point.
- Decided MCP Hub will be the system core.

---

## Next Tasks

1. Build repository structure.
2. Write README.
3. Complete architecture document.
4. Design MCP communication flow.
5. Deploy Docker Compose.

---

## Architecture Summary

```
Internet
   ↓
Cloudflare
   ↓
Caddy
   ↓
Docker Compose
   ↓
MCP Hub
   ├── GitHub MCP
   ├── Filesystem MCP
   ├── Ombre MCP
   ├── ntfy MCP
   └── Future MCP Services
```

---

## Installed Components

| Component          | Status   |
|--------------------|----------|
| Docker Compose     | Planned  |
| Caddy              | Planned  |
| Cloudflare         | Planned  |
| MCP Hub            | Planned  |
| GitHub MCP         | Planned  |
| Filesystem MCP     | Planned  |
| Ombre              | Planned  |
| ntfy               | Planned  |

---

## Design Decisions

- Claude Desktop is the unified entry point.
- MCP Hub is the system core.
- Every new capability should preferably be added through MCP.
- Docker is only a deployment layer, not the architecture core.

---

## Notes

When resuming this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Read ARCHITECTURE.md
4. Continue the **Current Task**
