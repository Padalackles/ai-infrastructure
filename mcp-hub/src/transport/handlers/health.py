"""Handler for the MCP 'health' method."""

from __future__ import annotations

from typing import Any

from src.runtime.runtime import Runtime


async def handle_health(runtime: Runtime, params: dict[str, Any]) -> dict[str, Any]:
    """Aggregate health from all servers via Runtime."""
    return runtime.aggregate_health()
