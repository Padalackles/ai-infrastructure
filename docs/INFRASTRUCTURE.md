# Infrastructure Plan

## Purpose

This document defines the long-term infrastructure architecture of the AI Infrastructure project.

It describes where services will run, how they will be exposed to the Internet, and how future MCP services will be integrated.

This is a target architecture document.

Implementation will occur in later tasks.

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
Cloudflare
    │
HTTPS
    │
Caddy
    │
MCP Hub
    │
 ├── Ombre
    ├── ntfy
    ├── GitHub
    ├── Calendar
    └── Future MCP Services
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
├── ntfy
├── Monitoring
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

Target architecture:

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

Planned MCP integration.

Purpose:

* Notifications
* Mobile alerts
* Long-running task completion messages

Future architecture:

```text
Claude Desktop
        │
        ▼
     MCP Hub
        │
        ├── Ombre
        └── ntfy
```

---

# Cloudflare

Cloudflare will be introduced during production deployment.

Responsibilities:

* DNS management
* HTTPS support
* Security protection
* Traffic proxying
* Public endpoint management

Example:

```text
mcp.example.com
        │
   Cloudflare
        │
      VPS
```

---

# Caddy

Caddy acts as the reverse proxy.

Responsibilities:

* HTTPS termination
* Routing
* Certificate management
* Service exposure

Example:

```text
Internet
    │
Cloudflare
    │
Caddy
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

# Deployment Roadmap

Task009
Integrate Existing Ombre Deployment

Task010
Integrate ntfy

Task011
Claude Desktop Integration

Task012
Docker Production Deployment

Task013
Cloudflare + Caddy

Task014
Production Hardening

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
