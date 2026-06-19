"""Decision Engine — rule-based event evaluation.

Transforms Activity Events into Trigger objects by running
registered rules against recent events.  The Decision Engine
is the bridge between raw device events and autonomous Claude
awareness.

Phase 1 — console-only:
    * ``DecisionService.evaluate()`` reads events and runs rules.
    * Rules return ``Trigger`` or ``None``.
    * ``decision.scheduler`` runs the loop — Triggers print to stdout.
    * No Claude, no ntfy, no reminder text.

Design:
    * ``models.py`` — ``Trigger`` dataclass (stable schema).
    * ``rules.py``  — ``@register`` decorator + placeholder rules.
    * ``service.py`` — ``DecisionService`` (reads Activity → runs rules).
    * ``scheduler.py`` — ``run()`` blocking 60-second loop.

Architecture constraint:
    Claude is the **only** intelligent layer.  The Decision Engine
    decides *whether* to emit a Trigger — never *what to say*.
"""

from decision.models import Trigger
from decision.rules import (
    RuleFn,
    battery_low_rule,
    clear_rules,
    focus_timeout_rule,
    get_rules,
    register,
    screen_awake_rule,
)
from decision.service import DecisionService
from decision.scheduler import run

__all__ = [
    "Trigger",
    "RuleFn",
    "register",
    "get_rules",
    "clear_rules",
    "battery_low_rule",
    "screen_awake_rule",
    "focus_timeout_rule",
    "DecisionService",
    "run",
]
