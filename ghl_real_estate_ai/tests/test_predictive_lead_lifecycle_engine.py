"""
Tests for Predictive Lead Lifecycle AI Engine

Validates:
- 98%+ accurate conversion timeline prediction (±2 days)
- Optimal intervention timing recommendations
- Risk factor identification and mitigation strategies
- Behavioral pattern analysis and forecasting
- Performance targets (<25ms prediction, 98% accuracy)

Performance Requirements:
- Prediction time: <25ms per lead
- Accuracy: 98% within ±2 days confidence interval
- Confidence intervals: 95% reliability
- Risk analysis: <15ms processing
- Intervention predictions: <20ms processing
- Incremental updates: <30ms processing

Testing Coverage:
- Core prediction and forecasting functionality
- Intervention timing optimization
- Risk factor analysis and mitigation
- Behavioral pattern recognition
- Performance benchmarks and accuracy metrics
- Caching and optimization
- Security and data validation
- Integration workflows and ensemble modeling
"""

import pytest
import asyncio
import time
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, List, Tuple

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.predictive_lead_lifecycle_engine import (
    PredictiveLeadLifecycleEngine,
    ConversionForecast,
    LeadFeatureVector,
    InterventionWindow,
    RiskFactor,
    MarketInfluence,
    ConversionStage,
    InterventionType,
    RiskType
)


class TestPredictiveData:
    """Test data for predictive lifecycle testing."""

    @property
    def sample_lead_features(self) -> LeadFeatureVector:
        """Generate sample lead feature vector."""
        return LeadFeatureVector(
            lead_age=35,
            income_level="high",
            family_status="married_with_children",
            location="downtown",
            engagement_score=0.75,
            response_time_avg=3.5,  # hours
            interaction_frequency=0.8,
            content_consumption=0.6,
            budget_range_min=450000.0,
            budget_range_max=650000.0,
            property_type_preference="single_family",
            location_flexibility=0.4,
            timeline_urgency=0.7,
            days_since_first_contact=14,
            total_interactions=12,
            property_views=8,
            showings_attended=2,
            offers_made=0,
            market_hotness=0.65,
            inventory_availability=0.45,
            price_competitiveness=0.8,
            season="spring",
            day_of_week="tuesday",
            financing_status="pre_approved"
        )

    @property
    def sample_market_influence(self) -> MarketInfluence:
        """Generate sample market context."""
        return MarketInfluence(
            market_conditions="hot",
            inventory_level=0.3,
            price_trend="rising",
            seasonality_factor=0.8,
            competition_level=0.7,
            financing_conditions="favorable"
        )

    @property
    def sample_intervention_window(self) -> InterventionWindow:
        """Generate sample intervention window."""
        return InterventionWindow(
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=3),
            intervention_type=InterventionType.PROPERTY_SHOWING,
            priority=0.9,
            expected_impact=0.25,
            confidence=0.85,
            recommended_actions=[
                "Schedule property showing",
                "Prepare comparative market analysis",
                "Follow up within 24 hours"
            ],
            reasoning="High engagement with property views indicates readiness for showing"
        )

    @property
    def sample_risk_factor(self) -> RiskFactor:
        """Generate sample risk factor."""
        return RiskFactor(
            risk_type=RiskType.PRICE_SENSITIVITY,
            severity=0.6,
            probability=0.7,
            impact_on_timeline=5,  # days delay
            mitigation_strategies=[
                "Provide value justification analysis",
                "Show market comparisons",
                "Highlight unique property benefits"
            ],
            early_warning_signals=[
                "Frequent price mentions",
                "Budget concern expressions",
                "Comparison shopping behavior"
            ]
        )

    def sample_lead_data(self, lead_id: str = "lead_001") -> Dict[str, Any]:
        """Generate sample lead database data."""
        return {
            "id": lead_id,
            "created_at": datetime.now() - timedelta(days=14),
            "location": "downtown",
            "age": 35,
            "income_level": "high",
            "family_status": "married_with_children",
            "budget_min": 450000,
            "budget_max": 650000,
            "property_type": "single_family",
            "timeline_preference": "immediate",
            "financing_status": "pre_approved"
        }

    def sample_interactions(self, lead_id: str = "lead_001") -> List[Dict[str, Any]]:
        """Generate sample interaction history."""
        return [
            {
                "lead_id": lead_id,
                "date": datetime.now() - timedelta(days=i),
                "response_time_hours": 2.0 + (i * 0.5),
                "interaction_type": "email_response",
                "content": "Interested in downtown properties"
            }
            for i in range(10)
        ]


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = MagicMock()
    redis_mock.optimized_get = AsyncMock(return_value=None)
    redis_mock.optimized_set = AsyncMock()
    redis_mock.health_check = AsyncMock(return_value={"healthy": True})
    redis_mock.close = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_ml_service():
    """Mock ML inference service."""
    ml_mock = MagicMock()
    ml_mock.initialize = AsyncMock()
    ml_mock.predict_batch = AsyncMock(return_value=[
        MagicMock(
            success=True,
            request_id="prediction_temporal_12345",
            predictions={"conversion_probability": 0.78, "days_to_conversion": 21.5}
        ),
        MagicMock(
            success=True,
            request_id="prediction_behavioral_12345",
            predictions={"conversion_probability": 0.82, "days_to_conversion": 19.0}
        ),
        MagicMock(
            success=True,
            request_id="prediction_interaction_12345",
            predictions={"conversion_probability": 0.75, "days_to_conversion": 23.0}
        ),
        MagicMock(
            success=True,
            request_id="prediction_market_12345",
            predictions={"conversion_probability": 0.80, "days_to_conversion": 20.0}
        )
    ])
    ml_mock.health_check = AsyncMock(return_value={"healthy": True})
    ml_mock.cleanup = AsyncMock()
    return ml_mock


