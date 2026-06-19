"""Unit tests for RuleManager."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision.rule_manager import RuleManager


# ── Helpers ─────────────────────────────────────────────────────────


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_manager(**rule_overrides) -> RuleManager:
    """Create a RuleManager pointing at a temp YAML file."""
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "rules.yaml"
    rule = {
        "id": "test_rule",
        "enabled": True,
        "trigger": "test.fired",
        "threshold_minutes": 30,
        "cooldown_minutes": 60,
    }
    rule.update(rule_overrides)
    import yaml

    _write_yaml(path, yaml.dump({"rules": [rule]}))
    return RuleManager(config_path=str(path))


# ── get_rule ────────────────────────────────────────────────────────


def test_get_rule_returns_config():
    """get_rule() returns the full rule dict."""
    mgr = _make_manager()
    rule = mgr.get_rule("test_rule")
    assert rule is not None
    assert rule["id"] == "test_rule"
    assert rule["threshold_minutes"] == 30


def test_get_rule_unknown_id():
    """get_rule() returns None for an unknown rule id."""
    mgr = _make_manager()
    assert mgr.get_rule("nonexistent") is None


# ── get_enabled_rules ──────────────────────────────────────────────


def test_get_enabled_rules_includes_enabled():
    """Enabled rules are returned."""
    mgr = _make_manager(enabled=True)
    rules = mgr.get_enabled_rules()
    assert len(rules) == 1


def test_get_enabled_rules_excludes_disabled():
    """Disabled rules are excluded."""
    mgr = _make_manager(enabled=False)
    rules = mgr.get_enabled_rules()
    assert len(rules) == 0


# ── Reload ──────────────────────────────────────────────────────────


def test_reload_picks_up_changes():
    """After editing the YAML, reload() sees the changes."""
    mgr = _make_manager(threshold_minutes=10)
    assert mgr.get_rule("test_rule")["threshold_minutes"] == 10

    # Edit the file directly
    import yaml

    path = Path(mgr._config_path)
    _write_yaml(
        path,
        yaml.dump(
            {
                "rules": [
                    {
                        "id": "test_rule",
                        "enabled": True,
                        "threshold_minutes": 99,
                    }
                ]
            }
        ),
    )

    mgr.reload()
    assert mgr.get_rule("test_rule")["threshold_minutes"] == 99


# ── Multiple rules ─────────────────────────────────────────────────


def test_multiple_rules():
    """RuleManager handles multiple rules, only returning enabled ones."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rules.yaml"
        import yaml

        data = {
            "rules": [
                {"id": "r1", "enabled": True},
                {"id": "r2", "enabled": False},
                {"id": "r3", "enabled": True},
            ]
        }
        _write_yaml(path, yaml.dump(data))
        mgr = RuleManager(config_path=str(path))

        enabled = mgr.get_enabled_rules()
        assert len(enabled) == 2
        ids = [r["id"] for r in enabled]
        assert ids == ["r1", "r3"]

        assert mgr.get_rule("r2") is not None  # still accessible by id
        assert mgr.get_rule("r2")["enabled"] is False


# ── Empty config ────────────────────────────────────────────────────


def test_empty_config_no_crash():
    """An empty config file produces an empty rule list."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty.yaml"
        _write_yaml(path, "")
        mgr = RuleManager(config_path=str(path))
        assert mgr.get_enabled_rules() == []
        assert mgr.get_rule("anything") is None
