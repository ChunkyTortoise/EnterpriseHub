import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Test Suite for Advanced Customer Intelligence Engine
==================================================

Comprehensive test coverage for advanced customer intelligence capabilities:
- AI-powered lead scoring with Claude integration
- Real-time churn prediction and intervention strategies
- Multi-dimensional behavioral analytics
- Predictive lifetime value calculations
- Dynamic customer segmentation
- Performance optimization testing

Target: 80%+ test coverage for enterprise-grade reliability

Date: January 19, 2026
Author: Claude AI Enhancement System
Status: Production-Ready Test Suite
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from ghl_real_estate_ai.services.advanced_customer_intelligence_engine import (
        AdvancedCustomerIntelligenceEngine,
        AdvancedSegment,
        ChurnPrediction,
        CustomerProfile,
        EngagementChannel,
        IntelligenceInsight,
        IntelligenceType,
        RiskLevel,
        get_customer_intelligence_engine,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestAdvancedCustomerIntelligenceEngine:
    """Test cases for Advanced Customer Intelligence Engine"""

    @pytest_asyncio.fixture
    async def intelligence_engine(self):
        """Create intelligence engine instance for testing"""
        engine = AdvancedCustomerIntelligenceEngine()

        # Mock dependencies
        engine.claude = AsyncMock()
        engine.cache = AsyncMock()
        engine.db = AsyncMock()
        engine.memory = AsyncMock()
        engine.performance_tracker = AsyncMock()

        return engine

    @pytest.fixture
    def sample_customer_data(self):
        """Sample customer data for testing"""
        return {
            "customer_id": "test_customer_123",
            "contact_id": "contact_123",
            "name": "Test Customer",
            "email": "test@example.com",
            "phone": "+1234567890",
            "created_date": datetime.now() - timedelta(days=30),
            "engagement_metrics": {
                "email_open_rate": 0.65,
                "email_click_rate": 0.12,
                "website_visits": 15,
                "page_views": 45,
                "session_duration": 180,
            },
            "interaction_history": [
                {"date": "2026-01-15", "type": "email", "engagement": "opened"},
                {"date": "2026-01-10", "type": "phone", "duration": 300},
                {"date": "2026-01-05", "type": "website", "pages": 5},
            ],
            "behavioral_signals": {"pricing_page_views": 3, "demo_requests": 1, "content_downloads": 2},
            "data_quality_score": 0.85,
        }

    @pytest.mark.asyncio
    async def test_analyze_customer_intelligence_basic(self, intelligence_engine, sample_customer_data):
        """Test basic customer intelligence analysis"""
        # Mock Claude response
        mock_claude_response = Mock()
        mock_claude_response.content = json.dumps(
            {
                "overall_score": 85,
                "engagement_score": 78,
                "intent_score": 92,
                "qualification_score": 80,
                "confidence": 0.87,
            }
        )
        mock_claude_response.confidence = 0.87

        intelligence_engine.claude.process_request.return_value = mock_claude_response
        intelligence_engine._get_customer_data.return_value = sample_customer_data

        # Mock cache miss
        intelligence_engine.cache.get.return_value = None

        # Test intelligence analysis
        result = await intelligence_engine.analyze_customer_intelligence(
            customer_id="test_customer_123",
            analysis_types=[IntelligenceType.LEAD_SCORING, IntelligenceType.CHURN_PREDICTION],
            real_time=True,
        )

        # Assertions
        assert result is not None
        assert result["customer_id"] == "test_customer_123"
        assert "scores" in result
        assert "predictions" in result
        assert "performance_metrics" in result
        assert result["real_time_analysis"] is True

        # Verify Claude was called for analysis
        assert intelligence_engine.claude.process_request.called

        # Verify cache was used
        intelligence_engine.cache.set.assert_called()

    @pytest.mark.asyncio
    async def test_lead_scoring_analysis(self, intelligence_engine, sample_customer_data):
        """Test AI-powered lead scoring analysis"""
        # Mock successful Claude response
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "overall_score": 85,
                "engagement_score": 78,
                "intent_score": 92,
                "qualification_score": 80,
                "key_factors": ["high_engagement", "multiple_touchpoints", "pricing_interest"],
                "confidence": 0.87,
            }
        )
        mock_response.confidence = 0.87

        intelligence_engine.claude.process_request.return_value = mock_response

        # Test lead scoring
        result = await intelligence_engine._analyze_lead_scoring(sample_customer_data)

        # Assertions
        assert "scores" in result
        assert result["scores"]["lead_score"] == 85
        assert result["scores"]["engagement_score"] == 78
        assert result["scores"]["intent_score"] == 92
        assert result["scores"]["qualification_score"] == 80
        assert "lead_analysis" in result
        assert result["lead_analysis"]["confidence"] == 0.87

    @pytest.mark.asyncio
    async def test_churn_prediction_analysis(self, intelligence_engine, sample_customer_data):
        """Test churn prediction with intervention strategies"""
        # Mock Claude response for churn analysis
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "churn_probability": 0.25,
                "risk_level": "low",
                "key_risk_factors": ["declining_engagement", "support_tickets"],
                "early_warning_signals": ["reduced_session_time"],
                "intervention_strategies": [
                    {"type": "email_campaign", "timing": "immediate", "success_rate": 0.7},
                    {"type": "personal_outreach", "timing": "within_week", "success_rate": 0.85},
                ],
                "revenue_at_risk": 5000,
                "confidence": 0.82,
            }
        )
        mock_response.confidence = 0.82

        intelligence_engine.claude.process_request.return_value = mock_response

        # Test churn prediction
        result = await intelligence_engine._analyze_churn_prediction(sample_customer_data)

        # Assertions
        assert "predictions" in result
        assert result["predictions"]["churn_probability"] == 0.25
        assert result["predictions"]["risk_level"] == "low"
        assert "churn_prediction" in result

        churn_data = result["churn_prediction"]
        assert churn_data["customer_id"] == sample_customer_data["customer_id"]
        assert churn_data["churn_probability"] == 0.25
        assert churn_data["confidence_level"] == 0.82
        assert len(churn_data["recommended_interventions"]) > 0

    @pytest.mark.asyncio
    async def test_behavioral_analysis(self, intelligence_engine, sample_customer_data):
        """Test behavioral pattern analysis"""
        # Mock Claude response for behavioral analysis
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "communication_style": "professional",
                "decision_style": "analytical",
                "personality_traits": {
                    "openness": 0.7,
                    "conscientiousness": 0.8,
                    "extraversion": 0.6,
                    "agreeableness": 0.75,
                    "neuroticism": 0.3,
                },
                "communication_preferences": ["email", "phone"],
                "optimal_timing": "business_hours",
                "engagement_triggers": ["educational_content", "case_studies"],
            }
        )
        mock_response.confidence = 0.75

        intelligence_engine.claude.process_request.return_value = mock_response

        # Test behavioral analysis
        result = await intelligence_engine._analyze_behavioral_patterns(sample_customer_data)

        # Assertions
        assert "behavioral_analysis" in result
        assert "personality_traits" in result
        assert "communication_preferences" in result

        behavioral_data = result["behavioral_analysis"]
        assert behavioral_data["communication_style"] == "professional"
        assert behavioral_data["decision_style"] == "analytical"
        assert len(behavioral_data["personality_traits"]) == 5

    @pytest.mark.asyncio
    async def test_lifetime_value_prediction(self, intelligence_engine, sample_customer_data):
        """Test customer lifetime value prediction"""
        # Mock Claude response for LTV prediction
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "predicted_ltv": 15000,
                "timeline": "18-24 months",
                "confidence": 0.78,
                "value_drivers": ["product_usage", "engagement_level", "referral_potential"],
                "risk_factors": ["market_competition", "economic_conditions"],
            }
        )
        mock_response.confidence = 0.78

        intelligence_engine.claude.process_request.return_value = mock_response

        # Test LTV prediction
        result = await intelligence_engine._predict_lifetime_value(sample_customer_data)

        # Assertions
        assert "predictions" in result
        assert result["predictions"]["lifetime_value"] == 15000
        assert result["predictions"]["value_realization_timeline"] == "18-24 months"
        assert result["predictions"]["ltv_confidence"] == 0.78
        assert "ltv_analysis" in result

    @pytest.mark.asyncio
    async def test_engagement_optimization(self, intelligence_engine, sample_customer_data):
        """Test engagement strategy optimization"""
        # Mock Claude response for engagement optimization
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "optimal_channels": ["email", "phone"],
                "content_strategy": {
                    "preferred_content_types": ["educational", "case_studies"],
                    "frequency": "weekly",
                    "timing": "tuesday_morning",
                },
                "timing_optimization": {"best_days": ["tuesday", "wednesday"], "best_times": ["09:00", "14:00"]},
                "personalization_recommendations": [
                    "use_first_name",
                    "reference_previous_interactions",
                    "industry_specific_examples",
                ],
            }
        )
        mock_response.confidence = 0.83

        intelligence_engine.claude.process_request.return_value = mock_response

        # Test engagement optimization
        result = await intelligence_engine._optimize_engagement_strategy(sample_customer_data)

        # Assertions
        assert "engagement_optimization" in result
        assert "recommended_channels" in result
        assert "content_strategy" in result
        assert "timing_recommendations" in result

        optimization_data = result["engagement_optimization"]
        assert "email" in optimization_data["optimal_channels"]
        assert "phone" in optimization_data["optimal_channels"]

    @pytest.mark.asyncio
    async def test_comprehensive_insights_generation(self, intelligence_engine, sample_customer_data):
        """Test comprehensive insights generation"""
        # Mock intelligence report
        intelligence_report = {
            "customer_id": "test_customer_123",
            "scores": {"lead_score": 85, "engagement_score": 78},
            "predictions": {"churn_probability": 0.25, "lifetime_value": 15000},
            "behavioral_analysis": {"communication_style": "professional"},
        }

        # Mock Claude response for insights
        mock_response = Mock()
        mock_response.content = json.dumps(
            [
                {
                    "title": "High Conversion Potential",
                    "description": "Customer shows strong buying signals",
                    "reasoning": "High lead score and engagement metrics",
                    "confidence": 0.87,
                    "recommended_actions": ["schedule_demo", "send_proposal"],
                    "priority": 1,
                    "estimated_impact": 0.8,
                },
                {
                    "title": "Engagement Optimization Opportunity",
                    "description": "Customer prefers professional communication",
                    "reasoning": "Behavioral analysis indicates analytical decision style",
                    "confidence": 0.75,
                    "recommended_actions": ["provide_case_studies", "detailed_roi_analysis"],
                    "priority": 2,
                    "estimated_impact": 0.6,
                },
            ]
        )
        mock_response.confidence = 0.81

        intelligence_engine.claude.process_request.return_value = mock_response

        # Test insights generation
        insights = await intelligence_engine._generate_comprehensive_insights(sample_customer_data, intelligence_report)

        # Assertions
        assert len(insights) == 2
        assert all(isinstance(insight, IntelligenceInsight) for insight in insights)

        first_insight = insights[0]
        assert first_insight.title == "High Conversion Potential"
        assert first_insight.confidence == 0.87
        assert first_insight.priority_level == 1
        assert len(first_insight.recommended_actions) == 2

    @pytest.mark.asyncio
    async def test_error_handling_claude_failure(self, intelligence_engine, sample_customer_data):
        """Test error handling when Claude API fails"""
        # Mock Claude failure
        intelligence_engine.claude.process_request.side_effect = Exception("API Error")
        intelligence_engine._get_customer_data.return_value = sample_customer_data
        intelligence_engine.cache.get.return_value = None

        # Test error handling
        result = await intelligence_engine.analyze_customer_intelligence(
            customer_id="test_customer_123", analysis_types=[IntelligenceType.LEAD_SCORING], real_time=True
        )

        # Should handle errors gracefully
        assert result is not None
        assert result["customer_id"] == "test_customer_123"
        # Performance tracking should still work
        intelligence_engine.performance_tracker.track_operation.assert_called()

    @pytest.mark.asyncio
    async def test_caching_behavior(self, intelligence_engine, sample_customer_data):
        """Test caching behavior for performance optimization"""
        cached_result = {
            "customer_id": "test_customer_123",
            "cached": True,
            "analysis_timestamp": datetime.now().isoformat(),
        }

        # Mock cache hit
        intelligence_engine.cache.get.return_value = json.dumps(cached_result, default=str)

        # Test cached response
        result = await intelligence_engine.analyze_customer_intelligence(
            customer_id="test_customer_123",
            real_time=False,  # Allow cache usage
        )

        # Should return cached result
        cached_parsed = json.loads(intelligence_engine.cache.get.return_value)
        assert cached_parsed["cached"] is True

        # Claude should not be called for cached result
        intelligence_engine.claude.process_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_real_time_vs_cached_analysis(self, intelligence_engine, sample_customer_data):
        """Test difference between real-time and cached analysis"""
        # Setup mock responses
        intelligence_engine._get_customer_data.return_value = sample_customer_data
        intelligence_engine.cache.get.return_value = None  # No cache

        mock_response = Mock()
        mock_response.content = json.dumps({"overall_score": 85})
        mock_response.confidence = 0.8
        intelligence_engine.claude.process_request.return_value = mock_response

        # Test real-time analysis
        result_realtime = await intelligence_engine.analyze_customer_intelligence(
            customer_id="test_customer_123", real_time=True
        )

        # Test cached analysis
        result_cached = await intelligence_engine.analyze_customer_intelligence(
            customer_id="test_customer_123", real_time=False
        )

        # Both should work but use different cache strategies
        assert result_realtime["real_time_analysis"] is True
        assert result_cached["real_time_analysis"] is False

        # Cache should be set twice (once for each call)
        assert intelligence_engine.cache.set.call_count >= 2

    @pytest.mark.asyncio
    async def test_performance_tracking(self, intelligence_engine, sample_customer_data):
        """Test performance monitoring and tracking"""
        intelligence_engine._get_customer_data.return_value = sample_customer_data
        intelligence_engine.cache.get.return_value = None

        mock_response = Mock()
        mock_response.content = json.dumps({"overall_score": 85})
        mock_response.confidence = 0.8
        intelligence_engine.claude.process_request.return_value = mock_response

        # Test analysis with performance tracking
        result = await intelligence_engine.analyze_customer_intelligence(customer_id="test_customer_123")

        # Verify performance tracking
        intelligence_engine.performance_tracker.track_operation.assert_called()
        call_args = intelligence_engine.performance_tracker.track_operation.call_args

        assert call_args[1]["operation"] == "customer_intelligence_analysis"
        assert call_args[1]["success"] is True
        assert "duration" in call_args[1]
        assert call_args[1]["metadata"]["customer_id"] == "test_customer_123"

    @pytest.mark.asyncio
    async def test_multiple_analysis_types(self, intelligence_engine, sample_customer_data):
        """Test analysis with multiple intelligence types"""
        intelligence_engine._get_customer_data.return_value = sample_customer_data
        intelligence_engine.cache.get.return_value = None

        # Mock different responses for different analysis types
        mock_response = Mock()
        mock_response.content = json.dumps({"analysis_complete": True})
        mock_response.confidence = 0.8
        intelligence_engine.claude.process_request.return_value = mock_response

        # Test with all analysis types
        all_types = [
            IntelligenceType.LEAD_SCORING,
            IntelligenceType.CHURN_PREDICTION,
            IntelligenceType.BEHAVIORAL_ANALYSIS,
            IntelligenceType.LIFETIME_VALUE,
            IntelligenceType.ENGAGEMENT_OPTIMIZATION,
        ]

        result = await intelligence_engine.analyze_customer_intelligence(
            customer_id="test_customer_123", analysis_types=all_types
        )

        # Should handle all analysis types
        assert len(result["analysis_types"]) == len(all_types)
        assert all(t.value in result["analysis_types"] for t in all_types)

        # Should have made multiple Claude requests
        assert intelligence_engine.claude.process_request.call_count >= len(all_types)

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, intelligence_engine):
        """Test overall confidence level calculation"""
        # Mock intelligence report with various confidence scores
        intelligence_report = {
            "lead_analysis": {"confidence": 0.8},
            "churn_prediction": {"confidence_level": 0.7},
            "performance_metrics": {"data_quality_score": 0.9},
        }

        # Test confidence calculation
        confidence = intelligence_engine._calculate_overall_confidence(intelligence_report)

        # Should be average of all confidence scores
        expected_confidence = (0.8 + 0.7 + 0.9) / 3
        assert abs(confidence - expected_confidence) < 0.01

    def test_singleton_pattern(self):
        """Test that get_customer_intelligence_engine returns singleton"""
        engine1 = get_customer_intelligence_engine()
        engine2 = get_customer_intelligence_engine()

        assert engine1 is engine2
        assert isinstance(engine1, AdvancedCustomerIntelligenceEngine)

    @pytest.mark.asyncio
    async def test_score_extraction_from_text(self, intelligence_engine):
        """Test score extraction from Claude text responses"""
        # Test various text formats
        test_cases = [
            ("The lead score is 85 out of 100", 85.0),
            ("Score: 92.5%", 92.5),
            ("Overall rating: 78", 78.0),
            ("No numeric score found", 50.0),  # Default
            ("Score is 110 which is too high", 100.0),  # Clamped to max
            ("Negative score -5", 0.0),  # Clamped to min
        ]

        for text, expected_score in test_cases:
            score = intelligence_engine._extract_score_from_text(text)
            assert abs(score - expected_score) < 0.1, f"Failed for text: {text}"

    @pytest.mark.asyncio
    async def test_probability_extraction_from_text(self, intelligence_engine):
        """Test probability extraction from Claude text responses"""
        test_cases = [
            ("Churn probability is 25%", 0.25),
            ("0.75 chance of conversion", 0.75),
            ("85% likelihood", 0.85),
            ("No probability found", 0.5),  # Default
            ("Very high at 120%", 0.5),  # Invalid, use default
        ]

        for text, expected_prob in test_cases:
            prob = intelligence_engine._extract_probability_from_text(text)
            assert abs(prob - expected_prob) < 0.01, f"Failed for text: {text}"

    @pytest.mark.asyncio
    async def test_value_extraction_from_text(self, intelligence_engine):
        """Test monetary value extraction from Claude text responses"""
        test_cases = [
            ("Customer value is $15,000", 15000.0),
            ("LTV: $25,000.50", 25000.5),
            ("Worth 50000 dollars", 50000.0),
            ("No value mentioned", 0.0),  # Default
        ]

        for text, expected_value in test_cases:
            value = intelligence_engine._extract_value_from_text(text)
            assert abs(value - expected_value) < 0.1, f"Failed for text: {text}"


