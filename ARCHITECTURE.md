# ai-infrastructure — Architecture

## High-Level Design

```
Internet → Cloudflare Tunnel → Caddy → MCP Hub (Docker)
                                          ├── GitHub MCP
                                          ├── Filesystem MCP
                                          ├── Ombre MCP
                                          └── ntfy MCP
```

## Layers

### 1. External Access — Cloudflare

- Cloudflare Tunnel (`cloudflared`) provides secure inbound connectivity without opening firewall ports.
- DNS is managed through Cloudflare for the project domain.

### 2. Reverse Proxy — Caddy

- Terminates TLS with automatic Let's Encrypt certificates.
- Routes traffic to the MCP Hub (and optionally to individual MCP servers).

### 3. Orchestration — Docker Compose

- Every component runs in a container on the `ai-net` bridge network.
- Environment variables flow from `.env` → `docker-compose.yml` → service configs.

### 4. Core — MCP Hub

- Central registry and router for all MCP servers.
- Authenticates and dispatches MCP requests from Claude Desktop.
- Agnostic to which MCP servers are registered — new servers plug in via config.

### 5. MCP Servers

Each MCP server is an independent container that exposes a standard MCP interface:

| Server       | Purpose                                |
|--------------|----------------------------------------|
| GitHub MCP   | Repo management, issues, PRs via LLM   |
| Filesystem MCP | Read/write local files via LLM       |
| Ombre MCP    | Ombre platform integration             |
| ntfy MCP     | Push notifications via ntfy            |

## Design Decisions

- **MCP Hub is the single entry point** — Claude Desktop connects only to the Hub, not to individual MCP servers directly.
- **Docker is deployment, not architecture** — the system is designed around MCP protocol boundaries, not container boundaries.
- **Config-driven server registration** — adding a new MCP server means adding a config entry + a container; no Hub code changes.