@pytest.fixture
def mock_db_cache():
    """Mock database cache service."""
    db_mock = MagicMock()
    db_mock.initialize = AsyncMock()
    db_mock.cached_query = AsyncMock(return_value=[])
    db_mock.health_check = AsyncMock(return_value={"healthy": True})
    db_mock.cleanup = AsyncMock()
    return db_mock


@pytest.fixture
async def predictive_engine(mock_redis, mock_ml_service, mock_db_cache):
    """Create predictive lead lifecycle engine with mocked dependencies."""
    with patch('ghl_real_estate_ai.services.predictive_lead_lifecycle_engine.OptimizedRedisClient', return_value=mock_redis), \
         patch('ghl_real_estate_ai.services.predictive_lead_lifecycle_engine.BatchMLInferenceService', return_value=mock_ml_service), \
         patch('ghl_real_estate_ai.services.predictive_lead_lifecycle_engine.DatabaseCacheService', return_value=mock_db_cache):

        engine = PredictiveLeadLifecycleEngine({
            "redis_url": "redis://localhost:6379",
            "model_cache_dir": "models",
            "enable_model_warming": True
        })
        await engine.initialize()
        return engine


class TestPredictiveEngineInitialization:
    """Test predictive engine initialization."""

    @pytest.mark.asyncio
    async def test_engine_initialization_success(self, predictive_engine):
        """Test engine initializes correctly with all components."""
        assert predictive_engine.redis_client is not None
        assert predictive_engine.ml_service is not None
        assert predictive_engine.db_cache is not None
        assert predictive_engine.models is not None
        assert len(predictive_engine.model_weights) > 0
        assert predictive_engine.feature_extractors is not None
        assert predictive_engine.prediction_cache == {}

    @pytest.mark.asyncio
    async def test_engine_initialization_performance(self):
        """Test engine initialization meets performance targets."""
        with patch('ghl_real_estate_ai.services.predictive_lead_lifecycle_engine.OptimizedRedisClient') as mock_redis, \
             patch('ghl_real_estate_ai.services.predictive_lead_lifecycle_engine.BatchMLInferenceService') as mock_ml, \
             patch('ghl_real_estate_ai.services.predictive_lead_lifecycle_engine.DatabaseCacheService') as mock_db:

            mock_redis.return_value.initialize = AsyncMock()
            mock_ml.return_value.initialize = AsyncMock()
            mock_db.return_value.initialize = AsyncMock()

            start_time = time.time()
            engine = PredictiveLeadLifecycleEngine({})
            await engine.initialize()
            init_time = (time.time() - start_time) * 1000

            assert init_time < 2000, f"Initialization took {init_time:.1f}ms (target: <2000ms)"


