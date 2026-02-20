"""Tests for self-querying retrieval system."""

from uuid import uuid4

import pytest
from src.core.types import DocumentChunk, SearchResult
from src.retrieval.self_query import (
    Entity,
    ExecutionStrategy,
    FallbackHandler,
    FilterCondition,
    FilterOperator,
    FilterTranslator,
    MetadataFilter,
    QueryAnalysis,
    QueryAnalyzer,
    QueryIntent,
    QueryPlanner,
    SelfQueryResult,
    SelfQueryRetriever,
    TemporalRef,
)


@pytest.mark.integration

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def query_analyzer():
    """Create query analyzer."""
    return QueryAnalyzer()


@pytest.fixture
def filter_translator():
    """Create filter translator."""
    return FilterTranslator()


@pytest.fixture
def query_planner():
    """Create query planner."""
    return QueryPlanner()


@pytest.fixture
def fallback_handler():
    """Create fallback handler."""
    return FallbackHandler(
        confidence_threshold=0.5,
        min_results_threshold=1,
    )


@pytest.fixture
def mock_vector_store():
    """Create mock vector store for testing."""

    class MockVectorStore:
        def __init__(self):
            self.documents = []

        async def initialize(self):
            pass

        async def search(self, embedding, options=None):
            # Return mock results
            return [
                SearchResult(
                    chunk=DocumentChunk(
                        document_id=uuid4(),
                        content="Test document",
                        embedding=[0.1, 0.2, 0.3],
                    ),
                    score=0.9,
                    rank=1,
                )
            ]

        async def add_chunks(self, chunks):
            self.documents.extend(chunks)

    return MockVectorStore()


# ============================================================================
# QueryAnalyzer Tests
# ============================================================================


