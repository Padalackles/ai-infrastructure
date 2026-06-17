"""Router — method-based dispatch for JSON-RPC requests.

Completely generic. Routes through ServerManager registry only.
Never imports, instantiates, or references any concrete server class.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.core.base_server import ToolNotFoundError
from src.core.server_manager import ServerManager
from src.transport.request import JSONRPCRequest
from src.transport.response import (
    ErrorCode,
    JSONRPCError,
    JSONRPCErrorResponse,
    JSONRPCResponse,
    build_error,
    build_result,
)

logger = logging.getLogger("transport")


class Router:
    """Dispatches JSON-RPC requests to registered MCP servers via ServerManager."""

    def __init__(self, server_manager: ServerManager) -> None:
        self._server_manager: ServerManager = server_manager

    async def route(self, request: JSONRPCRequest) -> JSONRPCResponse | JSONRPCErrorResponse:
        """Route a JSON-RPC request and return a response.

        Supported methods:
          - initialize   → Hub capabilities + server info
          - tools/list   → aggregate tools from all registered servers
          - tools/call   → forward a tool call to the specified server
          - health       → aggregate health from all servers
        """
        t0 = time.perf_counter()
        req_id = request.id
        method = request.method
        params = request.params

        logger.info("REQUEST  id=%s method=%s", req_id, method)

        # Notifications — no response
        if request.is_notification:
            logger.debug("NOTIFICATION method=%s — no response", method)
            return JSONRPCResponse(id=None, result=None)

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "health":
                result = await self._handle_health()
            else:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                logger.info("RESPONSE id=%s status=error code=%d method=%s elapsed=%.1fms",
                            req_id, ErrorCode.METHOD_NOT_FOUND, method, elapsed_ms)
                return build_error(req_id, ErrorCode.METHOD_NOT_FOUND,
                                   f"Method not found: {method}")

            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("RESPONSE id=%s status=success method=%s elapsed=%.1fms",
                        req_id, method, elapsed_ms)
            return build_result(req_id, result)

        except JSONRPCError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("RESPONSE id=%s status=error code=%d method=%s elapsed=%.1fms",
                        req_id, exc.code, method, elapsed_ms)
            return exc.to_response(req_id)
        except Exception:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.exception("RESPONSE id=%s status=error method=%s elapsed=%.1fms",
                             req_id, method, elapsed_ms)
            return build_error(req_id, ErrorCode.INTERNAL_ERROR, "Internal error")

    # ── Method handlers ──────────────────────────────────────────

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Return Hub capabilities in MCP initialize format."""
        servers = self._server_manager.list_servers()
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "mcp-hub",
                "version": "0.1.0",
            },
            "capabilities": {
                "tools": {},
            },
            "servers": [
                {"name": s["name"], "version": s["version"], "running": s["running"]}
                for s in servers
            ],
        }

    async def _handle_tools_list(self) -> dict[str, Any]:
        """Aggregate tools from every registered server."""
        tools: list[dict[str, Any]] = []
        for name, server in self._server_manager.servers.items():
            try:
                server_tools = await server.get_tools()
                tools.append({
                    "server": name,
                    "tools": server_tools,
                })
            except Exception:
                logger.exception("Failed to get tools from server: %s", name)
                tools.append({
                    "server": name,
                    "tools": [],
                    "error": "Failed to retrieve tools",
                })
        return {"tools": tools}

    async def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Forward a tool call to the specified server."""
        server_name = params.get("server")
        tool_name = params.get("tool")
        arguments = params.get("arguments", {})

        if not server_name or not isinstance(server_name, str):
            raise JSONRPCError(ErrorCode.INVALID_PARAMS, "params.server is required")
        if not tool_name or not isinstance(tool_name, str):
            raise JSONRPCError(ErrorCode.INVALID_PARAMS, "params.tool is required")

        server = self._server_manager.get_server(server_name)
        if server is None:
            raise JSONRPCError(
                ErrorCode.SERVER_NOT_FOUND,
                f"Server not found: {server_name}",
                {"server": server_name},
            )

        try:
            result = await server.call_tool(tool_name, arguments)
            return {
                "server": server_name,
                "tool": tool_name,
                "result": result,
            }
        except ToolNotFoundError as exc:
            raise JSONRPCError(
                ErrorCode.TOOL_NOT_FOUND,
                str(exc),
                {"server": server_name, "tool": tool_name},
            )
        except JSONRPCError:
            raise
        except Exception as exc:
            logger.exception("Tool call failed: %s/%s", server_name, tool_name)
            raise JSONRPCError(
                ErrorCode.INTERNAL_ERROR,
                f"Tool execution failed: {exc}",
                {"server": server_name, "tool": tool_name},
            )

    async def _handle_health(self) -> dict[str, Any]:
        """Aggregate health checks from all servers."""
        servers_health = []
        all_ok = True
        for name, server in self._server_manager.servers.items():
            try:
                h = await server.health()
                servers_health.append(h)
                if h.get("status") != "ok":
                    all_ok = False
            except Exception as exc:
                servers_health.append({"name": name, "status": "error", "error": str(exc)})
                all_ok = False
        if all_ok and servers_health:
            aggregate = "healthy"
        elif not servers_health:
            aggregate = "healthy"  # no servers = healthy
        elif all(s["status"] != "ok" for s in servers_health if "status" in s):
            aggregate = "failed"
        else:
            aggregate = "degraded"
        return {"status": aggregate, "servers": servers_health}
