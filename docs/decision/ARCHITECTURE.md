# Decision Engine Architecture

**Version:** 2.0.0
**Status:** ✅ Implemented (Task A009 — Phase 2: Configuration-driven)
**Created:** 2026-06-19
**Updated:** 2026-06-19

---

## Overview

The Decision Engine bridges raw device events and autonomous Claude awareness.
It evaluates recent Activity Events against configured rules and emits **Trigger**
objects when rules match.

Phase 2 is **configuration-driven**: all rule parameters come from YAML.
No thresholds, apps, or cooldowns are hard-coded in Python.

```
Activity Events
        │
        ▼
SessionAnalyzer  (screen / app session extraction)
        │
        ▼
Rule Engine  (configured rules from rules.yaml)
        │
        ▼
CooldownStore  (suppress repeated triggers)
        │
        ▼
Trigger objects
        │
        ▼
Console (print)  →  future: Claude Trigger
```

---

## Architecture Constraint

**Claude is the only intelligent layer.**

The Decision Engine decides **whether** to emit a Trigger.  It never:

| Constraint | Why |
|---|---|
| ❌ Generates reminder text | Claude decides what to say |
| ❌ Calls Claude / MCP Hub | Phase 3 — Claude Trigger bridges this |
| ❌ Sends ntfy notifications | Phase 3 — Trigger consumer handles delivery |
| ❌ Stores memory / Ombre | Phase 3 — Claude Trigger writes memory |
| ❌ Hard-codes business parameters | All thresholds, apps, cooldowns from YAML |
| ✅ Emits Trigger objects | Stable schema consumed by downstream components |

---

## Module Structure

```
decision/
├── __init__.py        # Public API
├── models.py          # Trigger dataclass — the *only* output
├── rules.py           # Rule functions + @register decorator + registry
├── service.py         # DecisionService.evaluate() — orchestration
├── scheduler.py       # 60-second loop + CLI entry point
├── cooldown.py        # CooldownStore ABC + MemoryCooldownStore
├── rule_manager.py    # RuleManager — config facade
├── config/
│   ├── __init__.py
│   ├── loader.py      # load_rules() / reload_rules()
│   └── rules.yaml     # All rule parameters
├── analyzers/
│   ├── __init__.py
│   └── session.py     # SessionAnalyzer — screen & app sessions
└── tests/
    ├── test_models.py           # Trigger creation, uniqueness, repr
    ├── test_rules.py            # Real rules, cooldown, disabled rules
    ├── test_service.py          # evaluate() edge cases
    ├── test_scheduler.py        # Scheduler loop
    ├── test_config_loader.py    # YAML loading, errors, reload
    ├── test_rule_manager.py     # Rule filtering, reload
    ├── test_cooldown.py         # MemoryCooldownStore
    └── test_session_analyzer.py # Screen & app sessions
```

---

## Trigger Model

The `Trigger` is a stable dataclass — the contract between Decision and
all downstream consumers.

```python
@dataclass
class Trigger:
    id: str           # trg_<ULID-style> — globally unique
    type: str         # Stable type: screen.long_use, app.long_use, ...
    timestamp: str    # ISO 8601 UTC
    payload: dict     # Rule-specific data (threshold_minutes, actual_minutes, ...)
```

Every Trigger payload MUST include:
- `threshold_minutes` — the configured threshold that was exceeded.
- `actual_minutes` — the measured duration at time of firing.

---

## Configuration System

### Rule Config (YAML)

```yaml
rules:
  - id: screen_long_use
    enabled: true
    trigger: screen.long_use
    threshold_minutes: 40
    cooldown_minutes: 60

  - id: app_long_use
    enabled: true
    trigger: app.long_use
    package: com.ss.android.ugc.aweme
    threshold_minutes: 30
    cooldown_minutes: 120
```

### Config Loader

```python
from decision.config.loader import load_rules, reload_rules

rules = load_rules()        # first load from default path
rules = reload_rules()      # hot-reload same file
```

- Missing file / invalid YAML → logged, returns `[]`.
- Never crashes the process.

### Rule Manager

```python
from decision.rule_manager import RuleManager

mgr = RuleManager()
rule = mgr.get_rule("screen_long_use")   # → dict | None
enabled = mgr.get_enabled_rules()         # → list[dict]
mgr.reload()                              # hot-reload
```

DecisionService and rules access config through RuleManager —
they never touch YAML directly.

---

## Session Analyzer

Extracts time-window information from events.  Injected at construction:

```python
from decision.analyzers import SessionAnalyzer

analyzer = SessionAnalyzer(events)
screen = analyzer.get_current_screen_session()
app    = analyzer.get_current_app_session("com.ss.android.ugc.aweme")
```

### Screen Session

- **Start:** most recent `screen.on` event.
- **End:** `screen.off` after start, or `None` if still on.
- **Duration:** `now - start` for active; `end - start` for completed.

### App Session

- **Start:** most recent `app.opened` with matching `package`.
- **End:** `app.closed` with matching `package`, or `None`.
- **Duration:** same logic as screen session.

---

## Cooldown

```python
from decision.cooldown import MemoryCooldownStore

store = MemoryCooldownStore()
store.set("screen_long_use", datetime.now(timezone.utc))
last = store.get("screen_long_use")  # → datetime | None
```

- Abstract interface — swap to `RedisCooldownStore` with zero rule changes.
- Cooldown check: `elapsed_minutes < cooldown_minutes` → suppress.

---

## Rule Framework

### Rule Signature

```python
(events: list[dict]) -> Trigger | None
```

### Adding a New Rule

1. Add config to `decision/config/rules.yaml`.
2. Write a rule function, decorated with `@register`.
3. Access config via `get_rule_manager().get_rule("rule_id")`.
4. Analyze events via `SessionAnalyzer(events)`.
5. Check cooldown via `get_cooldown_store().get("rule_id")`.

**Zero changes to DecisionService or any other file.**

### Current Rules

| Rule | Trigger Type | Config Keys |
|---|---|---|
| `screen_long_use_rule` | `screen.long_use` | `threshold_minutes`, `cooldown_minutes` |
| `app_long_use_rule` | `app.long_use` | `package`, `threshold_minutes`, `cooldown_minutes` |

### Error Isolation

If a rule raises an exception, the DecisionService catches it
and continues with the remaining rules — never crashes the cycle.

---

## Acceptance Criteria

All of the following require **zero code changes** — edit `rules.yaml` only:

| Change | YAML Edit |
|---|---|
| 40 min → 60 min threshold | `threshold_minutes: 60` |
| Douyin → Bilibili | `package: tv.danmaku.bili` |
| Add a new app | New rule block |
| Disable a rule | `enabled: false` |
| Adjust cooldown | `cooldown_minutes: <new_value>` |

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
                                      SessionAnalyzer
                                            │
                                            ▼
                                      DecisionService.evaluate()
                                            │
                                            ▼
                                      Rule Engine  (@register)
                                            │
                                      ┌─────┴─────┐
                                      ▼           ▼
                                  RuleManager  CooldownStore
                                  (YAML)       (memory)
                                            │
                                            ▼
                                       Trigger objects
                                            │
                                     ┌──────┴──────┐
                                     ▼              ▼
                                  Console        Claude Trigger
                                 (current)       (Phase 3)
```

---

## Related Documents

- `docs/decision/RULES.md` — Rule configuration reference.
- `docs/activity/SCHEMA.md` — Activity Event schema.
- `PROJECT_STATE.md` — Current development status.
- `ROADMAP.md` — Long-term planning.
