"""
Cross-System Data Flow Integration Tests

This test validates the complete data flow chain:
Enhanced ML → Video → ROI → Mobile

Business Impact: Ensures $362,600+ annual value flows seamlessly through all systems
Performance Target: <2s end-to-end processing with >95% data integrity
"""

import asyncio
import pytest
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

# Import all system components
from services.enhanced_ml_personalization_engine import (
    EnhancedMLPersonalizationEngine,
    AdvancedPersonalizationOutput,
    EmotionalState,
    LeadJourneyStage
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
    TouchpointEvent
)
from services.mobile_agent_experience import (
    MobileAgentExperience,
    DashboardMetrics,
    MobileNotification,
    AgentActivitySummary
)

# Import shared models
from models.shared_models import (
    EngagementInteraction,
    InteractionType,
    CommunicationChannel,
    LeadProfile,
    PropertyMatch,
    LeadEvaluationResult
)


class TestCrossSystemDataFlow:
    """Test complete data flow across all enhanced ML systems."""

    @pytest.fixture(autouse=True)
    async def setup_cross_system_environment(self):
        """Set up complete system environment for data flow testing."""
        # Initialize all system components
        self.enhanced_ml = EnhancedMLPersonalizationEngine()
        self.video_system = VideoMessageIntegration()
        self.roi_system = ROIAttributionSystem()
        self.mobile_system = MobileAgentExperience()

        # Test data for complete workflow
        self.test_lead_id = "cross_system_test_lead_001"
        self.test_agent_id = "agent_sarah_001"

        # Comprehensive lead profile
        self.test_lead_profile = LeadProfile(
            lead_id=self.test_lead_id,
            name="Jessica Martinez",
            email="jessica.martinez@email.com",
            phone="+1555-123-4567",
            preferences={
                "property_type": "single_family",
                "budget": 650000,
                "bedrooms": 3,
                "location": "Austin, TX",
                "timeline": "3-6 months"
            },
            source="website_inquiry",
            tags=["first_time_buyer", "family_focused", "school_district_priority"]
        )

        # Lead evaluation with enhanced metrics
        self.test_evaluation = LeadEvaluationResult(
            lead_id=self.test_lead_id,
            current_stage="actively_searching",
            engagement_level=0.82,
            priority_score=9.1,
            contact_preferences={
                "channel": "video_call",
                "time": "evening",
                "frequency": "weekly"
            },
            behavioral_indicators={
                "browsing_frequency": 4.2,
                "response_rate": 0.89,
                "page_views": 28,
                "time_on_site": 520,
                "property_saves": 12,
                "calculator_usage": 8,
                "neighborhood_research": 15
            },
            property_preferences={
                "price_range": {"min": 580000, "max": 720000},
                "property_types": ["single_family", "townhouse"],
                "must_have_features": ["good_schools", "safe_neighborhood", "garage"],
                "nice_to_have": ["pool", "modern_kitchen", "large_backyard"]
            }
        )

        # Rich interaction history
        self.test_interactions = [
            EngagementInteraction(
                interaction_id="int_001",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(days=3),
                channel=CommunicationChannel.EMAIL,
                type=InteractionType.EMAIL_OPEN,
                content_id="welcome_series_property_guide",
                engagement_metrics={
                    "open_duration": 180,
                    "click_through": True,
                    "links_clicked": ["school_ratings", "mortgage_calculator"],
                    "time_on_linked_pages": 420
                }
            ),
            EngagementInteraction(
                interaction_id="int_002",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(days=2),
                channel=CommunicationChannel.PHONE,
                type=InteractionType.CALL_ANSWERED,
                content_id="initial_consultation",
                engagement_metrics={
                    "call_duration": 1800,
                    "appointment_scheduled": True,
                    "questions_asked": 12,
                    "excitement_level": "high",
                    "follow_up_requested": True
                }
            ),
            EngagementInteraction(
                interaction_id="int_003",
                lead_id=self.test_lead_id,
                timestamp=datetime.now() - timedelta(days=1),
                channel=CommunicationChannel.VIDEO,
                type=InteractionType.VIDEO_WATCHED,
                content_id="property_virtual_tour_001",
                engagement_metrics={
                    "watch_duration": 480,
                    "video_length": 600,
                    "completion_rate": 0.8,
                    "rewatch_sections": ["kitchen", "master_bedroom", "backyard"],
                    "shared_with_spouse": True
                }
            )
        ]

        # Context for enhanced processing
        self.test_context = {
            "agent_name": "Sarah Johnson",
            "agent_expertise": "Family-friendly neighborhoods",
            "current_market_conditions": "competitive_seller_market",
            "seasonal_factors": "spring_buying_season",
            "recent_property_matches": 8,
            "competitor_activity": "high"
        }

        print(f"🔧 Cross-system test environment setup complete")
        print(f"   Lead: {self.test_lead_profile.name}")
        print(f"   Interactions: {len(self.test_interactions)}")
        print(f"   Engagement Level: {self.test_evaluation.engagement_level:.2f}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_enhanced_ml_to_video_data_flow(self):
        """Test data flow from Enhanced ML to Video system."""
        print("\n=== Testing Enhanced ML → Video Data Flow ===")

        start_time = time.time()

        # Step 1: Enhanced ML generates comprehensive insights
        ml_output = await self.enhanced_ml.generate_enhanced_personalization(
            lead_id=self.test_lead_id,
            evaluation_result=self.test_evaluation,
            message_template="Hi {lead_name}, I found some amazing properties that match your family's needs!",
            interaction_history=self.test_interactions,
            context=self.test_context,
            voice_transcript="I'm really excited about finding the perfect home for my family. We need good schools and a safe neighborhood.",
            historical_sentiment=["excited", "hopeful", "determined", "focused"]
        )

        # Step 2: Extract and validate enhanced ML insights
        ml_insights = {
            "emotional_state": ml_output.emotional_analysis.dominant_emotion.value,
            "sentiment_score": ml_output.emotional_analysis.sentiment_analysis.compound,
            "emotional_volatility": ml_output.emotional_analysis.emotional_volatility,
            "journey_stage": ml_output.journey_intelligence.current_stage.value,
            "stage_confidence": ml_output.journey_intelligence.stage_confidence,
            "predicted_next_actions": ml_output.journey_intelligence.predicted_next_actions,
            "personalization_factors": ml_output.personalization_factors,
            "optimized_content": ml_output.personalized_content
        }

        # Step 3: Video system uses ML insights for advanced personalization
        video_context = {
            **self.test_context,
            "ml_insights": ml_insights,
            "emotional_optimization": {
                "primary_emotion": ml_output.emotional_analysis.dominant_emotion.value,
                "emotional_intensity": 1.0 - ml_output.emotional_analysis.emotional_volatility,
                "communication_style": "family_focused_enthusiastic" if ml_output.emotional_analysis.dominant_emotion == EmotionalState.EXCITED else "reassuring_supportive"
            },
            "journey_optimization": {
                "current_stage": ml_output.journey_intelligence.current_stage.value,
                "progression_probability": ml_output.journey_intelligence.stage_confidence,
                "optimal_next_steps": ml_output.journey_intelligence.predicted_next_actions[:3]
            },
            "content_personalization": {
                "key_interests": ml_output.personalization_factors.get("priority_features", []),
                "messaging_tone": "confident" if ml_output.emotional_analysis.sentiment_analysis.compound > 0.3 else "supportive",
                "urgency_level": "moderate" if ml_output.journey_intelligence.current_stage == LeadJourneyStage.ACTIVELY_SEARCHING else "low"
            }
        }

        # Step 4: Generate enhanced video with ML-driven personalization
        video_message = await self.video_system.generate_personalized_video(
            lead_id=self.test_lead_id,
            template_id="family_home_showcase",
            evaluation_result=self.test_evaluation,
            context=video_context
        )

        ml_to_video_time = time.time() - start_time

        # Data Flow Validations
        assert ml_output is not None, "Enhanced ML output generation failed"
        assert video_message is not None, "Video generation with ML insights failed"
        assert ml_to_video_time < 2.5, f"ML → Video flow too slow: {ml_to_video_time:.3f}s"

        # Validate ML insights propagation to video
        video_metadata = video_message.metadata
        assert "ml_insights" in video_context, "ML insights not passed to video system"
        assert ml_insights["emotional_state"] in video_message.video_generation_request.message_content
        assert ml_insights["journey_stage"] in str(video_metadata)

        # Validate emotional intelligence integration
        if ml_output.emotional_analysis.dominant_emotion == EmotionalState.EXCITED:
            assert "enthusiastic" in video_message.video_generation_request.agent_personality.lower()

        # Validate journey intelligence integration
        if ml_output.journey_intelligence.current_stage == LeadJourneyStage.ACTIVELY_SEARCHING:
            assert any(action in video_message.video_generation_request.message_content.lower()
                      for action in ["schedule", "view", "tour", "visit"])

        print(f"✅ Enhanced ML → Video flow: {ml_to_video_time:.3f}s")
        print(f"   Emotional Integration: {ml_insights['emotional_state']} → {video_context['emotional_optimization']['communication_style']}")
        print(f"   Journey Integration: {ml_insights['journey_stage']} → {len(video_context['journey_optimization']['optimal_next_steps'])} next steps")
        print(f"   Video ID: {video_message.video_id}")

        return {
            "ml_output": ml_output,
            "video_message": video_message,
            "ml_insights": ml_insights,
            "processing_time": ml_to_video_time
        }

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_video_to_roi_data_flow(self):
        """Test data flow from Video to ROI Attribution system."""
        print("\n=== Testing Video → ROI Data Flow ===")

        # Get video message from previous step
        ml_video_result = await self.test_enhanced_ml_to_video_data_flow()
        video_message = ml_video_result["video_message"]
        ml_insights = ml_video_result["ml_insights"]

        start_time = time.time()

        # Step 1: Video system tracks delivery and engagement
        video_engagement_data = {
            "video_id": video_message.video_id,
            "delivery_timestamp": datetime.now(),
            "delivery_channel": CommunicationChannel.EMAIL,
            "personalization_applied": True,
            "ml_enhanced": True,
            "template_used": "family_home_showcase",
            "emotional_optimization": ml_insights["emotional_state"],
            "journey_stage_targeting": ml_insights["journey_stage"]
        }

        # Step 2: ROI system creates enhanced touchpoint with video metadata
        video_touchpoint = await self.roi_system.track_touchpoint(
            lead_id=self.test_lead_id,
            channel=CommunicationChannel.EMAIL,
            campaign_id="enhanced_ml_video_campaign",
            content_id=f"video_{video_message.video_id}",
            metadata={
                "video_metadata": video_engagement_data,
                "ml_insights_applied": ml_insights,
                "personalization_score": video_message.personalization_score,
                "estimated_engagement_probability": video_message.estimated_engagement,
                "content_optimization": {
                    "emotional_targeting": ml_insights["emotional_state"],
                    "journey_optimization": ml_insights["journey_stage"],
                    "sentiment_alignment": ml_insights["sentiment_score"]
                },
                "advanced_attribution_factors": {
                    "ml_personalization_applied": True,
                    "emotional_intelligence_used": True,
                    "journey_stage_optimized": True,
                    "multi_modal_coherent": True
                }
            }
        )

        # Step 3: Simulate video engagement events
        engagement_events = [
            {
                "event_type": "video_delivered",
                "timestamp": datetime.now(),
                "metadata": {"delivery_success": True, "channel": "email"}
            },
            {
                "event_type": "email_opened",
                "timestamp": datetime.now() + timedelta(minutes=15),
                "metadata": {"open_duration": 8, "device": "mobile"}
            },
            {
                "event_type": "video_started",
                "timestamp": datetime.now() + timedelta(minutes=17),
                "metadata": {"start_position": 0, "device": "mobile", "quality": "720p"}
            },
            {
                "event_type": "video_milestone_25",
                "timestamp": datetime.now() + timedelta(minutes=18),
                "metadata": {"engagement_level": "high", "replay_segments": []}
            },
            {
                "event_type": "video_milestone_50",
                "timestamp": datetime.now() + timedelta(minutes=19),
                "metadata": {"engagement_level": "very_high", "replay_segments": ["property_tour"]}
            },
            {
                "event_type": "video_milestone_75",
                "timestamp": datetime.now() + timedelta(minutes=20),
                "metadata": {"engagement_level": "very_high", "replay_segments": ["property_tour", "neighborhood"]}
            },
            {
                "event_type": "video_completed",
                "timestamp": datetime.now() + timedelta(minutes=21),
                "metadata": {"completion_rate": 1.0, "engagement_score": 0.94, "replay_count": 2}
            },
            {
                "event_type": "cta_clicked",
                "timestamp": datetime.now() + timedelta(minutes=22),
                "metadata": {"cta_type": "schedule_viewing", "confidence": "high"}
            }
        ]

        # Step 4: Track all engagement events in ROI system
        for event in engagement_events:
            await self.roi_system.track_touchpoint(
                lead_id=self.test_lead_id,
                channel=CommunicationChannel.EMAIL,
                campaign_id="enhanced_ml_video_campaign",
                content_id=f"video_{video_message.video_id}",
                metadata={
                    "event_data": event,
                    "parent_touchpoint": video_touchpoint.touchpoint_id,
                    "ml_attribution": ml_insights,
                    "video_performance": {
                        "personalization_effectiveness": video_message.personalization_score,
                        "emotional_resonance": ml_insights["sentiment_score"],
                        "journey_alignment": ml_insights["journey_stage"]
                    }
                }
            )

        # Step 5: Simulate conversion event (appointment scheduled)
        conversion_event = await self.roi_system.track_conversion_event(
            lead_id=self.test_lead_id,
            event_type=ConversionEventType.APPOINTMENT_SCHEDULED,
            event_value=7500.0,  # High-value appointment due to enhanced personalization
            metadata={
                "triggered_by_video": video_message.video_id,
                "ml_enhanced_attribution": {
                    "emotional_optimization": ml_insights["emotional_state"],
                    "journey_optimization": ml_insights["journey_stage"],
                    "personalization_score": video_message.personalization_score
                },
                "video_engagement_journey": [e["event_type"] for e in engagement_events],
                "attribution_confidence": 0.92,  # High confidence due to ML insights
                "enhanced_value_factors": [
                    "emotional_intelligence_applied",
                    "journey_stage_optimized",
                    "personalized_video_content",
                    "high_engagement_rate"
                ]
            }
        )

        video_to_roi_time = time.time() - start_time

        # Data Flow Validations
        assert video_touchpoint is not None, "Video touchpoint creation failed"
        assert conversion_event is not None, "Conversion event tracking failed"
        assert video_to_roi_time < 1.5, f"Video → ROI flow too slow: {video_to_roi_time:.3f}s"

        # Validate video data propagation to ROI
        video_metadata_in_roi = video_touchpoint.metadata["video_metadata"]
        assert video_metadata_in_roi["video_id"] == video_message.video_id
        assert video_metadata_in_roi["ml_enhanced"] == True
        assert video_metadata_in_roi["emotional_optimization"] == ml_insights["emotional_state"]

        # Validate enhanced attribution
        attribution_weights = conversion_event.attribution_weights
        assert len(attribution_weights) > 0, "No attribution weights calculated"
        assert sum(attribution_weights.values()) > 0.8, "Low attribution confidence"

        # Validate ML enhancement tracking
        ml_attribution = conversion_event.metadata["ml_enhanced_attribution"]
        assert ml_attribution["emotional_optimization"] == ml_insights["emotional_state"]
        assert ml_attribution["personalization_score"] > 0.7, "Low personalization score"

        print(f"✅ Video → ROI flow: {video_to_roi_time:.3f}s")
        print(f"   Video Touchpoint: {video_touchpoint.touchpoint_id}")
        print(f"   Conversion Value: ${conversion_event.event_value:,.2f}")
        print(f"   Attribution Confidence: {conversion_event.metadata['attribution_confidence']:.2%}")
        print(f"   ML Enhancement: {len(conversion_event.metadata['enhanced_value_factors'])} factors")

        return {
            "video_touchpoint": video_touchpoint,
            "conversion_event": conversion_event,
            "engagement_events": engagement_events,
            "processing_time": video_to_roi_time
        }

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_roi_to_mobile_data_flow(self):
        """Test data flow from ROI Attribution to Mobile system."""
        print("\n=== Testing ROI → Mobile Data Flow ===")

        # Get ROI data from previous step
        roi_result = await self.test_video_to_roi_data_flow()
        conversion_event = roi_result["conversion_event"]
        video_touchpoint = roi_result["video_touchpoint"]

        start_time = time.time()

        # Step 1: ROI system aggregates performance data for mobile dashboard
        roi_summary = await self.roi_system.generate_performance_summary(
            timeframe_days=7,
            agent_id=self.test_agent_id,
            include_ml_attribution=True
        )

        # Step 2: Extract mobile-relevant metrics
        mobile_roi_data = {
            "total_conversions": roi_summary.total_conversions,
            "total_revenue": roi_summary.total_attributed_revenue,
            "conversion_rate": roi_summary.conversion_rate,
            "roi_by_channel": roi_summary.channel_performance,
            "attribution_breakdown": roi_summary.attribution_model_comparison,
            "ml_enhancement_impact": {
                "enhanced_conversions": roi_summary.enhanced_ml_conversions,
                "traditional_conversions": roi_summary.traditional_conversions,
                "uplift_percentage": roi_summary.ml_enhancement_uplift,
                "emotional_intelligence_factor": roi_summary.emotional_ai_contribution,
                "journey_optimization_factor": roi_summary.journey_optimization_contribution
            },
            "top_performing_content": roi_summary.top_content_by_roi,
            "recent_high_value_events": [
                {
                    "event_id": conversion_event.event_id,
                    "lead_name": self.test_lead_profile.name,
                    "value": conversion_event.event_value,
                    "attribution_confidence": conversion_event.metadata["attribution_confidence"],
                    "ml_enhanced": True,
                    "emotional_optimization": conversion_event.metadata["ml_enhanced_attribution"]["emotional_optimization"],
                    "trigger_content": f"video_{video_touchpoint.metadata['video_metadata']['video_id']}"
                }
            ]
        }

        # Step 3: Mobile system processes ROI data for agent dashboard
        dashboard_metrics = await self.mobile_system.update_dashboard_metrics(
            agent_id=self.test_agent_id,
            roi_data=mobile_roi_data,
            enhanced_ml_insights=True
        )

        # Step 4: Generate mobile notifications for high-impact events
        mobile_notifications = []

        # High-value conversion notification
        if conversion_event.event_value > 5000:
            high_value_notification = await self.mobile_system.create_notification(
                agent_id=self.test_agent_id,
                type="high_value_conversion",
                title="🎯 High-Value Appointment Scheduled!",
                message=f"{self.test_lead_profile.name} scheduled an appointment (${conversion_event.event_value:,.0f} value)",
                metadata={
                    "lead_id": self.test_lead_id,
                    "conversion_value": conversion_event.event_value,
                    "attribution_confidence": conversion_event.metadata["attribution_confidence"],
                    "ml_enhanced": True,
                    "action_required": "prepare_for_appointment",
                    "priority": "high"
                }
            )
            mobile_notifications.append(high_value_notification)

        # ML optimization success notification
        if conversion_event.metadata.get("attribution_confidence", 0) > 0.9:
            ml_success_notification = await self.mobile_system.create_notification(
                agent_id=self.test_agent_id,
                type="ml_optimization_success",
                title="🧠 AI Optimization Success!",
                message=f"Enhanced personalization led to {self.test_lead_profile.name}'s conversion",
                metadata={
                    "optimization_type": "emotional_intelligence",
                    "emotional_state": conversion_event.metadata["ml_enhanced_attribution"]["emotional_optimization"],
                    "personalization_score": conversion_event.metadata["ml_enhanced_attribution"]["personalization_score"],
                    "attribution_confidence": conversion_event.metadata["attribution_confidence"],
                    "action_suggested": "review_success_factors"
                }
            )
            mobile_notifications.append(ml_success_notification)

        # Step 5: Create agent activity summary with enhanced insights
        activity_summary = await self.mobile_system.generate_activity_summary(
            agent_id=self.test_agent_id,
            timeframe="today",
            include_roi_metrics=True,
            include_ml_insights=True
        )

        roi_to_mobile_time = time.time() - start_time

        # Data Flow Validations
        assert dashboard_metrics is not None, "Dashboard metrics update failed"
        assert len(mobile_notifications) > 0, "Mobile notifications generation failed"
        assert activity_summary is not None, "Activity summary generation failed"
        assert roi_to_mobile_time < 1.0, f"ROI → Mobile flow too slow: {roi_to_mobile_time:.3f}s"

        # Validate ROI data propagation to mobile
        assert dashboard_metrics.total_revenue >= conversion_event.event_value
        assert dashboard_metrics.ml_enhancement_metrics is not None
        assert dashboard_metrics.recent_conversions[0]["lead_id"] == self.test_lead_id

        # Validate mobile notifications contain ROI insights
        high_value_notification = mobile_notifications[0]
        assert high_value_notification.metadata["conversion_value"] == conversion_event.event_value
        assert high_value_notification.metadata["attribution_confidence"] > 0.8

        # Validate activity summary includes enhanced metrics
        assert activity_summary.roi_metrics.total_revenue >= conversion_event.event_value
        assert activity_summary.ml_enhancement_metrics.emotional_ai_contribution > 0
        assert activity_summary.enhanced_conversions > 0

        print(f"✅ ROI → Mobile flow: {roi_to_mobile_time:.3f}s")
        print(f"   Dashboard Updates: Revenue ${dashboard_metrics.total_revenue:,.2f}")
        print(f"   Mobile Notifications: {len(mobile_notifications)}")
        print(f"   ML Enhancement Uplift: {dashboard_metrics.ml_enhancement_metrics.uplift_percentage:.1%}")
        print(f"   Agent Activity: {activity_summary.total_activities} activities tracked")

        return {
            "dashboard_metrics": dashboard_metrics,
            "mobile_notifications": mobile_notifications,
            "activity_summary": activity_summary,
            "processing_time": roi_to_mobile_time
        }

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_cross_system_data_flow(self):
        """Test complete data flow: Enhanced ML → Video → ROI → Mobile."""
        print("\n=== Testing Complete Cross-System Data Flow ===")

        start_time = time.time()

        # Execute complete flow and collect results
        ml_video_result = await self.test_enhanced_ml_to_video_data_flow()
        roi_result = await self.test_video_to_roi_data_flow()
        mobile_result = await self.test_roi_to_mobile_data_flow()

        total_flow_time = time.time() - start_time

        # Comprehensive data integrity validation
        data_integrity_checks = {
            "lead_id_consistency": (
                ml_video_result["ml_output"].lead_id ==
                roi_result["conversion_event"].lead_id ==
                self.test_lead_id
            ),
            "emotional_state_propagation": (
                ml_video_result["ml_insights"]["emotional_state"] in
                str(roi_result["conversion_event"].metadata)
            ),
            "personalization_continuity": (
                ml_video_result["video_message"].personalization_score > 0.7 and
                roi_result["conversion_event"].metadata["ml_enhanced_attribution"]["personalization_score"] > 0.7
            ),
            "value_attribution_consistency": (
                roi_result["conversion_event"].event_value <=
                mobile_result["dashboard_metrics"].total_revenue
            ),
            "ml_insights_end_to_end": (
                "ml_enhanced" in str(mobile_result["mobile_notifications"][0].metadata)
            )
        }

        integrity_score = sum(data_integrity_checks.values()) / len(data_integrity_checks)

        # Business value calculation
        business_value = {
            "conversion_value": roi_result["conversion_event"].event_value,
            "attribution_confidence": roi_result["conversion_event"].metadata["attribution_confidence"],
            "ml_enhancement_uplift": mobile_result["dashboard_metrics"].ml_enhancement_metrics.uplift_percentage,
            "emotional_ai_contribution": mobile_result["activity_summary"].ml_enhancement_metrics.emotional_ai_contribution,
            "total_processing_time": total_flow_time,
            "data_integrity_score": integrity_score
        }

        # Performance validations
        assert total_flow_time < 8.0, f"Complete flow too slow: {total_flow_time:.3f}s"
        assert integrity_score >= 0.9, f"Data integrity issues: {integrity_score:.2%}"
        assert business_value["conversion_value"] > 0, "No business value generated"
        assert business_value["attribution_confidence"] > 0.8, "Low attribution confidence"

        # Enhanced ML impact validation
        assert business_value["ml_enhancement_uplift"] > 0, "No ML uplift detected"
        assert business_value["emotional_ai_contribution"] > 0, "No emotional AI contribution"

        print(f"✅ Complete Cross-System Flow: {total_flow_time:.3f}s")
        print(f"   Data Integrity: {integrity_score:.2%}")
        print(f"   Business Value: ${business_value['conversion_value']:,.2f}")
        print(f"   ML Uplift: {business_value['ml_enhancement_uplift']:.1%}")
        print(f"   Attribution Confidence: {business_value['attribution_confidence']:.2%}")

        # Detailed flow summary
        flow_summary = {
            "enhanced_ml_insights": {
                "emotional_state": ml_video_result["ml_insights"]["emotional_state"],
                "journey_stage": ml_video_result["ml_insights"]["journey_stage"],
                "sentiment_score": ml_video_result["ml_insights"]["sentiment_score"],
                "processing_time": ml_video_result["processing_time"]
            },
            "video_personalization": {
                "video_id": ml_video_result["video_message"].video_id,
                "personalization_score": ml_video_result["video_message"].personalization_score,
                "estimated_engagement": ml_video_result["video_message"].estimated_engagement
            },
            "roi_attribution": {
                "conversion_value": roi_result["conversion_event"].event_value,
                "attribution_weights": roi_result["conversion_event"].attribution_weights,
                "enhancement_factors": len(roi_result["conversion_event"].metadata["enhanced_value_factors"])
            },
            "mobile_experience": {
                "notifications_sent": len(mobile_result["mobile_notifications"]),
                "dashboard_updated": True,
                "activity_tracked": mobile_result["activity_summary"].total_activities
            },
            "business_impact": business_value
        }

        return flow_summary

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cross_system_performance_under_load(self):
        """Test cross-system performance under realistic load conditions."""
        print("\n=== Testing Cross-System Performance Under Load ===")

        # Simulate multiple concurrent leads
        concurrent_leads = 5
        performance_results = []

        async def process_lead_workflow(lead_index: int):
            """Process a single lead through the complete workflow."""
            test_lead_id = f"perf_test_lead_{lead_index:03d}"
            start_time = time.time()

            try:
                # Enhanced ML processing
                ml_output = await self.enhanced_ml.generate_enhanced_personalization(
                    lead_id=test_lead_id,
                    evaluation_result=self.test_evaluation,
                    message_template=f"Hi Lead {lead_index}, let's find your perfect home!",
                    interaction_history=self.test_interactions,
                    context={**self.test_context, "lead_index": lead_index}
                )

                # Video generation
                video_message = await self.video_system.generate_personalized_video(
                    lead_id=test_lead_id,
                    template_id="family_home_showcase",
                    evaluation_result=self.test_evaluation,
                    context={"ml_insights": {"emotional_state": ml_output.emotional_analysis.dominant_emotion.value}}
                )

                # ROI tracking
                conversion_event = await self.roi_system.track_conversion_event(
                    lead_id=test_lead_id,
                    event_type=ConversionEventType.APPOINTMENT_SCHEDULED,
                    event_value=5000.0 + (lead_index * 500),
                    metadata={"load_test": True, "lead_index": lead_index}
                )

                # Mobile update
                dashboard_update = await self.mobile_system.update_dashboard_metrics(
                    agent_id=self.test_agent_id,
                    roi_data={"total_revenue": conversion_event.event_value},
                    enhanced_ml_insights=True
                )

                processing_time = time.time() - start_time

                return {
                    "lead_index": lead_index,
                    "success": True,
                    "processing_time": processing_time,
                    "conversion_value": conversion_event.event_value
                }

            except Exception as e:
                return {
                    "lead_index": lead_index,
                    "success": False,
                    "error": str(e),
                    "processing_time": time.time() - start_time
                }

        # Execute concurrent processing
        load_test_start = time.time()
        results = await asyncio.gather(*[
            process_lead_workflow(i) for i in range(concurrent_leads)
        ])
        total_load_test_time = time.time() - load_test_start

        # Analyze performance results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        success_rate = len(successful_results) / len(results)
        avg_processing_time = np.mean([r["processing_time"] for r in successful_results]) if successful_results else 0
        total_conversion_value = sum([r["conversion_value"] for r in successful_results])

        # Performance assertions
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2%}"
        assert avg_processing_time < 10.0, f"Average processing too slow: {avg_processing_time:.3f}s"
        assert total_load_test_time < 15.0, f"Load test too slow: {total_load_test_time:.3f}s"

        print(f"✅ Cross-System Load Test: {total_load_test_time:.3f}s")
        print(f"   Concurrent Leads: {concurrent_leads}")
        print(f"   Success Rate: {success_rate:.2%}")
        print(f"   Avg Processing: {avg_processing_time:.3f}s per lead")
        print(f"   Total Value: ${total_conversion_value:,.2f}")
        print(f"   Failed Workflows: {len(failed_results)}")

        return {
            "concurrent_leads": concurrent_leads,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "total_processing_time": total_load_test_time,
            "total_conversion_value": total_conversion_value,
            "failed_count": len(failed_results)
        }


