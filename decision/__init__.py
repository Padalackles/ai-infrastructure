"""Decision Engine — rule-based event evaluation.

Transforms Activity Events into TriggerRequest objects by running
configured rules against recent events.  The Decision Engine
is the bridge between raw device events and autonomous Claude
awareness.

Phase 2 — configuration-driven:
    * All rule parameters come from ``decision/config/rules.yaml``.
    * ``RuleManager`` loads and serves config — no hard-coded values.
    * ``SessionAnalyzer`` extracts session info from events.
    * ``CooldownStore`` prevents repeated firings within a window.
    * ``DecisionService.evaluate()`` runs rules and returns TriggerRequests.
    * ``decision.scheduler`` runs the loop — TriggerRequests flow to SQLite.

Design:
    * ``models.py`` — ``TriggerRequest`` dataclass (domain model).
    * ``config/``  — YAML rule definitions + loader.
    * ``rules.py`` — ``@register`` decorator + real config-driven rules.
    * ``analyzers/`` — ``SessionAnalyzer`` for screen & app windows.
    * ``cooldown.py`` — ``CooldownStore`` interface + memory impl.
    * ``rule_manager.py`` — ``RuleManager`` config facade.
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
    app_long_use_rule,
    battery_low_rule,
    clear_rules,
    get_cooldown_store,
    get_rule_manager,
    get_rules,
    late_sleep_rule,
    procrastination_rule,
    register,
    screen_long_use_rule,
    set_cooldown_store,
    set_rule_manager,
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
    "screen_long_use_rule",
    "app_long_use_rule",
    "battery_low_rule",
    "procrastination_rule",
    "late_sleep_rule",
    "get_rule_manager",
    "set_rule_manager",
    "get_cooldown_store",
    "set_cooldown_store",
    "DecisionService",
    "run",
]
