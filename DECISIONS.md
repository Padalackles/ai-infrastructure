# Architecture Decision Records

Stable architectural decisions. Each decision is immutable once accepted.
New decisions are added at the bottom.

---

## Decision-001: Claude Desktop is the Only User Interface

**Status:** Accepted

**Context:** The system needs a user-facing AI interface. Multiple options exist: web UI, API, CLI, IDE plugin.

**Decision:** Claude Desktop is the sole user entry point. All user interaction flows through Claude Desktop. No alternative UI will be built.

**Consequences:**
- The Hub only needs to speak MCP (JSON-RPC 2.0)
- No web dashboard, REST API for users, or CLI tool is needed
- Claude Desktop configuration is the only client-side setup required

---

## Decision-002: MCP Hub is the System Core

**Status:** Accepted

**Context:** The architecture needs a central integration point between Claude Desktop and backend services.

**Decision:** The MCP Hub is the central orchestration layer. It handles registration, routing, lifecycle management, and configuration. It never contains business logic.

**Consequences:**
- All service-to-service communication passes through the Hub
- The Hub is a single point of control (and a single point of failure — mitigated by health checks)
- Adding a new service only requires Hub registration, never Hub modification

---

## Decision-003: Docker is Only the Deployment Layer

**Status:** Accepted

**Context:** The project needs a deployment strategy.

**Decision:** Docker Compose is used exclusively for deployment. The architecture is defined in Python code, not in Docker configuration. Docker does not influence architectural decisions.

**Consequences:**
- Services can run without Docker during development (`uvicorn src.main:app --reload`)
- The architecture is portable across deployment mechanisms
- Dockerfiles exist per service but are secondary to the source code

---

## Decision-004: MCP First

**Status:** Accepted

**Context:** New capabilities need an integration pattern.

**Decision:** Every new capability is implemented as an MCP service whenever possible. Functionality is never tightly coupled into the Hub Core.

**Consequences:**
- The Core remains small and stable
- Services are independently testable and replaceable
- The system scales horizontally by adding MCP services
- Non-MCP integrations (direct API calls, shared libraries) are avoided

---

## Decision-005: Stable Core Should Rarely Change

**Status:** Accepted

**Context:** The Hub Core (Gateway, Registry, Router, Lifecycle, Transport, Config) is the foundation all services depend on.

**Decision:** Changes to the Core Layer require explicit justification. The default answer to "should this go in Core?" is "no — make it an MCP service."

**Consequences:**
- Core changes are deliberate and well-documented
- Services can rely on stable Core interfaces
- Backward compatibility is prioritized in Core

---

## Decision-006: Service Layer Must Remain Independently Extensible

**Status:** Accepted

**Context:** The system should support an open-ended number of MCP services.

**Decision:** Adding a new MCP service requires only a new directory under `mcp_servers/` with a `manifest.yaml` and `server.py`. Zero Core changes are required. Services have no direct dependencies on each other.

**Consequences:**
- Plugin architecture: drop in a directory, auto-discovered at startup
- Services can be developed, tested, and deployed independently
- The service ecosystem can grow without Core team involvement

---

## Decision-007: Services Communicate Through the Hub

**Status:** Accepted

**Context:** MCP services may need to coordinate (e.g., Ombre stores a memory → ntfy pushes a notification).

**Decision:** All inter-service communication goes through the Hub's EventBus or Router. Services never call each other directly.

**Consequences:**
- Loose coupling: services don't know about each other
- The Hub can enforce policies (rate limiting, auth) on inter-service messages
- EventBus is the single integration surface for service coordination
- Direct service-to-service imports are forbidden
