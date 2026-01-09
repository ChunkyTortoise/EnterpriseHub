"""
Test Suite for ML-Enhanced Property Matcher
Comprehensive testing for confidence scoring and ML features
"""

import pytest
import numpy as np
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from ghl_real_estate_ai.services.property_matcher_ml import PropertyMatcherML, ConfidenceScore


class TestConfidenceScore:
    """Test the ConfidenceScore dataclass"""

    def test_confidence_score_creation(self):
        """Test creating a confidence score with all components"""
        score = ConfidenceScore(
            overall=85.5,
            budget_match=90.0,
            location_match=80.0,
            feature_match=85.0,
            market_context=88.0,
            reasoning=["Great price", "Perfect location"],
            confidence_level="high"
        )

        assert score.overall == 85.5
        assert score.confidence_level == "high"
        assert len(score.reasoning) == 2

    def test_confidence_level_classification(self):
        """Test automatic confidence level classification"""
        high_score = ConfidenceScore(overall=92.0)
        medium_score = ConfidenceScore(overall=75.0)
        low_score = ConfidenceScore(overall=55.0)

        assert high_score.get_confidence_level() == "high"
        assert medium_score.get_confidence_level() == "medium"
        assert low_score.get_confidence_level() == "low"


class TestPropertyMatcherML:
    """Test the ML-enhanced property matcher"""

    @pytest.fixture
    def sample_property(self) -> Dict[str, Any]:
        """Sample property for testing"""
        return {
            "id": "prop_123",
            "price": 750000,
            "address": {
                "street": "123 Oak Street",
                "neighborhood": "Downtown",
                "city": "Austin",
                "zip": "78701"
            },
            "bedrooms": 3,
            "bathrooms": 2.5,
            "sqft": 2100,
            "property_type": "Single Family",
            "year_built": 2015,
            "amenities": ["pool", "garage", "garden"],
            "school_rating": 8.5,
            "crime_score": 7.2,
            "walkability_score": 85,
            "days_on_market": 15,
            "price_per_sqft": 357.14
        }

    @pytest.fixture
    def sample_preferences(self) -> Dict[str, Any]:
        """Sample lead preferences for testing"""
        return {
            "budget": 800000,
            "location": "Downtown",
            "bedrooms": 3,
            "property_type": "Single Family",
            "must_haves": ["garage", "good_schools"],
            "nice_to_haves": ["pool", "walkable"],
            "max_commute_time": 30
        }

    @pytest.fixture
    def matcher(self) -> PropertyMatcherML:
        """Create a PropertyMatcherML instance for testing"""
        return PropertyMatcherML()

    def test_feature_extraction(self, matcher, sample_property):
        """Test that features are extracted correctly from property data"""
        features = matcher.extract_features(sample_property)

        assert "price_normalized" in features
        assert "location_score" in features
        assert "amenity_count" in features
        assert "price_per_sqft_percentile" in features
        assert "market_hotness" in features

        # Test feature values are reasonable
        assert 0 <= features["location_score"] <= 1
        assert features["amenity_count"] == 3
        assert isinstance(features["price_normalized"], float)

    def test_budget_confidence_scoring(self, matcher, sample_property, sample_preferences):
        """Test budget match confidence scoring"""
        confidence = matcher.calculate_budget_confidence(sample_property, sample_preferences)

        # Property at $750k with $800k budget should have high confidence
        assert confidence >= 0.85

        # Test over-budget scenario
        over_budget_prefs = sample_preferences.copy()
        over_budget_prefs["budget"] = 700000
        confidence_over = matcher.calculate_budget_confidence(sample_property, over_budget_prefs)
        assert confidence_over < confidence

        # Test stretch budget scenario
        stretch_prefs = sample_preferences.copy()
        stretch_prefs["budget"] = 745000  # Just under property price
        confidence_stretch = matcher.calculate_budget_confidence(sample_property, stretch_prefs)
        assert 0.3 <= confidence_stretch <= 0.7  # Medium confidence

    def test_location_confidence_scoring(self, matcher, sample_property, sample_preferences):
        """Test location match confidence scoring"""
        confidence = matcher.calculate_location_confidence(sample_property, sample_preferences)

        # Perfect location match should have high confidence
        assert confidence >= 0.9

        # Test different neighborhood
        diff_location_prefs = sample_preferences.copy()
        diff_location_prefs["location"] = "South Austin"
        confidence_diff = matcher.calculate_location_confidence(sample_property, diff_location_prefs)
        assert confidence_diff < confidence

    def test_feature_match_scoring(self, matcher, sample_property, sample_preferences):
        """Test feature and amenity matching confidence"""
        confidence = matcher.calculate_feature_confidence(sample_property, sample_preferences)

        # Property has garage (must-have) and pool (nice-to-have)
        assert confidence >= 0.8

        # Test missing must-haves
        missing_must_haves_prefs = sample_preferences.copy()
        missing_must_haves_prefs["must_haves"] = ["elevator", "wine_cellar"]
        confidence_missing = matcher.calculate_feature_confidence(sample_property, missing_must_haves_prefs)
        assert confidence_missing < 0.5  # Low confidence for missing must-haves

    def test_market_context_scoring(self, matcher, sample_property):
        """Test market context confidence scoring"""
        confidence = matcher.calculate_market_confidence(sample_property)

        # Property with 15 days on market should indicate good market positioning
        assert 0.6 <= confidence <= 1.0

        # Test stale listing
        stale_property = sample_property.copy()
        stale_property["days_on_market"] = 120
        confidence_stale = matcher.calculate_market_confidence(stale_property)
        assert confidence_stale < confidence

    def test_overall_confidence_calculation(self, matcher, sample_property, sample_preferences):
        """Test the overall confidence score calculation"""
        confidence_score = matcher.calculate_confidence_score(sample_property, sample_preferences)

        # Check structure
        assert isinstance(confidence_score, ConfidenceScore)
        assert 0 <= confidence_score.overall <= 100
        assert confidence_score.confidence_level in ["low", "medium", "high"]
        assert len(confidence_score.reasoning) > 0

        # Check component scores
        assert 0 <= confidence_score.budget_match <= 100
        assert 0 <= confidence_score.location_match <= 100
        assert 0 <= confidence_score.feature_match <= 100
        assert 0 <= confidence_score.market_context <= 100

    def test_reasoning_generation(self, matcher, sample_property, sample_preferences):
        """Test that meaningful reasoning is generated"""
        confidence_score = matcher.calculate_confidence_score(sample_property, sample_preferences)

        reasoning = confidence_score.reasoning
        assert len(reasoning) >= 2  # Should have multiple reasons

        # Check for key reasoning elements
        reasoning_text = " ".join(reasoning)
        assert any(word in reasoning_text.lower() for word in ["budget", "price", "affordable"])
        assert any(word in reasoning_text.lower() for word in ["location", "neighborhood", "downtown"])

    def test_confidence_level_thresholds(self, matcher):
        """Test confidence level classification thresholds"""
        # High confidence
        high_score = ConfidenceScore(overall=88.0)
        assert high_score.get_confidence_level() == "high"

        # Medium confidence
        medium_score = ConfidenceScore(overall=72.0)
        assert medium_score.get_confidence_level() == "medium"

        # Low confidence
        low_score = ConfidenceScore(overall=45.0)
        assert low_score.get_confidence_level() == "low"

        # Edge cases
        edge_high = ConfidenceScore(overall=80.0)  # Exactly at threshold
        edge_medium = ConfidenceScore(overall=60.0)  # Exactly at threshold

        assert edge_high.get_confidence_level() == "high"
        assert edge_medium.get_confidence_level() == "medium"

    def test_enhanced_property_matching(self, matcher):
        """Test the enhanced matching with ML confidence scores"""
        # Mock property data
        properties = [
            {
                "id": "prop_1", "price": 750000, "address": {"neighborhood": "Downtown"},
                "bedrooms": 3, "amenities": ["pool", "garage"], "days_on_market": 15
            },
            {
                "id": "prop_2", "price": 850000, "address": {"neighborhood": "Westlake"},
                "bedrooms": 4, "amenities": ["garage"], "days_on_market": 45
            }
        ]

        preferences = {
            "budget": 800000,
            "location": "Downtown",
            "bedrooms": 3,
            "must_haves": ["garage"]
        }

        with patch.object(matcher, 'listings', properties):
            matches = matcher.find_enhanced_matches(preferences, limit=2)

            assert len(matches) <= 2
            assert all(isinstance(match.get("confidence_score"), ConfidenceScore) for match in matches)

            # First property should score higher (better price, location match)
            if len(matches) == 2:
                assert matches[0]["confidence_score"].overall >= matches[1]["confidence_score"].overall

    def test_ml_model_integration_placeholder(self, matcher):
        """Test placeholder for future ML model integration"""
        # This test documents where ML models would be integrated
        assert hasattr(matcher, 'ml_models')
        assert matcher.ml_models is None  # Currently placeholder

        # Test the model training pipeline structure
        features = np.array([[0.5, 0.8, 0.3], [0.7, 0.6, 0.9]])
        labels = np.array([0.85, 0.75])

        # This would be the interface for training
        # result = matcher.train_confidence_model(features, labels)
        # For now, just test the method exists
        assert hasattr(matcher, 'train_confidence_model')

    def test_feature_importance_analysis(self, matcher, sample_property, sample_preferences):
        """Test feature importance for interpretability"""
        confidence_score = matcher.calculate_confidence_score(sample_property, sample_preferences)

        # Test that we can analyze which features contributed most
        feature_importance = matcher.analyze_feature_importance(sample_property, sample_preferences)

        assert isinstance(feature_importance, dict)
        assert "budget" in feature_importance
        assert "location" in feature_importance
        assert "features" in feature_importance
        assert "market" in feature_importance

        # All importance scores should sum to approximately 1.0
        total_importance = sum(feature_importance.values())
        assert 0.95 <= total_importance <= 1.05

    def test_confidence_score_edge_cases(self, matcher):
        """Test edge cases in confidence scoring"""
        # Missing price information
        property_no_price = {"id": "prop_test", "address": {"neighborhood": "Test"}}
        preferences = {"budget": 500000}

        confidence = matcher.calculate_budget_confidence(property_no_price, preferences)
        assert confidence >= 0  # Should handle gracefully

        # Empty preferences
        property_test = {"price": 400000, "address": {"neighborhood": "Test"}}
        empty_preferences = {}

        confidence_score = matcher.calculate_confidence_score(property_test, empty_preferences)
        assert isinstance(confidence_score, ConfidenceScore)
        assert confidence_score.overall >= 0


