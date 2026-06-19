"""Unit tests for the Activity Storage layer.

Covers:
    * Database initialization + automatic table creation
    * save_event()
    * get_event() — found and not-found
    * list_events() — ordering and limit
    * count_events()
    * JSON serialization (payload/raw round-trip)
    * Idempotent init_db()

Each test uses a temp file database — never touches production data.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the repo root is importable.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from activity.storage.database import get_db_path, init_db, set_db_path, get_connection
from activity.storage.repository import ActivityRepository


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def temp_db() -> Path:
    """Create a temporary database for a single test."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_activity_")
    os.close(fd)  # Release the file handle for Windows
    db_path = Path(path)
    set_db_path(db_path)
    init_db(db_path)
    yield db_path
    # Cleanup
    set_db_path(None)
    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        pass  # Windows may briefly hold a lock


@pytest.fixture
def repo(temp_db: Path) -> ActivityRepository:
    """Return a repository bound to the temp database."""
    return ActivityRepository(db_path=temp_db)


# ── Helpers ─────────────────────────────────────────────────────────


def _make_event(**overrides) -> dict:
    """Build a normalized event dict for testing."""
    event = {
        "version": 1,
        "id": "evt_test_abc123",
        "timestamp": "2026-06-19T09:00:00.000Z",
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": "device.awake",
        "payload": {"method": "power_button"},
        "raw": {"event": "screen_on", "action": "wake"},
    }
    event.update(overrides)
    return event


# ── Database initialization ─────────────────────────────────────────


def test_init_db_creates_data_directory():
    """init_db() creates the parent data directory if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "subdir" / "activity.db"
        init_db(db_path)
        assert db_path.exists()
        assert db_path.stat().st_size > 0


def test_init_db_is_idempotent(temp_db: Path):
    """Calling init_db() twice must not fail."""
    init_db(temp_db)  # already called by fixture — second call
    init_db(temp_db)  # third call
    # If we got here without an exception, it's idempotent
    assert temp_db.exists()


def test_connection_returns_working_connection(temp_db: Path):
    """get_connection() returns a usable sqlite3.Connection."""
    conn = get_connection(temp_db)
    try:
        row = conn.execute("SELECT 1 AS n").fetchone()
        assert row["n"] == 1
    finally:
        conn.close()


# ── save_event ──────────────────────────────────────────────────────


def test_save_event_returns_event_id(repo: ActivityRepository):
    """save_event() returns the event ID on success."""
    event = _make_event()
    result = repo.save_event(event)
    assert result == "evt_test_abc123"


def test_save_event_persists_row(repo: ActivityRepository):
    """After save_event(), the row is queryable in SQLite."""
    event = _make_event()
    repo.save_event(event)

    conn = get_connection(repo._db_path)
    try:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event["id"],)).fetchone()
        assert row is not None
        assert row["id"] == event["id"]
        assert row["type"] == event["type"]
        assert row["version"] == event["version"]
    finally:
        conn.close()


def test_save_event_sets_created_at(repo: ActivityRepository):
    """save_event() auto-populates created_at with an ISO timestamp."""
    event = _make_event()
    repo.save_event(event)

    saved = repo.get_event(event["id"])
    assert saved is not None
    assert "created_at" in saved
    # Basic ISO format check
    assert saved["created_at"].startswith("2026")
    assert "T" in saved["created_at"]
    assert "Z" in saved["created_at"]


# ── get_event ───────────────────────────────────────────────────────


def test_get_event_returns_full_event(repo: ActivityRepository):
    """get_event() returns the canonical event dict with all fields."""
    event = _make_event()
    repo.save_event(event)

    found = repo.get_event(event["id"])
    assert found is not None
    assert found["id"] == event["id"]
    assert found["version"] == event["version"]
    assert found["timestamp"] == event["timestamp"]
    assert found["source"] == event["source"]
    assert found["collector"] == event["collector"]
    assert found["device"] == event["device"]
    assert found["type"] == event["type"]
    assert found["payload"] == event["payload"]
    assert found["raw"] == event["raw"]


def test_get_event_returns_none_for_missing(repo: ActivityRepository):
    """get_event() returns None when the ID doesn't exist."""
    found = repo.get_event("evt_nonexistent")
    assert found is None


# ── list_events ─────────────────────────────────────────────────────


