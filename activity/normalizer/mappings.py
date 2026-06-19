"""Event name mapping table.

Maps collector-specific event names (flat, snake_case) to
canonical event names (hierarchical dot-notation).

Extending for a new collector:
    Add entries to ``EVENT_MAPPINGS`` that map the collector's
    raw event names to the canonical equivalents below.

    If the collector uses a separator prefix (e.g. tasker_*),
    consider adding a per-collector dict and merging at lookup
    time.  The lookup function ``canonical_type()`` is the
    single extension point.

Canonical event types are defined in:
    activity/types.ts
    docs/activity/SCHEMA.md
"""

from __future__ import annotations

# ── Canonical event type constants ──────────────────────────────────
# Reused by service.py and tests to avoid string duplication.

CANONICAL_DEVICE_AWAKE = "device.awake"
CANONICAL_DEVICE_SLEEP = "device.sleep"
CANONICAL_DEVICE_BOOT = "device.boot"
CANONICAL_DEVICE_SHUTDOWN = "device.shutdown"

CANONICAL_BATTERY_LOW = "battery.low"
CANONICAL_BATTERY_FULL = "battery.full"
CANONICAL_BATTERY_CHARGING_STARTED = "battery.charging.started"
CANONICAL_BATTERY_CHARGING_STOPPED = "battery.charging.stopped"
CANONICAL_BATTERY_LEVEL_CHANGED = "battery.level_changed"

CANONICAL_APP_OPENED = "app.opened"
CANONICAL_APP_CLOSED = "app.closed"

CANONICAL_NETWORK_CONNECTED = "network.connected"
CANONICAL_NETWORK_DISCONNECTED = "network.disconnected"

CANONICAL_LOCATION_CHANGED = "location.changed"

CANONICAL_NOTIFICATION_RECEIVED = "notification.received"
CANONICAL_NOTIFICATION_DISMISSED = "notification.dismissed"

CANONICAL_CALL_STARTED = "call.started"
CANONICAL_CALL_ENDED = "call.ended"
CANONICAL_CALL_MISSED = "call.missed"

CANONICAL_SCREEN_ON = "screen.on"
CANONICAL_SCREEN_OFF = "screen.off"
CANONICAL_SCREEN_UNLOCKED = "screen.unlocked"

CANONICAL_SENSOR_READING = "sensor.reading"

CANONICAL_BLUETOOTH_CONNECTED = "bluetooth.connected"
CANONICAL_BLUETOOTH_DISCONNECTED = "bluetooth.disconnected"

CANONICAL_WIFI_CONNECTED = "wifi.connected"
CANONICAL_WIFI_DISCONNECTED = "wifi.disconnected"

CANONICAL_SCHEDULE_TRIGGERED = "schedule.triggered"

# Sentinel for unmapped event types.
CANONICAL_UNKNOWN = "unknown"


# ── Master mapping table ────────────────────────────────────────────
#
# Keys   → collector-specific event names (snake_case).
# Values → canonical event names (dot-notation).
#
# Both direct aliases and semantic mappings live here.  For example,
# ``screen_on`` could come from MacroDroid while ``display_on`` might
# come from Tasker — both map to ``device.awake``.

EVENT_MAPPINGS: dict[str, str] = {
    # ── Device ──────────────────────────────────────────────────
    "screen_on": CANONICAL_DEVICE_AWAKE,
    "screen_off": CANONICAL_DEVICE_SLEEP,
    "device_boot": CANONICAL_DEVICE_BOOT,
    "device_shutdown": CANONICAL_DEVICE_SHUTDOWN,
    # Alternative collector names (Tasker / Home Assistant style)
    "display_on": CANONICAL_DEVICE_AWAKE,
    "display_off": CANONICAL_DEVICE_SLEEP,
    "device_on": CANONICAL_DEVICE_AWAKE,
    "device_off": CANONICAL_DEVICE_SLEEP,
    # ── Battery ─────────────────────────────────────────────────
    "battery_low": CANONICAL_BATTERY_LOW,
    "battery_full": CANONICAL_BATTERY_FULL,
    "charging_started": CANONICAL_BATTERY_CHARGING_STARTED,
    "charging_stopped": CANONICAL_BATTERY_CHARGING_STOPPED,
    "battery_level_changed": CANONICAL_BATTERY_LEVEL_CHANGED,
    "battery_changed": CANONICAL_BATTERY_LEVEL_CHANGED,
    # Alternative names
    "power_connected": CANONICAL_BATTERY_CHARGING_STARTED,
    "power_disconnected": CANONICAL_BATTERY_CHARGING_STOPPED,
    # ── App ─────────────────────────────────────────────────────
    "app_opened": CANONICAL_APP_OPENED,
    "app_closed": CANONICAL_APP_CLOSED,
    # ── Network ─────────────────────────────────────────────────
    "network_connected": CANONICAL_NETWORK_CONNECTED,
    "network_disconnected": CANONICAL_NETWORK_DISCONNECTED,
    "wifi_connected": CANONICAL_NETWORK_CONNECTED,
    "wifi_disconnected": CANONICAL_NETWORK_DISCONNECTED,
    # ── Location ────────────────────────────────────────────────
    "location_changed": CANONICAL_LOCATION_CHANGED,
    # ── Notification ────────────────────────────────────────────
    "notification_received": CANONICAL_NOTIFICATION_RECEIVED,
    "notification_posted": CANONICAL_NOTIFICATION_RECEIVED,
    "notification_dismissed": CANONICAL_NOTIFICATION_DISMISSED,
    # ── Call ────────────────────────────────────────────────────
    "call_started": CANONICAL_CALL_STARTED,
    "call_ended": CANONICAL_CALL_ENDED,
    "call_missed": CANONICAL_CALL_MISSED,
    # ── Screen (direct pass-through; also mapped via device.*) ──
    "screen_on_direct": CANONICAL_SCREEN_ON,
    "screen_off_direct": CANONICAL_SCREEN_OFF,
    "screen_unlocked": CANONICAL_SCREEN_UNLOCKED,
    # ── Sensor ──────────────────────────────────────────────────
    "sensor_reading": CANONICAL_SENSOR_READING,
    # ── Bluetooth ───────────────────────────────────────────────
    "bluetooth_connected": CANONICAL_BLUETOOTH_CONNECTED,
    "bluetooth_disconnected": CANONICAL_BLUETOOTH_DISCONNECTED,
    # ── Wi-Fi ───────────────────────────────────────────────────
    "wifi_connected_direct": CANONICAL_WIFI_CONNECTED,
    "wifi_disconnected_direct": CANONICAL_WIFI_DISCONNECTED,
    # ── Schedule ────────────────────────────────────────────────
    "schedule_triggered": CANONICAL_SCHEDULE_TRIGGERED,
}


def canonical_type(raw_type: str) -> str:
    """Resolve a collector-specific event name to its canonical form.

    Returns ``CANONICAL_UNKNOWN`` ("unknown") when no mapping exists.
    Callers should log unknown types for debugging.
    """
    return EVENT_MAPPINGS.get(raw_type, CANONICAL_UNKNOWN)
