"""Tests for AgentForge memory system.

This module contains comprehensive tests for all memory providers:
- WorkingMemory
- SessionMemory
- FileMemory
- SQLiteCheckpointStore
- InMemoryCheckpointStore
"""

import os
import tempfile

import pytest

from agentforge.core.types import Message, MessageRole
from agentforge.memory import (
    Checkpoint,
    FileMemory,
    FileMemoryConfig,
    InMemoryCheckpointStore,
    LegacyInMemoryVectorStore,  # Use legacy store for backward compat tests
    MemoryEntry,
    SearchResult,
    SessionMemory,
    SessionMemoryConfig,
    SQLiteCheckpointStore,
    WorkingMemory,
)

# Alias for backward compatibility in tests
InMemoryVectorStore = LegacyInMemoryVectorStore

# =============================================================================
# WorkingMemory Tests
# =============================================================================


class TestWorkingMemory:
    """Tests for WorkingMemory."""

    @pytest.fixture
    def memory(self) -> WorkingMemory:
        """Create a fresh WorkingMemory instance."""
        return WorkingMemory()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, memory: WorkingMemory) -> None:
        """Test basic store and retrieve operations."""
        await memory.store("key1", "value1")
        result = await memory.retrieve("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_store_with_metadata(self, memory: WorkingMemory) -> None:
        """Test storing with metadata."""
        await memory.store("key1", "value1", {"source": "test"})
        entry = await memory.get_entry("key1")
        assert entry is not None
        assert entry.value == "value1"
        assert entry.metadata == {"source": "test"}

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent(self, memory: WorkingMemory) -> None:
        """Test retrieving a nonexistent key."""
        result = await memory.retrieve("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, memory: WorkingMemory) -> None:
        """Test delete operation."""
        await memory.store("key1", "value1")
        deleted = await memory.delete("key1")
        assert deleted is True
        assert await memory.retrieve("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, memory: WorkingMemory) -> None:
        """Test deleting a nonexistent key."""
        deleted = await memory.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists(self, memory: WorkingMemory) -> None:
        """Test exists operation."""
        await memory.store("key1", "value1")
        assert await memory.exists("key1") is True
        assert await memory.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear(self, memory: WorkingMemory) -> None:
        """Test clear operation."""
        await memory.store("key1", "value1")
        await memory.store("key2", "value2")
        await memory.clear()
        assert len(memory) == 0
        assert await memory.keys() == []

    @pytest.mark.asyncio
    async def test_keys(self, memory: WorkingMemory) -> None:
        """Test keys operation."""
        await memory.store("key1", "value1")
        await memory.store("key2", "value2")
        keys = await memory.keys()
        assert set(keys) == {"key1", "key2"}

    @pytest.mark.asyncio
    async def test_get_all(self, memory: WorkingMemory) -> None:
        """Test get_all operation."""
        await memory.store("key1", "value1")
        await memory.store("key2", "value2")
        all_data = await memory.get_all()
        assert all_data == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_snapshot_and_restore(self, memory: WorkingMemory) -> None:
        """Test snapshot and restore operations."""
        await memory.store("key1", "value1")
        await memory.store("key2", {"nested": "data"})

        snapshot = memory.snapshot()
        assert "key1" in snapshot
        assert "key2" in snapshot

        # Create new memory and restore
        new_memory = WorkingMemory()
        new_memory.restore(snapshot)
        assert await new_memory.retrieve("key1") == "value1"
        assert await new_memory.retrieve("key2") == {"nested": "data"}

    def test_len(self, memory: WorkingMemory) -> None:
        """Test __len__ method."""
        assert len(memory) == 0
        memory._data["key1"] = MemoryEntry(key="key1", value="value1")
        assert len(memory) == 1

    def test_contains(self, memory: WorkingMemory) -> None:
        """Test __contains__ method."""
        memory._data["key1"] = MemoryEntry(key="key1", value="value1")
        assert "key1" in memory
        assert "nonexistent" not in memory

    @pytest.mark.asyncio
    async def test_get_with_default(self, memory: WorkingMemory) -> None:
        """Test get with default value."""
        await memory.store("key1", "value1")
        assert await memory.get("key1") == "value1"
        assert await memory.get("nonexistent", "default") == "default"

    @pytest.mark.asyncio
    async def test_update_existing(self, memory: WorkingMemory) -> None:
        """Test update method."""
        await memory.store("key1", "value1")
        updated = await memory.update("key1", "new_value")
        assert updated is True
        assert await memory.retrieve("key1") == "new_value"

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, memory: WorkingMemory) -> None:
        """Test update on nonexistent key."""
        updated = await memory.update("nonexistent", "value")
        assert updated is False


# =============================================================================
# SessionMemory Tests
# =============================================================================


class TestSessionMemory:
    """Tests for SessionMemory."""

    @pytest.fixture
    def memory(self) -> SessionMemory:
        """Create a fresh SessionMemory instance."""
        return SessionMemory()

    @pytest.mark.asyncio
    async def test_add_message(self, memory: SessionMemory) -> None:
        """Test adding messages."""
        msg = Message(role=MessageRole.USER, content="Hello")
        await memory.add_message(msg)
        messages = await memory.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_add_multiple_messages(self, memory: SessionMemory) -> None:
        """Test adding multiple messages."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!"),
            Message(role=MessageRole.USER, content="How are you?"),
        ]
        await memory.add_messages(messages)
        assert len(memory) == 3

    @pytest.mark.asyncio
    async def test_get_messages_with_limit(self, memory: SessionMemory) -> None:
        """Test getting messages with limit."""
        for i in range(5):
            await memory.add_message(Message(role=MessageRole.USER, content=f"Msg {i}"))

        messages = await memory.get_messages(limit=2)
        assert len(messages) == 2
        assert messages[0].content == "Msg 3"
        assert messages[1].content == "Msg 4"

    @pytest.mark.asyncio
    async def test_sliding_window(self) -> None:
        """Test sliding window functionality."""
        config = SessionMemoryConfig(max_messages=3, sliding_window=True)
        memory = SessionMemory(config)

        for i in range(5):
            await memory.add_message(Message(role=MessageRole.USER, content=f"Msg {i}"))

        assert len(memory) == 3
        messages = await memory.get_messages()
        assert messages[0].content == "Msg 2"
        assert messages[1].content == "Msg 3"
        assert messages[2].content == "Msg 4"

    @pytest.mark.asyncio
    async def test_no_sliding_window(self) -> None:
        """Test with sliding window disabled."""
        config = SessionMemoryConfig(max_messages=3, sliding_window=False)
        memory = SessionMemory(config)

        for i in range(5):
            await memory.add_message(Message(role=MessageRole.USER, content=f"Msg {i}"))

        assert len(memory) == 5

    @pytest.mark.asyncio
    async def test_get_last_message(self, memory: SessionMemory) -> None:
        """Test getting last message."""
        await memory.add_message(Message(role=MessageRole.USER, content="First"))
        await memory.add_message(Message(role=MessageRole.ASSISTANT, content="Last"))

        last = await memory.get_last_message()
        assert last is not None
        assert last.content == "Last"

    @pytest.mark.asyncio
    async def test_get_first_message(self, memory: SessionMemory) -> None:
        """Test getting first message."""
        await memory.add_message(Message(role=MessageRole.USER, content="First"))
        await memory.add_message(Message(role=MessageRole.ASSISTANT, content="Last"))

        first = await memory.get_first_message()
        assert first is not None
        assert first.content == "First"

    @pytest.mark.asyncio
    async def test_metadata_storage(self, memory: SessionMemory) -> None:
        """Test metadata storage (not messages)."""
        await memory.store("user_id", "12345")
        await memory.store("preferences", {"theme": "dark"})

        assert await memory.retrieve("user_id") == "12345"
        assert await memory.retrieve("preferences") == {"theme": "dark"}

    @pytest.mark.asyncio
    async def test_to_openai_messages(self, memory: SessionMemory) -> None:
        """Test conversion to OpenAI format."""
        await memory.add_message(Message(role=MessageRole.SYSTEM, content="System prompt"))
        await memory.add_message(Message(role=MessageRole.USER, content="Hello"))
        await memory.add_message(Message(role=MessageRole.ASSISTANT, content="Hi!"))

        openai_msgs = memory.to_openai_messages()
        assert len(openai_msgs) == 3
        assert openai_msgs[0] == {"role": "system", "content": "System prompt"}
        assert openai_msgs[1] == {"role": "user", "content": "Hello"}
        assert openai_msgs[2] == {"role": "assistant", "content": "Hi!"}

    @pytest.mark.asyncio
    async def test_to_anthropic_messages(self, memory: SessionMemory) -> None:
        """Test conversion to Anthropic format."""
        await memory.add_message(Message(role=MessageRole.USER, content="Hello"))

        anthropic_msgs = memory.to_anthropic_messages()
        assert len(anthropic_msgs) == 1
        assert anthropic_msgs[0] == {"role": "user", "content": "Hello"}

    @pytest.mark.asyncio
    async def test_from_messages(self) -> None:
        """Test creating SessionMemory from existing messages."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi!"),
        ]
        memory = SessionMemory.from_messages(messages)
        assert len(memory) == 2

    @pytest.mark.asyncio
    async def test_snapshot_and_restore(self, memory: SessionMemory) -> None:
        """Test snapshot and restore."""
        await memory.add_message(Message(role=MessageRole.USER, content="Hello"))
        await memory.store("key1", "value1")

        snapshot = memory.snapshot()
        restored = SessionMemory.restore(snapshot)

        assert len(restored) == 1
        assert await restored.retrieve("key1") == "value1"

    @pytest.mark.asyncio
    async def test_clear_messages(self, memory: SessionMemory) -> None:
        """Test clearing messages only."""
        await memory.add_message(Message(role=MessageRole.USER, content="Hello"))
        await memory.store("key1", "value1")

        await memory.clear_messages()
        assert len(memory) == 0
        assert await memory.retrieve("key1") == "value1"


