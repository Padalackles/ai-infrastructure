"""Decision Engine — simple periodic scheduler.

Runs ``DecisionService.evaluate()`` once every 60 seconds (by default).
Each Trigger is printed to the console — no Claude, no ntfy, no reminders.

Usage::

    from activity.storage.repository import ActivityRepository
    from activity.service import ActivityService
    from decision.service import DecisionService
    from decision.scheduler import run

    repo = ActivityRepository()
    activity = ActivityService(repo)
    decision = DecisionService(activity)
    run(decision, interval=60)  # blocking loop

Design constraints (Phase 1):
    * Console output only — ``print(trigger)``.
    * Zero external dependencies (no Claude, no ntfy).
    * Blocking loop — intended to run as a background thread or process.
"""

from __future__ import annotations

import signal
import sys
import time
from typing import Any

from decision.service import DecisionService


def run(
    service: DecisionService,
    interval: int = 60,
    *,
    _sleep: Any = time.sleep,
) -> None:
    """Run the decision loop indefinitely.

    Every *interval* seconds:
        1. Call ``service.evaluate()``.
        2. Print each returned Trigger to stdout.
        3. Sleep.

    Press Ctrl+C to stop.

    Args:
        service: A configured ``DecisionService`` instance.
        interval: Seconds between evaluation cycles (default 60).
    """
    print(f"[Decision Scheduler] Running every {interval}s.  Ctrl+C to stop.")
    print("[Decision Scheduler] Phase 1 — console output only.")

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
            triggers = service.evaluate()
            for trigger in triggers:
                print(trigger)
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

    # Bootstrap the database (idempotent).
    init_db()

    repo = ActivityRepository()
    activity = ActivityService(repo)
    decision = DecisionService(activity)

    run(decision, interval=60)


if __name__ == "__main__":
    main()
