"""Trigger Queue — persistence and API for pending triggers.

The Trigger Queue sits between the Decision Engine and MacroDroid::

    Activity → Decision → Trigger Queue → API → MacroDroid → Claude

Triggers are stored in the shared ``data/activity.db`` SQLite database
alongside Activity Events.

Design:
    * ``models.py``      — ``Trigger`` dataclass (plain Python, no ORM).
    * ``schemas.py``     — Pydantic models for the REST API.
    * ``repository.py``  — ``TriggerRepository`` (pure SQL CRUD).
    * ``service.py``     — ``TriggerService`` (business logic layer).
    * ``router.py``      — FastAPI router (HTTP → Service → Repository).
"""

from trigger.models import Trigger
from trigger.repository import TriggerRepository
from trigger.service import TriggerService
from trigger.router import router

__all__ = [
    "Trigger",
    "TriggerRepository",
    "TriggerService",
    "router",
]
