"""Ombre MCP Server — Hub adapter for the external Ombre deployment.

Ombre is an independently deployed MCP-compatible long-term memory service.
This adapter bridges the Hub to Ombre via HTTP.

Delegates HTTP concerns to adapter.py. No Ombre business logic.
"""

from __future__ import annotations

import logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

from mcp_servers.ombre.adapter import OmbreAdapter

logger = logging.getLogger(__name__)


class OmbreServer(BaseMCPServer):
    """Adapter that connects MCP Hub to the external Ombre deployment."""

    def __init__(
        self,
        name: str = "ombre",
        version: str = "0.1.0",
        endpoint: str | None = None,
    ) -> None:
        super().__init__(name=name, version=version)
        self._adapter = OmbreAdapter(endpoint=endpoint)

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        logger.info("Ombre adapter initializing — endpoint: %s", self._adapter.endpoint)
        status = await self._adapter.connect()
        if status == "CONNECTED":
            logger.info("✓ Ombre (CONNECTED) — %s", self._adapter.endpoint)
        else:
            logger.warning("Ombre health check: %s", status)

    async def start(self) -> None:
        if self._adapter.connected:
            logger.info("Ombre adapter started — endpoint: %s", self._adapter.endpoint)
        else:
            logger.warning("Ombre adapter started but not connected")

    async def stop(self) -> None:
        await self._adapter.disconnect()
        logger.info("Ombre adapter stopped")

    # ── Health ───────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        return {
            "name": self.name,
            **await self._adapter.health(),
        }

    # ── Tools ────────────────────────────────────────────────────

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "ombre_health",
                "description": "Check connectivity to the external Ombre deployment",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "ombre_status",
                "description": "Get Ombre service status and endpoint info",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        if tool_name == "ombre_health":
            return await self.health()
        if tool_name == "ombre_status":
            return {
                "name": self.name,
                "version": self.version,
                **self._adapter.info(),
            }
        raise ToolNotFoundError(self.name, tool_name)
