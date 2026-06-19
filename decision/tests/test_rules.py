"""Unit tests for the rule framework and placeholder rules."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest

from decision.models import Trigger
from decision.rules import (
    battery_low_rule,
    clear_rules,
    focus_timeout_rule,
    get_rules,
    register,
    screen_awake_rule,
)


# ── Setup / teardown ───────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_rules():
    """Ensure a clean registry before and after each test."""
    clear_rules()
    yield
    clear_rules()


# ── Registry ──────────────────────────────────────────────────────


def test_register_adds_rule():
    """@register adds the function to the rule registry."""

    @register
    def my_rule(events):
        return None

    rules = get_rules()
    assert my_rule in rules


def test_get_rules_returns_copy():
    """get_rules() returns a copy — mutating it doesn't affect registry."""

    @register
    def rule_a(events):
        return None

    rules = get_rules()
    rules.clear()
    assert len(get_rules()) == 1  # original unchanged


def test_clear_rules_removes_all():
    """clear_rules() empties the registry."""

    @register
    def rule_x(events):
        return None

    assert len(get_rules()) == 1
    clear_rules()
    assert len(get_rules()) == 0


def test_rules_evaluated_in_registration_order():
    """Rules are called in the order they were registered."""
    order = []

    @register
    def first(events):
        order.append("first")
        return None

    @register
    def second(events):
        order.append("second")
        return None

    for rule in get_rules():
        rule([])
    assert order == ["first", "second"]


# ── Placeholder rules ─────────────────────────────────────────────


def test_battery_low_rule_returns_none():
    """Placeholder rule always returns None."""
    result = battery_low_rule([])
    assert result is None


def test_screen_awake_rule_returns_none():
    """Placeholder rule always returns None."""
    result = screen_awake_rule([])
    assert result is None


def test_focus_timeout_rule_returns_none():
    """Placeholder rule always returns None."""
    result = focus_timeout_rule([])
    assert result is None


# ── Rule isolation ────────────────────────────────────────────────


def test_rule_receives_events_list():
    """Rules receive the events list passed by the service."""
    received = []

    @register
    def inspector(events):
        received.append(events)
        return None

    sample_events = [{"id": "evt_1", "type": "device.awake"}]
    for rule in get_rules():
        rule(sample_events)

    assert len(received) == 1
    assert received[0] == sample_events


def test_rule_can_return_trigger():
    """A rule that returns a Trigger works correctly."""

    @register
    def active_rule(events):
        if events:
            return Trigger(type="test.fired", payload={"count": len(events)})
        return None

    # With events → fires
    result = active_rule([{"id": "evt_x"}])
    assert result is not None
    assert result.type == "test.fired"
    assert result.payload == {"count": 1}

    # Without events → no fire
    result = active_rule([])
    assert result is None
