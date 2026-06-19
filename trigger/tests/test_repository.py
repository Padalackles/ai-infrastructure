"""Unit tests for TriggerRepository.

Covers:
    * save() — persist a trigger, returns trg_ id
    * get_by_id() — found and not-found
    * get_oldest_pending() — priority ordering, empty queue
    * list_pending() — all pending, respects limit
    * ack() — sets status='acked' and acked_at
    * ack() — returns None for nonexistent id
    * acked triggers don't appear as pending

Each test uses a temp file database — never touches production data.
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
from trigger.repository import TriggerRepository


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def temp_db() -> Path:
    """Create a temporary database with triggers table."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_trigger_")
    os.close(fd)
    db_path = Path(path)
    set_db_path(db_path)
    init_db(db_path)
    yield db_path
    set_db_path(None)
    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.fixture
def repo(temp_db: Path) -> TriggerRepository:
    """Return a repository bound to the temp database."""
    return TriggerRepository(db_path=temp_db)


# ── Helpers ─────────────────────────────────────────────────────────


def _make_trigger(**overrides) -> dict:
    """Build a trigger dict with sensible defaults."""
    import time
    record = {
        "id": f"trg_test{int(time.time() * 1000):x}",
        "type": "procrastination",
        "payload": {},
        "status": "pending",
        "priority": 1,
        "created_at": "2026-06-20T10:00:00.000Z",
        "acked_at": None,
    }
    record.update(overrides)
    return record


# ── save() ──────────────────────────────────────────────────────────


def test_save_returns_id(repo: TriggerRepository):
    """save() returns the trigger id."""
    trigger = _make_trigger()
    result = repo.save(trigger)
    assert result == trigger["id"]
    assert result.startswith("trg_"), f"Expected trg_ prefix, got {result!r}"


def test_save_persists_all_fields(repo: TriggerRepository):
    """All fields round-trip correctly."""
    trigger = _make_trigger(
        type="sleep",
        payload={"hours": 8, "quality": "good"},
        priority=0,
        status="pending",
        created_at="2026-06-20T22:00:00.000Z",
    )
    trigger_id = repo.save(trigger)

    fetched = repo.get_by_id(trigger_id)
    assert fetched is not None
    assert fetched["type"] == "sleep"
    assert fetched["payload"] == {"hours": 8, "quality": "good"}
    assert fetched["priority"] == 0
    assert fetched["status"] == "pending"
    assert fetched["created_at"] == "2026-06-20T22:00:00.000Z"
    assert fetched["acked_at"] is None


def test_save_payload_is_freeform_json(repo: TriggerRepository):
    """Payload accepts arbitrary JSON structures."""
    trigger = _make_trigger(
        payload={
            "reason": "连续使用Bilibili 30分钟",
            "duration": 7200,
            "app": "bilibili",
            "activities": [
                {"type": "app.foreground", "app": "bilibili"},
                {"type": "screen.on", "at": "2026-06-20T10:00:00Z"},
            ],
        }
    )
    trigger_id = repo.save(trigger)
    fetched = repo.get_by_id(trigger_id)
    assert fetched["payload"] == trigger["payload"]


# ── get_by_id() ─────────────────────────────────────────────────────


def test_get_by_id_found(repo: TriggerRepository):
    """get_by_id() returns the trigger when it exists."""
    trigger = _make_trigger(id="trg_known001", type="focus")
    repo.save(trigger)

    result = repo.get_by_id("trg_known001")
    assert result is not None
    assert result["id"] == "trg_known001"
    assert result["type"] == "focus"


def test_get_by_id_not_found(repo: TriggerRepository):
    """get_by_id() returns None for nonexistent ids."""
    result = repo.get_by_id("trg_nonexistent")
    assert result is None


# ── get_oldest_pending() ────────────────────────────────────────────


def test_get_oldest_pending_returns_none_when_empty(repo: TriggerRepository):
    """Empty queue returns None."""
    result = repo.get_oldest_pending()
    assert result is None


def test_get_oldest_pending_returns_only_pending(repo: TriggerRepository):
    """Returns the single pending trigger."""
    repo.save(_make_trigger(id="trg_a", type="procrastination", status="pending"))
    result = repo.get_oldest_pending()
    assert result is not None
    assert result["id"] == "trg_a"


def test_get_oldest_pending_respects_priority(repo: TriggerRepository):
    """Highest priority (lowest number) wins, regardless of creation order."""
    repo.save(_make_trigger(
        id="trg_low", type="sleep", priority=2,
        created_at="2026-06-20T10:00:00.000Z",
    ))
    repo.save(_make_trigger(
        id="trg_high", type="procrastination", priority=0,
        created_at="2026-06-20T11:00:00.000Z",  # newer, but higher priority
    ))
    repo.save(_make_trigger(
        id="trg_normal", type="study", priority=1,
        created_at="2026-06-20T09:00:00.000Z",
    ))

    result = repo.get_oldest_pending()
    assert result is not None
    assert result["id"] == "trg_high", f"Expected highest priority, got {result['id']}"
    assert result["priority"] == 0


