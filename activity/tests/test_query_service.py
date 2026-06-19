"""Unit tests for the ActivityService query layer.

Verifies the Service correctly delegates to the repository,
handles edge cases (empty types, clamping), and returns
proper results.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from activity.storage.database import init_db, set_db_path
from activity.storage.repository import ActivityRepository
from activity.service import ActivityService


# ── Helpers ─────────────────────────────────────────────────────────


def _make_event(**overrides) -> dict:
    event = {
        "version": 1,
        "id": "evt_svc_test",
        "timestamp": "2026-06-19T09:00:00.000Z",
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "device.awake",
        "payload": {},
        "raw": {},
    }
    event.update(overrides)
    return event


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def repo() -> ActivityRepository:
    """Repository backed by a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_svc_")
    os.close(fd)
    db_path = Path(path)
    set_db_path(db_path)
    init_db(db_path)
    r = ActivityRepository(db_path=db_path)
    yield r
    set_db_path(None)
    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.fixture
def service(repo: ActivityRepository) -> ActivityService:
    """Service wrapping a temp-database repository."""
    return ActivityService(repo)


# ── get_recent ──────────────────────────────────────────────────────


def test_get_recent_returns_events(service: ActivityService, repo: ActivityRepository):
    """get_recent() returns the most recent events."""
    for i in range(3):
        repo.save_event(_make_event(id=f"evt_rec_{i:03d}"))

    results = service.get_recent(limit=10)
    assert len(results) == 3


def test_get_recent_empty_when_no_events(service: ActivityService):
    """get_recent() returns [] when the database is empty."""
    results = service.get_recent()
    assert results == []


def test_get_recent_respects_limit(service: ActivityService, repo: ActivityRepository):
    """get_recent(limit=N) returns at most N results."""
    for i in range(5):
        repo.save_event(_make_event(id=f"evt_rl_{i:03d}"))

    results = service.get_recent(limit=2)
    assert len(results) == 2


# ── get_latest ──────────────────────────────────────────────────────


def test_get_latest_returns_most_recent(service: ActivityService, repo: ActivityRepository):
    """get_latest() returns the newest event of the given type."""
    repo.save_event(_make_event(
        id="evt_lat_1", type="device.awake",
        timestamp="2026-06-19T08:00:00.000Z",
    ))
    repo.save_event(_make_event(
        id="evt_lat_2", type="device.awake",
        timestamp="2026-06-19T09:00:00.000Z",
    ))

    latest = service.get_latest("device.awake")
    assert latest is not None
    assert latest["id"] == "evt_lat_2"


def test_get_latest_returns_none_for_missing(service: ActivityService):
    """get_latest() returns None when type doesn't exist."""
    assert service.get_latest("nonexistent.type") is None


def test_get_latest_rejects_empty_type(service: ActivityService):
    """get_latest() returns None for empty/blank type strings."""
    assert service.get_latest("") is None
    assert service.get_latest("   ") is None


# ── get_between ─────────────────────────────────────────────────────


def test_get_between_returns_range(service: ActivityService, repo: ActivityRepository):
    """get_between() returns events within [start, end]."""
    repo.save_event(_make_event(
        id="evt_01", timestamp="2026-06-19T01:00:00.000Z",
    ))
    repo.save_event(_make_event(
        id="evt_02", timestamp="2026-06-19T02:00:00.000Z",
    ))
    repo.save_event(_make_event(
        id="evt_03", timestamp="2026-06-19T03:00:00.000Z",
    ))

    results = service.get_between(
        start="2026-06-19T01:30:00.000Z",
        end="2026-06-19T02:30:00.000Z",
    )
    assert len(results) == 1
    assert results[0]["id"] == "evt_02"


def test_get_between_empty(service: ActivityService):
    """get_between() returns [] when no events match."""
    results = service.get_between(
        start="2026-01-01T00:00:00.000Z",
        end="2026-01-02T00:00:00.000Z",
    )
    assert results == []


# ── get_by_type ─────────────────────────────────────────────────────


def test_get_by_type_returns_matching(service: ActivityService, repo: ActivityRepository):
    """get_by_type() returns only events of the given type."""
    repo.save_event(_make_event(id="evt_gbt_a", type="device.awake"))
    repo.save_event(_make_event(id="evt_gbt_b", type="app.opened"))
    repo.save_event(_make_event(id="evt_gbt_c", type="device.awake"))

    results = service.get_by_type("device.awake")
    assert len(results) == 2
    assert all(r["type"] == "device.awake" for r in results)


def test_get_by_type_empty_for_unknown(service: ActivityService):
    """get_by_type() returns [] for an unknown type."""
    results = service.get_by_type("nonexistent.type")
    assert results == []


def test_get_by_type_rejects_empty_type(service: ActivityService):
    """get_by_type() returns [] for empty/blank type strings."""
    assert service.get_by_type("") == []
    assert service.get_by_type("   ") == []


# ── list_types ──────────────────────────────────────────────────────


def test_list_types_returns_distinct(service: ActivityService, repo: ActivityRepository):
    """list_types() returns distinct canonical types."""
    repo.save_event(_make_event(id="evt_lt_a", type="device.awake"))
    repo.save_event(_make_event(id="evt_lt_b", type="app.opened"))
    repo.save_event(_make_event(id="evt_lt_c", type="device.awake"))

    types = service.list_types()
    assert sorted(types) == ["app.opened", "device.awake"]


def test_list_types_empty(service: ActivityService):
    """list_types() returns [] for empty database."""
    assert service.list_types() == []
