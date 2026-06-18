# Ombre Adapter

## Architecture

```
Claude Desktop
        │
        ▼
     MCP Hub  (this repository)
        │
        ▼
  Ombre Adapter  (mcp_servers/ombre/)
        │  HTTP
        ▼
  Ombre Service  (external, 45.76.169.98:8000/mcp)
```

Ombre source code is **not** in this repository. The adapter is a pure HTTP bridge.

## Endpoint

```
http://45.76.169.98:8000/mcp
```

Override: `export OMBRE_URL=http://<host>:<port>/mcp`

## Configuration

```yaml
# mcp-hub/config.yaml
services:
  ombre:
    enabled: true
    endpoint: "${OMBRE_URL:-http://45.76.169.98:8000/mcp}"
```

## Health Check Flow

```
Hub Startup
    │
    ▼
Discovery scans mcp_servers/ombre/manifest.yaml
    │
    ▼
OmbreServer.initialize()
    │
    ▼
OmbreAdapter.connect()
    │
    ▼
Connect to MCP endpoint
http://45.76.169.98:8000/mcp
    │
    ▼
Initialize MCP session
    │
    ├── MCP session established + tools discovered → CONNECTED  ✓
    ├── Connection failed                          → UNHEALTHY
    └── Network error                              → DISCONNECTED
```

## Startup Log

```
Loading Services...
✓ Ombre (CONNECTED) — http://45.76.169.98:8000/mcp
Hub Ready
```

## Files

| File | Purpose |
|---|---|
| `mcp_servers/ombre/manifest.yaml` | Service declaration |
| `mcp_servers/ombre/adapter.py` | HTTP bridge (connection, health) |
| `mcp_servers/ombre/server.py` | BaseMCPServer subclass |
| `mcp_servers/ombre/README.md` | Service documentation |
| `mcp_servers/ombre/Dockerfile` | Container build context |