# =============================================================================
# FileMemory Tests
# =============================================================================


class TestFileMemory:
    """Tests for FileMemory."""

    @pytest.fixture
    def temp_file(self) -> str:
        """Create a temporary file path."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def memory(self, temp_file: str) -> FileMemory:
        """Create a FileMemory instance with temp file."""
        config = FileMemoryConfig(path=temp_file, autosave=True)
        return FileMemory(config)

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, memory: FileMemory) -> None:
        """Test basic store and retrieve."""
        await memory.store("key1", "value1")
        result = await memory.retrieve("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_persistence(self, temp_file: str) -> None:
        """Test that data persists across instances."""
        config = FileMemoryConfig(path=temp_file, autosave=True)

        # Store data in first instance
        memory1 = FileMemory(config)
        await memory1.store("key1", "value1")
        await memory1.store("key2", {"nested": "data"})

        # Create new instance and verify data
        memory2 = FileMemory(config)
        assert await memory2.retrieve("key1") == "value1"
        assert await memory2.retrieve("key2") == {"nested": "data"}

    @pytest.mark.asyncio
    async def test_delete(self, memory: FileMemory) -> None:
        """Test delete operation."""
        await memory.store("key1", "value1")
        deleted = await memory.delete("key1")
        assert deleted is True
        assert await memory.retrieve("key1") is None

    @pytest.mark.asyncio
    async def test_autosave_disabled(self, temp_file: str) -> None:
        """Test with autosave disabled."""
        config = FileMemoryConfig(path=temp_file, autosave=False)
        memory = FileMemory(config)

        await memory.store("key1", "value1")

        # Data should not be saved yet
        memory2 = FileMemory(config)
        assert await memory2.retrieve("key1") is None

        # Manual save
        memory.save()

        # Now data should be persisted
        memory3 = FileMemory(config)
        assert await memory3.retrieve("key1") == "value1"

    @pytest.mark.asyncio
    async def test_reload(self, memory: FileMemory, temp_file: str) -> None:
        """Test reload functionality."""
        await memory.store("key1", "value1")

        # Modify file externally
        config = FileMemoryConfig(path=temp_file)
        other_memory = FileMemory(config)
        await other_memory.store("key1", "modified")

        # Reload should pick up changes
        memory.reload()
        assert await memory.retrieve("key1") == "modified"

    @pytest.mark.asyncio
    async def test_create_directories(self) -> None:
        """Test automatic directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "nested", "memory.json")
            config = FileMemoryConfig(path=path, create_dirs=True)
            memory = FileMemory(config)

            await memory.store("key1", "value1")
            assert os.path.exists(path)


