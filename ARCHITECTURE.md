# System Architecture

## Overview

This project is an **MCP Hub** — not an AI application. It routes requests between Claude Desktop and multiple independent MCP services through the Model Context Protocol.

The architecture has two layers:

- **Stable Core** — Gateway, Registry, Router, Lifecycle, Transport, Config. Changes here are rare and deliberate.
- **Extensible MCP Service Layer** — Independent, replaceable services. Adding one requires zero Core changes.

---

## Claude Desktop — Unified Entry Point

Claude Desktop is the **single point of interaction** for the user. It communicates exclusively with the MCP Hub via JSON-RPC 2.0. The user never interacts with backend services directly.

```
User
 │
 ▼
Claude Desktop          ← local machine
 │  JSON-RPC / MCP
 ▼
MCP Hub (Gateway)       ← VPS
 │
 ├── Ombre MCP
 ├── ntfy MCP
 └── ...
```

---

## Stable Core Layer

```
Gateway (main.py)
    │
Config (src/config/)
    │
Registry (src/registry/)
    │
Lifecycle (src/lifecycle/)
    │
Loader (src/loader/)
    │
Router (src/router/ + src/transport/handlers/)
    │
Runtime (src/runtime/)
    │
Transport (src/transport/ — JSON-RPC 2.0)
    │
Models (src/models/)
    │
Utils (src/utils/)
```

| Component | Responsibility |
|---|---|
| **Gateway** | FastAPI application entry point, lifespan management |
| **Registry** | Service registration, discovery, enable/disable, lifecycle |
| **Router** | Thin JSON-RPC method dispatch → handler |
| **Handlers** | Per-method logic (initialize, tools/list, tools/call, health) |
| **Runtime** | Middleware layer (future: auth, metrics, retries) |
| **Lifecycle** | Server initialize → start → stop with rollback guarantees |
| **Transport** | JSON-RPC 2.0 wire protocol (POST /mcp) |
| **Config** | YAML-based configuration with defaults |

**Core Principle:** The Core is stable. Adding a new MCP service must not require Core changes.

---

## MCP Service Layer

Each MCP service is an independent module:

```
mcp_servers/
    ombre/
        manifest.yaml      ← declarative: name, version, class
        server.py          ← implementation: BaseMCPServer subclass
    ntfy/
        manifest.yaml
        server.py
    ...
```

Services are:
- **Loosely coupled** — no direct dependencies between services
- **Independently deployable** — can be updated without affecting others
- **Single responsibility** — one service, one capability
- **Auto-discovered** — scanned at Hub startup via manifest.yaml

---

## Request Flow

```
Claude Desktop
      │  POST /mcp  (JSON-RPC 2.0)
      ▼
Transport Server  (src/transport/server.py)
      │
      ▼
Router            (src/transport/router.py)  ← dispatch by method
      │
      ▼
Handler           (src/transport/handlers/)  ← per-method logic
      │
      ▼
Runtime           (src/runtime/)             ← future middleware
      │
      ▼
ServerManager     (src/core/)                ← resolve → call tool
      │
      ▼
MCP Server        (mcp_servers/)             ← concrete implementation
```

---

## Deployment

- **Claude Desktop** runs locally on the user's machine
- **MCP Hub** is deployed on a VPS
- **MCP Servers** run on the same VPS as the Hub
- Docker Compose is the deployment layer, not the architecture

### Core Services (docker-compose.yml)

| Service | Purpose |
|---|---|
| `mcp-hub` | MCP Hub (orchestration core) |
| `caddy` | Reverse proxy + automatic TLS |
| `cloudflared` | Cloudflare Tunnel (reserved) |

### MCP Services (docker-compose.yml)

| Service | Purpose |
|---|---|
| `github-mcp` | GitHub MCP Server (reserved) |
| `filesystem-mcp` | Filesystem MCP Server (reserved) |

Ombre and ntfy are **external services** integrated via Hub-loaded Python adapters — they do not run as separate Docker containers. See `mcp_servers/ombre/` and `mcp_servers/ntfy/`.

---

## MCP Hub — Expanded Responsibilities

### 1. Service Registration

```
MCP Service ──► register(name, capabilities, endpoint) ──► Registry
```

### 2. Routing

```
Claude Desktop ──► Hub ──► resolve("github") ──► GitHub MCP
```

### 3. Lifecycle Management

