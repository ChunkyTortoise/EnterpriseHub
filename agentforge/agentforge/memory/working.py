"""Working memory implementation for AgentForge.

Working memory provides an in-execution scratchpad for temporary data
storage during agent workflows. It's designed for fast, ephemeral storage
that doesn't persist between executions.
"""

from typing import Any

from agentforge.memory.base import MemoryEntry, MemoryProvider


class WorkingMemory(MemoryProvider):
    """In-execution scratchpad (dict-based, per-execution).

    Working memory is the fastest and simplest memory tier, using an
    in-memory dictionary for storage. It's ideal for:

    - Temporary variables during agent execution
    - Intermediate computation results
    - Context that doesn't need to persist

    Data is lost when the WorkingMemory instance is destroyed.
    For persistence across executions, use SessionMemory or FileMemory.

    Example:
        ```python
        memory = WorkingMemory()
        await memory.store("current_step", 1)
        await memory.store("intermediate_result", {"data": [1, 2, 3]})

        step = await memory.retrieve("current_step")  # 1
        all_data = await memory.get_all()  # {"current_step": 1, ...}
        ```
    """

    def __init__(self) -> None:
        """Initialize an empty working memory."""
        self._data: dict[str, MemoryEntry] = {}

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Store a value in working memory.

        Args:
            key: Unique identifier for the value.
            value: The value to store.
            metadata: Optional additional information.
        """
        self._data[key] = MemoryEntry(key=key, value=value, metadata=metadata)

    async def retrieve(self, key: str) -> Any | None:
        """Retrieve a value by key.

        Args:
            key: The unique identifier for the value.

        Returns:
            The stored value, or None if not found.
        """
        entry = self._data.get(key)
        return entry.value if entry else None

    async def delete(self, key: str) -> bool:
        """Delete a value by key.

        Args:
            key: The unique identifier to delete.

        Returns:
            True if deleted, False if key didn't exist.
        """
        if key in self._data:
            del self._data[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: The unique identifier to check.

        Returns:
            True if the key exists.
        """
        return key in self._data

    async def clear(self) -> None:
        """Clear all stored data."""
        self._data.clear()

    async def keys(self) -> list[str]:
        """List all stored keys.

        Returns:
            List of all keys in working memory.
        """
        return list(self._data.keys())

    async def get_all(self) -> dict[str, Any]:
        """Get all key-value pairs.

        Returns:
            Dictionary of all stored key-value pairs.
        """
        return {k: v.value for k, v in self._data.items()}

    async def get_entry(self, key: str) -> MemoryEntry | None:
        """Get the full memory entry including metadata.

        Args:
            key: The unique identifier.

        Returns:
            The full MemoryEntry, or None if not found.
        """
        return self._data.get(key)

    def snapshot(self) -> dict[str, Any]:
        """Create a snapshot for checkpointing.

        Creates a serializable representation of all stored data
        that can be used to restore state later.

        Returns:
            Dictionary representation of all entries.
        """
        return {k: v.model_dump() for k, v in self._data.items()}

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore from a snapshot.

        Replaces all current data with the snapshot data.

        Args:
            snapshot: Dictionary from a previous snapshot() call.
        """
        self._data = {k: MemoryEntry(**v) for k, v in snapshot.items()}

    def __len__(self) -> int:
        """Return the number of stored entries."""
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        """Check if a key exists (supports 'in' operator)."""
        return key in self._data

    def __repr__(self) -> str:
        """String representation of working memory."""
        return f"WorkingMemory(entries={len(self._data)})"


__all__ = ["WorkingMemory"]
