"""Self-Querying Retriever for Advanced RAG System.

Parses natural language queries to extract structured metadata filters
and a semantic search query, then executes both together.

The QueryAnalyzer uses rule-based extraction to identify filter patterns
like 'by <author>', 'from <source>', 'after <date>', 'tagged <tag>'.
A protocol is provided for LLM-based analyzers as a future extension.

Example:
    ```python
    retriever = SelfQueryRetriever(vector_store)
    result = await retriever.retrieve("papers by Alice from arxiv after 2024-01-01")
    # result.analysis.filters → [author=Alice, source=arxiv, created_at>=2024-01-01]
    # result.results → filtered + semantically matched documents
    ```
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, SearchResult
from src.vector_store.base import SearchOptions, VectorStore


class FilterOperator(str, Enum):
    """Supported filter comparison operators."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"


class MetadataFilter(BaseModel):
    """A single metadata filter condition.

    Attributes:
        field: Metadata field to filter on (e.g. 'author', 'source')
        operator: Comparison operator
        value: Value to compare against
    """

    model_config = ConfigDict(extra="forbid")

    field: str
    operator: FilterOperator
    value: Any


class QueryAnalysis(BaseModel):
    """Result of analyzing a natural language query.

    Attributes:
        original_query: The raw user query
        semantic_query: The semantic portion for embedding search
        filters: Extracted metadata filters
        confidence: Confidence that filter extraction is correct (0-1)
    """

    model_config = ConfigDict(extra="forbid")

    original_query: str
    semantic_query: str
    filters: List[MetadataFilter] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @property
    def has_filters(self) -> bool:
        return len(self.filters) > 0

    def to_search_filters(self) -> Dict[str, Any]:
        """Convert filters to a flat dict for SearchOptions compatibility.

        Returns simple ``{field: value}`` for EQ/CONTAINS operators and
        ``{field: {"$operator": value}}`` for range operators.
        """
        result: Dict[str, Any] = {}
        for f in self.filters:
            if f.operator in (FilterOperator.EQ, FilterOperator.CONTAINS):
                result[f.field] = f.value
            else:
                result[f.field] = {f"${f.operator.value}": f.value}
        return result


class SelfQueryResult(BaseModel):
    """Result from a self-querying retrieval operation.

    Attributes:
        results: Filtered and ranked search results
        analysis: The query analysis that produced the filters
        search_time_ms: Total retrieval time in milliseconds
    """

    model_config = ConfigDict(extra="forbid")

    results: List[SearchResult] = Field(default_factory=list)
    analysis: Optional[QueryAnalysis] = None
    search_time_ms: float = Field(default=0.0, ge=0.0)


@dataclass
class SelfQueryConfig:
    """Configuration for the self-querying retriever.

    Attributes:
        top_k: Maximum results to return
        threshold: Minimum similarity threshold
        min_filter_confidence: Below this, skip filters and do pure semantic
        enable_date_parsing: Whether to parse date filters
    """

    top_k: int = 10
    threshold: float = 0.0
    min_filter_confidence: float = 0.3
    enable_date_parsing: bool = True


# ---------------------------------------------------------------------------
# Filter extraction patterns
# ---------------------------------------------------------------------------

# author: "by <Name>" where Name is one or more capitalized words
_AUTHOR_PATTERN = re.compile(
    r"\bby\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b"
)

# source: "from <source>"
_SOURCE_PATTERN = re.compile(
    r"\bfrom\s+([a-zA-Z][a-zA-Z0-9_.-]+)\b", re.IGNORECASE
)

# date after: "after <YYYY-MM-DD>"
_DATE_AFTER_PATTERN = re.compile(
    r"\bafter\s+(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE
)

# date before: "before <YYYY-MM-DD>"
_DATE_BEFORE_PATTERN = re.compile(
    r"\bbefore\s+(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE
)

# tag: "tagged <tag>"
_TAG_PATTERN = re.compile(
    r"\btagged\s+([a-zA-Z][a-zA-Z0-9_-]+)\b", re.IGNORECASE
)