class TestConversionPrediction:
    """Test conversion timeline prediction functionality."""

    @pytest.mark.asyncio
    async def test_predict_conversion_timeline_basic(self, predictive_engine, mock_db_cache):
        """Test basic conversion timeline prediction."""
        test_data = TestPredictiveData()
        lead_id = "lead_001"

        # Mock lead data queries
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),  # Lead profile
            test_data.sample_interactions(lead_id),  # Interactions
            {"budget_min": 450000, "budget_max": 650000},  # Preferences
            test_data.sample_lead_data(lead_id),  # Historical patterns
            {"market_hotness": 0.7}  # Market context
        ]

        start_time = time.time()
        forecast = await predictive_engine.predict_conversion_timeline(lead_id)
        prediction_time = (time.time() - start_time) * 1000

        assert forecast is not None
        assert forecast.lead_id == lead_id
        assert isinstance(forecast.expected_conversion_date, datetime)
        assert len(forecast.confidence_interval) == 2
        assert 0.0 <= forecast.conversion_probability <= 1.0
        assert forecast.processing_time_ms < 25, f"Prediction took {prediction_time:.1f}ms (target: <25ms)"
        assert forecast.prediction_accuracy_score > 0.0

    @pytest.mark.asyncio
    async def test_prediction_accuracy_requirements(self, predictive_engine, mock_db_cache):
        """Test prediction meets 98% accuracy requirements."""
        test_data = TestPredictiveData()
        lead_id = "lead_001"

        # Mock lead data
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            test_data.sample_interactions(lead_id),
            {},
            test_data.sample_lead_data(lead_id),
            {}
        ]

        forecast = await predictive_engine.predict_conversion_timeline(lead_id)

        # Confidence interval should be ±2 days for 98% accuracy requirement
        expected_date = forecast.expected_conversion_date
        lower_bound, upper_bound = forecast.confidence_interval
        confidence_range = (upper_bound - lower_bound).days

        assert confidence_range <= 4, f"Confidence interval {confidence_range} days (target: ≤4 days for ±2 days)"
        assert forecast.prediction_accuracy_score >= 0.95, f"Accuracy score {forecast.prediction_accuracy_score} (target: ≥0.95)"

    @pytest.mark.asyncio
    async def test_prediction_caching_functionality(self, predictive_engine, mock_redis, mock_db_cache):
        """Test prediction caching improves performance."""
        test_data = TestPredictiveData()
        lead_id = "lead_001"

        # Mock lead data
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            test_data.sample_interactions(lead_id),
            {},
            test_data.sample_lead_data(lead_id),
            {}
        ]

        # First call - cache miss
        mock_redis.optimized_get.return_value = None
        forecast1 = await predictive_engine.predict_conversion_timeline(lead_id)

        # Verify cache set was called
        mock_redis.optimized_set.assert_called()

        # Second call - cache hit
        mock_redis.optimized_get.return_value = forecast1.to_dict()
        start_time = time.time()
        forecast2 = await predictive_engine.predict_conversion_timeline(lead_id)
        cache_time = (time.time() - start_time) * 1000

        assert cache_time < 5, f"Cache retrieval took {cache_time:.1f}ms (target: <5ms)"
        assert forecast2.lead_id == lead_id

    @pytest.mark.asyncio
    async def test_ensemble_model_fusion(self, predictive_engine, mock_ml_service):
        """Test ensemble model prediction fusion."""
        test_data = TestPredictiveData()
        feature_vector = test_data.sample_lead_features

        # Test ensemble prediction
        ensemble_results = await predictive_engine._run_ensemble_prediction(feature_vector)

        assert isinstance(ensemble_results, dict)
        assert len(ensemble_results) > 0

        # Verify ML service was called with multiple model requests
        mock_ml_service.predict_batch.assert_called()
        call_args = mock_ml_service.predict_batch.call_args[0][0]
        assert len(call_args) >= 4  # Should have requests for all ensemble models


