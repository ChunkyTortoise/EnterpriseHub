"""Tests for vector store base classes."""

from typing import List, Optional
from uuid import UUID, uuid4

import pytest
from src.core.exceptions import VectorStoreError
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.vector_store.base import SearchOptions, VectorStore, VectorStoreConfig


class MockVectorStore(VectorStore):
    """Mock implementation for testing."""

    def __init__(self, config: Optional[VectorStoreConfig] = None) -> None:
        super().__init__(config)
        self._chunks: dict = {}

    async def initialize(self) -> None:
        """Initialize mock store."""
        self._initialized = True

    async def close(self) -> None:
        """Close mock store."""
        self._initialized = False

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add chunks to mock store."""
        self._ensure_initialized()
        for chunk in chunks:
            if chunk.embedding is None:
                raise VectorStoreError(
                    message=f"Chunk {chunk.id} has no embedding",
                    error_code="MISSING_EMBEDDING",
                )
            self._validate_embedding(chunk.embedding)
            self._chunks[chunk.id] = chunk

    async def delete_chunks(self, chunk_ids: List[UUID]) -> None:
        """Delete chunks from mock store."""
        self._ensure_initialized()
        for chunk_id in chunk_ids:
            self._chunks.pop(chunk_id, None)

    async def search(
        self,
        query_embedding: List[float],
        options: Optional[SearchOptions] = None,
    ) -> List[SearchResult]:
        """Search mock store."""
        self._ensure_initialized()
        self._validate_embedding(query_embedding)
        return []

    async def get_chunk(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get chunk from mock store."""
        self._ensure_initialized()
        return self._chunks.get(chunk_id)

    async def update_chunk(self, chunk: DocumentChunk) -> None:
        """Update chunk in mock store."""
        self._ensure_initialized()
        if chunk.id not in self._chunks:
            raise VectorStoreError(
                message=f"Chunk {chunk.id} not found",
                error_code="NOT_FOUND",
            )
        self._chunks[chunk.id] = chunk

    async def count(self) -> int:
        """Get chunk count."""
        self._ensure_initialized()
        return len(self._chunks)

    async def clear(self) -> None:
        """Clear mock store."""
        self._ensure_initialized()
        self._chunks.clear()

    async def health_check(self) -> bool:
        """Check health."""
        return self._initialized


