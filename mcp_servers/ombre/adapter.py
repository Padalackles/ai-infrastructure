"""Ombre MCP Client — thin adapter over RemoteMCPClient.

All MCP protocol logic lives in src.core.remote_client.RemoteMCPClient.
This module only provides Ombre-specific defaults (URL, timeout).
"""

from __future__ import annotations

import os

from src.core.remote_client import RemoteMCPClient

DEFAULT_OMBRE_URL = os.getenv("OMBRE_URL", "http://45.76.169.98:8000/mcp")
DEFAULT_TIMEOUT = float(os.getenv("OMBRE_TIMEOUT", "10"))

# Re-export for backward compatibility
CONNECTED = "CONNECTED"
CONNECTING = "CONNECTING"
DISCONNECTED = "DISCONNECTED"


class OmbreMCPClient(RemoteMCPClient):
    """MCP client for the remote Ombre Brain server.

    Inherits all protocol logic from RemoteMCPClient.  Only sets
    Ombre-specific defaults so existing callers don't need to change.
    """

    def __init__(
        self,
        url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__(
            label="Ombre",
            url=url or DEFAULT_OMBRE_URL,
            timeout=timeout,
        )
