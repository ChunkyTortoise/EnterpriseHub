"""
Jorge's Seller Bot Configuration

This module contains all configuration settings, constants, and parameters
for Jorge's seller qualification bot. Centralizes all Jorge-specific
settings for easy management and deployment.

Author: Claude Code Assistant
Created: 2026-01-19
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class JorgeSellerConfig:
    """Central configuration for Jorge's seller bot"""

    # ========== SIMPLE MODE ==========
    # Simple mode: disables enterprise features (investor arbitrage, loss aversion,
    # psychology profiling, Voss negotiation, drift detection, market insights)
    # When True, bot follows strict 4-question flow (high conversion)
    # When False, bot follows full 10-question flow (deep qualification)
    # Can be overridden by JORGE_SIMPLE_MODE environment variable
    JORGE_SIMPLE_MODE: bool = os.getenv("JORGE_SIMPLE_MODE", "true").lower() == "true"

    # ========== ACTIVATION/DEACTIVATION TAGS ==========
    ACTIVATION_TAGS = ["needs qualifying", "Needs Qualifying", "Seller-Lead"]
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
    # Hot seller criteria - Simple Mode (4 questions)
    HOT_QUESTIONS_REQUIRED_SIMPLE = 4  # Must answer all 4 questions
    HOT_QUALITY_THRESHOLD = 0.7  # Minimum response quality for hot
    HOT_TIMELINE_REQUIRED = True  # Must accept 30-45 day timeline

    # Warm seller criteria - Simple Mode (4 questions)
    WARM_QUESTIONS_REQUIRED_SIMPLE = 3  # Must answer at least 3 questions
    WARM_QUALITY_THRESHOLD = 0.5  # Minimum response quality for warm

    # Hot seller criteria - Full Mode (10 questions)
    HOT_QUESTIONS_REQUIRED_FULL = 10  # Must answer all 10 questions
    HOT_QUALITY_THRESHOLD_FULL = 0.7  # High quality responses required

    # Warm seller criteria - Full Mode (10 questions)
    WARM_QUESTIONS_REQUIRED_FULL = 7  # Must answer at least 7 questions
    WARM_QUALITY_THRESHOLD_FULL = 0.5  # Decent responses required

    # Dynamic thresholds based on mode
    HOT_QUESTIONS_REQUIRED = HOT_QUESTIONS_REQUIRED_SIMPLE  # Default to simple
    WARM_QUESTIONS_REQUIRED = WARM_QUESTIONS_REQUIRED_SIMPLE  # Default to simple

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
    HOT_SELLER_WORKFLOW_ID = ""  # Set via HOT_SELLER_WORKFLOW_ID env var
    WARM_SELLER_WORKFLOW_ID = ""  # Set via WARM_SELLER_WORKFLOW_ID env var
    AGENT_NOTIFICATION_WORKFLOW = ""  # Set via NOTIFY_AGENT_WORKFLOW_ID env var

    # Custom field mapping for GHL
    CUSTOM_FIELDS = {
        "seller_temperature": "",
        "seller_motivation": "",
        "relocation_destination": "",
        "timeline_urgency": "",
        "property_condition": "",
        "price_expectation": "",
        "questions_answered": "",
        "qualification_score": "",
        "expected_roi": "",
        "lead_value_tier": "",
        "ai_valuation_price": "",
        "detected_persona": "",
        "psychology_type": "",
        "urgency_level": "",
        # Phase 2: Additional fields from original spec
        "mortgage_balance": os.environ.get("CUSTOM_FIELD_MORTGAGE_BALANCE", ""),
        "repair_estimate": os.environ.get("CUSTOM_FIELD_REPAIR_ESTIMATE", ""),
        "listing_history": "",
        "decision_maker_confirmed": "",
        "preferred_contact_method": "",
        "property_address": "",
        "property_type": "",
        "last_bot_interaction": "",
        "qualification_complete": "",
        # Bot tracking fields (recommended for CRM reporting)
        "bot_buyer_persona": os.environ.get("CUSTOM_FIELD_BOT_BUYER_PERSONA", ""),
        "bot_language": os.environ.get("CUSTOM_FIELD_BOT_LANGUAGE", ""),
        "bot_conversation_stage": os.environ.get("CUSTOM_FIELD_BOT_CONVERSATION_STAGE", ""),
        "bot_last_interaction": os.environ.get("CUSTOM_FIELD_BOT_LAST_INTERACTION", ""),
        "bot_qualification_score": os.environ.get("CUSTOM_FIELD_BOT_QUALIFICATION_SCORE", ""),
        "bot_active": os.environ.get("CUSTOM_FIELD_BOT_ACTIVE", ""),
        # Offer pathway classification (derived from Q2-Q4)
        "offer_type": os.environ.get("CUSTOM_FIELD_OFFER_TYPE", ""),
    }

    @staticmethod
    def classify_offer_type(
        property_condition: str = "",
        seller_motivation: str = "",
        timeline_urgency: str = "",
    ) -> str:
        """Classify seller intent as 'wholesale', 'listing', or 'unknown'.

        Derived from the 4 existing qualification answers — no 5th question needed.
        Wholesale signals: distressed condition, inherited/divorce/foreclosure motivation,
        or urgent timeline with poor condition.
        Listing signals: move-in ready condition, standard relocation/upgrade motivation.
        """
        condition = (property_condition or "").lower()
        motivation = (seller_motivation or "").lower()
        timeline = (timeline_urgency or "").lower()

        wholesale_condition = any(
            kw in condition for kw in ("fixer", "needs work", "work", "repair", "rough", "poor", "as-is", "distressed")
        )
        wholesale_motivation = any(
            kw in motivation
            for kw in ("inherited", "inherit", "divorce", "foreclosure", "behind", "distressed", "estate")
        )
        listing_condition = any(
            kw in condition
            for kw in ("move-in", "move in", "ready", "excellent", "good", "updated", "renovated", "remodeled")
        )
        listing_motivation = any(
            kw in motivation for kw in ("upsize", "upgrade", "downsize", "retire", "relocat", "new job", "family")
        )

        # Strong wholesale signals (condition is the most reliable indicator)
        if wholesale_condition or wholesale_motivation:
            return "wholesale"
        if listing_condition or listing_motivation:
            return "listing"
        return "unknown"

    # ========== MESSAGE SETTINGS ==========
    # Jorge's friendly SMS requirements
    MAX_SMS_LENGTH = 320
    FRIENDLY_APPROACH = True
    USE_WARM_LANGUAGE = True
    NO_HYPHENS = True
    NO_ROBOTIC_LANGUAGE = True

    # Message response time targets
    RESPONSE_TIME_TARGET_SECONDS = 2  # Webhook processing under 2 seconds
    MESSAGE_DELIVERY_TARGET = 0.99  # 99% delivery success rate

    # ========== JORGE'S QUESTIONS ==========
    # Full 10-question qualification flow (original spec)
    # Can be configured via JORGE_SIMPLE_MODE to use 4-question flow
    SELLER_QUESTIONS_FULL = {
        1: "What's the address of the property you're thinking about selling?",
        2: "What's got you considering wanting to sell, where would you move to?",
        3: "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
        4: "How would you describe your home, would you say it's move-in ready or would it need some work?",
        5: "What price would incentivize you to sell?",
        6: "Do you have any existing mortgage or liens on the property?",
        7: "Are there any repairs or improvements needed before listing?",
        8: "Have you tried listing this property before?",
        9: "Are you the primary decision-maker, or would anyone else need to be involved?",
        10: "What's the best way to reach you - call, text, or email?",
    }

    # Simplified 5-question flow (friendly/high-conversion)
    # Q0: address capture (asked only on first message, triggers MLS/CMA lookup)
    # Q1-Q4: qualification questions
    SELLER_QUESTIONS_SIMPLE = {
        0: "Before we dive in — what's the property address? Just so I can look up the right information for your area.",
        1: "What's making you think about selling, and where would you move to?",
        2: "If our team sold your home within the next 30 to 45 days, would that work for you?",
        3: "How would you describe your home — move in ready or would it need some work?",
        4: "What price would make you feel good about selling?",
    }

    # Default to simple mode (configured via JORGE_SIMPLE_MODE)
    SELLER_QUESTIONS = SELLER_QUESTIONS_SIMPLE

    # Question field mapping for data extraction (full flow)
    QUESTION_FIELD_MAPPING_FULL = {
        1: {"field": "property_address", "secondary": "property_type"},
        2: {"field": "motivation", "secondary": "relocation_destination"},
        3: {"field": "timeline_acceptable", "secondary": "timeline_urgency"},
        4: {"field": "property_condition", "secondary": "repair_estimate"},
        5: {"field": "price_expectation", "secondary": "price_flexibility"},
        6: {"field": "mortgage_balance", "secondary": "has_liens"},
        7: {"field": "repair_needs", "secondary": "repair_estimate"},
        8: {"field": "listing_history", "secondary": "previous_asking_price"},
        9: {"field": "decision_maker_confirmed", "secondary": "other_decision_makers"},
        10: {"field": "preferred_contact_method", "secondary": "best_contact_times"},
    }

    # Question field mapping for simple flow
    # Q0 captures property_address before the 4 qualification questions
    QUESTION_FIELD_MAPPING_SIMPLE = {
        0: {"field": "property_address", "secondary": "property_type"},
        1: {"field": "motivation", "secondary": "relocation_destination"},
        2: {"field": "timeline_acceptable", "secondary": "timeline_urgency"},
        3: {"field": "property_condition", "secondary": "repair_estimate"},
        4: {"field": "price_expectation", "secondary": "price_flexibility"},
    }

    # Default to simple mode mapping
    QUESTION_FIELD_MAPPING = QUESTION_FIELD_MAPPING_SIMPLE

    # ========== FRIENDLY CONSULTATION TEMPLATES ==========
    # Jorge's helpful messaging style
    FRIENDLY_CONSULTATION_PROMPTS = {
        "clarification_needed": [
            "I'd love to better understand your situation. Could you help me with that?",
            "I want to make sure I'm giving you the best advice. Can we clarify a few details?",
            "To help you make the best decision, I'd like to understand your priorities better.",
        ],
        "supportive_follow_up": [
            "I'd be happy to help clarify: {question}",
            "Let me ask this in a helpful way: {question}",
            "To give you the best guidance: {question}",
        ],
        "timeline_discussion": [
            "What timeline would work best for your situation?",
            "Is this timeline something that feels comfortable for you?",
            "I want to make sure this works with your schedule and needs.",
        ],
        "price_conversation": [
            "What price range would feel right for you?",
            "I'd love to help you understand realistic market values.",
            "What outcome would make this feel like a great decision?",
        ],
    }

    # ========== CMA DISCLAIMER & CONFIDENCE ROUTING ==========
    CMA_DISCLAIMERS = {
        "high": "This estimate is based on {comp_count} comparable sales in your area. Market conditions, property condition, and buyer demand may affect actual value. Not a professional appraisal.",
        "medium": "This is a preliminary estimate based on limited comparable data. For a precise valuation, Jorge can walk you through it in person.",
        "low": "We don't have enough recent sales data to give a reliable estimate for your area right now. Jorge can provide a personalized analysis.",
    }
    CMA_CONFIDENCE_THRESHOLDS = {"high": 70.0, "medium": 50.0}

    # ========== HOT SELLER HANDOFF MESSAGES ==========
    HOT_SELLER_HANDOFF_MESSAGES = [
        "Great news! I'm connecting you with Jorge directly. He'll reach out shortly to go over everything.",
        "You're a great fit. Let me get Jorge on the line — he'll follow up with you soon.",
        "Awesome, you answered everything! Jorge's going to love working with you. He'll be in touch shortly.",
    ]

    # ========== BUYER BOT SETTINGS ==========
    # Buyer follow-up schedule (mirrors seller pattern per spec)
    BUYER_FOLLOWUP_SCHEDULE = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]
    BUYER_LONGTERM_INTERVAL = 14
    BUYER_TEMPERATURE_TAGS = {"hot": "Hot-Buyer", "warm": "Warm-Buyer", "cold": "Cold-Buyer"}

    # ========== ANALYTICS & MONITORING ==========
    # Success metrics and KPIs (Simple Mode - 4 questions)
    SUCCESS_METRICS_SIMPLE = {
        "qualification_completion_rate": 0.60,  # 60% complete all 4 questions
        "hot_lead_conversion_rate": 0.15,  # 15% become hot leads
        "agent_handoff_rate": 0.20,  # 20% advance to agent calls
        "followup_engagement_rate": 0.30,  # 30% engage with follow-ups
        "opt_out_rate": 0.05,  # <5% request no contact
    }

    # Success metrics and KPIs (Full Mode - 10 questions)
    SUCCESS_METRICS_FULL = {
        "qualification_completion_rate": 0.40,  # 40% complete all 10 questions (more challenging)
        "hot_lead_conversion_rate": 0.20,  # 20% become hot leads (deeper qualification)
        "agent_handoff_rate": 0.25,  # 25% advance to agent calls (better qualified)
        "followup_engagement_rate": 0.30,  # 30% engage with follow-ups
        "opt_out_rate": 0.08,  # <8% request no contact (longer flow = slightly higher drop)
    }

    # Default to simple mode metrics
    SUCCESS_METRICS = SUCCESS_METRICS_SIMPLE

    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        "webhook_response_time": 2.0,  # Max 2 seconds
        "message_delivery_rate": 0.99,  # Min 99%
        "classification_accuracy": 0.90,  # Min 90% accuracy
        "sms_compliance_rate": 1.0,  # 100% SMS compliant
    }

    # ========== MODE SWITCHING ==========
    @classmethod
    def set_mode(cls, simple_mode: bool):
        """
        Switch between simple mode (4 questions) and full mode (10 questions).

        Args:
            simple_mode: If True, use 4-question flow. If False, use 10-question flow.

        Updates:
            - JORGE_SIMPLE_MODE
            - SELLER_QUESTIONS
            - QUESTION_FIELD_MAPPING
            - HOT_QUESTIONS_REQUIRED
            - WARM_QUESTIONS_REQUIRED
        """
        cls.JORGE_SIMPLE_MODE = simple_mode

        if simple_mode:
            cls.SELLER_QUESTIONS = cls.SELLER_QUESTIONS_SIMPLE
            cls.QUESTION_FIELD_MAPPING = cls.QUESTION_FIELD_MAPPING_SIMPLE
            cls.HOT_QUESTIONS_REQUIRED = cls.HOT_QUESTIONS_REQUIRED_SIMPLE
            cls.WARM_QUESTIONS_REQUIRED = cls.WARM_QUESTIONS_REQUIRED_SIMPLE
            logger.info("Jorge Seller Bot: Switched to SIMPLE mode (4 questions)")
        else:
            cls.SELLER_QUESTIONS = cls.SELLER_QUESTIONS_FULL
            cls.QUESTION_FIELD_MAPPING = cls.QUESTION_FIELD_MAPPING_FULL
            cls.HOT_QUESTIONS_REQUIRED = cls.HOT_QUESTIONS_REQUIRED_FULL
            cls.WARM_QUESTIONS_REQUIRED = cls.WARM_QUESTIONS_REQUIRED_FULL
            logger.info("Jorge Seller Bot: Switched to FULL mode (10 questions)")

    # ========== ENVIRONMENT SPECIFIC SETTINGS ==========
    @classmethod
    def get_environment_config(cls) -> Dict:
        """Get environment-specific configuration"""
        # Check if simple mode is enabled (default: True)
        simple_mode = os.getenv("JORGE_SIMPLE_MODE", "true").lower() == "true"

        # Set questions and thresholds based on mode
        if simple_mode:
            questions = cls.SELLER_QUESTIONS_SIMPLE
            field_mapping = cls.QUESTION_FIELD_MAPPING_SIMPLE
            hot_questions = cls.HOT_QUESTIONS_REQUIRED_SIMPLE
            warm_questions = cls.WARM_QUESTIONS_REQUIRED_SIMPLE
        else:
            questions = cls.SELLER_QUESTIONS_FULL
            field_mapping = cls.QUESTION_FIELD_MAPPING_FULL
            hot_questions = cls.HOT_QUESTIONS_REQUIRED_FULL
            warm_questions = cls.WARM_QUESTIONS_REQUIRED_FULL

        return {
            "jorge_seller_mode": os.getenv("JORGE_SELLER_MODE", "false").lower() == "true",
            "simple_mode": simple_mode,
            "seller_questions": questions,
            "field_mapping": field_mapping,
            "friendly_approach": os.getenv("FRIENDLY_APPROACH", "true").lower() == "true",
            "max_sms_length": int(os.getenv("MAX_SMS_LENGTH", "160")),
            "hot_seller_threshold": float(os.getenv("HOT_SELLER_THRESHOLD", "1.0")),
            "warm_seller_threshold": float(os.getenv("WARM_SELLER_THRESHOLD", "0.75")),
            "active_followup_days": int(os.getenv("ACTIVE_FOLLOWUP_DAYS", "30")),
            "longterm_followup_interval": int(os.getenv("LONGTERM_FOLLOWUP_INTERVAL", "14")),
            "hot_seller_workflow_id": os.getenv("HOT_SELLER_WORKFLOW_ID"),
            "warm_seller_workflow_id": os.getenv("WARM_SELLER_WORKFLOW_ID"),
            # Temperature classification thresholds (configurable via environment)
            "hot_questions_required": int(os.getenv("HOT_QUESTIONS_REQUIRED", str(hot_questions))),
            "hot_quality_threshold": float(os.getenv("HOT_QUALITY_THRESHOLD", str(cls.HOT_QUALITY_THRESHOLD))),
            "warm_questions_required": int(os.getenv("WARM_QUESTIONS_REQUIRED", str(warm_questions))),
            "warm_quality_threshold": float(os.getenv("WARM_QUALITY_THRESHOLD", str(cls.WARM_QUALITY_THRESHOLD))),
        }

    # ========== VALIDATION RULES ==========
    @classmethod
    def validate_seller_response(cls, response: str) -> Dict:
        """Validate seller response quality"""
        response = response.strip()

        validation_result = {"is_valid": True, "quality_score": 1.0, "issues": [], "provide_support": False}

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
            message = re.sub(r"[^\w\s,.!?]", "", message)

        # Remove hyphens (Jorge requirement)
        if cls.NO_HYPHENS:
            message = message.replace("-", " ")

        # Remove robotic language patterns
        if cls.NO_ROBOTIC_LANGUAGE:
            robotic_patterns = [
                r"I'm here to help",
                r"Thank you for your time",
                r"I appreciate your response",
                r"Have a great day",
            ]
            for pattern in robotic_patterns:
                message = re.sub(pattern, "", message, flags=re.IGNORECASE)

        # Ensure SMS length compliance (reserve 30 chars for AI disclosure footer)
        effective_limit = cls.MAX_SMS_LENGTH - 30
        if len(message) > effective_limit:
            message = message[: effective_limit - 3] + "..."

        return message.strip()

    # ========== TEMPERATURE CLASSIFICATION ==========
    @classmethod
    def classify_seller_temperature(
        cls,
        questions_answered: int,
        timeline_acceptable: Optional[bool],
        response_quality: float,
        responsiveness: float,
    ) -> str:
        """Classify seller temperature based on Jorge's criteria"""

        # Hot seller criteria (Jorge's exact requirements)
        if (
            questions_answered == 4
            and timeline_acceptable is True
            and response_quality >= cls.HOT_SELLER_MIN_RESPONSE_QUALITY
            and responsiveness > 0.7
        ):
            return "hot"

        # Warm seller criteria
        elif questions_answered >= 3 and response_quality >= cls.WARM_SELLER_MIN_RESPONSE_QUALITY:
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

    # ========== MODE SWITCHING METHODS ==========
    @classmethod
    def get_questions_for_mode(cls, simple_mode: bool = True) -> Dict[int, str]:
        """Get seller questions based on mode"""
        return cls.SELLER_QUESTIONS_SIMPLE if simple_mode else cls.SELLER_QUESTIONS_FULL

    @classmethod
    def get_field_mapping_for_mode(cls, simple_mode: bool = True) -> Dict:
        """Get question field mapping based on mode"""
        return cls.QUESTION_FIELD_MAPPING_SIMPLE if simple_mode else cls.QUESTION_FIELD_MAPPING_FULL

    @classmethod
    def get_thresholds_for_mode(cls, simple_mode: bool = True) -> Dict:
        """Get temperature classification thresholds based on mode"""
        if simple_mode:
            return {
                "hot_questions_required": cls.HOT_QUESTIONS_REQUIRED_SIMPLE,
                "warm_questions_required": cls.WARM_QUESTIONS_REQUIRED_SIMPLE,
                "hot_threshold": cls.HOT_SELLER_THRESHOLD,
                "warm_threshold": cls.WARM_SELLER_THRESHOLD,
            }
        else:
            return {
                "hot_questions_required": cls.HOT_QUESTIONS_REQUIRED_FULL,
                "warm_questions_required": cls.WARM_QUESTIONS_REQUIRED_FULL,
                "hot_threshold": 1.0,  # 10/10 = 100%
                "warm_threshold": 0.70,  # 7/10 = 70%
            }

    @classmethod
    def get_success_metrics_for_mode(cls, simple_mode: bool = True) -> Dict:
        """Get success metrics based on mode"""
        return cls.SUCCESS_METRICS_SIMPLE if simple_mode else cls.SUCCESS_METRICS_FULL

    @classmethod
    def set_mode(cls, simple_mode: bool = True) -> None:
        """Switch between simple and full qualification modes"""
        cls.JORGE_SIMPLE_MODE = simple_mode
        cls.SELLER_QUESTIONS = cls.get_questions_for_mode(simple_mode)
        cls.QUESTION_FIELD_MAPPING = cls.get_field_mapping_for_mode(simple_mode)
        thresholds = cls.get_thresholds_for_mode(simple_mode)
        cls.HOT_QUESTIONS_REQUIRED = thresholds["hot_questions_required"]
        cls.WARM_QUESTIONS_REQUIRED = thresholds["warm_questions_required"]
        cls.SUCCESS_METRICS = cls.get_success_metrics_for_mode(simple_mode)
        logger.info(f"Jorge bot mode switched to: {'SIMPLE (4 questions)' if simple_mode else 'FULL (10 questions)'}")


