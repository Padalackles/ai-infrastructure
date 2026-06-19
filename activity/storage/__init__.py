"""Activity Storage — SQLite persistence layer.

Stores normalized Activity Events in a local SQLite database.
Provides a clean repository interface — callers never touch SQL.

Responsibilities:
* ``database.py`` — connection management, table creation.
* ``repository.py`` — CRUD operations (save, get, list, count).

This layer is *only* persistence.  It knows nothing about:
* The Gateway (HTTP)
* The Normalizer (transformation)
* Decision logic
* Claude or ntfy

Database: ``data/activity.db`` (auto-created on first use).
"""

from .database import get_db_path, init_db
from .repository import ActivityRepository

__all__ = ["get_db_path", "init_db", "ActivityRepository"]
