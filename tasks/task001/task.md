# Task-001 — Migrate Ombre MCP Server to Docker Compose

## Objective

Take over the existing Ombre MCP Server container and migrate it from a standalone `docker run` deployment to the project's unified Docker Compose management.

This task establishes Docker Compose as the standard deployment method for all current and future services.

---

## Background

The Ombre MCP Server service is already deployed and running correctly.

Current deployment uses a standalone Docker container.

Future development requires every service to be managed through the project's `docker-compose.yml`.

---

## Scope

### Step 1

Inspect the current Ombre MCP Server container.

Collect:

- Container name
- Image
- Ports
- Volumes
- Environment variables
- Restart policy

---

### Step 2

Create the Compose definition.

Requirements:

- Place service configuration under the project Compose structure.
- Mount configuration files from `config/`.
- Mount persistent data under `data/`.

---

### Step 3

Verify migration.

Confirm:

- `docker compose up -d`
- `docker compose stop`
- `docker compose start`
- `docker compose logs`

all function correctly.

---

## Deliverables

- `docker-compose.yml`
- Updated directory structure
- Verified Compose deployment

---

## Success Criteria

- Ombre MCP Server runs under Docker Compose.
- No data is lost.
- Future management no longer relies on `docker run`.

---

## Dependencies

- Docker
- Existing Ombre MCP Server container

---

## Next Task

Task-002 — Standardize Project Directory Structure
