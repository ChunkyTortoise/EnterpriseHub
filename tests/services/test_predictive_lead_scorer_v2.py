import pytest

pytestmark = pytest.mark.integration

"""
Tests for Predictive Lead Scorer V2.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.ml.closing_probability_model import ModelPrediction
from ghl_real_estate_ai.ml.feature_engineering import ConversationFeatures, MarketFeatures
from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import (
    LeadInsights,
    LeadPriority,
    PredictiveLeadScorerV2,
    PredictiveScore,
)


class TestPredictiveLeadScorerV2:
    """Test suite for PredictiveLeadScorerV2 class."""

    @pytest.fixture
    def scorer(self):
        """Create PredictiveLeadScorerV2 instance for testing."""
        return PredictiveLeadScorerV2()

    @pytest.fixture
    def mock_conversation_context(self):
        """Create mock conversation context for testing."""
        return {
            "conversation_history": [
                {"role": "user", "text": "Hi, I'm looking for a house"},
                {"role": "assistant", "text": "Great! I'd love to help you find the perfect home."},
                {"role": "user", "text": "I need 3 bedrooms and 2 bathrooms in downtown area"},
                {"role": "assistant", "text": "That's a great area! What's your budget range?"},
                {"role": "user", "text": "Around $500,000. I need to move ASAP for work"},
                {"role": "assistant", "text": "Perfect! I can help you find something quickly."},
                {"role": "user", "text": "Do you have any properties available for viewing this week?"},
            ],
            "extracted_preferences": {
                "budget": "$500,000",
                "location": "downtown",
                "bedrooms": "3",
                "bathrooms": "2",
                "timeline": "ASAP",
                "motivation": "work relocation",
                "financing": "pre-approved",
            },
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
        }

    @pytest.fixture
    def mock_minimal_context(self):
        """Create minimal conversation context for testing edge cases."""
        return {
            "conversation_history": [{"role": "user", "text": "Hello"}],
            "extracted_preferences": {},
            "created_at": datetime.now().isoformat(),
        }

    @pytest.fixture
    def mock_conv_features(self):
        """Create mock conversation features."""
        return ConversationFeatures(
            message_count=7,
            avg_response_time=180.0,
            conversation_duration_minutes=60.0,
            overall_sentiment=0.7,
            urgency_score=0.9,
            engagement_score=0.8,
            question_asking_frequency=0.4,
            price_mention_count=2,
            timeline_urgency_signals=2,
            location_specificity=0.8,
            budget_to_market_ratio=0.77,
            budget_confidence=0.9,
            qualification_completeness=0.86,  # 6/7 questions answered
            missing_critical_info=["home_condition"],
            message_length_variance=300.0,
            response_consistency=0.8,
            weekend_activity=False,
            late_night_activity=False,
        )

    @pytest.fixture
    def mock_market_features(self):
        """Create mock market features."""
        return MarketFeatures(
            inventory_level=0.6,
            average_days_on_market=28,
            price_trend=0.05,  # 5% appreciation
            seasonal_factor=0.8,  # Good season
            competition_level=0.7,
            interest_rate_level=7.1,
        )

    @pytest.fixture
    def mock_ml_prediction(self):
        """Create mock ML prediction."""
        return ModelPrediction(
            closing_probability=0.75,
            confidence_interval=(0.65, 0.85),
            risk_factors=["Competition in target area"],
            positive_signals=["High engagement", "Clear budget", "Urgent timeline"],
            model_confidence=0.82,
            feature_importance={
                "qualification_completeness": 0.3,
                "engagement_score": 0.25,
                "urgency_score": 0.2,
                "budget_market_ratio": 0.15,
                "other": 0.1,
            },
        )

    @pytest.mark.asyncio
    async def test_calculate_predictive_score_success(
        self, scorer, mock_conversation_context, mock_conv_features, mock_ml_prediction
    ):
        """Test successful predictive score calculation."""
        # Mock dependencies
        with (
            patch.object(
                scorer.traditional_scorer, "calculate_with_reasoning", new_callable=AsyncMock
            ) as mock_traditional,
            patch.object(scorer.ml_model, "predict_closing_probability", return_value=mock_ml_prediction) as mock_ml,
            patch.object(
                scorer.feature_engineer, "extract_conversation_features", return_value=mock_conv_features
            ) as mock_features,
        ):
            mock_traditional.return_value = {
                "score": 6,  # 6/7 questions answered
                "classification": "hot",
                "recommended_actions": ["Schedule showing", "Follow up"],
            }

            score = await scorer.calculate_predictive_score(mock_conversation_context)

            assert isinstance(score, PredictiveScore)
            assert score.qualification_score == 6
            assert score.qualification_percentage == 85  # From scorer mapping
            assert score.closing_probability == 0.75
            assert score.priority_level == LeadPriority.HIGH or score.priority_level == LeadPriority.CRITICAL
            assert score.overall_priority_score > 70  # Should be high priority
            assert len(score.recommended_actions) > 0
            assert score.estimated_revenue_potential > 0

    @pytest.mark.asyncio
    async def test_calculate_predictive_score_minimal_data(self, scorer, mock_minimal_context):
        """Test predictive score calculation with minimal data."""
        score = await scorer.calculate_predictive_score(mock_minimal_context)

        assert isinstance(score, PredictiveScore)
        assert score.qualification_score >= 0
        assert score.closing_probability >= 0.0
        assert score.overall_priority_score >= 0.0
        assert score.priority_level in [
            LeadPriority.CRITICAL,
            LeadPriority.HIGH,
            LeadPriority.MEDIUM,
            LeadPriority.LOW,
            LeadPriority.COLD,
        ]

    @pytest.mark.asyncio
    async def test_generate_lead_insights(self, scorer, mock_conversation_context, mock_conv_features):
        """Test lead insights generation."""
        # Mock dependencies
        with (
            patch.object(scorer, "calculate_predictive_score") as mock_score,
            patch.object(scorer.feature_engineer, "extract_conversation_features", return_value=mock_conv_features),
        ):
            mock_score.return_value = PredictiveScore(
                qualification_score=6,
                qualification_percentage=85,
                closing_probability=0.75,
                closing_confidence_interval=(0.65, 0.85),
                engagement_score=80.0,
                urgency_score=90.0,
                risk_score=25.0,
                overall_priority_score=82.0,
                priority_level=LeadPriority.HIGH,
                risk_factors=["Competition"],
                positive_signals=["High engagement"],
                recommended_actions=["Call immediately"],
                optimal_contact_timing="Within 2 hours",
                time_investment_recommendation="High investment",
                estimated_revenue_potential=20000.0,
                effort_efficiency_score=400.0,
                model_confidence=0.8,
                last_updated=datetime.now(),
            )

            insights = await scorer.generate_lead_insights(mock_conversation_context)

            assert isinstance(insights, LeadInsights)
            assert insights.engagement_trend in ["increasing", "stable", "declining"]
            assert insights.conversation_quality_score >= 0.0
            assert insights.estimated_time_to_close > 0
            assert insights.probability_of_churn >= 0.0
            assert insights.recommended_effort_level in ["minimal", "standard", "intensive"]

    @pytest.mark.asyncio
    async def test_calculate_engagement_score(self, scorer, mock_conv_features):
        """Test engagement score calculation."""
        engagement_score = await scorer._calculate_engagement_score(mock_conv_features)

        assert isinstance(engagement_score, float)
        assert 0.0 <= engagement_score <= 100.0

        # High engagement features should result in high score
        assert engagement_score > 50.0  # With good conversation features

    @pytest.mark.asyncio
    async def test_calculate_urgency_score(self, scorer, mock_conversation_context, mock_conv_features):
        """Test urgency score calculation."""
        urgency_score = await scorer._calculate_urgency_score(mock_conv_features, mock_conversation_context)

        assert isinstance(urgency_score, float)
        assert 0.0 <= urgency_score <= 100.0

        # ASAP timeline should result in high urgency
        assert urgency_score > 60.0

    @pytest.mark.asyncio
    async def test_calculate_risk_score(self, scorer, mock_conv_features, mock_ml_prediction):
        """Test risk score calculation."""
        risk_score = await scorer._calculate_risk_score(mock_conv_features, mock_ml_prediction)

        assert isinstance(risk_score, float)
        assert 0.0 <= risk_score <= 100.0

        # Well-qualified lead should have lower risk
        assert risk_score < 50.0  # Good qualification features

    def test_calculate_composite_score(self, scorer):
        """Test composite score calculation."""
        composite = scorer._calculate_composite_score(
            qualification_pct=85.0, closing_probability_pct=75.0, engagement_score=80.0, urgency_score=90.0
        )

        assert isinstance(composite, float)
        assert 0.0 <= composite <= 100.0
        # Should be weighted average, so between input values
        assert 75.0 <= composite <= 90.0

    def test_determine_priority_level(self, scorer):
        """Test priority level determination."""
        # Test different score ranges
        test_cases = [
            (95.0, LeadPriority.CRITICAL),
            (80.0, LeadPriority.HIGH),
            (60.0, LeadPriority.MEDIUM),
            (35.0, LeadPriority.LOW),
            (10.0, LeadPriority.COLD),
        ]

        for score, expected_priority in test_cases:
            priority = scorer._determine_priority_level(score)
            assert priority == expected_priority

    @pytest.mark.asyncio
    async def test_generate_advanced_recommendations(self, scorer, mock_conv_features, mock_ml_prediction):
        """Test advanced recommendations generation."""
        traditional_result = {"score": 6, "recommended_actions": ["Schedule showing"]}

        # Test critical priority
        actions = await scorer._generate_advanced_recommendations(
            LeadPriority.CRITICAL, mock_ml_prediction, mock_conv_features, traditional_result
        )

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert any("IMMEDIATE" in action for action in actions)

        # Test low priority
        actions_low = await scorer._generate_advanced_recommendations(
            LeadPriority.LOW, mock_ml_prediction, mock_conv_features, traditional_result
        )

        assert isinstance(actions_low, list)
        assert any("nurture" in action.lower() for action in actions_low)

    @pytest.mark.asyncio
    async def test_calculate_roi_predictions(self, scorer, mock_conv_features, mock_conversation_context):
        """Test ROI predictions calculation."""
        revenue, efficiency, yield_est, margin = await scorer._calculate_roi_predictions(
            closing_probability=0.75, conv_features=mock_conv_features, context=mock_conversation_context
        )

        assert isinstance(revenue, float)
        assert isinstance(efficiency, float)
        assert revenue > 0  # Should have positive revenue potential
        assert efficiency > 0  # Should have positive efficiency

    @pytest.mark.asyncio
    async def test_analyze_optimal_contact_timing(self, scorer, mock_conv_features):
        """Test optimal contact timing analysis."""
        timing = await scorer._analyze_optimal_contact_timing(mock_conv_features, 85.0)  # High urgency

        assert isinstance(timing, str)
        assert len(timing) > 0
        # High urgency should suggest quick contact
        assert "hour" in timing.lower()

    @pytest.mark.asyncio
    async def test_recommend_time_investment(self, scorer):
        """Test time investment recommendation."""
        # High probability, high efficiency
        recommendation = await scorer._recommend_time_investment(0.8, 600.0)
        assert "Maximum" in recommendation or "High" in recommendation

        # Low probability, low efficiency
        recommendation = await scorer._recommend_time_investment(0.2, 100.0)
        assert "Minimal" in recommendation or "minimal" in recommendation

    @pytest.mark.asyncio
    async def test_fallback_scoring(self, scorer, mock_conversation_context):
        """Test fallback scoring when ML model fails."""
        score = await scorer._fallback_scoring(mock_conversation_context)

        assert isinstance(score, PredictiveScore)
        assert score.closing_probability > 0.0
        assert "ML model unavailable" in score.risk_factors
        assert score.priority_level in [
            LeadPriority.CRITICAL,
            LeadPriority.HIGH,
            LeadPriority.MEDIUM,
            LeadPriority.LOW,
            LeadPriority.COLD,
        ]

    @pytest.mark.asyncio
    async def test_caching_behavior(self, scorer, mock_conversation_context):
        """Test that scoring results are properly cached."""
        # Mock cache to verify caching behavior
        with patch.object(scorer.traditional_scorer, "calculate_with_reasoning", new_callable=AsyncMock) as mock_scorer:
            mock_scorer.return_value = {"score": 5, "classification": "hot", "recommended_actions": ["Follow up"]}

            # First call
            score1 = await scorer.calculate_predictive_score(mock_conversation_context)

            # Second call with same context
            score2 = await scorer.calculate_predictive_score(mock_conversation_context)

            # Should get consistent results
            assert score1.qualification_score == score2.qualification_score
            assert score1.overall_priority_score == score2.overall_priority_score

    @pytest.mark.asyncio
    async def test_error_handling(self, scorer):
        """Test error handling with invalid inputs."""
        # Test with None context
        score = await scorer.calculate_predictive_score(None)
        assert isinstance(score, PredictiveScore)

        # Test with malformed context
        malformed_context = {"invalid": "data"}
        score = await scorer.calculate_predictive_score(malformed_context)
        assert isinstance(score, PredictiveScore)

    @pytest.mark.asyncio
    async def test_edge_case_scoring(self, scorer):
        """Test scoring with edge case data."""
        # Empty conversation
        empty_context = {
            "conversation_history": [],
            "extracted_preferences": {},
            "created_at": datetime.now().isoformat(),
        }

        score = await scorer.calculate_predictive_score(empty_context)
        assert isinstance(score, PredictiveScore)
        assert score.qualification_score == 0
        assert score.priority_level == LeadPriority.COLD

        # Very long conversation
        long_context = {
            "conversation_history": [
                {"role": "user", "text": f"Message {i}? I am very interested in learning more about this property."}
                for i in range(100)
            ],
            "extracted_preferences": {"budget": "1000000", "location": "luxury area", "timeline": "urgent"},
            "created_at": datetime.now().isoformat(),
        }

        score_long = await scorer.calculate_predictive_score(long_context)
        assert isinstance(score_long, PredictiveScore)
        assert score_long.engagement_score > score.engagement_score  # More engagement

    @pytest.mark.asyncio
    async def test_priority_level_consistency(self, scorer, mock_conversation_context):
        """Test that priority levels are consistently assigned."""
        score = await scorer.calculate_predictive_score(mock_conversation_context)

        # Verify priority level matches the overall score
        if score.overall_priority_score >= 90:
            assert score.priority_level == LeadPriority.CRITICAL
        elif score.overall_priority_score >= 75:
            assert score.priority_level == LeadPriority.HIGH
        elif score.overall_priority_score >= 50:
            assert score.priority_level == LeadPriority.MEDIUM
        elif score.overall_priority_score >= 25:
            assert score.priority_level == LeadPriority.LOW
        else:
            assert score.priority_level == LeadPriority.COLD

    @pytest.mark.asyncio
    async def test_response_pattern_analysis(self, scorer, mock_conv_features):
        """Test response pattern analysis."""
        pattern = await scorer._analyze_response_patterns(mock_conv_features)

        assert isinstance(pattern, str)
        assert len(pattern) > 0
        # Should describe the pattern meaningfully
        assert any(word in pattern.lower() for word in ["consistent", "inconsistent", "engaged"])

    @pytest.mark.asyncio
    async def test_engagement_trend_analysis(self, scorer, mock_conversation_context):
        """Test engagement trend analysis."""
        trend = await scorer._analyze_engagement_trend(mock_conversation_context)

        assert trend in ["increasing", "stable", "declining"]

    @pytest.mark.asyncio
    async def test_conversation_quality_calculation(self, scorer, mock_conv_features):
        """Test conversation quality score calculation."""
        quality = await scorer._calculate_conversation_quality(mock_conv_features)

        assert isinstance(quality, float)
        assert 0.0 <= quality <= 100.0
        # High-quality conversation features should yield high score
        assert quality > 60.0  # With good mock features

    @pytest.mark.asyncio
    async def test_market_timing_analysis(self, scorer, mock_market_features):
        """Test market timing analysis."""
        timing = await scorer._analyze_market_timing(mock_market_features)

        assert isinstance(timing, str)
        assert len(timing) > 0
        # Should provide meaningful market timing insight
        assert any(word in timing.lower() for word in ["excellent", "good", "neutral", "challenging"])

    @pytest.mark.asyncio
    async def test_next_best_action_recommendation(self, scorer, mock_conv_features):
        """Test next best action recommendation."""
        mock_score = PredictiveScore(
            qualification_score=6,
            qualification_percentage=85,
            closing_probability=0.75,
            closing_confidence_interval=(0.65, 0.85),
            engagement_score=80.0,
            urgency_score=90.0,
            risk_score=25.0,
            overall_priority_score=82.0,
            priority_level=LeadPriority.CRITICAL,
            risk_factors=[],
            positive_signals=[],
            recommended_actions=[],
            optimal_contact_timing="",
            time_investment_recommendation="",
            estimated_revenue_potential=20000.0,
            effort_efficiency_score=400.0,
            model_confidence=0.8,
            last_updated=datetime.now(),
        )

        action = await scorer._recommend_next_best_action(mock_score, mock_conv_features)

        assert isinstance(action, str)
        assert len(action) > 0
        # Critical priority with high qualification should suggest showing
        assert any(word in action.lower() for word in ["show", "property", "schedule", "immediate"])

    @pytest.mark.asyncio
    async def test_time_to_close_estimation(self, scorer, mock_conv_features):
        """Test time to close estimation."""
        # High closing probability
        days_high = await scorer._estimate_time_to_close(0.8, mock_conv_features)

        # Low closing probability
        days_low = await scorer._estimate_time_to_close(0.3, mock_conv_features)

        assert isinstance(days_high, int)
        assert isinstance(days_low, int)
        assert days_high > 0
        assert days_low > 0
        # High probability should close faster
        assert days_high < days_low

    @pytest.mark.asyncio
    async def test_churn_probability_calculation(self, scorer, mock_conv_features):
        """Test churn probability calculation."""
        mock_score = PredictiveScore(
            qualification_score=6,
            qualification_percentage=85,
            closing_probability=0.75,
            closing_confidence_interval=(0.65, 0.85),
            engagement_score=80.0,
            urgency_score=90.0,
            risk_score=25.0,
            overall_priority_score=82.0,
            priority_level=LeadPriority.HIGH,
            risk_factors=[],
            positive_signals=[],
            recommended_actions=[],
            optimal_contact_timing="",
            time_investment_recommendation="",
            estimated_revenue_potential=20000.0,
            effort_efficiency_score=400.0,
            model_confidence=0.8,
            last_updated=datetime.now(),
        )

        churn_prob = await scorer._calculate_churn_probability(mock_conv_features, mock_score)

        assert isinstance(churn_prob, float)
        assert 0.0 <= churn_prob <= 1.0
        # Well-engaged lead should have lower churn probability
        assert churn_prob < 0.4  # With good features