"""Activity Service — unified read interface for event queries.

Provides the single access point for all event queries.  Downstream
components (Decision Script, Claude Trigger, Web UI) read events
through this service — never through direct database access.

Design:
    * 100 % read-only — writes stay on the Repository / Gateway.
    * Thin pass-through — delegates directly to ActivityRepository.
    * No business logic, no decision-making, no side effects.
    * Constructor injection makes the repository swappable (e.g.
      PostgreSQL-backed repository in the future).

Example::

    from activity.storage.repository import ActivityRepository
    from activity.service import ActivityService

    repo = ActivityRepository()
    service = ActivityService(repo)
    recent = service.get_recent(20)
"""

from __future__ import annotations

from typing import Any

from activity.storage.repository import ActivityRepository


class ActivityService:
    """Read-only query service for Activity Events.

    Wraps an ``ActivityRepository`` instance so that all consumers
    go through a single, swappable interface — never touching
    SQLite or the repository directly.
    """

    def __init__(self, repository: ActivityRepository) -> None:
        """Create a service backed by *repository*."""
        self._repo = repository

    # ── Queries ──────────────────────────────────────────────────

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent events, newest first.

        *limit* is clamped to [1, 1000] by the repository.
        """
        return self._repo.list_events(limit=limit)

    def get_latest(self, event_type: str) -> dict[str, Any] | None:
        """Return the most recent event of *event_type*, or ``None``."""
        if not event_type or not event_type.strip():
            return None
        return self._repo.get_latest(event_type.strip())

    def get_between(
        self, start: str, end: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Return events with ``timestamp`` in [*start*, *end*].

        Results are ordered newest-first.  *limit* is clamped to
        [1, 1000] by the repository.
        """
        return self._repo.get_between(start, end, limit=limit)

    def get_by_type(
        self, event_type: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return events of *event_type*, newest first.

        *limit* is clamped to [1, 1000] by the repository.
        """
        if not event_type or not event_type.strip():
            return []
        return self._repo.get_by_type(event_type.strip(), limit=limit)

    def list_types(self) -> list[str]:
        """Return all distinct canonical event types currently stored."""
        return self._repo.list_types()
