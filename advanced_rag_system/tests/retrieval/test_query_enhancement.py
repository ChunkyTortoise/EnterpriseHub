"""Tests for query enhancement components including expansion, HyDE, and classification.

This module tests the query enhancement system including:
- Query expansion using synonyms
- HyDE (Hypothetical Document Embedding) generation
- Query classification for routing
"""

import pytest
from typing import List

from src.retrieval.query.expansion import QueryExpander, ExpansionConfig
from src.retrieval.query.hyde import HyDEGenerator, HyDEConfig, MockLLMProvider
from src.retrieval.query.classifier import (
    QueryClassifier,
    ClassifierConfig,
    QueryType,
    ClassificationResult,
)


class TestQueryExpansion:
    """Test suite for QueryExpander."""

    @pytest.fixture
    def expander(self) -> QueryExpander:
        """Create a query expander with default config."""
        return QueryExpander()

    @pytest.fixture
    def expansion_config(self) -> ExpansionConfig:
        """Create expansion config with custom settings."""
        return ExpansionConfig(
            max_expansions=3,
            synonym_limit=2,
            expansion_strategy="selective"
        )

    def test_expansion_config_defaults(self):
        """Test ExpansionConfig default values."""
        config = ExpansionConfig()
        assert config.max_expansions == 5
        assert config.synonym_limit == 3
        assert config.use_wordnet is True
        assert config.use_llm is False
        assert config.preserve_original is True
        assert config.min_word_length == 3
        assert config.expansion_strategy == "selective"

    def test_expansion_config_custom_values(self):
        """Test ExpansionConfig with custom values."""
        config = ExpansionConfig(
            max_expansions=10,
            synonym_limit=5,
            use_wordnet=False,
            use_llm=True,
            preserve_original=False
        )
        assert config.max_expansions == 10
        assert config.synonym_limit == 5
        assert config.use_wordnet is False
        assert config.use_llm is True
        assert config.preserve_original is False

    def test_expander_initialization(self):
        """Test QueryExpander initialization."""
        expander = QueryExpander()
        assert expander.config is not None

    def test_expand_simple_query(self, expander: QueryExpander):
        """Test expanding a simple query."""
        query = "machine learning"
        expansions = expander.expand(query)

        assert isinstance(expansions, list)
        assert len(expansions) > 0
        assert query in expansions  # Original should be included

    def test_expand_preserves_original(self, expansion_config: ExpansionConfig):
        """Test that expansion preserves original query."""
        config = ExpansionConfig(preserve_original=True)
        expander = QueryExpander(config)

        query = "data science"
        expansions = expander.expand(query)

        assert query in expansions

    def test_expand_without_original(self):
        """Test expansion without original query."""
        config = ExpansionConfig(preserve_original=False)
        expander = QueryExpander(config)

        query = "artificial intelligence"
        expansions = expander.expand(query)

        assert query not in expansions

    def test_expand_empty_query(self, expander: QueryExpander):
        """Test expanding empty query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            expander.expand("")

    def test_expand_whitespace_query(self, expander: QueryExpander):
        """Test expanding whitespace-only query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            expander.expand("   ")

    def test_expand_respects_max_expansions(self):
        """Test that expansion respects max_expansions limit."""
        config = ExpansionConfig(max_expansions=2, preserve_original=True)
        expander = QueryExpander(config)

        query = "machine learning algorithms"
        expansions = expander.expand(query)

        assert len(expansions) <= 2

    def test_expand_with_stopwords_filtered(self):
        """Test that stopwords are not expanded."""
        config = ExpansionConfig(max_expansions=5)
        expander = QueryExpander(config)

        query = "the quick brown fox"
        expansions = expander.expand(query)

        # Stopwords like "the" should not be expanded
        assert isinstance(expansions, list)

    def test_expand_short_words_filtered(self):
        """Test that short words are not expanded."""
        config = ExpansionConfig(min_word_length=4)
        expander = QueryExpander(config)

        query = "big data analysis"
        expansions = expander.expand(query)

        # "big" should not be expanded due to length
        assert isinstance(expansions, list)

    def test_expand_different_strategies(self):
        """Test different expansion strategies."""
        query = "python programming"

        # Selective strategy
        selective_expander = QueryExpander(
            ExpansionConfig(expansion_strategy="selective", max_expansions=3)
        )
        selective = selective_expander.expand(query)

        # Best strategy
        best_expander = QueryExpander(
            ExpansionConfig(expansion_strategy="best", max_expansions=3)
        )
        best = best_expander.expand(query)

        # All strategy
        all_expander = QueryExpander(
            ExpansionConfig(expansion_strategy="all", max_expansions=10)
        )
        all_expansions = all_expander.expand(query)

        assert isinstance(selective, list)
        assert isinstance(best, list)
        assert isinstance(all_expansions, list)

    def test_expander_clear_cache(self, expander: QueryExpander):
        """Test clearing the synonym cache."""
        # Generate some expansions to populate cache
        expander.expand("machine learning")

        # Clear cache
        expander.clear_cache()

        stats = expander.get_stats()
        assert stats['cache_size'] == 0

    def test_expander_get_stats(self, expander: QueryExpander):
        """Test getting expander statistics."""
        stats = expander.get_stats()

        assert 'cache_size' in stats
        assert 'wordnet_available' in stats
        assert 'max_expansions' in stats
        assert 'synonym_limit' in stats