# ========== ENVIRONMENT CONFIGURATION ==========


class JorgeEnvironmentSettings:
    """Environment-specific settings for Jorge's seller bot"""

    def __init__(self):
        """Initialize with environment variables"""
        self.jorge_seller_mode = os.getenv("JORGE_SELLER_MODE", "false").lower() == "true"
        self.jorge_buyer_mode = os.getenv("JORGE_BUYER_MODE", "false").lower() == "true"
        self.buyer_activation_tag = os.getenv("BUYER_LEAD_TAG", "Buyer-Lead")
        self.activation_tags = self._parse_list_env("ACTIVATION_TAGS", JorgeSellerConfig.ACTIVATION_TAGS)
        self.deactivation_tags = self._parse_list_env("DEACTIVATION_TAGS", JorgeSellerConfig.DEACTIVATION_TAGS)

        # Thresholds
        self.hot_seller_threshold = float(os.getenv("HOT_SELLER_THRESHOLD", "1.0"))
        self.warm_seller_threshold = float(os.getenv("WARM_SELLER_THRESHOLD", "0.75"))

        # Temperature classification thresholds (configurable)
        self.hot_questions_required = int(
            os.getenv("HOT_QUESTIONS_REQUIRED", str(JorgeSellerConfig.HOT_QUESTIONS_REQUIRED))
        )
        self.hot_quality_threshold = float(
            os.getenv("HOT_QUALITY_THRESHOLD", str(JorgeSellerConfig.HOT_QUALITY_THRESHOLD))
        )
        self.warm_questions_required = int(
            os.getenv("WARM_QUESTIONS_REQUIRED", str(JorgeSellerConfig.WARM_QUESTIONS_REQUIRED))
        )
        self.warm_quality_threshold = float(
            os.getenv("WARM_QUALITY_THRESHOLD", str(JorgeSellerConfig.WARM_QUALITY_THRESHOLD))
        )

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
        self.hot_buyer_workflow_id = os.getenv("HOT_BUYER_WORKFLOW_ID")
        self.warm_buyer_workflow_id = os.getenv("WARM_BUYER_WORKFLOW_ID")

        # Analytics
        self.analytics_enabled = os.getenv("JORGE_ANALYTICS_ENABLED", "true").lower() == "true"

        # Lead bot mode
        self.jorge_lead_mode = os.getenv("JORGE_LEAD_MODE", "true").lower() == "true"
        self.lead_activation_tag = os.getenv("LEAD_ACTIVATION_TAG", "Needs Qualifying")

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
    def JORGE_BUYER_MODE(self) -> bool:
        """Compatibility property for buyer mode routing"""
        return self.jorge_buyer_mode

    @property
    def BUYER_ACTIVATION_TAG(self) -> str:
        """Tag that activates buyer mode routing"""
        return self.buyer_activation_tag

    @property
    def ACTIVATION_TAGS(self) -> List[str]:
        """Get activation tags"""
        return self.activation_tags

    @property
    def DEACTIVATION_TAGS(self) -> List[str]:
        """Get deactivation tags"""
        return self.deactivation_tags

    @property
    def JORGE_LEAD_MODE(self) -> bool:
        """Compatibility property for lead mode routing"""
        return self.jorge_lead_mode

    @property
    def LEAD_ACTIVATION_TAG(self) -> str:
        """Tag that activates lead mode routing"""
        return self.lead_activation_tag

    def validate_ghl_integration(self) -> List[str]:
        """Return warnings for missing GHL configuration."""
        warnings = []
        if self.jorge_seller_mode:
            if not os.getenv("HOT_SELLER_WORKFLOW_ID"):
                warnings.append("HOT_SELLER_WORKFLOW_ID not set — hot seller workflows disabled")
            if not os.getenv("WARM_SELLER_WORKFLOW_ID"):
                warnings.append("WARM_SELLER_WORKFLOW_ID not set — warm seller workflows disabled")
        if self.jorge_buyer_mode:
            if not os.getenv("HOT_BUYER_WORKFLOW_ID"):
                warnings.append("HOT_BUYER_WORKFLOW_ID not set — hot buyer workflows disabled")
            if not os.getenv("WARM_BUYER_WORKFLOW_ID"):
                warnings.append("WARM_BUYER_WORKFLOW_ID not set — warm buyer workflows disabled")
        critical_fields = ["LEAD_SCORE", "SELLER_TEMPERATURE", "BUDGET"]
        for field in critical_fields:
            if not os.getenv(f"CUSTOM_FIELD_{field}"):
                warnings.append(f"CUSTOM_FIELD_{field} not set — field updates will use semantic names")
        return warnings


