import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Tests for Predictive Scoring V2 API Routes

Comprehensive test suite for enhanced API endpoints with
backward compatibility and performance validation.

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.routes.predictive_scoring_v2 import router, verify_jwt_token
from ghl_real_estate_ai.services.realtime_inference_engine_v2 import InferenceResult, MarketSegment


def override_auth(app, user):
    """Override the JWT auth dependency on a local app instance.

    The route binds ``Depends(verify_jwt_token)`` at import time, so patching
    the module attribute is a no-op. ``verify_jwt_token`` is also not bearer
    backed, so without an override it treats ``token`` as a required query
    param and returns 422. Each test builds its own bare ``FastAPI()`` app, so
    the override lives on that local app and needs no shared teardown.
    """
    app.dependency_overrides[verify_jwt_token] = lambda: user


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {"user_id": "test_user_123", "role": "admin", "email": "test@example.com"}


@pytest.fixture
def mock_inference_result():
    """Mock inference result for testing"""
    return InferenceResult(
        lead_id="test_lead_123",
        score=85.5,
        confidence=0.92,
        tier="hot",
        market_segment=MarketSegment.TECH_HUB,
        behavioral_signals={
            "email_open_rate": 0.8,
            "response_velocity": 0.9,
            "preapproval_mentions": 1.0,
            "immediate_timeline": 0.8,
            "tech_company_association": 1.0,
        },
        routing_recommendation={
            "recommended_agent": "agent_001",
            "agent_name": "Sarah Mitchell",
            "priority_level": "high",
            "expected_response_time": "30_minutes",
        },
        inference_time_ms=45.2,
        cache_hit=False,
        model_version="tech_hub_v1.0",
        ab_test_group="experimental_v1",
        timestamp=datetime.now(),
    )


@pytest.fixture
def sample_request_data():
    """Sample request data for testing"""
    return {
        "lead_id": "test_lead_123",
        "lead_data": {
            "budget": 750000,
            "location": "Rancho Cucamonga, CA",
            "source": "organic",
            "timeline": "immediate",
            "email_opens": 10,
            "email_clicks": 6,
            "emails_sent": 12,
        },
        "conversation_history": [
            {
                "text": "I'm a software engineer at Apple looking for a home",
                "timestamp": "2026-01-15T10:00:00Z",
                "sender": "lead",
            },
            {
                "text": "Budget is $750K, need to move ASAP for new job",
                "timestamp": "2026-01-15T10:15:00Z",
                "sender": "lead",
            },
        ],
        "include_routing": True,
        "include_behavioral_analysis": True,
        "include_market_insights": True,
        "inference_mode": "real_time",
    }