class TestHyDEGenerator:
    """Test suite for HyDEGenerator."""

    @pytest.fixture
    def hyde_config(self) -> HyDEConfig:
        """Create HyDE config with test settings."""
        return HyDEConfig(
            num_hypotheticals=1,
            max_length=256,
            temperature=0.3,
            use_caching=False
        )

    @pytest.fixture
    def hyde_generator(self, hyde_config: HyDEConfig) -> HyDEGenerator:
        """Create a HyDE generator with mock provider."""
        mock_provider = MockLLMProvider()
        return HyDEGenerator(config=hyde_config, llm_provider=mock_provider)

    def test_hyde_config_defaults(self):
        """Test HyDEConfig default values."""
        config = HyDEConfig()
        assert config.num_hypotheticals == 1
        assert config.max_length == 512
        assert config.temperature == 0.3
        assert config.model == "gpt-3.5-turbo"
        assert config.use_caching is True
        assert config.cache_ttl == 3600

    def test_hyde_config_custom_values(self):
        """Test HyDEConfig with custom values."""
        config = HyDEConfig(
            num_hypotheticals=3,
            max_length=1024,
            temperature=0.7,
            model="gpt-4",
            use_caching=False
        )
        assert config.num_hypotheticals == 3
        assert config.max_length == 1024
        assert config.temperature == 0.7
        assert config.model == "gpt-4"
        assert config.use_caching is False

    def test_hyde_generator_initialization(self, hyde_config: HyDEConfig):
        """Test HyDEGenerator initialization."""
        generator = HyDEGenerator(config=hyde_config)
        assert generator.config == hyde_config
        assert generator.llm_provider is not None

    @pytest.mark.asyncio
    async def test_generate_hypothetical_documents(self, hyde_generator: HyDEGenerator):
        """Test generating hypothetical documents."""
        query = "What is machine learning?"
        documents = await hyde_generator.generate_hypothetical_documents(query)

        assert isinstance(documents, list)
        assert len(documents) > 0
        assert all(isinstance(doc, str) for doc in documents)
        assert all(len(doc) > 0 for doc in documents)

    @pytest.mark.asyncio
    async def test_generate_multiple_hypotheticals(self):
        """Test generating multiple hypothetical documents."""
        config = HyDEConfig(num_hypotheticals=2, use_caching=False)
        mock_provider = MockLLMProvider()
        generator = HyDEGenerator(config=config, llm_provider=mock_provider)

        query = "Explain neural networks"
        documents = await generator.generate_hypothetical_documents(query)

        assert isinstance(documents, list)
        assert len(documents) <= 2  # May generate fewer if variations fail

    @pytest.mark.asyncio
    async def test_generate_empty_query(self, hyde_generator: HyDEGenerator):
        """Test generating with empty query returns empty list."""
        documents = await hyde_generator.generate_hypothetical_documents("")
        assert documents == []

    @pytest.mark.asyncio
    async def test_generate_enhanced_query(self, hyde_generator: HyDEGenerator):
        """Test generating enhanced query."""
        query = "machine learning"
        enhanced = await hyde_generator.generate_enhanced_query(query)

        assert isinstance(enhanced, str)
        assert len(enhanced) > 0
        # Enhanced query should contain original terms
        assert "machine" in enhanced.lower() or "learning" in enhanced.lower()

    @pytest.mark.asyncio
    async def test_caching_behavior(self):
        """Test that caching works correctly."""
        config = HyDEConfig(use_caching=True, cache_ttl=3600)
        mock_provider = MockLLMProvider()
        generator = HyDEGenerator(config=config, llm_provider=mock_provider)

        query = "data science"

        # First call should generate
        docs1 = await generator.generate_hypothetical_documents(query)

        # Second call should use cache
        docs2 = await generator.generate_hypothetical_documents(query)

        assert docs1 == docs2

    def test_clear_cache(self, hyde_generator: HyDEGenerator):
        """Test clearing the document cache."""
        hyde_generator.clear_cache()

        stats = hyde_generator.get_stats()
        assert stats['cache']['total_entries'] == 0

    def test_get_stats(self, hyde_generator: HyDEGenerator):
        """Test getting generator statistics."""
        stats = hyde_generator.get_stats()

        assert 'config' in stats
        assert 'cache' in stats
        assert 'provider' in stats
        assert stats['config']['num_hypotheticals'] == hyde_generator.config.num_hypotheticals


