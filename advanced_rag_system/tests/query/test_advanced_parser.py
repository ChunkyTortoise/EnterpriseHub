"""Tests for Advanced Parser module."""


import pytest
from src.core.exceptions import RetrievalError
from src.query.advanced_parser import (
    AdvancedQueryParser,
    ParsedQuery,
    ParserConfig,
    QueryComplexity,
    QueryProcessingPipeline,
    QueryUnderstandingResult,
)
from src.query.entity_extractor import EntityType
from src.query.intent_classifier_v2 import IntentType


@pytest.mark.integration


class TestParsedQuery:
    """Test ParsedQuery class."""

    def test_parsed_query_creation(self):
        """Test creating a parsed query."""
        from src.query.temporal_processor import TemporalContext

        parsed = ParsedQuery(
            original_query="Show me houses",
            normalized_query="show me houses",
            tokens=["show", "me", "houses"],
            intents=[IntentType.PROPERTY_SEARCH],
            primary_intent=IntentType.PROPERTY_SEARCH,
            entities=[],
            temporal_context=TemporalContext(),
            complexity=QueryComplexity.SIMPLE,
        )

        assert parsed.original_query == "Show me houses"
        assert parsed.normalized_query == "show me houses"
        assert parsed.primary_intent == IntentType.PROPERTY_SEARCH

    def test_parsed_query_to_dict(self):
        """Test parsed query serialization."""
        from src.query.temporal_processor import TemporalContext

        parsed = ParsedQuery(
            original_query="test",
            normalized_query="test",
            tokens=["test"],
            intents=[IntentType.INFORMATIONAL],
            primary_intent=IntentType.INFORMATIONAL,
            entities=[],
            temporal_context=TemporalContext(),
            complexity=QueryComplexity.SIMPLE,
        )

        d = parsed.to_dict()
        assert d["original_query"] == "test"
        assert d["complexity"] == "simple"
        assert "intents" in d


class TestQueryUnderstandingResult:
    """Test QueryUnderstandingResult class."""

    def test_result_creation(self):
        """Test creating a result."""
        from src.query.entity_extractor import KnowledgeGraphPrep
        from src.query.intent_classifier_v2 import (
            IntentClassificationResult,
            MultiLabelResult,
        )
        from src.query.temporal_processor import TemporalContext

        result = QueryUnderstandingResult(
            parsed_query=ParsedQuery(
                original_query="test",
                normalized_query="test",
                tokens=["test"],
                intents=[IntentType.INFORMATIONAL],
                primary_intent=IntentType.INFORMATIONAL,
                entities=[],
                temporal_context=TemporalContext(),
                complexity=QueryComplexity.SIMPLE,
            ),
            intent_result=IntentClassificationResult(
                primary_intent=IntentType.INFORMATIONAL,
                confidence=0.9,
                raw_confidence=0.9,
                features={},
            ),
            multi_label_result=MultiLabelResult(
                intents=[IntentType.INFORMATIONAL],
                primary_intent=IntentType.INFORMATIONAL,
                confidence_scores={IntentType.INFORMATIONAL: 0.9},
                coverage_score=0.9,
            ),
            kg_prep=KnowledgeGraphPrep(entities=[]),
            confidence=0.9,
            processing_time_ms=100.0,
        )

        assert result.confidence == 0.9
        assert result.processing_time_ms == 100.0

    def test_result_to_dict(self):
        """Test result serialization."""
        from src.query.entity_extractor import KnowledgeGraphPrep
        from src.query.intent_classifier_v2 import (
            IntentClassificationResult,
            MultiLabelResult,
        )
        from src.query.temporal_processor import TemporalContext

        result = QueryUnderstandingResult(
            parsed_query=ParsedQuery(
                original_query="test",
                normalized_query="test",
                tokens=["test"],
                intents=[IntentType.INFORMATIONAL],
                primary_intent=IntentType.INFORMATIONAL,
                entities=[],
                temporal_context=TemporalContext(),
                complexity=QueryComplexity.SIMPLE,
            ),
            intent_result=IntentClassificationResult(
                primary_intent=IntentType.INFORMATIONAL,
                confidence=0.9,
                raw_confidence=0.9,
                features={},
            ),
            multi_label_result=MultiLabelResult(
                intents=[IntentType.INFORMATIONAL],
                primary_intent=IntentType.INFORMATIONAL,
                confidence_scores={IntentType.INFORMATIONAL: 0.9},
                coverage_score=0.9,
            ),
            kg_prep=KnowledgeGraphPrep(entities=[]),
            confidence=0.9,
        )

        d = result.to_dict()
        assert "parsed_query" in d
        assert "intent_result" in d
        assert "confidence" in d


