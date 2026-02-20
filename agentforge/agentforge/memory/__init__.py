"""Memory system for AgentForge.

This package provides a comprehensive memory architecture:

1. **Working Memory** (`WorkingMemory`): In-execution scratchpad for temporary
   data during agent workflows. Fast, ephemeral, dict-based storage.

2. **Session Memory** (`SessionMemory`): Conversation-level storage with
   message history management and sliding window support.

3. **Persistent Memory** (`FileMemory`): Long-term storage that persists
   across executions using file-based backends.

4. **Long-term Memory** (`LongTermMemory`): Semantic memory backed by vector
   stores for similarity-based retrieval.

5. **Vector Stores** (`VectorStore`): Pluggable vector database backends for
   semantic search (in-memory, Qdrant, ChromaDB).

6. **Checkpoints** (`Checkpoint`, `CheckpointStore`): State snapshots for
   pause/resume functionality and workflow recovery.

Example:
    ```python
    from agentforge.memory import (
        WorkingMemory, SessionMemory, FileMemory,
        LongTermMemory, InMemoryVectorStore
    )

    # Working memory for temporary data
    working = WorkingMemory()
    await working.store("temp_result", {"value": 42})

    # Session memory for conversations
    session = SessionMemory()
    await session.add_message(Message(role=MessageRole.USER, content="Hello"))

    # Persistent memory for long-term storage
    persistent = FileMemory(FileMemoryConfig(path="data/memory.json"))
    await persistent.store("user_prefs", {"theme": "dark"})

    # Long-term memory with semantic search
    async def embed(text: str) -> list[float]:
        # Your embedding function
        ...

    store = InMemoryVectorStore(dimension=1536)
    ltm = LongTermMemory(vector_store=store, embedder=embed)
    await ltm.store("fact1", "User prefers dark mode")
    results = await ltm.search("user preferences")
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

# Long-term memory
from agentforge.memory.longterm import LongTermMemory

# Persistent memory
from agentforge.memory.persistent import (
    FileMemory,
    FileMemoryConfig,
)
from agentforge.memory.persistent import (
    InMemoryVectorStore as LegacyInMemoryVectorStore,
)

# Session memory
from agentforge.memory.session import SessionMemory, SessionMemoryConfig

# Vector store base types
from agentforge.memory.vector_base import (
    VectorEntry,
    VectorSearchResult,
    VectorStore,
)

# In-memory vector store (new implementation)
from agentforge.memory.vector_memory import InMemoryVectorStore

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
    # Vector store base
    "VectorStore",
    "VectorEntry",
    "VectorSearchResult",
    # Vector store implementations
    "InMemoryVectorStore",
    # Long-term memory
    "LongTermMemory",
    # Checkpoints
    "Checkpoint",
    "CheckpointStore",
    "InMemoryCheckpointStore",
    "SQLiteCheckpointStore",
    # Legacy (backward compatibility)
    "LegacyInMemoryVectorStore",
]
