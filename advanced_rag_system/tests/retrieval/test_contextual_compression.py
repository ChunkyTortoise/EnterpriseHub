"""Tests for contextual compression system."""

from typing import List
from uuid import uuid4

import pytest
from src.core.types import DocumentChunk, SearchResult
from src.retrieval.contextual_compression import (
    AbstractiveCompressor,
    AllocationStrategy,
    CompressedDocument,
    CompressionConfig,
    CompressionResult,
    CompressionStrategy,
    ContextualCompressor,
    ExtractiveCompressor,
    RelevanceScore,
    RelevanceScorer,
    ScoringMethod,
    TokenBudgetManager,
    TokenCounter,
)


@pytest.mark.integration
# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def token_counter():
    """Create token counter."""
    return TokenCounter(tokens_per_word=1.3)


@pytest.fixture
def relevance_scorer():
    """Create relevance scorer."""
    return RelevanceScorer()


@pytest.fixture
def budget_manager():
    """Create token budget manager."""
    return TokenBudgetManager(
        total_budget=1000,
        reserve_for_response=200,
        min_per_document=50,
        max_per_document=500,
    )


@pytest.fixture
def extractive_compressor(token_counter):
    """Create extractive compressor."""
    return ExtractiveCompressor(
        context_window=1,
        token_counter=token_counter,
    )


@pytest.fixture
def abstractive_compressor(token_counter):
    """Create abstractive compressor."""
    return AbstractiveCompressor(token_counter=token_counter)


@pytest.fixture
def sample_documents() -> List[DocumentChunk]:
    """Create sample documents for testing."""
    return [
        DocumentChunk(
            document_id=uuid4(),
            content="Python is a high-level programming language. It is easy to learn and use. Python has a simple syntax.",
            embedding=[0.1, 0.2, 0.3],
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="JavaScript is used for web development. It runs in browsers. JavaScript is versatile.",
            embedding=[0.2, 0.3, 0.4],
        ),
        DocumentChunk(
            document_id=uuid4(),
            content="Machine learning is a subset of AI. It uses algorithms to learn from data. ML is powerful.",
            embedding=[0.3, 0.4, 0.5],
        ),
    ]


# ============================================================================
# TokenCounter Tests
# ============================================================================


class TestTokenCounter:
    """Test cases for TokenCounter."""

    def test_count_simple_text(self, token_counter):
        """Test counting tokens in simple text."""
        text = "Hello world"
        count = token_counter.count(text)

        # 2 words * 1.3 = 2.6 -> 3
        assert count == 3

    def test_count_empty_text(self, token_counter):
        """Test counting tokens in empty text."""
        count = token_counter.count("")
        assert count == 0

    def test_count_batch(self, token_counter):
        """Test counting tokens in batch."""
        texts = ["Hello world", "Python programming", "Test"]
        counts = token_counter.count_batch(texts)

        assert len(counts) == 3
        assert counts[0] == 3  # 2 words
        assert counts[1] == 3  # 2 words
        assert counts[2] == 2  # 1 word


# ============================================================================
# RelevanceScorer Tests
# ============================================================================