| Phase | Action |
|---|---|
| **Startup** | Discover → Register → Initialize → Lifecycle Start → Running |
| **Health** | Hub health-checks every registered server |
| **Shutdown** | Lifecycle Stop → Drain → Unregister |
| **Failure** | Failed servers are isolated; never block healthy ones |

### 4. Auto-Discovery

Manifest-first: `*/manifest.yaml` → fallback to `server.py` scan.
Error isolation: a broken plugin never blocks others.

### 5. Configuration

Per-service configuration in `config.yaml`. Hub metadata (protocol version, name, capabilities) is configurable.

---

## Ombre — External MCP Service

Ombre is an **existing external MCP-compatible long-term memory service** deployed at `http://45.76.169.98:8000/mcp`. This repository does **not** contain Ombre source code. The MCP Hub connects to Ombre through an HTTP adapter layer.

```
Claude Desktop
        │
        ▼
     MCP Hub  (this repository)
        │
        ▼
  Ombre Adapter  (mcp_servers/ombre/server.py — HTTP bridge)
        │
        ▼
External Ombre Deployment  (45.76.169.98:8000 — NOT in this repository)
```

The adapter (`mcp_servers/ombre/`) handles health checks, tool forwarding, and connection state. All Ombre business logic lives in the external deployment.

---

## Design Principles

### MCP First
Every new capability is an MCP service. Nothing is baked into the Core.

### Hub Contains No Business Logic
The MCP Hub is an orchestration layer. It routes, registers, manages lifecycles. It never processes data, makes decisions, or implements features.

### Loose Coupling
Services communicate only through the Hub. No direct inter-service dependencies.

### Plugin Architecture
Adding a new MCP: create `mcp_servers/<name>/manifest.yaml` + `server.py`. Zero Core changes.

### Claude Desktop as Sole Entry Point
The user never interacts with backend services directly.

### Documentation First
Architecture changes are documented before or alongside implementation.

---

## Activity Subsystem

A separate event-driven pipeline that ingests device activity, normalizes
it, and feeds autonomous decision-making:

```
Android (MacroDroid)
        │
        ▼
Activity Gateway         ← Ingest raw events
        │
        ▼
Event Normalizer         ← Map to unified schema
        │
        ▼
Event Database           ← Persist + query
        │
        ▼
Activity Service         ← Unified read interface
        │
        ▼
Decision Script          ← Evaluate rules
        │
        ▼
Claude Trigger           ← Notify Claude
```

| Component | Responsibility |
|---|---|
| **Gateway** | HTTP ingest endpoint. Receives raw events from collectors (MacroDroid, Tasker, …) |
| **Normalizer** | Maps collector-specific formats to the unified Activity Event Schema.  Source-independent mapping table with per-type payload normalizers.  Unknown events are logged and marked, never rejected. |
| **Database** | SQLite persistence. Auto-creates `data/activity.db` on startup. Repository API with save/get/list/count/get_by_type/get_between/get_latest/list_types. JSON payload + raw. WAL mode, no ORM. Indexed on type + timestamp. |
| **Service** | Read-only query layer. All downstream reads go through `ActivityService` — never direct SQLite. Constructor-injected repository for future PostgreSQL swap. |
| **Decision** | Evaluates rules against events. Triggers actions (notify, schedule, escalate) |
| **Claude Trigger** | Bridges Activity decisions to Claude via the MCP Hub |

**Design Principles:**

- **Source Agnostic** — Android, iOS, desktop, IoT all produce the same event shape
- **Normalize Late** — raw collector data is always preserved alongside normalized payloads
- **Schema-Versioned** — breaking changes to the event schema bump a version integer
- **Typed Payload** — each event type maps to a specific, typed payload sub-schema

**Current Status:** 🟡 In Progress — Full ingestion pipeline verified: Schema (A001), Gateway (A002), Normalizer (A003), SQLite (A004), MacroDroid Integration (A005), Event Normalization (A006), Event Query Service (A007).
See `docs/activity/` for API, SCHEMA, NORMALIZER, STORAGE, and MACRODROID documentation.

---

## Future Expansion

New MCP services are added by creating directories under `mcp_servers/`. The architecture evolves through **extension, not reconstruction**.

New subsystems (like Activity) are added as top-level directories with their own
documentation, types, and services — following the same low-coupling principles.

**Candidate services:** Calendar MCP, Email MCP, Database MCP, Home Assistant MCP, Monitoring MCP, Redis MCP.
