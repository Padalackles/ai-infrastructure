# Decision Engine — Rule Configuration

**Version:** 1.0.0
**Status:** ✅ Implemented (Task A009)
**Created:** 2026-06-19

---

## Overview

All rule parameters live in `decision/config/rules.yaml`.  Decision code
MUST NOT hard-code thresholds, apps, cooldowns, or any other business
parameters.  To change behaviour, edit the YAML file — no code changes
required.

---

## Configuration File

**Location:** `decision/config/rules.yaml`

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

### Rule Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | ✅ | Unique rule identifier. Used for cooldown tracking. |
| `enabled` | `boolean` | ✅ | `false` to disable without deleting. |
| `trigger` | `string` | ✅ | Trigger type emitted when the rule fires. |
| `threshold_minutes` | `number` | ✅ | Minimum duration before the rule fires. |
| `cooldown_minutes` | `number` | ✅ | Quiet period after firing (no repeat triggers). |
| `package` | `string` | per-rule | Android package name (app rules only). |

---

## Adding a New Rule

1. Add the rule definition to `decision/config/rules.yaml`.
2. Write a Python function with the signature `(events) -> Trigger | None`.
3. Decorate it with `@register` from `decision.rules`.
4. Zero changes to `DecisionService` or any other file.

---

## Modifying Behaviour (No Code Changes)

| Change | Action |
|---|---|
| Change threshold from 40 to 60 min | Edit `threshold_minutes` in YAML |
| Monitor Bilibili instead of Douyin | Change `package` to `tv.danmaku.bili` |
| Add a new app to monitor | Add a new rule block in YAML |
| Disable a rule | Set `enabled: false` |
| Adjust cooldown | Edit `cooldown_minutes` |

---

## Rule Logic vs Configuration

| Layer | Responsibility | Example |
|---|---|---|
| **YAML** | Parameters | `threshold_minutes: 40` |
| **Python** | Logic | How to compute a screen session, when to fire |

YAML never describes logic.  Python never hard-codes values.

---

## Session Definitions

### Screen Session

- **Start:** most recent `screen.on` event.
- **End:** matching `screen.off`, or current time if still on.
- **Duration:** `now - screen.on.timestamp`.

### App Session

- **Start:** most recent `app.opened` event with matching `package`.
- **End:** matching `app.closed`, or current time if still open.
- **Duration:** `now - app.opened.timestamp`.

All rules use `SessionAnalyzer` — they never scan events directly.

---

## Cooldown

After a rule fires, it enters a cooldown window.  Subsequent evaluation
cycles within that window silently skip the rule.

Cooldowns are managed by `CooldownStore`:
- `MemoryCooldownStore` — in-memory (Phase 1).
- `RedisCooldownStore` — durable (future).

---

## Trigger Payload

Every Trigger includes both the configured threshold and the actual
measured duration:

```json
{
    "type": "screen.long_use",
    "payload": {
        "threshold_minutes": 40,
        "actual_minutes": 53
    }
}
```

```json
{
    "type": "app.long_use",
    "payload": {
        "app": "com.ss.android.ugc.aweme",
        "threshold_minutes": 30,
        "actual_minutes": 37
    }
}
```

---

## Architecture Constraint

Decision Engine responsibilities:
- ✅ Read Activity Events.
- ✅ Analyze sessions.
- ✅ Evaluate rules against thresholds.
- ✅ Emit Trigger objects.

Decision Engine does NOT:
- ❌ Generate reminder text.
- ❌ Call Claude or the MCP Hub.
- ❌ Send notifications.
- ❌ Store memory.

Claude is the only intelligent layer.

---

## Related Documents

- `docs/decision/ARCHITECTURE.md` — Full module architecture.
- `docs/activity/SCHEMA.md` — Activity Event schema.
- `PROJECT_STATE.md` — Current development status.
