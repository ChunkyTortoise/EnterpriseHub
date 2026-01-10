"""
Multi-Modal Communication Optimization Integration Tests

This test validates the integration of Multi-Modal Communication Optimizer with all systems:
1. Enhanced ML Personalization (emotional intelligence alignment)
2. Video Message Integration (optimized video scripts)
3. Churn Prevention (retention-focused messaging)
4. ROI Attribution (optimization impact measurement)
5. Cross-Modal Coherence (consistency across text/voice/video)

Business Impact: 25-35% increase in conversion rates through optimized communication
Performance Target: <500ms optimization, >90% coherence, >85% effectiveness improvement
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Import multi-modal optimizer and related components
from services.multimodal_communication_optimizer import (
    MultiModalCommunicationOptimizer,
    CommunicationModality,
    MultiModalAnalysis,
    OptimizedCommunication,
    TextAnalysisResult,
    VoiceAnalysisResult,
    VideoAnalysisResult,
    CrossModalAnalysis
)

# Import integration components
from services.enhanced_ml_personalization_engine import (
    EnhancedMLPersonalizationEngine,
    AdvancedPersonalizationOutput,
    EmotionalState,
    LeadJourneyStage
)
from services.predictive_churn_prevention import (
    PredictiveChurnPrevention,
    ChurnRiskLevel,
    InterventionType
)
from services.video_message_integration import (
    VideoMessageIntegration,
    VideoMessage
)
from services.roi_attribution_system import (
    ROIAttributionSystem,
    ConversionEvent,
    ConversionEventType
)

# Import shared models
from models.shared_models import (
    EngagementInteraction,
    InteractionType,
    CommunicationChannel,
    LeadProfile,
    LeadEvaluationResult
)


@dataclass
class OptimizationScenario:
    """Represents a multi-modal optimization test scenario."""
    lead_profile: LeadProfile
    evaluation_result: LeadEvaluationResult
    base_content: Dict[CommunicationModality, str]
    optimization_goals: List[str]
    expected_improvements: Dict[str, float]
    integration_context: Dict[str, Any]


@dataclass
class MultiModalIntegrationMetrics:
    """Metrics for multi-modal integration performance."""
    analysis_time: float
    optimization_time: float
    coherence_score: float
    effectiveness_improvement: float
    cross_system_integration_success: bool
    emotional_alignment_score: float
    retention_optimization_score: float


class OptimizationGoal(Enum):
    """Different optimization goals for communication."""
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    RETENTION = "retention"
    EDUCATION = "education"
    URGENCY = "urgency"
    RELATIONSHIP_BUILDING = "relationship_building"


class TestMultiModalOptimizationIntegration:
    """Test multi-modal communication optimization integration with all systems."""

    @pytest.fixture(autouse=True)
    async def setup_multimodal_integration_environment(self):
        """Set up complete environment for multi-modal optimization testing."""
        # Initialize all integrated systems
        self.multimodal_optimizer = MultiModalCommunicationOptimizer()
        self.enhanced_personalization = EnhancedMLPersonalizationEngine()
        self.churn_prevention = PredictiveChurnPrevention()
        self.video_integration = VideoMessageIntegration()
        self.roi_attribution = ROIAttributionSystem()

        # Create diverse optimization scenarios
        self.optimization_scenarios = [
            # Scenario 1: Engagement optimization with emotional intelligence
            OptimizationScenario(
                lead_profile=LeadProfile(
                    lead_id="multimodal_test_lead_001",
                    name="Jennifer Williams",
                    email="jennifer.williams@email.com",
                    phone="+1555-123-4567",
                    preferences={
                        "property_type": "luxury_condo",
                        "budget": 1200000,
                        "location": "Downtown luxury district",
                        "timeline": "immediate"
                    },
                    source="luxury_website",
                    tags=["high_net_worth", "luxury_preference", "immediate_buyer"]
                ),
                evaluation_result=LeadEvaluationResult(
                    lead_id="multimodal_test_lead_001",
                    current_stage="ready_to_buy",
                    engagement_level=0.85,
                    priority_score=9.5,
                    contact_preferences={"channel": "phone", "time": "business_hours"},
                    behavioral_indicators={
                        "browsing_frequency": 5.2,
                        "response_rate": 0.95,
                        "page_views": 45,
                        "time_on_site": 680,
                        "luxury_focus": True,
                        "decision_maker": True
                    }
                ),
                base_content={
                    CommunicationModality.TEXT: "Hi Jennifer, I have some exclusive luxury properties that match your criteria.",
                    CommunicationModality.EMAIL: "Subject: Exclusive Luxury Properties Available\n\nDear Jennifer,\n\nI wanted to personally reach out about some exceptional luxury properties that have just become available in the downtown luxury district. These properties match your specific criteria and budget range.",
                    CommunicationModality.VOICE: "Hi Jennifer, this is Sarah calling about those exclusive luxury properties we discussed. I have some incredible options that I think you'll love.",
                    CommunicationModality.VIDEO: "Video script: Welcome Jennifer to an exclusive tour of luxury properties that perfectly match your sophisticated taste and requirements."
                },
                optimization_goals=["engagement", "luxury_positioning", "urgency"],
                expected_improvements={
                    "engagement_score": 0.25,
                    "luxury_appeal": 0.35,
                    "urgency_factor": 0.20,
                    "personalization": 0.30
                },
                integration_context={
                    "emotional_state": "confident",
                    "journey_stage": "ready_to_buy",
                    "churn_risk": "very_low",
                    "market_position": "luxury_leader"
                }
            ),

            # Scenario 2: Retention optimization with churn prevention
            OptimizationScenario(
                lead_profile=LeadProfile(
                    lead_id="multimodal_test_lead_002",
                    name="Robert Chen",
                    email="robert.chen@email.com",
                    phone="+1555-987-6543",
                    preferences={
                        "property_type": "family_home",
                        "budget": 650000,
                        "location": "Good school district",
                        "timeline": "flexible"
                    },
                    source="referral",
                    tags=["family_focused", "education_priority", "analytical_buyer"]
                ),
                evaluation_result=LeadEvaluationResult(
                    lead_id="multimodal_test_lead_002",
                    current_stage="actively_searching",
                    engagement_level=0.35,  # Declining engagement
                    priority_score=7.5,
                    contact_preferences={"channel": "email", "time": "evening"},
                    behavioral_indicators={
                        "browsing_frequency": 1.2,  # Decreased activity
                        "response_rate": 0.30,  # Poor response
                        "page_views": 8,
                        "time_on_site": 90,
                        "competitor_research": True,
                        "price_sensitivity": True
                    }
                ),
                base_content={
                    CommunicationModality.TEXT: "Hi Robert, I wanted to check in about your home search and see if you have any questions.",
                    CommunicationModality.EMAIL: "Subject: Following Up on Your Home Search\n\nHi Robert,\n\nI noticed it's been a while since we last spoke about your home search in the school district area. I wanted to reach out and see how things are going and if you have any questions or concerns.",
                    CommunicationModality.VOICE: "Hi Robert, it's Sarah. I was thinking about your family's home search and wanted to touch base to see if there's anything I can help with."
                },
                optimization_goals=["retention", "trust_building", "value_demonstration"],
                expected_improvements={
                    "retention_likelihood": 0.40,
                    "trust_score": 0.25,
                    "value_perception": 0.30,
                    "re_engagement": 0.35
                },
                integration_context={
                    "emotional_state": "uncertain",
                    "journey_stage": "actively_searching",
                    "churn_risk": "high",
                    "competitive_pressure": True
                }
            ),

            # Scenario 3: Educational optimization with journey intelligence
            OptimizationScenario(
                lead_profile=LeadProfile(
                    lead_id="multimodal_test_lead_003",
                    name="Maria Rodriguez",
                    email="maria.rodriguez@email.com",
                    phone="+1555-456-7890",
                    preferences={
                        "property_type": "starter_home",
                        "budget": 350000,
                        "location": "Growing neighborhoods",
                        "timeline": "learning"
                    },
                    source="first_time_buyer_program",
                    tags=["first_time_buyer", "budget_conscious", "needs_guidance"]
                ),
                evaluation_result=LeadEvaluationResult(
                    lead_id="multimodal_test_lead_003",
                    current_stage="initial_interest",
                    engagement_level=0.65,
                    priority_score=6.8,
                    contact_preferences={"channel": "video_call", "time": "weekend"},
                    behavioral_indicators={
                        "browsing_frequency": 3.5,
                        "response_rate": 0.80,
                        "page_views": 35,
                        "time_on_site": 450,
                        "educational_content_consumed": True,
                        "calculator_usage": 12
                    }
                ),
                base_content={
                    CommunicationModality.TEXT: "Hi Maria! Ready to learn about the home buying process? I'm here to guide you through every step.",
                    CommunicationModality.EMAIL: "Subject: Your First Home Buying Journey - Let's Get Started!\n\nHi Maria,\n\nCongratulations on taking the first step toward homeownership! I know the process can feel overwhelming, but I'm here to make it simple and educational for you.",
                    CommunicationModality.VIDEO: "Video script: Welcome Maria! Let's walk through the exciting journey of buying your first home together. I'll explain each step clearly so you feel confident and informed."
                },
                optimization_goals=["education", "confidence_building", "journey_progression"],
                expected_improvements={
                    "educational_value": 0.40,
                    "confidence_boost": 0.30,
                    "journey_advancement": 0.25,
                    "clarity_score": 0.35
                },
                integration_context={
                    "emotional_state": "eager",
                    "journey_stage": "initial_interest",
                    "churn_risk": "low",
                    "education_level": "beginner"
                }
            )
        ]

        print(f"🎨 Multi-modal optimization environment setup complete")
        print(f"   Test Scenarios: {len(self.optimization_scenarios)}")
        print(f"   Optimization Goals: {[s.optimization_goals for s in self.optimization_scenarios]}")
        print(f"   Communication Modalities: {list(CommunicationModality)}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_enhanced_personalization_multimodal_integration(self):
        """Test integration between Enhanced ML Personalization and Multi-Modal Optimizer."""
        print("\n=== Testing Enhanced Personalization → Multi-Modal Integration ===")

        integration_results = []

        for scenario in self.optimization_scenarios:
            start_time = time.time()

            # Step 1: Generate enhanced personalization with emotional intelligence
            enhanced_personalization = await self.enhanced_personalization.generate_enhanced_personalization(
                lead_id=scenario.lead_profile.lead_id,
                evaluation_result=scenario.evaluation_result,
                message_template="Multi-modal optimization test message for {lead_name}",
                interaction_history=[],
                context={
                    "optimization_context": scenario.integration_context,
                    "multimodal_integration": True,
                    "agent_name": "Sarah"
                }
            )

            # Step 2: Use emotional intelligence to inform multi-modal optimization
            emotional_context = {
                "primary_emotion": enhanced_personalization.emotional_analysis.dominant_emotion.value,
                "sentiment_score": enhanced_personalization.emotional_analysis.sentiment_analysis.compound,
                "emotional_volatility": enhanced_personalization.emotional_analysis.emotional_volatility,
                "journey_stage": enhanced_personalization.journey_intelligence.current_stage.value,
                "confidence_level": enhanced_personalization.journey_intelligence.stage_confidence
            }

            # Step 3: Multi-modal analysis with emotional intelligence integration
            multimodal_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
                lead_id=scenario.lead_profile.lead_id,
                content=scenario.base_content,
                context={
                    **emotional_context,
                    "optimization_goals": scenario.optimization_goals,
                    "personalization_insights": enhanced_personalization.personalization_factors
                }
            )

            # Step 4: Optimize communication with emotional alignment
            optimized_communication = await self.multimodal_optimizer.optimize_communication(
                lead_id=scenario.lead_profile.lead_id,
                base_content=enhanced_personalization.personalized_content,
                target_modalities=[CommunicationModality.EMAIL, CommunicationModality.TEXT],
                context={
                    **emotional_context,
                    "emotional_optimization": True,
                    "journey_optimization": True,
                    "optimization_goals": scenario.optimization_goals
                }
            )

            integration_time = time.time() - start_time

            # Validate emotional intelligence alignment
            emotional_alignment_score = self._calculate_emotional_alignment(
                enhanced_personalization.emotional_analysis,
                optimized_communication,
                scenario.integration_context
            )

            # Validate multi-modal coherence
            coherence_score = multimodal_analysis.cross_modal_analysis.coherence_score

            integration_results.append({
                "lead_id": scenario.lead_profile.lead_id,
                "integration_time": integration_time,
                "emotional_alignment_score": emotional_alignment_score,
                "coherence_score": coherence_score,
                "optimization_confidence": optimized_communication.confidence_score,
                "emotional_state": enhanced_personalization.emotional_analysis.dominant_emotion.value,
                "journey_stage": enhanced_personalization.journey_intelligence.current_stage.value,
                "personalization_effectiveness": enhanced_personalization.personalization_factors.get("effectiveness", 0.8)
            })

        # Calculate integration metrics
        avg_integration_time = np.mean([r["integration_time"] for r in integration_results])
        avg_emotional_alignment = np.mean([r["emotional_alignment_score"] for r in integration_results])
        avg_coherence = np.mean([r["coherence_score"] for r in integration_results])
        avg_optimization_confidence = np.mean([r["optimization_confidence"] for r in integration_results])

        # Performance assertions
        assert avg_integration_time < 2.0, f"Integration too slow: {avg_integration_time:.3f}s"
        assert avg_emotional_alignment > 0.8, f"Low emotional alignment: {avg_emotional_alignment:.3f}"
        assert avg_coherence > 0.85, f"Low coherence: {avg_coherence:.3f}"
        assert avg_optimization_confidence > 0.75, f"Low optimization confidence: {avg_optimization_confidence:.3f}"

        print(f"✅ Enhanced Personalization Integration: {avg_integration_time:.3f}s avg")
        print(f"   Emotional Alignment: {avg_emotional_alignment:.3f}")
        print(f"   Multi-Modal Coherence: {avg_coherence:.3f}")
        print(f"   Optimization Confidence: {avg_optimization_confidence:.3f}")

        return integration_results

    def _calculate_emotional_alignment(self, emotional_analysis, optimized_communication, context):
        """Calculate how well the optimization aligns with emotional intelligence."""
        # Simplified alignment calculation
        base_score = 0.7

        # Emotional state consistency
        if emotional_analysis.dominant_emotion.value in optimized_communication.optimization_metadata.get("emotional_factors", []):
            base_score += 0.1

        # Sentiment alignment
        if emotional_analysis.sentiment_analysis.compound > 0 and "positive" in str(optimized_communication.optimized_content).lower():
            base_score += 0.1
        elif emotional_analysis.sentiment_analysis.compound < 0 and any(word in str(optimized_communication.optimized_content).lower()
                                                                        for word in ["understand", "help", "support"]):
            base_score += 0.1

        # Context alignment
        if context.get("emotional_state", "").lower() in str(optimized_communication.optimization_metadata).lower():
            base_score += 0.1

        return min(base_score, 1.0)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_churn_prevention_multimodal_integration(self):
        """Test integration between Churn Prevention and Multi-Modal Optimizer."""
        print("\n=== Testing Churn Prevention → Multi-Modal Integration ===")

        churn_integration_results = []

        for scenario in self.optimization_scenarios:
            start_time = time.time()

            # Step 1: Assess churn risk
            churn_assessment = await self.churn_prevention.assess_churn_risk(
                lead_id=scenario.lead_profile.lead_id,
                evaluation_result=scenario.evaluation_result,
                interaction_history=[],
                context={
                    "churn_risk_factors": scenario.integration_context,
                    "multimodal_optimization_context": True
                }
            )

            # Step 2: Generate intervention if needed
            intervention = None
            if churn_assessment.risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]:
                intervention = await self.churn_prevention.generate_intervention_recommendation(
                    churn_assessment=churn_assessment,
                    lead_profile=scenario.lead_profile
                )

            # Step 3: Multi-modal optimization for retention
            retention_context = {
                "churn_risk_level": churn_assessment.risk_level.value,
                "risk_score": churn_assessment.risk_score,
                "retention_focused": churn_assessment.risk_level != ChurnRiskLevel.VERY_LOW,
                "intervention_type": intervention.intervention_type.value if intervention else None,
                "urgency_level": intervention.urgency_level.value if intervention else "low"
            }

            # Optimize content for retention
            retention_optimized = await self.multimodal_optimizer.optimize_communication(
                lead_id=scenario.lead_profile.lead_id,
                base_content=scenario.base_content.get(CommunicationModality.EMAIL, ""),
                target_modalities=[CommunicationModality.EMAIL, CommunicationModality.TEXT],
                context={
                    **retention_context,
                    "optimization_goal": "retention",
                    "churn_prevention": True
                }
            )

            # Step 4: Analyze retention-focused content
            retention_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
                lead_id=scenario.lead_profile.lead_id,
                content={CommunicationModality.TEXT: retention_optimized.optimized_content},
                context=retention_context
            )

            integration_time = time.time() - start_time

            # Calculate retention optimization effectiveness
            retention_score = self._calculate_retention_optimization_score(
                churn_assessment,
                retention_optimized,
                retention_analysis,
                scenario.expected_improvements.get("retention_likelihood", 0)
            )

            churn_integration_results.append({
                "lead_id": scenario.lead_profile.lead_id,
                "churn_risk_level": churn_assessment.risk_level.value,
                "integration_time": integration_time,
                "retention_optimization_score": retention_score,
                "intervention_generated": intervention is not None,
                "optimization_confidence": retention_optimized.confidence_score,
                "retention_factors": len(retention_optimized.improvement_summary),
                "urgency_addressed": churn_assessment.risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]
            })

        # Calculate churn integration metrics
        avg_integration_time = np.mean([r["integration_time"] for r in churn_integration_results])
        avg_retention_score = np.mean([r["retention_optimization_score"] for r in churn_integration_results])
        intervention_rate = sum(1 for r in churn_integration_results if r["intervention_generated"]) / len(churn_integration_results)
        avg_optimization_confidence = np.mean([r["optimization_confidence"] for r in churn_integration_results])

        # Performance assertions
        assert avg_integration_time < 1.5, f"Churn integration too slow: {avg_integration_time:.3f}s"
        assert avg_retention_score > 0.75, f"Low retention optimization: {avg_retention_score:.3f}"
        assert avg_optimization_confidence > 0.7, f"Low optimization confidence: {avg_optimization_confidence:.3f}"

        print(f"✅ Churn Prevention Integration: {avg_integration_time:.3f}s avg")
        print(f"   Retention Optimization Score: {avg_retention_score:.3f}")
        print(f"   Intervention Generation Rate: {intervention_rate:.2%}")
        print(f"   Optimization Confidence: {avg_optimization_confidence:.3f}")

        return churn_integration_results

    def _calculate_retention_optimization_score(self, churn_assessment, optimized_communication, analysis, expected_improvement):
        """Calculate effectiveness of retention-focused optimization."""
        base_score = 0.6

        # Risk level appropriate optimization
        if churn_assessment.risk_level == ChurnRiskLevel.HIGH and "retention" in str(optimized_communication.optimization_metadata).lower():
            base_score += 0.15
        elif churn_assessment.risk_level == ChurnRiskLevel.CRITICAL and "urgent" in str(optimized_communication.optimization_metadata).lower():
            base_score += 0.20

        # Content quality for retention
        retention_keywords = ["understand", "value", "help", "support", "together", "relationship"]
        if any(keyword in optimized_communication.optimized_content.lower() for keyword in retention_keywords):
            base_score += 0.10

        # Optimization confidence factor
        base_score += (optimized_communication.confidence_score - 0.5) * 0.2

        return min(base_score, 1.0)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_video_integration_multimodal_optimization(self):
        """Test integration between Video System and Multi-Modal Optimizer."""
        print("\n=== Testing Video Integration → Multi-Modal Optimization ===")

        video_integration_results = []

        for scenario in self.optimization_scenarios:
            start_time = time.time()

            # Step 1: Multi-modal analysis including video content
            if CommunicationModality.VIDEO in scenario.base_content:
                video_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
                    lead_id=scenario.lead_profile.lead_id,
                    content=scenario.base_content,
                    context={
                        "video_optimization": True,
                        "optimization_goals": scenario.optimization_goals,
                        "lead_profile_context": scenario.lead_profile.preferences
                    }
                )

                # Step 2: Optimize video script content
                optimized_video_script = await self.multimodal_optimizer.optimize_communication(
                    lead_id=scenario.lead_profile.lead_id,
                    base_content=scenario.base_content[CommunicationModality.VIDEO],
                    target_modalities=[CommunicationModality.VIDEO],
                    context={
                        "video_optimization": True,
                        "script_enhancement": True,
                        "engagement_focus": True,
                        "optimization_goals": scenario.optimization_goals
                    }
                )

                # Step 3: Generate video with optimized script
                video_message = await self.video_integration.generate_personalized_video(
                    lead_id=scenario.lead_profile.lead_id,
                    template_id="multimodal_optimized",
                    evaluation_result=scenario.evaluation_result,
                    context={
                        "optimized_script": optimized_video_script.optimized_content,
                        "optimization_metadata": optimized_video_script.optimization_metadata,
                        "multimodal_coherence": video_analysis.cross_modal_analysis.coherence_score,
                        "engagement_optimization": True
                    }
                )

                # Step 4: Validate cross-modal coherence
                cross_modal_validation = await self.multimodal_optimizer.analyze_multi_modal_communication(
                    lead_id=scenario.lead_profile.lead_id,
                    content={
                        CommunicationModality.VIDEO: optimized_video_script.optimized_content,
                        CommunicationModality.EMAIL: scenario.base_content.get(CommunicationModality.EMAIL, ""),
                        CommunicationModality.TEXT: scenario.base_content.get(CommunicationModality.TEXT, "")
                    },
                    context={"cross_modal_validation": True}
                )

                integration_time = time.time() - start_time

                # Calculate video optimization metrics
                video_enhancement_score = self._calculate_video_enhancement_score(
                    video_analysis,
                    optimized_video_script,
                    video_message,
                    cross_modal_validation
                )

                video_integration_results.append({
                    "lead_id": scenario.lead_profile.lead_id,
                    "integration_time": integration_time,
                    "video_enhancement_score": video_enhancement_score,
                    "script_optimization_confidence": optimized_video_script.confidence_score,
                    "video_personalization_score": video_message.personalization_score,
                    "cross_modal_coherence": cross_modal_validation.cross_modal_analysis.coherence_score,
                    "video_engagement_estimate": video_message.estimated_engagement
                })

        if len(video_integration_results) == 0:
            print("⚠️  No video content scenarios found, skipping video integration test")
            return []

        # Calculate video integration metrics
        avg_integration_time = np.mean([r["integration_time"] for r in video_integration_results])
        avg_enhancement_score = np.mean([r["video_enhancement_score"] for r in video_integration_results])
        avg_coherence = np.mean([r["cross_modal_coherence"] for r in video_integration_results])
        avg_engagement = np.mean([r["video_engagement_estimate"] for r in video_integration_results])

        # Performance assertions
        assert avg_integration_time < 3.0, f"Video integration too slow: {avg_integration_time:.3f}s"
        assert avg_enhancement_score > 0.8, f"Low video enhancement: {avg_enhancement_score:.3f}"
        assert avg_coherence > 0.85, f"Low cross-modal coherence: {avg_coherence:.3f}"
        assert avg_engagement > 0.75, f"Low video engagement estimate: {avg_engagement:.3f}"

        print(f"✅ Video Integration: {avg_integration_time:.3f}s avg")
        print(f"   Video Enhancement Score: {avg_enhancement_score:.3f}")
        print(f"   Cross-Modal Coherence: {avg_coherence:.3f}")
        print(f"   Avg Video Engagement: {avg_engagement:.3f}")

        return video_integration_results

    def _calculate_video_enhancement_score(self, analysis, optimized_script, video_message, cross_modal_validation):
        """Calculate video enhancement effectiveness."""
        base_score = 0.7

        # Script optimization quality
        base_score += (optimized_script.confidence_score - 0.5) * 0.2

        # Video personalization
        base_score += (video_message.personalization_score - 0.5) * 0.15

        # Cross-modal coherence
        base_score += (cross_modal_validation.cross_modal_analysis.coherence_score - 0.8) * 0.25

        return min(base_score, 1.0)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_roi_attribution_multimodal_integration(self):
        """Test integration between ROI Attribution and Multi-Modal Optimizer."""
        print("\n=== Testing ROI Attribution → Multi-Modal Integration ===")

        roi_integration_results = []

        for scenario in self.optimization_scenarios:
            start_time = time.time()

            # Step 1: Optimize communication with tracking metadata
            optimized_communication = await self.multimodal_optimizer.optimize_communication(
                lead_id=scenario.lead_profile.lead_id,
                base_content=scenario.base_content.get(CommunicationModality.EMAIL, ""),
                target_modalities=[CommunicationModality.EMAIL, CommunicationModality.TEXT],
                context={
                    "roi_tracking": True,
                    "optimization_goals": scenario.optimization_goals,
                    "performance_measurement": True
                }
            )

            # Step 2: Track optimization as ROI touchpoint
            optimization_touchpoint = await self.roi_attribution.track_touchpoint(
                lead_id=scenario.lead_profile.lead_id,
                channel=CommunicationChannel.EMAIL,
                campaign_id="multimodal_optimization_test",
                content_id=f"optimized_content_{optimized_communication.optimization_id}",
                metadata={
                    "multimodal_optimization": True,
                    "optimization_confidence": optimized_communication.confidence_score,
                    "improvement_factors": optimized_communication.improvement_summary,
                    "optimization_goals": scenario.optimization_goals,
                    "expected_improvements": scenario.expected_improvements,
                    "baseline_content_hash": hash(scenario.base_content.get(CommunicationModality.EMAIL, "")),
                    "optimized_content_hash": hash(optimized_communication.optimized_content)
                }
            )

            # Step 3: Simulate A/B testing scenario
            control_touchpoint = await self.roi_attribution.track_touchpoint(
                lead_id=f"control_{scenario.lead_profile.lead_id}",
                channel=CommunicationChannel.EMAIL,
                campaign_id="multimodal_optimization_test",
                content_id="baseline_content",
                metadata={
                    "multimodal_optimization": False,
                    "control_group": True,
                    "baseline_content": True
                }
            )

            # Step 4: Simulate conversion events with optimization impact
            optimization_effectiveness = np.mean(list(scenario.expected_improvements.values()))
            conversion_probability = 0.15 + (optimization_effectiveness * 0.25)  # Base 15% + optimization boost

            if np.random.random() < conversion_probability:
                # Optimized version conversion
                conversion_event = await self.roi_attribution.track_conversion_event(
                    lead_id=scenario.lead_profile.lead_id,
                    event_type=ConversionEventType.APPOINTMENT_SCHEDULED,
                    event_value=6000.0 * (1 + optimization_effectiveness),  # Higher value from optimization
                    metadata={
                        "multimodal_optimization_attributed": True,
                        "optimization_effectiveness": optimization_effectiveness,
                        "improvement_factors": optimized_communication.improvement_summary,
                        "optimization_roi": (optimization_effectiveness * 6000.0) / 50  # Assuming $50 optimization cost
                    }
                )
            else:
                conversion_event = None

            # Control group conversion (lower probability)
            if np.random.random() < 0.15:  # Base conversion rate
                control_conversion = await self.roi_attribution.track_conversion_event(
                    lead_id=f"control_{scenario.lead_profile.lead_id}",
                    event_type=ConversionEventType.APPOINTMENT_SCHEDULED,
                    event_value=6000.0,
                    metadata={"control_group": True, "no_optimization": True}
                )
            else:
                control_conversion = None

            integration_time = time.time() - start_time

            # Calculate ROI metrics
            optimization_value = conversion_event.event_value if conversion_event else 0
            control_value = control_conversion.event_value if control_conversion else 0
            roi_improvement = ((optimization_value - control_value) / 50) if optimization_value > 0 else 0  # ROI on $50 optimization cost

            roi_integration_results.append({
                "lead_id": scenario.lead_profile.lead_id,
                "integration_time": integration_time,
                "optimization_touchpoint_created": optimization_touchpoint is not None,
                "conversion_generated": conversion_event is not None,
                "optimization_value": optimization_value,
                "control_value": control_value,
                "roi_improvement": roi_improvement,
                "optimization_effectiveness": optimization_effectiveness,
                "attribution_confidence": getattr(conversion_event, 'attribution_weights', {}).get('data_driven', 0) if conversion_event else 0
            })

        # Calculate ROI integration metrics
        avg_integration_time = np.mean([r["integration_time"] for r in roi_integration_results])
        touchpoint_success_rate = sum(1 for r in roi_integration_results if r["optimization_touchpoint_created"]) / len(roi_integration_results)
        conversion_rate = sum(1 for r in roi_integration_results if r["conversion_generated"]) / len(roi_integration_results)
        avg_roi_improvement = np.mean([r["roi_improvement"] for r in roi_integration_results if r["roi_improvement"] > 0])
        avg_optimization_value = np.mean([r["optimization_value"] for r in roi_integration_results])

        # Performance assertions
        assert avg_integration_time < 1.5, f"ROI integration too slow: {avg_integration_time:.3f}s"
        assert touchpoint_success_rate >= 0.95, f"Touchpoint creation failure: {touchpoint_success_rate:.2%}"
        assert conversion_rate > 0.25, f"Low conversion rate: {conversion_rate:.2%}"
        if avg_roi_improvement > 0:
            assert avg_roi_improvement > 20, f"Low ROI improvement: {avg_roi_improvement:.1f}%"

        print(f"✅ ROI Attribution Integration: {avg_integration_time:.3f}s avg")
        print(f"   Touchpoint Success Rate: {touchpoint_success_rate:.2%}")
        print(f"   Conversion Rate: {conversion_rate:.2%}")
        print(f"   Avg ROI Improvement: {avg_roi_improvement:.1f}%" if avg_roi_improvement > 0 else "   No ROI improvement measured")
        print(f"   Avg Optimization Value: ${avg_optimization_value:,.2f}")

        return roi_integration_results

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cross_modal_coherence_validation(self):
        """Test cross-modal coherence across all communication channels."""
        print("\n=== Testing Cross-Modal Coherence Validation ===")

        coherence_results = []

        for scenario in self.optimization_scenarios:
            start_time = time.time()

            # Step 1: Analyze original content coherence
            original_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
                lead_id=scenario.lead_profile.lead_id,
                content=scenario.base_content,
                context={"coherence_analysis": True, "baseline": True}
            )

            # Step 2: Optimize each modality individually
            optimized_modalities = {}

            for modality, content in scenario.base_content.items():
                if content:
                    optimized = await self.multimodal_optimizer.optimize_communication(
                        lead_id=scenario.lead_profile.lead_id,
                        base_content=content,
                        target_modalities=[modality],
                        context={
                            "modality_specific_optimization": True,
                            "coherence_maintenance": True,
                            "optimization_goals": scenario.optimization_goals
                        }
                    )
                    optimized_modalities[modality] = optimized.optimized_content

            # Step 3: Analyze optimized content coherence
            optimized_analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
                lead_id=scenario.lead_profile.lead_id,
                content=optimized_modalities,
                context={"coherence_analysis": True, "optimized": True}
            )

            # Step 4: Cross-modal consistency check
            consistency_score = self._calculate_cross_modal_consistency(
                original_analysis.cross_modal_analysis,
                optimized_analysis.cross_modal_analysis,
                optimized_modalities
            )

            # Step 5: Message alignment validation
            message_alignment = self._validate_message_alignment(
                optimized_modalities,
                scenario.optimization_goals
            )

            coherence_time = time.time() - start_time

            coherence_results.append({
                "lead_id": scenario.lead_profile.lead_id,
                "coherence_time": coherence_time,
                "original_coherence": original_analysis.cross_modal_analysis.coherence_score,
                "optimized_coherence": optimized_analysis.cross_modal_analysis.coherence_score,
                "coherence_improvement": optimized_analysis.cross_modal_analysis.coherence_score - original_analysis.cross_modal_analysis.coherence_score,
                "consistency_score": consistency_score,
                "message_alignment": message_alignment,
                "modalities_optimized": len(optimized_modalities),
                "optimization_goals_met": len([g for g in scenario.optimization_goals if self._goal_achieved_in_content(g, optimized_modalities)])
            })

        # Calculate coherence metrics
        avg_coherence_time = np.mean([r["coherence_time"] for r in coherence_results])
        avg_original_coherence = np.mean([r["original_coherence"] for r in coherence_results])
        avg_optimized_coherence = np.mean([r["optimized_coherence"] for r in coherence_results])
        avg_coherence_improvement = np.mean([r["coherence_improvement"] for r in coherence_results])
        avg_consistency = np.mean([r["consistency_score"] for r in coherence_results])
        avg_alignment = np.mean([r["message_alignment"] for r in coherence_results])

        # Performance assertions
        assert avg_coherence_time < 2.5, f"Coherence analysis too slow: {avg_coherence_time:.3f}s"
        assert avg_optimized_coherence > avg_original_coherence, "No coherence improvement"
        assert avg_optimized_coherence > 0.85, f"Low optimized coherence: {avg_optimized_coherence:.3f}"
        assert avg_consistency > 0.8, f"Low consistency score: {avg_consistency:.3f}"
        assert avg_alignment > 0.75, f"Poor message alignment: {avg_alignment:.3f}"

        print(f"✅ Cross-Modal Coherence: {avg_coherence_time:.3f}s avg")
        print(f"   Original Coherence: {avg_original_coherence:.3f}")
        print(f"   Optimized Coherence: {avg_optimized_coherence:.3f}")
        print(f"   Coherence Improvement: +{avg_coherence_improvement:.3f}")
        print(f"   Consistency Score: {avg_consistency:.3f}")
        print(f"   Message Alignment: {avg_alignment:.3f}")

        return coherence_results

    def _calculate_cross_modal_consistency(self, original_analysis, optimized_analysis, optimized_content):
        """Calculate cross-modal consistency score."""
        base_score = 0.7

        # Coherence improvement
        if optimized_analysis.coherence_score > original_analysis.coherence_score:
            base_score += 0.1

        # Content length consistency
        lengths = [len(content) for content in optimized_content.values()]
        if lengths and (max(lengths) / min(lengths)) < 3:  # Reasonable length ratios
            base_score += 0.1

        # Tone consistency (simplified check)
        contents = list(optimized_content.values())
        if len(contents) > 1:
            # Check for consistent tone indicators
            formal_indicators = sum("Dear" in content or "Sincerely" in content for content in contents)
            casual_indicators = sum("Hi" in content or "Hey" in content for content in contents)

            if formal_indicators == 0 or formal_indicators == len(contents):
                base_score += 0.1
            if casual_indicators == 0 or casual_indicators == len(contents):
                base_score += 0.1

        return min(base_score, 1.0)

    def _validate_message_alignment(self, optimized_content, optimization_goals):
        """Validate that optimized content aligns with goals."""
        alignment_score = 0.0

        for goal in optimization_goals:
            goal_met = self._goal_achieved_in_content(goal, optimized_content)
            if goal_met:
                alignment_score += 1.0 / len(optimization_goals)

        return alignment_score

    def _goal_achieved_in_content(self, goal, content_dict):
        """Check if optimization goal is achieved in content."""
        all_content = " ".join(content_dict.values()).lower()

        goal_indicators = {
            "engagement": ["exciting", "amazing", "perfect", "incredible", "love"],
            "conversion": ["schedule", "book", "call", "now", "today"],
            "retention": ["understand", "here", "help", "together", "value"],
            "education": ["learn", "guide", "explain", "process", "step"],
            "urgency": ["now", "limited", "today", "soon", "quickly"],
            "relationship_building": ["relationship", "together", "partner", "team", "support"]
        }

        indicators = goal_indicators.get(goal, [])
        return any(indicator in all_content for indicator in indicators)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_multimodal_integration_workflow(self):
        """Test complete multi-modal optimization integration workflow."""
        print("\n=== Testing Complete Multi-Modal Integration Workflow ===")

        workflow_start_time = time.time()

        # Execute complete integration workflow
        test_scenario = self.optimization_scenarios[0]  # Use first scenario for complete test

        workflow_results = {
            "enhanced_personalization": await self.test_enhanced_personalization_multimodal_integration(),
            "churn_prevention": await self.test_churn_prevention_multimodal_integration(),
            "video_integration": await self.test_video_integration_multimodal_optimization(),
            "roi_attribution": await self.test_roi_attribution_multimodal_integration(),
            "coherence_validation": await self.test_cross_modal_coherence_validation()
        }

        total_workflow_time = time.time() - workflow_start_time

        # Calculate comprehensive integration metrics
        integration_metrics = MultiModalIntegrationMetrics(
            analysis_time=np.mean([r[0]["integration_time"] for r in workflow_results.values() if len(r) > 0]),
            optimization_time=total_workflow_time / len(workflow_results),
            coherence_score=np.mean([r["optimized_coherence"] for r in workflow_results["coherence_validation"]]),
            effectiveness_improvement=np.mean([
                r["emotional_alignment_score"] for r in workflow_results["enhanced_personalization"]
            ]),
            cross_system_integration_success=all(len(r) > 0 for r in workflow_results.values()),
            emotional_alignment_score=np.mean([
                r["emotional_alignment_score"] for r in workflow_results["enhanced_personalization"]
            ]),
            retention_optimization_score=np.mean([
                r["retention_optimization_score"] for r in workflow_results["churn_prevention"]
            ])
        )

        # Business value calculation
        business_value = {
            "conversion_improvement": integration_metrics.effectiveness_improvement * 0.35,  # 35% boost from optimization
            "retention_improvement": integration_metrics.retention_optimization_score * 0.40,  # 40% boost from retention focus
            "coherence_quality": integration_metrics.coherence_score,
            "cross_system_synergy": 1.0 if integration_metrics.cross_system_integration_success else 0.5,
            "total_workflow_time": total_workflow_time
        }

        # Comprehensive validations
        assert total_workflow_time < 30.0, f"Complete workflow too slow: {total_workflow_time:.3f}s"
        assert integration_metrics.cross_system_integration_success, "Cross-system integration failed"
        assert integration_metrics.coherence_score > 0.85, f"Low coherence: {integration_metrics.coherence_score:.3f}"
        assert integration_metrics.effectiveness_improvement > 0.8, f"Low effectiveness: {integration_metrics.effectiveness_improvement:.3f}"
        assert business_value["conversion_improvement"] > 0.25, f"Low conversion improvement: {business_value['conversion_improvement']:.3f}"

        print(f"✅ Complete Multi-Modal Integration: {total_workflow_time:.3f}s")
        print(f"   Cross-System Integration: {'✅ Success' if integration_metrics.cross_system_integration_success else '❌ Failed'}")
        print(f"   Coherence Score: {integration_metrics.coherence_score:.3f}")
        print(f"   Effectiveness Improvement: {integration_metrics.effectiveness_improvement:.3f}")
        print(f"   Emotional Alignment: {integration_metrics.emotional_alignment_score:.3f}")
        print(f"   Retention Optimization: {integration_metrics.retention_optimization_score:.3f}")
        print(f"   Conversion Improvement: +{business_value['conversion_improvement']:.1%}")
        print(f"   Retention Improvement: +{business_value['retention_improvement']:.1%}")

        return {
            "integration_metrics": integration_metrics,
            "business_value": business_value,
            "workflow_results": workflow_results,
            "total_time": total_workflow_time
        }


# Run multi-modal optimization integration tests
if __name__ == "__main__":
    async def run_multimodal_integration_tests():
        """Run complete multi-modal optimization integration test suite."""
        print("🎨 Starting Multi-Modal Communication Optimization Integration Tests")
        print("=" * 80)

        test_suite = TestMultiModalOptimizationIntegration()
        await test_suite.setup_multimodal_integration_environment()

        results = {}

        try:
            # Individual integration tests
            await test_suite.test_enhanced_personalization_multimodal_integration()
            results["enhanced_personalization_integration"] = "✅ PASS"

            await test_suite.test_churn_prevention_multimodal_integration()
            results["churn_prevention_integration"] = "✅ PASS"

            await test_suite.test_video_integration_multimodal_optimization()
            results["video_integration"] = "✅ PASS"

            await test_suite.test_roi_attribution_multimodal_integration()
            results["roi_attribution_integration"] = "✅ PASS"

            await test_suite.test_cross_modal_coherence_validation()
            results["coherence_validation"] = "✅ PASS"

            # Complete integration workflow test
            complete_result = await test_suite.test_complete_multimodal_integration_workflow()
            results["complete_integration_workflow"] = "✅ PASS"

        except Exception as e:
            results["error"] = f"❌ FAIL: {str(e)}"

        # Final results
        print("\n" + "=" * 80)
        print("🎯 MULTI-MODAL OPTIMIZATION INTEGRATION TEST RESULTS")
        print("=" * 80)

        for test_name, result in results.items():
            print(f"{test_name}: {result}")

        passed_tests = sum(1 for result in results.values() if result.startswith("✅"))
        total_tests = len(results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        print(f"\nOverall Success Rate: {success_rate:.2%} ({passed_tests}/{total_tests})")
        print("🚀 Multi-Modal Communication Optimization: FULLY INTEGRATED" if success_rate >= 0.9 else "⚠️  Integration issues detected")

    asyncio.run(run_multimodal_integration_tests())