"""
Jorge's Friendly Customer Service Bot Configuration - Rancho Cucamonga Edition
============================================================================

Updated configuration for Jorge's friendly, helpful real estate bots focused on
Rancho Cucamonga, California market. This replaces the confrontational Rancho Cucamonga
approach with warm, consultative customer service that builds relationships.

Key Changes:
- Personality: Confrontational → Friendly & Helpful
- Market: Rancho Cucamonga CA → Rancho Cucamonga CA
- Approach: Aggressive → Consultative relationship building
- Compliance: DRE → California DRE regulations

Author: Claude Code Assistant
Updated: 2026-01-25 for Friendly CA Approach
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import os


@dataclass
class JorgeFriendlyConfig:
    """Central configuration for Jorge's friendly customer service bots"""

    # ========== ACTIVATION/DEACTIVATION TAGS ==========
    ACTIVATION_TAGS = ["Needs Qualifying", "New Lead", "Interested"]
    DEACTIVATION_TAGS = ["AI-Off", "Qualified", "Stop-Bot", "DNC", "Unsubscribed"]

    # ========== FRIENDLY TEMPERATURE TAGS ==========
    HOT_SELLER_TAG = "Ready-to-Move"
    WARM_SELLER_TAG = "Interested-Seller"
    COLD_SELLER_TAG = "Exploring-Options"

    # ========== FRIENDLY CLASSIFICATION THRESHOLDS ==========
    # Jorge's friendly requirements - less aggressive, more supportive
    HOT_SELLER_THRESHOLD = 0.85  # Slightly lower to be more inclusive (3.4/4 = 85%)
    WARM_SELLER_THRESHOLD = 0.65  # More generous warm classification (2.6/4 = 65%)
    COLD_SELLER_THRESHOLD = 0.0   # Everyone gets helpful service

    # Response quality thresholds - more forgiving for relationship building
    HOT_SELLER_MIN_RESPONSE_QUALITY = 0.6   # Lower barrier for hot classification
    WARM_SELLER_MIN_RESPONSE_QUALITY = 0.4  # More inclusive warm classification
    TIMELINE_URGENCY_WEIGHT = 0.25          # Reduced timeline pressure (25% vs 35%)

    # ========== FRIENDLY TEMPERATURE CLASSIFICATION ==========
    # Ready-to-move criteria (friendly approach)
    HOT_QUESTIONS_REQUIRED = 3      # More flexible (3/4 vs 4/4)
    HOT_QUALITY_THRESHOLD = 0.6     # Lower quality bar for inclusivity
    HOT_TIMELINE_FLEXIBLE = True    # Accept flexible timelines

    # Interested criteria
    WARM_QUESTIONS_REQUIRED = 2     # Only need 2 answers to show interest
    WARM_QUALITY_THRESHOLD = 0.4    # Very inclusive approach

    # ========== RANCHO CUCAMONGA MARKET SETTINGS ==========
    # Local Inland Empire market specifics
    PRIMARY_MARKET = "Rancho Cucamonga"
    SECONDARY_MARKETS = ["Upland", "Ontario", "Claremont", "Fontana", "Chino", "Etiwanda"]
    MARKET_REGION = "Inland Empire"
    STATE_COMPLIANCE = "California DRE"

    # Price ranges for Rancho Cucamonga (2026 market)
    ENTRY_LEVEL_MIN = 700000      # $700k entry level
    MID_MARKET_MIN = 800000       # $800k-$1.2M mid market
    LUXURY_MIN = 1200000          # $1.2M+ luxury market
    AVERAGE_PRICE = 750000        # Market average around $750k

    # ========== FOLLOW-UP SETTINGS - RELATIONSHIP BUILDING ==========
    # Nurture-focused follow-up (building long-term relationships)
    ACTIVE_FOLLOWUP_DAYS = 45              # Extended to 45 days (vs 30)
    ACTIVE_FOLLOWUP_INTERVAL_MIN = 3       # Gentler 3-4 day intervals
    ACTIVE_FOLLOWUP_INTERVAL_MAX = 4

    # Relationship building schedule (every 3-4 days, less aggressive)
    ACTIVE_FOLLOWUP_SCHEDULE = [3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43]  # Days 1-45

    # Long-term relationship nurture (vs aggressive pursuit)
    LONGTERM_FOLLOWUP_INTERVAL = 21        # Every 3 weeks (vs 14 days)
    MAX_FOLLOWUP_ATTEMPTS = 8              # Fewer attempts, more respectful

    # ========== GHL INTEGRATION - CALIFORNIA WORKFLOWS ==========
    # Updated workflow IDs for Rancho Cucamonga operations
    HOT_SELLER_WORKFLOW_ID = "friendly_hot_seller_ca"
    WARM_SELLER_WORKFLOW_ID = "friendly_warm_seller_ca"
    AGENT_NOTIFICATION_WORKFLOW = "ca_agent_notification"

    # Custom field mapping for California DRE compliance
    CUSTOM_FIELDS = {
        "seller_temperature": "ca_seller_temp_field",
        "seller_motivation": "ca_motivation_field",
        "relocation_destination": "ca_relocation_field",
        "timeline_preferences": "ca_timeline_field",  # Changed from urgency
        "property_condition": "ca_condition_field",
        "price_range_interest": "ca_price_field",     # Softened language
        "questions_answered": "ca_progress_field",
        "relationship_score": "ca_relationship_field", # New friendly metric
        "preferred_contact_method": "ca_contact_pref",
        "family_situation": "ca_family_field",
        "school_district_importance": "ca_schools_field",
        "commute_considerations": "ca_commute_field"
    }

    # ========== FRIENDLY MESSAGE SETTINGS ==========
    # Jorge's warm, professional customer service approach
    MAX_SMS_LENGTH = 160
    FRIENDLY_APPROACH = True
    USE_WARM_LANGUAGE = True
    USE_CONSULTATIVE_TONE = True
    RELATIONSHIP_FOCUSED = True
    NO_PRESSURE_TACTICS = True
    FAMILY_FRIENDLY = True

    # Message response targets - professional service
    RESPONSE_TIME_TARGET_SECONDS = 3      # Slightly more relaxed
    MESSAGE_DELIVERY_TARGET = 0.99       # Maintain high delivery

    # ========== JORGE'S 4 FRIENDLY QUESTIONS ==========
    # Rewritten for warm, consultative approach
    SELLER_QUESTIONS = {
        1: "I'd love to understand your situation better. What's prompting you to consider selling, and do you have a location in mind for your next home?",
        2: "To help you plan properly, would selling within the next 2-3 months work with your timeline and family needs?",
        3: "Could you help me understand your home's condition? Would you describe it as move-in ready, or are there areas that might need attention?",
        4: "What price range would feel right for you? I want to make sure we're aligned with realistic market values for your area."
    }

    # Question field mapping for gentle data extraction
    QUESTION_FIELD_MAPPING = {
        1: {"field": "motivation", "secondary": "relocation_destination"},
        2: {"field": "timeline_preferences", "secondary": "family_considerations"},
        3: {"field": "property_condition", "secondary": "improvement_interests"},
        4: {"field": "price_range_interest", "secondary": "market_research_done"}
    }

    # ========== FRIENDLY CONSULTATION TEMPLATES ==========
    # Jorge's warm, helpful messaging style
    FRIENDLY_CONSULTATION_PROMPTS = {
        "warm_greeting": [
            "Hi! I'm here to help you explore your real estate options.",
            "Thanks for reaching out! I'd be happy to guide you through the process.",
            "I appreciate you considering us for your real estate needs."
        ],
        "clarification_request": [
            "I want to make sure I understand your needs correctly. Could you help me with that?",
            "To give you the best guidance, I'd love to learn a bit more about your situation.",
            "I'm here to help make this as smooth as possible for you. Can we clarify a few details?"
        ],
        "supportive_follow_up": [
            "I'm happy to help clarify: {question}",
            "Let me ask this in a way that might be helpful: {question}",
            "To make sure I give you great advice: {question}"
        ],
        "timeline_discussion": [
            "What timeline feels comfortable for you and your family?",
            "I want to make sure we work within your schedule. What timeframe are you thinking?",
            "Let's find a timeline that works best for your situation."
        ],
        "price_conversation": [
            "What price range are you hoping to achieve?",
            "I'd love to help you understand current market values in your area.",
            "What would make this feel like a successful outcome for you?"
        ],
        "appreciation": [
            "I appreciate you taking the time to share that with me.",
            "Thank you for being so helpful with these questions.",
            "I'm grateful for your openness in discussing your needs."
        ]
    }

    # ========== READY-TO-MOVE HANDOFF MESSAGES ==========
    # Warm, professional handoff for qualified leads
    HOT_SELLER_HANDOFF_MESSAGES = [
        "Based on our conversation, I think our team can really help you. I'd love to connect you with one of our local Rancho Cucamonga specialists. Would you prefer a morning or afternoon call?",
        "You sound like exactly the kind of client we love working with. Let me introduce you to our team who can walk you through your options. Are mornings or afternoons better for you?",
        "I'm confident we can help you achieve your goals. Our local team would love to meet with you and discuss your specific situation. When would work best for a brief conversation?"
    ]

    # ========== RANCHO CUCAMONGA MARKET INTELLIGENCE ==========
    # Local market insights for consultative conversations
    MARKET_INSIGHTS = {
        "neighborhood_highlights": {
            "Alta Loma": "Highly rated schools, established neighborhoods, mountain views",
            "Etiwanda": "New developments, modern amenities, family-friendly",
            "Central RC": "Historic charm, mature trees, walkable communities",
            "North RC": "Newer construction, larger lots, premium locations"
        },
        "school_districts": {
            "Etiwanda School District": "Top-rated K-8, excellent test scores",
            "Chaffey Joint Union": "Strong high school programs, college prep",
            "Alta Loma Elementary": "Award-winning elementary programs"
        },
        "family_amenities": [
            "Victoria Gardens shopping and dining",
            "Central Park with sports facilities",
            "Close to Ontario Airport (15 minutes)",
            "Easy 60/210 freeway access to LA/OC",
            "Mountain hiking trails nearby"
        ],
        "market_trends": {
            "inventory_status": "Balanced market with good selection",
            "price_trajectory": "Steady appreciation, strong fundamentals",
            "buyer_activity": "Active but respectful market conditions",
            "best_selling_season": "Spring and early fall optimal"
        }
    }

    # ========== ANALYTICS & FRIENDLY METRICS ==========
    # Success metrics focused on relationship quality
    SUCCESS_METRICS = {
        "conversation_completion_rate": 0.75,    # Higher completion due to friendliness
        "relationship_quality_score": 0.80,     # New metric for service quality
        "ready_to_move_rate": 0.18,             # Slightly higher due to better experience
        "agent_consultation_rate": 0.25,        # Better conversion to consultations
        "follow_up_engagement_rate": 0.40,      # Higher engagement with friendly approach
        "referral_rate": 0.15,                  # Track referrals from good experience
        "opt_out_rate": 0.02                    # Lower opt-out with respectful approach
    }

    # Performance thresholds for friendly service
    PERFORMANCE_THRESHOLDS = {
        "response_time": 3.0,                   # Maintain quick response
        "message_delivery_rate": 0.99,         # High delivery standards
        "relationship_satisfaction": 0.85,     # New metric for friendly approach
        "california_dre_compliance": 1.0       # 100% California compliance
    }

    # ========== CALIFORNIA DRE COMPLIANCE ==========
    DRE_COMPLIANCE_REQUIREMENTS = {
        "license_disclosure": True,
        "fair_housing_compliance": True,
        "truthful_advertising": True,
        "proper_authorization": True,
        "client_confidentiality": True,
        "disclosure_obligations": True
    }

    # Required disclosures for California
    REQUIRED_DISCLOSURES = [
        "This communication is from a licensed real estate professional",
        "All information provided is for informational purposes",
        "Consult with qualified professionals for legal/financial advice",
        "Equal housing opportunity provider"
    ]

    # ========== ENVIRONMENT SPECIFIC SETTINGS ==========
    @classmethod
    def get_environment_config(cls) -> Dict:
        """Get environment-specific configuration for CA operations"""
        return {
            "friendly_approach": os.getenv("FRIENDLY_APPROACH", "true").lower() == "true",
            "california_market": os.getenv("CALIFORNIA_MARKET", "true").lower() == "true",
            "rancho_cucamonga_focus": os.getenv("RC_FOCUS", "true").lower() == "true",
            "max_sms_length": int(os.getenv("MAX_SMS_LENGTH", "160")),
            "hot_seller_threshold": float(os.getenv("HOT_SELLER_THRESHOLD", "0.85")),
            "warm_seller_threshold": float(os.getenv("WARM_SELLER_THRESHOLD", "0.65")),
            "active_followup_days": int(os.getenv("ACTIVE_FOLLOWUP_DAYS", "45")),
            "longterm_followup_interval": int(os.getenv("LONGTERM_FOLLOWUP_INTERVAL", "21")),
            "hot_seller_workflow_id": os.getenv("HOT_SELLER_WORKFLOW_ID"),
            "warm_seller_workflow_id": os.getenv("WARM_SELLER_WORKFLOW_ID"),

            # California-specific settings
            "dre_license_number": os.getenv("CA_DRE_LICENSE"),
            "brokerage_name": os.getenv("CA_BROKERAGE_NAME"),
            "compliance_mode": os.getenv("DRE_COMPLIANCE", "strict"),

            # Friendly classification thresholds
            "hot_questions_required": int(os.getenv("HOT_QUESTIONS_REQUIRED", str(cls.HOT_QUESTIONS_REQUIRED))),
            "hot_quality_threshold": float(os.getenv("HOT_QUALITY_THRESHOLD", str(cls.HOT_QUALITY_THRESHOLD))),
            "warm_questions_required": int(os.getenv("WARM_QUESTIONS_REQUIRED", str(cls.WARM_QUESTIONS_REQUIRED))),
            "warm_quality_threshold": float(os.getenv("WARM_QUALITY_THRESHOLD", str(cls.WARM_QUALITY_THRESHOLD))),
        }

    # ========== FRIENDLY VALIDATION RULES ==========
    @classmethod
    def validate_seller_response(cls, response: str) -> Dict:
        """Validate seller response with friendly, supportive approach"""
        response = response.strip()

        validation_result = {
            "is_valid": True,
            "quality_score": 1.0,
            "feedback": [],
            "support_level": "standard"
        }

        # Gentler assessment for short responses
        if len(response) < 8:
            validation_result["quality_score"] = 0.5
            validation_result["support_level"] = "extra_support"
            validation_result["feedback"].append("Would love to hear more details when you're ready")

        # Supportive response to uncertainty
        uncertain_words = ["maybe", "not sure", "idk", "thinking about it", "unsure", "don't know"]
        if any(word in response.lower() for word in uncertain_words):
            validation_result["quality_score"] *= 0.7  # Less penalty than confrontational
            validation_result["support_level"] = "guidance"
            validation_result["feedback"].append("Happy to help you think through the options")

        # Positive recognition for good engagement
        engagement_indicators = ["definitely", "yes", "exactly", "specifically", "$", "interested", "ready"]
        if any(indicator in response.lower() for indicator in engagement_indicators):
            validation_result["quality_score"] = min(1.0, validation_result["quality_score"] + 0.2)
            validation_result["feedback"].append("Great, thank you for sharing that")

        return validation_result

    # ========== FRIENDLY MESSAGE OPTIMIZATION ==========
    @classmethod
    def optimize_message_for_friendliness(cls, message: str) -> str:
        """Optimize message for warm, friendly customer service"""
        import re

        # Add warm language markers
        if cls.USE_WARM_LANGUAGE:
            # Keep professional but warm tone
            message = re.sub(r'^', '', message)  # No aggressive opening

        # Remove any confrontational language
        confrontational_patterns = [
            r"you need to",
            r"you have to",
            r"you must",
            r"listen",
            r"look",
            r"here's the deal",
            r"bottom line"
        ]

        for pattern in confrontational_patterns:
            message = re.sub(pattern, "", message, flags=re.IGNORECASE)

        # Add consultative language where appropriate
        if cls.USE_CONSULTATIVE_TONE:
            # Replace direct demands with consultative requests
            message = message.replace("Tell me", "Could you help me understand")
            message = message.replace("What's", "I'd love to know what's")
            message = message.replace("When", "When would")

        # Ensure SMS length compliance
        if len(message) > cls.MAX_SMS_LENGTH:
            message = message[:cls.MAX_SMS_LENGTH - 3] + "..."

        # Add friendly closing if space allows
        if len(message) < cls.MAX_SMS_LENGTH - 20:
            friendly_closings = [
                " Thanks!",
                " I appreciate it!",
                " Looking forward to helping!"
            ]
            # Add random friendly closing if there's space
            import random
            closing = random.choice(friendly_closings)
            if len(message + closing) <= cls.MAX_SMS_LENGTH:
                message += closing

        return message.strip()

    # ========== FRIENDLY TEMPERATURE CLASSIFICATION ==========
    @classmethod
    def classify_seller_temperature_friendly(
        cls,
        questions_answered: int,
        timeline_flexible: Optional[bool],
        response_quality: float,
        engagement_level: float
    ) -> str:
        """Classify seller temperature using friendly, inclusive criteria"""

        # Ready-to-move criteria (more inclusive than confrontational)
        if (questions_answered >= cls.HOT_QUESTIONS_REQUIRED and
            response_quality >= cls.HOT_QUALITY_THRESHOLD and
            engagement_level > 0.6):  # Consider flexible timelines
            return "ready_to_move"

        # Interested seller criteria (very inclusive)
        elif (questions_answered >= cls.WARM_QUESTIONS_REQUIRED and
              response_quality >= cls.WARM_QUALITY_THRESHOLD):
            return "interested"

        # Exploring options (everyone gets good service)
        else:
            return "exploring"

    # ========== RANCHO CUCAMONGA MARKET HELPERS ==========
    @classmethod
    def get_market_insight(cls, property_type: str = "single_family") -> Dict:
        """Get Rancho Cucamonga specific market insights"""
        return {
            "market_region": cls.MARKET_REGION,
            "primary_market": cls.PRIMARY_MARKET,
            "avg_price": cls.AVERAGE_PRICE,
            "market_activity": "Balanced with good inventory",
            "price_trend": "Steady appreciation",
            "days_on_market": "25-35 days typical",
            "best_features": cls.MARKET_INSIGHTS["family_amenities"][:3],
            "school_quality": "Excellent rated districts available"
        }

    @classmethod
    def get_neighborhood_highlights(cls, area: str) -> List[str]:
        """Get specific highlights for Rancho Cucamonga neighborhoods"""
        return cls.MARKET_INSIGHTS["neighborhood_highlights"].get(
            area, ["Great location", "Family friendly", "Good value"]
        )

    # ========== FRIENDLY FOLLOW-UP SCHEDULING ==========
    @classmethod
    def get_next_followup_day_friendly(cls, days_since_start: int) -> Optional[int]:
        """Get next follow-up day using friendly, respectful intervals"""
        if days_since_start <= cls.ACTIVE_FOLLOWUP_DAYS:
            # Active relationship building phase
            for day in cls.ACTIVE_FOLLOWUP_SCHEDULE:
                if day > days_since_start:
                    return day
            return None
        else:
            # Long-term relationship nurture phase
            return days_since_start + cls.LONGTERM_FOLLOWUP_INTERVAL

    # ========== CALIFORNIA DRE INTEGRATION HELPERS ==========
    @classmethod
    def get_dre_custom_field_id(cls, field_name: str) -> Optional[str]:
        """Get California DRE compliant custom field ID"""
        env_var = f"CA_CUSTOM_FIELD_{field_name.upper()}"
        return os.getenv(env_var) or cls.CUSTOM_FIELDS.get(field_name)

    @classmethod
    def get_ca_workflow_id(cls, temperature: str) -> Optional[str]:
        """Get California workflow ID based on seller temperature"""
        if temperature in ["ready_to_move", "hot"]:
            return os.getenv("CA_HOT_SELLER_WORKFLOW_ID") or cls.HOT_SELLER_WORKFLOW_ID
        elif temperature in ["interested", "warm"]:
            return os.getenv("CA_WARM_SELLER_WORKFLOW_ID") or cls.WARM_SELLER_WORKFLOW_ID
        return None

    # ========== FRIENDLY ANALYTICS HELPERS ==========
    @classmethod
    def calculate_relationship_score(cls, interactions: List[Dict]) -> float:
        """Calculate relationship quality score for friendly approach"""
        if not interactions:
            return 0.0

        # Factors: response rate, engagement quality, positive sentiment
        response_rate = len([i for i in interactions if i.get("response")]) / len(interactions)
        avg_quality = sum(i.get("quality", 0.5) for i in interactions) / len(interactions)
        sentiment_score = sum(i.get("sentiment", 0.5) for i in interactions) / len(interactions)

        # Weight factors for relationship building
        relationship_score = (response_rate * 0.4 + avg_quality * 0.3 + sentiment_score * 0.3)
        return min(1.0, relationship_score)

    @classmethod
    def is_performance_threshold_met_friendly(cls, metric: str, value: float) -> bool:
        """Check if friendly performance threshold is met"""
        threshold = cls.PERFORMANCE_THRESHOLDS.get(metric, 0.0)
        return value >= threshold