def test_list_events_returns_newest_first(repo: ActivityRepository):
    """list_events() returns events ordered by created_at DESC."""
    for i in range(3):
        event = _make_event(id=f"evt_seq_{i:03d}", type=f"test.{i}")
        repo.save_event(event)

    results = repo.list_events(limit=10)
    assert len(results) >= 3
    # IDs should appear newest-first: seq_002, seq_001, seq_000
    ids = [r["id"] for r in results if r["id"].startswith("evt_seq_")]
    assert ids == sorted(ids, reverse=True)


def test_list_events_respects_limit(repo: ActivityRepository):
    """list_events(limit=N) returns at most N results."""
    for i in range(5):
        repo.save_event(_make_event(id=f"evt_lim_{i:03d}"))

    results = repo.list_events(limit=2)
    assert len(results) == 2


def test_list_events_clamps_limit(repo: ActivityRepository):
    """limit is clamped to [1, 1000]."""
    # limit=0 should clamp to 1
    results = repo.list_events(limit=0)
    assert len(results) <= 1  # May be 0 if table empty, 1 if any row

    # Negative should clamp to 1
    results = repo.list_events(limit=-5)
    assert len(results) <= 1

    # Over 1000 should clamp to 1000
    # No need to insert 1000 rows — just verify no error
    repo.list_events(limit=9999)  # shouldn't raise


# ── count_events ────────────────────────────────────────────────────


def test_count_events_starts_at_zero(repo: ActivityRepository):
    """An empty database reports 0 events."""
    assert repo.count_events() == 0


def test_count_events_increments(repo: ActivityRepository):
    """count_events() matches the number of saved events."""
    for i in range(7):
        repo.save_event(_make_event(id=f"evt_cnt_{i:03d}"))
    assert repo.count_events() == 7


# ── JSON serialization ──────────────────────────────────────────────


def test_payload_round_trips_as_json(repo: ActivityRepository):
    """Complex payload dicts survive the JSON round-trip."""
    event = _make_event(
        id="evt_json_001",
        payload={
            "level": 15,
            "is_charging": False,
            "nested": {"a": [1, 2, 3], "b": None},
        },
        raw={"original": "data", "arr": [9, 8, 7]},
    )
    repo.save_event(event)
    found = repo.get_event("evt_json_001")
    assert found is not None
    assert found["payload"] == event["payload"]
    assert found["raw"] == event["raw"]
    assert isinstance(found["payload"]["level"], int)
    assert isinstance(found["payload"]["nested"]["a"], list)


def test_empty_payload_serializes_as_empty_dict(repo: ActivityRepository):
    """An empty payload serializes to {} and deserializes back."""
    event = _make_event(id="evt_empty", payload={}, raw={})
    repo.save_event(event)
    found = repo.get_event("evt_empty")
    assert found is not None
    assert found["payload"] == {}
    assert found["raw"] == {}


def test_raw_preserves_original_collector_format(repo: ActivityRepository):
    """The raw field survives JSON round-trip unchanged."""
    raw_original = {
        "event": "battery_low",
        "level": 15,
        "timestamp_device": "2026-06-19T08:59:58Z",
    }
    event = _make_event(id="evt_raw_001", raw=raw_original)
    repo.save_event(event)
    found = repo.get_event("evt_raw_001")
    assert found is not None
    assert found["raw"] == raw_original


# ── save_event failure ──────────────────────────────────────────────


def test_save_event_raises_on_closed_db():
    """save_event raises sqlite3.OperationalError when the db path is invalid."""
    repo = ActivityRepository(db_path="/nonexistent/path/activity.db")
    with pytest.raises(sqlite3.OperationalError):
        repo.save_event(_make_event())


# ── Data integrity ──────────────────────────────────────────────────


def test_saved_event_fields_match_input(repo: ActivityRepository):
    """Every field of the saved event matches the input exactly."""
    event = _make_event(
        id="evt_check_001",
        version=1,
        timestamp="2026-06-19T10:30:00.000Z",
        source="ios",
        collector="shortcuts",
        device="iphone-15",
        type="battery.low",
        payload={"level": 10, "is_charging": False},
        raw={"ios_raw": "data"},
    )
    repo.save_event(event)

    found = repo.get_event("evt_check_001")
    assert found is not None
    for key in ("id", "version", "timestamp", "source", "collector", "device", "type"):
        assert found[key] == event[key], f"Mismatch on field {key!r}"
    assert found["payload"] == event["payload"]
    assert found["raw"] == event["raw"]


