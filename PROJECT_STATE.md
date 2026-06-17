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
| Task-001 | ✅ | Project Specification — MCP Gateway architecture |
| Task-002 | ✅ | Foundation — repository structure, FastAPI stubs |
| Task-003 | ✅ | MCP Hub Skeleton — modules, models, interfaces |
| Task-004 | ✅ | Registry — ServerManager, Discovery |
| Task-005 | ✅ | Router — JSON-RPC dispatch, handlers |
| Task-006 | ✅ | Lifecycle Manager — BaseMCPServer, lifecycle_start/stop |
| Task-007 | ✅ | Configuration — config.yaml, load_config() |
| Task-008 | ✅ | Plugin Loader — Loader ABC, PythonLoader |
| Task-009 | ✅ | Ombre Adapter — HTTP bridge to external Ombre |
| Task-010 | ⬜ | ntfy MCP Integration |
| Task-011 | ⬜ | Claude Desktop Integration |
| Task-012 | ⬜ | Docker Production |
| Task-013 | ⬜ | Cloudflare + Caddy |
| Task-014 | ⬜ | Production Hardening |

---

## Current Task

| Field | Value |
|---|---|
| **Task ID** | Task-010 |
| **Status** | ⬜ Pending |
| **Description** | ntfy MCP Integration — push notifications |

---

## Next Task

| Field | Value |
|---|---|
| **Task ID** | Task-011 |
| **Description** | Claude Desktop Integration — end-to-end MCP wiring |

---

## Hub Module Structure

```
mcp-hub/src/
├── main.py              Entry point — 7-step startup pipeline
├── config/              load_config() — unified YAML config
├── lifecycle/           BaseMCPServer, ToolNotFoundError
├── registry/            ServerManager — service registry
├── loader/              Discovery, Loader, PythonLoader
├── router/              Router + RouterInterface + RouteRegistry
├── runtime/             Runtime — middleware pass-through
├── transport/           JSON-RPC 2.0 stack (server, handlers)
├── models/              ServiceInfo, PluginManifest, HubState, RuntimeContext
├── api/                 REST endpoints (/health, /status, /tools)
├── core/                EventBus
└── utils/               generate_id() helpers
```

---

## Completed Tasks

1. Task-001 — Project Specification (MCP Gateway architecture)
2. Task-002 — Foundation (repository structure, stubs)
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
| Server lifecycle | `mcp-hub/src/lifecycle/` |
| ServerManager (registry) | `mcp-hub/src/registry/` |
| Auto-discovery + Loader | `mcp-hub/src/loader/` |
| Event bus | `mcp-hub/src/core/events.py` |
| JSON-RPC 2.0 transport | `mcp-hub/src/transport/` |
| Router + handlers | `mcp-hub/src/router/` + `transport/handlers/` |
| Runtime middleware | `mcp-hub/src/runtime/` |
| REST endpoints | `mcp-hub/src/api/routes.py` |
| Configuration | `mcp-hub/src/config/` |
| Shared models | `mcp-hub/src/models/` |
| Ombre MCP Docker build context | `mcp_servers/ombre/Dockerfile` |
| Docker Compose | `docker-compose.yml` |
| Unit tests | `mcp-hub/tests/` |

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
| Ombre MCP | External (Docker only) |
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
