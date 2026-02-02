"""Tests for Contextual Compression.

Validates the contextual compression pipeline that extracts the most
relevant portions of retrieved documents relative to a query.
"""

import pytest
from uuid import uuid4
from typing import List

import numpy as np

from src.core.types import DocumentChunk, Metadata, SearchResult
from src.retrieval.contextual_compression import (
    CompressionConfig,
    CompressionStrategy,
    CompressionResult,
    CompressedDocument,
    RelevanceExtractor,
    ContextualCompressor,
    TokenBudgetManager,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_result(content: str, score: float = 0.9, rank: int = 1) -> SearchResult:
    """Create a SearchResult with given content."""
    doc_id = uuid4()
    chunk = DocumentChunk(
        document_id=doc_id,
        content=content,
        index=0,
        metadata=Metadata(),
    )
    return SearchResult(chunk=chunk, score=score, rank=rank, distance=1.0 - score)


def _long_document(topic: str, sentences: int = 10) -> str:
    """Generate a multi-sentence document about a topic."""
    filler = [
        "This section provides background context for the discussion.",
        "Additional details can be found in the referenced literature.",
        "The methodology follows standard research practices.",
        "Several related works have explored similar concepts.",
        "Implementation details are discussed in the appendix.",
        "Performance benchmarks demonstrate the effectiveness.",
        "Future work may extend these findings to new domains.",
        "The results are consistent with theoretical predictions.",
    ]
    relevant = [
        f"{topic} is a key concept in modern computing.",
        f"Recent advances in {topic} have shown significant improvements.",
        f"The application of {topic} has transformed the field.",
    ]
    # Mix relevant and filler sentences
    result_sentences = []
    for i in range(sentences):
        if i % 3 == 0 and relevant:
            result_sentences.append(relevant.pop(0))
        else:
            result_sentences.append(filler[i % len(filler)])
    return " ".join(result_sentences)


# ============================================================================
# RelevanceExtractor Tests
# ============================================================================

class TestRelevanceExtractor:
    """Test sentence-level relevance scoring."""

    def setup_method(self):
        self.extractor = RelevanceExtractor()

    def test_split_sentences(self):
        """Should correctly split text into sentences."""
        text = "First sentence. Second sentence. Third one here."
        sentences = self.extractor.split_sentences(text)
        assert len(sentences) == 3

    def test_split_handles_abbreviations(self):
        """Should not split on common abbreviations."""
        text = "Dr. Smith published the paper. It was about ML."
        sentences = self.extractor.split_sentences(text)
        assert len(sentences) == 2

    def test_score_relevance_high_overlap(self):
        """Sentence with high word overlap should score high."""
        query = "machine learning algorithms"
        sentence = "Machine learning algorithms are widely used in practice."
        score = self.extractor.score_sentence(query, sentence)
        assert score > 0.5

    def test_score_relevance_low_overlap(self):
        """Sentence with no overlap should score low."""
        query = "machine learning algorithms"
        sentence = "The weather today is sunny and warm."
        score = self.extractor.score_sentence(query, sentence)
        assert score < 0.2

    def test_score_is_bounded(self):
        """Score should be in [0, 1]."""
        query = "test query words"
        for sentence in [
            "test query words exactly match",
            "nothing related here",
            "",
            "test",
        ]:
            score = self.extractor.score_sentence(query, sentence)
            assert 0.0 <= score <= 1.0

    def test_extract_relevant_sentences(self):
        """Should return sentences sorted by relevance."""
        query = "neural networks"
        text = (
            "Neural networks are computational models. "
            "The weather is nice today. "
            "Deep neural networks have many layers. "
            "Cats are wonderful pets."
        )
        scored = self.extractor.extract_relevant(query, text, top_k=2)
        assert len(scored) == 2
        # Both should contain 'neural'
        for sentence, score in scored:
            assert "neural" in sentence.lower()

    def test_extract_preserves_order_option(self):
        """Should optionally preserve document order."""
        query = "neural networks"
        text = (
            "First, background context. "
            "Neural networks are key. "
            "More background info. "
            "Deep networks excel."
        )
        scored = self.extractor.extract_relevant(
            query, text, top_k=2, preserve_order=True
        )
        # If order preserved, first relevant sentence should come first
        assert len(scored) == 2

    def test_empty_text(self):
        """Should handle empty text gracefully."""
        scored = self.extractor.extract_relevant("test", "", top_k=5)
        assert scored == []


# ============================================================================
# TokenBudgetManager Tests
# ============================================================================

class TestTokenBudgetManager:
    """Test token budget allocation across documents."""

    def setup_method(self):
        self.manager = TokenBudgetManager()

    def test_estimate_tokens(self):
        """Token estimation should be roughly words * 1.3."""
        text = "This is a simple test sentence with eight words."
        tokens = self.manager.estimate_tokens(text)
        assert 8 <= tokens <= 15  # Roughly word count * 1.3

    def test_allocate_equal_budget(self):
        """Should distribute budget equally when scores are equal."""
        scores = [0.5, 0.5, 0.5]
        budget = 300
        allocations = self.manager.allocate(scores, budget)
        assert len(allocations) == 3
        assert sum(allocations) <= budget
        # Each should get roughly 100
        for a in allocations:
            assert 80 <= a <= 120

    def test_allocate_proportional_to_scores(self):
        """Higher-scored documents should get more budget."""
        scores = [0.9, 0.5, 0.1]
        budget = 300
        allocations = self.manager.allocate(scores, budget)
        assert allocations[0] > allocations[1] > allocations[2]
        assert sum(allocations) <= budget

    def test_allocate_minimum_budget(self):
        """Each document should get at least a minimum allocation."""
        scores = [0.9, 0.01, 0.01]
        budget = 300
        allocations = self.manager.allocate(scores, budget, min_per_doc=50)
        # Even low-scored docs get minimum
        assert all(a >= 50 for a in allocations)

    def test_allocate_empty(self):
        """Empty input should return empty allocations."""
        assert self.manager.allocate([], 100) == []

    def test_allocate_zero_budget(self):
        """Zero budget should return zeros."""
        allocations = self.manager.allocate([0.5, 0.5], 0)
        assert all(a == 0 for a in allocations)


# ============================================================================
# ContextualCompressor Tests
# ============================================================================

class TestContextualCompressor:
    """Test the main contextual compression pipeline."""

    def setup_method(self):
        self.compressor = ContextualCompressor()

    @pytest.mark.asyncio
    async def test_compress_single_document(self):
        """Should compress a single document to relevant sentences."""
        content = _long_document("machine learning", sentences=10)
        results = [_make_result(content, score=0.9, rank=1)]

        config = CompressionConfig(max_tokens=40)
        compressor = ContextualCompressor(config)
        compressed = await compressor.compress(
            "machine learning", results
        )
        assert isinstance(compressed, CompressionResult)
        assert len(compressed.documents) == 1
        assert compressed.compression_ratio < 1.0  # Actually compressed
        assert compressed.documents[0].content != ""

    @pytest.mark.asyncio
    async def test_compress_multiple_documents(self):
        """Should compress multiple documents."""
        results = [
            _make_result(
                _long_document("neural networks", sentences=8),
                score=0.9, rank=1,
            ),
            _make_result(
                _long_document("deep learning", sentences=8),
                score=0.7, rank=2,
            ),
            _make_result(
                _long_document("computer vision", sentences=8),
                score=0.5, rank=3,
            ),
        ]

        config = CompressionConfig(max_tokens=80)
        compressor = ContextualCompressor(config)
        compressed = await compressor.compress("neural networks", results)
        assert len(compressed.documents) == 3
        assert compressed.original_token_count > compressed.compressed_token_count

    @pytest.mark.asyncio
    async def test_compress_respects_token_budget(self):
        """Output should stay within the configured token budget."""
        config = CompressionConfig(max_tokens=100)
        compressor = ContextualCompressor(config)

        results = [
            _make_result(_long_document("AI", sentences=20), score=0.9, rank=1),
        ]
        compressed = await compressor.compress("artificial intelligence", results)
        assert compressed.compressed_token_count <= 120  # Allow small overhead

    @pytest.mark.asyncio
    async def test_compress_empty_results(self):
        """Should handle empty results gracefully."""
        compressed = await self.compressor.compress("test", [])
        assert len(compressed.documents) == 0
        assert compressed.compression_ratio == 1.0
        assert compressed.original_token_count == 0

    @pytest.mark.asyncio
    async def test_compress_preserves_chunk_id(self):
        """Compressed documents should reference their original chunk."""
        result = _make_result("Machine learning is great. Cats are nice.", score=0.9, rank=1)
        compressed = await self.compressor.compress("machine learning", [result])
        assert compressed.documents[0].original_chunk_id == result.chunk.id

    @pytest.mark.asyncio
    async def test_compress_short_document_unchanged(self):
        """Very short documents should pass through mostly unchanged."""
        result = _make_result("Machine learning works well.", score=0.9, rank=1)
        compressed = await self.compressor.compress("machine learning", [result])
        assert len(compressed.documents) == 1
        # Short doc should not lose much content
        assert "machine learning" in compressed.documents[0].content.lower()

    @pytest.mark.asyncio
    async def test_compress_relevance_threshold(self):
        """Sentences below relevance threshold should be dropped."""
        config = CompressionConfig(min_relevance_score=0.5)
        compressor = ContextualCompressor(config)

        content = (
            "Machine learning is a subset of AI. "
            "The weather is sunny. "
            "Cats enjoy sleeping. "
            "ML models learn from data."
        )
        result = _make_result(content, score=0.9, rank=1)
        compressed = await compressor.compress("machine learning", [result])
        doc = compressed.documents[0]
        # Irrelevant sentences about weather and cats should be dropped
        assert "weather" not in doc.content.lower()
        assert "cats" not in doc.content.lower()

    @pytest.mark.asyncio
    async def test_compression_stats(self):
        """Should report accurate compression statistics."""
        results = [
            _make_result(
                _long_document("ML", sentences=10), score=0.9, rank=1
            ),
        ]
        config = CompressionConfig(max_tokens=50)
        compressor = ContextualCompressor(config)

        compressed = await compressor.compress("machine learning", results)
        assert compressed.original_token_count > 0
        assert compressed.compressed_token_count > 0
        assert compressed.compressed_token_count <= compressed.original_token_count
        assert 0.0 < compressed.compression_ratio <= 1.0

    @pytest.mark.asyncio
    async def test_extractive_strategy(self):
        """Extractive strategy should select exact sentences."""
        config = CompressionConfig(strategy=CompressionStrategy.EXTRACTIVE)
        compressor = ContextualCompressor(config)

        content = (
            "Neural networks learn patterns. "
            "The sky is blue. "
            "Deep learning uses neural networks."
        )
        result = _make_result(content, score=0.9, rank=1)
        compressed = await compressor.compress("neural networks", [result])
        doc = compressed.documents[0]
        # Each sentence in output should be an exact sentence from input
        for sent in doc.content.split(". "):
            sent_clean = sent.strip().rstrip(".")
            if sent_clean:
                assert sent_clean in content

    @pytest.mark.asyncio
    async def test_higher_scored_docs_get_more_budget(self):
        """Documents with higher relevance should get more token budget."""
        config = CompressionConfig(max_tokens=200)
        compressor = ContextualCompressor(config)

        results = [
            _make_result(
                _long_document("neural networks", sentences=10),
                score=0.95, rank=1,
            ),
            _make_result(
                _long_document("cooking recipes", sentences=10),
                score=0.3, rank=2,
            ),
        ]
        compressed = await compressor.compress("neural networks", results)
        if len(compressed.documents) == 2:
            # First doc (higher score) should get more tokens
            tokens_0 = compressed.documents[0].token_count
            tokens_1 = compressed.documents[1].token_count
            assert tokens_0 >= tokens_1


# ============================================================================
# CompressedDocument Tests
# ============================================================================

class TestCompressedDocument:
    """Test CompressedDocument data model."""

    def test_create(self):
        chunk_id = uuid4()
        doc = CompressedDocument(
            original_chunk_id=chunk_id,
            content="Compressed content here.",
            token_count=4,
            relevance_score=0.85,
        )
        assert doc.original_chunk_id == chunk_id
        assert doc.token_count == 4
        assert doc.relevance_score == 0.85

    def test_empty_content_allowed(self):
        """A document could be fully filtered out."""
        doc = CompressedDocument(
            original_chunk_id=uuid4(),
            content="",
            token_count=0,
            relevance_score=0.0,
        )
        assert doc.content == ""
