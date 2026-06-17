"""MCP Registry — service registration, routing, lifecycle management, and configuration."""

from __future__ import annotations

from typing import Any

from app.mcp.server import MCPServer


class MCPRegistry:
    """Central registry that manages the lifecycle of all MCP services.

    Responsibilities (per ARCHITECTURE.md):
      - Service registration — register MCP servers by name.
      - Routing — resolve a service name to its server instance.
      - Lifecycle management — start / stop registered services.
      - Configuration — store and retrieve per-service configuration.
    """

    def __init__(self) -> None:
        self._services: dict[str, MCPServer] = {}
        self._configs: dict[str, dict[str, Any]] = {}

    # ── Registration ────────────────────────────────────────────

    def register(self, name: str, server: MCPServer, config: dict[str, Any] | None = None) -> None:
        """Register an MCP server under a unique name.

        Args:
            name: Unique service name (e.g. 'github', 'filesystem').
            server: An MCPServer instance.
            config: Optional service-level configuration dictionary.
        """
        self._services[name] = server
        if config:
            self._configs[name] = config

    def unregister(self, name: str) -> bool:
        """Unregister an MCP server by name.

        Returns:
            True if the service was removed, False if it was not found.
        """
        if name in self._services:
            del self._services[name]
            self._configs.pop(name, None)
            return True
        return False

    # ── Routing ─────────────────────────────────────────────────

    def get_service(self, name: str) -> MCPServer | None:
        """Resolve a service name to its MCPServer instance.

        Returns:
            The MCPServer if registered, otherwise None.
        """
        return self._services.get(name)

    def list_services(self) -> list[str]:
        """Return the names of all currently registered services."""
        return list(self._services.keys())

    # ── Lifecycle ───────────────────────────────────────────────

    async def start_all(self) -> None:
        """Start every registered MCP server."""
        for server in self._services.values():
            await server.start()

    async def stop_all(self) -> None:
        """Stop every registered MCP server."""
        for server in self._services.values():
            await server.stop()

    # ── Configuration ───────────────────────────────────────────

    def get_config(self, name: str) -> dict[str, Any]:
        """Return the configuration dictionary for a registered service."""
        return self._configs.get(name, {})

    def set_config(self, name: str, config: dict[str, Any]) -> None:
        """Set or update the configuration for a registered service."""
        self._configs[name] = config
