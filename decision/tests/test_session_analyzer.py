"""Unit tests for SessionAnalyzer."""

from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from decision.analyzers.session import SessionAnalyzer


# ── Helpers ─────────────────────────────────────────────────────────


def _now_iso() -> str:
    """Return current UTC time as ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
           f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def _iso_offset(minutes_ago: float) -> str:
    """Return ISO 8601 timestamp *minutes_ago* in the past."""
    dt = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _make_event(event_type: str, timestamp: str, **payload) -> dict:
    """Build a minimal Activity Event for analyzer tests."""
    return {
        "version": 1,
        "id": f"evt_test_{event_type.replace('.', '_')}",
        "timestamp": timestamp,
        "source": "android",
        "collector": "macrodroid",
        "device": "pixel-8-pro",
        "type": event_type,
        "payload": dict(payload),
        "raw": {},
    }


# ── Screen sessions ────────────────────────────────────────────────


def test_current_screen_session_active():
    """When screen.on exists without matching screen.off, session is active."""
    events = [
        _make_event("screen.on", _iso_offset(45)),
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_screen_session()
    assert session is not None
    assert session["is_active"] is True
    assert session["end_time"] is None
    assert session["duration_minutes"] >= 44  # ~45 minutes ago


def test_current_screen_session_none_when_off():
    """When screen.off is after screen.on, no current session."""
    events = [
        _make_event("screen.on", _iso_offset(60)),
        _make_event("screen.off", _iso_offset(30)),
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_screen_session()
    assert session is None


def test_current_screen_session_no_events():
    """Empty events → no session."""
    analyzer = SessionAnalyzer([])
    assert analyzer.get_current_screen_session() is None


def test_current_screen_session_uses_most_recent_on():
    """Only the most recent screen.on matters."""
    events = [
        _make_event("screen.on", _iso_offset(120)),
        _make_event("screen.off", _iso_offset(90)),
        _make_event("screen.on", _iso_offset(20)),  # most recent on, no off after
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_screen_session()
    assert session is not None
    assert session["duration_minutes"] >= 19


def test_last_screen_session_completed():
    """A completed screen session is returned by get_last_screen_session."""
    events = [
        _make_event("screen.on", _iso_offset(60)),
        _make_event("screen.off", _iso_offset(30)),
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_last_screen_session()
    assert session is not None
    assert session["is_active"] is False
    assert session["end_time"] is not None
    # Duration should be ~30 min (60 - 30)


def test_last_screen_session_none_when_active():
    """If screen is still on, get_last_screen_session returns None."""
    events = [
        _make_event("screen.on", _iso_offset(45)),
    ]
    analyzer = SessionAnalyzer(events)
    assert analyzer.get_last_screen_session() is None


def test_last_screen_session_none_no_events():
    """No events → no last session."""
    analyzer = SessionAnalyzer([])
    assert analyzer.get_last_screen_session() is None


# ── App sessions ────────────────────────────────────────────────────


def test_current_app_session_active():
    """When app.opened exists without matching app.closed, session is active."""
    events = [
        _make_event("app.opened", _iso_offset(25),
                     package="com.example.app", label="TestApp"),
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_app_session("com.example.app")
    assert session is not None
    assert session["is_active"] is True
    assert session["package"] == "com.example.app"
    assert session["label"] == "TestApp"
    assert session["duration_minutes"] >= 24


def test_current_app_session_none_when_closed():
    """When app.closed exists after app.opened, no current session."""
    events = [
        _make_event("app.opened", _iso_offset(60),
                     package="com.example.app"),
        _make_event("app.closed", _iso_offset(10),
                     package="com.example.app"),
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_app_session("com.example.app")
    assert session is None


def test_current_app_session_different_package():
    """Only events for the requested package are considered."""
    events = [
        _make_event("app.opened", _iso_offset(10),
                     package="com.other.app"),
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_current_app_session("com.example.app")
    assert session is None


def test_current_app_session_no_events():
    """Empty events → no app session."""
    analyzer = SessionAnalyzer([])
    assert analyzer.get_current_app_session("com.example.app") is None


def test_last_app_session_completed():
    """A completed app session is returned."""
    events = [
        _make_event("app.opened", _iso_offset(60),
                     package="com.example.app", label="TestApp"),
        _make_event("app.closed", _iso_offset(30),
                     package="com.example.app"),
    ]
    analyzer = SessionAnalyzer(events)
    session = analyzer.get_last_app_session("com.example.app")
    assert session is not None
    assert session["is_active"] is False
    assert session["end_time"] is not None
    assert session["package"] == "com.example.app"


def test_last_app_session_none_when_active():
    """If app is still open, get_last_app_session returns None."""
    events = [
        _make_event("app.opened", _iso_offset(25),
                     package="com.example.app"),
    ]
    analyzer = SessionAnalyzer(events)
    assert analyzer.get_last_app_session("com.example.app") is None


def test_last_app_session_none_no_events():
    """No events → no last app session."""
    analyzer = SessionAnalyzer([])
    assert analyzer.get_last_app_session("com.example.app") is None


# ── Multiple apps ───────────────────────────────────────────────────


def test_multiple_apps_independent():
    """Sessions for different packages are tracked independently."""
    events = [
        _make_event("app.opened", _iso_offset(60),
                     package="com.app.a"),
        _make_event("app.closed", _iso_offset(50),
                     package="com.app.a"),
        _make_event("app.opened", _iso_offset(15),
                     package="com.app.b"),  # still open
    ]
    analyzer = SessionAnalyzer(events)

    # App A is closed
    assert analyzer.get_current_app_session("com.app.a") is None
    last_a = analyzer.get_last_app_session("com.app.a")
    assert last_a is not None

    # App B is open
    curr_b = analyzer.get_current_app_session("com.app.b")
    assert curr_b is not None
    assert curr_b["is_active"] is True


# ── Event ordering ──────────────────────────────────────────────────


def test_events_sorted_internally():
    """Events are sorted by timestamp regardless of input order."""
    t1 = _iso_offset(60)
    t2 = _iso_offset(30)
    t3 = _iso_offset(10)
    events = [
        _make_event("screen.on", t3),  # newest first in input
        _make_event("screen.on", t1),  # oldest
        _make_event("screen.on", t2),  # middle
    ]
    analyzer = SessionAnalyzer(events)
    # Should use the most recent (t3) regardless of input order
    session = analyzer.get_current_screen_session()
    assert session is not None
    assert session["start_time"] == t3