# ========== MARKET CONFIGURATION ==========


class JorgeMarketManager:
    """Market configuration manager for Jorge bots"""

    def __init__(self):
        """Initialize with default market (Rancho Cucamonga)"""
        self.current_market = os.getenv("JORGE_MARKET", "rancho_cucamonga")
        self._rancho_config = None

    def get_market_config(self):
        """Get configuration for current market"""
        if self.current_market == "rancho_cucamonga":
            return self._get_rancho_config()
        else:
            # Default to Rancho Cucamonga
            return self._get_rancho_config()

    def _get_rancho_config(self):
        """Get Rancho Cucamonga configuration"""
        if self._rancho_config is None:
            try:
                from .jorge_rancho_config import rancho_config

                self._rancho_config = rancho_config
            except ImportError:
                # Fallback configuration
                self._rancho_config = self._create_fallback_config()
        return self._rancho_config

    def _get_rancho_cucamonga_config(self):
        """Legacy Rancho Cucamonga configuration (maintained for compatibility)"""
        return {
            "market_name": "Rancho Cucamonga",
            "state": "CA",
            "price_ranges": {
                "entry_level": {"min": 500000, "max": 700000},
                "mid_market": {"min": 700000, "max": 1200000},
                "luxury": {"min": 1200000, "max": 7000000},
            },
            "regulatory": {"license_authority": "DRE", "state_regulations": "California Department of Real Estate"},
        }

    def _create_fallback_config(self):
        """Create fallback Rancho configuration if import fails"""
        return {
            "market_name": "Rancho Cucamonga",
            "state": "CA",
            "price_ranges": {
                "entry_level": {"min": 500000, "max": 700000},
                "mid_market": {"min": 700000, "max": 1200000},
                "luxury": {"min": 1200000, "max": 7000000},
            },
            "regulatory": {"license_authority": "DRE", "state_regulations": "California Department of Real Estate"},
        }


