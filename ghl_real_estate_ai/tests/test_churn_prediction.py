"""
Comprehensive Test Suite for Churn Prediction System

This test suite provides thorough coverage of the churn prediction and intervention
system components, including unit tests, integration tests, and edge case handling.

Test Categories:
- Feature extraction accuracy
- Prediction model calibration
- Risk stratification logic
- Intervention orchestration
- Integration service coordination
- Error handling and resilience

Author: EnterpriseHub AI
Last Updated: 2026-01-09
"""

import asyncio
import os

# Import system under test
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
import pytest_asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghl_real_estate_ai.prompts.churn_intervention_templates import (
    CriticalRiskTemplates,
    HighRiskTemplates,
    MessageTone,
    TemplateSelector,
)
from ghl_real_estate_ai.services.churn_integration_service import (
    ChurnIntegrationService,
    ChurnPredictionRequest,
    ChurnSystemHealth,
)
from ghl_real_estate_ai.services.churn_intervention_orchestrator import (
    InterventionExecution,
    InterventionOrchestrator,
    InterventionStatus,
    InterventionType,
)
from ghl_real_estate_ai.services.churn_prediction_engine import (
    ChurnFeatureExtractor,
    ChurnFeatures,
    ChurnPrediction,
    ChurnPredictionEngine,
    ChurnRiskPredictor,
    ChurnRiskStratifier,
    ChurnRiskTier,
)


