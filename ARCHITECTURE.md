# System Architecture

## Overview

This project is an **MCP Gateway (Hub)** — not an AI application. It routes requests between Claude Desktop and multiple independent MCP services through the Model Context Protocol.

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
| `mcp-hub` | MCP Gateway (the Hub itself) |
| `caddy` | Reverse proxy + automatic TLS |
| `cloudflared` | Cloudflare Tunnel |

### MCP Services (docker-compose.yml)

| Service | Purpose |
|---|---|
| `ombre-mcp` | Ombre MCP Server |
| `ntfy-mcp` | ntfy MCP Server |
| `github-mcp` | GitHub MCP Server |
| `filesystem-mcp` | Filesystem MCP Server |

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

Ombre is an **existing external MCP-compatible long-term memory service** that has already been deployed and validated independently. This repository does not reimplement Ombre. Instead, the MCP Hub integrates Ombre as one of its external MCP services through the standard manifest + server.py plugin mechanism.

The relationship:

```
MCP Hub (this repository)
    │
    ├── Ombre MCP   ← external, already deployed
    ├── ntfy MCP    ← future
    └── ...
```

Ombre's `services/ombre/` foundation (Task-002) provides the Hub-facing adapter. The actual Ombre service runs separately and communicates through the Hub.

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

## Future Expansion

New MCP services are added by creating directories under `mcp_servers/`. The architecture evolves through **extension, not reconstruction**.

**Candidate services:** Calendar MCP, Email MCP, Database MCP, Home Assistant MCP, Monitoring MCP, Redis MCP.
