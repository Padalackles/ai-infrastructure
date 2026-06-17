"""JSON-RPC 2.0 response models and error codes.

Spec: https://www.jsonrpc.org/specification
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(IntEnum):
    """Standard JSON-RPC 2.0 error codes plus MCP Hub extensions."""

    # ── JSON-RPC 2.0 standard errors ──
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # ── MCP Hub extensions (server errors: -32000 to -32099) ──
    SERVER_NOT_FOUND = -32001
    TOOL_NOT_FOUND = -32002


class JSONRPCErrorDetail(BaseModel):
    """The error object inside a JSON-RPC error response."""

    code: int
    message: str
    data: Any = Field(default=None)


class JSONRPCResponse(BaseModel):
    """A JSON-RPC 2.0 success response."""

    jsonrpc: str = Field(default="2.0")
    id: int | str | None = Field(default=None)
    result: Any = Field(default=None)


class JSONRPCErrorResponse(BaseModel):
    """A JSON-RPC 2.0 error response."""

    jsonrpc: str = Field(default="2.0")
    id: int | str | None = Field(default=None)
    error: JSONRPCErrorDetail


# ── Response builders ──────────────────────────────────────────


def build_result(id: int | str | None, result: Any) -> JSONRPCResponse:
    """Build a JSON-RPC success response."""
    return JSONRPCResponse(id=id, result=result)


def build_error(
    id: int | str | None,
    code: int,
    message: str,
    data: Any = None,
) -> JSONRPCErrorResponse:
    """Build a JSON-RPC error response."""
    return JSONRPCErrorResponse(
        id=id,
        error=JSONRPCErrorDetail(code=code, message=message, data=data),
    )


# ── Exception for router dispatch ──────────────────────────────


class JSONRPCError(Exception):
    """Raised by router handlers to signal a JSON-RPC error.

    The router catches this and converts it to a JSONRPCErrorResponse.
    This class is an Exception so it works with raise/except.
    """

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code: int = code
        self.message: str = message
        self.data: Any = data

    def to_response(self, req_id: int | str | None = None) -> JSONRPCErrorResponse:
        return build_error(req_id, self.code, self.message, self.data)