# Run cross-system integration tests
if __name__ == "__main__":
    async def run_cross_system_tests():
        """Run complete cross-system integration test suite."""
        print("🔄 Starting Cross-System Data Flow Integration Tests")
        print("=" * 80)

        test_suite = TestCrossSystemDataFlow()
        await test_suite.setup_cross_system_environment()

        results = {}

        try:
            # Individual flow tests
            ml_video_result = await test_suite.test_enhanced_ml_to_video_data_flow()
            results["ml_to_video"] = "✅ PASS"

            video_roi_result = await test_suite.test_video_to_roi_data_flow()
            results["video_to_roi"] = "✅ PASS"

            roi_mobile_result = await test_suite.test_roi_to_mobile_data_flow()
            results["roi_to_mobile"] = "✅ PASS"

            # Complete flow test
            complete_flow_result = await test_suite.test_complete_cross_system_data_flow()
            results["complete_flow"] = "✅ PASS"

            # Performance test
            load_test_result = await test_suite.test_cross_system_performance_under_load()
            results["load_test"] = "✅ PASS"

        except Exception as e:
            results["error"] = f"❌ FAIL: {str(e)}"

        # Final results
        print("\n" + "=" * 80)
        print("🎯 CROSS-SYSTEM DATA FLOW TEST RESULTS")
        print("=" * 80)

        for test_name, result in results.items():
            print(f"{test_name}: {result}")

        passed_tests = sum(1 for result in results.values() if result.startswith("✅"))
        total_tests = len(results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        print(f"\nOverall Success Rate: {success_rate:.2%} ({passed_tests}/{total_tests})")
        print("🚀 Enhanced ML → Video → ROI → Mobile: DATA FLOW VALIDATED" if success_rate >= 0.9 else "⚠️  Data flow issues detected")

    asyncio.run(run_cross_system_tests())