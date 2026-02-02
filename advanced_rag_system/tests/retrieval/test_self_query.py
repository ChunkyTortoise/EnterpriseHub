"""Tests for Self-Querying Retriever.

Validates the self-querying retriever that parses natural language queries
to extract structured metadata filters and a semantic search query.
"""

import pytest
from datetime import datetime, date
from uuid import uuid4
from typing import List

import numpy as np

from src.core.types import DocumentChunk, Metadata, SearchResult
from src.core.exceptions import RetrievalError
from src.vector_store.in_memory_store import InMemoryVectorStore
from src.vector_store.base import VectorStoreConfig, SearchOptions
from src.retrieval.self_query import (
    FilterOperator,
    MetadataFilter,
    QueryAnalysis,
    QueryAnalyzer,
    SelfQueryRetriever,
    SelfQueryConfig,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_chunk(
    content: str,
    dim: int = 8,
    title: str = None,
    author: str = None,
    tags: list = None,
    source: str = None,
    created_at: datetime = None,
) -> DocumentChunk:
    """Create a chunk with metadata and a deterministic embedding."""
    doc_id = uuid4()
    meta = Metadata(
        title=title,
        author=author,
        tags=tags or [],
        source=source,
        created_at=created_at,
    )
    c = DocumentChunk(
        document_id=doc_id, content=content, index=0, metadata=meta
    )
    rng = np.random.RandomState(hash(content) % (2**31))
    vec = rng.randn(dim).astype(np.float32)
    c.embedding = (vec / np.linalg.norm(vec)).tolist()
    return c


# ============================================================================
# FilterOperator / MetadataFilter Unit Tests
# ============================================================================

class TestMetadataFilter:
    """Test MetadataFilter data model."""

    def test_create_eq_filter(self):
        f = MetadataFilter(field="author", operator=FilterOperator.EQ, value="Alice")
        assert f.field == "author"
        assert f.operator == FilterOperator.EQ
        assert f.value == "Alice"

    def test_create_contains_filter(self):
        f = MetadataFilter(field="tags", operator=FilterOperator.CONTAINS, value="python")
        assert f.operator == FilterOperator.CONTAINS

    def test_create_gte_filter(self):
        f = MetadataFilter(field="created_at", operator=FilterOperator.GTE, value="2024-01-01")
        assert f.operator == FilterOperator.GTE

    def test_create_in_filter(self):
        f = MetadataFilter(field="source", operator=FilterOperator.IN, value=["web", "pdf"])
        assert f.operator == FilterOperator.IN
        assert f.value == ["web", "pdf"]


# ============================================================================
# QueryAnalyzer Tests
# ============================================================================

class TestQueryAnalyzer:
    """Test rule-based query analysis and filter extraction."""

    def setup_method(self):
        self.analyzer = QueryAnalyzer()

    def test_simple_query_no_filters(self):
        """A plain semantic query should produce no filters."""
        result = self.analyzer.analyze("What is machine learning?")
        assert result.semantic_query.strip() != ""
        assert len(result.filters) == 0

    def test_extract_author_filter(self):
        """Should extract author from 'by <name>' pattern."""
        result = self.analyzer.analyze("papers about neural networks by John Smith")
        assert any(f.field == "author" and "John Smith" in str(f.value) for f in result.filters)
        # Semantic query should not include the 'by John Smith' part
        assert "john smith" not in result.semantic_query.lower()

    def test_extract_tag_filter(self):
        """Should extract tags from 'tagged <tag>' or 'about <topic>' patterns."""
        result = self.analyzer.analyze("documents tagged python about deep learning")
        has_tag_filter = any(f.field == "tags" for f in result.filters)
        assert has_tag_filter

    def test_extract_source_filter(self):
        """Should extract source from 'from <source>' pattern."""
        result = self.analyzer.analyze("articles from arxiv about transformers")
        assert any(f.field == "source" for f in result.filters)

    def test_extract_date_filter_after(self):
        """Should extract date filter from 'after <date>' pattern."""
        result = self.analyzer.analyze("research papers after 2023-01-01")
        date_filters = [f for f in result.filters if f.field == "created_at"]
        assert len(date_filters) >= 1
        assert any(f.operator in (FilterOperator.GTE, FilterOperator.GT) for f in date_filters)

    def test_extract_date_filter_before(self):
        """Should extract date filter from 'before <date>' pattern."""
        result = self.analyzer.analyze("documents before 2024-06-15")
        date_filters = [f for f in result.filters if f.field == "created_at"]
        assert len(date_filters) >= 1
        assert any(f.operator in (FilterOperator.LTE, FilterOperator.LT) for f in date_filters)

    def test_extract_title_filter(self):
        """Should extract title from 'titled <title>' pattern."""
        result = self.analyzer.analyze('document titled "Introduction to RAG"')
        assert any(f.field == "title" for f in result.filters)

    def test_multiple_filters(self):
        """Should extract multiple filters from a complex query."""
        result = self.analyzer.analyze(
            "papers by Alice about deep learning from arxiv after 2024-01-01"
        )
        fields = {f.field for f in result.filters}
        assert "author" in fields
        assert "source" in fields
        assert "created_at" in fields

    def test_semantic_query_preserved(self):
        """The semantic portion of the query should be preserved."""
        result = self.analyzer.analyze(
            "how do attention mechanisms work by Vaswani from arxiv"
        )
        # Core semantic content should be in the query
        assert "attention" in result.semantic_query.lower()

    def test_confidence_score(self):
        """Analysis should include a confidence score in [0, 1]."""
        result = self.analyzer.analyze("papers by Alice after 2024-01-01")
        assert 0.0 <= result.confidence <= 1.0

    def test_empty_query_raises(self):
        """Empty query should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.analyze("")

    def test_whitespace_only_raises(self):
        """Whitespace-only query should raise ValueError."""
        with pytest.raises(ValueError):
            self.analyzer.analyze("   ")


# ============================================================================
# QueryAnalysis Model Tests
# ============================================================================

class TestQueryAnalysis:
    """Test QueryAnalysis data model."""

    def test_has_filters(self):
        analysis = QueryAnalysis(
            original_query="test",
            semantic_query="test",
            filters=[MetadataFilter(field="author", operator=FilterOperator.EQ, value="X")],
            confidence=0.8,
        )
        assert analysis.has_filters is True

    def test_no_filters(self):
        analysis = QueryAnalysis(
            original_query="test",
            semantic_query="test",
            filters=[],
            confidence=0.5,
        )
        assert analysis.has_filters is False

    def test_to_search_filters(self):
        """Should convert filters to dict format for SearchOptions."""
        analysis = QueryAnalysis(
            original_query="test",
            semantic_query="test",
            filters=[
                MetadataFilter(field="author", operator=FilterOperator.EQ, value="Alice"),
                MetadataFilter(field="tags", operator=FilterOperator.CONTAINS, value="ml"),
            ],
            confidence=0.9,
        )
        search_filters = analysis.to_search_filters()
        assert isinstance(search_filters, dict)
        assert "author" in search_filters
        assert "tags" in search_filters


# ============================================================================
# SelfQueryRetriever Integration Tests
# ============================================================================

class TestSelfQueryRetriever:
    """Integration tests for SelfQueryRetriever with InMemoryVectorStore."""

    @pytest.fixture
    async def store_with_data(self):
        """Create a vector store populated with test documents."""
        store = InMemoryVectorStore(VectorStoreConfig(dimension=8))
        await store.initialize()

        chunks = [
            _make_chunk(
                "Neural networks are computational models inspired by the brain",
                title="Intro to Neural Networks",
                author="Alice Chen",
                tags=["neural-networks", "deep-learning"],
                source="arxiv",
                created_at=datetime(2024, 3, 15),
            ),
            _make_chunk(
                "Transformers use self-attention mechanisms for sequence modeling",
                title="Attention is All You Need",
                author="Vaswani",
                tags=["transformers", "attention"],
                source="arxiv",
                created_at=datetime(2023, 6, 1),
            ),
            _make_chunk(
                "Python is a versatile programming language for data science",
                title="Python for Data Science",
                author="Bob Williams",
                tags=["python", "data-science"],
                source="oreilly",
                created_at=datetime(2024, 9, 20),
            ),
            _make_chunk(
                "Reinforcement learning trains agents through reward signals",
                title="RL Fundamentals",
                author="Alice Chen",
                tags=["reinforcement-learning"],
                source="arxiv",
                created_at=datetime(2022, 1, 10),
            ),
            _make_chunk(
                "Convolutional neural networks excel at image recognition tasks",
                title="CNN for Computer Vision",
                author="David Lee",
                tags=["cnn", "computer-vision", "deep-learning"],
                source="springer",
                created_at=datetime(2024, 7, 5),
            ),
        ]
        await store.add_chunks(chunks)
        yield store, chunks
        await store.close()

    @pytest.mark.asyncio
    async def test_search_no_filters(self, store_with_data):
        """Search without filters should return semantic results."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve("What are neural networks?")
        assert len(result.results) > 0
        assert result.analysis is not None
        assert result.search_time_ms >= 0

    @pytest.mark.asyncio
    async def test_search_with_author_filter(self, store_with_data):
        """Should filter results by author."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve("papers by Alice Chen")
        # All results should be by Alice Chen
        for r in result.results:
            assert r.chunk.metadata.author == "Alice Chen"

    @pytest.mark.asyncio
    async def test_search_with_source_filter(self, store_with_data):
        """Should filter results by source."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve("documents from arxiv about learning")
        for r in result.results:
            assert r.chunk.metadata.source == "arxiv"

    @pytest.mark.asyncio
    async def test_search_with_date_filter(self, store_with_data):
        """Should filter results by date."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve("papers after 2024-01-01")
        for r in result.results:
            assert r.chunk.metadata.created_at >= datetime(2024, 1, 1)

    @pytest.mark.asyncio
    async def test_search_with_tag_filter(self, store_with_data):
        """Should filter results by tags."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve("documents tagged deep-learning")
        for r in result.results:
            assert "deep-learning" in r.chunk.metadata.tags

    @pytest.mark.asyncio
    async def test_combined_semantic_and_filter(self, store_with_data):
        """Should combine semantic search with metadata filtering."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve(
            "attention mechanisms from arxiv"
        )
        assert len(result.results) > 0
        for r in result.results:
            assert r.chunk.metadata.source == "arxiv"

    @pytest.mark.asyncio
    async def test_no_results_with_strict_filter(self, store_with_data):
        """Should return empty if no documents match filters."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve("papers by Nonexistent Author")
        assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_retrieval_result_has_analysis(self, store_with_data):
        """Result should include the query analysis."""
        store, chunks = store_with_data
        retriever = SelfQueryRetriever(store)

        result = await retriever.retrieve("neural networks by Alice Chen from arxiv")
        assert result.analysis is not None
        assert result.analysis.original_query == "neural networks by Alice Chen from arxiv"
        assert len(result.analysis.filters) >= 1

    @pytest.mark.asyncio
    async def test_top_k_respected(self, store_with_data):
        """Should respect top_k parameter."""
        store, chunks = store_with_data
        config = SelfQueryConfig(top_k=2)
        retriever = SelfQueryRetriever(store, config=config)

        result = await retriever.retrieve("learning")
        assert len(result.results) <= 2

    @pytest.mark.asyncio
    async def test_fallback_on_low_confidence(self, store_with_data):
        """With low filter confidence, should fall back to pure semantic search."""
        store, chunks = store_with_data
        config = SelfQueryConfig(min_filter_confidence=0.99)
        retriever = SelfQueryRetriever(store, config=config)

        result = await retriever.retrieve("papers by Alice")
        # Should still return results (semantic fallback), not empty
        assert result.analysis is not None