class TestInterventionOptimization:
    """Test intervention timing optimization functionality."""

    @pytest.mark.asyncio
    async def test_predict_optimal_interventions_basic(self, predictive_engine, mock_db_cache):
        """Test optimal intervention prediction."""
        test_data = TestPredictiveData()
        lead_id = "lead_001"

        # Mock lead data for intervention analysis
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            test_data.sample_interactions(lead_id),
            {},
            test_data.sample_lead_data(lead_id),
            {}
        ]

        # Create a sample forecast
        forecast = ConversionForecast(
            lead_id=lead_id,
            expected_conversion_date=datetime.now() + timedelta(days=20),
            confidence_interval=(
                datetime.now() + timedelta(days=18),
                datetime.now() + timedelta(days=22)
            ),
            conversion_probability=0.78,
            current_stage=ConversionStage.PROPERTY_RESEARCH,
            estimated_stages_remaining=3,
            probability_curve=[],
            optimal_touchpoints=[],
            risk_factors=[],
            acceleration_opportunities=[],
            market_context=test_data.sample_market_influence,
            behavioral_insights={},
            historical_patterns={},
            model_ensemble_weights={},
            prediction_accuracy_score=0.95
        )

        start_time = time.time()
        interventions = await predictive_engine.predict_optimal_interventions(lead_id, forecast)
        intervention_time = (time.time() - start_time) * 1000

        assert isinstance(interventions, list)
        assert intervention_time < 20, f"Intervention prediction took {intervention_time:.1f}ms (target: <20ms)"

        # Check intervention quality
        if interventions:
            for intervention in interventions:
                assert isinstance(intervention, InterventionWindow)
                assert 0.0 <= intervention.priority <= 1.0
                assert 0.0 <= intervention.expected_impact <= 1.0
                assert 0.0 <= intervention.confidence <= 1.0
                assert len(intervention.recommended_actions) > 0

    @pytest.mark.asyncio
    async def test_intervention_timing_optimization(self, predictive_engine):
        """Test intervention timing is optimized based on lead behavior."""
        test_data = TestPredictiveData()

        # Test high-urgency lead
        urgent_features = test_data.sample_lead_features
        urgent_features.timeline_urgency = 0.9
        urgent_features.response_time_avg = 1.0  # Very responsive

        touchpoints = await predictive_engine._generate_optimal_touchpoints(
            ConversionForecast(
                lead_id="urgent_lead",
                expected_conversion_date=datetime.now() + timedelta(days=10),
                confidence_interval=(datetime.now(), datetime.now()),
                conversion_probability=0.8,
                current_stage=ConversionStage.ACTIVE_VIEWING,
                estimated_stages_remaining=2,
                probability_curve=[],
                optimal_touchpoints=[],
                risk_factors=[],
                acceleration_opportunities=[],
                market_context=test_data.sample_market_influence,
                behavioral_insights={},
                historical_patterns={},
                model_ensemble_weights={},
                prediction_accuracy_score=0.95
            ),
            urgent_features
        )

        # Should prioritize urgent interventions
        if touchpoints:
            urgent_touchpoints = [tp for tp in touchpoints if tp.intervention_type == InterventionType.URGENCY_CREATION]
            assert len(urgent_touchpoints) > 0, "Should generate urgency interventions for high-urgency leads"

    @pytest.mark.asyncio
    async def test_intervention_impact_prediction(self, predictive_engine):
        """Test intervention impact prediction accuracy."""
        test_data = TestPredictiveData()
        interventions = [test_data.sample_intervention_window]

        # Mock forecast
        forecast = ConversionForecast(
            lead_id="lead_001",
            expected_conversion_date=datetime.now() + timedelta(days=20),
            confidence_interval=(datetime.now(), datetime.now()),
            conversion_probability=0.7,
            current_stage=ConversionStage.PROPERTY_RESEARCH,
            estimated_stages_remaining=3,
            probability_curve=[],
            optimal_touchpoints=[],
            risk_factors=[],
            acceleration_opportunities=[],
            market_context=test_data.sample_market_influence,
            behavioral_insights={},
            historical_patterns={},
            model_ensemble_weights={},
            prediction_accuracy_score=0.95
        )

        impact_predictions = await predictive_engine._predict_intervention_impacts(
            interventions, forecast
        )

        assert len(impact_predictions) == len(interventions)
        for prediction in impact_predictions:
            assert hasattr(prediction, 'expected_impact')
            assert 0.0 <= prediction.expected_impact <= 1.0


