"""Session memory implementation for AgentForge.

Session memory provides conversation-level storage with message history
management, including sliding window support for context length control.
"""

from typing import Any

from pydantic import BaseModel

from agentforge.core.types import Message
from agentforge.memory.base import MemoryEntry, MemoryProvider


class SessionMemoryConfig(BaseModel):
    """Configuration for session memory.

    Attributes:
        max_messages: Maximum number of messages to retain.
        sliding_window: Whether to automatically trim old messages.
        session_id: Optional identifier for this session.
    """
    max_messages: int = 100
    sliding_window: bool = True
    session_id: str | None = None


class SessionMemory(MemoryProvider):
    """Session/conversation memory with sliding window.

    Session memory is designed for storing conversation history and
    session-level metadata. It provides:

    - Message history management with optional sliding window
    - Metadata storage separate from messages
    - Format conversion for different LLM providers

    The sliding window automatically trims old messages when the
    maximum is reached, keeping only the most recent messages.

    Example:
        ```python
        config = SessionMemoryConfig(max_messages=50, sliding_window=True)
        memory = SessionMemory(config)

        # Add messages
        await memory.add_message(Message(role=MessageRole.USER, content="Hello"))
        await memory.add_message(Message(role=MessageRole.ASSISTANT, content="Hi!"))

        # Get messages for LLM
        messages = await memory.get_messages()
        openai_format = memory.to_openai_messages()
        ```
    """

    def __init__(self, config: SessionMemoryConfig | None = None) -> None:
        """Initialize session memory.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or SessionMemoryConfig()
        self._messages: list[Message] = []
        self._metadata: dict[str, MemoryEntry] = {}

    async def add_message(self, message: Message) -> None:
        """Add a message to the conversation.

        If sliding window is enabled and max_messages is exceeded,
        older messages are automatically removed.

        Args:
            message: The message to add.
        """
        self._messages.append(message)
        if self.config.sliding_window and len(self._messages) > self.config.max_messages:
            self._messages = self._messages[-self.config.max_messages:]

    async def add_messages(self, messages: list[Message]) -> None:
        """Add multiple messages to the conversation.

        Args:
            messages: List of messages to add.
        """
        for message in messages:
            await self.add_message(message)

    async def get_messages(self, limit: int | None = None) -> list[Message]:
        """Get messages from the conversation.

        Args:
            limit: Maximum number of recent messages to return.
                   If None, returns all messages.

        Returns:
            List of messages (most recent last).
        """
        if limit:
            return self._messages[-limit:]
        return self._messages.copy()

    async def get_last_message(self) -> Message | None:
        """Get the most recent message.

        Returns:
            The last message, or None if no messages exist.
        """
        return self._messages[-1] if self._messages else None

    async def get_first_message(self) -> Message | None:
        """Get the first message.

        Returns:
            The first message, or None if no messages exist.
        """
        return self._messages[0] if self._messages else None

    async def clear_messages(self) -> None:
        """Clear all messages from the conversation."""
        self._messages.clear()

    async def message_count(self) -> int:
        """Get the number of messages in the conversation.

        Returns:
            The message count.
        """
        return len(self._messages)

    # MemoryProvider implementation for metadata storage

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Store metadata (not messages).

        Use add_message() for conversation messages. This method
        stores session-level metadata like user preferences, context, etc.

        Args:
            key: Unique identifier for the metadata.
            value: The value to store.
            metadata: Optional additional information.
        """
        self._metadata[key] = MemoryEntry(key=key, value=value, metadata=metadata)

    async def retrieve(self, key: str) -> Any | None:
        """Retrieve metadata by key.

        Args:
            key: The unique identifier.

        Returns:
            The stored value, or None if not found.
        """
        entry = self._metadata.get(key)
        return entry.value if entry else None

    async def delete(self, key: str) -> bool:
        """Delete metadata by key.

        Args:
            key: The unique identifier to delete.

        Returns:
            True if deleted, False if not found.
        """
        if key in self._metadata:
            del self._metadata[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a metadata key exists.

        Args:
            key: The unique identifier to check.

        Returns:
            True if the key exists.
        """
        return key in self._metadata

    async def clear(self) -> None:
        """Clear all messages and metadata."""
        self._messages.clear()
        self._metadata.clear()

    async def keys(self) -> list[str]:
        """List all metadata keys.

        Returns:
            List of all metadata keys.
        """
        return list(self._metadata.keys())

    # Format conversion methods

    def to_openai_messages(self) -> list[dict]:
        """Convert to OpenAI message format.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self._messages
        ]

    def to_anthropic_messages(self) -> list[dict]:
        """Convert to Anthropic message format.

        Currently identical to OpenAI format as both use the same
        role/content structure.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        return self.to_openai_messages()

    def to_dict_list(self) -> list[dict]:
        """Convert messages to list of dictionaries.

        Includes all message fields (role, content, name, metadata, etc.).

        Returns:
            List of message dictionaries.
        """
        return [msg.model_dump() for msg in self._messages]

    @classmethod
    def from_messages(
        cls,
        messages: list[Message],
        config: SessionMemoryConfig | None = None,
    ) -> "SessionMemory":
        """Create a SessionMemory from existing messages.

        Args:
            messages: Initial messages to populate.
            config: Optional configuration.

        Returns:
            A new SessionMemory instance.
        """
        memory = cls(config)
        memory._messages = messages.copy()
        return memory

    def snapshot(self) -> dict[str, Any]:
        """Create a snapshot for checkpointing.

        Returns:
            Dictionary with messages and metadata.
        """
        return {
            "config": self.config.model_dump(),
            "messages": [msg.model_dump() for msg in self._messages],
            "metadata": {k: v.model_dump() for k, v in self._metadata.items()},
        }

    @classmethod
    def restore(cls, snapshot: dict[str, Any]) -> "SessionMemory":
        """Restore from a snapshot.

        Args:
            snapshot: Dictionary from a previous snapshot() call.

        Returns:
            A new SessionMemory instance with restored state.
        """
        config = SessionMemoryConfig(**snapshot.get("config", {}))
        memory = cls(config)
        memory._messages = [Message(**msg) for msg in snapshot.get("messages", [])]
        memory._metadata = {
            k: MemoryEntry(**v) for k, v in snapshot.get("metadata", {}).items()
        }
        return memory

    def __len__(self) -> int:
        """Return the number of messages."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation of session memory."""
        return (
            f"SessionMemory(session_id={self.config.session_id}, "
            f"messages={len(self._messages)}, metadata_keys={len(self._metadata)})"
        )


__all__ = ["SessionMemory", "SessionMemoryConfig"]
