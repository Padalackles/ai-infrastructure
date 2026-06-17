"""Transport — JSON-RPC 2.0 protocol layer between Claude Desktop and MCP Hub.

Generic transport. No server-specific logic. No hardcoded server names.
All dispatch goes through ServerManager registry.
"""

from src.transport.jsonrpc import parse_request
from src.transport.request import JSONRPCRequest
from src.transport.response import (
    ErrorCode,
    JSONRPCError,
    JSONRPCErrorDetail,
    JSONRPCErrorResponse,
    JSONRPCResponse,
    build_error,
    build_result,
)
from src.transport.router import Router

__all__ = [
    "ErrorCode",
    "JSONRPCError",
    "JSONRPCErrorDetail",
    "JSONRPCErrorResponse",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "Router",
    "build_error",
    "build_result",
    "parse_request",
]
