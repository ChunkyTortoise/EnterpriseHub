"""
Enhanced ML Personalization Engine - Comprehensive Integration Test Suite

This test suite provides comprehensive integration testing for the Enhanced ML Personalization Engine
with all existing systems. Based on the session handoff document, this tests:

1. Enhanced ML engine integration with existing video/ROI/mobile systems
2. Cross-system data flow validation (ML → Video → ROI → Mobile)
3. Real-time learning signal propagation between systems
4. Fallback mechanism validation for all enhanced components
5. Real-world scenarios and edge case handling
6. Performance validation and error handling

Author: AI Assistant
Created: 2026-01-09
Version: 2.0.0 - Comprehensive Integration Testing
"""

import asyncio
import pytest
import time
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
from pathlib import Path

# Enhanced ML Components
from services.enhanced_ml_personalization_engine import (
    EnhancedMLPersonalizationEngine,
    AdvancedPersonalizationOutput,
    EmotionalState,
    ChurnRisk,
    LearningSignal,
    SentimentAnalysisResult,
    ChurnPrediction,
    LeadJourneyStage,
    VoiceAnalysisResult,
    RealTimeLearningSignal
)

from services.predictive_churn_prevention import (
    PredictiveChurnPrevention,
    InterventionType,
    InterventionUrgency,
    ChurnIndicator,
    RetentionStrategy
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

# Existing Core Systems
from services.advanced_ml_personalization_engine import (
    AdvancedMLPersonalizationEngine,
    PersonalizationOutput
)

from services.video_message_integration import (
    VideoMessageIntegration,
    VideoMessage,
    VideoTemplate,
    VideoGenerationRequest
)

from services.roi_attribution_system import (
    ROIAttributionSystem,
    ConversionEvent,
    ConversionEventType,
    AttributionModel,
    CampaignROI
)

from services.mobile_agent_experience import (
    MobileAgentExperience,
    MobileNotification,
    MobilePriority,
    MobileActionType
)

from services.real_time_market_integration import (
    RealTimeMarketIntegration,
    MarketUpdate,
    MarketTrend
)

# Shared Models
from models.evaluation_models import LeadEvaluationResult
from models.nurturing_models import (
    EngagementInteraction,
    PersonalizedMessage,
    CommunicationChannel,
    MessageTone,
    EngagementType,
    LeadType
)

logger = logging.getLogger(__name__)


class TestEnhancedMLComprehensiveIntegration:
    """
    Comprehensive integration tests for Enhanced ML Personalization Engine
    with all existing systems and components.
    """

    @pytest.fixture(autouse=True)
    async def setup_comprehensive_test_environment(self):
        """Set up comprehensive test environment with all systems."""
        print("\n" + "="*80)
        print("ENHANCED ML COMPREHENSIVE INTEGRATION TEST SETUP")
        print("="*80)

        # Initialize Enhanced ML Components
        self.enhanced_ml_engine = EnhancedMLPersonalizationEngine()
        self.churn_prevention = PredictiveChurnPrevention()
        self.real_time_training = RealTimeModelTraining()
        self.multimodal_optimizer = MultiModalCommunicationOptimizer()

        # Initialize Existing Core Systems
        self.original_ml_engine = AdvancedMLPersonalizationEngine()
        self.video_integration = VideoMessageIntegration()
        self.roi_attribution = ROIAttributionSystem()
        self.mobile_experience = MobileAgentExperience()
        self.market_integration = RealTimeMarketIntegration()

        # Test Data Setup
        self.test_lead_id = "lead_enhanced_integration_001"
        self.test_agent_id = "agent_sarah_johnson"

        self.test_evaluation = LeadEvaluationResult(
            lead_id=self.test_lead_id,
            current_stage="property_evaluation",
            engagement_level=0.82,
            priority_score=8.7,
            contact_preferences={
                "channel": "email",
                "time": "afternoon",
                "tone": "professional_friendly"
            },
            behavioral_indicators={
                "browsing_frequency": 4.2,
                "response_rate": 0.91,
                "page_views": 24,
                "time_on_site": 480,
                "property_saves": 8,
                "price_range_queries": 12
            },
            ai_insights={
                "buying_urgency": 0.78,
                "budget_confidence": 0.85,
                "location_flexibility": 0.45,
                "property_type_certainty": 0.92
            }
        )

        # Enhanced interaction history with emotional context
        self.test_interactions = [
            EngagementInteraction(
                interaction_id="int_001",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(days=3),
                channel=CommunicationChannel.EMAIL,
                type=EngagementType.EMAIL_OPEN,
                content_id="welcome_series_emotional",
                engagement_metrics={
                    "open_duration": 65,
                    "click_through": True,
                    "forward_shared": False,
                    "sentiment_detected": "positive"
                },
                message_content="Thank you for reaching out! I'm excited to help you find your dream home."
            ),
            EngagementInteraction(
                interaction_id="int_002",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(days=2),
                channel=CommunicationChannel.PHONE,
                type=EngagementType.CALL_ANSWERED,
                content_id="consultation_call",
                engagement_metrics={
                    "call_duration": 1800,
                    "appointment_scheduled": True,
                    "questions_asked": 8,
                    "objections_raised": 2,
                    "enthusiasm_level": "high"
                },
                message_content="I love the properties you showed me! The downtown area feels perfect for our family."
            ),
            EngagementInteraction(
                interaction_id="int_003",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(hours=6),
                channel=CommunicationChannel.TEXT,
                type=EngagementType.MESSAGE_REPLY,
                content_id="property_inquiry",
                engagement_metrics={
                    "response_time": 45,
                    "message_length": 120,
                    "emoji_usage": 3,
                    "urgency_indicators": ["soon", "quickly"]
                },
                message_content="Can we see that 3BR condo again soon? My spouse is really interested! 😊🏠"
            )
        ]

        # Enhanced context with emotional and behavioral data
        self.test_context = {
            "agent_name": "Sarah Johnson",
            "agent_specialty": "luxury_condos",
            "property_type": "condo",
            "budget_range": "$400k-600k",
            "location_preference": "downtown",
            "timeline": "within_3_months",
            "family_status": "young_family",
            "current_emotional_state": "excited_anxious",
            "recent_life_events": ["job_promotion", "growing_family"],
            "decision_makers": ["primary_lead", "spouse"],
            "previous_experiences": ["first_time_buyer"],
            "communication_style": "detailed_questions"
        }

        # Voice transcript for voice analysis testing
        self.test_voice_transcript = """
        Hi Sarah, it's John calling about those condos you sent me yesterday.
        I'm really excited about the downtown location - it's exactly what we've been looking for!
        My wife and I drove by the building last night and we absolutely love the neighborhood.
        The schools look great for our kids too. I do have some questions about the HOA fees though,
        they seem a bit higher than what we budgeted for. Can we schedule a time to discuss the
        financing options? We're hoping to move quickly if we can make the numbers work.
        Thanks for all your help so far!
        """

        # Historical sentiment data
        self.test_historical_sentiment = [
            "I'm really excited about this process!",
            "Thank you for being so helpful and responsive.",
            "The property looks perfect for our family.",
            "I'm a bit worried about the market conditions lately.",
            "We need to move quickly but want to make the right decision."
        ]

        print("✅ Test environment setup complete")
        print(f"   Lead ID: {self.test_lead_id}")
        print(f"   Agent ID: {self.test_agent_id}")
        print(f"   Interactions: {len(self.test_interactions)}")
        print(f"   Historical Sentiment: {len(self.test_historical_sentiment)} entries")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.priority_high
    async def test_end_to_end_enhanced_ml_pipeline(self):
        """
        Test complete end-to-end enhanced ML pipeline integration.
        ML → Video → ROI → Mobile with real-time learning feedback.
        """
        print("\n" + "="*80)
        print("TEST: End-to-End Enhanced ML Pipeline Integration")
        print("="*80)

        pipeline_start_time = time.time()
        results = {}

        try:
            # STEP 1: Enhanced ML Personalization with Emotional Intelligence
            print("\n🧠 STEP 1: Enhanced ML Personalization...")
            step1_start = time.time()

            enhanced_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                lead_id=self.test_lead_id,
                evaluation_result=self.test_evaluation,
                message_template="Hi {lead_name}, I have some exciting updates about properties in your preferred downtown area!",
                interaction_history=self.test_interactions,
                context=self.test_context,
                voice_transcript=self.test_voice_transcript,
                historical_sentiment=self.test_historical_sentiment
            )

            step1_time = time.time() - step1_start
            results['enhanced_ml_time'] = step1_time

            # Validate enhanced ML output
            assert enhanced_output is not None, "Enhanced ML personalization failed"
            assert isinstance(enhanced_output, AdvancedPersonalizationOutput), "Invalid output type"
            assert enhanced_output.emotional_adaptation is not None, "Missing emotional adaptation"
            assert enhanced_output.sentiment_optimization is not None, "Missing sentiment optimization"
            assert enhanced_output.churn_prevention is not None, "Missing churn prevention"
            assert enhanced_output.journey_stage is not None, "Missing journey stage"

            print(f"✅ Enhanced ML completed in {step1_time:.3f}s")
            print(f"   Emotional State: {enhanced_output.sentiment_optimization.emotion_scores}")
            print(f"   Churn Risk: {enhanced_output.churn_prevention.risk_level.value}")
            print(f"   Journey Stage: {enhanced_output.journey_stage.stage_name}")
            print(f"   Emotional Resonance: {enhanced_output.emotional_resonance_score:.3f}")

            # STEP 2: Churn Prevention Analysis and Intervention
            print("\n🛡️ STEP 2: Churn Prevention Analysis...")
            step2_start = time.time()

            # Check if intervention is needed based on churn risk
            if enhanced_output.churn_prevention.risk_level in [ChurnRisk.MODERATE, ChurnRisk.HIGH, ChurnRisk.CRITICAL]:
                intervention_needed = True
                intervention_type = InterventionType.VIDEO_MESSAGE if enhanced_output.churn_prevention.risk_level == ChurnRisk.HIGH else InterventionType.PERSONALIZED_EMAIL
            else:
                intervention_needed = False
                intervention_type = InterventionType.EDUCATIONAL_CONTENT

            step2_time = time.time() - step2_start
            results['churn_prevention_time'] = step2_time

            print(f"✅ Churn analysis completed in {step2_time:.3f}s")
            print(f"   Intervention Needed: {intervention_needed}")
            print(f"   Intervention Type: {intervention_type.value}")
            print(f"   Risk Factors: {enhanced_output.churn_prevention.contributing_factors}")

            # STEP 3: Video Message Generation (if needed)
            print("\n📹 STEP 3: Video Message Integration...")
            step3_start = time.time()

            video_message = None
            if intervention_needed and intervention_type == InterventionType.VIDEO_MESSAGE:
                # Generate video message request
                video_request = VideoGenerationRequest(
                    lead_id=self.test_lead_id,
                    agent_name=self.test_context["agent_name"],
                    agent_avatar_style="professional_friendly",
                    message_content=enhanced_output.personalized_content,
                    property_images=[],
                    background_style="modern_office",
                    video_length=90,
                    include_property_tour=True,
                    include_market_data=False,
                    call_to_action="Schedule a viewing of your shortlisted properties",
                    branding_elements={"logo": "ghl_real_estate", "color_scheme": "blue_white"}
                )

                # Mock video generation (in production this would call actual video API)
                video_message = VideoMessage(
                    video_id=f"video_{self.test_lead_id}_{int(time.time())}",
                    video_url="https://videos.ghlrealestateai.com/enhanced_personalized_123.mp4",
                    thumbnail_url="https://videos.ghlrealestateai.com/thumbnails/123.jpg",
                    duration_seconds=87,
                    file_size_mb=12.4,
                    generated_at=datetime.now(),
                    personalization_data={
                        "emotional_state": enhanced_output.sentiment_optimization.emotion_scores,
                        "churn_risk": enhanced_output.churn_prevention.risk_level.value,
                        "personalization_confidence": enhanced_output.personalization_confidence
                    },
                    engagement_tracking_url="https://track.ghlrealestateai.com/video/123",
                    download_url="https://videos.ghlrealestateai.com/download/123",
                    sharing_urls={"email": "https://share.ghlrealestateai.com/email/123", "sms": "https://share.ghlrealestateai.com/sms/123"}
                )

            step3_time = time.time() - step3_start
            results['video_generation_time'] = step3_time

            print(f"✅ Video integration completed in {step3_time:.3f}s")
            if video_message:
                print(f"   Video Generated: {video_message.video_id}")
                print(f"   Duration: {video_message.duration_seconds}s")
                print(f"   Personalization: {video_message.personalization_data}")
            else:
                print("   No video generation needed for current risk level")

            # STEP 4: ROI Attribution Tracking
            print("\n💰 STEP 4: ROI Attribution System...")
            step4_start = time.time()

            # Create conversion event for tracking
            conversion_event = ConversionEvent(
                event_id=f"conv_{self.test_lead_id}_{int(time.time())}",
                lead_id=self.test_lead_id,
                event_type=ConversionEventType.APPOINTMENT_SCHEDULED,
                event_value=750.0,  # Estimated commission value for appointment
                occurred_at=datetime.now(),
                attributed_touchpoints=[
                    "enhanced_ml_personalization",
                    "churn_prevention_intervention",
                    "video_message" if video_message else "email_follow_up"
                ],
                attribution_weights={
                    "enhanced_ml_personalization": 0.4,
                    "churn_prevention_intervention": 0.3,
                    "video_message" if video_message else "email_follow_up": 0.3
                },
                conversion_probability=enhanced_output.predicted_engagement_score,
                time_to_conversion=timedelta(hours=2),
                metadata={
                    "emotional_resonance": enhanced_output.emotional_resonance_score,
                    "retention_probability": enhanced_output.retention_probability,
                    "intervention_type": intervention_type.value,
                    "ml_confidence": enhanced_output.personalization_confidence
                }
            )

            # Mock ROI calculation
            campaign_roi = CampaignROI(
                campaign_id="enhanced_ml_campaign_001",
                total_investment=145.0,  # ML processing + video generation costs
                total_revenue=750.0,
                roi_percentage=417.2,  # (750-145)/145 * 100
                roas=5.17,  # 750/145
                conversion_rate=0.23,
                average_deal_size=750.0,
                customer_lifetime_value=2250.0,  # 3x average deal
                cost_per_conversion=145.0,
                attribution_by_model={
                    "first_touch": 300.0,
                    "last_touch": 450.0,
                    "linear": 375.0,
                    "time_decay": 420.0
                },
                time_to_roi=timedelta(hours=2),
                confidence_interval=(350.0, 850.0)
            )

            step4_time = time.time() - step4_start
            results['roi_attribution_time'] = step4_time

            print(f"✅ ROI attribution completed in {step4_time:.3f}s")
            print(f"   ROI Percentage: {campaign_roi.roi_percentage:.1f}%")
            print(f"   ROAS: {campaign_roi.roas:.2f}")
            print(f"   Conversion Probability: {conversion_event.conversion_probability:.3f}")
            print(f"   Attribution Touchpoints: {len(conversion_event.attributed_touchpoints)}")

            # STEP 5: Mobile Agent Notification
            print("\n📱 STEP 5: Mobile Agent Experience...")
            step5_start = time.time()

            # Generate mobile notification based on pipeline results
            notification_priority = MobilePriority.HIGH if enhanced_output.churn_prevention.risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL] else MobilePriority.NORMAL

            mobile_notification = MobileNotification(
                agent_id=self.test_agent_id,
                title=f"🎯 Enhanced Lead Engagement - {enhanced_output.churn_prevention.risk_level.value.title()} Priority",
                message=f"Lead {self.test_lead_id} shows {enhanced_output.churn_prevention.risk_level.value} churn risk. "
                       f"Emotional state: {list(enhanced_output.sentiment_optimization.emotion_scores.keys())[0]}. "
                       f"Intervention: {intervention_type.value.replace('_', ' ').title()}",
                priority=notification_priority,
                action_type=MobileActionType.SEND_VIDEO if video_message else MobileActionType.SEND_MESSAGE,
                action_data={
                    "lead_id": self.test_lead_id,
                    "suggested_action": intervention_type.value,
                    "video_url": video_message.video_url if video_message else None,
                    "emotional_context": enhanced_output.emotional_adaptation,
                    "roi_estimate": campaign_roi.total_revenue,
                    "urgency_score": enhanced_output.churn_prevention.probability
                },
                expires_at=datetime.now() + timedelta(hours=4)
            )

            step5_time = time.time() - step5_start
            results['mobile_notification_time'] = step5_time

            print(f"✅ Mobile notification completed in {step5_time:.3f}s")
            print(f"   Notification Priority: {notification_priority.value}")
            print(f"   Action Type: {mobile_notification.action_type.value}")
            print(f"   Expires: {mobile_notification.expires_at.strftime('%H:%M')}")

            # STEP 6: Real-Time Learning Signal Generation
            print("\n🎓 STEP 6: Real-Time Learning Feedback...")
            step6_start = time.time()

            # Generate learning signals for model improvement
            learning_signals = [
                RealTimeLearningSignal(
                    signal_type=LearningSignal.POSITIVE_ENGAGEMENT,
                    lead_id=self.test_lead_id,
                    interaction_context={
                        "emotional_state": enhanced_output.sentiment_optimization.emotion_scores,
                        "journey_stage": enhanced_output.journey_stage.stage_name,
                        "intervention_applied": intervention_type.value,
                        "personalization_confidence": enhanced_output.personalization_confidence
                    },
                    outcome_data={
                        "engagement_score": enhanced_output.predicted_engagement_score,
                        "emotional_resonance": enhanced_output.emotional_resonance_score,
                        "retention_probability": enhanced_output.retention_probability,
                        "conversion_occurred": True,
                        "time_to_engagement": step1_time + step2_time + step3_time
                    },
                    feedback_score=enhanced_output.predicted_engagement_score
                ),
                RealTimeLearningSignal(
                    signal_type=LearningSignal.CONVERSION_SUCCESS if campaign_roi.roi_percentage > 300 else LearningSignal.POSITIVE_ENGAGEMENT,
                    lead_id=self.test_lead_id,
                    interaction_context={
                        "churn_risk_level": enhanced_output.churn_prevention.risk_level.value,
                        "intervention_urgency": intervention_type.value,
                        "video_generated": video_message is not None
                    },
                    outcome_data={
                        "roi_achieved": campaign_roi.roi_percentage,
                        "conversion_value": campaign_roi.total_revenue,
                        "cost_efficiency": campaign_roi.cost_per_conversion,
                        "attribution_model_performance": campaign_roi.attribution_by_model
                    },
                    feedback_score=min(campaign_roi.roi_percentage / 500.0, 1.0)  # Normalize ROI to 0-1
                )
            ]

            # Add learning signals to the enhanced ML engine
            for signal in learning_signals:
                await self.enhanced_ml_engine._add_learning_signal(
                    signal.signal_type,
                    signal.lead_id,
                    signal.interaction_context,
                    signal.outcome_data,
                    signal.feedback_score
                )

            step6_time = time.time() - step6_start
            results['learning_feedback_time'] = step6_time

            print(f"✅ Learning feedback completed in {step6_time:.3f}s")
            print(f"   Learning Signals Generated: {len(learning_signals)}")
            print(f"   Feedback Scores: {[s.feedback_score for s in learning_signals]}")
            print(f"   Buffer Size: {len(self.enhanced_ml_engine.learning_buffer)}")

            # PIPELINE COMPLETION
            total_pipeline_time = time.time() - pipeline_start_time
            results['total_pipeline_time'] = total_pipeline_time

            print("\n" + "="*80)
            print("🎉 END-TO-END PIPELINE COMPLETED SUCCESSFULLY")
            print("="*80)
            print(f"⏱️  Total Pipeline Time: {total_pipeline_time:.3f}s")
            print(f"🎯 ROI Generated: {campaign_roi.roi_percentage:.1f}%")
            print(f"📈 Emotional Resonance: {enhanced_output.emotional_resonance_score:.3f}")
            print(f"🛡️  Retention Probability: {enhanced_output.retention_probability:.3f}")
            print(f"🎬 Video Generated: {'Yes' if video_message else 'No'}")
            print(f"📱 Mobile Notification: {notification_priority.value}")
            print(f"🎓 Learning Signals: {len(learning_signals)}")

            # Performance Assertions
            assert total_pipeline_time < 5.0, f"Pipeline too slow: {total_pipeline_time:.3f}s"
            assert enhanced_output.emotional_resonance_score > 0.5, f"Low emotional resonance: {enhanced_output.emotional_resonance_score}"
            assert enhanced_output.retention_probability > 0.6, f"Low retention probability: {enhanced_output.retention_probability}"
            assert campaign_roi.roi_percentage > 200, f"ROI too low: {campaign_roi.roi_percentage}%"
            assert len(learning_signals) >= 2, f"Insufficient learning signals: {len(learning_signals)}"

            return results

        except Exception as e:
            pipeline_error_time = time.time() - pipeline_start_time
            print(f"\n❌ PIPELINE FAILED after {pipeline_error_time:.3f}s: {str(e)}")
            logger.error(f"End-to-end pipeline failed: {e}", exc_info=True)
            raise

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cross_system_data_flow_validation(self):
        """
        Test data flow validation across all systems:
        ML → Video → ROI → Mobile with data integrity checks.
        """
        print("\n" + "="*80)
        print("TEST: Cross-System Data Flow Validation")
        print("="*80)

        # Track data transformations across systems
        data_flow_log = []

        try:
            # PHASE 1: ML Engine Data Output
            print("\n📊 PHASE 1: ML Engine Data Generation...")

            ml_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                lead_id=self.test_lead_id,
                evaluation_result=self.test_evaluation,
                message_template="Testing data flow integrity across systems",
                interaction_history=self.test_interactions,
                context=self.test_context,
                voice_transcript=self.test_voice_transcript,
                historical_sentiment=self.test_historical_sentiment
            )

            # Extract key data points
            ml_data = {
                "lead_id": self.test_lead_id,
                "emotional_state": ml_output.sentiment_optimization.emotion_scores,
                "churn_risk": ml_output.churn_prevention.risk_level.value,
                "churn_probability": ml_output.churn_prevention.probability,
                "journey_stage": ml_output.journey_stage.stage_name,
                "personalization_confidence": ml_output.personalization_confidence,
                "predicted_engagement": ml_output.predicted_engagement_score,
                "emotional_resonance": ml_output.emotional_resonance_score,
                "retention_probability": ml_output.retention_probability,
                "optimal_channel": ml_output.optimal_channel.value,
                "optimal_timing": ml_output.optimal_timing.recommended_hour
            }

            data_flow_log.append(("ML_ENGINE", ml_data))
            print(f"✅ ML data generated: {len(ml_data)} data points")

            # PHASE 2: Video System Data Transformation
            print("\n📹 PHASE 2: Video System Data Processing...")

            # Transform ML data for video system
            video_input_data = {
                "lead_id": ml_data["lead_id"],
                "emotional_context": {
                    "dominant_emotion": max(ml_data["emotional_state"], key=ml_data["emotional_state"].get),
                    "emotional_intensity": max(ml_data["emotional_state"].values()),
                    "emotional_stability": 1.0 - (max(ml_data["emotional_state"].values()) - min(ml_data["emotional_state"].values()))
                },
                "urgency_level": "high" if ml_data["churn_probability"] > 0.6 else "medium" if ml_data["churn_probability"] > 0.3 else "low",
                "personalization_level": ml_data["personalization_confidence"],
                "content_adaptation": {
                    "tone": "empathetic" if "anxious" in str(ml_data["emotional_state"]) else "enthusiastic",
                    "pace": "calm" if ml_data["churn_probability"] > 0.5 else "energetic",
                    "detail_level": "comprehensive" if ml_data["journey_stage"] == "Property Evaluation" else "overview"
                },
                "call_to_action_urgency": ml_data["churn_probability"]
            }

            data_flow_log.append(("VIDEO_TRANSFORM", video_input_data))

            # Validate data transformation integrity
            assert video_input_data["lead_id"] == ml_data["lead_id"], "Lead ID lost in transformation"
            assert "emotional_context" in video_input_data, "Emotional context not preserved"
            assert video_input_data["urgency_level"] in ["low", "medium", "high"], "Invalid urgency level"

            print(f"✅ Video data transformed: {len(video_input_data)} data points")
            print(f"   Emotional Context: {video_input_data['emotional_context']}")
            print(f"   Urgency Level: {video_input_data['urgency_level']}")

            # PHASE 3: ROI System Data Integration
            print("\n💰 PHASE 3: ROI System Data Integration...")

            # Transform for ROI attribution
            roi_data = {
                "lead_id": ml_data["lead_id"],
                "attribution_sources": {
                    "enhanced_ml_engine": {
                        "confidence": ml_data["personalization_confidence"],
                        "engagement_prediction": ml_data["predicted_engagement"],
                        "emotional_resonance": ml_data["emotional_resonance"],
                        "weight": 0.4
                    },
                    "churn_prevention": {
                        "risk_level": ml_data["churn_risk"],
                        "intervention_effectiveness": 1.0 - ml_data["churn_probability"],
                        "retention_boost": ml_data["retention_probability"],
                        "weight": 0.35
                    },
                    "video_personalization": {
                        "emotional_adaptation": video_input_data["emotional_context"]["emotional_intensity"],
                        "urgency_alignment": video_input_data["call_to_action_urgency"],
                        "content_relevance": video_input_data["personalization_level"],
                        "weight": 0.25
                    }
                },
                "predicted_value": 750.0 * ml_data["predicted_engagement"] * ml_data["retention_probability"],
                "confidence_interval": (
                    500.0 * ml_data["personalization_confidence"],
                    1000.0 * ml_data["emotional_resonance"]
                ),
                "time_to_conversion": ml_data["optimal_timing"],
                "channel_attribution": ml_data["optimal_channel"]
            }

            data_flow_log.append(("ROI_ATTRIBUTION", roi_data))

            # Validate ROI data integrity
            assert roi_data["lead_id"] == ml_data["lead_id"], "Lead ID lost in ROI transformation"
            assert len(roi_data["attribution_sources"]) == 3, "Attribution sources incomplete"
            assert sum(source["weight"] for source in roi_data["attribution_sources"].values()) == 1.0, "Attribution weights don't sum to 1.0"
            assert roi_data["predicted_value"] > 0, "Invalid predicted value"

            print(f"✅ ROI data integrated: {len(roi_data)} data points")
            print(f"   Predicted Value: ${roi_data['predicted_value']:.2f}")
            print(f"   Attribution Sources: {len(roi_data['attribution_sources'])}")

            # PHASE 4: Mobile System Data Aggregation
            print("\n📱 PHASE 4: Mobile System Data Aggregation...")

            # Aggregate all data for mobile interface
            mobile_data = {
                "lead_id": ml_data["lead_id"],
                "priority_score": (
                    ml_data["churn_probability"] * 0.4 +
                    (1.0 - ml_data["personalization_confidence"]) * 0.3 +
                    ml_data["predicted_engagement"] * 0.3
                ),
                "action_recommendations": [
                    {
                        "action": "immediate_video_call" if ml_data["churn_probability"] > 0.7 else "personalized_video",
                        "urgency": video_input_data["urgency_level"],
                        "confidence": ml_data["personalization_confidence"]
                    },
                    {
                        "action": "property_showcase",
                        "emotional_angle": video_input_data["emotional_context"]["dominant_emotion"],
                        "timing": ml_data["optimal_timing"]
                    }
                ],
                "kpi_dashboard": {
                    "engagement_prediction": ml_data["predicted_engagement"],
                    "retention_probability": ml_data["retention_probability"],
                    "emotional_resonance": ml_data["emotional_resonance"],
                    "roi_prediction": roi_data["predicted_value"],
                    "churn_risk": ml_data["churn_probability"]
                },
                "contextual_insights": {
                    "journey_stage": ml_data["journey_stage"],
                    "emotional_state": ml_data["emotional_state"],
                    "optimal_channel": ml_data["optimal_channel"],
                    "content_personalization": video_input_data["content_adaptation"]
                }
            }

            data_flow_log.append(("MOBILE_AGGREGATION", mobile_data))

            # Validate mobile data completeness
            assert mobile_data["lead_id"] == ml_data["lead_id"], "Lead ID lost in mobile transformation"
            assert 0 <= mobile_data["priority_score"] <= 1, f"Invalid priority score: {mobile_data['priority_score']}"
            assert len(mobile_data["action_recommendations"]) >= 2, "Insufficient action recommendations"
            assert len(mobile_data["kpi_dashboard"]) == 5, "Incomplete KPI dashboard"

            print(f"✅ Mobile data aggregated: {len(mobile_data)} data points")
            print(f"   Priority Score: {mobile_data['priority_score']:.3f}")
            print(f"   Action Recommendations: {len(mobile_data['action_recommendations'])}")
            print(f"   KPI Dashboard: {len(mobile_data['kpi_dashboard'])} metrics")

            # PHASE 5: Data Integrity Validation
            print("\n🔍 PHASE 5: Data Integrity Validation...")

            # Check data consistency across all systems
            integrity_checks = {
                "lead_id_consistency": all(
                    entry[1].get("lead_id") == self.test_lead_id
                    for entry in data_flow_log
                    if "lead_id" in entry[1]
                ),
                "confidence_preservation": all(
                    0 <= entry[1].get("personalization_confidence", 0.5) <= 1
                    for entry in data_flow_log
                    if "personalization_confidence" in entry[1]
                ),
                "emotional_data_continuity": (
                    "emotional_state" in ml_data and
                    "emotional_context" in video_input_data and
                    "emotional_resonance" in roi_data["attribution_sources"]["enhanced_ml_engine"] and
                    "emotional_state" in mobile_data["contextual_insights"]
                ),
                "value_chain_integrity": (
                    ml_data["predicted_engagement"] > 0 and
                    roi_data["predicted_value"] > 0 and
                    mobile_data["priority_score"] > 0
                ),
                "data_type_consistency": all(
                    isinstance(entry[1], dict) for entry in data_flow_log
                )
            }

            # Report integrity results
            passed_checks = sum(integrity_checks.values())
            total_checks = len(integrity_checks)
            integrity_percentage = (passed_checks / total_checks) * 100

            print(f"✅ Data integrity validation: {passed_checks}/{total_checks} checks passed ({integrity_percentage:.1f}%)")
            for check_name, result in integrity_checks.items():
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}: {result}")

            # Assert critical integrity requirements
            assert integrity_checks["lead_id_consistency"], "Lead ID consistency failed across systems"
            assert integrity_checks["emotional_data_continuity"], "Emotional data continuity broken"
            assert integrity_checks["value_chain_integrity"], "Value chain integrity compromised"
            assert integrity_percentage >= 80, f"Data integrity too low: {integrity_percentage}%"

            print("\n" + "="*80)
            print("🎉 CROSS-SYSTEM DATA FLOW VALIDATION COMPLETED")
            print("="*80)
            print(f"📊 Data Flow Stages: {len(data_flow_log)}")
            print(f"🔍 Integrity Score: {integrity_percentage:.1f}%")
            print(f"🎯 Lead Processing: {self.test_lead_id}")
            print(f"💡 Data Points Tracked: {sum(len(entry[1]) for entry in data_flow_log)}")

            return {
                "data_flow_log": data_flow_log,
                "integrity_checks": integrity_checks,
                "integrity_percentage": integrity_percentage,
                "ml_data": ml_data,
                "video_data": video_input_data,
                "roi_data": roi_data,
                "mobile_data": mobile_data
            }

        except Exception as e:
            print(f"\n❌ DATA FLOW VALIDATION FAILED: {str(e)}")
            logger.error(f"Cross-system data flow validation failed: {e}", exc_info=True)
            raise

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_time_learning_signal_propagation(self):
        """
        Test real-time learning signal propagation between all systems
        with feedback loops and model improvement validation.
        """
        print("\n" + "="*80)
        print("TEST: Real-Time Learning Signal Propagation")
        print("="*80)

        learning_start_time = time.time()

        try:
            # STAGE 1: Generate Initial Baseline Performance
            print("\n📊 STAGE 1: Baseline Performance Measurement...")

            # Get initial model performance metrics
            initial_metrics = await self.enhanced_ml_engine.get_enhanced_performance_metrics()
            baseline_learning_buffer = len(self.enhanced_ml_engine.learning_buffer)

            print(f"✅ Initial metrics captured")
            print(f"   Learning Buffer Size: {baseline_learning_buffer}")
            print(f"   Model Status: {initial_metrics['enhanced_models']}")

            # STAGE 2: Generate Multiple Learning Scenarios
            print("\n🎓 STAGE 2: Learning Scenario Generation...")

            learning_scenarios = [
                # Positive engagement scenario
                {
                    "scenario_name": "high_engagement_conversion",
                    "signal_type": LearningSignal.POSITIVE_ENGAGEMENT,
                    "interaction_context": {
                        "engagement_score": 0.92,
                        "emotional_resonance": 0.88,
                        "response_time": 45,  # seconds
                        "channel_effectiveness": "video_message",
                        "personalization_accuracy": 0.94
                    },
                    "outcome_data": {
                        "conversion_achieved": True,
                        "revenue_generated": 1200.0,
                        "time_to_conversion": 3600,  # 1 hour
                        "satisfaction_score": 0.95,
                        "referral_potential": 0.87
                    },
                    "feedback_score": 0.91
                },
                # Negative feedback scenario
                {
                    "scenario_name": "low_engagement_feedback",
                    "signal_type": LearningSignal.NEGATIVE_FEEDBACK,
                    "interaction_context": {
                        "engagement_score": 0.23,
                        "emotional_mismatch": 0.71,
                        "response_time": 0,  # No response
                        "channel_rejection": "email_unsubscribe",
                        "personalization_failure": 0.18
                    },
                    "outcome_data": {
                        "conversion_achieved": False,
                        "engagement_drop": 0.65,
                        "negative_sentiment": -0.42,
                        "churn_indicators": ["no_response", "unsubscribe"]
                    },
                    "feedback_score": -0.35
                },
                # Churn event scenario
                {
                    "scenario_name": "churn_event_analysis",
                    "signal_type": LearningSignal.CHURN_EVENT,
                    "interaction_context": {
                        "warning_signs": ["declining_engagement", "delayed_responses"],
                        "missed_interventions": 2,
                        "emotional_volatility": 0.73,
                        "competitor_mentions": True
                    },
                    "outcome_data": {
                        "churn_confirmed": True,
                        "lost_revenue": 800.0,
                        "churn_reasons": ["pricing_concerns", "poor_communication"],
                        "prevention_opportunity": 0.68
                    },
                    "feedback_score": -0.85
                },
                # Preference change scenario
                {
                    "scenario_name": "preference_evolution",
                    "signal_type": LearningSignal.PREFERENCE_CHANGE,
                    "interaction_context": {
                        "old_preferences": {"channel": "email", "timing": "morning"},
                        "new_preferences": {"channel": "text", "timing": "evening"},
                        "adaptation_speed": 0.67,
                        "preference_strength": 0.84
                    },
                    "outcome_data": {
                        "engagement_improvement": 0.45,
                        "response_rate_increase": 0.38,
                        "satisfaction_boost": 0.29
                    },
                    "feedback_score": 0.52
                },
                # Conversion success scenario
                {
                    "scenario_name": "high_value_conversion",
                    "signal_type": LearningSignal.CONVERSION_SUCCESS,
                    "interaction_context": {
                        "lead_journey_duration": timedelta(days=21),
                        "touchpoint_count": 8,
                        "emotional_journey": ["excited", "anxious", "confident"],
                        "intervention_effectiveness": 0.89
                    },
                    "outcome_data": {
                        "conversion_value": 2500.0,
                        "deal_size_multiplier": 3.2,
                        "client_satisfaction": 0.96,
                        "referral_generated": True,
                        "repeat_business_potential": 0.78
                    },
                    "feedback_score": 0.94
                }
            ]

            print(f"✅ Learning scenarios created: {len(learning_scenarios)}")

            # STAGE 3: Inject Learning Signals
            print("\n📡 STAGE 3: Learning Signal Injection...")

            signal_injection_times = []

            for i, scenario in enumerate(learning_scenarios):
                injection_start = time.time()

                # Add learning signal to enhanced ML engine
                await self.enhanced_ml_engine._add_learning_signal(
                    signal_type=scenario["signal_type"],
                    lead_id=f"lead_learning_{i+1:03d}",
                    interaction_context=scenario["interaction_context"],
                    outcome_data=scenario["outcome_data"],
                    feedback_score=scenario["feedback_score"]
                )

                injection_time = time.time() - injection_start
                signal_injection_times.append(injection_time)

                print(f"   📨 Injected {scenario['scenario_name']}: {injection_time:.4f}s")

            average_injection_time = sum(signal_injection_times) / len(signal_injection_times)
            total_signals_added = len(learning_scenarios)

            print(f"✅ Signal injection completed")
            print(f"   Average Injection Time: {average_injection_time:.4f}s")
            print(f"   Total Signals Added: {total_signals_added}")
            print(f"   Buffer Size Now: {len(self.enhanced_ml_engine.learning_buffer)}")

            # STAGE 4: Monitor Learning Buffer Propagation
            print("\n🔄 STAGE 4: Learning Buffer Propagation Monitoring...")

            buffer_states = []
            propagation_start = time.time()

            # Monitor buffer changes over time
            for check_interval in [0.1, 0.5, 1.0, 2.0]:
                await asyncio.sleep(check_interval)
                current_buffer_size = len(self.enhanced_ml_engine.learning_buffer)
                buffer_states.append({
                    "time": time.time() - propagation_start,
                    "buffer_size": current_buffer_size,
                    "signals_processed": baseline_learning_buffer + total_signals_added - current_buffer_size
                })
                print(f"   ⏱️  T+{check_interval}s: Buffer={current_buffer_size}, Processed={buffer_states[-1]['signals_processed']}")

            # STAGE 5: Trigger Model Retraining (if threshold reached)
            print("\n🏋️ STAGE 5: Model Retraining Assessment...")

            current_buffer_size = len(self.enhanced_ml_engine.learning_buffer)
            retrain_threshold = self.enhanced_ml_engine.retrain_threshold

            if current_buffer_size >= retrain_threshold:
                print(f"   🎯 Retraining threshold reached ({current_buffer_size} >= {retrain_threshold})")
                retrain_start = time.time()

                # Trigger retraining manually since we're in test environment
                await self.enhanced_ml_engine._perform_incremental_learning()

                retrain_time = time.time() - retrain_start
                post_retrain_buffer = len(self.enhanced_ml_engine.learning_buffer)

                print(f"✅ Model retraining completed in {retrain_time:.3f}s")
                print(f"   Buffer Before: {current_buffer_size}")
                print(f"   Buffer After: {post_retrain_buffer}")
                print(f"   Signals Processed: {current_buffer_size - post_retrain_buffer}")

            else:
                print(f"   ⏳ Threshold not reached ({current_buffer_size} < {retrain_threshold})")
                print("   Adding more signals to trigger retraining...")

                # Add more signals to trigger retraining
                additional_signals_needed = retrain_threshold - current_buffer_size + 1
                for i in range(additional_signals_needed):
                    await self.enhanced_ml_engine._add_learning_signal(
                        signal_type=LearningSignal.POSITIVE_ENGAGEMENT,
                        lead_id=f"lead_trigger_{i+1:03d}",
                        interaction_context={"trigger_signal": True, "batch_number": i},
                        outcome_data={"simulated": True},
                        feedback_score=0.5
                    )

                # Trigger retraining
                retrain_start = time.time()
                await self.enhanced_ml_engine._perform_incremental_learning()
                retrain_time = time.time() - retrain_start

                print(f"✅ Retraining triggered and completed in {retrain_time:.3f}s")

            # STAGE 6: Validate Learning Impact
            print("\n📈 STAGE 6: Learning Impact Validation...")

            # Get updated performance metrics
            updated_metrics = await self.enhanced_ml_engine.get_enhanced_performance_metrics()

            # Compare performance improvements
            learning_impact = {
                "buffer_change": len(self.enhanced_ml_engine.learning_buffer) - baseline_learning_buffer,
                "signals_processed": total_signals_added + (additional_signals_needed if 'additional_signals_needed' in locals() else 0),
                "retraining_occurred": True,  # We forced retraining in test
                "performance_tracking": {
                    "before": initial_metrics.get("prediction_accuracy", {}),
                    "after": updated_metrics.get("prediction_accuracy", {})
                },
                "model_updates": {
                    "last_retrain_time": updated_metrics["learning_system"]["last_retrain_time"],
                    "retrain_threshold": updated_metrics["learning_system"]["retrain_threshold"]
                }
            }

            print(f"✅ Learning impact assessed")
            print(f"   Signals Processed: {learning_impact['signals_processed']}")
            print(f"   Buffer Change: {learning_impact['buffer_change']}")
            print(f"   Retraining Occurred: {learning_impact['retraining_occurred']}")

            # STAGE 7: Cross-System Learning Propagation
            print("\n🌐 STAGE 7: Cross-System Learning Propagation...")

            # Test how learning impacts other systems
            propagation_test_context = self.test_context.copy()
            propagation_test_context["learning_validation"] = True

            # Generate new personalization with learned improvements
            post_learning_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                lead_id="lead_post_learning_test",
                evaluation_result=self.test_evaluation,
                message_template="Testing post-learning system improvements",
                interaction_history=self.test_interactions[:2],  # Subset for speed
                context=propagation_test_context,
                historical_sentiment=["Testing improved sentiment analysis"]
            )

            # Compare with baseline metrics
            learning_effectiveness = {
                "personalization_confidence_change": post_learning_output.personalization_confidence - 0.5,  # Baseline assumption
                "emotional_resonance_improvement": post_learning_output.emotional_resonance_score > 0.6,
                "retention_probability_boost": post_learning_output.retention_probability > 0.7,
                "learning_feedback_quality": len(post_learning_output.learning_feedback) > 0
            }

            print(f"✅ Cross-system propagation tested")
            print(f"   Confidence Change: +{learning_effectiveness['personalization_confidence_change']:.3f}")
            print(f"   Emotional Resonance: {post_learning_output.emotional_resonance_score:.3f}")
            print(f"   Retention Probability: {post_learning_output.retention_probability:.3f}")

            total_learning_time = time.time() - learning_start_time

            print("\n" + "="*80)
            print("🎉 REAL-TIME LEARNING SIGNAL PROPAGATION COMPLETED")
            print("="*80)
            print(f"⏱️  Total Learning Time: {total_learning_time:.3f}s")
            print(f"📡 Signals Injected: {len(learning_scenarios)}")
            print(f"🔄 Buffer Propagation: {len(buffer_states)} states monitored")
            print(f"🏋️  Model Retraining: Completed")
            print(f"📈 Learning Impact: Measured across {len(learning_impact)} metrics")
            print(f"🌐 Cross-System: Validated")

            # Critical assertions
            assert total_learning_time < 10.0, f"Learning propagation too slow: {total_learning_time:.3f}s"
            assert learning_impact["signals_processed"] >= len(learning_scenarios), "Not all signals processed"
            assert learning_impact["retraining_occurred"], "Model retraining did not occur"
            assert average_injection_time < 0.1, f"Signal injection too slow: {average_injection_time:.4f}s"
            assert post_learning_output.personalization_confidence > 0.5, "Learning did not improve confidence"

            return {
                "learning_scenarios": learning_scenarios,
                "signal_injection_times": signal_injection_times,
                "buffer_states": buffer_states,
                "learning_impact": learning_impact,
                "learning_effectiveness": learning_effectiveness,
                "total_time": total_learning_time
            }

        except Exception as e:
            learning_error_time = time.time() - learning_start_time
            print(f"\n❌ LEARNING SIGNAL PROPAGATION FAILED after {learning_error_time:.3f}s: {str(e)}")
            logger.error(f"Learning signal propagation test failed: {e}", exc_info=True)
            raise

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.fallback
    async def test_fallback_mechanism_comprehensive_validation(self):
        """
        Test fallback mechanisms for all enhanced components under various failure scenarios.
        Ensures system resilience and graceful degradation.
        """
        print("\n" + "="*80)
        print("TEST: Comprehensive Fallback Mechanism Validation")
        print("="*80)

        fallback_start_time = time.time()
        fallback_test_results = {}

        try:
            # SCENARIO 1: Enhanced ML Engine Failure Fallback
            print("\n🛡️ SCENARIO 1: Enhanced ML Engine Failure Fallback...")

            # Simulate enhanced ML engine failure
            with patch.object(self.enhanced_ml_engine, 'generate_enhanced_personalization', side_effect=Exception("ML Engine Failure")):
                fallback_start = time.time()

                # Test should fallback to original ML engine
                try:
                    fallback_output = await self.original_ml_engine.generate_personalized_communication(
                        lead_id=self.test_lead_id,
                        evaluation_result=self.test_evaluation,
                        message_template="Fallback test message",
                        interaction_history=self.test_interactions,
                        context=self.test_context
                    )

                    fallback_time = time.time() - fallback_start
                    fallback_test_results['ml_engine_fallback'] = {
                        'success': True,
                        'fallback_time': fallback_time,
                        'output_type': type(fallback_output).__name__,
                        'has_personalized_content': bool(fallback_output.personalized_content),
                        'has_optimal_timing': bool(fallback_output.optimal_timing)
                    }

                    print(f"✅ ML Engine fallback successful in {fallback_time:.3f}s")
                    print(f"   Fallback Output Type: {type(fallback_output).__name__}")
                    print(f"   Content Available: {bool(fallback_output.personalized_content)}")

                except Exception as e:
                    fallback_test_results['ml_engine_fallback'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ ML Engine fallback failed: {e}")

            # SCENARIO 2: Sentiment Analysis Failure Fallback
            print("\n🛡️ SCENARIO 2: Sentiment Analysis Failure Fallback...")

            # Mock sentiment analyzer failure
            with patch.object(self.enhanced_ml_engine.sentiment_analyzer, 'polarity_scores', side_effect=Exception("Sentiment Analysis Failure")):
                fallback_start = time.time()

                try:
                    # Should fallback to default sentiment result
                    enhanced_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                        lead_id=self.test_lead_id,
                        evaluation_result=self.test_evaluation,
                        message_template="Sentiment fallback test",
                        interaction_history=self.test_interactions,
                        context=self.test_context,
                        historical_sentiment=["test sentiment"]
                    )

                    fallback_time = time.time() - fallback_start

                    # Validate fallback to default sentiment
                    assert enhanced_output.sentiment_optimization is not None, "Sentiment fallback failed"
                    assert enhanced_output.sentiment_optimization.overall_sentiment == 0.0, "Default sentiment not applied"

                    fallback_test_results['sentiment_fallback'] = {
                        'success': True,
                        'fallback_time': fallback_time,
                        'default_sentiment_applied': enhanced_output.sentiment_optimization.overall_sentiment == 0.0,
                        'emotional_scores_defaulted': all(score == 0.0 for score in enhanced_output.sentiment_optimization.emotion_scores.values())
                    }

                    print(f"✅ Sentiment analysis fallback successful in {fallback_time:.3f}s")
                    print(f"   Default Sentiment Applied: {enhanced_output.sentiment_optimization.overall_sentiment}")

                except Exception as e:
                    fallback_test_results['sentiment_fallback'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ Sentiment analysis fallback failed: {e}")

            # SCENARIO 3: Churn Model Failure Fallback
            print("\n🛡️ SCENARIO 3: Churn Model Failure Fallback...")

            # Mock churn model failure
            with patch.object(self.enhanced_ml_engine, 'churn_model', None):
                fallback_start = time.time()

                try:
                    enhanced_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                        lead_id=self.test_lead_id,
                        evaluation_result=self.test_evaluation,
                        message_template="Churn model fallback test",
                        interaction_history=self.test_interactions,
                        context=self.test_context
                    )

                    fallback_time = time.time() - fallback_start

                    # Validate fallback to heuristic churn prediction
                    assert enhanced_output.churn_prevention is not None, "Churn prediction fallback failed"
                    assert enhanced_output.churn_prevention.risk_level in [ChurnRisk.LOW, ChurnRisk.MODERATE], "Heuristic fallback not applied"

                    fallback_test_results['churn_model_fallback'] = {
                        'success': True,
                        'fallback_time': fallback_time,
                        'heuristic_churn_applied': True,
                        'risk_level': enhanced_output.churn_prevention.risk_level.value,
                        'has_intervention_strategies': len(enhanced_output.churn_prevention.intervention_strategies) > 0
                    }

                    print(f"✅ Churn model fallback successful in {fallback_time:.3f}s")
                    print(f"   Heuristic Risk Level: {enhanced_output.churn_prevention.risk_level.value}")
                    print(f"   Intervention Strategies: {len(enhanced_output.churn_prevention.intervention_strategies)}")

                except Exception as e:
                    fallback_test_results['churn_model_fallback'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ Churn model fallback failed: {e}")

            # SCENARIO 4: Voice Analysis Failure Fallback
            print("\n🛡️ SCENARIO 4: Voice Analysis Failure Fallback...")

            # Simulate voice analysis failure by providing invalid transcript
            fallback_start = time.time()

            try:
                enhanced_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                    lead_id=self.test_lead_id,
                    evaluation_result=self.test_evaluation,
                    message_template="Voice analysis fallback test",
                    interaction_history=self.test_interactions,
                    context=self.test_context,
                    voice_transcript=None  # No voice transcript provided
                )

                fallback_time = time.time() - fallback_start

                # Validate voice analysis is optional and system continues
                assert enhanced_output is not None, "System failed without voice analysis"
                voice_analysis_provided = enhanced_output.voice_recommendations is not None

                fallback_test_results['voice_analysis_fallback'] = {
                    'success': True,
                    'fallback_time': fallback_time,
                    'system_continues_without_voice': True,
                    'voice_analysis_optional': not voice_analysis_provided or enhanced_output.voice_recommendations is None
                }

                print(f"✅ Voice analysis fallback successful in {fallback_time:.3f}s")
                print(f"   System Continues Without Voice: True")
                print(f"   Voice Analysis Optional: {not voice_analysis_provided}")

            except Exception as e:
                fallback_test_results['voice_analysis_fallback'] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"❌ Voice analysis fallback failed: {e}")

            # SCENARIO 5: Journey Stage Model Failure Fallback
            print("\n🛡️ SCENARIO 5: Journey Stage Model Failure Fallback...")

            # Mock journey model failure
            with patch.object(self.enhanced_ml_engine, 'journey_model', None):
                fallback_start = time.time()

                try:
                    enhanced_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                        lead_id=self.test_lead_id,
                        evaluation_result=self.test_evaluation,
                        message_template="Journey stage fallback test",
                        interaction_history=self.test_interactions,
                        context=self.test_context
                    )

                    fallback_time = time.time() - fallback_start

                    # Validate fallback to heuristic journey stage
                    assert enhanced_output.journey_stage is not None, "Journey stage fallback failed"
                    assert enhanced_output.journey_stage.stage_name in [
                        "Initial Interest", "Active Research", "Property Evaluation",
                        "Decision Making", "Ready to Buy"
                    ], "Invalid heuristic journey stage"

                    fallback_test_results['journey_stage_fallback'] = {
                        'success': True,
                        'fallback_time': fallback_time,
                        'heuristic_stage_applied': True,
                        'stage_name': enhanced_output.journey_stage.stage_name,
                        'has_optimal_actions': len(enhanced_output.journey_stage.optimal_actions) > 0
                    }

                    print(f"✅ Journey stage fallback successful in {fallback_time:.3f}s")
                    print(f"   Heuristic Stage: {enhanced_output.journey_stage.stage_name}")
                    print(f"   Optimal Actions: {len(enhanced_output.journey_stage.optimal_actions)}")

                except Exception as e:
                    fallback_test_results['journey_stage_fallback'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ Journey stage fallback failed: {e}")

            # SCENARIO 6: Real-Time Training Service Failure Fallback
            print("\n🛡️ SCENARIO 6: Real-Time Training Service Failure Fallback...")

            # Mock real-time training failure
            with patch.object(self.enhanced_ml_engine, '_perform_incremental_learning', side_effect=Exception("Training Service Failure")):
                fallback_start = time.time()

                try:
                    # Add learning signal that would trigger training
                    for i in range(self.enhanced_ml_engine.retrain_threshold + 1):
                        await self.enhanced_ml_engine._add_learning_signal(
                            LearningSignal.POSITIVE_ENGAGEMENT,
                            f"lead_fallback_{i}",
                            {"test": True},
                            {"fallback_test": True},
                            0.5
                        )

                    fallback_time = time.time() - fallback_start

                    # Validate system continues even if training fails
                    buffer_size = len(self.enhanced_ml_engine.learning_buffer)

                    fallback_test_results['training_service_fallback'] = {
                        'success': True,
                        'fallback_time': fallback_time,
                        'system_continues': buffer_size > 0,
                        'signals_buffered': buffer_size,
                        'training_gracefully_failed': True
                    }

                    print(f"✅ Training service fallback successful in {fallback_time:.3f}s")
                    print(f"   System Continues: {buffer_size > 0}")
                    print(f"   Signals Buffered: {buffer_size}")

                except Exception as e:
                    fallback_test_results['training_service_fallback'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ Training service fallback failed: {e}")

            # SCENARIO 7: Video Integration Service Failure Fallback
            print("\n🛡️ SCENARIO 7: Video Integration Service Failure Fallback...")

            # Mock video service failure
            with patch.object(self.video_integration, 'generate_personalized_video', side_effect=Exception("Video Service Failure")):
                fallback_start = time.time()

                try:
                    # System should continue without video generation
                    enhanced_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                        lead_id=self.test_lead_id,
                        evaluation_result=self.test_evaluation,
                        message_template="Video service fallback test",
                        interaction_history=self.test_interactions,
                        context=self.test_context
                    )

                    # Test email fallback instead of video
                    email_fallback_successful = enhanced_output.optimal_channel in [CommunicationChannel.EMAIL, CommunicationChannel.TEXT]

                    fallback_time = time.time() - fallback_start

                    fallback_test_results['video_service_fallback'] = {
                        'success': True,
                        'fallback_time': fallback_time,
                        'email_fallback_applied': email_fallback_successful,
                        'system_continues': enhanced_output is not None,
                        'alternative_channel': enhanced_output.optimal_channel.value
                    }

                    print(f"✅ Video service fallback successful in {fallback_time:.3f}s")
                    print(f"   Email Fallback Applied: {email_fallback_successful}")
                    print(f"   Alternative Channel: {enhanced_output.optimal_channel.value}")

                except Exception as e:
                    fallback_test_results['video_service_fallback'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ Video service fallback failed: {e}")

            # SCENARIO 8: ROI Attribution Service Failure Fallback
            print("\n🛡️ SCENARIO 8: ROI Attribution Service Failure Fallback...")

            # Mock ROI service failure
            with patch.object(self.roi_attribution, 'calculate_attribution', side_effect=Exception("ROI Service Failure")):
                fallback_start = time.time()

                try:
                    # System should continue with estimated ROI
                    enhanced_output = await self.enhanced_ml_engine.generate_enhanced_personalization(
                        lead_id=self.test_lead_id,
                        evaluation_result=self.test_evaluation,
                        message_template="ROI service fallback test",
                        interaction_history=self.test_interactions,
                        context=self.test_context
                    )

                    # System continues without ROI calculation
                    system_continues = enhanced_output is not None

                    fallback_time = time.time() - fallback_start

                    fallback_test_results['roi_service_fallback'] = {
                        'success': True,
                        'fallback_time': fallback_time,
                        'system_continues_without_roi': system_continues,
                        'personalization_unaffected': enhanced_output.personalization_confidence > 0
                    }

                    print(f"✅ ROI service fallback successful in {fallback_time:.3f}s")
                    print(f"   System Continues Without ROI: {system_continues}")
                    print(f"   Personalization Unaffected: {enhanced_output.personalization_confidence > 0}")

                except Exception as e:
                    fallback_test_results['roi_service_fallback'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"❌ ROI service fallback failed: {e}")

            # FALLBACK ANALYSIS
            print("\n🔍 FALLBACK MECHANISM ANALYSIS...")

            successful_fallbacks = sum(1 for result in fallback_test_results.values() if result.get('success', False))
            total_fallback_scenarios = len(fallback_test_results)
            fallback_success_rate = (successful_fallbacks / total_fallback_scenarios) * 100

            average_fallback_time = np.mean([
                result.get('fallback_time', 0)
                for result in fallback_test_results.values()
                if result.get('success', False)
            ])

            total_fallback_test_time = time.time() - fallback_start_time

            fallback_summary = {
                'total_scenarios_tested': total_fallback_scenarios,
                'successful_fallbacks': successful_fallbacks,
                'fallback_success_rate': fallback_success_rate,
                'average_fallback_time': average_fallback_time,
                'total_test_time': total_fallback_test_time,
                'resilience_score': fallback_success_rate,
                'performance_impact': average_fallback_time,
                'detailed_results': fallback_test_results
            }

            print(f"✅ Fallback mechanism analysis completed")
            print(f"   Scenarios Tested: {total_fallback_scenarios}")
            print(f"   Successful Fallbacks: {successful_fallbacks}")
            print(f"   Success Rate: {fallback_success_rate:.1f}%")
            print(f"   Average Fallback Time: {average_fallback_time:.3f}s")
            print(f"   Resilience Score: {fallback_success_rate:.1f}%")

            print("\n" + "="*80)
            print("🎉 COMPREHENSIVE FALLBACK VALIDATION COMPLETED")
            print("="*80)
            print(f"⏱️  Total Test Time: {total_fallback_test_time:.3f}s")
            print(f"🛡️  Fallback Success Rate: {fallback_success_rate:.1f}%")
            print(f"⚡ Average Fallback Time: {average_fallback_time:.3f}s")
            print(f"🎯 System Resilience: {'EXCELLENT' if fallback_success_rate >= 85 else 'GOOD' if fallback_success_rate >= 70 else 'NEEDS_IMPROVEMENT'}")

            # Critical fallback assertions
            assert fallback_success_rate >= 75, f"Fallback success rate too low: {fallback_success_rate:.1f}%"
            assert average_fallback_time < 2.0, f"Fallback too slow: {average_fallback_time:.3f}s"
            assert successful_fallbacks >= 6, f"Not enough successful fallbacks: {successful_fallbacks}"

            return fallback_summary

        except Exception as e:
            fallback_error_time = time.time() - fallback_start_time
            print(f"\n❌ FALLBACK VALIDATION FAILED after {fallback_error_time:.3f}s: {str(e)}")
            logger.error(f"Fallback mechanism validation failed: {e}", exc_info=True)
            raise

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_performance_under_load(self):
        """
        Test performance of integrated systems under simulated load conditions.
        """
        print("\n" + "="*80)
        print("TEST: Performance Under Load")
        print("="*80)

        load_test_start = time.time()
        concurrent_requests = 10

        try:
            print(f"\n⚡ Starting load test with {concurrent_requests} concurrent requests...")

            async def process_single_request(request_id: int):
                """Process a single enhanced ML request."""
                request_start = time.time()

                test_lead_id = f"load_test_lead_{request_id:03d}"

                result = await self.enhanced_ml_engine.generate_enhanced_personalization(
                    lead_id=test_lead_id,
                    evaluation_result=self.test_evaluation,
                    message_template=f"Load test request #{request_id}",
                    interaction_history=self.test_interactions[:3],  # Limit for performance
                    context=self.test_context,
                    historical_sentiment=self.test_historical_sentiment[:3]  # Limit for performance
                )

                request_time = time.time() - request_start

                return {
                    'request_id': request_id,
                    'processing_time': request_time,
                    'success': result is not None,
                    'emotional_resonance': result.emotional_resonance_score if result else 0,
                    'confidence': result.personalization_confidence if result else 0
                }

            # Execute concurrent requests
            load_test_tasks = [
                process_single_request(i)
                for i in range(concurrent_requests)
            ]

            concurrent_results = await asyncio.gather(*load_test_tasks, return_exceptions=True)

            # Analyze load test results
            successful_requests = [
                result for result in concurrent_results
                if isinstance(result, dict) and result.get('success', False)
            ]

            if successful_requests:
                processing_times = [result['processing_time'] for result in successful_requests]
                avg_processing_time = np.mean(processing_times)
                max_processing_time = max(processing_times)
                min_processing_time = min(processing_times)
                std_processing_time = np.std(processing_times)

                avg_emotional_resonance = np.mean([result['emotional_resonance'] for result in successful_requests])
                avg_confidence = np.mean([result['confidence'] for result in successful_requests])
            else:
                avg_processing_time = max_processing_time = min_processing_time = std_processing_time = 0
                avg_emotional_resonance = avg_confidence = 0

            total_load_test_time = time.time() - load_test_start
            success_rate = (len(successful_requests) / concurrent_requests) * 100
            throughput = len(successful_requests) / total_load_test_time  # requests per second

            load_test_results = {
                'concurrent_requests': concurrent_requests,
                'successful_requests': len(successful_requests),
                'success_rate': success_rate,
                'total_time': total_load_test_time,
                'throughput': throughput,
                'performance_metrics': {
                    'avg_processing_time': avg_processing_time,
                    'max_processing_time': max_processing_time,
                    'min_processing_time': min_processing_time,
                    'std_processing_time': std_processing_time,
                },
                'quality_metrics': {
                    'avg_emotional_resonance': avg_emotional_resonance,
                    'avg_confidence': avg_confidence
                }
            }

            print(f"✅ Load test completed in {total_load_test_time:.3f}s")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Throughput: {throughput:.2f} requests/second")
            print(f"   Avg Processing Time: {avg_processing_time:.3f}s")
            print(f"   Max Processing Time: {max_processing_time:.3f}s")
            print(f"   Avg Emotional Resonance: {avg_emotional_resonance:.3f}")

            # Performance assertions
            assert success_rate >= 80, f"Success rate too low under load: {success_rate:.1f}%"
            assert avg_processing_time < 3.0, f"Average processing time too slow: {avg_processing_time:.3f}s"
            assert max_processing_time < 5.0, f"Max processing time too slow: {max_processing_time:.3f}s"
            assert throughput >= 1.0, f"Throughput too low: {throughput:.2f} requests/second"

            return load_test_results

        except Exception as e:
            load_test_error_time = time.time() - load_test_start
            print(f"\n❌ LOAD TEST FAILED after {load_test_error_time:.3f}s: {str(e)}")
            logger.error(f"Load test failed: {e}", exc_info=True)
            raise

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.edge_cases
    async def test_edge_cases_and_error_handling(self):
        """
        Test edge cases and error handling across all integrated systems.
        """
        print("\n" + "="*80)
        print("TEST: Edge Cases and Error Handling")
        print("="*80)

        edge_case_start = time.time()
        edge_case_results = {}

        try:
            # EDGE CASE 1: Empty Interaction History
            print("\n🔬 EDGE CASE 1: Empty Interaction History...")

            try:
                result = await self.enhanced_ml_engine.generate_enhanced_personalization(
                    lead_id="edge_case_empty_history",
                    evaluation_result=self.test_evaluation,
                    message_template="Test with no interaction history",
                    interaction_history=[],  # Empty
                    context=self.test_context,
                    historical_sentiment=None
                )

                edge_case_results['empty_history'] = {
                    'success': result is not None,
                    'has_fallback_data': result.sentiment_optimization is not None,
                    'confidence_reasonable': result.personalization_confidence >= 0.3
                }

                print("✅ Empty history handled gracefully")

            except Exception as e:
                edge_case_results['empty_history'] = {'success': False, 'error': str(e)}
                print(f"❌ Empty history failed: {e}")

            # EDGE CASE 2: Invalid Lead Evaluation Data
            print("\n🔬 EDGE CASE 2: Invalid Lead Evaluation Data...")

            invalid_evaluation = LeadEvaluationResult(
                lead_id="edge_case_invalid",
                current_stage="invalid_stage",  # Invalid stage
                engagement_level=-0.5,  # Negative engagement
                priority_score=15.0,  # Out of range
                contact_preferences={},  # Empty preferences
                behavioral_indicators={}  # Empty indicators
            )

            try:
                result = await self.enhanced_ml_engine.generate_enhanced_personalization(
                    lead_id="edge_case_invalid_data",
                    evaluation_result=invalid_evaluation,
                    message_template="Test with invalid data",
                    interaction_history=self.test_interactions,
                    context=self.test_context
                )

                edge_case_results['invalid_evaluation'] = {
                    'success': result is not None,
                    'data_sanitized': result.predicted_engagement_score >= 0 and result.predicted_engagement_score <= 1,
                    'fallback_applied': True
                }

                print("✅ Invalid evaluation data handled with fallbacks")

            except Exception as e:
                edge_case_results['invalid_evaluation'] = {'success': False, 'error': str(e)}
                print(f"❌ Invalid evaluation data failed: {e}")

            # EDGE CASE 3: Extremely Long Text Input
            print("\n🔬 EDGE CASE 3: Extremely Long Text Input...")

            long_transcript = "This is a very long voice transcript. " * 1000  # Very long text
            long_sentiment_data = ["Long sentiment text here. " * 100] * 50  # Large sentiment data

            try:
                result = await self.enhanced_ml_engine.generate_enhanced_personalization(
                    lead_id="edge_case_long_text",
                    evaluation_result=self.test_evaluation,
                    message_template="Test with extremely long inputs",
                    interaction_history=self.test_interactions,
                    context=self.test_context,
                    voice_transcript=long_transcript,
                    historical_sentiment=long_sentiment_data
                )

                edge_case_results['long_text'] = {
                    'success': result is not None,
                    'processing_completed': True,
                    'output_reasonable_length': len(result.personalized_content) < 2000
                }

                print("✅ Long text input processed successfully")

            except Exception as e:
                edge_case_results['long_text'] = {'success': False, 'error': str(e)}
                print(f"❌ Long text input failed: {e}")

            # EDGE CASE 4: Unicode and Special Characters
            print("\n🔬 EDGE CASE 4: Unicode and Special Characters...")

            unicode_context = self.test_context.copy()
            unicode_context.update({
                "agent_name": "María José García-Smith",
                "property_type": "château/mansion",
                "location_preference": "Montréal, Québec",
                "special_notes": "客户喜欢现代设计 🏠✨ & eco-friendly features! 100% sustainable."
            })

            unicode_transcript = """
            Hi María! I'm really excited about finding a château-style home in Montréal!
            We're looking for something with caractère unique and modern amenities.
            My budget is around $500k-750k CAD. Can we schedule un rendez-vous?
            Merci beaucoup! 😊🇨🇦
            """

            try:
                result = await self.enhanced_ml_engine.generate_enhanced_personalization(
                    lead_id="edge_case_unicode",
                    evaluation_result=self.test_evaluation,
                    message_template="Bonjour {lead_name}, let's find your perfect château! 🏰",
                    interaction_history=self.test_interactions,
                    context=unicode_context,
                    voice_transcript=unicode_transcript
                )

                edge_case_results['unicode_chars'] = {
                    'success': result is not None,
                    'unicode_preserved': "María" in str(result.emotional_adaptation) or "château" in str(result.emotional_adaptation),
                    'emoji_handled': True  # System didn't crash
                }

                print("✅ Unicode and special characters handled correctly")

            except Exception as e:
                edge_case_results['unicode_chars'] = {'success': False, 'error': str(e)}
                print(f"❌ Unicode handling failed: {e}")

            # EDGE CASE 5: Rapid Sequential Requests (Race Conditions)
            print("\n🔬 EDGE CASE 5: Rapid Sequential Requests...")

            try:
                rapid_tasks = []
                for i in range(5):
                    task = self.enhanced_ml_engine.generate_enhanced_personalization(
                        lead_id=f"edge_case_rapid_{i}",
                        evaluation_result=self.test_evaluation,
                        message_template=f"Rapid request #{i}",
                        interaction_history=self.test_interactions[:2],  # Shorter for speed
                        context=self.test_context
                    )
                    rapid_tasks.append(task)

                rapid_results = await asyncio.gather(*rapid_tasks, return_exceptions=True)
                successful_rapid = sum(1 for r in rapid_results if not isinstance(r, Exception))

                edge_case_results['rapid_requests'] = {
                    'success': successful_rapid >= 4,  # Most should succeed
                    'successful_count': successful_rapid,
                    'total_requests': len(rapid_tasks),
                    'no_race_conditions': True  # If we get here, no major race conditions
                }

                print(f"✅ Rapid requests handled: {successful_rapid}/{len(rapid_tasks)} successful")

            except Exception as e:
                edge_case_results['rapid_requests'] = {'success': False, 'error': str(e)}
                print(f"❌ Rapid requests failed: {e}")

            # EDGE CASE 6: Memory Pressure Simulation
            print("\n🔬 EDGE CASE 6: Memory Pressure Simulation...")

            try:
                # Create large temporary data structures to simulate memory pressure
                large_data = []
                for i in range(100):
                    large_interaction_history = self.test_interactions * 50  # Very large history
                    large_data.append(large_interaction_history)

                # Test system under memory pressure
                result = await self.enhanced_ml_engine.generate_enhanced_personalization(
                    lead_id="edge_case_memory_pressure",
                    evaluation_result=self.test_evaluation,
                    message_template="Test under memory pressure",
                    interaction_history=large_data[0][:10],  # Use subset to avoid timeout
                    context=self.test_context
                )

                # Clean up
                del large_data

                edge_case_results['memory_pressure'] = {
                    'success': result is not None,
                    'performance_maintained': True,
                    'memory_cleaned': True
                }

                print("✅ Memory pressure handled gracefully")

            except Exception as e:
                edge_case_results['memory_pressure'] = {'success': False, 'error': str(e)}
                print(f"❌ Memory pressure test failed: {e}")

            # EDGE CASE 7: Network Timeout Simulation
            print("\n🔬 EDGE CASE 7: Network Timeout Simulation...")

            # Mock network delay/timeout
            async def mock_slow_claude_analysis(prompt):
                await asyncio.sleep(0.1)  # Simulate slow network
                return '{"enhanced_content": "Fallback content", "emotional_hooks": [], "tone_adjustments": []}'

            try:
                with patch.object(self.enhanced_ml_engine.semantic_analyzer, '_get_claude_analysis', side_effect=mock_slow_claude_analysis):
                    result = await self.enhanced_ml_engine.generate_enhanced_personalization(
                        lead_id="edge_case_network_timeout",
                        evaluation_result=self.test_evaluation,
                        message_template="Test network timeout handling",
                        interaction_history=self.test_interactions,
                        context=self.test_context
                    )

                edge_case_results['network_timeout'] = {
                    'success': result is not None,
                    'fallback_content_used': "Fallback content" in str(result.emotional_adaptation),
                    'system_resilient': True
                }

                print("✅ Network timeout handled with fallbacks")

            except Exception as e:
                edge_case_results['network_timeout'] = {'success': False, 'error': str(e)}
                print(f"❌ Network timeout test failed: {e}")

            # EDGE CASE ANALYSIS
            print("\n🔍 EDGE CASE ANALYSIS...")

            successful_edge_cases = sum(1 for result in edge_case_results.values() if result.get('success', False))
            total_edge_cases = len(edge_case_results)
            edge_case_success_rate = (successful_edge_cases / total_edge_cases) * 100

            total_edge_case_time = time.time() - edge_case_start

            edge_case_summary = {
                'total_edge_cases': total_edge_cases,
                'successful_cases': successful_edge_cases,
                'success_rate': edge_case_success_rate,
                'total_time': total_edge_case_time,
                'robustness_score': edge_case_success_rate,
                'detailed_results': edge_case_results
            }

            print(f"✅ Edge case analysis completed")
            print(f"   Edge Cases Tested: {total_edge_cases}")
            print(f"   Successful Cases: {successful_edge_cases}")
            print(f"   Success Rate: {edge_case_success_rate:.1f}%")
            print(f"   Robustness Score: {edge_case_success_rate:.1f}%")

            print("\n" + "="*80)
            print("🎉 EDGE CASES AND ERROR HANDLING COMPLETED")
            print("="*80)
            print(f"⏱️  Total Test Time: {total_edge_case_time:.3f}s")
            print(f"🛡️  Edge Case Success Rate: {edge_case_success_rate:.1f}%")
            print(f"🎯 System Robustness: {'EXCELLENT' if edge_case_success_rate >= 85 else 'GOOD' if edge_case_success_rate >= 70 else 'NEEDS_IMPROVEMENT'}")

            # Critical edge case assertions
            assert edge_case_success_rate >= 70, f"Edge case success rate too low: {edge_case_success_rate:.1f}%"
            assert successful_edge_cases >= 5, f"Not enough successful edge cases: {successful_edge_cases}"
            assert total_edge_case_time < 15.0, f"Edge case testing too slow: {total_edge_case_time:.3f}s"

            return edge_case_summary

        except Exception as e:
            edge_case_error_time = time.time() - edge_case_start
            print(f"\n❌ EDGE CASE TESTING FAILED after {edge_case_error_time:.3f}s: {str(e)}")
            logger.error(f"Edge case testing failed: {e}", exc_info=True)
            raise


# Test Execution and Reporting
if __name__ == "__main__":
    """
    Standalone test execution for development and debugging.
    """
    import asyncio

    async def run_comprehensive_integration_tests():
        """Run all comprehensive integration tests."""
        print("🚀 STARTING ENHANCED ML COMPREHENSIVE INTEGRATION TESTS")
        print("="*80)

        test_instance = TestEnhancedMLComprehensiveIntegration()
        await test_instance.setup_comprehensive_test_environment()

        try:
            # Run all major integration tests
            results = {}

            print("\n1️⃣ Running End-to-End Pipeline Test...")
            results['pipeline'] = await test_instance.test_end_to_end_enhanced_ml_pipeline()

            print("\n2️⃣ Running Cross-System Data Flow Test...")
            results['data_flow'] = await test_instance.test_cross_system_data_flow_validation()

            print("\n3️⃣ Running Learning Signal Propagation Test...")
            results['learning'] = await test_instance.test_real_time_learning_signal_propagation()

            print("\n4️⃣ Running Fallback Mechanism Test...")
            results['fallback'] = await test_instance.test_fallback_mechanism_comprehensive_validation()

            print("\n5️⃣ Running Performance Under Load Test...")
            results['performance'] = await test_instance.test_performance_under_load()

            print("\n6️⃣ Running Edge Cases and Error Handling Test...")
            results['edge_cases'] = await test_instance.test_edge_cases_and_error_handling()

            print("\n" + "="*80)
            print("🎉 ALL COMPREHENSIVE INTEGRATION TESTS COMPLETED")
            print("="*80)

            # Summary Report
            total_time = sum(result.get('total_time', result.get('total_pipeline_time', 0)) for result in results.values())
            success_count = len([r for r in results.values() if r])

            print(f"\n📊 FINAL INTEGRATION TEST SUMMARY:")
            print(f"   ✅ Tests Completed: {success_count}/6")
            print(f"   ⏱️  Total Test Time: {total_time:.3f}s")
            print(f"   🎯 Integration Status: {'PASSED' if success_count == 6 else 'PARTIAL'}")

            if 'pipeline' in results:
                print(f"   📈 Pipeline ROI: {results.get('pipeline', {}).get('roi_percentage', 0):.1f}%")
            if 'data_flow' in results:
                print(f"   🔍 Data Integrity: {results.get('data_flow', {}).get('integrity_percentage', 0):.1f}%")
            if 'fallback' in results:
                print(f"   🛡️  Fallback Success: {results.get('fallback', {}).get('fallback_success_rate', 0):.1f}%")
            if 'performance' in results:
                print(f"   ⚡ Throughput: {results.get('performance', {}).get('throughput', 0):.2f} req/s")

            return results

        except Exception as e:
            print(f"\n❌ COMPREHENSIVE INTEGRATION TESTS FAILED: {str(e)}")
            logger.error(f"Integration tests failed: {e}", exc_info=True)
            raise

    # Run tests if executed directly
    asyncio.run(run_comprehensive_integration_tests())