# Invocation Validation

## Standard MCP Format (params.name)

```json
// Request
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ntfy_health"}}

// Response
{"result":{"server":"ntfy","tool":"ntfy_health","result":{"name":"ntfy","status":"ok"}}}
```

```json
// Request
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"ombre_health"}}

// Response
{"result":{"server":"ombre","tool":"ombre_health","result":{"name":"ombre","status":"CONNECTED"}}}
```

## Hub Namespaced Format (params.server + params.tool)

```json
// Request
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"server":"ntfy","tool":"ntfy_health"}}

// Response
{"result":{"server":"ntfy","tool":"ntfy_health","result":{"name":"ntfy","status":"ok"}}}
```

## Error Handling

```json
// Unknown tool (global)
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"nonexistent"}}
→ {"error":{"code":-32002,"message":"Tool not found on any server: nonexistent"}}

// Unknown server
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"server":"ghost","tool":"x"}}
→ {"error":{"code":-32001,"message":"Server not found: ghost"}}
```

## Verification

All tool invocations succeed in both standard MCP format and Hub namespaced format. Tool names are resolved globally when no server is specified.