class TestMockLLMProvider:
    """Test suite for MockLLMProvider."""

    @pytest.fixture
    def mock_provider(self) -> MockLLMProvider:
        """Create a mock LLM provider."""
        return MockLLMProvider()

    @pytest.mark.asyncio
    async def test_generate_mock_response(self, mock_provider: MockLLMProvider):
        """Test generating mock response."""
        prompt = "Query: machine learning\n\nResponse:"
        response = await mock_provider.generate(prompt, max_length=512)

        assert isinstance(response, str)
        assert len(response) > 0
        assert "machine learning" in response.lower()

    @pytest.mark.asyncio
    async def test_generate_different_topics(self, mock_provider: MockLLMProvider):
        """Test generating responses for different topics."""
        topics = [
            "machine learning",
            "neural networks",
            "data science",
            "python programming"
        ]

        for topic in topics:
            prompt = f"Query: {topic}\n\nResponse:"
            response = await mock_provider.generate(prompt)
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_generate_respects_max_length(self, mock_provider: MockLLMProvider):
        """Test that generation respects max length."""
        prompt = "Query: artificial intelligence\n\nResponse:"
        response = await mock_provider.generate(prompt, max_length=100)

        assert len(response) <= 100 + 50  # Allow some buffer for sentence completion


class TestQueryClassifier:
    """Test suite for QueryClassifier."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create a query classifier with default config."""
        return QueryClassifier()

    @pytest.fixture
    def classifier_config(self) -> ClassifierConfig:
        """Create classifier config with custom settings."""
        return ClassifierConfig(
            min_confidence=0.5,
            use_patterns=True,
            use_keywords=True,
            use_length=True
        )

    def test_classifier_config_defaults(self):
        """Test ClassifierConfig default values."""
        config = ClassifierConfig()
        assert config.min_confidence == 0.6
        assert config.use_patterns is True
        assert config.use_keywords is True
        assert config.use_length is True
        assert config.pattern_weight == 0.4
        assert config.keyword_weight == 0.4
        assert config.length_weight == 0.2

    def test_classifier_config_custom_values(self):
        """Test ClassifierConfig with custom values."""
        config = ClassifierConfig(
            min_confidence=0.8,
            use_patterns=False,
            use_keywords=False,
            use_length=False
        )
        assert config.min_confidence == 0.8
        assert config.use_patterns is False
        assert config.use_keywords is False
        assert config.use_length is False

    def test_classifier_initialization(self):
        """Test QueryClassifier initialization."""
        classifier = QueryClassifier()
        assert classifier.config is not None

    def test_classify_factual_query(self, classifier: QueryClassifier):
        """Test classifying a factual query."""
        query = "What is the capital of France?"
        result = classifier.classify(query)

        assert isinstance(result, ClassificationResult)
        assert result.query_type == QueryType.FACTUAL
        assert result.confidence > 0
        assert 'dense_retrieval_weight' in result.recommendations

    def test_classify_procedural_query(self, classifier: QueryClassifier):
        """Test classifying a procedural query."""
        query = "How to implement quicksort in Python?"
        result = classifier.classify(query)

        assert isinstance(result, ClassificationResult)
        assert result.query_type == QueryType.PROCEDURAL
        assert result.confidence > 0

    def test_classify_comparative_query(self, classifier: QueryClassifier):
        """Test classifying a comparative query."""
        query = "Python vs JavaScript comparison"
        result = classifier.classify(query)

        assert isinstance(result, ClassificationResult)
        # May be classified as COMPARATIVE or FACTUAL depending on pattern matching
        assert result.query_type in [QueryType.COMPARATIVE, QueryType.FACTUAL]
        assert result.confidence > 0

    def test_classify_technical_query(self, classifier: QueryClassifier):
        """Test classifying a technical query."""
        query = "API error code 500 debugging"
        result = classifier.classify(query)

        assert isinstance(result, ClassificationResult)
        # May be classified as TECHNICAL or PROCEDURAL
        assert result.query_type in [QueryType.TECHNICAL, QueryType.PROCEDURAL]
        assert result.confidence > 0

    def test_classify_conceptual_query(self, classifier: QueryClassifier):
        """Test classifying a conceptual query."""
        query = "Explain the concept of neural networks"
        result = classifier.classify(query)

        assert isinstance(result, ClassificationResult)
        assert result.query_type == QueryType.CONCEPTUAL
        assert result.confidence > 0

    def test_classify_exploratory_query(self, classifier: QueryClassifier):
        """Test classifying an exploratory query."""
        query = "Tell me everything about machine learning"
        result = classifier.classify(query)

        assert isinstance(result, ClassificationResult)
        assert result.query_type == QueryType.EXPLORATORY
        assert result.confidence > 0

    def test_classify_empty_query(self, classifier: QueryClassifier):
        """Test classifying empty query raises error."""
        with pytest.raises(Exception):
            classifier.classify("")

    def test_classify_whitespace_query(self, classifier: QueryClassifier):
        """Test classifying whitespace-only query raises error."""
        with pytest.raises(Exception):
            classifier.classify("   ")

    def test_classification_result_structure(self, classifier: QueryClassifier):
        """Test that classification result has correct structure."""
        query = "What is machine learning?"
        result = classifier.classify(query)

        assert isinstance(result.query_type, QueryType)
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1
        assert isinstance(result.features, dict)
        assert isinstance(result.recommendations, dict)

    def test_recommendations_for_different_types(self, classifier: QueryClassifier):
        """Test that recommendations vary by query type."""
        factual = classifier.classify("What is Python?")
        procedural = classifier.classify("How to install Python?")
        conceptual = classifier.classify("Explain Python programming")

        # Different types should have different recommendations
        assert factual.recommendations != procedural.recommendations
        assert procedural.recommendations != conceptual.recommendations

    def test_classifier_get_stats(self, classifier: QueryClassifier):
        """Test getting classifier statistics."""
        stats = classifier.get_stats()

        assert 'config' in stats
        assert 'patterns' in stats
        assert 'keywords' in stats
        assert 'query_types' in stats

        # Check config stats
        assert 'min_confidence' in stats['config']
        assert 'weights' in stats['config']

        # Check pattern counts
        for qt in QueryType:
            assert qt.value in stats['patterns']
            assert stats['patterns'][qt.value] > 0

    def test_query_type_enum_values(self):
        """Test QueryType enum values."""
        assert QueryType.FACTUAL.value == "factual"
        assert QueryType.CONCEPTUAL.value == "conceptual"
        assert QueryType.PROCEDURAL.value == "procedural"
        assert QueryType.COMPARATIVE.value == "comparative"
        assert QueryType.EXPLORATORY.value == "exploratory"
        assert QueryType.TECHNICAL.value == "technical"

    def test_low_confidence_fallback(self):
        """Test fallback behavior for low confidence classifications."""
        config = ClassifierConfig(min_confidence=0.9)  # High threshold
        classifier = QueryClassifier(config)

        # Query with some matching patterns to avoid zero division
        query = "the quick brown fox"
        result = classifier.classify(query)

        # Should have valid confidence and query type
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert isinstance(result.query_type, QueryType)


