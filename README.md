# MCP Gateway

An **MCP Gateway (Hub)** deployed on a VPS — not an AI application, not a chatbot.

The Hub connects **Claude Desktop** (the user's AI interface) to multiple **MCP services** through the Model Context Protocol.

```
Claude Desktop        ← runs locally
     │
     │  JSON-RPC / MCP
     ▼
MCP Hub (Gateway)     ← runs on VPS
     │
     ├── Ombre MCP         (long-term memory)
     ├── ntfy MCP          (push notifications)
     ├── Filesystem MCP    (file operations)
     ├── GitHub MCP        (repository management)
     ├── Browser MCP       (web interaction)
     └── Future MCPs
```

> **Ombre Status:** Ombre is an existing external MCP-compatible long-term memory service, deployed at `http://45.76.169.98:8000`. This repository builds the MCP Hub — it does **not** reimplement Ombre. The Hub connects to Ombre through an HTTP adapter (`mcp_servers/ombre/server.py`).

---

## Design Principles

- **MCP First** — Every capability is an MCP service. Nothing is baked into the Core.
- **Gateway, not Application** — The Hub routes requests; servers implement behavior.
- **Plugin Architecture** — Adding a new MCP service requires zero Core changes.
- **Docker is Deployment Only** — The architecture is defined in code, not in containers.

---

## Repository Structure

```
├── mcp-hub/              MCP Hub Gateway (Core)
│   ├── src/
│   │   ├── config/       Configuration loader
│   │   ├── lifecycle/    BaseMCPServer, lifecycle contracts
│   │   ├── registry/     ServerManager, service registry
│   │   ├── loader/       Discovery, Loader, plugin loading
│   │   ├── router/       Router, route interfaces
│   │   ├── runtime/      Middleware layer
│   │   ├── transport/    JSON-RPC 2.0 endpoint + handlers
│   │   ├── api/          REST endpoints (/health, /status, /tools)
│   │   ├── models/       Shared dataclasses
│   │   ├── core/         EventBus
│   │   └── utils/        Helpers
│   ├── tests/
│   ├── config.yaml
│   └── Dockerfile
├── mcp_servers/          MCP Service Layer (extensible)
│   ├── ombre/            Ombre MCP (external — Docker build context)
│   ├── ntfy/             ntfy MCP (Docker build context)
│   ├── github/           GitHub MCP (Docker build context)
│   ├── filesystem/       Filesystem MCP (Docker build context)
│   └── example/          Example Server (Hub pipeline test)
├── docker-compose.yml
├── ARCHITECTURE.md
├── ROADMAP.md
├── PROJECT_STATE.md
├── DECISIONS.md
├── docs/
└── tasks/
```

---

## Quick Start

```bash
cd mcp-hub
pip install -r requirements.txt
uvicorn src.main:app --reload
```

```
GET  /health  →  {"status":"healthy","total_servers":1,...}
GET  /status  →  {"version":"0.1.0","runtime":"mcp-hub",...}
POST /mcp     →  JSON-RPC 2.0  (initialize, tools/list, tools/call, health)
```

---

## Current Status

See [`PROJECT_STATE.md`](PROJECT_STATE.md).

---

## License

MIT