class TestAdvancedQueryParser:
    """Test AdvancedQueryParser functionality."""

    @pytest.fixture
    def parser(self):
        """Create an advanced parser."""
        config = ParserConfig(domain="real_estate")
        return AdvancedQueryParser(config=config)

    def test_parser_initialization(self, parser):
        """Test parser initialization."""
        assert parser.config.domain == "real_estate"
        assert parser.intent_classifier is not None
        assert parser.entity_extractor is not None
        assert parser.temporal_processor is not None

    def test_parse_simple_query(self, parser):
        """Test parsing a simple query."""
        result = parser.parse("Show me houses")

        assert isinstance(result, QueryUnderstandingResult)
        assert result.parsed_query.original_query == "Show me houses"
        assert result.confidence > 0
        assert result.processing_time_ms > 0

    def test_parse_property_search(self, parser):
        """Test parsing property search query."""
        result = parser.parse("Show me 3-bedroom houses in Rancho Cucamonga")

        assert result.parsed_query.primary_intent == IntentType.PROPERTY_SEARCH
        assert len(result.parsed_query.entities) > 0

        # Check for expected entities
        entity_types = {e.type for e in result.parsed_query.entities}
        assert EntityType.BEDROOMS in entity_types
        assert EntityType.CITY in entity_types

    def test_parse_with_price(self, parser):
        """Test parsing query with price."""
        result = parser.parse("Homes under $800k in Rancho Cucamonga")

        entity_types = {e.type for e in result.parsed_query.entities}
        assert EntityType.MONEY in entity_types

    def test_parse_with_temporal(self, parser):
        """Test parsing query with temporal constraints."""
        result = parser.parse("Show me houses listed last week")

        assert len(result.parsed_query.temporal_context.constraints) > 0
        assert result.parsed_query.temporal_context.recency_preference > 0.5

    def test_parse_buying_intent(self, parser):
        """Test parsing buying intent query."""
        result = parser.parse("I want to buy a house in Rancho Cucamonga")

        assert result.parsed_query.primary_intent == IntentType.BUYING_INTENT

    def test_parse_selling_intent(self, parser):
        """Test parsing selling intent query."""
        result = parser.parse("What's my home worth?")

        assert result.parsed_query.primary_intent == IntentType.SELLING_INTENT

    def test_parse_multi_intent(self, parser):
        """Test parsing query with multiple intents."""
        result = parser.parse("I'm looking to buy a 3-bedroom house and schedule a showing")

        assert len(result.multi_label_result.intents) >= 1
        assert IntentType.BUYING_INTENT in result.multi_label_result.intents

    def test_parse_complex_query(self, parser):
        """Test parsing complex query."""
        result = parser.parse(
            "Show me 3-bedroom, 2-bathroom houses under $800k in Rancho Cucamonga "
            "in the Etiwanda school district listed last week"
        )

        assert result.parsed_query.complexity == QueryComplexity.COMPLEX
        assert len(result.parsed_query.entities) >= 5

    def test_retrieval_params_generation(self, parser):
        """Test retrieval parameters generation."""
        result = parser.parse("3-bedroom houses in Rancho Cucamonga under $800k")

        assert "filters" in result.retrieval_params
        assert "boost" in result.retrieval_params
        assert "limit" in result.retrieval_params

        filters = result.retrieval_params["filters"]
        assert "bedrooms" in filters
        assert "city" in filters

    def test_retrieval_params_with_temporal(self, parser):
        """Test retrieval params include temporal filters."""
        result = parser.parse("Houses listed last week in Rancho Cucamonga")

        filters = result.retrieval_params["filters"]
        assert "date_from" in filters or "date_to" in filters

    def test_retrieval_params_recency_boost(self, parser):
        """Test retrieval params include recency boost."""
        result = parser.parse("Recent listings in Rancho Cucamonga")

        if "recency" in result.retrieval_params.get("boost", {}):
            assert result.retrieval_params["boost"]["recency"]["enabled"] is True

    def test_complexity_calculation_simple(self, parser):
        """Test simple complexity detection."""
        result = parser.parse("Show houses")

        assert result.parsed_query.complexity == QueryComplexity.SIMPLE

    def test_complexity_calculation_moderate(self, parser):
        """Test moderate complexity detection."""
        result = parser.parse("3-bedroom houses in Rancho Cucamonga")

        assert result.parsed_query.complexity in [
            QueryComplexity.SIMPLE,
            QueryComplexity.MODERATE,
        ]

    def test_normalize_query(self, parser):
        """Test query normalization."""
        normalized = parser._normalize_query("I'm looking for houses")

        assert "i'm" not in normalized
        assert "i am" in normalized
        assert normalized == normalized.lower()

    def test_tokenize(self, parser):
        """Test query tokenization."""
        tokens = parser._tokenize("show me houses")

        assert "show" in tokens
        assert "me" in tokens
        assert "houses" in tokens

    def test_parse_empty_query_raises_error(self, parser):
        """Test that empty query raises error."""
        with pytest.raises(RetrievalError):
            parser.parse("")

    def test_parse_whitespace_query_raises_error(self, parser):
        """Test that whitespace query raises error."""
        with pytest.raises(RetrievalError):
            parser.parse("   ")

    def test_kg_prep_in_result(self, parser):
        """Test that KG prep is included in result."""
        result = parser.parse("3-bedroom house in Rancho Cucamonga")

        assert result.kg_prep is not None
        assert len(result.kg_prep.entities) > 0
        assert len(result.kg_prep.kg_nodes) > 0

    def test_overall_confidence_calculation(self, parser):
        """Test overall confidence calculation."""
        result = parser.parse("Show me houses in Rancho Cucamonga")

        assert 0 <= result.confidence <= 1

    def test_batch_parse(self, parser):
        """Test batch parsing."""
        queries = [
            "Show me houses",
            "I want to buy",
            "What's the market like?",
        ]

        results = parser.batch_parse(queries)

        assert len(results) == 3
        assert all(isinstance(r, QueryUnderstandingResult) for r in results)

    def test_batch_parse_with_error(self, parser):
        """Test batch parsing handles errors gracefully."""
        queries = ["Show me houses", "", "Valid query"]

        results = parser.batch_parse(queries)

        assert len(results) == 3
        # Empty query should have error metadata
        assert "error" in results[1].parsed_query.metadata

    def test_get_stats(self, parser):
        """Test getting parser statistics."""
        stats = parser.get_stats()

        assert "config" in stats
        assert "classifier" in stats
        assert "extractor" in stats


