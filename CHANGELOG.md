# Changelog

All notable changes to the MCP Hub project.

---

## [v0.5.0] — 2026-06-19 (Event Normalizer Implemented)

### Event Normalizer (Task A003)

Second executable component of the Activity subsystem.  Transforms
collector-specific events into the unified canonical format consumed
by all downstream components.

- **`activity/normalizer/`**: Python normalization package
  - `mappings.py`: Extensible event-name mapping table — collector-specific
    names (snake_case) → canonical names (dot-notation).  30+ mappings covering
    MacroDroid, Tasker, and Home Assistant aliases.
  - `service.py`: Pure normalization functions — `normalize_event()` entry point,
    per-type payload normalizers (device.awake, device.sleep, battery.low,
    battery.charging.started, battery.charging.stopped), type coercion with safe
    defaults.
  - `__init__.py`: Package docstring and public API (`normalize_event`)
- **`activity/normalizer/tests/test_normalizer.py`**: 20 unit tests covering:
  - Canonical type mapping (screen_on, screen_off, battery_low, charging_started)
  - Payload normalization with field coercion
  - Unknown event handling (marked as `"unknown"`, logged, raw preserved)
  - Raw preservation (known and unknown events)
  - Alternative collector aliases (display_on, power_connected)
  - Original event immutability
- **`activity/gateway/router.py`**: Integrated Normalizer into pipeline —
  Gateway build → Normalizer normalize → Console log → Response

### Design Highlights

- **Source-independent**: MacroDroid, Tasker, Apple Shortcuts, Home Assistant
  all produce the same canonical output shape.
- **Mapping table**: Extensible dict — new collectors add entries, not code.
- **Unknown events**: Never crash. Marked `"unknown"`, preserved in `raw`, logged.
- **Payload normalizers**: Per-type coercion with safe defaults — missing/wrong
  types never raise.
- **Zero downstream impact**: Existing Gateway, tests, and MCP Hub unaffected.

### Documentation

- `docs/activity/NORMALIZER.md`: Normalization flow, mapping strategy, canonical
  naming, unknown event handling
- `ARCHITECTURE.md`: Updated Activity Subsystem component descriptions
- `ROADMAP.md`: Event Normalizer marked ✅ Implemented
- `PROJECT_STATE.md`: Task A003 marked complete, v0.5.0
- `CHANGELOG.md`: This entry

### Tag

`v0.5.0` — Activity pipeline normalizing events, growing toward persistence

---

## [v0.4.0] — 2026-06-19 (Activity Gateway Implemented)

### Activity Gateway (Task A002)

First executable component of the Activity subsystem.  External devices (Android →
MacroDroid) can now submit events into the system.

- **`activity/gateway/`**: Python FastAPI module
  - `models.py`: Pydantic models — `ActivityEventRequest` (5 required + 4 optional fields), `ActivityEventResponse`
  - `service.py`: Pure functions — ULID-inspired `generate_event_id()`, `utc_now_iso()`, `build_event()`
  - `router.py`: `POST /activity/events` — validates request, auto-populates server fields, logs, returns acceptance
- **`mcp-hub/src/main.py`**: Integrated `activity_router` into FastAPI app
- Source-agnostic: MacroDroid, Tasker, Shortcuts, Home Assistant all use the same endpoint
- Server-side field auto-population: version→1, id→`evt_<ULID>`, timestamp→ISO 8601 UTC
- Temporary human-readable console logging for development visibility

### Activity Event Schema (Task A001)

First architectural milestone for the Activity subsystem — a new event-driven
pipeline for ingesting device activity and triggering autonomous Claude awareness.

- **`docs/activity/SCHEMA.md`**: Comprehensive event schema documentation
  - Unified event contract: version, id, timestamp, source, collector, device, type, payload, raw
  - Hierarchical dot-notation naming convention (`device.awake`, `battery.low`, …)
  - 12 reserved event domains, 25+ typed event types defined
  - Payload sub-schemas for every event type
  - Design principles: source agnostic, normalize late, schema-versioned, typed payload
- **`activity/types.ts`**: TypeScript type contract with discriminated union types

### Documentation Updates

- `ARCHITECTURE.md`: Added Activity Subsystem section with pipeline diagram
- `ROADMAP.md`: Added Phase 7 (Background Automation) + Phase 8 (Activity) + updated vision
- `PROJECT_STATE.md`: Restructured, added Activity subsystem + task tracking
- `CHANGELOG.md`: This entry

### Tag

`v0.4.0` — Activity Gateway receiving events, subsystem pipeline taking shape

---

## [v0.3.0] — 2026-06-18 (Claude Web Connected)

### First End-to-End Closed Loop

Claude Web Connector successfully connected to MCP Hub. This is the first
version where Claude (the AI) can discover and invoke tools through the Hub
over the standard MCP Streamable HTTP protocol.

- **Claude Web Connector** connected to `https://raven-victor.click/mcp`
- Auth mode: `none` (Claude Web has no Bearer Token input field)
- Protocol: MCP Streamable HTTP 2024-11-05 (via FastMCP 1.28.0)
- Transport: ASGI middleware proxy (zero-buffer SSE passthrough)
- 7 tools across 3 servers auto-discovered
- DEBUG protocol logging active (request/response dump)
- `docs/CLAUDE_DESKTOP_SETUP.md`: documented AUTH_MODE=none/bearer/oauth

### Tag

`v0.3.0` — MCP Hub successfully connected with Claude Connector

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
