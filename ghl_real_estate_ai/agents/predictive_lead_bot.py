"""
Predictive Lead Bot - Enhanced Lifecycle Management
ML-powered timing optimization with behavioral pattern recognition.
Extends the base LeadBotWorkflow with Track 1 enhancements.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.workflows import LeadFollowUpState

# Track 3.1 Integration
try:
    from bots.shared.ml_analytics_engine import (
        ConversionProbabilityAnalysis,
        LeadJourneyPrediction,
        MLAnalyticsEngine,
        TouchpointOptimization,
    )
except ImportError:
    from ghl_real_estate_ai.stubs.bots_stub import (
        ConversionProbabilityAnalysis,
        LeadJourneyPrediction,
        MLAnalyticsEngine,
        TouchpointOptimization,
    )

logger = get_logger(__name__)


@dataclass
class ResponsePattern:
    """Tracks lead response patterns for optimization."""

    avg_response_hours: float
    response_count: int
    channel_preferences: Dict[str, float]  # SMS, Email, Voice, WhatsApp
    engagement_velocity: str  # "fast", "moderate", "slow"
    best_contact_times: List[int]  # Hours of day (0-23)
    message_length_preference: str  # "brief", "detailed"


@dataclass
class SequenceOptimization:
    """Optimized sequence timing based on behavioral patterns."""

    day_3: int
    day_7: int
    day_14: int
    day_30: int
    channel_sequence: List[str]  # Ordered list of channels to use


class BehavioralAnalyticsEngine:
    """Analyzes lead behavior patterns for predictive optimization."""

    def __init__(self):
        self._patterns_cache: Dict[str, ResponsePattern] = {}

    async def analyze_response_patterns(self, lead_id: str, conversation_history: List[Dict]) -> ResponsePattern:
        """Analyze lead's response patterns for optimization."""

        if lead_id in self._patterns_cache:
            return self._patterns_cache[lead_id]

        # Calculate response velocity
        response_times = []
        for i in range(1, len(conversation_history)):
            current_msg = conversation_history[i]
            prev_msg = conversation_history[i - 1]

            # Mock timestamp analysis (in production, use actual timestamps)
            if current_msg.get("role") == "user" and prev_msg.get("role") == "assistant":
                # Simulate response time analysis
                response_times.append(4.5)  # Mock: 4.5 hours average

        avg_response_hours = sum(response_times) / len(response_times) if response_times else 24.0

        # Determine engagement velocity
        if avg_response_hours < 2:
            velocity = "fast"
        elif avg_response_hours < 12:
            velocity = "moderate"
        else:
            velocity = "slow"

        # Analyze channel preferences (mock implementation)
        channel_prefs = {"SMS": 0.8, "Email": 0.3, "Voice": 0.6, "WhatsApp": 0.2}

        # Analyze message length preference
        avg_msg_length = sum(len(m.get("content", "").split()) for m in conversation_history if m.get("role") == "user")
        avg_msg_length = avg_msg_length / max(1, len([m for m in conversation_history if m.get("role") == "user"]))

        length_pref = "brief" if avg_msg_length < 10 else "detailed"

        pattern = ResponsePattern(
            avg_response_hours=avg_response_hours,
            response_count=len([m for m in conversation_history if m.get("role") == "user"]),
            channel_preferences=channel_prefs,
            engagement_velocity=velocity,
            best_contact_times=[9, 14, 18],  # Mock: 9 AM, 2 PM, 6 PM
            message_length_preference=length_pref,
        )

        self._patterns_cache[lead_id] = pattern
        return pattern

    async def predict_optimal_sequence(self, pattern: ResponsePattern) -> SequenceOptimization:
        """Predict optimal sequence timing based on behavioral patterns."""

        # Optimize intervals based on response velocity
        if pattern.engagement_velocity == "fast":
            # Accelerate sequence for fast responders
            optimization = SequenceOptimization(
                day_3=1,  # Contact tomorrow
                day_7=3,  # Contact in 3 days
                day_14=7,  # Contact in 1 week
                day_30=14,  # Contact in 2 weeks
                channel_sequence=["SMS", "Voice", "SMS", "Email"],
            )
        elif pattern.engagement_velocity == "slow":
            # Extend intervals for slow responders
            optimization = SequenceOptimization(
                day_3=5,  # Wait 5 days
                day_7=14,  # Wait 2 weeks
                day_14=21,  # Wait 3 weeks
                day_30=45,  # Wait 6+ weeks
                channel_sequence=["Email", "SMS", "Voice", "SMS"],
            )
        else:
            # Standard intervals for moderate responders
            optimization = SequenceOptimization(
                day_3=3, day_7=7, day_14=14, day_30=30, channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )

        # Adjust channel sequence based on preferences
        sorted_channels = sorted(pattern.channel_preferences.items(), key=lambda x: x[1], reverse=True)
        optimization.channel_sequence = [ch[0] for ch in sorted_channels]

        return optimization


