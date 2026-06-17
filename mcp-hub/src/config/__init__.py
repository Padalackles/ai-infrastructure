"""Configuration — unified configuration loading.

Reads config.yaml and exposes structured access.
Environment variables override file values.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = str(Path(__file__).resolve().parent.parent.parent / "config.yaml")


def load_config(path: str | None = None) -> dict[str, Any]:
    """Load and return the YAML configuration.

    Args:
        path: Path to config.yaml. Defaults to <mcp-hub>/config.yaml.

    Returns:
        Config dict, or empty dict if the file is missing/malformed.
    """
    config_path = Path(path or os.getenv("MCP_HUB_CONFIG", DEFAULT_CONFIG_PATH))
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                logger.info("Config loaded: %s", config_path)
                return data
        except Exception:
            logger.exception("Failed to parse config: %s", config_path)
    logger.warning("Config file not found: %s — using defaults", config_path)
    return {}
