"""Decision Engine — periodic scheduler with Trigger persistence.

Runs ``DecisionService.evaluate()`` once every 60 seconds (by default).
Each ``TriggerRequest`` is passed to ``TriggerService.create()`` which
persists it to SQLite — ready for MacroDroid to poll via ``GET /trigger/pending``.

Usage::

    from activity.storage.repository import ActivityRepository
    from activity.service import ActivityService
    from decision.service import DecisionService
    from decision.scheduler import run
    from trigger.repository import TriggerRepository
    from trigger.service import TriggerService

    repo = ActivityRepository()
    activity = ActivityService(repo)
    decision = DecisionService(activity)

    trigger_repo = TriggerRepository()
    trigger_service = TriggerService(trigger_repo)

    run(decision, trigger_service, interval=60)  # blocking loop

Design:
    * Scheduler is the orchestrator — bridges Decision → Trigger.
    * Decision never touches database or calls TriggerService.
    * TriggerService is injected for testability.
"""

from __future__ import annotations

import signal
import sys
import time
from typing import Any

from decision.models import TriggerRequest
from decision.service import DecisionService


def run(
    service: DecisionService,
    trigger_service: Any,
    interval: int = 60,
    *,
    _sleep: Any = time.sleep,
) -> None:
    """Run the decision loop indefinitely.

    Every *interval* seconds:
        1. Call ``service.evaluate()``.
        2. For each ``TriggerRequest``, call ``trigger_service.create()``.
        3. Print the created trigger ID.
        4. Sleep.

    Press Ctrl+C to stop.

    Args:
        service: A configured ``DecisionService`` instance.
        trigger_service: A ``TriggerService`` instance for persistence.
        interval: Seconds between evaluation cycles (default 60).
    """
    print(f"[Decision Scheduler] Running every {interval}s.  Ctrl+C to stop.")
    print("[Decision Scheduler] Decision → TriggerQueue pipeline active.")

    # ── Graceful shutdown ──────────────────────────────────────
    running = True

    def _handle_signal(signum: int, frame: Any) -> None:
        nonlocal running
        print("\n[Decision Scheduler] Shutting down...")
        running = False

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # ── Main loop ──────────────────────────────────────────────
    while running:
        try:
            requests = service.evaluate()
            for req in requests:
                record = trigger_service.create_trigger(
                    type=req.type,
                    payload=req.payload,
                    priority=req.priority,
                )
                print(f"[Decision Scheduler] Trigger created: {record['id']}  type={req.type}")
        except Exception as exc:
            print(f"[Decision Scheduler] Error in evaluation cycle: {exc}")

        if not running:
            break
        _sleep(interval)

    print("[Decision Scheduler] Stopped.")


# ── CLI entry point ─────────────────────────────────────────────────


def main() -> None:
    """Entry point for ``python -m decision.scheduler``."""
    from activity.storage.database import init_db
    from activity.storage.repository import ActivityRepository
    from activity.service import ActivityService
    from trigger.repository import TriggerRepository
    from trigger.service import TriggerService

    # Bootstrap the database (idempotent).
    init_db()

    repo = ActivityRepository()
    activity = ActivityService(repo)
    decision = DecisionService(activity)

    trigger_repo = TriggerRepository()
    trigger_service = TriggerService(trigger_repo)

    run(decision, trigger_service, interval=60)


if __name__ == "__main__":
    main()