class PersonalityAdapter:
    """Adapts messaging based on lead personality and preferences."""

    def __init__(self):
        self.personality_profiles = {
            "analytical": {
                "style": "data-driven",
                "tone": "professional",
                "format": "bullet points",
                "keywords": ["analysis", "data", "research", "comparison"],
            },
            "relationship": {
                "style": "personal",
                "tone": "warm",
                "format": "conversational",
                "keywords": ["understand", "help", "partnership", "together"],
            },
            "results": {
                "style": "direct",
                "tone": "urgent",
                "format": "brief",
                "keywords": ["action", "results", "quickly", "efficiently"],
            },
            "security": {
                "style": "cautious",
                "tone": "reassuring",
                "format": "detailed",
                "keywords": ["safe", "secure", "guaranteed", "protected"],
            },
        }

    async def detect_personality(self, conversation_history: List[Dict]) -> str:
        """Detect lead personality type from conversation patterns."""
        all_text = " ".join([m.get("content", "").lower() for m in conversation_history])

        personality_scores = {}
        for personality, profile in self.personality_profiles.items():
            score = sum(1 for keyword in profile["keywords"] if keyword in all_text)
            personality_scores[personality] = score

        # Return highest scoring personality or default to 'relationship'
        return (
            max(personality_scores, key=personality_scores.get) if any(personality_scores.values()) else "relationship"
        )

    async def adapt_message(self, base_message: str, personality_type: str, pattern: ResponsePattern) -> str:
        """Adapt message based on personality type and response patterns."""
        profile = self.personality_profiles.get(personality_type, self.personality_profiles["relationship"])

        # Adjust message length based on preference
        if pattern.message_length_preference == "brief" and profile["format"] != "brief":
            # Shorten message for brief preference
            sentences = base_message.split(". ")
            adapted_message = ". ".join(sentences[:2]) + "."
        else:
            adapted_message = base_message

        # Add personality-specific elements
        if personality_type == "analytical":
            adapted_message = f"Based on market data: {adapted_message}"
        elif personality_type == "relationship":
            adapted_message = f"I wanted to personally reach out: {adapted_message}"
        elif personality_type == "results":
            adapted_message = f"Quick update: {adapted_message}"
        elif personality_type == "security":
            adapted_message = f"To ensure we're on the right track: {adapted_message}"

        return adapted_message


class TemperaturePredictionEngine:
    """Predicts lead temperature changes and provides early warnings."""

    def __init__(self):
        self.temperature_history: Dict[str, List[float]] = {}

    async def predict_temperature_trend(self, lead_id: str, current_scores: Dict[str, float]) -> Dict:
        """Predict lead temperature trend and provide early warnings."""

        # Store current temperature score
        current_temp = (current_scores.get("frs_score", 0) + current_scores.get("pcs_score", 0)) / 2

        if lead_id not in self.temperature_history:
            self.temperature_history[lead_id] = []

        self.temperature_history[lead_id].append(current_temp)

        # Keep only last 10 interactions for trend analysis
        if len(self.temperature_history[lead_id]) > 10:
            self.temperature_history[lead_id] = self.temperature_history[lead_id][-10:]

        history = self.temperature_history[lead_id]

        # Predict trend
        if len(history) < 2:
            trend = "stable"
            confidence = 0.5
            diff = 0
        else:
            # Simple linear trend analysis
            recent_avg = sum(history[-3:]) / min(3, len(history))
            older_avg = sum(history[:-3]) / max(1, len(history) - 3) if len(history) > 3 else recent_avg

            diff = recent_avg - older_avg

            if abs(diff) < 5:
                trend = "stable"
                confidence = 0.8
            elif diff > 0:
                trend = "heating_up"
                confidence = 0.7
            else:
                trend = "cooling_down"
                confidence = 0.7

        # Generate early warning if cooling
        early_warning = None
        if trend == "cooling_down" and current_temp > 40:
            early_warning = {
                "type": "temperature_declining",
                "urgency": "medium",
                "recommendation": "Immediate engagement recommended - lead showing signs of disengagement",
                "suggested_action": "Schedule call within 24 hours",
            }

        return {
            "current_temperature": current_temp,
            "trend": trend,
            "confidence": confidence,
            "early_warning": early_warning,
            "prediction_next_interaction": max(0, current_temp + (diff * 1.5)),
        }


