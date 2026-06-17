"""MCP Server — base class for MCP service implementations."""

from typing import Any


class MCPServer:
    """Base class for MCP service implementations.

    Every MCP service (Filesystem, GitHub, Ombre, ntfy, etc.) extends this class
    and registers itself with the MCP Hub via the MCPRegistry.
    """

    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name: str = name
        self.version: str = version
        self._running: bool = False

    async def start(self) -> None:
        """Start the MCP server and register with the Hub."""
        self._running = True

    async def stop(self) -> None:
        """Stop the MCP server and deregister from the Hub."""
        self._running = False

    async def handle_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Handle an incoming request from the MCP Hub.

        Args:
            method: The method name to invoke.
            params: Optional parameters for the method.

        Returns:
            The result of the method invocation.
        """
        pass

    @property
    def is_running(self) -> bool:
        """Return whether the server is currently running."""
        return self._running
