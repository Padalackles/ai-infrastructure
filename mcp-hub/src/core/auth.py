"""MCP Auth — Bearer Token authentication for the /mcp endpoint.

If MCP_HUB_AUTH_TOKEN is set, all POST /mcp requests must include:
    Authorization: Bearer <token>

Otherwise auth is skipped (local dev / backward compatible).
REST endpoints (/health, /status, /tools) are never authenticated.

Uses FastAPI dependency injection — zero changes to handlers or router.
"""

from __future__ import annotations

import logging
import os

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

_AUTH_HEADER = "Authorization"
_BEARER_PREFIX = "Bearer "


def _get_configured_token() -> str | None:
    """Read the configured token. Empty string means auth is disabled.

    Called on every request so token changes take effect immediately
    and tests can control auth via environment variable without
    import-time caching side-effects.
    """
    token = os.getenv("MCP_HUB_AUTH_TOKEN", "").strip()
    return token if token else None


async def verify_bearer_token(request: Request) -> None:
    """FastAPI dependency: verify the Authorization header.

    Raises HTTPException(401) or returns None if auth passes / is disabled.
    Called once per request at the transport layer.
    """
    configured = _get_configured_token()
    if configured is None:
        # Auth not configured — pass through (local dev / backward compat)
        return

    auth_header = request.headers.get(_AUTH_HEADER, "")
    if not auth_header.startswith(_BEARER_PREFIX):
        logger.warning("AUTH_DENIED — missing or malformed Authorization header")
        raise _unauthorized(
            "Missing or malformed Authorization header. "
            "Expected: Bearer <token>"
        )

    token = auth_header[len(_BEARER_PREFIX):].strip()
    if token != configured:
        logger.warning("AUTH_DENIED — invalid token")
        raise _unauthorized("Invalid Bearer token")


def _unauthorized(message: str) -> HTTPException:
    """Build an HTTP 401 with a JSON-RPC-style error body."""
    return HTTPException(
        status_code=401,
        detail={
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32003,
                "message": f"Unauthorized: {message}",
            },
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
