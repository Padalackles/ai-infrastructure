"""MacroDroid Integration Tests — end-to-end pipeline verification.

Simulates MacroDroid HTTP POST requests and verifies the full pipeline:

    MacroDroid JSON → Gateway → Normalizer → SQLite

Each test:
  1. Builds a realistic MacroDroid-style JSON payload.
  2. POSTs it to /activity/events via FastAPI TestClient.
  3. Asserts HTTP 200 + "accepted" status.
  4. Queries the database to confirm the canonical event exists.

Uses a temporary SQLite database — never touches production data.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure the repo root is importable.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from activity.storage.database import get_db_path, init_db, set_db_path
from activity.storage.repository import ActivityRepository


# ── Test App ─────────────────────────────────────────────────────────
#
# A minimal FastAPI app that includes only the Activity router.
# This keeps tests fast and isolated — no MCP Hub, no lifecycle,
# no service discovery.


def _build_test_app(db_path: Path) -> FastAPI:
    """Create a FastAPI app wired to a temporary database."""
    set_db_path(db_path)
    init_db(db_path)

    app = FastAPI()
    from activity.gateway.router import router as activity_router

    app.include_router(activity_router)
    return app


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def db_path() -> Path:
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_macrodroid_")
    os.close(fd)
    return Path(path)


@pytest.fixture
def client(db_path: Path) -> TestClient:
    """Return a TestClient wired to a temp-database app."""
    app = _build_test_app(db_path)
    return TestClient(app)


@pytest.fixture
def repo(db_path: Path) -> ActivityRepository:
    """Return a repository pointing at the temp database."""
    return ActivityRepository(db_path=db_path)


# ── Helpers ─────────────────────────────────────────────────────────


def _post(client: TestClient, payload: dict) -> dict:
    """POST a MacroDroid-style event and return the parsed JSON response."""
    resp = client.post("/activity/events", json=payload)
    return resp.status_code, resp.json()


def _assert_accepted(status_code: int, body: dict) -> None:
    """Verify the Gateway returned a success response."""
    assert status_code == 200, f"Expected 200, got {status_code}: {body}"
    assert body["status"] == "accepted"
    assert body["id"].startswith("evt_"), f"Expected evt_ prefix, got {body['id']!r}"
    assert "timestamp" in body
    assert body["version"] == 1


def _assert_persisted(repo: ActivityRepository, event_id: str, canonical_type: str) -> dict:
    """Fetch the event from SQLite and verify the canonical type."""
    event = repo.get_event(event_id)
    assert event is not None, f"Event {event_id} was not persisted"
    assert event["type"] == canonical_type, (
        f"Expected canonical type {canonical_type!r}, got {event['type']!r}"
    )
    return event


# ── Device Events ────────────────────────────────────────────────────


def test_screen_on_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid screen_on → device.awake → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "screen_on",
            "payload": {"method": "power_button"},
        },
    )
    _assert_accepted(status, body)
    event = _assert_persisted(repo, body["id"], "device.awake")
    assert event["payload"] == {"method": "power_button"}
    assert event["source"] == "android"
    assert event["collector"] == "macrodroid"
    assert event["device"] == "pixel-8-pro"


def test_screen_off_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid screen_off → device.sleep → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "screen_off",
            "payload": {"method": "power_button"},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "device.sleep")


# ── Battery Events ───────────────────────────────────────────────────


def test_charging_started_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid charging_started → battery.charging.started → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "charging_started",
            "payload": {"level": 72, "method": "usb"},
        },
    )
    _assert_accepted(status, body)
    event = _assert_persisted(repo, body["id"], "battery.charging.started")
    assert event["payload"]["level"] == 72
    assert event["payload"]["method"] == "usb"


def test_charging_stopped_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid charging_stopped → battery.charging.stopped → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "charging_stopped",
            "payload": {"level": 100},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "battery.charging.stopped")


def test_battery_changed_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid battery_changed → battery.level_changed → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "battery_changed",
            "payload": {"level": 85, "is_charging": False},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "battery.level_changed")


# ── Network Events ───────────────────────────────────────────────────


def test_wifi_connected_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid wifi_connected → network.wifi.connected → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "wifi_connected",
            "payload": {"type": "wifi", "name": "HomeWiFi"},
        },
    )
    _assert_accepted(status, body)
    event = _assert_persisted(repo, body["id"], "network.wifi.connected")
    assert event["payload"]["ssid"] == "HomeWiFi"


def test_wifi_disconnected_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid wifi_disconnected → network.disconnected → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "wifi_disconnected",
            "payload": {"type": "wifi"},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "network.disconnected")


# ── Bluetooth Events ─────────────────────────────────────────────────


def test_bluetooth_connected_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid bluetooth_connected → bluetooth.connected → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "bluetooth_connected",
            "payload": {"device_name": "AirPods", "device_address": "00:11:22:33:44:55"},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "bluetooth.connected")


def test_bluetooth_disconnected_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid bluetooth_disconnected → bluetooth.disconnected → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "bluetooth_disconnected",
            "payload": {"device_name": "AirPods", "device_address": "00:11:22:33:44:55"},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "bluetooth.disconnected")


# ── Location Events ──────────────────────────────────────────────────


def test_location_changed_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid location_changed → location.changed → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "location_changed",
            "payload": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "accuracy_m": 10.0,
                "provider": "gps",
            },
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "location.changed")


# ── Notification Events ──────────────────────────────────────────────


def test_notification_posted_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid notification_posted → notification.received → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "notification_posted",
            "payload": {
                "package": "com.whatsapp",
                "title": "Alice",
                "category": "msg",
            },
        },
    )
    _assert_accepted(status, body)
    event = _assert_persisted(repo, body["id"], "notification.received")
    assert event["payload"]["package"] == "com.whatsapp"


# ── App Events ───────────────────────────────────────────────────────


def test_app_opened_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid app_opened → app.opened → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "app_opened",
            "payload": {"package": "com.whatsapp", "label": "WhatsApp"},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "app.opened")


def test_app_closed_event(client: TestClient, repo: ActivityRepository):
    """MacroDroid app_closed → app.closed → persisted."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "app_closed",
            "payload": {"package": "com.whatsapp", "label": "WhatsApp"},
        },
    )
    _assert_accepted(status, body)
    _assert_persisted(repo, body["id"], "app.closed")


