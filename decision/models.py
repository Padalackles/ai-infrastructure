"""Decision Engine — domain models.

Two output models:

1.  ``TriggerRequest`` (current) — a rule's *intent* to create a trigger.
    Rules return what should happen; the Trigger service decides how
    to persist and manage it.  No database concepts leak into rules.

2.  ``Trigger`` (deprecated) — Phase 1 console-only output.  Kept for
    backward compatibility.  New code should use ``TriggerRequest``.

Design:
    * Plain dataclasses — no Pydantic, no ORM.
    * Rules never touch database IDs, status, or timestamps.
    * The ``type`` + ``payload`` contract is consumed by TriggerService.
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
class TriggerRequest:
    """A rule's intent to create a Trigger.

    Rules return this when they detect a condition worth acting on.
    It carries no database concepts — no id, status, or timestamps.
    The TriggerService is responsible for turning this into a
    persisted ``Trigger`` record.

    Attributes:
        type: Stable trigger type, e.g. ``procrastination``, ``battery.low``.
        payload: Free-form JSON payload with rule-specific data.
        priority: Queue priority — 0 highest, 1 normal, 2 low.
    """

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 1

    def __repr__(self) -> str:
        return (
            f"TriggerRequest(type={self.type!r}, "
            f"priority={self.priority!r}, payload={self.payload!r})"
        )


# Deprecated — kept for Phase 1 console scheduler backward compatibility.
# New code should use ``TriggerRequest`` instead.
@dataclass
class Trigger:
    """Deprecated — use ``TriggerRequest`` for new code.

    Phase 1 console-only output.  Kept for backward compatibility
    with ``decision.scheduler`` printing.

    Attributes:
        id: Globally unique trigger ID (``trg_<...>``).
        type: Stable trigger type, e.g. ``focus.timeout``, ``battery.low``.
        timestamp: ISO 8601 UTC timestamp of trigger creation.
        payload: Rule-specific data payload.
    """

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=_generate_trigger_id)
    timestamp: str = field(default_factory=_utc_now_iso)

    def __repr__(self) -> str:
        return (
            f"Trigger(id={self.id!r}, type={self.type!r}, "
            f"timestamp={self.timestamp!r}, payload={self.payload!r})"
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
