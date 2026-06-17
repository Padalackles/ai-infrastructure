"""API routes for the MCP Hub.

Endpoints:
    GET /health  — health check with server inventory
    GET /status  — runtime status with version info
    GET /tools   — aggregated tool list
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.runtime.runtime import Runtime


def _runtime(request: Request) -> Runtime:
    return request.app.state.runtime


router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> dict[str, Any]:
    rt = _runtime(request)
    health = rt.aggregate_health()
    stats = rt.server_stats()
    return {
        "status": health["status"],
        "total_servers": stats["total_servers"],
        "running_servers": stats["running_servers"],
        "failed_servers": stats["failed_servers"],
        "servers": stats["servers"],
    }


@router.get("/status")
async def status(request: Request) -> dict[str, Any]:
    app = request.app
    rt = _runtime(request)
    stats = rt.server_stats()
    return {
        "version": app.state.version,
        "runtime": app.state.runtime_name,
        **stats,
    }


@router.get("/tools")
async def tools_list(request: Request) -> dict[str, Any]:
    rt = _runtime(request)
    return await rt.list_tools()
