# ai-infrastructure

Personal AI infrastructure centered on **Claude Desktop + MCP Hub** — self-hosted, modular, MCP-first.

## Design Principles

- **MCP First** — every new capability is added through the Model Context Protocol.
- **Docker Compose** — one-command deployment for the full stack.
- **Caddy** — automatic HTTPS reverse proxy.
- **Cloudflare** — DNS and secure external access.
- **Modular** — swap or extend components without rewiring the system.

## Architecture

```
Internet → Cloudflare → Caddy → Docker Compose → MCP Hub
                                                    ├── GitHub MCP
                                                    ├── Filesystem MCP
                                                    ├── Ombre MCP
                                                    ├── ntfy MCP
                                                    └── Future MCP Services
```

Claude Desktop is the unified AI entry point. The MCP Hub is the system core — Docker is only the deployment layer.

## Quick Start

```bash
git clone https://github.com/Padalackles/ai-infrastructure.git
cd ai-infrastructure
cp .env.example .env   # edit with your domain, tokens, etc.
docker compose up -d
```

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- [Claude Desktop](https://claude.ai/download)
- A domain managed by Cloudflare
- (Optional) NVIDIA GPU + nvidia-container-toolkit

## Documentation

| Document | Purpose |
|---|---|
| [PROJECT_STATE.md](PROJECT_STATE.md) | Current status, phase, and next tasks. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Design decisions and system layout. |
| [ROADMAP.md](ROADMAP.md) | Planned features and milestones. |
| [docs/MCP.md](docs/MCP.md) | MCP server catalog and integration guide. |

## License

MIT
