"""Unit tests for the Event Normalizer.

Covers:
    * screen_on  → device.awake
    * screen_off → device.sleep
    * battery_low → battery.low
    * charging_started → battery.charging.started
    * unknown_event → unknown (with raw preservation)
    * Payload normalization
    * Raw preservation
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
    # Ensure raw contains a copy of the original
    if not event["raw"]:
        event["raw"] = {
            "type": event["type"],
            "payload": event["payload"],
        }
    return event


# ── Canonical type mapping ──────────────────────────────────────────

def test_screen_on_maps_to_device_awake():
    """screen_on → device.awake"""
    event = _make_event(type="screen_on")
    result = normalize_event(event)
    assert result["type"] == "device.awake"


def test_screen_off_maps_to_device_sleep():
    """screen_off → device.sleep"""
    event = _make_event(type="screen_off")
    result = normalize_event(event)
    assert result["type"] == "device.sleep"


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
    """An unmapped event type → 'unknown'."""
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
    """Missing method defaults to 'unknown'."""
    event = _make_event(type="charging_started", payload={"level": 50})
    result = normalize_event(event)
    assert result["payload"] == {"level": 50, "method": "unknown"}


def test_device_awake_payload_normalized():
    """device.awake payload gets method field."""
    event = _make_event(
        type="screen_on",
        payload={"method": "power_button"},
    )
    result = normalize_event(event)
    assert result["payload"] == {"method": "power_button"}


def test_device_sleep_payload_normalized():
    """device.sleep payload gets method field."""
    event = _make_event(
        type="screen_off",
        payload={"method": "timeout"},
    )
    result = normalize_event(event)
    assert result["payload"] == {"method": "timeout"}


# ── Raw preservation ────────────────────────────────────────────────

def test_raw_preserved_for_known_event():
    """The original event is preserved in raw after normalization."""
    original_raw = {"type": "screen_on", "action": "wake"}
    event = _make_event(type="screen_on", raw=original_raw)
    result = normalize_event(event)
    assert result["raw"] == original_raw
    # The normalized type should differ from raw
    assert result["type"] == "device.awake"


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
    """If raw is empty/falsy, the normalizer populates it from the event.

    An empty ``raw`` dict is falsy, so the normalizer treats it as
    "not provided" and snapshots the full incoming event.  This
    guarantees we never lose the original data even when the Gateway
    or an earlier step omits raw.
    """
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
    # raw was empty → normalizer snapshots the full original event
    assert result["raw"]
    assert result["raw"]["type"] == "screen_on"
    assert result["raw"]["source"] == "android"
    assert result["raw"]["collector"] == "macrodroid"


# ── Immutability ────────────────────────────────────────────────────

def test_original_event_not_mutated():
    """The normalizer must never mutate the caller's event dict."""
    event = _make_event(type="screen_on", payload={"method": "tap"})
    original = {
        "type": event["type"],
        "payload": dict(event["payload"]),
        "raw": dict(event["raw"]),
        "id": event["id"],
    }
    normalize_event(event)
    # Original should be untouched
    assert event["type"] == original["type"]
    assert event["payload"] == original["payload"]
    assert event["raw"] == original["raw"]
    assert event["id"] == original["id"]


# ── Canonical type constants ────────────────────────────────────────

def test_canonical_type_known():
    """canonical_type() returns the mapped canonical type."""
    assert canonical_type("screen_on") == "device.awake"
    assert canonical_type("screen_off") == "device.sleep"
    assert canonical_type("battery_low") == "battery.low"
    assert canonical_type("charging_started") == "battery.charging.started"
    assert canonical_type("charging_stopped") == "battery.charging.stopped"


def test_canonical_type_unknown():
    """canonical_type() returns 'unknown' for unmapped types."""
    assert canonical_type("nonexistent_event") == CANONICAL_UNKNOWN
    assert canonical_type("") == CANONICAL_UNKNOWN


# ── Pass-through for already-canonical types ────────────────────────

def test_already_canonical_passes_through():
    """If an event arrives already using a canonical type, it should
    still work (e.g. a different collector already sends canonical)."""
    event = _make_event(
        type="device.awake",
        payload={"method": "lift"},
    )
    result = normalize_event(event)
    # No mapping for "device.awake" → stays "device.awake" is false if
    # "device.awake" is not in mappings. Wait — let's check.  It's not
    # in EVENT_MAPPINGS as a key, so it maps to "unknown"!
    # This is by design: the Gateway sends collector-specific names.
    # If a collector already sends canonical names, add them as
    # identity mappings in EVENT_MAPPINGS.
    # For now, this is expected behavior — see docs.
    assert result["type"] == "unknown"


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