class TestQueryAnalyzer:
    """Test cases for QueryAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyze_simple_query(self, query_analyzer):
        """Test analyzing a simple query."""
        analysis = await query_analyzer.analyze("Python programming")

        assert analysis.original_query == "Python programming"
        assert analysis.intent == QueryIntent.SEARCH
        assert analysis.confidence > 0

    @pytest.mark.asyncio
    async def test_extract_author_entity(self, query_analyzer):
        """Test extracting author entity."""
        analysis = await query_analyzer.analyze("documents by John")

        assert len(analysis.entities) >= 1
        author_entities = [e for e in analysis.entities if e.type == "author"]
        assert len(author_entities) >= 1
        assert any("John" in e.value for e in author_entities)

    @pytest.mark.asyncio
    async def test_extract_tag_entity(self, query_analyzer):
        """Test extracting tag/topic entity."""
        analysis = await query_analyzer.analyze("documents about Python")

        tag_entities = [e for e in analysis.entities if e.type == "tags"]
        assert len(tag_entities) >= 1
        assert any("python" in e.value.lower() for e in tag_entities)

    @pytest.mark.asyncio
    async def test_extract_temporal_last_year(self, query_analyzer):
        """Test extracting temporal reference - last year."""
        analysis = await query_analyzer.analyze("documents from last year")

        assert len(analysis.temporal_refs) >= 1
        assert any("last year" in t.raw_text.lower() for t in analysis.temporal_refs)

    @pytest.mark.asyncio
    async def test_extract_temporal_this_month(self, query_analyzer):
        """Test extracting temporal reference - this month."""
        analysis = await query_analyzer.analyze("documents this month")

        assert len(analysis.temporal_refs) >= 1

    @pytest.mark.asyncio
    async def test_determine_filter_intent(self, query_analyzer):
        """Test determining FILTER intent."""
        analysis = await query_analyzer.analyze("by author John category Python")

        assert analysis.intent == QueryIntent.FILTER

    @pytest.mark.asyncio
    async def test_determine_combined_intent(self, query_analyzer):
        """Test determining COMBINED intent."""
        analysis = await query_analyzer.analyze("What are the benefits of Python programming by John")

        assert analysis.intent in [QueryIntent.COMBINED, QueryIntent.SEARCH]

    @pytest.mark.asyncio
    async def test_determine_aggregate_intent(self, query_analyzer):
        """Test determining AGGREGATE intent."""
        analysis = await query_analyzer.analyze("how many documents by John")

        assert analysis.intent == QueryIntent.AGGREGATE

    @pytest.mark.asyncio
    async def test_calculate_confidence_with_entities(self, query_analyzer):
        """Test confidence calculation with entities."""
        analysis = await query_analyzer.analyze("documents by John about Python")

        assert analysis.confidence > 0.5

    @pytest.mark.asyncio
    async def test_calculate_confidence_without_entities(self, query_analyzer):
        """Test confidence calculation without entities."""
        analysis = await query_analyzer.analyze("hello world")

        assert analysis.confidence < 0.5


# ============================================================================
# FilterTranslator Tests
# ============================================================================


class TestFilterTranslator:
    """Test cases for FilterTranslator."""

    @pytest.mark.asyncio
    async def test_translate_author_filter(self, filter_translator):
        """Test translating author entity to filter."""
        analysis = QueryAnalysis(
            original_query="by John",
            intent=QueryIntent.FILTER,
            entities=[Entity(type="author", value="John", confidence=0.8)],
        )

        filter = filter_translator.translate(analysis)

        assert filter is not None
        assert len(filter.conditions) == 1
        assert filter.conditions[0].field == "author"
        assert filter.conditions[0].value == "John"
        assert filter.conditions[0].operator == FilterOperator.EQ

    @pytest.mark.asyncio
    async def test_translate_multiple_entities(self, filter_translator):
        """Test translating multiple entities."""
        analysis = QueryAnalysis(
            original_query="by John about Python",
            intent=QueryIntent.FILTER,
            entities=[
                Entity(type="author", value="John", confidence=0.8),
                Entity(type="tags", value="python", confidence=0.7),
            ],
        )

        filter = filter_translator.translate(analysis)

        assert filter is not None
        assert len(filter.conditions) == 2

    @pytest.mark.asyncio
    async def test_translate_with_temporal(self, filter_translator):
        """Test translating with temporal reference."""
        from datetime import datetime

        analysis = QueryAnalysis(
            original_query="from last year",
            intent=QueryIntent.FILTER,
            temporal_refs=[
                TemporalRef(
                    type="last_year",
                    raw_text="last year",
                    start_date=datetime(2024, 1, 1),
                )
            ],
        )

        filter = filter_translator.translate(analysis)

        assert filter is not None
        assert any(c.field == "created_at" for c in filter.conditions)

    @pytest.mark.asyncio
    async def test_translate_no_entities(self, filter_translator):
        """Test translating with no entities."""
        analysis = QueryAnalysis(
            original_query="hello world",
            intent=QueryIntent.SEARCH,
            entities=[],
        )

        filter = filter_translator.translate(analysis)

        assert filter is None

    def test_build_raw_filter_single_condition(self, filter_translator):
        """Test building raw filter with single condition."""
        conditions = [FilterCondition(field="author", operator=FilterOperator.EQ, value="John")]

        raw = filter_translator._build_raw_filter(conditions)

        assert raw == {"author": {"$eq": "John"}}

    def test_build_raw_filter_multiple_conditions(self, filter_translator):
        """Test building raw filter with multiple conditions."""
        conditions = [
            FilterCondition(field="author", operator=FilterOperator.EQ, value="John"),
            FilterCondition(field="tags", operator=FilterOperator.EQ, value="python"),
        ]

        raw = filter_translator._build_raw_filter(conditions)

        assert "$and" in raw
        assert len(raw["$and"]) == 2


# ============================================================================
# QueryPlanner Tests
# ============================================================================


class TestQueryPlanner:
    """Test cases for QueryPlanner."""

    def test_plan_no_filter(self, query_planner):
        """Test planning with no filter."""
        analysis = QueryAnalysis(
            original_query="test",
            intent=QueryIntent.SEARCH,
        )

        plan = query_planner.plan(analysis, None)

        assert plan.strategy == ExecutionStrategy.SEARCH_FIRST
        assert plan.filter is None

    def test_plan_high_selectivity(self, query_planner):
        """Test planning with high selectivity filter."""
        analysis = QueryAnalysis(
            original_query="by John",
            intent=QueryIntent.FILTER,
        )
        filter = MetadataFilter(
            conditions=[
                FilterCondition(field="author", operator=FilterOperator.EQ, value="John"),
                FilterCondition(field="id", operator=FilterOperator.EQ, value="123"),
            ]
        )

        plan = query_planner.plan(analysis, filter)

        assert plan.strategy == ExecutionStrategy.FILTER_FIRST
        assert plan.filter is not None

    def test_plan_low_selectivity(self, query_planner):
        """Test planning with low selectivity filter."""
        analysis = QueryAnalysis(
            original_query="recent documents",
            intent=QueryIntent.FILTER,
        )
        filter = MetadataFilter(
            conditions=[
                FilterCondition(field="date", operator=FilterOperator.GTE, value="2024-01-01"),
            ]
        )

        plan = query_planner.plan(analysis, filter)

        assert plan.strategy == ExecutionStrategy.SEARCH_FIRST

    def test_plan_medium_selectivity(self, query_planner):
        """Test planning with medium selectivity filter."""
        analysis = QueryAnalysis(
            original_query="by John recent",
            intent=QueryIntent.COMBINED,
        )
        filter = MetadataFilter(
            conditions=[
                FilterCondition(field="author", operator=FilterOperator.EQ, value="John"),
            ]
        )

        plan = query_planner.plan(analysis, filter)

        assert plan.strategy in [ExecutionStrategy.PARALLEL, ExecutionStrategy.FILTER_FIRST]

    def test_estimate_selectivity_equality(self, query_planner):
        """Test selectivity estimation for equality."""
        filter = MetadataFilter(
            conditions=[
                FilterCondition(field="author", operator=FilterOperator.EQ, value="John"),
            ]
        )

        selectivity = query_planner._estimate_selectivity(filter)

        assert selectivity == 0.1  # 10% for equality

    def test_estimate_selectivity_range(self, query_planner):
        """Test selectivity estimation for range."""
        filter = MetadataFilter(
            conditions=[
                FilterCondition(field="date", operator=FilterOperator.GTE, value="2024-01-01"),
            ]
        )

        selectivity = query_planner._estimate_selectivity(filter)

        assert selectivity == 0.3  # 30% for range


# ============================================================================
# FallbackHandler Tests
# ============================================================================


class TestFallbackHandler:
    """Test cases for FallbackHandler."""

    def test_should_fallback_low_confidence(self, fallback_handler):
        """Test fallback triggered by low confidence."""
        analysis = QueryAnalysis(
            original_query="test",
            intent=QueryIntent.SEARCH,
            confidence=0.3,  # Below threshold
        )
        results = []

        should_fallback = fallback_handler.should_fallback(analysis, results)

        assert should_fallback is True

    def test_should_fallback_no_results(self, fallback_handler):
        """Test fallback triggered by no results."""
        analysis = QueryAnalysis(
            original_query="test",
            intent=QueryIntent.FILTER,
            confidence=0.8,
        )
        results = []

        should_fallback = fallback_handler.should_fallback(analysis, results)

        assert should_fallback is True

    def test_should_fallback_search_intent(self, fallback_handler):
        """Test fallback triggered by search intent."""
        analysis = QueryAnalysis(
            original_query="test",
            intent=QueryIntent.SEARCH,
            confidence=0.8,
        )
        results = [SearchResult(chunk=None, score=0.9, rank=1)]

        should_fallback = fallback_handler.should_fallback(analysis, results)

        assert should_fallback is True

    def test_should_not_fallback(self, fallback_handler):
        """Test no fallback needed."""
        analysis = QueryAnalysis(
            original_query="by John",
            intent=QueryIntent.FILTER,
            confidence=0.8,
        )
        results = [
            SearchResult(chunk=None, score=0.9, rank=1),
            SearchResult(chunk=None, score=0.8, rank=2),
        ]

        should_fallback = fallback_handler.should_fallback(analysis, results)

        assert should_fallback is False

    def test_explain_fallback_low_confidence(self, fallback_handler):
        """Test explanation for low confidence fallback."""
        analysis = QueryAnalysis(
            original_query="test",
            intent=QueryIntent.SEARCH,
            confidence=0.3,
        )

        explanation = fallback_handler.explain_fallback(analysis)

        assert "Low filter confidence" in explanation

    def test_explain_fallback_search_intent(self, fallback_handler):
        """Test explanation for search intent fallback."""
        analysis = QueryAnalysis(
            original_query="test",
            intent=QueryIntent.SEARCH,
            confidence=0.8,
        )

        explanation = fallback_handler.explain_fallback(analysis)

        assert "semantic" in explanation.lower()


# ============================================================================
# SelfQueryRetriever Tests
# ============================================================================


class TestSelfQueryRetriever:
    """Test cases for SelfQueryRetriever."""

    @pytest.mark.asyncio
    async def test_retrieve_with_embedding(self, mock_vector_store):
        """Test retrieval with pre-computed embedding."""
        retriever = SelfQueryRetriever(
            vector_store=mock_vector_store,
            fallback_threshold=0.5,
        )
        await retriever.initialize()

        result = await retriever.retrieve(
            query="Python documents by John",
            query_embedding=[0.1, 0.2, 0.3],
        )

        assert isinstance(result, SelfQueryResult)
        assert result.query_analysis.original_query == "Python documents by John"
        assert len(result.results) == 1

    @pytest.mark.asyncio
    async def test_retrieve_without_embedding(self, mock_vector_store):
        """Test retrieval without pre-computed embedding."""
        retriever = SelfQueryRetriever(
            vector_store=mock_vector_store,
            fallback_threshold=0.5,
        )
        await retriever.initialize()

        result = await retriever.retrieve(
            query="test query",
        )

        assert isinstance(result, SelfQueryResult)
        # Without embedding, should return empty results
        assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_extracts_filter(self, mock_vector_store):
        """Test that filter is extracted from query."""
        retriever = SelfQueryRetriever(
            vector_store=mock_vector_store,
            fallback_threshold=0.5,
        )
        await retriever.initialize()

        result = await retriever.retrieve(
            query="documents by John about Python",
            query_embedding=[0.1, 0.2, 0.3],
        )

        assert result.filter_used is not None
        assert len(result.filter_used.conditions) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_no_filters(self, mock_vector_store):
        """Test retrieval with filters disabled."""
        retriever = SelfQueryRetriever(
            vector_store=mock_vector_store,
            fallback_threshold=0.5,
        )
        await retriever.initialize()

        result = await retriever.retrieve(
            query="documents by John",
            use_filters=False,
            query_embedding=[0.1, 0.2, 0.3],
        )

        assert result.filter_used is None

    def test_get_explanation(self, mock_vector_store):
        """Test getting explanation of retrieval."""
        retriever = SelfQueryRetriever(vector_store=mock_vector_store)

        result = SelfQueryResult(
            results=[],
            query_analysis=QueryAnalysis(
                original_query="test",
                intent=QueryIntent.FILTER,
                confidence=0.8,
            ),
            filter_used=MetadataFilter(
                conditions=[FilterCondition(field="author", operator=FilterOperator.EQ, value="John")]
            ),
            execution_time_ms=100.0,
        )

        explanation = retriever.get_explanation(result)

        assert "Query: test" in explanation
        assert "Intent: filter" in explanation
        assert "Confidence: 0.8" in explanation
        assert "Time: 100.0ms" in explanation


# ============================================================================
# Integration Tests
# ============================================================================


class TestSelfQueryIntegration:
    """Integration tests for self-querying system."""

    @pytest.mark.asyncio
    async def test_end_to_end_filter_extraction(self):
        """Test end-to-end filter extraction and planning."""
        analyzer = QueryAnalyzer()
        translator = FilterTranslator()
        planner = QueryPlanner()

        # Analyze query
        analysis = await analyzer.analyze("documents by John about Python from last year")

        # Translate to filter
        filter = translator.translate(analysis)

        # Create plan
        plan = planner.plan(analysis, filter)

        # Verify results
        assert analysis.intent in [QueryIntent.COMBINED, QueryIntent.FILTER]
        assert len(analysis.entities) >= 2  # author and tag
        assert len(analysis.temporal_refs) >= 1
        assert filter is not None
        assert len(filter.conditions) >= 2
        assert plan.filter is not None

    @pytest.mark.asyncio
    async def test_complex_query_analysis(self):
        """Test analysis of complex query."""
        analyzer = QueryAnalyzer()

        analysis = await analyzer.analyze("What are the latest Python tutorials written by Alice or Bob this month")

        # Should extract multiple entities
        assert len(analysis.entities) >= 2

        # Should have temporal reference
        assert len(analysis.temporal_refs) >= 1

        # Should be combined intent (semantic + filter)
        assert analysis.intent in [QueryIntent.COMBINED, QueryIntent.SEARCH]

    def test_filter_operators(self):
        """Test all filter operators."""
        operators = [
            FilterOperator.EQ,
            FilterOperator.NE,
            FilterOperator.GT,
            FilterOperator.GTE,
            FilterOperator.LT,
            FilterOperator.LTE,
            FilterOperator.IN,
            FilterOperator.NIN,
            FilterOperator.CONTAINS,
            FilterOperator.AND,
            FilterOperator.OR,
        ]

        for op in operators:
            assert op.value.startswith("$")

    def test_execution_strategies(self):
        """Test execution strategy values."""
        strategies = [
            ExecutionStrategy.FILTER_FIRST,
            ExecutionStrategy.SEARCH_FIRST,
            ExecutionStrategy.PARALLEL,
        ]

        for strategy in strategies:
            assert isinstance(strategy.value, str)