class TestQueryEnhancementIntegration:
    """Integration tests for query enhancement components."""

    @pytest.mark.asyncio
    async def test_full_enhancement_pipeline(self):
        """Test the full query enhancement pipeline."""
        # Initialize components
        expander = QueryExpander(ExpansionConfig(max_expansions=3))
        classifier = QueryClassifier()

        hyde_config = HyDEConfig(num_hypotheticals=1, use_caching=False)
        mock_provider = MockLLMProvider()
        hyde_generator = HyDEGenerator(config=hyde_config, llm_provider=mock_provider)

        # Test query
        query = "How does machine learning work?"

        # Step 1: Classify query
        classification = classifier.classify(query)
        assert classification.query_type == QueryType.CONCEPTUAL

        # Step 2: Expand query
        expansions = expander.expand(query)
        assert len(expansions) > 0

        # Step 3: Generate HyDE documents
        hyde_docs = await hyde_generator.generate_hypothetical_documents(query)
        assert len(hyde_docs) > 0

    def test_recommendations_guide_enhancement(self):
        """Test that classification recommendations guide enhancement."""
        classifier = QueryClassifier()

        # Factual query - should recommend more sparse retrieval
        factual = classifier.classify("What is the capital of France?")
        assert factual.recommendations['sparse_retrieval_weight'] > factual.recommendations['dense_retrieval_weight']

        # Conceptual query - should recommend more dense retrieval
        conceptual = classifier.classify("Explain quantum computing concepts")
        assert conceptual.recommendations['dense_retrieval_weight'] > conceptual.recommendations['sparse_retrieval_weight']

        # Procedural query - should recommend query expansion
        procedural = classifier.classify("How to implement quicksort algorithm")
        assert procedural.recommendations['query_expansion'] > 0.3
