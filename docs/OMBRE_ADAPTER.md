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
  Ombre Service  (external, 45.76.169.98:8000)
```

Ombre source code is **not** in this repository. The adapter is a pure HTTP bridge.

## Endpoint

```
http://45.76.169.98:8000
```

Override: `export OMBRE_ENDPOINT=http://<host>:<port>`

## Configuration

```yaml
# mcp-hub/config.yaml
services:
  ombre:
    enabled: true
    endpoint: "${OMBRE_ENDPOINT:-http://45.76.169.98:8000}"
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
GET http://45.76.169.98:8000/health
    │
    ├── 200 + status=="ok"  → CONNECTED  ✓
    ├── non-200             → UNHEALTHY
    └── network error       → DISCONNECTED
```

## Startup Log

```
Loading Services...
✓ Ombre (CONNECTED) — http://45.76.169.98:8000
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
