"""
Jorge Seller Bot - LangGraph Orchestrator (Enhanced with Track 3.1 Predictive Intelligence)
Implements the confrontational 'No-BS' Jorge Salas persona for motivated sellers.

Track 3.1 Enhancement:
- Predictive journey analysis for strategic timing
- Behavioral pattern recognition for optimal approach
- Market context injection for enhanced confrontational effectiveness
- Conversion probability-driven decision making
"""
import asyncio
from typing import Dict, Any, List, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Track 3.1 Predictive Intelligence Integration
from bots.shared.ml_analytics_engine import MLAnalyticsEngine, get_ml_analytics_engine

logger = get_logger(__name__)

class JorgeSellerBot:
    """
    Autonomous seller bot that uses confrontational qualification.
    Designed to expose 'Lookers' and prioritize 'Motivated Sellers'.

    Enhanced with Track 3.1 Predictive Intelligence:
    - Journey progression analysis for strategic timing
    - Behavioral pattern recognition for optimal confrontational approach
    - Market context injection for enhanced effectiveness
    - Conversion probability-driven decision making
    """

    def __init__(self, tenant_id: str = "jorge_seller"):
        self.intent_decoder = LeadIntentDecoder()
        self.claude = ClaudeAssistant()
        self.event_publisher = get_event_publisher()

        # Track 3.1 Predictive Intelligence Engine
        self.ml_analytics = get_ml_analytics_engine(tenant_id)

        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(JorgeSellerState)

        # Define Nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("detect_stall", self.detect_stall)
        workflow.add_node("select_strategy", self.select_strategy)
        workflow.add_node("generate_jorge_response", self.generate_jorge_response)
        workflow.add_node("execute_follow_up", self.execute_follow_up)

        # Define Edges
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "detect_stall")
        workflow.add_edge("detect_stall", "select_strategy")
        
        # Routing based on next_action
        workflow.add_conditional_edges(
            "select_strategy",
            self._route_seller_action,
            {
                "respond": "generate_jorge_response",
                "follow_up": "execute_follow_up",
                "end": END
            }
        )
        
        workflow.add_edge("generate_jorge_response", END)
        workflow.add_edge("execute_follow_up", END)

        return workflow.compile()

    # --- Node Implementations ---

    async def analyze_intent(self, state: JorgeSellerState) -> Dict:
        """Score the lead and identify psychological commitment."""
        # Emit bot status update - starting analysis
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="analyze_intent"
        )

        logger.info(f"Analyzing seller intent for {state['lead_name']}")
        profile = self.intent_decoder.analyze_lead(
            state['lead_id'],
            state['conversation_history']
        )

        # Classify seller temperature based on scores
        seller_temperature = self._classify_temperature(profile)

        # Emit qualification progress
        await self.event_publisher.publish_jorge_qualification_progress(
            contact_id=state["lead_id"],
            current_question=1,  # Starting with Q1
            questions_answered=0,
            seller_temperature=seller_temperature,
            qualification_scores={
                "frs_score": profile.frs.total_score,
                "pcs_score": profile.pcs.total_score
            },
            next_action="detect_stall"
        )

        return {
            "intent_profile": profile,
            "psychological_commitment": profile.pcs.total_score,
            "is_qualified": profile.frs.classification in ["Hot Lead", "Warm Lead"],
            "seller_temperature": seller_temperature,
            "last_action_timestamp": datetime.now()
        }

    async def detect_stall(self, state: JorgeSellerState) -> Dict:
        """Detect if the lead is using standard stalling language."""
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="detect_stall"
        )

        last_msg = state['conversation_history'][-1]['content'].lower() if state['conversation_history'] else ""

        stall_map = {
            "thinking": ["think", "pondering", "consider", "decide"],
            "get_back": ["get back", "later", "next week", "busy"],
            "zestimate": ["zestimate", "zillow", "online value", "estimate says"],
            "agent": ["agent", "realtor", "broker", "with someone"]
        }

        detected_type = None
        for stall_type, keywords in stall_map.items():
            if any(k in last_msg for k in keywords):
                detected_type = stall_type
                break

        # Emit conversation event for stall detection
        if detected_type:
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state['lead_id'],
                stage="stall_detected",
                message=f"Stall type detected: {detected_type}"
            )

        return {
            "stall_detected": detected_type is not None,
            "detected_stall_type": detected_type
        }

    async def select_strategy(self, state: JorgeSellerState) -> Dict:
        """
        Enhanced strategy selection with Track 3.1 Predictive Intelligence.

        Maintains Jorge's confrontational methodology while adding:
        - Journey progression analysis for strategic timing
        - Behavioral pattern recognition for optimal approach
        - Market context injection for enhanced effectiveness
        - Conversion probability-driven decision making
        """
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="select_strategy_enhanced"
        )

        lead_id = state['lead_id']
        pcs = state['psychological_commitment']

        # EXISTING LOGIC: Jorge's proven confrontational foundation
        if state['stall_detected']:
            base_strategy = {"current_tone": "CONFRONTATIONAL", "next_action": "respond"}
        elif pcs < 30:
            # Low commitment = Take-away mode (don't waste time)
            base_strategy = {"current_tone": "TAKE-AWAY", "next_action": "respond"}
        else:
            base_strategy = {"current_tone": "DIRECT", "next_action": "respond"}

        try:
            # TRACK 3.1 ENHANCEMENT: Predictive Intelligence Layer
            logger.info(f"Applying Track 3.1 predictive intelligence for lead {lead_id}")

            # Get comprehensive predictive analysis
            journey_analysis = await self.ml_analytics.predict_lead_journey(lead_id)
            conversion_analysis = await self.ml_analytics.predict_conversion_probability(
                lead_id, state.get('current_journey_stage', 'qualification')
            )
            touchpoint_analysis = await self.ml_analytics.predict_optimal_touchpoints(lead_id)

            # BEHAVIORAL ENHANCEMENT: Adjust strategy based on response patterns
            enhanced_strategy = await self._apply_behavioral_intelligence(
                base_strategy, journey_analysis, conversion_analysis, touchpoint_analysis, state
            )

            # MARKET TIMING ENHANCEMENT: Add urgency and timing context
            final_strategy = await self._apply_market_timing_intelligence(
                enhanced_strategy, journey_analysis, conversion_analysis, state
            )

            # Emit enhanced conversation event with predictive context
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state['lead_id'],
                stage="strategy_selected_enhanced",
                message=f"Jorge tone: {final_strategy['current_tone']} (PCS: {pcs}) [Track 3.1: Conv={journey_analysis.conversion_probability:.2f}, Pattern={touchpoint_analysis.response_pattern}]"
            )

            # Emit Track 3.1 predictive insights event
            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-seller",
                contact_id=state["lead_id"],
                status="enhanced",
                current_step="predictive_analysis_complete",
                additional_data={
                    "conversion_probability": journey_analysis.conversion_probability,
                    "stage_progression_velocity": journey_analysis.stage_progression_velocity,
                    "response_pattern": touchpoint_analysis.response_pattern,
                    "urgency_score": conversion_analysis.urgency_score,
                    "optimal_action": conversion_analysis.optimal_action,
                    "enhancement_applied": True,
                    "processing_time_ms": (
                        journey_analysis.processing_time_ms +
                        conversion_analysis.processing_time_ms +
                        touchpoint_analysis.processing_time_ms
                    )
                }
            )

            logger.info(f"Track 3.1 enhanced strategy for {lead_id}: {final_strategy['current_tone']} "
                       f"(conv_prob={journey_analysis.conversion_probability:.3f}, "
                       f"pattern={touchpoint_analysis.response_pattern})")

            return final_strategy

        except Exception as e:
            # GRACEFUL FALLBACK: Use Jorge's proven logic if Track 3.1 fails
            logger.warning(f"Track 3.1 enhancement failed for lead {lead_id}, using base strategy: {e}")

            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state['lead_id'],
                stage="strategy_selected",
                message=f"Jorge tone: {base_strategy['current_tone']} (PCS: {pcs}) [Fallback mode]"
            )

            return base_strategy

    async def generate_jorge_response(self, state: JorgeSellerState) -> Dict:
        """Generate the actual response content using Jorge's specific persona."""
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="generate_response"
        )

        stall_breakers = {
            "thinking": "What specifically are you thinking about? The timeline, the price, or whether you actually want to sell? Because if it's exploration, you're wasting both our time.",
            "get_back": "I appreciate it, but I need to know: are you *actually* selling, or just exploring? If you're serious, we talk today. If not, let's not pretend.",
            "zestimate": "Zillow's algorithm doesn't know your kitchen was just renovated. It's a guess. I deal in reality. Want to see real comps?",
            "agent": "Cool. Quick question: has your agent actually *toured* those comps? If not, they're just reading a screen. I've been inside them."
        }

        tone_instructions = {
            "confrontational": "Be direct and challenge their stall. Force a 'Yes' or 'No' commitment.",
            "take-away": "Act like you don't need your business. If they aren't serious, disqualify them immediately.",
            "direct": "Professional but zero fluff. Focus on the math and the next steps."
        }

        # Base prompt for Jorge Persona
        prompt = f"""
        You are Jorge Salas, a high-performance real estate investor. 
        Your tone is: DIRECT, NO-BS, CONFRONTATIONAL when necessary.
        You hate wasting time on 'Lookers'. You want 'Motivated Sellers'.

        CURRENT CONTEXT:
        Lead: {state['lead_name']}
        Tone Mode: {state['current_tone']} ({tone_instructions.get(state['current_tone'])})
        Stall Detected: {state['detected_stall_type'] or 'None'}
        FRS Classification: {state['intent_profile'].frs.classification} 
        
        TASK: Generate a response to the lead's last message.
        """
        
        if state['stall_detected'] and state['detected_stall_type'] in stall_breakers:
            prompt += f"\nINCORPORATE THIS STALL-BREAKER: {stall_breakers[state['detected_stall_type']]}"
        
        response = await self.claude.analyze_with_context(prompt)
        content = response.get('content') or response.get('analysis') or "Are we selling this property or just talking about it?"

        # Update qualification progress - increment question count
        current_q = state.get('current_question', 1)
        questions_answered = len([h for h in state.get('conversation_history', []) if h.get('role') == 'user'])

        await self.event_publisher.publish_jorge_qualification_progress(
            contact_id=state["lead_id"],
            current_question=min(current_q + 1, 4),
            questions_answered=min(questions_answered, 4),
            seller_temperature=state.get('seller_temperature', 'cold'),
            qualification_scores={
                "frs_score": state.get('intent_profile', {}).get('frs', {}).get('total_score', 0),
                "pcs_score": state.get('psychological_commitment', 0)
            },
            next_action="await_response"
        )

        # Emit conversation event for response generated
        await self.event_publisher.publish_conversation_update(
            conversation_id=f"jorge_{state['lead_id']}",
            lead_id=state['lead_id'],
            stage="response_generated",
            message=content
        )

        # Mark bot as active (waiting for response)
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="active",
            current_step="awaiting_response"
        )

        return {"response_content": content}

    async def execute_follow_up(self, state: JorgeSellerState) -> Dict:
        """Execute automated follow-up for unresponsive or lukewarm sellers."""
        follow_up_count = state.get('follow_up_count', 0) + 1

        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="execute_follow_up"
        )

        logger.info(f"Executing follow-up for {state['lead_name']} (Attempt {follow_up_count})")

        # Follow-up scripts based on previous stage
        follow_ups = {
            "qualification": "Checking back—did you ever decide on a timeline for {address}?",
            "valuation_defense": "I've updated the comps for your neighborhood. Zillow is still high. Ready for the truth?",
            "listing_prep": "The photographer is in your area Thursday. Should I book him for your place?"
        }

        stage = state.get('current_journey_stage', 'qualification')
        template = follow_ups.get(stage, "Still interested in selling {address} or should I close the file?")
        follow_up_message = template.format(address=state.get('property_address', 'your property'))

        # Emit conversation event for follow-up
        await self.event_publisher.publish_conversation_update(
            conversation_id=f"jorge_{state['lead_id']}",
            lead_id=state['lead_id'],
            stage="follow_up_sent",
            message=f"Follow-up #{follow_up_count}: {follow_up_message[:50]}..."
        )

        # Mark bot as completed for this cycle
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="completed",
            current_step="follow_up_sent"
        )

        # In prod, send via GHL
        return {
            "response_content": follow_up_message,
            "follow_up_count": follow_up_count
        }

    # --- Helper Logic ---

    def _classify_temperature(self, profile) -> str:
        """Classify seller temperature based on intent scores."""
        total_score = profile.pcs.total_score + profile.frs.total_score

        if total_score >= 75:
            return "hot"
        elif total_score >= 50:
            return "warm"
        else:
            return "cold"

    def _route_seller_action(self, state: JorgeSellerState) -> Literal["respond", "follow_up", "end"]:
        """Determine if we should respond immediately or queue a follow-up."""
        if state['next_action'] == "follow_up":
            return "follow_up"
        if state['next_action'] == "end":
            return "end"
        return "respond"

    # ================================
    # TRACK 3.1: PREDICTIVE INTELLIGENCE ENHANCEMENT METHODS
    # ================================

    async def _apply_behavioral_intelligence(self, base_strategy: Dict, journey_analysis,
                                           conversion_analysis, touchpoint_analysis,
                                           state: JorgeSellerState) -> Dict:
        """
        Apply behavioral intelligence to enhance Jorge's confrontational approach.

        Uses Track 3.1 behavioral patterns to optimize strategy effectiveness while
        maintaining Jorge's proven confrontational methodology.
        """
        enhanced_strategy = base_strategy.copy()

        # BEHAVIORAL PATTERN ANALYSIS
        response_pattern = touchpoint_analysis.response_pattern
        conversion_prob = journey_analysis.conversion_probability
        stage_velocity = journey_analysis.stage_progression_velocity

        # ENHANCEMENT 1: Response Pattern Optimization
        if response_pattern == "fast" and conversion_prob > 0.6:
            # Fast responders with high conversion probability = MORE AGGRESSIVE
            if enhanced_strategy["current_tone"] == "DIRECT":
                enhanced_strategy["current_tone"] = "CONFRONTATIONAL"
                enhanced_strategy["enhancement_reason"] = "fast_responder_high_conversion"
            elif enhanced_strategy["current_tone"] == "CONFRONTATIONAL":
                enhanced_strategy["intensity"] = "AGGRESSIVE"
                enhanced_strategy["enhancement_reason"] = "fast_responder_escalation"

        elif response_pattern == "slow" and conversion_prob < 0.3:
            # Slow responders with low conversion = CUT LOSSES FASTER
            if enhanced_strategy["current_tone"] == "DIRECT":
                enhanced_strategy["current_tone"] = "TAKE-AWAY"
                enhanced_strategy["enhancement_reason"] = "slow_responder_low_conversion"
            elif enhanced_strategy["current_tone"] == "CONFRONTATIONAL":
                enhanced_strategy["current_tone"] = "TAKE-AWAY"
                enhanced_strategy["enhancement_reason"] = "unresponsive_cut_losses"

        # ENHANCEMENT 2: Stage Progression Velocity
        if stage_velocity > 0.8:
            # Fast-moving leads = MAINTAIN MOMENTUM
            enhanced_strategy["urgency_boost"] = True
            enhanced_strategy["momentum_factor"] = "high"
        elif stage_velocity < 0.3:
            # Stalled progression = INCREASE PRESSURE
            if enhanced_strategy["current_tone"] != "TAKE-AWAY":
                enhanced_strategy["pressure_increase"] = True
                enhanced_strategy["stall_breaking"] = True

        # ENHANCEMENT 3: Conversion Probability Context
        if conversion_prob > 0.7:
            # High conversion probability = MAINTAIN CURRENT APPROACH
            enhanced_strategy["confidence_level"] = "high"
            enhanced_strategy["approach_validation"] = "maintain_course"
        elif conversion_prob < 0.3 and enhanced_strategy["current_tone"] != "TAKE-AWAY":
            # Low conversion probability = DISQUALIFY FASTER
            enhanced_strategy["disqualification_urgency"] = True

        # Track behavioral intelligence application
        enhanced_strategy["track3_behavioral_applied"] = True
        enhanced_strategy["behavioral_factors"] = {
            "response_pattern": response_pattern,
            "conversion_probability": conversion_prob,
            "stage_progression_velocity": stage_velocity
        }

        logger.info(f"Applied behavioral intelligence for {state['lead_id']}: "
                   f"{base_strategy['current_tone']} → {enhanced_strategy['current_tone']}")

        return enhanced_strategy

    async def _apply_market_timing_intelligence(self, strategy: Dict, journey_analysis,
                                              conversion_analysis, state: JorgeSellerState) -> Dict:
        """
        Apply market timing intelligence to enhance Jorge's strategic effectiveness.

        Incorporates market context and timing urgency to optimize confrontational approach.
        """
        final_strategy = strategy.copy()

        urgency_score = conversion_analysis.urgency_score
        optimal_action = conversion_analysis.optimal_action
        stage_bottlenecks = journey_analysis.stage_bottlenecks

        # MARKET TIMING ENHANCEMENT 1: Urgency-Based Intensity
        if urgency_score > 0.8:
            # HIGH URGENCY = MAXIMUM PRESSURE
            final_strategy["market_urgency"] = "high"

            if final_strategy["current_tone"] == "DIRECT":
                final_strategy["current_tone"] = "CONFRONTATIONAL"
                final_strategy["timing_reason"] = "high_market_urgency"
            elif final_strategy["current_tone"] == "CONFRONTATIONAL":
                final_strategy["intensity"] = "MAXIMUM"
                final_strategy["timing_reason"] = "peak_urgency_escalation"

        elif urgency_score < 0.3:
            # LOW URGENCY = PATIENT DISQUALIFICATION
            if final_strategy["current_tone"] == "CONFRONTATIONAL":
                final_strategy["current_tone"] = "DIRECT"
                final_strategy["timing_reason"] = "low_urgency_de_escalation"

        # MARKET TIMING ENHANCEMENT 2: Optimal Action Integration
        jorge_action_mapping = {
            "schedule_qualification_call": "DIRECT",
            "schedule_appointment": "DIRECT",
            "clarify_requirements": "CONFRONTATIONAL",
            "nurture_relationship": "TAKE-AWAY",  # If nurture needed, they're not ready
            "follow_up_contact": "DIRECT"
        }

        suggested_tone = jorge_action_mapping.get(optimal_action)
        if suggested_tone and suggested_tone != final_strategy["current_tone"]:
            # Only adjust if it increases intensity (Jorge doesn't back down)
            tone_intensity = {"TAKE-AWAY": 3, "CONFRONTATIONAL": 2, "DIRECT": 1}

            current_intensity = tone_intensity.get(final_strategy["current_tone"], 1)
            suggested_intensity = tone_intensity.get(suggested_tone, 1)

            if suggested_intensity >= current_intensity:
                final_strategy["current_tone"] = suggested_tone
                final_strategy["action_alignment"] = True
                final_strategy["optimal_action_applied"] = optimal_action

        # MARKET TIMING ENHANCEMENT 3: Bottleneck-Based Strategy
        if "stalled_in_stage" in stage_bottlenecks or "slow_response_time" in stage_bottlenecks:
            # STALLS = CONFRONTATIONAL BREAKTHROUGH
            if final_strategy["current_tone"] == "DIRECT":
                final_strategy["current_tone"] = "CONFRONTATIONAL"
                final_strategy["bottleneck_reason"] = "stage_stall_detected"

        elif "price_misalignment" in stage_bottlenecks:
            # PRICE ISSUES = IMMEDIATE TAKE-AWAY
            final_strategy["current_tone"] = "TAKE-AWAY"
            final_strategy["bottleneck_reason"] = "price_reality_check_needed"

        # Track market timing intelligence application
        final_strategy["track3_timing_applied"] = True
        final_strategy["timing_factors"] = {
            "urgency_score": urgency_score,
            "optimal_action": optimal_action,
            "stage_bottlenecks": stage_bottlenecks
        }

        # JORGE PHILOSOPHY: Never compromise on confrontational approach
        # If Track 3.1 suggests backing down, Jorge doubles down instead
        if final_strategy.get("suggested_de_escalation"):
            final_strategy["current_tone"] = "CONFRONTATIONAL"
            final_strategy["jorge_override"] = "never_back_down"

        logger.info(f"Applied market timing intelligence for {state['lead_id']}: "
                   f"urgency={urgency_score:.2f}, action={optimal_action}")

        return final_strategy

    async def process_seller_message(self,
                                   lead_id: str,
                                   lead_name: str,
                                   history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process a message through the Jorge Seller Bot workflow."""
        initial_state = {
            "lead_id": lead_id,
            "lead_name": lead_name,
            "conversation_history": history,
            "property_address": None,
            "intent_profile": None,
            "current_tone": "direct",
            "stall_detected": False,
            "detected_stall_type": None,
            "next_action": "respond", # Changed from "analyze"
            "response_content": "",
            "psychological_commitment": 0.0,
            "is_qualified": False,
            "current_journey_stage": "qualification",
            "follow_up_count": 0,
            "last_action_timestamp": None
        }
        
        return await self.workflow.ainvoke(initial_state)
