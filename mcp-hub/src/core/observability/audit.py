"""Audit Logger — immutable record of every MCP tool invocation.

Audit records are metadata-only: plugin, tool, status, duration_ms,
request_id.  No prompt content, arguments, responses, tokens, or
Authorization headers are ever written.

The audit log (logs/audit.log) is separate from debug/error logs
and is designed as the data source for future Metrics and Dashboards.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

from src.core.request_context import RequestContext

_AUDIT_LOG_NAME = "audit.log"
_AUDIT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_AUDIT_BACKUP_COUNT = 5

_log_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "logs"
)


def _ensure_dir() -> str:
    os.makedirs(_log_dir, exist_ok=True)
    return _log_dir


# ── Logger singleton ────────────────────────────────────────────

_audit_logger: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    global _audit_logger
    if _audit_logger is not None:
        return _audit_logger

    directory = _ensure_dir()
    _audit_logger = logging.getLogger("mcp-hub.audit")
    _audit_logger.propagate = False
    _audit_logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        os.path.join(directory, _AUDIT_LOG_NAME),
        maxBytes=_AUDIT_MAX_BYTES,
        backupCount=_AUDIT_BACKUP_COUNT,
    )
    # Passthrough formatter — audit.record() already outputs valid JSON
    handler.setFormatter(logging.Formatter("%(message)s"))
    _audit_logger.addHandler(handler)
    return _audit_logger


# ── Public API ──────────────────────────────────────────────────


def record(
    plugin: str,
    tool: str,
    status: str,
    duration_ms: float,
    error_type: str = "",
) -> None:
    """Write an immutable audit record for a tool invocation.

    Args:
        plugin:      MCP service name (e.g. "ombre", "ntfy").
        tool:        Tool name (e.g. "hold", "notify.send").
        status:      "success" or "failure".
        duration_ms: Wall-clock time in milliseconds.
        error_type:  Python exception class name on failure, or "".

    Privacy: this function intentionally accepts NO arguments,
    responses, prompts, tokens, or headers.  It records only
    operational metadata.
    """
    ctx = RequestContext.current()
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

    record: dict[str, Any] = {
        "event": "tool_call",
        "ts": ts,
        "request_id": ctx.request_id,
        "plugin": plugin,
        "tool": tool,
        "status": status,
        "duration_ms": round(duration_ms, 1),
    }
    if error_type:
        record["error_type"] = error_type

    _get_logger().info(json.dumps(record, ensure_ascii=False))
