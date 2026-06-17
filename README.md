# ai-infrastructure

Self-hosted AI Infrastructure based on Docker Compose, Cloudflare, Caddy and MCP.

## Overview

A modular, self-hosted stack for running AI workloads on your own hardware. It bundles LLM serving, agent orchestration, and secure remote access into a single `docker compose up` experience — so you own your data, your models, and your inference costs.

## Key Components

- **Docker Compose** — one‐command deployment for the full stack.
- **Caddy** — automatic HTTPS reverse proxy with Let's Encrypt.
- **Cloudflare** — DNS, tunnel, and DDoS protection for exposing services safely.
- **MCP (Model Context Protocol)** — standardized interface between LLMs and external tools/data sources.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Padalackles/ai-infrastructure.git
cd ai-infrastructure

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your domain, API keys, etc.

# Start all services
docker compose up -d
```

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- A domain name managed by Cloudflare (for TLS and tunnels)
- (Optional) NVIDIA GPU + nvidia-container-toolkit for local GPU inference

## Documentation

- [PROJECT_STATE.md](PROJECT_STATE.md) — current status and what's working.
- [ARCHITECTURE.md](ARCHITECTURE.md) — design decisions and system layout.
- [ROADMAP.md](ROADMAP.md) — planned features and milestones.

## License

MIT
