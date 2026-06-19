# Project State

**Status:** 🟡 In Progress
**Version:** v0.11.0
**Last Updated:** 2026-06-19 — Decision Engine Phase 2: configuration-driven rule system (Task A009)

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
| Task-A002 | ✅ | Activity Gateway — HTTP ingest endpoint (POST /activity/events) |
| Task-A003 | ✅ | Event Normalizer — canonical event transformation |
| Task-A004 | ✅ | Activity SQLite Persistence — repository + auto-create DB |
| Task-A005 | ✅ | MacroDroid Integration — documented, tested, 30 integration tests |
| Task-A006 | ✅ | Support Current Android Events — network.wifi.connected canonical type + payload normalizer |
| Task-A007 | ✅ | Event Query Service — Service layer + GET /activity/recent, /latest, /history, /types |
| Task-A008 | ✅ | Decision Engine Phase 1 — rule framework + Trigger model + 60s scheduler |
| Task-A009 | ✅ | Decision Engine Phase 2 — config-driven rules, SessionAnalyzer, Cooldown, RuleManager |

---

## Activity Subsystem (New)

**Status:** 🟡 In Progress — Decision Engine Phase 2 complete

The Activity subsystem ingests device events (Android → MacroDroid → Gateway),
normalizes them into a unified schema, stores them, and triggers Claude awareness.

**Pipeline:**

```
Android (MacroDroid) → Activity Gateway → Event Normalizer → Event Database → Decision Engine → Claude Trigger
```

| Component | Status |
|---|---|
| Event Schema | ✅ Defined (Task A001 — `docs/activity/SCHEMA.md`) |
| Activity Gateway | ✅ Implemented (Task A002 — POST /activity/events) |
| Event Normalizer | ✅ Implemented (Task A003 — maps collector→canonical types, normalizes payloads, updated for screen.on/off + app.opened/closed) |
| Event Database | ✅ Implemented (Task A004 — SQLite persistence, repository API) |
| Activity Service | ✅ Implemented (Task A007 — read-only query layer) |
| Query API | ✅ Implemented (Task A007 — GET /recent, /latest, /history, /types) |
| Decision Engine | ✅ Implemented (Task A008 + A009 — config-driven rule engine, SessionAnalyzer, Cooldown, RuleManager) |
| Claude Trigger | ⬜ Planned |

**Design Principles:** Source agnostic, normalize late, schema-versioned, typed payload.
See `docs/activity/SCHEMA.md` for the full event contract.

---

## Current Task

