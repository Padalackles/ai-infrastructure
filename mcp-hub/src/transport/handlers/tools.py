"""Handlers for MCP 'tools/list' and 'tools/call' methods."""

from __future__ import annotations

from typing import Any

from src.runtime.runtime import Runtime
from src.transport.response import ErrorCode, JSONRPCError


async def handle_tools_list(runtime: Runtime, params: dict[str, Any]) -> dict[str, Any]:
    """Aggregate tools from all registered servers via Runtime."""
    return await runtime.list_tools()


async def handle_tools_call(runtime: Runtime, params: dict[str, Any]) -> dict[str, Any]:
    """Forward a tool call through Runtime."""
    server_name = params.get("server")
    tool_name = params.get("tool")
    arguments = params.get("arguments", {})

    if not server_name or not isinstance(server_name, str):
        raise JSONRPCError(ErrorCode.INVALID_PARAMS, "params.server is required")
    if not tool_name or not isinstance(tool_name, str):
        raise JSONRPCError(ErrorCode.INVALID_PARAMS, "params.tool is required")

    return await runtime.call_tool(server_name, tool_name, arguments)
