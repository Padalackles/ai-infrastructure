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
│   │   ├── api/          REST endpoints
│   │   ├── core/         ServerManager, Discovery, BaseMCPServer, EventBus
│   │   ├── runtime/      Middleware layer (auth, metrics, retries — future)
│   │   ├── transport/    JSON-RPC 2.0 endpoint, Router, Handlers
│   │   └── main.py       FastAPI entry point
│   ├── tests/
│   ├── config.yaml
│   └── Dockerfile
├── mcp_servers/          MCP Service Layer (extensible)
│   ├── ombre/            Ombre MCP Server
│   ├── ntfy/             ntfy MCP Server (Docker only)
│   ├── github/           GitHub MCP Server (Docker only)
│   ├── filesystem/       Filesystem MCP Server (Docker only)
│   └── example/          Example Server (test pipeline)
├── services/             Service implementations
│   └── ombre/            Ombre MCP Server foundation (Task-002)
├── docker-compose.yml
├── ARCHITECTURE.md
├── ROADMAP.md
├── PROJECT_STATE.md
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
