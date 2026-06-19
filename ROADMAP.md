# ROADMAP

## Vision

Build an **MCP Hub** that connects Claude Desktop to multiple MCP services through a standardized protocol.

> **MCP First**: Every new capability is an MCP service. The Core never grows business logic.

---

## Phase 1 — Infrastructure

Deployable foundation: Docker Compose, Caddy reverse proxy, Cloudflare Tunnel.

**Status:** ✅ Deployed — Docker Compose + Caddy active; Cloudflare Tunnel reserved

---

## Phase 2 — MCP Hub Gateway

Central orchestration runtime: ServerManager, Discovery, JSON-RPC transport, Router, Runtime layer.

**Status:** ✅ Implemented (Task-003 through Task-009)

---

## Phase 3 — Registry & Discovery

Formal MCP registry with per-service manifests. Enable/disable services. Lifecycle management.

**Status:** ✅ Implemented — ServerManager + manifest discovery (see `docs/REGISTRY.md`)

---

## Phase 4 — Core MCP Services

MCP server integrations through Hub adapters:

| Service | Purpose | Status |
|---|---|---|
| Ombre MCP | External deployment — Hub adapter complete | ✅ Integrated |
| ntfy MCP | Push notifications — ntfy.sh API via adapter | ✅ Completed (Task-010) |
| Filesystem MCP | File operations | Planned |
| GitHub MCP | Repository management | Planned |
| Browser MCP | Web interaction | Planned |

---

## Phase 5 — Claude Desktop Integration

Wire Claude Desktop to the MCP Hub via JSON-RPC / MCP protocol. End-to-end tool invocation.

**Status:** ✅ Completed (Task-011 Transport + Task-013 E2E Integration)
- HTTPS endpoint: `https://raven-victor.click/mcp`
- Bearer Token authentication
- 12/12 end-to-end tests passed
- 8 tools across 3 servers (example, ntfy, ombre)
- Claude Desktop config guide: `docs/CLAUDE_DESKTOP_SETUP.md`

---

## Phase 6 — Production Hardening

Authentication, TLS, health-check loops, metrics, structured logging, CI/CD.

**Status:** 🟡 In Progress

---

## Phase 7 — Background Automation

Autonomous background jobs running on schedule. Foundation for AI-driven daily workflows.

| Component | Purpose | Status |
|---|---|---|
| Scheduler Service | Cron-based job engine (TypeScript) | ✅ Implemented (Task-016) |
| Daily Journal | Daily heartbeat → Ombre | Planned (Task-017) |
| Weekly Summary | Weekly reflection → Ombre | Planned |
| GitHub Observer | Repository monitoring | Planned |
| Reminder | Notification scheduling | Planned |

---

## Phase 8 — Activity Subsystem

Event-driven device activity pipeline. Ingests raw events from Android (MacroDroid),
normalizes them, stores them, and triggers autonomous Claude awareness.

```
Android (MacroDroid) → Activity Gateway → Event Normalizer → Event Database → Decision Script → Claude Trigger
```

| Component | Purpose | Status |
|---|---|---|
| Event Schema | Unified event contract | 🟡 Defined (Task A001) |
| Activity Gateway | HTTP ingest endpoint | Planned (Task A002) |
| Event Normalizer | Map collector → unified schema | Planned |
| Event Database | Persist + query events | Planned |
| Decision Script | Rule evaluation engine | Planned |
| Claude Trigger | Bridge Activity → Claude via MCP Hub | Planned |

---

## Phase 9 — External MCP Services

Community and third-party MCP services. Remote adapters (HTTP/SSE/WebSocket). Service marketplace design.

**Status:** Future

---

## Long-Term Vision

```
                         ┌──────────────────────┐
                         │   Android Device      │
                         │   (MacroDroid)        │
                         └──────┬───────────────┘
                                │  HTTP webhook
                                ▼
Claude Desktop          Activity Gateway
        │                     │
        ▼                     ▼
  MCP Hub (Gateway)     Event Normalizer
        │                     │
 ┌──────┼──────────┐          ▼
 │      │          │     Event Database
Ombre  ntfy  Scheduler         │
        │          │           ▼
   Future MCP   Daily Jobs  Decision Script
   Services     (background)     │
        │                       ▼
 Browser · SSH          Claude Trigger ──→ MCP Hub ──→ Claude Desktop
 Calendar · Email              (autonomous awareness)
```

The architecture evolves through **extension, not reconstruction**.
Adding a new MCP service requires a manifest + server.py — zero Core changes.
Adding a new Activity event type requires only a payload sub-schema — zero pipeline changes.
