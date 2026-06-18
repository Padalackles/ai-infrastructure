# Claude Desktop — Remote MCP Configuration

Connect Claude Desktop to the MCP Hub at `https://raven-victor.click/mcp`.

## Architecture

```
Claude Desktop (local)
    │  HTTPS + Bearer Token
    ▼
MCP Hub Gateway (VPS: raven-victor.click)
    │
    ├── Ombre  ──HTTP──► 45.76.169.98:8000  (long-term memory)
    ├── ntfy   ──HTTP──► ntfy.sh             (push notifications)
    └── example                              (test server)
```

## Configuration File

### macOS
`~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
`%APPDATA%\Claude\claude_desktop_config.json`

### Linux
`~/.config/Claude/claude_desktop_config.json`

## Configuration

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

Replace `YOUR_TOKEN_HERE` with the value of `MCP_HUB_AUTH_TOKEN` from the VPS `.env` file.

> **Note:** Claude Desktop MCP transport format may vary by version.
> The MCP Hub exposes a standard JSON-RPC 2.0 endpoint compatible with any
> MCP client supporting HTTP transport with custom headers.

## Available Tools

After connection, Claude Desktop discovers these tools automatically:

| Tool | Server | Description |
|---|---|---|
| `echo` | example | Echo back input (pipeline verification) |
| `ping` | example | Always returns pong |
| `ombre_health` | ombre | Check Ombre connectivity |
| `ombre_status` | ombre | Get Ombre service metadata |
| `ntfy_health` | ntfy | Check ntfy service health |
| `ntfy_info` | ntfy | Get ntfy service metadata |
| `ntfy_send` | ntfy | Send a push notification |

## Verification

After configuring Claude Desktop, restart it and verify:

```bash
# From CLI (if available):
curl -sk -X POST https://raven-victor.click/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Claude Desktop should list all 7 tools across 3 servers.

## Troubleshooting

| Symptom | Check |
|---|---|
| Connection refused | Verify network access to `raven-victor.click:443` |
| HTTP 401 | Token is missing or incorrect |
| No tools listed | Hub is running (`docker compose ps`) |
| Tool call fails | Check server-specific logs (`docker compose logs mcp-hub`) |
