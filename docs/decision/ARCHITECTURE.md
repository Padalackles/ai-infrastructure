# Decision Engine Architecture

**Version:** 1.0.0
**Status:** ✅ Implemented (Task A008 — Phase 1)
**Created:** 2026-06-19

---

## Overview

The Decision Engine bridges raw device events and autonomous Claude awareness.
It evaluates recent Activity Events against registered rules and emits **Trigger**
objects when rules match.

Phase 1 is **console-only**: Triggers are printed to stdout.  Claude integration
comes in Phase 2+.

```
Activity API (GET /activity/recent)
        │
        ▼
DecisionService.evaluate()
        │
        ▼
Rule Engine (registered rules)
        │
        ▼
Trigger objects
        │
        ▼
Console (print)
```

---

## Architecture Constraint

**Claude is the only intelligent layer.**

The Decision Engine decides **whether** to emit a Trigger.  It never:

| Constraint | Why |
|---|---|
| ❌ Generates reminder text | Claude decides what to say |
| ❌ Calls Claude / MCP Hub | Phase 2 — Claude Trigger bridges this |
| ❌ Sends ntfy notifications | Phase 2 — Trigger consumer handles delivery |
| ❌ Stores memory / Ombre | Phase 2 — Claude Trigger writes memory |
| ✅ Emits Trigger objects | Stable schema consumed by downstream components |

---

## Module Structure

```
decision/
├── __init__.py        # Public API: Trigger, DecisionService, run, rules
├── models.py          # Trigger dataclass — the *only* output
├── rules.py           # Rule functions + @register decorator + registry
├── service.py         # DecisionService.evaluate() — orchestration
├── scheduler.py       # 60-second loop + CLI entry point
└── tests/
    ├── test_models.py    # Trigger creation, uniqueness, repr
    ├── test_rules.py     # Registry, placeholder rules, rule isolation
    ├── test_service.py   # evaluate() edge cases, broken rules, limits
    └── test_scheduler.py # Scheduler loop, output, error handling
```

---

## Trigger Model

The `Trigger` is a stable dataclass — the contract between Decision and
all downstream consumers (console, future Claude bridge).

```python
@dataclass
class Trigger:
    id: str           # trg_<ULID-style> — globally unique
    type: str         # Stable type: battery.low, focus.timeout, ...
    timestamp: str    # ISO 8601 UTC
    payload: dict     # Rule-specific data
```

Trigger types are **stable** — once defined, they should not be renamed
without updating all consumers.

---

## Rule Framework

### Rule Signature

```python
(events: list[dict]) -> Trigger | None
```

### Registry

Rules are registered via the `@register` decorator:

```python
from decision.rules import register
from decision.models import Trigger

@register
def my_rule(events: list[dict]) -> Trigger | None:
    for e in events:
        if e["type"] == "battery.low":
            return Trigger(type="battery.low", payload={"level": e["payload"]["level"]})
    return None
```

### Adding a New Rule

1. Write a function matching the rule signature.
2. Decorate it with `@register`.
3. Import the module somewhere (or place it in `rules.py`).

**Zero changes to DecisionService or any other file.**

### Current Rules (Phase 1)

| Rule | Status | Behavior |
|---|---|---|
| `battery_low_rule` | Placeholder | Returns `None` |
| `screen_awake_rule` | Placeholder | Returns `None` |
| `focus_timeout_rule` | Placeholder | Returns `None` |

Phase 2 will implement real logic in these rules.

### Error Isolation

If a rule raises an exception, the DecisionService catches it
and continues with the remaining rules.  The error is logged;
it never crashes the evaluation cycle.

---

## DecisionService

```python
class DecisionService:
    def __init__(self, activity_service: ActivityService): ...
    def evaluate(self) -> list[Trigger]: ...
```

- Reads the 50 most recent events via `ActivityService.get_recent(50)`.
- Iterates all registered rules in registration order.
- Collects non-None Trigger results.
- Returns the list (may be empty).

Constructor injection of `ActivityService` keeps the Decision Engine
decoupled from the storage layer — swap to PostgreSQL-backed
ActivityService without changing DecisionService.

---

## Scheduler

```python
from decision.scheduler import run

run(decision_service, interval=60)  # blocking loop
```

- Calls `evaluate()` every N seconds (default 60).
- Prints each Trigger via `print(trigger)`.
- Press Ctrl+C to stop.
- Handles evaluate() errors gracefully — logs and continues.

### CLI Entry Point

```bash
python -m decision.scheduler
```

Bootstraps the database, creates the service chain, and starts the loop.

---

## Data Flow (Full Pipeline)

```
MacroDroid (Android)
        │  HTTP POST /activity/events
        ▼
Activity Gateway  ──▶  Normalizer  ──▶  SQLite
                                            │
                                            ▼
                                       ActivityService  (read)
                                            │
                                            ▼
                                      DecisionService.evaluate()
                                            │
                                            ▼
                                       Rule Engine  (@register)
                                            │
                                            ▼
                                       Trigger objects
                                            │
                                     ┌──────┴──────┐
                                     ▼              ▼
                                  Console        Claude Trigger
                                 (Phase 1)       (Phase 2)
```

---

## Related Documents

- `ARCHITECTURE.md` — System architecture (top-level)
- `docs/activity/API.md` — Activity API reference
- `docs/activity/SCHEMA.md` — Event schema specification
- `PROJECT_STATE.md` — Current development status
- `ROADMAP.md` — Long-term planning
