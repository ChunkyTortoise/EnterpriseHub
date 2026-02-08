"""Tests for Intent Classification V2 module."""

from datetime import datetime

import numpy as np
import pytest
from src.core.exceptions import RetrievalError
from src.query.intent_classifier_v2 import (
    ClassifierConfig,
    ConfidenceCalibrator,
    IntentClassificationResult,
    IntentClassifierV2,
    IntentType,
    MultiLabelResult,
)


class TestConfidenceCalibrator:
    """Test confidence calibration functionality."""

    def test_calibrator_initialization(self):
        """Test calibrator initializes correctly."""
        calibrator = ConfidenceCalibrator(method="isotonic")
        assert calibrator.method == "isotonic"
        assert not calibrator.is_fitted

    def test_temperature_scaling(self):
        """Test temperature scaling calibration."""
        calibrator = ConfidenceCalibrator(method="temperature")

        # Create synthetic data
        logits = np.array([[2.0, 1.0, 0.0], [0.0, 2.0, 1.0], [1.0, 0.0, 2.0]])
        labels = np.array([1, 1, 1])  # All correct

        calibrator.fit(logits, labels)
        assert calibrator.is_fitted
        assert calibrator.temperature != 1.0

    def test_platt_scaling(self):
        """Test Platt scaling calibration."""
        calibrator = ConfidenceCalibrator(method="sigmoid")

        logits = np.array([1.0, 2.0, 0.5, 3.0, 1.5])
        labels = np.array([0, 1, 0, 1, 1])

        calibrator.fit(logits, labels)
        assert calibrator.is_fitted

    def test_calibration_output_range(self):
        """Test calibrated outputs are in valid range."""
        calibrator = ConfidenceCalibrator(method="temperature")
        calibrator.temperature = 1.5
        calibrator.is_fitted = True

        logits = np.array([1.0, 2.0, 0.5])
        probs = calibrator.calibrate(logits)

        assert all(0 <= p <= 1 for p in probs)
        assert np.isclose(sum(probs), 1.0, atol=0.01)


