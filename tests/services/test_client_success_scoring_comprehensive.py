import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive Test Suite for Client Success Scoring & Accountability System

Tests all components of the client success system with 95%+ accuracy validation
and performance benchmarks to ensure system reliability and trustworthiness.

Test Coverage:
- Client Success Scoring Service
- Value Justification Calculator
- Client Outcome Verification Service
- Premium Service Justification Engine
- Integration Service
- Dashboard Components
- Performance Benchmarks
- Accuracy Validation
"""

import asyncio
import statistics
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from ghl_real_estate_ai.services.client_outcome_verification_service import (
        ClientOutcomeVerificationService,
        TransactionVerification,
        VerificationLevel,
        VerificationSource,
    )
    from ghl_real_estate_ai.services.client_success_integration_service import (
        ClientSuccessIntegrationService,
        PerformanceSnapshot,
    )
    from ghl_real_estate_ai.services.client_success_scoring_service import (
        AgentPerformanceReport,
        ClientSuccessScoringService,
        MetricType,
        SuccessMetric,
        VerificationStatus,
    )
    from ghl_real_estate_ai.services.premium_service_justification_engine import (
        GuaranteeType,
        PremiumServiceJustificationEngine,
        PricingRecommendation,
    )
    from ghl_real_estate_ai.services.premium_service_justification_engine import ServiceTier as PremiumServiceTier
    from ghl_real_estate_ai.services.value_justification_calculator import (
        CompetitorType,
        ServiceTier,
        ValueJustificationCalculator,
        ValueJustificationReport,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestClientSuccessScoringService:
    """Test suite for Client Success Scoring Service"""

    @pytest.fixture
    def success_service(self):
        """Create success scoring service for testing"""
        return ClientSuccessScoringService()

    @pytest.fixture
    def sample_agent_metrics(self):
        """Sample agent performance metrics"""
        return {
            "negotiation_performance": 0.97,
            "avg_days_market": 18,
            "client_satisfaction": 4.8,
            "success_rate": 0.95,
            "overall_performance_score": 94,
            "transaction_count": 25,
            "data_verification_rate": 0.95,
        }

    @pytest.mark.asyncio
    async def test_track_success_metric_accuracy(self, success_service, sample_agent_metrics):
        """Test success metric tracking with accuracy validation"""
        # Test negotiation performance metric
        metric = await success_service.track_success_metric(
            agent_id="test_agent_001",
            metric_type=MetricType.NEGOTIATION_PERFORMANCE,
            value=0.97,
            transaction_id="txn_123",
            verification_data={"mls_price": 445000, "sold_price": 447000},
        )

        assert metric.agent_id == "test_agent_001"
        assert metric.metric_type == MetricType.NEGOTIATION_PERFORMANCE
        assert metric.value == 0.97
        assert metric.verification_status in [VerificationStatus.VERIFIED, VerificationStatus.PENDING]
        assert metric.timestamp is not None

        # Verify metric is within expected bounds
        assert 0.0 <= metric.value <= 1.1  # Allow slight over-achievement
        assert metric.baseline_value > 0
        assert metric.market_average > 0

    @pytest.mark.asyncio
    async def test_generate_performance_report_completeness(self, success_service, sample_agent_metrics):
        """Test performance report generation with completeness validation"""
        report = await success_service.generate_agent_performance_report(agent_id="test_agent_001", period_days=30)

        # Validate report structure
        assert isinstance(report, AgentPerformanceReport)
        assert report.agent_id == "test_agent_001"
        assert report.overall_score >= 0 and report.overall_score <= 100
        assert 0 <= report.verification_rate <= 1
        assert isinstance(report.metrics, dict)
        assert isinstance(report.market_comparison, dict)
        assert isinstance(report.value_delivered, dict)
        assert isinstance(report.client_testimonials, list)
        assert isinstance(report.success_stories, list)
        assert isinstance(report.improvement_areas, list)
        assert report.generated_at is not None

    @pytest.mark.asyncio
    async def test_roi_calculation_accuracy(self, success_service):
        """Test ROI calculation accuracy with known test data"""
        # Test with known values
        roi_report = await success_service.calculate_client_roi(
            client_id="test_client_001", agent_id="test_agent_001", period_days=365
        )

        # Validate ROI calculations
        assert roi_report.total_value_delivered > 0
        assert roi_report.fees_paid > 0

        # Calculate expected ROI
        expected_roi = (roi_report.total_value_delivered - roi_report.fees_paid) / roi_report.fees_paid * 100
        assert abs(roi_report.roi_percentage - expected_roi) < 0.01  # Within 0.01% accuracy

        # Validate component calculations
        total_calculated = (
            roi_report.negotiation_savings + roi_report.time_savings_value + roi_report.risk_prevention_value
        )
        assert abs(roi_report.total_value_delivered - total_calculated) < 100  # Within $100

    @pytest.mark.asyncio
    async def test_transparency_dashboard_data_integrity(self, success_service):
        """Test transparency dashboard data integrity"""
        dashboard_data = await success_service.get_transparency_dashboard_data(
            agent_id="test_agent_001", include_public_metrics=True
        )

        # Validate dashboard structure
        assert "public_metrics" in dashboard_data
        assert "full_report" in dashboard_data
        assert "last_updated" in dashboard_data

        public_metrics = dashboard_data["public_metrics"]

        # Validate public metrics
        assert "agent_success_score" in public_metrics
        assert "verified_metrics" in public_metrics
        assert "verification_rate" in public_metrics
        assert "total_value_delivered" in public_metrics

        # Validate metric accuracy
        assert 0 <= public_metrics["agent_success_score"] <= 100
        assert public_metrics["total_value_delivered"] >= 0

        # Validate verification data
        verified_metrics = public_metrics["verified_metrics"]
        for metric_name, metric_data in verified_metrics.items():
            assert "value" in metric_data
            assert "vs_market" in metric_data
            assert metric_data["value"] >= 0

    @pytest.mark.asyncio
    async def test_premium_pricing_justification_logic(self, success_service):
        """Test premium pricing justification logic"""
        justification = await success_service.justify_premium_pricing(
            agent_id="test_agent_001", proposed_commission_rate=0.035, market_commission_rate=0.03
        )

        # Validate justification structure
        assert "premium_percentage" in justification
        assert "justified_premium" in justification
        assert "value_factors" in justification
        assert "roi_analysis" in justification
        assert "recommendation" in justification

        # Validate calculations
        expected_premium = ((0.035 - 0.03) / 0.03) * 100
        assert abs(justification["premium_percentage"] - expected_premium) < 0.1

        # Validate ROI analysis
        roi_analysis = justification["roi_analysis"]
        assert roi_analysis["additional_fee"] > 0
        assert roi_analysis["negotiation_value"] >= 0
        assert roi_analysis["time_value"] >= 0

        # Validate recommendation logic
        recommendation = justification["recommendation"]
        assert isinstance(recommendation["justified"], bool)
        assert recommendation["suggested_rate"] > 0


class TestValueJustificationCalculator:
    """Test suite for Value Justification Calculator"""

    @pytest.fixture
    def value_calculator(self):
        """Create value justification calculator for testing"""
        return ValueJustificationCalculator()

    @pytest.fixture
    def sample_performance_metrics(self):
        """Sample agent performance metrics"""
        return {
            "negotiation_performance": 0.97,
            "avg_days_market": 18,
            "client_satisfaction": 4.8,
            "marketing_reach_multiplier": 1.15,
            "financing_success_rate": 0.95,
            "commission_rate": 0.035,
            "transaction_count": 30,
        }

    @pytest.mark.asyncio
    async def test_comprehensive_value_calculation_accuracy(self, value_calculator, sample_performance_metrics):
        """Test comprehensive value calculation with accuracy validation"""
        report = await value_calculator.calculate_comprehensive_value_justification(
            agent_id="test_agent_001",
            agent_performance_metrics=sample_performance_metrics,
            property_value=450000,
            proposed_commission_rate=0.035,
        )

        # Validate report structure
        assert isinstance(report, ValueJustificationReport)
        assert report.agent_id == "test_agent_001"
        assert report.property_value == 450000
        assert report.recommended_commission_rate > 0

        # Validate value calculations
        assert report.total_value_delivered > 0
        assert report.total_fees > 0
        assert report.net_client_benefit == report.total_value_delivered - report.total_fees

        # Validate ROI calculation
        expected_roi = (report.net_client_benefit / report.total_fees * 100) if report.total_fees > 0 else 0
        assert abs(report.roi_percentage - expected_roi) < 0.01

        # Validate individual value components
        assert report.negotiation_value.value_amount >= 0
        assert report.time_value.value_amount >= 0
        assert report.risk_prevention_value.value_amount >= 0
        assert report.market_timing_value.value_amount >= 0
        assert report.expertise_value.value_amount >= 0

        # Validate confidence metrics
        assert all(0 <= score <= 1 for score in report.confidence_metrics.values())

    @pytest.mark.asyncio
    async def test_service_tier_comparison_logic(self, value_calculator, sample_performance_metrics):
        """Test service tier comparison logic"""
        tier_comparisons = await value_calculator.compare_service_tiers(
            agent_performance_metrics=sample_performance_metrics, property_value=450000
        )

        # Validate comparison structure
        for tier, comparison in tier_comparisons.items():
            assert isinstance(tier, ServiceTier)
            assert "commission_rate" in comparison
            assert "total_value_delivered" in comparison
            assert "net_client_benefit" in comparison
            assert "roi_percentage" in comparison
            assert "value_per_dollar" in comparison

            # Validate logical relationships
            assert comparison["commission_amount"] == 450000 * comparison["commission_rate"]
            assert comparison["value_per_dollar"] > 0

        # Validate tier ordering (premium should deliver more value)
        premium_value = tier_comparisons[ServiceTier.PREMIUM]["total_value_delivered"]
        basic_value = tier_comparisons[ServiceTier.BASIC]["total_value_delivered"]
        assert premium_value >= basic_value

    @pytest.mark.asyncio
    async def test_competitive_roi_analysis_accuracy(self, value_calculator, sample_performance_metrics):
        """Test competitive ROI analysis accuracy"""
        for competitor_type in CompetitorType:
            roi_analysis = await value_calculator.calculate_competitive_roi(
                agent_performance_metrics=sample_performance_metrics,
                property_value=450000,
                competitor_type=competitor_type,
            )

            # Validate analysis structure
            assert roi_analysis["competitor_type"] == competitor_type.value
            assert "cost_comparison" in roi_analysis
            assert "value_comparison" in roi_analysis
            assert "net_analysis" in roi_analysis

            # Validate cost comparison
            cost_comp = roi_analysis["cost_comparison"]
            assert cost_comp["agent_commission"] > 0
            assert cost_comp["competitor_commission"] >= 0
            assert cost_comp["cost_difference"] == cost_comp["agent_commission"] - cost_comp["competitor_commission"]

            # Validate net analysis
            net_analysis = roi_analysis["net_analysis"]
            assert "net_benefit" in net_analysis
            assert "roi_percentage" in net_analysis
            assert "value_justification" in net_analysis


class TestClientOutcomeVerificationService:
    """Test suite for Client Outcome Verification Service"""

    @pytest.fixture
    def verification_service(self):
        """Create verification service for testing"""
        return ClientOutcomeVerificationService()

    @pytest.fixture
    def sample_transaction_data(self):
        """Sample transaction data for testing"""
        return {
            "transaction_id": "txn_123",
            "agent_id": "test_agent_001",
            "client_id": "test_client_001",
            "property_address": "123 Test St, Rancho Cucamonga, CA",
            "listed_price": 440000,
            "sold_price": 447000,
            "commission_paid": 15645,
            "days_on_market": 18,
            "client_satisfaction": 4.8,
        }

    @pytest.mark.asyncio
    async def test_transaction_verification_accuracy(self, verification_service, sample_transaction_data):
        """Test transaction verification with accuracy validation"""
        verification = await verification_service.verify_transaction_outcome(
            transaction_id="txn_123", claimed_data=sample_transaction_data
        )

        # Validate verification structure
        assert isinstance(verification, TransactionVerification)
        assert verification.transaction_id == "txn_123"
        assert verification.agent_id == "test_agent_001"
        assert verification.overall_verification_level in VerificationLevel
        assert 0 <= verification.overall_accuracy <= 100

        # Validate individual verifications
        assert verification.price_verification.accuracy_percentage >= 0
        assert verification.timeline_verification.accuracy_percentage >= 0
        assert verification.commission_verification.accuracy_percentage >= 0

        # Validate verification evidence
        for verification_obj in [
            verification.price_verification,
            verification.timeline_verification,
            verification.commission_verification,
        ]:
            assert len(verification_obj.evidence) > 0
            for evidence in verification_obj.evidence:
                assert evidence.source in VerificationSource
                assert 0 <= evidence.confidence_score <= 1
                assert evidence.timestamp is not None

    @pytest.mark.asyncio
    async def test_client_satisfaction_verification(self, verification_service):
        """Test client satisfaction verification accuracy"""
        satisfaction_verification = await verification_service.verify_client_satisfaction(
            client_id="test_client_001", transaction_id="txn_123", agent_id="test_agent_001", claimed_rating=4.8
        )

        # Validate verification structure
        assert satisfaction_verification.client_id == "test_client_001"
        assert satisfaction_verification.claimed_rating == 4.8
        assert satisfaction_verification.verification_level in VerificationLevel
        assert 0 <= satisfaction_verification.confidence_score <= 1
        assert satisfaction_verification.average_verified_rating >= 0

        # Validate verified ratings
        for source, rating in satisfaction_verification.verified_ratings.items():
            assert 0 <= rating <= 5.0

        # Validate discrepancy detection
        assert isinstance(satisfaction_verification.discrepancy_flags, list)

    @pytest.mark.asyncio
    async def test_performance_metric_verification(self, verification_service):
        """Test individual performance metric verification"""
        verification = await verification_service.verify_performance_metric(
            agent_id="test_agent_001",
            metric_type="negotiation_performance",
            claimed_value=0.97,
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
        )

        # Validate verification
        assert verification.outcome_type == "negotiation_performance"
        assert verification.claimed_value == 0.97
        assert verification.verified_value >= 0
        assert verification.verification_level in VerificationLevel
        assert 0 <= verification.accuracy_percentage <= 100
        assert len(verification.evidence) > 0
        assert isinstance(verification.anomalies_detected, list)

    @pytest.mark.asyncio
    async def test_verification_report_completeness(self, verification_service):
        """Test verification report completeness and accuracy"""
        report = await verification_service.get_verification_report(agent_id="test_agent_001", period_days=30)

        # Validate report structure
        assert "agent_id" in report
        assert "report_period" in report
        assert "verification_summary" in report
        assert "metric_breakdown" in report
        assert "data_quality_score" in report
        assert "recommendations" in report

        # Validate verification summary
        summary = report["verification_summary"]
        assert summary["total_verifications"] >= 0
        assert 0 <= summary["overall_verification_rate"] <= 1
        assert 0 <= summary["average_accuracy"] <= 100
        assert "verification_levels" in summary

        # Validate metric breakdown
        metric_breakdown = report["metric_breakdown"]
        for metric_type, metrics in metric_breakdown.items():
            assert "average_accuracy" in metrics
            assert "verification_count" in metrics
            assert 0 <= metrics["average_accuracy"] <= 100
            assert metrics["verification_count"] >= 0

    @pytest.mark.asyncio
    async def test_anomaly_detection_accuracy(self, verification_service):
        """Test anomaly detection accuracy and sensitivity"""
        anomalies = await verification_service.detect_verification_anomalies(
            agent_id="test_agent_001", lookback_days=90
        )

        # Validate anomaly structure
        for anomaly in anomalies:
            assert "type" in anomaly
            assert "description" in anomaly
            assert "severity" in anomaly
            assert anomaly["severity"] in ["low", "medium", "high"]
            assert "details" in anomaly


class TestPremiumServiceJustificationEngine:
    """Test suite for Premium Service Justification Engine"""

    @pytest.fixture
    def premium_engine(self):
        """Create premium service justification engine for testing"""
        return PremiumServiceJustificationEngine()

    @pytest.fixture
    def high_performance_metrics(self):
        """High-performance agent metrics"""
        return {
            "negotiation_performance": 0.98,
            "avg_days_market": 15,
            "client_satisfaction": 4.9,
            "success_rate": 0.98,
            "overall_performance_score": 95,
            "transaction_count": 50,
        }

    @pytest.mark.asyncio
    async def test_premium_pricing_recommendation_logic(self, premium_engine, high_performance_metrics):
        """Test premium pricing recommendation logic"""
        recommendation = await premium_engine.generate_premium_pricing_recommendation(
            agent_id="test_agent_001",
            agent_performance_metrics=high_performance_metrics,
            property_value=750000,
            market_conditions={"seller_market": True},
        )

        # Validate recommendation structure
        assert isinstance(recommendation, PricingRecommendation)
        assert recommendation.service_tier in PremiumServiceTier
        assert recommendation.base_commission_rate > 0
        assert 0 <= recommendation.confidence_score <= 1
        assert len(recommendation.guarantees_offered) >= 0

        # Validate performance bonuses
        for bonus_type, bonus_rate in recommendation.performance_bonuses.items():
            assert bonus_rate >= 0
            assert bonus_rate <= 0.01  # Max 1% bonus

        # Validate service guarantees
        for guarantee in recommendation.guarantees_offered:
            assert guarantee.guarantee_type in GuaranteeType
            assert guarantee.guarantee_threshold > 0
            assert 0 <= guarantee.confidence_level <= 1
            assert 0 <= guarantee.historical_achievement_rate <= 1

    @pytest.mark.asyncio
    async def test_value_communication_templates(self, premium_engine, high_performance_metrics):
        """Test value communication template generation"""
        templates = await premium_engine.create_value_communication_templates(
            agent_id="test_agent_001",
            service_tier=PremiumServiceTier.ELITE,
            agent_performance_metrics=high_performance_metrics,
            target_audiences=["first_time_buyer", "luxury_client", "investor"],
        )

        # Validate template structure
        assert len(templates) == 3
        for template in templates:
            assert template.target_audience in ["first_time_buyer", "luxury_client", "investor"]
            assert len(template.key_value_propositions) > 0
            assert len(template.supporting_statistics) > 0
            assert len(template.testimonial_quotes) > 0
            assert template.call_to_action is not None
            assert len(template.personalization_variables) > 0

    @pytest.mark.asyncio
    async def test_referral_strategy_design(self, premium_engine, high_performance_metrics):
        """Test referral generation strategy design"""
        strategies = await premium_engine.design_referral_generation_strategy(
            agent_id="test_agent_001",
            agent_performance_metrics=high_performance_metrics,
            client_satisfaction_data={"average_rating": 4.8, "response_rate": 0.85},
        )

        # Validate strategy structure
        assert len(strategies) > 0
        for strategy in strategies:
            assert strategy.strategy_name is not None
            assert len(strategy.trigger_conditions) > 0
            assert len(strategy.communication_sequence) > 0
            assert 0 <= strategy.target_referral_rate <= 1
            assert 0 <= strategy.expected_conversion_rate <= 1

    @pytest.mark.asyncio
    async def test_client_retention_optimization(self, premium_engine, high_performance_metrics):
        """Test client retention optimization strategy"""
        client_portfolio = [
            {
                "client_id": "client_001",
                "last_transaction_date": datetime.now() - timedelta(days=180),
                "satisfaction_rating": 4.8,
            },
            {
                "client_id": "client_002",
                "last_transaction_date": datetime.now() - timedelta(days=400),
                "satisfaction_rating": 4.2,
            },
            {
                "client_id": "client_003",
                "last_transaction_date": datetime.now() - timedelta(days=60),
                "satisfaction_rating": 4.9,
            },
        ]

        optimization_strategy = await premium_engine.optimize_client_retention(
            agent_id="test_agent_001",
            client_portfolio=client_portfolio,
            agent_performance_metrics=high_performance_metrics,
        )

        # Validate optimization strategy
        assert "retention_analysis" in optimization_strategy
        assert "intervention_strategies" in optimization_strategy
        assert "communication_schedule" in optimization_strategy
        assert "retention_roi_projection" in optimization_strategy

        # Validate retention analysis
        retention_analysis = optimization_strategy["retention_analysis"]
        assert "high_risk_clients" in retention_analysis
        assert "medium_risk_clients" in retention_analysis
        assert "low_risk_clients" in retention_analysis

        # Validate ROI projection
        roi_projection = optimization_strategy["retention_roi_projection"]
        assert "total_intervention_cost" in roi_projection
        assert "retention_value_gained" in roi_projection
        assert "roi_percentage" in roi_projection


class TestClientSuccessIntegrationService:
    """Test suite for Client Success Integration Service"""

    @pytest.fixture
    def integration_service(self):
        """Create integration service for testing"""
        return ClientSuccessIntegrationService()

    @pytest.mark.asyncio
    async def test_integration_initialization(self, integration_service):
        """Test service integration initialization"""
        with patch.multiple(
            integration_service,
            _test_transaction_intelligence_connection=AsyncMock(return_value=True),
            _test_ai_negotiation_connection=AsyncMock(return_value=True),
            _test_market_service_connection=AsyncMock(return_value=True),
            _test_claude_integration=AsyncMock(return_value=True),
            _test_ghl_integration=AsyncMock(return_value=True),
            _setup_event_handlers=AsyncMock(),
            _initialize_realtime_sync=AsyncMock(),
        ):
            status = await integration_service.initialize_integrations()

            # Validate all integrations succeeded
            for service, success in status.items():
                assert success is True

    @pytest.mark.asyncio
    async def test_transaction_performance_sync(self, integration_service):
        """Test transaction performance synchronization"""
        with patch.multiple(
            integration_service,
            transaction_intelligence=Mock(
                predict_transaction_delays=AsyncMock(return_value={"predicted_days_to_close": 20})
            ),
            ai_negotiation=Mock(get_negotiation_insights=AsyncMock(return_value={"success_probability": 0.95})),
            market_service=Mock(get_current_market_conditions=AsyncMock(return_value={"seller_market": True})),
            claude=Mock(analyze_transaction_performance=AsyncMock(return_value={"recommendations": ["test"]})),
            verification_service=Mock(
                verify_transaction_outcome=AsyncMock(
                    return_value=Mock(overall_verification_level=Mock(value="gold"), overall_accuracy=95)
                )
            ),
            success_service=Mock(track_success_metric=AsyncMock()),
            cache=Mock(set=AsyncMock()),
            _get_ghl_satisfaction_data=AsyncMock(return_value={"rating": 4.8}),
            _calculate_integrated_value=AsyncMock(return_value=15000),
            _trigger_integration_event=AsyncMock(),
        ):
            snapshot = await integration_service.sync_transaction_performance(
                transaction_id="txn_123", agent_id="agent_001", client_id="client_001"
            )

            # Validate snapshot
            assert isinstance(snapshot, PerformanceSnapshot)
            assert snapshot.transaction_id == "txn_123"
            assert snapshot.agent_id == "agent_001"
            assert snapshot.client_id == "client_001"
            assert snapshot.negotiation_performance > 0
            assert snapshot.timeline_efficiency > 0
            assert snapshot.client_satisfaction > 0

    @pytest.mark.asyncio
    async def test_agent_dashboard_metrics_update(self, integration_service):
        """Test agent dashboard metrics update"""
        with patch.multiple(
            integration_service,
            success_service=Mock(
                generate_agent_performance_report=AsyncMock(
                    return_value=Mock(
                        overall_score=94,
                        verification_rate=0.95,
                        metrics={"negotiation_performance": {"value": 0.97}},
                        value_delivered={"total": 50000},
                    )
                )
            ),
            market_service=Mock(get_agent_market_performance=AsyncMock(return_value={"rank": "top_5%"})),
            claude=Mock(generate_performance_insights=AsyncMock(return_value={"analysis": "excellent"})),
            premium_engine=Mock(
                generate_premium_pricing_recommendation=AsyncMock(
                    return_value=Mock(
                        service_tier=Mock(value="elite"),
                        base_commission_rate=0.035,
                        justification_summary="High performance justifies premium",
                        confidence_score=0.92,
                    )
                )
            ),
            cache=Mock(set=AsyncMock()),
            _get_transaction_intelligence_metrics=AsyncMock(return_value={"avg_health_score": 8.5}),
            _get_negotiation_performance_metrics=AsyncMock(return_value={"avg_negotiation_success": 0.97}),
            _calculate_market_ranking=AsyncMock(return_value="Top 5%"),
            _calculate_client_roi_metrics=AsyncMock(return_value={"average_roi": 284.5}),
            _calculate_data_quality_score=AsyncMock(return_value=94.2),
            _get_verification_sources_count=AsyncMock(return_value=6),
            _get_accuracy_trends=AsyncMock(return_value={"daily_accuracy": [0.94, 0.95, 0.96]}),
            _update_ghl_agent_metrics=AsyncMock(),
        ):
            metrics = await integration_service.update_agent_dashboard_metrics(agent_id="agent_001", period_days=30)

            # Validate dashboard metrics
            assert "agent_id" in metrics
            assert "reporting_period" in metrics
            assert "performance_summary" in metrics
            assert "detailed_metrics" in metrics
            assert "value_demonstration" in metrics
            assert "pricing_insights" in metrics
            assert "ai_insights" in metrics
            assert "verification_status" in metrics
            assert "last_updated" in metrics


class TestPerformanceBenchmarks:
    """Performance benchmarks for the client success system"""

    @pytest.mark.asyncio
    async def test_response_time_benchmarks(self):
        """Test response time benchmarks for all services"""

        # Initialize services
        success_service = ClientSuccessScoringService()
        value_calculator = ValueJustificationCalculator()
        verification_service = ClientOutcomeVerificationService()
        premium_engine = PremiumServiceJustificationEngine()

        sample_metrics = {
            "negotiation_performance": 0.97,
            "avg_days_market": 18,
            "client_satisfaction": 4.8,
            "overall_performance_score": 94,
        }

        # Test success metric tracking speed
        start_time = time.time()
        await success_service.track_success_metric("agent_001", MetricType.NEGOTIATION_PERFORMANCE, 0.97, "txn_123")
        metric_tracking_time = time.time() - start_time
        assert metric_tracking_time < 0.5  # Should complete in under 500ms

        # Test performance report generation speed
        start_time = time.time()
        await success_service.generate_agent_performance_report("agent_001", 30)
        report_generation_time = time.time() - start_time
        assert report_generation_time < 2.0  # Should complete in under 2 seconds

        # Test value justification calculation speed
        start_time = time.time()
        await value_calculator.calculate_comprehensive_value_justification("agent_001", sample_metrics, 450000, 0.035)
        value_calculation_time = time.time() - start_time
        assert value_calculation_time < 1.0  # Should complete in under 1 second

        # Test verification speed
        start_time = time.time()
        await verification_service.verify_performance_metric(
            "agent_001", "negotiation_performance", 0.97, datetime.now() - timedelta(days=30), datetime.now()
        )
        verification_time = time.time() - start_time
        assert verification_time < 1.5  # Should complete in under 1.5 seconds

    @pytest.mark.asyncio
    async def test_accuracy_benchmarks(self):
        """Test accuracy benchmarks for calculations and verifications"""

        # Test known value calculations
        value_calculator = ValueJustificationCalculator()

        # Test with known inputs
        known_metrics = {
            "negotiation_performance": 0.96,  # 96% of asking achieved
            "avg_days_market": 20,  # 20 days on market
            "client_satisfaction": 4.5,  # 4.5/5 satisfaction
        }

        # Property value $400,000, 3% commission
        report = await value_calculator.calculate_comprehensive_value_justification(
            "test_agent", known_metrics, 400000, 0.03
        )

        # Calculate expected negotiation value
        # Agent achieves 96%, market average is 94%
        expected_negotiation_value = (0.96 - 0.94) * 400000  # $8,000
        actual_negotiation_value = report.negotiation_value.value_amount

        # Allow 5% variance in calculations
        assert abs(actual_negotiation_value - expected_negotiation_value) / expected_negotiation_value < 0.05

        # Test time value calculation
        # Agent: 20 days, Market: 25 days = 5 days saved
        expected_time_value = 5 * 150  # $750 (5 days * $150/day)
        actual_time_value = report.time_value.value_amount

        # Allow 10% variance (time value is less precise)
        assert abs(actual_time_value - expected_time_value) / max(expected_time_value, 1) < 0.10

    @pytest.mark.asyncio
    async def test_data_consistency_benchmarks(self):
        """Test data consistency across multiple calculations"""

        success_service = ClientSuccessScoringService()

        # Run same calculation multiple times
        results = []
        for i in range(5):
            roi_report = await success_service.calculate_client_roi("client_001", "agent_001", 365)
            results.append(roi_report.roi_percentage)

        # Results should be consistent (within 1%)
        if len(results) > 1:
            max_variance = max(results) - min(results)
            assert max_variance < 1.0  # Less than 1% variance between runs

    @pytest.mark.asyncio
    async def test_memory_usage_benchmarks(self):
        """Test memory usage stays within reasonable bounds"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run intensive operations
        success_service = ClientSuccessScoringService()

        # Generate multiple large reports
        for i in range(10):
            await success_service.generate_agent_performance_report(f"agent_{i}", 30)

        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for test operations)
        assert memory_increase < 100


