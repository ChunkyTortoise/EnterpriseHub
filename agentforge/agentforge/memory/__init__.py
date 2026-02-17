"""Memory system for AgentForge.

This package provides a four-tier memory architecture:

1. **Working Memory** (`WorkingMemory`): In-execution scratchpad for temporary
   data during agent workflows. Fast, ephemeral, dict-based storage.

2. **Session Memory** (`SessionMemory`): Conversation-level storage with
   message history management and sliding window support.

3. **Persistent Memory** (`FileMemory`, `InMemoryVectorStore`): Long-term
   storage that persists across executions using file or database backends.

4. **Checkpoints** (`Checkpoint`, `CheckpointStore`): State snapshots for
   pause/resume functionality and workflow recovery.

Example:
    ```python
    from agentforge.memory import WorkingMemory, SessionMemory, FileMemory

    # Working memory for temporary data
    working = WorkingMemory()
    await working.store("temp_result", {"value": 42})

    # Session memory for conversations
    session = SessionMemory()
    await session.add_message(Message(role=MessageRole.USER, content="Hello"))

    # Persistent memory for long-term storage
    persistent = FileMemory(FileMemoryConfig(path="data/memory.json"))
    await persistent.store("user_prefs", {"theme": "dark"})
    ```
"""

# Base types
from agentforge.memory.base import MemoryEntry, MemoryProvider, SearchResult

# Checkpoints
from agentforge.memory.checkpoint import (
    Checkpoint,
    CheckpointStore,
    InMemoryCheckpointStore,
    SQLiteCheckpointStore,
)

# Persistent memory
from agentforge.memory.persistent import (
    FileMemory,
    FileMemoryConfig,
    InMemoryVectorStore,
)

# Session memory
from agentforge.memory.session import SessionMemory, SessionMemoryConfig

# Working memory
from agentforge.memory.working import WorkingMemory

__all__ = [
    # Base
    "MemoryEntry",
    "MemoryProvider",
    "SearchResult",
    # Working memory
    "WorkingMemory",
    # Session memory
    "SessionMemory",
    "SessionMemoryConfig",
    # Persistent memory
    "FileMemory",
    "FileMemoryConfig",
    "InMemoryVectorStore",
    # Checkpoints
    "Checkpoint",
    "CheckpointStore",
    "InMemoryCheckpointStore",
    "SQLiteCheckpointStore",
]
