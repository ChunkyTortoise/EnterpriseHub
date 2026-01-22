from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile

class LeadFollowUpState(TypedDict):
    """
    State definition for the LangGraph 3-7-30 Day Follow-Up Workflow.
    Tracks the lead's journey through the re-engagement funnel.
    """
    lead_id: str
    lead_name: str
    contact_phone: str
    contact_email: Optional[str]
    property_address: Optional[str]
    
    # Conversation Context
    conversation_history: List[Dict[str, str]]
    intent_profile: Optional[LeadIntentProfile]
    
    # Workflow Status
    current_step: str  # "initial", "day_3_sms", "day_7_call", "day_14_email", "day_30_nudge", "handed_off", "nurture"
    engagement_status: str # "new", "ghosted", "re_engaged", "qualified"
    
    # Logic Tracking
    last_interaction_time: Optional[datetime]
    stall_breaker_attempted: bool
    cma_generated: bool