# ========== BUYER BUDGET CONFIGURATION ==========


@dataclass
class BuyerBudgetConfig:
    """Centralized configuration for buyer budget and qualification thresholds.

    This class externalizes all hardcoded budget ranges and thresholds from the
    Buyer Bot to support environment-based configuration overrides.
    """

    # ========== DEFAULT BUDGET RANGES ==========
    # Maps budget phrases to max/min values and buyer types
    DEFAULT_BUDGET_RANGES: Dict[str, Dict] = None

    def __post_init__(self):
        if self.DEFAULT_BUDGET_RANGES is None:
            self.DEFAULT_BUDGET_RANGES = {
                "under 300": {"budget_max": 700000, "buyer_type": "first_time"},
                "under 400": {"budget_max": 400000, "buyer_type": "entry_level"},
                "under 500": {"budget_max": 700000, "buyer_type": "mid_market"},
                "under 600": {"budget_max": 600000, "buyer_type": "mid_market"},
                "under 700": {"budget_max": 700000, "buyer_type": "move_up"},
                "under 800": {"budget_max": 800000, "buyer_type": "move_up"},
                "under 1m": {"budget_max": 1200000, "buyer_type": "luxury"},
                "under 1 million": {"budget_max": 1200000, "buyer_type": "luxury"},
                "over 1m": {"budget_min": 1200000, "buyer_type": "luxury_plus"},
            }

    # ========== FINANCING THRESHOLDS ==========
    # Score thresholds for financing readiness assessment
    FINANCING_PRE_APPROVED_THRESHOLD: int = 75
    FINANCING_NEEDS_APPROVAL_THRESHOLD: int = 50
    FINANCING_CASH_BUDGET_THRESHOLD: int = 70

    # Budget amount thresholds for parsing
    BUDGET_AMOUNT_K_THRESHOLD: int = 1000
    BUDGET_SINGLE_AMOUNT_MIN_FACTOR: float = 0.8

    # ========== URGENCY THRESHOLDS ==========
    # Score thresholds for buyer urgency classification
    URGENCY_IMMEDIATE_THRESHOLD: int = 75
    URGENCY_3_MONTHS_THRESHOLD: int = 50
    URGENCY_6_MONTHS_THRESHOLD: int = 30

    # ========== QUALIFICATION THRESHOLDS ==========
    # Score thresholds for buyer qualification levels
    QUALIFICATION_HOT_THRESHOLD: int = 75
    QUALIFICATION_WARM_THRESHOLD: int = 50
    QUALIFICATION_LUKEWARM_THRESHOLD: int = 30

    # Follow-up hours for each qualification level
    QUALIFICATION_HOT_FOLLOWUP_HOURS: int = 2
    QUALIFICATION_WARM_FOLLOWUP_HOURS: int = 24
    QUALIFICATION_LUKEWARM_FOLLOWUP_HOURS: int = 72
    QUALIFICATION_COLD_FOLLOWUP_HOURS: int = 168

    # ========== ROUTING THRESHOLDS ==========
    # Score thresholds for routing decisions
    ROUTING_QUALIFIED_THRESHOLD: int = 50
    ROUTING_SCHEDULE_THRESHOLD: int = 30

    # ========== ENVIRONMENT OVERRIDES ==========

    @classmethod
    def from_environment(cls) -> "BuyerBudgetConfig":
        """Create BuyerBudgetConfig instance with environment variable overrides.

        Environment variables:
        - BUYER_BUDGET_RANGES: JSON-encoded budget ranges dict
        - BUYER_FINANCING_PRE_APPROVED_THRESHOLD: int (default 75)
        - BUYER_FINANCING_NEEDS_APPROVAL_THRESHOLD: int (default 50)
        - BUYER_FINANCING_CASH_BUDGET_THRESHOLD: int (default 70)
        - BUYER_URGENCY_IMMEDIATE_THRESHOLD: int (default 75)
        - BUYER_URGENCY_3_MONTHS_THRESHOLD: int (default 50)
        - BUYER_URGENCY_6_MONTHS_THRESHOLD: int (default 30)
        - BUYER_QUALIFICATION_HOT_THRESHOLD: int (default 75)
        - BUYER_QUALIFICATION_WARM_THRESHOLD: int (default 50)
        - BUYER_QUALIFICATION_LUKEWARM_THRESHOLD: int (default 30)
        - BUYER_ROUTING_QUALIFIED_THRESHOLD: int (default 50)
        - BUYER_ROUTING_SCHEDULE_THRESHOLD: int (default 30)
        """
        import json

        # Parse budget ranges from environment if provided
        budget_ranges = None
        budget_ranges_env = os.getenv("BUYER_BUDGET_RANGES")
        if budget_ranges_env:
            try:
                budget_ranges = json.loads(budget_ranges_env)
            except json.JSONDecodeError:
                logger.warning("Invalid BUYER_BUDGET_RANGES format, using defaults")

        return cls(
            DEFAULT_BUDGET_RANGES=budget_ranges,
            FINANCING_PRE_APPROVED_THRESHOLD=int(os.getenv("BUYER_FINANCING_PRE_APPROVED_THRESHOLD", "75")),
            FINANCING_NEEDS_APPROVAL_THRESHOLD=int(os.getenv("BUYER_FINANCING_NEEDS_APPROVAL_THRESHOLD", "50")),
            FINANCING_CASH_BUDGET_THRESHOLD=int(os.getenv("BUYER_FINANCING_CASH_BUDGET_THRESHOLD", "70")),
            URGENCY_IMMEDIATE_THRESHOLD=int(os.getenv("BUYER_URGENCY_IMMEDIATE_THRESHOLD", "75")),
            URGENCY_3_MONTHS_THRESHOLD=int(os.getenv("BUYER_URGENCY_3_MONTHS_THRESHOLD", "50")),
            URGENCY_6_MONTHS_THRESHOLD=int(os.getenv("BUYER_URGENCY_6_MONTHS_THRESHOLD", "30")),
            QUALIFICATION_HOT_THRESHOLD=int(os.getenv("BUYER_QUALIFICATION_HOT_THRESHOLD", "75")),
            QUALIFICATION_WARM_THRESHOLD=int(os.getenv("BUYER_QUALIFICATION_WARM_THRESHOLD", "50")),
            QUALIFICATION_LUKEWARM_THRESHOLD=int(os.getenv("BUYER_QUALIFICATION_LUKEWARM_THRESHOLD", "30")),
            ROUTING_QUALIFIED_THRESHOLD=int(os.getenv("BUYER_ROUTING_QUALIFIED_THRESHOLD", "50")),
            ROUTING_SCHEDULE_THRESHOLD=int(os.getenv("BUYER_ROUTING_SCHEDULE_THRESHOLD", "30")),
        )

    # ========== HELPER METHODS ==========

    def get_budget_range(self, budget_phrase: str) -> Optional[Dict]:
        """Get budget range configuration for a given budget phrase."""
        return self.DEFAULT_BUDGET_RANGES.get(budget_phrase.lower())

    def get_urgency_level(self, urgency_score: int) -> str:
        """Get urgency level based on score."""
        if urgency_score >= self.URGENCY_IMMEDIATE_THRESHOLD:
            return "immediate"
        elif urgency_score >= self.URGENCY_3_MONTHS_THRESHOLD:
            return "3_months"
        elif urgency_score >= self.URGENCY_6_MONTHS_THRESHOLD:
            return "6_months"
        return "browsing"

    def get_qualification_level(self, score: int) -> str:
        """Get qualification level based on score."""
        if score >= self.QUALIFICATION_HOT_THRESHOLD:
            return "hot"
        elif score >= self.QUALIFICATION_WARM_THRESHOLD:
            return "warm"
        elif score >= self.QUALIFICATION_LUKEWARM_THRESHOLD:
            return "lukewarm"
        return "cold"

    def get_next_action(self, qualification_score: int) -> tuple:
        """Get next action and follow-up hours based on qualification score."""
        if qualification_score >= self.QUALIFICATION_HOT_THRESHOLD:
            return ("schedule_property_tour", self.QUALIFICATION_HOT_FOLLOWUP_HOURS)
        elif qualification_score >= self.QUALIFICATION_WARM_THRESHOLD:
            return ("send_property_updates", self.QUALIFICATION_WARM_FOLLOWUP_HOURS)
        elif qualification_score >= self.QUALIFICATION_LUKEWARM_THRESHOLD:
            return ("market_education", self.QUALIFICATION_LUKEWARM_FOLLOWUP_HOURS)
        return ("re_qualification", self.QUALIFICATION_COLD_FOLLOWUP_HOURS)

    def get_routing_action(self, qualification_score: int, next_action: str = "respond") -> str:
        """Get routing action based on qualification score."""
        if qualification_score >= self.ROUTING_SCHEDULE_THRESHOLD:
            return "schedule"
        # Default to "respond" so generate_buyer_response always runs and asks
        # qualifying questions. Only "schedule" is a meaningful early-exit; "end"
        # (which routes to LangGraph END) would skip response generation entirely.
        return "respond"


