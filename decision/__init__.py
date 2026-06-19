"""Decision Engine — rule-based event evaluation.

Transforms Activity Events into TriggerRequest objects by running
registered rules against recent events.  The Decision Engine
is the bridge between raw device events and autonomous Claude
awareness.

Design:
    * ``models.py`` — ``TriggerRequest`` dataclass (domain model).
    * ``rules.py``  — ``@register`` decorator + placeholder rules.
    * ``service.py`` — ``DecisionService`` (reads Activity → runs rules).
    * ``scheduler.py`` — ``run()`` blocking 60-second loop.

Flow:
    Activity → DecisionService.evaluate() → list[TriggerRequest]
        → scheduler → TriggerService.create() → SQLite → MacroDroid

Architecture constraint:
    Claude is the **only** intelligent layer.  The Decision Engine
    decides *whether* to emit a TriggerRequest — never *what to say*.
"""

from decision.models import Trigger, TriggerRequest  # Trigger is deprecated
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
    "TriggerRequest",
    "Trigger",  # deprecated — kept for backward compat
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
