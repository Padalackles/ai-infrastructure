"""Server Manager — lifecycle management for registered MCP servers.

Responsibilities:
  - Register MCP server instances
  - Start all servers (initialize → lifecycle_start with rollback)
  - Stop all servers gracefully (lifecycle_stop with finally guarantee)
  - Query server status for /health and /status endpoints
  - Track failed servers for diagnostics

No business logic — purely orchestration.
Server running state lives ONLY in BaseMCPServer._running.
ServerManager never touches _running directly.
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
        self._failed: set[str] = set()

    # ── Registration ────────────────────────────────────────────

    def register(self, server: BaseMCPServer) -> None:
        """Register an MCP server instance."""
        self._servers[server.name] = server
        logger.info("Registered server: %s (v%s)", server.name, server.version)

    def unregister(self, name: str) -> bool:
        """Unregister a server by name."""
        if name in self._servers:
            del self._servers[name]
            self._failed.discard(name)
            logger.info("Unregistered server: %s", name)
            return True
        return False

    # ── Lifecycle ───────────────────────────────────────────────

    async def start_all(self) -> None:
        """Initialize and start every registered server.

        Lifecycle per server:
            initialize() → lifecycle_start()
                If lifecycle_start() fails after initialize() succeeds,
                lifecycle_stop() is called to roll back any resources
                allocated by initialize() (or partially by start()).

        lifecycle_start() is the SINGLE source of truth for _running = True.
        ServerManager never sets _running directly.

        Failures are isolated — one failing server does not prevent others.
        """
        self._failed.clear()
        for name, server in self._servers.items():
            try:
                logger.info("Initializing server: %s", name)
                await server.initialize()

                try:
                    await server.lifecycle_start()
                except Exception:
                    logger.exception(
                        "Server start failed for %s after initialize succeeded — rolling back", name
                    )
                    # Rollback: call lifecycle_stop to clean up leaked resources.
                    # lifecycle_stop() has a finally that guarantees _running = False.
                    try:
                        await server.lifecycle_stop()
                    except Exception:
                        logger.exception("Rollback stop also failed for %s", name)
                    self._failed.add(name)

            except Exception:
                # initialize() itself failed — no resources to roll back
                logger.exception("Failed to start server: %s", name)
                self._failed.add(name)

    async def stop_all(self) -> None:
        """Stop every registered server gracefully.

        lifecycle_stop() is the SINGLE source of truth for _running = False.
        Its finally block guarantees _running is cleared even if stop() raises.
        ServerManager never sets _running directly.

        Failures are isolated — one failing server does not prevent others.
        """
        for name, server in self._servers.items():
            try:
                if server.is_running:
                    await server.lifecycle_stop()
            except Exception:
                logger.exception("Failed to stop server: %s", name)

    # ── Query ───────────────────────────────────────────────────

    @property
    def servers(self) -> dict[str, BaseMCPServer]:
        """Return a read-only view of registered servers.

        Used by Router._handle_tools_list() and _handle_health()
        to iterate all servers without accessing private state.
        """
        return dict(self._servers)

    def get_server(self, name: str) -> BaseMCPServer | None:
        """Resolve a server by name."""
        return self._servers.get(name)

    def list_servers(self) -> list[dict[str, Any]]:
        """Return metadata for all registered servers."""
        return [
            {
                "name": s.name,
                "version": s.version,
                "running": s.is_running,
                "failed": s.name in self._failed,
            }
            for s in self._servers.values()
        ]

    @property
    def count(self) -> int:
        """Total number of registered servers."""
        return len(self._servers)

    @property
    def running_count(self) -> int:
        """Number of servers currently running."""
        return sum(1 for s in self._servers.values() if s.is_running)

    @property
    def failed_count(self) -> int:
        """Number of servers that failed to start."""
        return len(self._failed)

    @property
    def failed_servers(self) -> list[str]:
        """Names of servers that failed to start."""
        return sorted(self._failed)
