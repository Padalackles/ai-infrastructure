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
