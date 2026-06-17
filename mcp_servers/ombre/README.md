# Ombre MCP Service

External long-term AI memory service — integrated through MCP Hub adapter.

## Status

Deployed at `http://45.76.169.98:8000`. Independently operated.

This directory contains the Hub-facing adapter only. Ombre source code is **not** in this repository.

## Files

| File | Purpose |
|---|---|
| `manifest.yaml` | Service declaration for Hub auto-discovery |
| `adapter.py` | HTTP bridge — connection, health check, endpoint management |
| `server.py` | BaseMCPServer subclass — lifecycle + tool dispatch |
| `Dockerfile` | Docker build context for containerized deployment |

## Health Check

```
GET http://45.76.169.98:8000/health
→ {"status": "ok", "buckets": 0, "decay_engine": "stopped"}
```

States: `CONNECTED` | `UNHEALTHY` | `DISCONNECTED`

## Tools

| Tool | Description |
|---|---|
| `ombre_health` | Connectivity check to external Ombre |
| `ombre_status` | Endpoint, connection state, adapter info |
