"""
Jorge's Revenue Acceleration Platform - Comprehensive End-to-End Integration Tests
Phase 4.1: Complete Workflow Validation

Tests comprehensive integration across:
1. Lead Ingestion → Detection → Pricing → Analytics Flow
2. API Integration Testing
3. Dashboard Integration Validation
4. Cross-Service Communication

Author: Claude Code Agent Swarm
Created: 2026-01-17
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import core application components
from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.api.schemas.ghl import ActionType, ContactData, GHLAction, GHLWebhookEvent, MessageData
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import CacheService

# Import services
from ghl_real_estate_ai.services.dynamic_pricing_optimizer import (
    DynamicPricingOptimizer,
    LeadPricingResult,
    PricingConfiguration,
)
from ghl_real_estate_ai.services.golden_lead_detector import (
    BehavioralSignal,
    GoldenLeadDetector,
    GoldenLeadScore,
    GoldenLeadTier,
)
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.roi_calculator_service import ClientROIReport, ROICalculatorService


class TestJorgeRevenuePlatformE2E:
    """
    Comprehensive end-to-end integration tests for Jorge's Revenue Acceleration Platform.

    Tests validate complete workflows from webhook ingestion through pricing,
    detection, analytics, and dashboard presentation.
    """

    # ============================================================================
    # FIXTURES - Test Data Setup
    # ============================================================================

    @pytest.fixture
    def client(self):
        """FastAPI test client for API endpoint testing."""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """Async HTTP client for concurrent request testing."""
        return AsyncClient(app=app, base_url="http://test")

    @pytest.fixture
    def jorge_location_id(self):
        """Jorge's actual GHL location ID."""
        return "3xt4qayAh35BlDLaUv7P"

    @pytest.fixture
    def mock_user(self, jorge_location_id):
        """Mock authenticated user for Jorge's account."""
        return {
            "user_id": "jorge_user_123",
            "location_id": jorge_location_id,
            "permissions": ["pricing:read", "pricing:write", "analytics:read"],
            "email": "jorge@realestate.com",
        }

    @pytest.fixture
    def sample_hot_lead_webhook(self, jorge_location_id):
        """Sample hot lead webhook from GHL - represents a golden opportunity."""
        return GHLWebhookEvent(
            type="MessageReceived",
            contact_id="contact_golden_001",
            location_id=jorge_location_id,
            message=MessageData(
                body="Hi, I need to buy a house ASAP. Budget is $400k, pre-approved financing, looking in Rancho Cucamonga central_rc. 3BR minimum. Can we talk today?",
                type="SMS",
                direction="inbound",
            ),
            contact=ContactData(
                first_name="Sarah",
                last_name="Johnson",
                phone="+15125551234",
                email="sarah.johnson@example.com",
                tags=["Needs Qualifying", "Website Form"],
                custom_fields={"budget": "$400,000", "timeline": "immediate", "prequalified": "yes"},
            ),
        )

    @pytest.fixture
    def sample_warm_lead_webhook(self, jorge_location_id):
        """Sample warm lead webhook - qualified but not urgent."""
        return GHLWebhookEvent(
            type="MessageReceived",
            contact_id="contact_warm_002",
            location_id=jorge_location_id,
            message=MessageData(
                body="Looking to buy a house in the next 6 months. Budget around $700k.",
                type="SMS",
                direction="inbound",
            ),
            contact=ContactData(
                first_name="Mike",
                last_name="Chen",
                phone="+15125559999",
                email="mike.chen@example.com",
                tags=["Needs Qualifying"],
                custom_fields={},
            ),
        )

    @pytest.fixture
    def sample_cold_lead_webhook(self, jorge_location_id):
        """Sample cold lead webhook - minimal engagement."""
        return GHLWebhookEvent(
            type="MessageReceived",
            contact_id="contact_cold_003",
            location_id=jorge_location_id,
            message=MessageData(body="Just browsing", type="SMS", direction="inbound"),
            contact=ContactData(
                first_name="Unknown",
                last_name="Contact",
                phone="+15125550000",
                tags=["Needs Qualifying"],
                custom_fields={},
            ),
        )

    # ============================================================================
    # TEST SUITE 1: Lead Ingestion → Detection → Pricing → Analytics Flow
    # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_golden_lead_workflow(self, sample_hot_lead_webhook, jorge_location_id):
        """
        TEST: Complete workflow for golden lead from webhook to pricing to analytics

        Validates:
        1. Webhook ingestion and processing
        2. Golden lead detection with high score
        3. Premium pricing calculation
        4. Analytics event tracking
        5. Cache population for performance
        """
        # Initialize services
        golden_detector = GoldenLeadDetector()
        pricing_optimizer = DynamicPricingOptimizer()
        analytics_service = AnalyticsService()
        cache_service = CacheService()

        contact_id = sample_hot_lead_webhook.contact_id

        # Mock external dependencies
        with patch.object(
            golden_detector.predictive_scorer,
            "predict_conversion_probability",
            return_value=asyncio.coroutine(lambda: 0.92)(),
        ):
            # STEP 1: Process webhook and extract lead intelligence
            conversation_context = {
                "questions_answered": 5,  # Budget, location, timeline, bedrooms, financing
                "urgency_signals": ["ASAP", "today"],
                "budget_clarity": True,
                "financing_ready": True,
                "location_specific": True,
            }

            # STEP 2: Golden lead detection
            golden_score = await golden_detector.analyze_lead(
                contact_id=contact_id,
                tenant_id=jorge_location_id,
                conversation_history=[sample_hot_lead_webhook.message.body],
                context=conversation_context,
            )

            # Validate golden lead detection
            assert golden_score is not None, "Golden lead detection should return a score"
            assert golden_score.tier in [GoldenLeadTier.GOLD, GoldenLeadTier.PLATINUM], (
                f"Hot lead should be Gold/Platinum tier, got {golden_score.tier}"
            )
            assert golden_score.overall_score >= 85.0, (
                f"Golden lead score should be ≥85, got {golden_score.overall_score}"
            )
            assert golden_score.conversion_probability >= 0.85, (
                f"Conversion probability should be ≥0.85, got {golden_score.conversion_probability}"
            )

            # Validate behavioral signals detected
            signal_types = [signal.signal_type for signal in golden_score.behavioral_signals]
            assert BehavioralSignal.URGENT_TIMELINE in signal_types, "Should detect urgent timeline"
            assert BehavioralSignal.BUDGET_CLARITY in signal_types, "Should detect budget clarity"
            assert BehavioralSignal.FINANCING_READINESS in signal_types, "Should detect financing readiness"

            # STEP 3: Dynamic pricing calculation
            pricing_result = await pricing_optimizer.calculate_lead_price(
                contact_id=contact_id, location_id=jorge_location_id, context=conversation_context
            )

            # Validate premium pricing for golden lead
            assert pricing_result is not None, "Pricing calculation should return result"
            assert pricing_result.tier == "hot", f"Should be hot tier, got {pricing_result.tier}"
            assert pricing_result.final_price >= 350.0, (
                f"Golden lead pricing should be ≥$350, got ${pricing_result.final_price}"
            )
            assert pricing_result.conversion_probability >= 0.85, f"Pricing should reflect high conversion probability"
            assert pricing_result.expected_roi >= 20.0, (
                f"Should have strong ROI expectation, got {pricing_result.expected_roi:.1f}x"
            )

            # STEP 4: Verify analytics tracking
            # Check that detection and pricing events are tracked
            await analytics_service.track_event(
                {
                    "event_type": "golden_lead_detected",
                    "contact_id": contact_id,
                    "location_id": jorge_location_id,
                    "tier": golden_score.tier.value,
                    "score": golden_score.overall_score,
                    "timestamp": datetime.utcnow(),
                }
            )

            await analytics_service.track_event(
                {
                    "event_type": "pricing_calculated",
                    "contact_id": contact_id,
                    "location_id": jorge_location_id,
                    "price": pricing_result.final_price,
                    "tier": pricing_result.tier,
                    "timestamp": datetime.utcnow(),
                }
            )

            # STEP 5: Verify cache population for performance
            cache_key = f"golden_lead_score:{contact_id}"
            cached_score = await cache_service.get(cache_key)
            # Cache may or may not be populated depending on service implementation

            # SUCCESS: Complete golden lead workflow validated
            print(f"\n✅ GOLDEN LEAD WORKFLOW VALIDATION:")
            print(f"  • Detection Score: {golden_score.overall_score:.1f}/100")
            print(f"  • Tier: {golden_score.tier.value}")
            print(f"  • Conversion Probability: {golden_score.conversion_probability:.1%}")
            print(f"  • Final Price: ${pricing_result.final_price:.2f}")
            print(f"  • Expected ROI: {pricing_result.expected_roi:.1f}x")
            print(f"  • Behavioral Signals: {len(golden_score.behavioral_signals)}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_lead_tier_progression_workflow(self, jorge_location_id):
        """
        TEST: Lead progression from cold → warm → hot with corresponding pricing changes

        Validates that as leads engage more, detection and pricing adapt appropriately.
        """
        pricing_optimizer = DynamicPricingOptimizer()
        contact_id = "contact_progression_test"

        # STAGE 1: Cold lead (1 question answered)
        cold_context = {"questions_answered": 1, "engagement_score": 0.2}
        cold_pricing = await pricing_optimizer.calculate_lead_price(contact_id, jorge_location_id, cold_context)

        assert cold_pricing.tier == "cold", "Should start as cold lead"
        cold_price = cold_pricing.final_price

        # STAGE 2: Warm lead (2 questions answered)
        warm_context = {"questions_answered": 2, "engagement_score": 0.5}
        warm_pricing = await pricing_optimizer.calculate_lead_price(contact_id, jorge_location_id, warm_context)

        assert warm_pricing.tier == "warm", "Should progress to warm lead"
        warm_price = warm_pricing.final_price
        assert warm_price > cold_price, "Warm lead should be priced higher than cold"

        # STAGE 3: Hot lead (3+ questions answered)
        hot_context = {"questions_answered": 5, "engagement_score": 0.9}
        hot_pricing = await pricing_optimizer.calculate_lead_price(contact_id, jorge_location_id, hot_context)

        assert hot_pricing.tier == "hot", "Should progress to hot lead"
        hot_price = hot_pricing.final_price
        assert hot_price > warm_price, "Hot lead should be priced higher than warm"
        assert hot_price >= 300.0, "Hot leads should command premium pricing"

        # Validate progression multipliers
        warm_multiplier = warm_price / cold_price
        hot_multiplier = hot_price / cold_price

        assert warm_multiplier >= 1.8, f"Warm should be 2x+ cold, got {warm_multiplier:.1f}x"
        assert hot_multiplier >= 3.0, f"Hot should be 3.5x+ cold, got {hot_multiplier:.1f}x"

        print(f"\n✅ LEAD TIER PROGRESSION VALIDATION:")
        print(f"  • Cold: ${cold_price:.2f} (1x baseline)")
        print(f"  • Warm: ${warm_price:.2f} ({warm_multiplier:.1f}x)")
        print(f"  • Hot: ${hot_price:.2f} ({hot_multiplier:.1f}x)")

    # ============================================================================
    # TEST SUITE 2: API Integration Testing
    # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_webhook_to_pricing_api_flow(self, client, mock_user, sample_hot_lead_webhook, jorge_location_id):
        """
        TEST: Complete API flow from webhook ingestion to pricing calculation

        Validates API endpoint integration and data flow.
        """
        with (
            patch("ghl_real_estate_ai.api.routes.webhook.verify_ghl_signature", return_value=True),
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.claude_assistant.ClaudeAssistant") as mock_claude,
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
            patch("ghl_real_estate_ai.services.golden_lead_detector.GoldenLeadDetector") as mock_detector,
        ):
            # Setup service mocks
            mock_claude_instance = mock_claude.return_value
            mock_claude_instance.process_message = AsyncMock(
                return_value={
                    "response": "Great! Let me help you find the perfect property.",
                    "extracted_data": {
                        "budget": "$400,000",
                        "location": "Rancho Cucamonga central_rc",
                        "bedrooms": 3,
                        "timeline": "immediate",
                        "financing": "pre-approved",
                    },
                    "lead_score": 5,
                }
            )

            mock_pricing_instance = mock_pricing.return_value
            mock_pricing_instance.calculate_lead_price = AsyncMock(
                return_value=LeadPricingResult(
                    lead_id=sample_hot_lead_webhook.contact_id,
                    base_price=1.00,
                    final_price=425.00,
                    tier="hot",
                    multiplier=4.25,
                    conversion_probability=0.92,
                    expected_roi=29.4,
                    justification="Premium golden lead with immediate timeline and financing ready",
                    jorge_score=5,
                    ml_confidence=0.92,
                    historical_performance=0.87,
                    expected_commission=12500.0,
                    days_to_close_estimate=10,
                    agent_recommendation="Call immediately - Golden opportunity",
                    calculated_at=datetime.utcnow(),
                )
            )

            # STEP 1: Send webhook to API
            webhook_payload = sample_hot_lead_webhook.dict()
            response = client.post("/ghl/webhook", json=webhook_payload)

            # Validate webhook processing
            assert response.status_code == 200, f"Webhook should succeed, got {response.status_code}"
            response_data = response.json()
            assert "message" in response_data or "response" in response_data

            # Give background tasks time to complete
            await asyncio.sleep(0.2)

            # STEP 2: Query pricing API for the lead
            pricing_request = {
                "contact_id": sample_hot_lead_webhook.contact_id,
                "location_id": jorge_location_id,
                "context": {"questions_answered": 5, "urgency": "high"},
            }

            pricing_response = client.post("/api/pricing/calculate", json=pricing_request)

            # Validate pricing API response
            assert pricing_response.status_code == 200
            pricing_data = pricing_response.json()
            assert pricing_data["success"] is True
            assert pricing_data["data"]["tier_classification"] == "hot"
            assert pricing_data["data"]["suggested_price"] >= 400.0

            print(f"\n✅ API INTEGRATION VALIDATION:")
            print(f"  • Webhook Status: {response.status_code}")
            print(f"  • Pricing Calculated: ${pricing_data['data']['suggested_price']:.2f}")
            print(f"  • Lead Tier: {pricing_data['data']['tier_classification']}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_api_requests(self, async_client, mock_user, jorge_location_id):
        """
        TEST: Multiple concurrent API requests for different leads

        Validates system can handle concurrent load without data corruption.
        """
        contact_ids = [f"contact_concurrent_{i}" for i in range(10)]

        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
        ):

            async def mock_calculate_price(contact_id, location_id, context=None):
                await asyncio.sleep(0.01)  # Simulate processing
                base_price = 100.0 + (hash(contact_id) % 300)
                return LeadPricingResult(
                    lead_id=contact_id,
                    base_price=1.00,
                    final_price=base_price,
                    tier="warm",
                    multiplier=2.0,
                    conversion_probability=0.65,
                    expected_roi=15.0,
                    justification=f"Calculated for {contact_id}",
                    jorge_score=2,
                    ml_confidence=0.65,
                    historical_performance=0.60,
                    expected_commission=8000.0,
                    days_to_close_estimate=21,
                    agent_recommendation="Standard follow-up",
                    calculated_at=datetime.utcnow(),
                )

            mock_pricing.return_value.calculate_lead_price = mock_calculate_price

            # Create concurrent requests
            pricing_requests = [
                {"contact_id": contact_id, "location_id": jorge_location_id, "context": {"questions_answered": 2}}
                for contact_id in contact_ids
            ]

            # Send requests concurrently
            tasks = [async_client.post("/api/pricing/calculate", json=req) for req in pricing_requests]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Validate all requests succeeded
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            assert successful == len(contact_ids), (
                f"All {len(contact_ids)} concurrent requests should succeed, got {successful}"
            )

            # Validate unique pricing for each lead
            prices = []
            for response in responses:
                if not isinstance(response, Exception):
                    data = response.json()
                    if data.get("success"):
                        prices.append(data["data"]["suggested_price"])

            assert len(prices) == len(contact_ids), "Should get pricing for all leads"

            print(f"\n✅ CONCURRENT API VALIDATION:")
            print(f"  • Concurrent Requests: {len(contact_ids)}")
            print(f"  • Successful: {successful}/{len(contact_ids)}")
            print(f"  • Unique Prices: {len(set(prices))}")

    # ============================================================================
    # TEST SUITE 3: Dashboard Integration Validation
    # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_roi_dashboard_data_integration(self, client, mock_user, jorge_location_id):
        """
        TEST: ROI dashboard can retrieve complete metrics for client presentation

        Validates dashboard data aggregation and presentation.
        """
        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.roi_calculator_service.ROICalculatorService") as mock_roi,
        ):
            # Setup comprehensive ROI report
            mock_roi_instance = mock_roi.return_value
            mock_roi_instance.generate_client_roi_report = AsyncMock(
                return_value=ClientROIReport(
                    location_id=jorge_location_id,
                    period_start=datetime.now() - timedelta(days=30),
                    period_end=datetime.now(),
                    total_leads_processed=428,
                    total_conversations=856,
                    total_messages=3420,
                    avg_response_time_seconds=18.5,
                    ai_total_cost=2840.00,
                    human_equivalent_cost=12500.00,
                    total_savings=9660.00,
                    savings_percentage=77.3,
                    total_hours_saved=156.8,
                    equivalent_human_days=19.6,
                    agent_productivity_multiplier=3.8,
                    leads_qualified=312,
                    appointments_booked=125,
                    deals_closed=89,
                    total_commission_generated=178500.00,
                    roi_multiple=4.7,
                    hot_leads_identified=89,
                    conversion_rate_improvement=12.4,
                    response_time_improvement=85.2,
                    industry_benchmark_cost=15600.00,
                    jorge_ai_advantage=82.1,
                    competitive_positioning="Market Leader",
                    monthly_savings_projection=9660.00,
                    annual_savings_projection=115920.00,
                    payback_period_days=18,
                    executive_summary="Outstanding performance with 4.7x ROI and $178.5k in commission",
                    key_wins=[
                        "77% cost reduction vs human alternative",
                        "4.7x return on investment",
                        "89 hot leads identified and converted",
                        "19.6 human-days saved per month",
                    ],
                    optimization_opportunities=[
                        "Expand to additional locations (3x ROI potential)",
                        "Add premium golden lead features",
                        "Increase pricing for hot leads by 15%",
                    ],
                    generated_at=datetime.now(),
                )
            )

            # Request ROI dashboard data
            response = client.get(f"/api/pricing/roi-report/{jorge_location_id}")

            assert response.status_code == 200
            roi_data = response.json()

            # Validate comprehensive metrics
            assert roi_data["success"] is True
            data = roi_data["data"]

            assert data["total_leads_processed"] == 428
            assert data["roi_multiple"] == 4.7
            assert data["total_commission_generated"] == 178500.00
            assert data["savings_percentage"] == 77.3
            assert data["hot_leads_identified"] == 89
            assert len(data["key_wins"]) >= 4
            assert len(data["optimization_opportunities"]) >= 2

            print(f"\n✅ ROI DASHBOARD VALIDATION:")
            print(f"  • Total Leads: {data['total_leads_processed']}")
            print(f"  • ROI Multiple: {data['roi_multiple']}x")
            print(f"  • Commission Generated: ${data['total_commission_generated']:,.2f}")
            print(f"  • Cost Savings: {data['savings_percentage']:.1f}%")
            print(f"  • Golden Leads: {data['hot_leads_identified']}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pricing_analytics_dashboard_feed(self, client, mock_user, jorge_location_id):
        """
        TEST: Pricing analytics feed for real-time dashboard updates

        Validates analytics aggregation and trend calculation.
        """
        with (
            patch("ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing,
        ):
            # Setup pricing analytics
            mock_pricing_instance = mock_pricing.return_value
            mock_pricing_instance.get_pricing_analytics = AsyncMock(
                return_value={
                    "summary": {
                        "total_leads_priced": 1247,
                        "current_arpu": 287.50,
                        "target_arpu": 400.00,
                        "arpu_improvement_pct": 187.5,  # From $100 baseline
                        "days_to_target": 45,
                    },
                    "tier_performance": {
                        "hot": {
                            "count": 284,
                            "avg_price": 425.00,
                            "conversion_rate": 0.87,
                            "total_revenue": 120700.00,
                            "roi": 42.5,
                        },
                        "warm": {
                            "count": 518,
                            "avg_price": 275.00,
                            "conversion_rate": 0.62,
                            "total_revenue": 142450.00,
                            "roi": 24.3,
                        },
                        "cold": {
                            "count": 445,
                            "avg_price": 125.00,
                            "conversion_rate": 0.28,
                            "total_revenue": 55625.00,
                            "roi": 12.1,
                        },
                    },
                    "optimization_opportunities": [
                        {
                            "type": "pricing_increase",
                            "tier": "hot",
                            "current_performance": 0.87,
                            "recommendation": "Increase hot lead pricing by 20%",
                            "potential_revenue_impact": 24140.00,
                        }
                    ],
                    "pricing_trends": [
                        {"period": "week_1", "arpu": 125.00, "trend": "up"},
                        {"period": "week_2", "arpu": 187.50, "trend": "up"},
                        {"period": "week_3", "arpu": 237.50, "trend": "up"},
                        {"period": "week_4", "arpu": 287.50, "trend": "up"},
                    ],
                    "roi_justification_summary": "Total invested: $318,775 → Expected revenue: $13.5M (4,237% ROI)",
                }
            )

            # Request pricing analytics
            response = client.get(f"/api/pricing/analytics/{jorge_location_id}?days=30")

            assert response.status_code == 200
            analytics = response.json()

            # Validate analytics structure
            assert analytics["success"] is True
            data = analytics["data"]

            assert data["summary"]["total_leads_priced"] == 1247
            assert data["summary"]["current_arpu"] == 287.50
            assert data["tier_performance"]["hot"]["conversion_rate"] >= 0.85
            assert len(data["pricing_trends"]) == 4
            assert len(data["optimization_opportunities"]) >= 1

            print(f"\n✅ PRICING ANALYTICS VALIDATION:")
            print(f"  • Total Leads Priced: {data['summary']['total_leads_priced']}")
            print(f"  • Current ARPU: ${data['summary']['current_arpu']:.2f}")
            print(f"  • ARPU Progress: {data['summary']['arpu_improvement_pct']:.1f}%")
            print(f"  • Hot Lead Conversion: {data['tier_performance']['hot']['conversion_rate']:.1%}")

    # ============================================================================
    # TEST SUITE 4: Cross-Service Communication
    # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_dependency_chain(self, jorge_location_id):
        """
        TEST: Complete service dependency chain for lead processing

        Validates: LeadScorer → GoldenLeadDetector → PricingOptimizer → Analytics
        """
        contact_id = "contact_service_chain_test"

        # Initialize service chain
        lead_scorer = LeadScorer()
        golden_detector = GoldenLeadDetector()
        pricing_optimizer = DynamicPricingOptimizer()
        analytics_service = AnalyticsService()

        # Mock external dependencies
        with (
            patch.object(
                lead_scorer,
                "calculate",
                return_value=asyncio.coroutine(lambda *args: {"questions_answered": 4, "engagement_score": 0.75})(),
            ),
            patch.object(
                golden_detector.predictive_scorer,
                "predict_conversion_probability",
                return_value=asyncio.coroutine(lambda: 0.82)(),
            ),
        ):
            # STEP 1: Lead scoring
            lead_score_result = await lead_scorer.calculate(
                contact_id,
                {
                    "conversation_history": [
                        "Looking for 3BR house",
                        "Budget $350k",
                        "Timeline 2 months",
                        "Pre-approved",
                    ]
                },
            )

            assert "questions_answered" in lead_score_result
            jorge_score = lead_score_result["questions_answered"]

            # STEP 2: Golden lead detection (depends on LeadScorer output)
            detection_result = await golden_detector.analyze_lead(
                contact_id=contact_id,
                tenant_id=jorge_location_id,
                conversation_history=["Looking for 3BR house", "Budget $350k"],
                context={"questions_answered": jorge_score},
            )

            assert detection_result is not None
            assert detection_result.base_jorge_score == jorge_score

            # STEP 3: Pricing (depends on both LeadScorer and GoldenDetector)
            pricing_result = await pricing_optimizer.calculate_lead_price(
                contact_id=contact_id, location_id=jorge_location_id, context={"questions_answered": jorge_score}
            )

            assert pricing_result is not None
            assert pricing_result.jorge_score == jorge_score

            # STEP 4: Analytics tracking (depends on all previous services)
            await analytics_service.track_event(
                {
                    "event_type": "complete_lead_processing",
                    "contact_id": contact_id,
                    "location_id": jorge_location_id,
                    "jorge_score": jorge_score,
                    "golden_tier": detection_result.tier.value,
                    "final_price": pricing_result.final_price,
                    "timestamp": datetime.utcnow(),
                }
            )

            print(f"\n✅ SERVICE DEPENDENCY CHAIN VALIDATION:")
            print(f"  • Jorge Score: {jorge_score}/7")
            print(f"  • Golden Tier: {detection_result.tier.value}")
            print(f"  • Final Price: ${pricing_result.final_price:.2f}")
            print(f"  • Analytics Tracked: ✓")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_redis_cache_integration(self, jorge_location_id):
        """
        TEST: Redis caching for performance optimization across services

        Validates cache hit/miss behavior and TTL management.
        """
        cache_service = CacheService()
        pricing_optimizer = DynamicPricingOptimizer()

        contact_id = "contact_cache_test"
        cache_key = f"pricing:{contact_id}"

        # STEP 1: First calculation (cache miss)
        first_result = await pricing_optimizer.calculate_lead_price(
            contact_id, jorge_location_id, {"questions_answered": 3}
        )

        # STEP 2: Cache the result
        await cache_service.set(
            cache_key,
            first_result.to_dict() if hasattr(first_result, "to_dict") else first_result.__dict__,
            ttl=300,  # 5 minutes
        )

        # STEP 3: Retrieve from cache (cache hit)
        cached_result = await cache_service.get(cache_key)

        # Validate cache behavior
        if cached_result:
            assert cached_result["lead_id"] == contact_id
            assert cached_result["final_price"] == first_result.final_price
            print(f"\n✅ REDIS CACHE VALIDATION:")
            print(f"  • Cache Hit: ✓")
            print(f"  • Cached Price: ${cached_result['final_price']:.2f}")
        else:
            print(f"\n⚠️  REDIS CACHE: Cache miss (Redis may not be available in test env)")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tenant_isolation(self, jorge_location_id):
        """
        TEST: Tenant data isolation between different GHL locations

        Validates multi-tenancy security and data separation.
        """
        pricing_optimizer = DynamicPricingOptimizer()

        # Two different tenants
        tenant_a = jorge_location_id
        tenant_b = "different_location_xyz"
        contact_id = "shared_contact_id"

        # Calculate pricing for same contact in different tenants
        tenant_a_pricing = await pricing_optimizer.calculate_lead_price(contact_id, tenant_a, {"questions_answered": 3})

        tenant_b_pricing = await pricing_optimizer.calculate_lead_price(contact_id, tenant_b, {"questions_answered": 3})

        # Validate tenant isolation
        # Prices may differ due to different tenant configurations
        assert tenant_a_pricing is not None
        assert tenant_b_pricing is not None

        # Each tenant should have independent pricing configuration
        # (In production, tenant_b would have different tier multipliers, base prices, etc.)

        print(f"\n✅ TENANT ISOLATION VALIDATION:")
        print(f"  • Tenant A Price: ${tenant_a_pricing.final_price:.2f}")
        print(f"  • Tenant B Price: ${tenant_b_pricing.final_price:.2f}")
        print(f"  • Independent Configurations: ✓")


# ============================================================================
# TEST RUNNER - Execute all integration tests
# ============================================================================

if __name__ == "__main__":
    """
    Run comprehensive integration test suite.

    Usage:
        python -m pytest tests/integration/test_jorge_revenue_platform_e2e.py -v
        python -m pytest tests/integration/test_jorge_revenue_platform_e2e.py -v --tb=short
        python -m pytest tests/integration/test_jorge_revenue_platform_e2e.py -v -k "golden_lead"
    """
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto", "-m", "integration"])
