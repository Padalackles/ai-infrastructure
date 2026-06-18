"""Remote MCP Client — reusable infrastructure for connecting to remote MCP servers.

Provides a generic MCP Streamable HTTP client that:
- Establishes MCP sessions (initialize)
- Auto-discovers tools (tools/list)
- Forwards tool calls (tools/call)
- Manages connection lifecycle (connect, disconnect, state tracking)
- Emits structured logs for all protocol operations

Subclass or compose this for any remote MCP server (Ombre, GitHub, Filesystem,
Browser, etc.).  Only a URL and optional timeout are required — the rest is
handled automatically.

Usage:
    client = RemoteMCPClient("Ombre", url="http://host:8000/mcp")
    await client.connect()           # → CONNECTED, tools cached
    client.tools                     # → [{"name": "...", ...}]
    await client.call_tool("hold", {"content": "..."})
    await client.disconnect()
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

CONNECTING = "CONNECTING"
CONNECTED = "CONNECTED"
DISCONNECTED = "DISCONNECTED"

DEFAULT_MCP_TIMEOUT = 10.0


class RemoteMCPClient:
    """Generic MCP client for any remote Streamable HTTP MCP server.

    All protocol logic (initialize, tools/list, tools/call) lives here.
    Server-specific configuration (URL, timeout) is passed at init.
    """

    def __init__(
        self,
        label: str,
        *,
        url: str,
        timeout: float = DEFAULT_MCP_TIMEOUT,
    ) -> None:
        self._label = label          # e.g. "Ombre", "GitHub" — for logs
        self._url = url
        self._timeout = timeout
        self._state = DISCONNECTED
        self._tools: list[dict[str, Any]] = []
        self._server_info: dict[str, Any] = {}

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

    @property
    def state(self) -> str:
        return self._state

    # ── Connection Lifecycle ────────────────────────────────────

    async def connect(self) -> str:
        """Establish MCP session and discover tools.

        Performs: streamable HTTP handshake → initialize → tools/list.
        Caches discovered tools in self.tools.
        """
        self._state = CONNECTING
        logger.info("%s MCP client connecting to %s", self._label, self._url)

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
                    logger.info("Connected to %s — %s v%s",
                                self._label,
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
                    logger.info("Discovered %d tools from %s: %s",
                                len(self._tools),
                                self._label,
                                [t["name"] for t in self._tools])

                    self._state = CONNECTED
        except Exception as exc:
            self._state = DISCONNECTED
            logger.warning("%s MCP connection failed: %s", self._label, exc)

        return self._state

    async def disconnect(self) -> None:
        """Release resources and clear cached state."""
        self._state = DISCONNECTED
        self._tools.clear()
        logger.info("%s MCP client disconnected", self._label)

    # ── Tool Forwarding ─────────────────────────────────────────

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Forward a tool call to the remote MCP server.

        Opens a fresh session per call (compatible with stateless servers).
        """
        if self._state != CONNECTED:
            return {
                "error": True,
                "message": f"{self._label} not connected (state={self._state})",
            }

        logger.info("Forward tools/call → %s: %s(%s)",
                     self._label, tool_name, arguments)

        try:
            async with streamablehttp_client(
                self._url,
                timeout=self._timeout,
                sse_read_timeout=self._timeout,
            ) as (read, write, _get_session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments or {})

                    texts = []
                    for c in result.content:
                        if hasattr(c, "text"):
                            texts.append(c.text)
                    logger.info("%s response: %s", self._label, texts)
                    return {"content": texts, "tool": tool_name}
        except Exception as exc:
            logger.exception("%s tool call failed: %s", self._label, tool_name)
            return {"error": True, "message": str(exc), "tool": tool_name}

    # ── Health ──────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        return {
            "label": self._label,
            "endpoint": self._url,
            "state": self._state,
            "server": self._server_info,
            "tools_count": len(self._tools),
        }
