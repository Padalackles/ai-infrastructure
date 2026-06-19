"""Pydantic schemas for the Trigger API.

Request and response models for the Trigger REST endpoints.
Separate from the dataclass to keep the DB model and API contract
independently evolvable.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateTriggerRequest(BaseModel):
    """Request body for POST /trigger."""

    type: str = Field(
        ...,
        description="Trigger type, e.g. procrastination, sleep, focus",
        examples=["procrastination"],
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form JSON payload set by the Decision rule",
        examples=[{"app": "bilibili", "duration": 7200}],
    )
    priority: int = Field(
        default=1,
        ge=0,
        le=2,
        description="Queue priority — 0 highest, 1 normal, 2 low",
        examples=[1],
    )


class TriggerResponse(BaseModel):
    """Response model representing a Trigger record."""

    id: str
    type: str
    payload: dict[str, Any]
    status: str
    priority: int
    created_at: str
    acked_at: str | None = None


class PendingResponse(BaseModel):
    """Response for GET /trigger/pending — always the same shape."""

    trigger: TriggerResponse | None
    recent_activity: list[dict[str, Any]]
