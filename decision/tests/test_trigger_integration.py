"""Integration tests — Decision → Trigger pipeline end-to-end.

Covers the full chain::

    Rule fires → TriggerRequest → TriggerService.create()
        → TriggerRepository.save() → SQLite → assert record exists

Uses a temporary SQLite database — never touches production data.
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
from decision.models import TriggerRequest
from decision.rules import clear_rules, register
from decision.service import DecisionService
from trigger.repository import TriggerRepository
from trigger.service import TriggerService


# ── Helpers ─────────────────────────────────────────────────────────


def _make_event(**overrides) -> dict:
    event = {
        "version": 1,
        "id": "evt_test0001",
        "timestamp": "2026-06-20T10:00:00.000Z",
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


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def temp_db() -> Path:
    """Create a temporary database with events and triggers tables."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_integration_")
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
def activity_repo(temp_db: Path) -> ActivityRepository:
    return ActivityRepository(db_path=temp_db)


@pytest.fixture
def activity_service(activity_repo: ActivityRepository) -> ActivityService:
    return ActivityService(activity_repo)


@pytest.fixture
def decision_service(activity_service: ActivityService) -> DecisionService:
    return DecisionService(activity_service)


@pytest.fixture
def trigger_repo(temp_db: Path) -> TriggerRepository:
    return TriggerRepository(db_path=temp_db)


@pytest.fixture
def trigger_service(trigger_repo: TriggerRepository) -> TriggerService:
    return TriggerService(trigger_repo)


@pytest.fixture(autouse=True)
def _clear_rules():
    clear_rules()
    yield
    clear_rules()


# ── Integration tests ───────────────────────────────────────────────


def test_rule_fires_creates_trigger_record(
    decision_service: DecisionService,
    trigger_service: TriggerService,
    trigger_repo: TriggerRepository,
    activity_repo: ActivityRepository,
):
    """Full pipeline: Rule → TriggerRequest → TriggerService → SQLite."""
    _seed(activity_repo, id="evt_int_01", type="battery.low", payload={"level": 10})

    @register
    def battery_rule(events):
        for e in events:
            if e["type"] == "battery.low":
                return TriggerRequest(
                    type="battery.low",
                    payload={"level": e["payload"]["level"]},
                    priority=0,
                )
        return None

    # 1. Decision evaluates → returns TriggerRequest list
    requests = decision_service.evaluate()
    assert len(requests) == 1
    assert requests[0].type == "battery.low"
    assert requests[0].payload == {"level": 10}
    assert requests[0].priority == 0

    # 2. TriggerService persists the request
    record = trigger_service.create_trigger(
        type=requests[0].type,
        payload=requests[0].payload,
        priority=requests[0].priority,
    )
    assert record["id"].startswith("trg_")
    assert record["type"] == "battery.low"
    assert record["status"] == "pending"
    assert record["priority"] == 0
    assert record["acked_at"] is None

    # 3. Trigger is queryable from repository
    db_trigger = trigger_repo.get_by_id(record["id"])
    assert db_trigger is not None
    assert db_trigger["type"] == "battery.low"
    assert db_trigger["payload"] == {"level": 10}

    # 4. Trigger appears in pending queue
    pending = trigger_repo.get_oldest_pending()
    assert pending is not None
    assert pending["id"] == record["id"]


def test_rule_returns_none_no_trigger_created(
    decision_service: DecisionService,
    trigger_service: TriggerService,
    trigger_repo: TriggerRepository,
    activity_repo: ActivityRepository,
):
    """When no rules fire, evaluate() returns [] and nothing is in DB."""
    _seed(activity_repo, id="evt_int_02", type="device.awake")

    @register
    def never_fires(events):
        return None

    requests = decision_service.evaluate()
    assert requests == []

    # No pending triggers in DB
    pending = trigger_repo.get_oldest_pending()
    assert pending is None


def test_multiple_rules_create_multiple_triggers(
    decision_service: DecisionService,
    trigger_service: TriggerService,
    trigger_repo: TriggerRepository,
    activity_repo: ActivityRepository,
):
    """Two rules firing → two Trigger records in DB."""
    _seed(activity_repo, id="evt_int_03a", type="battery.low", payload={"level": 5})
    _seed(activity_repo, id="evt_int_03b", type="device.awake")

    @register
    def battery_rule(events):
        for e in events:
            if e["type"] == "battery.low":
                return TriggerRequest(type="battery.low", priority=0)
        return None

    @register
    def awake_rule(events):
        for e in events:
            if e["type"] == "device.awake":
                return TriggerRequest(type="device.awake.seen", priority=1)
        return None

    requests = decision_service.evaluate()
    assert len(requests) == 2

    # Create both via TriggerService
    ids = []
    for req in requests:
        record = trigger_service.create_trigger(
            type=req.type,
            payload=req.payload,
            priority=req.priority,
        )
        ids.append(record["id"])

    # Both are in pending
    pending = trigger_repo.list_pending()
    assert len(pending) == 2
    pending_ids = {t["id"] for t in pending}
    assert set(ids) == pending_ids


def test_trigger_payload_round_trip(
    decision_service: DecisionService,
    trigger_service: TriggerService,
    trigger_repo: TriggerRepository,
    activity_repo: ActivityRepository,
):
    """Complex payload survives the full round-trip unchanged."""
    complex_payload = {
        "reason": "连续使用Bilibili 2小时",
        "duration": 7200,
        "app": "bilibili",
        "related_activities": [
            {"type": "app.foreground", "timestamp": "2026-06-20T08:00:00Z"},
            {"type": "screen.on", "timestamp": "2026-06-20T08:00:00Z"},
        ],
    }

    _seed(
        activity_repo,
        id="evt_int_04",
        type="app.foreground",
        payload={"app": "bilibili", "duration": 7200},
    )

    @register
    def procrastination_rule(events):
        for e in events:
            if e["type"] == "app.foreground" and e["payload"].get("app") == "bilibili":
                return TriggerRequest(
                    type="procrastination",
                    payload=complex_payload,
                    priority=2,
                )
        return None

    requests = decision_service.evaluate()
    assert len(requests) == 1
    assert requests[0].payload == complex_payload

    record = trigger_service.create_trigger(
        type=requests[0].type,
        payload=requests[0].payload,
        priority=requests[0].priority,
    )

    db_trigger = trigger_repo.get_by_id(record["id"])
    assert db_trigger["payload"] == complex_payload


def test_priority_preserved_in_db(
    decision_service: DecisionService,
    trigger_service: TriggerService,
    trigger_repo: TriggerRepository,
    activity_repo: ActivityRepository,
):
    """Priority set by the rule is preserved through the pipeline."""
    _seed(activity_repo, id="evt_int_05", type="battery.low", payload={"level": 3})

    @register
    def urgent_rule(events):
        for e in events:
            if e["type"] == "battery.low":
                return TriggerRequest(
                    type="battery.low",
                    priority=0,  # highest
                    payload={"level": e["payload"]["level"]},
                )
        return None

    requests = decision_service.evaluate()
    assert len(requests) == 1
    assert requests[0].priority == 0

    record = trigger_service.create_trigger(
        type=requests[0].type,
        payload=requests[0].payload,
        priority=requests[0].priority,
    )

    db_trigger = trigger_repo.get_by_id(record["id"])
    assert db_trigger["priority"] == 0


def test_evaluate_empty_activity_returns_empty(
    decision_service: DecisionService,
):
    """With no Activity events, evaluate() returns [].

    No DB needed — test runs without seeding any events.
    """
    requests = decision_service.evaluate()
    assert requests == []
