"""
Constants for the Lead Bot module.
"""
from typing import Dict, List

# Workflow constants
MAX_CONVERSATION_HISTORY = 50
SMS_MAX_LENGTH = 320  # 2-segment SMS, matches pipeline SMSTruncationProcessor and DEPLOYMENT_CHECKLIST

# Cache configuration
CACHE_MAX_ENTRIES = 1000
CACHE_TTL_SECONDS = 3600  # 60 minutes

# Default channel preferences
DEFAULT_CHANNEL_PREFS: Dict[str, float] = {"SMS": 0.5, "Email": 0.5, "Voice": 0.5, "WhatsApp": 0.3}

# Default best contact times (9 AM, 2 PM, 6 PM)
DEFAULT_BEST_CONTACT_TIMES: List[int] = [9, 14, 18]

# Milestone messages for escrow nurture
MILESTONE_MESSAGES = {
    "contract_signed": "Congrats {lead_name} on getting under contract! The next step is scheduling the home inspection. I'll help coordinate everything.",
    "inspection": "Great news {lead_name}! The inspection is the next major milestone. I'll be there to make sure everything is handled properly.",
    "appraisal": "{lead_name}, the appraisal is coming up. This is when the lender confirms the home's value. I'll keep you posted on the results.",
    "loan_approval": "Exciting progress {lead_name}! We're waiting on final loan approval. Once we get the clear to close, we're almost there!",
    "final_walkthrough": "{lead_name}, time for the final walkthrough! This is your chance to verify everything is in order before closing.",
    "closing": "The big day is here {lead_name}! Closing day - you're about to get the keys to your new home!",
}

# Stall breaker objection type mapping
STALL_BREAKER_MAPPING = {
    "thinking_about_it": ["thinking", "think about it"],
    "get_back_to_you": ["get back", "call me back", "follow up"],
    "zestimate_reference": ["zestimate", "zillow"],
    "has_realtor": ["agent", "realtor"],
}

# Buying/selling signals for lead classification
BUYING_SIGNALS = [
    "pre-approved",
    "preapproved",
    "ready to buy",
    "want to make an offer",
    "schedule a showing",
    "see the house",
    "budget is",
    "looking to buy",
    "sell my house",
    "list my home",
    "what's my home worth",
]

# Price-related keywords for CMA detection
PRICE_KEYWORDS = ["price", "value", "worth", "zestimate", "comps", "market analysis"]

# Milestone detection keywords
MILESTONE_KEYWORDS = {
    "closing": ["closing", "close of escrow", "coe", "keys", "final signing"],
    "final_walkthrough": ["walkthrough", "walk-through", "final walk"],
    "loan_approval": ["loan approved", "clear to close", "ctc", "underwriting"],
    "appraisal": ["appraisal", "appraiser", "appraisal value"],
    "inspection": ["inspection", "inspector", "home inspection"],
    "contract_signed": ["contract", "under contract", "accepted offer"],
}

# Personality profiles for adaptation
PERSONALITY_PROFILES = {
    "analytical": {
        "style": "data-driven",
        "tone": "professional",
        "format": "bullet points",
        "keywords": ["analysis", "data", "research", "comparison"],
        "prefix": "Based on market data: ",
    },
    "relationship": {
        "style": "personal",
        "tone": "warm",
        "format": "conversational",
        "keywords": ["understand", "help", "partnership", "together"],
        "prefix": "I wanted to personally reach out: ",
    },
    "results": {
        "style": "direct",
        "tone": "urgent",
        "format": "brief",
        "keywords": ["action", "results", "quickly", "efficiently"],
        "prefix": "Quick update: ",
    },
    "security": {
        "style": "cautious",
        "tone": "reassuring",
        "format": "detailed",
        "keywords": ["safe", "secure", "guaranteed", "protected"],
        "prefix": "To ensure we're on the right track: ",
    },
}