"""Hub State — shared references for MCP service plugins.

Plugins that need to inspect Hub internals (e.g. hub.status, hub.services)
import get_registry() / get_runtime() to access the live ServerManager
and Runtime without coupling to FastAPI request state.
"""

from __future__ import annotations

from typing import Any

_registry_ref: Any = None
_runtime_ref: Any = None
_started_at: float | None = None


def set_state(registry, runtime, started_at: float) -> None:
    """Called by main.py lifespan after discovery + runtime init."""
    global _registry_ref, _runtime_ref, _started_at
    _registry_ref = registry
    _runtime_ref = runtime
    _started_at = started_at


def get_registry() -> Any:
    if _registry_ref is None:
        raise RuntimeError("Registry not yet initialized")
    return _registry_ref


def get_runtime() -> Any:
    if _runtime_ref is None:
        raise RuntimeError("Runtime not yet initialized")
    return _runtime_ref


def get_started_at() -> float | None:
    return _started_at
