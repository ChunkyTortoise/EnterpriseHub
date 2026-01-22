from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile

class JorgeSellerState(TypedDict):
    """
    State for Jorge's Motivated Seller Bot.
    Focuses on confrontational qualification and stall-breaking.
    """
    lead_id: str
    lead_name: str
    property_address: Optional[str]
    
    # Context
    conversation_history: List[Dict[str, str]]
    intent_profile: Optional[LeadIntentProfile]
    
    # Bot Logic
    current_tone: str # "direct", "confrontational", "take-away"
    stall_detected: bool
    detected_stall_type: Optional[str] # "thinking", "get_back", "zestimate", "agent"
    
    # Decisions
    next_action: str
    response_content: str
    
    # Metrics
    psychological_commitment: float
    is_qualified: bool
    
    # Journey Tracking
    current_journey_stage: str # "qualification", "valuation_defense", "listing_prep", "active_listing", "under_contract", "closed"
    follow_up_count: int
    last_action_timestamp: Optional[datetime]
