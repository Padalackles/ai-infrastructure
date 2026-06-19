"""Trigger API — FastAPI router.

Endpoints::

    POST   /trigger              — Create a Trigger
    GET    /trigger/pending       — Oldest pending + recent activity
    POST   /trigger/{id}/ack     — Acknowledge a Trigger

Layering::

    Router  (HTTP, parameter validation, response assembly)
        │
    Service (business logic)
        │
    Repository (pure SQL)

The router never touches SQLite directly.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from activity.service import ActivityService
from activity.storage.repository import ActivityRepository
from trigger.repository import TriggerRepository
from trigger.schemas import CreateTriggerRequest, PendingResponse, TriggerResponse
from trigger.service import TriggerService

logger = logging.getLogger("mcp-hub.trigger.router")

router = APIRouter(prefix="/trigger", tags=["trigger"])

# Module-level singletons — created once at import time.
_trigger_repo = TriggerRepository()
_trigger_service = TriggerService(_trigger_repo)
_activity_repo = ActivityRepository()
_activity_service = ActivityService(_activity_repo)


# ── Create ──────────────────────────────────────────────────────────


@router.post("", response_model=TriggerResponse, status_code=200)
async def create_trigger(body: CreateTriggerRequest) -> dict[str, Any]:
    """Create a new Trigger in the queue.

    Called by the Decision Engine when a rule fires.
    """
    record = _trigger_service.create_trigger(
        type=body.type,
        payload=body.payload,
        priority=body.priority,
    )
    return record


# ── Read ────────────────────────────────────────────────────────────


@router.get("/pending", response_model=PendingResponse, status_code=200)
async def get_pending() -> dict[str, Any]:
    """Return the oldest pending Trigger and recent Activity Events.

    Always returns the same shape::

        {
            "trigger": <TriggerResponse | null>,
            "recent_activity": [...]
        }

    MacroDroid calls this single endpoint instead of making two
    separate requests (trigger + activity).
    """
    trigger = _trigger_service.get_oldest_pending()
    recent = _activity_service.get_recent(limit=50)

    return {
        "trigger": trigger,
        "recent_activity": recent,
    }


# ── Acknowledge ─────────────────────────────────────────────────────


@router.post("/{trigger_id}/ack", response_model=TriggerResponse, status_code=200)
async def ack_trigger(trigger_id: str) -> dict[str, Any]:
    """Mark a Trigger as acknowledged.

    Sets ``status='acked'`` and ``acked_at=now()``.
    Returns 404 if the trigger does not exist.
    """
    updated = _trigger_service.ack_trigger(trigger_id)
    if updated is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "not_found",
                "message": f"No trigger with id {trigger_id!r}",
            },
        )
    return updated
