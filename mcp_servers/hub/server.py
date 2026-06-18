"""Hub Management MCP Service — inspect Hub state via MCP tools.

Exposes hub.status, hub.services, hub.health as MCP tools so Claude
can introspect the Hub without REST endpoints.
"""

from __future__ import annotations

import time
from typing import Any

from src.core.hub_state import get_registry, get_started_at
from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

logger = __import__("logging").getLogger(__name__)


class HubServer(BaseMCPServer):
    """MCP service that exposes Hub runtime inspection tools."""

    def __init__(
        self,
        name: str = "hub",
        version: str = "0.1.0",
    ) -> None:
        super().__init__(name=name, version=version)

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        logger.info("Hub management service initialized")

    async def start(self) -> None:
        logger.info("Hub management service started")

    async def stop(self) -> None:
        logger.info("Hub management service stopped")

    # ── Health ───────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "status": "ok"}

    # ── Tools ────────────────────────────────────────────────────

    async def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "hub.status",
                "description": "Get MCP Hub runtime status: version, uptime, server count",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "hub.services",
                "description": "List all registered MCP services with metadata",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "hub.health",
                "description": "Health-check every registered MCP service",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        registry = get_registry()

        if tool_name == "hub.status":
            uptime = time.time() - (get_started_at() or time.time())
            return {
                "version": "0.3.0",
                "uptime_seconds": round(uptime, 0),
                "total_services": registry.count,
                "running_services": registry.running_count,
                "failed_services": registry.failed_count,
                "hub_status": "healthy" if registry.failed_count == 0 else "degraded",
            }

        if tool_name == "hub.services":
            servers = registry.list_servers()
            return {
                "services": [
                    {
                        "name": s["name"],
                        "version": s["version"],
                        "running": s["running"],
                        "failed": s.get("failed", False),
                    }
                    for s in servers
                ]
            }

        if tool_name == "hub.health":
            health_report = registry.aggregate_health()
            return {
                "aggregate": health_report["status"],
                "servers": health_report["servers"],
            }

        raise ToolNotFoundError(self.name, tool_name)
