"""Base MCP Server — abstract base class for all MCP service implementations.

Every MCP service (Ombre, ntfy, GitHub, Filesystem, etc.) inherits from this
class and implements initialize(), start(), and stop().

No special handling — this is a pure abstraction with no business logic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """Abstract base for every MCP server.

    Subclasses:
      - OmbreServer   (future)
      - NtfyServer    (future)
      - GithubServer  (future)
      - FilesystemServer (future)

    Lifecycle (called by ServerManager):
        initialize()
        lifecycle_start()  → start() + _running = True  (rollback on failure)
        lifecycle_stop()   → stop()  + _running = False (always, via finally)
    """

    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name: str = name
        self.version: str = version
        self._running: bool = False

    # ── Abstract lifecycle methods (subclasses implement these) ──

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the server — load config, warm up connections.

        Called once before start(). Must be implemented by every subclass.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the server — begin accepting requests.

        Called after initialize(). Must be implemented by every subclass.
        Server state (_running) is managed by lifecycle_start(), not here.
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the server — drain in-flight requests, release resources.

        Called during Hub shutdown. Must be implemented by every subclass.
        Server state (_running) is managed by lifecycle_stop(), not here.
        """
        ...

    # ── Lifecycle wrappers (called by ServerManager — single source of truth) ──

    async def lifecycle_start(self) -> None:
        """Wrapper that calls start() and manages running state with rollback.

        ServerManager calls this, NOT start() directly.
        This is the SINGLE place where _running transitions to True.

        If start() raises, stop() is called automatically to roll back
        any partially-allocated resources (sockets, files, connections).
        """
        logger.info("Server starting: %s", self.name)
        try:
            await self.start()
        except Exception:
            logger.exception("Server start failed for %s — rolling back", self.name)
            try:
                await self.stop()
            except Exception:
                logger.exception("Rollback stop also failed for %s", self.name)
            raise
        self._running = True
        logger.info("Server started: %s", self.name)

    async def lifecycle_stop(self) -> None:
        """Wrapper that calls stop() and guarantees _running = False.

        ServerManager calls this, NOT stop() directly.
        This is the SINGLE place where _running transitions to False.

        _running is set to False in a finally block so that even if
        stop() raises, the Hub shutdown proceeds cleanly and health
        checks no longer report this server as running.
        """
        logger.info("Server stopping: %s", self.name)
        try:
            await self.stop()
        finally:
            self._running = False
            logger.info("Server stopped: %s", self.name)

    # ── Concrete introspection methods ──────────────────────────

    async def health(self) -> dict[str, Any]:
        """Return a health-check summary for this server."""
        return {
            "name": self.name,
            "status": "ok" if self._running else "stopped",
        }

    async def info(self) -> dict[str, Any]:
        """Return metadata about this server."""
        return {
            "name": self.name,
            "version": self.version,
            "running": self._running,
        }

    @property
    def is_running(self) -> bool:
        """Return whether the server is currently running."""
        return self._running

    # ── Tool interface (Task004 transport layer) ─────────────────

    async def get_tools(self) -> list[dict[str, Any]]:
        """Return the tools this server exposes.

        Override in subclasses to declare available tools.
        Default: no tools.

        Tool schema:
            {"name": "...", "description": "...", "inputSchema": {...}}
        """
        return []

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Execute a tool by name.

        Override in subclasses. Default raises ToolNotFoundError.
        """
        raise ToolNotFoundError(self.name, tool_name)


class ToolNotFoundError(Exception):
    """Raised when a server does not recognize the requested tool."""

    def __init__(self, server_name: str, tool_name: str) -> None:
        super().__init__(f"Tool not found: '{tool_name}' on server '{server_name}'")
        self.server_name = server_name
        self.tool_name = tool_name
