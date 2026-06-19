"""Activity Gateway — FastAPI router.

Single endpoint::

    POST /activity/events

Pipeline::

    HTTP POST
        │
        ▼
    Gateway (validate, build)
        │
        ▼
    Normalizer (canonical type mapping, payload normalization)
        │
        ▼
    Repository (save to SQLite)
        │
        ▼
    Console (log)
        │
        ▼
    Response (accepted)

Receives raw device events, validates them, auto-populates server-side
fields, normalizes to canonical form, persists to SQLite, and returns
a success response.

Source-agnostic — no collector-specific logic.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from activity.normalizer.service import normalize_event
from activity.storage.repository import ActivityRepository
from activity.service import ActivityService

from .models import ActivityEventRequest, ActivityEventResponse
from .service import build_event

logger = logging.getLogger("mcp-hub.activity.gateway")

router = APIRouter(prefix="/activity", tags=["activity"])

# Repository + Service — created once at import time.
_repo = ActivityRepository()
_service = ActivityService(_repo)


@router.post("/events", response_model=ActivityEventResponse, status_code=200)
async def ingest_event(request: Request, body: ActivityEventRequest) -> dict[str, Any]:
    """Ingest an Activity Event from an external collector.

    Validates required fields, fills in server-side defaults, normalizes
    to canonical form, persists to SQLite, logs, and returns the assigned
    ID + timestamp.
    """
    # ── Build the complete event ──────────────────────────────────
    event = build_event(body)

    # ── Normalize to canonical form ───────────────────────────────
    normalized = normalize_event(event)

    # ── Persist to SQLite ────────────────────────────────────────
    try:
        _repo.save_event(normalized)
    except Exception:
        logger.exception("Failed to persist event id=%s", normalized.get("id", "?"))
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to persist event",
                "id": normalized["id"],
            },
        )

    # ── Log the event (temporary — for development visibility) ─────
    _log_event(normalized)

    # ── Return acceptance ─────────────────────────────────────────
    return {
        "status": "accepted",
        "id": normalized["id"],
        "timestamp": normalized["timestamp"],
        "version": normalized["version"],
    }


# ── Query endpoints ─────────────────────────────────────────────


@router.get("/recent", status_code=200)
async def get_recent(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent events, newest first.

    Query params:
        limit (int): max events to return, clamped to [1, 1000].  Default 50.
    """
    return _service.get_recent(limit=limit)


@router.get("/latest", status_code=200)
async def get_latest(type: str) -> dict[str, Any]:
    """Return the most recent event of a given canonical type.

    Query params:
        type (str): canonical event type, e.g. ``device.awake``.

    Returns 404 if no event of that type exists.
    """
    event = _service.get_latest(type)
    if event is None:
        return JSONResponse(
            status_code=404,
            content={"status": "not_found", "message": f"No events of type {type!r}"},
        )
    return event


@router.get("/history", status_code=200)
async def get_history(
    start: str, end: str, limit: int = 100
) -> list[dict[str, Any]]:
    """Return events within a timestamp range, newest first.

    Query params:
        start (str): ISO 8601 start timestamp (inclusive).
        end   (str): ISO 8601 end timestamp (inclusive).
        limit (int): max events to return, clamped to [1, 1000].  Default 100.
    """
    return _service.get_between(start=start, end=end, limit=limit)


@router.get("/types", status_code=200)
async def get_types() -> list[str]:
    """Return all distinct canonical event types currently stored."""
    return _service.list_types()


# ── Logging ──────────────────────────────────────────────────────

def _log_event(event: dict[str, Any]) -> None:
    """Print a human-readable event summary for development."""
    logger.info("[Activity Gateway]")
    logger.info("")
    logger.info("Received Event")
    logger.info("")
    logger.info("ID:         %s", event["id"])
    logger.info("Type:       %s", event["type"])
    logger.info("Source:     %s", event["source"])
    logger.info("Collector:  %s", event["collector"])
    logger.info("Device:     %s", event["device"])
    logger.info("Timestamp:  %s", event["timestamp"])
    logger.info("Version:    %s", event["version"])
    logger.info("Payload:    %s", event["payload"])
    if event.get("raw"):
        logger.info("Raw:        %s", event["raw"])
    logger.info("")