class TestIntentClassifierV2:
    """Test Intent Classifier V2 functionality."""

    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        config = ClassifierConfig(domain="real_estate", min_confidence=0.5)
        return IntentClassifierV2(config=config)

    def test_classifier_initialization(self, classifier):
        """Test classifier initializes correctly."""
        assert classifier.config.domain == "real_estate"
        assert classifier.config.min_confidence == 0.5
        assert len(classifier._intent_patterns) > 0

    def test_classify_property_search(self, classifier):
        """Test classification of property search query."""
        result = classifier.classify("Show me houses for sale")

        assert isinstance(result, IntentClassificationResult)
        # Intent can be PROPERTY_SEARCH or BUYING_INTENT
        assert result.primary_intent in [IntentType.PROPERTY_SEARCH, IntentType.BUYING_INTENT]
        assert result.confidence >= 0.5
        assert len(result.alternative_intents) > 0

    def test_classify_buying_intent(self, classifier):
        """Test classification of buying intent query."""
        result = classifier.classify("I want to buy a house")

        assert result.primary_intent == IntentType.BUYING_INTENT
        assert result.confidence >= 0.5

    def test_classify_selling_intent(self, classifier):
        """Test classification of selling intent query."""
        result = classifier.classify("What's my home worth?")

        assert result.primary_intent == IntentType.SELLING_INTENT

    def test_classify_price_inquiry(self, classifier):
        """Test classification of price inquiry."""
        result = classifier.classify("How much is a 3-bedroom house?")

        assert result.primary_intent == IntentType.PRICE_INQUIRY

    def test_classify_with_price_mention(self, classifier):
        """Test classification with price mention."""
        result = classifier.classify("Show me homes under $800k")

        assert result.primary_intent in [
            IntentType.PROPERTY_SEARCH,
            IntentType.PRICE_INQUIRY,
        ]
        assert result.features["has_price"] is True

    def test_classify_empty_query_raises_error(self, classifier):
        """Test that empty query raises error."""
        with pytest.raises(RetrievalError):
            classifier.classify("")

    def test_classify_whitespace_query_raises_error(self, classifier):
        """Test that whitespace-only query raises error."""
        with pytest.raises(RetrievalError):
            classifier.classify("   ")

    def test_multi_label_classification(self, classifier):
        """Test multi-label classification."""
        result = classifier.classify_multi_label("I'm looking to buy a 3-bedroom house in Etiwanda school district")

        assert isinstance(result, MultiLabelResult)
        assert len(result.intents) >= 1
        assert IntentType.BUYING_INTENT in result.intents
        assert result.coverage_score > 0

    def test_multi_label_with_correlation(self, classifier):
        """Test multi-label classification includes correlations."""
        result = classifier.classify_multi_label("Schedule a tour for a house I'm interested in buying")

        assert result.primary_intent in result.intents
        # Check for correlations between related intents
        if len(result.intents) > 1:
            assert len(result.label_correlations) > 0

    def test_multi_label_max_labels(self, classifier):
        """Test multi-label respects max labels limit."""
        classifier.config.max_labels = 2
        result = classifier.classify_multi_label("I want to buy a house in Rancho Cucamonga with a pool")

        assert len(result.intents) <= 2

    def test_feature_extraction(self, classifier):
        """Test feature extraction."""
        features = classifier._extract_features("Show me 3-bedroom homes under $800k in Rancho Cucamonga")

        assert "length" in features
        assert "word_count" in features
        assert "has_price" in features
        assert "has_number" in features
        assert "weighted_scores" in features
        assert features["has_price"] is True
        assert features["has_number"] is True

    def test_intent_correlation(self, classifier):
        """Test intent correlation calculation."""
        corr = classifier._calculate_intent_correlation(IntentType.BUYING_INTENT, IntentType.PROPERTY_SEARCH)
        assert corr > 0.5  # These intents should be highly correlated

        corr_unrelated = classifier._calculate_intent_correlation(IntentType.BUYING_INTENT, IntentType.SELLING_INTENT)
        assert corr_unrelated < corr  # Less correlated

    def test_calibrate_confidence(self, classifier):
        """Test confidence calibration."""
        queries = [
            "Show me houses",
            "I want to buy",
            "What's the price",
            "Market analysis",
        ]
        labels = [1, 1, 0, 1]  # Some correct, some incorrect

        result = classifier.calibrate_confidence(queries, labels)
        assert result is classifier  # Returns self
        assert classifier.calibrator.is_fitted

    def test_get_stats(self, classifier):
        """Test getting classifier statistics."""
        stats = classifier.get_stats()

        assert "config" in stats
        assert "intent_patterns" in stats
        assert "num_intents" in stats
        assert stats["num_intents"] == len(IntentType)


class TestIntentTypes:
    """Test intent type definitions."""

    def test_intent_type_values(self):
        """Test all intent types have correct values."""
        assert IntentType.INFORMATIONAL.value == "informational"
        assert IntentType.PROPERTY_SEARCH.value == "property_search"
        assert IntentType.BUYING_INTENT.value == "buying_intent"
        assert IntentType.SELLING_INTENT.value == "selling_intent"

    def test_all_intent_types(self):
        """Test that all expected intent types exist."""
        expected_types = [
            "informational",
            "navigational",
            "transactional",
            "comparison",
            "exploratory",
            "property_search",
            "price_inquiry",
            "location_query",
            "buying_intent",
            "selling_intent",
            "investment_research",
            "market_analysis",
            "cma_request",
            "showing_request",
            "financing_question",
            "neighborhood_info",
            "school_district_query",
            "amenities_search",
            "agent_contact",
        ]

        actual_types = [it.value for it in IntentType]
        for expected in expected_types:
            assert expected in actual_types


class TestClassifierConfig:
    """Test classifier configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ClassifierConfig()

        assert config.min_confidence == 0.6
        assert config.enable_calibration is True
        assert config.calibration_method == "isotonic"
        assert config.enable_multi_label is True
        assert config.multi_label_threshold == 0.3
        assert config.max_labels == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = ClassifierConfig(
            min_confidence=0.7,
            enable_calibration=False,
            calibration_method="sigmoid",
            max_labels=5,
        )

        assert config.min_confidence == 0.7
        assert config.enable_calibration is False
        assert config.calibration_method == "sigmoid"
        assert config.max_labels == 5
