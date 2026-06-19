# Event Normalizer — Normalization Flow & Mapping Strategy

**Version:** 1.0.0
**Status:** ✅ Implemented (Task A003)
**Created:** 2026-06-19

---

## Overview

The Event Normalizer transforms collector-specific Activity Events into the
unified canonical format consumed by all downstream components (Database,
Decision Script, Claude Trigger).

It sits between the Activity Gateway and the Event Database:

```
Gateway → Normalizer → Database → Decision → Claude Trigger
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
Normalizer
   ├── Map type (collector → canonical)
   ├── Normalize payload (per-type schema)
   ├── Preserve raw (original event snapshot)
   └── Log unknown types (warning, no crash)
      │
      ▼
Console (log)
      │
      ▼
Response (accepted)
```

---

## Mapping Strategy

### Design

The Normalizer uses an **extensible mapping table** rather than hard-coded
`if/else` chains. All mappings live in `activity/normalizer/mappings.py`.

```python
EVENT_MAPPINGS: dict[str, str] = {
    # MacroDroid
    "screen_on":  "device.awake",
    "screen_off": "device.sleep",

    # Tasker / Home Assistant
    "display_on":  "device.awake",
    "display_off": "device.sleep",

    # ...
}
```

### Canonical Event Naming

Event types use **hierarchical dot-notation**: `<domain>.<subdomain>.<action>`.

| Collector Name | Canonical Name |
|---|---|
| `screen_on` | `device.awake` |
| `screen_off` | `device.sleep` |
| `battery_low` | `battery.low` |
| `charging_started` | `battery.charging.started` |
| `charging_stopped` | `battery.charging.stopped` |
| `display_on` | `device.awake` |
| `display_off` | `device.sleep` |
| `power_connected` | `battery.charging.started` |
| `power_disconnected` | `battery.charging.stopped` |

### Adding a New Collector

1. Add entries to `EVENT_MAPPINGS` in `mappings.py`.
2. If the new collector introduces new payload shapes, add a payload
   normalizer in `service.py` under `_PAYLOAD_NORMALIZERS`.
3. Add the new event types to `activity/types.ts` and `docs/activity/SCHEMA.md`.
4. Update the mapping table in this document.

Zero Gateway changes required.

---

## Payload Normalization

Each canonical event type has an optional payload normalizer. These
validate and coerce fields to match the canonical sub-schema.

Example — `battery.low`:

```python
def _norm_battery_low(payload: dict) -> dict:
    return {
        "level": _int_field(payload, "level", 0),       # required
        "is_charging": _bool_field(payload, "is_charging", False),  # required
    }
```

Normalizers are dispatched by canonical type via `_PAYLOAD_NORMALIZERS`.
Types without an entry pass through unchanged.

### Type Coercion Rules

| Field Type | Missing | Wrong Type |
|---|---|---|
| `str` | `""` (empty string) | Falls back to default |
| `int` | `0` | Falls back to default |
| `bool` | `false` | Falls back to default |

The Normalizer never raises exceptions on bad payload data — it always
returns a valid canonical event.

---

## Unknown Event Handling

When a collector sends an event type not in `EVENT_MAPPINGS`:

1. The event type is set to `"unknown"`.
2. The full original event is preserved in `raw`.
3. A warning is logged with the collector, device, and raw type:

   ```
   WARNING — Unknown event type 'some_bizarre_event' from collector 'macrodroid'
            (device 'pixel-8-pro'). Event preserved in raw; type set to 'unknown'.
   ```

4. The Gateway continues functioning normally.

Downstream components can check `type == "unknown"` to identify unmapped
events without crashing.

---

## Raw Preservation

The Normalizer guarantees the original event is always preserved:

```
event.raw == original_collector_event  (always true)
```

This enables:
- **Re-processing** — If the Normalizer logic changes, historical events
  can be re-normalized from `raw`.
- **Debugging** — Collector-specific quirks are never lost.
- **Audit** — The normalization pipeline is fully traceable.

If the Gateway omitted `raw` (empty dict), the Normalizer snapshots the
full incoming event as `raw`.

---

## Source Independence

The Normalizer makes no assumptions about:

- Operating system (Android, iOS, desktop, IoT)
- Collector software (MacroDroid, Tasker, Shortcuts, Home Assistant)
- Transport mechanism (HTTP webhook, WebSocket, MQTT)

Adding a new source requires only mapping entries — zero code changes to
the Normalizer core.

---

## Constraints

The Normalizer must NOT:

- Write to SQLite (database is Task A004)
- Make business decisions (Decision Script is Task A006)
- Generate reminders (Claude Trigger is Task A007)
- Call Claude (MCP Hub handles that)
- Know anything about ntfy (separate MCP service)

It is a pure transformation layer.

---

## Code Location

```
activity/normalizer/
├── __init__.py       # Package docstring, exports normalize_event
├── mappings.py       # EVENT_MAPPINGS table + canonical_type()
├── service.py        # normalize_event() + payload normalizers
└── tests/
    └── test_normalizer.py  # 20 unit tests
```

---

## Related Documents

- `activity/types.ts` — TypeScript type contract
- `docs/activity/SCHEMA.md` — Event schema specification
- `ARCHITECTURE.md` — System architecture (Activity subsystem)
- `PROJECT_STATE.md` — Current development status
- `ROADMAP.md` — Long-term planning
