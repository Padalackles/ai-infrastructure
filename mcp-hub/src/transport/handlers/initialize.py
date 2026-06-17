"""Handler for the MCP 'initialize' method."""

from __future__ import annotations

from typing import Any

from src.runtime.runtime import Runtime


async def handle_initialize(runtime: Runtime, params: dict[str, Any]) -> dict[str, Any]:
    """Return Hub capabilities and registered server list."""
    return runtime.initialize_info()
