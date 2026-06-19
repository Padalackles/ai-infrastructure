"""Event Normalizer — service logic.

Pure functions that transform a Gateway-assembled Activity Event
into its canonical form.  No side effects — logging happens in
the caller (router layer).

Design:
    * ``normalize_event()`` is the single entry point.
    * Type mapping via ``mappings.canonical_type()``.
    * Payload normalization per event type (extensible).
    * ``raw`` is always preserved.
    * Unknown types are logged and marked, never rejected.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from .mappings import CANONICAL_UNKNOWN, canonical_type

logger = logging.getLogger("mcp-hub.activity.normalizer")


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Gateway-assembled Activity Event.

    Steps:
        1. Deep-copy the event so the original is never mutated.
        2. Map the collector-specific type to a canonical type.
        3. Normalize the payload structure per canonical type.
        4. Preserve the original event in ``raw``.
        5. Log unknown event types as warnings.

    Returns a new dict — the caller's input is untouched.
    """
    normalized = deepcopy(event)

    raw_type = normalized.get("type", "")
    resolved = canonical_type(raw_type)

    if resolved == CANONICAL_UNKNOWN:
        logger.warning(
            "Unknown event type %r from collector %r (device %r). "
            "Event preserved in raw; type set to 'unknown'.",
            raw_type,
            normalized.get("collector", "?"),
            normalized.get("device", "?"),
        )

    # ── Apply type mapping ──────────────────────────────────────
    normalized["type"] = resolved

    # ── Normalize payload ───────────────────────────────────────
    normalized["payload"] = _normalize_payload(resolved, normalized.get("payload", {}))

    # ── Preserve original event in raw ──────────────────────────
    # The Gateway already sets `raw`, but we ensure it's present.
    if not normalized.get("raw"):
        normalized["raw"] = deepcopy(event)

    return normalized


# ── Payload normalizers ─────────────────────────────────────────────
#
# Each function receives the collector's ``payload`` dict and returns
# a normalized payload dict conforming to the canonical sub-schema.
#
# Add new normalizers here as new event types are introduced.  The
# dispatcher ``_normalize_payload()`` routes by canonical type.


def _normalize_payload(canonical: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch payload normalization by canonical type.

    Unknown types pass through unchanged — we preserve whatever the
    collector sent.  Specific normalizers validate and coerce fields.
    """
    normalizer = _PAYLOAD_NORMALIZERS.get(canonical)
    if normalizer is not None:
        return normalizer(payload)
    # Unknown / pass-through: return as-is.
    return payload


# ── Per-type normalizers ────────────────────────────────────────────


def _norm_device_awake(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize device.awake payload."""
    return {
        "method": _str_field(payload, "method", "unknown"),
    }


def _norm_device_sleep(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize device.sleep payload."""
    return {
        "method": _str_field(payload, "method", "unknown"),
    }


def _norm_screen_on(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize screen.on payload."""
    return {
        "method": _str_field(payload, "method", "unknown"),
    }


def _norm_screen_off(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize screen.off payload."""
    return {
        "method": _str_field(payload, "method", "unknown"),
    }


def _norm_app_opened(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize app.opened payload."""
    return {
        "package": _str_field(payload, "package", "unknown"),
        "label": _str_field(payload, "label", "unknown"),
    }


def _norm_app_closed(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize app.closed payload."""
    return {
        "package": _str_field(payload, "package", "unknown"),
        "label": _str_field(payload, "label", "unknown"),
    }


def _norm_battery_low(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize battery.low payload."""
    return {
        "level": _int_field(payload, "level", 0),
        "is_charging": _bool_field(payload, "is_charging", False),
    }


def _norm_battery_charging_started(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize battery.charging.started payload."""
    return {
        "level": _int_field(payload, "level", 0),
        "method": _str_field(payload, "method", "unknown"),
    }


def _norm_battery_charging_stopped(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize battery.charging.stopped payload."""
    return {
        "level": _int_field(payload, "level", 0),
    }


def _norm_network_wifi_connected(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize network.wifi.connected payload.

    Extracts ``ssid`` from the collector's payload.  MacroDroid uses
    ``name`` for the SSID; other collectors may use ``ssid`` directly.
    Unknown fields are preserved — nothing is discarded.
    """
    result = dict(payload)  # preserve all existing fields
    # Normalize ssid: prefer explicit ssid, fall back to name (MacroDroid)
    if "ssid" not in result:
        if "name" in result:
            result["ssid"] = result.pop("name")
        else:
            result["ssid"] = "unknown"
    # Ensure ssid is a string
    if not isinstance(result.get("ssid"), str):
        result["ssid"] = "unknown"
    return result


# ── Mapping from canonical type → payload normalizer ────────────────

_PAYLOAD_NORMALIZERS: dict[str, Any] = {
    "device.awake": _norm_device_awake,
    "device.sleep": _norm_device_sleep,
    "screen.on": _norm_screen_on,
    "screen.off": _norm_screen_off,
    "app.opened": _norm_app_opened,
    "app.closed": _norm_app_closed,
    "battery.low": _norm_battery_low,
    "battery.charging.started": _norm_battery_charging_started,
    "battery.charging.stopped": _norm_battery_charging_stopped,
    "network.wifi.connected": _norm_network_wifi_connected,
    # Additional normalizers are added here as new event types are
    # introduced.  Types without an entry pass through unchanged.
}


# ── Helpers ─────────────────────────────────────────────────────────


def _str_field(d: dict[str, Any], key: str, default: str) -> str:
    """Extract a string field, falling back to *default*."""
    val = d.get(key, default)
    if not isinstance(val, str):
        return default
    return val


def _int_field(d: dict[str, Any], key: str, default: int) -> int:
    """Extract an integer field, falling back to *default*."""
    val = d.get(key, default)
    if not isinstance(val, (int, float)):
        return default
    return int(val)


def _bool_field(d: dict[str, Any], key: str, default: bool) -> bool:
    """Extract a boolean field, falling back to *default*."""
    val = d.get(key, default)
    if not isinstance(val, bool):
        return default
    return val
