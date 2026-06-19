"""Decision Engine — cooldown abstraction.

A CooldownStore tracks the last time each rule fired. After a rule
triggers it enters a cooldown window.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class CooldownStore(ABC):
    """Abstract interface for rule cooldown tracking."""

    @abstractmethod
    def get(self, rule_id: str) -> datetime | None:
        """Return the last trigger time for *rule_id*, or None."""
        ...

    @abstractmethod
    def set(self, rule_id: str, timestamp: datetime) -> None:
        """Record that *rule_id* fired at *timestamp*."""
        ...


class MemoryCooldownStore(CooldownStore):
    """In-memory cooldown store backed by a plain dict.

    Cooldown state is lost on restart — acceptable for Phase 1.
    Replace with RedisCooldownStore for durable cooldowns.
    """

    def __init__(self) -> None:
        self._store: dict[str, datetime] = {}

    def get(self, rule_id: str) -> datetime | None:
        return self._store.get(rule_id)

    def set(self, rule_id: str, timestamp: datetime) -> None:
        self._store[rule_id] = timestamp
