"""Tests for ChromaDB vector store."""

import shutil
import tempfile
from uuid import uuid4

import pytest
from src.core.exceptions import NotFoundError, VectorStoreError
from src.core.types import DocumentChunk, Metadata
from src.vector_store.base import SearchOptions, VectorStoreConfig
from src.vector_store.chroma_store import ChromaVectorStore


@pytest.mark.integration
@pytest.fixture
def temp_dir():
    """Create temporary directory for ChromaDB."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
async def store(temp_dir: str):
    """Create and initialize ChromaDB store."""
    config = VectorStoreConfig(
        collection_name="test_collection",
        dimension=3,
        distance_metric="cosine",
    )
    store = ChromaVectorStore(config, persist_directory=temp_dir)
    await store.initialize()
    yield store
    await store.close()


class TestChromaVectorStore:
    """Test cases for ChromaVectorStore."""

    @pytest.mark.asyncio
    async def test_initialization(self, temp_dir: str) -> None:
        """Test store initialization."""
        config = VectorStoreConfig(collection_name="test_init")
        store = ChromaVectorStore(config, persist_directory=temp_dir)
        await store.initialize()
        assert store._initialized is True
        assert store._collection is not None
        await store.close()

    @pytest.mark.asyncio
    async def test_add_and_get_chunk(self, store: ChromaVectorStore) -> None:
        """Test adding and retrieving a chunk."""
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            metadata=Metadata(title="Test"),
            index=0,
            token_count=10,
        )
        await store.add_chunks([chunk])

        result = await store.get_chunk(chunk.id)
        assert result is not None
        assert result.id == chunk.id
        assert result.content == "Test content"
        assert result.metadata.title == "Test"

    @pytest.mark.asyncio
    async def test_add_chunks_without_embedding(self, store: ChromaVectorStore) -> None:
        """Test adding chunks without embedding raises error."""
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test",
            embedding=None,
        )
        with pytest.raises(VectorStoreError) as exc_info:
            await store.add_chunks([chunk])
        assert exc_info.value.error_code == "MISSING_EMBEDDING"

    @pytest.mark.asyncio
    async def test_add_chunks_wrong_dimension(self, store: ChromaVectorStore) -> None:
        """Test adding chunks with wrong embedding dimension."""
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test",
            embedding=[0.1, 0.2],  # Wrong dimension
        )
        with pytest.raises(VectorStoreError) as exc_info:
            await store.add_chunks([chunk])
        assert exc_info.value.error_code == "DIMENSION_MISMATCH"

    @pytest.mark.asyncio
    async def test_search(self, store: ChromaVectorStore) -> None:
        """Test similarity search."""
        # Add test chunks
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content="First document",
                embedding=[1.0, 0.0, 0.0],
            ),
            DocumentChunk(
                document_id=uuid4(),
                content="Second document",
                embedding=[0.0, 1.0, 0.0],
            ),
            DocumentChunk(
                document_id=uuid4(),
                content="Third document",
                embedding=[0.0, 0.0, 1.0],
            ),
        ]
        await store.add_chunks(chunks)

        # Search with query similar to first chunk
        results = await store.search(
            query_embedding=[0.9, 0.1, 0.0],
            options=SearchOptions(top_k=2),
        )

        assert len(results) == 2
        # First result should be most similar
        assert results[0].chunk.content == "First document"
        assert results[0].rank == 1
        assert results[0].score > 0.8

    @pytest.mark.asyncio
    async def test_search_with_threshold(self, store: ChromaVectorStore) -> None:
        """Test search with similarity threshold."""
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content="Similar document",
                embedding=[1.0, 0.0, 0.0],
            ),
            DocumentChunk(
                document_id=uuid4(),
                content="Different document",
                embedding=[0.0, 1.0, 0.0],
            ),
        ]
        await store.add_chunks(chunks)

        results = await store.search(
            query_embedding=[0.99, 0.01, 0.0],
            options=SearchOptions(top_k=10, threshold=0.9),
        )

        # Only the very similar document should be returned
        assert len(results) == 1
        assert results[0].chunk.content == "Similar document"

    @pytest.mark.asyncio
    async def test_search_with_filters(self, store: ChromaVectorStore) -> None:
        """Test search with metadata filters."""
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content="Doc by Author A",
                embedding=[1.0, 0.0, 0.0],
                metadata=Metadata(author="Author A"),
            ),
            DocumentChunk(
                document_id=uuid4(),
                content="Doc by Author B",
                embedding=[1.0, 0.0, 0.0],
                metadata=Metadata(author="Author B"),
            ),
        ]
        await store.add_chunks(chunks)

        results = await store.search(
            query_embedding=[1.0, 0.0, 0.0],
            options=SearchOptions(
                top_k=10,
                filters={"author": "Author A"},
            ),
        )

        assert len(results) == 1
        assert results[0].chunk.metadata.author == "Author A"

    @pytest.mark.asyncio
    async def test_delete_chunks(self, store: ChromaVectorStore) -> None:
        """Test deleting chunks."""
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="To be deleted",
            embedding=[0.1, 0.2, 0.3],
        )
        await store.add_chunks([chunk])
        assert await store.count() == 1

        await store.delete_chunks([chunk.id])
        assert await store.count() == 0
        assert await store.get_chunk(chunk.id) is None

    @pytest.mark.asyncio
    async def test_update_chunk(self, store: ChromaVectorStore) -> None:
        """Test updating a chunk."""
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Original content",
            embedding=[0.1, 0.2, 0.3],
            metadata=Metadata(title="Original"),
        )
        await store.add_chunks([chunk])

        # Update the chunk
        updated_chunk = DocumentChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            content="Updated content",
            embedding=[0.4, 0.5, 0.6],
            metadata=Metadata(title="Updated"),
        )
        await store.update_chunk(updated_chunk)

        # Verify update
        result = await store.get_chunk(chunk.id)
        assert result is not None
        assert result.content == "Updated content"
        assert result.metadata.title == "Updated"

    @pytest.mark.asyncio
    async def test_update_nonexistent_chunk(self, store: ChromaVectorStore) -> None:
        """Test updating a non-existent chunk raises error."""
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Doesn't exist",
            embedding=[0.1, 0.2, 0.3],
        )
        with pytest.raises(NotFoundError):
            await store.update_chunk(chunk)

    @pytest.mark.asyncio
    async def test_count(self, store: ChromaVectorStore) -> None:
        """Test counting chunks."""
        assert await store.count() == 0

        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content=f"Chunk {i}",
                embedding=[0.1, 0.2, 0.3],
            )
            for i in range(5)
        ]
        await store.add_chunks(chunks)
        assert await store.count() == 5

    @pytest.mark.asyncio
    async def test_clear(self, store: ChromaVectorStore) -> None:
        """Test clearing all chunks."""
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content=f"Chunk {i}",
                embedding=[0.1, 0.2, 0.3],
            )
            for i in range(3)
        ]
        await store.add_chunks(chunks)
        assert await store.count() == 3

        await store.clear()
        assert await store.count() == 0

    @pytest.mark.asyncio
    async def test_health_check(self, store: ChromaVectorStore) -> None:
        """Test health check."""
        assert await store.health_check() is True

        await store.close()
        assert await store.health_check() is False

    @pytest.mark.asyncio
    async def test_empty_search(self, store: ChromaVectorStore) -> None:
        """Test search on empty store."""
        results = await store.search(
            query_embedding=[1.0, 0.0, 0.0],
            options=SearchOptions(top_k=5),
        )
        assert results == []

    def test_distance_to_score_cosine(self) -> None:
        """Test distance to score conversion for cosine."""
        config = VectorStoreConfig(distance_metric="cosine")
        store = ChromaVectorStore(config)
        # Cosine distance 0.2 should give score 0.8
        score = store._distance_to_score(0.2)
        assert abs(score - 0.8) < 0.01

    def test_distance_to_score_euclidean(self) -> None:
        """Test distance to score conversion for euclidean."""
        config = VectorStoreConfig(distance_metric="euclidean")
        store = ChromaVectorStore(config)
        # Small distance should give high score
        score = store._distance_to_score(0.1)
        assert score > 0.9

    def test_map_distance_metric(self) -> None:
        """Test distance metric mapping."""
        config = VectorStoreConfig(distance_metric="cosine")
        store = ChromaVectorStore(config)

        assert store._map_distance_metric("cosine") == "cosine"
        assert store._map_distance_metric("euclidean") == "l2"
        assert store._map_distance_metric("dot") == "ip"
        assert store._map_distance_metric("unknown") == "cosine"
