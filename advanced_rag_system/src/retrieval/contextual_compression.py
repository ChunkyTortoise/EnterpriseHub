"""Contextual compression for retrieved documents.

This module provides functionality to compress retrieved documents based on
query relevance, reducing token count while preserving important information.
It supports both extractive (selecting relevant parts) and abstractive
(summarizing) compression strategies.

Example:
    ```python
    compressor = ContextualCompressor(
        llm_client=openai_client,
        default_strategy=CompressionStrategy.EXTRACTIVE,
        token_budget=4000,
    )

    # Compress search results
    result = await compressor.compress(
        documents=search_results,
        query="What are the benefits of Python?",
        strategy=CompressionStrategy.EXTRACTIVE,
    )

    print(f"Compression ratio: {result.compression_ratio:.2%}")
    print(f"Compressed content: {result.compressed_documents[0].content}")
    ```
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from uuid import UUID

from src.core.types import DocumentChunk, SearchResult

logger = logging.getLogger(__name__)


class CompressionStrategy(Enum):
    """Compression strategies available."""

    EXTRACTIVE = "extractive"  # Select relevant sentences
    ABSTRACTIVE = "abstractive"  # Generate summary
    HYBRID = "hybrid"  # Combine both approaches


class ScoringMethod(Enum):
    """Methods for scoring relevance."""

    EMBEDDING = "embedding"  # Cosine similarity
    KEYWORD = "keyword"  # Keyword overlap
    LLM = "llm"  # LLM-based scoring


class AllocationStrategy(Enum):
    """Token budget allocation strategies."""

    UNIFORM = "uniform"  # Equal budget for all
    PROPORTIONAL = "proportional"  # Based on relevance
    THRESHOLD = "threshold"  # Minimum for high relevance
    GREEDY = "greedy"  # Fill with highest relevance first


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class RelevanceScore:
    """Relevance score for a document or segment.

    Attributes:
        document_id: Document identifier
        overall_score: Overall relevance score (0.0 to 1.0)
        segment_scores: Scores for individual segments
        method: Scoring method used
    """

    document_id: UUID
    overall_score: float
    segment_scores: List[Tuple[str, float]] = field(default_factory=list)
    method: ScoringMethod = ScoringMethod.KEYWORD


@dataclass
class SegmentScore:
    """Score for a document segment.

    Attributes:
        text: Segment text
        score: Relevance score
        index: Position in document
    """

    text: str
    score: float
    index: int = 0


@dataclass
class CompressedDocument:
    """A compressed document.

    Attributes:
        original_id: Original document ID
        content: Compressed content
        token_count: Number of tokens in compressed content
        compression_method: Method used for compression
        preserved_segments: References to original segments
        relevance_score: Relevance score used for compression
    """

    original_id: UUID
    content: str
    token_count: int
    compression_method: str
    preserved_segments: List[int] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class CompressionResult:
    """Result of compression operation.

    Attributes:
        original_documents: Original documents
        compressed_documents: Compressed documents
        original_token_count: Total tokens in originals
        compressed_token_count: Total tokens in compressed
        compression_ratio: Ratio of compressed to original
        strategy_used: Compression strategy used
        relevance_scores: Scores used for compression
    """

    original_documents: List[DocumentChunk]
    compressed_documents: List[CompressedDocument]
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    strategy_used: CompressionStrategy
    relevance_scores: List[RelevanceScore]


@dataclass
class CompressionConfig:
    """Configuration for compression.

    Attributes:
        default_strategy: Default compression strategy
        token_budget: Total token budget
        allocation_strategy: How to allocate budget across documents
        min_relevance_threshold: Minimum relevance to include
        preserve_structure: Whether to preserve document structure
        context_window: Context sentences around selected segments
    """

    default_strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE
    token_budget: int = 4000
    allocation_strategy: AllocationStrategy = AllocationStrategy.PROPORTIONAL
    min_relevance_threshold: float = 0.3
    preserve_structure: bool = True
    context_window: int = 1


# ============================================================================
# Token Counter
# ============================================================================


class TokenCounter:
    """Simple token counter using word-based approximation.

    For production, this should use the actual tokenizer used by the LLM.
    """

    def __init__(self, tokens_per_word: float = 1.3) -> None:
        """Initialize token counter.

        Args:
            tokens_per_word: Approximate tokens per word
        """
        self.tokens_per_word = tokens_per_word

    def count(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        words = len(text.split())
        return int(words * self.tokens_per_word)

    def count_batch(self, texts: List[str]) -> List[int]:
        """Count tokens for multiple texts.

        Args:
            texts: Texts to count

        Returns:
            List of token counts
        """
        return [self.count(t) for t in texts]


# ============================================================================
# Relevance Scorer
# ============================================================================


class RelevanceScorer:
    """Scores document relevance to a query.

    Supports multiple scoring methods:
    - Embedding similarity (cosine)
    - Keyword overlap
    - LLM-based scoring

    Example:
        ```python
        scorer = RelevanceScorer()
        score = await scorer.score_document(
            document=doc,
            query="Python benefits",
            method=ScoringMethod.KEYWORD,
        )
        ```
    """

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize relevance scorer.

        Args:
            llm_client: Optional LLM client for LLM-based scoring
        """
        self.llm_client = llm_client

    async def score_document(
        self,
        document: DocumentChunk,
        query: str,
        method: ScoringMethod = ScoringMethod.KEYWORD,
    ) -> RelevanceScore:
        """Score a single document.

        Args:
            document: Document to score
            query: Query string
            method: Scoring method

        Returns:
            Relevance score
        """
        if method == ScoringMethod.KEYWORD:
            return self._keyword_score(document, query)
        elif method == ScoringMethod.EMBEDDING:
            return await self._embedding_score(document, query)
        elif method == ScoringMethod.LLM:
            return await self._llm_score(document, query)
        else:
            return self._keyword_score(document, query)

    async def score_documents(
        self,
        documents: List[DocumentChunk],
        query: str,
        method: ScoringMethod = ScoringMethod.KEYWORD,
    ) -> List[RelevanceScore]:
        """Score multiple documents.

        Args:
            documents: Documents to score
            query: Query string
            method: Scoring method

        Returns:
            List of relevance scores
        """
        scores = []
        for doc in documents:
            score = await self.score_document(doc, query, method)
            scores.append(score)
        return scores

    def _keyword_score(
        self,
        document: DocumentChunk,
        query: str,
    ) -> RelevanceScore:
        """Calculate keyword-based relevance score."""
        query_words = set(query.lower().split())
        doc_words = set(document.content.lower().split())

        # Calculate overlap
        if not query_words:
            overlap = 0.0
        else:
            overlap = len(query_words & doc_words) / len(query_words)

        # Score segments
        segment_scores = self._score_segments(document.content, query_words)

        return RelevanceScore(
            document_id=document.id,
            overall_score=overlap,
            segment_scores=segment_scores,
            method=ScoringMethod.KEYWORD,
        )

    def _score_segments(
        self,
        content: str,
        query_words: set,
    ) -> List[Tuple[str, float]]:
        """Score individual segments (sentences) of content."""
        sentences = re.split(r'[.!?]+', content)
        scores = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_words = set(sentence.lower().split())
            if not query_words:
                score = 0.0
            else:
                score = len(query_words & sentence_words) / len(query_words)

            scores.append((sentence, score))

        return scores

    async def _embedding_score(
        self,
        document: DocumentChunk,
        query: str,
    ) -> RelevanceScore:
        """Calculate embedding-based relevance score."""
        # Placeholder for embedding-based scoring
        # In production, use actual embedding similarity
        if document.embedding:
            # Would calculate cosine similarity here
            score = 0.5  # Placeholder
        else:
            score = 0.0

        return RelevanceScore(
            document_id=document.id,
            overall_score=score,
            method=ScoringMethod.EMBEDDING,
        )

    async def _llm_score(
        self,
        document: DocumentChunk,
        query: str,
    ) -> RelevanceScore:
        """Calculate LLM-based relevance score."""
        # Placeholder for LLM-based scoring
        # Would ask LLM to rate relevance 1-10
        score = 0.5  # Placeholder

        return RelevanceScore(
            document_id=document.id,
            overall_score=score,
            method=ScoringMethod.LLM,
        )


