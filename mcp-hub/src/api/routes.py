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
    """Health-check endpoint with server inventory and aggregate status.

    Aggregate status:
        healthy  — all servers running, zero failed
        degraded — at least one server not running
        failed   — all registered servers failed to start

    Example:
        {"status": "healthy", "servers": [...], "total": 1, "running": 1, "failed": 0}
    """
    manager = _server_manager(request)
    total = manager.count
    running = manager.running_count
    failed = manager.failed_count

    if total == 0:
        aggregate = "healthy"
    elif failed == total:
        aggregate = "failed"
    elif running < total:
        aggregate = "degraded"
    else:
        aggregate = "healthy"

    return {
        "status": aggregate,
        "total_servers": total,
        "running_servers": running,
        "failed_servers": failed,
        "servers": manager.list_servers(),
    }


@router.get("/status")
async def status(request: Request) -> dict[str, Any]:
    """Runtime status with version info and server statistics.

    Example:
        {
            "version": "0.1.0",
            "runtime": "MCP Hub",
            "total_servers": 1,
            "running_servers": 1,
            "failed_servers": 0,
            "servers": [...]
        }
    """
    app = request.app
    manager = _server_manager(request)
    return {
        "version": app.state.version,
        "runtime": app.state.runtime_name,
        "total_servers": manager.count,
        "running_servers": manager.running_count,
        "failed_servers": manager.failed_count,
        "failed_names": manager.failed_servers,
        "servers": manager.list_servers(),
    }


@router.get("/tools")
async def tools_list(request: Request) -> dict[str, Any]:
    """Aggregated tool list from all registered MCP servers.

    Returns:
        {"tools": [{"server": "example", "tools": [...]}, ...]}
    """
    hub_router = request.app.state.router
    return await hub_router._handle_tools_list()
