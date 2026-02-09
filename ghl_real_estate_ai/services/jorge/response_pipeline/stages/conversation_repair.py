"""Conversation repair pipeline stage.

Detects conversational breakdowns (low confidence, repeated questions,
contradictions, stalls) and applies graduated repair strategies to keep
the conversation productive.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from ghl_real_estate_ai.services.jorge.repair_strategies import (
    RepairTrigger,
    RepairType,
    get_repair_strategy,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.base import (
    ResponseProcessorStage,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

# Thresholds
_CONFIDENCE_THRESHOLD = 0.4
_WORD_OVERLAP_THRESHOLD = 0.7
_MAX_RECENT_QUESTIONS = 5
_RECENT_WINDOW = 3  # compare against last N messages for repetition

# Contradiction keywords (user rejecting bot's previous answer)
_CONTRADICTION_PHRASES = frozenset(
    {
        "no that's wrong",
        "that's not right",
        "that's incorrect",
        "you're wrong",
        "wrong",
        "not what i asked",
        "that's not what i said",
        "no",
    }
)


@dataclass
class RepairState:
    """Per-contact repair tracking state."""

    recent_questions: List[str] = field(default_factory=list)
    escalation_level: int = 0
    repair_count: int = 0
    last_bot_response: str = ""


def _word_overlap_ratio(a: str, b: str) -> float:
    """Compute Jaccard-like word overlap ratio between two strings."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _is_contradiction(user_message: str) -> bool:
    """Check if the user message is a contradiction/rejection."""
    normalized = user_message.lower().strip().rstrip(".!?")
    return normalized in _CONTRADICTION_PHRASES


class ConversationRepairProcessor(ResponseProcessorStage):
    """Detects conversational breakdowns and applies repair strategies.

    Tracks per-contact state to detect repeated questions, low-confidence
    responses, contradictions, and stalled conversations.  Applies a
    graduated repair ladder: clarification -> rephrase -> multiple choice
    -> human escalation.
    """

    def __init__(self) -> None:
        self._contact_state: Dict[str, RepairState] = {}

    @property
    def name(self) -> str:
        return "conversation_repair"

    def _get_state(self, contact_id: str) -> RepairState:
        """Get or create per-contact repair state."""
        if contact_id not in self._contact_state:
            self._contact_state[contact_id] = RepairState()
        return self._contact_state[contact_id]

    def _detect_repeated_question(
        self, user_message: str, state: RepairState
    ) -> bool:
        """Check if user_message is similar to a recent question."""
        for prev in state.recent_questions[-_RECENT_WINDOW:]:
            if _word_overlap_ratio(user_message, prev) >= _WORD_OVERLAP_THRESHOLD:
                return True
        return False

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        # Skip if already blocked or short-circuited by earlier stage
        if response.action in (
            ProcessingAction.BLOCK,
            ProcessingAction.SHORT_CIRCUIT,
        ):
            return response

        state = self._get_state(context.contact_id)
        user_msg = context.user_message.strip()
        trigger = None

        # --- Detection logic (order matters: most specific first) ---

        # 1. Repeated question
        if user_msg and self._detect_repeated_question(user_msg, state):
            trigger = RepairTrigger.REPEATED_QUESTION
            logger.info(
                "Repeated question detected for %s", context.contact_id
            )

        # 2. Low confidence
        elif context.metadata.get("bot_confidence", 1.0) < _CONFIDENCE_THRESHOLD:
            trigger = RepairTrigger.LOW_CONFIDENCE
            logger.info(
                "Low confidence (%.2f) for %s",
                context.metadata.get("bot_confidence", 1.0),
                context.contact_id,
            )

        # 3. Contradiction
        elif _is_contradiction(user_msg) and state.last_bot_response:
            trigger = RepairTrigger.CONTRADICTION
            logger.info("Contradiction detected for %s", context.contact_id)

        # 4. No progress (high escalation + many repairs)
        if trigger and state.escalation_level >= 2 and state.repair_count >= 3:
            trigger = RepairTrigger.NO_PROGRESS
            logger.info(
                "No progress detected for %s (escalation=%d, repairs=%d)",
                context.contact_id,
                state.escalation_level,
                state.repair_count,
            )

        # --- Apply repair if triggered ---
        if trigger is not None:
            strategy = get_repair_strategy(trigger, state.escalation_level)

            # Build repair message
            repair_message = strategy.message_template.format(
                topic="your question",
                rephrased_question=response.message,
            )

            # Format multiple-choice options as numbered list
            if (
                strategy.repair_type == RepairType.MULTIPLE_CHOICE
                and strategy.options
            ):
                options_text = "\n".join(
                    f"{i}. {opt}" for i, opt in enumerate(strategy.options, 1)
                )
                repair_message = f"{repair_message}\n{options_text}"

            response.message = repair_message
            response.action = ProcessingAction.MODIFY
            context.metadata["repair_triggered"] = True
            context.metadata["repair_type"] = strategy.repair_type.value
            context.metadata["repair_trigger"] = trigger.value

            # Human escalation side-effect
            if strategy.repair_type == RepairType.HUMAN_ESCALATION:
                response.actions.append(
                    {"type": "add_tag", "tag": "Human-Escalation-Needed"}
                )

            state.escalation_level = min(state.escalation_level + 1, 2)
            state.repair_count += 1

            logger.info(
                "Repair applied for %s: type=%s trigger=%s level=%d",
                context.contact_id,
                strategy.repair_type.value,
                trigger.value,
                state.escalation_level,
            )

        # --- Update state ---
        if user_msg:
            state.recent_questions.append(user_msg)
            if len(state.recent_questions) > _MAX_RECENT_QUESTIONS:
                state.recent_questions = state.recent_questions[
                    -_MAX_RECENT_QUESTIONS:
                ]
        state.last_bot_response = response.message

        return response
