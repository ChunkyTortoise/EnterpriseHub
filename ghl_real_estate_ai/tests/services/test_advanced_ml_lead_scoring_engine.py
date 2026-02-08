"""
Comprehensive test suite for Advanced ML Lead Scoring Engine

Tests cover:
- ML feature extraction and validation
- Model prediction accuracy and reliability
- Error handling and fallback behavior
- Performance requirements (<100ms)
- Silent failure detection
- Integration with existing services
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import (
    AdvancedMLLeadScoringEngine,
    MLFeatureVector,
    MLScoringResult,
    XGBoostConversionModel,
    create_advanced_ml_scoring_engine,
)


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        "id": "lead_123",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@techcorp.com",
        "phone": "+1-555-123-4567",
        "company": "TechCorp Inc",
        "company_size": 500,
        "company_revenue": 50000000,
        "job_title": "VP Engineering",
        "source": "referral",
        "interactions": 5,
        "last_activity": datetime.now().isoformat(),
        "custom_fields": {
            "pageViews": 8,
            "timeOnSite": 420,
            "downloadedContent": True,
            "emailOpens": 3,
            "emailClicks": 2,
            "emailReplies": 1,
            "linkedinConnection": True,
        },
    }


@pytest.fixture
def sample_feature_vector():
    """Sample feature vector for testing"""
    return MLFeatureVector(
        email_open_rate=0.75,
        email_click_rate=0.5,
        response_velocity=2.5,
        conversation_depth=15.0,
        engagement_consistency=0.8,
        property_view_frequency=1.2,
        search_refinement_count=3,
        price_range_stability=0.9,
        location_focus_score=0.85,
        timing_urgency_signals=0.7,
        budget_clarity_score=0.8,
        financing_readiness=0.9,
        price_sensitivity=0.4,
        affordability_ratio=0.75,
        question_sophistication=0.8,
        decision_maker_confidence=0.95,
        family_situation_clarity=0.7,
        relocation_urgency=0.6,
        previous_interactions=5,
        conversion_funnel_stage=0.6,
        seasonal_patterns=0.8,
        market_conditions_score=0.7,
        communication_style_score=0.8,
        technical_sophistication=0.9,
        local_market_knowledge=0.6,
        data_completeness=0.9,
        recency_weight=0.95,
    )


class TestAdvancedMLLeadScoringEngine:
    """Test suite for the main ML scoring engine"""

    @pytest.fixture
    def engine(self):
        """Create engine instance for testing"""
        return AdvancedMLLeadScoringEngine()

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine.models is not None
        assert "conversion" in engine.models
        assert "engagement" in engine.models
        assert "intent" in engine.models
        assert engine.model_version == "v2.0.0"
        assert engine.prediction_count == 0
        assert engine.avg_latency_ms == 0.0

    @pytest.mark.asyncio
    async def test_comprehensive_lead_scoring_success(self, engine, sample_lead_data):
        """Test successful lead scoring with valid data"""
        result = await engine.score_lead_comprehensive("lead_123", sample_lead_data)

        # Validate result structure
        assert isinstance(result, MLScoringResult)
        assert result.lead_id == "lead_123"
        assert result.timestamp is not None

        # Validate scores are in valid range
        assert 0 <= result.conversion_probability <= 100
        assert 0 <= result.intent_strength <= 100
        assert 0 <= result.timing_urgency <= 100
        assert 0 <= result.financial_readiness <= 100
        assert 0 <= result.engagement_quality <= 100
        assert 0 <= result.final_ml_score <= 100

        # Validate confidence interval
        assert isinstance(result.confidence_interval, tuple)
        assert len(result.confidence_interval) == 2
        assert result.confidence_interval[0] <= result.confidence_interval[1]

        # Validate feature vector is populated
        assert isinstance(result.feature_vector, MLFeatureVector)

        # Validate insights are provided
        assert isinstance(result.recommended_actions, list)
        assert len(result.recommended_actions) > 0
        assert isinstance(result.expected_conversion_timeline, str)
        assert len(result.expected_conversion_timeline) > 0

    @pytest.mark.asyncio
    async def test_performance_requirement_sub_100ms(self, engine, sample_lead_data):
        """Test that scoring completes in <100ms as required"""
        start_time = time.time()
        result = await engine.score_lead_comprehensive("lead_123", sample_lead_data)
        execution_time_ms = (time.time() - start_time) * 1000

        # Performance requirement: <100ms
        assert execution_time_ms < 100, f"Scoring took {execution_time_ms:.1f}ms, requirement is <100ms"
        assert result.prediction_latency_ms < 100

    @pytest.mark.asyncio
    async def test_scoring_with_minimal_data(self, engine):
        """Test scoring works with minimal lead data"""
        minimal_data = {"id": "lead_minimal", "email": "test@example.com"}

        result = await engine.score_lead_comprehensive("lead_minimal", minimal_data)

        # Should still return valid result with fallback values
        assert isinstance(result, MLScoringResult)
        assert result.lead_id == "lead_minimal"
        assert 0 <= result.final_ml_score <= 100
        assert result.prediction_uncertainty > 0.5  # High uncertainty with minimal data

    @pytest.mark.asyncio
    async def test_error_handling_invalid_data(self, engine):
        """Test error handling with invalid/corrupted data"""
        invalid_data = {
            "id": "lead_invalid",
            "email": "invalid-email",
            "company_size": "not-a-number",
            "last_activity": "invalid-date",
        }

        # Should not raise exception, but return fallback result
        result = await engine.score_lead_comprehensive("lead_invalid", invalid_data)

        assert isinstance(result, MLScoringResult)
        assert result.lead_id == "lead_invalid"
        # Should have high uncertainty due to data quality issues
        assert result.prediction_uncertainty > 0.7

    @pytest.mark.asyncio
    async def test_caching_behavior(self, engine, sample_lead_data):
        """Test that results are properly cached"""
        with patch.object(engine.cache, "set") as mock_cache_set:
            await engine.score_lead_comprehensive("lead_cache", sample_lead_data)

            # Verify caching was attempted
            mock_cache_set.assert_called_once()
            cache_key = mock_cache_set.call_args[0][0]
            assert cache_key == "ml_score:lead_cache"
            assert mock_cache_set.call_args[1]["ttl"] == 1800  # 30 minutes

    @pytest.mark.asyncio
    async def test_fallback_on_all_model_failures(self, engine, sample_lead_data):
        """Test fallback behavior when all models fail"""
        # Mock all models to fail
        for model in engine.models.values():
            model.predict = AsyncMock(side_effect=Exception("Model failed"))

        result = await engine.score_lead_comprehensive("lead_fallback", sample_lead_data)

        # Should return fallback result, not raise exception
        assert isinstance(result, MLScoringResult)
        assert result.final_ml_score == 50.0  # Neutral fallback score
        assert result.prediction_uncertainty > 0.7  # High uncertainty
        assert "fallback" in result.expected_conversion_timeline.lower()

    @pytest.mark.asyncio
    async def test_feature_importance_calculation(self, engine, sample_lead_data):
        """Test feature importance calculation"""
        result = await engine.score_lead_comprehensive("lead_features", sample_lead_data)

        # Validate feature importance
        assert isinstance(result.top_features, list)
        assert len(result.top_features) > 0

        for feature in result.top_features:
            assert isinstance(feature, dict)
            # Should have feature name and importance score
            assert len(feature.keys()) >= 1
            for importance_score in feature.values():
                assert isinstance(importance_score, (int, float))
                assert importance_score >= 0

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, engine, sample_lead_data):
        """Test that performance metrics are tracked"""
        initial_count = engine.prediction_count
        initial_errors = engine.error_count

        await engine.score_lead_comprehensive("lead_metrics", sample_lead_data)

        assert engine.prediction_count == initial_count + 1
        assert engine.error_count == initial_errors  # No errors expected

    @pytest.mark.asyncio
    async def test_concurrent_scoring_requests(self, engine, sample_lead_data):
        """Test handling concurrent scoring requests"""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            lead_data = {**sample_lead_data, "id": f"lead_concurrent_{i}"}
            task = engine.score_lead_comprehensive(f"lead_concurrent_{i}", lead_data)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result.lead_id == f"lead_concurrent_{i}"
            assert isinstance(result, MLScoringResult)


class TestXGBoostConversionModel:
    """Test suite for XGBoost model component"""

    @pytest.fixture
    def model(self):
        """Create model instance for testing"""
        return XGBoostConversionModel()

    @pytest.mark.asyncio
    async def test_model_initialization(self, model):
        """Test model initializes correctly"""
        assert model.model is None
        assert model.scaler is not None
        assert model.feature_names is None
        assert not model.is_trained

    @pytest.mark.asyncio
    async def test_prediction_without_training(self, model, sample_feature_vector):
        """Test prediction falls back gracefully without trained model"""
        score, confidence = await model.predict(sample_feature_vector)

        # Should return fallback prediction
        assert isinstance(score, float)
        assert isinstance(confidence, float)
        assert 0 <= score <= 100
        assert 0 <= confidence <= 1

    @pytest.mark.asyncio
    async def test_feature_importance_calculation(self, model, sample_feature_vector):
        """Test feature importance calculation"""
        importance = await model.explain(sample_feature_vector)

        assert isinstance(importance, dict)
        assert len(importance) > 0

        # Check high-impact features are included
        assert "financial_readiness" in importance
        assert "timing_urgency_signals" in importance
        assert "budget_clarity_score" in importance

        # Importance values should be reasonable
        for feature, value in importance.items():
            assert isinstance(value, (int, float))
            assert value >= 0

    @pytest.mark.asyncio
    async def test_prediction_error_handling(self, model):
        """Test error handling with invalid feature data"""
        # Create invalid feature vector with None values
        invalid_features = MLFeatureVector(
            email_open_rate=None,
            email_click_rate=None,
            response_velocity=None,
            conversation_depth=None,
            engagement_consistency=None,
            property_view_frequency=None,
            search_refinement_count=None,
            price_range_stability=None,
            location_focus_score=None,
            timing_urgency_signals=None,
            budget_clarity_score=None,
            financing_readiness=None,
            price_sensitivity=None,
            affordability_ratio=None,
            question_sophistication=None,
            decision_maker_confidence=None,
            family_situation_clarity=None,
            relocation_urgency=None,
            previous_interactions=None,
            conversion_funnel_stage=None,
            seasonal_patterns=None,
            market_conditions_score=None,
            communication_style_score=None,
            technical_sophistication=None,
            local_market_knowledge=None,
            data_completeness=None,
            recency_weight=None,
        )

        # Should not raise exception
        score, confidence = await model.predict(invalid_features)
        assert isinstance(score, float)
        assert isinstance(confidence, float)


class TestMLScoringIntegration:
    """Integration tests for ML scoring with other services"""

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates engine correctly"""
        engine = await create_advanced_ml_scoring_engine()

        assert isinstance(engine, AdvancedMLLeadScoringEngine)
        assert engine.models is not None
        assert engine.cache is not None

    @pytest.mark.asyncio
    async def test_cache_service_integration(self):
        """Test integration with cache service"""
        from ghl_real_estate_ai.services.cache_service import CacheService

        engine = AdvancedMLLeadScoringEngine()
        assert isinstance(engine.cache, CacheService)

    @pytest.mark.asyncio
    async def test_memory_service_integration(self, sample_lead_data):
        """Test integration with memory service for historical data"""
        engine = AdvancedMLLeadScoringEngine()

        # Mock memory service
        with patch("ghl_real_estate_ai.services.memory_service.MemoryService") as mock_memory:
            mock_memory.return_value.get_lead_history.return_value = []

            result = await engine.score_lead_comprehensive("lead_memory", sample_lead_data)
            assert isinstance(result, MLScoringResult)


