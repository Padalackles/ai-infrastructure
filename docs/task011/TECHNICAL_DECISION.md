# Task011 — Technical Decision: Remote MCP Transport

## Current Implementation Analysis

The MCP Hub already implements a standard JSON-RPC 2.0 endpoint at `POST /mcp`:

| Layer | File | Role |
|---|---|---|
| Transport Server | `src/transport/server.py` | HTTP endpoint — accepts raw JSON-RPC body |
| Parser | `src/transport/jsonrpc.py` | Validates JSON-RPC 2.0 format |
| Router | `src/transport/router.py` | Method dispatch (initialize, tools/list, tools/call, health) |
| Handlers | `src/transport/handlers/` | Per-method logic |
| Runtime | `src/runtime/` | Middleware pass-through to ServerManager |
| Registry | `src/registry/` | Resolves servers, aggregates tools |

**Existing MCP methods:**

| Method | Handler | Status |
|---|---|---|
| `initialize` | `handlers/initialize.py` | ✅ Returns protocolVersion, serverInfo, capabilities, servers |
| `tools/list` | `handlers/tools.py` | ✅ Aggregates tools from all registered servers via Runtime → ServerManager |
| `tools/call` | `handlers/tools.py` | ✅ Dispatches to registered server via Runtime → ServerManager |
| `health` | `handlers/health.py` | ✅ Aggregates health from all servers |

**Auto-discovery:** Tool list is generated dynamically from all registered servers. No hardcoded tool names. Adding a new MCP server automatically adds its tools.

## Recommendation

**Keep the current custom JSON-RPC 2.0 implementation.**

### Rationale

1. **Already complete** — All required MCP methods (initialize, tools/list, tools/call) are implemented and tested
2. **Zero dependencies** — No external MCP SDK needed; only FastAPI + Pydantic
3. **Plugin-native** — Tool discovery works through the existing Registry → ServerManager → BaseMCPServer chain
4. **Adapter-safe** — Ombre and ntfy adapters work without modification
5. **MCP-compliant** — Follows JSON-RPC 2.0 spec and MCP protocol conventions

### Impact on Existing Code

**None.** The remote transport is already in place. This task documents, tests, and verifies it.

### What Task011 Adds

- Integration tests verifying the remote MCP contract
- Documentation of the endpoint and protocol
- README update with remote MCP usage
