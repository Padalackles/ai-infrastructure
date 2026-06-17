# System Architecture

## Overview

This project is a personal AI infrastructure built around **Claude Desktop** as the unified AI entry point and the **Model Context Protocol (MCP)** as the standard integration protocol.

The architecture is divided into two primary layers:

- **Core Layer** — Claude Desktop, MCP Hub, and the infrastructure that connects them.
- **MCP Service Layer** — Independent, replaceable services that provide capabilities through MCP.

---

## Claude Desktop — Unified Entry Point

Claude Desktop is the **single point of interaction** for the user. All AI capabilities, whether local or remote, are accessed through Claude Desktop. It does not connect directly to individual services; instead it communicates exclusively with the **MCP Hub**, which routes requests to the appropriate backend service.

```
                         User
                          │
                    ┌─────▼─────┐
                    │  Claude    │
                    │  Desktop   │  ◄── Unified AI entry point
                    └─────┬─────┘
                          │  MCP Protocol
                          │
```

This design means:

- The user never needs to know which backend service handles a request.
- New MCP services become available in Claude Desktop automatically once registered with the Hub.
- Claude Desktop's configuration only needs to point to the MCP Hub — not to every individual service.

---

## High-Level Architecture

```
                    ┌──────────────────────┐
                    │       Internet        │
                    └──────────┬───────────┘
                               │
                          Cloudflare
                               │
                            HTTPS
                               │
                             Caddy
                               │
                       Docker Compose
                               │
          ┌────────────────────┼────────────────────┐
          │              CORE LAYER                 │
          │                                         │
          │  ┌──────────┐      ┌───────────────┐   │
          │  │  Claude  │ MCP  │               │   │
          │  │ Desktop  ├─────►│   MCP Hub     │   │
          │  │          │      │               │   │
          │  └──────────┘      └───────┬───────┘   │
          │                            │           │
          └────────────────────────────┼───────────┘
                                       │
          ┌────────────────────────────┼───────────┐
          │                MCP SERVICE LAYER       │
          │                            │           │
          │     ┌──────────────────────┼───────┐   │
          │     │                      │       │   │
          │  ┌──▼──┐  ┌──────┐  ┌─────▼──┐ ┌──▼──┐│
          │  │Files│  │GitHub│  │ Ombre  │ │ntfy ││
          │  │system│  │ MCP  │  │  MCP   │ │ MCP ││
          │  └─────┘  └──────┘  └────────┘ └─────┘│
          │                                       │
          │  ┌──────┐  ┌──────┐                   │
          │  │Browser│  │ SSH  │  ... future      │
          │  │ MCP  │  │ MCP  │                   │
          │  └──────┘  └──────┘                   │
          │                                       │
          └───────────────────────────────────────┘
```

---

## Deployment

- **Claude Desktop** runs **locally** on the user's machine.
- **MCP Hub** is deployed on a **VPS**.
- All **MCP Servers** (Ombre, ntfy, GitHub, Filesystem, etc.) run on the **same VPS** as the Hub.
- Claude Desktop communicates **only** with the MCP Hub — never directly with individual MCP servers.
- The Hub routes every request to the appropriate MCP Server and returns the response.

```
┌── Local Machine ──┐         ┌── VPS ────────────────────────────┐
│                    │         │                                    │
│  Claude Desktop    │  MCP    │  MCP Hub                          │
│                    ├────────►│  (Gateway)                        │
│                    │         │    │                               │
│                    │         │    ├── Ombre MCP                   │
│                    │         │    ├── ntfy MCP                   │
│                    │         │    ├── GitHub MCP                 │
│                    │         │    ├── Filesystem MCP             │
│                    │         │    └── ... (future)               │
│                    │         │                                    │
└────────────────────┘         └────────────────────────────────────┘
```

---

## Layer Description

### Core Layer

The Core Layer is the **stable foundation** of the system. It contains the components that every MCP service depends on. Changes to the Core Layer should be rare and deliberate.

| Component | Responsibility |
|---|---|
| **Claude Desktop** | Unified AI entry point — all user interaction flows through it. |
| **MCP Hub** | Central integration layer — service registration, routing, lifecycle management, configuration. |
| **Docker Compose** | Deployment orchestration for all services. |
| **Caddy** | Reverse proxy and automatic TLS termination. |
| **Cloudflare** | External access, DDoS protection, DNS. |

### MCP Service Layer

The MCP Service Layer contains **independently replaceable** services. Each service provides one capability and communicates through the MCP Hub using the Model Context Protocol.

