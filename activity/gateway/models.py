"""Pydantic models for the Activity Gateway.

Defines the request/response shapes for POST /activity/events.
Validation is intentionally minimal — the Normalizer handles
schema conformance downstream.  The Gateway only checks that
required fields are present and have the correct types.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActivityEventRequest(BaseModel):
    """Incoming event from a collector (MacroDroid, Tasker, etc.).

    Only five fields are required.  The Gateway auto-populates
    version, id, timestamp, and raw if the client omits them.
    """

    source: str = Field(
        ...,
        description="Originating platform: android, ios, desktop, web, iot, service",
        min_length=1,
    )
    collector: str = Field(
        ...,
        description="Software that captured the event: macrodroid, tasker, shortcuts, etc.",
        min_length=1,
    )
    device: str = Field(
        ...,
        description="Human-readable device identifier: pixel-8-pro, iphone-15, etc.",
        min_length=1,
    )
    type: str = Field(
        ...,
        description="Hierarchical event type: device.awake, battery.low, app.opened, etc.",
        min_length=1,
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized event data.  Schema varies by type.",
    )
    version: int | None = Field(
        default=None,
        description="Schema version.  Gateway fills with 1 if omitted.",
    )
    id: str | None = Field(
        default=None,
        description="Event ID.  Gateway generates evt_<ULID> if omitted.",
    )
    timestamp: str | None = Field(
        default=None,
        description="ISO 8601 timestamp.  Gateway fills with server time if omitted.",
    )
    raw: dict[str, Any] | None = Field(
        default=None,
        description="Original collector event.  Gateway defaults to {} if omitted.",
    )


class ActivityEventResponse(BaseModel):
    """Returned to the collector after successful ingest."""

    status: str = Field(default="accepted", description="Always 'accepted'.")
    id: str = Field(..., description="Server-generated event ID.")
    timestamp: str = Field(..., description="Assigned ISO 8601 timestamp.")
    version: int = Field(default=1, description="Schema version used.")
