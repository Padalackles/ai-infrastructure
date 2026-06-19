"""Unit tests for CooldownStore."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision.cooldown import MemoryCooldownStore


def test_get_never_set_returns_none():
    """A rule that has never fired returns None."""
    store = MemoryCooldownStore()
    assert store.get("any_rule") is None


def test_set_and_get():
    """After set(), get() returns the stored timestamp."""
    store = MemoryCooldownStore()
    now = datetime.now(timezone.utc)
    store.set("screen_long_use", now)
    assert store.get("screen_long_use") == now


def test_multiple_rules_independent():
    """Setting one rule does not affect another."""
    store = MemoryCooldownStore()
    now = datetime.now(timezone.utc)
    store.set("rule_a", now)
    assert store.get("rule_b") is None
    assert store.get("rule_a") == now


def test_set_overwrites():
    """Setting the same rule again overwrites the previous timestamp."""
    store = MemoryCooldownStore()
    t1 = datetime(2026, 6, 19, 9, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 6, 19, 10, 0, 0, tzinfo=timezone.utc)

    store.set("rule_x", t1)
    assert store.get("rule_x") == t1

    store.set("rule_x", t2)
    assert store.get("rule_x") == t2
