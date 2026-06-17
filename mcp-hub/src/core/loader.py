"""Loader — abstraction for MCP server loading strategies.

Discovery delegates to a Loader to instantiate a server from a directory.
The default PythonLoader preserves current behavior (import server.py).
Future loaders: DockerLoader, RemoteLoader.
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml

from src.core.base_server import BaseMCPServer

logger = logging.getLogger(__name__)


# ── Abstract ──────────────────────────────────────────────────


class Loader(ABC):
    """Abstract loader — loads a BaseMCPServer from a directory."""

    @abstractmethod
    async def load(self, directory: Path, manifest: dict[str, Any] | None) -> BaseMCPServer | None:
        """Load and instantiate a server from the given directory.

        Args:
            directory: Path to the server subdirectory.
            manifest: Parsed manifest.yaml dict, or None if no manifest exists.

        Returns:
            A BaseMCPServer instance, or None if loading fails.
        """
        ...


# ── Python (current) ──────────────────────────────────────────


class PythonLoader(Loader):
    """Loads a server by importing its server.py module."""

    async def load(
        self, directory: Path, manifest: dict[str, Any] | None
    ) -> BaseMCPServer | None:
        server_py = directory / "server.py"
        if not server_py.exists():
            logger.debug("No server.py in %s", directory.name)
            return None

        class_name = manifest.get("class") if manifest else None
        return await self._import_and_instantiate(directory, server_py, class_name, manifest)

    async def _import_and_instantiate(
        self,
        directory: Path,
        server_py: Path,
        class_name: str | None,
        manifest: dict[str, Any] | None,
    ) -> BaseMCPServer | None:
        module_name = f"mcp_servers.{directory.name}.server"
        spec = importlib.util.spec_from_file_location(module_name, server_py)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create module spec for {directory.name}")

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

        return target_cls(**kwargs) if kwargs else target_cls()
