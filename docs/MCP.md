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

✅ Planned

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

⬜ Not Installed

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

Local database

### Communication

Claude Desktop
→ MCP Hub
→ Ombre

### Status

⬜ Planned

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
→ ntfy

### Status

⬜ Planned

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
