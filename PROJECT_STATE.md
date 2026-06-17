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

## Task Status

| Task | Status | Description |
|---|---|---|
| **Task-001** | ✅ Completed | Migrate Ombre Brain to Docker Compose (defined) |
| **Task-002** | ✅ Completed | Establish Ombre Brain Project Foundation (fully implemented) |
| **Task-003** | ✅ Completed | Implement MCP Hub Core Runtime (fully implemented) |
| **Task-004** | ✅ Completed | MCP Transport Layer — JSON-RPC 2.0 (fully implemented) |
| **Task-004.1** | ✅ Completed | Lifecycle fix, Discovery isolation, API stats, tests |

---

## Current Focus

**Task-005 — TBD**

Claude Desktop ↔ MCP Hub communication wiring.

---

## Currently Implemented (as of Task-004.1)

| Capability | Where |
|---|---|
| MCP Hub Gateway (FastAPI) | `mcp-hub/src/main.py` |
| Server lifecycle (init → lifecycle_start → lifecycle_stop) | `mcp-hub/src/core/base_server.py` |
| ServerManager (register, start_all, stop_all, stats) | `mcp-hub/src/core/server_manager.py` |
| Auto-discovery (manifest.yaml + server.py fallback) | `mcp-hub/src/core/discovery.py` |
| Error isolation (one failure never blocks others) | `mcp-hub/src/core/discovery.py` |
| Event bus (in-memory pub/sub) | `mcp-hub/src/core/events.py` |
| JSON-RPC 2.0 transport (initialize, tools/list, tools/call) | `mcp-hub/src/transport/` |
| REST endpoints (/health, /status, /tools) | `mcp-hub/src/api/routes.py` |
| Health status (healthy/degraded/failed) | `mcp-hub/src/api/routes.py` |
| Server statistics (total/running/failed counts) | `mcp-hub/src/core/server_manager.py` |
| Structured logging (REQUEST → RESPONSE with timing) | `mcp-hub/src/transport/router.py` |
| Graceful startup/shutdown | `mcp-hub/src/main.py` (lifespan) |
| Docker Compose integration | `docker-compose.yml` + `mcp-hub/Dockerfile` |
| Plugin architecture | `mcp_servers/` + Discovery |
| Unit tests (JSON-RPC, router, transport, tools, lifecycle, discovery) | `mcp-hub/tests/` |
| Ombre Brain foundation | `project/` (Task-002) |

| Capability | Where |
|---|---|
| MCP Hub Gateway (FastAPI) | `mcp-hub/src/main.py` |
| Server lifecycle (start/stop/health) | `mcp-hub/src/core/server_manager.py` |
| Abstract server base class | `mcp-hub/src/core/base_server.py` |
| Auto-discovery framework | `mcp-hub/src/core/discovery.py` |
| Event bus (in-memory pub/sub) | `mcp-hub/src/core/events.py` |
| Health endpoint `GET /health` | `mcp-hub/src/api/routes.py` |
| Status endpoint `GET /status` | `mcp-hub/src/api/routes.py` |
| Graceful startup/shutdown | `mcp-hub/src/main.py` (lifespan) |
| Docker Compose integration | `docker-compose.yml` + `mcp-hub/Dockerfile` |
| Plugin architecture | `mcp_servers/` + Discovery |
| Ombre Brain foundation | `project/` (Task-002) |

## Not Yet Implemented (→ Task-004+)

| Capability | Planned In |
|---|---|
| Concrete MCP Servers (Ombre, ntfy, GitHub, …) | Task-005+ |
| Claude Desktop ↔ Hub MCP protocol wiring | Task-005 |
| Per-service configuration in config.yaml | Task-005+ |
| Hub authentication / token validation | Task-006+ |
| Inter-service communication via EventBus | Task-006+ |
| Health-check loop for registered servers | Task-005 |
| Remote MCP server adapters (HTTP/SSE/WebSocket) | Task-006+ |

---

## Task-003 Deliverables

