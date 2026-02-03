"""
End-to-End Integration Tests for Week 5-8 API Routes

Tests cross-service flows through the FastAPI endpoints:
1. Lead qualification → behavioral analysis → compliance → channel routing
2. Market intelligence → commission forecast → export
3. Voice intelligence → sentiment → propensity scoring
4. HeyGen video generation flow
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a lightweight test client with only Week 5-8 routes."""
    from fastapi import FastAPI
    from ghl_real_estate_ai.api.routes import (
        langgraph_orchestration,
        behavioral_triggers,
        fha_respa_compliance,
        voice_intelligence,
        propensity_scoring,
        heygen_video,
        sentiment_analysis,
        channel_routing,
        rc_market_intelligence,
        export_engine,
        commission_forecast,
    )

    app = FastAPI(title="Week 5-8 Integration Tests")
    app.include_router(langgraph_orchestration.router)
    app.include_router(behavioral_triggers.router)
    app.include_router(fha_respa_compliance.router)
    app.include_router(voice_intelligence.router)
    app.include_router(propensity_scoring.router)
    app.include_router(heygen_video.router)
    app.include_router(sentiment_analysis.router)
    app.include_router(channel_routing.router)
    app.include_router(rc_market_intelligence.router)
    app.include_router(export_engine.router)
    app.include_router(commission_forecast.router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset service singletons between tests."""
    import ghl_real_estate_ai.services.langgraph_orchestrator as lgo
    import ghl_real_estate_ai.services.behavioral_trigger_detector as btd
    import ghl_real_estate_ai.services.compliance_middleware as cm
    import ghl_real_estate_ai.services.vapi_voice_integration as vvi
    import ghl_real_estate_ai.services.sentiment_analysis_engine as sae
    import ghl_real_estate_ai.services.unified_channel_router as ucr
    import ghl_real_estate_ai.services.real_time_market_intelligence as rtmi
    import ghl_real_estate_ai.services.professional_export_engine as pee
    import ghl_real_estate_ai.services.commission_forecast_engine as cfe
    import ghl_real_estate_ai.services.heygen_video_service as hvs
    import ghl_real_estate_ai.services.xgboost_propensity_engine as xpe

    lgo._orchestrator = None
    btd._detector = None
    cm._middleware = None
    vvi._intelligence = None
    sae._engine = None
    ucr._router = None
    rtmi._intel = None
    pee._engine = None
    cfe._engine = None
    hvs._service = None
    xpe._engine = None
    yield


# ===========================================================================
# Flow 1: Lead Qualification Pipeline
# ===========================================================================

class TestLeadQualificationFlow:
    """Test the full lead qualification → behavioral → compliance → routing pipeline."""

    def test_qualify_seller_lead(self, client):
        """Seller lead flows through orchestration and comes back qualified."""
        resp = client.post("/api/v1/orchestration/qualify", json={
            "contact_id": "c_seller_001",
            "location_id": "loc_001",
            "message": "I want to sell my home in Victoria, what's it worth?",
            "contact_tags": ["Needs Qualifying"],
            "contact_info": {"first_name": "Maria"},
            "conversation_history": [
                {"seller_preferences": {"motivation": "downsizing", "timeline_acceptable": True,
                                        "property_condition": "good", "price_expectation": 800000}}
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["lead_type"] == "seller"
        assert data["temperature"] in ("hot", "warm", "cold")
        assert data["qualification_stage"] == "complete"

    def test_qualify_buyer_lead(self, client):
        """Buyer lead qualification with behavioral signals."""
        resp = client.post("/api/v1/orchestration/qualify", json={
            "contact_id": "c_buyer_001",
            "location_id": "loc_001",
            "message": "I'm looking to buy a 3-bedroom house, pre-approved for $700k",
            "contact_tags": ["Buyer-Lead"],
            "contact_info": {"first_name": "John"},
            "conversation_history": [
                {"financial_readiness_score": 80, "buying_motivation_score": 75}
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["lead_type"] == "buyer"
        assert data["is_qualified"] is True

    def test_batch_qualification(self, client):
        """Batch qualification of multiple leads."""
        resp = client.post("/api/v1/orchestration/qualify/batch", json={
            "leads": [
                {
                    "contact_id": f"c_batch_{i}",
                    "location_id": "loc_001",
                    "message": msg,
                    "contact_tags": tags,
                    "contact_info": {},
                }
                for i, (msg, tags) in enumerate([
                    ("I want to sell", ["Needs Qualifying"]),
                    ("Looking to buy a home", ["Buyer-Lead"]),
                    ("Just browsing listings", []),
                ])
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        types = {r["lead_type"] for r in data["results"]}
        assert "seller" in types
        assert "buyer" in types

    def test_behavioral_analysis_integration(self, client):
        """Behavioral analysis detects hedging and recommends technique."""
        resp = client.post("/api/v1/behavioral/analyze", json={
            "message": "Maybe if the price is right, I might consider selling... not sure yet though",
            "contact_id": "c_behavioral_001",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["hedging_score"] > 0
        assert data["drift_direction"] in ("warming", "cooling", "stable")
        assert data["trigger_count"] > 0

    def test_compliance_enforcement_blocks_steering(self, client):
        """Compliance middleware blocks FHA steering language."""
        resp = client.post("/api/v1/compliance-enforcement/enforce", json={
            "message": "You should avoid that area, it's not safe and the schools are terrible",
            "contact_id": "c_compliance_001",
            "mode": "buyer",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("BLOCKED", "blocked")
        assert data["risk_score"] > 0.5
        assert len(data["violations"]) > 0
        assert data["safe_alternative"] is not None

    def test_compliance_passes_clean_message(self, client):
        """Compliance passes clean messages through."""
        resp = client.post("/api/v1/compliance-enforcement/enforce", json={
            "message": "I found a property that matches your requirements. Want to schedule a showing?",
            "contact_id": "c_compliance_002",
            "mode": "buyer",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("PASSED", "passed")
        assert data["risk_score"] == 0.0

    def test_channel_routing_sends_message(self, client):
        """Channel router sends a message via preferred channel."""
        resp = client.post("/api/v1/channels/send", json={
            "contact_id": "c_channel_001",
            "message": "Hi Sarah, I found 3 listings that match your criteria!",
            "preferred_channel": "sms",
            "priority": "normal",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["delivery_status"] in ("sent", "delivered", "fallback")
        assert data["compliance_status"] in ("PASSED", "passed")

    def test_channel_routing_blocks_non_compliant(self, client):
        """Channel router blocks non-compliant messages."""
        resp = client.post("/api/v1/channels/send", json={
            "contact_id": "c_channel_002",
            "message": "I'll give you a referral fee if you use our lender",
            "preferred_channel": "sms",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["delivery_status"] == "blocked"


# ===========================================================================
# Flow 2: Market Intelligence → Forecast → Export
# ===========================================================================

class TestMarketIntelligenceFlow:
    """Test market intelligence → commission forecast → export pipeline."""

    def test_market_snapshot(self, client):
        """Get market snapshot for Victoria neighborhood."""
        resp = client.get("/api/v1/rc-market/snapshot/victoria")
        assert resp.status_code == 200
        data = resp.json()
        assert data["neighborhood"] == "victoria"
        assert data["median_price"] > 0
        assert data["market_condition"] in ("sellers_market", "buyers_market", "balanced")

    def test_price_trends(self, client):
        """Get price trends for Etiwanda."""
        resp = client.get("/api/v1/rc-market/trends/etiwanda?days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert data["neighborhood"] == "etiwanda"
        assert data["direction"] in ("rising", "falling", "stable")
        assert data["confidence"] > 0

    def test_opportunity_detection(self, client):
        """Detect market opportunities across all neighborhoods."""
        resp = client.get("/api/v1/rc-market/opportunities?min_score=0.3")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["opportunities"], list)

    def test_neighborhood_comparison(self, client):
        """Compare all RC neighborhoods."""
        resp = client.get("/api/v1/rc-market/comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 4  # At least 4 neighborhoods

    def test_market_alerts(self, client):
        """Check for market alerts."""
        resp = client.get("/api/v1/rc-market/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["alerts"], list)

    def test_commission_forecast(self, client):
        """Forecast commission from pipeline data."""
        pipeline = [
            {"deal_id": "d1", "contact_name": "Alice", "property_value": 750000,
             "stage": "showing", "expected_close_month": 3, "deal_type": "buyer"},
            {"deal_id": "d2", "contact_name": "Bob", "property_value": 1300000,
             "stage": "offer", "expected_close_month": 3, "deal_type": "seller"},
            {"deal_id": "d3", "contact_name": "Carol", "property_value": 650000,
             "stage": "qualified", "expected_close_month": 4, "deal_type": "buyer"},
        ]
        resp = client.post("/api/v1/commission-forecast/forecast", json={
            "pipeline": pipeline,
            "horizon_months": 3,
            "current_month": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["deal_count"] == 3
        assert data["total_expected"] > 0
        assert data["total_weighted"] > 0
        assert len(data["monthly_forecasts"]) == 3

    def test_monte_carlo_simulation(self, client):
        """Run Monte Carlo simulation on pipeline."""
        pipeline = [
            {"deal_id": "d1", "contact_name": "Alice", "property_value": 750000,
             "stage": "showing", "expected_close_month": 3},
            {"deal_id": "d2", "contact_name": "Bob", "property_value": 900000,
             "stage": "offer", "expected_close_month": 4},
        ]
        resp = client.post("/api/v1/commission-forecast/monte-carlo", json={
            "pipeline": pipeline,
            "simulations": 500,
            "target_revenue": 20000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["simulations"] == 500
        assert data["mean_revenue"] > 0
        assert 0 <= data["probability_above_target"] <= 1

    def test_executive_summary(self, client):
        """Generate executive summary with Monte Carlo."""
        pipeline = [
            {"deal_id": f"d{i}", "contact_name": f"Lead {i}",
             "property_value": 700000 + i * 50000,
             "stage": stage, "expected_close_month": (i % 3) + 2}
            for i, stage in enumerate([
                "prospect", "qualified", "showing", "offer",
                "under_contract", "qualified", "showing",
            ])
        ]
        resp = client.post("/api/v1/commission-forecast/executive-summary", json={
            "pipeline": pipeline,
            "horizon_months": 3,
            "include_monte_carlo": True,
            "target_revenue": 30000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["forecast_confidence"] in ("high", "moderate", "low")
        assert data["recommendation"]
        assert data["monte_carlo"] is not None

    def test_export_market_report_html(self, client):
        """Generate an HTML market report."""
        resp = client.post("/api/v1/exports/market-report", json={
            "neighborhood": "victoria",
            "report_type": "monthly",
            "format": "html",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "html"
        assert "<html>" in data["content"]
        assert "Victoria" in data["content"]

    def test_export_market_report_csv(self, client):
        """Generate a CSV market report."""
        resp = client.post("/api/v1/exports/market-report", json={
            "neighborhood": "haven",
            "report_type": "weekly",
            "format": "csv",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "csv"
        assert "Metric" in data["content"]

    def test_export_cma_report(self, client):
        """Generate a CMA report."""
        resp = client.post("/api/v1/exports/cma-report", json={
            "address": "123 Haven Ave, Rancho Cucamonga",
            "property_data": {
                "bedrooms": 4, "bathrooms": 2.5, "sqft": 2200,
                "year_built": "2005", "lot_size": "6,500 sqft", "condition": "Good",
            },
            "comparables": [
                {"address": "125 Haven Ave", "sale_price": 780000, "sale_date": "2025-12-01",
                 "sqft": 2100, "bedrooms": 4, "bathrooms": 2, "distance_miles": 0.2,
                 "adjustments": {"sqft": 5000, "bathroom": -3000}},
                {"address": "200 Haven Ave", "sale_price": 810000, "sale_date": "2025-11-15",
                 "sqft": 2300, "bedrooms": 4, "bathrooms": 2.5, "distance_miles": 0.5,
                 "adjustments": {"sqft": -5000}},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_type"] == "cma"
        assert "123 Haven Ave" in data["content"]

    def test_export_leads_csv(self, client):
        """Export leads as CSV."""
        resp = client.post("/api/v1/exports/leads-csv", json={
            "leads": [
                {"name": "Alice Smith", "phone": "555-0001", "status": "qualified"},
                {"name": "Bob Jones", "phone": "555-0002", "status": "prospect"},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "csv"
        assert "Alice Smith" in data["content"]

    def test_full_market_to_export_flow(self, client):
        """End-to-end: market snapshot → forecast → export pipeline."""
        # Step 1: Get market data
        market_resp = client.get("/api/v1/rc-market/snapshot/etiwanda")
        assert market_resp.status_code == 200
        market = market_resp.json()

        # Step 2: Forecast with market-informed pipeline
        forecast_resp = client.post("/api/v1/commission-forecast/forecast", json={
            "pipeline": [
                {"deal_id": "flow_d1", "contact_name": "Integration Lead",
                 "property_value": market["median_price"],
                 "stage": "showing", "expected_close_month": 4},
            ],
            "horizon_months": 3,
        })
        assert forecast_resp.status_code == 200

        # Step 3: Export as report
        export_resp = client.post("/api/v1/exports/market-report", json={
            "neighborhood": "etiwanda",
            "report_type": "monthly",
            "format": "text",
        })
        assert export_resp.status_code == 200
        assert "Etiwanda" in export_resp.json()["content"]


# ===========================================================================
# Flow 3: Voice → Sentiment → Propensity
# ===========================================================================

class TestVoiceSentimentPropensityFlow:
    """Test voice analysis → sentiment → propensity scoring pipeline."""

    def test_transcript_analysis(self, client):
        """Analyze a voice transcript for qualification signals."""
        resp = client.post("/api/v1/voice-intelligence/analyze-transcript", json={
            "contact_id": "c_voice_001",
            "call_id": "call_001",
            "transcript_segments": [
                {"role": "agent", "text": "Hi, how can I help you today?"},
                {"role": "customer", "text": "I'm looking to buy a home in Rancho Cucamonga, "
                 "pre-approved for $700k, need to move within 2 months"},
                {"role": "agent", "text": "That's great! What areas interest you?"},
                {"role": "customer", "text": "Victoria or Haven, 3 bedrooms, good schools"},
            ],
            "call_duration_seconds": 180,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["lead_temperature"] in ("hot", "warm", "cold")
        assert data["qualification_signals"]["has_budget"] is True
        assert data["qualification_signals"]["has_timeline"] is True
        assert data["qualification_signals"]["has_location"] is True

    def test_sentiment_analysis(self, client):
        """Analyze message sentiment and emotions."""
        resp = client.post("/api/v1/sentiment/analyze", json={
            "contact_id": "c_sentiment_001",
            "message": "I'm really excited about that house on Haven Ave! Can't wait to see it!",
            "channel": "sms",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["polarity"] > 0  # Positive sentiment
        assert data["emotion"] in ("excited", "interested", "confident")

    def test_sentiment_conversation_tracking(self, client):
        """Track sentiment across a conversation."""
        messages = [
            "I love the property photos!",
            "It looks amazing, when can I see it?",
            "Hmm, the price is a bit high though",
        ]
        for msg in messages:
            resp = client.post("/api/v1/sentiment/analyze", json={
                "contact_id": "c_sentiment_track",
                "message": msg,
                "channel": "sms",
            })
            assert resp.status_code == 200

        # Get conversation-level sentiment
        conv_resp = client.get("/api/v1/sentiment/conversation/c_sentiment_track")
        assert conv_resp.status_code == 200
        data = conv_resp.json()
        assert data["message_count"] == 3
        assert len(data["sentiment_timeline"]) == 3

    def test_propensity_scoring(self, client):
        """Score lead propensity with behavioral signals."""
        resp = client.post("/api/v1/propensity/score", json={
            "contact_id": "c_propensity_001",
            "conversation_context": {
                "message_count": 15,
                "avg_response_time": 45,
                "sentiment": 0.6,
                "urgency_score": 0.7,
                "engagement_score": 0.8,
                "qualification_completeness": 0.9,
                "budget_confidence": 0.85,
                "price_mentions": 3,
                "location_specificity": 0.7,
            },
            "behavioral_signals": {
                "commitment_score": 0.7,
                "hedging_score": 0.2,
                "urgency_signal": 0.6,
                "composite_score": 0.65,
                "latency_factor": 0.3,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert 0 <= data["conversion_probability"] <= 1
        assert data["temperature"] in ("hot", "warm", "cold")
        assert data["recommended_approach"]

    def test_propensity_shap_explanation(self, client):
        """Get SHAP explanation for a propensity score."""
        resp = client.post("/api/v1/propensity/explain", json={
            "contact_id": "c_explain_001",
            "conversation_context": {
                "message_count": 15,
                "avg_response_time": 45,
                "sentiment": 0.6,
                "urgency_score": 0.7,
                "engagement_score": 0.8,
                "qualification_completeness": 0.9,
                "budget_confidence": 0.85,
                "price_mentions": 3,
                "location_specificity": 0.7,
            },
            "behavioral_signals": {
                "commitment_score": 0.7,
                "hedging_score": 0.2,
                "urgency_signal": 0.6,
                "composite_score": 0.65,
                "latency_factor": 0.3,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert 0 < data["conversion_probability"] <= 1
        assert data["base_value"] > 0
        assert len(data["feature_explanations"]) == 26
        assert len(data["key_drivers"]) > 0
        assert data["waterfall_data"]["entries"]
        # Verify feature categories
        categories = {e["category"] for e in data["feature_explanations"]}
        assert "life_event" in categories
        assert "conversation" in categories
        assert "behavioral" in categories

    def test_voice_to_propensity_flow(self, client):
        """End-to-end: voice transcript → sentiment → propensity."""
        # Step 1: Analyze voice transcript
        voice_resp = client.post("/api/v1/voice-intelligence/analyze-transcript", json={
            "contact_id": "c_flow_001",
            "call_id": "call_flow_001",
            "transcript_segments": [
                {"role": "customer", "text": "I definitely want to buy, pre-approved for $800k, "
                 "need to move to Etiwanda this month, let's do it"},
            ],
            "call_duration_seconds": 120,
        })
        assert voice_resp.status_code == 200
        voice = voice_resp.json()

        # Step 2: Analyze sentiment
        sentiment_resp = client.post("/api/v1/sentiment/analyze", json={
            "contact_id": "c_flow_001",
            "message": "I definitely want to buy, pre-approved for $800k, "
                       "need to move to Etiwanda this month, let's do it",
            "channel": "voice",
        })
        assert sentiment_resp.status_code == 200
        sentiment = sentiment_resp.json()
        assert sentiment["polarity"] > 0

        # Step 3: Score propensity using voice + sentiment signals
        propensity_resp = client.post("/api/v1/propensity/score", json={
            "contact_id": "c_flow_001",
            "behavioral_signals": {
                "commitment_score": voice["commitment_score"],
                "hedging_score": voice["hedging_score"],
                "urgency_signal": voice["urgency_score"],
                "composite_score": voice["composite_score"],
                "latency_factor": 0.3,
            },
            "conversation_context": {
                "message_count": 5,
                "sentiment": sentiment["polarity"],
                "urgency_score": voice["urgency_score"],
                "engagement_score": 0.8,
                "qualification_completeness": 0.9,
                "budget_confidence": 0.85,
            },
        })
        assert propensity_resp.status_code == 200
        propensity = propensity_resp.json()
        assert propensity["conversion_probability"] > 0


# ===========================================================================
# Flow 4: HeyGen Video
# ===========================================================================

class TestHeyGenVideoFlow:
    """Test video creation, status tracking, and engagement recording."""

    def test_create_video(self, client):
        """Create a personalized video for a lead."""
        resp = client.post("/api/v1/video/create", json={
            "lead_id": "l_video_001",
            "lead_name": "Sarah",
            "lead_profile": {
                "temperature": "warm",
                "area": "Victoria",
                "persona": "family",
                "bedrooms": "4",
            },
            "template": "buyer_welcome",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("completed", "processing")
        assert data["video_url"]
        assert data["lead_id"] == "l_video_001"
        assert data["request_id"]

    def test_video_lifecycle(self, client):
        """Full video lifecycle: create → status → deliver → view."""
        # Create
        create_resp = client.post("/api/v1/video/create", json={
            "lead_id": "l_lifecycle_001",
            "lead_name": "Mike",
            "lead_profile": {"temperature": "hot"},
            "template": "seller_cma",
        })
        assert create_resp.status_code == 200
        request_id = create_resp.json()["request_id"]

        # Check status
        status_resp = client.get(f"/api/v1/video/status/{request_id}")
        assert status_resp.status_code == 200

        # Mark delivered
        deliver_resp = client.post(f"/api/v1/video/delivered/{request_id}")
        assert deliver_resp.status_code == 200

        # Record view
        view_resp = client.post(f"/api/v1/video/view/{request_id}")
        assert view_resp.status_code == 200

        # Check lead videos
        lead_resp = client.get("/api/v1/video/lead/l_lifecycle_001")
        assert lead_resp.status_code == 200
        assert lead_resp.json()["total"] >= 1

    def test_video_cost_tracking(self, client):
        """Track video generation costs."""
        # Create a video first
        client.post("/api/v1/video/create", json={
            "lead_id": "l_cost_001",
            "lead_name": "Cost Test",
            "lead_profile": {},
        })
        resp = client.get("/api/v1/video/costs")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_videos" in data
        assert "total_cost" in data
        assert "daily_remaining" in data


# ===========================================================================
# Health Checks
# ===========================================================================

class TestHealthEndpoints:
    """Verify all service health endpoints respond."""

    @pytest.mark.parametrize("path", [
        "/api/v1/orchestration/health",
        "/api/v1/behavioral/health",
        "/api/v1/compliance-enforcement/health",
        "/api/v1/voice-intelligence/health",
        "/api/v1/propensity/health",
        "/api/v1/video/health",
        "/api/v1/sentiment/health",
        "/api/v1/channels/health",
        "/api/v1/rc-market/health",
        "/api/v1/exports/health",
        "/api/v1/commission-forecast/health",
    ])
    def test_health_endpoint(self, client, path):
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