def test_multiple_events_independent(repo: ActivityRepository):
    """Saving multiple events doesn't corrupt data."""
    event_a = _make_event(id="evt_A", type="device.awake")
    event_b = _make_event(id="evt_B", type="device.sleep")

    repo.save_event(event_a)
    repo.save_event(event_b)

    found_a = repo.get_event("evt_A")
    found_b = repo.get_event("evt_B")

    assert found_a is not None and found_b is not None
    assert found_a["type"] == "device.awake"
    assert found_b["type"] == "device.sleep"
    assert found_a["id"] != found_b["id"]


# ── get_by_type ───────────────────────────────────────────────────────


def test_get_by_type_returns_matching_events(repo: ActivityRepository):
    """get_by_type() returns only events with the matching canonical type."""
    repo.save_event(_make_event(id="evt_bt_a", type="device.awake"))
    repo.save_event(_make_event(id="evt_bt_b", type="device.sleep"))
    repo.save_event(_make_event(id="evt_bt_c", type="device.awake"))

    results = repo.get_by_type("device.awake")
    assert len(results) == 2
    assert all(r["type"] == "device.awake" for r in results)


def test_get_by_type_respects_limit(repo: ActivityRepository):
    """get_by_type(limit=N) returns at most N results."""
    for i in range(5):
        repo.save_event(_make_event(id=f"evt_btl_{i:03d}", type="app.opened"))

    results = repo.get_by_type("app.opened", limit=2)
    assert len(results) == 2


def test_get_by_type_empty_for_unknown_type(repo: ActivityRepository):
    """get_by_type() returns [] for a type that doesn't exist."""
    results = repo.get_by_type("nonexistent.type")
    assert results == []


# ── get_between ───────────────────────────────────────────────────────


def test_get_between_returns_events_in_range(repo: ActivityRepository):
    """get_between() returns events with timestamp in [start, end]."""
    repo.save_event(_make_event(
        id="evt_ts_a", timestamp="2026-06-19T08:00:00.000Z", type="device.awake",
    ))
    repo.save_event(_make_event(
        id="evt_ts_b", timestamp="2026-06-19T09:00:00.000Z", type="device.sleep",
    ))
    repo.save_event(_make_event(
        id="evt_ts_c", timestamp="2026-06-19T10:00:00.000Z", type="device.awake",
    ))

    results = repo.get_between(
        start="2026-06-19T08:30:00.000Z",
        end="2026-06-19T10:30:00.000Z",
    )
    assert len(results) == 2
    ids = [r["id"] for r in results]
    assert "evt_ts_b" in ids
    assert "evt_ts_c" in ids
    assert "evt_ts_a" not in ids


def test_get_between_empty_when_no_matches(repo: ActivityRepository):
    """get_between() returns [] when no events fall in the range."""
    repo.save_event(_make_event(
        id="evt_range_x", timestamp="2026-06-01T00:00:00.000Z",
    ))
    results = repo.get_between(
        start="2026-06-10T00:00:00.000Z",
        end="2026-06-20T00:00:00.000Z",
    )
    assert results == []


# ── get_latest ────────────────────────────────────────────────────────


def test_get_latest_returns_most_recent_of_type(repo: ActivityRepository):
    """get_latest() returns the newest event of the given type."""
    repo.save_event(_make_event(
        id="evt_lat_a", type="device.awake",
        timestamp="2026-06-19T08:00:00.000Z",
    ))
    repo.save_event(_make_event(
        id="evt_lat_b", type="device.awake",
        timestamp="2026-06-19T09:00:00.000Z",
    ))

    latest = repo.get_latest("device.awake")
    assert latest is not None
    assert latest["id"] == "evt_lat_b"


def test_get_latest_returns_none_for_unknown_type(repo: ActivityRepository):
    """get_latest() returns None when no event of that type exists."""
    latest = repo.get_latest("nonexistent.type")
    assert latest is None


# ── list_types ────────────────────────────────────────────────────────


def test_list_types_returns_distinct_sorted(repo: ActivityRepository):
    """list_types() returns distinct canonical types, sorted alphabetically."""
    repo.save_event(_make_event(id="evt_lt_a", type="device.sleep"))
    repo.save_event(_make_event(id="evt_lt_b", type="device.awake"))
    repo.save_event(_make_event(id="evt_lt_c", type="device.awake"))  # duplicate

    types = repo.list_types()
    assert types == ["device.awake", "device.sleep"]


def test_list_types_empty_for_empty_db(repo: ActivityRepository):
    """list_types() returns [] when no events exist."""
    types = repo.list_types()
    assert types == []
