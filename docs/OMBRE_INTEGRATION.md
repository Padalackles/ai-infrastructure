# Ombre Integration

## Status

Ombre is an **existing external MCP-compatible long-term memory service**.

It has already been deployed and validated independently at:

```
http://45.76.169.98:8000/mcp
```

This repository does **not** reimplement Ombre.

The MCP Hub connects to Ombre through an HTTP adapter.

---

## Architecture

```
Claude Desktop
        │
        ▼
     MCP Hub  (this repository, runs on VPS)
        │
        ├── Ombre Adapter  (mcp_servers/ombre/server.py)
        │        │
        │        ▼  HTTP
        │   Ombre Service  (external, already deployed)
        │   http://45.76.169.98:8000/mcp
        │
        └── ... other MCP services
```

---

## How It Works

1. **Discovery** scans `mcp_servers/ombre/manifest.yaml` at Hub startup
2. **OmbreServer** initializes and health-checks the external Ombre endpoint
3. On success: `✓ Ombre (CONNECTED)` appears in startup logs
4. Ombre is registered in the Hub's ServerManager
5. Router can target Ombre for `tools/call`
6. Health status is reported in `/health` and `/status`

---

## Configuration

```yaml
# mcp-hub/config.yaml
services:
  ombre:
    enabled: true
    endpoint: "${OMBRE_URL:-http://45.76.169.98:8000/mcp}"
```

Override via environment:
```bash
export OMBRE_URL=http://your-ombre-host:8000/mcp
```

---

## Tools Exposed

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

The available tool set depends on the remote Ombre server version and configuration.

---

## Health States

| State | Meaning |
|---|---|
| `CONNECTED` | MCP session established, tools discovered |
| `DISCONNECTED` | Ombre is unreachable (network error, timeout) |
| `UNHEALTHY` | Ombre responded but health check failed |

---

## Startup Log

```
Loading Services...
✓ Ombre (CONNECTED) — http://45.76.169.98:8000/mcp
Hub Ready
```

---

## Out of Scope

- Modifying Ombre source code
- Deploying Ombre
- Implementing Ombre business logic (memory, search, etc.)
- Authentication to Ombre (not currently required)
