"""
Adaptive Jorge Seller Bot - Enhanced Intelligence
Real-time question adaptation with calendar integration and predictive questioning.
Extends the base JorgeSellerBot with Track 1 enhancements.
"""

import asyncio
from typing import Dict, Any, List, Literal, Optional
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class ConversationMemory:
    """Maintains conversation context and patterns across sessions."""

    def __init__(self):
        self._memory: Dict[str, Dict] = {}

    async def get_context(self, conversation_id: str) -> Dict:
        """Get conversation context including last scores and patterns."""
        return self._memory.get(conversation_id, {
            "last_scores": None,
            "question_history": [],
            "response_patterns": {},
            "adaptation_count": 0
        })

    async def update_context(self, conversation_id: str, update: Dict):
        """Update conversation context with new information."""
        if conversation_id not in self._memory:
            self._memory[conversation_id] = {}
        self._memory[conversation_id].update(update)

class AdaptiveQuestionEngine:
    """Manages dynamic question selection and adaptation."""

    def __init__(self):
        # Core Jorge questions (unchanged foundation)
        self.jorge_core_questions = [
            "What's your timeline for selling?",
            "What's driving you to sell the property?",
            "What's your bottom-line number?",
            "Are you flexible on the closing date?"
        ]

        # Adaptive questions for different scenarios
        self.high_intent_accelerators = [
            "You sound motivated. When can we tour the property? I have slots tomorrow afternoon.",
            "Based on your situation, we should move fast. Can we schedule a walkthrough this week?",
            "I can make this happen quickly. What's your preferred closing timeline?"
        ]

        self.stall_breakers = {
            "zestimate": [
                "Zillow doesn't know about your kitchen renovation. Want to see what homes like yours ACTUALLY sold for?",
                "I've been inside those comps Zillow references. Want the real story?"
            ],
            "thinking": [
                "What specifically are you thinking about? Timeline, price, or if you actually want to sell?",
                "Thinking is expensive when the market's moving. What's the real concern?"
            ],
            "agent": [
                "Has your agent toured those comps personally, or just read them online?",
                "Cool. Quick question: when did they last sell a property in your neighborhood?"
            ]
        }

    async def select_next_question(self, state: JorgeSellerState, context: Dict) -> str:
        """Select the optimal next question based on real-time analysis."""
        current_scores = state['intent_profile']

        # Fast-track high-intent leads (PCS > 70)
        if current_scores.pcs.total_score > 70:
            return await self._fast_track_to_calendar(state)

        # Handle specific objections with targeted questions
        if state.get('detected_stall_type'):
            return await self._select_stall_breaker(state['detected_stall_type'])

        # Adaptive questioning based on score progression
        if context.get('adaptation_count', 0) > 0:
            return await self._select_adaptive_question(state, context)

        # Default to core questions for first-time qualification
        return await self._select_standard_question(state)

    async def _fast_track_to_calendar(self, state: JorgeSellerState) -> str:
        """Direct high-intent leads to calendar scheduling."""
        import random
        return random.choice(self.high_intent_accelerators)

    async def _select_stall_breaker(self, stall_type: str) -> str:
        """Select targeted stall-breaker based on objection type."""
        import random
        questions = self.stall_breakers.get(stall_type, self.stall_breakers['thinking'])
        return random.choice(questions)

    async def _select_adaptive_question(self, state: JorgeSellerState, context: Dict) -> str:
        """Select question based on conversation history and patterns."""
        # Analyze what's missing from qualification
        scores = state['intent_profile']

        if scores.frs.timeline.score < 50:
            return "Let's nail down timing - when do you NEED this property sold?"
        elif scores.frs.price.score < 50:
            return "What's your number? The price you'd be happy to walk away with?"
        elif scores.frs.condition.score < 50:
            return "Are you looking to sell as-is, or planning to fix things up?"

        # Default fallback
        return "What's the most important factor in getting this sold for you?"

    async def _select_standard_question(self, state: JorgeSellerState) -> str:
        """Select from core Jorge questions."""
        current_q = state.get('current_question', 1)
        if current_q <= len(self.jorge_core_questions):
            return self.jorge_core_questions[current_q - 1]
        return "Are we selling this property or just talking about it?"