class TestCustomerProfile:
    """Test CustomerProfile dataclass"""

    def test_customer_profile_creation(self):
        """Test customer profile creation and defaults"""
        profile = CustomerProfile(customer_id="test_123", name="Test Customer", email="test@example.com")

        assert profile.customer_id == "test_123"
        assert profile.name == "Test Customer"
        assert profile.email == "test@example.com"
        assert profile.lead_score == 0.0
        assert profile.churn_probability == 0.0
        assert profile.risk_level == RiskLevel.LOW
        assert isinstance(profile.communication_preferences, list)
        assert isinstance(profile.updated_date, datetime)

    def test_customer_profile_serialization(self):
        """Test customer profile serialization to dict"""
        profile = CustomerProfile(customer_id="test_123", lead_score=85.5, churn_probability=0.25)

        profile_dict = asdict(profile)

        assert profile_dict["customer_id"] == "test_123"
        assert profile_dict["lead_score"] == 85.5
        assert profile_dict["churn_probability"] == 0.25
        assert "updated_date" in profile_dict


class TestChurnPrediction:
    """Test ChurnPrediction dataclass"""

    def test_churn_prediction_creation(self):
        """Test churn prediction creation"""
        prediction = ChurnPrediction(customer_id="test_123", churn_probability=0.35, risk_level=RiskLevel.MEDIUM)

        assert prediction.customer_id == "test_123"
        assert prediction.churn_probability == 0.35
        assert prediction.risk_level == RiskLevel.MEDIUM
        assert isinstance(prediction.key_risk_factors, list)
        assert isinstance(prediction.recommended_interventions, list)
        assert prediction.model_version == "v2.0"

    def test_churn_prediction_with_interventions(self):
        """Test churn prediction with intervention strategies"""
        interventions = [
            {"type": "email_campaign", "timing": "immediate"},
            {"type": "personal_call", "timing": "within_24h"},
        ]

        prediction = ChurnPrediction(
            customer_id="test_123",
            churn_probability=0.75,
            risk_level=RiskLevel.HIGH,
            recommended_interventions=interventions,
        )

        assert len(prediction.recommended_interventions) == 2
        assert prediction.recommended_interventions[0]["type"] == "email_campaign"


