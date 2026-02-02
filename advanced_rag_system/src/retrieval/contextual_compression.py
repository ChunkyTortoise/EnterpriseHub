"""Contextual Compression for Advanced RAG System.

Extracts the most relevant portions of retrieved documents relative
to a query, reducing token usage while preserving information quality.

Supports extractive compression (sentence selection) with token budget
management across multiple documents.

Example:
    ```python
    compressor = ContextualCompressor(CompressionConfig(max_tokens=500))
    compressed = await compressor.compress("neural networks", search_results)
    # compressed.documents → list of CompressedDocument with relevant excerpts
    # compressed.compression_ratio → 0.35 (65% reduction)
    ```
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.core.types import SearchResult


class CompressionStrategy(str, Enum):
    """Compression strategy selection."""

    EXTRACTIVE = "extractive"


class CompressedDocument(BaseModel):
    """A document compressed to its most relevant portions.

    Attributes:
        original_chunk_id: ID of the source chunk
        content: Compressed text content
        token_count: Estimated token count of compressed content
        relevance_score: Average relevance of retained sentences
    """

    model_config = ConfigDict(extra="forbid")

    original_chunk_id: UUID
    content: str
    token_count: int = Field(default=0, ge=0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class CompressionResult(BaseModel):
    """Result of a contextual compression operation.

    Attributes:
        documents: List of compressed documents
        original_token_count: Total tokens before compression
        compressed_token_count: Total tokens after compression
        compression_ratio: compressed / original (lower = more compressed)
    """

    model_config = ConfigDict(extra="forbid")

    documents: List[CompressedDocument] = Field(default_factory=list)
    original_token_count: int = Field(default=0, ge=0)
    compressed_token_count: int = Field(default=0, ge=0)
    compression_ratio: float = Field(default=1.0, ge=0.0, le=1.0)


@dataclass
class CompressionConfig:
    """Configuration for contextual compression.

    Attributes:
        strategy: Compression strategy to use
        max_tokens: Maximum total tokens across all compressed documents
        min_relevance_score: Minimum sentence relevance to keep
        preserve_order: Keep sentences in document order
    """

    strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE
    max_tokens: int = 1000
    min_relevance_score: float = 0.1
    preserve_order: bool = True


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------

# Abbreviations that should not trigger sentence splitting
_ABBREVIATIONS = {"dr", "mr", "mrs", "ms", "prof", "sr", "jr", "st", "vs", "etc", "inc", "ltd", "e.g", "i.e"}

_SENTENCE_BOUNDARY = re.compile(
    r'(?<=[.!?])\s+(?=[A-Z])'
)

# Pattern to temporarily mask abbreviation periods
_ABBREV_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(a) for a in sorted(_ABBREVIATIONS, key=len, reverse=True)) + r')\.',
    re.IGNORECASE,
)


class RelevanceExtractor:
    """Scores and extracts relevant sentences from text."""

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Handles common abbreviations to avoid false splits.

        Args:
            text: Input text

        Returns:
            List of sentence strings
        """
        if not text.strip():
            return []

        # Mask abbreviation periods to prevent false splits
        _PLACEHOLDER = "\x00"
        masked = _ABBREV_PATTERN.sub(lambda m: m.group(0).replace(".", _PLACEHOLDER), text.strip())

        # Split on sentence boundaries
        parts = _SENTENCE_BOUNDARY.split(masked)

        # Restore masked periods
        sentences = [p.replace(_PLACEHOLDER, ".").strip() for p in parts if p.strip()]
        return sentences

    def score_sentence(self, query: str, sentence: str) -> float:
        """Score a sentence's relevance to a query using word overlap.

        Uses Jaccard-like overlap between query words and sentence words,
        weighted by word significance (longer words count more).

        Args:
            query: Search query
            sentence: Sentence to score

        Returns:
            Relevance score in [0, 1]
        """
        if not query.strip() or not sentence.strip():
            return 0.0

        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "about", "that", "this", "it", "its",
            "and", "or", "but", "not", "no", "so", "if", "then", "than",
        }

        query_words = {
            w.lower()
            for w in re.findall(r"\b\w+\b", query)
            if w.lower() not in stop_words and len(w) >= 2
        }
        sent_words = {
            w.lower()
            for w in re.findall(r"\b\w+\b", sentence)
            if w.lower() not in stop_words and len(w) >= 2
        }

        if not query_words:
            return 0.0

        overlap = query_words & sent_words
        if not overlap:
            return 0.0

        # Weighted overlap: longer matching words count more
        weighted_overlap = sum(len(w) for w in overlap)
        weighted_total = sum(len(w) for w in query_words)

        score = weighted_overlap / weighted_total
        return min(score, 1.0)

    def extract_relevant(
        self,
        query: str,
        text: str,
        top_k: int = 5,
        preserve_order: bool = False,
    ) -> List[Tuple[str, float]]:
        """Extract the most relevant sentences from text.

        Args:
            query: Search query
            text: Document text
            top_k: Maximum sentences to return
            preserve_order: If True, return in document order

        Returns:
            List of (sentence, score) tuples
        """
        sentences = self.split_sentences(text)
        if not sentences:
            return []

        scored = [
            (sent, self.score_sentence(query, sent))
            for sent in sentences
        ]

        # Sort by score descending to pick top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

        if preserve_order and top:
            # Restore original document order
            sentence_order = {sent: i for i, sent in enumerate(sentences)}
            top.sort(key=lambda x: sentence_order.get(x[0], 0))

        return top


