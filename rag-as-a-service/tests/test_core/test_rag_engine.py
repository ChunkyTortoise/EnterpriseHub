"""Tests for RAG engine orchestration pipeline."""

import pytest
from unittest.mock import AsyncMock

from rag_service.core.rag_engine import (
    RAGEngine,
    RAGResponse,
    SourceReference,
)
from rag_service.core.embedding_service import EmbeddingService
from rag_service.core.retriever import Retriever, RetrievedChunk
from rag_service.core.query_expander import QueryExpander, ExpandedQuery


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = AsyncMock(spec=EmbeddingService)
    service.embed_query = AsyncMock(return_value=[0.1] * 1536)
    return service


@pytest.fixture
def mock_retriever():
    """Mock retriever."""
    retriever = AsyncMock(spec=Retriever)
    return retriever


@pytest.fixture
def mock_query_expander():
    """Mock query expander."""
    expander = AsyncMock(spec=QueryExpander)
    return expander


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="This is a generated answer based on the context.")
    return llm


@pytest.fixture
def rag_engine(mock_embedding_service, mock_retriever, mock_query_expander, mock_llm_client):
    """RAG engine instance with mocks."""
    return RAGEngine(
        embedding_service=mock_embedding_service,
        retriever=mock_retriever,
        query_expander=mock_query_expander,
        llm_client=mock_llm_client,
        rerank_top_k=3,
    )


