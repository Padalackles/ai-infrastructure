"""Notification MCP Service — sends push notifications via ntfy.sh.

Uses curl on the VPS host to deliver notifications.  The Hub discovers
this service through manifest.yaml — no Core changes required.
"""

from __future__ import annotations

import logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

from mcp_servers.ntfy.adapter import health, info, send

logger = logging.getLogger(__name__)


class NtfyServer(BaseMCPServer):
    """Push notification MCP service — ntfy.sh via curl."""

    def __init__(
        self,
        name: str = "ntfy",
        version: str = "0.2.0",
    ) -> None:
        super().__init__(name=name, version=version)

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        h = await health()
        logger.info("ntfy initialized — %s/%s", h["server"], h["topic"])

    async def start(self) -> None:
        logger.info("ntfy started")

    async def stop(self) -> None:
        logger.info("ntfy stopped")

    # ── Health ───────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        return {
            "name": self.name,
            **(await health()),
        }

    # ── Tools ────────────────────────────────────────────────────

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "notify.send",
                "description": "Send a push notification via ntfy.sh",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Notification body text (required)",
                        },
                        "title": {
                            "type": "string",
                            "description": "Notification title (default: Claude)",
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority: default, min, low, high, urgent",
                        },
                        "tags": {
                            "type": "string",
                            "description": "Comma-separated tags",
                        },
                    },
                    "required": ["message"],
                },
            },
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
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        args = arguments or {}

        if tool_name == "notify.send":
            return await send(
                message=args.get("message", ""),
                title=args.get("title", "Claude"),
                priority=args.get("priority", "default"),
                tags=args.get("tags", ""),
            )

        if tool_name == "ntfy_health":
            return await self.health()

        if tool_name == "ntfy_info":
            return await info()

        raise ToolNotFoundError(self.name, tool_name)
