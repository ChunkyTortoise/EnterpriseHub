"""
Conversation memory and adaptive questioning service for Jorge Seller Bot.

Maintains conversation context and patterns across sessions.
"""

import random
from typing import Dict

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState

try:
    from ghl_real_estate_ai.ghl_utils.config import settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    settings = None

logger = get_logger(__name__)


class ConversationMemory:
    """Maintains conversation context and patterns across sessions (Adaptive Feature)"""

    def __init__(self):
        self._memory: Dict[str, Dict] = {}

    async def get_context(self, conversation_id: str) -> Dict:
        """Get conversation context including last scores and patterns"""
        return self._memory.get(
            conversation_id,
            {"last_scores": None, "question_history": [], "response_patterns": {}, "adaptation_count": 0},
        )

    async def update_context(self, conversation_id: str, update: Dict):
        """Update conversation context with new information"""
        if conversation_id not in self._memory:
            self._memory[conversation_id] = {}
        self._memory[conversation_id].update(update)


class AdaptiveQuestionEngine:
    """Manages dynamic question selection and adaptation (Adaptive Feature)"""

    def __init__(self, questions_config=None, simple_mode: bool = True):
        """Initialize adaptive question engine with mode-based question selection.

        Args:
            questions_config: QuestionConfig object from IndustryConfig
            simple_mode: If True, use 4-question flow. If False, use 10-question flow.
        """
        # Determine which question set to use based on mode
        if questions_config:
            if simple_mode and hasattr(questions_config, 'questions_simple') and questions_config.questions_simple:
                # Simple mode: 4 questions from config
                self.jorge_core_questions = [q.get("text", q) if isinstance(q, dict) else q for q in questions_config.questions_simple]
            elif not simple_mode and hasattr(questions_config, 'questions_full') and questions_config.questions_full:
                # Full mode: 10 questions from config
                self.jorge_core_questions = [q.get("text", q) if isinstance(q, dict) else q for q in questions_config.questions_full]
            elif hasattr(questions_config, 'questions') and questions_config.questions:
                # Fallback to default questions
                self.jorge_core_questions = [q.get("text", q) if isinstance(q, dict) else q for q in questions_config.questions]
            else:
                # No config questions found, use hardcoded fallback based on mode
                self.jorge_core_questions = self._get_hardcoded_questions(simple_mode)
        else:
            # No config provided, use hardcoded fallback based on mode
            self.jorge_core_questions = self._get_hardcoded_questions(simple_mode)

        self.simple_mode = simple_mode
        logger.info(f"AdaptiveQuestionEngine initialized: {'simple' if simple_mode else 'full'} mode ({len(self.jorge_core_questions)} questions)")

    def _get_hardcoded_questions(self, simple_mode: bool) -> list[str]:
        """Get hardcoded question set based on mode.

        Args:
            simple_mode: If True, return 4-question set. Otherwise return 10-question set.

        Returns:
            List of question strings.
        """
        if simple_mode:
            return [
                "What's got you considering wanting to sell, where would you move to?",
                "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
                "How would you describe your home, would you say it's move-in ready or would it need some work?",
                "What price would incentivize you to sell?",
            ]
        else:
            return [
                "What's the address of the property you're thinking about selling?",
                "What's got you considering wanting to sell, where would you move to?",
                "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
                "How would you describe your home, would you say it's move-in ready or would it need some work?",
                "What price would incentivize you to sell?",
                "Do you have any existing mortgage or liens on the property?",
                "Are there any repairs or improvements needed before listing?",
                "Have you tried listing this property before?",
                "Are you the primary decision-maker, or would anyone else need to be involved?",
                "What's the best way to reach you - call, text, or email?",
            ]

        # Friendly questions for high-intent leads (config-first, hardcoded fallback)
        if questions_config and hasattr(questions_config, 'accelerators') and questions_config.accelerators:
            self.high_intent_accelerators = questions_config.accelerators
        else:
            self.high_intent_accelerators = [
                "It sounds like you're ready to move forward! I'd love to see your property. Would tomorrow afternoon or this week work better for a visit?",
                "Based on what you've shared, it sounds like we have a great opportunity here. Would you like to schedule a time to discuss your options in detail?",
                "I'm excited to help you with this! What timeline would work best for your situation?",
                "You seem ready to take the next step - that's wonderful! When would be a good time to meet and go over your options?",
                "I can see this is important to you. Let's find a time to sit down and create a plan that works for your situation?",
            ]

        self.supportive_clarifiers = {
            "zestimate": [
                "Online estimates are a great starting point! I'd love to show you what similar homes in your area have actually sold for recently.",
                "Those online tools don't see the unique features of your home. Would you like a more personalized market analysis?",
            ],
            "thinking": [
                "I completely understand you need time to consider this. What specific questions can I help answer for you?",
                "Taking time to think it through is smart! What aspects would be most helpful for us to discuss?",
            ],
            "agent": [
                "That's great that you're working with someone! I'm happy to share some additional market insights that might be helpful.",
                "Wonderful! If you'd like, I can provide some complementary information that might be useful for your decision.",
            ],
        }

    async def select_next_question(self, state: JorgeSellerState, context: Dict) -> str:
        """Select the optimal next question based on real-time analysis"""
        current_scores = state.get("intent_profile")

        # Fast-track high-intent leads (PCS > 70)
        if current_scores and hasattr(current_scores, 'pcs') and current_scores.pcs.total_score > 70:
            return await self._fast_track_to_calendar(state)

        # Handle specific concerns with supportive questions
        if state.get("detected_stall_type"):
            return await self._select_supportive_clarifier(state["detected_stall_type"])

        # Adaptive questioning based on score progression
        if context.get("adaptation_count", 0) > 0:
            return await self._select_adaptive_question(state, context)

        # Default to core questions for first-time qualification
        return await self._select_standard_question(state)

    async def _fast_track_to_calendar(self, state: JorgeSellerState) -> str:
        """Direct high-intent leads to calendar scheduling"""
        base_msg = random.choice(self.high_intent_accelerators)

        if SETTINGS_AVAILABLE and settings and hasattr(settings, 'ghl_calendar_id') and settings.ghl_calendar_id:
            calendar_link = f"https://link.ghl.com/widget/booking/{settings.ghl_calendar_id}"
            return f"{base_msg} You can pick a time that works best for you right here: {calendar_link}"

        return base_msg

    async def _select_supportive_clarifier(self, clarifier_type: str) -> str:
        """Select supportive clarifier based on conversation context"""
        questions = self.supportive_clarifiers.get(clarifier_type, self.supportive_clarifiers["thinking"])
        return random.choice(questions)

    async def _select_adaptive_question(self, state: JorgeSellerState, context: Dict) -> str:
        """Select question based on conversation history and patterns"""
        # Analyze what's missing from qualification
        scores = state.get("intent_profile")

        if scores and hasattr(scores, 'frs'):
            if scores.frs.timeline.score < 50:
                return "I'd love to better understand your timeline. What would work best for your situation?"
            elif scores.frs.price.score < 50:
                return "What price range would make this feel like a great decision for you?"
            elif scores.frs.condition.score < 50:
                return "Would you prefer to sell as-is, or are you thinking about making some updates first?"

        # Default fallback
        return "What's the most important outcome for you in this process?"

    async def _select_standard_question(self, state: JorgeSellerState) -> str:
        """Select from core Jorge questions"""
        current_q = state.get("current_question", 1)
        if current_q <= len(self.jorge_core_questions):
            return self.jorge_core_questions[current_q - 1]
        return "How can I best help you with your property goals?"