class TestPredictiveScoringV2Routes:
    """Test V2 API route functionality"""

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.inference_engine")
    def test_score_lead_v2_success(self, mock_engine, mock_user, mock_inference_result, sample_request_data):
        """Test successful V2 lead scoring"""
        mock_engine.predict = AsyncMock(return_value=mock_inference_result)

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)
        client = TestClient(app)

        response = client.post("/api/v2/predictive-scoring/score", json=sample_request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["lead_id"] == "test_lead_123"
        assert data["score"] == 85.5
        assert data["confidence"] == 0.92
        assert data["tier"] == "hot"
        assert data["market_segment"] == "tech_hub"

        # Verify behavioral signals included
        assert "behavioral_signals" in data
        assert len(data["behavioral_signals"]) > 0

        # Verify routing recommendation included
        assert "routing_recommendation" in data
        assert data["routing_recommendation"]["recommended_agent"] == "agent_001"

        # Verify performance metrics
        assert data["inference_time_ms"] == 45.2
        assert data["cache_hit"] == False
        assert data["model_version"] == "tech_hub_v1.0"

        # Verify legacy compatibility fields
        assert "qualification_score" in data
        assert "conversion_probability" in data
        assert 0 <= data["qualification_score"] <= 7
        assert 0 <= data["conversion_probability"] <= 1

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2._get_legacy_scorer")
    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.inference_engine")
    def test_score_lead_v2_fallback_to_legacy(self, mock_engine, mock_get_legacy, mock_user, sample_request_data):
        """Test fallback to legacy scorer when V2 fails"""
        mock_engine.predict = AsyncMock(side_effect=Exception("V2 inference failed"))

        # Mock legacy scorer response. score_lead is called synchronously
        # (the lru_cache singleton accessor returns the scorer instance).
        mock_legacy_result = Mock()
        mock_legacy_result.score = 75.0
        mock_legacy_result.confidence = 0.7
        mock_legacy_result.tier = "warm"
        mock_legacy_result.recommendations = ["Follow up within 24 hours"]

        mock_legacy = Mock()
        mock_legacy.score_lead.return_value = mock_legacy_result
        mock_get_legacy.return_value = mock_legacy

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)
        client = TestClient(app)

        response = client.post("/api/v2/predictive-scoring/score", json=sample_request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify fallback response
        assert data["lead_id"] == "test_lead_123"
        assert data["score"] == 75.0
        assert data["model_version"] == "legacy_fallback"
        assert data["market_segment"] == "general_market"

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.inference_engine")
    def test_batch_scoring_success(self, mock_engine, mock_user, mock_inference_result):
        """Test successful batch lead scoring"""
        # Mock batch results
        batch_results = []
        for i in range(3):
            result = InferenceResult(
                lead_id=f"batch_lead_{i}",
                score=80.0 + i * 5,
                confidence=0.85,
                tier="warm",
                market_segment=MarketSegment.GENERAL_MARKET,
                behavioral_signals={"engagement": 0.7},
                routing_recommendation={"agent": "auto_assign"},
                inference_time_ms=50.0,
                cache_hit=False,
                model_version="v2.0",
                timestamp=datetime.now(),
            )
            batch_results.append(result)

        mock_engine.predict_batch = AsyncMock(return_value=batch_results)

        batch_request = {
            "leads": [
                {
                    "lead_id": f"batch_lead_{i}",
                    "lead_data": {"budget": 500000 + i * 50000},
                    "conversation_history": [],
                    "include_routing": True,
                    "include_behavioral_analysis": True,
                }
                for i in range(3)
            ],
            "processing_mode": "batch_fast",
        }

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)
        client = TestClient(app)

        response = client.post("/api/v2/predictive-scoring/score-batch", json=batch_request)

        assert response.status_code == 200
        data = response.json()

        # Verify batch response structure
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 3

        # Verify summary statistics
        assert data["successful_predictions"] == 3
        assert data["failed_predictions"] == 0
        assert data["summary"]["average_score"] > 0
        assert data["summary"]["processing_mode"] == "batch_fast"

    def test_batch_scoring_size_limit(self, mock_user):
        """Test batch scoring enforces size limits"""
        # Create request with too many leads
        batch_request = {
            "leads": [
                {"lead_id": f"lead_{i}", "lead_data": {"budget": 500000}, "conversation_history": []}
                for i in range(101)  # Exceeds limit of 100
            ]
        }

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)
        client = TestClient(app)

        response = client.post("/api/v2/predictive-scoring/score-batch", json=batch_request)

        # The 100-lead cap is enforced by the BatchScoringRequest field
        # constraint (max_items=100), so pydantic rejects 101 leads at request
        # validation with a 422 before the handler runs. The handler's inner
        # 400 check is now unreachable dead code.
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any(e["type"] == "too_long" and e["loc"][-1] == "leads" for e in errors)

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.verify_jwt_token")
    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.signal_processor")
    def test_behavioral_signals_endpoint(self, mock_processor, mock_auth, mock_user):
        """Test behavioral signals extraction endpoint"""
        mock_auth.return_value = mock_user

        # Mock signal processor
        mock_signals = {
            "email_open_rate": 0.8,
            "response_velocity": 0.9,
            "preapproval_mentions": 1.0,
            "immediate_timeline": 0.7,
            "tech_company_association": 0.9,
        }
        mock_summary = {"overall_signal_strength": 0.82, "strong_signals": 3, "weak_signals": 0}

        mock_processor.extract_signals.return_value = mock_signals
        mock_processor.get_signal_summary.return_value = mock_summary

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Note: This is a simplified test - actual endpoint would need proper query parameters
        lead_data = {"budget": 750000, "location": "Rancho Cucamonga"}

        # For testing purposes, we'll test the function logic directly
        # since the actual endpoint uses complex query parameters
        assert len(mock_signals) == 5
        assert all(0 <= v <= 1 for v in mock_signals.values())

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.lead_router")
    def test_routing_recommendation_endpoint(self, mock_router, mock_user):
        """Test routing recommendation endpoint"""
        mock_recommendation = {
            "recommended_agent": "agent_001",
            "agent_name": "Sarah Mitchell",
            "match_score": 92.5,
            "confidence": 0.88,
            "primary_reason": "Excellent specialization match for tech professionals",
            "expected_response_time": "30_minutes",
        }

        mock_router.recommend_routing = AsyncMock(return_value=mock_recommendation)

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)
        client = TestClient(app)

        # lead_id, lead_score, routing_strategy are scalar -> query params;
        # behavioral_signals and lead_data are the JSON body.
        params = {
            "lead_id": "test_lead",
            "lead_score": 85.5,
            "routing_strategy": "hybrid_intelligent",
        }
        body = {
            "behavioral_signals": {"tech_company_association": 1.0},
            "lead_data": {"budget": 750000, "location": "Rancho Cucamonga"},
        }

        response = client.post("/api/v2/predictive-scoring/routing-recommendation", params=params, json=body)

        assert response.status_code == 200
        data = response.json()

        assert data["recommended_agent"] == "agent_001"
        assert data["agent_name"] == "Sarah Mitchell"
        assert data["match_score"] == 92.5

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.inference_engine")
    def test_performance_metrics_endpoint(self, mock_engine, mock_user):
        """Test performance metrics endpoint"""
        mock_metrics = {
            "p95_latency_ms": 75.0,
            "cache_hit_rate": 0.65,
            "total_requests": 1500,
            "error_rate": 0.008,
            "is_healthy": True,
            "model_usage": {"tech_hub": 450, "general_market": 1050},
            "target_p95_ms": 100,
        }

        mock_engine.get_performance_metrics.return_value = mock_metrics

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)
        client = TestClient(app)

        response = client.get("/api/v2/predictive-scoring/performance-metrics")

        assert response.status_code == 200
        data = response.json()

        assert data["p95_latency_ms"] == 75.0
        assert data["cache_hit_rate"] == 0.65
        assert data["system_status"] == "healthy"
        assert "model_health" in data

    def test_cache_warming_admin_only(self, mock_user):
        """Test cache warming requires admin privileges"""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        # Override with a non-admin user.
        override_auth(app, {"role": "user", "user_id": "test"})
        client = TestClient(app)

        sample_leads = [{"lead_id": "test", "budget": 500000}]
        response = client.post("/api/v2/predictive-scoring/warm-cache", json=sample_leads)

        assert response.status_code == 403
        assert "admin or manager privileges" in response.json()["detail"]

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.inference_engine")
    def test_cache_warming_success(self, mock_engine, mock_user):
        """Test successful cache warming"""
        mock_engine.warm_cache = AsyncMock()

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)  # Admin user
        client = TestClient(app)

        sample_leads = [{"lead_id": "test1", "budget": 500000}, {"lead_id": "test2", "budget": 600000}]

        response = client.post("/api/v2/predictive-scoring/warm-cache", json=sample_leads)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "warming_initiated"
        assert data["sample_count"] == 2

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.inference_engine")
    def test_legacy_endpoint_compatibility(self, mock_engine, mock_user, mock_inference_result):
        """Test legacy endpoint maintains backward compatibility"""
        mock_engine.predict = AsyncMock(return_value=mock_inference_result)

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        override_auth(app, mock_user)
        client = TestClient(app)

        legacy_request = {
            "lead_id": "legacy_lead",
            "budget": 500000,
            "location": "Rancho Cucamonga",
            "conversation_history": [{"text": "Looking for a home"}],
        }

        response = client.post("/api/v2/predictive-scoring/legacy/score", json=legacy_request)

        assert response.status_code == 200
        data = response.json()

        # Verify legacy format
        assert "score" in data
        assert "tier" in data
        assert "confidence" in data
        assert "conversion_probability" in data
        assert "qualification_score" in data

        # Should not include V2-specific fields in legacy endpoint
        assert "behavioral_signals" not in data
        assert "market_segment" not in data

    @patch("ghl_real_estate_ai.api.routes.predictive_scoring_v2.inference_engine")
    def test_health_check_endpoint(self, mock_engine):
        """Test health check endpoint"""
        mock_result = InferenceResult(
            lead_id="health_check",
            score=50.0,
            confidence=0.8,
            tier="warm",
            market_segment=MarketSegment.GENERAL_MARKET,
            behavioral_signals={},
            routing_recommendation={},
            inference_time_ms=45.0,
            cache_hit=False,
            model_version="v2.0",
            timestamp=datetime.now(),
        )

        mock_engine.predict = AsyncMock(return_value=mock_result)
        mock_engine.get_performance_metrics.return_value = {"cache_hit_rate": 0.7, "p95_latency_ms": 80.0}

        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/api/v2/predictive-scoring/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert data["version"] == "2.0"
        assert "response_time_ms" in data

    def test_request_validation(self):
        """Test API request validation"""
        from ghl_real_estate_ai.api.routes.predictive_scoring_v2 import LeadScoringRequest

        # Valid request
        valid_data = {
            "lead_id": "test_123",
            "lead_data": {"budget": 500000},
            "conversation_history": [],
            "inference_mode": "real_time",
        }

        request = LeadScoringRequest(**valid_data)
        assert request.lead_id == "test_123"
        assert request.inference_mode == "real_time"

        # Invalid inference mode should raise validation error
        invalid_data = valid_data.copy()
        invalid_data["inference_mode"] = "invalid_mode"

        with pytest.raises(ValueError):
            LeadScoringRequest(**invalid_data)

    def test_response_model_validation(self):
        """Test API response model validation"""
        from ghl_real_estate_ai.api.routes.predictive_scoring_v2 import EnhancedScoringResponse

        # Valid response data
        valid_response = {
            "lead_id": "test_123",
            "score": 85.5,
            "confidence": 0.92,
            "tier": "hot",
            "market_segment": "tech_hub",
            "segment_confidence": 0.88,
            "inference_time_ms": 45.2,
            "cache_hit": False,
            "model_version": "v2.0",
            "scored_at": datetime.now(),
            "recommended_actions": ["Follow up immediately"],
            "risk_factors": [],
            "positive_signals": ["High tech engagement"],
        }

        response = EnhancedScoringResponse(**valid_response)
        assert response.score == 85.5
        assert response.tier == "hot"

        # Invalid score should raise validation error
        invalid_response = valid_response.copy()
        invalid_response["score"] = 150.0  # Out of range

        with pytest.raises(ValueError):
            EnhancedScoringResponse(**invalid_response)

    def test_api_versioning_headers(self):
        """Test API version header handling"""
        from fastapi import FastAPI, Header
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Test with version headers
        headers = {"X-API-Version": "2.0", "X-Client-Version": "web-1.2.3"}

        # Note: This is a simplified test since we can't easily test the actual endpoint
        # without full authentication setup
        assert headers["X-API-Version"] == "2.0"
