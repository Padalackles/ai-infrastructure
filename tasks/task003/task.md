# Task-003 — Implement MCP Hub Core Runtime

## Objective

Implement the **MCP Hub runtime** — the central orchestration gateway that sits between Claude Desktop and all MCP servers.

The MCP Hub contains **zero business logic**. It is a pure orchestration layer: registration, routing, lifecycle management, and auto-discovery.

---

## Background

- **Task-001** — Requirements, architecture, roadmap defined.
- **Task-002** — Ombre Brain project foundation established.

The MCP Hub is the system's **gateway**. Claude Desktop connects to it; all MCP services register with it.

---

## Scope

### 1. Base MCP Server (`src/core/base_server.py`)

Abstract base class with:
- `initialize()` — load config, warm up connections
- `start()` — begin accepting requests
- `stop()` — drain and release resources
- `health()` — return health status dict
- `info()` — return metadata dict

All future servers (OmbreServer, NtfyServer, GithubServer) inherit from this.

### 2. Server Manager (`src/core/server_manager.py`)

Lifecycle manager:
- `register(server)` — register a server instance
- `unregister(name)` — remove a server
- `start_all()` — initialize and start all servers
- `stop_all()` — stop all servers gracefully
- `get_server(name)` — resolve by name
- `list_servers()` — metadata for /health and /status
- `count` — number of registered servers

### 3. Event Bus (`src/core/events.py`)

In-memory pub/sub:
- `publish(event, data)`
- `subscribe(event, handler)`
- `unsubscribe(event, handler)`

Future: Ombre → EventBus → ntfy (memory stored → notification pushed).

### 4. Auto-Discovery (`src/core/discovery.py`)

Scans `mcp_servers/` subdirectories for `server.py` modules. Each subdirectory is a self-contained MCP server. Adding a new server requires zero Hub Core changes.

### 5. API Endpoints

- `GET /health` → `{"status":"ok","servers":[...]}`
- `GET /status` → `{"version":"0.1.0","runtime":"MCP Hub","servers":[...]}`

### 6. Application Lifecycle

```
Starting MCP Hub...
Config Loaded
Logger Ready
Server Manager Ready
0 Servers Loaded
HTTP API Ready
MCP Hub Ready
```

Graceful shutdown: stop all servers → exit.

---

## Deliverables

| File | Purpose |
|---|---|
| `mcp-hub/src/main.py` | FastAPI app + lifecycle |
| `mcp-hub/src/core/base_server.py` | Abstract BaseMCPServer |
| `mcp-hub/src/core/server_manager.py` | ServerManager |
| `mcp-hub/src/core/events.py` | EventBus |
| `mcp-hub/src/core/discovery.py` | Auto-discovery |
| `mcp-hub/src/api/routes.py` | /health, /status |
| `mcp-hub/mcp_servers/__init__.py` | Discovery namespace |
| `mcp-hub/requirements.txt` | Dependencies |
| `mcp-hub/Dockerfile` | Container build |
| `mcp-hub/config.yaml` | Hub configuration |
| `tasks/task003/task.md` | This document |

---

## What Was NOT Implemented

- No Ombre API
- No ntfy integration
- No Claude Desktop integration (future task)
- No prompt handling
- No memory system
- No agent logic
- No business logic of any kind

---

## Success Criteria

- ✅ `docker compose up mcp-hub` starts successfully
- ✅ Lifecycle logs print in order
- ✅ `GET /health` returns `{"status":"ok","servers":[]}`
- ✅ `GET /status` returns `{"version":"0.1.0","runtime":"MCP Hub","servers":[]}`
- ✅ All imports resolve correctly
- ✅ Zero business logic
- ✅ Plugin architecture — new servers require only a new directory

---

## Next Task

Task-004 — TBD
