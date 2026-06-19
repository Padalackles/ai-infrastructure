# Activity Storage — SQLite Persistence Layer

**Version:** 1.0.0
**Status:** ✅ Implemented (Task A004)
**Created:** 2026-06-19

---

## Overview

The Storage layer persists normalized Activity Events to a local SQLite
database. It sits downstream of the Normalizer and upstream of the Decision
Script:

```
Gateway → Normalizer → Storage → Decision → Claude Trigger
```

---

## Pipeline

```
HTTP POST
      │
      ▼
Gateway (validate + build event)
      │
      ▼
Normalizer (canonical type mapping + payload normalization)
      │
      ▼
Repository.save_event() → SQLite (data/activity.db)
      │
      ▼
Console (log)
      │
      ▼
Response (accepted / error)
```

Persistence failures return HTTP 500. The original event data is never
lost — the Normalizer has already run and the normalized dict is available
for logging even when the save fails.

---

## Database

| Property | Value |
|---|---|
| Engine | SQLite 3 (standard library `sqlite3`) |
| File | `data/activity.db` (auto-created) |
| Journal | WAL mode |
| Foreign Keys | ON |
| ORM | None — raw parameterized SQL |

### Table: `events`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | TEXT | PRIMARY KEY | Event ULID (e.g. `evt_abc123`) |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Schema version |
| `timestamp` | TEXT | NOT NULL | ISO 8601 event time |
| `source` | TEXT | NOT NULL | Platform (android, ios, …) |
| `collector` | TEXT | NOT NULL | Software (macrodroid, tasker, …) |
| `device` | TEXT | NOT NULL | Device identifier |
| `type` | TEXT | NOT NULL | Canonical event type |
| `payload` | TEXT | NOT NULL, DEFAULT `{}` | JSON — normalized payload |
| `raw` | TEXT | NOT NULL, DEFAULT `{}` | JSON — original collector event |
| `created_at` | TEXT | NOT NULL | ISO 8601 — when saved to DB |

Database is created automatically on first startup (`init_db()` called in
`main.py` lifespan). The DDL uses `CREATE TABLE IF NOT EXISTS` — safe to
call on every boot.

---

## Repository API

| Method | Returns | Description |
|---|---|---|
| `save_event(event)` | `str` (event ID) | Persist a normalized event. Raises `RuntimeError` on failure. |
| `get_event(id)` | `dict` or `None` | Retrieve a single event by ID. |
| `list_events(limit=100)` | `list[dict]` | Most recent events, newest first. Limit clamped [1, 1000]. |
| `count_events()` | `int` | Total number of stored events. |

SQL is never exposed to callers — all methods accept and return plain
`dict` objects.

### Example

```python
from activity.storage.repository import ActivityRepository

repo = ActivityRepository()
repo.save_event(normalized_event)
found = repo.get_event("evt_abc123")
recent = repo.list_events(limit=50)
total = repo.count_events()
```

---

## JSON Serialization

`payload` and `raw` are stored as compact JSON text (`json.dumps` with
no extra whitespace). They are deserialized back to Python `dict` on read.

Complex nested structures survive the round-trip intact:
- Nested dicts/lists
- `null`/`true`/`false`
- Unicode

---

## Architecture Rules

Each layer has a single responsibility:

| Layer | Responsibility | Must NOT |
|---|---|---|
| **Gateway** | HTTP ingest, validation, ULID generation | Query SQLite |
| **Normalizer** | Type mapping, payload normalization | Write to disk |
| **Repository** | CRUD operations | Make decisions, call Claude |
| **Database** | Connection management, DDL | Know about events or collectors |

No layer knows about layers two steps away.

---

## Code Location

```
activity/storage/
├── __init__.py       # Package docstring, exports
├── database.py       # get_db_path(), init_db(), get_connection()
├── repository.py     # ActivityRepository — save/get/list/count
└── tests/
    ├── __init__.py
    └── test_storage.py  # 19 unit tests
```

---

## Related Documents

- `activity/types.ts` — TypeScript type contract
- `docs/activity/SCHEMA.md` — Event schema specification
- `docs/activity/NORMALIZER.md` — Normalization flow and mapping strategy
- `ARCHITECTURE.md` — System architecture
- `PROJECT_STATE.md` — Current development status
- `ROADMAP.md` — Long-term planning
