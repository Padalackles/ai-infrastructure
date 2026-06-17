"""Server Manager — lifecycle management for registered MCP servers.

Public API:
  - register / unregister
  - start_all / stop_all
  - get_server / servers
  - list_tools / call_tool / aggregate_health
  - count / running_count / failed_count / failed_servers

No business logic. Server running state lives ONLY in BaseMCPServer._running.
"""

from __future__ import annotations

import logging
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

logger = logging.getLogger(__name__)


class ServerManager:
    """Manages the full lifecycle of registered MCP servers."""

    def __init__(self) -> None:
        self._servers: dict[str, BaseMCPServer] = {}
        self._failed: set[str] = set()

    # ── Registration ────────────────────────────────────────────

    def register(self, server: BaseMCPServer) -> None:
        self._servers[server.name] = server
        logger.info("Registered server: %s (v%s)", server.name, server.version)

    def unregister(self, name: str) -> bool:
        if name in self._servers:
            del self._servers[name]
            self._failed.discard(name)
            logger.info("Unregistered server: %s", name)
            return True
        return False

    # ── Lifecycle ───────────────────────────────────────────────

    async def start_all(self) -> None:
        self._failed.clear()
        for name, server in self._servers.items():
            try:
                logger.info("Initializing server: %s", name)
                await server.initialize()
                try:
                    await server.lifecycle_start()
                except Exception:
                    logger.exception("Server start failed for %s — rolling back", name)
                    try:
                        await server.lifecycle_stop()
                    except Exception:
                        logger.exception("Rollback stop also failed for %s", name)
                    self._failed.add(name)
            except Exception:
                logger.exception("Failed to start server: %s", name)
                self._failed.add(name)

    async def stop_all(self) -> None:
        for name, server in self._servers.items():
            try:
                if server.is_running:
                    await server.lifecycle_stop()
            except Exception:
                logger.exception("Failed to stop server: %s", name)

    # ── Query ───────────────────────────────────────────────────

    @property
    def servers(self) -> dict[str, BaseMCPServer]:
        return dict(self._servers)

    def get_server(self, name: str) -> BaseMCPServer | None:
        return self._servers.get(name)

    def list_servers(self) -> list[dict[str, Any]]:
        return [
            {"name": s.name, "version": s.version,
             "running": s.is_running, "failed": s.name in self._failed}
            for s in self._servers.values()
        ]

    # ── Public tool aggregation ─────────────────────────────────

    async def find_tool_server(self, tool_name: str) -> str | None:
        """Find which registered server owns a tool by name.

        Used for standard MCP tools/call where the client doesn't
        specify a server — the Hub resolves globally.

        Returns:
            Server name, or None if no server owns the tool.
        """
        for name, server in self._servers.items():
            try:
                tools = await server.get_tools()
                if any(t.get("name") == tool_name for t in tools):
                    return name
            except Exception:
                continue
        return None

    async def list_tools(self) -> dict[str, Any]:
        """Aggregate tools from all registered servers."""
        tools: list[dict[str, Any]] = []
        for name, server in self._servers.items():
            try:
                server_tools = await server.get_tools()
                tools.append({"server": name, "tools": server_tools})
            except Exception:
                logger.exception("Failed to get tools from server: %s", name)
                tools.append({"server": name, "tools": [], "error": "Failed to retrieve tools"})
        return {"tools": tools}

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve a server and call its tool. Raises JSONRPCError-compatible exceptions."""
        from src.transport.response import ErrorCode, JSONRPCError

        server = self.get_server(server_name)
        if server is None:
            raise JSONRPCError(ErrorCode.SERVER_NOT_FOUND, f"Server not found: {server_name}",
                               {"server": server_name})
        try:
            result = await server.call_tool(tool_name, arguments)
            return {"server": server_name, "tool": tool_name, "result": result}
        except ToolNotFoundError as exc:
            raise JSONRPCError(ErrorCode.TOOL_NOT_FOUND, str(exc),
                               {"server": server_name, "tool": tool_name})
        except JSONRPCError:
            raise
        except Exception as exc:
            logger.exception("Tool call failed: %s/%s", server_name, tool_name)
            raise JSONRPCError(ErrorCode.INTERNAL_ERROR, f"Tool execution failed: {exc}",
                               {"server": server_name, "tool": tool_name})

    # ── Public health aggregation ───────────────────────────────

    def aggregate_health(self) -> dict[str, Any]:
        """Aggregate health from all servers."""
        servers_health = []
        for name, server in self._servers.items():
            try:
                h = {"name": name, "status": "ok" if server.is_running else "stopped"}
                servers_health.append(h)
            except Exception as exc:
                servers_health.append({"name": name, "status": "error", "error": str(exc)})

        if not servers_health:
            aggregate = "healthy"
        elif all(s.get("status") != "ok" for s in servers_health):
            aggregate = "failed"
        elif any(s.get("status") != "ok" for s in servers_health):
            aggregate = "degraded"
        else:
            aggregate = "healthy"
        return {"status": aggregate, "servers": servers_health}

    # ── Counts ──────────────────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._servers)

    @property
    def running_count(self) -> int:
        return sum(1 for s in self._servers.values() if s.is_running)

    @property
    def failed_count(self) -> int:
        return len(self._failed)

    @property
    def failed_servers(self) -> list[str]:
        return sorted(self._failed)
