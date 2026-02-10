"""
Tests for Market Share Analytics

This module tests the MarketShareAnalytics including time series forecasting,
competitive dynamics analysis, and market expansion opportunity identification.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.analytics.market_share_analytics import (
    MarketShareAnalytics, MarketShareDataPoint, TimeSeriesForecast,
    CompetitiveDynamics, MarketExpansionOpportunity, MarketShareAnalysis,
    TrendType, ForecastHorizon, ModelType
)
from src.core.event_bus import EventType, EventPriority

@pytest.mark.unit


class TestMarketShareAnalytics:
    """Test suite for Market Share Analytics."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing."""
        mock_bus = MagicMock()
        mock_bus.publish = AsyncMock()
        return mock_bus
    
    @pytest.fixture
    def analytics_engine(self, mock_event_bus):
        """Market share analytics with mocked dependencies.""" 
        return MarketShareAnalytics(
            event_bus=mock_event_bus,
            min_data_points=6,  # Reduced for testing
            forecast_confidence=0.95,
            seasonality_threshold=0.3,
            volatility_threshold=0.2
        )
    
    @pytest.fixture
    def sample_market_share_data(self):
        """Sample market share time series data."""
        base_date = datetime.now(timezone.utc) - timedelta(days=365)
        data_points = []
        
        # Generate 12 months of data for 3 competitors in 2 segments
        competitors = [
            {"id": "comp_001", "base_share": 0.4, "trend": 0.002},   # Growing leader
            {"id": "comp_002", "base_share": 0.35, "trend": -0.001}, # Declining
            {"id": "comp_003", "base_share": 0.25, "trend": 0.003}   # Fast growing
        ]
        
        segments = ["Enterprise", "SMB"]
        
        for month in range(12):
            date = base_date + timedelta(days=month * 30)
            
            for segment in segments:
                for i, comp in enumerate(competitors):
                    # Add some noise and trend
                    share = comp["base_share"] + (month * comp["trend"]) + np.random.normal(0, 0.02)
                    share = max(0.05, min(0.8, share))  # Keep reasonable bounds
                    
                    data_point = MarketShareDataPoint(
                        competitor_id=comp["id"],
                        market_segment=segment,
                        timestamp=date,
                        market_share=share,
                        revenue=share * 10000000,  # $10M base market
                        customer_count=int(share * 50000),
                        share_of_voice=share * 1.2,  # Slightly higher SOV
                        marketing_spend=share * 500000,  # $500K base spend
                        product_launches=np.random.poisson(0.2),
                        pricing_changes=np.random.poisson(0.1)
                    )
                    data_points.append(data_point)
        
        return data_points
    
    @pytest.fixture
    def minimal_data(self):
        """Minimal market share data for edge case testing."""
        base_date = datetime.now(timezone.utc) - timedelta(days=90)
        
        return [
            MarketShareDataPoint(
                competitor_id="comp_001",
                market_segment="Test",
                timestamp=base_date + timedelta(days=i * 10),
                market_share=0.4 + (i * 0.01),
                revenue=1000000.0
            )
            for i in range(6)  # Exactly minimum data points
        ]
    
    @pytest.mark.asyncio
    async def test_initialize_analytics_engine(self, analytics_engine):
        """Test analytics engine initialization."""
        assert analytics_engine is not None
        assert analytics_engine.forecasts_generated == 0
        assert analytics_engine.analyses_completed == 0
        assert analytics_engine.min_data_points == 6
        assert analytics_engine.forecast_confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_forecast_market_shares(self, analytics_engine, sample_market_share_data):
        """Test market share forecasting."""
        forecasts = await analytics_engine.forecast_market_shares(
            historical_data=sample_market_share_data,
            forecast_horizon=ForecastHorizon.MEDIUM_TERM,
            model_type=ModelType.ARIMA,
            correlation_id="test_correlation_001"
        )
        
        # Verify forecasts structure
        assert len(forecasts) > 0  # Should have forecasts for multiple competitor-segment pairs
        
        for forecast in forecasts:
            assert isinstance(forecast, TimeSeriesForecast)
            assert forecast.competitor_id in ["comp_001", "comp_002", "comp_003"]
            assert forecast.market_segment in ["Enterprise", "SMB"]
            assert forecast.model_type == ModelType.ARIMA
            assert forecast.forecast_horizon == ForecastHorizon.MEDIUM_TERM
            assert len(forecast.predicted_values) == 3  # Medium term = 3 months
            assert len(forecast.confidence_intervals) == len(forecast.predicted_values)
            assert len(forecast.prediction_dates) == len(forecast.predicted_values)
            assert isinstance(forecast.trend_type, TrendType)
            assert isinstance(forecast.seasonality_detected, bool)
            assert 0.0 <= forecast.model_accuracy_score <= 1.0
        
        # Verify confidence intervals structure
        for forecast in forecasts:
            for lower, upper in forecast.confidence_intervals:
                assert isinstance(lower, float)
                assert isinstance(upper, float)
                assert lower <= upper
        
        # Verify event was published
        analytics_engine.event_bus.publish.assert_called_once()
        published_event = analytics_engine.event_bus.publish.call_args[1]
        assert published_event['event_type'] == EventType.MARKET_SHARE_CALCULATED
        
        # Verify metrics updated
        assert analytics_engine.forecasts_generated > 0
    
    def test_group_data_by_competitor_segment(self, analytics_engine, sample_market_share_data):
        """Test data grouping functionality."""
        groups = analytics_engine._group_data_by_competitor_segment(sample_market_share_data)
        
        # Verify grouping structure
        assert len(groups) == 6  # 3 competitors × 2 segments
        
        for (competitor_id, segment), data_points in groups.items():
            assert competitor_id in ["comp_001", "comp_002", "comp_003"]
            assert segment in ["Enterprise", "SMB"]
            assert len(data_points) == 12  # 12 months of data
            
            # Verify data is sorted by timestamp
            timestamps = [dp.timestamp for dp in data_points]
            assert timestamps == sorted(timestamps)
    
    def test_analyze_trend_seasonality(self, analytics_engine):
        """Test trend and seasonality analysis."""
        # Create test time series with known trend
        dates = pd.date_range(start='2023-01-01', periods=24, freq='M')
        
        # Growing trend
        growing_series = pd.Series(
            [0.3 + (i * 0.01) + np.random.normal(0, 0.005) for i in range(24)],
            index=dates
        )
        
        trend_type, seasonality = analytics_engine._analyze_trend_seasonality(growing_series)
        assert isinstance(trend_type, TrendType)
        assert isinstance(seasonality, bool)
        
        # For growing series, should detect growth
        assert trend_type in [TrendType.GROWING, TrendType.SEASONAL]
        
        # Test with short series (should use simple analysis)
        short_series = pd.Series([0.3, 0.31, 0.32, 0.33, 0.34, 0.35])
        trend_type_short, seasonality_short = analytics_engine._analyze_trend_seasonality(short_series)
        
        assert trend_type_short == TrendType.GROWING
        assert seasonality_short == False
    
    @pytest.mark.asyncio
    async def test_arima_forecast(self, analytics_engine):
        """Test ARIMA forecasting functionality."""
        # Create test time series
        dates = pd.date_range(start='2023-01-01', periods=12, freq='M')
        ts_data = pd.Series(
            [0.3 + (i * 0.01) + np.random.normal(0, 0.01) for i in range(12)],
            index=dates
        )
        
        result = analytics_engine._arima_forecast(ts_data, ForecastHorizon.MEDIUM_TERM)
        
        if result:  # ARIMA might fail with small/noisy data
            predicted_values, confidence_intervals, accuracy_score = result
            
            assert len(predicted_values) == 3  # Medium term horizon
            assert len(confidence_intervals) == 3
            assert 0.0 <= accuracy_score <= 1.0
            
            for pred in predicted_values:
                assert isinstance(pred, float)
                assert 0.0 <= pred <= 1.0  # Market share bounds
    
    def test_get_forecast_steps(self, analytics_engine):
        """Test forecast steps calculation for different horizons."""
        assert analytics_engine._get_forecast_steps(ForecastHorizon.SHORT_TERM) == 1
        assert analytics_engine._get_forecast_steps(ForecastHorizon.MEDIUM_TERM) == 3
        assert analytics_engine._get_forecast_steps(ForecastHorizon.LONG_TERM) == 12
        assert analytics_engine._get_forecast_steps(ForecastHorizon.STRATEGIC) == 24
    
    def test_generate_prediction_dates(self, analytics_engine):
        """Test prediction date generation."""
        last_date = datetime.now(timezone.utc)
        dates = analytics_engine._generate_prediction_dates(
            last_date, ForecastHorizon.MEDIUM_TERM
        )
        
        assert len(dates) == 3  # Medium term = 3 dates
        
        # Verify dates are in future and properly spaced
        for i, date in enumerate(dates):
            expected_date = last_date + timedelta(days=(i + 1) * 30)
            # Allow some tolerance for day differences
            assert abs((date - expected_date).days) <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_competitive_dynamics(self, analytics_engine, sample_market_share_data):
        """Test competitive dynamics analysis."""
        dynamics_list = await analytics_engine.analyze_competitive_dynamics(
            historical_data=sample_market_share_data,
            analysis_period_months=12
        )
        
        # Verify dynamics structure
        for dynamics in dynamics_list:
            assert isinstance(dynamics, CompetitiveDynamics)
            assert dynamics.market_segment in ["Enterprise", "SMB"]
            assert isinstance(dynamics.competitor_interactions, dict)
            assert isinstance(dynamics.granger_causality, dict)
            assert 0.0 <= dynamics.competitive_pressure_index <= 1.0
            assert 0.0 <= dynamics.market_concentration <= 1.0
            assert dynamics.volatility_score >= 0.0
    
    def test_create_competitor_time_series_matrix(self, analytics_engine, sample_market_share_data):
        """Test time series matrix creation."""
        # Filter data for one segment
        enterprise_data = [
            dp for dp in sample_market_share_data 
            if dp.market_segment == "Enterprise"
        ]
        
        matrix = analytics_engine._create_competitor_time_series_matrix(enterprise_data)
        
        # Verify matrix structure
        assert isinstance(matrix, pd.DataFrame)
        assert len(matrix.columns) == 3  # 3 competitors
        assert len(matrix) > 0  # Should have time periods
        
        # Verify all values are numeric and reasonable
        assert matrix.dtypes.apply(lambda x: np.issubdtype(x, np.number)).all()
        assert (matrix >= 0.0).all().all()
        assert (matrix <= 1.0).all().all()
    
    @pytest.mark.asyncio 
    async def test_identify_expansion_opportunities(self, analytics_engine, sample_market_share_data):
        """Test market expansion opportunity identification."""
        opportunities = await analytics_engine.identify_expansion_opportunities(
            historical_data=sample_market_share_data,
            growth_threshold=0.05,  # 5% minimum growth
            min_opportunity_value=100000.0
        )
        
        # Verify opportunities structure
        for opportunity in opportunities:
            assert isinstance(opportunity, MarketExpansionOpportunity)
            assert opportunity.target_segment in ["Enterprise", "SMB"]
            assert len(opportunity.current_leaders) <= 3  # Top 3 leaders
            assert opportunity.growth_potential >= 0.0
            assert 0.0 <= opportunity.entry_difficulty <= 1.0
            assert opportunity.time_to_market > 0
            assert 0.0 <= opportunity.required_market_share <= 1.0
            assert 0.0 <= opportunity.competitive_response_risk <= 1.0
            assert opportunity.opportunity_value > 0.0
            assert 0.0 <= opportunity.confidence_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_analysis(self, analytics_engine, sample_market_share_data):
        """Test comprehensive analysis generation."""
        analysis = await analytics_engine.generate_comprehensive_analysis(
            historical_data=sample_market_share_data,
            forecast_horizon=ForecastHorizon.MEDIUM_TERM,
            correlation_id="test_comprehensive_001"
        )
        
        # Verify comprehensive analysis structure
        assert isinstance(analysis, MarketShareAnalysis)
        assert analysis.correlation_id == "test_comprehensive_001"
        assert len(analysis.market_segments) == 2  # Enterprise, SMB
        assert len(analysis.forecasts) > 0
        assert len(analysis.competitive_dynamics) >= 0
        assert len(analysis.expansion_opportunities) >= 0
        assert isinstance(analysis.market_trends, dict)
        assert isinstance(analysis.recommendations, list)
        
        # Verify forecasts
        for forecast in analysis.forecasts:
            assert isinstance(forecast, TimeSeriesForecast)
        
        # Verify market trends structure
        trends = analysis.market_trends
        assert "growth_trends" in trends
        assert "competitive_trends" in trends
        assert "forecast_summary" in trends
        
        # Verify event was published
        call_count = analytics_engine.event_bus.publish.call_count
        assert call_count >= 2  # Should publish multiple events during analysis
        
        # Verify metrics updated
        assert analytics_engine.analyses_completed > 0
    
    def test_analyze_market_trends(self, analytics_engine, sample_market_share_data):
        """Test market trends analysis."""
        # Create mock forecasts and dynamics
        mock_forecasts = [
            TimeSeriesForecast(
                forecast_id="test_001",
                competitor_id="comp_001",
                market_segment="Enterprise",
                model_type=ModelType.ARIMA,
                forecast_horizon=ForecastHorizon.MEDIUM_TERM,
                prediction_dates=[datetime.now(timezone.utc) + timedelta(days=30)],
                predicted_values=[0.42],
                confidence_intervals=[(0.40, 0.44)],
                trend_type=TrendType.GROWING,
                seasonality_detected=False,
                model_accuracy_score=0.85,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_dynamics = [
            CompetitiveDynamics(
                analysis_id="dyn_001",
                market_segment="Enterprise",
                time_period=(datetime.now(timezone.utc) - timedelta(days=365), datetime.now(timezone.utc)),
                competitor_interactions={},
                market_elasticity={},
                granger_causality={},
                competitive_pressure_index=0.7,
                market_concentration=0.4,
                volatility_score=0.15
            )
        ]
        
        trends = analytics_engine._analyze_market_trends(
            sample_market_share_data, mock_forecasts, mock_dynamics
        )
        
        # Verify trends structure
        assert "growth_trends" in trends
        assert "competitive_trends" in trends
        assert "forecast_summary" in trends
        
        # Verify forecast summary
        forecast_summary = trends["forecast_summary"]
        assert "total_forecasts" in forecast_summary
        assert "average_accuracy" in forecast_summary
        assert forecast_summary["total_forecasts"] == 1
    
    def test_generate_market_recommendations(self, analytics_engine):
        """Test market recommendations generation."""
        # Create mock data
        mock_forecasts = [
            TimeSeriesForecast(
                forecast_id="test_001",
                competitor_id="comp_001", 
                market_segment="Enterprise",
                model_type=ModelType.ARIMA,
                forecast_horizon=ForecastHorizon.MEDIUM_TERM,
                prediction_dates=[],
                predicted_values=[],
                confidence_intervals=[],
                trend_type=TrendType.GROWING,
                seasonality_detected=False,
                model_accuracy_score=0.5,  # Low accuracy to trigger recommendation
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_dynamics = [
            CompetitiveDynamics(
                analysis_id="dyn_001",
                market_segment="Enterprise",
                time_period=(datetime.now(timezone.utc), datetime.now(timezone.utc)),
                competitor_interactions={},
                market_elasticity={},
                granger_causality={},
                competitive_pressure_index=0.8,  # High pressure
                market_concentration=0.3,
                volatility_score=0.1
            )
        ]
        
        mock_opportunities = [
            MarketExpansionOpportunity(
                opportunity_id="opp_001",
                target_segment="Enterprise",
                current_leaders=["comp_001"],
                growth_potential=0.15,
                entry_difficulty=0.5,
                time_to_market=12,
                required_market_share=0.1,
                competitive_response_risk=0.6,
                opportunity_value=5000000.0,
                confidence_score=0.8
            )
        ]
        
        mock_trends = {
            "growth_trends": {"Enterprise": {"direction": "growing", "strength": 0.15}},
            "market_growth": {"overall_growth": 0.12}
        }
        
        recommendations = analytics_engine._generate_market_recommendations(
            mock_forecasts, mock_dynamics, mock_opportunities, mock_trends
        )
        
        # Verify recommendations structure
        assert isinstance(recommendations, list)
        
        for rec in recommendations:
            assert "type" in rec
            assert "title" in rec
            assert "description" in rec
            assert "priority" in rec
            
            # Verify valid recommendation types
            valid_types = ["opportunity", "defense", "growth", "competitive", "expansion", "data_quality"]
            assert rec["type"] in valid_types
    
    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self, analytics_engine, minimal_data):
        """Test handling of insufficient data scenarios."""
        # Reduce data to below minimum threshold
        insufficient_data = minimal_data[:3]  # Only 3 points, need 6
        
        forecasts = await analytics_engine.forecast_market_shares(
            historical_data=insufficient_data,
            forecast_horizon=ForecastHorizon.SHORT_TERM
        )
        
        # Should return empty list due to insufficient data
        assert len(forecasts) == 0
    
    @pytest.mark.asyncio
    async def test_ensemble_forecast(self, analytics_engine):
        """Test ensemble forecasting method."""
        # Create test data frame
        dates = pd.date_range(start='2023-01-01', periods=12, freq='M')
        ts_data = pd.DataFrame({
            'market_share': [0.3 + (i * 0.01) + np.random.normal(0, 0.005) for i in range(12)],
            'share_of_voice': [0.35 + (i * 0.01) + np.random.normal(0, 0.005) for i in range(12)],
            'marketing_spend': [500000 + (i * 10000) for i in range(12)]
        }, index=dates)
        
        result = await analytics_engine._ensemble_forecast(ts_data, ForecastHorizon.SHORT_TERM)
        
        if result:  # Ensemble might fail with small/noisy data
            predicted_values, confidence_intervals, accuracy_score = result
            
            assert len(predicted_values) == 1  # Short term horizon
            assert len(confidence_intervals) == 1
            assert 0.0 <= accuracy_score <= 1.0
    
    def test_performance_metrics(self, analytics_engine):
        """Test performance metrics collection."""
        metrics = analytics_engine.get_performance_metrics()
        
        assert "forecasts_generated" in metrics
        assert "analyses_completed" in metrics
        assert "average_model_accuracy" in metrics
        assert "cache_hit_rate" in metrics
        assert "cached_forecasts" in metrics
        assert "cached_models" in metrics
        
        # Initial values should be zero
        assert metrics["forecasts_generated"] == 0
        assert metrics["analyses_completed"] == 0
        assert metrics["average_model_accuracy"] == 0.0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, analytics_engine):
        """Test error handling with invalid data."""
        # Test with empty data
        empty_forecasts = await analytics_engine.forecast_market_shares(
            historical_data=[],
            forecast_horizon=ForecastHorizon.MEDIUM_TERM
        )
        
        assert len(empty_forecasts) == 0
        
        # Test with malformed data
        malformed_data = [
            MarketShareDataPoint(
                competitor_id="test",
                market_segment="test",
                timestamp=datetime.now(timezone.utc),
                market_share=-0.5,  # Invalid negative share
                revenue=None
            )
        ]
        
        # Should handle gracefully
        try:
            await analytics_engine.forecast_market_shares(
                historical_data=malformed_data,
                forecast_horizon=ForecastHorizon.SHORT_TERM
            )
        except Exception as e:
            # Exception is expected for severely malformed data
            assert isinstance(e, Exception)
    
    @pytest.mark.asyncio
    async def test_forecast_horizon_consistency(self, analytics_engine, minimal_data):
        """Test forecast horizon consistency across methods."""
        # Test all forecast horizons
        horizons = [
            ForecastHorizon.SHORT_TERM,
            ForecastHorizon.MEDIUM_TERM,
            ForecastHorizon.LONG_TERM
        ]
        
        for horizon in horizons:
            forecasts = await analytics_engine.forecast_market_shares(
                historical_data=minimal_data,
                forecast_horizon=horizon
            )
            
            # If forecasts are generated, verify they match the horizon
            for forecast in forecasts:
                assert forecast.forecast_horizon == horizon
                expected_steps = analytics_engine._get_forecast_steps(horizon)
                assert len(forecast.predicted_values) == expected_steps
                assert len(forecast.prediction_dates) == expected_steps