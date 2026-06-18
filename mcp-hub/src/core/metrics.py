"""Runtime Metrics — thread-safe counters and latency trackers.

Tracks total/success/failed requests, per-service stats, and uptime.
All updates are O(1).  Exposed via hub.metrics MCP tool.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict

_lock = threading.Lock()

_started_at: float = time.time()

_requests_total: int = 0
_requests_success: int = 0
_requests_failed: int = 0
_requests_by_service: dict[str, int] = defaultdict(int)
_latency_samples: list[float] = []  # last 1000 samples for avg computation


def record_request(
    service: str,
    tool: str,
    duration_ms: float,
    success: bool,
) -> None:
    """Record a tool invocation result."""
    global _requests_total, _requests_success, _requests_failed
    with _lock:
        _requests_total += 1
        if success:
            _requests_success += 1
        else:
            _requests_failed += 1
        _requests_by_service[service] += 1

        # Rolling window of last 1000 latencies
        _latency_samples.append(duration_ms)
        if len(_latency_samples) > 1000:
            _latency_samples.pop(0)


def snapshot() -> dict:
    """Return a consistent snapshot of all metrics."""
    with _lock:
        avg_latency = (
            sum(_latency_samples) / len(_latency_samples)
            if _latency_samples else 0.0
        )
        return {
            "uptime_seconds": round(time.time() - _started_at, 0),
            "requests_total": _requests_total,
            "requests_success": _requests_success,
            "requests_failed": _requests_failed,
            "avg_latency_ms": round(avg_latency, 1),
            "requests_by_service": dict(_requests_by_service),
        }