# ========== CALIFORNIA ENVIRONMENT CONFIGURATION ==========

class JorgeFriendlyEnvironmentSettings:
    """Environment-specific settings for Jorge's friendly California bots"""

    def __init__(self):
        """Initialize with California-focused environment variables"""
        self.friendly_approach = os.getenv("FRIENDLY_APPROACH", "true").lower() == "true"
        self.california_market = os.getenv("CALIFORNIA_MARKET", "true").lower() == "true"
        self.rancho_cucamonga_focus = os.getenv("RC_FOCUS", "true").lower() == "true"

        self.activation_tags = self._parse_list_env("ACTIVATION_TAGS", JorgeFriendlyConfig.ACTIVATION_TAGS)
        self.deactivation_tags = self._parse_list_env("DEACTIVATION_TAGS", JorgeFriendlyConfig.DEACTIVATION_TAGS)

        # Friendly thresholds
        self.hot_seller_threshold = float(os.getenv("HOT_SELLER_THRESHOLD", "0.85"))
        self.warm_seller_threshold = float(os.getenv("WARM_SELLER_THRESHOLD", "0.65"))

        # Friendly classification thresholds
        self.hot_questions_required = int(os.getenv("HOT_QUESTIONS_REQUIRED", str(JorgeFriendlyConfig.HOT_QUESTIONS_REQUIRED)))
        self.hot_quality_threshold = float(os.getenv("HOT_QUALITY_THRESHOLD", str(JorgeFriendlyConfig.HOT_QUALITY_THRESHOLD)))
        self.warm_questions_required = int(os.getenv("WARM_QUESTIONS_REQUIRED", str(JorgeFriendlyConfig.WARM_QUESTIONS_REQUIRED)))
        self.warm_quality_threshold = float(os.getenv("WARM_QUALITY_THRESHOLD", str(JorgeFriendlyConfig.WARM_QUALITY_THRESHOLD)))

        # Friendly messaging
        self.max_sms_length = int(os.getenv("MAX_SMS_LENGTH", "160"))
        self.use_warm_language = os.getenv("USE_WARM_LANGUAGE", "true").lower() == "true"
        self.consultative_tone = os.getenv("CONSULTATIVE_TONE", "true").lower() == "true"
        self.relationship_focused = os.getenv("RELATIONSHIP_FOCUSED", "true").lower() == "true"

        # Relationship building follow-up
        self.active_followup_days = int(os.getenv("ACTIVE_FOLLOWUP_DAYS", "45"))
        self.longterm_followup_interval = int(os.getenv("LONGTERM_FOLLOWUP_INTERVAL", "21"))

        # California workflows
        self.hot_seller_workflow_id = os.getenv("CA_HOT_SELLER_WORKFLOW_ID")
        self.warm_seller_workflow_id = os.getenv("CA_WARM_SELLER_WORKFLOW_ID")

        # DRE compliance
        self.dre_license = os.getenv("CA_DRE_LICENSE")
        self.brokerage_name = os.getenv("CA_BROKERAGE_NAME")
        self.compliance_mode = os.getenv("DRE_COMPLIANCE", "strict")

        # Analytics
        self.analytics_enabled = os.getenv("FRIENDLY_ANALYTICS_ENABLED", "true").lower() == "true"

    def _parse_list_env(self, env_var: str, default: List[str]) -> List[str]:
        """Parse environment variable as list"""
        value = os.getenv(env_var)
        if value:
            try:
                import json
                return json.loads(value)
            except json.JSONDecodeError:
                return value.split(",")
        return default

    @property
    def FRIENDLY_MODE(self) -> bool:
        """Check if friendly mode is enabled"""
        return self.friendly_approach

    @property
    def CALIFORNIA_MARKET(self) -> bool:
        """Check if California market mode is enabled"""
        return self.california_market

    @property
    def ACTIVATION_TAGS(self) -> List[str]:
        """Get activation tags for friendly approach"""
        return self.activation_tags

    @property
    def DEACTIVATION_TAGS(self) -> List[str]:
        """Get deactivation tags"""
        return self.deactivation_tags


# ========== EXPORTS ==========

# Create global friendly settings instance
friendly_settings = JorgeFriendlyEnvironmentSettings()

# Export commonly used values for compatibility
FRIENDLY_MODE = friendly_settings.FRIENDLY_MODE
CALIFORNIA_MARKET = friendly_settings.CALIFORNIA_MARKET
ACTIVATION_TAGS = friendly_settings.ACTIVATION_TAGS
DEACTIVATION_TAGS = friendly_settings.DEACTIVATION_TAGS

__all__ = [
    "JorgeFriendlyConfig",
    "JorgeFriendlyEnvironmentSettings",
    "friendly_settings",
    "FRIENDLY_MODE",
    "CALIFORNIA_MARKET",
    "ACTIVATION_TAGS",
    "DEACTIVATION_TAGS"
]