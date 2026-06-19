"""Unit tests for the Event Normalizer.

Covers:
    * screen_on  → screen.on
    * screen_off → screen.off
    * battery_low → battery.low
    * charging_started → battery.charging.started
    * unknown_event → unknown (with raw preservation)
    * Payload normalization
    * Raw preservation
    * app.opened / app.closed payload normalization
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the repo root is importable.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from activity.normalizer.service import normalize_event
from activity.normalizer.mappings import canonical_type, CANONICAL_UNKNOWN


# ── Helpers ─────────────────────────────────────────────────────────

def _make_event(**overrides) -> dict:
    """Build a minimal Gateway-style event for testing."""
    event = {
        "version": 1,
        "id": "evt_test1234abcd",
        "timestamp": "2026-06-19T09:00:00.000Z",
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "screen_on",
        "payload": {},
        "raw": {},
    }
    event.update(overrides)
    if not event["raw"]:
        event["raw"] = {
            "type": event["type"],
            "payload": event["payload"],
        }
    return event


# ── Canonical type mapping ──────────────────────────────────────────

def test_screen_on_maps_to_screen_on():
    """screen_on → screen.on"""
    event = _make_event(type="screen_on")
    result = normalize_event(event)
    assert result["type"] == "screen.on"


def test_screen_off_maps_to_screen_off():
    """screen_off → screen.off"""
    event = _make_event(type="screen_off")
    result = normalize_event(event)
    assert result["type"] == "screen.off"


def test_battery_low_maps_to_battery_low():
    """battery_low → battery.low"""
    event = _make_event(type="battery_low", payload={"level": 15})
    result = normalize_event(event)
    assert result["type"] == "battery.low"


def test_charging_started_maps_to_battery_charging_started():
    """charging_started → battery.charging.started"""
    event = _make_event(type="charging_started", payload={"level": 80, "method": "usb"})
    result = normalize_event(event)
    assert result["type"] == "battery.charging.started"


def test_unknown_event_marked_unknown():
    """An unmapped event type → unknown."""
    event = _make_event(type="some_bizarre_event", payload={"foo": "bar"})
    result = normalize_event(event)
    assert result["type"] == "unknown"


# ── Payload normalization ───────────────────────────────────────────

def test_battery_low_payload_normalized():
    """battery.low payload gets level:int + is_charging:bool."""
    event = _make_event(
        type="battery_low",
        payload={"level": 15, "is_charging": False},
    )
    result = normalize_event(event)
    assert result["payload"] == {"level": 15, "is_charging": False}


def test_battery_low_payload_defaults():
    """Missing fields get sensible defaults."""
    event = _make_event(type="battery_low", payload={})
    result = normalize_event(event)
    assert result["payload"] == {"level": 0, "is_charging": False}


def test_charging_started_payload_normalized():
    """battery.charging.started payload gets level + method."""
    event = _make_event(
        type="charging_started",
        payload={"level": 72, "method": "wireless"},
    )
    result = normalize_event(event)
    assert result["payload"] == {"level": 72, "method": "wireless"}


def test_charging_started_payload_defaults():
    """Missing method defaults to unknown."""
    event = _make_event(type="charging_started", payload={"level": 50})
    result = normalize_event(event)
    assert result["payload"] == {"level": 50, "method": "unknown"}


def test_screen_on_payload_normalized():
    """screen.on payload gets method field."""
    event = _make_event(
        type="screen_on",
        payload={"method": "power_button"},
    )
    result = normalize_event(event)
    assert result["payload"] == {"method": "power_button"}


def test_screen_off_payload_normalized():
    """screen.off payload gets method field."""
    event = _make_event(
        type="screen_off",
        payload={"method": "timeout"},
    )
    result = normalize_event(event)
    assert result["payload"] == {"method": "timeout"}


def test_app_opened_payload_normalized():
    """app.opened payload gets package + label."""
    event = _make_event(
        type="app_opened",
        payload={"package": "com.whatsapp", "label": "WhatsApp"},
    )
    result = normalize_event(event)
    assert result["type"] == "app.opened"
    assert result["payload"] == {"package": "com.whatsapp", "label": "WhatsApp"}


def test_app_closed_payload_normalized():
    """app.closed payload gets package + label."""
    event = _make_event(
        type="app_closed",
        payload={"package": "com.whatsapp", "label": "WhatsApp"},
    )
    result = normalize_event(event)
    assert result["type"] == "app.closed"
    assert result["payload"] == {"package": "com.whatsapp", "label": "WhatsApp"}


def test_app_opened_payload_defaults():
    """Missing package/label default to unknown."""
    event = _make_event(type="app_opened", payload={})
    result = normalize_event(event)
    assert result["payload"] == {"package": "unknown", "label": "unknown"}


# ── Raw preservation ────────────────────────────────────────────────

def test_raw_preserved_for_known_event():
    """The original event is preserved in raw after normalization."""
    original_raw = {"type": "screen_on", "action": "wake"}
    event = _make_event(type="screen_on", raw=original_raw)
    result = normalize_event(event)
    assert result["raw"] == original_raw
    assert result["type"] == "screen.on"


def test_raw_preserved_for_unknown_event():
    """Unknown events preserve the full original in raw."""
    original_raw = {
        "type": "some_bizarre_event",
        "foo": "bar",
        "baz": 42,
    }
    event = _make_event(type="some_bizarre_event", raw=original_raw)
    result = normalize_event(event)
    assert result["raw"] == original_raw
    assert result["type"] == "unknown"


def test_raw_auto_populated_when_empty():
    """If raw is empty/falsy, the normalizer populates it from the event."""
    event = {
        "version": 1,
        "id": "evt_test9999",
        "timestamp": "2026-06-19T09:00:00.000Z",
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "screen_on",
        "payload": {},
        "raw": {},
    }
    result = normalize_event(event)
    assert result["raw"]
    assert result["raw"]["type"] == "screen_on"
    assert result["raw"]["source"] == "android"
    assert result["raw"]["collector"] == "macrodroid"


# ── Immutability ────────────────────────────────────────────────────

def test_original_event_not_mutated():
    """The normalizer must never mutate the callers event dict."""
    event = _make_event(type="screen_on", payload={"method": "tap"})
    original = {
        "type": event["type"],
        "payload": dict(event["payload"]),
        "raw": dict(event["raw"]),
        "id": event["id"],
    }
    normalize_event(event)
    assert event["type"] == original["type"]
    assert event["payload"] == original["payload"]
    assert event["raw"] == original["raw"]
    assert event["id"] == original["id"]


# ── Canonical type constants ────────────────────────────────────────

def test_canonical_type_known():
    """canonical_type() returns the mapped canonical type."""
    assert canonical_type("screen_on") == "screen.on"
    assert canonical_type("screen_off") == "screen.off"
    assert canonical_type("battery_low") == "battery.low"
    assert canonical_type("charging_started") == "battery.charging.started"
    assert canonical_type("charging_stopped") == "battery.charging.stopped"
    assert canonical_type("app_opened") == "app.opened"
    assert canonical_type("app_closed") == "app.closed"


def test_canonical_type_unknown():
    """canonical_type() returns unknown for unmapped types."""
    assert canonical_type("nonexistent_event") == CANONICAL_UNKNOWN
    assert canonical_type("") == CANONICAL_UNKNOWN


# ── Identity mappings for already-canonical types ───────────────────

def test_device_awake_passes_through():
    """device.awake is an identity mapping (already canonical)."""
    assert canonical_type("device.awake") == "device.awake"


def test_device_sleep_passes_through():
    """device.sleep is an identity mapping (already canonical)."""
    assert canonical_type("device.sleep") == "device.sleep"


# ── Alternative collector names ─────────────────────────────────────

def test_display_on_alias():
    """display_on (Tasker-style) → device.awake"""
    event = _make_event(type="display_on", collector="tasker")
    result = normalize_event(event)
    assert result["type"] == "device.awake"


def test_power_connected_alias():
    """power_connected (Home Assistant-style) → battery.charging.started"""
    event = _make_event(
        type="power_connected",
        collector="home-assistant",
        payload={"level": 99},
    )
    result = normalize_event(event)
    assert result["type"] == "battery.charging.started"


# ── network.wifi.connected ─────────────────────────────────────────

def test_wifi_connected_maps_to_network_wifi_connected():
    """wifi_connected → network.wifi.connected"""
    event = _make_event(
        type="wifi_connected",
        payload={"type": "wifi", "name": "HomeWiFi"},
    )
    result = normalize_event(event)
    assert result["type"] == "network.wifi.connected"


def test_network_wifi_connected_payload_ssid_from_name():
    """MacroDroid sends name=SSID → normalized to ssid field."""
    event = _make_event(
        type="wifi_connected",
        payload={"type": "wifi", "name": "HomeWiFi"},
    )
    result = normalize_event(event)
    assert result["payload"]["ssid"] == "HomeWiFi"
    assert "name" not in result["payload"]


def test_network_wifi_connected_payload_ssid_direct():
    """If ssid is provided directly, it is kept as-is."""
    event = _make_event(
        type="wifi_connected",
        payload={"type": "wifi", "ssid": "MyNetwork"},
    )
    result = normalize_event(event)
    assert result["payload"]["ssid"] == "MyNetwork"


def test_network_wifi_connected_preserves_unknown_fields():
    """Unknown payload fields are never discarded."""
    event = _make_event(
        type="wifi_connected",
        payload={
            "type": "wifi",
            "name": "HomeWiFi",
            "bssid": "aa:bb:cc:dd:ee:ff",
            "rssi": -45,
        },
    )
    result = normalize_event(event)
    assert result["payload"]["ssid"] == "HomeWiFi"
    assert result["payload"]["bssid"] == "aa:bb:cc:dd:ee:ff"
    assert result["payload"]["rssi"] == -45
    assert result["payload"]["type"] == "wifi"


def test_network_wifi_connected_payload_default_ssid():
    """Missing ssid/name defaults to unknown."""
    event = _make_event(
        type="wifi_connected",
        payload={"type": "wifi"},
    )
    result = normalize_event(event)
    assert result["payload"]["ssid"] == "unknown"


def test_canonical_type_wifi_connected():
    """canonical_type() for wifi_connected → network.wifi.connected"""
    assert canonical_type("wifi_connected") == "network.wifi.connected"