class TestMLScoringPerformance:
    """Performance and load tests"""

    @pytest.mark.asyncio
    async def test_high_volume_scoring(self):
        """Test scoring under high volume (load test)"""
        engine = AdvancedMLLeadScoringEngine()

        # Generate 100 scoring requests
        tasks = []
        for i in range(100):
            lead_data = {"id": f"lead_load_{i}", "email": f"user{i}@test.com", "company_size": 100, "source": "website"}
            task = engine.score_lead_comprehensive(f"lead_load_{i}", lead_data)
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Check for any exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Found {len(exceptions)} exceptions during load test"

        # Performance check: should complete 100 requests in reasonable time
        assert total_time < 10.0, f"Load test took {total_time:.2f}s, should be <10s"

        # Average latency check
        avg_latency = total_time / 100 * 1000  # Convert to ms
        assert avg_latency < 100, f"Average latency {avg_latency:.1f}ms exceeds 100ms requirement"

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, sample_lead_data):
        """Test memory usage doesn't grow excessively"""
        import os

        import psutil

        engine = AdvancedMLLeadScoringEngine()
        process = psutil.Process(os.getpid())

        initial_memory = process.memory_info().rss

        # Run 50 scoring operations
        for i in range(50):
            lead_data = {**sample_lead_data, "id": f"lead_mem_{i}"}
            await engine.score_lead_comprehensive(f"lead_mem_{i}", lead_data)

        final_memory = process.memory_info().rss
        memory_growth_mb = (final_memory - initial_memory) / 1024 / 1024

        # Memory growth should be reasonable (<50MB for 50 operations)
        assert memory_growth_mb < 50, f"Memory grew by {memory_growth_mb:.1f}MB, should be <50MB"


