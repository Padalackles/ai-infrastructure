"""Unit tests for the YAML config loader."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure repo root is importable
_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision.config.loader import load_rules, reload_rules


# ── Helpers ─────────────────────────────────────────────────────────


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── Normal loading ──────────────────────────────────────────────────


def test_load_valid_yaml():
    """load_rules() returns rule dicts from a valid YAML file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rules.yaml"
        _write_yaml(
            path,
            """
rules:
  - id: test_rule
    enabled: true
    threshold_minutes: 30
""",
        )
        rules = load_rules(path)
        assert len(rules) == 1
        assert rules[0]["id"] == "test_rule"
        assert rules[0]["threshold_minutes"] == 30


def test_load_multiple_rules():
    """Multiple rules are all loaded."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rules.yaml"
        _write_yaml(
            path,
            """
rules:
  - id: rule_a
    enabled: true
  - id: rule_b
    enabled: false
  - id: rule_c
    enabled: true
""",
        )
        rules = load_rules(path)
        assert len(rules) == 3
        ids = [r["id"] for r in rules]
        assert ids == ["rule_a", "rule_b", "rule_c"]


# ── Error handling ──────────────────────────────────────────────────


def test_missing_file_returns_empty():
    """A missing config file returns [] and does not crash."""
    rules = load_rules("/nonexistent/path/rules.yaml")
    assert rules == []


def test_empty_yaml_returns_empty():
    """An empty YAML file returns []."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty.yaml"
        _write_yaml(path, "")
        rules = load_rules(path)
        assert rules == []


def test_yaml_without_rules_key():
    """YAML without a top-level 'rules' key returns []."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "no_rules.yaml"
        _write_yaml(path, "other_key: [1, 2, 3]")
        rules = load_rules(path)
        assert rules == []


def test_rules_not_a_list():
    """If 'rules' is not a list, returns []."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad_rules.yaml"
        _write_yaml(path, "rules: not_a_list")
        rules = load_rules(path)
        assert rules == []


def test_invalid_yaml_returns_empty():
    """Malformed YAML returns [] and does not crash."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "invalid.yaml"
        _write_yaml(path, ": : : bad yaml : : :")
        rules = load_rules(path)
        assert rules == []


def test_null_rules_returns_empty():
    """YAML with rules: null returns []."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "null_rules.yaml"
        _write_yaml(path, "rules:")
        rules = load_rules(path)
        assert rules == []


# ── Reload ──────────────────────────────────────────────────────────


def test_reload_reads_updated_file():
    """reload_rules() picks up changes to the YAML file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rules.yaml"
        _write_yaml(
            path,
            """
rules:
  - id: v1
    threshold_minutes: 10
""",
        )

        rules = load_rules(path)
        assert rules[0]["threshold_minutes"] == 10

        # Update the file
        _write_yaml(
            path,
            """
rules:
  - id: v2
    threshold_minutes: 99
""",
        )

        rules = reload_rules()
        assert rules[0]["id"] == "v2"
        assert rules[0]["threshold_minutes"] == 99


def test_reload_without_prior_load():
    """reload_rules() falls back to default path if load_rules() was never called."""
    # This should not crash — it'll try the default path and return []
    # (the default file may or may not exist in test context)
    rules = reload_rules()
    assert isinstance(rules, list)


# ── Rule fields ────────────────────────────────────────────────────


def test_rule_fields_preserved():
    """All YAML fields on a rule are accessible."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rules.yaml"
        _write_yaml(
            path,
            """
rules:
  - id: full_rule
    enabled: false
    trigger: test.fired
    threshold_minutes: 45
    cooldown_minutes: 90
    package: com.example.app
""",
        )
        rules = load_rules(path)
        r = rules[0]
        assert r["id"] == "full_rule"
        assert r["enabled"] is False
        assert r["trigger"] == "test.fired"
        assert r["threshold_minutes"] == 45
        assert r["cooldown_minutes"] == 90
        assert r["package"] == "com.example.app"