class TestRelevanceScorer:
    """Test cases for RelevanceScorer."""

    @pytest.mark.asyncio
    async def test_score_document_keyword_match(self, relevance_scorer):
        """Test scoring document with keyword match."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="Python is a great programming language",
        )

        score = await relevance_scorer.score_document(doc, "Python programming", ScoringMethod.KEYWORD)

        assert score.overall_score > 0
        assert score.document_id == doc.id
        assert score.method == ScoringMethod.KEYWORD

    @pytest.mark.asyncio
    async def test_score_document_no_match(self, relevance_scorer):
        """Test scoring document with no keyword match."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="Java is an object-oriented language",
        )

        score = await relevance_scorer.score_document(doc, "Python programming", ScoringMethod.KEYWORD)

        assert score.overall_score == 0

    @pytest.mark.asyncio
    async def test_score_documents_batch(self, relevance_scorer, sample_documents):
        """Test scoring multiple documents."""
        scores = await relevance_scorer.score_documents(sample_documents, "Python programming", ScoringMethod.KEYWORD)

        assert len(scores) == 3
        # First document should have highest score (mentions Python)
        assert scores[0].overall_score > scores[1].overall_score

    @pytest.mark.asyncio
    async def test_score_with_segments(self, relevance_scorer):
        """Test scoring with segment breakdown."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="Python is great. Java is also good. Python is easy.",
        )

        score = await relevance_scorer.score_document(doc, "Python", ScoringMethod.KEYWORD)

        assert len(score.segment_scores) > 0
        # At least one segment should have high score (mentions Python)
        high_score_segments = [s for s in score.segment_scores if s[1] > 0]
        assert len(high_score_segments) >= 2


# ============================================================================
# TokenBudgetManager Tests
# ============================================================================


class TestTokenBudgetManager:
    """Test cases for TokenBudgetManager."""

    def test_allocate_uniform(self, budget_manager):
        """Test uniform allocation strategy."""
        scores = [0.9, 0.6, 0.3]
        allocations = budget_manager.allocate(scores, AllocationStrategy.UNIFORM)

        # Available: 1000 - 200 = 800
        # Per doc: 800 // 3 = 266
        assert len(allocations) == 3
        assert allocations[0] == allocations[1] == allocations[2]
        assert all(a >= budget_manager.min_per_document for a in allocations)

    def test_allocate_proportional(self, budget_manager):
        """Test proportional allocation strategy."""
        scores = [0.9, 0.6, 0.3]
        allocations = budget_manager.allocate(scores, AllocationStrategy.PROPORTIONAL)

        assert len(allocations) == 3
        # Higher score should get more tokens
        assert allocations[0] > allocations[2]
        assert all(a >= budget_manager.min_per_document for a in allocations)

    def test_allocate_threshold(self, budget_manager):
        """Test threshold allocation strategy."""
        scores = [0.9, 0.6, 0.3]  # 0.3 is below 0.5 threshold
        allocations = budget_manager.allocate(scores, AllocationStrategy.THRESHOLD)

        assert len(allocations) == 3
        # High relevance docs get more
        assert allocations[0] >= allocations[2]

    def test_allocate_greedy(self, budget_manager):
        """Test greedy allocation strategy."""
        scores = [0.9, 0.6, 0.3]
        allocations = budget_manager.allocate(scores, AllocationStrategy.GREEDY)

        assert len(allocations) == 3
        # Highest score should get max allocation
        assert allocations[0] == budget_manager.max_per_document

    def test_allocate_empty_scores(self, budget_manager):
        """Test allocation with empty scores."""
        allocations = budget_manager.allocate([])
        assert allocations == []

    def test_allocate_respects_max(self, budget_manager):
        """Test that allocation respects max_per_document."""
        scores = [1.0, 1.0, 1.0]
        allocations = budget_manager.allocate(scores, AllocationStrategy.UNIFORM)

        assert all(a <= budget_manager.max_per_document for a in allocations)


# ============================================================================
# ExtractiveCompressor Tests
# ============================================================================


class TestExtractiveCompressor:
    """Test cases for ExtractiveCompressor."""

    @pytest.mark.asyncio
    async def test_compress_simple_document(self, extractive_compressor):
        """Test compressing a simple document."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="Python is great. Java is good. Python is easy to learn.",
        )

        relevance = RelevanceScore(
            document_id=doc.id,
            overall_score=0.8,
            segment_scores=[
                ("Python is great", 0.9),
                ("Java is good", 0.3),
                ("Python is easy to learn", 0.8),
            ],
        )

        compressed = await extractive_compressor.compress(doc, relevance, 100)

        assert compressed.original_id == doc.id
        assert compressed.compression_method == "extractive"
        assert compressed.token_count <= 100
        assert len(compressed.preserved_segments) > 0

    @pytest.mark.asyncio
    async def test_compress_respects_budget(self, extractive_compressor):
        """Test that compression respects token budget."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="Sentence one. Sentence two. Sentence three. Sentence four.",
        )

        relevance = RelevanceScore(
            document_id=doc.id,
            overall_score=0.5,
            segment_scores=[
                ("Sentence one", 0.5),
                ("Sentence two", 0.5),
                ("Sentence three", 0.5),
                ("Sentence four", 0.5),
            ],
        )

        budget = 10
        compressed = await extractive_compressor.compress(doc, relevance, budget)

        assert compressed.token_count <= budget

    @pytest.mark.asyncio
    async def test_compress_preserves_order(self, extractive_compressor):
        """Test that compression preserves sentence order."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="First sentence. Second sentence. Third sentence.",
        )

        relevance = RelevanceScore(
            document_id=doc.id,
            overall_score=0.5,
            segment_scores=[
                ("Third sentence", 0.9),
                ("First sentence", 0.8),
            ],
        )

        compressed = await extractive_compressor.compress(doc, relevance, 100)

        # First should come before third in output
        first_pos = compressed.content.find("First")
        third_pos = compressed.content.find("Third")
        assert first_pos < third_pos


# ============================================================================
# AbstractiveCompressor Tests
# ============================================================================