class PredictiveLeadBot(LeadBotWorkflow):
    """
    Enhanced Lead Bot with ML-powered timing and behavioral optimization.
    Extends base functionality with predictive analytics.
    """

    def __init__(self, ghl_client=None):
        super().__init__(ghl_client)
        self.analytics_engine = BehavioralAnalyticsEngine()
        self.personality_adapter = PersonalityAdapter()
        self.temperature_engine = TemperaturePredictionEngine()

        # Track 3.1: ML Analytics Engine for market timing intelligence
        self.ml_analytics = MLAnalyticsEngine(tenant_id="jorge_lead_bot")

        # Add bot coordination capability to event publisher
        self.event_publisher.publish_bot_coordination_request = lambda **kwargs: publish_bot_coordination_request(
            self.event_publisher, **kwargs
        )

        # Override workflow with enhanced capabilities
        self.workflow = self._build_predictive_graph()

    def _build_predictive_graph(self) -> StateGraph:
        """Build enhanced workflow with predictive analytics."""
        workflow = StateGraph(LeadFollowUpState)

        # Enhanced nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("behavioral_analysis", self.analyze_behavioral_patterns)  # NEW
        workflow.add_node("predict_optimization", self.predict_sequence_optimization)  # NEW
        workflow.add_node("track3_market_intelligence", self.apply_track3_market_intelligence)  # TRACK 3.1
        workflow.add_node("determine_path", self.determine_path)
        workflow.add_node("generate_cma", self.generate_cma)

        # Optimized follow-up nodes
        workflow.add_node("send_optimized_day_3", self.send_optimized_day_3)  # ENHANCED
        workflow.add_node("initiate_predictive_day_7", self.initiate_predictive_day_7)  # ENHANCED
        workflow.add_node("send_adaptive_day_14", self.send_adaptive_day_14)  # ENHANCED
        workflow.add_node("send_intelligent_day_30", self.send_intelligent_day_30)  # ENHANCED

        # Lifecycle nodes (enhanced)
        workflow.add_node("schedule_showing", self.schedule_showing)
        workflow.add_node("post_showing_survey", self.post_showing_survey)
        workflow.add_node("facilitate_offer", self.facilitate_offer)
        workflow.add_node("contract_to_close_nurture", self.contract_to_close_nurture)

        # Enhanced flow with Track 3.1
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "behavioral_analysis")
        workflow.add_edge("behavioral_analysis", "predict_optimization")
        workflow.add_edge("predict_optimization", "track3_market_intelligence")  # TRACK 3.1
        workflow.add_edge("track3_market_intelligence", "determine_path")

        # Enhanced conditional routing
        workflow.add_conditional_edges(
            "determine_path",
            self._route_predictive_step,
            {
                "generate_cma": "generate_cma",
                "day_3": "send_optimized_day_3",
                "day_7": "initiate_predictive_day_7",
                "day_14": "send_adaptive_day_14",
                "day_30": "send_intelligent_day_30",
                "schedule_showing": "schedule_showing",
                "post_showing": "post_showing_survey",
                "facilitate_offer": "facilitate_offer",
                "closing_nurture": "contract_to_close_nurture",
                "qualified": END,
                "nurture": END,
            },
        )

        # All actions end
        for node in [
            "generate_cma",
            "send_optimized_day_3",
            "initiate_predictive_day_7",
            "send_adaptive_day_14",
            "send_intelligent_day_30",
            "schedule_showing",
            "post_showing_survey",
            "facilitate_offer",
            "contract_to_close_nurture",
        ]:
            workflow.add_edge(node, END)

        return workflow.compile()

    # --- New Enhancement Nodes ---

    async def analyze_behavioral_patterns(self, state: LeadFollowUpState) -> Dict:
        """Analyze lead behavioral patterns for optimization."""
        logger.info(f"Analyzing behavioral patterns for lead {state['lead_id']}")

        await self.event_publisher.publish_bot_status_update(
            bot_type="predictive-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="behavioral_analysis",
        )

        # Analyze response patterns
        pattern = await self.analytics_engine.analyze_response_patterns(state["lead_id"], state["conversation_history"])

        # Detect personality type
        personality = await self.personality_adapter.detect_personality(state["conversation_history"])

        # Predict temperature trend
        current_scores = {
            "frs_score": state["intent_profile"].frs.total_score,
            "pcs_score": state["intent_profile"].pcs.total_score,
        }
        temperature_prediction = await self.temperature_engine.predict_temperature_trend(
            state["lead_id"], current_scores
        )

        # Emit behavioral analysis event
        await self.event_publisher.publish_behavioral_analysis_complete(
            contact_id=state["lead_id"],
            response_velocity=pattern.engagement_velocity,
            personality_type=personality,
            temperature_trend=temperature_prediction["trend"],
            early_warning=temperature_prediction.get("early_warning"),
            channel_preferences=pattern.channel_preferences,
        )

        return {
            "response_pattern": pattern,
            "personality_type": personality,
            "temperature_prediction": temperature_prediction,
        }

    async def predict_sequence_optimization(self, state: LeadFollowUpState) -> Dict:
        """Predict optimal sequence timing and channels."""
        logger.info(f"Optimizing sequence for lead {state['lead_id']}")

        pattern = state["response_pattern"]
        optimization = await self.analytics_engine.predict_optimal_sequence(pattern)

        logger.info(f"Sequence optimization: {optimization}")

        return {"sequence_optimization": optimization}

    async def apply_track3_market_intelligence(self, state: LeadFollowUpState) -> Dict:
        """
        Track 3.1: Apply market timing intelligence to enhance nurture sequence.

        Integrates ML-powered predictions for:
        - Lead journey progression and bottlenecks
        - Stage-specific conversion probability
        - Optimal touchpoint timing and channels
        """
        logger.info(f"Applying Track 3.1 market intelligence for lead {state['lead_id']}")

        await self.event_publisher.publish_bot_status_update(
            bot_type="predictive-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="track3_market_analysis",
        )

        try:
            # TRACK 3.1 ENHANCEMENT: Get comprehensive predictive analysis
            journey_analysis = await self.ml_analytics.predict_lead_journey(state["lead_id"])
            conversion_analysis = await self.ml_analytics.predict_conversion_probability(
                state["lead_id"], state.get("current_journey_stage", "nurture")
            )
            touchpoint_analysis = await self.ml_analytics.predict_optimal_touchpoints(state["lead_id"])

            # Apply market timing enhancements to existing sequence optimization
            enhanced_optimization = await self._apply_market_timing_intelligence(
                state["sequence_optimization"], journey_analysis, conversion_analysis, touchpoint_analysis
            )

            # Detect critical scenarios requiring immediate action
            critical_scenario = await self._detect_critical_scenarios(journey_analysis, conversion_analysis, state)

            # Emit Track 3.1 analysis complete event
            await self.event_publisher.publish_bot_status_update(
                bot_type="predictive-lead-bot",
                contact_id=state["lead_id"],
                status="enhanced",
                current_step="track3_analysis_complete",
                additional_data={
                    "conversion_probability": journey_analysis.conversion_probability,
                    "stage_progression_velocity": journey_analysis.stage_progression_velocity,
                    "response_pattern": touchpoint_analysis.response_pattern,
                    "urgency_score": conversion_analysis.urgency_score,
                    "optimal_action": conversion_analysis.optimal_action,
                    "critical_scenario": critical_scenario,
                    "enhancement_applied": True,
                    "processing_time_ms": (
                        journey_analysis.processing_time_ms
                        + conversion_analysis.processing_time_ms
                        + touchpoint_analysis.processing_time_ms
                    ),
                },
            )

            return {
                "journey_analysis": journey_analysis,
                "conversion_analysis": conversion_analysis,
                "touchpoint_analysis": touchpoint_analysis,
                "enhanced_optimization": enhanced_optimization,
                "critical_scenario": critical_scenario,
                "track3_applied": True,
            }

        except Exception as e:
            logger.error(f"Track 3.1 market intelligence failed for {state['lead_id']}: {e}")
            # Graceful fallback - continue with existing optimization
            return {
                "track3_applied": False,
                "fallback_reason": str(e),
                "enhanced_optimization": state["sequence_optimization"],
            }

    # --- Enhanced Follow-up Nodes ---

    async def send_optimized_day_3(self, state: LeadFollowUpState) -> Dict:
        """Day 3 with Track 3.1 enhanced timing and personalization."""
        # Use Track 3.1 enhanced optimization if available
        optimization = state.get("enhanced_optimization", state["sequence_optimization"])
        pattern = state["response_pattern"]
        personality = state["personality_type"]

        # Track 3.1: Use market-intelligent timing
        actual_day = optimization.day_3
        preferred_channel = optimization.channel_sequence[0] if optimization.channel_sequence else "SMS"

        # Track 3.1: Check for critical scenarios requiring special handling
        critical_scenario = state.get("critical_scenario")
        if critical_scenario and critical_scenario["urgency"] == "critical":
            logger.warning(f"CRITICAL SCENARIO: {critical_scenario['type']} - {critical_scenario['recommendation']}")
            # Override to immediate contact for critical scenarios
            actual_day = 0  # Contact immediately
            preferred_channel = "Voice"  # Use most direct channel

        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=actual_day,
            action_type="track3_optimized_outreach",
            success=True,
            channel=preferred_channel,
            personalization_applied=True,
            track3_enhancement=state.get("track3_applied", False),
            critical_scenario=critical_scenario,
        )

        # Base message with Track 3.1 context
        if critical_scenario:
            base_msg = f"Hi {state['lead_name']}, following up on your property search. I have some time-sensitive information that could be valuable."
        else:
            base_msg = (
                f"Hi {state['lead_name']}, checking in about your property search. Any questions about the market?"
            )

        # Adapt message for personality
        adapted_msg = await self.personality_adapter.adapt_message(base_msg, personality, pattern)

        logger.info(f"Track 3.1 Enhanced Day {actual_day} {preferred_channel} to {state['lead_name']}: {adapted_msg}")

        return {
            "engagement_status": "track3_predictive_nurture",
            "current_step": "day_7_call",
            "optimized_timing_applied": True,
            "personalization_applied": True,
            "track3_enhancement_applied": state.get("track3_applied", False),
            "critical_scenario_handled": bool(critical_scenario),
        }

    async def initiate_predictive_day_7(self, state: LeadFollowUpState) -> Dict:
        """Day 7 with Track 3.1 predictive timing and channel optimization."""
        # Use Track 3.1 enhanced optimization
        optimization = state.get("enhanced_optimization", state["sequence_optimization"])
        temperature_pred = state["temperature_prediction"]
        journey_analysis = state.get("journey_analysis")
        conversion_analysis = state.get("conversion_analysis")

        # Track 3.1: Check conversion probability for Jorge handoff consideration
        if (
            conversion_analysis
            and conversion_analysis.stage_conversion_probability > 0.7
            and journey_analysis
            and journey_analysis.conversion_probability > 0.6
        ):
            logger.info(f"TRACK 3.1: High conversion indicators for {state['lead_name']} - consider Jorge handoff")
            await self.event_publisher.publish_bot_status_update(
                bot_type="predictive-lead-bot",
                contact_id=state["lead_id"],
                status="jorge_handoff_recommended",
                current_step="day_7_high_potential",
                additional_data={
                    "conversion_probability": journey_analysis.conversion_probability,
                    "stage_conversion_probability": conversion_analysis.stage_conversion_probability,
                    "recommendation": "Consider Jorge Seller Bot engagement for qualification",
                },
            )

        # Check for temperature early warning
        if temperature_pred.get("early_warning"):
            logger.warning(
                f"Temperature early warning for {state['lead_name']}: {temperature_pred['early_warning']['recommendation']}"
            )

        # Use Track 3.1 optimized channel and timing
        preferred_channel = optimization.channel_sequence[1] if len(optimization.channel_sequence) > 1 else "Voice"
        actual_day = optimization.day_7

        logger.info(f"Track 3.1 Predictive Day {actual_day} {preferred_channel} call for {state['lead_name']}")

        return {
            "engagement_status": "track3_predictive_nurture",
            "current_step": "day_14_email",
            "jorge_handoff_eligible": (conversion_analysis and conversion_analysis.stage_conversion_probability > 0.7)
            if conversion_analysis
            else False,
        }

    async def send_adaptive_day_14(self, state: LeadFollowUpState) -> Dict:
        """Day 14 with Track 3.1 adaptive messaging and channel selection."""
        # Use Track 3.1 enhanced optimization
        optimization = state.get("enhanced_optimization", state["sequence_optimization"])
        state["personality_type"]
        journey_analysis = state.get("journey_analysis")
        conversion_analysis = state.get("conversion_analysis")

        preferred_channel = optimization.channel_sequence[2] if len(optimization.channel_sequence) > 2 else "Email"
        actual_day = optimization.day_14

        # Track 3.1: Check for bottlenecks requiring intervention
        intervention_needed = False
        if (
            journey_analysis
            and journey_analysis.stage_bottlenecks
            and conversion_analysis
            and conversion_analysis.urgency_score > 0.6
        ):
            intervention_needed = True
            logger.warning(
                f"TRACK 3.1: Stage bottlenecks detected for {state['lead_name']}: {journey_analysis.stage_bottlenecks}"
            )

            # Escalate to more direct channel for bottleneck resolution
            preferred_channel = "Voice"  # Override to voice call for bottleneck resolution

            await self.event_publisher.publish_bot_status_update(
                bot_type="predictive-lead-bot",
                contact_id=state["lead_id"],
                status="bottleneck_intervention",
                current_step="day_14_bottleneck_resolution",
                additional_data={
                    "bottlenecks": journey_analysis.stage_bottlenecks,
                    "urgency_score": conversion_analysis.urgency_score,
                    "intervention": "escalated_to_voice_call",
                    "optimal_action": conversion_analysis.optimal_action,
                },
            )

        logger.info(f"Track 3.1 Adaptive Day {actual_day} {preferred_channel} for {state['lead_name']}")

        return {
            "engagement_status": "track3_predictive_nurture",
            "current_step": "day_30_nudge",
            "bottleneck_intervention": intervention_needed,
            "channel_escalated": intervention_needed,
        }

    async def send_intelligent_day_30(self, state: LeadFollowUpState) -> Dict:
        """Day 30 with Track 3.1 intelligent re-engagement strategy."""
        # Use Track 3.1 enhanced optimization
        optimization = state.get("enhanced_optimization", state["sequence_optimization"])
        temperature_pred = state["temperature_prediction"]
        journey_analysis = state.get("journey_analysis")
        conversion_analysis = state.get("conversion_analysis")

        actual_day = optimization.day_30

        # Track 3.1: Final decision point - nurture vs qualify vs disengage
        final_strategy = "nurture"  # Default

        if journey_analysis and conversion_analysis:
            # High potential - recommend Jorge qualification
            if journey_analysis.conversion_probability > 0.5 and conversion_analysis.stage_conversion_probability > 0.4:
                final_strategy = "jorge_qualification"

                await self.event_publisher.publish_bot_coordination_request(
                    source_bot="predictive-lead-bot",
                    target_bot="jorge-seller-bot",
                    contact_id=state["lead_id"],
                    handoff_type="day_30_qualification",
                    handoff_data={
                        "conversion_probability": journey_analysis.conversion_probability,
                        "stage_conversion_probability": conversion_analysis.stage_conversion_probability,
                        "lead_temperature": temperature_pred.get("current_temperature", 0),
                        "sequence_completion": "day_30_reached",
                        "recommendation": "Jorge confrontational qualification recommended",
                    },
                )

            # Low potential with cooling trend - disengage gracefully
            elif journey_analysis.conversion_probability < 0.2 and conversion_analysis.drop_off_risk > 0.8:
                final_strategy = "graceful_disengage"

        logger.info(
            f"Track 3.1 Intelligent Day {actual_day} final engagement for {state['lead_name']} - Strategy: {final_strategy}"
        )

        return {
            "engagement_status": "track3_intelligent_final",
            "current_step": final_strategy,
            "jorge_handoff_recommended": final_strategy == "jorge_qualification",
            "sequence_complete": True,
            "final_strategy": final_strategy,
        }

    # --- Helper Logic ---

    def _route_predictive_step(
        self, state: LeadFollowUpState
    ) -> Literal[
        "generate_cma",
        "day_3",
        "day_7",
        "day_14",
        "day_30",
        "schedule_showing",
        "post_showing",
        "facilitate_offer",
        "closing_nurture",
        "qualified",
        "nurture",
    ]:
        """Enhanced routing with predictive logic."""
        # Check for early warnings that require immediate action
        if state.get("temperature_prediction", {}).get("early_warning"):
            warning = state["temperature_prediction"]["early_warning"]
            if warning.get("urgency") == "high":
                return "schedule_showing"  # Immediate escalation

        # Use parent routing logic with enhancements
        return super()._route_next_step(state)

    # --- Track 3.1 Enhancement Methods ---

    async def _apply_market_timing_intelligence(
        self,
        base_optimization: SequenceOptimization,
        journey_analysis: LeadJourneyPrediction,
        conversion_analysis: ConversionProbabilityAnalysis,
        touchpoint_analysis: TouchpointOptimization,
    ) -> SequenceOptimization:
        """
        Apply Track 3.1 market timing intelligence to enhance sequence optimization.

        Adjusts timing and channels based on:
        - Lead journey stage progression velocity
        - Conversion probability and urgency
        - Optimal touchpoint predictions
        """
        enhanced_optimization = SequenceOptimization(
            day_3=base_optimization.day_3,
            day_7=base_optimization.day_7,
            day_14=base_optimization.day_14,
            day_30=base_optimization.day_30,
            channel_sequence=base_optimization.channel_sequence.copy(),
        )

        # TIMING ENHANCEMENT 1: Urgency-based acceleration
        urgency_score = conversion_analysis.urgency_score
        if urgency_score > 0.8:
            # HIGH URGENCY: Accelerate sequence significantly
            enhanced_optimization.day_3 = max(1, int(base_optimization.day_3 * 0.5))
            enhanced_optimization.day_7 = max(2, int(base_optimization.day_7 * 0.6))
            enhanced_optimization.day_14 = max(5, int(base_optimization.day_14 * 0.7))
            logger.info(f"HIGH URGENCY: Accelerated sequence timing by 30-50%")

        elif urgency_score < 0.3:
            # LOW URGENCY: Extend intervals to avoid over-communication
            enhanced_optimization.day_7 = min(14, int(base_optimization.day_7 * 1.5))
            enhanced_optimization.day_14 = min(30, int(base_optimization.day_14 * 1.3))
            enhanced_optimization.day_30 = min(60, int(base_optimization.day_30 * 1.2))
            logger.info(f"LOW URGENCY: Extended sequence timing to avoid fatigue")

        # TIMING ENHANCEMENT 2: Progression velocity optimization
        if journey_analysis.stage_progression_velocity > 0.7:
            # Fast progressors - maintain momentum
            enhanced_optimization.day_3 = min(enhanced_optimization.day_3, 2)
            logger.info(f"Fast progression detected - maintaining momentum with quick follow-up")

        # CHANNEL ENHANCEMENT: Use ML-predicted optimal channels
        if touchpoint_analysis.channel_preferences:
            # Sort channels by ML-predicted effectiveness
            optimal_channels = sorted(touchpoint_analysis.channel_preferences.items(), key=lambda x: x[1], reverse=True)
            enhanced_optimization.channel_sequence = [ch[0] for ch in optimal_channels[:4]]
            logger.info(f"Updated channel sequence based on ML preferences: {enhanced_optimization.channel_sequence}")

        return enhanced_optimization

    async def _detect_critical_scenarios(
        self,
        journey_analysis: LeadJourneyPrediction,
        conversion_analysis: ConversionProbabilityAnalysis,
        state: LeadFollowUpState,
    ) -> Optional[Dict[str, Any]]:
        """
        Detect critical scenarios requiring immediate intervention or Jorge Bot handoff.

        Returns scenario details if critical action needed, None otherwise.
        """
        # Scenario 1: High value lead cooling down rapidly
        if journey_analysis.conversion_probability > 0.6 and conversion_analysis.drop_off_risk > 0.7:
            return {
                "type": "high_value_cooling",
                "urgency": "critical",
                "recommendation": "immediate_jorge_handoff",
                "reason": f"High conversion probability ({journey_analysis.conversion_probability:.2f}) but high drop-off risk ({conversion_analysis.drop_off_risk:.2f})",
                "suggested_action": "Deploy Jorge Seller Bot for confrontational re-engagement within 2 hours",
            }

        # Scenario 2: Bottleneck detected with high urgency
        if journey_analysis.stage_bottlenecks and conversion_analysis.urgency_score > 0.8:
            return {
                "type": "urgent_bottleneck",
                "urgency": "high",
                "recommendation": "accelerated_sequence",
                "reason": f"Stage bottlenecks detected with high urgency ({conversion_analysis.urgency_score:.2f})",
                "bottlenecks": journey_analysis.stage_bottlenecks,
                "suggested_action": conversion_analysis.optimal_action,
            }

        # Scenario 3: Ready for qualification
        if journey_analysis.conversion_probability > 0.75 and conversion_analysis.stage_conversion_probability > 0.8:
            return {
                "type": "qualification_ready",
                "urgency": "medium",
                "recommendation": "jorge_qualification",
                "reason": f"High conversion indicators suggest readiness for Jorge's qualification process",
                "suggested_action": "Schedule Jorge Bot consultation within 24 hours",
            }

        return None

    # --- Public Interface ---

    async def process_predictive_lead_sequence(
        self, lead_id: str, sequence_day: int, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Process lead through predictive sequence workflow."""
        initial_state = {
            "lead_id": lead_id,
            "lead_name": f"Lead {lead_id}",
            "conversation_history": conversation_history,
            "sequence_day": sequence_day,
            "engagement_status": "responsive",
            "cma_generated": False,
            # Enhanced fields
            "response_pattern": None,
            "personality_type": None,
            "temperature_prediction": None,
            "sequence_optimization": None,
            # Track 3.1 fields
            "journey_analysis": None,
            "conversion_analysis": None,
            "touchpoint_analysis": None,
            "enhanced_optimization": None,
            "critical_scenario": None,
            "track3_applied": False,
        }

        return await self.workflow.ainvoke(initial_state)


# --- Utility Functions ---


def get_predictive_lead_bot(ghl_client=None) -> PredictiveLeadBot:
    """Factory function to get singleton predictive lead bot instance."""
    if not hasattr(get_predictive_lead_bot, "_instance"):
        get_predictive_lead_bot._instance = PredictiveLeadBot(ghl_client)
    return get_predictive_lead_bot._instance


# --- Event Publisher Extensions ---


async def publish_behavioral_analysis_complete(event_publisher, contact_id: str, **kwargs):
    """Publish behavioral analysis completion event."""
    await event_publisher.publish_event(event_type="behavioral_analysis_complete", contact_id=contact_id, data=kwargs)


# Add method to event publisher instance for bot coordination
async def publish_bot_coordination_request(
    event_publisher, source_bot: str, target_bot: str, contact_id: str, handoff_type: str, handoff_data: Dict
):
    """Publish bot coordination/handoff request event."""
    await event_publisher.publish_event(
        event_type="bot_coordination_request",
        contact_id=contact_id,
        data={
            "source_bot": source_bot,
            "target_bot": target_bot,
            "handoff_type": handoff_type,
            "handoff_data": handoff_data,
            "timestamp": datetime.now().isoformat(),
            "coordination_id": str(uuid.uuid4()),
        },
    )
