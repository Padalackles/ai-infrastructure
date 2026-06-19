"""Decision Engine — rule framework.

Each rule is an independent function with the signature::

    (events: list[dict]) -> Trigger | None

Rules are registered via the ``@register`` decorator.  The
DecisionService calls every registered rule for each evaluation
cycle — rules decide independently whether to fire.

Adding a new rule:
    1. Write a function matching the rule signature.
    2. Decorate it with ``@register``.
    3. Zero changes to DecisionService or any other file.

Current rules are **placeholder stubs** that return ``None``.
They exist to validate the framework and will be implemented
in Phase 2+.
"""

from __future__ import annotations

from typing import Any, Callable

from decision.models import Trigger

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


# ── Placeholder rules ──────────────────────────────────────────────


@register
def battery_low_rule(events: list[dict[str, Any]]) -> Trigger | None:
    """Check for recent battery.low events.

    Placeholder — returns None.  Will be implemented in Phase 2.
    """
    return None


@register
def screen_awake_rule(events: list[dict[str, Any]]) -> Trigger | None:
    """Check for recent device.awake events.

    Placeholder — returns None.  Will be implemented in Phase 2.
    """
    return None


@register
def focus_timeout_rule(events: list[dict[str, Any]]) -> Trigger | None:
    """Check for device inactivity (focus timeout).

    Placeholder — returns None.  Will be implemented in Phase 2.
    """
    return None
