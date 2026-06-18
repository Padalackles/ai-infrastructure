# Changelog

All notable changes to the MCP Hub project.

---

## [v0.1.0] — 2026-06-18 (Production Deployed)

### Task-016 — MCP Auth (Bearer Token) ✅

- `src/core/auth.py`: FastAPI dependency that validates `Authorization: Bearer <token>`
- Token configured via `MCP_HUB_AUTH_TOKEN` env var; empty = auth disabled
- POST /mcp requires valid token when configured; REST endpoints always public
- Wrong/missing token → HTTP 401 + JSON-RPC error body (code -32003)
- Per-request token resolution — no import-time caching, test-safe
- `tests/test_auth.py`: 9 tests covering all scenarios
- Total: 166 tests passing

### Task-013 — Claude Desktop End-to-End Integration ✅

- 12/12 end-to-end tests passed over HTTPS + Bearer Token
- Verified: initialize, tools/list, tools/call (global + server-scoped)
- Ombre: health (CONNECTED), status — external deployment reachable
- ntfy: health (ok), info, send (200) — real push notification sent
- example: ping (pong) — Hub pipeline fully functional
- Claude Desktop config guide: `docs/CLAUDE_DESKTOP_SETUP.md`
- E2E report: `docs/task013/E2E_REPORT.md`
- Zero Core changes — Hub architecture stable throughout

### Task-012 — Domain + HTTPS + Cloudflare ✅

**Domain:** `raven-victor.click`  
**VPS:** `45.76.169.98`  
**Status:** Deployed and verified

**Endpoints (all HTTPS):**
- `GET /health` → `{"status":"healthy","total_servers":3,...}`
- `GET /status` → `{"version":"0.1.0","runtime":"mcp-hub",...}`
- `POST /mcp` → JSON-RPC 2.0 (initialize, tools/list, tools/call)

**Infrastructure:**
- Caddy: Let's Encrypt certificate (acme-v02.api.letsencrypt.org)
- Cloudflare: DNS A record (45.76.169.98), SSL Full (strict)
- Docker: ai-caddy + ai-mcp-hub (2 containers, 3 Python adapters)

**Fixes during deployment:**
- Removed broken ombre-mcp/ntfy-mcp Docker stubs (external services, loaded by Hub discovery)
- Fixed discovery.py auto-detect for Docker flat layout (3 vs 4 directory levels)
- Added CADDY_ACME_EMAIL + DOMAIN environment variables to Caddy container
- 157/157 tests passing

---

## [v0.1.0] — 2026-06-18

### Architecture Consistency Audit (Pre-Deployment)

**Docker Compose:**
- Fixed stale `# TODO: implement` comments on ombre-mcp and ntfy-mcp (both implemented: Task-009, Task-010)
- Fixed env var names: `OMBRE_API_URL` → `OMBRE_ENDPOINT` (matches manifest.yaml and adapter)
- Commented out filesystem-mcp and github-mcp — reserved, no source code yet
- Updated caddy and cloudflared comments to reflect current state

**Documentation:**
- `docs/MCP.md`: Updated Ombre status (Planned → ✅ Integrated, Task-009), ntfy (Planned → ✅ Integrated, Task-010), Filesystem/GitHub (Reserved)
- `caddy/README.md`: Fixed misleading `/$DOMAIN/mcp` → correctly describes `/mcp`, `/health`, `/status`, `/tools` proxy paths
- `docs/task012/CLOUDFLARE_SETUP.md`: Added HTTPS-Only Enforcement section (Always Use HTTPS, HSTS, Automatic HTTPS Rewrites)

**Code:**
- `base_server.py`: Fixed subclass docstring — OmbreServer/NtfyServer no longer marked "future", now "implemented"

**Governance:**
- `docs/SPECIFICATION.md`: Added §9 Definition of Completed (5 gates) + §10 Review Gate (7-step pipeline)
- `CLAUDE.md`: Added Completed definition + Task Transition Pipeline

### Task-012 — Domain + HTTPS + Cloudflare

**Status:** Implemented — pending real domain binding

**Deliverables:**
- `caddy/Caddyfile`: Auto HTTPS reverse proxy (`/mcp`, `/health`, `/status`, `/tools` → `mcp-hub:8080`)
- `caddy/README.md`: Configuration guide with DOMAIN and CADDY_ACME_EMAIL vars
- `docs/task012/DOMAIN_SETUP.md`: DNS A record setup (Cloudflare + direct)
- `docs/task012/CLOUDFLARE_SETUP.md`: SSL/TLS, proxy, Cloudflare Tunnel, HTTPS-Only
- `docs/task012/HTTPS_VALIDATION.md`: 5-step HTTPS validation checklist
- `docs/task012/TASK012_REPORT.md`: Architecture overview and deployment steps
- `scripts/verify_https.sh`: Automated HTTPS + MCP endpoint verification
- `cloudflare/tunnel-config.yaml`: Tunnel ingress rules template
- `.env.example`: Updated with DOMAIN, CADDY_ACME_EMAIL, Cloudflare vars

**Pending for Task-013:**
- Purchase/configure real domain
- Point DNS A record to VPS IP
- Set up Cloudflare with Full SSL/TLS
- Deploy `docker compose up -d` on VPS
- Verify with `scripts/verify_https.sh`
- Wire Claude Desktop to `https://<domain>/mcp`
