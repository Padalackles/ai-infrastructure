# Project Specification

---

## 1. Project Principles

This project follows these core principles:

### 1. MCP First

New capabilities should be implemented as MCP services whenever possible.

Avoid tightly coupling functionality into the infrastructure.

---

### 2. Documentation First

Every architectural change must be documented before implementation.

Documentation is considered part of the source code.

---

### 3. Context Preservation

Project knowledge must always exist inside the GitHub repository.

No critical design decision should exist only inside AI conversations.

---

### 4. Modular Architecture

Each component should have a single responsibility.

Components communicate through standardized interfaces.

---

### 5. Incremental Development

Build the project step by step.

Avoid large-scale refactoring whenever possible.

---

## 2. Repository Structure

| File | Purpose |
|---|---|
| README.md | Project overview |
| PROJECT_STATE.md | Current development status |
| ARCHITECTURE.md | System architecture |
| ROADMAP.md | Development roadmap |

| Directory | Purpose |
|---|---|
| `docs/` | Technical documentation |
| `tasks/` | Current implementation tasks |
| `docker/` | Infrastructure configuration |
| `scripts/` | Automation scripts |

Files must be placed in their designated directories. Do not create ad-hoc files at the repository root.

---

## 3. Documentation Rules

Whenever a new feature is implemented:

- Update PROJECT_STATE.md
- Update ARCHITECTURE.md if architecture changes
- Update MCP.md if a new MCP is added
- Create a new task document if necessary
- Keep README.md consistent with project goals

Documentation updates happen *before* or *alongside* implementation, never after.

---

## 4. MCP Integration Rules

Before adding any new functionality:

1. Determine whether it can be implemented as an MCP.
2. If yes:
   - Register it in `docs/MCP.md`
   - Document permissions
   - Document communication flow
   - Update architecture if required
3. Avoid bypassing the MCP Hub.

Follow the **MCP First** principle at all times.

---

## 5. Development Workflow

```
Idea
  ↓
Task
  ↓
Documentation
  ↓
Implementation
  ↓
Testing
  ↓
Deployment
  ↓
Update PROJECT_STATE
```

Every feature follows this sequence. Documentation comes before code.

---

## 6. Naming Convention

| Pattern | Example |
|---|---|
| Task documents | `Task-001.md`, `Task-002.md`, `Task-003.md` |
| MCP registry | `MCP.md` |
| Project state | `PROJECT_STATE.md` |
| Architecture | `ARCHITECTURE.md` |
| Roadmap | `ROADMAP.md` |

Use consistent, descriptive names. Avoid abbreviations unless well-established.

---

## 7. Git Workflow

```
Feature Branch
  ↓
Implementation
  ↓
Documentation Update
  ↓
Commit
  ↓
Push
  ↓
Merge
```

- Branch from `main` for each feature.
- Commit documentation changes together with code.
- Push regularly to avoid losing context.

---

## 8. Future Expansion

The architecture should grow by adding new MCP services.

- Avoid redesigning the infrastructure unless absolutely necessary.
- Core architecture should remain stable.
- New functionality should be added through standardized interfaces.

The architecture should evolve through **extension**, not reconstruction.
