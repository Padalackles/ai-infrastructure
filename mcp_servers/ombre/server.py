"""Ombre MCP Server plugin — remote MCP client bridge.

Connects to the deployed Ombre Brain MCP server (45.76.169.98:8000/mcp)
via the MCP Streamable HTTP protocol.  All tools are auto-discovered from
the remote server — no hardcoded tool definitions.

Implements the BaseMCPServer contract so the Hub's Discovery / Registry /
Lifecycle can manage it like any other plugin.
"""

from __future__ import annotations

import logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

from mcp_servers.ombre.adapter import (
    CONNECTED,
    DISCONNECTED,
    OmbreMCPClient,
)

logger = logging.getLogger(__name__)


class OmbreServer(BaseMCPServer):
    """MCP Hub plugin that bridges to the remote Ombre Brain MCP server."""

    def __init__(
        self,
        name: str = "ombre",
        version: str = "0.1.0",
        endpoint: str | None = None,
    ) -> None:
        super().__init__(name=name, version=version)
        self._client = OmbreMCPClient(url=endpoint)

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        logger.info("Ombre plugin initializing — endpoint: %s", self._client.url)
        state = await self._client.connect()
        if state == CONNECTED:
            logger.info("Ombre — %s v%s (%d tools)",
                        self._client.server_info.get("name", "?"),
                        self._client.server_info.get("version", "?"),
                        len(self._client.tools))
        else:
            logger.warning("Ombre unavailable — state=%s", state)

    async def start(self) -> None:
        if self._client.connected:
            logger.info("Ombre plugin started (%d tools)", len(self._client.tools))
        else:
            logger.warning("Ombre plugin started but not connected")

    async def stop(self) -> None:
        await self._client.disconnect()
        logger.info("Ombre plugin stopped")

    # ── Health ───────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        return {
            "name": self.name,
            **(await self._client.health()),
        }

    # ── Tools (auto-discovered) ──────────────────────────────────

    async def get_tools(self) -> list[dict[str, Any]]:
        """Return tools discovered from the remote Ombre server."""
        tools = self._client.tools
        # ── TEMPORARY DIAGNOSTIC ──────────────────────────────────
        logger.info("=" * 60)
        logger.info("DIAGNOSTIC: OmbreServer.get_tools() — remote returned %d tools",
                     len(tools))
        for t in tools:
            logger.info("  - %s", t.get("name", "?"))
        if not tools:
            logger.warning("  (Ombre client state=%s, connected=%s)",
                           self._client.state, self._client.connected)
        logger.info("=" * 60)
        return tools

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Forward tool call to the remote Ombre server."""
        args = arguments or {}
        result = await self._client.call_tool(tool_name, args)

        if result.get("error"):
            raise ToolNotFoundError(self.name, tool_name)

        return result
