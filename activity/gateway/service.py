"""Activity Gateway — service logic.

Pure functions for ID generation, timestamp assignment, and event assembly.
No side effects — logging happens in the router layer.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import ActivityEventRequest


def generate_event_id() -> str:
    """Generate a unique event ID.

    Format: evt_<12-char base36 timestamp><8-char base36 random>
    This is ULID-inspired: time-sortable, URL-safe, globally unique.
    """
    now_ms = int(time.time() * 1000)
    # Base36 encode the timestamp for compactness
    ts_part = _base36_encode(now_ms).zfill(8)
    rand_part = uuid.uuid4().hex[:8]
    return f"evt_{ts_part}{rand_part}"


def utc_now_iso() -> str:
    """Current UTC time as ISO 8601 with millisecond precision."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def build_event(request: ActivityEventRequest) -> dict[str, Any]:
    """Assemble a complete Activity Event from a client request.

    Fills in server-side fields (version, id, timestamp, raw) when
    the client omits them.  Returns the full event dict ready for
    downstream processing.
    """
    return {
        "version": request.version if request.version is not None else 1,
        "id": request.id if request.id else generate_event_id(),
        "timestamp": request.timestamp if request.timestamp else utc_now_iso(),
        "source": request.source,
        "collector": request.collector,
        "device": request.device,
        "type": request.type,
        "payload": request.payload,
        "raw": request.raw if request.raw is not None else {},
    }


# ── Helpers ───────────────────────────────────────────────────────

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
