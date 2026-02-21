"""
Voss Negotiation State Model
Defines the state structure for the LangGraph-powered Voss Negotiation Agent.
"""

from typing import List, Optional, TypedDict


class ConversationTurn(TypedDict, total=False):
    """TypedDict for a single conversation turn."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str]


class NegotiationMetadata(TypedDict, total=False):
    """TypedDict for negotiation metadata."""

    negotiation_start_time: str
    last_response_time: str
    turn_count: int
    strategy_used: Optional[str]
    tactics_applied: List[str]


class VossNegotiationState(TypedDict):
    # Identity
    lead_id: str
    lead_name: str
    property_address: str

    # Conversation history
    conversation_history: List[ConversationTurn]

    # Behavioral analysis (Phase 1)
    drift_score: float  # 0.0 - 1.0
    is_drifting: bool
    drift_recommendation: str

    # Tone & Level (Phase 2)
    voss_level: int  # 1-5 (Warm -> Assertive -> Confrontational -> Direct Challenge -> Accusation Audit)
    tone_intensity: str  # "Warm", "Direct", "Aggressive"

    # Compliance & Safety (Phase 3)
    is_compliant: bool
    compliance_feedback: Optional[str]

    # Output
    generated_response: str
    metadata: NegotiationMetadata
