# Infrastructure Plan

## Purpose

This document describes the current architecture of the AI Infrastructure project.

It is updated to reflect the current production implementation.

---

# Design Principles

1. Claude Desktop is the primary user interface.

2. MCP Hub is the system core.

3. New capabilities should be added through MCP services whenever possible.

4. Docker is a deployment mechanism, not an architectural component.

5. Infrastructure should support future MCP services without redesign.

---

# High-Level Architecture

```text
Internet
    │
Cloudflare (DNS + SSL Full strict)
    │
HTTPS (:443)
    │
Caddy (reverse proxy + Let's Encrypt)
    │
MCP Hub (:8080)
    │
 ├── Ombre (external, 45.76.169.98:8000/mcp)
 └── ntfy  (external, ntfy.sh)
```

---

# VPS Strategy

The VPS acts as the central AI infrastructure host.

Responsibilities:

* Run MCP Hub
* Run supporting services
* Host Docker containers
* Provide a stable public endpoint
* Enable remote access from Claude Desktop

The VPS becomes the permanent runtime environment for the AI ecosystem.

---

# Docker Strategy

Docker is used for deployment and service isolation.

Docker is not part of the core architecture.

Typical deployment:

```text
Docker
│
├── MCP Hub
├── Caddy
└── Future Services
```

---

# MCP Hub

MCP Hub is the central orchestration layer.

Responsibilities:

* Service discovery
* Service registration
* Request routing
* Lifecycle management
* Configuration management

All MCP services connect through the Hub.

---

# Ombre

Status:

Existing external deployment.

Ombre is an independently deployed MCP-compatible long-term memory service.

This repository does not reimplement Ombre.

MCP Hub integrates Ombre through the MCP interface.

Architecture:

```text
Claude Desktop
        │
        ▼
     MCP Hub
        │
        ▼
      Ombre
```

---

# ntfy

Status:

Implemented — push notifications via curl adapter to ntfy.sh.

The MCP Hub connects to ntfy.sh through `mcp_servers/ntfy/adapter.py` (HTTP bridge).
Three tools are exposed: `notify_send`, `ntfy_health`, `ntfy_info`.

Purpose:

* Notifications
* Mobile alerts
* Long-running task completion messages

Architecture:

```text
Claude Desktop
        │
        ▼
     MCP Hub
        │
        ├── Ombre
        └── ntfy (ntfy.sh)
```

---

# Cloudflare

Cloudflare provides DNS, SSL/TLS (Full strict), and DDoS protection for the production domain `raven-victor.click`.

Responsibilities:

* DNS management (A record → VPS 45.76.169.98)
* HTTPS support (SSL Full strict, edge certificate)
* Security protection (WAF, DDoS)
* Traffic proxying (orange-cloud)
* Public endpoint management

Architecture:

```text
raven-victor.click
        │
   Cloudflare (DNS + SSL Full strict)
        │
      VPS (45.76.169.98)
```

---

# Caddy

Caddy is the reverse proxy providing HTTPS termination and routing on the VPS.

Responsibilities:

* HTTPS termination (Let's Encrypt via acme-v02.api.letsencrypt.org)
* Routing (`/mcp`, `/health`, `/status`, `/tools` → `mcp-hub:8080`)
* Certificate management (auto-renewal)
* Service exposure

Architecture:

```text
Internet
    │
Cloudflare (DNS + SSL Full strict)
    │
Caddy (Let's Encrypt, reverse proxy :443 → :8080)
    │
MCP Hub
```

---

# Future MCP Services

Potential future integrations:

* GitHub
* Calendar
* Email
* Task Management
* Search
* Monitoring
* Custom MCP Servers

The architecture should support new MCP services without modifying the Hub core.

---

# Implementation Milestones

**Core Infrastructure**
MCP Hub foundation — FastAPI + FastMCP Streamable HTTP, plugin system, service discovery

**Plugin System**
Ombre adapter, ntfy adapter — MCP service plugins loaded via manifest discovery

**Ombre Integration** — Task-011
External Ombre Brain connected via Streamable HTTP MCP protocol

**Notification Integration** — Task-011
ntfy.sh push notifications via curl adapter

**HTTPS Deployment** — Task-012
Domain (`raven-victor.click`), Cloudflare SSL Full strict, Caddy reverse proxy with Let's Encrypt

**Production Validation** — Task-013
End-to-end testing: Claude Web ↔ Hub ↔ Ombre / ntfy

---

# Future Work

* GitHub MCP — repository interaction (reserved, not yet implemented)
* Filesystem MCP — secure file access on VPS (reserved, not yet implemented)
* Calendar / Email / Task Management integrations
* Monitoring and alerting
* Remote MCP registry federation
* Production hardening (rate limiting, Cloudflare WAF rules, auth upgrade)

---

# Long-Term Goal

Create a personal AI infrastructure platform where:

Claude Desktop

↓

MCP Hub

↓

Multiple MCP Services

↓

Persistent AI capabilities running on a VPS

The system should remain modular, extensible, and maintainable over time.
