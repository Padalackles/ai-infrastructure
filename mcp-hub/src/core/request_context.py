"""Request Context — per-request metadata via contextvars.

Each MCP request gets a unique context propagated through all Hub
layers (MCPProxy → FastMCP → handlers → ServerManager → plugins)
without modifying function signatures.

Usage:
    ctx = RequestContext()          # auto-generates UUID request_id
    with ctx:
        ...                         # all code here shares the same context

    # In any downstream module:
    ctx = RequestContext.current()
    ctx.request_id                  # "a1b2c3d4e5f6"
    ctx.set("tool", "notify.send")
"""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any

_ctx: ContextVar["RequestContext | None"] = ContextVar("request_ctx", default=None)


class RequestContext:
    """Per-request metadata container, backed by a ContextVar.

    Fields:
        request_id   — UUID hex string (auto-generated)
        start_time   — time.time() when created
        plugin       — MCP service name (set by handler)
        tool         — tool name (set by handler)
    """

    __slots__ = ("request_id", "start_time", "_extra")

    def __init__(self, request_id: str | None = None) -> None:
        self.request_id = request_id or uuid.uuid4().hex[:12]
        self.start_time = time.time()
        self._extra: dict[str, Any] = {}

    # ── Dict-like access for extra fields ──────────────────────

    def set(self, key: str, value: Any) -> None:
        self._extra[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._extra.get(key, default)

    @property
    def plugin(self) -> str:
        return self._extra.get("plugin", "")

    @property
    def tool(self) -> str:
        return self._extra.get("tool", "")

    @property
    def duration_ms(self) -> float:
        return (time.time() - self.start_time) * 1000

    # ── Context manager ────────────────────────────────────────

    def __enter__(self) -> "RequestContext":
        self._token: Token = _ctx.set(self)
        return self

    def __exit__(self, *args: Any) -> None:
        _ctx.reset(self._token)

    # ── Static accessors ───────────────────────────────────────

    @staticmethod
    def current() -> "RequestContext":
        """Return the active context, or a no-op sentinel.

        Never returns None — callers can always access .request_id etc.
        without a None check.  The sentinel has request_id="" and
        duration_ms=0.
        """
        c = _ctx.get()
        if c is not None:
            return c
        return _SENTINEL


# Module-level sentinel so callers never get None
class _SentinelContext(RequestContext):
    __slots__ = ()

    def __init__(self) -> None:
        self.request_id = ""
        self.start_time = 0.0
        self._extra = {}

    def __enter__(self) -> "RequestContext":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


_SENTINEL = _SentinelContext()
