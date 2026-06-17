# MCP Protocol Audit

## Current Implementation (`src/transport/`)

| Component | File | Role |
|---|---|---|
| Request model | `request.py` | JSON-RPC 2.0 request validation (Pydantic) |
| Response model | `response.py` | JSON-RPC 2.0 response + error builders |
| Parser | `jsonrpc.py` | Raw dict → typed request, error handling |
| Router | `router.py` | Method dispatch (initialize, tools/list, tools/call, health) |
| Handlers | `handlers/` | Per-method logic (initialize, tools, health) |
| Server | `server.py` | HTTP endpoint at `POST /mcp` |

## MCP Specification Requirements (2024-11-05)

### 1. initialize

| Requirement | Status | Notes |
|---|---|---|
| Returns `protocolVersion` | ✅ | `"2024-11-05"` from config |
| Returns `capabilities` | ✅ | `{"tools": {}}` from config |
| Returns `serverInfo` | ✅ | `{"name": "mcp-hub", "version": "0.1.0"}` |
| Client sends `notifications/initialized` | ✅ | Supported (notifications with no id) |

### 2. tools/list

| Requirement | Status | Notes |
|---|---|---|
| Returns array of tool definitions | ✅ | Aggregated from all registered servers |
| Each tool has `name` | ✅ | e.g. `ntfy_send` |
| Each tool has `description` | ✅ | Human-readable |
| Each tool has `inputSchema` | ✅ | JSON Schema object |
| No hardcoded tools | ✅ | Dynamic via `server.get_tools()` |

### 3. tools/call

| Requirement | Status | Notes |
|---|---|---|
| Accepts `name` (tool name) | ✅ | Via `params.tool` |
| Accepts `arguments` | ✅ | Via `params.arguments` |
| Returns structured result | ✅ | `{"server","tool","result"}` |
| Unknown tool → error | ✅ | Code -32002 |

### 4. Error Handling

| Code | Meaning | Status |
|---|---|---|
| -32700 | Parse error | ✅ |
| -32600 | Invalid Request | ✅ |
| -32601 | Method not found | ✅ |
| -32602 | Invalid params | ✅ |
| -32603 | Internal error | ✅ |
| -32001 | Server not found | ✅ (Hub extension) |
| -32002 | Tool not found | ✅ (Hub extension) |

### 5. Transport

| Requirement | Status | Notes |
|---|---|---|
| HTTP POST | ✅ | `POST /mcp` |
| Content-Type: application/json | ✅ | FastAPI handles this |
| JSON-RPC 2.0 envelope | ✅ | `{"jsonrpc":"2.0","id":...,"method/result/error":...}` |

## Differences / Gaps

| Item | Detail | Risk |
|---|---|---|
| `tools/call` params use `params.server` + `params.tool` | MCP spec uses `params.name` + `params.arguments` directly | **Low** — our format wraps MCP format. Claude Desktop sends `tools/call` with `name` and `arguments` at the top level. Our handler reads from `params.server` + `params.tool` which is a Hub-level routing convention. A direct MCP `tools/call` without `server` would fail. |

### ⚠️ Critical Finding: tools/call parameter mismatch

MCP spec expects:
```json
{"method":"tools/call","params":{"name":"ntfy_send","arguments":{"title":"X","message":"Y"}}}
```

Our implementation expects:
```json
{"method":"tools/call","params":{"server":"ntfy","tool":"ntfy_send","arguments":{...}}}
```

This is a Hub-level routing decision (tools are namespaced by server). A direct MCP client would not include `server` in params — it would use the tool name globally.

## Risk Assessment

**Risk: Medium** — The `tools/call` parameter format differs from the base MCP spec because our Hub routes tools by server namespace. This is architecturally correct for a multi-server Hub but would need adaptation for direct Claude Desktop connection.

**Mitigation:** Add a `tools/call` handler that accepts both formats — direct MCP format (resolve tool name across all servers) and namespaced format (server.tool).

## Recommendation

Fix `tools/call` to accept the standard MCP format before declaring Claude Desktop Ready.
