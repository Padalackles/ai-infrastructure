"""Ombre MCP Client — connects to the remote Ombre Brain server via MCP protocol.

Uses the official MCP SDK client to:
- Establish a Streamable HTTP session
- Discover tools automatically (tools/list)
- Forward tool calls (tools/call)
- Manage connection lifecycle (connect, reconnect, disconnect)

No hardcoded tool definitions.  All tools are discovered from the remote server.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

DEFAULT_OMBRE_URL = os.getenv("OMBRE_URL", "http://45.76.169.98:8000/mcp")
DEFAULT_TIMEOUT = float(os.getenv("OMBRE_TIMEOUT", "10"))
DEFAULT_RECONNECT_DELAY = 3.0

CONNECTING = "CONNECTING"
CONNECTED = "CONNECTED"
DISCONNECTED = "DISCONNECTED"


class OmbreMCPClient:
    """MCP client adapter for the remote Ombre Brain server.

    Responsibilities:
      - MCP session management (initialize, session lifecycle)
      - Tool discovery (tools/list → cached tool registry)
      - Tool forwarding (tools/call → remote server → response)
      - Connection health tracking
    """

    def __init__(
        self,
        url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._url = url or DEFAULT_OMBRE_URL
        self._timeout = timeout
        self._state = DISCONNECTED
        self._tools: list[dict[str, Any]] = []
        self._server_info: dict[str, Any] = {}
        self._session: ClientSession | None = None

    # ── Properties ──────────────────────────────────────────────

    @property
    def url(self) -> str:
        return self._url

    @property
    def connected(self) -> bool:
        return self._state == CONNECTED

    @property
    def tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    @property
    def server_info(self) -> dict[str, Any]:
        return dict(self._server_info)

    # ── Connection Lifecycle ────────────────────────────────────

    async def connect(self) -> str:
        """Establish MCP session and discover tools.

        Returns:
            CONNECTED  — session established, tools discovered
            CONNECTING — in progress
            DISCONNECTED — failed
        """
        self._state = CONNECTING
        logger.info("Ombre MCP client connecting to %s", self._url)

        try:
            async with streamablehttp_client(
                self._url,
                timeout=self._timeout,
                sse_read_timeout=self._timeout,
            ) as (read, write, _get_session_id):
                async with ClientSession(read, write) as session:
                    # MCP handshake
                    init_result = await session.initialize()
                    self._server_info = {
                        "name": init_result.serverInfo.name,
                        "version": init_result.serverInfo.version,
                    }
                    logger.info("Connected to Ombre — %s v%s",
                                self._server_info["name"],
                                self._server_info["version"])

                    # Discover tools
                    tools_result = await session.list_tools()
                    self._tools = [
                        {
                            "name": t.name,
                            "description": t.description or "",
                            "inputSchema": t.inputSchema,
                        }
                        for t in tools_result.tools
                    ]
                    logger.info("Discovered %d tools from Ombre: %s",
                                 len(self._tools),
                                 [t["name"] for t in self._tools])

                    self._state = CONNECTED
        except Exception as exc:
            self._state = DISCONNECTED
            logger.warning("Ombre MCP connection failed: %s", exc)

        return self._state

    async def disconnect(self) -> None:
        """Mark as disconnected (session auto-closes via context manager)."""
        self._state = DISCONNECTED
        self._tools.clear()
        logger.info("Ombre MCP client disconnected")

    # ── Tool Forwarding ─────────────────────────────────────────

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Forward a tool call to the remote Ombre server.

        Opens a fresh session for each call (stateless mode compatible).
        """
        if self._state != CONNECTED:
            return {
                "error": True,
                "message": f"Ombre not connected (state={self._state})",
            }

        logger.info("Forward tools/call → Ombre: %s(%s)", tool_name, arguments)

        try:
            async with streamablehttp_client(
                self._url,
                timeout=self._timeout,
                sse_read_timeout=self._timeout,
            ) as (read, write, _get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments or {})

                    # Extract text content
                    texts = []
                    for c in result.content:
                        if hasattr(c, "text"):
                            texts.append(c.text)
                    logger.info("Ombre response: %s", texts)
                    return {"content": texts, "tool": tool_name}
        except Exception as exc:
            logger.exception("Ombre tool call failed: %s", tool_name)
            return {"error": True, "message": str(exc), "tool": tool_name}

    # ── Health ──────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        return {
            "endpoint": self._url,
            "state": self._state,
            "server": self._server_info,
            "tools_count": len(self._tools),
        }