# Additional edge case tests
class TestMLScoringEdgeCases:
    """Edge case and robustness tests"""

    @pytest.mark.asyncio
    async def test_empty_lead_data(self):
        """Test scoring with completely empty lead data"""
        engine = AdvancedMLLeadScoringEngine()

        result = await engine.score_lead_comprehensive("lead_empty", {})

        assert isinstance(result, MLScoringResult)
        assert result.lead_id == "lead_empty"
        assert result.prediction_uncertainty > 0.8  # Very high uncertainty

    @pytest.mark.asyncio
    async def test_extremely_large_values(self):
        """Test handling of extremely large values"""
        engine = AdvancedMLLeadScoringEngine()

        large_data = {
            "id": "lead_large",
            "company_size": 999999999,
            "company_revenue": 999999999999,
            "custom_fields": {"pageViews": 999999, "timeOnSite": 999999},
        }

        result = await engine.score_lead_comprehensive("lead_large", large_data)

        # Should handle gracefully without overflow
        assert isinstance(result, MLScoringResult)
        assert 0 <= result.final_ml_score <= 100

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters in data"""
        engine = AdvancedMLLeadScoringEngine()

        unicode_data = {
            "id": "lead_unicode",
            "first_name": "José",
            "last_name": "García-López",
            "email": "josé@münchen-tech.de",
            "company": "Münchën Tech GmbH & Co. KG",
        }

        result = await engine.score_lead_comprehensive("lead_unicode", unicode_data)

        assert isinstance(result, MLScoringResult)
        assert result.lead_id == "lead_unicode"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