class TestRAGEngine:
    """Test RAG engine pipeline orchestration."""

    async def test_basic_query_without_expansion(
        self, rag_engine, mock_retriever, mock_llm_client
    ):
        """Test basic RAG query without expansion."""
        # Arrange
        chunks = [
            RetrievedChunk(
                chunk_id="chunk1",
                document_id="doc1",
                content="Real estate prices in California are high.",
                score=0.95,
                metadata={"source": "report.pdf"},
            ),
            RetrievedChunk(
                chunk_id="chunk2",
                document_id="doc1",
                content="Market trends show steady growth.",
                score=0.85,
                metadata={"source": "report.pdf"},
            ),
        ]
        mock_retriever.search = AsyncMock(return_value=chunks)

        # Act
        result = await rag_engine.query("What are real estate prices?", expand=False)

        # Assert
        assert isinstance(result, RAGResponse)
        assert result.answer == "This is a generated answer based on the context."
        assert len(result.sources) == 2
        assert result.sources[0].chunk_id == "chunk1"
        # Score boosted by reranker: 3 overlapping terms * 0.01 = 0.03
        assert result.sources[0].score == pytest.approx(0.98, abs=0.01)
        assert result.latency_ms >= 0
        assert result.metadata["expanded_queries"] == 1
        mock_llm_client.generate.assert_called_once()

    async def test_query_with_expansion(
        self, rag_engine, mock_query_expander, mock_retriever, mock_embedding_service
    ):
        """Test RAG query with multi-query expansion."""
        # Arrange
        mock_query_expander.expand = AsyncMock(
            return_value=ExpandedQuery(
                original="What is the price?",
                expansions=[
                    "What is the price?",
                    "How much does it cost?",
                    "What is the cost?",
                ],
                method="multi_query",
            )
        )

        chunks = [
            RetrievedChunk(
                chunk_id=f"chunk{i}",
                document_id="doc1",
                content=f"Content {i}",
                score=0.9 - i * 0.1,
            )
            for i in range(5)
        ]
        mock_retriever.search = AsyncMock(return_value=chunks[:2])

        # Act
        result = await rag_engine.query("What is the price?", expand=True, top_k=5)

        # Assert
        assert result.metadata["expanded_queries"] == 3
        mock_query_expander.expand.assert_called_once()
        assert mock_embedding_service.embed_query.call_count == 3  # 3 expanded queries

    async def test_query_deduplication(self, rag_engine, mock_retriever):
        """Test that duplicate chunks are deduplicated."""
        # Arrange
        duplicate_chunk = RetrievedChunk(
            chunk_id="chunk1",
            document_id="doc1",
            content="Same content",
            score=0.95,
        )
        mock_retriever.search = AsyncMock(
            side_effect=[
                [duplicate_chunk],
                [duplicate_chunk],  # Same chunk returned twice
            ]
        )

        # Mock expansion to return 2 queries
        rag_engine.query_expander.expand = AsyncMock(
            return_value=ExpandedQuery(
                original="test",
                expansions=["test", "test expanded"],
                method="multi_query",
            )
        )

        # Act
        result = await rag_engine.query("test", expand=True)

        # Assert: should only have 1 unique chunk
        assert len(result.sources) == 1
        assert result.sources[0].chunk_id == "chunk1"

    async def test_reranking_with_term_overlap(self, rag_engine, mock_retriever):
        """Test that reranking boosts scores based on term overlap."""
        # Arrange
        chunks = [
            RetrievedChunk(
                chunk_id="chunk1",
                document_id="doc1",
                content="California real estate market",
                score=0.70,
            ),
            RetrievedChunk(
                chunk_id="chunk2",
                document_id="doc1",
                content="Market trends in California",
                score=0.65,
            ),
            RetrievedChunk(
                chunk_id="chunk3",
                document_id="doc1",
                content="Unrelated document content",
                score=0.72,
            ),
        ]
        mock_retriever.search = AsyncMock(return_value=chunks)

        # Act
        result = await rag_engine.query("California real estate market", expand=False)

        # Assert: chunk1 should be boosted to top despite chunk3 having higher initial score
        assert result.sources[0].chunk_id == "chunk1"  # Highest overlap with query

    async def test_fallback_answer_when_no_llm(
        self, mock_embedding_service, mock_retriever, mock_query_expander
    ):
        """Test fallback answer generation when no LLM client."""
        # Arrange
        engine = RAGEngine(
            embedding_service=mock_embedding_service,
            retriever=mock_retriever,
            query_expander=mock_query_expander,
            llm_client=None,  # No LLM
        )
        chunks = [
            RetrievedChunk(
                chunk_id="chunk1",
                document_id="doc1",
                content="This is the relevant content that should be shown.",
                score=0.95,
            )
        ]
        mock_retriever.search = AsyncMock(return_value=chunks)

        # Act
        result = await engine.query("test query", expand=False)

        # Assert
        assert "Based on 1 relevant sources" in result.answer
        assert "This is the relevant content" in result.answer

    async def test_empty_results_handling(self, rag_engine, mock_retriever):
        """Test handling when no chunks are retrieved."""
        # Arrange
        mock_retriever.search = AsyncMock(return_value=[])

        # Act
        result = await rag_engine.query("nonexistent topic", expand=False)

        # Assert
        assert "couldn't find any relevant information" in result.answer
        assert len(result.sources) == 0

    async def test_collection_filter(
        self, rag_engine, mock_retriever, mock_embedding_service
    ):
        """Test querying with collection filter."""
        # Arrange
        collection_id = "col123"
        mock_retriever.search = AsyncMock(
            return_value=[
                RetrievedChunk(
                    chunk_id="chunk1",
                    document_id="doc1",
                    content="Content",
                    score=0.9,
                )
            ]
        )

        # Act
        await rag_engine.query("test", collection_id=collection_id, expand=False)

        # Assert
        call_args = mock_retriever.search.call_args
        assert call_args.kwargs["collection_id"] == collection_id

    async def test_top_k_limiting(self, rag_engine, mock_retriever):
        """Test that rerank_top_k limits returned sources."""
        # Arrange
        chunks = [
            RetrievedChunk(
                chunk_id=f"chunk{i}",
                document_id="doc1",
                content=f"Content {i}",
                score=0.9 - i * 0.05,
            )
            for i in range(10)
        ]
        mock_retriever.search = AsyncMock(return_value=chunks)

        # Act (rerank_top_k is 3 in fixture)
        result = await rag_engine.query("test", expand=False, top_k=10)

        # Assert: should only return top 3 after reranking
        assert len(result.sources) == 3
        assert result.metadata["total_chunks_retrieved"] == 10
        assert result.metadata["reranked_count"] == 3

    async def test_query_stream(self, rag_engine, mock_retriever, mock_query_expander):
        """Test streaming query response."""
        # Arrange
        mock_query_expander.expand = AsyncMock(
            return_value=ExpandedQuery(
                original="test query",
                expansions=["test query"],
                method="multi_query",
            )
        )
        chunks = [
            RetrievedChunk(
                chunk_id="chunk1",
                document_id="doc1",
                content="Content",
                score=0.9,
                metadata={"source": "test.pdf"},
            )
        ]
        mock_retriever.search = AsyncMock(return_value=chunks)

        # Act
        stream_chunks = []
        async for chunk in rag_engine.query_stream("test query"):
            stream_chunks.append(chunk)

        # Assert
        full_response = "".join(stream_chunks)
        assert "This is a generated answer" in full_response
        assert "Sources:" in full_response
        assert "test.pdf" in full_response


class TestSourceReference:
    """Test SourceReference model."""

    def test_source_reference_creation(self):
        """Test creating a source reference."""
        ref = SourceReference(
            chunk_id="chunk1",
            document_id="doc1",
            content="Some content",
            score=0.95,
            metadata={"page": 5},
        )

        assert ref.chunk_id == "chunk1"
        assert ref.document_id == "doc1"
        assert ref.score == 0.95
        assert ref.metadata["page"] == 5

    def test_source_reference_defaults(self):
        """Test source reference with default metadata."""
        ref = SourceReference(
            chunk_id="chunk1",
            document_id="doc1",
            content="Content",
            score=0.9,
        )

        assert ref.metadata == {}
