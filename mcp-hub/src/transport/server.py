"""Transport server — FastAPI route that accepts JSON-RPC 2.0 requests.

This is the wire entry point for Claude Desktop (or any MCP client).
All business logic lives in the Router; this module handles HTTP concerns only.

Authentication is enforced via the verify_bearer_token dependency when
MCP_HUB_AUTH_TOKEN is configured. REST endpoints are never authenticated.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request

from src.core.auth import verify_bearer_token
from src.transport.jsonrpc import build_parse_error, parse_request
from src.transport.response import JSONRPCErrorResponse

logger = logging.getLogger("transport")

router = APIRouter()


@router.post("/mcp")
async def mcp_endpoint(
    request: Request,
    _auth: None = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """Accept a JSON-RPC 2.0 request and return a response.

    Request body format:
        {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}

    The response is always a JSON-RPC 2.0 response or error object.
    Notifications (requests without an id) return HTTP 202 with no body.
    """
    # Parse raw body
    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        error = build_parse_error(str(exc))
        logger.warning("PARSE_ERROR %s", exc)
        # id is unknown for parse errors
        return error.model_dump(exclude_none=True)

    # Parse and validate the JSON-RPC request
    parsed = parse_request(body)
    if isinstance(parsed, JSONRPCErrorResponse):
        return parsed.model_dump(exclude_none=True)

    # Route to the dispatcher
    hub_router = request.app.state.router
    response = await hub_router.route(parsed)

    # Notifications get a minimal response (not sent per spec)
    if parsed.is_notification:
        return {}

    return response.model_dump(exclude_none=True)
