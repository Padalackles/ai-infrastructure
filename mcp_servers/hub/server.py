"""Hub Diagnostics — hidden MCP tools for developers only.

Tools are exposed ONLY when HUB_EXPOSE_INTERNAL_TOOLS=true.
In production, get_tools() returns [] so Claude never sees them.

When enabled, tools appear under hub.debug.* namespace.
"""

from __future__ import annotations

import os
import time
from typing import Any

from src.core.hub_state import get_registry, get_started_at
from src.core.metrics import snapshot as metrics_snapshot
from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

logger = __import__("logging").getLogger(__name__)

_EXPOSE = os.getenv("HUB_EXPOSE_INTERNAL_TOOLS", "").lower() in ("true", "1", "yes")


class HubServer(BaseMCPServer):
    """Internal diagnostics — hidden from Claude by default."""

    def __init__(
        self,
        name: str = "hub",
        version: str = "0.1.0",
    ) -> None:
        super().__init__(name=name, version=version)

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        logger.info("Hub diagnostics initialized (expose=%s)", _EXPOSE)

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "status": "ok"}

    # ── Tools (hidden unless HUB_EXPOSE_INTERNAL_TOOLS=true) ─────

    async def get_tools(self) -> list[dict[str, Any]]:
        if not _EXPOSE:
            return []
        return [
            {
                "name": "hub.debug.status",
                "description": "[dev] Hub runtime status: version, uptime, server counts",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "hub.debug.services",
                "description": "[dev] List all registered MCP services",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "hub.debug.health",
                "description": "[dev] Health-check every registered service",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "hub.debug.metrics",
                "description": "[dev] Runtime metrics: requests, latency, uptime",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        registry = get_registry()

        if tool_name == "hub.debug.status":
            uptime = time.time() - (get_started_at() or time.time())
            return {
                "version": "0.3.0",
                "uptime_seconds": round(uptime, 0),
                "total_services": registry.count,
                "running_services": registry.running_count,
                "failed_services": registry.failed_count,
            }

        if tool_name == "hub.debug.services":
            return {
                "services": [
                    {"name": s["name"], "version": s["version"],
                     "running": s["running"], "failed": s.get("failed", False)}
                    for s in registry.list_servers()
                ]
            }

        if tool_name == "hub.debug.health":
            report = registry.aggregate_health()
            return {"aggregate": report["status"], "servers": report["servers"]}

        if tool_name == "hub.debug.metrics":
            return metrics_snapshot()

        raise ToolNotFoundError(self.name, tool_name)