class TestQueryProcessingPipeline:
    """Test QueryProcessingPipeline functionality."""

    @pytest.fixture
    def pipeline(self):
        """Create a processing pipeline."""
        return QueryProcessingPipeline()

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert len(pipeline.stages) == 0
        assert pipeline.parser is not None

    def test_add_stage(self, pipeline):
        """Test adding stages to pipeline."""

        def stage1(data, context):
            return data + "1"

        def stage2(data, context):
            return data + "2"

        pipeline.add_stage("stage1", stage1).add_stage("stage2", stage2)

        assert len(pipeline.stages) == 2
        assert pipeline.stages[0][0] == "stage1"
        assert pipeline.stages[1][0] == "stage2"

    def test_process_through_stages(self, pipeline):
        """Test processing through multiple stages."""

        def stage1(data, context):
            return data.upper()

        def stage2(data, context):
            return data + "!"

        pipeline.add_stage("upper", stage1).add_stage("exclaim", stage2)

        result = pipeline.process("hello")

        assert result["final_output"] == "HELLO!"
        assert result["stages"]["upper"]["status"] == "success"
        assert result["stages"]["exclaim"]["status"] == "success"

    def test_process_with_error(self, pipeline):
        """Test handling errors in pipeline."""

        def good_stage(data, context):
            return data + "1"

        def bad_stage(data, context):
            raise ValueError("Test error")

        pipeline.add_stage("good", good_stage).add_stage("bad", bad_stage)

        result = pipeline.process("test")

        assert result["stages"]["good"]["status"] == "success"
        assert result["stages"]["bad"]["status"] == "error"
        assert "error" in result["stages"]["bad"]

    def test_process_with_context(self, pipeline):
        """Test processing with context."""

        def context_stage(data, context):
            context["modified"] = True
            return data

        pipeline.add_stage("context", context_stage)

        context = {}
        result = pipeline.process("test", context)

        assert context["modified"] is True
        assert result["final_output"] == "test"

    def test_process_with_parser(self, pipeline):
        """Test processing with built-in parser."""
        result = pipeline.process_with_parser("Show me houses in Rancho Cucamonga")

        assert isinstance(result, QueryUnderstandingResult)
        assert result.parsed_query.primary_intent == IntentType.PROPERTY_SEARCH