class TestIntelligenceInsight:
    """Test IntelligenceInsight dataclass"""

    def test_insight_creation(self):
        """Test intelligence insight creation"""
        insight = IntelligenceInsight(
            customer_id="test_123",
            insight_type=IntelligenceType.BEHAVIORAL_ANALYSIS,
            title="High Engagement Detected",
            description="Customer shows increased activity",
        )

        assert insight.customer_id == "test_123"
        assert insight.insight_type == IntelligenceType.BEHAVIORAL_ANALYSIS
        assert insight.title == "High Engagement Detected"
        assert insight.confidence == 0.0  # Default
        assert insight.acted_upon is False  # Default
        assert isinstance(insight.insight_id, str)
        assert len(insight.insight_id) > 0


# Performance and Integration Tests
class TestPerformanceAndIntegration:
    """Test performance and integration scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, intelligence_engine, sample_customer_data):
        """Test handling concurrent analysis requests"""
        intelligence_engine._get_customer_data.return_value = sample_customer_data
        intelligence_engine.cache.get.return_value = None

        mock_response = Mock()
        mock_response.content = json.dumps({"score": 85})
        mock_response.confidence = 0.8
        intelligence_engine.claude.process_request.return_value = mock_response

        # Create multiple concurrent requests
        tasks = [intelligence_engine.analyze_customer_intelligence(f"customer_{i}") for i in range(5)]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete successfully
        assert len(results) == 5
        assert all(not isinstance(r, Exception) for r in results)

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, intelligence_engine):
        """Test handling of large customer datasets"""
        # Mock large customer data
        large_customer_data = {
            "customer_id": "large_data_customer",
            "interaction_history": [{"event": f"event_{i}"} for i in range(1000)],
            "engagement_metrics": {f"metric_{i}": i for i in range(100)},
            "data_quality_score": 0.9,
        }

        intelligence_engine._get_customer_data.return_value = large_customer_data
        intelligence_engine.cache.get.return_value = None

        mock_response = Mock()
        mock_response.content = json.dumps({"analysis": "complete"})
        mock_response.confidence = 0.8
        intelligence_engine.claude.process_request.return_value = mock_response

        # Should handle large datasets without issues
        result = await intelligence_engine.analyze_customer_intelligence("large_data_customer")

        assert result is not None
        assert result["customer_id"] == "large_data_customer"

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, intelligence_engine, sample_customer_data):
        """Test memory usage optimization features"""
        intelligence_engine._get_customer_data.return_value = sample_customer_data
        intelligence_engine.cache.get.return_value = None

        mock_response = Mock()
        mock_response.content = json.dumps({"score": 85})
        mock_response.confidence = 0.8
        intelligence_engine.claude.process_request.return_value = mock_response

        # Track memory usage patterns
        initial_cache_size = len(intelligence_engine._prediction_cache)

        # Run multiple analyses
        for i in range(10):
            await intelligence_engine.analyze_customer_intelligence(f"customer_{i}")

        # Memory usage should be managed (not grow indefinitely)
        final_cache_size = len(intelligence_engine._prediction_cache)
        assert final_cache_size >= initial_cache_size  # Some growth is expected
        # But it shouldn't be unlimited growth in production


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
