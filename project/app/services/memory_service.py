"""Memory service — manages persistent AI memory storage and retrieval."""

from typing import Any


class MemoryService:
    """Service for storing, retrieving, searching, and deleting memories."""

    async def store(self, key: str, value: Any, tags: list[str] | None = None) -> str:
        """Store a new memory entry. Returns the memory ID."""
        pass

    async def retrieve(self, memory_id: str) -> dict[str, Any] | None:
        """Retrieve a memory by ID."""
        pass

    async def search(self, query: str, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Search memories by query text and optional tags."""
        pass

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        pass

    async def list_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """List all memories with a given tag."""
        pass