Services in this layer:

- Are **loosely coupled** — no direct dependencies between services.
- Are **independently deployable** — each can be updated or replaced without affecting others.
- Follow **single responsibility** — one service, one capability.
- Register with the MCP Hub at startup and deregister at shutdown.

---

## MCP Hub — Expanded Responsibilities

The MCP Hub is the **central nervous system** of the architecture. Its responsibilities go beyond simple proxying:

### 1. Service Registration

When an MCP service starts, it registers with the Hub:

```
MCP Service ──► register(name, capabilities, endpoint) ──► MCP Hub
```

The Hub maintains a live registry of available services, their capabilities, and their health status.

### 2. Routing

Claude Desktop sends every MCP request to the Hub. The Hub inspects the request, resolves the target service, and forwards it:

```
Claude Desktop ──► MCP Hub ──► resolve("github") ──► GitHub MCP
```

Routing is **transparent to Claude Desktop** — it never knows which service instance handles a request.

### 3. Lifecycle Management

The Hub manages the full lifecycle of every registered service:

| Phase | Action |
|---|---|
| **Startup** | Service registers → Hub validates → Hub adds to active registry. |
| **Health** | Hub periodically health-checks every registered service. |
| **Shutdown** | Service deregisters → Hub removes from registry → in-flight requests drain. |
| **Failure** | Unhealthy services are marked offline; requests are rejected with a clear error. |

### 4. Configuration

The Hub stores per-service configuration, making it the single source of truth for:

- Service endpoints and ports.
- Authentication credentials (referenced, not stored in plaintext).
- Capability declarations (which methods each service exposes).
- Rate limits and quotas.

---

## Communication Flow

### Standard Request Path

```
User
 │
 │  "What's in my GitHub repo?"
 │
 ▼
Claude Desktop
 │
 │  MCP request: { service: "github", method: "list_repos" }
 │
 ▼
MCP Hub
 │
 │  1. Authenticate request
 │  2. Resolve "github" → GitHub MCP
 │  3. Forward request
 │
 ▼
GitHub MCP
 │
 │  Call GitHub API
 │
 ▼
GitHub Repository
 │
 │  Response flows back through the same chain
 │
 ▼
Claude Desktop → User
```

### Service Registration Flow

```
MCP Service starts
 │
 ▼
Register with MCP Hub  ──►  Hub validates
 │                              │
 │                              ▼
 │                           Add to active registry
 │                              │
 │                              ▼
 │                           Health-check loop begins
 │
 ▼
Service ready to handle requests
```

---

## Planned MCP Services

| Service      | Purpose                  | Layer  | Status   |
|--------------|--------------------------|--------|----------|
| Filesystem   | Local file operations    | MCP    | Planned  |
| GitHub       | Repository management    | MCP    | Planned  |
| Browser      | Web interaction          | MCP    | Planned  |
| ntfy         | Push notifications       | MCP    | Planned  |
| Ombre        | Long-term AI memory      | MCP    | Planned  |
| SSH          | Remote server access     | MCP    | Planned  |

---

## Design Principles

### MCP First

Every new capability should be implemented as an MCP service. Avoid tightly coupling functionality into the Core Layer.

---

### Loose Coupling

Services must not directly depend on each other. All inter-service communication goes through the MCP Hub.

---

### Single Responsibility

Each MCP service provides exactly one capability. If a service starts handling two unrelated domains, split it.

---

### Replaceability

Any MCP service can be replaced with an alternative implementation without modifying the Core Layer, the Hub, or any other service.

---

### Claude Desktop as Sole Entry Point

The user never interacts with backend services directly. Claude Desktop is the only interface — this simplifies the architecture and provides a consistent experience.

---

### Hub Contains No Business Logic

The MCP Hub is an **orchestration layer**.

It should **never** contain business logic.

All domain logic belongs to individual MCP servers. The Hub routes, registers, manages lifecycles, and stores configuration — it does not process data, make decisions, or implement features. If a capability involves domain knowledge, it belongs in an MCP service, not in the Hub.

---

### Documentation First

Architecture changes must be documented before or alongside implementation. The architecture document is part of the source code.

---

## Future Expansion

New capabilities are added by introducing new MCP services — never by modifying the Core Layer.

**Candidate future services:**

- Calendar MCP
- Email MCP
- Database MCP
- Home Assistant MCP
- Monitoring MCP
- Kubernetes MCP
- Redis MCP

The architecture evolves through **extension, not reconstruction**.