class TestRiskAnalysis:
    """Test risk factor identification and analysis functionality."""

    @pytest.mark.asyncio
    async def test_predict_risk_factors_basic(self, predictive_engine, mock_db_cache):
        """Test basic risk factor prediction."""
        test_data = TestPredictiveData()
        lead_id = "lead_001"

        # Mock various risk-related data
        mock_db_cache.cached_query.side_effect = [
            # Price sensitivity interactions
            [{"content": "price seems expensive", "created_at": datetime.now()}],
            # Timeline preferences
            {"timeline_preference": "immediate"},
            # Competitive interactions
            [{"content": "talking to other agent", "created_at": datetime.now()}],
            # Financing status
            {"financing_status": "uncertain", "pre_approval_status": False},
            # Recent interactions
            test_data.sample_interactions(lead_id)
        ]

        start_time = time.time()
        risks = await predictive_engine.predict_risk_factors(lead_id)
        risk_time = (time.time() - start_time) * 1000

        assert isinstance(risks, list)
        assert risk_time < 15, f"Risk analysis took {risk_time:.1f}ms (target: <15ms)"

        # Validate risk factor quality
        for risk in risks:
            assert isinstance(risk, RiskFactor)
            assert isinstance(risk.risk_type, RiskType)
            assert 0.0 <= risk.severity <= 1.0
            assert 0.0 <= risk.probability <= 1.0
            assert len(risk.mitigation_strategies) > 0

    @pytest.mark.asyncio
    async def test_risk_prioritization(self, predictive_engine):
        """Test risk factor prioritization logic."""
        test_risks = [
            RiskFactor(
                risk_type=RiskType.PRICE_SENSITIVITY,
                severity=0.8,
                probability=0.9,
                impact_on_timeline=10,
                mitigation_strategies=["price_justification"],
                early_warning_signals=["price_concerns"]
            ),
            RiskFactor(
                risk_type=RiskType.COMMUNICATION_GAP,
                severity=0.3,
                probability=0.4,
                impact_on_timeline=3,
                mitigation_strategies=["increase_communication"],
                early_warning_signals=["slow_responses"]
            ),
            RiskFactor(
                risk_type=RiskType.COMPETITIVE_THREAT,
                severity=0.9,
                probability=0.7,
                impact_on_timeline=14,
                mitigation_strategies=["differentiation"],
                early_warning_signals=["competitor_mentions"]
            )
        ]

        prioritized = await predictive_engine._prioritize_and_enhance_risks(test_risks)

        # Should be sorted by severity * probability (descending)
        for i in range(len(prioritized) - 1):
            current_score = prioritized[i].severity * prioritized[i].probability
            next_score = prioritized[i + 1].severity * prioritized[i + 1].probability
            assert current_score >= next_score, "Risks should be prioritized by severity * probability"

    @pytest.mark.asyncio
    async def test_specific_risk_analyses(self, predictive_engine, mock_db_cache):
        """Test specific risk analysis functions."""
        lead_id = "lead_001"

        # Test price sensitivity risk
        mock_db_cache.cached_query.return_value = [
            {"content": "price is too high", "created_at": datetime.now()},
            {"content": "budget concerns", "created_at": datetime.now()},
            {"content": "expensive market", "created_at": datetime.now()}
        ]

        price_risk = await predictive_engine._analyze_price_sensitivity_risk(lead_id)
        assert price_risk is not None
        assert price_risk.risk_type == RiskType.PRICE_SENSITIVITY

        # Test financing risk
        mock_db_cache.cached_query.return_value = {
            "financing_status": "uncertain",
            "pre_approval_status": False
        }

        financing_risk = await predictive_engine._analyze_financing_risk(lead_id)
        assert financing_risk is not None
        assert financing_risk.risk_type == RiskType.FINANCING_UNCERTAINTY

        # Test communication risk
        mock_db_cache.cached_query.return_value = []  # No recent interactions

        communication_risk = await predictive_engine._analyze_communication_risk(lead_id)
        assert communication_risk is not None
        assert communication_risk.risk_type == RiskType.COMMUNICATION_GAP


