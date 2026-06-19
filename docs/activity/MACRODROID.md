# MacroDroid Integration — Activity Gateway

**Version:** 1.0.0
**Status:** ✅ Implemented (Task A005)
**Created:** 2026-06-19

---

## Overview

MacroDroid sends device events to the Activity Gateway via HTTP POST.
The Gateway validates, normalizes, and persists every event to SQLite.

```
MacroDroid (Android)
        │  HTTP POST /activity/events
        ▼
Activity Gateway (VPS)
        │
        ▼
Normalizer (canonical type mapping)
        │
        ▼
SQLite (persistence)
```

No MacroDroid-specific logic exists in the Normalizer or downstream —
the mapping table handles all collector-to-canonical conversion.

---

## Endpoint

```
POST /activity/events
Content-Type: application/json
```

| Property | Value |
|---|---|
| URL (production) | `https://<your-domain>/activity/events` |
| URL (local dev) | `http://localhost:8080/activity/events` |
| Method | `POST` |
| Content-Type | `application/json` |

---

## Request Format

### Required Fields

| Field | Type | Example | Description |
|---|---|---|---|
| `source` | string | `"android"` | Originating platform |
| `collector` | string | `"macrodroid"` | Software that captured the event |
| `device` | string | `"pixel-8-pro"` | Human-readable device name |
| `type` | string | `"screen_on"` | Collector-specific event name |
| `payload` | object | `{"method":"power_button"}` | Event data (can be `{}`) |

### Optional Fields (Gateway fills if omitted)

| Field | Type | Default | Description |
|---|---|---|---|
| `version` | integer | `1` | Schema version |
| `id` | string | `evt_<ULID>` | Unique event identifier |
| `timestamp` | string | Server UTC | ISO 8601 timestamp |
| `raw` | object | `{}` | Original collector event |

---

## Supported Event Types

These are the MacroDroid (`collector: "macrodroid"`) event names and
their canonical equivalents after normalization:

| MacroDroid `type` | Canonical `type` | Payload Fields |
|---|---|---|
| `screen_on` | `device.awake` | `method` (power_button, tap, lift, notification, alarm) |
| `screen_off` | `device.sleep` | `method` (power_button, timeout, manual) |
| `charging_started` | `battery.charging.started` | `level` (int), `method` (usb, wireless, unknown) |
| `charging_stopped` | `battery.charging.stopped` | `level` (int) |
| `battery_changed` | `battery.level_changed` | `level` (int), `is_charging` (bool) |
| `wifi_connected` | `network.wifi.connected` | `ssid` (Wi-Fi network name), all other fields preserved |
| `wifi_disconnected` | `network.disconnected` | `type` ("wifi") |
| `bluetooth_connected` | `bluetooth.connected` | `device_name`, `device_address` |
| `bluetooth_disconnected` | `bluetooth.disconnected` | `device_name`, `device_address` |
| `location_changed` | `location.changed` | `latitude`, `longitude`, `accuracy_m`, `provider` |
| `notification_posted` | `notification.received` | `package`, `title`, `category` |
| `app_opened` | `app.opened` | `package`, `label` |
| `app_closed` | `app.closed` | `package`, `label` |

Unknown event types are logged and preserved — they never crash the system.

---

## Example Payloads

### Screen On

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "screen_on",
  "payload": {
    "method": "power_button"
  }
}
```

### Screen Off

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "screen_off",
  "payload": {
    "method": "timeout"
  }
}
```

### Charging Started

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "charging_started",
  "payload": {
    "level": 65,
    "method": "usb"
  }
}
```

### Charging Stopped

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "charging_stopped",
  "payload": {
    "level": 100
  }
}
```

### Battery Level Changed

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "battery_changed",
  "payload": {
    "level": 42,
    "is_charging": false
  }
}
```

### Wi-Fi Connected

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "wifi_connected",
  "payload": {
    "type": "wifi",
    "name": "HomeWiFi"
  }
}
```

> Normalized to `network.wifi.connected` with `payload.ssid` extracted from `name`. All extra fields (e.g. `bssid`, `rssi`) are preserved.

### Bluetooth Connected

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "bluetooth_connected",
  "payload": {
    "device_name": "AirPods",
    "device_address": "00:11:22:33:44:55"
  }
}
```

### Location Changed

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "location_changed",
  "payload": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy_m": 10.0,
    "provider": "gps"
  }
}
```

### Notification Received

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "notification_posted",
  "payload": {
    "package": "com.whatsapp",
    "title": "Alice",
    "category": "msg"
  }
}
```

### App Opened

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "app_opened",
  "payload": {
    "package": "com.whatsapp",
    "label": "WhatsApp"
  }
}
```

