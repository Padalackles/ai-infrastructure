"""Ombre MCP Server — Hub adapter for the external Ombre deployment.

Ombre is an independently deployed MCP-compatible long-term memory service
running at a remote endpoint. This adapter bridges the Hub to Ombre via HTTP.

No Ombre business logic lives here — this is pure integration.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from src.lifecycle.base_server import BaseMCPServer, ToolNotFoundError

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "http://45.76.169.98:8000"


class OmbreServer(BaseMCPServer):
    """Adapter that connects MCP Hub to the external Ombre deployment."""

    def __init__(
        self,
        name: str = "ombre",
        version: str = "0.1.0",
        endpoint: str | None = None,
    ) -> None:
        super().__init__(name=name, version=version)
        self._endpoint: str = endpoint or os.getenv("OMBRE_ENDPOINT", DEFAULT_ENDPOINT)
        self._connected: bool = False
        self._health_status: str = "DISCONNECTED"

    # ── Lifecycle ────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Check connectivity to the external Ombre deployment."""
        logger.info("Ombre adapter initializing — endpoint: %s", self._endpoint)
        try:
            status = await self._check_health()
            if status == "CONNECTED":
                self._connected = True
                self._health_status = "CONNECTED"
                logger.info("✓ Ombre (CONNECTED) — %s", self._endpoint)
            else:
                self._health_status = "UNHEALTHY"
                logger.warning("Ombre health check returned: %s", status)
        except Exception as exc:
            self._health_status = "DISCONNECTED"
            logger.warning("Ombre unreachable: %s — %s", self._endpoint, exc)

    async def start(self) -> None:
        """Mark as running if the health check passed."""
        if self._connected:
            logger.info("Ombre adapter started — endpoint: %s", self._endpoint)
        else:
            logger.warning("Ombre adapter started but not connected")

    async def stop(self) -> None:
        """Deregister from external Ombre."""
        self._connected = False
        self._health_status = "DISCONNECTED"
        logger.info("Ombre adapter stopped")

    # ── Health ───────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        """Return health status. Refreshes connectivity check."""
        try:
            self._health_status = await self._check_health()
            self._connected = self._health_status == "CONNECTED"
        except Exception:
            self._health_status = "DISCONNECTED"
            self._connected = False
        return {
            "name": self.name,
            "status": self._health_status,
            "endpoint": self._endpoint,
        }

    async def _check_health(self) -> str:
        """Call GET /health on the external Ombre deployment."""
        import http.client
        import json
        from urllib.parse import urlparse

        url = urlparse(self._endpoint)
        conn = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=5)
        try:
            conn.request("GET", "/health")
            resp = conn.getresponse()
            if resp.status == 200:
                body = json.loads(resp.read().decode())
                if body.get("status") == "ok":
                    return "CONNECTED"
            return "UNHEALTHY"
        except Exception:
            return "DISCONNECTED"
        finally:
            conn.close()

    # ── Tools ────────────────────────────────────────────────────

    async def get_tools(self) -> list[dict[str, Any]]:
        """Expose tools that forward to the external Ombre service."""
        return [
            {
                "name": "ombre_health",
                "description": "Check connectivity to the external Ombre deployment",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "ombre_status",
                "description": "Get Ombre service status and endpoint info",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Handle tool calls by forwarding to Ombre or returning local status."""
        if tool_name == "ombre_health":
            return await self.health()
        if tool_name == "ombre_status":
            return {
                "name": self.name,
                "version": self.version,
                "endpoint": self._endpoint,
                "connected": self._connected,
                "health": self._health_status,
            }
        raise ToolNotFoundError(self.name, tool_name)