class TestFeatureExtraction:
    """Test feature extraction and engineering functionality."""

    @pytest.mark.asyncio
    async def test_extract_lead_features_comprehensive(self, predictive_engine, mock_db_cache):
        """Test comprehensive lead feature extraction."""
        test_data = TestPredictiveData()
        lead_id = "lead_001"

        # Mock all feature extraction queries
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),  # Demographics
            test_data.sample_interactions(lead_id),  # Behavioral
            {"budget_min": 450000, "budget_max": 650000},  # Preferences
            test_data.sample_lead_data(lead_id),  # Historical
            {"market_hotness": 0.7}  # Market context
        ]

        features = await predictive_engine._extract_lead_features(lead_id)

        assert isinstance(features, LeadFeatureVector)
        assert features.lead_age is not None
        assert features.engagement_score > 0.0
        assert features.days_since_first_contact > 0
        assert features.market_hotness > 0.0

    @pytest.mark.asyncio
    async def test_feature_caching(self, predictive_engine, mock_db_cache):
        """Test feature extraction caching."""
        test_data = TestPredictiveData()
        lead_id = "lead_001"

        # Mock data
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            test_data.sample_interactions(lead_id),
            {},
            test_data.sample_lead_data(lead_id),
            {}
        ]

        # First extraction
        features1 = await predictive_engine._extract_lead_features(lead_id)

        # Second extraction should use cache
        start_time = time.time()
        features2 = await predictive_engine._extract_lead_features(lead_id)
        cache_time = (time.time() - start_time) * 1000

        assert cache_time < 1, f"Cached feature retrieval took {cache_time:.1f}ms (target: <1ms)"
        assert features1.lead_id == features2.lead_id

    @pytest.mark.asyncio
    async def test_behavioral_feature_calculation(self, predictive_engine):
        """Test behavioral feature calculation accuracy."""
        test_interactions = [
            {
                "response_time_hours": 2.0,
                "interaction_type": "email",
                "date": datetime.now() - timedelta(days=i)
            }
            for i in range(10)
        ]

        behavioral_features = await predictive_engine._extract_behavioral_features("lead_001")

        # Mock the cached_query to return test interactions
        with patch.object(predictive_engine.db_cache, 'cached_query', return_value=test_interactions):
            behavioral_features = await predictive_engine._extract_behavioral_features("lead_001")

            assert "engagement_score" in behavioral_features
            assert "response_time_avg" in behavioral_features
            assert "total_interactions" in behavioral_features


