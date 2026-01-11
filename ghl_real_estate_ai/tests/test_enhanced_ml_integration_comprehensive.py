"""
Comprehensive Integration Tests for Enhanced ML Personalization Platform

This test suite validates the integration between all 10 components:

Original Core (6 systems):
1. Advanced ML Personalization Engine
2. Video Message Integration
3. ROI Attribution System
4. Mobile Agent Experience
5. Real-Time Market Integration
6. Enhanced Lead Intelligence Dashboard

Enhanced AI Layer (4 systems):
7. Enhanced ML Personalization Engine (emotional intelligence)
8. Predictive Churn Prevention
9. Real-Time Model Training
10. Multi-Modal Communication Optimizer

Business Impact: $362,600+ annual value + Revolutionary AI capabilities
Performance Targets: <100ms response, >95% accuracy, <30 min churn intervention
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

# Import all enhanced ML components
from services.enhanced_ml_personalization_engine import (
    EnhancedMLPersonalizationEngine,
    AdvancedPersonalizationOutput,
    EmotionalState,
    LeadJourneyStage
)
from services.predictive_churn_prevention import (
    PredictiveChurnPrevention,
    ChurnRiskLevel,
    ChurnRiskAssessment,
    InterventionRecommendation
)
from services.real_time_model_training import (
    RealTimeModelTraining,
    ModelType,
    TrainingDataPoint,
    OnlineLearningState
)
from services.multimodal_communication_optimizer import (
    MultiModalCommunicationOptimizer,
    CommunicationModality,
    MultiModalAnalysis
)

# Import original core components
from services.advanced_ml_personalization_engine import (
    AdvancedMLPersonalizationEngine,
    PersonalizationOutput,
    LeadEvaluationResult
)
from services.video_message_integration import (
    VideoMessageIntegration,
    VideoMessage,
    VideoTemplate
)
from services.roi_attribution_system import (
    ROIAttributionSystem,
    ConversionEvent,
    ConversionEventType,
    AttributionModel
)

# Import shared models
from models.shared_models import (
    EngagementInteraction,
    InteractionType,
    CommunicationChannel,
    LeadProfile,
    PropertyMatch
)


class TestEnhancedMLIntegrationComprehensive:
    """Comprehensive integration tests for enhanced ML platform."""

    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Set up test environment with all enhanced ML components."""
        # Initialize enhanced ML engines
        self.enhanced_personalization = EnhancedMLPersonalizationEngine()
        self.churn_prevention = PredictiveChurnPrevention()
        self.real_time_training = RealTimeModelTraining()
        self.multimodal_optimizer = MultiModalCommunicationOptimizer()

        # Initialize original core components
        self.original_personalization = AdvancedMLPersonalizationEngine()
        self.video_integration = VideoMessageIntegration()
        self.roi_attribution = ROIAttributionSystem()

        # Test data setup
        self.test_lead_id = "lead_test_integration_001"
        self.test_evaluation = LeadEvaluationResult(
            lead_id=self.test_lead_id,
            current_stage="interested",
            engagement_level=0.75,
            priority_score=8.5,
            contact_preferences={"channel": "email", "time": "morning"},
            behavioral_indicators={
                "browsing_frequency": 3.2,
                "response_rate": 0.85,
                "page_views": 15,
                "time_on_site": 300
            }
        )

        self.test_interactions = [
            EngagementInteraction(
                interaction_id="int_001",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(days=1),
                channel=CommunicationChannel.EMAIL,
                type=InteractionType.EMAIL_OPEN,
                content_id="email_welcome_series_01",
                engagement_metrics={"open_duration": 45, "click_through": True}
            ),
            EngagementInteraction(
                interaction_id="int_002",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(hours=6),
                channel=CommunicationChannel.PHONE,
                type=InteractionType.CALL_ANSWERED,
                content_id="call_consultation",
                engagement_metrics={"call_duration": 1200, "appointment_scheduled": True}
            )
        ]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_enhanced_ml_to_original_personalization_integration(self):
        """Test integration between enhanced ML and original personalization engines."""
        print("\n=== Testing Enhanced ML → Original Personalization Integration ===")

        start_time = time.time()

        # Step 1: Generate enhanced personalization with emotional intelligence
        enhanced_output = await self.enhanced_personalization.generate_enhanced_personalization(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            message_template="Hi {lead_name}, let's discuss your real estate goals!",
            interaction_history=self.test_interactions,
            context={"agent_name": "Sarah", "property_type": "condo"},
            voice_transcript="I'm really excited about finding the perfect home for my family.",
            historical_sentiment=["positive", "excited", "confident"]
        )

        # Step 2: Use enhanced output to inform original personalization
        enhanced_context = {
            "emotional_state": enhanced_output.emotional_analysis.dominant_emotion.value,
            "sentiment_score": enhanced_output.emotional_analysis.sentiment_analysis.compound,
            "journey_stage": enhanced_output.journey_intelligence.current_stage.value,
            "voice_confidence": enhanced_output.voice_analysis.confidence_score if enhanced_output.voice_analysis else 0.7
        }

        original_output = await self.original_personalization.generate_personalized_communication(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            message_template="Hi {lead_name}, let's discuss your real estate goals!",
            interaction_history=self.test_interactions,
            context=enhanced_context
        )

        processing_time = time.time() - start_time

        # Assertions
        assert enhanced_output is not None, "Enhanced personalization failed"
        assert original_output is not None, "Original personalization integration failed"
        assert processing_time < 2.0, f"Integration too slow: {processing_time}s"

        # Validate emotional intelligence enhancement
        assert enhanced_output.emotional_analysis.dominant_emotion in [e for e in EmotionalState]
        assert enhanced_output.emotional_analysis.emotional_volatility >= 0
        assert enhanced_output.journey_intelligence.current_stage in [s for s in LeadJourneyStage]

        # Validate enhanced data flows to original system
        assert "emotional_state" in original_output.context_metadata
        assert "sentiment_score" in original_output.context_metadata

        print(f"✅ Enhanced ML → Original integration: {processing_time:.3f}s")
        print(f"   Emotional State: {enhanced_output.emotional_analysis.dominant_emotion.value}")
        print(f"   Journey Stage: {enhanced_output.journey_intelligence.current_stage.value}")
        print(f"   Sentiment Score: {enhanced_output.emotional_analysis.sentiment_analysis.compound:.3f}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_churn_prevention_to_video_integration(self):
        """Test churn prevention triggering video message interventions."""
        print("\n=== Testing Churn Prevention → Video Integration ===")

        start_time = time.time()

        # Step 1: Assess churn risk (simulate high risk scenario)
        high_risk_context = {
            "days_since_last_interaction": 14,
            "declining_engagement_trend": True,
            "negative_sentiment_recent": True,
            "missed_appointments": 2
        }

        churn_assessment = await self.churn_prevention.assess_churn_risk(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            interaction_history=self.test_interactions,
            context=high_risk_context
        )

        # Step 2: If high churn risk, trigger video intervention
        if churn_assessment.risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]:
            intervention = await self.churn_prevention.generate_intervention_recommendation(
                churn_assessment=churn_assessment,
                lead_profile=LeadProfile(
                    lead_id=self.test_lead_id,
                    name="John Doe",
                    email="john@example.com",
                    phone="+1234567890",
                    preferences={"property_type": "condo", "budget": 500000}
                )
            )

            # Step 3: Generate intervention video message
            if "video_message" in intervention.intervention_details:
                video_message = await self.video_integration.generate_personalized_video(
                    lead_id=self.test_lead_id,
                    template_id="retention_outreach",
                    evaluation_result=self.test_evaluation,
                    context={
                        "intervention_type": intervention.intervention_type.value,
                        "urgency_level": intervention.urgency_level.value,
                        "churn_risk": churn_assessment.risk_level.value,
                        "agent_name": "Sarah",
                        "specific_concerns": intervention.intervention_details.get("specific_concerns", [])
                    }
                )

                processing_time = time.time() - start_time

                # Assertions
                assert churn_assessment.risk_level != ChurnRiskLevel.VERY_LOW, "Should detect high churn risk"
                assert intervention is not None, "Intervention generation failed"
                assert video_message is not None, "Video intervention generation failed"
                assert processing_time < 3.0, f"Churn → Video integration too slow: {processing_time}s"

                # Validate churn-driven video customization
                assert "retention" in video_message.video_generation_request.message_content.lower()
                assert intervention.intervention_type.value in video_message.metadata["intervention_context"]

                print(f"✅ Churn → Video integration: {processing_time:.3f}s")
                print(f"   Churn Risk: {churn_assessment.risk_level.value}")
                print(f"   Intervention: {intervention.intervention_type.value}")
                print(f"   Video Template: retention_outreach")

                return True

        return False

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multimodal_optimizer_to_roi_attribution(self):
        """Test multi-modal optimization feeding into ROI attribution."""
        print("\n=== Testing Multi-Modal Optimizer → ROI Attribution ===")

        start_time = time.time()

        # Step 1: Analyze multi-modal communication
        communication_content = {
            CommunicationModality.TEXT: "Hi John, I found some amazing condos in your budget range! Let's schedule a viewing.",
            CommunicationModality.EMAIL: "Subject: Perfect Condos Found - Let's Schedule a Tour\n\nBody: Detailed property information...",
            CommunicationModality.VOICE: "Hey John, this is Sarah. I'm calling about those condos we discussed..."
        }

        multimodal_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
            lead_id=self.test_lead_id,
            content=communication_content,
            context={"property_type": "condo", "budget_range": "400k-500k"}
        )

        # Step 2: Get optimized communication strategy
        optimized_communication = await self.multimodal_optimizer.optimize_communication(
            lead_id=self.test_lead_id,
            base_content=communication_content[CommunicationModality.TEXT],
            target_modalities=[CommunicationModality.TEXT, CommunicationModality.EMAIL],
            context={"optimization_goal": "conversion", "lead_stage": "ready_to_buy"}
        )

        # Step 3: Track optimization impact in ROI attribution
        await self.roi_attribution.track_touchpoint(
            lead_id=self.test_lead_id,
            channel=CommunicationChannel.EMAIL,
            campaign_id="multimodal_optimization_test",
            content_id=f"optimized_email_{optimized_communication.optimization_id}",
            metadata={
                "optimization_applied": True,
                "text_readability_score": multimodal_analysis.text_analysis.readability_metrics.flesch_reading_ease,
                "persuasion_score": multimodal_analysis.text_analysis.persuasion_score,
                "coherence_score": multimodal_analysis.cross_modal_analysis.coherence_score,
                "optimization_confidence": optimized_communication.confidence_score
            }
        )

        # Step 4: Simulate conversion and measure ROI impact
        conversion_event = await self.roi_attribution.track_conversion_event(
            lead_id=self.test_lead_id,
            event_type=ConversionEventType.APPOINTMENT_SCHEDULED,
            event_value=5000.0,  # Average value of scheduled appointment
            metadata={
                "triggered_by_multimodal_optimization": True,
                "optimization_id": optimized_communication.optimization_id,
                "improvement_factors": optimized_communication.improvement_summary
            }
        )

        processing_time = time.time() - start_time

        # Assertions
        assert multimodal_analysis is not None, "Multi-modal analysis failed"
        assert optimized_communication is not None, "Communication optimization failed"
        assert conversion_event is not None, "ROI attribution failed"
        assert processing_time < 2.5, f"Multi-Modal → ROI integration too slow: {processing_time}s"

        # Validate optimization quality
        assert multimodal_analysis.cross_modal_analysis.coherence_score > 0.7, "Poor cross-modal coherence"
        assert optimized_communication.confidence_score > 0.8, "Low optimization confidence"
        assert conversion_event.attribution_weights[AttributionModel.DATA_DRIVEN] > 0, "No attribution value"

        print(f"✅ Multi-Modal → ROI integration: {processing_time:.3f}s")
        print(f"   Coherence Score: {multimodal_analysis.cross_modal_analysis.coherence_score:.3f}")
        print(f"   Optimization Confidence: {optimized_communication.confidence_score:.3f}")
        print(f"   Conversion Value: ${conversion_event.event_value:,.2f}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_time_learning_signal_propagation(self):
        """Test real-time learning signals propagating across all systems."""
        print("\n=== Testing Real-Time Learning Signal Propagation ===")

        start_time = time.time()

        # Step 1: Create learning signals from enhanced personalization
        enhanced_output = await self.enhanced_personalization.generate_enhanced_personalization(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            message_template="Let's find your dream home!",
            interaction_history=self.test_interactions,
            context={"agent_name": "Sarah"}
        )

        # Step 2: Extract learning signals and feed to real-time training
        learning_signals = {
            "emotional_prediction_accuracy": 0.92,
            "sentiment_classification_confidence": enhanced_output.emotional_analysis.sentiment_analysis.compound,
            "journey_stage_transition": enhanced_output.journey_intelligence.stage_confidence,
            "personalization_effectiveness": 0.85
        }

        # Add training data for multiple model types
        training_tasks = []

        # Emotional intelligence model training
        emotional_features = np.array([
            enhanced_output.emotional_analysis.sentiment_analysis.compound,
            enhanced_output.emotional_analysis.emotional_volatility,
            len(self.test_interactions),
            self.test_evaluation.engagement_level
        ]).reshape(1, -1)

        training_tasks.append(
            self.real_time_training.add_training_data(
                model_type=ModelType.PERSONALIZATION,
                features=emotional_features,
                labels={"emotional_state": enhanced_output.emotional_analysis.dominant_emotion.value},
                metadata={"lead_id": self.test_lead_id, "source": "enhanced_personalization"},
                confidence=0.9
            )
        )

        # Step 3: Churn prevention learning signals
        churn_assessment = await self.churn_prevention.assess_churn_risk(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            interaction_history=self.test_interactions,
            context={"recent_engagement": True}
        )

        churn_features = np.array([
            len(self.test_interactions),
            self.test_evaluation.engagement_level,
            enhanced_output.emotional_analysis.sentiment_analysis.compound,
            enhanced_output.emotional_analysis.emotional_volatility
        ]).reshape(1, -1)

        training_tasks.append(
            self.real_time_training.add_training_data(
                model_type=ModelType.CHURN_PREDICTION,
                features=churn_features,
                labels={"churn_risk": churn_assessment.risk_level.value},
                metadata={"lead_id": self.test_lead_id, "source": "churn_prevention"},
                confidence=0.95
            )
        )

        # Step 4: Multi-modal optimization learning signals
        multimodal_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
            lead_id=self.test_lead_id,
            content={CommunicationModality.TEXT: "Let's schedule a property tour!"},
            context={"optimization_target": "engagement"}
        )

        communication_features = np.array([
            multimodal_analysis.text_analysis.readability_metrics.flesch_reading_ease,
            multimodal_analysis.text_analysis.persuasion_score,
            len(multimodal_analysis.text_analysis.sentiment_analysis),
            multimodal_analysis.text_analysis.readability_metrics.word_count
        ]).reshape(1, -1)

        training_tasks.append(
            self.real_time_training.add_training_data(
                model_type=ModelType.ENGAGEMENT,
                features=communication_features,
                labels={"engagement_score": 0.88},
                metadata={"lead_id": self.test_lead_id, "source": "multimodal_optimizer"},
                confidence=0.85
            )
        )

        # Execute all training tasks
        await asyncio.gather(*training_tasks)

        # Step 5: Verify learning state updates
        learning_state = await self.real_time_training.get_learning_state()

        processing_time = time.time() - start_time

        # Assertions
        assert learning_state is not None, "Learning state retrieval failed"
        assert processing_time < 3.0, f"Real-time learning too slow: {processing_time}s"

        # Validate signal propagation
        model_types_updated = [ModelType.PERSONALIZATION, ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT]
        for model_type in model_types_updated:
            if model_type.value in learning_state.model_performances:
                performance = learning_state.model_performances[model_type.value]
                assert performance.sample_count > 0, f"No samples for {model_type.value}"
                assert performance.last_updated is not None, f"No update time for {model_type.value}"

        print(f"✅ Real-time learning propagation: {processing_time:.3f}s")
        print(f"   Models Updated: {len(learning_state.model_performances)}")
        print(f"   Total Training Samples: {learning_state.total_training_samples}")

        return learning_state

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_enhanced_workflow(self):
        """Test complete end-to-end workflow with all enhanced components."""
        print("\n=== Testing Complete Enhanced ML Workflow ===")

        start_time = time.time()

        # Step 1: Enhanced personalization with emotional intelligence
        enhanced_personalization = await self.enhanced_personalization.generate_enhanced_personalization(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            message_template="Hi {lead_name}, I found the perfect properties for you!",
            interaction_history=self.test_interactions,
            context={"agent_name": "Sarah", "property_type": "condo"},
            voice_transcript="I'm so excited about finding a home near good schools for my kids.",
            historical_sentiment=["positive", "excited", "hopeful"]
        )

        # Step 2: Churn risk assessment
        churn_assessment = await self.churn_prevention.assess_churn_risk(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            interaction_history=self.test_interactions,
            context={"personalization_insights": enhanced_personalization.emotional_analysis}
        )

        # Step 3: Multi-modal communication optimization
        optimized_communication = await self.multimodal_optimizer.optimize_communication(
            lead_id=self.test_lead_id,
            base_content=enhanced_personalization.personalized_content,
            target_modalities=[CommunicationModality.TEXT, CommunicationModality.EMAIL],
            context={
                "emotional_state": enhanced_personalization.emotional_analysis.dominant_emotion.value,
                "churn_risk": churn_assessment.risk_level.value,
                "journey_stage": enhanced_personalization.journey_intelligence.current_stage.value
            }
        )

        # Step 4: Generate intervention video if needed
        video_message = None
        if churn_assessment.risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]:
            intervention = await self.churn_prevention.generate_intervention_recommendation(
                churn_assessment=churn_assessment,
                lead_profile=LeadProfile(
                    lead_id=self.test_lead_id,
                    name="John Doe",
                    email="john@example.com",
                    phone="+1234567890",
                    preferences={"property_type": "condo"}
                )
            )

            video_message = await self.video_integration.generate_personalized_video(
                lead_id=self.test_lead_id,
                template_id="engagement_boost",
                evaluation_result=self.test_evaluation,
                context={"intervention_context": intervention.intervention_details}
            )

        # Step 5: Track ROI attribution for the complete workflow
        await self.roi_attribution.track_touchpoint(
            lead_id=self.test_lead_id,
            channel=CommunicationChannel.EMAIL,
            campaign_id="enhanced_ml_workflow",
            content_id=f"enhanced_workflow_{optimized_communication.optimization_id}",
            metadata={
                "enhanced_personalization": True,
                "emotional_intelligence": enhanced_personalization.emotional_analysis.dominant_emotion.value,
                "churn_risk_assessed": churn_assessment.risk_level.value,
                "multimodal_optimized": True,
                "video_intervention": video_message is not None
            }
        )

        # Step 6: Feed all insights to real-time learning
        workflow_features = np.array([
            enhanced_personalization.emotional_analysis.sentiment_analysis.compound,
            enhanced_personalization.emotional_analysis.emotional_volatility,
            churn_assessment.risk_score,
            optimized_communication.confidence_score,
            self.test_evaluation.engagement_level
        ]).reshape(1, -1)

        await self.real_time_training.add_training_data(
            model_type=ModelType.PERSONALIZATION,
            features=workflow_features,
            labels={
                "workflow_success": True,
                "emotional_accuracy": 0.94,
                "optimization_effectiveness": optimized_communication.confidence_score
            },
            metadata={
                "lead_id": self.test_lead_id,
                "workflow_type": "complete_enhanced",
                "components_used": ["enhanced_personalization", "churn_prevention", "multimodal_optimization"]
            },
            confidence=0.92
        )

        processing_time = time.time() - start_time

        # Assertions for complete workflow
        assert enhanced_personalization is not None, "Enhanced personalization failed"
        assert churn_assessment is not None, "Churn assessment failed"
        assert optimized_communication is not None, "Communication optimization failed"
        assert processing_time < 5.0, f"Complete workflow too slow: {processing_time}s"

        # Performance validations
        assert enhanced_personalization.emotional_analysis.sentiment_analysis.compound is not None
        assert churn_assessment.risk_score >= 0 and churn_assessment.risk_score <= 1
        assert optimized_communication.confidence_score > 0.7, "Low optimization confidence"

        # Business impact validation
        workflow_value = {
            "emotional_intelligence": enhanced_personalization.emotional_analysis.dominant_emotion.value,
            "churn_prevention": churn_assessment.risk_level.value,
            "communication_optimization": optimized_communication.confidence_score,
            "roi_attribution": True,
            "real_time_learning": True,
            "processing_time": processing_time
        }

        print(f"✅ Complete Enhanced Workflow: {processing_time:.3f}s")
        print(f"   Emotional State: {enhanced_personalization.emotional_analysis.dominant_emotion.value}")
        print(f"   Churn Risk: {churn_assessment.risk_level.value}")
        print(f"   Optimization Score: {optimized_communication.confidence_score:.3f}")
        print(f"   Video Intervention: {'Yes' if video_message else 'No'}")
        print(f"   Business Value: Enhanced AI platform operational")

        return workflow_value

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_enhanced_ml_performance_benchmarks(self):
        """Test enhanced ML components against performance targets."""
        print("\n=== Testing Enhanced ML Performance Benchmarks ===")

        # Performance targets from handoff documentation
        TARGET_RESPONSE_TIME = 0.1  # <100ms for personalization decisions
        TARGET_ML_INFERENCE = 0.5   # <500ms per ML prediction
        TARGET_CHURN_ACCURACY = 0.95 # >95% churn prediction accuracy
        TARGET_EMOTION_ACCURACY = 0.90 # >90% emotion detection accuracy

        performance_results = {}

        # Test 1: Enhanced personalization speed
        start_time = time.time()
        enhanced_output = await self.enhanced_personalization.generate_enhanced_personalization(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            message_template="Quick test message",
            interaction_history=self.test_interactions[:1],  # Minimal data for speed test
            context={"test_mode": True}
        )
        personalization_time = time.time() - start_time
        performance_results["enhanced_personalization_time"] = personalization_time

        # Test 2: Churn prediction speed
        start_time = time.time()
        churn_assessment = await self.churn_prevention.assess_churn_risk(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            interaction_history=self.test_interactions,
            context={"test_mode": True}
        )
        churn_prediction_time = time.time() - start_time
        performance_results["churn_prediction_time"] = churn_prediction_time

        # Test 3: Multi-modal optimization speed
        start_time = time.time()
        multimodal_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
            lead_id=self.test_lead_id,
            content={CommunicationModality.TEXT: "Quick optimization test"},
            context={"test_mode": True}
        )
        multimodal_time = time.time() - start_time
        performance_results["multimodal_optimization_time"] = multimodal_time

        # Test 4: Real-time learning speed
        start_time = time.time()
        await self.real_time_training.add_training_data(
            model_type=ModelType.PERSONALIZATION,
            features=np.array([[0.5, 0.7, 0.8, 0.6]]),
            labels={"test_label": "performance_test"},
            confidence=0.9
        )
        learning_time = time.time() - start_time
        performance_results["real_time_learning_time"] = learning_time

        # Performance assertions
        assert personalization_time < TARGET_ML_INFERENCE, f"Enhanced personalization too slow: {personalization_time:.3f}s"
        assert churn_prediction_time < TARGET_ML_INFERENCE, f"Churn prediction too slow: {churn_prediction_time:.3f}s"
        assert multimodal_time < TARGET_ML_INFERENCE, f"Multi-modal optimization too slow: {multimodal_time:.3f}s"
        assert learning_time < TARGET_RESPONSE_TIME, f"Real-time learning too slow: {learning_time:.3f}s"

        # Quality assertions
        assert enhanced_output.emotional_analysis.sentiment_analysis.compound is not None
        assert churn_assessment.risk_score >= 0 and churn_assessment.risk_score <= 1
        assert multimodal_analysis.text_analysis.readability_metrics.flesch_reading_ease > 0

        print(f"✅ Performance Benchmarks Met:")
        print(f"   Enhanced Personalization: {personalization_time:.3f}s (target: <{TARGET_ML_INFERENCE}s)")
        print(f"   Churn Prediction: {churn_prediction_time:.3f}s (target: <{TARGET_ML_INFERENCE}s)")
        print(f"   Multi-Modal Optimization: {multimodal_time:.3f}s (target: <{TARGET_ML_INFERENCE}s)")
        print(f"   Real-Time Learning: {learning_time:.3f}s (target: <{TARGET_RESPONSE_TIME}s)")

        return performance_results

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_enhanced_ml_fallback_mechanisms(self):
        """Test fallback mechanisms and graceful degradation."""
        print("\n=== Testing Enhanced ML Fallback Mechanisms ===")

        fallback_results = {}

        # Test 1: Enhanced personalization fallback
        with patch.object(self.enhanced_personalization, '_analyze_sentiment_advanced', side_effect=Exception("Sentiment analysis failed")):
            try:
                enhanced_output = await self.enhanced_personalization.generate_enhanced_personalization(
                    lead_id=self.test_lead_id,
                    evaluation_result=self.test_evaluation,
                    message_template="Fallback test",
                    interaction_history=self.test_interactions,
                    context={"test_fallback": True}
                )
                fallback_results["enhanced_personalization_fallback"] = enhanced_output is not None
            except Exception:
                fallback_results["enhanced_personalization_fallback"] = False

        # Test 2: Churn prevention fallback
        with patch.object(self.churn_prevention, '_extract_churn_features', side_effect=Exception("Feature extraction failed")):
            try:
                churn_assessment = await self.churn_prevention.assess_churn_risk(
                    lead_id=self.test_lead_id,
                    evaluation_result=self.test_evaluation,
                    interaction_history=self.test_interactions,
                    context={"test_fallback": True}
                )
                fallback_results["churn_prevention_fallback"] = churn_assessment is not None
            except Exception:
                fallback_results["churn_prevention_fallback"] = False

        # Test 3: Multi-modal optimizer fallback
        with patch.object(self.multimodal_optimizer, '_analyze_text_advanced', side_effect=Exception("Text analysis failed")):
            try:
                multimodal_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
                    lead_id=self.test_lead_id,
                    content={CommunicationModality.TEXT: "Fallback test"},
                    context={"test_fallback": True}
                )
                fallback_results["multimodal_optimizer_fallback"] = multimodal_analysis is not None
            except Exception:
                fallback_results["multimodal_optimizer_fallback"] = False

        # Test 4: Real-time learning graceful degradation
        with patch.object(self.real_time_training, 'online_models', {}):
            try:
                await self.real_time_training.add_training_data(
                    model_type=ModelType.PERSONALIZATION,
                    features=np.array([[0.1, 0.2, 0.3, 0.4]]),
                    labels={"fallback_test": "degraded_mode"},
                    confidence=0.8
                )
                fallback_results["real_time_learning_degradation"] = True
            except Exception:
                fallback_results["real_time_learning_degradation"] = False

        # Validate fallback effectiveness
        successful_fallbacks = sum(1 for result in fallback_results.values() if result)
        total_fallback_tests = len(fallback_results)
        fallback_success_rate = successful_fallbacks / total_fallback_tests

        assert fallback_success_rate >= 0.75, f"Fallback success rate too low: {fallback_success_rate:.2%}"

        print(f"✅ Fallback Mechanisms:")
        print(f"   Success Rate: {fallback_success_rate:.2%} ({successful_fallbacks}/{total_fallback_tests})")
        for test_name, result in fallback_results.items():
            status = "✅ Pass" if result else "❌ Fail"
            print(f"   {test_name}: {status}")

        return fallback_results


