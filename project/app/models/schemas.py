"""Pydantic models — minimal field set, extensible for future tasks.

These models represent the core domain objects of Ombre Brain:
  - Conversation — tracks an AI conversation thread.
  - Memory — a persistent, keyed memory entry.
  - Task — a scheduled or tracked task.
  - UserConfig — per-user configuration preferences.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Conversation(BaseModel):
    """A conversation with an AI agent."""

    id: str = Field(default="")
    title: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: list[dict[str, Any]] = Field(default_factory=list)


class Memory(BaseModel):
    """A persistent memory entry stored by Ombre Brain."""

    id: str = Field(default="")
    key: str = Field(default="")
    value: Any = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Task(BaseModel):
    """A scheduled or tracked task."""

    id: str = Field(default="")
    title: str = Field(default="")
    description: str = Field(default="")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    due_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserConfig(BaseModel):
    """Per-user configuration and preferences."""

    user_id: str = Field(default="default")
    name: str = Field(default="")
    preferences: dict[str, Any] = Field(default_factory=dict)
