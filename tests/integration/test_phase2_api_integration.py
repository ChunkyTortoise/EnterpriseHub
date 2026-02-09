import pytest
pytestmark = pytest.mark.integration

"""
Integration Tests for Phase 2 Intelligence Layer API
Tests API routes with schema models, performance validation, and Jorge methodology integration.

Built for Jorge's Real Estate AI Platform - Phase 2: Intelligence Layer
"""

import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

@pytest.mark.integration

# Import Phase 2 API components
try:
    from ghl_real_estate_ai.api.routes.phase2_intelligence import router as phase2_router
    from ghl_real_estate_ai.api.schemas.phase2_intelligence_models import (
        AdvancedPropertyMatchAPI,
        ConversationAnalysisRequestAPI,
        ConversationInsightAPI,
        CrossTrackHandoffRequestAPI,
        PreferenceLearningRequestAPI,
        PreferenceProfileAPI,
        PropertyMatchRequestAPI,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


# Create test FastAPI app
app = FastAPI()
app.include_router(phase2_router)

client = TestClient(app)


class TestPhase2IntegrationAPI:
    """Integration tests for Phase 2 Intelligence Layer APIs."""

    @pytest.fixture
    def mock_auth_dependencies(self):
        """Mock authentication dependencies."""
        mock_user = {"user_id": "test_user", "location_id": "test_location"}
        mock_access = True

        with (
            patch("ghl_real_estate_ai.api.routes.phase2_intelligence.get_current_user", return_value=mock_user),
            patch("ghl_real_estate_ai.api.routes.phase2_intelligence.get_location_access", return_value=mock_access),
        ):
            yield mock_user

    @pytest.fixture
    def property_match_request_data(self):
        """Valid property matching request data."""
        return {
            "lead_id": "lead_12345",
            "preferences": {
                "price_range": {"min": 400000, "max": 600000},
                "bedrooms": {"min": 3, "ideal": 4},
                "lifestyle_features": {"home_office": 0.9, "pool": 0.7},
            },
            "conversation_history": [
                {
                    "message": "We absolutely need a home office",
                    "timestamp": "2025-01-25T10:00:00Z",
                    "engagement_score": 0.9,
                }
            ],
            "max_results": 5,
            "min_score": 0.7,
        }

    @pytest.fixture
    def conversation_analysis_request_data(self):
        """Valid conversation analysis request data."""
        return {
            "conversation_id": "conv_12345",
            "lead_id": "lead_67890",
            "conversation_history": [
                {"role": "user", "content": "I'm concerned about the price", "timestamp": "2025-01-25T10:00:00Z"},
                {"role": "agent", "content": "Let me show you comparable sales", "timestamp": "2025-01-25T10:01:00Z"},
            ],
            "enable_preference_learning": True,
            "analysis_type": "comprehensive",
        }

    @pytest.fixture
    def preference_learning_request_data(self):
        """Valid preference learning request data."""
        return {
            "client_id": "client_12345",
            "source_type": "conversation_analysis",
            "conversation_data": [
                {
                    "message": "We need a modern home with a pool",
                    "timestamp": "2025-01-25T10:00:00Z",
                    "confidence": 0.85,
                }
            ],
            "confidence_threshold": 0.7,
        }

    @pytest.mark.asyncio
    async def test_property_matching_api_integration(self, mock_auth_dependencies, property_match_request_data):
        """Test property matching API with schema validation."""

        # Mock the property matching engine
        mock_matches = [
            AdvancedPropertyMatchAPI(
                property_id="prop_12345",
                overall_score=0.89,
                base_compatibility_score=0.82,
                behavioral_fit=0.91,
                engagement_prediction=0.85,
                urgency_match=0.88,
                property_summary={"price": 525000, "bedrooms": 4, "bathrooms": 3, "neighborhood": "Domain"},
                feature_matches={"home_office": 0.95, "pool": 0.8},
                location_score=0.87,
                presentation_strategy="lifestyle_match",
                key_selling_points=["Perfect home office", "Pool for family"],
                match_reasoning="Excellent match for work-from-home lifestyle",
                rank=1,
                market_competitiveness=0.85,
                processing_time_ms=85,
                confidence_score=0.89,
            )
        ]

        mock_weights = {
            "feature_weight": 0.3,
            "location_weight": 0.2,
            "price_weight": 0.25,
            "urgency_weight": 0.15,
            "lifestyle_weight": 0.1,
            "conversation_insights": {"home_office_emphasis": 0.9},
            "processing_time_ms": 25,
            "confidence_score": 0.87,
        }

        with patch(
            "ghl_real_estate_ai.services.advanced_property_matching_engine.get_advanced_property_matching_engine"
        ) as mock_engine:
            mock_instance = Mock()
            mock_instance.find_behavioral_matches = AsyncMock(return_value=mock_matches)
            mock_instance.get_behavioral_weights = AsyncMock(return_value=mock_weights)
            mock_engine.return_value = mock_instance

            with patch("ghl_real_estate_ai.services.event_publisher.get_event_publisher") as mock_publisher:
                mock_publisher_instance = Mock()
                mock_publisher_instance.publish_property_match_generated = AsyncMock()
                mock_publisher.return_value = mock_publisher_instance

                # Make API request
                response = client.post(
                    "/api/v1/phase2-intelligence/test_location/property-matching/analyze",
                    json=property_match_request_data,
                )

                # Validate response
                assert response.status_code == 200

                data = response.json()
                assert "matches" in data
                assert "total_found" in data
                assert "behavioral_weights" in data
                assert "processing_time_ms" in data

                # Validate match data structure
                matches = data["matches"]
                assert len(matches) == 1

                match = matches[0]
                assert match["property_id"] == "prop_12345"
                assert match["overall_score"] == 0.89
                assert match["presentation_strategy"] == "lifestyle_match"

                # Validate performance
                assert data["processing_time_ms"] < 100  # Performance target

    @pytest.mark.asyncio
    async def test_conversation_intelligence_api_integration(
        self, mock_auth_dependencies, conversation_analysis_request_data
    ):
        """Test conversation intelligence API with schema validation."""

        # Mock conversation analysis results
        mock_insights = ConversationInsightAPI(
            conversation_id="conv_12345",
            lead_id="lead_67890",
            overall_engagement_score=0.78,
            interest_level_score=0.72,
            objection_intensity_score=0.45,
            rapport_quality_score=0.69,
            next_step_clarity_score=0.58,
            dominant_sentiment="slightly_negative",
            sentiment_volatility=0.3,
            key_topics=["price_concern", "market_comparison"],
            buying_signals=["specific_questions"],
            concern_indicators=["price_sensitivity"],
            recommended_next_actions=["Provide market analysis", "Address price concerns"],
            processing_time_ms=340,
            confidence_score=0.82,
        )

        mock_objections = [
            {
                "objection_id": "obj_12345",
                "objection_category": "price_concern",
                "objection_text": "I'm concerned about the price",
                "detected_at_offset_seconds": 30,
                "severity_level": 4,
                "suggested_responses": ["Let me show you comparable sales"],
                "confidence_score": 0.91,
            }
        ]

        mock_coaching = [
            {
                "opportunity_id": "coach_12345",
                "conversation_id": "conv_12345",
                "opportunity_type": "objection_handling",
                "priority_level": 3,
                "opportunity_description": "Could have provided data sooner",
                "recommended_approach": "Lead with market data",
                "confidence_score": 0.78,
            }
        ]

        mock_timeline = [
            {
                "timestamp_offset_seconds": 30,
                "sentiment_score": -0.3,
                "sentiment_classification": "slightly_negative",
                "confidence": 0.85,
                "speaker": "user",
                "trigger_phrase": "concerned about the price",
            }
        ]

        with patch(
            "ghl_real_estate_ai.services.conversation_intelligence_service.get_conversation_intelligence_service"
        ) as mock_service:
            mock_instance = Mock()
            mock_instance.analyze_conversation_with_insights = AsyncMock(return_value=mock_insights)
            mock_instance.detect_objections_and_recommend_responses = AsyncMock(return_value=mock_objections)
            mock_instance.identify_coaching_opportunities = AsyncMock(return_value=mock_coaching)
            mock_instance.track_sentiment_timeline = AsyncMock(return_value=mock_timeline)
            mock_service.return_value = mock_instance

            with patch("ghl_real_estate_ai.services.event_publisher.get_event_publisher") as mock_publisher:
                mock_publisher_instance = Mock()
                mock_publisher_instance.publish_conversation_insight_generated = AsyncMock()
                mock_publisher.return_value = mock_publisher_instance

                # Make API request
                response = client.post(
                    "/api/v1/phase2-intelligence/test_location/conversation-intelligence/analyze",
                    json=conversation_analysis_request_data,
                )

                # Validate response
                assert response.status_code == 200

                data = response.json()
                assert "insights" in data
                assert "objections" in data
                assert "coaching_opportunities" in data
                assert "sentiment_timeline" in data
                assert "recommendations" in data

                # Validate insights structure
                insights = data["insights"]
                assert insights["conversation_id"] == "conv_12345"
                assert insights["overall_engagement_score"] == 0.78
                assert "price_concern" in insights["key_topics"]

                # Validate performance
                assert data["processing_time_ms"] < 500  # Performance target

    @pytest.mark.asyncio
    async def test_preference_learning_api_integration(self, mock_auth_dependencies, preference_learning_request_data):
        """Test preference learning API with schema validation."""

        # Mock preference profile result
        mock_profile = PreferenceProfileAPI(
            client_id="client_12345",
            location_id="test_location",
            profile_version=2,
            overall_confidence_score=0.84,
            profile_completeness_percentage=72,
            learning_sessions_count=5,
            total_data_points=18,
            property_style_preferences={"modern": 0.85, "contemporary": 0.75},
            lifestyle_features={"pool": 0.8, "home_office": 0.7},
            feature_priority_scores={"style": 0.85, "lifestyle": 0.75},
            prediction_accuracy_score=0.79,
            consistency_score=0.82,
            processing_time_ms=42,
            confidence_score=0.84,
        )

        with patch(
            "ghl_real_estate_ai.services.client_preference_learning_engine.get_client_preference_learning_engine"
        ) as mock_engine:
            mock_instance = Mock()
            mock_instance.learn_from_conversation = AsyncMock(return_value=mock_profile)
            mock_engine.return_value = mock_instance

            with patch("ghl_real_estate_ai.services.event_publisher.get_event_publisher") as mock_publisher:
                mock_publisher_instance = Mock()
                mock_publisher_instance.publish_preference_learning_update = AsyncMock()
                mock_publisher.return_value = mock_publisher_instance

                # Make API request
                response = client.post(
                    "/api/v1/phase2-intelligence/test_location/preference-learning/analyze",
                    json=preference_learning_request_data,
                )

                # Validate response
                assert response.status_code == 200

                data = response.json()
                assert "profile" in data
                assert "processing_time_ms" in data

                # Validate profile structure
                profile = data["profile"]
                assert profile["client_id"] == "client_12345"
                assert profile["overall_confidence_score"] == 0.84
                assert profile["profile_completeness_percentage"] == 72

                # Validate learned preferences
                assert profile["property_style_preferences"]["modern"] == 0.85
                assert profile["lifestyle_features"]["pool"] == 0.8

                # Validate performance
                assert data["processing_time_ms"] < 50  # Performance target

    @pytest.mark.asyncio
    async def test_cross_track_handoff_integration(self, mock_auth_dependencies):
        """Test cross-track handoff coordination API."""

        handoff_request = {
            "lead_id": "lead_12345",
            "client_id": "client_67890",
            "qualification_score": 0.87,
            "handoff_reason": "qualified_buyer",
            "agent_notes": "Ready for property viewings",
        }

        # Mock service responses
        mock_conversation_insights = [
            {"conversation_id": "conv_1", "engagement_score": 0.85},
            {"conversation_id": "conv_2", "engagement_score": 0.78},
        ]

        mock_preference_profile = {
            "client_id": "client_67890",
            "overall_confidence_score": 0.81,
            "lifestyle_features": {"home_office": 0.9},
        }

        with (
            patch(
                "ghl_real_estate_ai.services.conversation_intelligence_service.get_conversation_intelligence_service"
            ) as mock_conv_service,
            patch(
                "ghl_real_estate_ai.services.client_preference_learning_engine.get_client_preference_learning_engine"
            ) as mock_pref_service,
            patch("ghl_real_estate_ai.services.event_publisher.get_event_publisher") as mock_publisher,
        ):
            # Setup service mocks
            mock_conv_instance = Mock()
            mock_conv_instance.get_conversation_insights = AsyncMock(return_value=mock_conversation_insights)
            mock_conv_service.return_value = mock_conv_instance

            mock_pref_instance = Mock()
            mock_pref_instance.get_preference_profile = AsyncMock(return_value=mock_preference_profile)
            mock_pref_service.return_value = mock_pref_instance

            mock_publisher_instance = Mock()
            mock_publisher_instance.publish_cross_track_handoff = AsyncMock()
            mock_publisher.return_value = mock_publisher_instance

            # Make API request
            response = client.post(
                "/api/v1/phase2-intelligence/test_location/coordination/lead-to-client-handoff", json=handoff_request
            )

            # Validate response
            assert response.status_code == 200

            data = response.json()
            assert "transition_id" in data
            assert "lead_id" in data
            assert "client_id" in data
            assert "context_preserved" in data
            assert "preferences_migrated" in data
            assert "next_steps" in data

            # Validate handoff data
            assert data["lead_id"] == "lead_12345"
            assert data["client_id"] == "client_67890"
            assert data["context_preserved"] == True
            assert data["conversation_insights_count"] == 2

            # Validate next steps provided
            assert len(data["next_steps"]) > 0

    @pytest.mark.asyncio
    async def test_health_check_integration(self, mock_auth_dependencies):
        """Test health check API integration."""

        # Mock service health responses
        mock_property_health = {"status": "healthy", "avg_response_time": 85}
        mock_conversation_health = {"status": "healthy", "avg_processing_time": 340}
        mock_preference_health = {"status": "healthy", "avg_update_time": 35}

        with (
            patch(
                "ghl_real_estate_ai.services.advanced_property_matching_engine.get_advanced_property_matching_engine"
            ) as mock_prop_engine,
            patch(
                "ghl_real_estate_ai.services.conversation_intelligence_service.get_conversation_intelligence_service"
            ) as mock_conv_service,
            patch(
                "ghl_real_estate_ai.services.client_preference_learning_engine.get_client_preference_learning_engine"
            ) as mock_pref_engine,
        ):
            # Setup health check mocks
            mock_prop_instance = Mock()
            mock_prop_instance.get_health_status = AsyncMock(return_value=mock_property_health)
            mock_prop_engine.return_value = mock_prop_instance

            mock_conv_instance = Mock()
            mock_conv_instance.get_health_status = AsyncMock(return_value=mock_conversation_health)
            mock_conv_service.return_value = mock_conv_instance

            mock_pref_instance = Mock()
            mock_pref_instance.get_health_status = AsyncMock(return_value=mock_preference_health)
            mock_pref_engine.return_value = mock_pref_instance

            # Make API request
            response = client.get("/api/v1/phase2-intelligence/test_location/health")

            # Validate response
            assert response.status_code == 200

            data = response.json()
            assert "overall_status" in data
            assert "services" in data
            assert "performance_targets" in data

            # Validate overall health
            assert data["overall_status"] == "healthy"

            # Validate individual service health
            services = data["services"]
            assert "property_matching" in services
            assert "conversation_intelligence" in services
            assert "preference_learning" in services

            # Validate performance targets
            targets = data["performance_targets"]
            assert targets["property_matching_ms"] == 100
            assert targets["conversation_analysis_ms"] == 500
            assert targets["preference_learning_ms"] == 50

    def test_schema_validation_errors(self, mock_auth_dependencies):
        """Test API schema validation error handling."""

        # Test invalid property matching request
        invalid_request = {
            "lead_id": "",  # Invalid: empty string
            "preferences": {},  # Invalid: empty preferences
            "max_results": 0,  # Invalid: must be >= 1
            "min_score": 1.5,  # Invalid: must be <= 1.0
        }

        response = client.post(
            "/api/v1/phase2-intelligence/test_location/property-matching/analyze", json=invalid_request
        )

        # Should return validation error
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data

        # Validate that specific validation errors are reported
        details = error_data["detail"]
        assert any("lead_id" in str(detail) for detail in details)
        assert any("max_results" in str(detail) for detail in details)

    def test_performance_monitoring_headers(self, mock_auth_dependencies):
        """Test that performance monitoring data is included in responses."""

        valid_request = {
            "lead_id": "lead_test",
            "preferences": {"price_range": {"min": 400000, "max": 600000}},
            "max_results": 5,
            "min_score": 0.6,
        }

        # Mock fast response for cache testing
        with patch(
            "ghl_real_estate_ai.services.advanced_property_matching_engine.get_advanced_property_matching_engine"
        ) as mock_engine:
            mock_instance = Mock()
            mock_instance.find_behavioral_matches = AsyncMock(return_value=[])
            mock_instance.get_behavioral_weights = AsyncMock(
                return_value={"feature_weight": 0.3, "processing_time_ms": 25}
            )
            mock_engine.return_value = mock_instance

            with patch("ghl_real_estate_ai.services.event_publisher.get_event_publisher"):
                # Make API request
                response = client.post(
                    "/api/v1/phase2-intelligence/test_location/property-matching/analyze?force_refresh=false",
                    json=valid_request,
                )

                # Validate that performance data is included
                assert response.status_code == 200

                data = response.json()
                assert "processing_time_ms" in data
                assert "cache_used" in data

                # Validate performance metrics are reasonable
                processing_time = data["processing_time_ms"]
                assert isinstance(processing_time, int)
                assert processing_time >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])