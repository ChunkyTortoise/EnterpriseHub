"""Tests for dense retrieval components (MockDenseRetriever and DenseRetriever).

Validates Bug #1 fix (add_documents uses add_chunks) and Bug #4 fix
(SearchOptions uses top_k, not limit).
"""

import sys
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.retrieval.dense.dense_retriever_mock import MockDenseRetriever
from src.vector_store.base import SearchOptions, VectorStoreConfig

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_chunks() -> List[DocumentChunk]:
    doc_id = uuid4()
    return [
        DocumentChunk(
            document_id=doc_id,
            content="Python is a powerful programming language for data science",
            index=0,
            metadata=Metadata(title="Doc 1"),
        ),
        DocumentChunk(
            document_id=doc_id,
            content="Machine learning algorithms can analyze large datasets quickly",
            index=1,
            metadata=Metadata(title="Doc 2"),
        ),
        DocumentChunk(
            document_id=doc_id,
            content="Database query optimization improves retrieval performance",
            index=2,
            metadata=Metadata(title="Doc 3"),
        ),
    ]


# ===========================================================================
# MockDenseRetriever tests
# ===========================================================================


class TestMockDenseRetriever:
    @pytest.mark.asyncio
    async def test_initialize(self):
        retriever = MockDenseRetriever()
        assert retriever.is_initialized is False
        await retriever.initialize()
        assert retriever.is_initialized is True

    @pytest.mark.asyncio
    async def test_not_initialized_raises(self):
        retriever = MockDenseRetriever()
        with pytest.raises(RetrievalError, match="not initialized"):
            await retriever.add_documents([])

    @pytest.mark.asyncio
    async def test_add_documents(self, sample_chunks):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        await retriever.add_documents(sample_chunks)
        assert retriever.document_count == 3

    @pytest.mark.asyncio
    async def test_add_empty(self):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        await retriever.add_documents([])
        assert retriever.document_count == 0

    @pytest.mark.asyncio
    async def test_search_returns_valid_search_results(self, sample_chunks):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        await retriever.add_documents(sample_chunks)

        results = await retriever.search("python programming", top_k=2)
        assert len(results) <= 2
        for r in results:
            assert isinstance(r, SearchResult)
            assert 0.0 <= r.score <= 1.0
            assert r.rank >= 1
            assert r.distance >= 0.0
            assert r.explanation is not None

    @pytest.mark.asyncio
    async def test_search_empty_query(self, sample_chunks):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        await retriever.add_documents(sample_chunks)
        results = await retriever.search("   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_no_documents(self):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        results = await retriever.search("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_clear(self, sample_chunks):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        await retriever.add_documents(sample_chunks)
        retriever.clear()
        assert retriever.document_count == 0

    @pytest.mark.asyncio
    async def test_stats(self, sample_chunks):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        await retriever.add_documents(sample_chunks)
        stats = await retriever.get_stats()
        assert stats["document_count"] == 3
        assert stats["mock_retriever"] is True
        assert stats["initialized"] is True

    @pytest.mark.asyncio
    async def test_close(self):
        retriever = MockDenseRetriever()
        await retriever.initialize()
        await retriever.close()
        assert retriever.is_initialized is False


# ===========================================================================
# DenseRetriever tests (with mocked providers)
# ===========================================================================
# The production DenseRetriever imports chromadb at module level, which may
# not be available in all environments.  We mock the heavy imports so we can
# test the *logic* of add_documents / search without needing a real ChromaDB.


def _import_dense_retriever():
    """Lazily import DenseRetriever, mocking chromadb if needed."""
    try:
        from src.retrieval.dense.dense_retriever import DenseRetriever

        return DenseRetriever
    except (ImportError, Exception):
        # Patch chromadb so the module can be imported
        mock_chromadb = MagicMock()
        mock_chromadb.config.Settings = MagicMock
        sys.modules.setdefault("chromadb", mock_chromadb)
        sys.modules.setdefault("chromadb.api", MagicMock())
        sys.modules.setdefault("chromadb.api.models", MagicMock())
        sys.modules.setdefault("chromadb.api.models.Collection", MagicMock())
        sys.modules.setdefault("chromadb.config", mock_chromadb.config)

        # Also patch pydantic settings if needed
        mock_settings_mod = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "chromadb": mock_chromadb,
                "chromadb.config": mock_chromadb.config,
                "chromadb.api.models.Collection": MagicMock(),
            },
        ):
            # Force re-import
            import importlib

            if "src.vector_store.chroma_store" in sys.modules:
                importlib.reload(sys.modules["src.vector_store.chroma_store"])
            if "src.retrieval.dense.dense_retriever" in sys.modules:
                importlib.reload(sys.modules["src.retrieval.dense.dense_retriever"])
            from src.retrieval.dense.dense_retriever import DenseRetriever

            return DenseRetriever