class TestVectorStoreConfig:
    """Test cases for VectorStoreConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = VectorStoreConfig()
        assert config.collection_name == "default"
        assert config.dimension == 1536
        assert config.distance_metric == "cosine"
        assert config.metadata_schema is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = VectorStoreConfig(
            collection_name="test_collection",
            dimension=768,
            distance_metric="euclidean",
            metadata_schema={"field": "string"},
        )
        assert config.collection_name == "test_collection"
        assert config.dimension == 768
        assert config.distance_metric == "euclidean"
        assert config.metadata_schema == {"field": "string"}


class TestSearchOptions:
    """Test cases for SearchOptions."""

    def test_default_values(self) -> None:
        """Test default search options."""
        options = SearchOptions()
        assert options.top_k == 10
        assert options.threshold == 0.0
        assert options.filters is None
        assert options.include_embeddings is False
        assert options.include_metadata is True

    def test_custom_values(self) -> None:
        """Test custom search options."""
        options = SearchOptions(
            top_k=5,
            threshold=0.8,
            filters={"author": "test"},
            include_embeddings=True,
            include_metadata=False,
        )
        assert options.top_k == 5
        assert options.threshold == 0.8
        assert options.filters == {"author": "test"}
        assert options.include_embeddings is True
        assert options.include_metadata is False


class TestVectorStore:
    """Test cases for VectorStore base class."""

    @pytest.fixture
    def store(self) -> MockVectorStore:
        """Create mock store fixture."""
        return MockVectorStore()

    def test_initialization(self) -> None:
        """Test store initialization."""
        config = VectorStoreConfig(collection_name="test")
        store = MockVectorStore(config)
        assert store.config == config
        assert store._initialized is False

    def test_default_config(self) -> None:
        """Test store with default config."""
        store = MockVectorStore()
        assert store.config.collection_name == "default"

    def test_validate_embedding_correct_dimension(self) -> None:
        """Test validation with correct dimension."""
        config = VectorStoreConfig(dimension=3)
        store = MockVectorStore(config)
        # Should not raise
        store._validate_embedding([0.1, 0.2, 0.3])

    def test_validate_embedding_wrong_dimension(self) -> None:
        """Test validation with wrong dimension."""
        config = VectorStoreConfig(dimension=3)
        store = MockVectorStore(config)
        with pytest.raises(VectorStoreError) as exc_info:
            store._validate_embedding([0.1, 0.2])
        assert exc_info.value.error_code == "DIMENSION_MISMATCH"

    def test_ensure_initialized_raises(self) -> None:
        """Test that operations fail when not initialized."""
        store = MockVectorStore()
        with pytest.raises(VectorStoreError) as exc_info:
            store._ensure_initialized()
        assert exc_info.value.error_code == "NOT_INITIALIZED"

    def test_chunk_to_dict(self) -> None:
        """Test converting chunk to dictionary."""
        store = MockVectorStore()
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test content",
            index=1,
            token_count=10,
            metadata=Metadata(
                source="test.txt",
                title="Test",
                author="Author",
                language="en",
                tags=["tag1"],
                custom={"custom_field": "value"},
            ),
        )
        data = store._chunk_to_dict(chunk)
        assert data["id"] == str(chunk.id)
        assert data["document_id"] == str(chunk.document_id)
        assert data["content"] == "Test content"
        assert data["index"] == 1
        assert data["token_count"] == 10

    def test_dict_to_chunk(self) -> None:
        """Test converting dictionary to chunk."""
        store = MockVectorStore()
        chunk_id = uuid4()
        doc_id = uuid4()
        data = {
            "id": str(chunk_id),
            "document_id": str(doc_id),
            "content": "Test content",
            "index": 1,
            "token_count": 10,
            "metadata": {
                "source": "test.txt",
                "title": "Test",
                "custom_field": "value",
            },
        }
        embedding = [0.1, 0.2, 0.3]
        chunk = store._dict_to_chunk(data, embedding)
        assert chunk.id == chunk_id
        assert chunk.document_id == doc_id
        assert chunk.content == "Test content"
        assert chunk.embedding == embedding
        assert chunk.metadata.source == "test.txt"

    @pytest.mark.asyncio
    async def test_add_chunks(self, store: MockVectorStore) -> None:
        """Test adding chunks."""
        await store.initialize()
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content="Test",
                embedding=[0.1, 0.2, 0.3],
            ),
        ]
        await store.add_chunks(chunks)
        assert await store.count() == 1

    @pytest.mark.asyncio
    async def test_add_chunks_missing_embedding(self, store: MockVectorStore) -> None:
        """Test adding chunks without embedding raises error."""
        await store.initialize()
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content="Test",
                embedding=None,
            ),
        ]
        with pytest.raises(VectorStoreError) as exc_info:
            await store.add_chunks(chunks)
        assert exc_info.value.error_code == "MISSING_EMBEDDING"

    @pytest.mark.asyncio
    async def test_get_chunk(self, store: MockVectorStore) -> None:
        """Test getting chunk."""
        await store.initialize()
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test",
            embedding=[0.1, 0.2, 0.3],
        )
        await store.add_chunks([chunk])
        result = await store.get_chunk(chunk.id)
        assert result is not None
        assert result.id == chunk.id

    @pytest.mark.asyncio
    async def test_delete_chunks(self, store: MockVectorStore) -> None:
        """Test deleting chunks."""
        await store.initialize()
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test",
            embedding=[0.1, 0.2, 0.3],
        )
        await store.add_chunks([chunk])
        await store.delete_chunks([chunk.id])
        assert await store.count() == 0

    @pytest.mark.asyncio
    async def test_clear(self, store: MockVectorStore) -> None:
        """Test clearing store."""
        await store.initialize()
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content=f"Test {i}",
                embedding=[0.1, 0.2, 0.3],
            )
            for i in range(3)
        ]
        await store.add_chunks(chunks)
        assert await store.count() == 3
        await store.clear()
        assert await store.count() == 0

    @pytest.mark.asyncio
    async def test_health_check(self, store: MockVectorStore) -> None:
        """Test health check."""
        assert await store.health_check() is False
        await store.initialize()
        assert await store.health_check() is True
        await store.close()
        assert await store.health_check() is False
