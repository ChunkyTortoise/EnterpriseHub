"""Self-querying system for natural language to metadata filter translation.

This module provides the ability to convert natural language queries into
structured metadata filters for vector store searches. It includes:
- Query analysis and entity extraction
- Filter translation to ChromaDB format
- Query planning for optimal execution
- Fallback handling when filters are insufficient

Example:
    ```python
    retriever = SelfQueryRetriever(
        vector_store=store,
        llm_client=openai_client,
    )
    await retriever.initialize()

    # Query with automatic filter extraction
    results = await retriever.retrieve(
        "Find documents about Python written by John last year"
    )
    # Automatically generates: {"author": {"$eq": "John"}, "tags": {"$in": ["python"]}}
    ```
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.types import SearchResult
from src.vector_store.base import SearchOptions, VectorStore

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Enumeration of query intents."""

    SEARCH = "search"  # General semantic search
    FILTER = "filter"  # Metadata-based filtering
    COMBINED = "combined"  # Both semantic and metadata filtering
    AGGREGATE = "aggregate"  # Count, group, summarize


class FilterOperator(Enum):
    """ChromaDB filter operators."""

    EQ = "$eq"  # Equal
    NE = "$ne"  # Not equal
    GT = "$gt"  # Greater than
    GTE = "$gte"  # Greater than or equal
    LT = "$lt"  # Less than
    LTE = "$lte"  # Less than or equal
    IN = "$in"  # In list
    NIN = "$nin"  # Not in list
    CONTAINS = "$contains"  # Contains substring
    AND = "$and"  # Logical AND
    OR = "$or"  # Logical OR


class ExecutionStrategy(Enum):
    """Query execution strategies."""

    FILTER_FIRST = "filter_first"  # Apply filters before semantic search
    SEARCH_FIRST = "search_first"  # Do semantic search then filter
    PARALLEL = "parallel"  # Execute both simultaneously


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class Entity:
    """Extracted entity from query.

    Attributes:
        type: Entity type (e.g., "author", "date", "tag")
        value: Entity value
        confidence: Confidence score (0.0 to 1.0)
        position: Position in query string
    """

    type: str
    value: str
    confidence: float
    position: int = 0


@dataclass
class TemporalRef:
    """Temporal reference extracted from query.

    Attributes:
        type: Type of temporal reference (e.g., "absolute", "relative")
        start_date: Start date if range
        end_date: End date if range
        raw_text: Raw text from query
    """

    type: str
    raw_text: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class QueryAnalysis:
    """Result of query analysis.

    Attributes:
        original_query: Original user query
        intent: Query intent
        entities: Extracted entities
        temporal_refs: Temporal references
        attributes: Additional attributes
        confidence: Overall confidence
    """

    original_query: str
    intent: QueryIntent
    entities: List[Entity] = field(default_factory=list)
    temporal_refs: List[TemporalRef] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class FilterCondition:
    """A single filter condition.

    Attributes:
        field: Metadata field to filter on
        operator: Filter operator
        value: Filter value
    """

    field: str
    operator: FilterOperator
    value: Any


@dataclass
class MetadataFilter:
    """Structured metadata filter.

    Attributes:
        conditions: List of filter conditions
        operator: Logical operator to combine conditions
        raw_filter: Raw ChromaDB filter dict
    """

    conditions: List[FilterCondition] = field(default_factory=list)
    operator: FilterOperator = FilterOperator.AND
    raw_filter: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryPlan:
    """Execution plan for a query.

    Attributes:
        strategy: Execution strategy
        filter: Metadata filter to apply
        search_params: Parameters for semantic search
        estimated_selectivity: Estimated filter selectivity
        fallback_enabled: Whether fallback is enabled
    """

    strategy: ExecutionStrategy
    filter: Optional[MetadataFilter]
    search_params: Dict[str, Any] = field(default_factory=dict)
    estimated_selectivity: float = 1.0
    fallback_enabled: bool = True


@dataclass
class SelfQueryResult:
    """Result from self-query retrieval.

    Attributes:
        results: Search results
        query_analysis: Analysis of the query
        filter_used: Filter that was applied
        execution_time_ms: Execution time in milliseconds
        fallback_used: Whether fallback was used
    """

    results: List[SearchResult]
    query_analysis: QueryAnalysis
    filter_used: Optional[MetadataFilter]
    execution_time_ms: float = 0.0
    fallback_used: bool = False


