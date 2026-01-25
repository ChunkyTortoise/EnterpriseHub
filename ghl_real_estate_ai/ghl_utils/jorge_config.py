"""
Jorge's Seller Bot Configuration

This module contains all configuration settings, constants, and parameters
for Jorge's seller qualification bot. Centralizes all Jorge-specific
settings for easy management and deployment.

Author: Claude Code Assistant
Created: 2026-01-19
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import os


@dataclass
class JorgeSellerConfig:
    """Central configuration for Jorge's seller bot"""

    # ========== ACTIVATION/DEACTIVATION TAGS ==========
    ACTIVATION_TAGS = ["Needs Qualifying"]
    DEACTIVATION_TAGS = ["AI-Off", "Qualified", "Stop-Bot", "Seller-Qualified"]

    # ========== TEMPERATURE TAGS ==========
    HOT_SELLER_TAG = "Hot-Seller"
    WARM_SELLER_TAG = "Warm-Seller"
    COLD_SELLER_TAG = "Cold-Seller"

    # ========== CLASSIFICATION THRESHOLDS ==========
    # Jorge's specific requirements for lead temperature
    HOT_SELLER_THRESHOLD = 1.0  # Must answer all 4 questions (4/4 = 100%)
    WARM_SELLER_THRESHOLD = 0.75  # Must answer 3+ questions (3/4 = 75%)
    COLD_SELLER_THRESHOLD = 0.0  # Below warm threshold

    # Additional qualification criteria
    HOT_SELLER_MIN_RESPONSE_QUALITY = 0.7  # High quality responses required
    WARM_SELLER_MIN_RESPONSE_QUALITY = 0.5  # Decent responses required
    TIMELINE_URGENCY_WEIGHT = 0.35  # 35% weight for timeline in scoring

    # ========== TEMPERATURE CLASSIFICATION THRESHOLDS (Configurable) ==========
    # Hot seller criteria (strictest)
    HOT_QUESTIONS_REQUIRED = 4  # Must answer all 4 questions
    HOT_QUALITY_THRESHOLD = 0.7  # Minimum response quality for hot
    HOT_TIMELINE_REQUIRED = True  # Must accept 30-45 day timeline

    # Warm seller criteria
    WARM_QUESTIONS_REQUIRED = 3  # Must answer at least 3 questions
    WARM_QUALITY_THRESHOLD = 0.5  # Minimum response quality for warm

    # ========== FOLLOW-UP SETTINGS ==========
    # Active follow-up phase (first 30 days)
    ACTIVE_FOLLOWUP_DAYS = 30
    ACTIVE_FOLLOWUP_INTERVAL_MIN = 2  # Minimum days between follow-ups
    ACTIVE_FOLLOWUP_INTERVAL_MAX = 3  # Maximum days between follow-ups

    # Specific follow-up schedule for Jorge (every 2-3 days)
    ACTIVE_FOLLOWUP_SCHEDULE = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]  # Days 1-30

    # Long-term follow-up phase (after 30 days)
    LONGTERM_FOLLOWUP_INTERVAL = 14  # Every 14 days
    MAX_FOLLOWUP_ATTEMPTS = 10  # Stop after 10 long-term attempts

    # ========== GHL INTEGRATION ==========
    # Workflow IDs for different seller temperatures
    HOT_SELLER_WORKFLOW_ID = "jorge_hot_seller_workflow"
    WARM_SELLER_WORKFLOW_ID = "jorge_warm_seller_workflow"
    AGENT_NOTIFICATION_WORKFLOW = "jorge_agent_notification"

    # Custom field mapping for GHL
    CUSTOM_FIELDS = {
        "seller_temperature": "seller_temp_field_id",
        "seller_motivation": "seller_motivation_field_id",
        "relocation_destination": "relocation_dest_field_id",
        "timeline_urgency": "timeline_urgency_field_id",
        "property_condition": "property_condition_field_id",
        "price_expectation": "price_expectation_field_id",
        "questions_answered": "questions_answered_field_id",
        "qualification_score": "qualification_score_field_id",
        "expected_roi": "expected_roi_field_id",
        "lead_value_tier": "lead_value_tier_field_id",
        "ai_valuation_price": "ai_valuation_price_field_id",
        "detected_persona": "detected_persona_field_id",
        "psychology_type": "psychology_type_field_id",
        "urgency_level": "urgency_level_field_id"
    }

    # ========== MESSAGE SETTINGS ==========
    # Jorge's friendly SMS requirements
    MAX_SMS_LENGTH = 160
    FRIENDLY_APPROACH = True
    USE_WARM_LANGUAGE = True
    NO_HYPHENS = True
    NO_ROBOTIC_LANGUAGE = True

    # Message response time targets
    RESPONSE_TIME_TARGET_SECONDS = 2  # Webhook processing under 2 seconds
    MESSAGE_DELIVERY_TARGET = 0.99  # 99% delivery success rate

    # ========== JORGE'S 4 QUESTIONS ==========
    # Exact questions in Jorge's preferred order
    SELLER_QUESTIONS = {
        1: "What's got you considering wanting to sell, where would you move to?",
        2: "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
        3: "How would you describe your home, would you say it's move-in ready or would it need some work?",
        4: "What price would incentivize you to sell?"
    }

    # Question field mapping for data extraction
    QUESTION_FIELD_MAPPING = {
        1: {"field": "motivation", "secondary": "relocation_destination"},
        2: {"field": "timeline_acceptable", "secondary": "timeline_urgency"},
        3: {"field": "property_condition", "secondary": "repair_estimate"},
        4: {"field": "price_expectation", "secondary": "price_flexibility"}
    }

    # ========== FRIENDLY CONSULTATION TEMPLATES ==========
    # Jorge's helpful messaging style
    FRIENDLY_CONSULTATION_PROMPTS = {
        "clarification_needed": [
            "I'd love to better understand your situation. Could you help me with that?",
            "I want to make sure I'm giving you the best advice. Can we clarify a few details?",
            "To help you make the best decision, I'd like to understand your priorities better."
        ],
        "supportive_follow_up": [
            "I'd be happy to help clarify: {question}",
            "Let me ask this in a helpful way: {question}",
            "To give you the best guidance: {question}"
        ],
        "timeline_discussion": [
            "What timeline would work best for your situation?",
            "Is this timeline something that feels comfortable for you?",
            "I want to make sure this works with your schedule and needs."
        ],
        "price_conversation": [
            "What price range would feel right for you?",
            "I'd love to help you understand realistic market values.",
            "What outcome would make this feel like a great decision?"
        ]
    }

    # ========== HOT SELLER HANDOFF MESSAGES ==========
    HOT_SELLER_HANDOFF_MESSAGES = [
        "Based on your answers, you're exactly who we help. Let me get you scheduled with our team to discuss your options. When works better for you, morning or afternoon?",
        "Perfect. You're a great fit for our program. I'm connecting you with our team now. Are mornings or afternoons better for a quick call?",
        "You answered all my questions, which tells me you're serious. Let me get you scheduled with our team today. Morning or afternoon?"
    ]

    # ========== ANALYTICS & MONITORING ==========
    # Success metrics and KPIs
    SUCCESS_METRICS = {
        "qualification_completion_rate": 0.60,  # 60% complete all 4 questions
        "hot_lead_conversion_rate": 0.15,  # 15% become hot leads
        "agent_handoff_rate": 0.20,  # 20% advance to agent calls
        "followup_engagement_rate": 0.30,  # 30% engage with follow-ups
        "opt_out_rate": 0.05  # <5% request no contact
    }

    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        "webhook_response_time": 2.0,  # Max 2 seconds
        "message_delivery_rate": 0.99,  # Min 99%
        "classification_accuracy": 0.90,  # Min 90% accuracy
        "sms_compliance_rate": 1.0  # 100% SMS compliant
    }

    # ========== ENVIRONMENT SPECIFIC SETTINGS ==========
    @classmethod
    def get_environment_config(cls) -> Dict:
        """Get environment-specific configuration"""
        return {
            "jorge_seller_mode": os.getenv("JORGE_SELLER_MODE", "false").lower() == "true",
            "friendly_approach": os.getenv("FRIENDLY_APPROACH", "true").lower() == "true",
            "max_sms_length": int(os.getenv("MAX_SMS_LENGTH", "160")),
            "hot_seller_threshold": float(os.getenv("HOT_SELLER_THRESHOLD", "1.0")),
            "warm_seller_threshold": float(os.getenv("WARM_SELLER_THRESHOLD", "0.75")),
            "active_followup_days": int(os.getenv("ACTIVE_FOLLOWUP_DAYS", "30")),
            "longterm_followup_interval": int(os.getenv("LONGTERM_FOLLOWUP_INTERVAL", "14")),
            "hot_seller_workflow_id": os.getenv("HOT_SELLER_WORKFLOW_ID"),
            "warm_seller_workflow_id": os.getenv("WARM_SELLER_WORKFLOW_ID"),
            # Temperature classification thresholds (configurable via environment)
            "hot_questions_required": int(os.getenv("HOT_QUESTIONS_REQUIRED", str(cls.HOT_QUESTIONS_REQUIRED))),
            "hot_quality_threshold": float(os.getenv("HOT_QUALITY_THRESHOLD", str(cls.HOT_QUALITY_THRESHOLD))),
            "warm_questions_required": int(os.getenv("WARM_QUESTIONS_REQUIRED", str(cls.WARM_QUESTIONS_REQUIRED))),
            "warm_quality_threshold": float(os.getenv("WARM_QUALITY_THRESHOLD", str(cls.WARM_QUALITY_THRESHOLD))),
        }

    # ========== VALIDATION RULES ==========
    @classmethod
    def validate_seller_response(cls, response: str) -> Dict:
        """Validate seller response quality"""
        response = response.strip()

        validation_result = {
            "is_valid": True,
            "quality_score": 1.0,
            "issues": [],
            "provide_support": False
        }

        # Check for very short responses (need more info)
        if len(response) < 10:
            validation_result["quality_score"] = 0.2
            validation_result["provide_support"] = True
            validation_result["issues"].append("Could use more detail")

        # Check for uncertain indicators (opportunity to help)
        uncertain_words = ["maybe", "not sure", "idk", "i don't know", "thinking about it", "unsure"]
        if any(word in response.lower() for word in uncertain_words):
            validation_result["quality_score"] *= 0.5
            validation_result["provide_support"] = True
            validation_result["issues"].append("Could use guidance")

        # Check for good quality indicators
        specific_indicators = ["definitely", "yes", "no", "exactly", "specifically", "$", "days", "weeks"]
        if any(indicator in response.lower() for indicator in specific_indicators):
            validation_result["quality_score"] = min(1.0, validation_result["quality_score"] + 0.3)

        return validation_result

    # ========== MESSAGE SANITIZATION ==========
    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """Sanitize message for Jorge's requirements"""
        import re

        # Keep warm, professional language
        if cls.USE_WARM_LANGUAGE:
            # Allow basic punctuation and keep friendly tone
            message = re.sub(r'[^\w\s,.!?😊👍]', '', message)

        # Remove hyphens (Jorge requirement)
        if cls.NO_HYPHENS:
            message = message.replace('-', ' ')

        # Remove robotic language patterns
        if cls.NO_ROBOTIC_LANGUAGE:
            robotic_patterns = [
                r"I'm here to help",
                r"Thank you for your time",
                r"I appreciate your response",
                r"Have a great day"
            ]
            for pattern in robotic_patterns:
                message = re.sub(pattern, '', message, flags=re.IGNORECASE)

        # Ensure SMS length compliance
        if len(message) > cls.MAX_SMS_LENGTH:
            message = message[:cls.MAX_SMS_LENGTH - 3] + "..."

        return message.strip()

    # ========== TEMPERATURE CLASSIFICATION ==========
    @classmethod
    def classify_seller_temperature(
        cls,
        questions_answered: int,
        timeline_acceptable: Optional[bool],
        response_quality: float,
        responsiveness: float
    ) -> str:
        """Classify seller temperature based on Jorge's criteria"""

        # Hot seller criteria (Jorge's exact requirements)
        if (questions_answered == 4 and
            timeline_acceptable is True and
            response_quality >= cls.HOT_SELLER_MIN_RESPONSE_QUALITY and
            responsiveness > 0.7):
            return "hot"

        # Warm seller criteria
        elif (questions_answered >= 3 and
              response_quality >= cls.WARM_SELLER_MIN_RESPONSE_QUALITY):
            return "warm"

        # Cold seller (default)
        else:
            return "cold"

    # ========== FOLLOW-UP SCHEDULING ==========
    @classmethod
    def get_next_followup_day(cls, days_since_start: int) -> Optional[int]:
        """Get the next scheduled follow-up day"""
        if days_since_start <= cls.ACTIVE_FOLLOWUP_DAYS:
            # Active phase - use Jorge's specific schedule
            for day in cls.ACTIVE_FOLLOWUP_SCHEDULE:
                if day > days_since_start:
                    return day
            return None
        else:
            # Long-term phase - every 14 days
            return days_since_start + cls.LONGTERM_FOLLOWUP_INTERVAL

    # ========== GHL INTEGRATION HELPERS ==========
    @classmethod
    def get_ghl_custom_field_id(cls, field_name: str) -> Optional[str]:
        """Get GHL custom field ID for seller data field"""
        env_var = f"CUSTOM_FIELD_{field_name.upper()}"
        return os.getenv(env_var) or cls.CUSTOM_FIELDS.get(field_name)

    @classmethod
    def get_workflow_id(cls, temperature: str) -> Optional[str]:
        """Get appropriate workflow ID based on seller temperature"""
        if temperature == "hot":
            return os.getenv("HOT_SELLER_WORKFLOW_ID") or cls.HOT_SELLER_WORKFLOW_ID
        elif temperature == "warm":
            return os.getenv("WARM_SELLER_WORKFLOW_ID") or cls.WARM_SELLER_WORKFLOW_ID
        return None

    # ========== ANALYTICS HELPERS ==========
    @classmethod
    def calculate_completion_rate(cls, total_leads: int, completed_leads: int) -> float:
        """Calculate qualification completion rate"""
        if total_leads == 0:
            return 0.0
        return completed_leads / total_leads

    @classmethod
    def is_performance_threshold_met(cls, metric: str, value: float) -> bool:
        """Check if performance threshold is met"""
        threshold = cls.PERFORMANCE_THRESHOLDS.get(metric, 0.0)
        return value >= threshold


