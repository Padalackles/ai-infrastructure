"""Decision Engine — rule manager.

The RuleManager is the single source of truth for rule configuration.
DecisionService and individual rules read parameters through it —
they never touch YAML directly.
"""

from __future__ import annotations

import logging
from typing import Any

from decision.config.loader import load_rules, reload_rules

logger = logging.getLogger("mcp-hub.decision.rule_manager")


class RuleManager:
    """Load and serve rule configuration.

    Constructor-injected *config_path* makes the manager testable:
    point it at a temporary YAML file during tests.
    """

    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = config_path
        self._rules: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        """(Re-)load rules from the YAML file."""
        self._rules = load_rules(self._config_path)

    def reload(self) -> None:
        """Hot-reload rules from the same file."""
        self._rules = reload_rules()

    def get_enabled_rules(self) -> list[dict[str, Any]]:
        """Return all rules whose enabled flag is truthy."""
        return [r for r in self._rules if r.get("enabled", True)]

    def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        """Return the rule dict for *rule_id*, or None if not found."""
        for rule in self._rules:
            if rule.get("id") == rule_id:
                return rule
        return None
