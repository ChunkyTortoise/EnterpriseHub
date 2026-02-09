import pytest
pytestmark = pytest.mark.integration

"""
Unit Tests for Phase 7 Intelligence Services.

Comprehensive unit tests for the Phase 7 Advanced AI Intelligence services:
- Enhanced Revenue Forecasting Engine
- Business Intelligence Dashboard Service
- Conversation Analytics Service
- Market Intelligence Automation
- Real-time Stream Processing
- Cache Intelligence Service

Tests individual service functionality, business logic, and AI integration.

Built for Jorge's Real Estate AI Platform - Phase 7: Advanced AI Intelligence
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

@pytest.mark.integration

# Import Phase 7 intelligence services
try:
    from ghl_real_estate_ai.intelligence.business_intelligence_dashboard import (
        AlertSeverity,
        BusinessIntelligenceAlert,
        BusinessIntelligenceDashboard,
        DashboardMetricType,
        ExecutiveSummary,
    )
    from ghl_real_estate_ai.intelligence.conversation_analytics_service import (
        AdvancedConversationAnalyticsService,
        ConversationInsight,
        JorgeMethodologyScore,
        SentimentAnalysisResult,
    )
    from ghl_real_estate_ai.intelligence.market_intelligence_automation import (
        CompetitiveIntelligence,
        EnhancedMarketIntelligenceAutomation,
        MarketOpportunity,
        MarketTrend,
    )
    from ghl_real_estate_ai.intelligence.revenue_forecasting_engine import (
        AdvancedRevenueForecast,
        DealProbabilityScore,
        EnhancedRevenueForecastingEngine,
        ForecastAccuracy,
        ForecastModelType,
        RevenueStreamType,
    )
    from ghl_real_estate_ai.prediction.business_forecasting_engine import ForecastTimeframe
    from ghl_real_estate_ai.services.bi_cache_service import BICacheService
    from ghl_real_estate_ai.services.bi_stream_processor import BIStreamProcessor
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestEnhancedRevenueForecastingEngine:
    """Test Enhanced Revenue Forecasting Engine functionality."""

    @pytest.fixture
    def revenue_engine(self):
        """Create Revenue Forecasting Engine for testing."""
        return EnhancedRevenueForecastingEngine()

    @pytest.fixture
    def mock_historical_data(self):
        """Mock historical revenue data."""
        return {
            "revenue_by_month": {
                "2025-01": 425000,
                "2025-02": 467000,
                "2025-03": 485000,
                "2025-04": 512000,
                "2025-05": 534000,
            },
            "commission_data": {
                "2025-01": {"jorge_commission": 25500, "commission_rate": 0.06},
                "2025-02": {"jorge_commission": 28020, "commission_rate": 0.06},
                "2025-03": {"jorge_commission": 29100, "commission_rate": 0.06},
            },
            "deal_velocity": {"average_days_to_close": 28, "conversion_rate": 0.284, "pipeline_velocity": 0.92},
        }

    @pytest.mark.asyncio
    async def test_advanced_forecast_generation(self, revenue_engine, mock_historical_data):
        """Test advanced revenue forecast generation with ML models."""

        with (
            patch.object(revenue_engine, "_gather_historical_revenue_data", return_value=mock_historical_data),
            patch.object(revenue_engine, "_run_prophet_model") as mock_prophet,
            patch.object(revenue_engine, "_run_arima_model") as mock_arima,
            patch.object(revenue_engine, "_run_lstm_model") as mock_lstm,
        ):
            # Setup ML model responses
            mock_prophet.return_value = (490000, 0.92)
            mock_arima.return_value = (475000, 0.87)
            mock_lstm.return_value = (495000, 0.94)

            # Generate forecast
            forecast = await revenue_engine.forecast_revenue_advanced(
                timeframe=ForecastTimeframe.MONTHLY,
                revenue_stream=RevenueStreamType.TOTAL_REVENUE,
                include_pipeline=True,
                use_ensemble=True,
            )

            # Verify forecast structure
            assert isinstance(forecast, AdvancedRevenueForecast)
            assert forecast.timeframe == ForecastTimeframe.MONTHLY
            assert forecast.revenue_stream == RevenueStreamType.TOTAL_REVENUE
            assert forecast.base_forecast > 0
            assert forecast.optimistic_forecast >= forecast.base_forecast
            assert forecast.conservative_forecast <= forecast.base_forecast

            # Verify ML model integration
            assert forecast.prophet_forecast == 490000
            assert forecast.arima_forecast == 475000
            assert forecast.lstm_forecast == 495000

            # Verify ensemble calculation
            expected_ensemble = 490000 * 0.3 + 475000 * 0.25 + 495000 * 0.25 + forecast.base_forecast * 0.2
            assert abs(float(forecast.ensemble_forecast) - expected_ensemble) < 1000

            # Verify Jorge-specific metrics
            assert forecast.jorge_commission_rate == 0.06
            assert float(forecast.commission_optimization_potential) > 0
            assert float(forecast.methodology_impact) > 0

    @pytest.mark.asyncio
    async def test_deal_probability_scoring(self, revenue_engine):
        """Test deal probability scoring algorithm."""

        lead_ids = ["lead_123", "lead_456"]

        with (
            patch.object(revenue_engine, "_get_lead_data") as mock_lead,
            patch.object(revenue_engine, "_get_property_data") as mock_property,
            patch.object(revenue_engine, "_get_conversation_analysis") as mock_conversation,
        ):
            # Setup mock data
            mock_lead.return_value = {
                "financial_qualification": {"score": 0.88, "verified": True},
                "engagement_score": 0.82,
                "urgency_level": "high",
                "lead_source": "jorge_bot",
            }

            mock_property.return_value = {
                "estimated_price": 650000,
                "market_conditions": "favorable",
                "property_fit_score": 0.91,
                "competitive_factors": ["low_inventory", "high_demand"],
            }

            mock_conversation.return_value = {
                "sentiment_score": 0.87,
                "jorge_methodology_alignment": 0.94,
                "commitment_indicators": ["timeline_defined", "budget_confirmed"],
                "risk_factors": ["financing_uncertainty"],
            }

            # Calculate deal probabilities
            deal_scores = await revenue_engine.calculate_deal_probability_scores(
                lead_ids=lead_ids, include_pipeline_analysis=True
            )

            # Verify deal scores
            assert len(deal_scores) == len(lead_ids)

            for deal_score in deal_scores:
                assert isinstance(deal_score, DealProbabilityScore)

                # Verify probability range
                assert 0 <= deal_score.closing_probability <= 1
                assert 0 <= deal_score.confidence_score <= 1

                # Verify scoring components
                assert 0 <= deal_score.financial_readiness_score <= 1
                assert 0 <= deal_score.psychological_commitment_score <= 1
                assert 0 <= deal_score.property_fit_score <= 1
                assert 0 <= deal_score.market_conditions_score <= 1

                # Verify Jorge methodology integration
                assert deal_score.jorge_methodology_alignment > 0
                assert deal_score.commission_amount == deal_score.expected_sale_price * Decimal("0.06")

                # Verify actionable outputs
                assert len(deal_score.recommended_actions) > 0
                assert len(deal_score.optimization_opportunities) > 0
                assert deal_score.time_to_close_days > 0

    def test_forecast_accuracy_calculation(self, revenue_engine):
        """Test forecast accuracy calculation methodology."""

        # Mock historical actuals vs predictions
        historical_predictions = [450000, 470000, 485000, 500000]
        actual_results = [445000, 475000, 490000, 495000]

        accuracy = revenue_engine._calculate_forecast_accuracy(
            predictions=historical_predictions, actuals=actual_results
        )

        # Verify accuracy calculation
        assert isinstance(accuracy, ForecastAccuracy)
        assert accuracy.value > 0.85  # Should have high accuracy

        # Calculate expected MAPE
        mapes = [abs(pred - actual) / actual for pred, actual in zip(historical_predictions, actual_results)]
        expected_mape = sum(mapes) / len(mapes)
        expected_accuracy = 1 - expected_mape

        assert abs(accuracy.value - expected_accuracy) < 0.01

    @pytest.mark.asyncio
    async def test_revenue_optimization_plan_generation(self, revenue_engine):
        """Test revenue optimization plan generation logic."""

        # Create current forecast
        current_forecast = AdvancedRevenueForecast(
            timeframe=ForecastTimeframe.MONTHLY,
            revenue_stream=RevenueStreamType.TOTAL_REVENUE,
            base_forecast=Decimal("485000"),
            optimistic_forecast=Decimal("545000"),
            conservative_forecast=Decimal("425000"),
            confidence_level=0.89,
            strategic_insights=["Market conditions favorable"],
            market_factors=["spring_boost", "low_inventory"],
        )

        target_growth = 0.15  # 15% growth target

        # Generate optimization plan
        plan = await revenue_engine.generate_revenue_optimization_plan(
            current_forecast=current_forecast, target_growth=target_growth
        )

        # Verify plan structure
        assert "revenue_analysis" in plan
        assert "immediate_actions" in plan
        assert "strategic_initiatives" in plan
        assert "success_metrics" in plan
        assert "implementation_roadmap" in plan

        # Verify revenue analysis
        revenue_analysis = plan["revenue_analysis"]
        assert revenue_analysis["current_revenue"] == 485000
        assert revenue_analysis["growth_target"] == 0.15
        assert revenue_analysis["target_revenue"] == 485000 * 1.15
        assert revenue_analysis["revenue_gap"] > 0

        # Verify actionable recommendations
        immediate_actions = plan["immediate_actions"]
        assert len(immediate_actions) > 0
        assert any("Jorge" in action for action in immediate_actions)  # Should include Jorge methodology

        # Verify strategic initiatives
        strategic_initiatives = plan["strategic_initiatives"]
        assert len(strategic_initiatives) > 0

        # Verify success metrics
        success_metrics = plan["success_metrics"]
        assert "revenue_growth_target" in success_metrics
        assert "commission_optimization_target" in success_metrics


class TestBusinessIntelligenceDashboard:
    """Test Business Intelligence Dashboard functionality."""

    @pytest.fixture
    def bi_dashboard(self):
        """Create BI Dashboard for testing."""
        return BusinessIntelligenceDashboard()

    @pytest.fixture
    def mock_dashboard_dependencies(self):
        """Mock dashboard dependencies."""
        return {
            "cache_service": Mock(),
            "event_publisher": Mock(),
            "revenue_engine": Mock(),
            "conversation_analytics": Mock(),
            "market_intelligence": Mock(),
        }

    @pytest.mark.asyncio
    async def test_executive_summary_generation(self, bi_dashboard, mock_dashboard_dependencies):
        """Test executive summary generation logic."""

        with patch.multiple(bi_dashboard, **mock_dashboard_dependencies):
            # Setup mock responses
            bi_dashboard.revenue_engine.generate_revenue_forecast = AsyncMock(
                return_value={
                    "monthly_forecast": {"total_projection": 485000, "growth_rate": 0.187},
                    "commission_total": 29100,
                }
            )

            bi_dashboard.conversation_analytics.get_unified_analytics = AsyncMock(
                return_value={
                    "conversation_metrics": {"total_conversations": 1247, "quality_score": 0.89},
                    "conversion_metrics": {"overall_conversion_rate": 0.284},
                    "sentiment_analysis": {"average_sentiment_score": 0.832},
                    "jorge_methodology_analysis": {"effectiveness_score": 0.914},
                }
            )

            bi_dashboard.market_intelligence.get_market_intelligence_dashboard_data = AsyncMock(
                return_value={
                    "market_summary": {"market_health_score": 0.867, "active_trends": 12, "critical_alerts": 2},
                    "market_opportunities": [{"value": 45000}, {"value": 68000}],
                }
            )

            # Generate executive summary
            executive_summary = await bi_dashboard._generate_executive_summary()

            # Verify summary structure
            assert isinstance(executive_summary, ExecutiveSummary)
            assert executive_summary.period == "Last 30 days"

            # Verify revenue summary
            revenue_summary = executive_summary.revenue_summary
            assert revenue_summary["current_month_projection"] == 485000
            assert revenue_summary["commission_total"] == 29100
            assert revenue_summary["growth_rate"] == 0.187

            # Verify conversation summary
            conversation_summary = executive_summary.conversation_summary
            assert conversation_summary["total_conversations"] == 1247
            assert conversation_summary["conversion_rate"] == 0.284
            assert conversation_summary["jorge_methodology_performance"] == 0.914

            # Verify key insights generation
            assert len(executive_summary.key_insights) > 0
            assert any("18.7%" in insight for insight in executive_summary.key_insights)  # Growth rate

            # Verify action items
            assert len(executive_summary.action_items) > 0

            # Verify performance score calculation
            assert 0.8 <= executive_summary.performance_score <= 1.0

    @pytest.mark.asyncio
    async def test_strategic_alerts_generation(self, bi_dashboard):
        """Test strategic alerts generation and prioritization."""

        # Mock conditions that should trigger alerts
        dashboard_metrics = {
            "revenue_growth": -0.05,  # Negative growth
            "conversion_rate": 0.20,  # Below target (25%)
            "pipeline_health": 0.65,  # Below healthy threshold
            "market_temperature": "hot",  # Opportunity
        }

        alerts = await bi_dashboard._generate_strategic_alerts(dashboard_metrics)

        # Verify alerts generated
        assert len(alerts) >= 2  # Should have revenue and conversion alerts

        # Find revenue alert
        revenue_alert = next((alert for alert in alerts if alert.alert_type == DashboardMetricType.REVENUE), None)
        assert revenue_alert is not None
        assert revenue_alert.severity == AlertSeverity.HIGH
        assert "Revenue Growth Declining" in revenue_alert.title
        assert len(revenue_alert.recommended_actions) > 0

        # Find conversion alert
        conversion_alert = next(
            (alert for alert in alerts if alert.alert_type == DashboardMetricType.CONVERSATION), None
        )
        assert conversion_alert is not None
        assert conversion_alert.severity == AlertSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_jorge_kpis_calculation(self, bi_dashboard):
        """Test Jorge-specific KPIs calculation."""

        with patch.object(bi_dashboard, "_get_jorge_performance_data") as mock_jorge_data:
            mock_jorge_data.return_value = {
                "confrontational_success_rate": 0.91,
                "commission_defense_rate": 0.96,
                "methodology_effectiveness": 0.94,
                "qualification_accuracy": 0.88,
                "competitive_win_rate": 0.87,
                "technology_leadership_score": 0.95,
                "revenue_compound_growth": 0.234,
                "technology_roi": 4.2,
            }

            jorge_kpis = await bi_dashboard._get_jorge_kpis()

            # Verify Jorge signature metrics
            signature_metrics = jorge_kpis["jorge_signature_metrics"]
            assert signature_metrics["confrontational_qualification_success"] == 0.91
            assert signature_metrics["commission_defense_rate"] == 0.96
            assert signature_metrics["commission_defense_rate"] >= 0.95  # High standard

            # Verify methodology performance
            methodology_performance = jorge_kpis["jorge_methodology_performance"]
            assert methodology_performance["qualification_accuracy"] == 0.88
            assert methodology_performance["competitive_win_rate"] == 0.87

            # Verify market position
            market_position = jorge_kpis["jorge_market_position"]
            assert market_position["technology_leadership"] == 0.95
            assert market_position["technology_leadership"] > 0.9  # Industry leading

            # Verify growth trajectory
            growth_trajectory = jorge_kpis["jorge_growth_trajectory"]
            assert growth_trajectory["revenue_compound_growth"] == 0.234
            assert growth_trajectory["technology_roi"] == 4.2
            assert growth_trajectory["technology_roi"] > 3.0  # Strong ROI


class TestAdvancedConversationAnalyticsService:
    """Test Advanced Conversation Analytics Service functionality."""

    @pytest.fixture
    def conversation_analytics(self):
        """Create Conversation Analytics Service for testing."""
        return AdvancedConversationAnalyticsService()

    @pytest.fixture
    def mock_conversation_data(self):
        """Mock conversation data for testing."""
        return [
            {
                "conversation_id": "conv_001",
                "lead_id": "lead_123",
                "bot_type": "jorge-seller",
                "messages": [
                    {
                        "role": "bot",
                        "content": "Are you actually serious about selling or just looking around?",
                        "timestamp": "2025-01-25T10:00:00",
                    },
                    {
                        "role": "user",
                        "content": "Yes, we need to sell within 3 months",
                        "timestamp": "2025-01-25T10:01:00",
                    },
                    {
                        "role": "bot",
                        "content": "Good. What's your rock-bottom price?",
                        "timestamp": "2025-01-25T10:02:00",
                    },
                ],
                "outcome": "qualified_hot",
                "sentiment_scores": [0.3, 0.8, 0.6],  # Confrontational, positive response, neutral
                "jorge_methodology_score": 0.94,
            }
        ]

    @pytest.mark.asyncio
    async def test_conversation_sentiment_analysis(self, conversation_analytics, mock_conversation_data):
        """Test conversation sentiment analysis with Jorge methodology."""

        with patch.object(conversation_analytics, "_get_conversation_data", return_value=mock_conversation_data):
            sentiment_results = await conversation_analytics.analyze_conversation_sentiment(
                conversation_ids=["conv_001"], include_jorge_methodology=True
            )

            # Verify sentiment analysis
            assert len(sentiment_results) == 1

            sentiment_result = sentiment_results[0]
            assert isinstance(sentiment_result, SentimentAnalysisResult)
            assert sentiment_result.conversation_id == "conv_001"
            assert sentiment_result.overall_sentiment > 0.4  # Overall positive despite confrontational

            # Verify Jorge methodology scoring
            jorge_score = sentiment_result.jorge_methodology_score
            assert isinstance(jorge_score, JorgeMethodologyScore)
            assert jorge_score.confrontational_effectiveness > 0.8
            assert jorge_score.qualification_depth > 0.8
            assert jorge_score.commitment_extraction > 0.7

    @pytest.mark.asyncio
    async def test_conversion_pattern_analysis(self, conversation_analytics, mock_conversation_data):
        """Test conversion pattern analysis and optimization."""

        with patch.object(conversation_analytics, "_get_conversation_data", return_value=mock_conversation_data):
            patterns = await conversation_analytics.analyze_conversion_patterns(
                timeframe_days=30, bot_types=["jorge-seller"], include_optimization_recommendations=True
            )

            # Verify pattern analysis
            assert "conversion_metrics" in patterns
            assert "jorge_methodology_patterns" in patterns
            assert "optimization_opportunities" in patterns

            # Verify conversion metrics
            conversion_metrics = patterns["conversion_metrics"]
            assert "overall_conversion_rate" in conversion_metrics
            assert "hot_lead_conversion_rate" in conversion_metrics

            # Verify Jorge methodology patterns
            jorge_patterns = patterns["jorge_methodology_patterns"]
            assert "confrontational_success_rate" in jorge_patterns
            assert "qualification_effectiveness" in jorge_patterns

            # Verify optimization opportunities
            optimizations = patterns["optimization_opportunities"]
            assert len(optimizations) > 0
            assert all("action" in opp and "impact" in opp for opp in optimizations)

    @pytest.mark.asyncio
    async def test_jorge_methodology_performance_tracking(self, conversation_analytics):
        """Test Jorge methodology performance tracking and analytics."""

        mock_jorge_conversations = [
            {
                "conversation_id": "conv_001",
                "confrontational_score": 0.95,
                "qualification_depth": 0.88,
                "commitment_extraction": 0.91,
                "outcome": "qualified_hot",
                "lead_temperature": "hot",
            },
            {
                "conversation_id": "conv_002",
                "confrontational_score": 0.87,
                "qualification_depth": 0.82,
                "commitment_extraction": 0.79,
                "outcome": "qualified_warm",
                "lead_temperature": "warm",
            },
        ]

        with patch.object(conversation_analytics, "_get_jorge_conversations", return_value=mock_jorge_conversations):
            performance = await conversation_analytics.get_jorge_methodology_performance(
                timeframe_days=30, include_detailed_analysis=True
            )

            # Verify performance metrics
            assert "overall_effectiveness" in performance
            assert "confrontational_effectiveness" in performance
            assert "qualification_accuracy" in performance

            # Verify effectiveness calculation
            overall_effectiveness = performance["overall_effectiveness"]
            expected_effectiveness = (0.95 + 0.87) / 2  # Average of confrontational scores
            assert abs(overall_effectiveness - expected_effectiveness) < 0.01

            # Verify temperature distribution
            assert "temperature_distribution" in performance
            temp_dist = performance["temperature_distribution"]
            assert temp_dist["hot"] == 0.5  # 1 out of 2 conversations
            assert temp_dist["warm"] == 0.5


class TestMarketIntelligenceAutomation:
    """Test Market Intelligence Automation functionality."""

    @pytest.fixture
    def market_intelligence(self):
        """Create Market Intelligence Automation for testing."""
        return EnhancedMarketIntelligenceAutomation()

    @pytest.mark.asyncio
    async def test_market_trend_detection(self, market_intelligence):
        """Test automated market trend detection and analysis."""

        with patch.object(market_intelligence, "_gather_market_data") as mock_market_data:
            mock_market_data.return_value = {
                "inventory_levels": {"current": 2.1, "historical_avg": 4.5, "trend": "decreasing"},
                "price_trends": {"median_price": 485000, "month_over_month": 0.08, "year_over_year": 0.15},
                "buyer_activity": {"active_buyers": 1247, "showing_requests": 2890, "offer_activity": "high"},
                "seasonal_factors": ["spring_market", "low_inventory_surge"],
            }

            trends = await market_intelligence.detect_market_trends(
                analysis_depth="comprehensive", include_predictive_insights=True
            )

            # Verify trend detection
            assert len(trends) > 0

            for trend in trends:
                assert isinstance(trend, MarketTrend)
                assert trend.trend_type in ["inventory", "pricing", "demand", "seasonal"]
                assert trend.confidence_score > 0.7
                assert len(trend.impact_factors) > 0
                assert len(trend.recommended_actions) > 0

    @pytest.mark.asyncio
    async def test_competitive_intelligence_gathering(self, market_intelligence):
        """Test competitive intelligence gathering and analysis."""

        with patch.object(market_intelligence, "_analyze_competitive_landscape") as mock_competitive:
            mock_competitive.return_value = {
                "competitor_analysis": {
                    "top_competitors": ["Competitor A", "Competitor B", "Competitor C"],
                    "market_share_changes": {"jorge": 0.125, "competitor_a": 0.18, "competitor_b": 0.15},
                    "pricing_strategies": {"jorge": "premium_value", "market_avg": "discount_focused"},
                },
                "competitive_advantages": [
                    "advanced_ai_qualification",
                    "confrontational_methodology",
                    "6_percent_commission_defense",
                ],
                "threat_assessment": {
                    "new_entrants": "medium",
                    "pricing_pressure": "low",
                    "technology_competition": "medium",
                },
            }

            competitive_intel = await market_intelligence.analyze_competitive_landscape(
                include_threat_assessment=True, jorge_methodology_focus=True
            )

            # Verify competitive analysis
            assert isinstance(competitive_intel, CompetitiveIntelligence)
            assert competitive_intel.jorge_market_share == 0.125
            assert len(competitive_intel.competitive_advantages) == 3
            assert "confrontational_methodology" in competitive_intel.competitive_advantages

            # Verify threat assessment
            threat_assessment = competitive_intel.threat_assessment
            assert "pricing_pressure" in threat_assessment
            assert threat_assessment["pricing_pressure"] == "low"  # Jorge's strong positioning

    @pytest.mark.asyncio
    async def test_market_opportunity_identification(self, market_intelligence):
        """Test market opportunity identification and prioritization."""

        with patch.object(market_intelligence, "_scan_market_opportunities") as mock_opportunities:
            mock_opportunities.return_value = [
                {
                    "opportunity_type": "luxury_segment_expansion",
                    "market_size": 125000000,
                    "jorge_fit_score": 0.92,
                    "competition_intensity": "low",
                    "time_to_market": 45,
                    "revenue_potential": 2400000,
                },
                {
                    "opportunity_type": "first_time_buyer_market",
                    "market_size": 95000000,
                    "jorge_fit_score": 0.76,
                    "competition_intensity": "high",
                    "time_to_market": 90,
                    "revenue_potential": 1800000,
                },
            ]

            opportunities = await market_intelligence.identify_market_opportunities(
                prioritize_by_jorge_fit=True, include_risk_assessment=True
            )

            # Verify opportunities
            assert len(opportunities) == 2

            # Verify luxury segment opportunity (should be top priority)
            luxury_opp = opportunities[0]
            assert isinstance(luxury_opp, MarketOpportunity)
            assert luxury_opp.opportunity_type == "luxury_segment_expansion"
            assert luxury_opp.jorge_fit_score == 0.92
            assert luxury_opp.revenue_potential == 2400000

            # Verify opportunity prioritization (luxury should rank higher due to Jorge fit)
            assert opportunities[0].jorge_fit_score >= opportunities[1].jorge_fit_score


class TestBIStreamProcessor:
    """Test BI Stream Processor functionality."""

    @pytest.fixture
    def stream_processor(self):
        """Create BI Stream Processor for testing."""
        return BIStreamProcessor()

    @pytest.mark.asyncio
    async def test_revenue_event_processing(self, stream_processor):
        """Test revenue event processing and aggregation."""

        revenue_event = {
            "event_type": "REVENUE_FORECAST_UPDATED",
            "timestamp": datetime.now().isoformat(),
            "data": {"forecast_amount": 485000, "confidence": 0.89, "timeframe": "monthly", "jorge_commission": 29100},
        }

        # Process revenue event
        result = await stream_processor.process_revenue_event(revenue_event)

        # Verify processing success
        assert result is True

        # Verify event stored for aggregation
        aggregated_metrics = await stream_processor.aggregate_real_time_metrics(window_minutes=15)

        assert "revenue_velocity" in aggregated_metrics
        assert "forecast_confidence_avg" in aggregated_metrics
        assert aggregated_metrics["forecast_confidence_avg"] >= 0.89

    @pytest.mark.asyncio
    async def test_conversation_event_processing(self, stream_processor):
        """Test conversation event processing and analytics."""

        conversation_event = {
            "event_type": "CONVERSATION_COMPLETED",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "conversation_id": "conv_001",
                "bot_type": "jorge-seller",
                "outcome": "qualified_hot",
                "sentiment_score": 0.87,
                "jorge_methodology_score": 0.94,
            },
        }

        # Process conversation event
        result = await stream_processor.process_conversation_event(conversation_event)

        # Verify processing success
        assert result is True

        # Verify analytics aggregation
        analytics = await stream_processor.get_conversation_analytics(window_minutes=30)

        assert "conversion_momentum" in analytics
        assert "jorge_methodology_effectiveness" in analytics
        assert analytics["jorge_methodology_effectiveness"] >= 0.94

    @pytest.mark.asyncio
    async def test_real_time_aggregation(self, stream_processor):
        """Test real-time metrics aggregation across multiple events."""

        # Create multiple events for aggregation testing
        events = [
            {
                "event_type": "DEAL_PROBABILITY_UPDATED",
                "data": {"deal_id": "deal_001", "probability": 0.85, "value": 39000},
            },
            {
                "event_type": "DEAL_PROBABILITY_UPDATED",
                "data": {"deal_id": "deal_002", "probability": 0.72, "value": 45000},
            },
            {"event_type": "PIPELINE_VALUE_UPDATED", "data": {"total_pipeline": 2840000, "deal_count": 45}},
        ]

        # Process all events
        for event in events:
            await stream_processor.process_pipeline_event(event)

        # Aggregate metrics
        metrics = await stream_processor.aggregate_real_time_metrics()

        # Verify aggregation
        assert "pipeline_health" in metrics
        assert "weighted_deal_probability" in metrics
        assert "total_pipeline_value" in metrics

        # Verify calculations
        expected_weighted_prob = (0.85 * 39000 + 0.72 * 45000) / (39000 + 45000)
        assert abs(metrics["weighted_deal_probability"] - expected_weighted_prob) < 0.01


class TestBICacheService:
    """Test BI Cache Service functionality."""

    @pytest.fixture
    def cache_service(self):
        """Create BI Cache Service for testing."""
        return BICacheService()

    @pytest.mark.asyncio
    async def test_dashboard_data_caching(self, cache_service):
        """Test dashboard data caching and retrieval."""

        dashboard_data = {
            "revenue_forecast": {"amount": 485000, "confidence": 0.89},
            "conversion_metrics": {"rate": 0.284, "total": 1247},
            "generated_at": datetime.now().isoformat(),
        }

        cache_key = "dashboard:executive:30d"

        # Cache dashboard data
        success = await cache_service.cache_dashboard_data(
            key=cache_key,
            data=dashboard_data,
            ttl_seconds=300,  # 5 minutes
        )

        assert success is True

        # Retrieve cached data
        cached_data = await cache_service.get_dashboard_data(cache_key)

        assert cached_data is not None
        assert cached_data["revenue_forecast"]["amount"] == 485000
        assert cached_data["conversion_metrics"]["rate"] == 0.284

    @pytest.mark.asyncio
    async def test_intelligent_cache_warming(self, cache_service):
        """Test intelligent cache warming based on usage patterns."""

        # Mock usage pattern data
        usage_patterns = {
            "executive_dashboard": {"frequency": "high", "peak_hours": [8, 9, 17, 18]},
            "revenue_forecasts": {"frequency": "medium", "refresh_interval": 300},
            "conversation_analytics": {"frequency": "low", "on_demand": True},
        }

        with patch.object(cache_service, "_get_usage_patterns", return_value=usage_patterns):
            # Trigger cache warming
            warmed_keys = await cache_service.warm_intelligent_cache()

            # Verify high-frequency items were warmed
            assert len(warmed_keys) > 0
            assert any("executive_dashboard" in key for key in warmed_keys)
            assert any("revenue_forecast" in key for key in warmed_keys)

    def test_cache_hit_rate_tracking(self, cache_service):
        """Test cache hit rate tracking and optimization."""

        # Simulate cache interactions
        cache_service._record_cache_hit("dashboard:executive")
        cache_service._record_cache_miss("dashboard:revenue")
        cache_service._record_cache_hit("dashboard:executive")
        cache_service._record_cache_hit("dashboard:conversations")

        # Calculate hit rate
        hit_rate = cache_service.get_cache_hit_rate()

        # Verify hit rate calculation (3 hits, 1 miss = 75%)
        assert hit_rate == 0.75

        # Verify individual key performance
        key_stats = cache_service.get_key_performance("dashboard:executive")
        assert key_stats["hits"] == 2
        assert key_stats["misses"] == 0
        assert key_stats["hit_rate"] == 1.0


if __name__ == "__main__":
    # Run service tests
    pytest.main(
        [
            __file__ + "::TestEnhancedRevenueForecastingEngine",
            __file__ + "::TestBusinessIntelligenceDashboard",
            __file__ + "::TestAdvancedConversationAnalyticsService",
            __file__ + "::TestBIStreamProcessor",
            "-v",
        ]
    )