# ============================================================================
# Token Budget Manager
# ============================================================================


class TokenBudgetManager:
    """Manages token budget allocation across documents.

    Allocates tokens based on relevance scores and configured strategy.

    Example:
        ```python
        manager = TokenBudgetManager(total_budget=4000)
        allocations = manager.allocate(
            scores=[0.9, 0.6, 0.3],
            strategy=AllocationStrategy.PROPORTIONAL,
        )
        # allocations = [1800, 1200, 600] (proportional to scores)
        ```
    """

    def __init__(
        self,
        total_budget: int = 4000,
        reserve_for_response: int = 1000,
        min_per_document: int = 100,
        max_per_document: int = 2000,
    ) -> None:
        """Initialize token budget manager.

        Args:
            total_budget: Total token budget
            reserve_for_response: Tokens to reserve for response
            min_per_document: Minimum tokens per document
            max_per_document: Maximum tokens per document
        """
        self.total_budget = total_budget
        self.reserve_for_response = reserve_for_response
        self.min_per_document = min_per_document
        self.max_per_document = max_per_document
        self.token_counter = TokenCounter()

    def allocate(
        self,
        scores: List[float],
        strategy: AllocationStrategy = AllocationStrategy.PROPORTIONAL,
    ) -> List[int]:
        """Allocate token budget across documents.

        Args:
            scores: Relevance scores for each document
            strategy: Allocation strategy

        Returns:
            Token allocations for each document
        """
        available = self.total_budget - self.reserve_for_response
        n = len(scores)

        if n == 0:
            return []

        if strategy == AllocationStrategy.UNIFORM:
            return self._uniform_allocation(available, n)
        elif strategy == AllocationStrategy.PROPORTIONAL:
            return self._proportional_allocation(available, scores)
        elif strategy == AllocationStrategy.THRESHOLD:
            return self._threshold_allocation(available, scores)
        elif strategy == AllocationStrategy.GREEDY:
            return self._greedy_allocation(available, scores)
        else:
            return self._proportional_allocation(available, scores)

    def _uniform_allocation(self, available: int, n: int) -> List[int]:
        """Allocate budget uniformly."""
        per_doc = available // n
        per_doc = max(per_doc, self.min_per_document)
        per_doc = min(per_doc, self.max_per_document)
        return [per_doc] * n

    def _proportional_allocation(
        self,
        available: int,
        scores: List[float],
    ) -> List[int]:
        """Allocate budget proportional to scores."""
        total_score = sum(scores)
        if total_score == 0:
            return self._uniform_allocation(available, len(scores))

        allocations = []
        for score in scores:
            alloc = int((score / total_score) * available)
            alloc = max(alloc, self.min_per_document)
            alloc = min(alloc, self.max_per_document)
            allocations.append(alloc)

        return allocations

    def _threshold_allocation(
        self,
        available: int,
        scores: List[float],
    ) -> List[int]:
        """Allocate based on threshold."""
        threshold = 0.5
        high_relevance = [s for s in scores if s >= threshold]

        if not high_relevance:
            return self._uniform_allocation(available, len(scores))

        per_doc = available // len(high_relevance)
        per_doc = max(per_doc, self.min_per_document)
        per_doc = min(per_doc, self.max_per_document)

        return [
            per_doc if s >= threshold else self.min_per_document
            for s in scores
        ]

    def _greedy_allocation(
        self,
        available: int,
        scores: List[float],
    ) -> List[int]:
        """Allocate greedily to highest relevance first."""
        # Sort by score descending
        indexed_scores = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )

        allocations = [0] * len(scores)
        remaining = available

        for idx, score in indexed_scores:
            if remaining <= 0:
                break

            alloc = min(self.max_per_document, remaining)
            alloc = max(alloc, self.min_per_document)
            allocations[idx] = alloc
            remaining -= alloc

        return allocations


