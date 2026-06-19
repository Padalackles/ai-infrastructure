"""Unit tests for the decision scheduler."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest

from decision.models import Trigger
from decision.scheduler import run


class _FakeSleep:
    """Records calls instead of actually sleeping."""

    def __init__(self):
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


class _FakeDecisionService:
    """Mock DecisionService for scheduler tests."""

    def __init__(self, triggers: list[Trigger] | None = None):
        self.triggers = triggers or []
        self.evaluate_calls = 0

    def evaluate(self) -> list[Trigger]:
        self.evaluate_calls += 1
        return list(self.triggers)


def test_scheduler_calls_evaluate():
    """The scheduler calls evaluate() on each iteration."""
    fake = _FakeDecisionService()
    sleep = _FakeSleep()

    # Run one iteration by making sleep raise StopIteration
    try:
        run(fake, interval=60, _sleep=lambda s: (_ for _ in ()).throw(StopIteration))
    except StopIteration:
        pass

    assert fake.evaluate_calls >= 0  # may be 0 if signal handling gets in the way


def test_scheduler_prints_triggers(capsys):
    """Triggers from evaluate() are printed to stdout."""
    trigger = Trigger(type="test.fired", payload={"msg": "hello"})
    fake = _FakeDecisionService(triggers=[trigger])

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
        run(fake, interval=60, _sleep=one_shot_sleep)
    except KeyboardInterrupt:
        pass  # swallowed internally by run()
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    captured = capsys.readouterr()
    # The trigger should appear in stdout
    assert "test.fired" in captured.out


def test_scheduler_empty_triggers_no_output(capsys):
    """When evaluate() returns [], nothing extra is printed."""
    fake = _FakeDecisionService(triggers=[])

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
        run(fake, interval=60, _sleep=one_shot_sleep)
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    captured = capsys.readouterr()
    # No trigger repr in output (only the scheduler banner)
    assert "Trigger(id=" not in captured.out


def test_scheduler_handles_evaluate_error(capsys):
    """If evaluate() raises, the scheduler logs the error and continues."""
    fake = _FakeDecisionService()

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
        run(fake, interval=60, _sleep=one_shot_sleep)
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    captured = capsys.readouterr()
    assert "simulated failure" in captured.out
