# Changelog

All notable changes to the MCP Hub project.

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
