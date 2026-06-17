# ROADMAP

## Vision

Build a personal AI infrastructure centered around **Claude Desktop** and an **MCP Hub**, enabling extensible AI capabilities through standardized MCP services.

**Design Principle:**

> **MCP First**
>
> Any new capability should be integrated through an MCP service whenever possible, rather than tightly coupling it into the infrastructure.

---

# Phase 0 — Project Bootstrap

## Goal

Establish the project structure and documentation so development can continue consistently across AI assistants and human contributors.

### Key Tasks

- [x] Create GitHub repository
- [x] Create README.md
- [x] Create PROJECT_STATE.md
- [x] Create ARCHITECTURE.md
- [x] Create ROADMAP.md
- [x] Create docs/
- [x] Create tasks/

### Completion Criteria

- Documentation structure completed
- Project context fully recoverable from GitHub

---

# Phase 1 — Infrastructure

## Goal

Build the underlying deployment environment.

### Key Tasks

- Docker Compose
- Caddy Reverse Proxy
- Cloudflare Tunnel
- Environment configuration
- SSL
- Network design

### Completion Criteria

- Infrastructure deployable with one command
- External access available through Cloudflare

---

# Phase 2 — MCP Platform

## Goal

Create the central MCP platform that connects Claude Desktop with backend services.

### Key Tasks

- MCP Hub
- Claude Desktop integration
- MCP communication workflow
- Configuration management

### Completion Criteria

- Claude Desktop successfully communicates with MCP Hub
- MCP services can be registered dynamically

---

# Phase 3 — Core MCP Services

## Goal

Integrate essential capabilities as independent MCP services.

### Planned MCPs

- Filesystem MCP
- GitHub MCP
- Ombre MCP
- ntfy MCP
- Browser MCP
- SSH MCP

### Completion Criteria

- Core services independently usable
- Unified MCP communication architecture established

---

# Phase 4 — Operations

## Goal

Improve reliability and maintainability.

### Key Tasks

- Monitoring
- Logging
- Backup
- Health Checks
- Metrics Collection

### Completion Criteria

- Infrastructure can self-monitor
- Recovery procedures documented

---

# Phase 5 — Automation

## Goal

Reduce manual operations through automation.

### Key Tasks

- GitHub Actions
- CI/CD Pipeline
- Automatic Deployment
- Configuration Validation
- Scheduled Tasks

### Completion Criteria

- Automated testing
- Automated deployment
- Automated documentation updates

---

# Phase 6 — Production

## Goal

Operate a stable long-term personal AI infrastructure.

### Key Tasks

- Performance optimization
- Security hardening
- Resource optimization
- Long-term maintenance
- Continuous MCP expansion

### Completion Criteria

- Stable production environment
- Easy onboarding for new MCP services
- Architecture supports long-term evolution

---

# Long-Term Vision

```
Claude Desktop
        │
        ▼
     MCP Hub
        │
 ┌──────┼──────────────┐
 │      │      │       │
Filesystem GitHub Ombre ntfy
        │
   Future MCP Services
        │
 Browser · SSH · Memory · Calendar · Email · ...
```

The infrastructure is designed so that future capabilities are added by introducing new MCP services rather than modifying the core architecture.

The architecture should evolve through extension, not reconstruction.
