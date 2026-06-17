"""Pydantic models — minimal field set, extensible for future tasks."""

from datetime import datetime
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: list[dict[str, Any]] = Field(default_factory=list)


class Memory(BaseModel):
    """A persistent memory entry."""

    id: str = Field(default="")
    key: str = Field(default="")
    value: Any = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    """A scheduled or tracked task."""

    id: str = Field(default="")
    title: str = Field(default="")
    description: str = Field(default="")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserConfig(BaseModel):
    """User-level configuration."""

    name: str = Field(default="")
    preferences: dict[str, Any] = Field(default_factory=dict)
