"""Trigger Service — business logic for the Trigger Queue.

Sits between the API router and the TriggerRepository.  Contains
all business logic: validation, ordering, deduplication, etc.
The router never touches the repository directly.

Example::

    from trigger.repository import TriggerRepository
    from trigger.service import TriggerService

    repo = TriggerRepository()
    service = TriggerService(repo)
    trigger = service.create_trigger(type="procrastination", payload={...})
    pending = service.get_oldest_pending()
    acked   = service.ack_trigger(trigger_id)
"""

from __future__ import annotations

from typing import Any

from trigger.models import Trigger
from trigger.repository import TriggerRepository


class TriggerService:
    """Business logic for the Trigger Queue.

    Wraps a ``TriggerRepository`` instance.  All consumers go
    through this service — never touching the repository directly.
    """

    def __init__(self, repository: TriggerRepository) -> None:
        """Create a service backed by *repository*."""
        self._repo = repository

    # ── Commands ──────────────────────────────────────────────────

    def create_trigger(
        self,
        type: str,
        payload: dict[str, Any] | None = None,
        priority: int = 1,
    ) -> dict[str, Any]:
        """Create and persist a new Trigger.

        Args:
            type: Trigger type, e.g. ``procrastination``.
            payload: Free-form JSON payload (default empty).
            priority: Queue priority — 0 highest, 1 normal, 2 low.

        Returns:
            The created trigger as a dict.
        """
        trigger = Trigger(
            type=type,
            payload=payload or {},
            priority=priority,
        )
        record = _trigger_to_dict(trigger)
        self._repo.save(record)
        return record

    def ack_trigger(self, trigger_id: str) -> dict[str, Any] | None:
        """Acknowledge a trigger.

        Marks the trigger as ``acked`` and sets ``acked_at``.

        Returns the updated trigger dict, or ``None`` if the trigger
        does not exist.
        """
        return self._repo.ack(trigger_id)

    # ── Queries ───────────────────────────────────────────────────

    def get_oldest_pending(self) -> dict[str, Any] | None:
        """Return the oldest pending trigger, or ``None``."""
        return self._repo.get_oldest_pending()

    def get_by_id(self, trigger_id: str) -> dict[str, Any] | None:
        """Return a trigger by ID, or ``None``."""
        return self._repo.get_by_id(trigger_id)

    def list_pending(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return all pending triggers, ordered by priority then age."""
        return self._repo.list_pending(limit=limit)


# ── Helpers ─────────────────────────────────────────────────────────


def _trigger_to_dict(trigger: Trigger) -> dict[str, Any]:
    """Convert a Trigger dataclass instance to a plain dict for storage."""
    return {
        "id": trigger.id,
        "type": trigger.type,
        "payload": trigger.payload,
        "status": trigger.status,
        "priority": trigger.priority,
        "created_at": trigger.created_at,
        "acked_at": trigger.acked_at,
    }
