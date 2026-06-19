"""Decision Engine — rule-based event evaluation.

Transforms Activity Events into Trigger objects by running
configured rules against recent events.  The Decision Engine
is the bridge between raw device events and autonomous Claude
awareness.

Phase 2 — configuration-driven:
    * All rule parameters come from ``decision/config/rules.yaml``.
    * ``RuleManager`` loads and serves config — no hard-coded values.
    * ``SessionAnalyzer`` extracts session info from events.
    * ``CooldownStore`` prevents repeated firings within a window.
    * ``DecisionService.evaluate()`` runs rules and returns Triggers.
    * ``decision.scheduler`` runs the loop — Triggers print to stdout.

Design:
    * ``models.py`` — ``Trigger`` dataclass (stable schema).
    * ``config/``  — YAML rule definitions + loader.
    * ``rules.py`` — ``@register`` decorator + real config-driven rules.
    * ``analyzers/`` — ``SessionAnalyzer`` for screen & app windows.
    * ``cooldown.py`` — ``CooldownStore`` interface + memory impl.
    * ``rule_manager.py`` — ``RuleManager`` config facade.
    * ``service.py`` — ``DecisionService`` (reads Activity → runs rules).
    * ``scheduler.py`` — ``run()`` blocking 60-second loop.

Architecture constraint:
    Claude is the **only** intelligent layer.  The Decision Engine
    decides *whether* to emit a Trigger — never *what to say*.
"""

from decision.models import Trigger
from decision.rules import (
    RuleFn,
    app_long_use_rule,
    clear_rules,
    get_cooldown_store,
    get_rule_manager,
    get_rules,
    register,
    screen_long_use_rule,
    set_cooldown_store,
    set_rule_manager,
)
from decision.service import DecisionService
from decision.scheduler import run

__all__ = [
    "Trigger",
    "RuleFn",
    "register",
    "get_rules",
    "clear_rules",
    "screen_long_use_rule",
    "app_long_use_rule",
    "get_rule_manager",
    "set_rule_manager",
    "get_cooldown_store",
    "set_cooldown_store",
    "DecisionService",
    "run",
]
