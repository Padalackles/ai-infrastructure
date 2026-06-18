# Claude Desktop — Remote MCP Configuration

Connect Claude Desktop / Claude Web to the MCP Hub at `https://raven-victor.click/mcp`.

## Architecture

```
Claude (Desktop / Web)
    │  HTTPS
    ▼
Cloudflare (DNS + DDoS, SSL Full strict)
    │  HTTPS :443
    ▼
Caddy (Reverse Proxy + Let's Encrypt TLS)
    │  HTTP :8080
    ▼
MCP Hub (FastAPI + FastMCP Streamable HTTP)
    │
    ├── Ombre  ──HTTP──► 45.76.169.98:8000  (long-term memory)
    ├── ntfy   ──HTTP──► ntfy.sh             (push notifications)
    └── example                              (test server)
```

---

## Authentication

### Current: `AUTH_MODE=none` (default)

Claude Web Connector does **not** support custom HTTP headers (Bearer Token).
Setting `MCP_HUB_AUTH_TOKEN=` (empty) disables authentication so Claude Web
can connect directly. Security relies on:

- HTTPS (Let's Encrypt + Cloudflare Full strict)
- Domain obscurity
- Cloudflare WAF / Rate Limiting (recommended)
- Cloudflare Access / IP whitelist (future option)

### Future: `AUTH_MODE=bearer`

When MCP clients add Bearer Token support, set `MCP_HUB_AUTH_TOKEN=<token>`
in `.env`. The Hub will enforce `Authorization: Bearer <token>` on all
`POST /mcp` requests. Claude Desktop (local app) already supports custom
headers; only Claude Web is restricted.

### Future: `AUTH_MODE=oauth`

Full OAuth 2.0 flow via FastMCP's built-in `AuthSettings`. Requires:
- OAuth provider (e.g., Auth0, Google)
- `issuer_url` + `resource_server_url` configuration
- Client registration

---

## Claude Web — Add Custom Connector

1. Open Claude Web → **Settings** → **Connectors**
2. Click **Add Custom Connector**
3. Fill in:
   - **Name:** `MCP Hub`
   - **Remote MCP Server URL:** `https://raven-victor.click/mcp`
4. Leave OAuth fields blank
5. Click **Connect**

> **Note:** Claude Web's "Add Custom Connector" beta currently only supports
> unauthenticated or OAuth connections. Bearer Token is not available as an
> input field. If you need authenticated access, use Claude Desktop instead.

## Claude Desktop — Configuration

Configuration file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mcp-hub": {
      "type": "http",
      "url": "https://raven-victor.click/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE",
        "Content-Type": "application/json"
      }
    }
  }
}
```

Replace `YOUR_TOKEN_HERE` with the value of `MCP_HUB_AUTH_TOKEN` from `.env`.

## Available Tools

After connection, Claude discovers these tools automatically:

| Tool | Server | Description |
|---|---|---|
| `echo` | example | Echo back input (pipeline verification) |
| `ping` | example | Always returns pong |
| `ombre_health` | ombre | Check Ombre connectivity |
| `ombre_status` | ombre | Get Ombre service metadata |
| `ntfy_health` | ntfy | Check ntfy service health |
| `ntfy_info` | ntfy | Get ntfy service metadata |
| `ntfy_send` | ntfy | Send a push notification |

## Troubleshooting

| Symptom | Check |
|---|---|
| Connection refused | Verify network access to `raven-victor.click:443` |
| HTTP 401 | Token is missing or incorrect (set `MCP_HUB_AUTH_TOKEN=` to disable) |
| No tools listed | Hub is running (`docker compose ps`) |
| Tool call fails | Check server-specific logs (`docker compose logs mcp-hub`) |
| Claude Web: "Couldn't register" | Auth is enabled — clear `MCP_HUB_AUTH_TOKEN` in `.env` |
