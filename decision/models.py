"""Decision Engine — unified Trigger model.

The Trigger is the *only* output of the Decision Engine.  Every rule
that fires produces exactly one Trigger.  Downstream components
(console printer, future Claude bridge) consume Triggers — they
never interact with rules directly.

Design:
    * Plain dataclass — no Pydantic, no ORM.
    * Stable schema — the ``type`` + ``payload`` contract will be
      consumed by Claude in Phase 2.
    * ID is auto-generated for traceability.
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
    """A decision emitted by the Decision Engine.

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
