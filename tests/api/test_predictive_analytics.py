"""
Tests for Predictive Analytics API endpoints.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import json

from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import (
    PredictiveScore, LeadInsights, LeadPriority
)
from ghl_real_estate_ai.services.action_recommendations import (
    ActionRecommendation, ActionSequence, TimingOptimization,
    ActionType, CommunicationChannel
)
from ghl_real_estate_ai.ml.closing_probability_model import ModelMetrics


class TestPredictiveAnalyticsAPI:
    """Test suite for Predictive Analytics API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def mock_jwt_token(self):
        """Mock JWT token for authentication."""
        return "mock.jwt.token"

    @pytest.fixture
    def auth_headers(self, mock_jwt_token):
        """Create authorization headers."""
        return {"Authorization": f"Bearer {mock_jwt_token}"}

    @pytest.fixture
    def sample_conversation_request(self):
        """Create sample conversation request data."""
        return {
            "conversation_history": [
                {"role": "user", "text": "I'm looking for a house"},
                {"role": "assistant", "text": "I can help you with that!"},
                {"role": "user", "text": "My budget is $500,000 and I need 3 bedrooms"},
                {"role": "assistant", "text": "Great! Let me find some options."}
            ],
            "extracted_preferences": {
                "budget": "$500,000",
                "bedrooms": "3",
                "location": "downtown",
                "timeline": "ASAP"
            },
            "created_at": datetime.now().isoformat(),
            "location": "downtown",
            "lead_id": "test_lead_123"
        }

    @pytest.fixture
    def mock_predictive_score(self):
        """Create mock predictive score."""
        return PredictiveScore(
            qualification_score=5,
            qualification_percentage=75,
            closing_probability=0.68,
            closing_confidence_interval=(0.58, 0.78),
            engagement_score=72.0,
            urgency_score=85.0,
            risk_score=30.0,
            overall_priority_score=76.0,
            priority_level=LeadPriority.HIGH,
            risk_factors=["Market competition"],
            positive_signals=["High urgency", "Clear budget"],
            recommended_actions=["Schedule call within 2 hours", "Prepare property options"],
            optimal_contact_timing="Within 2-4 hours",
            time_investment_recommendation="High investment recommended",
            estimated_revenue_potential=18750.0,
            effort_efficiency_score=375.0,
            model_confidence=0.82,
            last_updated=datetime.now()
        )

    @pytest.fixture
    def mock_lead_insights(self):
        """Create mock lead insights."""
        return LeadInsights(
            response_pattern_analysis="Highly consistent and engaged responses",
            engagement_trend="increasing",
            conversation_quality_score=78.5,
            market_timing_advantage="Good timing - favorable market conditions",
            competitive_pressure_level="High - competitive market conditions",
            inventory_availability_impact="Moderate inventory - good selection available",
            next_best_action="Schedule property showing immediately",
            optimal_communication_channel="Phone call",
            recommended_follow_up_interval="Every 2-3 days with value-added content",
            pricing_strategy_recommendation="Act quickly - prices rising",
            estimated_time_to_close=32,
            recommended_effort_level="intensive",
            probability_of_churn=0.25
        )

    @pytest.fixture
    def mock_action_recommendation(self):
        """Create mock action recommendation."""
        return ActionRecommendation(
            action_type=ActionType.IMMEDIATE_CALL,
            priority_level=9,
            recommended_timing="Within 1 hour",
            communication_channel=CommunicationChannel.PHONE,
            title="🚨 URGENT: Immediate Phone Call Required",
            description="Critical lead with high closing probability requires immediate personal contact",
            talking_points=["Thank them for their interest", "Confirm requirements"],
            questions_to_ask=["What properties are you most interested in?", "When can we schedule showing?"],
            materials_to_prepare=["Top property recommendations", "Market analysis"],
            success_probability=0.85,
            expected_outcomes=["Schedule property showing", "Confirm budget"],
            potential_objections=["Not ready to see properties yet"],
            objection_responses={"Not ready to see properties yet": "Let's start with consultation"},
            follow_up_timing="Immediately after call",
            escalation_criteria="If no response within 2 hours",
            success_metrics=["Call connection rate", "Showing scheduled"],
            estimated_time_investment=30,
            effort_level="high",
            roi_potential=18750.0
        )

    @pytest.mark.asyncio
    async def test_get_predictive_score_success(
        self,
        client,
        auth_headers,
        sample_conversation_request,
        mock_predictive_score
    ):
        """Test successful predictive score retrieval."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.predictive_scorer') as mock_scorer:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_scorer.calculate_predictive_score.return_value = mock_predictive_score

            response = client.post(
                "/api/v1/predictive/score",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["qualification_score"] == 5
            assert data["qualification_percentage"] == 75
            assert abs(data["closing_probability"] - 0.68) < 0.01
            assert data["priority_level"] == "high"
            assert data["overall_priority_score"] == 76.0
            assert len(data["risk_factors"]) > 0
            assert len(data["positive_signals"]) > 0

    @pytest.mark.asyncio
    async def test_get_predictive_score_unauthorized(self, client, sample_conversation_request):
        """Test predictive score retrieval without authentication."""
        response = client.post(
            "/api/v1/predictive/score",
            json=sample_conversation_request
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED or \
               response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_lead_insights_success(
        self,
        client,
        auth_headers,
        sample_conversation_request,
        mock_lead_insights
    ):
        """Test successful lead insights retrieval."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.predictive_scorer') as mock_scorer:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_scorer.generate_lead_insights.return_value = mock_lead_insights

            response = client.post(
                "/api/v1/predictive/insights",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["response_pattern_analysis"] == "Highly consistent and engaged responses"
            assert data["engagement_trend"] == "increasing"
            assert data["conversation_quality_score"] == 78.5
            assert data["estimated_time_to_close"] == 32
            assert data["recommended_effort_level"] == "intensive"

    @pytest.mark.asyncio
    async def test_get_action_recommendations_success(
        self,
        client,
        auth_headers,
        sample_conversation_request,
        mock_action_recommendation
    ):
        """Test successful action recommendations retrieval."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.action_engine') as mock_engine:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_engine.generate_action_recommendations.return_value = [mock_action_recommendation]

            response = client.post(
                "/api/v1/predictive/actions",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert isinstance(data, list)
            assert len(data) == 1

            action = data[0]
            assert action["action_type"] == "immediate_call"
            assert action["priority_level"] == 9
            assert action["title"] == "🚨 URGENT: Immediate Phone Call Required"
            assert action["success_probability"] == 0.85
            assert action["estimated_time_investment"] == 30

    @pytest.mark.asyncio
    async def test_get_action_recommendations_with_limit(
        self,
        client,
        auth_headers,
        sample_conversation_request,
        mock_action_recommendation
    ):
        """Test action recommendations with limit parameter."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.action_engine') as mock_engine:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            # Return multiple recommendations
            mock_engine.generate_action_recommendations.return_value = [
                mock_action_recommendation,
                mock_action_recommendation,
                mock_action_recommendation
            ]

            response = client.post(
                "/api/v1/predictive/actions?limit=2",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2  # Should respect limit

    @pytest.mark.asyncio
    async def test_get_action_sequence_success(
        self,
        client,
        auth_headers,
        sample_conversation_request,
        mock_action_recommendation
    ):
        """Test successful action sequence retrieval."""
        mock_sequence = ActionSequence(
            sequence_name="High-Conversion Lead Sequence",
            total_estimated_duration=21,
            success_probability=0.72,
            estimated_revenue=18750.0,
            immediate_actions=[mock_action_recommendation],
            short_term_actions=[],
            medium_term_actions=[],
            long_term_actions=[]
        )

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.action_engine') as mock_engine:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_engine.generate_action_sequence.return_value = mock_sequence

            response = client.post(
                "/api/v1/predictive/action-sequence",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["sequence_name"] == "High-Conversion Lead Sequence"
            assert data["total_estimated_duration"] == 21
            assert data["success_probability"] == 0.72
            assert len(data["immediate_actions"]) == 1
            assert data["immediate_actions"][0]["action_type"] == "immediate_call"

    @pytest.mark.asyncio
    async def test_optimize_timing_success(
        self,
        client,
        auth_headers,
        sample_conversation_request
    ):
        """Test successful timing optimization."""
        mock_timing = TimingOptimization(
            best_call_times=["9:00-11:00 AM", "2:00-4:00 PM"],
            best_days=["Tuesday", "Wednesday", "Thursday"],
            avoid_times=["Before 8 AM", "After 7 PM"],
            urgency_window="24-48 hours",
            competitive_timing="Competitive market - respond within 2 hours"
        )

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.action_engine') as mock_engine:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_engine.optimize_timing.return_value = mock_timing

            response = client.post(
                "/api/v1/predictive/timing-optimization?action_type=immediate_call",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["action_type"] == "immediate_call"
            assert data["best_call_times"] == ["9:00-11:00 AM", "2:00-4:00 PM"]
            assert data["best_days"] == ["Tuesday", "Wednesday", "Thursday"]
            assert data["urgency_window"] == "24-48 hours"

    @pytest.mark.asyncio
    async def test_optimize_timing_invalid_action_type(
        self,
        client,
        auth_headers,
        sample_conversation_request
    ):
        """Test timing optimization with invalid action type."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth:
            mock_auth.return_value = {"role": "user", "user_id": "test"}

            response = client.post(
                "/api/v1/predictive/timing-optimization?action_type=invalid_action",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_model_performance_success(self, client, auth_headers):
        """Test successful model performance retrieval."""
        mock_metrics = ModelMetrics(
            accuracy=0.82,
            precision=0.78,
            recall=0.84,
            f1_score=0.81,
            auc_score=0.86,
            feature_importances={
                "qualification_completeness": 0.3,
                "engagement_score": 0.25,
                "urgency_score": 0.2
            },
            confusion_matrix=[[50, 5], [8, 37]],
            validation_date=datetime.now()
        )

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.ml_model') as mock_model:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_model.get_model_performance.return_value = mock_metrics
            mock_model.needs_retraining.return_value = False

            response = client.get(
                "/api/v1/predictive/model-performance",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["accuracy"] == 0.82
            assert data["precision"] == 0.78
            assert data["auc_score"] == 0.86
            assert data["needs_retraining"] is False
            assert "qualification_completeness" in data["feature_importances"]

    @pytest.mark.asyncio
    async def test_get_model_performance_no_model(self, client, auth_headers):
        """Test model performance when no model is trained."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.ml_model') as mock_model:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_model.get_model_performance.return_value = None

            response = client.get(
                "/api/v1/predictive/model-performance",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["accuracy"] == 0.0
            assert data["needs_retraining"] is True

    @pytest.mark.asyncio
    async def test_train_model_admin_success(self, client, auth_headers):
        """Test successful model training with admin privileges."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth:
            mock_auth.return_value = {"role": "admin", "user_id": "admin"}

            response = client.post(
                "/api/v1/predictive/train-model?use_synthetic_data=true",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "training_started"
            assert data["use_synthetic_data"] is True

    @pytest.mark.asyncio
    async def test_train_model_non_admin_forbidden(self, client, auth_headers):
        """Test model training without admin privileges."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth:
            mock_auth.return_value = {"role": "user", "user_id": "test"}

            response = client.post(
                "/api/v1/predictive/train-model",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_pipeline_status_success(self, client, auth_headers):
        """Test successful pipeline status retrieval."""
        mock_metrics = ModelMetrics(
            accuracy=0.82,
            precision=0.78,
            recall=0.84,
            f1_score=0.81,
            auc_score=0.86,
            feature_importances={},
            confusion_matrix=[[50, 5], [8, 37]],
            validation_date=datetime.now()
        )

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.ml_model') as mock_model:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_model.get_model_performance.return_value = mock_metrics
            mock_model.needs_retraining.return_value = False
            mock_model.last_training_date = datetime.now()

            response = client.get(
                "/api/v1/predictive/pipeline-status",
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["pipeline_health"] == "healthy"
            assert data["ml_model"]["trained"] is True
            assert data["ml_model"]["needs_retraining"] is False
            assert data["services"]["predictive_scorer"] == "active"
            assert data["cache"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_batch_score_leads_success(
        self,
        client,
        auth_headers,
        mock_predictive_score
    ):
        """Test successful batch lead scoring."""
        batch_request = [
            {
                "conversation_history": [{"role": "user", "text": "Hello"}],
                "extracted_preferences": {"budget": "500k"},
                "lead_id": "lead_1"
            },
            {
                "conversation_history": [{"role": "user", "text": "Hi there"}],
                "extracted_preferences": {"budget": "600k"},
                "lead_id": "lead_2"
            }
        ]

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.predictive_scorer') as mock_scorer:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            mock_scorer.calculate_predictive_score.return_value = mock_predictive_score

            response = client.post(
                "/api/v1/predictive/batch-score",
                json=batch_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["summary"]["total_processed"] == 2
            assert data["summary"]["successful"] == 2
            assert data["summary"]["failed"] == 0
            assert len(data["results"]) == 2
            assert all(result["status"] == "success" for result in data["results"])

    @pytest.mark.asyncio
    async def test_batch_score_leads_too_large(self, client, auth_headers):
        """Test batch scoring with too many leads."""
        # Create a batch that's too large (>50 leads)
        large_batch = [
            {
                "conversation_history": [{"role": "user", "text": f"Hello {i}"}],
                "extracted_preferences": {},
                "lead_id": f"lead_{i}"
            }
            for i in range(51)
        ]

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth:
            mock_auth.return_value = {"role": "user", "user_id": "test"}

            response = client.post(
                "/api/v1/predictive/batch-score",
                json=large_batch,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_error_handling_in_endpoints(self, client, auth_headers, sample_conversation_request):
        """Test error handling in API endpoints."""
        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth, \
             patch('ghl_real_estate_ai.api.routes.predictive_analytics.predictive_scorer') as mock_scorer:

            mock_auth.return_value = {"role": "user", "user_id": "test"}
            # Simulate an error in the scoring service
            mock_scorer.calculate_predictive_score.side_effect = Exception("Service error")

            response = client.post(
                "/api/v1/predictive/score",
                json=sample_conversation_request,
                headers=auth_headers
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "error" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_invalid_request_data(self, client, auth_headers):
        """Test endpoints with invalid request data."""
        invalid_request = {
            "invalid_field": "invalid_data"
        }

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth:
            mock_auth.return_value = {"role": "user", "user_id": "test"}

            response = client.post(
                "/api/v1/predictive/score",
                json=invalid_request,
                headers=auth_headers
            )

            # Should handle gracefully or return validation error
            assert response.status_code in [400, 422, 500]  # Various possible error codes

    @pytest.mark.asyncio
    async def test_request_validation(self, client, auth_headers):
        """Test request validation with missing required fields."""
        # Missing conversation_history
        incomplete_request = {
            "extracted_preferences": {"budget": "500k"}
        }

        with patch('ghl_real_estate_ai.api.routes.predictive_analytics.verify_jwt_token') as mock_auth:
            mock_auth.return_value = {"role": "user", "user_id": "test"}

            response = client.post(
                "/api/v1/predictive/score",
                json=incomplete_request,
                headers=auth_headers
            )

            # Pydantic should validate and possibly set defaults
            # The exact behavior depends on how the model is configured
            assert response.status_code in [200, 422]  # Either works with defaults or validation error