# ========== SELLER BOT CONFIGURATION ==========


@dataclass
class SellerBotConfig:
    """Centralized configuration for seller bot feature flags and thresholds.

    Follows BuyerBudgetConfig pattern with environment-based overrides.
    """

    # Feature flags
    enable_cma_generation: bool = True
    enable_market_intelligence: bool = True
    enable_listing_prep: bool = True
    enable_valuation_defense: bool = True
    enable_seller_intent_decoder: bool = True

    # CMA thresholds
    cma_confidence_threshold: float = 70.0
    listing_prep_qualification_threshold: float = 0.75

    # Temperature thresholds for seller FRS
    hot_frs_threshold: float = 75.0
    warm_frs_threshold: float = 50.0

    @classmethod
    def from_environment(cls) -> "SellerBotConfig":
        """Create SellerBotConfig with environment variable overrides."""
        return cls(
            enable_cma_generation=os.getenv("SELLER_ENABLE_CMA", "true").lower() == "true",
            enable_market_intelligence=os.getenv("SELLER_ENABLE_MARKET_INTEL", "true").lower() == "true",
            enable_listing_prep=os.getenv("SELLER_ENABLE_LISTING_PREP", "true").lower() == "true",
            enable_valuation_defense=os.getenv("SELLER_ENABLE_VALUATION_DEFENSE", "true").lower() == "true",
            enable_seller_intent_decoder=os.getenv("SELLER_ENABLE_INTENT_DECODER", "true").lower() == "true",
            cma_confidence_threshold=float(os.getenv("SELLER_CMA_CONFIDENCE_THRESHOLD", "70.0")),
            listing_prep_qualification_threshold=float(os.getenv("SELLER_LISTING_PREP_THRESHOLD", "0.75")),
            hot_frs_threshold=float(os.getenv("SELLER_HOT_FRS_THRESHOLD", "75.0")),
            warm_frs_threshold=float(os.getenv("SELLER_WARM_FRS_THRESHOLD", "50.0")),
        )


