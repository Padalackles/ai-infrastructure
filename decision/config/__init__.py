"""Decision Engine — configuration layer.

Provides:
    * ``load_rules()`` — read rules from YAML config.
    * ``reload_rules()`` — hot-reload rules without restart.
"""

from decision.config.loader import load_rules, reload_rules

__all__ = ["load_rules", "reload_rules"]