class TokenBudgetManager:
    """Manages token budget allocation across multiple documents."""

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text.

        Uses a simple heuristic: word_count * 1.3 (accounts for
        subword tokenization in typical LLM tokenizers).

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        if not text.strip():
            return 0
        word_count = len(text.split())
        return int(word_count * 1.3)

    def allocate(
        self,
        scores: List[float],
        budget: int,
        min_per_doc: int = 0,
    ) -> List[int]:
        """Allocate token budget proportional to relevance scores.

        Args:
            scores: Relevance scores for each document
            budget: Total token budget
            min_per_doc: Minimum tokens per document

        Returns:
            List of token allocations (same length as scores)
        """
        n = len(scores)
        if n == 0:
            return []
        if budget <= 0:
            return [0] * n

        # Ensure minimum allocations fit
        total_min = min_per_doc * n
        if total_min >= budget:
            per_doc = budget // n
            return [per_doc] * n

        remaining = budget - total_min
        total_score = sum(scores)

        if total_score <= 0:
            # Equal distribution
            per_doc = remaining // n
            return [min_per_doc + per_doc] * n

        # Proportional allocation
        allocations = []
        for s in scores:
            proportion = s / total_score
            alloc = min_per_doc + int(remaining * proportion)
            allocations.append(alloc)

        # Fix rounding: distribute any leftover to highest-scored doc
        used = sum(allocations)
        if used < budget:
            max_idx = scores.index(max(scores))
            allocations[max_idx] += budget - used

        return allocations


