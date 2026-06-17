"""MCP Hub — Core module (backward-compatible re-exports).

Modules reorganized into dedicated packages:
  - lifecycle/   BaseMCPServer, ToolNotFoundError
  - registry/    ServerManager
  - loader/      Discovery, Loader, PythonLoader
  - config/      load_config()
  - models/      (future Pydantic models)

events.py stays in core/ — it has no dedicated module yet.
"""

from src.core.events import EventBus
from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError
from src.loader.discovery import Discovery, DiscoveryError, DiscoveryResult
from src.loader.loader import Loader, PythonLoader
from src.registry.server_manager import ServerManager

__all__ = [
    "BaseMCPServer",
    "Discovery",
    "DiscoveryError",
    "DiscoveryResult",
    "EventBus",
    "Loader",
    "PythonLoader",
    "ServerManager",
    "ToolNotFoundError",
]
