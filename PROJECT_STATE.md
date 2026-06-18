# Project State

**Status:** 🟡 In Progress
**Version:** v0.3.1
**Last Updated:** 2026-06-19 — MCP Tool 命名修复 + 诊断日志

---

## Project Goal

Build an **MCP Hub** deployed on a VPS that connects Claude Desktop to multiple MCP services.

**Design Principles:**

- **MCP First** — every capability is an MCP service. Core never grows business logic.
- **Gateway, not Application** — the Hub routes; servers implement.
- **Plugin Architecture** — new MCP = new directory, zero Core changes.
- **Docker is Deployment Only** — architecture lives in code, not containers.

---

## Current Phase

**Phase 2 — MCP Hub Gateway** (see ROADMAP.md)

---

## Task Status

| Task | Status | Description |
|---|---|---|
| Task-001 | ✅ | Project Specification — MCP Hub architecture |
| Task-002 | ✅ | Foundation — repository structure, FastAPI stubs |
| Task-003 | ✅ | MCP Hub Skeleton — modules, models, interfaces |
| Task-004 | ✅ | Registry — ServerManager, Discovery |
| Task-005 | ✅ | Router — JSON-RPC dispatch, handlers |
| Task-006 | ✅ | Lifecycle Manager — BaseMCPServer, lifecycle_start/stop |
| Task-007 | ✅ | Configuration — config.yaml, load_config() |
| Task-008 | ✅ | Plugin Loader — Loader ABC, PythonLoader |
| Task-009 | ✅ | Ombre Adapter — HTTP bridge to external Ombre |
| Task-010 | ✅ | ntfy External Service Integration — via ntfy.sh API |
| Task-011 | ✅ | Remote MCP Transport — protocol validated, Claude Desktop Ready |
| Task-012 | ✅ | Domain + HTTPS + Cloudflare — deployed at raven-victor.click |
| Task-013 | ✅ | Claude Desktop End-to-End Integration (12/12 tests passed) |
| Task-014 | ✅ | Real ntfy Notification Test — notify_send verified via Hub |
| Task-015 | ⬜ | Docker Production |
| Task-016 | 🟡 | Production Hardening (MCP Auth ✅, Tool naming ✅, diagnostics ✅) |
| Task-017 | ✅ | MCP Tool 诊断 — 排查 breath/trace 消失问题，追溯全链路 |
| Task-018 | ✅ | 修复 notify.send → notify_send（`.` 违反 ^[a-zA-Z0-9_-]{1,64}$） |
| Task-019 | ✅ | 隐藏内部 Tool — ExampleServer 复用 HUB_EXPOSE_INTERNAL_TOOLS |
| Task-020 | ✅ | 诊断日志 — 4 处临时日志 + TROUBLESHOOTING_MCP_TOOLS.md |
| Task-021 | ✅ | 文档筛查 — 7 docs 修复（工具名、状态、环境变量、架构图） |

---

## Current Task

| Field | Value |
|---|---|
| **Task ID** | Task-015 |
| **Status** | ⬜ Planned |
| **Description** | Docker Production — optimize docker-compose for production deployment |

---

## Hub Module Structure

```
mcp-hub/src/
├── main.py              Entry point — 7-step startup pipeline
├── config/              load_config() — unified YAML config
├── lifecycle/           BaseMCPServer, ToolNotFoundError
├── registry/            ServerManager — service registry
├── loader/              Discovery, Loader, PythonLoader
├── router/              Router + RouterInterface + RouteRegistry
├── runtime/             Runtime — middleware pass-through
├── transport/           JSON-RPC 2.0 stack (server, handlers)
├── models/              ServiceInfo, PluginManifest, HubState, RuntimeContext
├── api/                 REST endpoints (/health, /status, /tools)
├── core/                EventBus, RemoteMCPClient, HubState, Auth, Audit, Metrics
└── utils/               generate_id() helpers
```

---

## Completed Tasks

1. Task-001 — Project Specification (MCP Hub architecture)
2. Task-002 — Foundation (repository structure, stubs)
3. Task-003 — MCP Hub Core Runtime
4. Task-004 — JSON-RPC 2.0 Transport Layer
5. Task-004.1 — Lifecycle fixes, Discovery isolation, API stats
6. Task-004 Review — Router→handlers, Runtime, Loader, unified dirs
7. Task-002 Refactor — Repository architecture alignment
8. Task-Documentation-Refinement — PROJECT_STATE, CLAUDE, DECISIONS
9. Task-014 — Real ntfy Notification Test (notify_send verified via Hub)
10. Task-017 — MCP Tool 诊断（确认 Hub 层无过滤，Ombre 6 tool 全部在线）
11. Task-018 — 修复 Tool 命名（notify.send → notify_send）
12. Task-019 — 隐藏内部 Tool（ExampleServer 复用 HUB_EXPOSE_INTERNAL_TOOLS）
13. Task-020 — 诊断日志 + TROUBLESHOOTING_MCP_TOOLS.md
14. Task-021 — 文档筛查（INFRASTRUCTURE, CLAUDE_DESKTOP, NOTIFICATION_MCP, OMBRE_INTEGRATION, REGISTRY, SPECIFICATION）