# ============================================================================
# Extractive Compressor
# ============================================================================


class ExtractiveCompressor:
    """Extractive compression - selects most relevant sentences.

    Preserves original text by selecting the most relevant sentences
    based on relevance scores.

    Example:
        ```python
        compressor = ExtractiveCompressor()
        compressed = await compressor.compress(
            document=doc,
            query="Python benefits",
            token_budget=500,
        )
        ```
    """

    def __init__(
        self,
        context_window: int = 1,
        token_counter: Optional[TokenCounter] = None,
    ) -> None:
        """Initialize extractive compressor.

        Args:
            context_window: Sentences to include around selected ones
            token_counter: Token counter instance
        """
        self.context_window = context_window
        self.token_counter = token_counter or TokenCounter()

    async def compress(
        self,
        document: DocumentChunk,
        relevance_score: RelevanceScore,
        token_budget: int,
    ) -> CompressedDocument:
        """Compress document using extractive method.

        Args:
            document: Document to compress
            relevance_score: Relevance scores for document
            token_budget: Maximum tokens for compressed document

        Returns:
            Compressed document
        """
        # Get sentences with scores
        sentences = relevance_score.segment_scores

        # Sort by score descending
        sentences.sort(key=lambda x: x[1], reverse=True)

        # Select sentences within budget
        selected_indices = set()
        current_tokens = 0

        for sentence, score in sentences:
            if current_tokens >= token_budget:
                break

            # Find sentence index
            idx = self._find_sentence_index(document.content, sentence)
            if idx is None:
                continue

            # Add context window
            for ctx_idx in range(
                max(0, idx - self.context_window),
                min(len(sentences), idx + self.context_window + 1),
            ):
                if ctx_idx not in selected_indices:
                    ctx_sentence = self._get_sentence_at_index(
                        document.content, ctx_idx
                    )
                    if ctx_sentence:
                        tokens = self.token_counter.count(ctx_sentence)
                        if current_tokens + tokens <= token_budget:
                            selected_indices.add(ctx_idx)
                            current_tokens += tokens

        # Sort indices to preserve order
        selected_indices = sorted(selected_indices)

        # Build compressed content
        compressed_content = self._build_content(document.content, selected_indices)

        return CompressedDocument(
            original_id=document.id,
            content=compressed_content,
            token_count=current_tokens,
            compression_method="extractive",
            preserved_segments=selected_indices,
            relevance_score=relevance_score.overall_score,
        )

    def _find_sentence_index(self, content: str, sentence: str) -> Optional[int]:
        """Find the index of a sentence in content."""
        sentences = re.split(r'[.!?]+', content)
        for i, s in enumerate(sentences):
            if sentence.strip() in s.strip():
                return i
        return None

    def _get_sentence_at_index(self, content: str, index: int) -> Optional[str]:
        """Get sentence at specific index."""
        sentences = re.split(r'[.!?]+', content)
        if 0 <= index < len(sentences):
            return sentences[index].strip()
        return None

    def _build_content(self, content: str, indices: List[int]) -> str:
        """Build compressed content from selected indices."""
        sentences = re.split(r'[.!?]+', content)
        selected = [sentences[i].strip() for i in indices if i < len(sentences)]
        return ". ".join(selected) + "." if selected else ""


