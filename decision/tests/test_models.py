"""Unit tests for TriggerRequest and Trigger (deprecated) models."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is importable
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision.models import Trigger, TriggerRequest


def test_trigger_request_creation_with_defaults():
    """A TriggerRequest can be created with only the required type field."""
    tr = TriggerRequest(type="procrastination")
    assert tr.type == "procrastination"
    assert tr.payload == {}
    assert tr.priority == 1


def test_trigger_request_creation_with_all_fields():
    """All fields are preserved exactly as passed."""
    tr = TriggerRequest(
        type="battery.low",
        payload={"level": 15},
        priority=0,
    )
    assert tr.type == "battery.low"
    assert tr.payload == {"level": 15}
    assert tr.priority == 0


def test_trigger_request_no_id_or_timestamp():
    """TriggerRequest has no database concepts — no id, status, or timestamps."""
    tr = TriggerRequest(type="focus")
    assert not hasattr(tr, "id")
    assert not hasattr(tr, "status")
    assert not hasattr(tr, "created_at")


def test_trigger_request_repr():
    """__repr__ includes type, priority, and payload."""
    tr = TriggerRequest(type="sleep", payload={"hours": 8}, priority=2)
    r = repr(tr)
    assert "sleep" in r
    assert "2" in r
    assert "hours" in r


# ── Deprecated Trigger tests (kept for backward compat) ──────────
    """A Trigger can be created with only the required type field."""
    t = Trigger(type="battery.low")
    assert t.type == "battery.low"
    assert t.id.startswith("trg_"), f"Expected trg_ prefix, got {t.id!r}"
    assert "T" in t.timestamp
    assert t.payload == {}


def test_trigger_creation_with_payload():
    """Payload is preserved exactly as passed."""
    t = Trigger(type="focus.timeout", payload={"minutes": 30})
    assert t.type == "focus.timeout"
    assert t.payload == {"minutes": 30}


def test_trigger_id_is_unique():
    """Each Trigger gets a unique ID."""
    ids = {Trigger(type="test").id for _ in range(10)}
    assert len(ids) == 10


def test_trigger_repr():
    """__repr__ includes all fields for readability."""
    t = Trigger(type="battery.low", payload={"level": 15})
    r = repr(t)
    assert "battery.low" in r
    assert "trg_" in r
    assert "level" in r


def test_trigger_timestamp_is_iso8601():
    """Timestamp is ISO 8601 with Z suffix."""
    t = Trigger(type="test")
    assert t.timestamp.endswith("Z")
    assert "T" in t.timestamp