# =============================================================================
# InMemoryVectorStore Tests
# =============================================================================


class TestInMemoryVectorStore:
    """Tests for InMemoryVectorStore."""

    @pytest.fixture
    def store(self) -> InMemoryVectorStore:
        """Create a fresh InMemoryVectorStore instance."""
        return InMemoryVectorStore()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, store: InMemoryVectorStore) -> None:
        """Test basic store and retrieve."""
        await store.store("key1", "content1")
        assert await store.retrieve("key1") == "content1"

    @pytest.mark.asyncio
    async def test_store_with_embedding(self, store: InMemoryVectorStore) -> None:
        """Test storing with embedding."""
        await store.store_with_embedding(
            key="doc1",
            content="Hello world",
            embedding=[0.1, 0.2, 0.3],
        )
        assert await store.retrieve("doc1") == "Hello world"

    @pytest.mark.asyncio
    async def test_search_by_embedding(self, store: InMemoryVectorStore) -> None:
        """Test similarity search by embedding."""
        # Store documents with different embeddings
        await store.store_with_embedding(
            key="doc1",
            content="Document one",
            embedding=[1.0, 0.0, 0.0],
        )
        await store.store_with_embedding(
            key="doc2",
            content="Document two",
            embedding=[0.0, 1.0, 0.0],
        )
        await store.store_with_embedding(
            key="doc3",
            content="Document three",
            embedding=[0.9, 0.1, 0.0],  # Similar to doc1
        )

        # Search with embedding similar to doc1
        results = await store.search_by_embedding([1.0, 0.0, 0.0], top_k=2)

        assert len(results) == 2
        # doc1 should be first (exact match)
        assert results[0].entry.key == "doc1"
        assert results[0].score == pytest.approx(1.0)
        # doc3 should be second (similar)
        assert results[1].entry.key == "doc3"

    @pytest.mark.asyncio
    async def test_search_not_implemented(self, store: InMemoryVectorStore) -> None:
        """Test that search raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await store.search("query")


# =============================================================================
# SQLiteCheckpointStore Tests
# =============================================================================


class TestSQLiteCheckpointStore:
    """Tests for SQLiteCheckpointStore."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create a temporary database path."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def store(self, temp_db: str) -> SQLiteCheckpointStore:
        """Create a SQLiteCheckpointStore instance."""
        return SQLiteCheckpointStore(temp_db)

    @pytest.mark.asyncio
    async def test_save_and_load(self, store: SQLiteCheckpointStore) -> None:
        """Test saving and loading checkpoints."""
        state = {"counter": 5, "data": [1, 2, 3]}
        await store.save("thread-1", step=1, state=state)

        checkpoint = await store.load("thread-1", step=1)
        assert checkpoint is not None
        assert checkpoint.thread_id == "thread-1"
        assert checkpoint.step == 1
        assert checkpoint.state == state

    @pytest.mark.asyncio
    async def test_load_latest(self, store: SQLiteCheckpointStore) -> None:
        """Test loading the latest checkpoint."""
        await store.save("thread-1", step=1, state={"step": 1})
        await store.save("thread-1", step=2, state={"step": 2})
        await store.save("thread-1", step=3, state={"step": 3})

        checkpoint = await store.load("thread-1")
        assert checkpoint is not None
        assert checkpoint.step == 3

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, store: SQLiteCheckpointStore) -> None:
        """Test listing all checkpoints for a thread."""
        await store.save("thread-1", step=1, state={})
        await store.save("thread-1", step=2, state={})
        await store.save("thread-1", step=3, state={})

        checkpoints = await store.list_checkpoints("thread-1")
        assert len(checkpoints) == 3
        assert [cp.step for cp in checkpoints] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_delete(self, store: SQLiteCheckpointStore) -> None:
        """Test deleting a checkpoint."""
        await store.save("thread-1", step=1, state={})

        deleted = await store.delete("thread-1", step=1)
        assert deleted is True

        checkpoint = await store.load("thread-1", step=1)
        assert checkpoint is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store: SQLiteCheckpointStore) -> None:
        """Test deleting a nonexistent checkpoint."""
        deleted = await store.delete("nonexistent", step=1)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_delete_thread(self, store: SQLiteCheckpointStore) -> None:
        """Test deleting all checkpoints for a thread."""
        await store.save("thread-1", step=1, state={})
        await store.save("thread-1", step=2, state={})
        await store.save("thread-2", step=1, state={})

        count = await store.delete_thread("thread-1")
        assert count == 2

        assert await store.list_checkpoints("thread-1") == []
        assert len(await store.list_checkpoints("thread-2")) == 1

    @pytest.mark.asyncio
    async def test_list_threads(self, store: SQLiteCheckpointStore) -> None:
        """Test listing all thread IDs."""
        await store.save("thread-1", step=1, state={})
        await store.save("thread-2", step=1, state={})
        await store.save("thread-3", step=1, state={})

        threads = await store.list_threads()
        assert set(threads) == {"thread-1", "thread-2", "thread-3"}

    @pytest.mark.asyncio
    async def test_persistence(self, temp_db: str) -> None:
        """Test that checkpoints persist across instances."""
        store1 = SQLiteCheckpointStore(temp_db)
        await store1.save("thread-1", step=1, state={"data": "persisted"})

        store2 = SQLiteCheckpointStore(temp_db)
        checkpoint = await store2.load("thread-1", step=1)
        assert checkpoint is not None
        assert checkpoint.state == {"data": "persisted"}

    @pytest.mark.asyncio
    async def test_metadata(self, store: SQLiteCheckpointStore) -> None:
        """Test checkpoint metadata."""
        metadata = {"agent": "test-agent", "version": "1.0"}
        await store.save("thread-1", step=1, state={}, metadata=metadata)

        checkpoint = await store.load("thread-1", step=1)
        assert checkpoint is not None
        assert checkpoint.metadata == metadata


