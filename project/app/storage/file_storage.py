"""File storage — local JSON read/write operations."""

import json
import os
from pathlib import Path
from typing import Any


class FileStorage:
    """Local JSON file storage."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve a key to a file path."""
        return self._base_dir / f"{key}.json"

    def save_json(self, key: str, data: dict[str, Any]) -> None:
        """Save a dictionary as a JSON file."""
        path = self._resolve(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def load_json(self, key: str) -> dict[str, Any] | None:
        """Load a JSON file. Returns None if not found."""
        path = self._resolve(key)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete(self, key: str) -> bool:
        """Delete a JSON file. Returns True if deleted, False if not found."""
        path = self._resolve(key)
        if path.exists():
            os.remove(path)
            return True
        return False

    def list(self) -> list[str]:
        """List all stored keys (filenames without extension)."""
        return [p.stem for p in self._base_dir.glob("*.json")]
