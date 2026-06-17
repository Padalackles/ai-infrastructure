# MCP — Model Context Protocol

## What is MCP?

The Model Context Protocol (MCP) is an open standard that lets LLMs interact with external tools, data sources, and services through a uniform interface. In this project, MCP is the backbone — every capability is exposed as an MCP server.

## How This Project Uses MCP

```
Claude Desktop
    │
    │  MCP protocol (stdio / HTTP)
    ▼
MCP Hub ─── registry, auth, routing
    │
    ├── GitHub MCP      →   repos, issues, PRs
    ├── Filesystem MCP  →   local file read/write
    ├── Ombre MCP       →   Ombre platform
    └── ntfy MCP        →   push notifications
```

## MCP Server Catalog

### GitHub MCP
- **Repo:** TBD
- **Protocol:** HTTP (port 3000)
- **Capabilities:** repo CRUD, issue tracking, PR management, code search

### Filesystem MCP
- **Repo:** TBD
- **Protocol:** HTTP (port 3000)
- **Capabilities:** read files, write files, list directories, search

### Ombre MCP
- **Repo:** TBD
- **Protocol:** HTTP (port 3000)
- **Capabilities:** TBD (Ombre platform integration)

### ntfy MCP
- **Repo:** TBD
- **Protocol:** HTTP (port 3000)
- **Capabilities:** send push notifications, subscribe to topics

## Adding a New MCP Server

1. Create `mcp-servers/<name>/Dockerfile`
2. Create `mcp-servers/<name>/config.yaml`
3. Register in `mcp-hub/config.yaml` under `mcp_servers`
4. Add the service to `docker-compose.yml`
5. Document capabilities in this file

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/en/docs/claude/mcp)
