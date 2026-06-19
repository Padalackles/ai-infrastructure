# Project State

**Status:** 🟡 In Progress
**Version:** v0.4.0
**Last Updated:** 2026-06-19 — Activity Gateway implemented (Task A002)

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

**Phase 6 — Production Hardening** (see ROADMAP.md)

- Phase 1–5: ✅ Complete (Infrastructure → Gateway → Registry → Services → Claude Desktop)
- Phase 6: 🟡 In Progress — Docker Production, auth, diagnostics, docs

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
| Task-016 | ✅ | Scheduler Framework — TypeScript scheduler service with Job registry |
| Task-A001 | ✅ | Activity Event Schema — unified event contract for device activity pipeline |
| Task-A002 | 🟡 | Activity Gateway — HTTP ingest endpoint (POST /activity/events) |

---

## Activity Subsystem (New)

**Status:** 🟡 In Progress — Gateway implemented

The Activity subsystem ingests device events (Android → MacroDroid → Gateway),
normalizes them into a unified schema, stores them, and triggers Claude awareness.

**Pipeline:**

```
Android (MacroDroid) → Activity Gateway → Event Normalizer → Event Database → Decision Script → Claude Trigger
```

| Component | Status |
|---|---|
| Event Schema | ✅ Defined (Task A001 — `docs/activity/SCHEMA.md`) |
| Activity Gateway | 🟡 Implemented (Task A002 — POST /activity/events) |
| Event Normalizer | ⬜ Planned |
| Event Database | ⬜ Planned |
| Decision Script | ⬜ Planned |
| Claude Trigger | ⬜ Planned |

**Design Principles:** Source agnostic, normalize late, schema-versioned, typed payload.
See `docs/activity/SCHEMA.md` for the full event contract.

---

## Current Task

| Field | Value |
|---|---|
| **Task ID** | Task-A002 |
| **Status** | 🟡 In Progress |
| **Description** | Activity Gateway — HTTP POST /activity/events endpoint |

---

## Repository Structure

```
ai-infrastructure/
├── mcp-hub/                 Python MCP Hub (FastAPI)
│   └── src/
│       ├── main.py          Entry point — 8-step startup pipeline
│       ├── config/          load_config() — unified YAML config
│       ├── lifecycle/       BaseMCPServer, ToolNotFoundError
│       ├── registry/        ServerManager — service registry
│       ├── loader/          Discovery, Loader, PythonLoader
│       ├── router/          Router + RouterInterface + RouteRegistry
│       ├── runtime/         Runtime — middleware pass-through
│       ├── transport/       JSON-RPC 2.0 stack (server, handlers)
│       ├── models/          ServiceInfo, PluginManifest, HubState, RuntimeContext
│       ├── api/             REST endpoints (/health, /status, /tools)
│       ├── core/            EventBus, RemoteMCPClient, HubState, Auth, Audit, Metrics
│       └── utils/           generate_id() helpers
├── services/
│   └── scheduler/           TypeScript Scheduler Service
│       └── src/
│           ├── index.ts     Entry point — startup + signal handling
│           ├── scheduler.ts Cron engine + job execution + logging
│           ├── registry.ts  JobRegistry — register/get/remove
│           ├── config.ts    YAML config loader with defaults
│           ├── types.ts     Job interface + ExecutionResult
│           └── jobs/        DailyJournal (placeholder)
├── activity/
│   ├── types.ts             Activity Event Schema — TypeScript contract
│   └── gateway/             Activity Gateway (Python/FastAPI)
│       ├── __init__.py
│       ├── models.py        Pydantic request/response models
│       ├── service.py       ID generation, timestamp, event assembly
│       └── router.py        POST /activity/events endpoint
├── docs/
│   └── activity/
│       └── SCHEMA.md        Activity Event Schema documentation
├── mcp_servers/             MCP server adapters (Python)
├── caddy/                   Reverse proxy config
├── cloudflare/              Tunnel config
└── docker-compose.yml       Deployment orchestration
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
| GitHub MCP Server | Future |
| Filesystem MCP Server | Future |
| Docker Production optimization | Task-015 |
| Activity Gateway | Task A002+ |
| Event Normalizer | Task A003+ |
| Event Database | Task A004+ |
| Decision Script | Future |
| Claude Trigger (Activity) | Future |
| Health-check loop | Future |
| Remote server adapters (HTTP/SSE/WebSocket) | Future |
| Prometheus / Grafana metrics | Future |
| CI/CD pipeline | Future |

---

## Installed Components

| Component | Status |
|---|---|
| MCP Hub (Gateway) | ✅ Runtime |
| Scheduler Service | ✅ Runtime (TypeScript, cron-based background jobs) |
| Caddy | ✅ Running (Let's Encrypt TLS) |
| Cloudflare | ✅ DNS + Proxy |
| Ombre MCP | ✅ External (45.76.169.98:8000) — 6 tools |
| ntfy MCP | ✅ External (ntfy.sh) — 3 tools |
| Activity Subsystem | 🟡 In Design (Event Schema defined) |
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
| **Hash** | (pending — Task A001) |
| **Summary** | feat(activity): introduce unified activity event schema |

---

## Notes

When resuming this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Read ARCHITECTURE.md
4. Continue from **Task-015** — Docker Production
