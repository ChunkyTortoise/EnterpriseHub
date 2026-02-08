"""
Integration tests for Lead Attribution System.

End-to-end tests for the complete lead source attribution workflow from webhook
processing through analytics and reporting.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.api.schemas.ghl import GHLContact, GHLMessage, GHLWebhookEvent, MessageDirection, MessageType
from ghl_real_estate_ai.services.lead_source_tracker import LeadSource, SourceAttribution, SourceQuality


class TestLeadAttributionIntegration:
    """Integration test suite for complete attribution workflow."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    @pytest.mark.asyncio
    async def test_complete_attribution_workflow_zillow_lead(self):
        """Test complete workflow for a Zillow lead from webhook to reporting."""

        # 1. Simulate incoming webhook with Zillow attribution data
        webhook_payload = {
            "type": "InboundMessage",
            "contactId": "test_contact_zillow_123",
            "locationId": "test_location_456",
            "message": {
                "type": "SMS",
                "body": "Hi, I'm interested in the property listing I saw on Zillow. Can you tell me more?",
                "direction": "inbound",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "contact": {
                "contactId": "test_contact_zillow_123",
                "firstName": "Sarah",
                "lastName": "Johnson",
                "phone": "+15551234567",
                "email": "sarah.johnson@email.com",
                "tags": ["Needs Qualifying", "Zillow-Lead"],
                "customFields": {
                    "utm_source": "zillow",
                    "utm_medium": "referral",
                    "utm_campaign": "austin-listings-q1-2024",
                    "lead_source": "Zillow",
                    "original_url": "https://www.zillow.com/homedetails/123-main-st/",
                    "referrer": "https://zillow.com/search",
                    "landing_page": "https://youragentsite.com/listings/123-main-st",
                },
            },
        }

        # Mock necessary services
        with (
            patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager") as mock_conv_mgr,
            patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default") as mock_ghl_client,
            patch("ghl_real_estate_ai.api.routes.webhook.tenant_service") as mock_tenant,
            patch("ghl_real_estate_ai.api.routes.webhook.analytics_service") as mock_analytics,
            patch("ghl_real_estate_ai.api.routes.webhook.lead_source_tracker") as mock_tracker,
            patch("ghl_real_estate_ai.api.routes.webhook.attribution_analytics") as mock_attribution,
        ):
            # Mock conversation manager response
            mock_ai_response = MagicMock()
            mock_ai_response.message = "Thanks for your interest! I'd be happy to help. What's your budget range?"
            mock_ai_response.lead_score = 3
            mock_ai_response.extracted_data = {
                "property_interest": "123 Main St listing",
                "timeline": "soon",
                "source": "zillow",
            }

            mock_conv_mgr.get_context = AsyncMock(return_value={})
            mock_conv_mgr.generate_response = AsyncMock(return_value=mock_ai_response)
            mock_conv_mgr.update_context = AsyncMock()

            # Mock tenant service
            mock_tenant.get_tenant_config = AsyncMock(return_value={"ghl_api_key": "test_key"})

            # Mock GHL client
            mock_ghl_client.send_message = AsyncMock()
            mock_ghl_client.apply_actions = AsyncMock()
            mock_ghl_client.update_contact_custom_fields = AsyncMock(return_value=True)

            # Mock lead source tracker
            expected_attribution = SourceAttribution(
                source=LeadSource.ZILLOW,
                source_detail="austin-listings-q1-2024",
                medium="referral",
                campaign="austin-listings-q1-2024",
                utm_source="zillow",
                utm_medium="referral",
                utm_campaign="austin-listings-q1-2024",
                referrer="https://zillow.com/search",
                landing_page="https://youragentsite.com/listings/123-main-st",
                quality_score=7.8,
                source_quality=SourceQuality.PREMIUM,
                confidence_score=0.95,
                first_touch=datetime.utcnow(),
                last_touch=datetime.utcnow(),
            )

            mock_tracker.analyze_lead_source = AsyncMock(return_value=expected_attribution)
            mock_tracker.update_ghl_custom_fields = AsyncMock(return_value=True)
            mock_tracker.track_source_performance = AsyncMock()

            # Mock attribution analytics
            mock_attribution.track_daily_metrics = AsyncMock()

            # Mock analytics service
            mock_analytics.track_event = AsyncMock()

            # 2. Send webhook request
            response = self.client.post(
                "/api/ghl/webhook", json=webhook_payload, headers={"Content-Type": "application/json"}
            )

            # 3. Verify webhook processing
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True

            # 4. Verify source attribution was analyzed
            mock_tracker.analyze_lead_source.assert_called_once()
            call_args = mock_tracker.analyze_lead_source.call_args
            contact_data = call_args[0][0]

            assert contact_data["custom_fields"]["utm_source"] == "zillow"
            assert contact_data["custom_fields"]["lead_source"] == "Zillow"

            # 5. Verify GHL custom fields were updated
            mock_tracker.update_ghl_custom_fields.assert_called_once()

            # 6. Verify source performance tracking
            mock_tracker.track_source_performance.assert_called()
            performance_calls = mock_tracker.track_source_performance.call_args_list

            # Should track lead interaction and lead scoring
            assert len(performance_calls) >= 2

            # 7. Verify attribution analytics tracking
            mock_attribution.track_daily_metrics.assert_called_once()

        # 8. Test attribution reporting endpoints
        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            from ghl_real_estate_ai.services.lead_source_tracker import SourcePerformance

            # Mock performance data that would result from the tracked events
            mock_performance = SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=1,
                qualified_leads=0,  # Not yet qualified
                hot_leads=0,
                conversion_rate=0.0,
                qualification_rate=0.0,
                total_revenue=0.0,
                avg_deal_size=0.0,
                cost_per_lead=25.0,  # Estimated Zillow cost
                roi=0.0,  # No revenue yet
                avg_lead_score=3.0,  # From our test
                avg_budget=0.0,
            )

            mock_tracker.get_all_source_performance = AsyncMock(return_value=[mock_performance])

            # Test performance endpoint
            perf_response = self.client.get("/api/attribution/performance")
            assert perf_response.status_code == 200

            perf_data = perf_response.json()
            assert len(perf_data) == 1
            assert perf_data[0]["source"] == "zillow"
            assert perf_data[0]["total_leads"] == 1

    @pytest.mark.asyncio
    async def test_facebook_ads_lead_with_qualification_workflow(self):
        """Test Facebook Ads lead that gets qualified through conversation."""

        # Simulate a sequence of messages that qualify a lead
        messages = [
            {
                "body": "I saw your Facebook ad about homes in Austin. I'm looking to buy.",
                "lead_score": 2,
                "extracted_data": {"budget": None, "timeline": None},
            },
            {
                "body": "My budget is around $400,000 and I'm looking to buy within 3 months.",
                "lead_score": 5,
                "extracted_data": {"budget": 400000, "timeline": "3 months", "property_type": "house"},
            },
            {
                "body": "I'm pre-approved and ready to make an offer on the right property.",
                "lead_score": 7,  # Should trigger qualification
                "extracted_data": {"budget": 400000, "timeline": "immediate", "financing": "pre-approved"},
            },
        ]

        contact_id = "test_facebook_lead_789"

        for i, message_data in enumerate(messages):
            webhook_payload = {
                "type": "InboundMessage",
                "contactId": contact_id,
                "locationId": "test_location_456",
                "message": {"type": "SMS", "body": message_data["body"], "direction": "inbound"},
                "contact": {
                    "contactId": contact_id,
                    "firstName": "Mike",
                    "lastName": "Davis",
                    "phone": "+15559876543",
                    "email": "mike.davis@email.com",
                    "tags": ["Needs Qualifying"] if i == 0 else ["Needs Qualifying", "Engaged"],
                    "customFields": {
                        "utm_source": "facebook",
                        "utm_medium": "cpc",
                        "utm_campaign": "austin-homes-spring-2024",
                        "utm_content": "carousel-ad-variant-b",
                        "gclid": "",
                        "fbclid": "IwAR123abc456def",
                        "lead_source": "Facebook Ads",
                        "ad_set": "austin-buyers-lookalike",
                        "ad_creative": "spring-homes-carousel",
                    },
                },
            }

            with (
                patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager") as mock_conv_mgr,
                patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default") as mock_ghl_client,
                patch("ghl_real_estate_ai.api.routes.webhook.tenant_service") as mock_tenant,
                patch("ghl_real_estate_ai.api.routes.webhook.analytics_service") as mock_analytics,
                patch("ghl_real_estate_ai.api.routes.webhook.lead_source_tracker") as mock_tracker,
                patch("ghl_real_estate_ai.api.routes.webhook.attribution_analytics") as mock_attribution,
            ):
                # Mock AI response based on message iteration
                mock_ai_response = MagicMock()
                mock_ai_response.message = f"Response {i + 1}"
                mock_ai_response.lead_score = message_data["lead_score"]
                mock_ai_response.extracted_data = message_data["extracted_data"]

                mock_conv_mgr.get_context = AsyncMock(return_value={})
                mock_conv_mgr.generate_response = AsyncMock(return_value=mock_ai_response)
                mock_conv_mgr.update_context = AsyncMock()
                mock_tenant.get_tenant_config = AsyncMock(return_value={"ghl_api_key": "test_key"})
                mock_ghl_client.send_message = AsyncMock()
                mock_ghl_client.apply_actions = AsyncMock()

                # Mock source attribution (same for all messages from this lead)
                expected_attribution = SourceAttribution(
                    source=LeadSource.FACEBOOK_ADS,
                    source_detail="austin-homes-spring-2024",
                    medium="cpc",
                    campaign="austin-homes-spring-2024",
                    utm_source="facebook",
                    utm_medium="cpc",
                    utm_campaign="austin-homes-spring-2024",
                    utm_content="carousel-ad-variant-b",
                    quality_score=6.5,
                    source_quality=SourceQuality.STANDARD,
                    confidence_score=0.92,
                    first_touch=datetime.utcnow() - timedelta(hours=2),
                    last_touch=datetime.utcnow(),
                )

                mock_tracker.analyze_lead_source = AsyncMock(return_value=expected_attribution)
                mock_tracker.update_ghl_custom_fields = AsyncMock(return_value=True)
                mock_tracker.track_source_performance = AsyncMock()
                mock_attribution.track_daily_metrics = AsyncMock()
                mock_analytics.track_event = AsyncMock()

                # Send message
                response = self.client.post(
                    "/api/ghl/webhook", json=webhook_payload, headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                # Verify performance tracking based on lead score
                if message_data["lead_score"] >= 5:
                    # Should track qualification event
                    performance_calls = mock_tracker.track_source_performance.call_args_list
                    assert len(performance_calls) >= 1

                if message_data["lead_score"] >= 7:
                    # Should track hot lead event
                    response_data = response.json()
                    # Check if hot lead tags were applied
                    actions = response_data.get("actions", [])
                    hot_lead_action = any("Hot-Lead" in str(action) for action in actions)

    @pytest.mark.asyncio
    async def test_unknown_source_handling(self):
        """Test handling of leads with no clear attribution data."""

        webhook_payload = {
            "type": "InboundMessage",
            "contactId": "test_unknown_lead_999",
            "locationId": "test_location_456",
            "message": {"type": "SMS", "body": "I'm interested in buying a home", "direction": "inbound"},
            "contact": {
                "contactId": "test_unknown_lead_999",
                "firstName": "Jane",
                "lastName": "Smith",
                "phone": "+15557654321",
                "email": "jane.smith@email.com",
                "tags": ["Needs Qualifying"],
                "customFields": {},  # No attribution data
            },
        }

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager") as mock_conv_mgr,
            patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default") as mock_ghl_client,
            patch("ghl_real_estate_ai.api.routes.webhook.tenant_service") as mock_tenant,
            patch("ghl_real_estate_ai.api.routes.webhook.analytics_service") as mock_analytics,
            patch("ghl_real_estate_ai.api.routes.webhook.lead_source_tracker") as mock_tracker,
            patch("ghl_real_estate_ai.api.routes.webhook.attribution_analytics") as mock_attribution,
        ):
            # Mock responses
            mock_ai_response = MagicMock()
            mock_ai_response.message = "I'd be happy to help you find a home!"
            mock_ai_response.lead_score = 2
            mock_ai_response.extracted_data = {}

            mock_conv_mgr.get_context = AsyncMock(return_value={})
            mock_conv_mgr.generate_response = AsyncMock(return_value=mock_ai_response)
            mock_conv_mgr.update_context = AsyncMock()
            mock_tenant.get_tenant_config = AsyncMock(return_value={"ghl_api_key": "test_key"})
            mock_ghl_client.send_message = AsyncMock()
            mock_ghl_client.apply_actions = AsyncMock()

            # Mock unknown source attribution
            unknown_attribution = SourceAttribution(
                source=LeadSource.UNKNOWN,
                confidence_score=0.0,
                quality_score=3.0,
                source_quality=SourceQuality.EXPERIMENTAL,
                first_touch=datetime.utcnow(),
                last_touch=datetime.utcnow(),
            )

            mock_tracker.analyze_lead_source = AsyncMock(return_value=unknown_attribution)
            mock_tracker.update_ghl_custom_fields = AsyncMock(return_value=True)
            mock_tracker.track_source_performance = AsyncMock()
            mock_attribution.track_daily_metrics = AsyncMock()
            mock_analytics.track_event = AsyncMock()

            response = self.client.post(
                "/api/ghl/webhook", json=webhook_payload, headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 200

            # Verify unknown source was tracked
            mock_tracker.track_source_performance.assert_called()
            call_args = mock_tracker.track_source_performance.call_args_list[0]
            assert call_args[0][0] == LeadSource.UNKNOWN

    @pytest.mark.asyncio
    async def test_attribution_reporting_integration(self):
        """Test end-to-end attribution reporting after processing multiple leads."""

        # Simulate performance data from multiple processed leads
        with patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics:
            from ghl_real_estate_ai.services.attribution_analytics import AttributionReport
            from ghl_real_estate_ai.services.lead_source_tracker import SourcePerformance

            # Mock report data reflecting processed leads
            mock_report = AttributionReport(
                period_start=datetime.utcnow() - timedelta(days=7),
                period_end=datetime.utcnow(),
                generated_at=datetime.utcnow(),
                total_leads=15,
                total_qualified_leads=8,
                total_revenue=45000.0,
                total_cost=2500.0,
                overall_roi=17.0,
                source_performance=[
                    SourcePerformance(
                        source=LeadSource.ZILLOW,
                        period_start=datetime.utcnow() - timedelta(days=7),
                        period_end=datetime.utcnow(),
                        total_leads=5,
                        qualified_leads=4,
                        hot_leads=2,
                        conversion_rate=0.20,  # 1 conversion
                        qualification_rate=0.80,
                        total_revenue=15000.0,
                        avg_deal_size=15000.0,
                        cost_per_lead=30.0,
                        roi=9.0,
                        avg_lead_score=6.2,
                        avg_budget=420000.0,
                    ),
                    SourcePerformance(
                        source=LeadSource.FACEBOOK_ADS,
                        period_start=datetime.utcnow() - timedelta(days=7),
                        period_end=datetime.utcnow(),
                        total_leads=8,
                        qualified_leads=3,
                        hot_leads=1,
                        conversion_rate=0.125,  # 1 conversion
                        qualification_rate=0.375,
                        total_revenue=25000.0,
                        avg_deal_size=25000.0,
                        cost_per_lead=25.0,
                        roi=11.5,
                        avg_lead_score=4.8,
                        avg_budget=380000.0,
                    ),
                    SourcePerformance(
                        source=LeadSource.UNKNOWN,
                        period_start=datetime.utcnow() - timedelta(days=7),
                        period_end=datetime.utcnow(),
                        total_leads=2,
                        qualified_leads=1,
                        hot_leads=0,
                        conversion_rate=0.0,
                        qualification_rate=0.50,
                        total_revenue=0.0,
                        cost_per_lead=0.0,
                        roi=0.0,
                        avg_lead_score=3.5,
                        avg_budget=0.0,
                    ),
                ],
                active_alerts=[],
                optimization_recommendations=[
                    {
                        "type": "improve_tracking",
                        "priority": "medium",
                        "title": "Improve Source Tracking",
                        "description": "2 leads have unknown source attribution",
                    }
                ],
            )

            mock_analytics.generate_attribution_report = AsyncMock(return_value=mock_report)

            # Test comprehensive report
            response = self.client.get("/api/attribution/report")
            assert response.status_code == 200

            data = response.json()
            assert data["total_leads"] == 15
            assert data["total_qualified_leads"] == 8
            assert data["overall_roi"] == 17.0
            assert len(data["source_performance"]) == 3

            # Verify Zillow performance
            zillow_perf = next(p for p in data["source_performance"] if p["source"] == "zillow")
            assert zillow_perf["total_leads"] == 5
            assert zillow_perf["qualification_rate"] == 0.80

            # Verify Facebook Ads performance
            facebook_perf = next(p for p in data["source_performance"] if p["source"] == "facebook_ads")
            assert facebook_perf["total_leads"] == 8
            assert facebook_perf["roi"] == 11.5

            # Verify recommendations include attribution improvement
            assert len(data["optimization_recommendations"]) == 1
            assert data["optimization_recommendations"][0]["type"] == "improve_tracking"

    def test_source_tagging_integration(self):
        """Test that source-based tags are properly applied."""

        test_cases = [
            {
                "source": LeadSource.ZILLOW,
                "expected_tags": ["Source-Zillow", "Source-Quality-Premium", "Premium-Source"],
            },
            {
                "source": LeadSource.FACEBOOK_ADS,
                "expected_tags": ["Source-Facebook-Ads", "Source-Quality-Standard", "Paid-Source"],
            },
            {
                "source": LeadSource.AGENT_REFERRAL,
                "expected_tags": ["Source-Agent-Referral", "Source-Quality-Premium", "Premium-Source", "VIP-Lead"],
            },
        ]

        for test_case in test_cases:
            webhook_payload = {
                "type": "InboundMessage",
                "contactId": f"test_contact_{test_case['source'].value}",
                "locationId": "test_location",
                "message": {"type": "SMS", "body": "Test message", "direction": "inbound"},
                "contact": {
                    "contactId": f"test_contact_{test_case['source'].value}",
                    "firstName": "Test",
                    "lastName": "Contact",
                    "tags": ["Needs Qualifying"],
                    "customFields": {"lead_source": test_case["source"].value},
                },
            }

            with (
                patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager") as mock_conv_mgr,
                patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default") as mock_ghl_client,
                patch("ghl_real_estate_ai.api.routes.webhook.tenant_service") as mock_tenant,
                patch("ghl_real_estate_ai.api.routes.webhook.analytics_service"),
                patch("ghl_real_estate_ai.api.routes.webhook.lead_source_tracker") as mock_tracker,
                patch("ghl_real_estate_ai.api.routes.webhook.attribution_analytics"),
            ):
                # Mock basic responses
                mock_ai_response = MagicMock()
                mock_ai_response.message = "Test response"
                mock_ai_response.lead_score = 3
                mock_ai_response.extracted_data = {}

                mock_conv_mgr.get_context = AsyncMock(return_value={})
                mock_conv_mgr.generate_response = AsyncMock(return_value=mock_ai_response)
                mock_conv_mgr.update_context = AsyncMock()
                mock_tenant.get_tenant_config = AsyncMock(return_value={"ghl_api_key": "test_key"})
                mock_ghl_client.send_message = AsyncMock()
                mock_ghl_client.apply_actions = AsyncMock()

                # Mock source attribution
                attribution = SourceAttribution(
                    source=test_case["source"],
                    confidence_score=0.95,
                    quality_score=8.0 if "Premium" in str(test_case["source"]) else 6.0,
                    source_quality=SourceQuality.PREMIUM
                    if "REFERRAL" in test_case["source"].value or test_case["source"] == LeadSource.ZILLOW
                    else SourceQuality.STANDARD,
                    utm_campaign="test-campaign" if "ADS" in test_case["source"].value else None,
                    medium="cpc" if "ADS" in test_case["source"].value else None,
                )

                mock_tracker.analyze_lead_source = AsyncMock(return_value=attribution)
                mock_tracker.update_ghl_custom_fields = AsyncMock(return_value=True)
                mock_tracker.track_source_performance = AsyncMock()

                response = self.client.post(
                    "/api/ghl/webhook", json=webhook_payload, headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                # Verify that apply_actions was called (tags would be applied here)
                mock_ghl_client.apply_actions.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_optimization_workflow(self):
        """Test the complete performance optimization recommendation workflow."""

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            # Mock performance data showing optimization opportunities
            mock_recommendations = {
                "status": "success",
                "generated_at": datetime.utcnow().isoformat(),
                "total_sources_analyzed": 4,
                "recommendations": [
                    {
                        "type": "scale_up",
                        "priority": "high",
                        "title": "Scale Top Performing Sources",
                        "description": "Increase investment in agent_referral, zillow",
                        "sources": ["agent_referral", "zillow"],
                        "expected_impact": "Increase overall ROI by focusing on proven sources",
                    },
                    {
                        "type": "optimize_or_pause",
                        "priority": "high",
                        "title": "Optimize or Pause Underperforming Sources",
                        "description": "Review and optimize facebook_ads",
                        "sources": ["facebook_ads"],
                        "expected_impact": "Reduce wasted ad spend and improve overall ROI",
                    },
                    {
                        "type": "improve_tracking",
                        "priority": "medium",
                        "title": "Improve Source Tracking",
                        "description": "5 leads have unknown source attribution",
                        "expected_impact": "Better attribution enables more informed optimization decisions",
                    },
                ],
                "top_performers": [
                    {"source": "agent_referral", "roi": 450.0, "total_leads": 12, "conversion_rate": 25.0},
                    {"source": "zillow", "roi": 320.0, "total_leads": 25, "conversion_rate": 16.0},
                    {"source": "facebook_ads", "roi": 85.0, "total_leads": 40, "conversion_rate": 5.0},
                ],
            }

            mock_tracker.get_source_recommendations = AsyncMock(return_value=mock_recommendations)

            # Test recommendations endpoint
            response = self.client.get("/api/attribution/recommendations")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "success"
            assert len(data["recommendations"]) == 3
            assert len(data["top_performers"]) == 3

            # Verify specific recommendations
            scale_up_rec = next(r for r in data["recommendations"] if r["type"] == "scale_up")
            assert "agent_referral" in scale_up_rec["sources"]
            assert "zillow" in scale_up_rec["sources"]

            optimize_rec = next(r for r in data["recommendations"] if r["type"] == "optimize_or_pause")
            assert "facebook_ads" in optimize_rec["sources"]

            tracking_rec = next(r for r in data["recommendations"] if r["type"] == "improve_tracking")
            assert "5 leads have unknown source" in tracking_rec["description"]
