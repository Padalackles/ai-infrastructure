# System Architecture

## Overview

This project is a personal AI infrastructure built around **Claude Desktop** and the **Model Context Protocol (MCP)**.

The architecture follows the principle of **MCP First**, where new capabilities are added as independent MCP services instead of being tightly coupled to the core system.

---

## High-Level Architecture

```
                Internet
                    │
               Cloudflare
                    │
                 HTTPS
                    │
                 Caddy
                    │
            Docker Compose
                    │
      ───────────────────────────
        Infrastructure Layer
      ───────────────────────────
                    │
                 MCP Hub
        ┌──────────┼──────────┐
        │          │          │
   Filesystem   GitHub     Ombre
        │          │          │
       ntfy     Browser      SSH
        │
   Future MCP Services
```

---

## Layer Description

### External Layer

Responsible for secure external access.

**Components:**

- Cloudflare
- HTTPS
- Caddy

---

### Infrastructure Layer

Responsible for deployment and service management.

**Components:**

- Docker Compose
- Networking
- Persistent Storage

---

### MCP Layer

The core of the entire system.

**Responsibilities:**

- Connect Claude Desktop with services
- Standardize communication
- Isolate different modules
- Allow future expansion

---

### Service Layer

Provides actual capabilities through MCP.

**Examples:**

- Filesystem MCP
- GitHub MCP
- Browser MCP
- ntfy MCP
- Ombre MCP
- SSH MCP

Every service should be replaceable without affecting other modules.

---

## Communication Flow

```
User
   │
Claude Desktop
   │
MCP Hub
   │
Selected MCP Service
   │
External Resource
```

**Example:**

```
Claude Desktop
      ↓
GitHub MCP
      ↓
GitHub Repository
```

---

## Design Principles

### MCP First

Prefer implementing every new capability as an MCP service.

---

### Loose Coupling

Services should not directly depend on each other.

---

### Single Responsibility

Each MCP should provide one clear capability.

---

### Replaceability

Any service can be replaced without redesigning the architecture.

---

### Documentation First

Architecture changes should always be reflected in documentation.

---

## Planned MCP Services

| Service      | Purpose                  | Status   |
|--------------|--------------------------|----------|
| Filesystem   | Local file operations    | Planned  |
| GitHub       | Repository management    | Planned  |
| Browser      | Web interaction          | Planned  |
| ntfy         | Notifications            | Planned  |
| Ombre        | Long-term memory         | Planned  |
| SSH          | Remote server access     | Planned  |

---

## Future Expansion

Future capabilities should be added by introducing new MCP services rather than modifying the core architecture.

**Examples:**

- Calendar MCP
- Email MCP
- Database MCP
- Home Assistant MCP
- Monitoring MCP

This keeps the system modular and scalable over time.
