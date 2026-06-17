"""Example MCP Server — minimal implementation to verify the Hub pipeline.

This server exists solely to validate the transport layer:
  - Discovery finds it via manifest.yaml
  - tools/list aggregates its tools
  - tools/call dispatches to its call_tool()
  - Errors propagate as JSON-RPC errors

No business logic. No Ombre/Memory/Agent concepts.
"""

from __future__ import annotations

import logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

logger = logging.getLogger(__name__)


class ExampleServer(BaseMCPServer):
    """A do-nothing MCP server used to validate the Hub runtime + transport."""

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        logger.info("ExampleServer: initialize() called")

    async def start(self) -> None:
        logger.info("ExampleServer: start() called")

    async def stop(self) -> None:
        logger.info("ExampleServer: stop() called")

    # ── Tools ────────────────────────────────────────────────────

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "echo",
                "description": "Echo back the input arguments. Used to verify the tools/call pipeline.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "A message to echo back",
                        }
                    },
                },
            },
            {
                "name": "ping",
                "description": "Always returns pong. No arguments.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        if tool_name == "echo":
            return arguments or {}
        if tool_name == "ping":
            return {"response": "pong"}
        raise ToolNotFoundError(self.name, tool_name)