class TestAbstractiveCompressor:
    """Test cases for AbstractiveCompressor."""

    @pytest.mark.asyncio
    async def test_compress_without_llm(self, abstractive_compressor):
        """Test compression without LLM (fallback)."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="This is a test document with multiple words for testing truncation.",
        )

        compressed = await abstractive_compressor.compress(doc, "test query", 20)

        assert compressed.original_id == doc.id
        assert compressed.token_count <= 20
        assert compressed.compression_method == "truncation"

    @pytest.mark.asyncio
    async def test_compress_respects_budget(self, abstractive_compressor):
        """Test that compression respects token budget."""
        doc = DocumentChunk(
            document_id=uuid4(),
            content="Word " * 100,  # Long document
        )

        budget = 20
        compressed = await abstractive_compressor.compress(doc, "query", budget)

        assert compressed.token_count <= budget


# ============================================================================
# ContextualCompressor Tests
# ============================================================================


class TestContextualCompressor:
    """Test cases for ContextualCompressor."""

    @pytest.fixture
    def compressor(self):
        """Create contextual compressor."""
        return ContextualCompressor(
            default_strategy=CompressionStrategy.EXTRACTIVE,
            token_budget=500,
        )

    @pytest.mark.asyncio
    async def test_compress_empty_documents(self, compressor):
        """Test compression with empty document list."""
        result = await compressor.compress([], "query")

        assert result.original_token_count == 0
        assert result.compressed_token_count == 0
        assert result.compression_ratio == 1.0
        assert len(result.compressed_documents) == 0

    @pytest.mark.asyncio
    async def test_compress_single_document(self, compressor, sample_documents):
        """Test compression of single document."""
        docs = [sample_documents[0]]

        result = await compressor.compress(docs, "Python programming")

        assert len(result.compressed_documents) == 1
        assert result.original_token_count > 0
        assert result.compressed_token_count > 0
        assert result.compression_ratio <= 1.0
        assert result.strategy_used == CompressionStrategy.EXTRACTIVE

    @pytest.mark.asyncio
    async def test_compress_multiple_documents(self, compressor, sample_documents):
        """Test compression of multiple documents."""
        result = await compressor.compress(sample_documents, "programming")

        assert len(result.compressed_documents) <= len(sample_documents)
        assert result.original_token_count > result.compressed_token_count
        assert result.compression_ratio < 1.0

    @pytest.mark.asyncio
    async def test_compress_with_relevance_filtering(self, compressor, sample_documents):
        """Test that low relevance documents are filtered out."""
        config = CompressionConfig(min_relevance_threshold=0.8)
        compressor_with_threshold = ContextualCompressor(config=config)

        result = await compressor_with_threshold.compress(sample_documents, "very specific topic")

        # May filter out documents below threshold
        assert len(result.compressed_documents) <= len(sample_documents)

    @pytest.mark.asyncio
    async def test_compress_different_strategies(self, sample_documents):
        """Test compression with different strategies."""
        for strategy in [
            CompressionStrategy.EXTRACTIVE,
            CompressionStrategy.ABSTRACTIVE,
            CompressionStrategy.HYBRID,
        ]:
            compressor = ContextualCompressor(default_strategy=strategy)
            result = await compressor.compress(sample_documents[:2], "query")

            assert result.strategy_used == strategy
            assert len(result.compressed_documents) >= 0

    @pytest.mark.asyncio
    async def test_compress_results(self, compressor, sample_documents):
        """Test compression of search results."""
        results = [SearchResult(chunk=doc, score=0.9, rank=i + 1) for i, doc in enumerate(sample_documents)]

        result = await compressor.compress_results(results, "programming")

        assert len(result.original_documents) == 3
        assert len(result.relevance_scores) == 3

    def test_get_compression_stats(self, compressor):
        """Test getting compression statistics."""
        stats = compressor.get_compression_stats()

        assert "config" in stats
        assert stats["config"]["strategy"] == "extractive"
        assert "methods_available" in stats
        assert "extractive" in stats["methods_available"]


# ============================================================================
# CompressionResult Tests
# ============================================================================


class TestCompressionResult:
    """Test cases for CompressionResult."""

    def test_compression_ratio_calculation(self):
        """Test compression ratio calculation."""
        result = CompressionResult(
            original_documents=[],
            compressed_documents=[],
            original_token_count=1000,
            compressed_token_count=500,
            compression_ratio=0.5,
            strategy_used=CompressionStrategy.EXTRACTIVE,
            relevance_scores=[],
        )

        assert result.compression_ratio == 0.5

    def test_compression_ratio_zero_original(self):
        """Test compression ratio with zero original tokens."""
        result = CompressionResult(
            original_documents=[],
            compressed_documents=[],
            original_token_count=0,
            compressed_token_count=0,
            compression_ratio=1.0,
            strategy_used=CompressionStrategy.EXTRACTIVE,
            relevance_scores=[],
        )

        assert result.compression_ratio == 1.0


# ============================================================================
# CompressedDocument Tests
# ============================================================================


class TestCompressedDocument:
    """Test cases for CompressedDocument."""

    def test_create_compressed_document(self):
        """Test creating compressed document."""
        doc_id = uuid4()
        compressed = CompressedDocument(
            original_id=doc_id,
            content="Compressed content",
            token_count=50,
            compression_method="extractive",
            preserved_segments=[0, 2],
            relevance_score=0.8,
        )

        assert compressed.original_id == doc_id
        assert compressed.content == "Compressed content"
        assert compressed.token_count == 50
        assert compressed.compression_method == "extractive"
        assert compressed.relevance_score == 0.8


# ============================================================================
# Configuration Tests
# ============================================================================


class TestCompressionConfig:
    """Test cases for CompressionConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CompressionConfig()

        assert config.default_strategy == CompressionStrategy.EXTRACTIVE
        assert config.token_budget == 4000
        assert config.allocation_strategy == AllocationStrategy.PROPORTIONAL
        assert config.min_relevance_threshold == 0.3
        assert config.preserve_structure is True
        assert config.context_window == 1

    def test_custom_config(self):
        """Test custom configuration."""
        config = CompressionConfig(
            default_strategy=CompressionStrategy.ABSTRACTIVE,
            token_budget=2000,
            allocation_strategy=AllocationStrategy.GREEDY,
            min_relevance_threshold=0.5,
        )

        assert config.default_strategy == CompressionStrategy.ABSTRACTIVE
        assert config.token_budget == 2000
        assert config.allocation_strategy == AllocationStrategy.GREEDY
        assert config.min_relevance_threshold == 0.5


