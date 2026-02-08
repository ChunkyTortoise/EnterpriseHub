"""Contextual compression for retrieved documents.

This module provides contextual compression that:
1. Extracts only relevant content from retrieved documents based on the query
2. Achieves 50%+ compression ratio while preserving key information
3. Supports multiple compression strategies (extractive, abstractive, hybrid)
4. Integrates with AdvancedHybridSearcher

Example:
    ```python
    # Compress search results
    compressor = ContextualCompressor(
        token_budget=4000,
        target_compression_ratio=0.5,  # 50% compression
    )

    result = await compressor.compress(
        results=search_results,
        query="What are the benefits of Python?",
        strategy=CompressionStrategy.EXTRACTIVE,
    )

    print(f"Compressed {result.original_token_count} to {result.compressed_token_count} tokens")
    print(f"Compression ratio: {result.compression_ratio:.1%}")

    # Use with AdvancedHybridSearcher
    enhanced_searcher = EnhancedSearcher(
        base_searcher=advanced_hybrid_searcher,
        compressor=compressor,
    )
    compressed_results = await enhanced_searcher.search(
        "What are the benefits of Python?",
        top_k=10,
        compress_results=True,
    )
    ```
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from src.core.types import DocumentChunk, SearchResult
from src.retrieval.advanced_hybrid_searcher import AdvancedHybridSearcher

logger = logging.getLogger(__name__)


class CompressionStrategy(Enum):
    """Compression strategies available."""

    EXTRACTIVE = "extractive"  # Select relevant sentences/paragraphs
    ABSTRACTIVE = "abstractive"  # Generate summary
    HYBRID = "hybrid"  # Extract then summarize


class ScoringMethod(Enum):
    """Methods for scoring relevance."""

    KEYWORD = "keyword"  # Keyword overlap
    EMBEDDING = "embedding"  # Embedding similarity
    POSITION = "position"  # Position-based (early content weighted)


@dataclass
class RelevanceScore:
    """Relevance score for a document segment.

    Attributes:
        segment_index: Index of segment in document
        segment_text: Text of the segment
        score: Relevance score (0.0 to 1.0)
        method: Scoring method used
    """

    segment_index: int
    segment_text: str
    score: float
    method: ScoringMethod


@dataclass
class CompressedDocument:
    """A compressed document with metadata.

    Attributes:
        original_id: Original document ID
        content: Compressed content
        original_content: Original full content
        token_count: Token count of compressed content
        compression_ratio: Ratio of compressed to original
        preserved_segments: Indices of preserved segments
        relevance_score: Overall relevance score
    """

    original_id: UUID
    content: str
    original_content: str
    token_count: int
    compression_ratio: float
    preserved_segments: List[int] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class CompressionResult:
    """Result of compression operation.

    Attributes:
        compressed_documents: List of compressed documents
        original_token_count: Total tokens before compression
        compressed_token_count: Total tokens after compression
        overall_compression_ratio: Overall compression ratio
        strategy_used: Compression strategy used
        query: Query used for compression
    """

    compressed_documents: List[CompressedDocument]
    original_token_count: int
    compressed_token_count: int
    overall_compression_ratio: float
    strategy_used: CompressionStrategy
    query: str

    def is_target_achieved(self, target_ratio: float = 0.5) -> bool:
        """Check if target compression ratio was achieved."""
        return self.overall_compression_ratio <= target_ratio


@dataclass
class CompressionConfig:
    """Configuration for contextual compression.

    Attributes:
        token_budget: Maximum tokens for compressed results
        target_compression_ratio: Target ratio (e.g., 0.5 for 50%)
        min_relevance_threshold: Minimum relevance to include segment
        context_window: Context segments around selected ones
        preserve_structure: Whether to preserve document structure
    """

    token_budget: int = 4000
    target_compression_ratio: float = 0.5
    min_relevance_threshold: float = 0.3
    context_window: int = 1
    preserve_structure: bool = True


# ============================================================================
# Token Counter
# ============================================================================


class TokenCounter:
    """Simple token counter using word-based approximation."""

    def __init__(self, tokens_per_word: float = 1.3) -> None:
        """Initialize token counter.

        Args:
            tokens_per_word: Approximate tokens per word
        """
        self.tokens_per_word = tokens_per_word

    def count(self, text: str) -> int:
        """Count tokens in text."""
        return int(len(text.split()) * self.tokens_per_word)

    def count_batch(self, texts: List[str]) -> List[int]:
        """Count tokens for multiple texts."""
        return [self.count(t) for t in texts]


# ============================================================================
# Relevance Scorer
# ============================================================================


class RelevanceScorer:
    """Scores document segments for relevance to a query."""

    def __init__(self) -> None:
        """Initialize relevance scorer."""
        pass

    def score_segments(
        self,
        content: str,
        query: str,
        method: ScoringMethod = ScoringMethod.KEYWORD,
    ) -> List[RelevanceScore]:
        """Score all segments of a document.

        Args:
            content: Document content
            query: Query string
            method: Scoring method

        Returns:
            List of relevance scores for segments
        """
        segments = self._segment_document(content)

        if method == ScoringMethod.KEYWORD:
            return self._keyword_score(segments, query)
        elif method == ScoringMethod.POSITION:
            return self._position_score(segments)
        else:
            return self._keyword_score(segments, query)

    def _segment_document(self, content: str) -> List[str]:
        """Split document into segments (sentences/paragraphs)."""
        # Try paragraph splitting first
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        if len(paragraphs) >= 3:
            return paragraphs

        # Fall back to sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", content)
        return [s.strip() for s in sentences if s.strip()]

    def _keyword_score(self, segments: List[str], query: str) -> List[RelevanceScore]:
        """Score segments based on keyword overlap."""
        query_words = set(query.lower().split())
        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "and",
            "but",
            "or",
            "yet",
            "so",
            "if",
            "because",
            "although",
            "though",
            "while",
            "where",
            "when",
            "that",
            "which",
            "who",
            "whom",
            "whose",
            "what",
            "this",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "her",
            "its",
            "our",
            "their",
            "mine",
            "yours",
            "hers",
            "ours",
            "theirs",
            "myself",
            "yourself",
            "himself",
            "herself",
            "itself",
            "ourselves",
            "yourselves",
            "themselves",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "than",
            "too",
            "very",
            "just",
            "now",
        }
        query_words = query_words - stop_words

        scores = []
        for i, segment in enumerate(segments):
            segment_words = set(segment.lower().split())

            if not query_words:
                score = 0.5  # Neutral score if no query words
            else:
                overlap = len(query_words & segment_words)
                score = overlap / len(query_words)

            # Boost exact phrase matches
            query_lower = query.lower()
            segment_lower = segment.lower()
            if query_lower in segment_lower:
                score = min(1.0, score + 0.3)

            scores.append(
                RelevanceScore(
                    segment_index=i,
                    segment_text=segment,
                    score=score,
                    method=ScoringMethod.KEYWORD,
                )
            )

        return scores

    def _position_score(self, segments: List[str]) -> List[RelevanceScore]:
        """Score segments based on position (early content weighted)."""
        scores = []
        n = len(segments)

        for i, segment in enumerate(segments):
            # Exponential decay based on position
            position_score = 1.0 * (0.9**i)

            scores.append(
                RelevanceScore(
                    segment_index=i,
                    segment_text=segment,
                    score=position_score,
                    method=ScoringMethod.POSITION,
                )
            )

        return scores


# ============================================================================
# Extractive Compressor
# ============================================================================


class ExtractiveCompressor:
    """Extractive compression - selects most relevant segments."""

    def __init__(
        self,
        config: Optional[CompressionConfig] = None,
        token_counter: Optional[TokenCounter] = None,
    ) -> None:
        """Initialize extractive compressor.

        Args:
            config: Compression configuration
            token_counter: Token counter instance
        """
        self.config = config or CompressionConfig()
        self.token_counter = token_counter or TokenCounter()
        self.scorer = RelevanceScorer()

    async def compress(
        self,
        document: DocumentChunk,
        query: str,
        token_budget: Optional[int] = None,
    ) -> CompressedDocument:
        """Compress document using extractive method.

        Args:
            document: Document to compress
            query: Query for relevance scoring
            token_budget: Optional override for token budget

        Returns:
            Compressed document
        """
        budget = token_budget or self.config.token_budget
        original_tokens = self.token_counter.count(document.content)

        # Score segments
        scores = self.scorer.score_segments(document.content, query, ScoringMethod.KEYWORD)

        # Sort by score descending
        scores.sort(key=lambda s: s.score, reverse=True)

        # Select segments within budget
        selected_indices: Set[int] = set()
        current_tokens = 0

        for score in scores:
            if current_tokens >= budget * self.config.target_compression_ratio:
                break

            if score.score < self.config.min_relevance_threshold:
                continue

            # Add segment
            segment_tokens = self.token_counter.count(score.segment_text)

            if current_tokens + segment_tokens <= budget:
                selected_indices.add(score.segment_index)
                current_tokens += segment_tokens

                # Add context window
                for ctx_idx in range(
                    max(0, score.segment_index - self.config.context_window),
                    min(len(scores), score.segment_index + self.config.context_window + 1),
                ):
                    if ctx_idx not in selected_indices:
                        ctx_text = scores[ctx_idx].segment_text if ctx_idx < len(scores) else ""
                        if ctx_text:
                            ctx_tokens = self.token_counter.count(ctx_text)
                            if current_tokens + ctx_tokens <= budget:
                                selected_indices.add(ctx_idx)
                                current_tokens += ctx_tokens

        # Sort indices to preserve order
        sorted_indices = sorted(selected_indices)

        # Build compressed content
        all_segments = self.scorer._segment_document(document.content)
        compressed_content = self._build_content(all_segments, sorted_indices)

        compressed_tokens = self.token_counter.count(compressed_content)
        compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        return CompressedDocument(
            original_id=document.id,
            content=compressed_content,
            original_content=document.content,
            token_count=compressed_tokens,
            compression_ratio=compression_ratio,
            preserved_segments=sorted_indices,
            relevance_score=max((s.score for s in scores), default=0.0),
        )

    def _build_content(self, segments: List[str], indices: List[int]) -> str:
        """Build compressed content from selected segments."""
        selected = [segments[i] for i in indices if i < len(segments)]

        if not selected:
            # Fallback: return first segment
            return segments[0] if segments else ""

        if self.config.preserve_structure:
            return "\n\n".join(selected)
        else:
            return " ".join(selected)


# ============================================================================
# Abstractive Compressor
# ============================================================================


class AbstractiveCompressor:
    """Abstractive compression - generates summaries."""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        config: Optional[CompressionConfig] = None,
        token_counter: Optional[TokenCounter] = None,
    ) -> None:
        """Initialize abstractive compressor.

        Args:
            llm_client: LLM client for summarization
            config: Compression configuration
            token_counter: Token counter instance
        """
        self.llm_client = llm_client
        self.config = config or CompressionConfig()
        self.token_counter = token_counter or TokenCounter()

    async def compress(
        self,
        document: DocumentChunk,
        query: str,
        token_budget: Optional[int] = None,
    ) -> CompressedDocument:
        """Compress document using abstractive summarization.

        Args:
            document: Document to compress
            query: Query for context
            token_budget: Optional override for token budget

        Returns:
            Compressed document
        """
        budget = token_budget or self.config.token_budget
        original_tokens = self.token_counter.count(document.content)
        target_tokens = int(budget * self.config.target_compression_ratio)

        if not self.llm_client:
            # Fallback to truncation
            return self._truncate(document, target_tokens)

        try:
            summary = await self._generate_summary(document.content, query, target_tokens)

            compressed_tokens = self.token_counter.count(summary)
            compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

            return CompressedDocument(
                original_id=document.id,
                content=summary,
                original_content=document.content,
                token_count=compressed_tokens,
                compression_ratio=compression_ratio,
                preserved_segments=[],
                relevance_score=1.0,
            )
        except Exception as e:
            logger.error(f"Abstractive compression failed: {e}")
            return self._truncate(document, target_tokens)

    async def _generate_summary(self, content: str, query: str, max_tokens: int) -> str:
        """Generate summary using LLM."""
        # Placeholder implementation
        # In production, this would call an LLM API
        max_words = int(max_tokens / 1.3)
        words = content.split()[:max_words]
        return " ".join(words) + "..."

    def _truncate(self, document: DocumentChunk, target_tokens: int) -> CompressedDocument:
        """Fallback truncation."""
        original_tokens = self.token_counter.count(document.content)
        max_words = int(target_tokens / 1.3)
        words = document.content.split()[:max_words]
        truncated = " ".join(words) + "..."

        compressed_tokens = self.token_counter.count(truncated)
        compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        return CompressedDocument(
            original_id=document.id,
            content=truncated,
            original_content=document.content,
            token_count=compressed_tokens,
            compression_ratio=compression_ratio,
            preserved_segments=[],
            relevance_score=0.5,
        )


# ============================================================================
# Contextual Compressor
# ============================================================================


class ContextualCompressor:
    """Main contextual compression class.

    Provides compression capabilities:
    - Extractive: Select relevant segments
    - Abstractive: Generate summaries
    - Hybrid: Extract then summarize

    Target: 50%+ compression ratio while preserving key information

    Example:
        ```python
        compressor = ContextualCompressor(
            config=CompressionConfig(
                target_compression_ratio=0.5,
                token_budget=4000,
            )
        )

        # Compress search results
        result = await compressor.compress_results(
            results=search_results,
            query="What are Python benefits?",
            strategy=CompressionStrategy.EXTRACTIVE,
        )

        print(f"Compression: {result.original_token_count} -> {result.compressed_token_count}")
        print(f"Ratio: {result.overall_compression_ratio:.1%}")
        print(f"Target achieved: {result.is_target_achieved()}")
        ```
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        config: Optional[CompressionConfig] = None,
    ) -> None:
        """Initialize contextual compressor.

        Args:
            llm_client: LLM client for abstractive compression
            config: Compression configuration
        """
        self.config = config or CompressionConfig()
        self.token_counter = TokenCounter()
        self.extractive = ExtractiveCompressor(self.config, self.token_counter)
        self.abstractive = AbstractiveCompressor(llm_client, self.config, self.token_counter)

        # Statistics
        self._stats = {
            "total_compressions": 0,
            "total_tokens_saved": 0,
            "avg_compression_ratio": 0.0,
        }

    async def compress(
        self,
        documents: List[DocumentChunk],
        query: str,
        strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE,
        token_budget: Optional[int] = None,
    ) -> CompressionResult:
        """Compress documents based on query relevance.

        Args:
            documents: Documents to compress
            query: Query string for relevance
            strategy: Compression strategy
            token_budget: Optional token budget override

        Returns:
            Compression result
        """
        if not documents:
            return CompressionResult(
                compressed_documents=[],
                original_token_count=0,
                compressed_token_count=0,
                overall_compression_ratio=1.0,
                strategy_used=strategy,
                query=query,
            )

        budget = token_budget or self.config.token_budget
        budget_per_doc = budget // len(documents)

        # Calculate original token count
        original_tokens = sum(self.token_counter.count(doc.content) for doc in documents)

        # Compress each document
        compressed_docs = []
        for document in documents:
            if strategy == CompressionStrategy.EXTRACTIVE:
                compressed = await self.extractive.compress(document, query, budget_per_doc)
            elif strategy == CompressionStrategy.ABSTRACTIVE:
                compressed = await self.abstractive.compress(document, query, budget_per_doc)
            elif strategy == CompressionStrategy.HYBRID:
                # First extractive, then abstractive
                extracted = await self.extractive.compress(document, query, budget_per_doc)
                temp_doc = DocumentChunk(
                    document_id=document.document_id,
                    content=extracted.content,
                )
                compressed = await self.abstractive.compress(temp_doc, query, budget_per_doc)
                compressed.original_content = document.content
                # Recalculate ratio against original
                orig_tokens = self.token_counter.count(document.content)
                compressed.compression_ratio = compressed.token_count / orig_tokens if orig_tokens > 0 else 1.0
            else:
                compressed = await self.extractive.compress(document, query, budget_per_doc)

            compressed_docs.append(compressed)

        # Calculate totals
        compressed_tokens = sum(doc.token_count for doc in compressed_docs)
        overall_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        # Update stats
        self._stats["total_compressions"] += 1
        self._stats["total_tokens_saved"] += original_tokens - compressed_tokens
        n = self._stats["total_compressions"]
        self._stats["avg_compression_ratio"] = (self._stats["avg_compression_ratio"] * (n - 1) + overall_ratio) / n

        return CompressionResult(
            compressed_documents=compressed_docs,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            overall_compression_ratio=overall_ratio,
            strategy_used=strategy,
            query=query,
        )

    async def compress_results(
        self,
        results: List[SearchResult],
        query: str,
        strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE,
        token_budget: Optional[int] = None,
    ) -> CompressionResult:
        """Compress search results.

        Args:
            results: Search results to compress
            query: Query string
            strategy: Compression strategy
            token_budget: Optional token budget

        Returns:
            Compression result
        """
        documents = [r.chunk for r in results]
        return await self.compress(documents, query, strategy, token_budget)

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        return {
            **self._stats,
            "target_ratio": self.config.target_compression_ratio,
            "config": {
                "token_budget": self.config.token_budget,
                "min_relevance_threshold": self.config.min_relevance_threshold,
            },
        }