| Field | Value |
|---|---|
| **Task ID** | Task-A009 |
| **Status** | ✅ Completed |
| **Description** | Decision Engine Phase 2 — Configuration-driven rule system: SessionAnalyzer, Cooldown, RuleManager, real rules (screen_long_use, app_long_use) |

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
├── decision/                Decision Engine (Python)
│   ├── __init__.py          Public API
│   ├── models.py            Trigger dataclass — stable schema
│   ├── rules.py             @register framework + real config-driven rules
│   ├── service.py           DecisionService.evaluate()
│   ├── scheduler.py         60s loop + CLI entry point
│   ├── cooldown.py          CooldownStore ABC + MemoryCooldownStore
│   ├── rule_manager.py      RuleManager — YAML config facade
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py        load_rules() / reload_rules()
│   │   └── rules.yaml       All rule parameters (thresholds, apps, cooldowns)
│   ├── analyzers/
│   │   ├── __init__.py
│   │   └── session.py       SessionAnalyzer — screen & app sessions
│   └── tests/
│       ├── test_models.py
│       ├── test_rules.py
│       ├── test_service.py
│       ├── test_scheduler.py
│       ├── test_config_loader.py
│       ├── test_rule_manager.py
│       ├── test_cooldown.py
│       └── test_session_analyzer.py
├── activity/
│   ├── types.ts             Activity Event Schema — TypeScript contract
│   ├── gateway/             Activity Gateway (Python/FastAPI)
│   │   ├── __init__.py
│   │   ├── models.py        Pydantic request/response models
│   │   ├── service.py       ID generation, timestamp, event assembly
│   │   └── router.py        POST /activity/events endpoint
│   ├── normalizer/          Event Normalizer (Python)
│   │   ├── __init__.py
│   │   ├── mappings.py      Collector→canonical event type mapping table
│   │   ├── service.py       normalize_event() + payload normalizers
│   │   └── tests/
│   │       └── test_normalizer.py  26 unit tests
│   └── storage/             Activity Storage (Python)
│       ├── __init__.py
│       ├── database.py      SQLite connection + table creation
│       ├── repository.py    ActivityRepository — save/get/list/count
│       └── tests/
│           └── test_storage.py  19 unit tests
│   └── tests/                Activity integration tests
│       └── test_macrodroid_integration.py  30 integration tests
├── docs/
│   ├── activity/
│   │   └── SCHEMA.md        Activity Event Schema documentation
│   └── decision/
│       ├── ARCHITECTURE.md  Decision Engine architecture
│       └── RULES.md         Rule configuration reference
├── mcp_servers/             MCP server adapters (Python)
├── caddy/                   Reverse proxy config
├── cloudflare/              Tunnel config
└── docker-compose.yml       Deployment orchestration
```

---

## Decision Engine (Task A009)

### What changed

- **Placeholder rules removed** — `battery_low_rule`, `screen_awake_rule`, `focus_timeout_rule`.
- **Real config-driven rules added** — `screen_long_use_rule`, `app_long_use_rule`.
- **SessionAnalyzer** — Extracts screen/app sessions from events; rules never scan events directly.
- **RuleManager** — Loads YAML config; rules and DecisionService never touch YAML.
- **CooldownStore** — Abstract interface (`MemoryCooldownStore` now, `RedisCooldownStore` future).
- **Config loader** — `load_rules()` / `reload_rules()` with graceful error handling.
- **Normalizer updated** — `screen_on` → `screen.on`, `screen_off` → `screen.off`; added `app.opened`/`app.closed` payload normalizers.

### Design principles

- **Configuration-driven** — All thresholds, apps, cooldowns from `rules.yaml`. Zero code changes for tuning.
- **Separation of concerns** — YAML = parameters, Python = logic.
- **Claude is the only intelligent layer** — Decision emits Triggers, never text.

### Acceptance criteria met

| Change | Action |
|---|---|
| 40 min → 60 min threshold | Edit `threshold_minutes` in YAML |
| Douyin → Bilibili | Change `package` in YAML |
| Add a new app rule | Add rule block in YAML |
| Disable a rule | Set `enabled: false` |
| Adjust cooldown | Edit `cooldown_minutes` |

All without modifying any Python code.

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
| Docker Compose | `docker-compose.yml` |
| Decision Engine (config-driven) | `decision/` |
| SessionAnalyzer | `decision/analyzers/session.py` |
| RuleManager | `decision/rule_manager.py` |
| CooldownStore | `decision/cooldown.py` |
| Unit tests | `decision/tests/` (8 test files) |

## Not Yet Implemented

| Capability | Target |
|---|---|
| GitHub MCP Server | Future |
| Filesystem MCP Server | Future |
| Docker Production optimization | Task-015 |
| Claude Trigger (Activity) | Future |
| RedisCooldownStore | Future |
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
| Activity Subsystem | 🟡 In Progress — Decision Engine Phase 2 complete |
| Decision Engine | ✅ Implemented — configuration-driven rule system |
| Filesystem MCP | Reserved |
| GitHub MCP | Reserved |

---

## Repository Health

| Check | Status |
|---|---|
| Documentation | ✅ Consistent |
| Architecture | ✅ Stable Core / Extensible Service Layer |
| Architecture Audit | ✅ Pre-deployment check passed (2026-06-18) |
| Tests | ✅ Decision: 8 test files; Activity: 4 test files; MCP Hub: 6 test files |
| GitHub Sync | ✅ Up to date |
| No duplicate docs | ✅ Single source of truth per concern |
| CHANGELOG | ✅ Created |

## Last Commit

| Field | Value |
|---|---|
| **Hash** | (pending — Task A009) |
| **Summary** | feat(decision): Configuration-driven rule system — SessionAnalyzer, Cooldown, RuleManager, real rules |

---

## Notes

When resuming this project:

1. Read README.md
2. Read PROJECT_STATE.md
3. Read ARCHITECTURE.md
4. Continue from **Task-A009** — Decision Engine Phase 2 (completed); next: **Claude Trigger (Phase 3)** or **Task-015** (Docker Production)
