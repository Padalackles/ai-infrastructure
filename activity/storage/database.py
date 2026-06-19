"""Database connection management.

Handles SQLite connection lifecycle and schema bootstrapping.
No ORM — standard-library ``sqlite3`` only.

The database file is created automatically on first access.
Default path: ``data/activity.db`` (repo-relative).
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger("mcp-hub.activity.storage.database")

# Repo-relative default path.
_DEFAULT_DB_PATH = Path("data") / "activity.db"

# Module-level overridable for tests.
_db_path: Path | None = None


def get_db_path() -> Path:
    """Return the resolved database path.

    Respects ``set_db_path()`` overrides (used by tests).
    Otherwise defaults to ``<repo-root>/data/activity.db``.
    """
    if _db_path is not None:
        return _db_path
    return _DEFAULT_DB_PATH.resolve()


def set_db_path(path: Path | str) -> None:
    """Override the database path (intended for tests).

    Pass ``None`` to reset to the default.
    """
    global _db_path
    _db_path = Path(path) if path is not None else None


def init_db(db_path: Path | str | None = None) -> Path:
    """Bootstrap the database.

    1. Ensure the parent directory exists.
    2. Create the ``events`` table if it does not already exist.
    3. Return the resolved database path.

    Idempotent — safe to call on every startup.
    """
    path = Path(db_path) if db_path else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(_CREATE_EVENTS_DDL)
        conn.commit()
        logger.info("Database ready: %s", path)
    finally:
        conn.close()

    return path


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Return a new read/write connection.

    Caller is responsible for closing it.
    """
    path = Path(db_path) if db_path else get_db_path()
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


# ── DDL ────────────────────────────────────────────────────────────

_CREATE_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS events (
    id          TEXT PRIMARY KEY,
    version     INTEGER NOT NULL DEFAULT 1,
    timestamp   TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    collector   TEXT    NOT NULL,
    device      TEXT    NOT NULL,
    type        TEXT    NOT NULL,
    payload     TEXT    NOT NULL DEFAULT '{}',
    raw         TEXT    NOT NULL DEFAULT '{}',
    created_at  TEXT    NOT NULL
)
"""
