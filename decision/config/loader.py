"""Decision Engine — YAML config loader.

Reads ``rules.yaml`` from the decision/config directory.  All errors
are logged — a broken config file must not crash the Decision Engine.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("mcp-hub.decision.config")

_DEFAULT_PATH = Path(__file__).resolve().parent / "rules.yaml"
_current_path: Path | None = None


def load_rules(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load rule definitions from *path* (default: decision/config/rules.yaml).

    Returns a list of rule dicts. May be empty on error.
    Errors are logged — the caller receives an empty list.
    """
    target = _resolve_path(path)
    global _current_path
    _current_path = target
    return _read_rules(target)


def reload_rules() -> list[dict[str, Any]]:
    """Re-read the rules file last opened by load_rules()."""
    global _current_path
    if _current_path is None:
        _current_path = _DEFAULT_PATH
    return _read_rules(_current_path)


def _resolve_path(path: str | Path | None) -> Path:
    if path is None:
        return _DEFAULT_PATH
    if isinstance(path, str):
        return Path(path)
    return path


def _read_rules(path: Path) -> list[dict[str, Any]]:
    try:
        if not path.exists():
            logger.error("Rules config file not found: %s", path)
            return []
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if data is None:
            logger.warning("Rules config file is empty: %s", path)
            return []
        if not isinstance(data, dict):
            logger.error("Rules config root must be a dict, got %s", type(data).__name__)
            return []
        rules = data.get("rules")
        if rules is None:
            logger.warning("No rules key in config file: %s", path)
            return []
        if not isinstance(rules, list):
            logger.error("rules must be a list, got %s", type(rules).__name__)
            return []
        return rules
    except yaml.YAMLError as exc:
        logger.error("YAML parse error in %s: %s", path, exc)
        return []
    except OSError as exc:
        logger.error("Cannot read rules file %s: %s", path, exc)
        return []
