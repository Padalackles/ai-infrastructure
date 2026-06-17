"""Ombre Adapter — HTTP bridge to the external Ombre deployment.

Handles: endpoint management, connection, health checking.
Does NOT implement: memory, search, or any Ombre business logic.
"""

from __future__ import annotations

import http.client
import json
import logging
import os
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = "http://45.76.169.98:8000"
DEFAULT_TIMEOUT = 5  # seconds


class OmbreAdapter:
    """HTTP adapter for the external Ombre deployment.

    Responsibilities:
      - endpoint management
      - connection handling
      - health checking
      - service metadata
    """

    def __init__(self, endpoint: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._endpoint: str = endpoint or os.getenv("OMBRE_ENDPOINT", DEFAULT_ENDPOINT)
        self._timeout: int = timeout
        self._connected: bool = False

    # ── Properties ──────────────────────────────────────────────

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def timeout(self) -> int:
        return self._timeout

    # ── Connection ──────────────────────────────────────────────

    async def connect(self) -> str:
        """Check connectivity and return health status.

        Returns:
            CONNECTED   — HTTP 200, status=="ok"
            UNHEALTHY   — HTTP response but health check failed
            DISCONNECTED — network error or timeout
        """
        try:
            status = await self._check_health()
            self._connected = status == "CONNECTED"
            return status
        except Exception as exc:
            self._connected = False
            logger.warning("Ombre unreachable at %s: %s", self._endpoint, exc)
            return "DISCONNECTED"

    async def disconnect(self) -> None:
        """Mark as disconnected."""
        self._connected = False

    # ── Health ──────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        """Return health status of the external Ombre deployment."""
        status = await self.connect()
        return {
            "endpoint": self._endpoint,
            "status": status,
            "connected": self._connected,
        }

    async def _check_health(self) -> str:
        """Call GET /health on the external deployment."""
        url = urlparse(self._endpoint)
        conn = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=self._timeout)
        try:
            conn.request("GET", "/health")
            resp = conn.getresponse()
            if resp.status == 200:
                body = json.loads(resp.read().decode())
                if body.get("status") == "ok":
                    return "CONNECTED"
            return "UNHEALTHY"
        finally:
            conn.close()

    # ── Info ────────────────────────────────────────────────────

    def info(self) -> dict[str, Any]:
        """Return adapter metadata."""
        return {
            "endpoint": self._endpoint,
            "connected": self._connected,
            "timeout": self._timeout,
        }