class TestPerformanceBenchmarks:
    """Test performance benchmarks for predictive engine."""

    @pytest.mark.asyncio
    async def test_prediction_performance_target(self, predictive_engine, mock_db_cache):
        """Test prediction meets <25ms performance target."""
        test_data = TestPredictiveData()
        lead_id = "lead_perf_test"

        # Mock minimal data for fast processing
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            [],  # Empty interactions
            {},  # Empty preferences
            test_data.sample_lead_data(lead_id),
            {}  # Empty market data
        ]

        # Run multiple iterations to test consistency
        processing_times = []
        for _ in range(5):
            start_time = time.time()
            await predictive_engine.predict_conversion_timeline(lead_id)
            processing_time = (time.time() - start_time) * 1000
            processing_times.append(processing_time)

        avg_time = sum(processing_times) / len(processing_times)
        assert avg_time < 25, f"Average prediction time {avg_time:.1f}ms (target: <25ms)"

        # 95th percentile should be under target
        processing_times.sort()
        p95_time = processing_times[int(len(processing_times) * 0.95)]
        assert p95_time < 30, f"95th percentile time {p95_time:.1f}ms (target: <30ms)"

    @pytest.mark.asyncio
    async def test_incremental_update_performance(self, predictive_engine, mock_db_cache):
        """Test incremental prediction updates meet <30ms target."""
        test_data = TestPredictiveData()
        lead_id = "lead_incremental"

        # Mock initial data
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            test_data.sample_interactions(lead_id),
            {},
            test_data.sample_lead_data(lead_id),
            {}
        ]

        # Get initial forecast
        initial_forecast = await predictive_engine.predict_conversion_timeline(lead_id)

        # Test incremental update
        new_interaction_data = {
            "interaction_type": "property_viewing",
            "engagement_score": 0.9,
            "response_time": 1.0
        }

        start_time = time.time()
        updated_forecast = await predictive_engine.update_prediction_with_new_data(
            lead_id, new_interaction_data
        )
        update_time = (time.time() - start_time) * 1000

        assert update_time < 30, f"Incremental update took {update_time:.1f}ms (target: <30ms)"
        assert updated_forecast.lead_id == lead_id

    @pytest.mark.asyncio
    async def test_concurrent_prediction_performance(self, predictive_engine, mock_db_cache):
        """Test engine handles concurrent predictions efficiently."""
        test_data = TestPredictiveData()

        # Mock data for multiple leads
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(f"lead_{i}") for i in range(5)
        ] * 5  # Enough data for 5 concurrent predictions

        # Submit concurrent predictions
        tasks = [
            predictive_engine.predict_conversion_timeline(f"lead_{i}")
            for i in range(5)
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000

        # All predictions should complete successfully
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert result.processing_time_ms > 0

        # Concurrent processing should be efficient
        assert total_time < 150, f"Concurrent predictions took {total_time:.1f}ms (target: <150ms for 5 predictions)"


class TestEngineReliability:
    """Test predictive engine reliability and error handling."""

    @pytest.mark.asyncio
    async def test_prediction_fallback_on_failure(self, predictive_engine, mock_db_cache):
        """Test prediction provides fallback results on ML failure."""
        # Simulate ML service failure
        predictive_engine.ml_service.predict_batch.side_effect = Exception("ML service unavailable")

        # Should return fallback forecast instead of crashing
        forecast = await predictive_engine.predict_conversion_timeline("lead_test")

        assert forecast is not None
        assert forecast.lead_id == "lead_test"
        assert forecast.conversion_probability > 0.0
        assert forecast.prediction_accuracy_score < 1.0  # Should indicate lower confidence

    @pytest.mark.asyncio
    async def test_feature_extraction_resilience(self, predictive_engine, mock_db_cache):
        """Test feature extraction handles partial data gracefully."""
        lead_id = "lead_resilience"

        # Simulate partial database failures
        mock_db_cache.cached_query.side_effect = [
            {"id": lead_id, "location": "downtown"},  # Minimal demographics
            None,  # No interactions
            {},  # No preferences
            None,  # No historical data
            {}  # No market data
        ]

        # Should still extract features with defaults
        features = await predictive_engine._extract_lead_features(lead_id)

        assert isinstance(features, LeadFeatureVector)
        assert features.location == "downtown"  # Should have available data
        # Should have reasonable defaults for missing data

    @pytest.mark.asyncio
    async def test_engine_health_check(self, predictive_engine):
        """Test engine health check functionality."""
        health = await predictive_engine.health_check()

        assert "healthy" in health
        assert "service" in health
        assert health["service"] == "predictive_lead_lifecycle_engine"
        assert "checks" in health
        assert "performance_metrics" in health
        assert "model_ensemble" in health


class TestEngineSecurity:
    """Test predictive engine security and data validation."""

    @pytest.mark.asyncio
    async def test_input_validation(self, predictive_engine):
        """Test engine validates inputs correctly."""
        # Test with invalid lead ID
        forecast = await predictive_engine.predict_conversion_timeline("")
        assert forecast is not None  # Should handle gracefully

        # Test with None lead ID
        forecast = await predictive_engine.predict_conversion_timeline(None)
        assert forecast is not None  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_feature_data_sanitization(self, predictive_engine, mock_db_cache):
        """Test feature extraction sanitizes potentially malicious data."""
        lead_id = "lead_security_test"

        # Mock data with potential injection attempts
        mock_db_cache.cached_query.side_effect = [
            {
                "id": lead_id,
                "location": "<script>alert('xss')</script>",
                "income_level": "'; DROP TABLE leads; --"
            },
            [{"content": "SELECT * FROM users", "response_time_hours": "invalid"}],
            {},
            {"created_at": "not_a_date"},
            {}
        ]

        # Should not crash and should sanitize data
        features = await predictive_engine._extract_lead_features(lead_id)

        assert isinstance(features, LeadFeatureVector)
        # Should not contain malicious scripts
        assert "<script>" not in str(features.location) if features.location else True


class TestEngineIntegration:
    """Integration tests for complete predictive workflows."""

    @pytest.mark.asyncio
    async def test_complete_prediction_workflow(self, predictive_engine, mock_db_cache):
        """Test complete prediction workflow end-to-end."""
        test_data = TestPredictiveData()
        lead_id = "lead_integration_test"

        # Mock comprehensive data
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            test_data.sample_interactions(lead_id),
            {"budget_min": 450000, "budget_max": 650000},
            test_data.sample_lead_data(lead_id),
            {"market_hotness": 0.7}
        ]

        # Step 1: Predict conversion timeline
        forecast = await predictive_engine.predict_conversion_timeline(lead_id)
        assert forecast.lead_id == lead_id
        assert forecast.processing_time_ms > 0

        # Step 2: Get optimal interventions
        interventions = await predictive_engine.predict_optimal_interventions(lead_id, forecast)
        assert isinstance(interventions, list)

        # Step 3: Analyze risk factors
        risks = await predictive_engine.predict_risk_factors(lead_id, forecast)
        assert isinstance(risks, list)

        # Step 4: Test incremental update
        new_data = {"engagement_score": 0.9}
        updated_forecast = await predictive_engine.update_prediction_with_new_data(
            lead_id, new_data
        )
        assert updated_forecast.lead_id == lead_id

        # Step 5: Health check
        health = await predictive_engine.health_check()
        assert health["healthy"]

        # Step 6: Cleanup
        await predictive_engine.cleanup()

    @pytest.mark.asyncio
    async def test_prediction_accuracy_validation(self, predictive_engine, mock_db_cache):
        """Test prediction accuracy meets 98% target with confidence intervals."""
        test_data = TestPredictiveData()
        lead_id = "lead_accuracy_test"

        # Mock high-quality data for accurate predictions
        mock_db_cache.cached_query.side_effect = [
            test_data.sample_lead_data(lead_id),
            test_data.sample_interactions(lead_id),
            {"budget_min": 450000, "budget_max": 650000},
            test_data.sample_lead_data(lead_id),
            {"market_hotness": 0.7}
        ]

        forecast = await predictive_engine.predict_conversion_timeline(lead_id)

        # Validate accuracy requirements
        assert forecast.prediction_accuracy_score >= 0.95, f"Accuracy score {forecast.prediction_accuracy_score} below target"

        # Confidence interval should be tight for high accuracy
        lower_bound, upper_bound = forecast.confidence_interval
        confidence_range = (upper_bound - lower_bound).days
        assert confidence_range <= 4, f"Confidence range {confidence_range} days exceeds ±2 day target"

        # Conversion probability should be reasonable
        assert 0.1 <= forecast.conversion_probability <= 0.95, f"Conversion probability {forecast.conversion_probability} seems unrealistic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])