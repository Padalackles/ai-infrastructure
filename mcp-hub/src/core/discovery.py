"""Auto-Discovery — scans mcp_servers/ for MCP server modules.

Convention (fixed):
    mcp_servers/
        ombre/
            manifest.yaml
            server.py
        ntfy/
            manifest.yaml
            server.py
        ...

Discovery:
    Only scans */manifest.yaml first.
    If no manifest — fall back to server.py module scanning.

Adding a new MCP server requires only a new subdirectory with a
manifest.yaml + server.py — zero changes to Hub Core.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

import yaml

from src.core.base_server import BaseMCPServer

logger = logging.getLogger(__name__)

_DISCOVERY_DIR = "mcp_servers"


class Discovery:
    """Scans mcp_servers/ and instantiates MCP server classes."""

    def __init__(self, base_path: str | None = None) -> None:
        if base_path is None:
            base_path = str(
                Path(__file__).resolve().parent.parent.parent / _DISCOVERY_DIR
            )
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def discover(self) -> list[BaseMCPServer]:
        """Scan mcp_servers/ and return instantiated server objects.

        For each subdirectory:
          1. Try manifest.yaml  (declarative)
          2. Fall back to scanning server.py for a BaseMCPServer subclass

        Returns:
            A list of BaseMCPServer instances ready for registration.
        """
        servers: list[BaseMCPServer] = []

        if not self._base_path.exists():
            logger.warning("Discovery directory not found: %s", self._base_path)
            return servers

        for entry in sorted(self._base_path.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("_") or entry.name.startswith("."):
                continue

            server = await self._load_from_manifest(entry)
            if server is None:
                server = await self._load_from_module(entry)

            if server is not None:
                servers.append(server)

        return servers

    # ── Manifest-based (preferred) ────────────────────────────────

    async def _load_from_manifest(self, directory: Path) -> BaseMCPServer | None:
        """Try loading a server via manifest.yaml.

        manifest.yaml format:
            name: example
            version: "0.1.0"
            class: ExampleServer
            enabled: true          # optional, defaults to true

        The 'class' value must match the name of a BaseMCPServer subclass
        defined in server.py within the same directory.
        """
        manifest_path = directory / "manifest.yaml"
        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
        except Exception:
            logger.exception("Failed to parse manifest: %s", manifest_path)
            return None

        if not isinstance(manifest, dict):
            logger.warning("manifest.yaml in %s is not a mapping — skipping", directory.name)
            return None

        # Check enabled flag
        if manifest.get("enabled") is False:
            logger.info("Server %s is disabled — skipping", directory.name)
            return None

        server_class_name = manifest.get("class")
        if not server_class_name:
            logger.warning("manifest.yaml in %s missing 'class' key — skipping", directory.name)
            return None

        # Import the server.py module to find the named class
        server_py = directory / "server.py"
        if not server_py.exists():
            logger.warning(
                "manifest.yaml references class '%s' but no server.py found in %s",
                server_class_name,
                directory.name,
            )
            return None

        return await self._instantiate_class(
            directory, server_py, server_class_name, manifest
        )

    # ── Module-based (fallback) ───────────────────────────────────

    async def _load_from_module(self, directory: Path) -> BaseMCPServer | None:
        """Fallback: scan server.py for any BaseMCPServer subclass."""
        server_py = directory / "server.py"
        if not server_py.exists():
            logger.debug("No server.py in %s — skipping", directory.name)
            return None

        return await self._instantiate_class(directory, server_py, class_name=None)

    # ── Shared import + instantiate ───────────────────────────────

    async def _instantiate_class(
        self,
        directory: Path,
        server_py: Path,
        class_name: str | None,
        manifest: dict[str, Any] | None = None,
    ) -> BaseMCPServer | None:
        """Import server.py and instantiate the target class.

        Args:
            directory: The server subdirectory.
            server_py: Path to server.py.
            class_name: If set, look for this exact class name.
                        If None, find the first BaseMCPServer subclass.
            manifest: Optional manifest dict for passing constructor kwargs.

        Returns:
            An instantiated BaseMCPServer, or None.
        """
        try:
            module_name = f"{_DISCOVERY_DIR}.{directory.name}.server"
            spec = importlib.util.spec_from_file_location(module_name, server_py)
            if spec is None or spec.loader is None:
                logger.warning("Could not create module spec for %s", directory.name)
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            target_cls: type[BaseMCPServer] | None = None

            if class_name is not None:
                # Look up the explicitly named class
                obj = getattr(module, class_name, None)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseMCPServer)
                    and obj is not BaseMCPServer
                ):
                    target_cls = obj
                else:
                    logger.warning(
                        "Class '%s' not found or not a BaseMCPServer subclass in %s",
                        class_name,
                        directory.name,
                    )
                    return None
            else:
                # Scan for the first BaseMCPServer subclass
                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseMCPServer)
                        and obj is not BaseMCPServer
                    ):
                        target_cls = obj
                        break

            if target_cls is None:
                logger.debug("No BaseMCPServer subclass found in %s", directory.name)
                return None

            # Instantiate — pass manifest for constructor kwargs if available
            kwargs: dict[str, Any] = {}
            if manifest:
                kwargs["name"] = manifest.get("name", directory.name)
                kwargs["version"] = manifest.get("version", "0.1.0")

            instance = target_cls(**kwargs) if kwargs else target_cls()

            logger.info(
                "Discovered server: %s (v%s) in %s",
                instance.name,
                instance.version,
                directory.name,
            )
            return instance

        except Exception:
            logger.exception("Failed to load server from %s", directory.name)
            return None
