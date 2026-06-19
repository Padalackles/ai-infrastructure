"""Activity Gateway — FastAPI router.

Single endpoint::

    POST /activity/events

Receives raw device events, validates them, auto-populates server-side
fields, logs them, and returns a success response.

Source-agnostic — no collector-specific logic.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .models import ActivityEventRequest, ActivityEventResponse
from .service import build_event

logger = logging.getLogger("mcp-hub.activity.gateway")

router = APIRouter(prefix="/activity", tags=["activity"])


@router.post("/events", response_model=ActivityEventResponse, status_code=200)
async def ingest_event(request: Request, body: ActivityEventRequest) -> dict[str, Any]:
    """Ingest an Activity Event from an external collector.

    Validates required fields, fills in server-side defaults, logs
    the event to the console, and returns the assigned ID + timestamp.
    """
    # ── Build the complete event ──────────────────────────────────
    event = build_event(body)

    # ── Log the event (temporary — for development visibility) ─────
    _log_event(event)

    # ── Return acceptance ─────────────────────────────────────────
    return {
        "status": "accepted",
        "id": event["id"],
        "timestamp": event["timestamp"],
        "version": event["version"],
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