# ============================================================================
# Query Analyzer
# ============================================================================


class QueryAnalyzer:
    """Analyzes natural language queries to extract structured information.

    Extracts entities, temporal references, and determines query intent.

    Example:
        ```python
        analyzer = QueryAnalyzer()
        analysis = await analyzer.analyze(
            "Find documents about Python written by John last year"
        )
        # analysis.entities = [Entity(type="tag", value="python"), ...]
        # analysis.intent = QueryIntent.COMBINED
        ```
    """

    # Common field mappings
    FIELD_SYNONYMS = {
        "author": ["author", "writer", "by", "created by", "written by"],
        "title": ["title", "name", "called"],
        "category": ["category", "type", "kind"],
        "tags": ["tag", "tags", "topic", "about", "subject"],
        "date": ["date", "created", "modified", "published"],
        "source": ["source", "from", "url"],
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
        """Initialize query analyzer.

        Args:
            llm_client: Optional LLM client for advanced analysis
        """
        self.llm_client = llm_client

    async def analyze(self, query: str) -> QueryAnalysis:
        """Analyze a natural language query.

        Args:
            query: User query string

        Returns:
            QueryAnalysis with extracted information
        """
        # Extract entities
        entities = self._extract_entities(query)

        # Extract temporal references
        temporal_refs = self._extract_temporal_refs(query)

        # Determine intent
        intent = self._determine_intent(query, entities)

        # Calculate confidence
        confidence = self._calculate_confidence(entities, temporal_refs)

        return QueryAnalysis(
            original_query=query,
            intent=intent,
            entities=entities,
            temporal_refs=temporal_refs,
            confidence=confidence,
        )

    def _extract_entities(self, query: str) -> List[Entity]:
        """Extract entities from query."""
        entities = []
        query_lower = query.lower()

        # Extract author references
        author_patterns = [
            r"(?:by|written by|created by|author)\s+(\w+)",
            r"(\w+)['']s\s+(?:document|file|article)",
        ]
        for pattern in author_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                value = match.group(1)
                if value and len(value) > 1:
                    entities.append(
                        Entity(
                            type="author",
                            value=value.capitalize(),
                            confidence=0.8,
                            position=match.start(),
                        )
                    )

        # Extract tag/topic references
        tag_patterns = [
            r"(?:about|on|regarding)\s+(\w+)",
            r"(?:tagged|labeled)\s+(?:as\s+)?(\w+)",
        ]
        for pattern in tag_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                value = match.group(1)
                if value:
                    entities.append(
                        Entity(
                            type="tags",
                            value=value.lower(),
                            confidence=0.7,
                            position=match.start(),
                        )
                    )

        # Extract category references
        category_patterns = [
            r"(?:category|type)\s+(?:of\s+)?(\w+)",
        ]
        for pattern in category_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                value = match.group(1)
                if value:
                    entities.append(
                        Entity(
                            type="category",
                            value=value.lower(),
                            confidence=0.75,
                            position=match.start(),
                        )
                    )

        return entities

    def _extract_temporal_refs(self, query: str) -> List[TemporalRef]:
        """Extract temporal references from query."""
        temporal_refs = []
        query_lower = query.lower()
        now = datetime.now()

        for ref_type, pattern in self.TEMPORAL_PATTERNS.items():
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                raw_text = match.group(0)

                # Calculate date ranges
                start_date = None
                end_date = None

                if ref_type == "last_year":
                    start_date = datetime(now.year - 1, 1, 1)
                    end_date = datetime(now.year - 1, 12, 31, 23, 59, 59)
                elif ref_type == "this_year":
                    start_date = datetime(now.year, 1, 1)
                    end_date = now
                elif ref_type == "last_month":
                    if now.month == 1:
                        start_date = datetime(now.year - 1, 12, 1)
                        end_date = datetime(now.year - 1, 12, 31, 23, 59, 59)
                    else:
                        start_date = datetime(now.year, now.month - 1, 1)
                        # Approximate end of month
                        end_date = datetime(now.year, now.month, 1)
                elif ref_type == "this_month":
                    start_date = datetime(now.year, now.month, 1)
                    end_date = now
                elif ref_type == "last_week":
                    week_ago = now - timedelta(days=7)
                    start_date = week_ago - timedelta(days=week_ago.weekday())
                    end_date = start_date + timedelta(days=6, hours=23, minutes=59)
                elif ref_type == "today":
                    start_date = datetime(now.year, now.month, now.day)
                    end_date = now
                elif ref_type == "yesterday":
                    yesterday = now - timedelta(days=1)
                    start_date = datetime(yesterday.year, yesterday.month, yesterday.day)
                    end_date = start_date + timedelta(days=1, seconds=-1)

                temporal_refs.append(
                    TemporalRef(
                        type=ref_type,
                        raw_text=raw_text,
                        start_date=start_date,
                        end_date=end_date,
                    )
                )

        return temporal_refs

    def _determine_intent(self, query: str, entities: List[Entity]) -> QueryIntent:
        """Determine query intent based on query content."""
        query_lower = query.lower()

        # Check for aggregation keywords
        agg_keywords = ["count", "how many", "total", "number of"]
        if any(kw in query_lower for kw in agg_keywords):
            return QueryIntent.AGGREGATE

        # Check if query has both semantic and filter components
        has_semantic = len(query.split()) > 3  # Simple heuristic
        has_filter = len(entities) > 0

        if has_semantic and has_filter:
            return QueryIntent.COMBINED
        elif has_filter:
            return QueryIntent.FILTER
        else:
            return QueryIntent.SEARCH

    def _calculate_confidence(self, entities: List[Entity], temporal_refs: List[TemporalRef]) -> float:
        """Calculate overall confidence score."""
        if not entities and not temporal_refs:
            return 0.3  # Low confidence for pure semantic queries

        entity_confidence = sum(e.confidence for e in entities) / max(len(entities), 1)
        temporal_confidence = 0.8 if temporal_refs else 0.5

        return (entity_confidence + temporal_confidence) / 2


# ============================================================================
# Filter Translator
# ============================================================================


class FilterTranslator:
    """Translates extracted entities into ChromaDB filter format.

    Converts QueryAnalysis into structured metadata filters that can be
    used with ChromaDB's where clause.

    Example:
        ```python
        translator = FilterTranslator()
        analysis = QueryAnalysis(...)
        filter = translator.translate(analysis)
        # filter.raw_filter = {"author": {"$eq": "John"}}
        ```
    """

    def translate(self, analysis: QueryAnalysis) -> Optional[MetadataFilter]:
        """Translate query analysis into metadata filter.

        Args:
            analysis: Query analysis result

        Returns:
            MetadataFilter or None if no filters could be extracted
        """
        conditions = []

        # Convert entities to conditions
        for entity in analysis.entities:
            condition = self._entity_to_condition(entity)
            if condition:
                conditions.append(condition)

        # Convert temporal references to conditions
        for temporal in analysis.temporal_refs:
            condition = self._temporal_to_condition(temporal)
            if condition:
                conditions.append(condition)

        if not conditions:
            return None

        # Build raw filter
        raw_filter = self._build_raw_filter(conditions)

        return MetadataFilter(
            conditions=conditions,
            operator=FilterOperator.AND,
            raw_filter=raw_filter,
        )

    def _entity_to_condition(self, entity: Entity) -> Optional[FilterCondition]:
        """Convert entity to filter condition."""
        if entity.confidence < 0.5:
            return None

        return FilterCondition(
            field=entity.type,
            operator=FilterOperator.EQ,
            value=entity.value,
        )

    def _temporal_to_condition(self, temporal: TemporalRef) -> Optional[FilterCondition]:
        """Convert temporal reference to filter condition."""
        if not temporal.start_date:
            return None

        # For date ranges, we create a GTE condition on start date
        # and optionally an LTE condition on end date
        return FilterCondition(
            field="created_at",
            operator=FilterOperator.GTE,
            value=temporal.start_date.isoformat(),
        )

    def _build_raw_filter(self, conditions: List[FilterCondition]) -> Dict[str, Any]:
        """Build raw ChromaDB filter from conditions."""
        if len(conditions) == 1:
            return self._condition_to_dict(conditions[0])

        # Multiple conditions - use $and
        return {"$and": [self._condition_to_dict(c) for c in conditions]}

    def _condition_to_dict(self, condition: FilterCondition) -> Dict[str, Any]:
        """Convert condition to ChromaDB filter dict."""
        return {condition.field: {condition.operator.value: condition.value}}


# ============================================================================
# Query Planner
# ============================================================================


class QueryPlanner:
    """Plans optimal execution strategy for queries.

    Decides whether to apply filters before or after semantic search,
    or execute both in parallel.

    Example:
        ```python
        planner = QueryPlanner()
        plan = planner.plan(analysis, metadata_filter)
        # plan.strategy = ExecutionStrategy.FILTER_FIRST
        ```
    """

    def plan(
        self,
        analysis: QueryAnalysis,
        filter: Optional[MetadataFilter],
    ) -> QueryPlan:
        """Create execution plan for query.

        Args:
            analysis: Query analysis result
            filter: Optional metadata filter

        Returns:
            QueryPlan with execution strategy
        """
        if not filter:
            # No filters - just do semantic search
            return QueryPlan(
                strategy=ExecutionStrategy.SEARCH_FIRST,
                filter=None,
                estimated_selectivity=1.0,
            )

        # Estimate selectivity
        selectivity = self._estimate_selectivity(filter)

        # Choose strategy based on selectivity
        if selectivity < 0.1:
            # High selectivity - filter first
            strategy = ExecutionStrategy.FILTER_FIRST
        elif selectivity > 0.7:
            # Low selectivity - search first
            strategy = ExecutionStrategy.SEARCH_FIRST
        else:
            # Medium selectivity - parallel
            strategy = ExecutionStrategy.PARALLEL

        return QueryPlan(
            strategy=strategy,
            filter=filter,
            estimated_selectivity=selectivity,
            search_params={"top_k": 10},
        )

    def _estimate_selectivity(self, filter: MetadataFilter) -> float:
        """Estimate filter selectivity (fraction of documents that will match).

        Returns:
            Estimated selectivity (0.0 to 1.0)
        """
        # Simple heuristic based on number and type of conditions
        base_selectivity = 1.0

        for condition in filter.conditions:
            if condition.operator == FilterOperator.EQ:
                # Equality on specific field - assume 10% selectivity
                base_selectivity *= 0.1
            elif condition.operator in (FilterOperator.GT, FilterOperator.GTE):
                # Range query - assume 30% selectivity
                base_selectivity *= 0.3
            elif condition.operator == FilterOperator.IN:
                # In list - depends on list size
                if isinstance(condition.value, list):
                    base_selectivity *= min(0.1 * len(condition.value), 0.5)

        return max(base_selectivity, 0.01)  # Minimum 1% selectivity


# ============================================================================
# Fallback Handler
# ============================================================================


class FallbackHandler:
    """Handles cases where filter-based retrieval is insufficient.

    Falls back to full semantic search when:
    - Filter confidence is too low
    - No results from filtered search
    - Query is primarily semantic in nature

    Example:
        ```python
        fallback = FallbackHandler(threshold=0.5)
        if fallback.should_fallback(analysis, results):
            results = await vector_store.search(query_embedding)
        ```
    """

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        min_results_threshold: int = 1,
    ) -> None:
        """Initialize fallback handler.

        Args:
            confidence_threshold: Minimum confidence to use filters
            min_results_threshold: Minimum results before fallback
        """
        self.confidence_threshold = confidence_threshold
        self.min_results_threshold = min_results_threshold

    def should_fallback(
        self,
        analysis: QueryAnalysis,
        filter_results: List[SearchResult],
    ) -> bool:
        """Determine if fallback to semantic search is needed.

        Args:
            analysis: Query analysis
            filter_results: Results from filter-based search

        Returns:
            True if fallback should be used
        """
        # Check confidence
        if analysis.confidence < self.confidence_threshold:
            return True

        # Check if we got enough results
        if len(filter_results) < self.min_results_threshold:
            return True

        # Check if query is primarily semantic
        if analysis.intent == QueryIntent.SEARCH:
            return True

        return False

    def explain_fallback(self, analysis: QueryAnalysis) -> str:
        """Generate explanation for why fallback was used.

        Args:
            analysis: Query analysis

        Returns:
            Human-readable explanation
        """
        if analysis.confidence < self.confidence_threshold:
            return f"Low filter confidence ({analysis.confidence:.2f}) - using semantic search"

        if analysis.intent == QueryIntent.SEARCH:
            return "Query appears to be primarily semantic - using full search"

        return "Fallback triggered due to insufficient filter results"


