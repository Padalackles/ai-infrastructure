"""Router interfaces — abstract definitions for request dispatch.

Future implementations may support multiple transport protocols
(JSON-RPC, WebSocket, SSE). The interface remains protocol-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RouterInterface(ABC):
    """Abstract router — maps requests to handlers.

    Implementations:
      - JSONRPCRouter (current — src/transport/router.py)
      - WebSocketRouter (future)
      - SSERouter (future)
    """

    @abstractmethod
    async def route_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Route a request to the appropriate handler.

        Args:
            method: The MCP method name (e.g. 'tools/list').
            params: Request parameters.

        Returns:
            Response dict.
        """
        ...

    @abstractmethod
    async def dispatch(self, server_name: str, method: str, params: dict[str, Any]) -> Any:
        """Dispatch a method call to a specific server.

        Args:
            server_name: Target MCP server name.
            method: Method to invoke on the server.
            params: Method parameters.

        Returns:
            Method result.
        """
        ...


class RouteRegistry(ABC):
    """Abstract route registry — maps method names to handlers.

    TODO: implement dynamic handler registration in Task-005+.
    """

    @abstractmethod
    def register_route(self, method: str, handler: Any) -> None:
        """Register a handler for a method name."""
        ...

    @abstractmethod
    def get_handler(self, method: str) -> Any | None:
        """Resolve a handler by method name."""
        ...
