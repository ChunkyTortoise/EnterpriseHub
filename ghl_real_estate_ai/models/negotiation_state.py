"""
Voss Negotiation State Model
Defines the state structure for the LangGraph-powered Voss Negotiation Agent.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict


class VossNegotiationState(TypedDict):
    # Identity
    lead_id: str
    lead_name: str
    property_address: str

    # Conversation history
    conversation_history: List[Dict[str, str]]

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
    metadata: Dict[str, Any]
