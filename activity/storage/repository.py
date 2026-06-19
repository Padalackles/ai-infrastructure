"""Repository — CRUD operations for Activity Events.

Every method receives or returns plain ``dict`` objects.
SQL is never exposed to callers.

Example::

    repo = ActivityRepository()
    repo.save_event(event)
    found = repo.get_event("evt_abc123")
    recent = repo.list_events(limit=50)
    total  = repo.count_events()
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .database import get_connection

logger = logging.getLogger("mcp-hub.activity.storage.repository")


class ActivityRepository:
    """Persistence operations for normalized Activity Events.

    Thin wrapper around a SQLite connection.  Each method opens
    and closes its own connection — no shared state or pooling.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Create a repository bound to a specific database path.

        If *db_path* is omitted the default ``data/activity.db`` is used.
        """
        self._db_path = db_path

    # ── Create ──────────────────────────────────────────────────

    def save_event(self, event: dict[str, Any]) -> str:
        """Persist a normalized Activity Event.

        Returns the event ``id`` on success.

        Raises ``RuntimeError`` if the insert fails (connection error,
        constraint violation, etc.).
        """
        conn = get_connection(self._db_path)
        try:
            now = _utc_now_iso()
            conn.execute(
                _INSERT_EVENT,
                {
                    "id": event["id"],
                    "version": event.get("version", 1),
                    "timestamp": event["timestamp"],
                    "source": event["source"],
                    "collector": event["collector"],
                    "device": event["device"],
                    "type": event["type"],
                    "payload": _serialize_json(event.get("payload", {})),
                    "raw": _serialize_json(event.get("raw", {})),
                    "created_at": now,
                },
            )
            conn.commit()
            logger.info(
                "Saved event  id=%s  type=%s  device=%s",
                event["id"],
                event["type"],
                event.get("device", "?"),
            )
            return event["id"]
        except Exception as exc:
            logger.exception("Failed to save event id=%s: %s", event.get("id", "?"), exc)
            raise RuntimeError(f"Failed to save event: {exc}") from exc
        finally:
            conn.close()

    # ── Read ────────────────────────────────────────────────────

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        """Retrieve a single event by ID.

        Returns ``None`` if not found.
        """
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(_SELECT_BY_ID, {"id": event_id}).fetchone()
            if row is None:
                return None
            return _row_to_event(row)
        finally:
            conn.close()

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent events, newest first.

        *limit* is clamped to [1, 1000].
        """
        limit = max(1, min(limit, 1000))
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(_SELECT_RECENT, {"limit": limit}).fetchall()
            return [_row_to_event(r) for r in rows]
        finally:
            conn.close()

    def count_events(self) -> int:
        """Return the total number of stored events."""
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(_COUNT_EVENTS).fetchone()
            return int(row[0]) if row else 0
        finally:
            conn.close()

    def get_by_type(self, event_type: str, limit: int = 100) -> list[dict[str, Any]]:
        """Return events of a specific canonical type, newest first.

        *limit* is clamped to [1, 1000].
        """
        limit = max(1, min(limit, 1000))
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(
                _SELECT_BY_TYPE,
                {"type": event_type, "limit": limit},
            ).fetchall()
            return [_row_to_event(r) for r in rows]
        finally:
            conn.close()

    def get_between(
        self, start: str, end: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Return events within a timestamp range, newest first.

        *limit* is clamped to [1, 1000].
        """
        limit = max(1, min(limit, 1000))
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(
                _SELECT_BETWEEN,
                {"start": start, "end": end, "limit": limit},
            ).fetchall()
            return [_row_to_event(r) for r in rows]
        finally:
            conn.close()

    def get_latest(self, event_type: str) -> dict[str, Any] | None:
        """Return the most recent event of a given type, or None."""
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                _SELECT_LATEST, {"type": event_type}
            ).fetchone()
            if row is None:
                return None
            return _row_to_event(row)
        finally:
            conn.close()

    def list_types(self) -> list[str]:
        """Return all distinct canonical event types in the database."""
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(_SELECT_DISTINCT_TYPES).fetchall()
            return sorted(r["type"] for r in rows)
        finally:
            conn.close()


# ── SQL (private) ───────────────────────────────────────────────────

_INSERT_EVENT = """
INSERT INTO events (id, version, timestamp, source, collector, device, type, payload, raw, created_at)
VALUES (:id, :version, :timestamp, :source, :collector, :device, :type, :payload, :raw, :created_at)
"""

_SELECT_BY_ID = """
SELECT id, version, timestamp, source, collector, device, type, payload, raw, created_at
FROM events
WHERE id = :id
"""

_SELECT_RECENT = """
SELECT id, version, timestamp, source, collector, device, type, payload, raw, created_at
FROM events
ORDER BY created_at DESC
LIMIT :limit
"""

_COUNT_EVENTS = "SELECT COUNT(*) FROM events"

_SELECT_BY_TYPE = """
SELECT id, version, timestamp, source, collector, device, type, payload, raw, created_at
FROM events
WHERE type = :type
ORDER BY created_at DESC
LIMIT :limit
"""

_SELECT_BETWEEN = """
SELECT id, version, timestamp, source, collector, device, type, payload, raw, created_at
FROM events
WHERE timestamp >= :start AND timestamp <= :end
ORDER BY timestamp DESC
LIMIT :limit
"""

_SELECT_LATEST = """
SELECT id, version, timestamp, source, collector, device, type, payload, raw, created_at
FROM events
WHERE type = :type
ORDER BY timestamp DESC
LIMIT 1
"""

_SELECT_DISTINCT_TYPES = """
SELECT DISTINCT type FROM events ORDER BY type
"""


# ── Helpers ─────────────────────────────────────────────────────────


def _row_to_event(row: Any) -> dict[str, Any]:
    """Convert a sqlite3.Row to the canonical event dict."""
    return {
        "version": row["version"],
        "id": row["id"],
        "timestamp": row["timestamp"],
        "source": row["source"],
        "collector": row["collector"],
        "device": row["device"],
        "type": row["type"],
        "payload": _deserialize_json(row["payload"]),
        "raw": _deserialize_json(row["raw"]),
        "created_at": row["created_at"],
    }


def _serialize_json(obj: Any) -> str:
    """Serialize *obj* to a compact JSON string."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _deserialize_json(text: str) -> Any:
    """Parse a JSON string back to a Python object."""
    return json.loads(text) if text else {}


def _utc_now_iso() -> str:
    """Current UTC time as ISO 8601 with millisecond precision."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
