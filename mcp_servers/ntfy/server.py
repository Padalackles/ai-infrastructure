"""Ntfy MCP — External Service Adapter.

ntfy is an EXTERNAL service (https://ntfy.sh). The Hub connects via HTTP adapter.

This server.py is the Hub-facing interface (BaseMCPServer subclass) required by
Discovery, Registry, Lifecycle, and Router. All actual communication with the
ntfy API happens in adapter.py.

Pattern: Hub → NtfyServer(BaseMCPServer) → NtfyAdapter → ntfy.sh API
"""

from __future__ import annotations

import logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

from mcp_servers.ntfy.adapter import NtfyAdapter

logger = logging.getLogger(__name__)


class NtfyServer(BaseMCPServer):
    """Push notification MCP service."""

    def __init__(
        self,
        name: str = "ntfy",
        version: str = "0.1.0",
    ) -> None:
        super().__init__(name=name, version=version)
        self._adapter = NtfyAdapter()

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        logger.info("ntfy adapter initializing — endpoint: %s", self._adapter.endpoint)
        health = await self._adapter.health()
        logger.info("✓ ntfy (%s)", "CONNECTED" if health["status"] == "ok" else health["status"])

    async def start(self) -> None:
        logger.info("ntfy adapter started")

    async def stop(self) -> None:
        logger.info("ntfy adapter stopped")

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
                "name": "ntfy_health",
                "description": "Check ntfy service health",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "ntfy_info",
                "description": "Get ntfy service metadata",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "ntfy_send",
                "description": "Send a push notification",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Notification title"},
                        "message": {"type": "string", "description": "Notification message"},
                    },
                    "required": ["title", "message"],
                },
            },
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        args = arguments or {}
        if tool_name == "ntfy_health":
            return await self.health()
        if tool_name == "ntfy_info":
            return await self._adapter.info()
        if tool_name == "ntfy_send":
            title = args.get("title", "")
            message = args.get("message", "")
            return await self._adapter.send(title, message)
        raise ToolNotFoundError(self.name, tool_name)
