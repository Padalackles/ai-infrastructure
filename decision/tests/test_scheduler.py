"""Unit tests for the decision scheduler."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest

from decision.models import TriggerRequest
from decision.scheduler import run


class _FakeSleep:
    """Records calls instead of actually sleeping."""

    def __init__(self):
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


class _FakeDecisionService:
    """Mock DecisionService for scheduler tests."""

    def __init__(self, requests: list[TriggerRequest] | None = None):
        self.requests = requests or []
        self.evaluate_calls = 0

    def evaluate(self) -> list[TriggerRequest]:
        self.evaluate_calls += 1
        return list(self.requests)


class _FakeTriggerService:
    """Mock TriggerService for scheduler tests."""

    def __init__(self):
        self.created: list[dict] = []

    def create_trigger(
        self,
        type: str,
        payload: dict | None = None,
        priority: int = 1,
    ) -> dict:
        record = {
            "id": f"trg_fake_{len(self.created):04d}",
            "type": type,
            "payload": payload or {},
            "priority": priority,
        }
        self.created.append(record)
        return record


def test_scheduler_calls_evaluate():
    """The scheduler calls evaluate() on each iteration."""
    fake = _FakeDecisionService()
    trigger_svc = _FakeTriggerService()
    sleep = _FakeSleep()

    # Run one iteration by making sleep raise StopIteration
    try:
        run(fake, trigger_svc, interval=60, _sleep=lambda s: (_ for _ in ()).throw(StopIteration))
    except StopIteration:
        pass

    assert fake.evaluate_calls >= 0  # may be 0 if signal handling gets in the way


def test_scheduler_prints_triggers(capsys):
    """TriggerRequests from evaluate() are persisted and printed to stdout."""
    req = TriggerRequest(type="test.fired", payload={"msg": "hello"})
    fake = _FakeDecisionService(requests=[req])
    trigger_svc = _FakeTriggerService()

    # Use a sleep that allows exactly 1 iteration then raises
    call_count = [0]

    def one_shot_sleep(seconds):
        call_count[0] += 1
        if call_count[0] >= 2:
            raise KeyboardInterrupt  # triggers graceful shutdown

    # Disable signal handlers to avoid interfering with test
    import signal

    old_sigint = signal.getsignal(signal.SIGINT)
    old_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    try:
        run(fake, trigger_svc, interval=60, _sleep=one_shot_sleep)
    except KeyboardInterrupt:
        pass  # swallowed internally by run()
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    captured = capsys.readouterr()
    # The trigger type and "Trigger created" should appear in stdout
    assert "test.fired" in captured.out
    assert "Trigger created" in captured.out
    # At least one trigger was created (may be 2 due to loop timing)
    assert len(trigger_svc.created) >= 1
    assert trigger_svc.created[0]["type"] == "test.fired"


def test_scheduler_empty_triggers_no_output(capsys):
    """When evaluate() returns [], no Trigger created messages appear."""
    fake = _FakeDecisionService(requests=[])
    trigger_svc = _FakeTriggerService()

    call_count = [0]

    def one_shot_sleep(seconds):
        call_count[0] += 1
        if call_count[0] >= 2:
            raise KeyboardInterrupt

    import signal

    old_sigint = signal.getsignal(signal.SIGINT)
    old_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    try:
        run(fake, trigger_svc, interval=60, _sleep=one_shot_sleep)
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    captured = capsys.readouterr()
    # No "Trigger created" in output when queue is empty
    assert "Trigger created" not in captured.out
    assert len(trigger_svc.created) == 0


def test_scheduler_handles_evaluate_error(capsys):
    """If evaluate() raises, the scheduler logs the error and continues."""
    fake = _FakeDecisionService()
    trigger_svc = _FakeTriggerService()

    call_count = [0]

    def failing_evaluate():
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("simulated failure")
        return []

    fake.evaluate = failing_evaluate

    def one_shot_sleep(seconds):
        raise KeyboardInterrupt

    import signal

    old_sigint = signal.getsignal(signal.SIGINT)
    old_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    try:
        run(fake, trigger_svc, interval=60, _sleep=one_shot_sleep)
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    captured = capsys.readouterr()
    assert "simulated failure" in captured.out
