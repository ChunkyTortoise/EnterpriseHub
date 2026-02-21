"""Conversation repair strategy templates.

Provides graduated repair responses when bot confidence is low,
user repeats questions, or contradictions are detected.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RepairType(str, Enum):
    CLARIFICATION = "clarification"
    REPHRASE = "rephrase"
    MULTIPLE_CHOICE = "multiple_choice"
    HUMAN_ESCALATION = "human_escalation"


class RepairTrigger(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    REPEATED_QUESTION = "repeated_question"
    CONTRADICTION = "contradiction"
    NO_PROGRESS = "no_progress"


@dataclass
class RepairStrategy:
    """A repair action to take."""

    repair_type: RepairType
    trigger: RepairTrigger
    message_template: str
    escalation_level: int  # 0=mild, 1=moderate, 2=escalate
    options: Optional[List[str]] = field(default=None)  # For multiple_choice


# Graduated repair ladder
REPAIR_LADDER: List[RepairStrategy] = [
    RepairStrategy(
        repair_type=RepairType.CLARIFICATION,
        trigger=RepairTrigger.LOW_CONFIDENCE,
        message_template=("I want to make sure I understand correctly. Could you tell me more about {topic}?"),
        escalation_level=0,
    ),
    RepairStrategy(
        repair_type=RepairType.REPHRASE,
        trigger=RepairTrigger.REPEATED_QUESTION,
        message_template="Let me put that differently. {rephrased_question}",
        escalation_level=0,
    ),
    RepairStrategy(
        repair_type=RepairType.CLARIFICATION,
        trigger=RepairTrigger.CONTRADICTION,
        message_template=("I may have misunderstood. Could you clarify what you meant about {topic}?"),
        escalation_level=0,
    ),
    RepairStrategy(
        repair_type=RepairType.MULTIPLE_CHOICE,
        trigger=RepairTrigger.NO_PROGRESS,
        message_template="To help you better, which of these best describes your situation?",
        escalation_level=1,
        options=[
            "I'm looking to buy",
            "I'm thinking of selling",
            "Just exploring options",
            "Something else",
        ],
    ),
    RepairStrategy(
        repair_type=RepairType.HUMAN_ESCALATION,
        trigger=RepairTrigger.NO_PROGRESS,
        message_template=(
            "I'd love to connect you with a team member who can help. Would you like me to arrange that?"
        ),
        escalation_level=2,
    ),
]


def get_repair_strategy(trigger: RepairTrigger, escalation_level: int = 0) -> RepairStrategy:
    """Get the appropriate repair strategy for a trigger and escalation level.

    Finds the first strategy matching the trigger whose escalation_level
    is >= the requested level.  Falls back to human escalation.
    """
    candidates = [s for s in REPAIR_LADDER if s.trigger == trigger and s.escalation_level >= escalation_level]
    if not candidates:
        # Fallback: escalate to human
        candidates = [s for s in REPAIR_LADDER if s.repair_type == RepairType.HUMAN_ESCALATION]
    return candidates[0] if candidates else REPAIR_LADDER[-1]