# ========== ENVIRONMENT CONFIGURATION ==========

class JorgeEnvironmentSettings:
    """Environment-specific settings for Jorge's seller bot"""

    def __init__(self):
        """Initialize with environment variables"""
        self.jorge_seller_mode = os.getenv("JORGE_SELLER_MODE", "false").lower() == "true"
        self.activation_tags = self._parse_list_env("ACTIVATION_TAGS", JorgeSellerConfig.ACTIVATION_TAGS)
        self.deactivation_tags = self._parse_list_env("DEACTIVATION_TAGS", JorgeSellerConfig.DEACTIVATION_TAGS)

        # Thresholds
        self.hot_seller_threshold = float(os.getenv("HOT_SELLER_THRESHOLD", "1.0"))
        self.warm_seller_threshold = float(os.getenv("WARM_SELLER_THRESHOLD", "0.75"))

        # Temperature classification thresholds (configurable)
        self.hot_questions_required = int(os.getenv("HOT_QUESTIONS_REQUIRED", str(JorgeSellerConfig.HOT_QUESTIONS_REQUIRED)))
        self.hot_quality_threshold = float(os.getenv("HOT_QUALITY_THRESHOLD", str(JorgeSellerConfig.HOT_QUALITY_THRESHOLD)))
        self.warm_questions_required = int(os.getenv("WARM_QUESTIONS_REQUIRED", str(JorgeSellerConfig.WARM_QUESTIONS_REQUIRED)))
        self.warm_quality_threshold = float(os.getenv("WARM_QUALITY_THRESHOLD", str(JorgeSellerConfig.WARM_QUALITY_THRESHOLD)))

        # Message settings
        self.max_sms_length = int(os.getenv("MAX_SMS_LENGTH", "160"))
        self.friendly_approach = os.getenv("FRIENDLY_APPROACH", "true").lower() == "true"
        self.use_warm_language = os.getenv("USE_WARM_LANGUAGE", "true").lower() == "true"
        self.no_hyphens = os.getenv("NO_HYPHENS", "true").lower() == "true"

        # Follow-up settings
        self.active_followup_days = int(os.getenv("ACTIVE_FOLLOWUP_DAYS", "30"))
        self.longterm_followup_interval = int(os.getenv("LONGTERM_FOLLOWUP_INTERVAL", "14"))

        # GHL integration
        self.hot_seller_workflow_id = os.getenv("HOT_SELLER_WORKFLOW_ID")
        self.warm_seller_workflow_id = os.getenv("WARM_SELLER_WORKFLOW_ID")

        # Analytics
        self.analytics_enabled = os.getenv("JORGE_ANALYTICS_ENABLED", "true").lower() == "true"

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
    def JORGE_SELLER_MODE(self) -> bool:
        """Compatibility property for existing code"""
        return self.jorge_seller_mode

    @property
    def ACTIVATION_TAGS(self) -> List[str]:
        """Get activation tags"""
        return self.activation_tags

    @property
    def DEACTIVATION_TAGS(self) -> List[str]:
        """Get deactivation tags"""
        return self.deactivation_tags


# ========== EXPORTS ==========

# Create global settings instance
settings = JorgeEnvironmentSettings()

# Export commonly used values
JORGE_SELLER_MODE = settings.JORGE_SELLER_MODE
ACTIVATION_TAGS = settings.ACTIVATION_TAGS
DEACTIVATION_TAGS = settings.DEACTIVATION_TAGS

__all__ = [
    "JorgeSellerConfig",
    "JorgeEnvironmentSettings",
    "settings",
    "JORGE_SELLER_MODE",
    "ACTIVATION_TAGS",
    "DEACTIVATION_TAGS"
]