# ========== EXPORTS ==========

# Create global settings instance
settings = JorgeEnvironmentSettings()
for _warning in settings.validate_ghl_integration():
    logger.warning(f"GHL Config: {_warning}")
market_manager = JorgeMarketManager()

# Export commonly used values
JORGE_SELLER_MODE = settings.JORGE_SELLER_MODE
JORGE_LEAD_MODE = settings.JORGE_LEAD_MODE
ACTIVATION_TAGS = settings.ACTIVATION_TAGS
DEACTIVATION_TAGS = settings.DEACTIVATION_TAGS
CURRENT_MARKET = market_manager.current_market
MARKET_CONFIG = market_manager.get_market_config()

__all__ = [
    "JorgeSellerConfig",
    "JorgeConfig",
    "JorgeEnvironmentSettings",
    "JorgeMarketManager",
    "BuyerBudgetConfig",
    "SellerBotConfig",
    "settings",
    "market_manager",
    "JORGE_SELLER_MODE",
    "JORGE_LEAD_MODE",
    "ACTIVATION_TAGS",
    "DEACTIVATION_TAGS",
    "CURRENT_MARKET",
    "MARKET_CONFIG",
]

# Backward-compatible alias used by prediction, compliance, intelligence modules
JorgeConfig = JorgeSellerConfig