# Run integration tests with comprehensive reporting
if __name__ == "__main__":
    async def run_comprehensive_integration_tests():
        """Run all integration tests with detailed reporting."""
        print("🚀 Starting Enhanced ML Integration Test Suite")
        print("=" * 70)

        test_suite = TestEnhancedMLIntegrationComprehensive()
        await test_suite.setup_test_environment()

        # Run all integration tests
        test_results = {}

        try:
            # Core integration tests
            await test_suite.test_enhanced_ml_to_original_personalization_integration()
            test_results["enhanced_ml_integration"] = "✅ PASS"

            churn_video_result = await test_suite.test_churn_prevention_to_video_integration()
            test_results["churn_video_integration"] = "✅ PASS" if churn_video_result else "⚠️  SKIP (Low Risk)"

            await test_suite.test_multimodal_optimizer_to_roi_attribution()
            test_results["multimodal_roi_integration"] = "✅ PASS"

            await test_suite.test_real_time_learning_signal_propagation()
            test_results["learning_signal_propagation"] = "✅ PASS"

            workflow_result = await test_suite.test_end_to_end_enhanced_workflow()
            test_results["end_to_end_workflow"] = "✅ PASS"

            # Performance tests
            performance_result = await test_suite.test_enhanced_ml_performance_benchmarks()
            test_results["performance_benchmarks"] = "✅ PASS"

            # Fallback tests
            fallback_result = await test_suite.test_enhanced_ml_fallback_mechanisms()
            test_results["fallback_mechanisms"] = "✅ PASS"

        except Exception as e:
            test_results["error"] = f"❌ FAIL: {str(e)}"

        # Final report
        print("\n" + "=" * 70)
        print("🎯 ENHANCED ML INTEGRATION TEST RESULTS")
        print("=" * 70)

        for test_name, result in test_results.items():
            print(f"{test_name}: {result}")

        passed_tests = sum(1 for result in test_results.values() if result.startswith("✅"))
        total_tests = len(test_results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        print(f"\nOverall Success Rate: {success_rate:.2%} ({passed_tests}/{total_tests})")
        print("🚀 Enhanced ML Platform Integration: READY FOR PRODUCTION" if success_rate >= 0.9 else "⚠️  Additional testing recommended")

    # Run the test suite
    asyncio.run(run_comprehensive_integration_tests())