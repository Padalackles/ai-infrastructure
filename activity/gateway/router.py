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

from .models import ActivityEventRequest, ActivityEventResponse
from .service import build_event

logger = logging.getLogger("mcp-hub.activity.gateway")

router = APIRouter(prefix="/activity", tags=["activity"])

# Repository is created once at import time.  The database is
# initialized by main.py's lifespan before any requests arrive.
_repo = ActivityRepository()


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
