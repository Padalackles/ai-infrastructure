"""JSON-RPC 2.0 parser — validates and converts raw dicts to typed models."""

from __future__ import annotations

import logging

from src.transport.request import JSONRPCRequest
from src.transport.response import (
    ErrorCode,
    JSONRPCErrorResponse,
    JSONRPCResponse,
    build_error,
)

logger = logging.getLogger(__name__)


def parse_request(data: dict) -> JSONRPCRequest | JSONRPCErrorResponse:
    """Parse and validate a raw dict into a JSONRPCRequest.

    Returns a JSONRPCErrorResponse if validation fails (for protocol-level
    errors). The caller should return this immediately without further routing.
    """
    # Must be a dict
    if not isinstance(data, dict):
        return build_error(None, ErrorCode.INVALID_REQUEST, "Request must be a JSON object")

    # Extract id early — it may be used in the error response
    req_id = data.get("id")

    # Validate jsonrpc version
    jsonrpc = data.get("jsonrpc")
    if jsonrpc != "2.0":
        return build_error(req_id, ErrorCode.INVALID_REQUEST, "jsonrpc must be '2.0'")

    # Validate method
    method = data.get("method")
    if not isinstance(method, str) or not method.strip():
        return build_error(req_id, ErrorCode.INVALID_REQUEST, "method must be a non-empty string")

    # Validate id type (if present). Per JSON-RPC 2.0 §5: if the id
    # cannot be determined, the response id MUST be Null.
    if req_id is not None and not isinstance(req_id, (int, str)):
        return build_error(None, ErrorCode.INVALID_REQUEST, "id must be a string, number, or null")

    # Build params
    params = data.get("params", {})

    try:
        return JSONRPCRequest(
            jsonrpc="2.0",
            id=req_id,
            method=method,
            params=params,
        )
    except Exception as exc:
        return build_error(req_id, ErrorCode.INVALID_REQUEST, str(exc))


def build_parse_error(exc_message: str) -> JSONRPCErrorResponse:
    """Return a PARSE_ERROR response when the request body is not valid JSON."""
    return build_error(None, ErrorCode.PARSE_ERROR, f"Parse error: {exc_message}")
