"""Base MCP Server — abstract base class for all MCP service implementations.

Every MCP service (Ombre, ntfy, GitHub, Filesystem, etc.) inherits from this
class and implements initialize(), start(), and stop().

No special handling — this is a pure abstraction with no business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseMCPServer(ABC):
    """Abstract base for every MCP server.

    Subclasses:
      - OmbreServer   (future)
      - NtfyServer    (future)
      - GithubServer  (future)
      - FilesystemServer (future)
    """

    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name: str = name
        self.version: str = version
        self._running: bool = False

    # ── Abstract lifecycle methods ──────────────────────────────

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the server — load config, warm up connections, validate prerequisites.

        Called once before start(). Must be implemented by every subclass.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the server — begin accepting requests.

        Called after initialize(). Must be implemented by every subclass.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the server — drain in-flight requests, release resources.

        Called during Hub shutdown. Must be implemented by every subclass.
        """
        ...

    # ── Concrete introspection methods ──────────────────────────

    async def health(self) -> dict[str, Any]:
        """Return a health-check summary for this server.

        Returns:
            dict with 'name' and 'status' keys.
        """
        return {
            "name": self.name,
            "status": "ok" if self._running else "stopped",
        }

    async def info(self) -> dict[str, Any]:
        """Return metadata about this server.

        Returns:
            dict with 'name', 'version', and 'running' keys.
        """
        return {
            "name": self.name,
            "version": self.version,
            "running": self._running,
        }

    @property
    def is_running(self) -> bool:
        """Return whether the server is currently running."""
        return self._running
