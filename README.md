# MCP Hub

**AI Infrastructure should be invisible.**

Claude interacts with capabilities, never with infrastructure.
Every architectural decision must reduce reasoning overhead while
increasing available capabilities.

---

## Design Principles

### Principle 0 — Capability-Oriented Architecture

The Hub exists to expose **capabilities**, not infrastructure.

Claude should reason about:
- memory, browser, github, notification, filesystem

Claude should **never** reason about:
- plugins, routing, registry, authentication, metrics, logging, service lifecycle

Infrastructure is an implementation detail.

### Principle 1 — Infrastructure Invisibility

Claude sees only business tools. The Hub's internal state (health, metrics,
service lists, uptime) is for operators, never for LLM reasoning.

Default: zero hub.* tools exposed.  
Development: `HUB_EXPOSE_INTERNAL_TOOLS=true` enables hub.debug.* tools.

### Principle 2 — Token Efficiency

Every design decision should reduce context usage.

- Fewer MCP tools
- Concise responses
- No infrastructure metadata
- No redundant explanations

The Hub should maximize capability while minimizing token consumption.

### Principle 3 — Composable MCP Services

- **MCP First** — Every capability is an MCP service. Nothing is baked into the Core.
- **Gateway, not Application** — The Hub routes requests; servers implement behavior.
- **Plugin Architecture** — Adding a new MCP service requires zero Core changes.

### Principle 4 — Internal Observability

Logging, metrics, diagnostics, and error tracking happen internally.
Claude should not spend context window understanding infrastructure.

- Structured JSON logs → `logs/hub.log`
- Audit trail → `logs/audit.log`
- Runtime metrics → internal only (future: Prometheus / Grafana)
- Request IDs propagate internally; surfaced only on errors

---

## Architecture

```
Claude Web / Desktop
     │  HTTPS + MCP Streamable HTTP
     ▼
MCP Hub (Gateway)     ← VPS: raven-victor.click
     │
     ├── Ombre MCP         (long-term memory — auto-discovered)
     ├── ntfy MCP          (push notifications — auto-discovered)
     ├── Hub Diagnostics   (hidden unless HUB_EXPOSE_INTERNAL_TOOLS=true)
     └── Future MCPs       (drop-in, zero Core changes)
```

---

## Repository Structure

```
├── mcp-hub/              MCP Hub (Stable Core)
│   ├── src/
│   │   ├── core/         RemoteMCPClient, HubState, Metrics, Logging
│   │   ├── config/       Configuration loader
│   │   ├── lifecycle/    BaseMCPServer, lifecycle contracts
│   │   ├── registry/     ServerManager, service registry
│   │   ├── loader/       Discovery, Loader, plugin loading
│   │   ├── runtime/      Middleware layer
│   │   ├── transport/    FastMCP Streamable HTTP bridge
│   │   ├── api/          REST endpoints (/health, /status, /tools)
│   │   └── models/       Shared dataclasses
│   ├── tests/
│   ├── config.yaml
│   └── Dockerfile
├── mcp_servers/          MCP Service Layer (extensible)
│   ├── ombre/            Ombre MCP client (RemoteMCPClient subclass)
│   ├── ntfy/             Notification MCP (curl → ntfy.sh)
│   ├── hub/              Hidden diagnostics (hub.debug.*)
│   ├── example/          Example Server — Hub pipeline test
│   ├── filesystem/       Reserved
│   └── github/           Reserved
├── docker-compose.yml
├── docs/
├── ARCHITECTURE.md
├── ROADMAP.md
├── PROJECT_STATE.md
└── DECISIONS.md
```

---

## Quick Start

```bash
cd mcp-hub
pip install -r requirements.txt
PYTHONPATH="src:.." uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

```
GET  /health  →  {"status":"healthy","total_servers":1,...}
POST /mcp     →  JSON-RPC 2.0  (Streamable HTTP)
```

---

## Current Status

See [`PROJECT_STATE.md`](PROJECT_STATE.md).

---

## License

MIT
