"""Configuration system — singleton, reads config/config.yaml."""

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """Singleton configuration loaded from YAML."""

    _instance = None
    _data: dict[str, Any] = {}

    def __new__(cls, config_path: str | None = None) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load(config_path)
        return cls._instance

    def _load(self, config_path: str | None = None) -> None:
        if config_path is None:
            config_path = os.getenv(
                "CONFIG_PATH",
                str(Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"),
            )
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any | None = None) -> Any:
        """Get a config value by dot-separated key (e.g. 'server.host')."""
        keys = key.split(".")
        value: Any = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @property
    def data(self) -> dict[str, Any]:
        """Return the full configuration dictionary."""
        return self._data
