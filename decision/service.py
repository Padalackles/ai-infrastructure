"""Decision Engine — evaluation service.

The DecisionService is the single entry point for the decision
pipeline.  It reads recent events from the Activity subsystem,
runs all registered rules, and collects any ``TriggerRequest``
objects they emit.

Design constraints:
    * Reads events through ActivityService — never touches SQLite.
    * Executes rules but never makes business decisions itself.
    * Returns ``TriggerRequest`` objects — domain models expressing
      intent, NOT persisted ``Trigger`` records.
    * The caller is responsible for passing ``TriggerRequest`` to
      ``TriggerService.create()``.
    * Claude remains the only intelligent layer.
"""

from __future__ import annotations

from typing import Any

from activity.service import ActivityService
from decision.models import TriggerRequest
from decision.rules import get_rules


class DecisionService:
    """Evaluate recent Activity Events against registered rules.

    Constructor-injected ``ActivityService`` keeps the Decision
    Engine decoupled from the storage layer.  Pass a real
    ``ActivityService`` in production, or a mock in tests.
    """

    def __init__(self, activity_service: ActivityService) -> None:
        self._activity = activity_service

    def evaluate(self) -> list[TriggerRequest]:
        """Read recent events and run all registered rules.

        Returns:
            A list of ``TriggerRequest`` objects from rules that fired.
            May be empty if no rules matched.
            The caller should pass each request to ``TriggerService.create()``.
        """
        events = self._activity.get_recent(limit=50)
        requests: list[TriggerRequest] = []

        for rule in get_rules():
            try:
                result = rule(events)
            except Exception:
                # A broken rule must not crash the evaluation cycle.
                # Log the error and continue with the next rule.
                result = None

            if result is not None:
                requests.append(result)

        return requests
