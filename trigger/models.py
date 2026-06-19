"""Trigger — database-backed dataclass for the Trigger Queue.

The Trigger is the unit of work between Decision and MacroDroid.
Decision rules create Trigger records; MacroDroid polls for pending
Triggers and acks them after processing.

Design:
    * Plain dataclass — no Pydantic, no ORM.
    * ID is time-sortable for efficient queue ordering.
    * ``status`` + ``acked_at`` track lifecycle.
    * ``priority`` controls queue order (0 = highest, 1 = normal, 2 = low).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _generate_trigger_id() -> str:
    """Generate a time-sortable trigger ID: trg_<base36-ts><hex-random>."""
    now_ms = int(time.time() * 1000)
    ts_part = _base36_encode(now_ms).zfill(8)
    rand_part = uuid.uuid4().hex[:8]
    return f"trg_{ts_part}{rand_part}"


def _utc_now_iso() -> str:
    """Current UTC time as ISO 8601 with millisecond precision."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


@dataclass
class Trigger:
    """A trigger record in the queue.

    Attributes:
        id: Globally unique trigger ID (``trg_<...>``).
        type: Stable trigger type, e.g. ``procrastination``, ``sleep``.
        payload: Free-form JSON payload set by the Decision rule.
        status: Lifecycle status — ``pending`` or ``acked``.
        priority: Queue priority — 0 highest, 1 normal, 2 low.
        created_at: ISO 8601 UTC timestamp of creation.
        acked_at: ISO 8601 UTC timestamp of acknowledgement, or None.
    """

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    status: str = "pending"
    id: str = field(default_factory=_generate_trigger_id)
    created_at: str = field(default_factory=_utc_now_iso)
    acked_at: str | None = None

    def __repr__(self) -> str:
        return (
            f"Trigger(id={self.id!r}, type={self.type!r}, "
            f"status={self.status!r}, priority={self.priority!r}, "
            f"created_at={self.created_at!r})"
        )


# ── Helpers ─────────────────────────────────────────────────────────

_BASE36_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"


def _base36_encode(num: int) -> str:
    """Encode an integer as a lowercase base-36 string."""
    if num == 0:
        return "0"
    chars = []
    while num > 0:
        num, rem = divmod(num, 36)
        chars.append(_BASE36_CHARS[rem])
    return "".join(reversed(chars))
