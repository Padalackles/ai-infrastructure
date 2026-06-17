# Task-002 — Establish Ombre Brain Project Foundation

## Objective

Build a runnable, extensible project foundation for Ombre Brain that strictly follows `specification.md`. No business logic, no demo code — just the skeleton that Task-003 and beyond can extend directly.

---

## Background

Completed:

- `MCP.md` — overall architecture
- `specification.md` — project specification
- `Task-001.md` — requirement definition

This task begins formal development.

---

## Scope

### 1. Project Directory Structure

```
project/
├── app/
│   ├── api/
│   ├── core/
│   ├── mcp/
│   ├── models/
│   ├── services/
│   ├── scheduler/
│   ├── storage/
│   ├── utils/
│   └── main.py
├── config/
│   ├── config.yaml
│   └── prompts.yaml
├── data/
│   ├── conversations/
│   ├── memories/
│   ├── tasks/
│   └── cache/
├── tests/
├── requirements.txt
├── README.md
└── .env.example
```

### 2. FastAPI

- `GET /health` returns `{"status": "ok"}`
- Runnable via `uvicorn app.main:app --reload`

### 3. Configuration System

- `app/core/config.py` — Config singleton reading `config/config.yaml`

### 4. MCP Module

- `client.py`, `server.py`, `registry.py` — class stubs only

### 5. Storage

- `file_storage.py` — `save_json()`, `load_json()`, `delete()`, `list()` using local JSON files

### 6. Scheduler

- `task_scheduler.py` — `TaskScheduler` with `add_task()`, `cancel()`, `run_pending()` — empty implementations

### 7. Services

- `conversation_service.py`, `memory_service.py`, `task_service.py` — interface stubs only

### 8. Models

- Pydantic models: `Conversation`, `Memory`, `Task`, `UserConfig` — minimal fields

### 9. requirements.txt

- `fastapi`, `uvicorn`, `pydantic`, `pyyaml`, `httpx`

### 10. README

- Project overview, directory structure, startup instructions

---

## Deliverables

- Complete project directory with all files
- Runnable `uvicorn app.main:app --reload`
- Task documentation

---

## Success Criteria

- `GET /health` returns `{"status": "ok"}`
- All imports resolve correctly
- No business logic implemented
- Ready for Task-003 to extend

---

## Next Task

Task-003 — TBD
