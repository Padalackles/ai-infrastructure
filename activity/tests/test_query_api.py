"""API integration tests for Activity query endpoints.

Verifies the GET endpoints return correct responses:
    GET /activity/recent
    GET /activity/latest
    GET /activity/history
    GET /activity/types

Uses FastAPI TestClient with a temporary database.
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
from activity.storage.repository import ActivityRepository


def _build_test_app(db_path: Path) -> FastAPI:
    """Create a FastAPI app wired to a temporary database."""
    set_db_path(db_path)
    init_db(db_path)

    app = FastAPI()
    from activity.gateway.router import router as activity_router

    app.include_router(activity_router)
    return app


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def db_path() -> Path:
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_api_")
    os.close(fd)
    return Path(path)


@pytest.fixture
def client(db_path: Path) -> TestClient:
    app = _build_test_app(db_path)
    return TestClient(app)


@pytest.fixture
def repo(db_path: Path) -> ActivityRepository:
    return ActivityRepository(db_path=db_path)


# ── Helpers ─────────────────────────────────────────────────────────


def _seed_event(repo: ActivityRepository, **overrides) -> dict:
    """Save a test event and return its dict."""
    event = {
        "version": 1,
        "id": f"evt_api_{overrides.get('id_suffix', '000')}",
        "timestamp": "2026-06-19T09:00:00.000Z",
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "device.awake",
        "payload": {},
        "raw": {},
    }
    event.update(overrides)
    event.pop("id_suffix", None)
    repo.save_event(event)
    return event


# ── GET /activity/recent ────────────────────────────────────────────


def test_recent_returns_events(client: TestClient, repo: ActivityRepository):
    """GET /activity/recent returns recently stored events."""
    _seed_event(repo, id="evt_r1", type="device.awake")
    _seed_event(repo, id="evt_r2", type="device.sleep")

    resp = client.get("/activity/recent?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_recent_respects_limit(client: TestClient, repo: ActivityRepository):
    """GET /activity/recent?limit=N returns at most N events."""
    for i in range(5):
        _seed_event(repo, id=f"evt_rl_{i:03d}")

    resp = client.get("/activity/recent?limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_recent_empty_database(client: TestClient):
    """GET /activity/recent returns [] when no events exist."""
    resp = client.get("/activity/recent")
    assert resp.status_code == 200
    assert resp.json() == []


# ── GET /activity/latest ───────────────────────────────────────────


def test_latest_returns_most_recent_of_type(
    client: TestClient, repo: ActivityRepository
):
    """GET /activity/latest?type=... returns the newest matching event."""
    _seed_event(repo, id="evt_la", type="device.awake",
                timestamp="2026-06-19T08:00:00.000Z")
    _seed_event(repo, id="evt_lb", type="device.awake",
                timestamp="2026-06-19T09:00:00.000Z")

    resp = client.get("/activity/latest?type=device.awake")
    assert resp.status_code == 200
    assert resp.json()["id"] == "evt_lb"


def test_latest_returns_404_for_unknown_type(client: TestClient):
    """GET /activity/latest?type=unknown returns 404."""
    resp = client.get("/activity/latest?type=nonexistent.type")
    assert resp.status_code == 404
    assert resp.json()["status"] == "not_found"


# ── GET /activity/history ──────────────────────────────────────────


def test_history_returns_events_in_range(
    client: TestClient, repo: ActivityRepository
):
    """GET /activity/history returns events with timestamp in [start, end]."""
    _seed_event(repo, id="evt_h1", timestamp="2026-06-19T01:00:00.000Z")
    _seed_event(repo, id="evt_h2", timestamp="2026-06-19T02:00:00.000Z")
    _seed_event(repo, id="evt_h3", timestamp="2026-06-19T03:00:00.000Z")

    resp = client.get(
        "/activity/history",
        params={
            "start": "2026-06-19T01:30:00.000Z",
            "end": "2026-06-19T02:30:00.000Z",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "evt_h2"


def test_history_empty_when_no_matches(client: TestClient):
    """GET /activity/history returns [] when no events in range."""
    resp = client.get(
        "/activity/history",
        params={
            "start": "2026-01-01T00:00:00.000Z",
            "end": "2026-01-02T00:00:00.000Z",
        },
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_requires_start_and_end(client: TestClient):
    """GET /activity/history without required params returns 422."""
    resp = client.get("/activity/history")
    assert resp.status_code == 422  # FastAPI validation error


# ── GET /activity/types ────────────────────────────────────────────


def test_types_returns_distinct_types(
    client: TestClient, repo: ActivityRepository
):
    """GET /activity/types returns distinct, sorted canonical types."""
    _seed_event(repo, id="evt_ty_a", type="device.awake")
    _seed_event(repo, id="evt_ty_b", type="app.opened")
    _seed_event(repo, id="evt_ty_c", type="device.awake")  # duplicate

    resp = client.get("/activity/types")
    assert resp.status_code == 200
    data = resp.json()
    assert data == ["app.opened", "device.awake"]


def test_types_empty_database(client: TestClient):
    """GET /activity/types returns [] when no events exist."""
    resp = client.get("/activity/types")
    assert resp.status_code == 200
    assert resp.json() == []


# ── Regression: POST still works ────────────────────────────────────


def test_post_event_still_works_alongside_get_endpoints(
    client: TestClient, repo: ActivityRepository
):
    """POST /activity/events works alongside the new GET endpoints."""
    resp = client.post("/activity/events", json={
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "screen_on",
        "payload": {},
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    # Verify it appears in GET /activity/recent
    recent = client.get("/activity/recent?limit=1")
    assert recent.status_code == 200
    assert len(recent.json()) == 1
    assert recent.json()[0]["type"] == "device.awake"
