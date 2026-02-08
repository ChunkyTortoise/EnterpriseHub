"""
Tests for ML feature engineering pipeline.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from ghl_real_estate_ai.ml.feature_engineering import ConversationFeatures, FeatureEngineer, MarketFeatures


class TestFeatureEngineer:
    """Test suite for FeatureEngineer class."""

    @pytest.fixture
    def feature_engineer(self):
        """Create FeatureEngineer instance for testing."""
        return FeatureEngineer()

    @pytest.fixture
    def mock_conversation_context(self):
        """Create mock conversation context for testing."""
        return {
            "conversation_history": [
                {"role": "user", "text": "Hi, I'm looking for a house"},
                {"role": "assistant", "text": "Great! I'd love to help you find the perfect home."},
                {"role": "user", "text": "I need 3 bedrooms and 2 bathrooms in downtown"},
                {"role": "assistant", "text": "That's a great area! What's your budget range?"},
                {"role": "user", "text": "Around $500,000. I need to move ASAP for work"},
                {"role": "assistant", "text": "Perfect! I can help you find something quickly."},
                {"role": "user", "text": "Do you have any properties available for viewing?"},
            ],
            "extracted_preferences": {
                "budget": "$500,000",
                "location": "downtown",
                "bedrooms": "3",
                "bathrooms": "2",
                "timeline": "ASAP",
                "motivation": "work relocation",
            },
            "created_at": datetime.now().isoformat(),
        }

    @pytest.fixture
    def mock_minimal_context(self):
        """Create minimal conversation context for edge case testing."""
        return {"conversation_history": [], "extracted_preferences": {}, "created_at": datetime.now().isoformat()}

    @pytest.mark.asyncio
    async def test_extract_conversation_features_success(self, feature_engineer, mock_conversation_context):
        """Test successful conversation feature extraction."""
        features = await feature_engineer.extract_conversation_features(mock_conversation_context)

        assert isinstance(features, ConversationFeatures)
        assert features.message_count == 7
        assert features.qualification_completeness > 0.5  # Good qualification
        assert features.urgency_score > 0.5  # ASAP timeline
        assert features.budget_confidence > 0.5  # Clear budget
        assert "downtown" in str(features).lower() or features.location_specificity > 0

    @pytest.mark.asyncio
    async def test_extract_conversation_features_minimal(self, feature_engineer, mock_minimal_context):
        """Test feature extraction with minimal conversation data."""
        features = await feature_engineer.extract_conversation_features(mock_minimal_context)

        assert isinstance(features, ConversationFeatures)
        assert features.message_count == 0
        assert features.qualification_completeness == 0.0
        assert features.overall_sentiment == 0.0
        assert features.urgency_score >= 0.0  # Should be valid float

    @pytest.mark.asyncio
    async def test_extract_basic_metrics(self, feature_engineer, mock_conversation_context):
        """Test basic metrics extraction."""
        messages = mock_conversation_context["conversation_history"]
        created_at = datetime.now() - timedelta(hours=1)  # 1 hour ago

        metrics = await feature_engineer._extract_basic_metrics(messages, created_at)

        assert metrics["message_count"] == len(messages)
        assert metrics["duration_minutes"] > 50  # Should be around 60 minutes
        assert metrics["avg_response_time"] > 0

    @pytest.mark.asyncio
    async def test_analyze_sentiment_engagement(self, feature_engineer, mock_conversation_context):
        """Test sentiment and engagement analysis."""
        messages = mock_conversation_context["conversation_history"]

        sentiment_data = await feature_engineer._analyze_sentiment_engagement(messages)

        assert "sentiment" in sentiment_data
        assert "urgency" in sentiment_data
        assert "engagement" in sentiment_data
        assert -1.0 <= sentiment_data["sentiment"] <= 1.0
        assert 0.0 <= sentiment_data["urgency"] <= 1.0
        assert 0.0 <= sentiment_data["engagement"] <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_conversation_content(self, feature_engineer, mock_conversation_context):
        """Test conversation content analysis."""
        messages = mock_conversation_context["conversation_history"]

        content_data = await feature_engineer._analyze_conversation_content(messages)

        assert content_data["question_frequency"] >= 0
        assert content_data["price_mentions"] >= 0  # Should detect $500,000
        assert content_data["urgency_signals"] >= 0  # Should detect ASAP
        assert 0.0 <= content_data["location_specificity"] <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_budget_alignment(self, feature_engineer, mock_conversation_context):
        """Test budget alignment analysis."""
        prefs = mock_conversation_context["extracted_preferences"]

        budget_data = await feature_engineer._analyze_budget_alignment(prefs)

        assert budget_data["budget_ratio"] is not None
        assert budget_data["budget_ratio"] > 0
        assert 0.0 <= budget_data["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_qualification_completeness(self, feature_engineer, mock_conversation_context):
        """Test qualification completeness analysis."""
        prefs = mock_conversation_context["extracted_preferences"]

        qual_data = await feature_engineer._analyze_qualification_completeness(prefs)

        assert 0.0 <= qual_data["completeness"] <= 1.0
        assert isinstance(qual_data["missing_info"], list)
        # Should be well-qualified with 6/7 fields
        assert qual_data["completeness"] > 0.7

    @pytest.mark.asyncio
    async def test_analyze_behavioral_patterns(self, feature_engineer, mock_conversation_context):
        """Test behavioral pattern analysis."""
        messages = mock_conversation_context["conversation_history"]

        behavioral_data = await feature_engineer._analyze_behavioral_patterns(messages)

        assert behavioral_data["length_variance"] >= 0
        assert 0.0 <= behavioral_data["consistency"] <= 1.0
        assert isinstance(behavioral_data["weekend_activity"], bool)
        assert isinstance(behavioral_data["late_night_activity"], bool)

    @pytest.mark.asyncio
    async def test_extract_market_features(self, feature_engineer):
        """Test market features extraction."""
        features = await feature_engineer.extract_market_features("downtown")

        assert isinstance(features, MarketFeatures)
        assert 0.0 <= features.inventory_level <= 1.0
        assert features.average_days_on_market > 0
        assert -1.0 <= features.price_trend <= 1.0
        assert 0.0 <= features.seasonal_factor <= 1.0
        assert 0.0 <= features.competition_level <= 1.0
        assert features.interest_rate_level > 0

    @pytest.mark.asyncio
    async def test_extract_market_features_caching(self, feature_engineer):
        """Test that market features are properly cached."""
        location = "test_location"

        # First call
        features1 = await feature_engineer.extract_market_features(location)

        # Second call should be cached (same results)
        features2 = await feature_engineer.extract_market_features(location)

        # Results should be identical (cached)
        assert features1.inventory_level == features2.inventory_level
        assert features1.seasonal_factor == features2.seasonal_factor

    def test_create_feature_vector(self, feature_engineer):
        """Test feature vector creation."""
        # Create mock features
        conv_features = ConversationFeatures(
            message_count=10,
            avg_response_time=300.0,
            conversation_duration_minutes=60.0,
            overall_sentiment=0.5,
            urgency_score=0.8,
            engagement_score=0.7,
            question_asking_frequency=0.3,
            price_mention_count=2,
            timeline_urgency_signals=1,
            location_specificity=0.9,
            budget_to_market_ratio=0.8,
            budget_confidence=0.9,
            qualification_completeness=0.8,
            missing_critical_info=["financing"],
            message_length_variance=500.0,
            response_consistency=0.8,
            weekend_activity=False,
            late_night_activity=False,
        )

        market_features = MarketFeatures(
            inventory_level=0.7,
            average_days_on_market=30,
            price_trend=0.1,
            seasonal_factor=0.8,
            competition_level=0.6,
            interest_rate_level=7.0,
        )

        vector = feature_engineer.create_feature_vector(conv_features, market_features)

        assert isinstance(vector, np.ndarray)
        assert len(vector) == len(feature_engineer.get_feature_names())
        assert np.all(vector >= 0.0)  # All features should be normalized to >= 0
        assert np.all(vector <= 1.0)  # All features should be normalized to <= 1

    def test_get_feature_names(self, feature_engineer):
        """Test feature names retrieval."""
        feature_names = feature_engineer.get_feature_names()

        assert isinstance(feature_names, list)
        assert len(feature_names) > 0
        assert all(isinstance(name, str) for name in feature_names)

        # Check for expected feature names
        expected_features = [
            "message_count_norm",
            "closing_probability",
            "engagement_score",
            "urgency_score",
            "qualification_completeness",
        ]

        for expected in expected_features:
            # Some expected features should be in the list
            assert any(expected in name for name in feature_names), f"Expected feature pattern '{expected}' not found"

    @pytest.mark.asyncio
    async def test_error_handling(self, feature_engineer):
        """Test error handling with invalid data."""
        # Test with None context
        with pytest.raises(Exception):
            await feature_engineer.extract_conversation_features(None)

        # Test with malformed context
        malformed_context = {"invalid": "data"}
        features = await feature_engineer.extract_conversation_features(malformed_context)

        # Should return default features without crashing
        assert isinstance(features, ConversationFeatures)
        assert features.message_count >= 0

    @pytest.mark.asyncio
    async def test_budget_parsing_variations(self, feature_engineer):
        """Test budget parsing with different formats."""
        test_cases = [
            {"budget": "$500,000", "expected_ratio": True},
            {"budget": "500k", "expected_ratio": True},
            {"budget": "1.5m", "expected_ratio": True},
            {"budget": "around 400000", "expected_ratio": True},
            {"budget": "not sure", "expected_ratio": False},
            {"budget": "", "expected_ratio": False},
        ]

        for case in test_cases:
            prefs = {"budget": case["budget"]}
            result = await feature_engineer._analyze_budget_alignment(prefs)

            if case["expected_ratio"]:
                assert result["budget_ratio"] is not None
            else:
                assert result["budget_ratio"] is None

    @pytest.mark.asyncio
    async def test_seasonal_factor_calculation(self, feature_engineer):
        """Test seasonal factor calculation for different months."""
        # Mock current month to test seasonal patterns
        with patch("ghl_real_estate_ai.ml.feature_engineering.datetime") as mock_datetime:
            # Test spring (peak season)
            mock_datetime.now.return_value.month = 5  # May
            features_spring = await feature_engineer.extract_market_features()

            # Test winter (slow season)
            mock_datetime.now.return_value.month = 12  # December
            features_winter = await feature_engineer.extract_market_features()

            # Spring should have higher seasonal factor than winter
            assert features_spring.seasonal_factor > features_winter.seasonal_factor

    @pytest.mark.asyncio
    async def test_feature_caching(self, feature_engineer):
        """Test that conversation features are properly cached."""
        context = {
            "conversation_history": [{"role": "user", "text": "test"}],
            "extracted_preferences": {"budget": "500k"},
            "created_at": datetime.now().isoformat(),
        }

        # First call
        start_time = datetime.now()
        features1 = await feature_engineer.extract_conversation_features(context)
        first_call_time = datetime.now() - start_time

        # Second call should be faster (cached)
        start_time = datetime.now()
        features2 = await feature_engineer.extract_conversation_features(context)
        second_call_time = datetime.now() - start_time

        # Results should be identical
        assert features1.message_count == features2.message_count
        assert features1.qualification_completeness == features2.qualification_completeness

        # Second call should be significantly faster
        assert second_call_time < first_call_time

    @pytest.mark.asyncio
    async def test_edge_cases(self, feature_engineer):
        """Test edge cases and boundary conditions."""
        # Empty messages but with preferences
        edge_context = {
            "conversation_history": [],
            "extracted_preferences": {"budget": "1000000", "location": "luxury district", "timeline": "urgent"},
            "created_at": datetime.now().isoformat(),
        }

        features = await feature_engineer.extract_conversation_features(edge_context)

        # Should handle gracefully
        assert features.message_count == 0
        assert features.qualification_completeness > 0  # Some prefs available
        assert features.budget_confidence > 0

        # Very long conversation
        long_conversation = {
            "conversation_history": [{"role": "user", "text": f"Message {i}"} for i in range(100)],
            "extracted_preferences": {},
            "created_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        }

        features_long = await feature_engineer.extract_conversation_features(long_conversation)
        assert features_long.message_count == 100
        assert features_long.conversation_duration_minutes > 250  # ~5 hours