### App Closed

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "app_closed",
  "payload": {
    "package": "com.whatsapp",
    "label": "WhatsApp"
  }
}
```

---

## curl Examples

```bash
# Screen on
curl -X POST http://localhost:8080/activity/events \
  -H "Content-Type: application/json" \
  -d '{
    "source": "android",
    "collector": "macrodroid",
    "device": "pixel-8-pro",
    "type": "screen_on",
    "payload": {"method": "power_button"}
  }'

# Charging started
curl -X POST http://localhost:8080/activity/events \
  -H "Content-Type: application/json" \
  -d '{
    "source": "android",
    "collector": "macrodroid",
    "device": "pixel-8-pro",
    "type": "charging_started",
    "payload": {"level": 65, "method": "usb"}
  }'

# Notification posted
curl -X POST http://localhost:8080/activity/events \
  -H "Content-Type: application/json" \
  -d '{
    "source": "android",
    "collector": "macrodroid",
    "device": "pixel-8-pro",
    "type": "notification_posted",
    "payload": {"package": "com.whatsapp", "title": "Alice", "category": "msg"}
  }'
```

---

## Expected Responses

### Success (200)

```json
{
  "status": "accepted",
  "id": "evt_01jx2k4n8p3q5r7s9t",
  "timestamp": "2026-06-19T09:00:00.000Z",
  "version": 1
}
```

### Persistence Failure (500)

```json
{
  "status": "error",
  "message": "Failed to persist event",
  "id": "evt_01jx2k4n8p3q5r7s9t"
}
```

### Validation Failure (422)

Returned automatically by FastAPI/Pydantic when required fields are missing
or have wrong types.

---

## MacroDroid Configuration

### HTTP Request Action

In MacroDroid, create an **HTTP Request** action:

1. **Method:** `POST`
2. **URL:** `https://<your-domain>/activity/events` (or `http://<vps-ip>:8080/activity/events`)
3. **Content-Type:** `application/json`
4. **Body:** JSON payload (see examples above)

### MacroDroid Variable → JSON

MacroDroid variables can be embedded in the JSON body:

```json
{
  "source": "android",
  "collector": "macrodroid",
  "device": "pixel-8-pro",
  "type": "battery_changed",
  "payload": {
    "level": {v=battery_level},
    "is_charging": {v=charging}
  }
}
```

Replace `{v=battery_level}` and `{v=charging}` with MacroDroid's actual
variable syntax (varies by version — check MacroDroid documentation).

### Trigger → Action Mapping

| MacroDroid Trigger | Action: HTTP Request Body `type` |
|---|---|
| Screen On | `"screen_on"` |
| Screen Off | `"screen_off"` |
| Power Connected | `"charging_started"` |
| Power Disconnected | `"charging_stopped"` |
| Battery Level Change | `"battery_changed"` |
| Wi-Fi Connected | `"wifi_connected"` |
| Wi-Fi Disconnected | `"wifi_disconnected"` |
| Bluetooth Connected | `"bluetooth_connected"` |
| Bluetooth Disconnected | `"bluetooth_disconnected"` |
| Location Change | `"location_changed"` |
| Notification Received | `"notification_posted"` |
| Application Launched | `"app_opened"` |
| Application Closed | `"app_closed"` |

---

## Testing the Integration

### From your dev machine

```bash
# Start the Hub
cd mcp-hub
PYTHONPATH="src:.." uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

# Send a test event
curl -X POST http://localhost:8080/activity/events \
  -H "Content-Type: application/json" \
  -d '{"source":"android","collector":"macrodroid","device":"test-device","type":"screen_on","payload":{"method":"power_button"}}'
```

### Run the integration test suite

```bash
python -m pytest activity/tests/test_macrodroid_integration.py -v
# 30 tests — verifies every event type end-to-end
```

---

## Architecture Boundaries

| Layer | Knows about MacroDroid? | Responsibility |
|---|---|---|
| **Gateway** | No (source-agnostic) | HTTP ingest, validation, ULID |
| **Normalizer** | No (mapping table only) | Type mapping, payload normalization |
| **Storage** | No | SQLite persistence |
| **MacroDroid** | Yes (this document) | Sends properly formatted JSON |

The mapping table (`activity/normalizer/mappings.py`) is the only place
collector-specific names appear — and it's designed to be extended without
code changes.

---

## Related Documents

- `docs/activity/SCHEMA.md` — Event schema specification
- `docs/activity/NORMALIZER.md` — Normalization flow and mapping strategy
- `docs/activity/STORAGE.md` — SQLite persistence layer
- `ARCHITECTURE.md` — System architecture
- `README.md` — Project overview
