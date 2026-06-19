"""Unit tests for the Trigger model."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is importable
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision.models import Trigger


def test_trigger_creation_with_required_fields():
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
