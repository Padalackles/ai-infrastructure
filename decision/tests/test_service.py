"""Unit tests for DecisionService.evaluate()."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest

from activity.storage.database import init_db, set_db_path
from activity.storage.repository import ActivityRepository
from activity.service import ActivityService
from decision.models import Trigger
from decision.rules import clear_rules, register
from decision.service import DecisionService


# ── Helpers ─────────────────────────────────────────────────────────


def _make_event(**overrides) -> dict:
    event = {
        "version": 1,
        "id": "evt_test0001",
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


def _seed(repo: ActivityRepository, **overrides) -> str:
    event = _make_event(**overrides)
    repo.save_event(event)
    return event["id"]


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def repo() -> ActivityRepository:
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_decision_")
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
def activity(repo: ActivityRepository) -> ActivityService:
    return ActivityService(repo)


@pytest.fixture
def service(activity: ActivityService) -> DecisionService:
    return DecisionService(activity)


@pytest.fixture(autouse=True)
def _clear():
    clear_rules()
    yield
    clear_rules()


# ── Tests ──────────────────────────────────────────────────────────


def test_evaluate_empty_database_returns_empty(service: DecisionService):
    """With no events in the database, evaluate() returns []."""
    results = service.evaluate()
    assert results == []


def test_evaluate_no_rules_registered(service: DecisionService, repo: ActivityRepository):
    """With events but no registered rules, evaluate() returns []."""
    _seed(repo, id="evt_a", type="device.awake")
    results = service.evaluate()
    assert results == []


def test_evaluate_rule_returns_none(service: DecisionService, repo: ActivityRepository):
    """When all rules return None, evaluate() returns []."""
    _seed(repo, id="evt_b", type="device.awake")

    @register
    def nop_rule(events):
        return None

    results = service.evaluate()
    assert results == []


def test_evaluate_single_rule_fires(service: DecisionService, repo: ActivityRepository):
    """A rule that returns a Trigger appears in evaluate() output."""
    _seed(repo, id="evt_c", type="battery.low", payload={"level": 10})

    @register
    def low_battery_detector(events):
        for e in events:
            if e["type"] == "battery.low":
                return Trigger(
                    type="battery.low",
                    payload={"level": e["payload"]["level"]},
                )
        return None

    results = service.evaluate()
    assert len(results) == 1
    assert results[0].type == "battery.low"
    assert results[0].payload == {"level": 10}


def test_evaluate_multiple_rules_fire(service: DecisionService, repo: ActivityRepository):
    """Multiple rules can fire in the same evaluation cycle."""
    _seed(repo, id="evt_d1", type="device.awake")
    _seed(repo, id="evt_d2", type="battery.low", payload={"level": 5})

    @register
    def awake_detector(events):
        for e in events:
            if e["type"] == "device.awake":
                return Trigger(type="device.awake.seen")
        return None

    @register
    def battery_detector(events):
        for e in events:
            if e["type"] == "battery.low":
                return Trigger(type="battery.low.seen")
        return None

    results = service.evaluate()
    assert len(results) == 2
    types = {r.type for r in results}
    assert types == {"device.awake.seen", "battery.low.seen"}


def test_evaluate_no_matching_events(service: DecisionService, repo: ActivityRepository):
    """When events exist but don't match rule criteria, no Triggers fire."""
    _seed(repo, id="evt_e", type="device.sleep")

    @register
    def only_awake(events):
        for e in events:
            if e["type"] == "device.awake":
                return Trigger(type="awake.found")
        return None

    results = service.evaluate()
    assert results == []


def test_evaluate_broken_rule_does_not_crash(service: DecisionService, repo: ActivityRepository):
    """If one rule raises, evaluation continues with remaining rules."""
    _seed(repo, id="evt_f", type="device.awake")

    @register
    def exploding_rule(events):
        raise RuntimeError("simulated rule failure")

    @register
    def good_rule(events):
        return Trigger(type="good.survived")

    results = service.evaluate()
    assert len(results) == 1
    assert results[0].type == "good.survived"


def test_evaluate_respects_event_limit(service: DecisionService, repo: ActivityRepository):
    """evaluate() reads at most 50 recent events (the default limit)."""
    for i in range(100):
        _seed(repo, id=f"evt_limit_{i:03d}", type="device.awake")

    count_seen = []

    @register
    def counter(events):
        count_seen.append(len(events))
        return None

    service.evaluate()
    # get_recent(50) is called, so at most 50
    assert count_seen[0] <= 50
