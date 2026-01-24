"""
Jorge Seller Bot - LangGraph Orchestrator
Implements the confrontational 'No-BS' Jorge Salas persona for motivated sellers.
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

logger = get_logger(__name__)

class JorgeSellerBot:
    """
    Autonomous seller bot that uses confrontational qualification.
    Designed to expose 'Lookers' and prioritize 'Motivated Sellers'.
    """

    def __init__(self):
        self.intent_decoder = LeadIntentDecoder()
        self.claude = ClaudeAssistant()
        self.event_publisher = get_event_publisher()
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
        """Choose between 'Direct', 'Confrontational', or 'Take-Away' mode."""
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="select_strategy"
        )

        pcs = state['psychological_commitment']

        if state['stall_detected']:
            strategy = {"current_tone": "CONFRONTATIONAL", "next_action": "respond"}
        elif pcs < 30:
            # Low commitment = Take-away mode (don't waste time)
            strategy = {"current_tone": "TAKE-AWAY", "next_action": "respond"}
        else:
            strategy = {"current_tone": "DIRECT", "next_action": "respond"}

        # Emit conversation event for strategy selection
        await self.event_publisher.publish_conversation_update(
            conversation_id=f"jorge_{state['lead_id']}",
            lead_id=state['lead_id'],
            stage="strategy_selected",
            message=f"Jorge tone: {strategy['current_tone']} (PCS: {pcs})"
        )

        return strategy

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