class ContextualCompressor:
    """Compresses retrieved documents to their most query-relevant portions.

    Uses extractive compression: selects the most relevant sentences
    from each document, respecting a global token budget.

    Args:
        config: Compression configuration
    """

    def __init__(self, config: Optional[CompressionConfig] = None) -> None:
        self._config = config or CompressionConfig()
        self._extractor = RelevanceExtractor()
        self._budget_mgr = TokenBudgetManager()

    async def compress(
        self,
        query: str,
        results: List[SearchResult],
    ) -> CompressionResult:
        """Compress search results to their most relevant content.

        Args:
            query: The search query
            results: Search results to compress

        Returns:
            CompressionResult with compressed documents
        """
        if not results:
            return CompressionResult(
                documents=[],
                original_token_count=0,
                compressed_token_count=0,
                compression_ratio=1.0,
            )

        # Calculate original token counts
        original_tokens = [
            self._budget_mgr.estimate_tokens(r.chunk.content)
            for r in results
        ]
        total_original = sum(original_tokens)

        # Allocate budget proportional to search scores
        scores = [r.score for r in results]
        allocations = self._budget_mgr.allocate(
            scores, self._config.max_tokens
        )

        # Compress each document
        compressed_docs: List[CompressedDocument] = []
        total_compressed = 0

        for result, token_budget in zip(results, allocations):
            doc = self._compress_document(query, result, token_budget)
            compressed_docs.append(doc)
            total_compressed += doc.token_count

        # Calculate compression ratio
        if total_original > 0:
            ratio = min(total_compressed / total_original, 1.0)
        else:
            ratio = 1.0

        return CompressionResult(
            documents=compressed_docs,
            original_token_count=total_original,
            compressed_token_count=total_compressed,
            compression_ratio=ratio,
        )

    def _compress_document(
        self,
        query: str,
        result: SearchResult,
        token_budget: int,
    ) -> CompressedDocument:
        """Compress a single document to fit within a token budget.

        Args:
            query: Search query
            result: Search result to compress
            token_budget: Maximum tokens for this document

        Returns:
            CompressedDocument with extracted content
        """
        content = result.chunk.content
        original_tokens = self._budget_mgr.estimate_tokens(content)

        # If document already fits, return as-is (with relevance filtering)
        if original_tokens <= token_budget:
            # Still filter by relevance if threshold > 0
            if self._config.min_relevance_score > 0.1:
                return self._extract_relevant(query, result, token_budget)
            return CompressedDocument(
                original_chunk_id=result.chunk.id,
                content=content,
                token_count=original_tokens,
                relevance_score=result.score,
            )

        return self._extract_relevant(query, result, token_budget)

    def _extract_relevant(
        self,
        query: str,
        result: SearchResult,
        token_budget: int,
    ) -> CompressedDocument:
        """Extract relevant sentences within token budget."""
        content = result.chunk.content
        sentences = self._extractor.split_sentences(content)

        if not sentences:
            return CompressedDocument(
                original_chunk_id=result.chunk.id,
                content="",
                token_count=0,
                relevance_score=0.0,
            )

        # Score all sentences
        scored = [
            (sent, self._extractor.score_sentence(query, sent))
            for sent in sentences
        ]

        # Filter by minimum relevance
        scored = [
            (s, sc) for s, sc in scored
            if sc >= self._config.min_relevance_score
        ]

        if not scored:
            # If nothing passes threshold, keep the highest-scored sentence
            all_scored = [
                (sent, self._extractor.score_sentence(query, sent))
                for sent in sentences
            ]
            if all_scored:
                best = max(all_scored, key=lambda x: x[1])
                scored = [best]

        # Sort by score to pick best sentences first
        scored.sort(key=lambda x: x[1], reverse=True)

        # Greedily select sentences within budget
        selected: List[Tuple[str, float]] = []
        running_tokens = 0

        for sent, sc in scored:
            sent_tokens = self._budget_mgr.estimate_tokens(sent)
            if running_tokens + sent_tokens <= token_budget:
                selected.append((sent, sc))
                running_tokens += sent_tokens
            elif not selected:
                # Always include at least one sentence
                selected.append((sent, sc))
                running_tokens += sent_tokens
                break

        # Restore document order if configured
        if self._config.preserve_order and selected:
            sentence_order = {sent: i for i, sent in enumerate(sentences)}
            selected.sort(key=lambda x: sentence_order.get(x[0], 0))

        compressed_text = " ".join(s for s, _ in selected)
        avg_relevance = (
            sum(sc for _, sc in selected) / len(selected)
            if selected else 0.0
        )

        return CompressedDocument(
            original_chunk_id=result.chunk.id,
            content=compressed_text,
            token_count=self._budget_mgr.estimate_tokens(compressed_text),
            relevance_score=min(avg_relevance, 1.0),
        )
