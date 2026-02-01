"""Tests for sparse retrieval components including BM25 index.

This module tests the BM25Index implementation with various scenarios
including document indexing, search ranking, and performance benchmarks.
"""

import pytest
from uuid import uuid4
from typing import List

from src.core.types import DocumentChunk, Metadata, SearchResult
from src.retrieval.sparse.bm25_index import BM25Index, BM25Config


class TestBM25Index:
    """Test suite for BM25Index implementation."""

    @pytest.fixture
    def sample_chunks(self) -> List[DocumentChunk]:
        """Create sample document chunks for testing."""
        doc_id = uuid4()
        return [
            DocumentChunk(
                document_id=doc_id,
                content="The quick brown fox jumps over the lazy dog",
                index=0,
                metadata=Metadata(title="Sample Doc 1")
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Python is a powerful programming language for data science",
                index=1,
                metadata=Metadata(title="Sample Doc 2")
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Machine learning algorithms can analyze large datasets quickly",
                index=2,
                metadata=Metadata(title="Sample Doc 3")
            ),
            DocumentChunk(
                document_id=doc_id,
                content="Quick data processing with pandas and numpy libraries",
                index=3,
                metadata=Metadata(title="Sample Doc 4")
            ),
        ]

    @pytest.fixture
    def bm25_index(self, sample_chunks: List[DocumentChunk]) -> BM25Index:
        """Create BM25Index with sample documents."""
        index = BM25Index()
        index.add_documents(sample_chunks)
        return index

    def test_bm25_config_defaults(self):
        """Test BM25Config default values."""
        config = BM25Config()
        assert config.k1 == 1.5
        assert config.b == 0.75
        assert config.top_k == 100

    def test_bm25_config_custom_values(self):
        """Test BM25Config with custom values."""
        config = BM25Config(k1=2.0, b=0.8, top_k=50)
        assert config.k1 == 2.0
        assert config.b == 0.8
        assert config.top_k == 50

    def test_bm25_index_initialization(self):
        """Test BM25Index initialization."""
        index = BM25Index()
        assert index.document_count == 0
        assert len(index.get_corpus()) == 0

    def test_add_single_document(self):
        """Test adding a single document to the index."""
        index = BM25Index()
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test document content",
            index=0
        )

        index.add_documents([chunk])

        assert index.document_count == 1
        corpus = index.get_corpus()
        assert len(corpus) == 1
        assert "test" in corpus[0]
        assert "document" in corpus[0]
        assert "content" in corpus[0]

    def test_add_multiple_documents(self, sample_chunks: List[DocumentChunk]):
        """Test adding multiple documents to the index."""
        index = BM25Index()
        index.add_documents(sample_chunks)

        assert index.document_count == 4
        corpus = index.get_corpus()
        assert len(corpus) == 4

        # Check that text is properly tokenized
        assert "quick" in corpus[0]
        assert "python" in corpus[1]
        assert "machine" in corpus[2]

    def test_search_returns_results(self, bm25_index: BM25Index):
        """Test that search returns SearchResult objects."""
        results = bm25_index.search("quick fox")

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(result, SearchResult) for result in results)

        # Check result structure
        result = results[0]
        assert hasattr(result, 'chunk')
        assert hasattr(result, 'score')
        assert hasattr(result, 'rank')
        assert result.score > 0.0
        assert result.rank >= 1

    def test_search_ranking_relevance(self, bm25_index: BM25Index):
        """Test that search results are ranked by relevance."""
        results = bm25_index.search("quick data")

        # Should return multiple results
        assert len(results) >= 2

        # Results should be ranked by score (descending)
        scores = [result.score for result in results]
        assert scores == sorted(scores, reverse=True)

        # First result should contain "quick" (exact match)
        first_result_content = results[0].chunk.content.lower()
        assert "quick" in first_result_content

    def test_search_with_top_k_limit(self, bm25_index: BM25Index):
        """Test search with top_k parameter."""
        results = bm25_index.search("data", top_k=2)

        assert len(results) <= 2

        if len(results) == 2:
            # Ensure ranking is preserved
            assert results[0].score >= results[1].score

    def test_search_no_matches(self, bm25_index: BM25Index):
        """Test search with query that has no matches."""
        results = bm25_index.search("nonexistent terms xyz")

        # Should return empty list or very low scores
        assert len(results) == 0 or all(result.score < 0.1 for result in results)

    def test_search_empty_query(self, bm25_index: BM25Index):
        """Test search with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            bm25_index.search("")

    def test_search_whitespace_query(self, bm25_index: BM25Index):
        """Test search with whitespace-only query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            bm25_index.search("   \n\t   ")

    def test_add_documents_after_initial_index(self, sample_chunks: List[DocumentChunk]):
        """Test adding documents to existing index."""
        index = BM25Index()
        index.add_documents(sample_chunks[:2])

        initial_count = index.document_count
        assert initial_count == 2

        # Add more documents
        index.add_documents(sample_chunks[2:])

        assert index.document_count == 4
        assert len(index.get_corpus()) == 4

    def test_clear_index(self, bm25_index: BM25Index):
        """Test clearing the index."""
        assert bm25_index.document_count > 0

        bm25_index.clear()

        assert bm25_index.document_count == 0
        assert len(bm25_index.get_corpus()) == 0

    def test_get_document_by_id(self, bm25_index: BM25Index, sample_chunks: List[DocumentChunk]):
        """Test retrieving document by chunk ID."""
        chunk_id = sample_chunks[0].id
        retrieved_chunk = bm25_index.get_document_by_id(chunk_id)

        assert retrieved_chunk is not None
        assert retrieved_chunk.id == chunk_id
        assert retrieved_chunk.content == sample_chunks[0].content

    def test_get_nonexistent_document(self, bm25_index: BM25Index):
        """Test retrieving non-existent document."""
        fake_id = uuid4()
        result = bm25_index.get_document_by_id(fake_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_search_performance(self, bm25_index: BM25Index):
        """Test search performance meets <20ms target."""
        import time

        # Warm up
        bm25_index.search("test query")

        # Measure search time
        start_time = time.perf_counter()
        results = bm25_index.search("machine learning data")
        end_time = time.perf_counter()

        search_time_ms = (end_time - start_time) * 1000

        # Should be under 20ms for small corpus
        assert search_time_ms < 20, f"Search took {search_time_ms:.2f}ms, expected <20ms"

        # Should return reasonable results
        assert len(results) > 0


class TestBM25Integration:
    """Integration tests for BM25 with other components."""

    def test_bm25_with_metadata_filtering(self):
        """Test BM25 integration with metadata-based filtering."""
        # This test will be implemented when metadata filtering is added
        pass

    def test_bm25_corpus_size_scaling(self):
        """Test BM25 performance with larger corpus."""
        # This test will be implemented for performance validation
        pass