# Task011 — Remote MCP Transport Implementation

## Overview

The MCP Hub exposes a standard JSON-RPC 2.0 endpoint at `POST /mcp` that any MCP-compatible client (including Claude Desktop) can connect to.

## Endpoint

```
POST http://<host>:8080/mcp
Content-Type: application/json
```

## Protocol

JSON-RPC 2.0. All requests and responses follow the spec.

### Initialize

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {"name": "mcp-hub", "version": "0.1.0"},
    "capabilities": {"tools": {}},
    "servers": [
      {"name": "example", "version": "0.1.0", "running": true, "failed": false},
      {"name": "ntfy", "version": "0.1.0", "running": true, "failed": false},
      {"name": "ombre", "version": "0.1.0", "running": true, "failed": false}
    ]
  }
}
```

### Tool Discovery

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Dynamically discovers tools from all registered servers:
- `ombre_health`, `ombre_status`
- `ntfy_health`, `ntfy_info`, `ntfy_send`
- `echo`, `ping` (example)

### Tool Invocation

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"server":"ntfy","tool":"ntfy_health"}}'
```

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"server":"ombre","tool":"ombre_health"}}'
```

## Architecture

```
Claude Desktop (or any MCP client)
        │  POST /mcp  (JSON-RPC 2.0)
        ▼
Transport Server  (src/transport/server.py)
        │
        ▼
Router            (src/transport/router.py)
        │
        ▼
Handlers          (src/transport/handlers/)
        │
        ▼
Runtime           (src/runtime/)
        │
        ▼
ServerManager     (src/registry/)
        │
        ▼
MCP Servers       (mcp_servers/ → Ombre, ntfy, example)
```

## Tool Auto-Discovery

Tools are NOT hardcoded. They are discovered dynamically:

```
tools/list request
    → Router
    → handle_tools_list()
    → Runtime.list_tools()
    → ServerManager.list_tools()
    → for each registered server: server.get_tools()
```

Adding a new MCP server automatically adds its tools to the discovery response.
