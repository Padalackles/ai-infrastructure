"""Event Bus — in-memory publish/subscribe messaging.

Provides a lightweight event system so MCP servers can communicate
asynchronously without direct coupling.

Future use:
    Ombre ──► EventBus ──► ntfy
    (memory stored → notification pushed)

Currently in-memory only. No persistence, no external broker.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[[str, Any], None]
"""Signature for event handlers: (event_name: str, data: Any) -> None"""


class EventBus:
    """Simple in-memory event bus for inter-service communication."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def publish(self, event: str, data: Any = None) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event name (e.g. 'memory.stored', 'task.completed').
            data: Optional payload to send with the event.

        Handlers are called synchronously. Exceptions in one handler do not
        prevent other handlers from receiving the event.
        """
        handlers = self._subscribers.get(event, [])
        if not handlers:
            return

        logger.debug("Event published: %s (handlers: %d)", event, len(handlers))
        for handler in handlers:
            try:
                handler(event, data)
            except Exception:
                logger.exception("Event handler failed for event: %s", event)

    def subscribe(self, event: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event.

        Args:
            event: The event name to listen for.
            handler: A callable matching the EventHandler signature.
        """
        self._subscribers[event].append(handler)
        logger.debug("Subscribed to event: %s", event)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event.

        Args:
            event: The event name.
            handler: The handler to remove.

        If the handler is not found, this is a no-op.
        """
        try:
            self._subscribers[event].remove(handler)
            logger.debug("Unsubscribed from event: %s", event)
        except ValueError:
            pass

    @property
    def event_count(self) -> int:
        """Return the number of distinct events with at least one subscriber."""
        return len(self._subscribers)