class TestChurnFeatureExtractor:
    """Test suite for feature extraction component"""

    @pytest_asyncio.fixture
    async def feature_extractor(self):
        """Create feature extractor with mocked services"""
        memory_service = AsyncMock()
        lifecycle_tracker = AsyncMock()
        behavioral_engine = AsyncMock()
        lead_scorer = AsyncMock()

        return ChurnFeatureExtractor(
            memory_service=memory_service,
            lifecycle_tracker=lifecycle_tracker,
            behavioral_engine=behavioral_engine,
            lead_scorer=lead_scorer,
        )

    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for testing"""
        return {
            "lead_id": "TEST_LEAD_001",
            "memory_data": {
                "context": {
                    "name": "John Doe",
                    "preferences": {
                        "budget_range": "$300K-$400K",
                        "locations": ["Rancho Cucamonga", "Cedar Park"],
                        "property_types": ["Single-family"],
                    },
                },
                "conversations": [
                    {
                        "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                        "channel": "email",
                        "opened": True,
                        "clicked": False,
                        "response": True,
                    },
                    {
                        "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                        "channel": "sms",
                        "response": False,
                    },
                ],
                "last_interaction": {
                    "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                    "type": "property_inquiry",
                },
            },
            "behavioral_data": {
                "recent_events": [
                    {"timestamp": (datetime.now() - timedelta(days=1)).isoformat(), "event_type": "property_view"},
                    {"timestamp": (datetime.now() - timedelta(days=3)).isoformat(), "event_type": "search_refinement"},
                ],
                "engagement_metrics": {
                    "trend": 0.2,
                    "avg_session_duration": 8.5,
                    "views_per_session": 3.2,
                    "saved_properties": 2.0,
                    "search_refinements": 1.0,
                },
            },
            "lifecycle_data": {
                "current_stage": "property_search",
                "progression_metrics": {"velocity": 0.8, "stagnation_days": 3.0, "backward_transitions": 0.0},
            },
            "scoring_data": {
                "current_score": 75,
                "score_history": [
                    {"score": 75, "timestamp": datetime.now().isoformat()},
                    {"score": 70, "timestamp": (datetime.now() - timedelta(days=7)).isoformat()},
                ],
            },
        }

    @pytest.mark.asyncio
    async def test_feature_extraction_success(self, feature_extractor, sample_lead_data):
        """Test successful feature extraction"""
        # Mock service responses
        feature_extractor.memory_service.get_lead_context.return_value = sample_lead_data["memory_data"]["context"]
        feature_extractor.memory_service.get_conversation_history.return_value = sample_lead_data["memory_data"][
            "conversations"
        ]
        feature_extractor.memory_service.get_last_interaction.return_value = sample_lead_data["memory_data"][
            "last_interaction"
        ]

        feature_extractor.behavioral_engine.get_recent_events.return_value = sample_lead_data["behavioral_data"][
            "recent_events"
        ]
        feature_extractor.behavioral_engine.calculate_engagement_metrics.return_value = sample_lead_data[
            "behavioral_data"
        ]["engagement_metrics"]
        feature_extractor.behavioral_engine.analyze_patterns.return_value = {}

        feature_extractor.lifecycle_tracker.get_current_stage.return_value = sample_lead_data["lifecycle_data"][
            "current_stage"
        ]
        feature_extractor.lifecycle_tracker.get_progression_metrics.return_value = sample_lead_data["lifecycle_data"][
            "progression_metrics"
        ]

        feature_extractor.lead_scorer.get_current_score.return_value = sample_lead_data["scoring_data"]["current_score"]
        feature_extractor.lead_scorer.get_score_history.return_value = sample_lead_data["scoring_data"]["score_history"]

        # Extract features
        features = await feature_extractor.extract_features(sample_lead_data["lead_id"])

        # Verify feature structure
        assert isinstance(features, ChurnFeatures)
        assert features.days_since_last_interaction == 2.0
        assert features.interaction_frequency_7d >= 0
        assert features.engagement_trend == 0.2
        assert features.stage_stagnation_days == 3.0

        # Verify feature vector conversion
        feature_vector = features.to_vector()
        assert isinstance(feature_vector, np.ndarray)
        assert len(feature_vector) == len(features.to_dict())

    @pytest.mark.asyncio
    async def test_feature_extraction_service_failure(self, feature_extractor):
        """Test feature extraction with service failures"""
        # Mock service failures
        feature_extractor.memory_service.get_lead_context.side_effect = Exception("Memory service unavailable")

        # Should return default features instead of failing
        features = await feature_extractor.extract_features("FAILED_LEAD")

        assert isinstance(features, ChurnFeatures)
        # Should have default values
        assert features.days_since_last_interaction == 7.0
        assert features.interaction_frequency_7d == 1.0

    def test_feature_to_dict_conversion(self):
        """Test feature dictionary conversion"""
        features = ChurnFeatures(
            days_since_last_interaction=5.0,
            interaction_frequency_7d=3.0,
            interaction_frequency_14d=6.0,
            interaction_frequency_30d=12.0,
            response_rate_7d=0.8,
            response_rate_14d=0.7,
            response_rate_30d=0.6,
            engagement_trend=0.1,
            session_duration_avg=10.0,
            property_views_per_session=4.0,
            saved_properties_count=3.0,
            search_refinements_count=2.0,
            stage_progression_velocity=0.5,
            stage_stagnation_days=2.0,
            backward_stage_transitions=0.0,
            qualification_score_change=5.0,
            email_open_rate=0.6,
            email_click_rate=0.3,
            sms_response_rate=0.7,
            call_pickup_rate=0.8,
            preferred_communication_channel_consistency=0.9,
            budget_range_changes=1.0,
            location_preference_changes=0.0,
            property_type_changes=0.0,
            feature_requirements_changes=1.0,
            market_activity_correlation=0.5,
            seasonal_activity_alignment=0.7,
        )

        feature_dict = features.to_dict()
        assert len(feature_dict) == 27  # All features present
        assert feature_dict["days_since_last_interaction"] == 5.0
        assert feature_dict["engagement_trend"] == 0.1


class TestChurnRiskPredictor:
    """Test suite for risk prediction model"""

    @pytest.fixture
    def risk_predictor(self):
        """Create risk predictor with default models"""
        return ChurnRiskPredictor(model_path=None)

    @pytest.fixture
    def sample_features(self):
        """Sample features for testing predictions"""
        return ChurnFeatures(
            days_since_last_interaction=10.0,  # High risk factor
            interaction_frequency_7d=1.0,  # Low engagement
            interaction_frequency_14d=2.0,
            interaction_frequency_30d=5.0,
            response_rate_7d=0.3,  # Low response
            response_rate_14d=0.4,
            response_rate_30d=0.5,
            engagement_trend=-0.2,  # Declining
            session_duration_avg=3.0,
            property_views_per_session=1.5,
            saved_properties_count=0.0,
            search_refinements_count=0.0,
            stage_progression_velocity=0.1,  # Slow progression
            stage_stagnation_days=15.0,  # High stagnation
            backward_stage_transitions=1.0,
            qualification_score_change=-10.0,  # Declining score
            email_open_rate=0.2,
            email_click_rate=0.1,
            sms_response_rate=0.3,
            call_pickup_rate=0.4,
            preferred_communication_channel_consistency=0.5,
            budget_range_changes=3.0,
            location_preference_changes=2.0,
            property_type_changes=1.0,
            feature_requirements_changes=2.0,
            market_activity_correlation=0.3,
            seasonal_activity_alignment=0.4,
        )

    def test_risk_prediction_structure(self, risk_predictor, sample_features):
        """Test risk prediction output structure"""
        risk_scores, confidence = risk_predictor.predict_risk(sample_features)

        # Verify risk scores
        assert isinstance(risk_scores, dict)
        assert "7d" in risk_scores
        assert "14d" in risk_scores
        assert "30d" in risk_scores

        # Verify score ranges
        for horizon, score in risk_scores.items():
            assert 0 <= score <= 100, f"Risk score {score} out of range for {horizon}"

        # Verify confidence
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1, f"Confidence {confidence} out of range"

    def test_feature_importance(self, risk_predictor, sample_features):
        """Test feature importance calculation"""
        importance_list = risk_predictor.get_feature_importance(sample_features)

        assert isinstance(importance_list, list)
        assert len(importance_list) > 0

        # Verify importance structure
        for feature_name, importance in importance_list:
            assert isinstance(feature_name, str)
            assert isinstance(importance, (int, float))
            assert importance >= 0

        # Verify sorted by importance (descending)
        if len(importance_list) > 1:
            assert importance_list[0][1] >= importance_list[1][1]

    def test_high_risk_features_prediction(self, risk_predictor):
        """Test prediction with high-risk features"""
        high_risk_features = ChurnFeatures(
            days_since_last_interaction=25.0,  # Very high
            interaction_frequency_7d=0.0,  # No engagement
            interaction_frequency_14d=0.0,
            interaction_frequency_30d=1.0,
            response_rate_7d=0.0,  # No response
            response_rate_14d=0.1,
            response_rate_30d=0.2,
            engagement_trend=-0.8,  # Severely declining
            session_duration_avg=1.0,
            property_views_per_session=0.5,
            saved_properties_count=0.0,
            search_refinements_count=0.0,
            stage_progression_velocity=-0.2,  # Backward movement
            stage_stagnation_days=30.0,  # Long stagnation
            backward_stage_transitions=3.0,
            qualification_score_change=-25.0,  # Major decline
            email_open_rate=0.0,
            email_click_rate=0.0,
            sms_response_rate=0.0,
            call_pickup_rate=0.2,
            preferred_communication_channel_consistency=0.2,
            budget_range_changes=5.0,
            location_preference_changes=4.0,
            property_type_changes=3.0,
            feature_requirements_changes=4.0,
            market_activity_correlation=0.1,
            seasonal_activity_alignment=0.2,
        )

        risk_scores, confidence = risk_predictor.predict_risk(high_risk_features)

        # High-risk features should produce high risk scores
        assert risk_scores["14d"] > 50, "High-risk features should produce high risk score"


class TestChurnRiskStratifier:
    """Test suite for risk stratification"""

    @pytest.fixture
    def risk_stratifier(self):
        """Create risk stratifier"""
        return ChurnRiskStratifier()

    def test_risk_tier_assignment(self, risk_stratifier):
        """Test risk tier assignment based on scores"""
        # Test critical risk
        critical_scores = {"7d": 85, "14d": 83, "30d": 80}
        tier, recommendations, urgency = risk_stratifier.stratify_risk(critical_scores, [])
        assert tier == ChurnRiskTier.CRITICAL
        assert urgency == "immediate"
        assert len(recommendations) > 0

        # Test high risk
        high_scores = {"7d": 70, "14d": 68, "30d": 65}
        tier, recommendations, urgency = risk_stratifier.stratify_risk(high_scores, [])
        assert tier == ChurnRiskTier.HIGH
        assert urgency == "urgent"

        # Test medium risk
        medium_scores = {"7d": 45, "14d": 43, "30d": 40}
        tier, recommendations, urgency = risk_stratifier.stratify_risk(medium_scores, [])
        assert tier == ChurnRiskTier.MEDIUM
        assert urgency == "moderate"

        # Test low risk
        low_scores = {"7d": 20, "14d": 18, "30d": 15}
        tier, recommendations, urgency = risk_stratifier.stratify_risk(low_scores, [])
        assert tier == ChurnRiskTier.LOW
        assert urgency == "low"

    def test_escalating_risk_urgency(self, risk_stratifier):
        """Test urgency escalation for rapidly increasing risk"""
        # Short-term risk much higher than long-term
        escalating_scores = {"7d": 85, "14d": 70, "30d": 45}
        tier, recommendations, urgency = risk_stratifier.stratify_risk(escalating_scores, [])

        # Should escalate urgency due to rapid increase
        assert urgency in ["urgent", "immediate"]

    def test_factor_specific_recommendations(self, risk_stratifier):
        """Test factor-specific recommendation generation"""
        risk_scores = {"7d": 75, "14d": 73, "30d": 70}
        risk_factors = [("days_since_last_interaction", 0.3), ("response_rate_7d", 0.2), ("email_open_rate", 0.15)]

        tier, recommendations, urgency = risk_stratifier.stratify_risk(risk_scores, risk_factors)

        # Should include factor-specific recommendations
        recommendation_text = " ".join(recommendations).lower()
        assert "outreach" in recommendation_text or "communication" in recommendation_text


class TestInterventionOrchestrator:
    """Test suite for intervention orchestration"""

    @pytest.fixture
    def intervention_orchestrator(self):
        """Create intervention orchestrator with mocked services"""
        reengagement_engine = AsyncMock()
        memory_service = AsyncMock()
        ghl_service = AsyncMock()

        return InterventionOrchestrator(
            reengagement_engine=reengagement_engine, memory_service=memory_service, ghl_service=ghl_service
        )

    @pytest.fixture
    def sample_churn_prediction(self):
        """Sample churn prediction for testing"""
        return ChurnPrediction(
            lead_id="TEST_LEAD_001",
            prediction_timestamp=datetime.now(),
            risk_score_7d=85.0,
            risk_score_14d=78.0,
            risk_score_30d=70.0,
            risk_tier=ChurnRiskTier.CRITICAL,
            confidence=0.85,
            top_risk_factors=[("days_since_last_interaction", 0.25), ("response_rate_7d", 0.20)],
            recommended_actions=["Immediate phone call", "Escalate to senior agent"],
            intervention_urgency="immediate",
            feature_vector={},
            model_version="test-1.0.0",
        )

    @pytest.mark.asyncio
    async def test_intervention_requirement_analysis(self, intervention_orchestrator, sample_churn_prediction):
        """Test intervention requirement analysis"""
        lead_id = sample_churn_prediction.lead_id

        required_interventions = await intervention_orchestrator._analyze_intervention_requirements(
            lead_id, sample_churn_prediction
        )

        assert isinstance(required_interventions, list)
        assert len(required_interventions) > 0

        # Critical risk should trigger high-priority interventions
        intervention_types = [intervention.value for intervention in required_interventions]
        assert "agent_escalation" in intervention_types
        assert "phone_callback" in intervention_types

    @pytest.mark.asyncio
    async def test_rate_limiting(self, intervention_orchestrator):
        """Test intervention rate limiting"""
        lead_id = "RATE_LIMITED_LEAD"

        # Simulate recent interventions
        recent_time = datetime.now() - timedelta(minutes=30)
        intervention_orchestrator._last_intervention_times = {
            (lead_id, InterventionType.EMAIL_REENGAGEMENT): recent_time
        }

        interventions = [InterventionType.EMAIL_REENGAGEMENT, InterventionType.SMS_URGENT]
        filtered = await intervention_orchestrator._filter_rate_limited_interventions(lead_id, interventions)

        # Email should be filtered out due to rate limiting
        assert InterventionType.EMAIL_REENGAGEMENT not in filtered
        assert InterventionType.SMS_URGENT in filtered

    @pytest.mark.asyncio
    async def test_intervention_scheduling(self, intervention_orchestrator, sample_churn_prediction):
        """Test intervention scheduling logic"""
        lead_id = sample_churn_prediction.lead_id
        interventions = [InterventionType.EMAIL_REENGAGEMENT, InterventionType.PHONE_CALLBACK]

        scheduled = await intervention_orchestrator._schedule_interventions(
            lead_id, interventions, sample_churn_prediction
        )

        assert len(scheduled) == len(interventions)

        for execution in scheduled:
            assert isinstance(execution, InterventionExecution)
            assert execution.lead_id == lead_id
            assert execution.status == InterventionStatus.PENDING
            assert execution.scheduled_time > datetime.now() - timedelta(minutes=1)

    @pytest.mark.asyncio
    async def test_intervention_execution(self, intervention_orchestrator, sample_churn_prediction):
        """Test intervention execution with mocked services"""
        # Mock successful execution
        intervention_orchestrator.reengagement_engine.trigger_reengagement_campaign.return_value = {"success": True}

        execution = InterventionExecution(
            execution_id="TEST_EXEC_001",
            lead_id="TEST_LEAD_001",
            intervention_type=InterventionType.EMAIL_REENGAGEMENT,
            trigger_prediction=sample_churn_prediction,
            scheduled_time=datetime.now(),
            personalization_data={"lead_name": "Test Lead"},
        )

        success = await intervention_orchestrator._execute_intervention(execution)
        assert success is True


class TestInterventionTemplates:
    """Test suite for intervention templates"""

    @pytest.fixture
    def sample_personalization_data(self):
        """Sample personalization data for template testing"""
        return {
            "lead_name": "Sarah Johnson",
            "risk_score": "85%",
            "risk_tier": "critical",
            "top_risk_factor": "days_since_last_interaction",
            "days_since_interaction": "12",
            "preferred_locations": "Rancho Cucamonga, CA",
            "budget_range": "$350K - $450K",
            "property_types": "Single-family homes",
            "last_property_viewed": "3-bedroom home in Cedar Park",
            "recommended_actions": ["Immediate phone call", "Property viewing"],
            "urgency_message": "The market is moving quickly in your area",
        }

    def test_critical_risk_template_generation(self, sample_personalization_data):
        """Test critical risk template generation"""
        template = CriticalRiskTemplates.incentive_offer_email(sample_personalization_data)

        assert "subject" in template
        assert "body" in template

        # Verify personalization
        assert "Sarah Johnson" in template["body"]
        assert "12" in template["body"]  # days_since_interaction
        assert "Rancho Cucamonga, CA" in template["body"]

        # Verify urgency indicators
        assert any(keyword in template["subject"].lower() for keyword in ["urgent", "limited", "exclusive", "special"])

    def test_template_selector_routing(self, sample_personalization_data):
        """Test template selector routing logic"""
        # Test critical risk routing
        critical_template = TemplateSelector.select_template(
            risk_tier="critical", intervention_type="incentive_offer", personalization_data=sample_personalization_data
        )

        assert critical_template is not None
        assert "subject" in critical_template
        assert "body" in critical_template

        # Test high risk routing
        high_template = TemplateSelector.select_template(
            risk_tier="high", intervention_type="email_reengagement", personalization_data=sample_personalization_data
        )

        assert high_template is not None
        assert high_template != critical_template  # Should be different templates

    def test_template_personalization_safety(self):
        """Test template personalization with missing data"""
        incomplete_data = {
            "lead_name": "John Doe",
            "risk_score": "60%",
            # Missing other fields
        }

        template = TemplateSelector.select_template(
            risk_tier="medium", intervention_type="email_reengagement", personalization_data=incomplete_data
        )

        # Should not fail with missing data
        assert template is not None
        assert "John Doe" in template["body"]


class TestChurnIntegrationService:
    """Test suite for the main integration service"""

    @pytest.fixture
    def integration_service(self):
        """Create integration service with mocked dependencies"""
        memory_service = AsyncMock()
        lifecycle_tracker = AsyncMock()
        behavioral_engine = AsyncMock()
        lead_scorer = AsyncMock()
        reengagement_engine = AsyncMock()
        ghl_service = AsyncMock()

        return ChurnIntegrationService(
            memory_service=memory_service,
            lifecycle_tracker=lifecycle_tracker,
            behavioral_engine=behavioral_engine,
            lead_scorer=lead_scorer,
            reengagement_engine=reengagement_engine,
            ghl_service=ghl_service,
        )

    @pytest.mark.asyncio
    async def test_prediction_request_validation(self, integration_service):
        """Test prediction request validation"""
        # Valid request
        valid_request = ChurnPredictionRequest(lead_ids=["LEAD_001", "LEAD_002"], force_refresh=False)

        # Should not raise exception
        await integration_service._validate_prediction_request(valid_request)

        # Invalid request - empty lead list
        with pytest.raises(ValueError, match="Lead IDs list cannot be empty"):
            empty_request = ChurnPredictionRequest(lead_ids=[])
            await integration_service._validate_prediction_request(empty_request)

        # Invalid request - too many leads
        with pytest.raises(ValueError, match="exceeds maximum batch size"):
            large_request = ChurnPredictionRequest(lead_ids=[f"LEAD_{i}" for i in range(250)])
            await integration_service._validate_prediction_request(large_request)

    @pytest.mark.asyncio
    async def test_batch_processing(self, integration_service):
        """Test batch processing logic"""
        lead_ids = [f"LEAD_{i:03d}" for i in range(75)]  # 75 leads
        batches = integration_service._batch_lead_ids(lead_ids)

        # Should create batches of max 50 leads
        assert len(batches) == 2  # 50 + 25
        assert len(batches[0]) == 50
        assert len(batches[1]) == 25

    @pytest.mark.asyncio
    async def test_high_risk_identification(self, integration_service):
        """Test high-risk lead identification"""
        # Mock predictions with various risk levels
        mock_predictions = {
            "LEAD_001": Mock(risk_tier=ChurnRiskTier.CRITICAL, risk_score_14d=85.0),
            "LEAD_002": Mock(risk_tier=ChurnRiskTier.HIGH, risk_score_14d=70.0),
            "LEAD_003": Mock(risk_tier=ChurnRiskTier.MEDIUM, risk_score_14d=45.0),
            "LEAD_004": Mock(risk_tier=ChurnRiskTier.LOW, risk_score_14d=20.0),
        }

        high_risk_leads = integration_service._identify_high_risk_leads(mock_predictions)

        # Should identify critical and high risk leads
        assert len(high_risk_leads) == 2
        assert "LEAD_001" in high_risk_leads
        assert "LEAD_002" in high_risk_leads
        assert "LEAD_003" not in high_risk_leads

        # Should be sorted by risk score (descending)
        assert high_risk_leads[0] == "LEAD_001"  # Highest score first

    @pytest.mark.asyncio
    async def test_manual_intervention_execution(self, integration_service):
        """Test manual intervention execution"""
        # Mock prediction generation
        with patch.object(integration_service.prediction_engine, "predict_churn_risk") as mock_predict:
            mock_prediction = Mock(
                risk_score_14d=75.0, risk_tier=ChurnRiskTier.HIGH, confidence=0.8, intervention_urgency="urgent"
            )
            mock_predict.return_value = mock_prediction

            # Mock intervention execution
            with patch.object(integration_service.intervention_orchestrator, "_execute_intervention") as mock_execute:
                mock_execute.return_value = True

                result = await integration_service.execute_manual_intervention(
                    lead_id="LEAD_001", intervention_type="phone_callback", urgency_override="immediate"
                )

                assert result["success"] is True
                assert result["lead_id"] == "LEAD_001"
                assert result["intervention_type"] == "phone_callback"
                assert "intervention_id" in result

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, integration_service):
        """Test system health monitoring"""
        health = await integration_service.get_system_health()

        assert isinstance(health, ChurnSystemHealth)
        assert hasattr(health, "prediction_engine_status")
        assert hasattr(health, "intervention_orchestrator_status")
        assert hasattr(health, "service_dependencies")
        assert isinstance(health.service_dependencies, dict)

    def test_error_handling_resilience(self, integration_service):
        """Test error handling and system resilience"""
        # Test error response creation
        error_response = integration_service._create_error_response("Test error")

        assert error_response.predictions == {}
        assert error_response.high_risk_leads == []
        assert len(error_response.errors) == 1
        assert "Test error" in error_response.errors[0]


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_empty_feature_data(self):
        """Test handling of empty/null feature data"""
        feature_extractor = ChurnFeatureExtractor(
            memory_service=AsyncMock(),
            lifecycle_tracker=AsyncMock(),
            behavioral_engine=AsyncMock(),
            lead_scorer=AsyncMock(),
        )

        # Mock empty responses from all services
        feature_extractor.memory_service.get_lead_context.return_value = {}
        feature_extractor.memory_service.get_conversation_history.return_value = []
        feature_extractor.memory_service.get_last_interaction.return_value = {}
        feature_extractor.behavioral_engine.get_recent_events.return_value = []
        feature_extractor.behavioral_engine.calculate_engagement_metrics.return_value = {}
        feature_extractor.lifecycle_tracker.get_progression_metrics.return_value = {}
        feature_extractor.lead_scorer.get_score_history.return_value = []

        # Should return default features without failing
        features = await feature_extractor.extract_features("EMPTY_LEAD")
        assert isinstance(features, ChurnFeatures)

    def test_invalid_risk_scores(self):
        """Test handling of invalid risk score values"""
        stratifier = ChurnRiskStratifier()

        # Test with negative scores
        negative_scores = {"7d": -10, "14d": -5, "30d": 0}
        tier, recommendations, urgency = stratifier.stratify_risk(negative_scores, [])

        # Should handle gracefully
        assert tier in [ChurnRiskTier.LOW, ChurnRiskTier.MEDIUM]
        assert len(recommendations) > 0

        # Test with scores > 100
        high_scores = {"7d": 150, "14d": 120, "30d": 110}
        tier, recommendations, urgency = stratifier.stratify_risk(high_scores, [])

        # Should cap at critical risk
        assert tier == ChurnRiskTier.CRITICAL
        assert urgency == "immediate"

    @pytest.mark.asyncio
    async def test_service_timeout_handling(self):
        """Test handling of service timeouts"""
        # Mock service that times out
        slow_service = AsyncMock()
        slow_service.get_lead_context.side_effect = asyncio.TimeoutError("Service timeout")

        feature_extractor = ChurnFeatureExtractor(
            memory_service=slow_service,
            lifecycle_tracker=AsyncMock(),
            behavioral_engine=AsyncMock(),
            lead_scorer=AsyncMock(),
        )

        # Should handle timeout gracefully
        features = await feature_extractor.extract_features("TIMEOUT_LEAD")
        assert isinstance(features, ChurnFeatures)

    def test_feature_vector_consistency(self):
        """Test feature vector consistency across different instances"""
        features1 = ChurnFeatures(
            days_since_last_interaction=5.0,
            interaction_frequency_7d=3.0,
            interaction_frequency_14d=6.0,
            interaction_frequency_30d=12.0,
            response_rate_7d=0.8,
            response_rate_14d=0.7,
            response_rate_30d=0.6,
            engagement_trend=0.1,
            session_duration_avg=10.0,
            property_views_per_session=4.0,
            saved_properties_count=3.0,
            search_refinements_count=2.0,
            stage_progression_velocity=0.5,
            stage_stagnation_days=2.0,
            backward_stage_transitions=0.0,
            qualification_score_change=5.0,
            email_open_rate=0.6,
            email_click_rate=0.3,
            sms_response_rate=0.7,
            call_pickup_rate=0.8,
            preferred_communication_channel_consistency=0.9,
            budget_range_changes=1.0,
            location_preference_changes=0.0,
            property_type_changes=0.0,
            feature_requirements_changes=1.0,
            market_activity_correlation=0.5,
            seasonal_activity_alignment=0.7,
        )

        features2 = ChurnFeatures(
            days_since_last_interaction=5.0,
            interaction_frequency_7d=3.0,
            interaction_frequency_14d=6.0,
            interaction_frequency_30d=12.0,
            response_rate_7d=0.8,
            response_rate_14d=0.7,
            response_rate_30d=0.6,
            engagement_trend=0.1,
            session_duration_avg=10.0,
            property_views_per_session=4.0,
            saved_properties_count=3.0,
            search_refinements_count=2.0,
            stage_progression_velocity=0.5,
            stage_stagnation_days=2.0,
            backward_stage_transitions=0.0,
            qualification_score_change=5.0,
            email_open_rate=0.6,
            email_click_rate=0.3,
            sms_response_rate=0.7,
            call_pickup_rate=0.8,
            preferred_communication_channel_consistency=0.9,
            budget_range_changes=1.0,
            location_preference_changes=0.0,
            property_type_changes=0.0,
            feature_requirements_changes=1.0,
            market_activity_correlation=0.5,
            seasonal_activity_alignment=0.7,
        )

        # Identical features should produce identical vectors
        vector1 = features1.to_vector()
        vector2 = features2.to_vector()

        assert np.array_equal(vector1, vector2)
        assert len(vector1) == len(vector2)


# Integration Test
@pytest.mark.integration
class TestChurnSystemIntegration:
    """Integration tests for the complete churn system"""

    @pytest_asyncio.fixture
    async def full_system(self):
        """Set up complete system with mocked external services"""
        # Mock external services
        memory_service = AsyncMock()
        lifecycle_tracker = AsyncMock()
        behavioral_engine = AsyncMock()
        lead_scorer = AsyncMock()
        reengagement_engine = AsyncMock()
        ghl_service = AsyncMock()

        # Create integration service
        integration_service = ChurnIntegrationService(
            memory_service=memory_service,
            lifecycle_tracker=lifecycle_tracker,
            behavioral_engine=behavioral_engine,
            lead_scorer=lead_scorer,
            reengagement_engine=reengagement_engine,
            ghl_service=ghl_service,
        )

        return integration_service

    @pytest.mark.asyncio
    async def test_end_to_end_churn_prediction_flow(self, full_system):
        """Test complete end-to-end churn prediction and intervention flow"""
        # Mock realistic service responses
        self._setup_realistic_mocks(full_system)

        # Create prediction request
        request = ChurnPredictionRequest(
            lead_ids=["LEAD_001", "LEAD_002", "LEAD_003"], force_refresh=True, trigger_interventions=True
        )

        # Execute full flow
        response = await full_system.predict_churn_risk(request)

        # Verify response structure
        assert len(response.predictions) == 3
        assert len(response.high_risk_leads) >= 0
        assert isinstance(response.processing_summary, dict)
        assert response.processing_summary["total_predictions"] == 3

        # Verify predictions have required fields
        for lead_id, prediction in response.predictions.items():
            assert isinstance(prediction, ChurnPrediction)
            assert prediction.lead_id == lead_id
            assert 0 <= prediction.risk_score_14d <= 100
            assert prediction.risk_tier in ChurnRiskTier
            assert len(prediction.recommended_actions) > 0

    def _setup_realistic_mocks(self, integration_service):
        """Set up realistic mock responses for integration testing"""
        # Mock memory service responses
        integration_service.memory_service.get_lead_context.return_value = {
            "name": "Integration Test Lead",
            "preferences": {
                "budget_range": "$400K-$500K",
                "locations": ["Rancho Cucamonga"],
                "property_types": ["Condo"],
            },
        }

        integration_service.memory_service.get_conversation_history.return_value = [
            {
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "channel": "email",
                "opened": True,
                "clicked": True,
                "response": True,
            }
        ]

        integration_service.memory_service.get_last_interaction.return_value = {
            "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
            "type": "property_inquiry",
        }

        # Mock behavioral engine responses
        integration_service.behavioral_engine.get_recent_events.return_value = [
            {"timestamp": (datetime.now() - timedelta(days=2)).isoformat(), "event_type": "property_view"}
        ]

        integration_service.behavioral_engine.calculate_engagement_metrics.return_value = {
            "trend": 0.1,
            "avg_session_duration": 5.0,
            "views_per_session": 2.0,
            "saved_properties": 1.0,
            "search_refinements": 0.0,
        }

        integration_service.behavioral_engine.analyze_patterns.return_value = {}

        # Mock lifecycle tracker responses
        integration_service.lifecycle_tracker.get_current_stage.return_value = "property_search"
        integration_service.lifecycle_tracker.get_stage_history.return_value = []
        integration_service.lifecycle_tracker.get_progression_metrics.return_value = {
            "velocity": 0.3,
            "stagnation_days": 5.0,
            "backward_transitions": 0.0,
        }

        # Mock lead scorer responses
        integration_service.lead_scorer.get_current_score.return_value = 65
        integration_service.lead_scorer.get_score_history.return_value = [
            {"score": 65, "timestamp": datetime.now().isoformat()},
            {"score": 60, "timestamp": (datetime.now() - timedelta(days=7)).isoformat()},
        ]

        integration_service.lead_scorer.get_qualification_factors.return_value = {}

        # Mock intervention execution
        integration_service.reengagement_engine.trigger_reengagement_campaign.return_value = {"success": True}
        integration_service.ghl_service.trigger_workflow.return_value = {"success": True}


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
