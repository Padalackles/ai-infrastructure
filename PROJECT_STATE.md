# Project State

**Status:** 🟡 In Progress
**Version:** v0.1.0
**Last Updated:** 2026-06-17

---

## Project Goal

Build an **MCP Gateway (Hub)** deployed on a VPS that connects Claude Desktop to multiple MCP services.

**Design Principles:**

- **MCP First** — every capability is an MCP service. Core never grows business logic.
- **Gateway, not Application** — the Hub routes; servers implement.
- **Plugin Architecture** — new MCP = new directory, zero Core changes.
- **Docker is Deployment Only** — architecture lives in code, not containers.

---

## Current Phase

**Phase 2 — MCP Hub Gateway** (see ROADMAP.md)

---

## Task Status

| Task | Status | Description |
|---|---|---|
| Task-001 | ✅ | Migrate Ombre MCP Server to Docker Compose |
| Task-002 | ✅ | Establish Ombre MCP Server foundation (FastAPI + stubs) |
| Task-003 | ✅ | MCP Hub Core Runtime (ServerManager, Discovery, lifecycle) |
| Task-004 | ✅ | JSON-RPC 2.0 Transport Layer |
| Task-004.1 | ✅ | Lifecycle fixes, Discovery isolation, API stats |
| Task-004 Review | ✅ | Router→handlers, Runtime layer, Loader, unified `mcp_servers/` |
| Task-Doc-Refine | ✅ | Documentation refinement (completed) |
| Task-005 | ⬜ | Claude Desktop ↔ MCP Hub wiring |

---

## Current Task

| Field | Value |
|---|---|
| **Task ID** | Task-Documentation-Refinement |
| **Status** | ✅ Completed |
| **Description** | Refine documentation: PROJECT_STATE, CLAUDE, DECISIONS |

---

## Completed Tasks

1. Task-001 — Migrate Ombre MCP Server to Docker Compose
2. Task-002 — Establish Ombre MCP Server foundation
3. Task-003 — MCP Hub Core Runtime
4. Task-004 — JSON-RPC 2.0 Transport Layer
5. Task-004.1 — Lifecycle fixes, Discovery isolation, API stats
6. Task-004 Review — Router→handlers, Runtime, Loader, unified dirs
7. Task-002 Refactor — Repository architecture alignment
8. Task-Documentation-Refinement — PROJECT_STATE, CLAUDE, DECISIONS

---

## Current Focus

**Task-005** — Claude Desktop ↔ MCP Hub communication wiring.

---

## Next Task

**Task-005** — Implement Claude Desktop to MCP Hub JSON-RPC wiring. Enable end-to-end tool invocation from Claude Desktop through the Hub to a registered MCP server.

---

## Architecture

```
                    Claude Desktop  (local)
                         │  JSON-RPC / MCP
          ╔══════════════╪══════════════╗
          ║         STABLE CORE         ║
          ║                             ║
          ║   Gateway → Registry       ║
          ║   Router  → Handlers       ║
          ║   Runtime → Lifecycle      ║
          ║   Transport (JSON-RPC)     ║
          ║   Config                   ║
          ╚══════════════╪══════════════╝
                         │
          ╔══════════════╪══════════════╗
          ║   EXTENSIBLE MCP SERVICES   ║
          ║                             ║
          ║  Ombre │ ntfy │ Filesystem ║
          ║  GitHub │ Browser │ ...    ║
          ╚═════════════════════════════╝
```

---

## Implemented

| Capability | Location |
|---|---|
| MCP Hub Gateway (FastAPI) | `mcp-hub/src/main.py` |
| Server lifecycle (init → lifecycle_start → lifecycle_stop) | `mcp-hub/src/core/base_server.py` |
| ServerManager (register, start_all, stop_all, stats, tools, health) | `mcp-hub/src/core/server_manager.py` |
| Auto-discovery (manifest.yaml + server.py, error isolation) | `mcp-hub/src/core/discovery.py` |
| Loader abstraction (PythonLoader, extensible) | `mcp-hub/src/core/loader.py` |
| Event bus (in-memory pub/sub) | `mcp-hub/src/core/events.py` |
| JSON-RPC 2.0 transport | `mcp-hub/src/transport/` |
| Handler modules (initialize, tools, health) | `mcp-hub/src/transport/handlers/` |
| Runtime middleware layer | `mcp-hub/src/runtime/` |
| REST endpoints (/health, /status, /tools) | `mcp-hub/src/api/routes.py` |
| Structured logging | All modules |
| Ombre MCP Server foundation | `services/ombre/` |
| Docker Compose (Core + MCP services) | `docker-compose.yml` |
| Unit tests (lifecycle, discovery, transport, tools) | `mcp-hub/tests/` |

## Not Yet Implemented

| Capability | Target |
|---|---|
| Claude Desktop ↔ Hub MCP wiring | Task-005 |
| Concrete MCP Servers (ntfy, GitHub, Filesystem) | Task-005+ |
| Formal MCP Registry (manifests, enable/disable) | Task-005+ |
| Authentication / token validation | Phase 6 |
| Health-check loop | Task-005 |
| Remote server adapters (HTTP/SSE/WebSocket) | Phase 7 |

---

## Installed Components

| Component | Status |
|---|---|
| MCP Hub (Gateway) | ✅ Runtime |
| Caddy | Planned |
| Cloudflare | Planned |
| Ombre MCP | ✅ Foundation |
| ntfy MCP | Planned |
| Filesystem MCP | Planned |
| GitHub MCP | Planned |

---

## Repository Health

| Check | Status |
|---|---|
| Documentation | ✅ Consistent |
| Architecture | ✅ Stable Core / Extensible Service Layer |
| Tests | ✅ 6 test files (lifecycle, discovery, transport, tools) |
| GitHub Sync | ✅ Up to date |
| No duplicate docs | ✅ Single source of truth per concern |

## Last Commit

| Field | Value |
|---|---|
| **Hash** | `a9e8f44` |
| **Summary** | docs: refine documentation — PROJECT_STATE, CLAUDE, DECISIONS |

---

## Notes

When resuming this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Read ARCHITECTURE.md
4. Continue from **Task-005**