def test_get_oldest_pending_same_priority_oldest_first(repo: TriggerRepository):
    """Same priority → oldest created_at wins."""
    repo.save(_make_trigger(
        id="trg_newer", type="focus", priority=1,
        created_at="2026-06-20T11:00:00.000Z",
    ))
    repo.save(_make_trigger(
        id="trg_older", type="sleep", priority=1,
        created_at="2026-06-20T09:00:00.000Z",
    ))

    result = repo.get_oldest_pending()
    assert result is not None
    assert result["id"] == "trg_older"


# ── list_pending() ──────────────────────────────────────────────────


def test_list_pending_returns_all_pending(repo: TriggerRepository):
    """list_pending() returns all triggers with status='pending'."""
    repo.save(_make_trigger(id="trg_a", status="pending"))
    repo.save(_make_trigger(id="trg_b", status="pending"))
    repo.save(_make_trigger(id="trg_c", status="pending"))

    results = repo.list_pending()
    assert len(results) == 3
    ids = {r["id"] for r in results}
    assert ids == {"trg_a", "trg_b", "trg_c"}


def test_list_pending_ordered_by_priority(repo: TriggerRepository):
    """list_pending() orders by priority then age."""
    repo.save(_make_trigger(id="trg_2", priority=2))
    repo.save(_make_trigger(id="trg_0", priority=0))
    repo.save(_make_trigger(id="trg_1", priority=1))

    results = repo.list_pending()
    assert len(results) == 3
    assert results[0]["priority"] <= results[1]["priority"]
    assert results[1]["priority"] <= results[2]["priority"]


def test_list_pending_excludes_acked(repo: TriggerRepository):
    """Only pending triggers are returned."""
    repo.save(_make_trigger(id="trg_pending", status="pending"))
    repo.save(_make_trigger(id="trg_acked", status="acked"))

    results = repo.list_pending()
    assert len(results) == 1
    assert results[0]["id"] == "trg_pending"


# ── ack() ──────────────────────────────────────────────────────────


def test_ack_sets_status_and_timestamp(repo: TriggerRepository):
    """ack() sets status='acked' and acked_at to a non-None value."""
    repo.save(_make_trigger(id="trg_ack_me", status="pending"))

    result = repo.ack("trg_ack_me")
    assert result is not None
    assert result["status"] == "acked"
    assert result["acked_at"] is not None
    assert "T" in result["acked_at"]
    assert result["acked_at"].endswith("Z")


def test_ack_returns_none_for_nonexistent(repo: TriggerRepository):
    """ack() returns None when the trigger does not exist."""
    result = repo.ack("trg_ghost")
    assert result is None


def test_acked_trigger_not_in_pending(repo: TriggerRepository):
    """After ack, the trigger is excluded from pending queries."""
    repo.save(_make_trigger(id="trg_was_pending", status="pending"))

    # Ack it
    repo.ack("trg_was_pending")

    # Should not appear as pending
    oldest = repo.get_oldest_pending()
    assert oldest is None

    pending_list = repo.list_pending()
    assert len(pending_list) == 0


def test_ack_is_idempotent(repo: TriggerRepository):
    """Acking an already-acked trigger updates acked_at again."""
    repo.save(_make_trigger(id="trg_re_ack", status="pending"))
    first = repo.ack("trg_re_ack")
    second = repo.ack("trg_re_ack")

    assert second is not None
    assert second["status"] == "acked"
    # acked_at should be updated (different from first ack)
    assert second["acked_at"] != first["acked_at"]


def test_save_with_explicit_payload_default(repo: TriggerRepository):
    """save() accepts an empty payload dict."""
    trigger = _make_trigger(payload={})
    trigger_id = repo.save(trigger)
    fetched = repo.get_by_id(trigger_id)
    assert fetched["payload"] == {}


def test_save_duplicate_id_raises(repo: TriggerRepository):
    """Saving a trigger with a duplicate id raises RuntimeError."""
    repo.save(_make_trigger(id="trg_dup"))
    with pytest.raises(RuntimeError):
        repo.save(_make_trigger(id="trg_dup"))


def test_save_rejects_missing_required_fields(repo: TriggerRepository):
    """Saving without 'type' or 'created_at' raises RuntimeError."""
    with pytest.raises(RuntimeError):
        repo.save({"id": "trg_bad", "payload": {}})
