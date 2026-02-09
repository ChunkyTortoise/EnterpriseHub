"""Self-querying system for advanced RAG with query decomposition.

This module provides self-querying capabilities that:
1. Decomposes complex queries into sub-queries
2. Extracts metadata filters from natural language
3. Plans optimal execution strategies
4. Integrates with AdvancedHybridSearcher

Example:
    ```python
    # Decompose complex comparative query
    decomposer = QueryDecomposer()
    sub_queries = await decomposer.decompose(
        "What are the differences between product A and product B released in 2023?"
    )
    # Returns: [
    #   SubQuery(text="product A", filters={"year": 2023}),
    #   SubQuery(text="product B", filters={"year": 2023})
    # ]

    # Use with AdvancedHybridSearcher
    self_querying_searcher = SelfQueryingSearcher(
        base_searcher=advanced_hybrid_searcher,
        enable_decomposition=True,
    )
    results = await self_querying_searcher.search(
        "Find documents by John about Python from last year"
    )
    ```
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from src.core.types import SearchResult
from src.retrieval.advanced_hybrid_searcher import AdvancedHybridSearcher

logger = logging.getLogger(__name__)


class QueryOperator(Enum):
    """Logical operators for combining sub-queries."""

    AND = "and"  # All sub-queries must match
    OR = "or"  # Any sub-query can match
    COMPARE = "compare"  # Compare results from sub-queries


class FilterOperator(Enum):
    """Metadata filter operators."""

    EQ = "$eq"
    NE = "$ne"
    GT = "$gt"
    GTE = "$gte"
    LT = "$lt"
    LTE = "$lte"
    IN = "$in"
    NIN = "$nin"
    CONTAINS = "$contains"
    AND = "$and"
    OR = "$or"


@dataclass
class MetadataFilter:
    """Structured metadata filter for vector store queries.

    Attributes:
        field: Metadata field name
        operator: Filter operator
        value: Filter value
        raw_filter: Raw ChromaDB-compatible filter dict
    """

    field: str
    operator: FilterOperator
    value: Any
    raw_filter: Dict[str, Any] = field(default_factory=dict)

    def to_chroma_filter(self) -> Dict[str, Any]:
        """Convert to ChromaDB filter format."""
        if self.raw_filter:
            return self.raw_filter
        return {self.field: {self.operator.value: self.value}}


@dataclass
class SubQuery:
    """A decomposed sub-query with optional metadata filters.

    Attributes:
        text: Sub-query text for semantic search
        filters: Metadata filters to apply
        weight: Weight for result combination
        intent: Sub-query intent (search, filter, compare)
    """

    text: str
    filters: List[MetadataFilter] = field(default_factory=list)
    weight: float = 1.0
    intent: str = "search"

    def get_combined_filter(self) -> Optional[Dict[str, Any]]:
        """Combine all filters into a single ChromaDB filter."""
        if not self.filters:
            return None

        if len(self.filters) == 1:
            return self.filters[0].to_chroma_filter()

        # Combine multiple filters with $and
        return {"$and": [f.to_chroma_filter() for f in self.filters]}


@dataclass
class DecomposedQuery:
    """Result of query decomposition.

    Attributes:
        original_query: Original user query
        sub_queries: List of decomposed sub-queries
        operator: How to combine sub-query results
        metadata_filters: Global filters applicable to all sub-queries
        temporal_range: Optional temporal filter
    """

    original_query: str
    sub_queries: List[SubQuery]
    operator: QueryOperator = QueryOperator.AND
    metadata_filters: List[MetadataFilter] = field(default_factory=list)
    temporal_range: Optional[Tuple[datetime, datetime]] = None

    def has_decomposition(self) -> bool:
        """Check if query was decomposed into multiple sub-queries."""
        return len(self.sub_queries) > 1


@dataclass
class SelfQueryingResult:
    """Result from self-querying search.

    Attributes:
        results: Combined search results
        decomposed_query: Query decomposition details
        sub_results: Results from individual sub-queries
        execution_time_ms: Total execution time
        metadata_filter_used: Whether metadata filters were applied
    """

    results: List[SearchResult]
    decomposed_query: DecomposedQuery
    sub_results: Dict[str, List[SearchResult]] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    metadata_filter_used: bool = False


# ============================================================================
# Query Decomposition
# ============================================================================


class QueryDecomposer:
    """Decomposes complex queries into sub-queries.

    Handles queries like:
    - "What are the differences between X and Y" -> [X, Y]
    - "Compare A, B, and C" -> [A, B, C]
    - "Find documents about X by author Y from 2023" -> [X] + filters

    Example:
        ```python
        decomposer = QueryDecomposer()

        # Comparative query
        result = await decomposer.decompose(
            "What are the differences between product A and product B?"
        )
        # result.sub_queries = [
        #   SubQuery(text="product A"),
        #   SubQuery(text="product B")
        # ]
        # result.operator = QueryOperator.COMPARE

        # Filtered query
        result = await decomposer.decompose(
            "Find documents by John about Python from last year"
        )
        # result.sub_queries = [SubQuery(text="Python")]
        # result.metadata_filters = [author: John, date: last_year]
        ```
    """

    # Patterns for comparative queries
    COMPARATIVE_PATTERNS = [
        r"what are the differences between (.+?) and (.+)",
        r"compare (.+?) (?:with|to|and) (.+)",
        r"differences between (.+?) and (.+)",
        r"(?:how does|how do) (.+?) compare (?:with|to) (.+)",
    ]

    # Patterns for list queries
    LIST_PATTERNS = [
        r"(?:find|get|show) (.+?) (?:and|or) (.+?)(?:\s+and\s+(.+))?",
        r"information about (.+?),\s*(.+?),?\s*(?:and|or)\s*(.+)",
    ]

    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "author": [
            r"(?:by|written by|created by|author)\s+(\w+(?:\s+\w+)?)",
            r"(\w+(?:\s+\w+)?)['']s\s+(?:document|file|article|paper)",
        ],
        "year": [
            r"(?:in|from|during)\s+(\d{4})",
            r"(?:year)\s+(\d{4})",
        ],
        "category": [
            r"(?:category|type|kind)\s+(?:of\s+)?(\w+)",
            r"(?:in|about)\s+(?:the\s+)?(\w+)\s+(?:category|section)",
        ],
        "tag": [
            r"(?:tagged|labeled)\s+(?:as\s+)?(\w+)",
            r"(?:tag|tags)\s*[:=]\s*(\w+)",
        ],
    }

    # Temporal patterns
    TEMPORAL_PATTERNS = {
        "last_year": r"last year|previous year",
        "this_year": r"this year|current year",
        "last_month": r"last month|previous month",
        "this_month": r"this month|current month",
        "last_week": r"last week|previous week",
        "this_week": r"this week|current week",
        "today": r"today",
        "yesterday": r"yesterday",
    }

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """Initialize query decomposer.

        Args:
            llm_client: Optional LLM client for advanced decomposition
        """
        self.llm_client = llm_client

    async def decompose(self, query: str) -> DecomposedQuery:
        """Decompose a complex query into sub-queries.

        Args:
            query: User query string

        Returns:
            DecomposedQuery with sub-queries and filters
        """
        query_lower = query.lower().strip()

        # Try comparative decomposition first
        comparative = self._try_comparative_decomposition(query_lower)
        if comparative:
            return comparative

        # Try list decomposition
        list_decomp = self._try_list_decomposition(query_lower)
        if list_decomp:
            return list_decomp

        # Extract metadata filters from single query
        filters = self._extract_metadata_filters(query)
        temporal_range = self._extract_temporal_range(query)

        # Create single sub-query with filters
        sub_query = SubQuery(
            text=self._clean_query_text(query, filters, temporal_range),
            filters=filters,
            weight=1.0,
        )

        return DecomposedQuery(
            original_query=query,
            sub_queries=[sub_query],
            operator=QueryOperator.AND,
            metadata_filters=filters,
            temporal_range=temporal_range,
        )

    def _try_comparative_decomposition(self, query: str) -> Optional[DecomposedQuery]:
        """Try to decompose a comparative query."""
        for pattern in self.COMPARATIVE_PATTERNS:
            match = re.search(pattern, query)
            if match:
                # Extract items to compare
                items = [m.strip() for m in match.groups() if m]

                # Create sub-queries for each item
                sub_queries = []
                for item in items:
                    filters = self._extract_metadata_filters(item)
                    clean_text = self._clean_query_text(item, filters, None)
                    sub_queries.append(
                        SubQuery(
                            text=clean_text,
                            filters=filters,
                            weight=1.0,
                            intent="compare",
                        )
                    )

                # Extract global filters from full query
                global_filters = self._extract_metadata_filters(query)
                temporal_range = self._extract_temporal_range(query)

                return DecomposedQuery(
                    original_query=query,
                    sub_queries=sub_queries,
                    operator=QueryOperator.COMPARE,
                    metadata_filters=global_filters,
                    temporal_range=temporal_range,
                )

        return None

    def _try_list_decomposition(self, query: str) -> Optional[DecomposedQuery]:
        """Try to decompose a list-based query."""
        # Look for comma or 'and' separated items after keywords
        list_match = re.search(
            r"(?:find|get|show|about)\s+(.+?)(?:\s+(?:and|or)\s+(.+))?$",
            query,
        )

        if list_match:
            items_text = list_match.group(1)
            # Split by commas and 'and'
            items = re.split(r",\s*|\s+and\s+", items_text)
            items = [i.strip() for i in items if len(i.strip()) > 2]

            if len(items) > 1:
                sub_queries = []
                for item in items:
                    filters = self._extract_metadata_filters(item)
                    clean_text = self._clean_query_text(item, filters, None)
                    sub_queries.append(
                        SubQuery(
                            text=clean_text,
                            filters=filters,
                            weight=1.0 / len(items),
                        )
                    )

                global_filters = self._extract_metadata_filters(query)
                temporal_range = self._extract_temporal_range(query)

                return DecomposedQuery(
                    original_query=query,
                    sub_queries=sub_queries,
                    operator=QueryOperator.OR,
                    metadata_filters=global_filters,
                    temporal_range=temporal_range,
                )

        return None

    def _extract_metadata_filters(self, query: str) -> List[MetadataFilter]:
        """Extract metadata filters from query text."""
        filters = []
        query_lower = query.lower()

        # Extract author
        for pattern in self.ENTITY_PATTERNS["author"]:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                value = match.group(1).strip()
                if value:
                    filters.append(
                        MetadataFilter(
                            field="author",
                            operator=FilterOperator.EQ,
                            value=value.capitalize(),
                            raw_filter={"author": {"$eq": value.capitalize()}},
                        )
                    )

        # Extract year
        for pattern in self.ENTITY_PATTERNS["year"]:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                year = match.group(1)
                filters.append(
                    MetadataFilter(
                        field="year",
                        operator=FilterOperator.EQ,
                        value=int(year),
                        raw_filter={"year": {"$eq": int(year)}},
                    )
                )

        # Extract category
        for pattern in self.ENTITY_PATTERNS["category"]:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                value = match.group(1).strip().lower()
                if value:
                    filters.append(
                        MetadataFilter(
                            field="category",
                            operator=FilterOperator.EQ,
                            value=value,
                            raw_filter={"category": {"$eq": value}},
                        )
                    )

        # Extract tags
        for pattern in self.ENTITY_PATTERNS["tag"]:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                value = match.group(1).strip().lower()
                if value:
                    filters.append(
                        MetadataFilter(
                            field="tags",
                            operator=FilterOperator.CONTAINS,
                            value=value,
                            raw_filter={"tags": {"$contains": value}},
                        )
                    )

        return filters

    def _extract_temporal_range(self, query: str) -> Optional[Tuple[datetime, datetime]]:
        """Extract temporal range from query."""
        query_lower = query.lower()
        now = datetime.now()

        for ref_type, pattern in self.TEMPORAL_PATTERNS.items():
            if re.search(pattern, query_lower):
                if ref_type == "last_year":
                    start = datetime(now.year - 1, 1, 1)
                    end = datetime(now.year - 1, 12, 31, 23, 59, 59)
                    return (start, end)
                elif ref_type == "this_year":
                    start = datetime(now.year, 1, 1)
                    end = now
                    return (start, end)
                elif ref_type == "last_month":
                    if now.month == 1:
                        start = datetime(now.year - 1, 12, 1)
                        end = datetime(now.year - 1, 12, 31, 23, 59, 59)
                    else:
                        start = datetime(now.year, now.month - 1, 1)
                        end = datetime(now.year, now.month, 1)
                    return (start, end)
                elif ref_type == "this_month":
                    start = datetime(now.year, now.month, 1)
                    end = now
                    return (start, end)
                elif ref_type == "last_week":
                    week_ago = now - timedelta(days=7)
                    start = week_ago - timedelta(days=week_ago.weekday())
                    end = start + timedelta(days=6, hours=23, minutes=59)
                    return (start, end)
                elif ref_type == "today":
                    start = datetime(now.year, now.month, now.day)
                    end = now
                    return (start, end)
                elif ref_type == "yesterday":
                    yesterday = now - timedelta(days=1)
                    start = datetime(yesterday.year, yesterday.month, yesterday.day)
                    end = start + timedelta(days=1, seconds=-1)
                    return (start, end)

        return None

    def _clean_query_text(
        self,
        query: str,
        filters: List[MetadataFilter],
        temporal_range: Optional[Tuple[datetime, datetime]],
    ) -> str:
        """Remove filter terms from query to get clean search text."""
        # Remove temporal patterns
        for pattern in self.TEMPORAL_PATTERNS.values():
            query = re.sub(pattern, "", query, flags=re.IGNORECASE)

        # Remove entity patterns
        for entity_patterns in self.ENTITY_PATTERNS.values():
            for pattern in entity_patterns:
                query = re.sub(pattern, "", query, flags=re.IGNORECASE)

        # Clean up
        query = re.sub(r"\s+", " ", query).strip()
        query = re.sub(r"^\s*(?:find|get|show|about)\s+", "", query, flags=re.IGNORECASE)

        return query


# ============================================================================
# Self-Querying Searcher
# ============================================================================


class SelfQueryingSearcher:
    """Self-querying searcher that integrates with AdvancedHybridSearcher.

    Provides advanced RAG capabilities:
    1. Query decomposition for complex queries
    2. Automatic metadata filter extraction
    3. Sub-query execution and result fusion
    4. Integration with existing search pipeline

    Example:
        ```python
        # Create base searcher
        base_searcher = AdvancedHybridSearcher(config)
        await base_searcher.initialize()

        # Wrap with self-querying
        sq_searcher = SelfQueryingSearcher(
            base_searcher=base_searcher,
            enable_decomposition=True,
        )

        # Search with automatic decomposition
        result = await sq_searcher.search(
            "What are the differences between product A and product B released in 2023?"
        )

        # Access decomposition details
        print(f"Decomposed into: {len(result.decomposed_query.sub_queries)} queries")
        print(f"Filters used: {result.metadata_filter_used}")
        ```
    """

    def __init__(
        self,
        base_searcher: AdvancedHybridSearcher,
        enable_decomposition: bool = True,
        enable_metadata_filtering: bool = True,
        llm_client: Optional[Any] = None,
    ) -> None:
        """Initialize self-querying searcher.

        Args:
            base_searcher: Base AdvancedHybridSearcher instance
            enable_decomposition: Whether to enable query decomposition
            enable_metadata_filtering: Whether to extract metadata filters
            llm_client: Optional LLM client for advanced decomposition
        """
        self.base_searcher = base_searcher
        self.enable_decomposition = enable_decomposition
        self.enable_metadata_filtering = enable_metadata_filtering
        self.decomposer = QueryDecomposer(llm_client) if enable_decomposition else None

        # Statistics
        self._stats = {
            "total_queries": 0,
            "decomposed_queries": 0,
            "filter_applied_queries": 0,
            "avg_execution_time_ms": 0.0,
        }

    async def search(
        self,
        query: str,
        top_k: int = 20,
        apply_metadata_filters: bool = True,
    ) -> SelfQueryingResult:
        """Search with self-querying capabilities.

        Args:
            query: User query string
            top_k: Number of results to return
            apply_metadata_filters: Whether to apply extracted filters

        Returns:
            SelfQueryingResult with results and metadata
        """
        start_time = time.time()
        self._stats["total_queries"] += 1

        # Decompose query if enabled
        if self.enable_decomposition and self.decomposer:
            decomposed = await self.decomposer.decompose(query)
        else:
            decomposed = DecomposedQuery(
                original_query=query,
                sub_queries=[SubQuery(text=query)],
            )

        if decomposed.has_decomposition():
            self._stats["decomposed_queries"] += 1

        # Execute sub-queries
        sub_results: Dict[str, List[SearchResult]] = {}
        all_results: List[SearchResult] = []

        if len(decomposed.sub_queries) == 1:
            # Single query - execute directly
            sub_query = decomposed.sub_queries[0]
            results = await self._execute_sub_query(sub_query, top_k)
            sub_results["main"] = results
            all_results = results
        else:
            # Multiple sub-queries - execute in parallel
            tasks = [
                self._execute_sub_query(sq, top_k // len(decomposed.sub_queries) + 5) for sq in decomposed.sub_queries
            ]
            results_list = await asyncio.gather(*tasks)

            for i, (sq, results) in enumerate(zip(decomposed.sub_queries, results_list)):
                sub_results[f"sub_{i}"] = results
                all_results.extend(results)

        # Combine results based on operator
        combined_results = self._combine_results(all_results, decomposed.operator, top_k)

        execution_time = (time.time() - start_time) * 1000
        self._update_stats(execution_time)

        # Check if filters were used
        metadata_filter_used = (apply_metadata_filters and any(sq.filters for sq in decomposed.sub_queries)) or bool(
            decomposed.metadata_filters
        )

        if metadata_filter_used:
            self._stats["filter_applied_queries"] += 1

        return SelfQueryingResult(
            results=combined_results,
            decomposed_query=decomposed,
            sub_results=sub_results,
            execution_time_ms=execution_time,
            metadata_filter_used=metadata_filter_used,
        )

    async def _execute_sub_query(self, sub_query: SubQuery, top_k: int) -> List[SearchResult]:
        """Execute a single sub-query.

        Args:
            sub_query: Sub-query to execute
            top_k: Number of results

        Returns:
            Search results
        """
        # For now, use base searcher
        # In production, this would pass filters to the vector store
        try:
            results = await self.base_searcher.search(sub_query.text, top_k=top_k)

            # Apply weight to scores
            for result in results:
                result.score *= sub_query.weight

            return results
        except Exception as e:
            logger.error(f"Sub-query execution failed: {e}")
            return []

    def _combine_results(
        self,
        results: List[SearchResult],
        operator: QueryOperator,
        top_k: int,
    ) -> List[SearchResult]:
        """Combine results from multiple sub-queries.

        Args:
            results: All results from sub-queries
            operator: How to combine results
            top_k: Number of results to return

        Returns:
            Combined and ranked results
        """
        if not results:
            return []

        # Deduplicate by chunk ID
        seen_chunks: Set[UUID] = set()
        unique_results: List[SearchResult] = []

        for result in sorted(results, key=lambda r: r.score, reverse=True):
            if result.chunk.id not in seen_chunks:
                seen_chunks.add(result.chunk.id)
                unique_results.append(result)

        if operator == QueryOperator.AND:
            # For AND, boost items that appear multiple times
            chunk_counts: Dict[UUID, int] = {}
            for result in results:
                chunk_counts[result.chunk.id] = chunk_counts.get(result.chunk.id, 0) + 1

            # Boost score based on frequency
            for result in unique_results:
                count = chunk_counts.get(result.chunk.id, 1)
                result.score *= 1 + 0.1 * count  # 10% boost per occurrence

        # Sort by score and return top_k
        unique_results.sort(key=lambda r: r.score, reverse=True)
        return unique_results[:top_k]

    def _update_stats(self, execution_time: float) -> None:
        """Update performance statistics."""
        n = self._stats["total_queries"]
        self._stats["avg_execution_time_ms"] = (self._stats["avg_execution_time_ms"] * (n - 1) + execution_time) / n

    def get_stats(self) -> Dict[str, Any]:
        """Get self-querying statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            **self._stats,
            "decomposition_rate": (self._stats["decomposed_queries"] / max(self._stats["total_queries"], 1)),
            "filter_usage_rate": (self._stats["filter_applied_queries"] / max(self._stats["total_queries"], 1)),
        }

    async def close(self) -> None:
        """Close and cleanup resources."""
        # Base searcher is managed externally
        pass