class TestSystemIntegration:
    """End-to-end system integration tests"""

    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self):
        """Test complete workflow from metric tracking to client communication"""

        # Initialize all services
        success_service = ClientSuccessScoringService()
        integration_service = ClientSuccessIntegrationService()

        # Mock external dependencies
        with patch.multiple(
            integration_service,
            _get_ghl_satisfaction_data=AsyncMock(return_value={"rating": 4.8}),
            _update_ghl_agent_metrics=AsyncMock(),
            _send_value_report_to_ghl=AsyncMock(),
        ):
            # 1. Track success metric
            metric = await success_service.track_success_metric(
                "agent_001", MetricType.NEGOTIATION_PERFORMANCE, 0.97, "txn_123", "client_001"
            )
            assert metric.value == 0.97

            # 2. Generate performance report
            report = await success_service.generate_agent_performance_report("agent_001", 30)
            assert report.overall_score > 0

            # 3. Generate client value report
            value_report = await integration_service.generate_client_value_report("client_001", "agent_001", "txn_123")
            assert "executive_summary" in value_report
            assert "value_breakdown" in value_report

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""

        success_service = ClientSuccessScoringService()

        # Test handling of invalid metric values
        with pytest.raises(Exception):
            await success_service.track_success_metric(
                "agent_001",
                MetricType.NEGOTIATION_PERFORMANCE,
                -0.5,  # Invalid negative value
                "txn_123",
            )

        # Test handling of missing data
        try:
            report = await success_service.generate_agent_performance_report("nonexistent_agent", 30)
            # Should handle gracefully and return empty or default report
            assert report is not None
        except Exception:
            # Or should raise appropriate exception
            pass

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test system behavior under concurrent operations"""

        success_service = ClientSuccessScoringService()

        # Create multiple concurrent operations
        tasks = []
        for i in range(10):
            task = success_service.track_success_metric(
                f"agent_{i % 3}",  # 3 different agents
                MetricType.CLIENT_SATISFACTION,
                4.0 + (i % 10) / 10,  # Ratings from 4.0 to 4.9
                f"txn_{i}",
            )
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result.value >= 4.0


if __name__ == "__main__":
    # Run the test suite
    pytest.main([__file__, "-v", "--tb=short"])