# ── Raw Preservation ─────────────────────────────────────────────────


def test_raw_preserves_macrodroid_original(client: TestClient, repo: ActivityRepository):
    """The raw field preserves the exact MacroDroid JSON that was sent."""
    payload = {
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "screen_on",
        "payload": {"method": "lift"},
    }
    status, body = _post(client, payload)
    _assert_accepted(status, body)

    event = repo.get_event(body["id"])
    assert event is not None
    assert "raw" in event
    raw = event["raw"]
    # The raw field should contain the collector's original perspective
    assert raw["type"] == "screen_on"


# ── ID and Timestamp Generation ──────────────────────────────────────


def test_gateway_generates_unique_ids(client: TestClient, repo: ActivityRepository):
    """Each event gets a unique, server-generated ULID."""
    ids = set()
    for i in range(5):
        _, body = _post(
            client,
            {
                "source": "android",
                "collector": "macrodroid",
                "device": "pixel-8-pro",
                "type": "screen_on",
                "payload": {"method": "tap"},
            },
        )
        ids.add(body["id"])
    assert len(ids) == 5, "All 5 events should have unique IDs"


def test_gateway_assigns_timestamp_when_omitted(client: TestClient, repo: ActivityRepository):
    """When no timestamp is sent, the Gateway assigns one."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "screen_on",
            "payload": {},
        },
    )
    _assert_accepted(status, body)
    event = repo.get_event(body["id"])
    assert event is not None
    # Verify ISO 8601 timestamp was assigned
    assert "T" in event["timestamp"]
    assert "Z" in event["timestamp"] or "+" in event["timestamp"] or "-" in event["timestamp"][10:]


# ── End-to-End Pipeline Verification ─────────────────────────────────
#
# The definitive test: simulate every MacroDroid event type, POST it,
# and confirm it's persisted with the correct canonical type.


_MACRODROID_EVENT_TYPES = [
    # (macro_type, payload, canonical_type)
    ("screen_on", {"method": "power_button"}, "device.awake"),
    ("screen_off", {"method": "timeout"}, "device.sleep"),
    ("charging_started", {"level": 65, "method": "usb"}, "battery.charging.started"),
    ("charging_stopped", {"level": 100}, "battery.charging.stopped"),
    ("battery_changed", {"level": 42, "is_charging": False}, "battery.level_changed"),
    ("wifi_connected", {"type": "wifi", "name": "HomeWiFi"}, "network.wifi.connected"),
    ("wifi_disconnected", {"type": "wifi"}, "network.disconnected"),
    ("bluetooth_connected", {"device_name": "AirPods", "device_address": "00:11:22:33:44:55"}, "bluetooth.connected"),
    ("bluetooth_disconnected", {"device_name": "AirPods", "device_address": "00:11:22:33:44:55"}, "bluetooth.disconnected"),
    ("location_changed", {"latitude": 37.7749, "longitude": -122.4194, "accuracy_m": 10.0, "provider": "gps"}, "location.changed"),
    ("notification_posted", {"package": "com.whatsapp", "title": "Alice", "category": "msg"}, "notification.received"),
    ("app_opened", {"package": "com.whatsapp", "label": "WhatsApp"}, "app.opened"),
    ("app_closed", {"package": "com.whatsapp", "label": "WhatsApp"}, "app.closed"),
]


@pytest.mark.parametrize("macro_type,payload,canonical_type", _MACRODROID_EVENT_TYPES)
def test_full_pipeline_macrodroid_to_sqlite(
    client: TestClient,
    repo: ActivityRepository,
    macro_type: str,
    payload: dict,
    canonical_type: str,
):
    """Every MacroDroid event type → normalizes → persists with canonical type."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": macro_type,
            "payload": payload,
        },
    )
    _assert_accepted(status, body)
    event = _assert_persisted(repo, body["id"], canonical_type)
    assert event["source"] == "android"
    assert event["collector"] == "macrodroid"
    assert event["raw"]  # raw must always be present


# ── Buffer-only MacroDroid payload ───────────────────────────────────
#
# MacroDroid may send a flat payload without wrapping it in a Gateway
# envelope.  The Gateway's Pydantic models expect the envelope; but
# a bare JSON like {"event":"screen_on","level":15} should still be
# accepted if the required Gateway fields are present.


def test_minimal_macrodroid_payload(client: TestClient, repo: ActivityRepository):
    """Only the 5 required Gateway fields — no optional fields."""
    status, body = _post(
        client,
        {
            "source": "android",
            "collector": "macrodroid",
            "device": "pixel-8-pro",
            "type": "charging_started",
            "payload": {"level": 50},
        },
    )
    _assert_accepted(status, body)
    event = repo.get_event(body["id"])
    assert event is not None
    # Gateway should have filled in defaults
    assert event["version"] == 1
    assert event["id"].startswith("evt_")
    assert "T" in event["timestamp"]