# ============================================================================
# Enhanced Searcher with Compression
# ============================================================================


class EnhancedSearcher:
    """Enhanced searcher with contextual compression integration.

    Wraps AdvancedHybridSearcher and adds compression capabilities.

    Example:
        ```python
        # Create base searcher
        base_searcher = AdvancedHybridSearcher(config)
        await base_searcher.initialize()

        # Wrap with compression
        enhanced = EnhancedSearcher(
            base_searcher=base_searcher,
            compressor=ContextualCompressor(),
            enable_compression=True,
        )

        # Search with automatic compression
        result = await enhanced.search(
            "What are Python benefits?",
            top_k=10,
            compress_results=True,
        )

        # Access compressed results
        for doc in result.compressed_documents:
            print(f"Compressed: {doc.compression_ratio:.1%} of original")
        ```
    """

    def __init__(
        self,
        base_searcher: AdvancedHybridSearcher,
        compressor: Optional[ContextualCompressor] = None,
        enable_compression: bool = True,
        default_strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE,
    ) -> None:
        """Initialize enhanced searcher.

        Args:
            base_searcher: Base AdvancedHybridSearcher
            compressor: Optional compressor instance
            enable_compression: Whether to enable compression
            default_strategy: Default compression strategy
        """
        self.base_searcher = base_searcher
        self.compressor = compressor or ContextualCompressor()
        self.enable_compression = enable_compression
        self.default_strategy = default_strategy

    async def search(
        self,
        query: str,
        top_k: int = 20,
        compress_results: bool = True,
        strategy: Optional[CompressionStrategy] = None,
    ) -> Tuple[List[SearchResult], Optional[CompressionResult]]:
        """Search with optional compression.

        Args:
            query: Search query
            top_k: Number of results
            compress_results: Whether to compress results
            strategy: Compression strategy override

        Returns:
            Tuple of (search results, compression result)
        """
        # Perform base search
        results = await self.base_searcher.search(query, top_k=top_k)

        if not compress_results or not self.enable_compression:
            return results, None

        # Compress results
        compression = await self.compressor.compress_results(
            results=results,
            query=query,
            strategy=strategy or self.default_strategy,
        )

        # Update search results with compressed content
        for result, compressed in zip(results, compression.compressed_documents):
            result.chunk.content = compressed.content

        return results, compression

    async def close(self) -> None:
        """Close resources."""
        # Base searcher is managed externally
        pass
