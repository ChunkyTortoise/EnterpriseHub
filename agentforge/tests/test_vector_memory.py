"""Tests for vector memory implementations.

This module tests:
- InMemoryVectorStore: insert/search/delete operations
- LongTermMemory: store/retrieve/search with embeddings
- Metadata filtering
- Batch operations
- Edge cases (empty store, dimension mismatch)
"""

import math

import pytest

from agentforge.memory.longterm import LongTermMemory
from agentforge.memory.vector_base import VectorEntry, VectorSearchResult
from agentforge.memory.vector_memory import InMemoryVectorStore


# Helper functions
def create_test_vector(dim: int = 1536, value: float = 0.1) -> list[float]:
    """Create a test vector with a constant value."""
    return [value] * dim


def create_unit_vector(dim: int = 1536, index: int = 0) -> list[float]:
    """Create a unit vector with 1.0 at the specified index."""
    vec = [0.0] * dim
    vec[index] = 1.0
    return vec


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class TestVectorEntry:
    """Tests for VectorEntry model."""

    def test_create_entry(self):
        """Test creating a basic vector entry."""
        entry = VectorEntry(
            id="test1",
            vector=[0.1, 0.2, 0.3],
            metadata={"source": "test"},
            content="Test content",
        )
        assert entry.id == "test1"
        assert entry.vector == [0.1, 0.2, 0.3]
        assert entry.metadata == {"source": "test"}
        assert entry.content == "Test content"
        assert entry.created_at is not None

    def test_entry_defaults(self):
        """Test default values for optional fields."""
        entry = VectorEntry(
            id="test1",
            vector=[0.1, 0.2, 0.3],
        )
        assert entry.metadata == {}
        assert entry.content is None
        assert entry.created_at is not None


