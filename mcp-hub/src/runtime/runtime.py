"""Runtime — thin pass-through between Router and ServerManager.

Pluggable middleware for future: auth, rate-limiting, retries, metrics, caching.
"""

from __future__ import annotations

import logging
from typing import Any

from src.core.events import EventBus
from src.registry.server_manager import ServerManager

logger = logging.getLogger(__name__)


class Runtime:
    """Middleware layer. Forwards all calls to ServerManager for now."""

    def __init__(
        self,
        server_manager: ServerManager,
        event_bus: EventBus,
        config: dict[str, Any],
    ) -> None:
        self._server_manager = server_manager
        self._event_bus = event_bus
        self._config = config

    # ── Config helpers ──────────────────────────────────────────

    @property
    def hub_config(self) -> dict[str, Any]:
        return self._config.get("hub", {})

    @property
    def server_config(self) -> dict[str, Any]:
        return self._config.get("server", {})

    # ── Server lifecycle ────────────────────────────────────────

    async def start_all(self) -> None:
        await self._server_manager.start_all()

    async def stop_all(self) -> None:
        await self._server_manager.stop_all()

    # ── Health & status ─────────────────────────────────────────

    def aggregate_health(self) -> dict[str, Any]:
        return self._server_manager.aggregate_health()

    def server_stats(self) -> dict[str, Any]:
        return {
            "total_servers": self._server_manager.count,
            "running_servers": self._server_manager.running_count,
            "failed_servers": self._server_manager.failed_count,
            "failed_names": self._server_manager.failed_servers,
            "servers": self._server_manager.list_servers(),
        }

    # ── Tools ───────────────────────────────────────────────────

    async def list_tools(self) -> dict[str, Any]:
        return await self._server_manager.list_tools()

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self._server_manager.call_tool(server_name, tool_name, arguments or {})

    # ── Initialize (MCP handshake) ──────────────────────────────

    def initialize_info(self) -> dict[str, Any]:
        hub = self.hub_config
        return {
            "protocolVersion": hub.get("protocol_version", "2024-11-05"),
            "serverInfo": {
                "name": hub.get("name", "mcp-hub"),
                "version": hub.get("version", "0.1.0"),
            },
            "capabilities": hub.get("capabilities", {"tools": {}}),
            "servers": self._server_manager.list_servers(),
        }
