# CLAUDE.md

## Project

MCP Gateway (Hub) — not an AI application, not a chatbot. Deployed on a VPS.
Claude Desktop is the unified user entry point. The Hub routes requests to MCP services.

## Architecture

```
Claude Desktop (local)
    ↓  JSON-RPC / MCP
MCP Hub (VPS)
    ├── Ombre MCP
    ├── ntfy MCP
    ├── Filesystem MCP
    ├── GitHub MCP
    └── ...
```

Stable Core → Extensible MCP Service Layer.
Adding a new MCP requires zero Core changes.

## Principles

- MCP First — every capability is an MCP service
- Hub is orchestration only — zero business logic
- Documentation First — update docs alongside code
- Keep modules independent
- Update PROJECT_STATE.md after every milestone

## Workflow

1. Read PROJECT_STATE.md
2. Read ARCHITECTURE.md
3. Continue Current Task
4. Update documentation
