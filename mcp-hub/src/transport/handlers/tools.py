"""Handlers for MCP 'tools/list' and 'tools/call' methods."""

from __future__ import annotations

from typing import Any

from src.runtime.runtime import Runtime
from src.transport.response import ErrorCode, JSONRPCError


async def handle_tools_list(runtime: Runtime, params: dict[str, Any]) -> dict[str, Any]:
    """Aggregate tools from all registered servers via Runtime."""
    return await runtime.list_tools()


async def handle_tools_call(runtime: Runtime, params: dict[str, Any]) -> dict[str, Any]:
    """Forward a tool call through Runtime.

    Accepts two formats:
      1. Hub namespaced:
         {"server": "ntfy", "tool": "ntfy_send", "arguments": {...}}

      2. Standard MCP (Claude Desktop):
         {"name": "ntfy_send", "arguments": {...}}
         Tool name is resolved globally across all registered servers.
    """
    server_name = params.get("server")
    tool_name = params.get("tool")

    # Standard MCP format: use params.name directly
    if not tool_name:
        tool_name = params.get("name")

    if not tool_name or not isinstance(tool_name, str):
        raise JSONRPCError(ErrorCode.INVALID_PARAMS,
                           "params.tool or params.name is required")

    arguments = params.get("arguments", {})

    # If no server specified (standard MCP), resolve globally
    if not server_name:
        server_name = await runtime.find_tool_server(tool_name)
        if not server_name:
            raise JSONRPCError(ErrorCode.TOOL_NOT_FOUND,
                               f"Tool not found on any server: {tool_name}",
                               {"tool": tool_name})

    return await runtime.call_tool(server_name, tool_name, arguments)
