# MCP Registry

## Purpose

The MCP Registry is the Hub's source of truth for what MCP services exist, which are enabled, and how they are configured.

The Registry is implemented in `mcp-hub/src/registry/server_manager.py` and `mcp-hub/src/loader/discovery.py`. This document describes its design and current behavior.

---

## Design

### Where Manifests Live

Manifests live alongside their MCP server code — one per service:

```
mcp_servers/
├── ombre/
│   ├── manifest.yaml      ← Service declaration
│   ├── server.py          ← BaseMCPServer subclass
│   └── adapter.py         ← HTTP bridge
├── ntfy/
│   ├── manifest.yaml
│   ├── server.py
│   └── adapter.py
├── filesystem/            ← Reserved
│   └── manifest.yaml
└── github/                ← Reserved
    └── manifest.yaml
```

The Discovery scan at `mcp_servers/*/manifest.yaml` finds them — no separate `registry/` directory needed.

### Manifest Format (`mcp_servers/<name>/manifest.yaml`)

```yaml
# ombre/manifest.yaml
name: ombre
version: "0.1.0"
class: OmbreServer
description: Long-term AI memory — external MCP-compatible service
endpoint: "${OMBRE_URL:-http://45.76.169.98:8000/mcp}"
```

The `enabled` flag lives in `mcp-hub/config.yaml`, not in the manifest.

### In-Memory Registry (ServerManager)

The ServerManager (`mcp-hub/src/registry/server_manager.py`) keeps an in-memory `_servers` dict. At startup, the Discovery + Loader pipeline registers each discovered server:

```
Discovery scans mcp_servers/*/manifest.yaml
    → PythonLoader imports server.py
    → ServerManager.register(server_instance)
    → _servers[name] = server
```

No `installed.yaml` file is generated — the registry is purely in-memory. Server running state lives in `BaseMCPServer._running`.

### Enable/Disable (`mcp-hub/config.yaml`)

Controlled per-service in the Hub config, not via a separate `enabled.yaml`:

```yaml
# mcp-hub/config.yaml
services:
  ombre:
    enabled: true
    endpoint: "${OMBRE_URL:-http://45.76.169.98:8000/mcp}"
```

---

## Lifecycle

```
Discover   scan mcp_servers/*/manifest.yaml   (Discovery)
    ↓
Validate   parse manifest, check fields       (Discovery)
    ↓
Load       import server.py module            (PythonLoader)
    ↓
Register   ServerManager.register(instance)   (in-memory dict)
    ↓
Initialize server.initialize()                (BaseMCPServer)
    ↓
Start      server.lifecycle_start()            (BaseMCPServer)
    ↓
Running    (_running = True)
    ↓
Stop       server.lifecycle_stop()             (BaseMCPServer)
    ↓
Unregister ServerManager.unregister(name)
```

Each MCP server follows this lifecycle. The ServerManager tracks state transitions in `_servers` (dict) and `_failed` (set).

---

## Hub Responsibilities

- **Discover** MCPs at startup
- **Register** validated servers
- **Enable/Disable** per configuration
- **Manage Lifecycle** (init → start → stop)
- **Report Status** via /health and /status

The Registry does NOT:
- Implement business logic
- Store user data
- Make routing decisions

---

## Future: Remote Registry

Later phases may support remote MCP registries:

```
Local Services (mcp_servers/*/)
    │
    ├── ombre/manifest.yaml   (local adapter)
    ├── ntfy/manifest.yaml    (local adapter)
    │
    ▼
Remote Registry (HTTP)
    │
    ├── community-weather.yaml
    └── org-internal-search.yaml
```
