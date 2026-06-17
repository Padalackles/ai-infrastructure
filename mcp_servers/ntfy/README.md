# ntfy MCP Service

Push notification service — self-contained MCP server.

## Status

No external deployment required. Health always returns `ok`.
Optional HTTP forwarding to ntfy.sh via `NTFY_BASE_URL` env var.

## Files

| File | Purpose |
|---|---|
| `manifest.yaml` | Service declaration for Hub auto-discovery |
| `adapter.py` | Notification adapter (stdout + optional HTTP) |
| `server.py` | BaseMCPServer subclass — lifecycle + tool dispatch |

## Tools

| Tool | Description |
|---|---|
| `ntfy_health` | Service health check |
| `ntfy_info` | Service metadata (name, version, endpoint) |
| `ntfy_send` | Send push notification (stdout or HTTP) |

## Configuration

```bash
# Optional: forward to ntfy.sh
export NTFY_BASE_URL=https://ntfy.sh
export NTFY_TOPIC=mcp-hub
```