# =============================================================================
# InMemoryCheckpointStore Tests
# =============================================================================


class TestInMemoryCheckpointStore:
    """Tests for InMemoryCheckpointStore."""

    @pytest.fixture
    def store(self) -> InMemoryCheckpointStore:
        """Create a fresh InMemoryCheckpointStore instance."""
        return InMemoryCheckpointStore()

    @pytest.mark.asyncio
    async def test_save_and_load(self, store: InMemoryCheckpointStore) -> None:
        """Test saving and loading checkpoints."""
        state = {"counter": 5}
        await store.save("thread-1", step=1, state=state)

        checkpoint = await store.load("thread-1", step=1)
        assert checkpoint is not None
        assert checkpoint.state == state

    @pytest.mark.asyncio
    async def test_load_latest(self, store: InMemoryCheckpointStore) -> None:
        """Test loading the latest checkpoint."""
        await store.save("thread-1", step=1, state={"step": 1})
        await store.save("thread-1", step=2, state={"step": 2})

        checkpoint = await store.load("thread-1")
        assert checkpoint is not None
        assert checkpoint.step == 2

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, store: InMemoryCheckpointStore) -> None:
        """Test listing checkpoints."""
        await store.save("thread-1", step=1, state={})
        await store.save("thread-1", step=2, state={})

        checkpoints = await store.list_checkpoints("thread-1")
        assert len(checkpoints) == 2

    @pytest.mark.asyncio
    async def test_delete(self, store: InMemoryCheckpointStore) -> None:
        """Test deleting a checkpoint."""
        await store.save("thread-1", step=1, state={})

        deleted = await store.delete("thread-1", step=1)
        assert deleted is True
        assert await store.load("thread-1", step=1) is None

    @pytest.mark.asyncio
    async def test_clear(self, store: InMemoryCheckpointStore) -> None:
        """Test clearing all checkpoints."""
        await store.save("thread-1", step=1, state={})
        await store.save("thread-2", step=1, state={})

        store.clear()

        assert await store.load("thread-1") is None
        assert await store.load("thread-2") is None


