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
    current_step: str  # "initial", "day_3_sms", "day_7_call", "day_14_email", "day_30_nudge", "showing_scheduled", "offer_stage", "closing_nurture", "handed_off", "nurture"
    engagement_status: str # "new", "ghosted", "re_engaged", "qualified", "showing_booked", "offer_sent", "under_contract", "closed"
    response_content: Optional[str]

    # Logic Tracking
    last_interaction_time: Optional[datetime]
    stall_breaker_attempted: bool
    cma_generated: bool

    # Full Lifecycle Fields
    showing_date: Optional[datetime]
    showing_feedback: Optional[str]
    offer_amount: Optional[float]
    closing_date: Optional[datetime]

    # Phase 3.3 Intelligence Enhancement Fields
    intelligence_context: Optional[Any]  # BotIntelligenceContext
    intelligence_performance_ms: Optional[float]

    # Enhanced nurture fields for intelligence-driven optimization
    preferred_engagement_timing: Optional[List[int]]  # Hours of day when lead is most responsive
    churn_risk_score: Optional[float]  # 0-1 risk of lead disengagement
    cross_bot_preferences: Optional[Dict[str, Any]]  # Shared preferences from Jorge bots
    sequence_optimization_applied: Optional[bool]  # Whether timing was optimized based on intelligence

class SellerWorkflowState(TypedDict):
    """
    State definition for the Jorge Seller Workflow.
    Tracks the seller's journey from qualification to closing.
    """
    lead_id: str
    lead_name: str
    contact_phone: str
    contact_email: Optional[str]
    property_address: Optional[str]
    
    # Conversation Context
    conversation_history: List[Dict[str, str]]
    seller_data: Dict[str, Any]
    temperature: str  # "hot", "warm", "cold"
    
    # Workflow Status
    current_step: str  # "qualification", "pre_listing", "active_listing", "under_contract", "closing_nurture", "closed"
    engagement_status: str # "new", "qualifying", "qualified", "listing_prep", "active", "under_contract", "closed"
    
    # Logic Tracking
    questions_answered: int
    last_interaction_time: Optional[datetime]
    valuation_provided: bool
    
    # Full Lifecycle Fields
    listing_date: Optional[datetime]
    contract_date: Optional[datetime]
    closing_date: Optional[datetime]
    final_sale_price: Optional[float]
    net_proceeds: Optional[float]
    closing_milestones: List[Dict[str, Any]] # Inspection, Appraisal, etc.
