"""
Test suite for Market Prediction Engine - Advanced ML-powered market analytics
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from ghl_real_estate_ai.services.market_prediction_engine import (
    MarketPredictionEngine,
    MarketDataPoint,
    PredictionResult,
    MarketOpportunity,
    PredictionType,
    MarketConfidence,
    TimeHorizon,
    get_market_prediction_engine
)


@pytest.fixture
def prediction_engine():
    """Create prediction engine instance for testing"""
    return MarketPredictionEngine()


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return MarketDataPoint(
        date=datetime.now() - timedelta(days=30),
        neighborhood="etiwanda",
        median_price=725000,
        days_on_market=22,
        inventory_months=2.3,
        price_per_sqft=385,
        interest_rate=5.5,
        employment_rate=0.94,
        population_growth=0.025,
        new_construction=150,
        month=datetime.now().month,
        quarter=((datetime.now().month - 1) // 3) + 1,
        is_spring_market=datetime.now().month in [3, 4, 5],
        is_holiday_season=datetime.now().month in [11, 12],
        gas_prices=4.2,
        mortgage_applications=12000,
        consumer_confidence=98.5
    )


@pytest.fixture
def sample_prediction_result():
    """Sample prediction result for testing"""
    return PredictionResult(
        prediction_id="pred-123",
        prediction_type=PredictionType.PRICE_APPRECIATION,
        target="etiwanda",
        time_horizon=TimeHorizon.MEDIUM_TERM,
        predicted_value=756000,
        current_value=725000,
        change_percentage=4.3,
        confidence_level=MarketConfidence.HIGH,
        confidence_score=0.85,
        key_factors=["Strong employment growth", "Limited inventory"],
        risk_factors=["Interest rate sensitivity"],
        opportunities=["Investment potential", "Timing advantage"],
        prediction_date=datetime.now(),
        target_date=datetime.now() + timedelta(days=365),
        update_frequency="weekly",
        model_accuracy=0.78,
        data_points_used=500,
        last_training_date=datetime.now() - timedelta(days=7)
    )


@pytest.mark.asyncio
class TestMarketPredictionEngine:
    """Test cases for Market Prediction Engine"""

    async def test_engine_initialization(self, prediction_engine):
        """Test prediction engine initializes correctly"""
        assert prediction_engine is not None
        assert hasattr(prediction_engine, 'llm_client')
        assert hasattr(prediction_engine, 'rc_assistant')
        assert hasattr(prediction_engine, 'models')
        assert hasattr(prediction_engine, 'scalers')

    async def test_historical_data_loading(self, prediction_engine):
        """Test historical data loading"""
        await prediction_engine._load_historical_data()

        assert len(prediction_engine.market_data) > 0
        assert all(isinstance(point, MarketDataPoint) for point in prediction_engine.market_data)

        # Check data covers multiple neighborhoods
        neighborhoods = set(point.neighborhood for point in prediction_engine.market_data)
        assert len(neighborhoods) >= 3

    async def test_synthetic_data_generation(self, prediction_engine):
        """Test synthetic data generation"""
        date = datetime(2023, 6, 15)
        neighborhood = "etiwanda"
        base_price = 650000

        data_point = prediction_engine._generate_synthetic_data_point(date, neighborhood, base_price)

        assert isinstance(data_point, MarketDataPoint)
        assert data_point.date == date
        assert data_point.neighborhood == neighborhood
        assert data_point.median_price > 0
        assert 0 < data_point.interest_rate < 10
        assert 0.8 < data_point.employment_rate < 1.0

    async def test_model_training(self, prediction_engine):
        """Test ML model training"""
        # Load data first
        await prediction_engine._load_historical_data()

        # Train models
        await prediction_engine._train_models()

        # Check models were created
        assert 'price_appreciation' in prediction_engine.models
        assert 'timing' in prediction_engine.models
        assert 'roi' in prediction_engine.models

        # Check model metadata
        assert 'price_appreciation' in prediction_engine.model_metadata
        price_model_meta = prediction_engine.model_metadata['price_appreciation']
        assert 'features' in price_model_meta
        assert 'mae' in price_model_meta
        assert 'r2' in price_model_meta

    async def test_price_appreciation_prediction(self, prediction_engine):
        """Test price appreciation prediction"""
        # Setup models
        await prediction_engine._load_historical_data()
        await prediction_engine._train_models()

        with patch.object(prediction_engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"key_factors": ["Market momentum", "Employment growth"], "risk_factors": ["Interest rate risk"], "opportunities": ["Investment timing", "Market entry"]}'
            )

            result = await prediction_engine.predict_price_appreciation(
                neighborhood="etiwanda",
                time_horizon=TimeHorizon.MEDIUM_TERM
            )

            assert isinstance(result, PredictionResult)
            assert result.prediction_type == PredictionType.PRICE_APPRECIATION
            assert result.target == "etiwanda"
            assert result.time_horizon == TimeHorizon.MEDIUM_TERM
            assert result.predicted_value > 0
            assert result.current_value > 0
            assert len(result.key_factors) > 0

    async def test_optimal_timing_prediction(self, prediction_engine):
        """Test optimal timing prediction"""
        await prediction_engine._load_historical_data()
        await prediction_engine._train_models()

        with patch.object(prediction_engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"key_factors": ["Seasonal advantage", "Low inventory"], "risk_factors": ["Rate volatility"], "opportunities": ["Negotiation power", "Selection"]}'
            )

            # Test sell timing
            sell_result = await prediction_engine.predict_optimal_timing(
                action_type="sell",
                neighborhood="etiwanda"
            )

            assert isinstance(sell_result, PredictionResult)
            assert sell_result.prediction_type == PredictionType.OPTIMAL_TIMING
            assert "sell_etiwanda" in sell_result.target

            # Test buy timing
            buy_result = await prediction_engine.predict_optimal_timing(
                action_type="buy",
                neighborhood="etiwanda"
            )

            assert isinstance(buy_result, PredictionResult)
            assert "buy_etiwanda" in buy_result.target

    async def test_investment_roi_prediction(self, prediction_engine):
        """Test investment ROI prediction"""
        await prediction_engine._load_historical_data()
        await prediction_engine._train_models()

        property_data = {
            "neighborhood": "etiwanda",
            "price": 750000,
            "sqft": 2000,
            "property_type": "single_family"
        }

        with patch.object(prediction_engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"key_factors": ["Rental demand", "Appreciation potential"], "risk_factors": ["Market cycles"], "opportunities": ["Tax benefits", "Leverage"]}'
            )

            result = await prediction_engine.predict_investment_roi(
                property_data=property_data,
                investment_horizon=5
            )

            assert isinstance(result, PredictionResult)
            assert result.prediction_type == PredictionType.INVESTMENT_ROI
            assert result.time_horizon == TimeHorizon.LONG_TERM
            assert isinstance(result.predicted_value, (int, float))  # ROI percentage (can be negative)

    async def test_market_opportunity_detection(self, prediction_engine):
        """Test market opportunity detection"""
        await prediction_engine._load_historical_data()
        await prediction_engine._train_models()

        with patch.object(prediction_engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"key_factors": ["Growth momentum"], "risk_factors": ["Rate sensitivity"], "opportunities": ["Early entry"]}'
            )

            opportunities = await prediction_engine.detect_market_opportunities()

            assert isinstance(opportunities, list)
            assert len(opportunities) >= 0

            if opportunities:
                opp = opportunities[0]
                assert isinstance(opp, MarketOpportunity)
                assert opp.opportunity_id
                assert opp.neighborhood
                assert opp.potential_return > 0
                assert 0 <= opp.confidence_score <= 1

    async def test_seasonal_pattern_analysis(self, prediction_engine):
        """Test seasonal pattern analysis"""
        await prediction_engine._load_historical_data()

        with patch.object(prediction_engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"peak_months": [4, 5, 6], "seasonal_trends": "Spring peak activity", "buyer_timing": "Winter for better prices", "seller_timing": "Spring for exposure"}'
            )

            analysis = await prediction_engine.analyze_seasonal_patterns("etiwanda")

            assert "neighborhood" in analysis
            assert "monthly_statistics" in analysis
            assert "patterns" in analysis
            assert "recommendations" in analysis

            # Check monthly statistics
            monthly_stats = analysis["monthly_statistics"]
            assert isinstance(monthly_stats, dict)

    async def test_interest_rate_impact_analysis(self, prediction_engine):
        """Test interest rate impact analysis"""
        analysis = await prediction_engine.analyze_interest_rate_impact(
            rate_change=0.5,  # 0.5% increase
            neighborhood="etiwanda"
        )

        assert "rate_change" in analysis
        assert "neighborhood_impacts" in analysis
        assert "strategic_insights" in analysis
        assert "timing_recommendations" in analysis

        # Check neighborhood impact
        etiwanda_impact = analysis["neighborhood_impacts"]["etiwanda"]
        assert "current_rate" in etiwanda_impact
        assert "new_rate" in etiwanda_impact
        assert "demand_impact_pct" in etiwanda_impact
        assert "buyer_affordability" in etiwanda_impact

    async def test_confidence_calculation(self, prediction_engine):
        """Test confidence score calculation"""
        # High accuracy, recent data, low volatility = high confidence
        high_conf = prediction_engine._calculate_confidence(
            model_accuracy=0.9,
            data_recency=0.95,
            market_volatility=0.1
        )
        assert high_conf > 0.7

        # Low accuracy, old data, high volatility = low confidence
        low_conf = prediction_engine._calculate_confidence(
            model_accuracy=0.3,
            data_recency=0.4,
            market_volatility=0.8
        )
        assert low_conf < 0.5

    async def test_confidence_level_mapping(self, prediction_engine):
        """Test confidence score to level mapping"""
        high_level = prediction_engine._score_to_confidence_level(0.85)
        assert high_level == MarketConfidence.HIGH

        medium_level = prediction_engine._score_to_confidence_level(0.65)
        assert medium_level == MarketConfidence.MEDIUM

        low_level = prediction_engine._score_to_confidence_level(0.45)
        assert low_level == MarketConfidence.LOW

        uncertain_level = prediction_engine._score_to_confidence_level(0.25)
        assert uncertain_level == MarketConfidence.UNCERTAIN

    async def test_time_horizon_conversion(self, prediction_engine):
        """Test time horizon to timedelta conversion"""
        short_delta = prediction_engine._get_horizon_timedelta(TimeHorizon.SHORT_TERM)
        assert short_delta == timedelta(days=90)

        medium_delta = prediction_engine._get_horizon_timedelta(TimeHorizon.MEDIUM_TERM)
        assert medium_delta == timedelta(days=365)

        long_delta = prediction_engine._get_horizon_timedelta(TimeHorizon.LONG_TERM)
        assert long_delta == timedelta(days=1095)

    async def test_current_market_conditions(self, prediction_engine):
        """Test current market conditions retrieval"""
        await prediction_engine._load_historical_data()

        conditions = await prediction_engine._get_current_market_conditions("etiwanda")

        assert isinstance(conditions, dict)
        assert "median_price" in conditions
        assert "days_on_market" in conditions
        assert "interest_rate" in conditions
        assert conditions["median_price"] > 0

    async def test_prediction_features_preparation(self, prediction_engine):
        """Test prediction features preparation"""
        await prediction_engine._load_historical_data()
        await prediction_engine._train_models()

        conditions = {
            "days_on_market": 25,
            "inventory_months": 2.5,
            "interest_rate": 5.5,
            "employment_rate": 0.94,
            "is_spring_market": True,
            "consumer_confidence": 95.0
        }

        features = prediction_engine._prepare_prediction_features(conditions, 'price_appreciation')

        assert isinstance(features, list)
        assert len(features) > 0
        assert all(isinstance(f, (int, float)) for f in features)

    async def test_opportunity_creation(self, prediction_engine, sample_prediction_result):
        """Test market opportunity creation"""
        opportunity = await prediction_engine._create_appreciation_opportunity(
            "etiwanda",
            sample_prediction_result
        )

        assert isinstance(opportunity, MarketOpportunity)
        assert opportunity.opportunity_type == "appreciation"
        assert opportunity.neighborhood == "etiwanda"
        assert opportunity.potential_return == sample_prediction_result.change_percentage
        assert len(opportunity.recommended_actions) > 0

    async def test_affordability_calculation(self, prediction_engine):
        """Test affordability impact calculation"""
        affordability = prediction_engine._calculate_affordability_impact(
            price=750000,
            old_rate=5.0,
            new_rate=6.0
        )

        assert "old_payment" in affordability
        assert "new_payment" in affordability
        assert "payment_change" in affordability
        assert "change_percentage" in affordability

        assert affordability["new_payment"] > affordability["old_payment"]
        assert affordability["change_percentage"] > 0

    async def test_prediction_caching(self, prediction_engine, sample_prediction_result):
        """Test prediction result caching"""
        with patch.object(prediction_engine.cache, 'set') as mock_set:
            await prediction_engine._cache_prediction_result(sample_prediction_result)
            mock_set.assert_called_once()

    async def test_prediction_analytics(self, prediction_engine):
        """Test prediction analytics generation"""
        # Add some model metadata
        prediction_engine.model_metadata['test_model'] = {
            'r2': 0.75,
            'mae': 0.05,
            'training_date': datetime.now(),
            'data_points': 1000
        }

        analytics = await prediction_engine.get_prediction_analytics()

        assert "model_performance" in analytics
        assert "prediction_trends" in analytics
        assert "confidence_distribution" in analytics
        assert "accuracy_tracking" in analytics

        # Check model performance data
        assert "test_model" in analytics["model_performance"]
        test_model_perf = analytics["model_performance"]["test_model"]
        assert test_model_perf["accuracy"] == 0.75
        assert test_model_perf["data_points"] == 1000

    async def test_error_handling_missing_model(self, prediction_engine):
        """Test error handling when models aren't trained"""
        # Clear models and mark as initialized to prevent re-training
        prediction_engine.models.clear()
        prediction_engine._is_initialized = True

        with pytest.raises(ValueError):
            await prediction_engine.predict_price_appreciation("etiwanda", TimeHorizon.MEDIUM_TERM)

    async def test_error_handling_ai_insights(self, prediction_engine):
        """Test fallback when AI insight generation fails"""
        with patch.object(prediction_engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.side_effect = Exception("AI service unavailable")

            insights = await prediction_engine._generate_prediction_insights(
                "etiwanda", "price_appreciation", 0.05, {}
            )

            # Should return fallback insights
            assert "key_factors" in insights
            assert "risk_factors" in insights
            assert "opportunities" in insights
            assert len(insights["key_factors"]) > 0

    async def test_singleton_pattern(self):
        """Test singleton pattern implementation"""
        engine1 = get_market_prediction_engine()
        engine2 = get_market_prediction_engine()

        assert engine1 is engine2


@pytest.mark.asyncio
class TestMarketDataPoint:
    """Test MarketDataPoint dataclass"""

    def test_data_point_creation(self):
        """Test market data point creation"""
        data_point = MarketDataPoint(
            date=datetime(2023, 6, 15),
            neighborhood="etiwanda",
            median_price=725000,
            days_on_market=22,
            inventory_months=2.3,
            price_per_sqft=385,
            interest_rate=5.5,
            employment_rate=0.94,
            population_growth=0.025,
            new_construction=150,
            month=6,
            quarter=2,
            is_spring_market=False,
            is_holiday_season=False,
            gas_prices=4.2,
            mortgage_applications=12000,
            consumer_confidence=98.5
        )

        assert data_point.neighborhood == "etiwanda"
        assert data_point.median_price == 725000
        assert data_point.month == 6
        assert data_point.quarter == 2
        assert data_point.is_spring_market is False


@pytest.mark.asyncio
class TestPredictionResult:
    """Test PredictionResult dataclass"""

    def test_result_creation(self):
        """Test prediction result creation"""
        result = PredictionResult(
            prediction_id="test-123",
            prediction_type=PredictionType.PRICE_APPRECIATION,
            target="etiwanda",
            time_horizon=TimeHorizon.MEDIUM_TERM,
            predicted_value=780000,
            current_value=750000,
            change_percentage=4.0,
            confidence_level=MarketConfidence.HIGH,
            confidence_score=0.85,
            key_factors=["Growth", "Demand"],
            risk_factors=["Rates"],
            opportunities=["Investment"],
            target_date=datetime(2024, 12, 31),
            update_frequency="weekly",
            model_accuracy=0.78,
            data_points_used=500,
            last_training_date=datetime(2023, 12, 1)
        )

        assert result.prediction_type == PredictionType.PRICE_APPRECIATION
        assert result.change_percentage == 4.0
        assert result.confidence_level == MarketConfidence.HIGH
        assert result.prediction_date is not None  # Auto-set in __post_init__

    def test_result_auto_date(self):
        """Test automatic prediction date setting"""
        result = PredictionResult(
            prediction_id="auto-date-test",
            prediction_type=PredictionType.OPTIMAL_TIMING,
            target="test",
            time_horizon=TimeHorizon.SHORT_TERM,
            predicted_value=100,
            current_value=95,
            change_percentage=5.3,
            confidence_level=MarketConfidence.MEDIUM,
            confidence_score=0.65,
            key_factors=[],
            risk_factors=[],
            opportunities=[],
            target_date=datetime.now() + timedelta(days=90),
            update_frequency="daily",
            model_accuracy=0.70,
            data_points_used=300,
            last_training_date=datetime.now()
        )

        assert result.prediction_date is not None
        assert isinstance(result.prediction_date, datetime)


@pytest.mark.asyncio
class TestMarketOpportunity:
    """Test MarketOpportunity dataclass"""

    def test_opportunity_creation(self):
        """Test market opportunity creation"""
        opportunity = MarketOpportunity(
            opportunity_id="opp-123",
            opportunity_type="appreciation",
            neighborhood="etiwanda",
            description="Strong appreciation expected",
            potential_return=12.5,
            confidence_score=0.80,
            timeline="6-12 months",
            investment_required=750000,
            risk_level="medium",
            risk_factors=["Rate sensitivity"],
            mitigation_strategies=["Timing flexibility"],
            recommended_actions=["Target investors"],
            ideal_client_profile="Investment buyers"
        )

        assert opportunity.opportunity_type == "appreciation"
        assert opportunity.potential_return == 12.5
        assert opportunity.confidence_score == 0.80
        assert opportunity.created_at is not None  # Auto-set


# Integration tests
@pytest.mark.integration
class TestMarketPredictionIntegration:
    """Integration tests for Market Prediction Engine"""

    @pytest.mark.asyncio
    async def test_complete_prediction_workflow(self):
        """Test complete prediction workflow"""
        engine = get_market_prediction_engine()

        # Wait for models to initialize
        await asyncio.sleep(0.1)

        # Ensure models are trained
        if not engine.models:
            await engine._load_historical_data()
            await engine._train_models()

        with patch.object(engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"key_factors": ["Market momentum"], "risk_factors": ["Rate risk"], "opportunities": ["Timing"]}'
            )

            # Test price prediction
            price_pred = await engine.predict_price_appreciation(
                "etiwanda", TimeHorizon.MEDIUM_TERM
            )
            assert price_pred.prediction_id

            # Test timing prediction
            timing_pred = await engine.predict_optimal_timing(
                "sell", "etiwanda"
            )
            assert timing_pred.prediction_id

            # Test ROI prediction
            roi_pred = await engine.predict_investment_roi(
                {"neighborhood": "etiwanda", "price": 750000, "sqft": 2000}
            )
            assert roi_pred.prediction_id

    @pytest.mark.asyncio
    async def test_market_analysis_pipeline(self):
        """Test comprehensive market analysis pipeline"""
        engine = get_market_prediction_engine()

        # Ensure models are ready
        if not engine.models:
            await engine._load_historical_data()
            await engine._train_models()

        with patch.object(engine.llm_client, 'agenerate') as mock_agenerate:
            # Return a response that works for both seasonal analysis and prediction insights
            mock_agenerate.return_value = Mock(
                content='{"peak_months": [4, 5], "seasonal_trends": "Spring surge", "buyer_timing": "Fall", "seller_timing": "Spring", "key_factors": ["Market momentum"], "risk_factors": ["Rate risk"], "opportunities": ["Timing"]}'
            )

            # Seasonal analysis
            seasonal = await engine.analyze_seasonal_patterns("etiwanda")
            assert "patterns" in seasonal

            # Interest rate impact
            rate_impact = await engine.analyze_interest_rate_impact(0.25)
            assert "strategic_insights" in rate_impact

            # Market opportunities
            opportunities = await engine.detect_market_opportunities()
            assert isinstance(opportunities, list)

    @pytest.mark.asyncio
    async def test_multi_neighborhood_analysis(self):
        """Test analysis across multiple neighborhoods"""
        engine = get_market_prediction_engine()

        if not engine.models:
            await engine._load_historical_data()
            await engine._train_models()

        neighborhoods = ["etiwanda", "alta_loma", "central_rc"]

        with patch.object(engine.llm_client, 'agenerate') as mock_agenerate:
            mock_agenerate.return_value = Mock(
                content='{"key_factors": ["Location"], "risk_factors": ["Market"], "opportunities": ["Growth"]}'
            )

            predictions = []
            for neighborhood in neighborhoods:
                pred = await engine.predict_price_appreciation(
                    neighborhood, TimeHorizon.MEDIUM_TERM
                )
                predictions.append(pred)

            assert len(predictions) == 3
            assert all(pred.target in neighborhoods for pred in predictions)

    @pytest.mark.asyncio
    async def test_model_retraining_workflow(self):
        """Test model retraining workflow"""
        engine = get_market_prediction_engine()

        # Initial training
        await engine._load_historical_data()
        await engine._train_models()

        initial_training_date = engine.model_metadata.get('price_appreciation', {}).get('training_date')

        # Add more data (simulate)
        additional_data = engine._generate_synthetic_data_point(
            datetime.now() - timedelta(days=1),
            "new_neighborhood",
            700000
        )
        engine.market_data.append(additional_data)

        # Retrain
        await engine._train_models()

        new_training_date = engine.model_metadata.get('price_appreciation', {}).get('training_date')

        # Training date should be updated
        if initial_training_date:
            assert new_training_date >= initial_training_date

    @pytest.mark.asyncio
    async def test_prediction_accuracy_tracking(self):
        """Test prediction accuracy tracking over time"""
        engine = get_market_prediction_engine()

        if not engine.models:
            await engine._load_historical_data()
            await engine._train_models()

        # Get analytics
        analytics = await engine.get_prediction_analytics()

        assert "model_performance" in analytics
        assert "accuracy_tracking" in analytics

        # Should have model performance data
        if analytics["model_performance"]:
            for model_name, perf in analytics["model_performance"].items():
                assert "accuracy" in perf
                assert 0 <= perf["accuracy"] <= 1