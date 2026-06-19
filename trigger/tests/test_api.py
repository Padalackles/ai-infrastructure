"""API integration tests for the Trigger endpoints.

Covers:
    * POST /trigger — creates a trigger, returns TriggerResponse
    * GET /trigger/pending — oldest pending + recent_activity
    * GET /trigger/pending — null when queue empty
    * POST /trigger/{id}/ack — marks acked, returns updated
    * POST /trigger/{id}/ack — 404 for nonexistent id
    * Pending only returns un-acked triggers after ack

Uses FastAPI TestClient with a temporary SQLite database.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from activity.storage.database import init_db, set_db_path


# ── Test App ────────────────────────────────────────────────────────


def _build_test_app(db_path: Path) -> FastAPI:
    """Create a FastAPI app with trigger router + activity router."""
    set_db_path(db_path)
    init_db(db_path)

    app = FastAPI()

    # Both routers needed because GET /trigger/pending uses ActivityService
    from activity.gateway.router import router as activity_router
    from trigger.router import router as trigger_router

    app.include_router(activity_router)
    app.include_router(trigger_router)
    return app


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def db_path() -> Path:
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_trigger_api_")
    os.close(fd)
    db_path = Path(path)
    yield db_path
    set_db_path(None)
    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.fixture
def client(db_path: Path) -> TestClient:
    """Return a TestClient wired to a temp-database app."""
    app = _build_test_app(db_path)
    return TestClient(app)


# ── Helpers ─────────────────────────────────────────────────────────


def _create_trigger(client: TestClient, **overrides) -> dict:
    """POST /trigger and return the parsed JSON body."""
    payload = {
        "type": "procrastination",
        "payload": {"app": "bilibili", "duration": 7200},
        "priority": 1,
    }
    payload.update(overrides)
    resp = client.post("/trigger", json=payload)
    return resp.status_code, resp.json()


def _assert_trigger_shape(trigger: dict, expected_type: str) -> None:
    """Verify a TriggerResponse has the correct shape."""
    assert trigger["id"].startswith("trg_"), f"Expected trg_ prefix, got {trigger['id']!r}"
    assert trigger["type"] == expected_type
    assert trigger["status"] == "pending"
    assert trigger["payload"] is not None
    assert "created_at" in trigger
    assert "T" in trigger["created_at"]
    assert trigger["acked_at"] is None


# ── POST /trigger ──────────────────────────────────────────────────


def test_create_trigger_defaults(client: TestClient):
    """POST /trigger with only 'type' creates a valid trigger with defaults."""
    resp = client.post("/trigger", json={"type": "focus"})
    assert resp.status_code == 200
    body = resp.json()
    _assert_trigger_shape(body, "focus")
    assert body["priority"] == 1
    assert body["payload"] == {}


def test_create_trigger_with_full_body(client: TestClient):
    """POST /trigger with all fields preserves them."""
    status, body = _create_trigger(
        client,
        type="procrastination",
        payload={"app": "bilibili", "duration": 7200},
        priority=0,
    )
    assert status == 200
    assert body["type"] == "procrastination"
    assert body["payload"] == {"app": "bilibili", "duration": 7200}
    assert body["priority"] == 0
    assert body["status"] == "pending"


def test_create_trigger_id_is_unique(client: TestClient):
    """Each trigger gets a unique time-sortable id."""
    ids = set()
    for _ in range(5):
        status, body = _create_trigger(client, type="test")
        assert status == 200
        ids.add(body["id"])
    assert len(ids) == 5


# ── GET /trigger/pending ───────────────────────────────────────────


def test_get_pending_empty_queue(client: TestClient):
    """When no triggers exist, returns trigger=null with recent_activity=[]."""
    resp = client.get("/trigger/pending")
    assert resp.status_code == 200
    body = resp.json()
    assert body["trigger"] is None
    assert body["recent_activity"] == []


def test_get_pending_returns_oldest(client: TestClient):
    """Returns the single pending trigger with correct shape."""
    status, created = _create_trigger(client, type="sleep")
    assert status == 200

    resp = client.get("/trigger/pending")
    assert resp.status_code == 200
    body = resp.json()
    assert body["trigger"] is not None
    assert body["trigger"]["id"] == created["id"]
    assert body["trigger"]["type"] == "sleep"
    assert body["recent_activity"] == []


def test_get_pending_respects_priority(client: TestClient):
    """Highest priority (0) is returned first regardless of creation order."""
    # Create low priority first (older)
    status1, low = _create_trigger(client, type="sleep", priority=2)
    assert status1 == 200
    # Create high priority second (newer)
    status2, high = _create_trigger(client, type="procrastination", priority=0)
    assert status2 == 200

    resp = client.get("/trigger/pending")
    body = resp.json()
    assert body["trigger"] is not None
    # Highest priority (lowest number) should be first
    assert body["trigger"]["id"] == high["id"]
    assert body["trigger"]["priority"] == 0


def test_get_pending_includes_recent_activity(client: TestClient):
    """recent_activity field contains events from the Activity subsystem."""
    # Seed an activity event
    activity_payload = {
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "screen_on",  # collector type → normalizer maps to device.awake
        "payload": {},
    }
    activity_resp = client.post("/activity/events", json=activity_payload)
    assert activity_resp.status_code == 200

    # Create a trigger
    _create_trigger(client, type="focus")

    # Pending should include the activity event
    resp = client.get("/trigger/pending")
    body = resp.json()
    assert body["trigger"] is not None
    assert len(body["recent_activity"]) >= 1
    activity_types = [e["type"] for e in body["recent_activity"]]
    assert "device.awake" in activity_types


# ── POST /trigger/{id}/ack ─────────────────────────────────────────


def test_ack_trigger_success(client: TestClient):
    """Ack marks the trigger as done."""
    status, created = _create_trigger(client, type="study")
    assert status == 200

    ack_resp = client.post(f"/trigger/{created['id']}/ack")
    assert ack_resp.status_code == 200
    acked = ack_resp.json()
    assert acked["id"] == created["id"]
    assert acked["status"] == "acked"
    assert acked["acked_at"] is not None
    assert "T" in acked["acked_at"]


def test_ack_nonexistent_returns_404(client: TestClient):
    """Acking a nonexistent id returns 404."""
    resp = client.post("/trigger/trg_ghost/ack")
    assert resp.status_code == 404
    body = resp.json()
    assert body["status"] == "not_found"


def test_acked_trigger_not_in_pending(client: TestClient):
    """After ack, GET /trigger/pending skips the acked trigger."""
    # Create two triggers
    _, first = _create_trigger(client, type="sleep", priority=2)
    _, second = _create_trigger(client, type="focus", priority=1)

    # Ack the higher-priority one (priority=1)
    client.post(f"/trigger/{second['id']}/ack")

    # Pending should now return the other one
    resp = client.get("/trigger/pending")
    body = resp.json()
    assert body["trigger"] is not None
    assert body["trigger"]["id"] == first["id"]
    assert body["trigger"]["status"] == "pending"


def test_ack_then_no_pending(client: TestClient):
    """After acking all triggers, pending returns null."""
    _, created = _create_trigger(client, type="focus")
    client.post(f"/trigger/{created['id']}/ack")

    resp = client.get("/trigger/pending")
    body = resp.json()
    assert body["trigger"] is None


# ── Edge cases ─────────────────────────────────────────────────────


def test_create_trigger_priority_out_of_range(client: TestClient):
    """Priority values outside [0, 2] are rejected by Pydantic validation."""
    resp = client.post("/trigger", json={"type": "test", "priority": 5})
    assert resp.status_code == 422  # validation error


def test_create_trigger_missing_type(client: TestClient):
    """Missing required 'type' field returns 422."""
    resp = client.post("/trigger", json={"payload": {}})
    assert resp.status_code == 422


def test_get_pending_consistent_shape(client: TestClient):
    """Response shape is identical whether trigger exists or not."""
    # Empty
    empty_resp = client.get("/trigger/pending")
    empty_body = empty_resp.json()
    assert "trigger" in empty_body
    assert "recent_activity" in empty_body

    # With trigger
    _create_trigger(client, type="focus")
    full_resp = client.get("/trigger/pending")
    full_body = full_resp.json()
    assert "trigger" in full_body
    assert "recent_activity" in full_body
    assert full_body["trigger"] is not None