# ============================================================================
# Self-Query Retriever
# ============================================================================


class SelfQueryRetriever:
    """Self-querying retriever with natural language to filter translation.

    Combines all components to provide intelligent retrieval that:
    1. Analyzes natural language queries
    2. Extracts metadata filters
    3. Plans optimal execution
    4. Falls back to semantic search when needed

    Example:
        ```python
        retriever = SelfQueryRetriever(
            vector_store=store,
            llm_client=openai_client,
            fallback_threshold=0.5,
        )
        await retriever.initialize()

        result = await retriever.retrieve(
            "Find Python documents by John from last year"
        )
        print(f"Found {len(result.results)} documents")
        print(f"Filter used: {result.filter_used}")
        ```
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: Optional[Any] = None,
        fallback_threshold: float = 0.5,
        min_results_threshold: int = 1,
    ) -> None:
        """Initialize self-query retriever.

        Args:
            vector_store: Vector store to search
            llm_client: Optional LLM client for advanced analysis
            fallback_threshold: Confidence threshold for fallback
            min_results_threshold: Minimum results before fallback
        """
        self.vector_store = vector_store
        self.analyzer = QueryAnalyzer(llm_client)
        self.translator = FilterTranslator()
        self.planner = QueryPlanner()
        self.fallback = FallbackHandler(
            confidence_threshold=fallback_threshold,
            min_results_threshold=min_results_threshold,
        )
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the retriever."""
        # Ensure vector store is initialized
        if hasattr(self.vector_store, "initialize"):
            await self.vector_store.initialize()
        self._initialized = True

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        use_filters: bool = True,
        query_embedding: Optional[List[float]] = None,
    ) -> SelfQueryResult:
        """Retrieve documents using self-querying.

        Args:
            query: Natural language query
            top_k: Number of results to return
            use_filters: Whether to attempt filter extraction
            query_embedding: Pre-computed query embedding (optional)

        Returns:
            SelfQueryResult with documents and metadata
        """
        import time

        start_time = time.time()

        # Analyze query
        analysis = await self.analyzer.analyze(query)

        # Translate to filter
        metadata_filter = None
        if use_filters:
            metadata_filter = self.translator.translate(analysis)

        # Create execution plan
        plan = self.planner.plan(analysis, metadata_filter)

        # Execute based on plan
        results = []
        fallback_used = False

        if plan.filter and plan.strategy == ExecutionStrategy.FILTER_FIRST:
            # Apply filters first
            search_options = SearchOptions(
                top_k=top_k,
                filters=plan.filter.raw_filter if plan.filter else None,
            )
            results = await self._search_with_embedding(query, search_options, query_embedding)

            # Check if fallback needed
            if self.fallback.should_fallback(analysis, results):
                fallback_used = True
                # Fall back to semantic search
                search_options = SearchOptions(top_k=top_k)
                results = await self._search_with_embedding(query, search_options, query_embedding)

        elif plan.strategy == ExecutionStrategy.SEARCH_FIRST:
            # Semantic search first
            search_options = SearchOptions(top_k=top_k)
            results = await self._search_with_embedding(query, search_options, query_embedding)

        else:
            # Default: semantic search with optional filters
            search_options = SearchOptions(
                top_k=top_k,
                filters=plan.filter.raw_filter if plan.filter else None,
            )
            results = await self._search_with_embedding(query, search_options, query_embedding)

        execution_time = (time.time() - start_time) * 1000

        return SelfQueryResult(
            results=results,
            query_analysis=analysis,
            filter_used=plan.filter,
            execution_time_ms=execution_time,
            fallback_used=fallback_used,
        )

    async def _search_with_embedding(
        self,
        query: str,
        options: SearchOptions,
        query_embedding: Optional[List[float]] = None,
    ) -> List[SearchResult]:
        """Search with optional pre-computed embedding."""
        if query_embedding is not None:
            return await self.vector_store.search(query_embedding, options)

        # If no embedding provided, we need to generate one
        # This is a simplified version - in production, use embedding provider
        # For now, return empty results
        logger.warning("No query embedding provided - returning empty results")
        return []

    def get_explanation(self, result: SelfQueryResult) -> str:
        """Get human-readable explanation of retrieval.

        Args:
            result: Self-query result

        Returns:
            Explanation string
        """
        lines = [
            f"Query: {result.query_analysis.original_query}",
            f"Intent: {result.query_analysis.intent.value}",
            f"Confidence: {result.query_analysis.confidence:.2f}",
        ]

        if result.filter_used:
            lines.append(f"Filter: {result.filter_used.raw_filter}")

        if result.fallback_used:
            lines.append("Fallback: Used semantic search")

        lines.append(f"Results: {len(result.results)} documents")
        lines.append(f"Time: {result.execution_time_ms:.2f}ms")

        return "\n".join(lines)
