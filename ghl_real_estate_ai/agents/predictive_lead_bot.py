"""
Predictive Lead Bot - Enhanced Lifecycle Management
ML-powered timing optimization with behavioral pattern recognition.
Extends the base LeadBotWorkflow with Track 1 enhancements.
"""

import asyncio
import json
from typing import Dict, Any, List, Literal, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.workflows import LeadFollowUpState
from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

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
            prev_msg = conversation_history[i-1]

            # Mock timestamp analysis (in production, use actual timestamps)
            if current_msg.get('role') == 'user' and prev_msg.get('role') == 'assistant':
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
        channel_prefs = {
            "SMS": 0.8,
            "Email": 0.3,
            "Voice": 0.6,
            "WhatsApp": 0.2
        }

        # Analyze message length preference
        avg_msg_length = sum(len(m.get('content', '').split()) for m in conversation_history if m.get('role') == 'user')
        avg_msg_length = avg_msg_length / max(1, len([m for m in conversation_history if m.get('role') == 'user']))

        length_pref = "brief" if avg_msg_length < 10 else "detailed"

        pattern = ResponsePattern(
            avg_response_hours=avg_response_hours,
            response_count=len([m for m in conversation_history if m.get('role') == 'user']),
            channel_preferences=channel_prefs,
            engagement_velocity=velocity,
            best_contact_times=[9, 14, 18],  # Mock: 9 AM, 2 PM, 6 PM
            message_length_preference=length_pref
        )

        self._patterns_cache[lead_id] = pattern
        return pattern

    async def predict_optimal_sequence(self, pattern: ResponsePattern) -> SequenceOptimization:
        """Predict optimal sequence timing based on behavioral patterns."""

        # Optimize intervals based on response velocity
        if pattern.engagement_velocity == "fast":
            # Accelerate sequence for fast responders
            optimization = SequenceOptimization(
                day_3=1,    # Contact tomorrow
                day_7=3,    # Contact in 3 days
                day_14=7,   # Contact in 1 week
                day_30=14,  # Contact in 2 weeks
                channel_sequence=["SMS", "Voice", "SMS", "Email"]
            )
        elif pattern.engagement_velocity == "slow":
            # Extend intervals for slow responders
            optimization = SequenceOptimization(
                day_3=5,    # Wait 5 days
                day_7=14,   # Wait 2 weeks
                day_14=21,  # Wait 3 weeks
                day_30=45,  # Wait 6+ weeks
                channel_sequence=["Email", "SMS", "Voice", "SMS"]
            )
        else:
            # Standard intervals for moderate responders
            optimization = SequenceOptimization(
                day_3=3,
                day_7=7,
                day_14=14,
                day_30=30,
                channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )

        # Adjust channel sequence based on preferences
        sorted_channels = sorted(
            pattern.channel_preferences.items(),
            key=lambda x: x[1],
            reverse=True
        )
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
                "keywords": ["analysis", "data", "research", "comparison"]
            },
            "relationship": {
                "style": "personal",
                "tone": "warm",
                "format": "conversational",
                "keywords": ["understand", "help", "partnership", "together"]
            },
            "results": {
                "style": "direct",
                "tone": "urgent",
                "format": "brief",
                "keywords": ["action", "results", "quickly", "efficiently"]
            },
            "security": {
                "style": "cautious",
                "tone": "reassuring",
                "format": "detailed",
                "keywords": ["safe", "secure", "guaranteed", "protected"]
            }
        }

    async def detect_personality(self, conversation_history: List[Dict]) -> str:
        """Detect lead personality type from conversation patterns."""
        all_text = " ".join([m.get("content", "").lower() for m in conversation_history])

        personality_scores = {}
        for personality, profile in self.personality_profiles.items():
            score = sum(1 for keyword in profile["keywords"] if keyword in all_text)
            personality_scores[personality] = score

        # Return highest scoring personality or default to 'relationship'
        return max(personality_scores, key=personality_scores.get) if any(personality_scores.values()) else "relationship"

    async def adapt_message(self, base_message: str, personality_type: str, pattern: ResponsePattern) -> str:
        """Adapt message based on personality type and response patterns."""
        profile = self.personality_profiles.get(personality_type, self.personality_profiles["relationship"])

        # Adjust message length based on preference
        if pattern.message_length_preference == "brief" and profile["format"] != "brief":
            # Shorten message for brief preference
            sentences = base_message.split('. ')
            adapted_message = '. '.join(sentences[:2]) + '.'
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
        current_temp = (current_scores.get('frs_score', 0) + current_scores.get('pcs_score', 0)) / 2

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
                "suggested_action": "Schedule call within 24 hours"
            }

        return {
            "current_temperature": current_temp,
            "trend": trend,
            "confidence": confidence,
            "early_warning": early_warning,
            "prediction_next_interaction": max(0, current_temp + (diff * 1.5))
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

        # Override workflow with enhanced capabilities
        self.workflow = self._build_predictive_graph()

    def _build_predictive_graph(self) -> StateGraph:
        """Build enhanced workflow with predictive analytics."""
        workflow = StateGraph(LeadFollowUpState)

        # Enhanced nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("behavioral_analysis", self.analyze_behavioral_patterns)  # NEW
        workflow.add_node("predict_optimization", self.predict_sequence_optimization)  # NEW
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

        # Enhanced flow
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "behavioral_analysis")
        workflow.add_edge("behavioral_analysis", "predict_optimization")
        workflow.add_edge("predict_optimization", "determine_path")

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
                "nurture": END
            }
        )

        # All actions end
        for node in ["generate_cma", "send_optimized_day_3", "initiate_predictive_day_7",
                    "send_adaptive_day_14", "send_intelligent_day_30", "schedule_showing",
                    "post_showing_survey", "facilitate_offer", "contract_to_close_nurture"]:
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
            current_step="behavioral_analysis"
        )

        # Analyze response patterns
        pattern = await self.analytics_engine.analyze_response_patterns(
            state['lead_id'],
            state['conversation_history']
        )

        # Detect personality type
        personality = await self.personality_adapter.detect_personality(state['conversation_history'])

        # Predict temperature trend
        current_scores = {
            'frs_score': state['intent_profile'].frs.total_score,
            'pcs_score': state['intent_profile'].pcs.total_score
        }
        temperature_prediction = await self.temperature_engine.predict_temperature_trend(
            state['lead_id'],
            current_scores
        )

        # Emit behavioral analysis event
        await self.event_publisher.publish_behavioral_analysis_complete(
            contact_id=state["lead_id"],
            response_velocity=pattern.engagement_velocity,
            personality_type=personality,
            temperature_trend=temperature_prediction['trend'],
            early_warning=temperature_prediction.get('early_warning'),
            channel_preferences=pattern.channel_preferences
        )

        return {
            "response_pattern": pattern,
            "personality_type": personality,
            "temperature_prediction": temperature_prediction
        }

    async def predict_sequence_optimization(self, state: LeadFollowUpState) -> Dict:
        """Predict optimal sequence timing and channels."""
        logger.info(f"Optimizing sequence for lead {state['lead_id']}")

        pattern = state['response_pattern']
        optimization = await self.analytics_engine.predict_optimal_sequence(pattern)

        logger.info(f"Sequence optimization: {optimization}")

        return {"sequence_optimization": optimization}

    # --- Enhanced Follow-up Nodes ---

    async def send_optimized_day_3(self, state: LeadFollowUpState) -> Dict:
        """Day 3 with optimized timing and personalization."""
        optimization = state['sequence_optimization']
        pattern = state['response_pattern']
        personality = state['personality_type']

        # Use optimized timing
        actual_day = optimization.day_3
        preferred_channel = optimization.channel_sequence[0]

        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=actual_day,
            action_type="optimized_outreach",
            success=True,
            channel=preferred_channel,
            personalization_applied=True
        )

        # Base message
        base_msg = f"Hi {state['lead_name']}, checking in about your property search. Any questions about the market?"

        # Adapt message for personality
        adapted_msg = await self.personality_adapter.adapt_message(base_msg, personality, pattern)

        logger.info(f"Optimized Day {actual_day} {preferred_channel} to {state['lead_name']}: {adapted_msg}")

        return {
            "engagement_status": "predictive_nurture",
            "current_step": "day_7_call",
            "optimized_timing_applied": True,
            "personalization_applied": True
        }

    async def initiate_predictive_day_7(self, state: LeadFollowUpState) -> Dict:
        """Day 7 with predictive timing and channel optimization."""
        optimization = state['sequence_optimization']
        temperature_pred = state['temperature_prediction']

        # Check for early warning
        if temperature_pred.get('early_warning'):
            logger.info(f"Early warning triggered for {state['lead_name']}: {temperature_pred['early_warning']['recommendation']}")

        # Use optimized channel and timing
        preferred_channel = optimization.channel_sequence[1] if len(optimization.channel_sequence) > 1 else "Voice"

        logger.info(f"Predictive Day {optimization.day_7} {preferred_channel} call for {state['lead_name']}")

        return {"engagement_status": "predictive_nurture", "current_step": "day_14_email"}

    async def send_adaptive_day_14(self, state: LeadFollowUpState) -> Dict:
        """Day 14 with adaptive messaging and channel selection."""
        optimization = state['sequence_optimization']
        personality = state['personality_type']

        preferred_channel = optimization.channel_sequence[2] if len(optimization.channel_sequence) > 2 else "Email"

        logger.info(f"Adaptive Day {optimization.day_14} {preferred_channel} for {state['lead_name']}")

        return {"engagement_status": "predictive_nurture", "current_step": "day_30_nudge"}

    async def send_intelligent_day_30(self, state: LeadFollowUpState) -> Dict:
        """Day 30 with intelligent re-engagement strategy."""
        optimization = state['sequence_optimization']
        temperature_pred = state['temperature_prediction']

        # Final attempt with predicted optimal approach
        logger.info(f"Intelligent Day {optimization.day_30} final engagement for {state['lead_name']}")

        return {"engagement_status": "intelligent_nurture", "current_step": "nurture"}

    # --- Helper Logic ---

    def _route_predictive_step(self, state: LeadFollowUpState) -> Literal["generate_cma", "day_3", "day_7", "day_14", "day_30", "schedule_showing", "post_showing", "facilitate_offer", "closing_nurture", "qualified", "nurture"]:
        """Enhanced routing with predictive logic."""
        # Check for early warnings that require immediate action
        if state.get('temperature_prediction', {}).get('early_warning'):
            warning = state['temperature_prediction']['early_warning']
            if warning.get('urgency') == 'high':
                return "schedule_showing"  # Immediate escalation

        # Use parent routing logic with enhancements
        return super()._route_next_step(state)

    # --- Public Interface ---

    async def process_predictive_lead_sequence(self,
                                             lead_id: str,
                                             sequence_day: int,
                                             conversation_history: List[Dict]) -> Dict[str, Any]:
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
            "sequence_optimization": None
        }

        return await self.workflow.ainvoke(initial_state)

# --- Utility Functions ---

def get_predictive_lead_bot(ghl_client=None) -> PredictiveLeadBot:
    """Factory function to get singleton predictive lead bot instance."""
    if not hasattr(get_predictive_lead_bot, '_instance'):
        get_predictive_lead_bot._instance = PredictiveLeadBot(ghl_client)
    return get_predictive_lead_bot._instance

# --- Event Publisher Extensions ---

async def publish_behavioral_analysis_complete(event_publisher, contact_id: str, **kwargs):
    """Publish behavioral analysis completion event."""
    await event_publisher.publish_event(
        event_type="behavioral_analysis_complete",
        contact_id=contact_id,
        data=kwargs
    )