class TestParserConfig:
    """Test parser configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = ParserConfig()

        assert config.enable_multi_label is True
        assert config.enable_kg_prep is True
        assert config.min_confidence == 0.5
        assert config.domain == "real_estate"

    def test_custom_config(self):
        """Test custom configuration."""
        config = ParserConfig(
            enable_multi_label=False,
            enable_kg_prep=False,
            min_confidence=0.7,
            domain="general",
        )

        assert config.enable_multi_label is False
        assert config.enable_kg_prep is False
        assert config.min_confidence == 0.7
        assert config.domain == "general"


class TestQueryComplexity:
    """Test query complexity enum."""

    def test_complexity_values(self):
        """Test complexity enum values."""
        assert QueryComplexity.SIMPLE.value == "simple"
        assert QueryComplexity.MODERATE.value == "moderate"
        assert QueryComplexity.COMPLEX.value == "complex"


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_property_search(self):
        """Test full pipeline with property search."""
        parser = AdvancedQueryParser()

        result = parser.parse(
            "I'm looking for a 3-bedroom, 2-bathroom house under $900k "
            "in the Etiwanda school district in Rancho Cucamonga. "
            "I'd like to schedule a showing this weekend."
        )

        # Verify intents
        assert IntentType.BUYING_INTENT in result.multi_label_result.intents
        assert IntentType.PROPERTY_SEARCH in result.multi_label_result.intents
        assert IntentType.SHOWING_REQUEST in result.multi_label_result.intents
        assert IntentType.SCHOOL_DISTRICT_QUERY in result.multi_label_result.intents

        # Verify entities
        entity_types = {e.type for e in result.parsed_query.entities}
        assert EntityType.BEDROOMS in entity_types
        assert EntityType.BATHROOMS in entity_types
        assert EntityType.CITY in entity_types
        assert EntityType.SCHOOL_DISTRICT in entity_types
        assert EntityType.MONEY in entity_types

        # Verify complexity
        assert result.parsed_query.complexity == QueryComplexity.COMPLEX

        # Verify confidence
        assert result.confidence > 0.5

        # Verify retrieval params
        assert "filters" in result.retrieval_params
        assert "bedrooms" in result.retrieval_params["filters"]
        assert "city" in result.retrieval_params["filters"]

        # Verify KG prep
        assert len(result.kg_prep.kg_nodes) > 0
        assert len(result.kg_prep.relationships) > 0

    def test_full_pipeline_market_analysis(self):
        """Test full pipeline with market analysis query."""
        parser = AdvancedQueryParser()

        result = parser.parse("What's the market trend in Rancho Cucamonga over the past year?")

        # Verify intent
        assert result.parsed_query.primary_intent == IntentType.MARKET_ANALYSIS

        # Verify temporal context
        assert result.parsed_query.temporal_context.temporal_focus == "past"

        # Verify entities
        entity_types = {e.type for e in result.parsed_query.entities}
        assert EntityType.CITY in entity_types

    def test_full_pipeline_investment_research(self):
        """Test full pipeline with investment research query."""
        parser = AdvancedQueryParser()

        result = parser.parse("Show me investment properties with good cash flow in Rancho Cucamonga")

        # Verify intent
        assert result.parsed_query.primary_intent == IntentType.INVESTMENT_RESEARCH

        # Verify entities
        entity_types = {e.type for e in result.parsed_query.entities}
        assert EntityType.CITY in entity_types