# Discovery Validation

## Test: Standard MCP Client tool discovery

### Initialize

```json
// Request
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}

// Response
{
  "protocolVersion": "2024-11-05",
  "serverInfo": {"name": "mcp-hub", "version": "0.1.0"},
  "capabilities": {"tools": {}},
  "servers": [
    {"name": "example", "version": "0.1.0", "running": true},
    {"name": "ntfy", "version": "0.1.0", "running": true},
    {"name": "ombre", "version": "0.1.0", "running": true}
  ]
}
```

### tools/list

```json
// Request
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}

// Response
{
  "tools": [
    {"server": "example", "tools": [{"name": "echo", ...}, {"name": "ping", ...}]},
    {"server": "ntfy", "tools": [
      {"name": "ntfy_health", ...},
      {"name": "ntfy_info", ...},
      {"name": "ntfy_send", ...}
    ]},
    {"server": "ombre", "tools": [
      {"name": "ombre_health", ...},
      {"name": "ombre_status", ...}
    ]}
  ]
}
```

## Discovered Tools

| Tool | Server | Confirmed |
|---|---|---|
| `ntfy_health` | ntfy | ✅ |
| `ntfy_info` | ntfy | ✅ |
| `ntfy_send` | ntfy | ✅ |
| `ombre_health` | ombre | ✅ |
| `ombre_status` | ombre | ✅ |
| `echo` | example | ✅ |
| `ping` | example | ✅ |

## Verification

Tools are auto-discovered from all registered servers via Registry → ServerManager → BaseMCPServer.get_tools(). No hardcoded tool names.
