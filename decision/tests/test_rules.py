"""Unit tests for configuration-driven rules.

Covers screen_long_use_rule, app_long_use_rule, battery_low_rule,
procrastination_rule, late_sleep_rule, cooldown, disabled rules.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision.models import TriggerRequest
from decision.rules import (
    app_long_use_rule,
    battery_low_rule,
    clear_rules,
    late_sleep_rule,
    procrastination_rule,
    screen_long_use_rule,
    set_cooldown_store,
    set_rule_manager,
)
from decision.cooldown import MemoryCooldownStore
from decision.rule_manager import RuleManager


# ── Helpers ─────────────────────────────────────────────────────────


def _setup_manager(**rule_overrides):
    """Create a RuleManager with temp config. Returns (mgr, tmpdir)."""
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "rules.yaml"
    rule = {
        "id": "test_rule",
        "enabled": True,
        "trigger": "test.fired",
        "threshold_minutes": 30,
        "cooldown_minutes": 60,
    }
    rule.update(rule_overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump({"rules": [rule]}), encoding="utf-8")
    mgr = RuleManager(config_path=str(path))
    set_rule_manager(mgr)
    return mgr, tmp


def _setup_multi_manager(*rule_dicts):
    """Create a RuleManager with multiple rules. Returns (mgr, tmpdir)."""
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "rules.yaml"
    path.write_text(yaml.dump({"rules": list(rule_dicts)}), encoding="utf-8")
    mgr = RuleManager(config_path=str(path))
    set_rule_manager(mgr)
    return mgr, tmp


def _iso_offset(minutes_ago):
    dt = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _make_event(event_type, minutes_ago, **payload):
    import random
    return {
        "version": 1,
        "id": f"evt_{event_type}_{random.randint(1000,9999)}",
        "timestamp": _iso_offset(minutes_ago),
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": event_type,
        "payload": dict(payload),
        "raw": {},
    }


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset():
    """Reset rule manager and cooldown before/after each test."""
    clear_rules()
    set_rule_manager(None)
    set_cooldown_store(MemoryCooldownStore())
    yield
    clear_rules()
    set_rule_manager(None)


# ── Registry ────────────────────────────────────────────────────────


def test_register_adds_rule():
    from decision.rules import register, get_rules

    @register
    def my_rule(events):
        return None

    assert my_rule in get_rules()


def test_clear_rules_removes_all():
    from decision.rules import register, get_rules

    @register
    def rule_x(events):
        return None

    assert len(get_rules()) >= 1
    clear_rules()
    assert len(get_rules()) == 0


# ── Rule isolation ──────────────────────────────────────────────────


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


def test_rule_can_return_trigger_request():
    """A rule that returns a TriggerRequest works correctly."""

    @register
    def active_rule(events):
        if events:
            return TriggerRequest(type="test.fired", payload={"count": len(events)})
        return None

    # With events -> fires
    result = active_rule([{"id": "evt_x"}])
    assert result is not None
    assert result.type == "test.fired"
    assert result.payload["count"] == 1

    # No events -> silent
    result = active_rule([])
    assert result is None


# ── Screen rule ─────────────────────────────────────────────────────


def test_screen_rule_fires_above_threshold():
    _setup_manager(id="screen_long_use", threshold_minutes=30, cooldown_minutes=60)
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 45)]
    result = screen_long_use_rule(events)
    assert result is not None
    assert result.type == "screen.long_use"
    assert result.payload["threshold_minutes"] == 30
    assert result.payload["actual_minutes"] >= 44


def test_screen_rule_silent_below_threshold():
    _setup_manager(id="screen_long_use", threshold_minutes=60, cooldown_minutes=60)
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 10)]
    assert screen_long_use_rule(events) is None


def test_screen_rule_silent_when_screen_off():
    _setup_manager(id="screen_long_use", threshold_minutes=10, cooldown_minutes=60)
    set_cooldown_store(MemoryCooldownStore())
    events = [
        _make_event("screen.on", 60),
        _make_event("screen.off", 5),
    ]
    assert screen_long_use_rule(events) is None


def test_screen_rule_disabled():
    _setup_manager(id="screen_long_use", enabled=False, threshold_minutes=5)
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 120)]
    assert screen_long_use_rule(events) is None


# ── App rule ────────────────────────────────────────────────────────


def test_app_rule_fires_above_threshold():
    _setup_manager(
        id="app_long_use",
        package="com.ss.android.ugc.aweme",
        threshold_minutes=20,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("app.opened", 35, package="com.ss.android.ugc.aweme")]
    result = app_long_use_rule(events)
    assert result is not None
    assert result.type == "app.long_use"
    assert result.payload["app"] == "com.ss.android.ugc.aweme"
    assert result.payload["threshold_minutes"] == 20
    assert result.payload["actual_minutes"] >= 34


def test_app_rule_silent_below_threshold():
    _setup_manager(
        id="app_long_use",
        package="com.ss.android.ugc.aweme",
        threshold_minutes=60,
        cooldown_minutes=120,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("app.opened", 10, package="com.ss.android.ugc.aweme")]
    assert app_long_use_rule(events) is None


def test_app_rule_wrong_package():
    _setup_manager(
        id="app_long_use",
        package="com.ss.android.ugc.aweme",
        threshold_minutes=5,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("app.opened", 60, package="com.other.app")]
    assert app_long_use_rule(events) is None


def test_app_rule_closed_app():
    _setup_manager(
        id="app_long_use",
        package="com.ss.android.ugc.aweme",
        threshold_minutes=5,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [
        _make_event("app.opened", 30, package="com.ss.android.ugc.aweme"),
        _make_event("app.closed", 5, package="com.ss.android.ugc.aweme"),
    ]
    assert app_long_use_rule(events) is None


def test_app_rule_disabled():
    _setup_manager(
        id="app_long_use",
        enabled=False,
        package="com.ss.android.ugc.aweme",
        threshold_minutes=5,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("app.opened", 120, package="com.ss.android.ugc.aweme")]
    assert app_long_use_rule(events) is None


# ── Battery low rule ────────────────────────────────────────────────


def test_battery_low_fires_below_threshold():
    _setup_manager(id="battery_low", threshold_level=20, cooldown_minutes=90)
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("battery.low", 5, level=15, is_charging=False)]
    result = battery_low_rule(events)
    assert result is not None
    assert result.type == "battery.low"
    assert result.priority == 2
    assert result.payload["level"] == 15
    assert result.payload["threshold"] == 20


def test_battery_low_silent_above_threshold():
    _setup_manager(id="battery_low", threshold_level=20, cooldown_minutes=90)
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("battery.low", 5, level=35, is_charging=False)]
    assert battery_low_rule(events) is None


def test_battery_low_silent_no_events():
    _setup_manager(id="battery_low", threshold_level=20, cooldown_minutes=90)
    set_cooldown_store(MemoryCooldownStore())
    assert battery_low_rule([]) is None


def test_battery_low_silent_disabled():
    _setup_manager(id="battery_low", enabled=False, threshold_level=20)
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("battery.low", 5, level=5, is_charging=False)]
    assert battery_low_rule(events) is None


def test_battery_low_uses_most_recent_event():
    """Only the most recent battery.low event matters."""
    _setup_manager(id="battery_low", threshold_level=20, cooldown_minutes=90)
    set_cooldown_store(MemoryCooldownStore())
    events = [
        _make_event("battery.low", 30, level=10, is_charging=False),
        _make_event("battery.low", 5, level=40, is_charging=True),  # most recent — above threshold
    ]
    assert battery_low_rule(events) is None


def test_battery_low_cooldown():
    _setup_manager(id="battery_low", threshold_level=20, cooldown_minutes=60)
    store = MemoryCooldownStore()
    set_cooldown_store(store)
    events = [_make_event("battery.low", 5, level=10, is_charging=False)]
    r1 = battery_low_rule(events)
    assert r1 is not None
    r2 = battery_low_rule(events)
    assert r2 is None


# ── Procrastination rule ────────────────────────────────────────────


def test_procrastination_fires_above_threshold():
    _setup_manager(
        id="procrastination",
        packages=["com.ss.android.ugc.aweme", "com.tencent.mm"],
        threshold_minutes=20,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("app.opened", 35, package="com.ss.android.ugc.aweme", label="TikTok")]
    result = procrastination_rule(events)
    assert result is not None
    assert result.type == "procrastination"
    assert result.priority == 1
    assert result.payload["app"] == "com.ss.android.ugc.aweme"
    assert result.payload["threshold_minutes"] == 20
    assert result.payload["actual_minutes"] >= 34


def test_procrastination_fires_second_package():
    """When first package is below threshold, second package can fire."""
    _setup_manager(
        id="procrastination",
        packages=["com.tencent.mm", "com.ss.android.ugc.aweme"],
        threshold_minutes=20,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [
        _make_event("app.opened", 5, package="com.tencent.mm", label="WeChat"),
        _make_event("app.opened", 45, package="com.ss.android.ugc.aweme", label="TikTok"),
    ]
    result = procrastination_rule(events)
    assert result is not None
    assert result.payload["app"] == "com.ss.android.ugc.aweme"


def test_procrastination_silent_below_threshold():
    _setup_manager(
        id="procrastination",
        packages=["com.ss.android.ugc.aweme"],
        threshold_minutes=60,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("app.opened", 10, package="com.ss.android.ugc.aweme")]
    assert procrastination_rule(events) is None


def test_procrastination_silent_app_closed():
    _setup_manager(
        id="procrastination",
        packages=["com.ss.android.ugc.aweme"],
        threshold_minutes=5,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [
        _make_event("app.opened", 30, package="com.ss.android.ugc.aweme"),
        _make_event("app.closed", 5, package="com.ss.android.ugc.aweme"),
    ]
    assert procrastination_rule(events) is None


def test_procrastination_silent_disabled():
    _setup_manager(
        id="procrastination",
        enabled=False,
        packages=["com.ss.android.ugc.aweme"],
        threshold_minutes=5,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("app.opened", 120, package="com.ss.android.ugc.aweme")]
    assert procrastination_rule(events) is None


def test_procrastination_cooldown():
    _setup_manager(
        id="procrastination",
        packages=["com.ss.android.ugc.aweme"],
        threshold_minutes=10,
        cooldown_minutes=60,
    )
    store = MemoryCooldownStore()
    set_cooldown_store(store)
    events = [_make_event("app.opened", 45, package="com.ss.android.ugc.aweme")]
    r1 = procrastination_rule(events)
    assert r1 is not None
    r2 = procrastination_rule(events)
    assert r2 is None


# ── Late sleep rule ─────────────────────────────────────────────────


def test_late_sleep_fires_past_cutoff():
    _setup_manager(
        id="late_sleep",
        cutoff_hour_utc=0,  # midnight — always fires
        threshold_minutes=10,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 45)]
    result = late_sleep_rule(events)
    assert result is not None
    assert result.type == "late_sleep"
    assert result.priority == 1
    assert result.payload["threshold_minutes"] == 10
    assert result.payload["actual_minutes"] >= 44


def test_late_sleep_silent_before_cutoff():
    """When current UTC hour is before cutoff, rule does not fire."""
    # Set cutoff to a value we can't be before in normal test conditions
    # — the test is inherently time-dependent, so we test the happy path
    # using cutoff=0 and the branch using a very high cutoff.
    _setup_manager(
        id="late_sleep",
        cutoff_hour_utc=24,  # hour 24 never happens
        threshold_minutes=5,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 120)]
    assert late_sleep_rule(events) is None


def test_late_sleep_silent_below_duration_threshold():
    _setup_manager(
        id="late_sleep",
        cutoff_hour_utc=0,
        threshold_minutes=60,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 10)]
    assert late_sleep_rule(events) is None


def test_late_sleep_silent_screen_off():
    _setup_manager(
        id="late_sleep",
        cutoff_hour_utc=0,
        threshold_minutes=5,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [
        _make_event("screen.on", 60),
        _make_event("screen.off", 5),
    ]
    assert late_sleep_rule(events) is None


def test_late_sleep_silent_disabled():
    _setup_manager(
        id="late_sleep",
        enabled=False,
        cutoff_hour_utc=0,
        threshold_minutes=5,
    )
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 120)]
    assert late_sleep_rule(events) is None


def test_late_sleep_cooldown():
    _setup_manager(
        id="late_sleep",
        cutoff_hour_utc=0,
        threshold_minutes=10,
        cooldown_minutes=60,
    )
    store = MemoryCooldownStore()
    set_cooldown_store(store)
    events = [_make_event("screen.on", 45)]
    r1 = late_sleep_rule(events)
    assert r1 is not None
    r2 = late_sleep_rule(events)
    assert r2 is None


# ── Cooldown ────────────────────────────────────────────────────────


def test_cooldown_prevents_refire():
    _setup_manager(id="screen_long_use", threshold_minutes=10, cooldown_minutes=60)
    store = MemoryCooldownStore()
    set_cooldown_store(store)
    events = [_make_event("screen.on", 45)]
    r1 = screen_long_use_rule(events)
    assert r1 is not None
    r2 = screen_long_use_rule(events)
    assert r2 is None


def test_cooldown_expired_allows_refire():
    _setup_manager(id="screen_long_use", threshold_minutes=10, cooldown_minutes=1)
    store = MemoryCooldownStore()
    store.set("screen_long_use", datetime.now(timezone.utc) - timedelta(minutes=5))
    set_cooldown_store(store)
    events = [_make_event("screen.on", 45)]
    result = screen_long_use_rule(events)
    assert result is not None


# ── Empty events ────────────────────────────────────────────────────


def test_screen_rule_empty_events():
    _setup_manager(id="screen_long_use", threshold_minutes=10, cooldown_minutes=60)
    set_cooldown_store(MemoryCooldownStore())
    assert screen_long_use_rule([]) is None


def test_app_rule_empty_events():
    _setup_manager(
        id="app_long_use",
        package="com.ss.android.ugc.aweme",
        threshold_minutes=10,
        cooldown_minutes=60,
    )
    set_cooldown_store(MemoryCooldownStore())
    assert app_long_use_rule([]) is None


def test_rule_without_config_no_crash():
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 60)]
    try:
        screen_long_use_rule(events)
    except Exception as exc:
        pytest.fail(f"Rule raised unexpectedly: {exc}")


# ── TriggerRequest vs Trigger ───────────────────────────────────────


def test_rules_return_trigger_request():
    """All registered rules return TriggerRequest, not Trigger."""
    _setup_manager(id="screen_long_use", threshold_minutes=10, cooldown_minutes=60)
    set_cooldown_store(MemoryCooldownStore())
    events = [_make_event("screen.on", 45)]
    result = screen_long_use_rule(events)
    assert result is not None
    assert isinstance(result, TriggerRequest)
    # TriggerRequest has no id, status, or created_at
    assert not hasattr(result, "id")
    assert not hasattr(result, "status")
    assert not hasattr(result, "created_at")