class TestInMemoryVectorStore:
    """Tests for InMemoryVectorStore."""

    @pytest.fixture
    def store(self):
        """Create a fresh store for each test."""
        return InMemoryVectorStore(dimension=10)

    @pytest.fixture
    def populated_store(self, store):
        """Create a store with test entries."""
        # Create orthogonal vectors for predictable similarity
        entries = [
            VectorEntry(
                id="doc1",
                vector=create_unit_vector(10, 0),
                content="First document",
                metadata={"category": "news", "priority": 1},
            ),
            VectorEntry(
                id="doc2",
                vector=create_unit_vector(10, 1),
                content="Second document",
                metadata={"category": "sports", "priority": 2},
            ),
            VectorEntry(
                id="doc3",
                vector=create_unit_vector(10, 2),
                content="Third document",
                metadata={"category": "news", "priority": 3},
            ),
        ]
        for entry in entries:
            store._vectors[entry.id] = entry.vector
            store._metadata[entry.id] = entry.metadata
            store._content[entry.id] = entry.content
            store._created_at[entry.id] = entry.created_at
        return store

    # Insert tests
    @pytest.mark.asyncio
    async def test_insert(self, store):
        """Test inserting a vector entry."""
        entry = VectorEntry(
            id="test1",
            vector=[0.1] * 10,
            content="Test content",
        )
        result = await store.insert(entry)
        assert result == "test1"
        assert await store.count() == 1

    @pytest.mark.asyncio
    async def test_insert_dimension_mismatch(self, store):
        """Test that wrong dimension raises error."""
        entry = VectorEntry(
            id="test1",
            vector=[0.1] * 5,  # Wrong dimension
        )
        with pytest.raises(ValueError, match="dimension mismatch"):
            await store.insert(entry)

    @pytest.mark.asyncio
    async def test_insert_overwrite(self, store):
        """Test that inserting with same ID overwrites."""
        entry1 = VectorEntry(id="test1", vector=[0.1] * 10, content="First")
        entry2 = VectorEntry(id="test1", vector=[0.2] * 10, content="Second")

        await store.insert(entry1)
        await store.insert(entry2)

        assert await store.count() == 1
        result = await store.get("test1")
        assert result.content == "Second"

    # Search tests
    @pytest.mark.asyncio
    async def test_search_empty_store(self, store):
        """Test search on empty store returns empty list."""
        results = await store.search([0.1] * 10, top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_basic(self, populated_store):
        """Test basic similarity search."""
        # Query matching doc1 exactly
        query = create_unit_vector(10, 0)
        results = await populated_store.search(query, top_k=3)

        assert len(results) == 3
        # doc1 should be first with highest similarity
        assert results[0].id == "doc1"
        assert results[0].score > 0.99  # Should be ~1.0

    @pytest.mark.asyncio
    async def test_search_top_k(self, populated_store):
        """Test that top_k limits results."""
        query = [0.5] * 10  # Equal similarity to all
        results = await populated_store.search(query, top_k=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_metadata_filter(self, populated_store):
        """Test metadata filtering in search."""
        query = [0.5] * 10
        results = await populated_store.search(
            query, top_k=10, filter_metadata={"category": "news"}
        )

        assert len(results) == 2
        for r in results:
            assert r.metadata["category"] == "news"

    @pytest.mark.asyncio
    async def test_search_metadata_filter_multiple(self, populated_store):
        """Test multiple metadata filters."""
        query = [0.5] * 10
        results = await populated_store.search(
            query, top_k=10, filter_metadata={"category": "news", "priority": 1}
        )

        assert len(results) == 1
        assert results[0].id == "doc1"

    @pytest.mark.asyncio
    async def test_search_zero_query(self, populated_store):
        """Test search with zero vector returns empty."""
        query = [0.0] * 10
        results = await populated_store.search(query, top_k=5)
        assert results == []

    # Get tests
    @pytest.mark.asyncio
    async def test_get_existing(self, populated_store):
        """Test getting an existing entry."""
        entry = await populated_store.get("doc1")
        assert entry is not None
        assert entry.id == "doc1"
        assert entry.content == "First document"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        """Test getting a non-existent entry returns None."""
        entry = await store.get("nonexistent")
        assert entry is None

    # Delete tests
    @pytest.mark.asyncio
    async def test_delete_existing(self, populated_store):
        """Test deleting an existing entry."""
        result = await populated_store.delete("doc1")
        assert result is True
        assert await populated_store.count() == 2
        assert await populated_store.get("doc1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        """Test deleting non-existent entry returns False."""
        result = await store.delete("nonexistent")
        assert result is False

    # Count tests
    @pytest.mark.asyncio
    async def test_count_empty(self, store):
        """Test count on empty store."""
        assert await store.count() == 0

    @pytest.mark.asyncio
    async def test_count_populated(self, populated_store):
        """Test count on populated store."""
        assert await populated_store.count() == 3

    # Batch operations
    @pytest.mark.asyncio
    async def test_insert_batch(self, store):
        """Test batch insert."""
        entries = [
            VectorEntry(id=f"doc{i}", vector=[0.1] * 10, content=f"Content {i}")
            for i in range(5)
        ]
        ids = await store.insert_batch(entries)
        assert len(ids) == 5
        assert await store.count() == 5

    @pytest.mark.asyncio
    async def test_insert_batch_dimension_error(self, store):
        """Test batch insert with dimension error."""
        entries = [
            VectorEntry(id="doc1", vector=[0.1] * 10),
            VectorEntry(id="doc2", vector=[0.1] * 5),  # Wrong dimension
        ]
        with pytest.raises(ValueError, match="dimension mismatch"):
            await store.insert_batch(entries)

    @pytest.mark.asyncio
    async def test_delete_batch(self, populated_store):
        """Test batch delete."""
        results = await populated_store.delete_batch(["doc1", "doc2"])
        assert all(results)
        assert await populated_store.count() == 1

    # Clear test
    @pytest.mark.asyncio
    async def test_clear(self, populated_store):
        """Test clearing the store."""
        await populated_store.clear()
        assert await populated_store.count() == 0

    # Exists test
    @pytest.mark.asyncio
    async def test_exists(self, populated_store):
        """Test exists method."""
        assert await populated_store.exists("doc1") is True
        assert await populated_store.exists("nonexistent") is False

    # Get all IDs test
    @pytest.mark.asyncio
    async def test_get_all_ids(self, populated_store):
        """Test getting all IDs."""
        ids = await populated_store.get_all_ids()
        assert set(ids) == {"doc1", "doc2", "doc3"}


class TestLongTermMemory:
    """Tests for LongTermMemory."""

    @pytest.fixture
    def mock_embedder(self):
        """Create a mock embedding function."""
        async def embed(text: str) -> list[float]:
            # Simple mock: use hash of text to create deterministic vector
            hash_val = hash(text) % 1000
            vec = [0.0] * 10
            vec[hash_val % 10] = 1.0
            return vec
        return embed

    @pytest.fixture
    def store(self):
        """Create a vector store."""
        return InMemoryVectorStore(dimension=10)

    @pytest.fixture
    def memory(self, store, mock_embedder):
        """Create a long-term memory with mock embedder."""
        return LongTermMemory(
            vector_store=store,
            embedder=mock_embedder,
            default_dimension=10,
        )

    # Store tests
    @pytest.mark.asyncio
    async def test_store_with_embedding(self, memory):
        """Test storing with automatic embedding."""
        await memory.store(
            key="fact1",
            value="The sky is blue",
            content="Sky color information",
            metadata={"category": "facts"},
        )

        result = await memory.retrieve("fact1")
        assert result == "Sky color information"

    @pytest.mark.asyncio
    async def test_store_string_value(self, memory):
        """Test storing a string value uses it as content."""
        await memory.store(key="fact1", value="The sky is blue")
        result = await memory.retrieve("fact1")
        assert result == "The sky is blue"

    @pytest.mark.asyncio
    async def test_store_non_string_value(self, memory):
        """Test storing non-string value stores in metadata."""
        await memory.store(key="data1", value={"nested": "data"})
        result = await memory.retrieve("data1")
        assert result == {"nested": "data"}

    @pytest.mark.asyncio
    async def test_store_without_embedder(self, store):
        """Test storing without embedder uses placeholder."""
        memory = LongTermMemory(
            vector_store=store,
            embedder=None,
            default_dimension=10  # Match store dimension
        )
        await memory.store(key="test", value="content")

        result = await memory.retrieve("test")
        assert result == "content"

    # Retrieve tests
    @pytest.mark.asyncio
    async def test_retrieve_existing(self, memory):
        """Test retrieving an existing entry."""
        await memory.store(key="test", value="content")
        result = await memory.retrieve("test")
        assert result == "content"

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent(self, memory):
        """Test retrieving non-existent entry returns None."""
        result = await memory.retrieve("nonexistent")
        assert result is None

    # Search tests
    @pytest.mark.asyncio
    async def test_search_with_embedder(self, memory):
        """Test semantic search with embedder."""
        await memory.store(key="doc1", value="Hello world")
        await memory.store(key="doc2", value="Goodbye world")

        results = await memory.search("Hello", top_k=2)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_without_embedder(self, store):
        """Test search without embedder raises error."""
        memory = LongTermMemory(vector_store=store, embedder=None)
        with pytest.raises(ValueError, match="Embedder required"):
            await memory.search("query")

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self, memory):
        """Test search with metadata filtering."""
        await memory.store(
            key="doc1", value="Content 1", metadata={"category": "news"}
        )
        await memory.store(
            key="doc2", value="Content 2", metadata={"category": "sports"}
        )

        results = await memory.search("Content", filter_metadata={"category": "news"})
        assert len(results) == 1
        assert results[0]["id"] == "doc1"

    @pytest.mark.asyncio
    async def test_search_by_vector(self, memory):
        """Test direct vector search bypassing embedder."""
        await memory.store(key="doc1", value="Test content")

        # Use a known vector
        query_vector = [0.0] * 10
        query_vector[0] = 1.0

        results = await memory.search_by_vector(query_vector, top_k=5)
        assert isinstance(results, list)

    # Delete tests
    @pytest.mark.asyncio
    async def test_delete(self, memory):
        """Test deleting an entry."""
        await memory.store(key="test", value="content")
        result = await memory.delete("test")
        assert result is True
        assert await memory.retrieve("test") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, memory):
        """Test deleting non-existent entry."""
        result = await memory.delete("nonexistent")
        assert result is False

    # Exists tests
    @pytest.mark.asyncio
    async def test_exists(self, memory):
        """Test exists method."""
        await memory.store(key="test", value="content")
        assert await memory.exists("test") is True
        assert await memory.exists("nonexistent") is False

    # Count tests
    @pytest.mark.asyncio
    async def test_count(self, memory):
        """Test count method."""
        assert await memory.count() == 0
        await memory.store(key="test1", value="content1")
        await memory.store(key="test2", value="content2")
        assert await memory.count() == 2

    # Batch operations
    @pytest.mark.asyncio
    async def test_store_batch(self, memory):
        """Test batch store operation."""
        entries = [
            {"key": "doc1", "value": "Content 1", "metadata": {"idx": 1}},
            {"key": "doc2", "value": "Content 2", "metadata": {"idx": 2}},
        ]
        ids = await memory.store_batch(entries)
        assert len(ids) == 2
        assert await memory.count() == 2

    # Clear tests
    @pytest.mark.asyncio
    async def test_clear(self, memory):
        """Test clearing all memories."""
        await memory.store(key="test1", value="content1")
        await memory.store(key="test2", value="content2")
        await memory.clear()
        assert await memory.count() == 0


class TestVectorSearchResult:
    """Tests for VectorSearchResult model."""

    def test_create_result(self):
        """Test creating a search result."""
        result = VectorSearchResult(
            id="test1",
            score=0.95,
            metadata={"category": "test"},
            content="Test content",
        )
        assert result.id == "test1"
        assert result.score == 0.95
        assert result.metadata == {"category": "test"}
        assert result.content == "Test content"

    def test_result_defaults(self):
        """Test default values."""
        result = VectorSearchResult(id="test1", score=0.5)
        assert result.metadata == {}
        assert result.content is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def store(self):
        return InMemoryVectorStore(dimension=10)

    @pytest.mark.asyncio
    async def test_large_vector(self, store):
        """Test handling of large vectors."""
        large_store = InMemoryVectorStore(dimension=10000)
        entry = VectorEntry(id="large", vector=[0.1] * 10000)
        await large_store.insert(entry)
        assert await large_store.count() == 1

    @pytest.mark.asyncio
    async def test_special_characters_in_id(self, store):
        """Test IDs with special characters."""
        entry = VectorEntry(
            id="test/special:chars-123_@#$%",
            vector=[0.1] * 10,
        )
        await store.insert(entry)
        result = await store.get("test/special:chars-123_@#$%")
        assert result is not None

    @pytest.mark.asyncio
    async def test_unicode_content(self, store):
        """Test Unicode content handling."""
        entry = VectorEntry(
            id="unicode",
            vector=[0.1] * 10,
            content="Hello, world! 123",
        )
        await store.insert(entry)
        result = await store.get("unicode")
        assert result.content == "Hello, world! 123"

    @pytest.mark.asyncio
    async def test_empty_metadata(self, store):
        """Test handling of empty metadata."""
        entry = VectorEntry(
            id="test",
            vector=[0.1] * 10,
            metadata={},
        )
        await store.insert(entry)
        result = await store.get("test")
        assert result.metadata == {}

    @pytest.mark.asyncio
    async def test_complex_metadata(self, store):
        """Test handling of complex metadata values."""
        entry = VectorEntry(
            id="test",
            vector=[0.1] * 10,
            metadata={
                "string": "value",
                "number": 42,
                "float": 3.14,
                "bool": True,
                "list": [1, 2, 3],
                "nested": {"key": "value"},
            },
        )
        await store.insert(entry)
        result = await store.get("test")
        assert result.metadata["string"] == "value"
        assert result.metadata["number"] == 42
        assert result.metadata["list"] == [1, 2, 3]
        assert result.metadata["nested"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_search_with_no_matches(self, store):
        """Test search that matches nothing due to filter."""
        entry = VectorEntry(
            id="test",
            vector=[0.1] * 10,
            metadata={"category": "a"},
        )
        await store.insert(entry)

        results = await store.search(
            [0.1] * 10,
            filter_metadata={"category": "b"},
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_search_top_k_greater_than_count(self, store):
        """Test search when top_k exceeds available entries."""
        entry = VectorEntry(id="test", vector=[0.1] * 10)
        await store.insert(entry)

        results = await store.search([0.1] * 10, top_k=100)
        assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