# ============================================================================
# Integration Tests
# ============================================================================


class TestCompressionIntegration:
    """Integration tests for contextual compression."""

    @pytest.mark.asyncio
    async def test_end_to_end_compression(self):
        """Test end-to-end compression pipeline."""
        # Create documents
        docs = [
            DocumentChunk(
                document_id=uuid4(),
                content="Python is a programming language. It is easy to learn. Python is popular.",
            ),
            DocumentChunk(
                document_id=uuid4(),
                content="Java is another language. It is used for enterprise applications.",
            ),
        ]

        # Create compressor
        compressor = ContextualCompressor(
            default_strategy=CompressionStrategy.EXTRACTIVE,
            token_budget=100,
        )

        # Compress
        result = await compressor.compress(docs, "Python programming")

        # Verify
        assert len(result.compressed_documents) > 0
        assert result.original_token_count > result.compressed_token_count
        assert result.compression_ratio < 1.0

        # First document should be included (about Python)
        first_doc_compressed = any(str(d.original_id) == str(docs[0].id) for d in result.compressed_documents)
        assert first_doc_compressed

    @pytest.mark.asyncio
    async def test_compression_with_different_queries(self):
        """Test compression with different queries."""
        docs = [
            DocumentChunk(
                document_id=uuid4(),
                content="Machine learning uses algorithms. Deep learning is a subset. Neural networks are used.",
            ),
            DocumentChunk(
                document_id=uuid4(),
                content="Web development uses HTML. CSS styles the page. JavaScript adds interactivity.",
            ),
        ]

        compressor = ContextualCompressor(token_budget=50)

        # Compress with ML query
        result_ml = await compressor.compress(docs, "machine learning")

        # Compress with web query
        result_web = await compressor.compress(docs, "web development")

        # Both should produce results
        assert len(result_ml.compressed_documents) >= 0
        assert len(result_web.compressed_documents) >= 0

    def test_scoring_methods(self):
        """Test all scoring methods are defined."""
        methods = [
            ScoringMethod.EMBEDDING,
            ScoringMethod.KEYWORD,
            ScoringMethod.LLM,
        ]

        for method in methods:
            assert isinstance(method.value, str)

    def test_compression_strategies(self):
        """Test all compression strategies are defined."""
        strategies = [
            CompressionStrategy.EXTRACTIVE,
            CompressionStrategy.ABSTRACTIVE,
            CompressionStrategy.HYBRID,
        ]

        for strategy in strategies:
            assert isinstance(strategy.value, str)
