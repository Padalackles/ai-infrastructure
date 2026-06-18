"""Structured Logging — JSON-format logs with request correlation.

Every request gets a unique request_id propagated through Hub and
plugin logs via contextvars.  Audit events are written to a
separate JSON log stream.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

# ── Request ID context ──────────────────────────────────────────

_request_id: ContextVar[str] = ContextVar("request_id", default="")

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")


def set_request_id(rid: str | None = None) -> str:
    """Set a request ID for the current async context. Returns the ID."""
    rid = rid or uuid.uuid4().hex[:12]
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    """Get the current request ID, or empty string if not set."""
    return _request_id.get("")


# ── JSON Formatter ─────────────────────────────────────────────


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = get_request_id()
        if rid:
            obj["request_id"] = rid
        if record.exc_info and record.exc_info[1]:
            obj["error"] = str(record.exc_info[1])
        return json.dumps(obj, ensure_ascii=False, default=str)


# ── Audit Logger ────────────────────────────────────────────────


_audit_logger: logging.Logger | None = None


def _get_audit_logger() -> logging.Logger:
    global _audit_logger
    if _audit_logger is not None:
        return _audit_logger

    os.makedirs(_LOG_DIR, exist_ok=True)

    _audit_logger = logging.getLogger("mcp-hub.audit")
    _audit_logger.propagate = False
    _audit_logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        os.path.join(_LOG_DIR, "audit.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
    )
    handler.setFormatter(JSONFormatter())
    _audit_logger.addHandler(handler)
    return _audit_logger


def audit(
    service: str,
    tool: str,
    duration_ms: float,
    success: bool,
    error: str = "",
) -> None:
    """Write an audit record for a tool invocation."""
    record = {
        "event": "tool_call",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "tool": tool,
        "execution_time_ms": round(duration_ms, 1),
        "success": success,
    }
    rid = get_request_id()
    if rid:
        record["request_id"] = rid
    if error:
        record["error"] = error
    _get_audit_logger().info(json.dumps(record, ensure_ascii=False, default=str))
