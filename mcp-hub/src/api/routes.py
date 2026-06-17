"""API routes for the MCP Hub.

Endpoints:
    GET /health  — health check with server inventory
    GET /status  — runtime status with version info
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request


def _server_manager(request: Request) -> Any:
    """Retrieve the ServerManager from app state."""
    return request.app.state.server_manager


router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> dict[str, Any]:
    """Health-check endpoint.

    Returns hub status and the health of every registered MCP server.

    Example:
        {"status": "ok", "servers": []}
    """
    manager = _server_manager(request)
    return {
        "status": "ok",
        "servers": manager.list_servers(),
    }


@router.get("/status")
async def status(request: Request) -> dict[str, Any]:
    """Runtime status endpoint.

    Returns version info and the current server inventory.

    Example:
        {"version": "0.1.0", "runtime": "MCP Hub", "servers": []}
    """
    app = request.app
    manager = _server_manager(request)
    return {
        "version": app.state.version,
        "runtime": app.state.runtime_name,
        "servers": manager.list_servers(),
    }