class TestMLIntegrationFramework:
    """Test the framework for ML model integration"""

    def test_feature_engineering_pipeline(self):
        """Test the feature engineering pipeline structure"""
        # This test documents the expected ML pipeline structure
        from ghl_real_estate_ai.services.property_matcher_ml import MLFeaturePipeline

        pipeline = MLFeaturePipeline()

        # Test feature categories
        assert hasattr(pipeline, 'numerical_features')
        assert hasattr(pipeline, 'categorical_features')
        assert hasattr(pipeline, 'derived_features')

        # Test transformation methods
        assert hasattr(pipeline, 'normalize_price_features')
        assert hasattr(pipeline, 'encode_categorical_features')
        assert hasattr(pipeline, 'create_interaction_features')

    def test_model_registry_interface(self):
        """Test the model registry for different algorithms"""
        from ghl_real_estate_ai.services.property_matcher_ml import MLModelRegistry

        registry = MLModelRegistry()

        # Test different algorithm strategies
        assert hasattr(registry, 'register_model')
        assert hasattr(registry, 'get_model')
        assert hasattr(registry, 'list_models')

        # Test model types that could be supported
        expected_models = [
            'random_forest_confidence',
            'gradient_boost_match',
            'neural_preference_scorer',
            'market_trend_predictor'
        ]

        for model_name in expected_models:
            # Test that we can register these model types
            assert registry.supports_model_type(model_name)


# Integration test for the enhanced property matcher UI component
class TestPropertyMatcherUIIntegration:
    """Test integration with the Streamlit UI component"""

    def test_enhanced_property_matcher_integration(self):
        """Test that the enhanced matcher integrates with existing UI"""
        # Mock the enhanced matcher being used in the UI component
        sample_lead_context = {
            'extracted_preferences': {
                'budget': 750000,
                'location': 'Downtown',
                'bedrooms': 3
            }
        }

        # This test ensures the interface remains compatible
        from ghl_real_estate_ai.streamlit_demo.components.property_matcher_ai import generate_property_matches

        matches = generate_property_matches(sample_lead_context)
        assert isinstance(matches, list)
        assert len(matches) > 0

        # Each match should have the required fields for UI display
        for match in matches:
            assert 'address' in match
            assert 'price' in match
            assert 'match_score' in match
            assert 'match_reasons' in match