class TestDenseRetriever:
    """Tests for the production DenseRetriever with mocked dependencies.

    Validates Bug #1 and #4 fixes.
    """

    @pytest.fixture(autouse=True)
    def _get_cls(self):
        self.DenseRetriever = _import_dense_retriever()

    @pytest.mark.asyncio
    async def test_add_documents_calls_add_chunks(self, sample_chunks):
        """Bug #1 fix: add_documents should embed then call add_chunks (not add_documents)."""
        retriever = self.DenseRetriever.__new__(self.DenseRetriever)
        retriever._collection_name = "test"
        retriever._embedding_model = "test"
        retriever._dimensions = 1536
        retriever._distance_metric = "cosine"
        retriever._document_count = 0

        # Mock embedding provider
        mock_embed_provider = AsyncMock()
        mock_embed_provider.embed = AsyncMock(return_value=[[0.1] * 1536 for _ in sample_chunks])

        # Mock vector store
        mock_vector_store = AsyncMock()
        mock_vector_store.add_chunks = AsyncMock()

        retriever._embedding_provider = mock_embed_provider
        retriever._vector_store = mock_vector_store
        retriever._initialized = True

        await retriever.add_documents(sample_chunks)

        # Verify add_chunks was called (not add_documents)
        mock_vector_store.add_chunks.assert_awaited_once()
        call_args = mock_vector_store.add_chunks.call_args
        chunks_arg = call_args[0][0]
        assert len(chunks_arg) == 3
        # Verify embeddings were set on each chunk
        for chunk in chunks_arg:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 1536

    @pytest.mark.asyncio
    async def test_search_uses_top_k(self, sample_chunks):
        """Bug #4 fix: SearchOptions should use top_k, not limit."""
        retriever = self.DenseRetriever.__new__(self.DenseRetriever)
        retriever._collection_name = "test"
        retriever._embedding_model = "test"
        retriever._dimensions = 1536
        retriever._distance_metric = "cosine"
        retriever._document_count = 0

        mock_embed_provider = AsyncMock()
        mock_embed_provider.embed = AsyncMock(return_value=[[0.1] * 1536])

        expected_result = SearchResult(
            chunk=sample_chunks[0],
            score=0.9,
            rank=1,
            distance=0.1,
        )
        mock_vector_store = AsyncMock()
        mock_vector_store.search = AsyncMock(return_value=[expected_result])

        retriever._embedding_provider = mock_embed_provider
        retriever._vector_store = mock_vector_store
        retriever._initialized = True

        results = await retriever.search("test query", top_k=5)

        assert len(results) == 1
        # Verify SearchOptions was constructed with top_k (not limit)
        call_args = mock_vector_store.search.call_args
        options = call_args[1]["options"]
        assert isinstance(options, SearchOptions)
        assert options.top_k == 5

    @pytest.mark.asyncio
    async def test_add_empty_documents(self):
        retriever = self.DenseRetriever.__new__(self.DenseRetriever)
        retriever._initialized = True
        retriever._document_count = 0
        # Should return early without error
        await retriever.add_documents([])

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        retriever = self.DenseRetriever.__new__(self.DenseRetriever)
        retriever._initialized = True
        results = await retriever.search("   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_not_initialized_raises(self):
        retriever = self.DenseRetriever.__new__(self.DenseRetriever)
        retriever._initialized = False
        with pytest.raises(RetrievalError, match="not initialized"):
            await retriever.search("test")

    @pytest.mark.asyncio
    async def test_lifecycle(self):
        retriever = self.DenseRetriever.__new__(self.DenseRetriever)
        retriever._collection_name = "test"
        retriever._embedding_model = "test"
        retriever._dimensions = 1536
        retriever._distance_metric = "cosine"
        retriever._document_count = 0

        mock_embed_provider = AsyncMock()
        mock_vector_store = AsyncMock()

        retriever._embedding_provider = mock_embed_provider
        retriever._vector_store = mock_vector_store
        retriever._initialized = True

        await retriever.close()
        assert retriever.is_initialized is False
        mock_embed_provider.close.assert_awaited_once()
        mock_vector_store.close.assert_awaited_once()
