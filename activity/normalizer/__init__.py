"""Event Normalizer — canonical event transformation.

Transforms collector-specific Activity Events into the unified
canonical format consumed by downstream components (Database,
Decision Script, Claude Trigger).

Responsibilities:
* Map collector-specific event names to canonical event names.
* Normalize payload structure where appropriate.
* Preserve the original event in the ``raw`` field.
* Mark unknown event types without crashing.

The Normalizer is source-independent — MacroDroid, Tasker,
Apple Shortcuts, Home Assistant, etc. all produce the same
canonical output shape.

Design:
* ``mappings.py`` — extensible event-name mapping table.
* ``service.py`` — pure normalization functions (no side effects).

Principles:
* No SQLite writes.
* No business decisions.
* No reminders, Claude calls, or ntfy awareness.
"""

from .service import normalize_event

__all__ = ["normalize_event"]
