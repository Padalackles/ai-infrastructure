# MCP Services

## Purpose

This document records every MCP service integrated into the AI Infrastructure.

It serves as the central registry for:

- Installed MCPs
- Configuration
- Permissions
- Communication methods
- Current status
- Future expansion

The project follows the **MCP First** design principle:

> Any new capability should be integrated as an MCP service whenever possible.

---

# MCP Architecture

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
```

---

# Installed MCPs

## Filesystem MCP

### Purpose

Provide secure access to project files.

### Capabilities

- Read files
- Write files
- Search files
- Create folders

### Permission

Local workspace only.

### Communication

Claude Desktop
→ MCP Hub
→ Filesystem MCP

### Status

⬜ Reserved — not yet implemented

### Future

- Workspace isolation
- Permission control

## GitHub MCP

### Purpose

Interact with GitHub repositories.

### Capabilities

- Read repositories
- Commit changes
- Create Pull Requests
- Manage Issues

### Permission

GitHub Personal Access Token

### Communication

Claude Desktop
→ MCP Hub
→ GitHub API

### Status

⬜ Reserved — not yet implemented

### Future

- Automatic documentation update
- CI/CD integration

## Ombre MCP

### Purpose

Provide long-term AI memory.

### Capabilities

- Store memories
- Retrieve memories
- Semantic search
- Context restoration

### Permission

External deployment (45.76.169.98:8000)

### Communication

Claude Desktop
→ MCP Hub
→ Ombre Adapter (HTTP)
→ External Ombre Deployment

### Status

✅ Integrated (Task-009) — Hub adapter complete. External Ombre deployment is independent.

### Future

- Multi-session memory
- Knowledge graph

## ntfy MCP

### Purpose

Push notifications to mobile devices.

### Capabilities

- Deployment notification
- Task completion
- Alert delivery

### Permission

Configured ntfy topic

### Communication

Claude Desktop
→ MCP Hub
→ ntfy Adapter (HTTP)
→ ntfy.sh API

### Status

✅ Integrated (Task-010) — Hub adapter complete. Notifications route via ntfy.sh.

## Browser MCP

### Purpose

Web browsing

### Status

Future

## SSH MCP

### Purpose

Remote server management

### Status

Future

---

# Planned MCPs

- Calendar
- Email
- Database
- Docker
- Kubernetes
- PostgreSQL
- Redis
- Monitoring
- AI Agent

---

# MCP Integration Rules

Every new capability should follow this workflow:

1. Evaluate whether it can be implemented as an MCP.
2. Register the MCP in this document.
3. Define permissions.
4. Define communication flow.
5. Update ARCHITECTURE.md if necessary.

Avoid directly coupling new functionality into the core infrastructure.