class AdaptiveJorgeBot(JorgeSellerBot):
    """
    Enhanced Jorge Bot with real-time adaptation and predictive questioning.
    Extends base functionality with intelligent question selection.
    """

    def __init__(self):
        super().__init__()
        self.conversation_memory = ConversationMemory()
        self.question_engine = AdaptiveQuestionEngine()

        # Override workflow to add new adaptive node
        self.workflow = self._build_adaptive_graph()

    def _build_adaptive_graph(self) -> StateGraph:
        """Build enhanced workflow with adaptive question selection."""
        workflow = StateGraph(JorgeSellerState)

        # Enhanced Nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("detect_stall", self.detect_stall)
        workflow.add_node("adaptive_strategy", self.adaptive_strategy_selection)  # NEW
        workflow.add_node("generate_adaptive_response", self.generate_adaptive_response)  # ENHANCED
        workflow.add_node("execute_follow_up", self.execute_follow_up)
        workflow.add_node("update_memory", self.update_conversation_memory)  # NEW

        # Enhanced Flow
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "detect_stall")
        workflow.add_edge("detect_stall", "adaptive_strategy")

        # Conditional routing with new logic
        workflow.add_conditional_edges(
            "adaptive_strategy",
            self._route_adaptive_action,
            {
                "respond": "generate_adaptive_response",
                "follow_up": "execute_follow_up",
                "fast_track": "generate_adaptive_response",  # NEW path
                "end": "update_memory"
            }
        )

        workflow.add_edge("generate_adaptive_response", "update_memory")
        workflow.add_edge("execute_follow_up", "update_memory")
        workflow.add_edge("update_memory", END)

        return workflow.compile()

    # --- New/Enhanced Node Implementations ---

    async def adaptive_strategy_selection(self, state: JorgeSellerState) -> Dict:
        """Enhanced strategy selection with adaptive questioning."""
        await self.event_publisher.publish_bot_status_update(
            bot_type="adaptive-jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="adaptive_strategy"
        )

        pcs = state['psychological_commitment']
        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)

        # Enhanced strategy logic
        if pcs > 70:  # High commitment - fast track
            strategy = {
                "current_tone": "DIRECT",
                "next_action": "fast_track",
                "adaptive_mode": "calendar_focused"
            }
        elif state['stall_detected']:
            strategy = {
                "current_tone": "CONFRONTATIONAL",
                "next_action": "respond",
                "adaptive_mode": "objection_handling"
            }
        elif context.get('adaptation_count', 0) > 2:  # Multiple adaptations
            strategy = {
                "current_tone": "TAKE-AWAY",
                "next_action": "respond",
                "adaptive_mode": "qualification_focused"
            }
        else:
            strategy = {
                "current_tone": "DIRECT",
                "next_action": "respond",
                "adaptive_mode": "standard_qualification"
            }

        # Emit enhanced conversation event
        await self.event_publisher.publish_conversation_update(
            conversation_id=conversation_id,
            lead_id=state['lead_id'],
            stage="adaptive_strategy_selected",
            message=f"Adaptive mode: {strategy['adaptive_mode']} (PCS: {pcs}, Adaptations: {context.get('adaptation_count', 0)})"
        )

        return strategy

    async def generate_adaptive_response(self, state: JorgeSellerState) -> Dict:
        """Generate response using adaptive question selection."""
        await self.event_publisher.publish_bot_status_update(
            bot_type="adaptive-jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="generate_adaptive_response"
        )

        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)

        # Select optimal question using adaptive engine
        next_question = await self.question_engine.select_next_question(state, context)

        # Enhanced prompt with adaptive context
        prompt = f"""
        You are Jorge Salas, confrontational real estate investor.

        CURRENT CONTEXT:
        Lead: {state['lead_name']}
        Adaptive Mode: {state.get('adaptive_mode', 'standard')}
        Tone: {state['current_tone']}
        PCS Score: {state['psychological_commitment']}
        FRS Classification: {state['intent_profile'].frs.classification}
        Previous Adaptations: {context.get('adaptation_count', 0)}

        RECOMMENDED QUESTION: {next_question}

        TASK: Deliver the question in Jorge's direct, no-BS style.
        If this is a fast-track scenario, be urgent and action-oriented.
        If handling objections, be confrontational but professional.
        """

        response = await self.claude.analyze_with_context(prompt)
        content = response.get('content', next_question)

        # Enhanced qualification progress tracking
        current_q = state.get('current_question', 1)
        questions_answered = len([h for h in state.get('conversation_history', []) if h.get('role') == 'user'])

        await self.event_publisher.publish_jorge_qualification_progress(
            contact_id=state["lead_id"],
            current_question=min(current_q + 1, 4),
            questions_answered=min(questions_answered, 4),
            seller_temperature=state.get('seller_temperature', 'cold'),
            qualification_scores={
                "frs_score": state["intent_profile"].frs.total_score if state.get("intent_profile") else 0,
                "pcs_score": state.get('psychological_commitment', 0)
            },
            next_action="await_adaptive_response",
            adaptive_mode=state.get('adaptive_mode', 'standard'),
            adaptation_count=context.get('adaptation_count', 0)
        )

        return {
            "response_content": content,
            "adaptive_question_used": next_question,
            "adaptation_applied": True
        }

    async def update_conversation_memory(self, state: JorgeSellerState) -> Dict:
        """Update conversation memory with new interaction patterns."""
        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)

        # Update context with new information
        update = {
            "last_scores": {
                "frs": state['intent_profile'].frs.total_score,
                "pcs": state['psychological_commitment']
            },
            "last_interaction_time": datetime.now(),
            "adaptation_count": context.get('adaptation_count', 0) + 1,
            "response_patterns": {
                "adaptive_mode": state.get('adaptive_mode'),
                "question_used": state.get('adaptive_question_used')
            }
        }

        await self.conversation_memory.update_context(conversation_id, update)

        logger.info(f"Updated conversation memory for {state['lead_name']} - Adaptation #{update['adaptation_count']}")

        return {"memory_updated": True}

    # --- Helper Logic ---

    def _route_adaptive_action(self, state: JorgeSellerState) -> Literal["respond", "follow_up", "fast_track", "end"]:
        """Enhanced routing with fast-track capability."""
        if state.get('adaptive_mode') == 'calendar_focused':
            return "fast_track"

        if state['next_action'] == "follow_up":
            return "follow_up"
        if state['next_action'] == "end":
            return "end"

        return "respond"

    # --- Public Interface ---

    async def process_adaptive_seller_message(self,
                                            lead_id: str,
                                            lead_name: str,
                                            history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process message through adaptive Jorge workflow."""
        initial_state = {
            "lead_id": lead_id,
            "lead_name": lead_name,
            "conversation_history": history,
            "property_address": None,
            "intent_profile": None,
            "current_tone": "direct",
            "stall_detected": False,
            "detected_stall_type": None,
            "next_action": "respond",
            "response_content": "",
            "psychological_commitment": 0.0,
            "is_qualified": False,
            "current_journey_stage": "qualification",
            "follow_up_count": 0,
            "last_action_timestamp": None,

            # New adaptive fields
            "adaptive_mode": "standard_qualification",
            "adaptive_question_used": None,
            "adaptation_applied": False,
            "memory_updated": False
        }

        return await self.workflow.ainvoke(initial_state)

# --- Utility Functions ---

def get_adaptive_jorge_bot() -> AdaptiveJorgeBot:
    """Factory function to get singleton adaptive Jorge bot instance."""
    if not hasattr(get_adaptive_jorge_bot, '_instance'):
        get_adaptive_jorge_bot._instance = AdaptiveJorgeBot()
    return get_adaptive_jorge_bot._instance