"""Decision Engine — session analyzer.

Extracts time-window information from Activity Events.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class SessionAnalyzer:
    """Analyze Activity Events for screen and app sessions.

    *events* is injected at construction.
    """

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._events = sorted(events, key=_event_ts)

    def get_current_screen_session(self) -> dict[str, Any] | None:
        """Return the *active* screen session, or None."""
        last_on = self._find_last("screen.on")
        if last_on is None:
            return None
        on_ts = _parse_iso(last_on["timestamp"])
        last_off = self._find_last("screen.off")
        if last_off is not None:
            off_ts = _parse_iso(last_off["timestamp"])
            if off_ts > on_ts:
                return None
        now = datetime.now(timezone.utc)
        duration = (now - on_ts).total_seconds() / 60.0
        return {
            "start_time": last_on["timestamp"],
            "end_time": None,
            "duration_minutes": round(duration, 1),
            "is_active": True,
        }

    def get_last_screen_session(self) -> dict[str, Any] | None:
        """Return the most recent *completed* screen session, or None."""
        last_on = self._find_last("screen.on")
        if last_on is None:
            return None
        on_ts = _parse_iso(last_on["timestamp"])
        last_off = self._find_last("screen.off")
        if last_off is None:
            return None
        off_ts = _parse_iso(last_off["timestamp"])
        if off_ts <= on_ts:
            return None
        duration = (off_ts - on_ts).total_seconds() / 60.0
        return {
            "start_time": last_on["timestamp"],
            "end_time": last_off["timestamp"],
            "duration_minutes": round(duration, 1),
            "is_active": False,
        }

    def get_current_app_session(self, package: str) -> dict[str, Any] | None:
        """Return the *active* app session for *package*, or None."""
        last_open = self._find_last_app_event("app.opened", package)
        if last_open is None:
            return None
        open_ts = _parse_iso(last_open["timestamp"])
        last_close = self._find_last_app_event("app.closed", package)
        if last_close is not None:
            close_ts = _parse_iso(last_close["timestamp"])
            if close_ts > open_ts:
                return None
        now = datetime.now(timezone.utc)
        duration = (now - open_ts).total_seconds() / 60.0
        return {
            "start_time": last_open["timestamp"],
            "end_time": None,
            "duration_minutes": round(duration, 1),
            "is_active": True,
            "package": package,
            "label": last_open.get("payload", {}).get("label", "unknown"),
        }

    def get_last_app_session(self, package: str) -> dict[str, Any] | None:
        """Return the most recent *completed* app session for *package*."""
        last_open = self._find_last_app_event("app.opened", package)
        if last_open is None:
            return None
        open_ts = _parse_iso(last_open["timestamp"])
        last_close = self._find_last_app_event("app.closed", package)
        if last_close is None:
            return None
        close_ts = _parse_iso(last_close["timestamp"])
        if close_ts <= open_ts:
            return None
        duration = (close_ts - open_ts).total_seconds() / 60.0
        return {
            "start_time": last_open["timestamp"],
            "end_time": last_close["timestamp"],
            "duration_minutes": round(duration, 1),
            "is_active": False,
            "package": package,
            "label": last_open.get("payload", {}).get("label", "unknown"),
        }

    def _find_last(self, event_type: str) -> dict[str, Any] | None:
        found = None
        for e in self._events:
            if e.get("type") == event_type:
                found = e
        return found

    def _find_last_app_event(self, event_type: str, package: str) -> dict[str, Any] | None:
        found = None
        for e in self._events:
            if e.get("type") != event_type:
                continue
            if e.get("payload", {}).get("package", "") == package:
                found = e
        return found


def _event_ts(event: dict[str, Any]) -> str:
    return event.get("timestamp", "9999")


def _parse_iso(ts: str) -> datetime:
    ts = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
