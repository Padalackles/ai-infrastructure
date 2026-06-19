# Activity API Reference

**Version:** 1.0.0
**Status:** ✅ Implemented (Task A007)
**Created:** 2026-06-19

---

## Overview

The Activity subsystem exposes a REST API for ingesting and querying device events.

```
                   ┌─────────────┐
MacroDroid ──────▶│    POST     │──────▶ Normalizer ──▶ SQLite
                   │  /events    │
                   └─────────────┘

                   ┌─────────────┐
Decision ◀────────│     GET     │◀────── Service ──◀── SQLite
Claude   ◀────────│  /recent    │
Web UI   ◀────────│  /latest    │
                   │  /history   │
                   │  /types     │
                   └─────────────┘
```

**Base URL:** `http://localhost:8080/activity` (dev) / `https://<domain>/activity` (prod)

---

## Endpoints

### POST /activity/events — Ingest an event

Receives raw device events from collectors (MacroDroid, Tasker, etc.).

**Request Body (JSON):**

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | ✅ | Platform: `android`, `ios`, `desktop`, `web`, `iot`, `service` |
| `collector` | string | ✅ | Collector: `macrodroid`, `tasker`, `shortcuts`, etc. |
| `device` | string | ✅ | Device identifier: `pixel-8-pro`, `iphone-15` |
| `type` | string | ✅ | Collector-specific event name: `screen_on`, `wifi_connected`, etc. |
| `payload` | object | — | Event data (defaults to `{}`) |
| `version` | integer | — | Schema version (defaults to `1`) |
| `id` | string | — | Event ID (server-generated if omitted) |
| `timestamp` | string | — | ISO 8601 timestamp (server time if omitted) |
| `raw` | object | — | Original collector event (defaults to `{}`) |

**Response 200:**

```json
{
  "status": "accepted",
  "id": "evt_01jx2k4n8p3q5r7s9t",
  "timestamp": "2026-06-19T09:00:00.000Z",
  "version": 1
}
```

**Response 500:**

```json
{
  "status": "error",
  "message": "Failed to persist event",
  "id": "evt_01jx2k4n8p3q5r7s9t"
}
```

---

### GET /activity/recent — Most recent events

Returns the most recently stored events, newest first.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `50` | Max events to return (clamped to 1–1000) |

**Response 200:**

```json
[
  {
    "version": 1,
    "id": "evt_01jx2k4n8p3q5r7s9t",
    "timestamp": "2026-06-19T09:00:00.000Z",
    "source": "android",
    "collector": "macrodroid",
    "device": "pixel-8-pro",
    "type": "device.awake",
    "payload": {"method": "power_button"},
    "raw": {"type": "screen_on", "method": "power_button"},
    "created_at": "2026-06-19T09:00:00.123Z"
  }
]
```

**Example:**

```bash
curl "http://localhost:8080/activity/recent?limit=5"
```

---

### GET /activity/latest — Latest event of a type

Returns the most recent event of a specific canonical type.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `type` | string | (required) | Canonical event type: `device.awake`, `app.opened`, etc. |

**Response 200:** Single event object (see `/recent` response shape).

**Response 404:**

```json
{
  "status": "not_found",
  "message": "No events of type 'nonexistent.type'"
}
```

**Example:**

```bash
curl "http://localhost:8080/activity/latest?type=device.awake"
```

---

### GET /activity/history — Events in a time range

Returns events with `timestamp` within `[start, end]`, newest first.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `start` | string | (required) | ISO 8601 start timestamp (inclusive) |
| `end` | string | (required) | ISO 8601 end timestamp (inclusive) |
| `limit` | integer | `100` | Max events to return (clamped to 1–1000) |

**Response 200:** Array of event objects (see `/recent` response shape).

**Response 422:** Missing `start` or `end` parameter.

**Example:**

```bash
curl "http://localhost:8080/activity/history?start=2026-06-01T00:00:00Z&end=2026-06-30T23:59:59Z&limit=50"
```

---

### GET /activity/types — Known event types

Returns all distinct canonical event types currently stored in the database, in alphabetical order.

**Query Parameters:** None.

**Response 200:**

```json
[
  "app.closed",
  "app.opened",
  "device.awake",
  "device.sleep",
  "network.wifi.connected"
]
```

**Example:**

```bash
curl "http://localhost:8080/activity/types"
```

---

## Architecture

```
Gateway (router.py)
    ├── POST /events    → build_event() → normalize_event() → _repo.save_event()
    └── GET  /recent    → _service.get_recent()
        GET  /latest    → _service.get_latest()
        GET  /history   → _service.get_between()
        GET  /types     → _service.list_types()

Service (service.py)
    └── ActivityService → wraps ActivityRepository (read-only)

Storage (storage/)
    ├── database.py     → SQLite connection + schema + indexes
    └── repository.py   → ActivityRepository (CRUD)
```

- **POST** writes through the Repository directly (the Normalizer transforms first).
- **GET** reads through the Service, which delegates to the Repository.
- The Service is constructor-injected — future PostgreSQL repo is a drop-in replacement.

---

## Related Documents

- `docs/activity/SCHEMA.md` — Event schema specification
- `docs/activity/NORMALIZER.md` — Normalization flow
- `docs/activity/STORAGE.md` — SQLite persistence
- `docs/activity/MACRODROID.md` — MacroDroid integration guide
- `ARCHITECTURE.md` — System architecture