# ============================================================================
# Abstractive Compressor
# ============================================================================


class AbstractiveCompressor:
    """Abstractive compression - generates summaries.

    Uses LLM to generate concise summaries of documents focused on
    query-relevant information.

    Example:
        ```python
        compressor = AbstractiveCompressor(llm_client=openai_client)
        compressed = await compressor.compress(
            document=doc,
            query="Python benefits",
            token_budget=200,
        )
        ```
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        token_counter: Optional[TokenCounter] = None,
    ) -> None:
        """Initialize abstractive compressor.

        Args:
            llm_client: LLM client for summarization
            token_counter: Token counter instance
        """
        self.llm_client = llm_client
        self.token_counter = token_counter or TokenCounter()

    async def compress(
        self,
        document: DocumentChunk,
        query: str,
        token_budget: int,
    ) -> CompressedDocument:
        """Compress document using abstractive method.

        Args:
            document: Document to compress
            query: Query string for context
            token_budget: Maximum tokens for summary

        Returns:
            Compressed document
        """
        if not self.llm_client:
            # Fallback to extractive if no LLM
            logger.warning("No LLM client available - returning truncated content")
            return self._fallback_compress(document, token_budget)

        try:
            summary = await self._generate_summary(
                document.content,
                query,
                token_budget,
            )

            return CompressedDocument(
                original_id=document.id,
                content=summary,
                token_count=self.token_counter.count(summary),
                compression_method="abstractive",
                preserved_segments=[],
                relevance_score=1.0,
            )
        except Exception as e:
            logger.error(f"Abstractive compression failed: {e}")
            return self._fallback_compress(document, token_budget)

    async def _generate_summary(
        self,
        content: str,
        query: str,
        max_tokens: int,
    ) -> str:
        """Generate summary using LLM."""
        # Placeholder for LLM summarization
        # In production, would call LLM with appropriate prompt
        prompt = f"""Summarize the following text focusing on information relevant to: {query}

Text:
{content[:2000]}  # Truncate for prompt

