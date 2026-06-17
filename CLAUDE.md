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

## Mandatory Development Workflow

Every completed task must follow this sequence:

1. **Implement** the required changes
2. **Review** all changes for correctness
3. **Review documentation** — update README, ARCHITECTURE, PROJECT_STATE, ROADMAP as needed
4. **Verify architecture consistency** — does the implementation match ARCHITECTURE.md?
5. **Run local tests** — `cd mcp-hub && python -m pytest tests/ -v`
6. **Execute** `git status` — review what changed
7. **Execute** `git add .` — stage all changes
8. **Execute** `git commit -m "..."` — descriptive commit message
9. **Execute** `git push` — push to GitHub
10. **Update PROJECT_STATE.md** — mark task complete, update Last Commit
11. **Continue** to the next task

## Rules

- Documentation must stay synchronized with implementation.
- Architecture documents must remain consistent with code.
- No task is considered complete until GitHub has been updated.
- Never create duplicate documentation files. Each concern has one canonical file:
  - `README.md` — Project introduction
  - `ARCHITECTURE.md` — System architecture
  - `ROADMAP.md` — Long-term planning
  - `PROJECT_STATE.md` — Current development status (single source of truth)
  - `CLAUDE.md` — Development workflow and coding rules (this file)
  - `DECISIONS.md` — Stable architectural decisions
