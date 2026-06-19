"""Decision Engine — rule framework (configuration-driven).

Each rule is an independent function with the signature::

    (events: list[dict]) -> Trigger | None

Rules are registered via the ``@register`` decorator.  The
DecisionService calls every registered rule for each evaluation
cycle — rules decide independently whether to fire.

Rule parameters (thresholds, apps, cooldowns) come from the
``RuleManager`` (YAML config).  Rules MUST NOT hard-code values.

Session analysis is delegated to ``SessionAnalyzer`` — rules
never scan raw events directly.

Adding a new rule:
    1. Define its config in ``decision/config/rules.yaml``.
    2. Write a function matching the rule signature.
    3. Decorate it with ``@register``.
    4. Import the module so registration fires.
    5. Zero changes to DecisionService.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from decision.analyzers.session import SessionAnalyzer
from decision.cooldown import CooldownStore, MemoryCooldownStore
from decision.models import Trigger
from decision.rule_manager import RuleManager

# ── Rule type ──────────────────────────────────────────────────────

#: Signature for a rule function.
RuleFn = Callable[[list[dict[str, Any]]], Trigger | None]

# ── Registry ───────────────────────────────────────────────────────

_RULES: list[RuleFn] = []


def register(rule_fn: RuleFn) -> RuleFn:
    """Register a rule function for evaluation.

    Intended for use as a decorator::

        @register
        def my_rule(events: list[dict]) -> Trigger | None:
            ...

    Rules are evaluated in registration order.
    """
    _RULES.append(rule_fn)
    return rule_fn


def get_rules() -> list[RuleFn]:
    """Return a copy of the registered rules list."""
    return list(_RULES)


def clear_rules() -> None:
    """Remove all registered rules (intended for tests)."""
    _RULES.clear()


# ── Shared singletons (swappable for tests) ────────────────────────

_rule_manager: RuleManager | None = None
_cooldown_store: CooldownStore | None = None


def get_rule_manager() -> RuleManager:
    """Return the module-level RuleManager, creating it on first call."""
    global _rule_manager
    if _rule_manager is None:
        _rule_manager = RuleManager()
    return _rule_manager


def get_cooldown_store() -> CooldownStore:
    """Return the module-level CooldownStore, creating it on first call."""
    global _cooldown_store
    if _cooldown_store is None:
        _cooldown_store = MemoryCooldownStore()
    return _cooldown_store


def set_rule_manager(mgr: RuleManager | None) -> None:
    """Inject a RuleManager (for tests).  Pass None to reset to default."""
    global _rule_manager
    _rule_manager = mgr


def set_cooldown_store(store: CooldownStore) -> None:
    """Inject a CooldownStore (for tests)."""
    global _cooldown_store
    _cooldown_store = store


# ── Helper: cooldown guard ─────────────────────────────────────────


def _is_in_cooldown(rule_id: str, cooldown_minutes: int) -> bool:
    """Return True if *rule_id* is still within its cooldown window."""
    store = get_cooldown_store()
    last = store.get(rule_id)
    if last is None:
        return False
    elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60.0
    return elapsed < cooldown_minutes


def _record_trigger(rule_id: str) -> None:
    """Record a trigger event for cooldown tracking."""
    store = get_cooldown_store()
    store.set(rule_id, datetime.now(timezone.utc))


# ── Real rules ─────────────────────────────────────────────────────


@register
def screen_long_use_rule(events: list[dict[str, Any]]) -> Trigger | None:
    """Fire when the current screen session exceeds the threshold.

    Config keys (in rules.yaml):
        * threshold_minutes  — minimum screen-on duration to trigger.
        * cooldown_minutes   — quiet period after triggering.
    """
    mgr = get_rule_manager()
    config = mgr.get_rule("screen_long_use")
    if config is None or not config.get("enabled"):
        return None

    threshold = config.get("threshold_minutes")
    if not isinstance(threshold, (int, float)):
        return None

    cooldown = config.get("cooldown_minutes", 60)

    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_screen_session()
    if session is None:
        return None

    if session["duration_minutes"] < threshold:
        return None

    if _is_in_cooldown("screen_long_use", cooldown):
        return None

    _record_trigger("screen_long_use")

    return Trigger(
        type="screen.long_use",
        payload={
            "threshold_minutes": threshold,
            "actual_minutes": session["duration_minutes"],
        },
    )


@register
def app_long_use_rule(events: list[dict[str, Any]]) -> Trigger | None:
    """Fire when the current app session exceeds the threshold.

    Config keys (in rules.yaml):
        * package            — Android package name to monitor.
        * threshold_minutes  — minimum app-usage duration to trigger.
        * cooldown_minutes   — quiet period after triggering.
    """
    mgr = get_rule_manager()
    config = mgr.get_rule("app_long_use")
    if config is None or not config.get("enabled"):
        return None

    package = config.get("package")
    if not package or not isinstance(package, str):
        return None

    threshold = config.get("threshold_minutes")
    if not isinstance(threshold, (int, float)):
        return None

    cooldown = config.get("cooldown_minutes", 120)

    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_app_session(package)
    if session is None:
        return None

    if session["duration_minutes"] < threshold:
        return None

    if _is_in_cooldown("app_long_use", cooldown):
        return None

    _record_trigger("app_long_use")

    return Trigger(
        type="app.long_use",
        payload={
            "app": package,
            "threshold_minutes": threshold,
            "actual_minutes": session["duration_minutes"],
        },
    )
