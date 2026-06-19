"""Repository — CRUD operations for Trigger records.

Every method receives or returns plain ``dict`` objects.
SQL is never exposed to callers.

Uses the shared ``activity.db`` database — Triggers live alongside
Activity Events in the same SQLite file.

Example::

    repo = TriggerRepository()
    trigger_id = repo.save(trigger_dict)
    pending = repo.get_oldest_pending()
    acked  = repo.ack(trigger_id)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from activity.storage.database import get_connection

logger = logging.getLogger("mcp-hub.trigger.repository")


class TriggerRepository:
    """Persistence operations for Trigger records.

    Thin wrapper around a SQLite connection.  Each method opens
    and closes its own connection — no shared state or pooling.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Create a repository bound to a specific database path.

        If *db_path* is omitted the default ``data/activity.db`` is used.
        """
        self._db_path = db_path

    # ── Create ──────────────────────────────────────────────────

    def save(self, trigger: dict[str, Any]) -> str:
        """Persist a Trigger record.

        Returns the trigger ``id`` on success.

        Raises ``RuntimeError`` if the insert fails.
        """
        conn = get_connection(self._db_path)
        try:
            conn.execute(
                _INSERT_TRIGGER,
                {
                    "id": trigger["id"],
                    "type": trigger["type"],
                    "payload": _serialize_json(trigger.get("payload", {})),
                    "status": trigger.get("status", "pending"),
                    "priority": trigger.get("priority", 1),
                    "created_at": trigger["created_at"],
                    "acked_at": trigger.get("acked_at"),
                },
            )
            conn.commit()
            logger.info(
                "Saved trigger  id=%s  type=%s  priority=%s",
                trigger["id"],
                trigger["type"],
                trigger.get("priority", 1),
            )
            return trigger["id"]
        except Exception as exc:
            logger.exception(
                "Failed to save trigger id=%s: %s", trigger.get("id", "?"), exc
            )
            raise RuntimeError(f"Failed to save trigger: {exc}") from exc
        finally:
            conn.close()

    # ── Read ────────────────────────────────────────────────────

    def get_by_id(self, trigger_id: str) -> dict[str, Any] | None:
        """Retrieve a single trigger by ID.

        Returns ``None`` if not found.
        """
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                _SELECT_BY_ID, {"id": trigger_id}
            ).fetchone()
            if row is None:
                return None
            return _row_to_trigger(row)
        finally:
            conn.close()

    def get_oldest_pending(self) -> dict[str, Any] | None:
        """Return the oldest pending trigger (lowest priority first).

        If multiple triggers share the same priority, the oldest
        (by ``created_at``) is returned.

        Returns ``None`` if no pending triggers exist.
        """
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(_SELECT_OLDEST_PENDING).fetchone()
            if row is None:
                return None
            return _row_to_trigger(row)
        finally:
            conn.close()

    def list_pending(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return all pending triggers, ordered by priority then age.

        *limit* is clamped to [1, 1000].
        """
        limit = max(1, min(limit, 1000))
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(
                _SELECT_PENDING, {"limit": limit}
            ).fetchall()
            return [_row_to_trigger(r) for r in rows]
        finally:
            conn.close()

    # ── Update ──────────────────────────────────────────────────

    def ack(self, trigger_id: str) -> dict[str, Any] | None:
        """Mark a trigger as acknowledged.

        Sets ``status='acked'`` and ``acked_at`` to the current UTC time.
        Returns the updated trigger dict, or ``None`` if the trigger
        does not exist.
        """
        conn = get_connection(self._db_path)
        try:
            now = _utc_now_iso()
            cursor = conn.execute(
                _ACK_TRIGGER,
                {"id": trigger_id, "acked_at": now},
            )
            conn.commit()
            if cursor.rowcount == 0:
                return None
            # Re-fetch to return full row
            row = conn.execute(
                _SELECT_BY_ID, {"id": trigger_id}
            ).fetchone()
            return _row_to_trigger(row) if row else None
        finally:
            conn.close()


# ── SQL (private) ───────────────────────────────────────────────────

_INSERT_TRIGGER = """
INSERT INTO triggers (id, type, payload, status, priority, created_at, acked_at)
VALUES (:id, :type, :payload, :status, :priority, :created_at, :acked_at)
"""

_SELECT_BY_ID = """
SELECT id, type, payload, status, priority, created_at, acked_at
FROM triggers
WHERE id = :id
"""

_SELECT_OLDEST_PENDING = """
SELECT id, type, payload, status, priority, created_at, acked_at
FROM triggers
WHERE status = 'pending'
ORDER BY priority ASC, created_at ASC
LIMIT 1
"""

_SELECT_PENDING = """
SELECT id, type, payload, status, priority, created_at, acked_at
FROM triggers
WHERE status = 'pending'
ORDER BY priority ASC, created_at ASC
LIMIT :limit
"""

_ACK_TRIGGER = """
UPDATE triggers
SET status = 'acked', acked_at = :acked_at
WHERE id = :id
"""


# ── Helpers ─────────────────────────────────────────────────────────


def _row_to_trigger(row: Any) -> dict[str, Any]:
    """Convert a sqlite3.Row to the canonical trigger dict."""
    return {
        "id": row["id"],
        "type": row["type"],
        "payload": _deserialize_json(row["payload"]),
        "status": row["status"],
        "priority": row["priority"],
        "created_at": row["created_at"],
        "acked_at": row["acked_at"],
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