# title: 'titled "<title>"'
_TITLE_PATTERN = re.compile(
    r'\btitled\s+"([^"]+)"', re.IGNORECASE
)


class QueryAnalyzer:
    """Rule-based query analyzer that extracts metadata filters.

    Scans the query for known patterns (author, source, date, tag, title)
    and produces a ``QueryAnalysis`` with the extracted filters and the
    remaining semantic query.
    """

    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze a query and extract metadata filters.

        Args:
            query: Natural language query string

        Returns:
            QueryAnalysis with semantic query and filters

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        working = query.strip()
        filters: List[MetadataFilter] = []
        confidence_signals: List[float] = []

        # --- Author ---
        m = _AUTHOR_PATTERN.search(working)
        if m:
            filters.append(MetadataFilter(
                field="author", operator=FilterOperator.EQ, value=m.group(1)
            ))
            working = working[:m.start()] + working[m.end():]
            confidence_signals.append(0.9)

        # --- Source ---
        m = _SOURCE_PATTERN.search(working)
        if m:
            filters.append(MetadataFilter(
                field="source", operator=FilterOperator.EQ, value=m.group(1)
            ))
            working = working[:m.start()] + working[m.end():]
            confidence_signals.append(0.85)

        # --- Date after ---
        m = _DATE_AFTER_PATTERN.search(working)
        if m:
            filters.append(MetadataFilter(
                field="created_at",
                operator=FilterOperator.GTE,
                value=m.group(1),
            ))
            working = working[:m.start()] + working[m.end():]
            confidence_signals.append(0.9)

        # --- Date before ---
        m = _DATE_BEFORE_PATTERN.search(working)
        if m:
            filters.append(MetadataFilter(
                field="created_at",
                operator=FilterOperator.LTE,
                value=m.group(1),
            ))
            working = working[:m.start()] + working[m.end():]
            confidence_signals.append(0.9)

        # --- Tag ---
        m = _TAG_PATTERN.search(working)
        if m:
            filters.append(MetadataFilter(
                field="tags", operator=FilterOperator.CONTAINS, value=m.group(1)
            ))
            working = working[:m.start()] + working[m.end():]
            confidence_signals.append(0.85)

        # --- Title ---
        m = _TITLE_PATTERN.search(working)
        if m:
            filters.append(MetadataFilter(
                field="title", operator=FilterOperator.EQ, value=m.group(1)
            ))
            working = working[:m.start()] + working[m.end():]
            confidence_signals.append(0.95)

        # Clean up residual whitespace
        semantic_query = re.sub(r"\s+", " ", working).strip()
        if not semantic_query:
            semantic_query = query.strip()

        # Confidence: average of extraction signals, or 0.5 if no filters
        if confidence_signals:
            confidence = sum(confidence_signals) / len(confidence_signals)
        else:
            confidence = 0.5

        return QueryAnalysis(
            original_query=query.strip(),
            semantic_query=semantic_query,
            filters=filters,
            confidence=confidence,
        )


def _match_filter(chunk: DocumentChunk, f: MetadataFilter) -> bool:
    """Check if a single chunk matches a metadata filter."""
    meta = chunk.metadata

    # Resolve the field value from metadata
    if f.field == "author":
        field_val = meta.author
    elif f.field == "source":
        field_val = meta.source
    elif f.field == "title":
        field_val = meta.title
    elif f.field == "tags":
        field_val = meta.tags
    elif f.field == "created_at":
        field_val = meta.created_at
    else:
        # Check custom metadata
        field_val = meta.custom.get(f.field)

    if field_val is None:
        return False

    # Apply operator
    if f.operator == FilterOperator.EQ:
        return field_val == f.value
    elif f.operator == FilterOperator.NEQ:
        return field_val != f.value
    elif f.operator == FilterOperator.CONTAINS:
        if isinstance(field_val, list):
            return f.value in field_val
        return str(f.value).lower() in str(field_val).lower()
    elif f.operator == FilterOperator.IN:
        return field_val in f.value
    elif f.operator in (FilterOperator.GT, FilterOperator.GTE, FilterOperator.LT, FilterOperator.LTE):
        return _compare_values(field_val, f.value, f.operator)
    return False