Provide a concise summary in {max_tokens} tokens or less."""

        # Return truncated content as placeholder
        words = content.split()[:max_tokens]
        return " ".join(words) + "..."

    def _fallback_compress(
        self,
        document: DocumentChunk,
        token_budget: int,
    ) -> CompressedDocument:
        """Fallback compression by truncation."""
        words = document.content.split()
        max_words = int(token_budget / 1.3)  # Approximate
        truncated = " ".join(words[:max_words])

        return CompressedDocument(
            original_id=document.id,
            content=truncated,
            token_count=self.token_counter.count(truncated),
            compression_method="truncation",
            preserved_segments=[],
            relevance_score=0.5,
        )


# ============================================================================
# Contextual Compressor
# ============================================================================


class ContextualCompressor:
    """Main contextual compression class.

    Orchestrates the compression pipeline including:
    - Relevance scoring
    - Token budget management
    - Compression strategy selection
    - Document compression

    Example:
        ```python
        compressor = ContextualCompressor(
            llm_client=openai_client,
            default_strategy=CompressionStrategy.EXTRACTIVE,
            token_budget=4000,
        )

        result = await compressor.compress(
            documents=search_results,
            query="What are Python benefits?",
            strategy=CompressionStrategy.EXTRACTIVE,
        )

        print(f"Compressed {result.original_token_count} to {result.compressed_token_count} tokens")
        ```
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        default_strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE,
        token_budget: int = 4000,
        config: Optional[CompressionConfig] = None,
    ) -> None:
        """Initialize contextual compressor.

        Args:
            llm_client: LLM client for abstractive compression
            default_strategy: Default compression strategy
            token_budget: Total token budget
            config: Compression configuration
        """
        self.config = config or CompressionConfig(
            default_strategy=default_strategy,
            token_budget=token_budget,
        )
        self.llm_client = llm_client
        self.relevance_scorer = RelevanceScorer(llm_client)
        self.budget_manager = TokenBudgetManager(token_budget)
        self.extractive = ExtractiveCompressor(
            context_window=self.config.context_window,
        )
        self.abstractive = AbstractiveCompressor(llm_client)
        self.token_counter = TokenCounter()

    async def compress(
        self,
        documents: List[DocumentChunk],
        query: str,
        strategy: Optional[CompressionStrategy] = None,
    ) -> CompressionResult:
        """Compress documents based on query relevance.

        Args:
            documents: Documents to compress
            query: Query string for relevance scoring
            strategy: Compression strategy (uses default if not specified)

        Returns:
            Compression result with compressed documents
        """
        if not documents:
            return CompressionResult(
                original_documents=[],
                compressed_documents=[],
                original_token_count=0,
                compressed_token_count=0,
                compression_ratio=1.0,
                strategy_used=strategy or self.config.default_strategy,
                relevance_scores=[],
            )

        strategy = strategy or self.config.default_strategy

        # Score relevance
        relevance_scores = await self.relevance_scorer.score_documents(
            documents, query, ScoringMethod.KEYWORD
        )

        # Calculate original token count
        original_tokens = sum(
            self.token_counter.count(doc.content) for doc in documents
        )

        # Allocate budget
        scores = [s.overall_score for s in relevance_scores]
        allocations = self.budget_manager.allocate(
            scores, self.config.allocation_strategy
        )

        # Compress documents
        compressed_docs = []
        for doc, score, budget in zip(documents, relevance_scores, allocations):
            if score.overall_score < self.config.min_relevance_threshold:
                # Skip low-relevance documents
                continue

            compressed = await self._compress_document(
                doc, score, query, budget, strategy
            )
            compressed_docs.append(compressed)

        # Calculate compressed token count
        compressed_tokens = sum(doc.token_count for doc in compressed_docs)

        # Calculate compression ratio
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        return CompressionResult(
            original_documents=documents,
            compressed_documents=compressed_docs,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            compression_ratio=ratio,
            strategy_used=strategy,
            relevance_scores=relevance_scores,
        )

    async def compress_results(
        self,
        results: List[SearchResult],
        query: str,
        strategy: Optional[CompressionStrategy] = None,
    ) -> CompressionResult:
        """Compress search results.

        Args:
            results: Search results to compress
            query: Query string
            strategy: Compression strategy

        Returns:
            Compression result
        """
        documents = [r.chunk for r in results]
        return await self.compress(documents, query, strategy)

    async def _compress_document(
        self,
        document: DocumentChunk,
        relevance_score: RelevanceScore,
        query: str,
        token_budget: int,
        strategy: CompressionStrategy,
    ) -> CompressedDocument:
        """Compress a single document."""
        if strategy == CompressionStrategy.EXTRACTIVE:
            return await self.extractive.compress(
                document, relevance_score, token_budget
            )
        elif strategy == CompressionStrategy.ABSTRACTIVE:
            return await self.abstractive.compress(document, query, token_budget)
        elif strategy == CompressionStrategy.HYBRID:
            # First extractive, then abstractive
            extracted = await self.extractive.compress(
                document, relevance_score, token_budget
            )
            # Create temporary document for abstractive
            temp_doc = DocumentChunk(
                document_id=document.document_id,
                content=extracted.content,
            )
            return await self.abstractive.compress(
                temp_doc, query, token_budget
            )
        else:
            return await self.extractive.compress(
                document, relevance_score, token_budget
            )

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics.

        Returns:
            Dictionary with compression statistics
        """
        return {
            "config": {
                "strategy": self.config.default_strategy.value,
                "token_budget": self.config.token_budget,
                "allocation_strategy": self.config.allocation_strategy.value,
            },
            "methods_available": [
                "extractive",
                "abstractive",
                "hybrid",
            ],
        }
