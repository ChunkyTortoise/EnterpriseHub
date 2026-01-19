"""
Test suite for Jorge's Advanced Features API Routes.

Tests all endpoints for:
- Voice AI Phone Integration
- Automated Marketing Campaign Generator
- Client Retention & Referral Automation
- Advanced Market Prediction Analytics
- Integration & Dashboard endpoints
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.services.voice_ai_handler import (
    VoiceCallContext,
    VoiceResponse,
    CallType,
    CallPriority,
    ConversationStage,
)
from ghl_real_estate_ai.services.automated_marketing_engine import (
    CampaignBrief,
    CampaignTrigger,
    ContentFormat,
    CampaignStatus,
)
from ghl_real_estate_ai.services.client_retention_engine import (
    ClientProfile,
    LifeEventType,
)
from ghl_real_estate_ai.services.market_prediction_engine import (
    PredictionResult,
    TimeHorizon,
)

client = TestClient(app)


# ================== VOICE AI TESTS ==================

class TestVoiceAIEndpoints:
    """Test voice AI API endpoints."""

    def test_start_voice_call_success(self):
        """Test successful voice call start."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.get_voice_ai_handler') as mock_handler:
            mock_handler.return_value.handle_incoming_call = AsyncMock(
                return_value=VoiceCallContext(
                    call_id="test-call-123",
                    phone_number="+19095551234"
                )
            )

            response = client.post(
                "/api/jorge-advanced/voice/start-call",
                json={
                    "phone_number": "+19095551234",
                    "caller_name": "John Doe"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["call_id"] == "test-call-123"
            assert data["status"] == "active"

    def test_start_voice_call_invalid_phone(self):
        """Test voice call start with invalid phone number."""
        response = client.post(
            "/api/jorge-advanced/voice/start-call",
            json={
                "phone_number": "",
                "caller_name": "John Doe"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_process_voice_input_success(self):
        """Test successful voice input processing."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.get_voice_ai_handler') as mock_handler:
            mock_handler.return_value.process_voice_input = AsyncMock(
                return_value=VoiceResponse(
                    text="Hello! I'm Jorge Martinez, your Inland Empire specialist.",
                    emotion="professional",
                    confidence=0.95
                )
            )

            response = client.post(
                "/api/jorge-advanced/voice/process-input",
                json={
                    "call_id": "test-call-123",
                    "speech_text": "Hi, I'm looking for a real estate agent",
                    "audio_confidence": 0.9
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "Jorge Martinez" in data["text"]
            assert data["emotion"] == "professional"

    def test_end_voice_call_success(self):
        """Test successful voice call completion."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.get_voice_ai_handler') as mock_handler:
            mock_handler.return_value.handle_call_completion = AsyncMock(
                return_value={
                    "call_id": "test-call-123",
                    "duration": 180,
                    "qualification_score": 75,
                    "transfer_to_jorge": True,
                    "lead_quality": "high",
                    "extracted_info": {"employer": "Amazon"},
                    "summary": "High-quality lead with relocation needs"
                }
            )

            response = client.post("/api/jorge-advanced/voice/end-call/test-call-123")

            assert response.status_code == 200
            data = response.json()
            assert data["call_id"] == "test-call-123"
            assert data["qualification_score"] == 75
            assert data["transfer_to_jorge"] is True

    def test_get_voice_analytics_success(self):
        """Test voice analytics retrieval."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.get_voice_ai_handler') as mock_handler:
            mock_handler.return_value.get_call_analytics = AsyncMock(
                return_value={
                    "total_calls": 45,
                    "avg_qualification_score": 68,
                    "transfer_rate": 0.35,
                    "top_industries": ["healthcare", "logistics"]
                }
            )

            response = client.get("/api/jorge-advanced/voice/analytics?days=7")

            assert response.status_code == 200
            data = response.json()
            assert data["analytics"]["total_calls"] == 45
            assert "top_industries" in data["analytics"]


# ================== MARKETING AUTOMATION TESTS ==================

class TestMarketingAutomationEndpoints:
    """Test marketing automation API endpoints."""

    def test_create_automated_campaign_success(self):
        """Test successful campaign creation."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.AutomatedMarketingEngine') as mock_engine:
            mock_engine.return_value.create_campaign_from_trigger = AsyncMock(
                return_value=CampaignBrief(
                    campaign_id="campaign-123",
                    name="New Listing Campaign - Etiwanda Heights",
                    trigger=CampaignTrigger.NEW_LISTING,
                    target_audience={"location": "Rancho Cucamonga"},
                    objectives=["Generate qualified leads", "Increase property visibility"]
                )
            )

            response = client.post(
                "/api/jorge-advanced/marketing/create-campaign",
                json={
                    "trigger_type": "new_listing",
                    "target_audience": {"location": "Rancho Cucamonga"},
                    "campaign_objectives": ["Generate qualified leads"],
                    "content_formats": ["email", "social_media"],
                    "budget_range": [1000, 5000]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["campaign_id"] == "campaign-123"
            assert "Etiwanda" in data["name"]

    def test_get_campaign_content_success(self):
        """Test campaign content retrieval."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.AutomatedMarketingEngine') as mock_engine:
            mock_engine.return_value.get_campaign_content = AsyncMock(
                return_value={
                    "email": {
                        "subject": "New Listing Alert in Etiwanda",
                        "content": "Jorge Martinez here with an exclusive listing..."
                    },
                    "social_media": {
                        "caption": "Just listed! Beautiful home in Etiwanda Heights...",
                        "hashtags": ["#RanchoCucamonga", "#EtiwandaHomes"]
                    }
                }
            )

            response = client.get("/api/jorge-advanced/marketing/campaigns/campaign-123/content")

            assert response.status_code == 200
            data = response.json()
            assert "email" in data["content"]
            assert "Jorge Martinez" in data["content"]["email"]["content"]

    def test_get_campaign_performance_success(self):
        """Test campaign performance metrics."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.AutomatedMarketingEngine') as mock_engine:
            mock_engine.return_value.get_campaign_performance = AsyncMock(
                return_value={
                    "impressions": 2500,
                    "clicks": 125,
                    "conversions": 8,
                    "ctr": 0.05,
                    "conversion_rate": 0.064,
                    "roi": 3.2,
                    "cost_per_lead": 187.50,
                    "lead_quality_score": 0.78
                }
            )

            response = client.get("/api/jorge-advanced/marketing/campaigns/campaign-123/performance")

            assert response.status_code == 200
            data = response.json()
            assert data["impressions"] == 2500
            assert data["roi"] == 3.2

    def test_start_ab_test_success(self):
        """Test A/B test initiation."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.AutomatedMarketingEngine') as mock_engine:
            mock_engine.return_value.start_ab_test = AsyncMock(
                return_value="ab-test-456"
            )

            response = client.post(
                "/api/jorge-advanced/marketing/ab-test/campaign-123",
                json={
                    "test_name": "Subject Line Test",
                    "variants": {
                        "A": {"subject": "New Listing Alert"},
                        "B": {"subject": "Exclusive Property Available"}
                    },
                    "metric": "open_rate",
                    "duration_days": 7
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["test_id"] == "ab-test-456"
            assert data["status"] == "active"


# ================== CLIENT RETENTION TESTS ==================

class TestClientRetentionEndpoints:
    """Test client retention API endpoints."""

    def test_update_client_lifecycle_success(self):
        """Test client lifecycle update."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.ClientRetentionEngine') as mock_engine:
            mock_engine.return_value.detect_life_event = AsyncMock()

            response = client.post(
                "/api/jorge-advanced/retention/update-lifecycle",
                json={
                    "client_id": "client-123",
                    "life_event": "job_change",
                    "event_context": {
                        "new_employer": "Amazon",
                        "location_change": "possible",
                        "timeline": "3_months"
                    }
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["client_id"] == "client-123"
            assert data["life_event"] == "job_change"

    def test_track_referral_success(self):
        """Test referral tracking."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.ClientRetentionEngine') as mock_engine:
            mock_engine.return_value.process_referral = AsyncMock(
                return_value="referral-789"
            )

            response = client.post(
                "/api/jorge-advanced/retention/track-referral",
                json={
                    "referrer_client_id": "client-123",
                    "referred_contact_info": {
                        "name": "Jane Smith",
                        "phone": "+19095554321",
                        "email": "jane@example.com"
                    },
                    "referral_source": "word_of_mouth",
                    "context": {
                        "relationship": "coworker",
                        "reason": "relocation"
                    }
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["referral_id"] == "referral-789"
            assert data["status"] == "tracked"

    def test_get_client_engagement_success(self):
        """Test client engagement retrieval."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.ClientRetentionEngine') as mock_engine:
            mock_engine.return_value.get_client_profile = AsyncMock(
                return_value=ClientProfile(
                    client_id="client-123",
                    total_interactions=25,
                    last_interaction=datetime.now() - timedelta(days=5),
                    referrals_made=3,
                    lifetime_value=450000.0
                )
            )
            mock_engine.return_value.calculate_engagement_score = AsyncMock(
                return_value={
                    "score": 0.85,
                    "retention_probability": 0.92
                }
            )

            response = client.get("/api/jorge-advanced/retention/client/client-123/engagement")

            assert response.status_code == 200
            data = response.json()
            assert data["client_id"] == "client-123"
            assert data["engagement_score"] == 0.85
            assert data["referrals_made"] == 3

    def test_get_retention_analytics_success(self):
        """Test retention analytics retrieval."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.ClientRetentionEngine') as mock_engine:
            mock_engine.return_value.get_retention_analytics = AsyncMock(
                return_value={
                    "total_clients": 150,
                    "active_clients": 120,
                    "retention_rate": 0.8,
                    "avg_referrals_per_client": 2.1,
                    "lifetime_value_avg": 320000
                }
            )

            response = client.get("/api/jorge-advanced/retention/analytics?days=30")

            assert response.status_code == 200
            data = response.json()
            assert data["analytics"]["retention_rate"] == 0.8
            assert data["period_days"] == 30


# ================== MARKET PREDICTION TESTS ==================

class TestMarketPredictionEndpoints:
    """Test market prediction API endpoints."""

    def test_analyze_market_success(self):
        """Test market analysis."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.MarketPredictionEngine') as mock_engine:
            mock_engine.return_value.predict_price_appreciation = AsyncMock(
                return_value=PredictionResult(
                    neighborhood="Etiwanda",
                    time_horizon=TimeHorizon.ONE_YEAR,
                    predicted_appreciation=0.08,
                    confidence_level=0.75,
                    supporting_factors=[
                        "New Amazon distribution center",
                        "School district improvements",
                        "Infrastructure upgrades"
                    ]
                )
            )

            response = client.post(
                "/api/jorge-advanced/market/analyze",
                json={
                    "neighborhood": "Etiwanda",
                    "time_horizon": "1_year",
                    "property_type": "single_family",
                    "price_range": [600000, 800000]
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["neighborhood"] == "Etiwanda"
            assert data["predicted_appreciation"] == 0.08

    def test_find_investment_opportunities_success(self):
        """Test investment opportunity analysis."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.MarketPredictionEngine') as mock_engine:
            mock_engine.return_value.identify_investment_opportunities = AsyncMock(
                return_value=[
                    {
                        "address": "123 Vineyard Ave, Rancho Cucamonga",
                        "predicted_roi": 0.12,
                        "risk_score": 0.3,
                        "appreciation_forecast": 0.06,
                        "cash_flow_potential": 850
                    }
                ]
            )

            response = client.post(
                "/api/jorge-advanced/market/investment-opportunities",
                json={
                    "client_budget": 750000,
                    "risk_tolerance": "medium",
                    "investment_goals": ["cash_flow", "appreciation"],
                    "time_horizon": "2_years"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["opportunities"]) == 1
            assert data["opportunities"][0]["predicted_roi"] == 0.12

    def test_get_market_trends_success(self):
        """Test market trends retrieval."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.MarketPredictionEngine') as mock_engine:
            mock_engine.return_value.get_market_trends = AsyncMock(
                return_value={
                    "historical_prices": [650000, 680000, 705000],
                    "predicted_prices": [720000, 735000, 750000],
                    "trend_direction": "upward",
                    "market_velocity": 0.15
                }
            )

            response = client.get("/api/jorge-advanced/market/trends/Etiwanda?months=12")

            assert response.status_code == 200
            data = response.json()
            assert data["neighborhood"] == "Etiwanda"
            assert data["trends"]["trend_direction"] == "upward"


# ================== INTEGRATION & DASHBOARD TESTS ==================

class TestIntegrationEndpoints:
    """Test integration and dashboard API endpoints."""

    def test_get_dashboard_metrics_success(self):
        """Test unified dashboard metrics."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.JorgeAdvancedIntegration') as mock_integration:
            mock_integration.return_value.get_unified_dashboard = AsyncMock(
                return_value={
                    "voice_ai": {
                        "active_calls": 3,
                        "daily_calls": 12,
                        "avg_qualification_score": 72
                    },
                    "marketing": {
                        "active_campaigns": 5,
                        "total_leads_generated": 28,
                        "avg_campaign_roi": 2.8
                    },
                    "client_retention": {
                        "active_clients": 145,
                        "retention_rate": 0.88,
                        "referrals_this_month": 8
                    },
                    "market_predictions": {
                        "neighborhoods_analyzed": 15,
                        "investment_opportunities": 6,
                        "avg_predicted_appreciation": 0.07
                    },
                    "integration_health": {
                        "status": "healthy",
                        "modules_online": 4
                    }
                }
            )

            response = client.get("/api/jorge-advanced/dashboard/metrics")

            assert response.status_code == 200
            data = response.json()
            assert data["voice_ai"]["daily_calls"] == 12
            assert data["marketing"]["active_campaigns"] == 5

    def test_get_module_health_success(self):
        """Test module health status."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.JorgeAdvancedIntegration') as mock_integration:
            mock_integration.return_value.check_module_health = AsyncMock(
                return_value={
                    "overall_status": "healthy",
                    "modules": [
                        {
                            "name": "voice_ai",
                            "status": "healthy",
                            "metrics": {"active_calls": 3},
                            "issues": []
                        },
                        {
                            "name": "marketing",
                            "status": "healthy",
                            "metrics": {"active_campaigns": 5},
                            "issues": []
                        }
                    ]
                }
            )

            response = client.get("/api/jorge-advanced/health/modules")

            assert response.status_code == 200
            data = response.json()
            assert data["overall_status"] == "healthy"
            assert len(data["modules"]) == 2

    def test_trigger_integration_event_success(self):
        """Test manual integration event triggering."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.JorgeAdvancedIntegration') as mock_integration:
            mock_integration.return_value.handle_integration_event = AsyncMock()

            response = client.post(
                "/api/jorge-advanced/integration/trigger-event",
                params={"event_type": "high_qualified_call"},
                json={
                    "call_id": "test-call-123",
                    "qualification_score": 85,
                    "lead_info": {"employer": "Amazon", "timeline": "30_days"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["event_type"] == "high_qualified_call"
            assert data["status"] == "processed"


# ================== SYSTEM TESTS ==================

class TestSystemEndpoints:
    """Test system-level endpoints."""

    def test_health_check_success(self):
        """Test health check endpoint."""
        response = client.get("/api/jorge-advanced/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jorge-advanced-features"
        assert len(data["modules"]) == 4

    def test_get_configuration_success(self):
        """Test configuration endpoint."""
        response = client.get("/api/jorge-advanced/config")

        assert response.status_code == 200
        data = response.json()
        assert "voice_ai" in data
        assert "marketing" in data
        assert "retention" in data
        assert "market_prediction" in data
        assert data["voice_ai"]["qualification_questions"] == 7


# ================== ERROR HANDLING TESTS ==================

class TestErrorHandling:
    """Test error handling across all endpoints."""

    def test_voice_handler_error(self):
        """Test voice handler service error."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.get_voice_ai_handler') as mock_handler:
            mock_handler.side_effect = Exception("Voice service unavailable")

            response = client.post(
                "/api/jorge-advanced/voice/start-call",
                json={
                    "phone_number": "+19095551234",
                    "caller_name": "John Doe"
                }
            )

            assert response.status_code == 500
            assert "Voice service unavailable" in response.json()["detail"]

    def test_campaign_not_found(self):
        """Test campaign not found error."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.AutomatedMarketingEngine') as mock_engine:
            mock_engine.return_value.get_campaign_content = AsyncMock(return_value=None)

            response = client.get("/api/jorge-advanced/marketing/campaigns/invalid-id/content")

            assert response.status_code == 404
            assert "Campaign not found" in response.json()["detail"]

    def test_client_not_found(self):
        """Test client not found error."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.ClientRetentionEngine') as mock_engine:
            mock_engine.return_value.get_client_profile = AsyncMock(return_value=None)

            response = client.get("/api/jorge-advanced/retention/client/invalid-id/engagement")

            assert response.status_code == 404
            assert "Client not found" in response.json()["detail"]


# ================== INTEGRATION TESTS ==================

@pytest.mark.integration
class TestJorgeAdvancedIntegration:
    """Integration tests for Jorge's advanced features."""

    @pytest.mark.asyncio
    async def test_end_to_end_voice_to_marketing_flow(self):
        """Test complete flow from voice call to marketing campaign."""
        # This would test the actual integration between modules
        # For now, just verify the endpoints can be called in sequence

        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.get_voice_ai_handler') as mock_voice:
            with patch('ghl_real_estate_ai.api.routes.jorge_advanced.AutomatedMarketingEngine') as mock_marketing:
                # Setup mocks
                mock_voice.return_value.handle_incoming_call = AsyncMock(
                    return_value=VoiceCallContext(call_id="test-123", phone_number="+19095551234")
                )
                mock_voice.return_value.handle_call_completion = AsyncMock(
                    return_value={
                        "call_id": "test-123",
                        "qualification_score": 85,
                        "transfer_to_jorge": True,
                        "extracted_info": {"employer": "Amazon"}
                    }
                )
                mock_marketing.return_value.create_campaign_from_trigger = AsyncMock(
                    return_value=CampaignBrief(campaign_id="campaign-456", name="High Qualified Lead Follow-up")
                )

                # Start call
                response1 = client.post(
                    "/api/jorge-advanced/voice/start-call",
                    json={"phone_number": "+19095551234"}
                )
                assert response1.status_code == 200

                # End call
                response2 = client.post("/api/jorge-advanced/voice/end-call/test-123")
                assert response2.status_code == 200

                # Create follow-up campaign
                response3 = client.post(
                    "/api/jorge-advanced/marketing/create-campaign",
                    json={
                        "trigger_type": "high_qualified_call",
                        "target_audience": {"employer": "Amazon"},
                        "campaign_objectives": ["Follow up on qualified lead"],
                        "content_formats": ["email"]
                    }
                )
                assert response3.status_code == 200

    def test_dashboard_metrics_integration(self):
        """Test dashboard metrics pulling from all modules."""
        with patch('ghl_real_estate_ai.api.routes.jorge_advanced.JorgeAdvancedIntegration') as mock_integration:
            mock_integration.return_value.get_unified_dashboard = AsyncMock(
                return_value={
                    "voice_ai": {"status": "active"},
                    "marketing": {"status": "active"},
                    "client_retention": {"status": "active"},
                    "market_predictions": {"status": "active"},
                    "integration_health": {"status": "healthy"}
                }
            )

            response = client.get("/api/jorge-advanced/dashboard/metrics")

            assert response.status_code == 200
            data = response.json()
            assert all(module["status"] == "active" for module in [
                data["voice_ai"], data["marketing"],
                data["client_retention"], data["market_predictions"]
            ])


if __name__ == "__main__":
    pytest.main([__file__])