def _compare_values(field_val: Any, filter_val: Any, op: FilterOperator) -> bool:
    """Compare values for range operators, handling datetime strings."""
    # If field_val is datetime and filter_val is string, parse the string
    if isinstance(field_val, datetime) and isinstance(filter_val, str):
        try:
            filter_val = datetime.fromisoformat(filter_val)
        except (ValueError, TypeError):
            return False

    try:
        if op == FilterOperator.GT:
            return field_val > filter_val
        elif op == FilterOperator.GTE:
            return field_val >= filter_val
        elif op == FilterOperator.LT:
            return field_val < filter_val
        elif op == FilterOperator.LTE:
            return field_val <= filter_val
    except TypeError:
        return False
    return False


class SelfQueryRetriever:
    """Self-querying retriever that combines filter extraction with semantic search.

    Analyzes natural language queries to extract metadata filters, then
    performs a semantic search with those filters applied in-memory.

    Args:
        vector_store: Initialized vector store to search
        analyzer: Query analyzer (defaults to rule-based QueryAnalyzer)
        config: Retriever configuration
    """

    def __init__(
        self,
        vector_store: VectorStore,
        analyzer: Optional[QueryAnalyzer] = None,
        config: Optional[SelfQueryConfig] = None,
    ) -> None:
        self._store = vector_store
        self._analyzer = analyzer or QueryAnalyzer()
        self._config = config or SelfQueryConfig()

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> SelfQueryResult:
        """Retrieve documents using self-querying.

        1. Analyze query to extract filters and semantic query
        2. Search vector store with semantic query
        3. Apply metadata filters in-memory
        4. Return filtered results

        Args:
            query: Natural language query
            top_k: Override for max results

        Returns:
            SelfQueryResult with filtered results and analysis
        """
        start = time.perf_counter()
        effective_top_k = top_k or self._config.top_k

        try:
            analysis = self._analyzer.analyze(query)
        except ValueError:
            raise

        # Decide whether to apply filters based on confidence
        use_filters = (
            analysis.has_filters
            and analysis.confidence >= self._config.min_filter_confidence
        )

        # Build a dummy embedding from the semantic query for search.
        # In production, an embedding provider would be injected.
        # Here we use a simple hash-based embedding to enable vector search.
        search_embedding = self._text_to_embedding(analysis.semantic_query)

        # Fetch more results than needed so we have room after filtering
        fetch_k = effective_top_k * 5 if use_filters else effective_top_k

        search_options = SearchOptions(
            top_k=fetch_k,
            threshold=self._config.threshold,
        )

        results = await self._store.search(search_embedding, search_options)

        # Apply metadata filters in-memory
        if use_filters:
            results = self._apply_filters(results, analysis.filters)

        # Trim to top_k and re-rank
        results = results[:effective_top_k]
        for i, r in enumerate(results):
            results[i] = SearchResult(
                chunk=r.chunk,
                score=r.score,
                rank=i + 1,
                distance=r.distance,
                explanation=r.explanation,
            )

        elapsed = (time.perf_counter() - start) * 1000

        return SelfQueryResult(
            results=results,
            analysis=analysis,
            search_time_ms=elapsed,
        )

    def _apply_filters(
        self,
        results: List[SearchResult],
        filters: List[MetadataFilter],
    ) -> List[SearchResult]:
        """Apply metadata filters to search results (AND logic)."""
        filtered = []
        for r in results:
            if all(_match_filter(r.chunk, f) for f in filters):
                filtered.append(r)
        return filtered

    def _text_to_embedding(self, text: str) -> List[float]:
        """Generate a deterministic embedding from text.

        This is a lightweight fallback for when no embedding provider
        is available. In production, replace with a real provider.
        """
        import hashlib
        import numpy as np

        dim = self._store.config.dimension
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
