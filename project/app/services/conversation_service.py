"""Conversation service — manages AI conversation lifecycle."""

from typing import Any


class ConversationService:
    """Service for creating, listing, and managing conversations."""

    async def create(self, title: str = "") -> dict[str, Any]:
        """Create a new conversation."""
        pass

    async def get(self, conversation_id: str) -> dict[str, Any] | None:
        """Retrieve a conversation by ID."""
        pass

    async def list(self) -> list[dict[str, Any]]:
        """List all conversations."""
        pass

    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        pass

    async def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Append a message to a conversation."""
        pass
