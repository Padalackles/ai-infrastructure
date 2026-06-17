"""Auto-Discovery — scans mcp_servers/ for MCP server modules.

Error isolation: a broken plugin never blocks others.
All output through the logger — no print().
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.core.base_server import BaseMCPServer
from src.core.loader import Loader, PythonLoader

logger = logging.getLogger("discovery")

_DISCOVERY_DIR = "mcp_servers"


@dataclass
class DiscoveryResult:
    loaded: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


class DiscoveryError(Exception):
    def __init__(self, server_dir: str, reason: str) -> None:
        super().__init__(f"Discovery failed for '{server_dir}': {reason}")
        self.server_dir: str = server_dir
        self.reason: str = reason


class Discovery:
    """Scans mcp_servers/ using a pluggable Loader."""

    def __init__(self, base_path: str | None = None, loader: Loader | None = None) -> None:
        if base_path is None:
            base_path = str(
                Path(__file__).resolve().parent.parent.parent.parent / _DISCOVERY_DIR
            )
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._loader: Loader = loader or PythonLoader()

    async def discover(self) -> tuple[list[BaseMCPServer], DiscoveryResult]:
        servers: list[BaseMCPServer] = []
        result = DiscoveryResult()

        if not self._base_path.exists():
            logger.warning("Discovery directory not found: %s", self._base_path)
            return servers, result

        logger.info("Scanning MCP namespace: %s", self._base_path)
        entries = sorted(
            e for e in self._base_path.iterdir()
            if e.is_dir() and not e.name.startswith("_") and not e.name.startswith(".")
        )
        if not entries:
            logger.info("No server directories found")
            return servers, result

        for entry in entries:
            logger.info("Found directory: %s", entry.name)
            try:
                manifest = self._read_manifest(entry)
                if manifest and manifest.get("enabled") is False:
                    logger.info("Server %s is disabled — skipping", entry.name)
                    continue
                server = await self._loader.load(entry, manifest)
                if server is not None:
                    servers.append(server)
                    result.loaded.append(server.name)
                    logger.info("Server ready: %s (v%s)", server.name, server.version)
                else:
                    reason = "Loader returned None"
                    logger.warning("Skipped %s: %s", entry.name, reason)
                    result.failed.append((entry.name, reason))
            except DiscoveryError as exc:
                logger.error("Load failed for %s: %s", exc.server_dir, exc.reason)
                result.failed.append((exc.server_dir, exc.reason))
            except Exception as exc:
                logger.exception("Unexpected error loading %s", entry.name)
                result.failed.append((entry.name, str(exc)))

        logger.info("Discovery complete — loaded: %d, failed: %d",
                     len(result.loaded), len(result.failed))
        for name in result.loaded:
            logger.info("  loaded: %s", name)
        for name, reason in result.failed:
            logger.warning("  failed: %s — %s", name, reason)
        return servers, result

    def _read_manifest(self, directory: Path) -> dict[str, Any] | None:
        manifest_path = directory / "manifest.yaml"
        if not manifest_path.exists():
            return None
        logger.info("Loading manifest: %s", manifest_path)
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as exc:
            raise DiscoveryError(directory.name, f"manifest.yaml parse error: {exc}") from exc
        if not isinstance(data, dict):
            raise DiscoveryError(directory.name, "manifest.yaml is not a mapping")
        if not data.get("class"):
            raise DiscoveryError(directory.name, "manifest.yaml missing 'class' key")
        return data
