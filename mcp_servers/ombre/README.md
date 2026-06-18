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
OmbreAdapter.connect()
    │
    ▼
Connect to MCP endpoint
http://45.76.169.98:8000/mcp
    │
    ▼
Initialize MCP session
    │
    ├── Session established + tools discovered → CONNECTED  ✓
    ├── Connection failed                      → UNHEALTHY
    └── Network error                          → DISCONNECTED
```

States: `CONNECTED` | `UNHEALTHY` | `DISCONNECTED`

## Tools

The Ombre adapter discovers tools dynamically from the remote Ombre server — no tool names are hardcoded in the Hub. The Hub forwards `tools/list` and `tools/call` directly to the remote server via the MCP Streamable HTTP protocol.

Current production deployment exposes tools such as:

| Tool | Description |
|---|---|
| `breath` | Memory breath — light recall |
| `hold` | Store a memory |
| `grow` | Expand / enrich a memory |
| `trace` | Trace memory connections |
| `pulse` | Memory health / status |
| `dream` | Deep semantic recall |

The available tool set depends on the remote Ombre server version.
