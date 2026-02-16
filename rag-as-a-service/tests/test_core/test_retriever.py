"""Tests for hybrid retriever with vector + keyword search."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from rag_service.core.retriever import Retriever, RetrievedChunk


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def retriever(mock_db):
    """Retriever instance with mock DB."""
    return Retriever(db_session=mock_db, top_k=10)


class TestRetriever:
    """Test hybrid search retrieval."""

    async def test_hybrid_search_with_vector_and_keyword(self, retriever, mock_db):
        """Test hybrid search combines vector and keyword results."""
        # Arrange - mock vector search results
        vector_results = MagicMock()
        vector_results.fetchall = MagicMock(
            return_value=[
                MagicMock(
                    id="chunk1",
                    document_id="doc1",
                    content="Real estate market analysis",
                    metadata={"source": "report.pdf"},
                    similarity=0.95,
                ),
                MagicMock(
                    id="chunk2",
                    document_id="doc1",
                    content="Housing prices increasing",
                    metadata={},
                    similarity=0.85,
                ),
            ]
        )

        # Mock keyword search results
        keyword_results = MagicMock()
        keyword_results.fetchall = MagicMock(
            return_value=[
                MagicMock(
                    id="chunk2",  # Duplicate with vector
                    document_id="doc1",
                    content="Housing prices increasing",
                    metadata={},
                    rank=0.5,
                ),
                MagicMock(
                    id="chunk3",
                    document_id="doc2",
                    content="Real estate investment guide",
                    metadata={},
                    rank=0.4,
                ),
            ]
        )

        mock_db.execute = AsyncMock(side_effect=[vector_results, keyword_results])

        # Act
        results = await retriever.search(
            query="real estate market",
            query_embedding=[0.1] * 1536,
            top_k=5,
        )

        # Assert
        assert len(results) <= 5
        assert all(isinstance(c, RetrievedChunk) for c in results)
        # RRF fusion should combine scores
        assert results[0].score > 0

    async def test_vector_search_only(self, retriever, mock_db):
        """Test vector search alone."""
        # Arrange
        vector_results = MagicMock()
        vector_results.fetchall = MagicMock(
            return_value=[
                MagicMock(
                    id="chunk1",
                    document_id="doc1",
                    content="Content",
                    metadata={},
                    similarity=0.90,
                )
            ]
        )

        keyword_results = MagicMock()
        keyword_results.fetchall = MagicMock(return_value=[])

        mock_db.execute = AsyncMock(side_effect=[vector_results, keyword_results])

        # Act
        results = await retriever.search(
            query="test",
            query_embedding=[0.1] * 1536,
        )

        # Assert
        assert len(results) == 1
        assert results[0].vector_score == 0.90

    async def test_keyword_search_only(self, retriever, mock_db):
        """Test keyword search alone."""
        # Arrange
        vector_results = MagicMock()
        vector_results.fetchall = MagicMock(return_value=[])

        keyword_results = MagicMock()
        keyword_results.fetchall = MagicMock(
            return_value=[
                MagicMock(
                    id="chunk1",
                    document_id="doc1",
                    content="Keyword match",
                    metadata={},
                    rank=0.7,
                )
            ]
        )

        mock_db.execute = AsyncMock(side_effect=[vector_results, keyword_results])

        # Act
        results = await retriever.search(
            query="keyword match",
            query_embedding=[0.1] * 1536,
        )

        # Assert
        assert len(results) == 1
        assert results[0].keyword_score == 0.7

    async def test_collection_filter(self, retriever, mock_db):
        """Test search with collection filter."""
        # Arrange
        collection_id = "col123"
        vector_results = MagicMock()
        vector_results.fetchall = MagicMock(return_value=[])
        keyword_results = MagicMock()
        keyword_results.fetchall = MagicMock(return_value=[])

        mock_db.execute = AsyncMock(side_effect=[vector_results, keyword_results])

        # Act
        await retriever.search(
            query="test",
            query_embedding=[0.1] * 1536,
            collection_id=collection_id,
        )

        # Assert
        calls = mock_db.execute.call_args_list
        # Both vector and keyword searches should include collection filter
        assert any("collection_id" in str(call) for call in calls)

    async def test_rrf_fusion_scoring(self, retriever):
        """Test Reciprocal Rank Fusion scoring algorithm."""
        # Arrange
        vector_results = [
            RetrievedChunk(
                chunk_id="chunk1",
                document_id="doc1",
                content="First in vector",
                score=0.95,
            ),
            RetrievedChunk(
                chunk_id="chunk2",
                document_id="doc1",
                content="Second in vector",
                score=0.85,
            ),
        ]

        keyword_results = [
            RetrievedChunk(
                chunk_id="chunk2",
                document_id="doc1",
                content="First in keyword",
                score=0.90,
            ),
            RetrievedChunk(
                chunk_id="chunk3",
                document_id="doc1",
                content="Second in keyword",
                score=0.80,
            ),
        ]

        # Act
        fused = retriever._rrf_fusion(vector_results, keyword_results)

        # Assert
        # chunk2 appears in both (rank 0 in keyword, rank 1 in vector) -> highest RRF
        assert fused[0].chunk_id == "chunk2"
        assert fused[0].score > fused[1].score

    async def test_no_db_returns_empty(self):
        """Test that retriever returns empty when no DB configured."""
        # Arrange
        retriever = Retriever(db_session=None)

        # Act
        results = await retriever.search(
            query="test",
            query_embedding=[0.1] * 1536,
        )

        # Assert
        assert results == []

    async def test_bm25_score_calculation(self):
        """Test BM25 scoring function."""
        # Arrange
        query_terms = ["real", "estate", "market"]
        doc_terms = ["real", "estate", "prices", "in", "california"]
        avg_doc_len = 10.0
        doc_count = 100
        term_doc_freqs = {"real": 50, "estate": 30, "market": 20, "prices": 40}

        # Act
        score = Retriever.bm25_score(
            query_terms, doc_terms, avg_doc_len, doc_count, term_doc_freqs
        )

        # Assert
        assert score > 0
        assert isinstance(score, float)

    async def test_top_k_limiting(self, retriever, mock_db):
        """Test that top_k limits results."""
        # Arrange
        vector_results = MagicMock()
        vector_results.fetchall = MagicMock(
            return_value=[
                MagicMock(
                    id=f"chunk{i}",
                    document_id="doc1",
                    content=f"Content {i}",
                    metadata={},
                    similarity=0.9 - i * 0.05,
                )
                for i in range(20)
            ]
        )

        keyword_results = MagicMock()
        keyword_results.fetchall = MagicMock(return_value=[])

        mock_db.execute = AsyncMock(side_effect=[vector_results, keyword_results])

        # Act
        results = await retriever.search(
            query="test",
            query_embedding=[0.1] * 1536,
            top_k=5,
        )

        # Assert
        assert len(results) == 5


class TestRetrievedChunk:
    """Test RetrievedChunk data model."""

    def test_chunk_creation(self):
        """Test creating a retrieved chunk."""
        chunk = RetrievedChunk(
            chunk_id="chunk1",
            document_id="doc1",
            content="This is the chunk content",
            score=0.95,
            metadata={"page": 10},
            vector_score=0.90,
            keyword_score=0.05,
        )

        assert chunk.chunk_id == "chunk1"
        assert chunk.document_id == "doc1"
        assert chunk.score == 0.95
        assert chunk.vector_score == 0.90
        assert chunk.keyword_score == 0.05
        assert chunk.metadata["page"] == 10

    def test_chunk_defaults(self):
        """Test retrieved chunk with default values."""
        chunk = RetrievedChunk(
            chunk_id="chunk1",
            document_id="doc1",
            content="Content",
            score=0.8,
        )

        assert chunk.metadata == {}
        assert chunk.vector_score == 0.0
        assert chunk.keyword_score == 0.0
