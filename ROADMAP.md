# ROADMAP

## Vision

Build an **MCP Gateway (Hub)** that connects Claude Desktop to multiple MCP services through a standardized protocol.

> **MCP First**: Every new capability is an MCP service. The Core never grows business logic.

---

## Phase 1 — Infrastructure

Deployable foundation: Docker Compose, Caddy reverse proxy, Cloudflare Tunnel.

**Status:** Planned

---

## Phase 2 — MCP Hub Gateway

Central orchestration runtime: ServerManager, Discovery, JSON-RPC transport, Router, Runtime layer.

**Status:** ✅ Implemented (Task-003, Task-004)

---

## Phase 3 — Registry & Discovery

Formal MCP registry with per-service manifests. Enable/disable services. Lifecycle management.

**Status:** Design complete (see `docs/REGISTRY.md`)

---

## Phase 4 — Core MCP Services

First concrete MCP server implementations:

| Service | Purpose | Status |
|---|---|---|
| Ombre MCP | Long-term AI memory | Foundation ✓ |
| ntfy MCP | Push notifications | Planned |
| Filesystem MCP | File operations | Planned |
| GitHub MCP | Repository management | Planned |
| Browser MCP | Web interaction | Planned |

---

## Phase 5 — Claude Desktop Integration

Wire Claude Desktop to the MCP Hub via JSON-RPC / MCP protocol. End-to-end tool invocation.

**Status:** Planned (Task-005)

---

## Phase 6 — Production Hardening

Authentication, TLS, health-check loops, metrics, structured logging, CI/CD.

**Status:** Planned

---

## Phase 7 — External MCP Services

Community and third-party MCP services. Remote adapters (HTTP/SSE/WebSocket). Service marketplace design.

**Status:** Future

---

## Long-Term Vision

```
Claude Desktop
        │
        ▼
  MCP Hub (Gateway)
        │
 ┌──────┼──────────────────┐
 │      │      │           │
Ombre  ntfy  Filesystem  GitHub
        │
   Future MCP Services
        │
 Browser · SSH · Calendar · Email · ...
```

The architecture evolves through **extension, not reconstruction**.
Adding a new MCP service requires a manifest + server.py — zero Core changes.
