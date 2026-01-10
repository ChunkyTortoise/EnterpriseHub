"""
Tests for Property Recommendation Engine with Claude Explanations.

Tests behavioral learning, Claude explanations, and personalized recommendations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ghl_real_estate_ai.services.property_recommendation_engine import (
    PropertyRecommendationEngine,
    PropertyMatch,
    PropertyInteraction,
    InteractionType,
    BehavioralPreference,
    PersonalizedRecommendations
)


class TestPropertyRecommendationEngine:
    """Test suite for property recommendation engine."""

    @pytest.fixture
    def mock_property_matcher(self):
        """Mock property matcher for testing."""
        matcher = Mock()
        matcher.find_matches.return_value = [
            {
                "property_id": "prop1",
                "price": 400000,
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "single_family",
                "address": {"city": "Austin", "neighborhood": "Downtown"},
                "features": ["pool", "garage"],
                "match_score": 0.8
            },
            {
                "property_id": "prop2",
                "price": 450000,
                "bedrooms": 4,
                "bathrooms": 3,
                "property_type": "townhome",
                "address": {"city": "Round Rock", "neighborhood": "Cedar Park"},
                "features": ["patio", "new_construction"],
                "match_score": 0.7
            }
        ]
        matcher.generate_match_reasoning.return_value = "Great match for your criteria!"
        return matcher

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing."""
        client = Mock()
        client.agenerate = AsyncMock()

        # Mock Claude response for explanations
        mock_response = Mock()
        mock_response.content = "This property is perfect because it matches your budget and has the pool you've been looking for!"
        client.agenerate.return_value = mock_response

        return client

    @pytest.fixture
    def recommendation_engine(self, mock_property_matcher, mock_llm_client):
        """Create recommendation engine with mocked dependencies."""
        return PropertyRecommendationEngine(
            tenant_id="test_tenant",
            property_matcher=mock_property_matcher,
            llm_client=mock_llm_client
        )

    @pytest.fixture
    def sample_extracted_preferences(self):
        """Sample extracted preferences for testing."""
        return {
            "budget": 450000,
            "location": ["Austin", "Round Rock"],
            "bedrooms": 3,
            "bathrooms": 2,
            "must_haves": ["pool", "garage"]
        }

    @pytest.fixture
    def sample_property_interactions(self):
        """Sample property interactions for behavioral learning."""
        return [
            PropertyInteraction(
                property_id="prop1",
                interaction_type=InteractionType.LIKE,
                timestamp=datetime.utcnow() - timedelta(days=1),
                duration_seconds=120,
                property_features={"price": 400000, "bedrooms": 3, "property_type": "single_family"}
            ),
            PropertyInteraction(
                property_id="prop2",
                interaction_type=InteractionType.VIEW,
                timestamp=datetime.utcnow() - timedelta(hours=2),
                duration_seconds=45,
                property_features={"price": 450000, "bedrooms": 4, "property_type": "townhome"}
            ),
            PropertyInteraction(
                property_id="prop3",
                interaction_type=InteractionType.DISLIKE,
                timestamp=datetime.utcnow() - timedelta(hours=1),
                duration_seconds=15,
                property_features={"price": 600000, "bedrooms": 5, "property_type": "luxury"}
            )
        ]

    def test_default_behavioral_profile(self, recommendation_engine):
        """Test default behavioral profile for new contacts."""
        profile = recommendation_engine._default_behavioral_profile()

        assert profile["total_interactions"] == 0
        assert profile["confidence_level"] == 0.0
        assert profile["interaction_types"]["dominant_behavior"] == "none"
        assert profile["engagement_patterns"]["engagement_level"] == "unknown"

    def test_analyze_interaction_types(self, recommendation_engine, sample_property_interactions):
        """Test analysis of interaction type patterns."""
        analysis = recommendation_engine._analyze_interaction_types(sample_property_interactions)

        assert analysis["counts"]["like"] == 1
        assert analysis["counts"]["view"] == 1
        assert analysis["counts"]["dislike"] == 1
        assert analysis["ratios"]["like"] == 1/3
        assert analysis["dominant_behavior"] in ["like", "view", "dislike"]

    def test_analyze_engagement_patterns(self, recommendation_engine, sample_property_interactions):
        """Test engagement pattern analysis."""
        analysis = recommendation_engine._analyze_engagement_patterns(sample_property_interactions)

        assert analysis["avg_duration"] == (120 + 45 + 15) / 3
        assert analysis["engagement_level"] in ["low", "medium", "high"]
        assert analysis["total_time_spent"] == 180

    def test_analyze_preference_patterns(self, recommendation_engine, sample_property_interactions):
        """Test preference pattern analysis from interactions."""
        analysis = recommendation_engine._analyze_preference_patterns(sample_property_interactions)

        assert "price" in analysis["all_features"]
        assert "bedrooms" in analysis["all_features"]
        assert "property_type" in analysis["all_features"]

        # Check liked features (from LIKE interaction)
        assert "price" in analysis["liked_features"]
        assert 400000 in analysis["liked_features"]["price"]

        # Check disliked features (from DISLIKE interaction)
        assert "price" in analysis["disliked_features"]
        assert 600000 in analysis["disliked_features"]["price"]

    @pytest.mark.asyncio
    async def test_track_property_interaction(self, recommendation_engine):
        """Test tracking property interactions for behavioral learning."""
        contact_id = "test_contact"

        await recommendation_engine.track_property_interaction(
            contact_id=contact_id,
            property_id="prop1",
            interaction_type=InteractionType.LIKE,
            duration_seconds=90,
            property_data={"price": 400000, "bedrooms": 3}
        )

        # Check that interaction was stored
        interactions = recommendation_engine.property_interactions.get(contact_id, [])
        assert len(interactions) == 1
        assert interactions[0].property_id == "prop1"
        assert interactions[0].interaction_type == InteractionType.LIKE
        assert interactions[0].duration_seconds == 90

    @pytest.mark.asyncio
    async def test_build_behavioral_profile_with_data(self, recommendation_engine, sample_property_interactions):
        """Test building behavioral profile with interaction data."""
        contact_id = "test_contact"
        recommendation_engine.property_interactions[contact_id] = sample_property_interactions

        profile = await recommendation_engine._build_behavioral_profile(contact_id)

        assert profile["total_interactions"] == 3
        assert profile["confidence_level"] > 0.0
        assert profile["interaction_types"]["dominant_behavior"] in ["like", "view", "dislike"]
        assert profile["engagement_patterns"]["engagement_level"] in ["low", "medium", "high"]
        assert profile["last_activity"] is not None

    @pytest.mark.asyncio
    async def test_build_behavioral_profile_no_data(self, recommendation_engine):
        """Test building behavioral profile with no interaction data."""
        contact_id = "new_contact"

        profile = await recommendation_engine._build_behavioral_profile(contact_id)

        assert profile["total_interactions"] == 0
        assert profile["confidence_level"] == 0.0
        assert profile["interaction_types"]["dominant_behavior"] == "none"

    def test_calculate_profile_confidence(self, recommendation_engine):
        """Test confidence calculation based on interaction count."""
        # No interactions
        assert recommendation_engine._calculate_profile_confidence({"total_interactions": 0}) == 0.0

        # Few interactions
        assert recommendation_engine._calculate_profile_confidence({"total_interactions": 2}) == 0.3

        # Medium interactions
        assert recommendation_engine._calculate_profile_confidence({"total_interactions": 5}) == 0.6

        # Many interactions
        assert recommendation_engine._calculate_profile_confidence({"total_interactions": 10}) == 0.8

        # Very high interactions
        assert recommendation_engine._calculate_profile_confidence({"total_interactions": 20}) == 1.0

    def test_score_property_for_preference_price(self, recommendation_engine):
        """Test scoring property for price preference."""
        property_data = {"price": 400000}

        # Exact match
        score = recommendation_engine._score_property_for_preference(
            property_data, "price", 400000, 0.8
        )
        assert score == 0.8

        # Close match (within 10%)
        score = recommendation_engine._score_property_for_preference(
            property_data, "price", 420000, 0.8
        )
        assert score == 0.8

        # Distant match
        score = recommendation_engine._score_property_for_preference(
            property_data, "price", 600000, 0.8
        )
        assert score == 0.3

    def test_score_property_for_preference_bedrooms(self, recommendation_engine):
        """Test scoring property for bedroom preference."""
        property_data = {"bedrooms": 3}

        # Exact match
        score = recommendation_engine._score_property_for_preference(
            property_data, "bedrooms", 3, 0.8
        )
        assert score == 0.8

        # Close match (within 1)
        score = recommendation_engine._score_property_for_preference(
            property_data, "bedrooms", 4, 0.8
        )
        assert score == 0.6

        # Distant match
        score = recommendation_engine._score_property_for_preference(
            property_data, "bedrooms", 1, 0.8
        )
        assert score == 0.4

    @pytest.mark.asyncio
    async def test_calculate_behavioral_score_no_data(self, recommendation_engine):
        """Test behavioral scoring with insufficient data."""
        property_data = {"price": 400000, "bedrooms": 3}
        behavioral_profile = {"total_interactions": 1}
        extracted_preferences = {}

        score = await recommendation_engine._calculate_behavioral_score(
            property_data, behavioral_profile, extracted_preferences
        )

        assert score == 0.5  # Neutral score for insufficient data

    @pytest.mark.asyncio
    async def test_calculate_behavioral_score_with_preferences(self, recommendation_engine):
        """Test behavioral scoring with learned preferences."""
        property_data = {"price": 400000, "bedrooms": 3}
        behavioral_profile = {
            "total_interactions": 5,
            "learned_preferences": {
                "price": {
                    "preference_value": 400000,
                    "confidence_score": 0.8,
                    "weight_multiplier": 1.0
                }
            }
        }
        extracted_preferences = {}

        score = await recommendation_engine._calculate_behavioral_score(
            property_data, behavioral_profile, extracted_preferences
        )

        assert score > 0.5  # Should be boosted by matching preference

    @pytest.mark.asyncio
    async def test_generate_personalized_recommendations_success(
        self,
        recommendation_engine,
        sample_extracted_preferences,
        sample_property_interactions
    ):
        """Test successful generation of personalized recommendations."""
        contact_id = "test_contact"
        recommendation_engine.property_interactions[contact_id] = sample_property_interactions

        recommendations = await recommendation_engine.generate_personalized_recommendations(
            contact_id=contact_id,
            extracted_preferences=sample_extracted_preferences,
            limit=2
        )

        assert isinstance(recommendations, PersonalizedRecommendations)
        assert len(recommendations.recommendations) <= 2
        assert recommendations.behavioral_profile["total_interactions"] == 3
        assert recommendations.learning_metadata["recommendation_method"] == "behavioral_enhanced"
        assert len(recommendations.next_learning_opportunities) > 0

    @pytest.mark.asyncio
    async def test_generate_personalized_recommendations_no_matches(
        self,
        recommendation_engine,
        sample_extracted_preferences
    ):
        """Test handling when no properties match criteria."""
        # Mock property matcher to return no matches
        recommendation_engine.property_matcher.find_matches.return_value = []

        contact_id = "test_contact"

        recommendations = await recommendation_engine.generate_personalized_recommendations(
            contact_id=contact_id,
            extracted_preferences=sample_extracted_preferences
        )

        assert len(recommendations.recommendations) == 0
        assert "no properties found" in recommendations.explanation_summary.lower()
        assert "broaden the search" in recommendations.explanation_summary.lower()

    @pytest.mark.asyncio
    async def test_generate_single_claude_explanation(
        self,
        recommendation_engine,
        mock_llm_client
    ):
        """Test Claude explanation generation for single property."""
        property_match = PropertyMatch(
            property={"price": 400000, "bedrooms": 3, "address": {"full_address": "123 Main St, Austin"}},
            base_score=0.8,
            behavioral_score=0.7,
            final_score=0.75,
            claude_explanation="",
            reasoning_breakdown={},
            behavioral_insights=[],
            recommendation_confidence=0.6
        )

        behavioral_profile = {"total_interactions": 5, "confidence_level": 0.6}
        extracted_preferences = {"budget": 450000, "bedrooms": 3}

        explanation = await recommendation_engine._generate_single_claude_explanation(
            property_match, behavioral_profile, extracted_preferences, None
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert len(explanation) <= 200  # SMS length limit
        mock_llm_client.agenerate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_single_claude_explanation_fallback(
        self,
        recommendation_engine,
        mock_llm_client
    ):
        """Test fallback explanation when Claude fails."""
        # Make Claude fail
        mock_llm_client.agenerate.side_effect = Exception("API Error")

        property_match = PropertyMatch(
            property={"price": 400000, "bedrooms": 3, "address": {"city": "Austin"}},
            base_score=0.8,
            behavioral_score=0.7,
            final_score=0.75,
            claude_explanation="",
            reasoning_breakdown={},
            behavioral_insights=[],
            recommendation_confidence=0.6
        )

        behavioral_profile = {}
        extracted_preferences = {}

        explanation = await recommendation_engine._generate_single_claude_explanation(
            property_match, behavioral_profile, extracted_preferences, None
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "400,000" in explanation  # Should include price
        assert "Austin" in explanation  # Should include location

    @pytest.mark.asyncio
    async def test_update_behavioral_preferences_like(self, recommendation_engine):
        """Test updating behavioral preferences from LIKE interaction."""
        contact_id = "test_contact"

        interaction = PropertyInteraction(
            property_id="prop1",
            interaction_type=InteractionType.LIKE,
            timestamp=datetime.utcnow(),
            property_features={"price": 400000, "bedrooms": 3, "property_type": "single_family"}
        )

        await recommendation_engine._update_behavioral_preferences(contact_id, interaction)

        preferences = recommendation_engine.behavioral_preferences.get(contact_id, [])
        assert len(preferences) == 3  # price, bedrooms, property_type

        # Check that preferences were created with appropriate confidence
        price_pref = next((p for p in preferences if p.preference_type == "price"), None)
        assert price_pref is not None
        assert price_pref.preference_value == 400000
        assert price_pref.confidence_score == 0.8  # LIKE should have high confidence

    @pytest.mark.asyncio
    async def test_update_behavioral_preferences_dislike(self, recommendation_engine):
        """Test updating behavioral preferences from DISLIKE interaction."""
        contact_id = "test_contact"

        interaction = PropertyInteraction(
            property_id="prop1",
            interaction_type=InteractionType.DISLIKE,
            timestamp=datetime.utcnow(),
            property_features={"price": 600000, "property_type": "luxury"}
        )

        await recommendation_engine._update_behavioral_preferences(contact_id, interaction)

        preferences = recommendation_engine.behavioral_preferences.get(contact_id, [])
        assert len(preferences) == 2  # price, property_type

        # Check that preferences were created with lower confidence for dislikes
        price_pref = next((p for p in preferences if p.preference_type == "price"), None)
        assert price_pref is not None
        assert price_pref.confidence_score == 0.3  # DISLIKE should have low confidence

    def test_calculate_engagement_consistency_consistent(self, recommendation_engine):
        """Test engagement consistency calculation with consistent durations."""
        durations = [60, 65, 55, 62, 58]  # Consistent around 60 seconds

        consistency = recommendation_engine._calculate_engagement_consistency(durations)

        assert consistency > 0.8  # Should be high consistency

    def test_calculate_engagement_consistency_inconsistent(self, recommendation_engine):
        """Test engagement consistency calculation with inconsistent durations."""
        durations = [10, 180, 5, 200, 15]  # Very inconsistent

        consistency = recommendation_engine._calculate_engagement_consistency(durations)

        assert consistency < 0.5  # Should be low consistency

    def test_calculate_preference_strength(self, recommendation_engine):
        """Test preference strength calculation."""
        liked_features = {"price": [400000, 450000], "property_type": ["single_family"]}
        disliked_features = {"price": [600000], "property_type": ["condo", "luxury"]}

        strengths = recommendation_engine._calculate_preference_strength(
            liked_features, disliked_features
        )

        # Price: 2 likes, 1 dislike = (2-1)/3 = 0.33
        assert strengths["price"] == (2-1)/(2+1)

        # Property type: 1 like, 2 dislikes = (1-2)/3 = -0.33
        assert strengths["property_type"] == (1-2)/(1+2)

    def test_identify_learning_opportunities_low_data(self, recommendation_engine):
        """Test learning opportunity identification with low interaction data."""
        behavioral_profile = {
            "total_interactions": 2,
            "confidence_level": 0.3,
            "learned_preferences": {}
        }

        opportunities = recommendation_engine._identify_learning_opportunities(
            behavioral_profile, []
        )

        assert "more property interactions" in " ".join(opportunities)
        assert "feedback on recommended properties" in " ".join(opportunities)
        assert "price sensitivity" in " ".join(opportunities)
        assert "preferred neighborhoods" in " ".join(opportunities)

    def test_identify_learning_opportunities_sufficient_data(self, recommendation_engine):
        """Test learning opportunity identification with sufficient data."""
        behavioral_profile = {
            "total_interactions": 10,
            "confidence_level": 0.8,
            "learned_preferences": {
                "price": {"confidence_score": 0.9},
                "location": {"confidence_score": 0.8}
            }
        }

        opportunities = recommendation_engine._identify_learning_opportunities(
            behavioral_profile, []
        )

        # Should have fewer opportunities with sufficient data
        assert len(opportunities) < 2

    @pytest.mark.asyncio
    async def test_fallback_recommendations(
        self,
        recommendation_engine,
        sample_extracted_preferences
    ):
        """Test fallback recommendations when main process fails."""
        recommendations = await recommendation_engine._fallback_recommendations(
            sample_extracted_preferences, limit=2
        )

        assert isinstance(recommendations, PersonalizedRecommendations)
        assert recommendations.learning_metadata["recommendation_method"] == "fallback_basic"
        assert len(recommendations.recommendations) <= 2

        # Should have basic explanations
        for rec in recommendations.recommendations:
            assert rec.claude_explanation != ""
            assert rec.recommendation_confidence == 0.3  # Low confidence for fallback

    def test_generate_fallback_explanation_high_score(self, recommendation_engine):
        """Test fallback explanation generation for high-scoring property."""
        property_match = PropertyMatch(
            property={
                "price": 400000,
                "bedrooms": 3,
                "address": {"city": "Austin"}
            },
            base_score=0.8,
            behavioral_score=0.8,
            final_score=0.9,  # High score
            claude_explanation="",
            reasoning_breakdown={},
            behavioral_insights=[],
            recommendation_confidence=0.6
        )

        explanation = recommendation_engine._generate_fallback_explanation(property_match)

        assert "excellent match" in explanation
        assert "400,000" in explanation
        assert "Austin" in explanation
        assert "3 bedrooms" in explanation

    def test_generate_fallback_explanation_low_score(self, recommendation_engine):
        """Test fallback explanation generation for low-scoring property."""
        property_match = PropertyMatch(
            property={
                "price": 500000,
                "bedrooms": 2,
                "address": {"city": "Round Rock"}
            },
            base_score=0.5,
            behavioral_score=0.5,
            final_score=0.5,  # Lower score
            claude_explanation="",
            reasoning_breakdown={},
            behavioral_insights=[],
            recommendation_confidence=0.4
        )

        explanation = recommendation_engine._generate_fallback_explanation(property_match)

        assert "trade-offs" in explanation
        assert "500,000" in explanation
        assert "Round Rock" in explanation