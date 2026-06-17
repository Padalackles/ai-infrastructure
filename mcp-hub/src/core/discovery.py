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

Error isolation:
    A broken manifest or import failure in one server never blocks
    discovery of other servers. Errors are logged and the Hub continues.

No print() — all output goes through the logger. CLI output is the
launcher's responsibility (uvicorn, docker, systemd, etc.).
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from src.core.base_server import BaseMCPServer

logger = logging.getLogger("discovery")

_DISCOVERY_DIR = "mcp_servers"


# ── Result ────────────────────────────────────────────────────


@dataclass
class DiscoveryResult:
    """Holds the outcome of a discovery scan."""

    loaded: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)  # (name, reason)


# ── Errors ────────────────────────────────────────────────────


class DiscoveryError(Exception):
    """Non-fatal discovery error — isolated to a single server.

    Subclasses are reserved for future structured error handling:
      - ManifestError   — manifest.yaml parse/validation errors
      - ImportError     — server.py import/instantiate failures
      - ValidationError — version or capability mismatches
    """

    def __init__(self, server_dir: str, reason: str) -> None:
        super().__init__(f"Discovery failed for '{server_dir}': {reason}")
        self.server_dir: str = server_dir
        self.reason: str = reason


# ── Scanner ───────────────────────────────────────────────────


class Discovery:
    """Scans mcp_servers/ and instantiates MCP server classes."""

    def __init__(self, base_path: str | None = None) -> None:
        if base_path is None:
            base_path = str(
                Path(__file__).resolve().parent.parent.parent.parent / _DISCOVERY_DIR
            )
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def discover(self) -> tuple[list[BaseMCPServer], DiscoveryResult]:
        """Scan mcp_servers/ and return instantiated servers + result metadata.

        For each subdirectory:
          1. Try manifest.yaml (declarative)
          2. Fall back to scanning server.py for a BaseMCPServer subclass

        Errors in one server are isolated — they never block other servers.

        Returns:
            (servers, result) where result tracks loaded and failed servers.
        """
        servers: list[BaseMCPServer] = []
        result = DiscoveryResult()

        if not self._base_path.exists():
            logger.warning("Discovery directory not found: %s", self._base_path)
            return servers, result

        logger.info("Scanning MCP namespace: %s", self._base_path)

        entries = [
            e for e in sorted(self._base_path.iterdir())
            if e.is_dir() and not e.name.startswith("_") and not e.name.startswith(".")
        ]

        if not entries:
            logger.info("No server directories found")
            return servers, result

        for entry in entries:
            logger.info("Found directory: %s", entry.name)

            try:
                server = await self._load_from_manifest(entry)
                if server is None:
                    server = await self._load_from_module(entry)
            except DiscoveryError as exc:
                logger.error("Load failed for %s: %s", exc.server_dir, exc.reason)
                result.failed.append((exc.server_dir, exc.reason))
                continue
            except Exception as exc:
                logger.exception("Unexpected error loading %s", entry.name)
                result.failed.append((entry.name, str(exc)))
                continue

            if server is not None:
                servers.append(server)
                result.loaded.append(server.name)
                logger.info("Server ready: %s (v%s)", server.name, server.version)
            else:
                reason = "No manifest.yaml or server.py found, or no BaseMCPServer subclass"
                logger.warning("Skipped %s: %s", entry.name, reason)
                result.failed.append((entry.name, reason))

        # Summary
        logger.info(
            "Discovery complete — loaded: %d, failed: %d",
            len(result.loaded), len(result.failed),
        )
        for name in result.loaded:
            logger.info("  loaded: %s", name)
        for name, reason in result.failed:
            logger.warning("  failed: %s — %s", name, reason)

        return servers, result

    # ── Manifest-based (preferred) ────────────────────────────────

    async def _load_from_manifest(self, directory: Path) -> BaseMCPServer | None:
        """Try loading a server via manifest.yaml."""
        manifest_path = directory / "manifest.yaml"
        if not manifest_path.exists():
            return None

        logger.info("Loading manifest: %s", manifest_path)

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
        except Exception as exc:
            raise DiscoveryError(directory.name, f"manifest.yaml parse error: {exc}") from exc

        if not isinstance(manifest, dict):
            raise DiscoveryError(directory.name, "manifest.yaml is not a mapping")

        if manifest.get("enabled") is False:
            logger.info("Server %s is disabled — skipping", directory.name)
            return None

        server_class_name = manifest.get("class")
        if not server_class_name:
            raise DiscoveryError(directory.name, "manifest.yaml missing 'class' key")

        server_py = directory / "server.py"
        if not server_py.exists():
            raise DiscoveryError(
                directory.name,
                f"manifest.yaml references class '{server_class_name}' but server.py not found",
            )

        return await self._instantiate_class(
            directory, server_py, server_class_name, manifest
        )

    # ── Module-based (fallback) ───────────────────────────────────

    async def _load_from_module(self, directory: Path) -> BaseMCPServer | None:
        """Fallback: scan server.py for any BaseMCPServer subclass."""
        server_py = directory / "server.py"
        if not server_py.exists():
            return None

        logger.info("No manifest in %s — scanning server.py", directory.name)
        return await self._instantiate_class(directory, server_py, class_name=None)

    # ── Shared import + instantiate ───────────────────────────────

    async def _instantiate_class(
        self,
        directory: Path,
        server_py: Path,
        class_name: str | None,
        manifest: dict[str, Any] | None = None,
    ) -> BaseMCPServer | None:
        """Import server.py and instantiate the target class."""
        try:
            module_name = f"{_DISCOVERY_DIR}.{directory.name}.server"
            spec = importlib.util.spec_from_file_location(module_name, server_py)
            if spec is None or spec.loader is None:
                raise DiscoveryError(directory.name, "Could not create module spec")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            target_cls: type[BaseMCPServer] | None = None

            if class_name is not None:
                obj = getattr(module, class_name, None)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseMCPServer)
                    and obj is not BaseMCPServer
                ):
                    target_cls = obj
                else:
                    raise DiscoveryError(
                        directory.name,
                        f"Class '{class_name}' not found or not a BaseMCPServer subclass",
                    )
            else:
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
                return None

            kwargs: dict[str, Any] = {}
            if manifest:
                kwargs["name"] = manifest.get("name", directory.name)
                kwargs["version"] = manifest.get("version", "0.1.0")

            instance = target_cls(**kwargs) if kwargs else target_cls()

            logger.info(
                "Discovered server: %s (v%s) in %s",
                instance.name, instance.version, directory.name,
            )
            return instance

        except DiscoveryError:
            raise
        except Exception as exc:
            raise DiscoveryError(directory.name, f"Import/instantiate failed: {exc}") from exc
