# Ombre Integration

## Status

Ombre is an **existing external MCP-compatible long-term memory service**.

It has already been deployed and validated independently at:

```
http://45.76.169.98:8000
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
        │   http://45.76.169.98:8000
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
    endpoint: "${OMBRE_ENDPOINT:-http://45.76.169.98:8000}"
```

Override via environment:
```bash
export OMBRE_ENDPOINT=http://your-ombre-host:8000
```

---

## Tools Exposed

| Tool | Description |
|---|---|
| `ombre_health` | Check connectivity to external Ombre |
| `ombre_status` | Get Ombre endpoint info and connection state |

---

## Health States

| State | Meaning |
|---|---|
| `CONNECTED` | Ombre returned HTTP 200 with `{"status":"ok"}` |
| `DISCONNECTED` | Ombre is unreachable (network error, timeout) |
| `UNHEALTHY` | Ombre responded but health check failed |

---

## Startup Log

```
Loading Services...
✓ Ombre (CONNECTED) — http://45.76.169.98:8000
Hub Ready
```

---

## Out of Scope

- Modifying Ombre source code
- Deploying Ombre
- Implementing Ombre business logic (memory, search, etc.)
- Authentication to Ombre (future task)
