# ai-infrastructure — Roadmap

## Phase 0 — Bootstrap (current)
- [x] Repository scaffolding
- [x] README, PROJECT_STATE
- [ ] Architecture document
- [ ] Repository structure
- [ ] docs/MCP.md

## Phase 1 — Core Infrastructure
- [ ] Implement MCP Hub (registry + router)
- [ ] Caddy reverse proxy with auto-TLS
- [ ] Cloudflare Tunnel integration
- [ ] `.env.example` with all required variables
- [ ] `docker compose up` works end-to-end

## Phase 2 — MCP Servers
- [ ] GitHub MCP server (issues, PRs, repos)
- [ ] Filesystem MCP server (read/write sandboxed)
- [ ] Ombre MCP server
- [ ] ntfy MCP server (push notifications)

## Phase 3 — Polish
- [ ] Claude Desktop connection guide
- [ ] Health checks and monitoring
- [ ] Backup / restore scripts
- [ ] CI/CD for container builds

## Phase 4 — Expansion
- [ ] Additional MCP servers (TBD)
- [ ] Multi-user support
- [ ] Observability (logs, metrics, traces)
