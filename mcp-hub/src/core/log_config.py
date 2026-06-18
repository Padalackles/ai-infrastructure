"""Structured Logging Foundation — unified JSON logger for the MCP Hub.

Provides:
  - JSONFormatter: machine-readable single-line JSON log entries
  - setup_logging(): one-call configuration of root + file handlers
  - Request ID propagation via RequestContext
  - Audit log stream (logs/audit.log)
  - Convenience get_logger() with component metadata

Usage:
    from src.core.log_config import setup_logging, get_logger
    setup_logging(level="DEBUG")
    log = get_logger("transport")
    log.info("Ready")
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any


# ── Request ID helpers (delegate to RequestContext) ─────────────

def get_request_id() -> str:
    """Return the current request ID, or empty string."""
    from src.core.request_context import RequestContext
    return RequestContext.current().request_id


def set_request_id(rid: str) -> str:
    """Backward-compat — use RequestContext() context manager instead."""
    from src.core.request_context import RequestContext
    ctx = RequestContext.current()
    # Can't set on sentinel; this is a best-effort helper
    return ctx.request_id


# ── JSON Formatter ─────────────────────────────────────────────


class JSONFormatter(logging.Formatter):
    """Single-line JSON log records with all required fields."""

    def format(self, record: logging.LogRecord) -> str:
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
        obj: dict[str, Any] = {
            "ts": ts,
            "level": record.levelname,
            "component": getattr(record, "component", record.name),
            "msg": record.getMessage(),
        }
        rid = get_request_id()
        if rid:
            obj["request_id"] = rid
        if record.exc_info and record.exc_info[1]:
            obj["error"] = str(record.exc_info[1])
        # Extra fields from LoggerAdapter / extra=
        for key in ("plugin", "tool", "duration_ms", "service"):
            val = getattr(record, key, None)
            if val is not None:
                obj[key] = val
        return json.dumps(obj, ensure_ascii=False, default=str)


# ── Log directory ──────────────────────────────────────────────

_LOG_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs"
)


def _ensure_log_dir() -> str:
    os.makedirs(_LOG_DIR, exist_ok=True)
    return _LOG_DIR


# ── Setup ──────────────────────────────────────────────────────


def setup_logging(
    level: str = "INFO",
    log_dir: str | None = None,
    json_stdout: bool = True,
) -> None:
    """Configure root logger with JSON format + rotating file handler.

    Call once at startup (main.py).  After this, all standard
    `logging.getLogger(__name__)` calls produce structured JSON.
    """
    directory = log_dir or _ensure_log_dir()
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear any pre-existing handlers to avoid duplicates
    root.handlers.clear()

    # Console — JSON
    if json_stdout:
        console = logging.StreamHandler()
        console.setLevel(getattr(logging, level.upper(), logging.INFO))
        console.setFormatter(JSONFormatter())
        root.addHandler(console)

    # File — JSON, rotated
    file_handler = RotatingFileHandler(
        os.path.join(directory, "hub.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)

    # Error log — ERROR+ only
    error_handler = RotatingFileHandler(
        os.path.join(directory, "error.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root.addHandler(error_handler)

    logging.getLogger("mcp").setLevel(logging.DEBUG)


def get_logger(name: str, **extra) -> logging.Logger:
    """Return a logger that attaches extra fields (plugin, tool, etc.)
    to every record via a LoggerAdapter."""
    logger = logging.getLogger(name)
    if extra:
        return logging.LoggerAdapter(logger, extra)  # type: ignore[return-value]
    return logger


# ── Audit Logger ────────────────────────────────────────────────

_audit_logger: logging.Logger | None = None


def _get_audit_logger() -> logging.Logger:
    global _audit_logger
    if _audit_logger is not None:
        return _audit_logger
    _ensure_log_dir()
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
    now = datetime.now(timezone.utc)
    record = {
        "event": "tool_call",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z",
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
