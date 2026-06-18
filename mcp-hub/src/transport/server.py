"""Transport layer — FastMCP Streamable HTTP bridge.

Replaces the hand-written JSON-RPC transport with the official MCP Python SDK.
The FastMCP instance is embedded into FastAPI via a thin ASGI wrapper that
proxies /mcp requests directly to FastMCP's Starlette app.

Lifespan management: FastMCP's Starlette app has its own lifespan that
initializes the session manager's anyio task group.  We merge these
lifespans so both FastAPI (for Hub services) and FastMCP (for MCP sessions)
start and stop together.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.streamable_http import TransportSecuritySettings
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

logger = logging.getLogger("transport")

# Lazy reference — set by main.py lifespan before any MCP request arrives
_runtime_ref: Any = None


def set_runtime(runtime) -> None:
    global _runtime_ref
    _runtime_ref = runtime


def _get_runtime() -> Any:
    if _runtime_ref is None:
        raise RuntimeError("Runtime not yet initialized")
    return _runtime_ref


# ── FastMCP Instance ─────────────────────────────────────────────

mcp = FastMCP(
    name="mcp-hub",
    instructions="MCP Hub — central orchestration gateway. "
                 "Routes tool calls to registered MCP service plugins.",
    stateless_http=True,
    json_response=True,
    debug=True,
    log_level="DEBUG",
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,  # behind Caddy/Cloudflare
    ),
)

_srv = mcp._mcp_server


# ── tools/list ───────────────────────────────────────────────────


@_srv.list_tools()
async def _list_tools(req: ListToolsRequest) -> ListToolsResult:
    runtime = _get_runtime()
    aggregated = await runtime.list_tools()
    tools: list[Tool] = []

    for entry in aggregated.get("tools", []):
        for tool_def in entry.get("tools", []):
            tools.append(Tool(
                name=tool_def["name"],
                description=tool_def.get("description", ""),
                inputSchema=tool_def.get(
                    "inputSchema", {"type": "object", "properties": {}}),
            ))

    logger.info("tools/list — %d tools", len(tools))
    return ListToolsResult(tools=tools)


# ── tools/call ───────────────────────────────────────────────────


@_srv.call_tool()
async def _call_tool(name: str, arguments: dict) -> list[TextContent]:
    import time as _time
    from src.core.request_context import RequestContext
    from src.core.observability.audit import record as audit_record

    runtime = _get_runtime()
    req_ctx = RequestContext.current()
    req_ctx.set("tool", name)

    logger.info("tools/call — %s(%s)", name, arguments)
    t0 = _time.perf_counter()

    try:
        server_name = await runtime.find_tool_server(name)
        if server_name:
            req_ctx.set("plugin", server_name)
            plugin = server_name
        else:
            plugin = "unknown"

        if not server_name:
            duration_ms = (_time.perf_counter() - t0) * 1000
            audit_record(plugin=plugin, tool=name, status="failure",
                         duration_ms=duration_ms, error_type="ToolNotFound")
            return [TextContent(
                type="text",
                text=f"Tool not found on any server: {name}",
            )]

        result = await runtime.call_tool(server_name, name, arguments or {})
        inner = result.get("result", result)

        duration_ms = (_time.perf_counter() - t0) * 1000
        is_error = isinstance(inner, dict) and inner.get("error")
        audit_record(
            plugin=plugin, tool=name,
            status="failure" if is_error else "success",
            duration_ms=duration_ms,
            error_type="ToolError" if is_error else "",
        )
        return [TextContent(type="text", text=str(inner))]
    except Exception as exc:
        duration_ms = (_time.perf_counter() - t0) * 1000
        plugin = req_ctx.plugin or "unknown"
        audit_record(plugin=plugin, tool=name, status="failure",
                     duration_ms=duration_ms,
                     error_type=type(exc).__name__)
        logger.exception("tools/call failed — %s", name)
        return [TextContent(type="text", text=str(exc))]


# ── ASGI wrapper — merges FastMCP Starlette app lifespan ─────────

#
# FastMCP.streamable_http_app() returns a Starlette app whose lifespan
# calls session_manager.run() (the anyio task group).  FastAPI does NOT
# invoke sub-app lifespans.  This wrapper merges the two lifespans so
# the session manager starts when FastAPI starts and stops when FastAPI
# stops — without manually entering fragile context managers.
#

_fastmcp_starlette = mcp.streamable_http_app()

# Snapshot the original lifespan so we can invoke it from FastAPI's lifespan.
_fastmcp_lifespan = _fastmcp_starlette.router.lifespan_context


async def start_mcp(app_state) -> None:
    """Enter the FastMCP Starlette lifespan from FastAPI's lifespan.

    This is the clean integration point — we call the Starlette app's
    lifespan, which internally calls session_manager.run(), creating
    the task group.  The anyio task group stays alive as long as the
    context manager is active.
    """
    # Starlette lifespan expects (app) → async context manager
    ctx = _fastmcp_lifespan(_fastmcp_starlette)
    await ctx.__aenter__()
    # Store on app.state so stop_mcp can access it
    app_state._fastmcp_lifespan_ctx = ctx
    logger.info("FastMCP session manager started")


async def stop_mcp(app_state) -> None:
    """Exit the FastMCP Starlette lifespan."""
    ctx = getattr(app_state, "_fastmcp_lifespan_ctx", None)
    if ctx is not None:
        await ctx.__aexit__(None, None, None)
        logger.info("FastMCP session manager stopped")


# ── Public ASGI app for mount / route passthrough ────────────────

_mcp_asgi = _fastmcp_starlette
