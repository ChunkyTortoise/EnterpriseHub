"""
Enhanced Workflow Nodes - Extended implementations for enhanced lead workflows.

This module contains enhanced node implementations used in the enhanced Lead Bot workflow graphs.
These are separated to keep the main workflow_nodes.py manageable.
"""

import time
from typing import Dict

from ghl_real_estate_ai.agents.lead.config import SequenceOptimization
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedWorkflowNodes:
    """Enhanced workflow nodes that extend the base WorkflowNodes class."""

    def __init__(self, base_nodes):
        """Initialize with reference to base WorkflowNodes instance."""
        self.base = base_nodes

    async def gather_lead_intelligence(self, state: Dict) -> Dict:
        """Gather comprehensive intelligence context for lead nurture optimization."""
        logger.info(f"Gathering lead intelligence for nurture optimization: {state['lead_id']}")

        await self.base.event_publisher.publish_bot_status_update(
            bot_type="enhanced-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="gather_lead_intelligence",
        )

        intelligence_start_time = time.time()
        intelligence_context = None

        try:
            if self.base.intelligence_middleware:
                intelligence_context = await self.base.intelligence_middleware.enhance_bot_context(
                    lead_id=state["lead_id"],
                    location_id="national",
                    bot_type="lead-bot",
                    conversation_context=state["conversation_history"],
                    preferences={
                        "sequence_day": state.get("sequence_day"),
                        "engagement_status": state.get("engagement_status"),
                        "nurture_focus": True,
                        "intent_profile": state.get("intent_profile").to_dict() if state.get("intent_profile") else {},
                    },
                )

                intelligence_performance_ms = (time.time() - intelligence_start_time) * 1000
                logger.info(f"Lead intelligence gathered for {state['lead_id']} in {intelligence_performance_ms:.1f}ms")

                return {
                    "intelligence_context": intelligence_context,
                    "intelligence_performance_ms": intelligence_performance_ms,
                }
            else:
                logger.warning(f"Intelligence middleware not available for lead {state['lead_id']}")
                return {"intelligence_context": None, "intelligence_performance_ms": 0.0}

        except Exception as e:
            intelligence_performance_ms = (time.time() - intelligence_start_time) * 1000
            logger.error(f"Failed to gather lead intelligence for {state['lead_id']}: {e}")
            return {
                "intelligence_context": None,
                "intelligence_performance_ms": intelligence_performance_ms,
            }

    async def analyze_behavioral_patterns(self, state: Dict) -> Dict:
        """Analyze lead behavioral patterns for optimization"""
        logger.info(f"Analyzing behavioral patterns for lead {state['lead_id']}")

        await self.base.event_publisher.publish_bot_status_update(
            bot_type="enhanced-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="behavioral_analysis",
        )

        pattern = None
        personality = "relationship"
        temperature_prediction = None

        # Analyze response patterns if engine available
        if self.base.analytics_engine:
            pattern = await self.base.analytics_engine.analyze_response_patterns(
                state["lead_id"], state["conversation_history"]
            )

        # Detect personality type if adapter available
        if self.base.personality_adapter:
            personality = await self.base.personality_adapter.detect_personality(state["conversation_history"])

        # Predict temperature trend if engine available
        if self.base.temperature_engine and state.get("intent_profile"):
            current_scores = {
                "frs_score": state["intent_profile"].frs.total_score,
                "pcs_score": state["intent_profile"].pcs.total_score,
            }
            temperature_prediction = await self.base.temperature_engine.predict_temperature_trend(
                state["lead_id"], current_scores
            )

        return {
            "response_pattern": pattern,
            "personality_type": personality,
            "temperature_prediction": temperature_prediction,
        }

    async def predict_sequence_optimization(self, state: Dict) -> Dict:
        """Predict optimal sequence timing and channels"""
        logger.info(f"Optimizing sequence for lead {state['lead_id']}")

        if not self.base.analytics_engine or not state.get("response_pattern"):
            # Return default optimization
            default_optimization = SequenceOptimization(
                day_3=3, day_7=7, day_14=14, day_30=30, channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )
            return {"sequence_optimization": default_optimization}

        pattern = state["response_pattern"]
        optimization = await self.base.analytics_engine.predict_optimal_sequence(pattern)

        logger.info(f"Sequence optimization: {optimization}")

        return {"sequence_optimization": optimization}

    async def apply_track3_market_intelligence(self, state: Dict) -> Dict:
        """Apply Track 3.1 market timing intelligence to enhance nurture sequence"""
        logger.info(f"Applying Track 3.1 market intelligence for lead {state['lead_id']}")

        await self.base.event_publisher.publish_bot_status_update(
            bot_type="enhanced-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="track3_market_analysis",
        )

        try:
            if not self.base.ml_analytics:
                logger.warning("Track 3.1 ML analytics not available")
                return {"track3_applied": False, "fallback_reason": "ML analytics not available"}

            # Get comprehensive predictive analysis
            journey_analysis = await self.base.ml_analytics.predict_lead_journey(state["lead_id"])
            conversion_analysis = await self.base.ml_analytics.predict_conversion_probability(
                state["lead_id"], state.get("current_journey_stage", "nurture")
            )
            touchpoint_analysis = await self.base.ml_analytics.predict_optimal_touchpoints(state["lead_id"])

            return {
                "journey_analysis": journey_analysis,
                "conversion_analysis": conversion_analysis,
                "touchpoint_analysis": touchpoint_analysis,
                "track3_applied": True,
            }

        except Exception as e:
            logger.error(f"Track 3.1 market intelligence failed for {state['lead_id']}: {e}")
            return {"track3_applied": False, "fallback_reason": str(e)}

    async def send_optimized_day_3(self, state: Dict) -> Dict:
        """Day 3 with enhanced timing and personalization"""
        logger.info(f"Sending intelligence-optimized Day 3 SMS for {state['lead_name']}")

        optimization = state.get("enhanced_optimization", state.get("sequence_optimization"))
        pattern = state.get("response_pattern")
        personality = state.get("personality_type", "relationship")
        intelligence_context = state.get("intelligence_context")

        churn_risk = 0.5
        personalized_insights = []

        if intelligence_context:
            churn_risk = self._extract_churn_risk(intelligence_context)
            getattr(intelligence_context, "preferred_engagement_timing", None)
            personalized_insights = getattr(intelligence_context, "priority_insights", []) or []

        actual_day = optimization.day_3 if optimization else 3
        preferred_channel = (
            optimization.channel_sequence[0] if optimization and optimization.channel_sequence else "SMS"
        )

        if churn_risk > 0.7:
            actual_day = max(1, actual_day - 1)
        elif churn_risk < 0.3:
            actual_day = min(5, actual_day + 1)

        base_msg = self.base.response_generator.construct_intelligent_day3_message(
            lead_name=state["lead_name"],
            intelligence_context=intelligence_context,
            personalized_insights=personalized_insights,
            critical_scenario=state.get("critical_scenario"),
            tone_variant=state.get("tone_variant", "empathetic"),
        )

        # Adapt message for personality
        adapted_msg = base_msg
        if self.base.personality_adapter and pattern:
            adapted_msg = await self.base.personality_adapter.adapt_message(base_msg, personality, pattern)

        logger.info(f"Enhanced Day {actual_day} {preferred_channel} to {state['lead_name']}: {adapted_msg}")

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_7_call",
            "response_content": adapted_msg,
            "churn_risk_score": churn_risk,
        }

    async def initiate_predictive_day_7(self, state: Dict) -> Dict:
        """Day 7 with predictive timing and channel optimization"""
        logger.info(f"Initiating intelligence-enhanced Day 7 call for {state['lead_name']}")

        optimization = state.get("enhanced_optimization", state.get("sequence_optimization"))
        intelligence_context = state.get("intelligence_context")
        churn_risk = state.get("churn_risk_score", 0.5)

        cross_bot_handoff_eligible = False

        if intelligence_context:
            engagement_score = intelligence_context.composite_engagement_score
            objections_detected = len(intelligence_context.conversation_intelligence.objections_detected)

            if engagement_score > 0.7 and churn_risk < 0.4 and objections_detected < 2:
                cross_bot_handoff_eligible = True

        preferred_channel = (
            optimization.channel_sequence[1] if optimization and len(optimization.channel_sequence) > 1 else "Voice"
        )
        actual_day = optimization.day_7 if optimization else 7

        msg = f"Intelligence-enhanced Day {actual_day} {preferred_channel} call for {state['lead_name']}"
        if cross_bot_handoff_eligible:
            msg += " (Jorge handoff candidate)"

        logger.info(msg)

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_14_email",
            "response_content": msg,
            "jorge_handoff_eligible": cross_bot_handoff_eligible,
        }

    async def send_adaptive_day_14(self, state: Dict) -> Dict:
        """Day 14 with adaptive messaging and channel selection"""
        logger.info(f"Sending intelligence-adaptive Day 14 message for {state['lead_name']}")

        optimization = state.get("enhanced_optimization", state.get("sequence_optimization"))
        intelligence_context = state.get("intelligence_context")
        churn_risk = state.get("churn_risk_score", 0.5)

        preferred_channel = (
            optimization.channel_sequence[2] if optimization and len(optimization.channel_sequence) > 2 else "Email"
        )

        content_adaptation_applied = False

        if intelligence_context:
            objections = intelligence_context.conversation_intelligence.objections_detected
            sentiment = intelligence_context.conversation_intelligence.overall_sentiment

            if objections and sentiment < 0:
                preferred_channel = "Voice"
                content_adaptation_applied = True

            if intelligence_context.property_intelligence.match_count > 0:
                content_adaptation_applied = True

        if churn_risk > 0.8:
            preferred_channel = "Voice"

        msg = self.base.response_generator.construct_adaptive_day14_message(
            lead_name=state["lead_name"],
            intelligence_context=intelligence_context,
            preferred_channel=preferred_channel,
            content_adaptation_applied=content_adaptation_applied,
            tone_variant=state.get("tone_variant", "empathetic"),
        )

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_30_nudge",
            "response_content": msg,
            "churn_risk_score": churn_risk,
        }

    async def send_intelligent_day_30(self, state: Dict) -> Dict:
        """Day 30 with intelligent re-engagement strategy"""
        logger.info(f"Executing intelligent Day 30 final engagement for {state['lead_name']}")

        state.get("enhanced_optimization", state.get("sequence_optimization"))
        intelligence_context = state.get("intelligence_context")
        churn_risk = state.get("churn_risk_score", 0.5)

        # Determine final strategy
        final_strategy = "nurture"
        intelligence_score = 0.0
        handoff_reasoning = []

        if intelligence_context:
            engagement_score = intelligence_context.composite_engagement_score
            property_matches = intelligence_context.property_intelligence.match_count
            objections_count = len(intelligence_context.conversation_intelligence.objections_detected)
            sentiment = intelligence_context.conversation_intelligence.overall_sentiment
            preference_completeness = intelligence_context.preference_intelligence.profile_completeness

            intelligence_score = (
                engagement_score * 0.3
                + min(property_matches / 5.0, 1.0) * 0.2
                + max(0, (5 - objections_count) / 5.0) * 0.2
                + max(0, (sentiment + 1) / 2.0) * 0.15
                + preference_completeness * 0.15
            )

            if intelligence_score > 0.7 and churn_risk < 0.4:
                final_strategy = "jorge_qualification"
                handoff_reasoning.append(f"High intelligence score ({intelligence_score:.2f})")
            elif intelligence_score > 0.5 and property_matches > 2 and sentiment > 0:
                final_strategy = "jorge_consultation"
            elif intelligence_score < 0.3 or churn_risk > 0.8:
                final_strategy = "graceful_disengage"

        # Execute Jorge handoff if recommended
        if final_strategy in ["jorge_qualification", "jorge_consultation"] and self.base.config.jorge_handoff_enabled:
            await self.base.handoff_manager.publish_intelligent_jorge_handoff_request(
                state, intelligence_context, final_strategy, intelligence_score, handoff_reasoning
            )

        msg = self.base.response_generator.construct_intelligent_day30_message(
            lead_name=state["lead_name"],
            final_strategy=final_strategy,
            intelligence_score=intelligence_score,
            handoff_reasoning=handoff_reasoning,
            tone_variant=state.get("tone_variant", "empathetic"),
        )

        return {
            "engagement_status": "enhanced_final",
            "current_step": final_strategy,
            "response_content": msg,
            "jorge_handoff_recommended": final_strategy in ["jorge_qualification", "jorge_consultation"],
            "final_strategy": final_strategy,
            "intelligence_score": intelligence_score,
        }

    def _extract_churn_risk(self, intelligence_context) -> float:
        """Extract churn risk score from intelligence context"""
        if not intelligence_context:
            return 0.5

        risk_factors = []

        sentiment = intelligence_context.conversation_intelligence.overall_sentiment
        if sentiment < -0.3:
            risk_factors.append(0.8)
        elif sentiment > 0.3:
            risk_factors.append(0.2)
        else:
            risk_factors.append(0.5)

        engagement_score = intelligence_context.composite_engagement_score
        risk_factors.append(1.0 - engagement_score)

        preference_completeness = intelligence_context.preference_intelligence.profile_completeness
        if preference_completeness < 0.3:
            risk_factors.append(0.7)
        else:
            risk_factors.append(0.3)

        return sum(risk_factors) / len(risk_factors)
