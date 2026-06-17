"""Server Manager — lifecycle management for registered MCP servers.

Responsibilities:
  - Register MCP server instances
  - Start all servers (calls initialize() then start())
  - Stop all servers gracefully
  - Query server status for /health and /status endpoints

No business logic — purely orchestration.
"""

from __future__ import annotations

import logging
from typing import Any

from src.core.base_server import BaseMCPServer

logger = logging.getLogger(__name__)


class ServerManager:
    """Manages the full lifecycle of registered MCP servers."""

    def __init__(self) -> None:
        self._servers: dict[str, BaseMCPServer] = {}

    # ── Registration ────────────────────────────────────────────

    def register(self, server: BaseMCPServer) -> None:
        """Register an MCP server instance.

        Args:
            server: A concrete BaseMCPServer subclass instance.
        """
        self._servers[server.name] = server
        logger.info("Registered server: %s (v%s)", server.name, server.version)

    def unregister(self, name: str) -> bool:
        """Unregister a server by name.

        Returns:
            True if removed, False if not found.
        """
        if name in self._servers:
            del self._servers[name]
            logger.info("Unregistered server: %s", name)
            return True
        return False

    # ── Lifecycle ───────────────────────────────────────────────

    async def start_all(self) -> None:
        """Initialize and start every registered server.

        Each server gets initialize() called first, then start().
        Failures are logged but do not prevent other servers from starting.
        """
        for name, server in self._servers.items():
            try:
                logger.info("Initializing server: %s", name)
                await server.initialize()
                await server.start()
                server._running = True
                logger.info("Server started: %s", name)
            except Exception:
                logger.exception("Failed to start server: %s", name)

    async def stop_all(self) -> None:
        """Stop every registered server gracefully.

        Each server's stop() is called. Failures are logged but do not
        prevent other servers from stopping.
        """
        for name, server in self._servers.items():
            try:
                logger.info("Stopping server: %s", name)
                await server.stop()
                server._running = False
                logger.info("Server stopped: %s", name)
            except Exception:
                logger.exception("Failed to stop server: %s", name)

    # ── Query ───────────────────────────────────────────────────

    def get_server(self, name: str) -> BaseMCPServer | None:
        """Resolve a server by name.

        Returns:
            The BaseMCPServer instance, or None if not registered.
        """
        return self._servers.get(name)

    def list_servers(self) -> list[dict[str, Any]]:
        """Return metadata for all registered servers.

        Used by /health and /status endpoints to report the server inventory.

        Returns:
            A list of info dicts (one per registered server).
        """
        return [
            {"name": s.name, "version": s.version, "running": s.is_running}
            for s in self._servers.values()
        ]

    @property
    def count(self) -> int:
        """Return the number of registered servers."""
        return len(self._servers)
