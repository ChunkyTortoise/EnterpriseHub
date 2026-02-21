"""Checkpoint system for AgentForge.

This module provides state checkpointing capabilities for agent workflows,
enabling pause/resume functionality and state recovery.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(UTC)


class Checkpoint(BaseModel):
    """A checkpoint of execution state.

    Represents a snapshot of an agent's execution state at a specific
    point in time, enabling state recovery and workflow resumption.

    Attributes:
        thread_id: Unique identifier for the execution thread.
        step: The step number within the thread.
        state: The serialized state dictionary.
        created_at: When the checkpoint was created.
        metadata: Optional additional information.
    """

    thread_id: str
    step: int
    state: dict[str, Any]
    created_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] | None = None


class CheckpointStore(ABC):
    """Abstract base class for checkpoint storage.

    Defines the interface for checkpoint persistence backends.
    Implementations can use different storage mechanisms (SQLite,
    file system, cloud storage, etc.).
    """

    @abstractmethod
    async def save(
        self,
        thread_id: str,
        step: int,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save a checkpoint.

        Args:
            thread_id: Unique identifier for the execution thread.
            step: The step number within the thread.
            state: The state dictionary to save.
            metadata: Optional additional information.
        """
        ...

    @abstractmethod
    async def load(self, thread_id: str, step: int | None = None) -> Checkpoint | None:
        """Load a checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number. If None, loads the latest checkpoint.

        Returns:
            The checkpoint, or None if not found.
        """
        ...

    @abstractmethod
    async def list_checkpoints(self, thread_id: str) -> list[Checkpoint]:
        """List all checkpoints for a thread.

        Args:
            thread_id: The execution thread identifier.

        Returns:
            List of checkpoints, sorted by step (ascending).
        """
        ...

    @abstractmethod
    async def delete(self, thread_id: str, step: int) -> bool:
        """Delete a specific checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...

    async def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: The execution thread identifier.

        Returns:
            Number of checkpoints deleted.
        """
        checkpoints = await self.list_checkpoints(thread_id)
        count = 0
        for cp in checkpoints:
            if await self.delete(thread_id, cp.step):
                count += 1
        return count

    async def get_latest_step(self, thread_id: str) -> int | None:
        """Get the latest step number for a thread.

        Args:
            thread_id: The execution thread identifier.

        Returns:
            The latest step number, or None if no checkpoints exist.
        """
        checkpoint = await self.load(thread_id)
        return checkpoint.step if checkpoint else None