# =============================================================================
# MemoryEntry Tests
# =============================================================================


class TestMemoryEntry:
    """Tests for MemoryEntry model."""

    def test_create_entry(self) -> None:
        """Test creating a memory entry."""
        entry = MemoryEntry(key="test", value="data")
        assert entry.key == "test"
        assert entry.value == "data"
        assert entry.metadata is None
        assert entry.created_at is not None
        assert entry.updated_at is not None

    def test_create_entry_with_metadata(self) -> None:
        """Test creating an entry with metadata."""
        metadata = {"source": "test", "version": 1}
        entry = MemoryEntry(key="test", value="data", metadata=metadata)
        assert entry.metadata == metadata

    def test_model_dump(self) -> None:
        """Test serialization."""
        entry = MemoryEntry(key="test", value={"nested": "data"})
        data = entry.model_dump()
        assert data["key"] == "test"
        assert data["value"] == {"nested": "data"}


# =============================================================================
# SearchResult Tests
# =============================================================================


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_create_result(self) -> None:
        """Test creating a search result."""
        entry = MemoryEntry(key="test", value="data")
        result = SearchResult(entry=entry, score=0.95)
        assert result.entry == entry
        assert result.score == 0.95

    def test_default_score(self) -> None:
        """Test default score value."""
        entry = MemoryEntry(key="test", value="data")
        result = SearchResult(entry=entry)
        assert result.score == 1.0


# =============================================================================
# Checkpoint Tests
# =============================================================================


class TestCheckpoint:
    """Tests for Checkpoint model."""

    def test_create_checkpoint(self) -> None:
        """Test creating a checkpoint."""
        checkpoint = Checkpoint(
            thread_id="thread-1",
            step=5,
            state={"counter": 10},
        )
        assert checkpoint.thread_id == "thread-1"
        assert checkpoint.step == 5
        assert checkpoint.state == {"counter": 10}
        assert checkpoint.created_at is not None
        assert checkpoint.metadata is None

    def test_checkpoint_with_metadata(self) -> None:
        """Test checkpoint with metadata."""
        metadata = {"agent": "test"}
        checkpoint = Checkpoint(
            thread_id="thread-1",
            step=1,
            state={},
            metadata=metadata,
        )
        assert checkpoint.metadata == metadata