---

## Architecture

```
                    Claude Desktop  (local)
                         │  JSON-RPC / MCP
          ╔══════════════╪══════════════╗
          ║         STABLE CORE         ║
          ║                             ║
          ║   Gateway → Registry       ║
          ║   Router  → Handlers       ║
          ║   Runtime → Lifecycle      ║
          ║   Transport (JSON-RPC)     ║
          ║   Config                   ║
          ╚══════════════╪══════════════╝
                         │
          ╔══════════════╪══════════════╗
          ║   EXTENSIBLE MCP SERVICES   ║
          ║                             ║
          ║  Ombre │ ntfy │ Filesystem ║
          ║  GitHub │ Browser │ ...    ║
          ╚═════════════════════════════╝
```

---

## Implemented

| Capability | Location |
|---|---|
| MCP Hub Gateway (FastAPI) | `mcp-hub/src/main.py` |
| Server lifecycle | `mcp-hub/src/lifecycle/` |
| ServerManager (registry) | `mcp-hub/src/registry/` |
| Auto-discovery + Loader | `mcp-hub/src/loader/` |
| Event bus | `mcp-hub/src/core/events.py` |
| JSON-RPC 2.0 transport | `mcp-hub/src/transport/` |
| Router + handlers | `mcp-hub/src/router/` + `transport/handlers/` |
| Runtime middleware | `mcp-hub/src/runtime/` |
| REST endpoints | `mcp-hub/src/api/routes.py` |
| Configuration | `mcp-hub/src/config/` |
| Shared models | `mcp-hub/src/models/` |
| RemoteMCPClient (Ombre bridge) | `mcp-hub/src/core/remote_client.py` |
| Audit logging | `mcp-hub/src/core/observability/audit.py` |
| Request context (contextvars) | `mcp-hub/src/core/request_context.py` |
| MCP Auth (Bearer Token) | Integrated in `mcp-hub/src/main.py` (MCPProxy) |
| Diagnostic logging (temporary) | `main.py`, `transport/server.py`, `mcp_servers/{ombre,ntfy}/server.py` |
| MCP Tool naming compliance | `notify.send` → `notify_send` |
| Internal tool hiding | `HUB_EXPOSE_INTERNAL_TOOLS` controls ExampleServer + HubServer |
| Docker Compose | `docker-compose.yml` |
| Unit tests | `mcp-hub/tests/` (166 tests) |

## Not Yet Implemented

| Capability | Target |
|---|---|
| GitHub MCP Server | Task-015+ |
| Filesystem MCP Server | Task-015+ |
| Docker Production optimization | Task-015 |
| Health-check loop | Future |
| Remote server adapters (HTTP/SSE/WebSocket) | Future |
| Prometheus / Grafana metrics | Future |
| CI/CD pipeline | Future |

---

## Installed Components

| Component | Status |
|---|---|
| MCP Hub (Gateway) | ✅ Runtime |
| Caddy | ✅ Running (Let's Encrypt TLS) |
| Cloudflare | ✅ DNS + Proxy |
| Ombre MCP | ✅ External (45.76.169.98:8000) — 6 tools |
| ntfy MCP | ✅ External (ntfy.sh) — 3 tools |
| Filesystem MCP | Reserved |
| GitHub MCP | Reserved |

---

## Repository Health

| Check | Status |
|---|---|
| Documentation | ✅ Consistent |
| Architecture | ✅ Stable Core / Extensible Service Layer |
| Architecture Audit | ✅ Pre-deployment check passed (2026-06-18) |
| Tests | ✅ 6 test files (lifecycle, discovery, transport, tools, auth, ntfy) |
| GitHub Sync | ✅ Up to date |
| No duplicate docs | ✅ Single source of truth per concern |
| CHANGELOG | ✅ Created |
| Troubleshooting doc | ✅ `docs/TROUBLESHOOTING_MCP_TOOLS.md` |

## Last Commit

| Field | Value |
|---|---|
| **Hash** | `19ad210` |
| **Summary** | docs: screen and fix all docs/ for accuracy — tool names, status, env vars, architecture |

---

## Notes

When resuming this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Read ARCHITECTURE.md
4. Continue from **Task-015** — Docker Production