- `src/core/base_server.py` — Abstract `BaseMCPServer` with `initialize()`, `start()`, `stop()`, `health()`, `info()`.
- `src/core/server_manager.py` — `ServerManager` with `register()`, `start_all()`, `stop_all()`, `get_server()`, `list_servers()`.
- `src/core/events.py` — `EventBus` in-memory pub/sub (`publish`, `subscribe`, `unsubscribe`).
- `src/core/discovery.py` — `Discovery` auto-scans `mcp_servers/` for server modules.
- `src/api/routes.py` — `GET /health` and `GET /status` endpoints.
- `src/main.py` — FastAPI application with full lifecycle (startup/shutdown logging).
- `mcp_servers/` — Auto-discovery namespace (empty — servers added in future tasks).
- `requirements.txt`, `Dockerfile`, `config.yaml` — Container-ready.
- `docker-compose.yml` — Updated to mount `mcp_servers/` for discovery.
- Plugin architecture — new MCP Server requires only a new directory, zero Hub Core changes.
- Zero business logic — pure orchestration only.
- Hub is **independent** of Ombre and any other MCP service.

---

## Task-002 Deliverables

- Complete `project/` directory structure with all module stubs.
- Runnable FastAPI application — `uvicorn app.main:app --reload`.
- `GET /health` returns `{"status": "ok"}`.
- MCP module: `client.py`, `server.py`, `registry.py` with method signatures.
- Service stubs: `ConversationService`, `MemoryService`, `TaskService`.
- Scheduler stub: `TaskScheduler` with `add_task()`, `cancel()`, `run_pending()`.
- Storage: `FileStorage` with `save_json()`, `load_json()`, `delete()`, `list()`.
- Pydantic models: `Conversation`, `Memory`, `Task`, `UserConfig`.
- `requirements.txt` with pinned dependencies.
- `README.md` for the Ombre Brain project.
- `ARCHITECTURE.md` updated — Claude Desktop as unified entry point, MCP Hub responsibilities expanded, Core Layer / MCP Service Layer separation.
- No business logic implemented — clean foundation for Task-003.

---

## Next Steps

1. Define Task-004 scope and acceptance criteria.
2. Implement the first concrete MCP Server (Ombre, ntfy, GitHub, etc.).
3. Wire Claude Desktop → MCP Hub communication.
4. Add tests for ServerManager and EventBus.

---

## Architecture Summary

```
                         User
                          │
                    Claude Desktop          ◄── Unified entry point
                          │
          ╔═══════════════╪═══════════════╗
          ║           CORE LAYER          ║
          ║                               ║
          ║          MCP Hub              ║
          ║   • Service registration      ║
          ║   • Routing                   ║
          ║   • Lifecycle management      ║
          ║   • Configuration             ║
          ╚═══════════════╪═══════════════╝
                          │
          ╔═══════════════╪═══════════════╗
          ║       MCP SERVICE LAYER       ║
          ║                               ║
          ║  GitHub │ Filesystem │ Ombre  ║
          ║  ntfy   │ Browser    │ SSH    ║
          ╚═══════════════════════════════╝
```

---

## Installed Components

| Component          | Status      |
|--------------------|-------------|
| Docker Compose     | Planned     |
| Caddy              | Planned     |
| Cloudflare         | Planned     |
| MCP Hub            | Runtime ✓   |
| GitHub MCP         | Planned     |
| Filesystem MCP     | Planned     |
| Ombre Brain        | Foundation ✓ |
| ntfy               | Planned     |

---

## Design Decisions

- Claude Desktop is the unified entry point — all user interaction flows through it.
- MCP Hub is the system core — registration, routing, lifecycle, configuration.
- Every new capability should preferably be added through MCP.
- Docker is only a deployment layer, not the architecture core.
- Architecture separated into Core Layer (stable) and MCP Service Layer (extensible).

---

## Notes

When resuming this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Read ARCHITECTURE.md
4. Continue from **Task-004**
