"""Handlers — per-method JSON-RPC request processing.

Each handler receives a Runtime reference and a parsed JSONRPCRequest.
No handler ever references a concrete server implementation.
"""

from src.transport.handlers.health import handle_health
from src.transport.handlers.initialize import handle_initialize
from src.transport.handlers.tools import handle_tools_call, handle_tools_list

__all__ = [
    "handle_health",
    "handle_initialize",
    "handle_tools_call",
    "handle_tools_list",
]
