"""Task service — manages task lifecycle."""

from typing import Any


class TaskService:
    """Service for creating, updating, listing, and deleting tasks."""

    async def create(self, title: str, description: str = "", due_at: str | None = None) -> str:
        """Create a new task. Returns the task ID."""
        pass

    async def get(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve a task by ID."""
        pass

    async def update(self, task_id: str, **fields: Any) -> bool:
        """Update fields on an existing task."""
        pass

    async def list(self, status: str | None = None) -> list[dict[str, Any]]:
        """List tasks, optionally filtered by status."""
        pass

    async def delete(self, task_id: str) -> bool:
        """Delete a task by ID."""
        pass
