"""Unit tests for configuration-driven rules.

Covers screen_long_use_rule, app_long_use_rule, cooldown, disabled rules.
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

from decision.rules import (
    clear_rules,
    screen_long_use_rule,
    app_long_use_rule,
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