class SQLiteCheckpointStore(CheckpointStore):
    """SQLite-based checkpoint storage.

    Provides persistent checkpoint storage using SQLite. Suitable for
    local development and single-server deployments.

    Features:
    - ACID compliance
    - Efficient querying by thread_id and step
    - Automatic database initialization

    Example:
        ```python
        store = SQLiteCheckpointStore("checkpoints.db")

        # Save checkpoint
        await store.save(
            thread_id="thread-123",
            step=5,
            state={"counter": 10, "data": [1, 2, 3]}
        )

        # Load latest
        checkpoint = await store.load("thread-123")

        # Load specific step
        checkpoint = await store.load("thread-123", step=3)
        ```
    """

    def __init__(self, db_path: str = "checkpoints.db") -> None:
        """Initialize SQLite checkpoint store.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database schema."""
        # Create parent directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                thread_id TEXT NOT NULL,
                step INTEGER NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT,
                PRIMARY KEY (thread_id, step)
            )
        """)

        # Create index for efficient latest lookup
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_thread_created
            ON checkpoints(thread_id, created_at DESC)
        """)

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def save(
        self,
        thread_id: str,
        step: int,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save a checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number.
            state: The state dictionary.
            metadata: Optional metadata.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints
                (thread_id, step, state, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    step,
                    json.dumps(state, default=str),
                    _utc_now().isoformat(),
                    json.dumps(metadata, default=str) if metadata else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    async def load(self, thread_id: str, step: int | None = None) -> Checkpoint | None:
        """Load a checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number. If None, loads the latest.

        Returns:
            The checkpoint, or None if not found.
        """
        conn = self._get_connection()
        try:
            if step is not None:
                cursor = conn.execute(
                    """
                    SELECT * FROM checkpoints
                    WHERE thread_id = ? AND step = ?
                    """,
                    (thread_id, step),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY step DESC
                    LIMIT 1
                    """,
                    (thread_id,),
                )

            row = cursor.fetchone()
            if row is None:
                return None

            return Checkpoint(
                thread_id=row["thread_id"],
                step=row["step"],
                state=json.loads(row["state"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            )
        finally:
            conn.close()

    async def list_checkpoints(self, thread_id: str) -> list[Checkpoint]:
        """List all checkpoints for a thread.

        Args:
            thread_id: The execution thread identifier.

        Returns:
            List of checkpoints sorted by step.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE thread_id = ?
                ORDER BY step ASC
                """,
                (thread_id,),
            )

            checkpoints = []
            for row in cursor.fetchall():
                checkpoints.append(
                    Checkpoint(
                        thread_id=row["thread_id"],
                        step=row["step"],
                        state=json.loads(row["state"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    )
                )

            return checkpoints
        finally:
            conn.close()

    async def delete(self, thread_id: str, step: int) -> bool:
        """Delete a specific checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number.

        Returns:
            True if deleted, False if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM checkpoints
                WHERE thread_id = ? AND step = ?
                """,
                (thread_id, step),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    async def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: The execution thread identifier.

        Returns:
            Number of checkpoints deleted.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM checkpoints
                WHERE thread_id = ?
                """,
                (thread_id,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    async def list_threads(self) -> list[str]:
        """List all thread IDs.

        Returns:
            List of unique thread IDs.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT DISTINCT thread_id FROM checkpoints
                ORDER BY thread_id
                """
            )
            return [row["thread_id"] for row in cursor.fetchall()]
        finally:
            conn.close()

    async def get_checkpoint_count(self, thread_id: str | None = None) -> int:
        """Get the count of checkpoints.

        Args:
            thread_id: Optional thread to count. If None, counts all.

        Returns:
            Number of checkpoints.
        """
        conn = self._get_connection()
        try:
            if thread_id:
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM checkpoints WHERE thread_id = ?",
                    (thread_id,),
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) as count FROM checkpoints")

            row = cursor.fetchone()
            return row["count"] if row else 0
        finally:
            conn.close()


class InMemoryCheckpointStore(CheckpointStore):
    """In-memory checkpoint storage for testing.

    Stores checkpoints in memory without persistence. Useful for
    testing and short-lived workflows.
    """

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._checkpoints: dict[str, dict[int, Checkpoint]] = {}

    async def save(
        self,
        thread_id: str,
        step: int,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save a checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number.
            state: The state dictionary.
            metadata: Optional metadata.
        """
        if thread_id not in self._checkpoints:
            self._checkpoints[thread_id] = {}

        self._checkpoints[thread_id][step] = Checkpoint(
            thread_id=thread_id,
            step=step,
            state=state,
            metadata=metadata,
        )

    async def load(self, thread_id: str, step: int | None = None) -> Checkpoint | None:
        """Load a checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number. If None, loads the latest.

        Returns:
            The checkpoint, or None if not found.
        """
        if thread_id not in self._checkpoints:
            return None

        thread_checkpoints = self._checkpoints[thread_id]

        if step is not None:
            return thread_checkpoints.get(step)

        if not thread_checkpoints:
            return None

        # Return the checkpoint with the highest step
        latest_step = max(thread_checkpoints.keys())
        return thread_checkpoints[latest_step]

    async def list_checkpoints(self, thread_id: str) -> list[Checkpoint]:
        """List all checkpoints for a thread.

        Args:
            thread_id: The execution thread identifier.

        Returns:
            List of checkpoints sorted by step.
        """
        if thread_id not in self._checkpoints:
            return []

        return sorted(
            self._checkpoints[thread_id].values(),
            key=lambda cp: cp.step,
        )

    async def delete(self, thread_id: str, step: int) -> bool:
        """Delete a specific checkpoint.

        Args:
            thread_id: The execution thread identifier.
            step: The step number.

        Returns:
            True if deleted, False if not found.
        """
        if thread_id not in self._checkpoints:
            return False

        if step not in self._checkpoints[thread_id]:
            return False

        del self._checkpoints[thread_id][step]

        # Clean up empty thread
        if not self._checkpoints[thread_id]:
            del self._checkpoints[thread_id]

        return True

    async def delete_thread(self, thread_id: str) -> int:
        """Delete all checkpoints for a thread.

        Args:
            thread_id: The execution thread identifier.

        Returns:
            Number of checkpoints deleted.
        """
        if thread_id not in self._checkpoints:
            return 0

        count = len(self._checkpoints[thread_id])
        del self._checkpoints[thread_id]
        return count

    def clear(self) -> None:
        """Clear all checkpoints."""
        self._checkpoints.clear()


__all__ = [
    "Checkpoint",
    "CheckpointStore",
    "SQLiteCheckpointStore",
    "InMemoryCheckpointStore",
]
