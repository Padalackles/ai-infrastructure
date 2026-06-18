# Project State

**Status:** 🟡 In Progress
**Version:** v0.1.0
**Last Updated:** 2026-06-18 (deployed to production)

---

## Project Goal

Build an **MCP Hub** deployed on a VPS that connects Claude Desktop to multiple MCP services.

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
| Task-001 | ✅ | Project Specification — MCP Hub architecture |
| Task-002 | ✅ | Foundation — repository structure, FastAPI stubs |
| Task-003 | ✅ | MCP Hub Skeleton — modules, models, interfaces |
| Task-004 | ✅ | Registry — ServerManager, Discovery |
| Task-005 | ✅ | Router — JSON-RPC dispatch, handlers |
| Task-006 | ✅ | Lifecycle Manager — BaseMCPServer, lifecycle_start/stop |
| Task-007 | ✅ | Configuration — config.yaml, load_config() |
| Task-008 | ✅ | Plugin Loader — Loader ABC, PythonLoader |
| Task-009 | ✅ | Ombre Adapter — HTTP bridge to external Ombre |
| Task-010 | ✅ | ntfy External Service Integration — via ntfy.sh API |
| Task-011 | ✅ | Remote MCP Transport — protocol validated, Claude Desktop Ready |
| Task-012 | ✅ | Domain + HTTPS + Cloudflare — deployed at raven-victor.click |
| Task-013 | ⬜ | Claude Desktop Remote Connection |
| Task-014 | ⬜ | Real ntfy Notification Test |
| Task-015 | ⬜ | Docker Production |
| Task-016 | 🟡 | Production Hardening (MCP Auth ✅, remaining items in progress) |

---

## Current Task

| Field | Value |
|---|---|
| **Task ID** | Task-013 |
| **Status** | ⬜ Planned |
| **Description** | Claude Desktop Remote Connection |

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

1. Task-001 — Project Specification (MCP Hub architecture)
2. Task-002 — Foundation (repository structure, stubs)
3. Task-003 — MCP Hub Core Runtime
4. Task-004 — JSON-RPC 2.0 Transport Layer
5. Task-004.1 — Lifecycle fixes, Discovery isolation, API stats
6. Task-004 Review — Router→handlers, Runtime, Loader, unified dirs
7. Task-002 Refactor — Repository architecture alignment
8. Task-Documentation-Refinement — PROJECT_STATE, CLAUDE, DECISIONS

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
| MCP Auth (Bearer Token) | `mcp-hub/src/core/auth.py` |
| Unit tests | `mcp-hub/tests/` (166 tests) |

## Not Yet Implemented

| Capability | Target |
|---|---|
| Claude Desktop ↔ Hub MCP wiring | Task-013 |
| Concrete MCP Servers (ntfy, GitHub, Filesystem) | Task-014+ |
| Formal MCP Registry (manifests, enable/disable) | Future |
| Authentication / token validation | ✅ Implemented (Bearer Token, Task-016) |
| Health-check loop | Future |
| Remote server adapters (HTTP/SSE/WebSocket) | Future |

---

## Installed Components

| Component | Status |
|---|---|
| MCP Hub (Gateway) | ✅ Runtime |
| Caddy | ✅ Running (Let's Encrypt TLS) |
| Cloudflare | ✅ DNS + Proxy |
| Ombre MCP | ✅ External (45.76.169.98:8000) |
| ntfy MCP | ✅ External (ntfy.sh) |
| Filesystem MCP | Reserved |
| GitHub MCP | Reserved |

---

## Repository Health

| Check | Status |
|---|---|
| Documentation | ✅ Consistent |
| Architecture | ✅ Stable Core / Extensible Service Layer |
| Architecture Audit | ✅ Pre-deployment check passed (2026-06-18) |
| Tests | ✅ 6 test files (lifecycle, discovery, transport, tools) |
| GitHub Sync | ✅ Up to date |
| No duplicate docs | ✅ Single source of truth per concern |
| CHANGELOG | ✅ Created |

## Last Commit

| Field | Value |
|---|---|
| **Hash** | `01c9e55` |
| **Summary** | feat: add Bearer Token authentication to POST /mcp endpoint |

---

## Notes

When resuming this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Read ARCHITECTURE.md
4. Continue from **Task-012**
