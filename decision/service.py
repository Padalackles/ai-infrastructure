"""Decision Engine — evaluation service.

The DecisionService is the single entry point for the decision
pipeline.  It reads recent events from the Activity subsystem,
runs all registered rules, and collects any Trigger objects
they emit.

Design constraints (Phase 1):
    * Reads events through ActivityService — never touches SQLite.
    * Executes rules but never makes business decisions itself.
    * Returns Trigger objects — never generates text, calls Claude,
      sends notifications, or stores memory.
    * Claude remains the only intelligent layer.
"""

from __future__ import annotations

from typing import Any

from activity.service import ActivityService
from decision.models import Trigger
from decision.rules import get_rules


class DecisionService:
    """Evaluate recent Activity Events against registered rules.

    Constructor-injected ``ActivityService`` keeps the Decision
    Engine decoupled from the storage layer.  Pass a real
    ``ActivityService`` in production, or a mock in tests.
    """

    def __init__(self, activity_service: ActivityService) -> None:
        self._activity = activity_service

    def evaluate(self) -> list[Trigger]:
        """Read recent events and run all registered rules.

        Returns:
            A list of Trigger objects from rules that fired.
            May be empty if no rules matched.
        """
        events = self._activity.get_recent(limit=50)
        triggers: list[Trigger] = []

        for rule in get_rules():
            try:
                result = rule(events)
            except Exception:
                # A broken rule must not crash the evaluation cycle.
                # Log the error and continue with the next rule.
                result = None

            if result is not None:
                triggers.append(result)

        return triggers
