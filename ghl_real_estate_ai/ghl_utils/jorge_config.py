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
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class JorgeSellerConfig:
    """Central configuration for Jorge's seller bot"""

    # ========== SIMPLE MODE ==========
    # Simple mode: disables enterprise features (investor arbitrage, loss aversion,
    # psychology profiling, Voss negotiation, drift detection, market insights)
    # When True, bot follows strict 4-question flow only
    JORGE_SIMPLE_MODE: bool = True

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

    # ========== EXPANDED SELLER INTAKE (EPIC B) ==========
    # Legacy 4-question fields kept for backwards compatibility and temperature logic.
    CORE_QUESTION_FIELDS = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]

    # Full seller intake progression (expanded qualification contract).
    SELLER_INTAKE_FIELD_SEQUENCE = [
        "property_address",
        "property_type",
        "property_condition",
        "timeline_days",
        "motivation",
        "asking_price",
        "mortgage_balance",
        "repair_estimate",
        "prior_listing_history",
        "decision_maker_confirmed",
        "best_contact_method",
        "availability_windows",
    ]

    # Minimum canonical fields required for a seller to be marked as qualified in GHL.
    CANONICAL_REQUIRED_FIELDS = [
        "seller_temperature",
        "seller_motivation",
        "property_condition",
        "timeline_days",
        "asking_price",
        "ai_valuation_price",
        "lead_value_tier",
        "qualification_complete",
    ]

    # Recommended but non-blocking fields.
    CANONICAL_PREFERRED_FIELDS = [
        "mortgage_balance",
        "repair_estimate",
        "decision_maker_confirmed",
        "best_contact_method",
        "availability_windows",
        "prior_listing_history",
    ]

    # Runtime intake completion gate used before final qualification.
    INTAKE_COMPLETION_REQUIRED_FIELDS = ["property_condition", "timeline_days", "motivation", "asking_price"]

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

    # WS-4 lifecycle cadence policy
    FOLLOWUP_CADENCE_DAYS = {
        "hot": 1,   # Daily
        "warm": 7,  # Weekly
        "cold": 30,  # Monthly
    }

    # Retry ceilings by lifecycle stage
    FOLLOWUP_RETRY_CEILING = {
        "hot": 14,
        "warm": 12,
        "cold": 6,
    }

    # De-escalation after repeated non-response
    FOLLOWUP_DEESCALATION_STREAK = {
        "hot": 3,   # HOT -> WARM
        "warm": 4,  # WARM -> COLD
    }

    # Escalation windows
    FOLLOWUP_ESCALATION_ATTEMPTS = 3
    FOLLOWUP_HIGH_VALUE_ESCALATION_ATTEMPTS = 2
    FOLLOWUP_SUPPRESSION_TAGS = ["AI-Off", "Do-Not-Contact", "Stop-Bot"]

    # ========== GHL INTEGRATION ==========
    # Workflow IDs for different seller temperatures
    HOT_SELLER_WORKFLOW_ID = ""  # Set via HOT_SELLER_WORKFLOW_ID env var
    WARM_SELLER_WORKFLOW_ID = ""  # Set via WARM_SELLER_WORKFLOW_ID env var
    AGENT_NOTIFICATION_WORKFLOW = ""  # Set via NOTIFY_AGENT_WORKFLOW_ID env var

    # Custom field mapping for GHL
    CUSTOM_FIELDS = {
        "seller_temperature": "",
        "seller_motivation": "",
        "property_address": "",
        "property_type": "",
        "relocation_destination": "",
        "timeline_urgency": "",
        "timeline_days": "",
        "property_condition": "",
        "price_expectation": "",
        "asking_price": "",
        "mortgage_balance": "",
        "repair_estimate": "",
        "last_bot_interaction": "",
        "qualification_complete": "",
        "decision_maker_confirmed": "",
        "best_contact_method": "",
        "availability_windows": "",
        "prior_listing_history": "",
        "field_provenance": "",
        "questions_answered": "",
        "qualification_score": "",
        "expected_roi": "",
        "lead_value_tier": "",
        "ai_valuation_price": "",
        "detected_persona": "",
        "psychology_type": "",
        "urgency_level": "",
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

    # ========== JORGE SELLER QUESTIONS ==========
    # Expanded qualification flow, with first four preserved in original order.
    SELLER_QUESTIONS = {
        1: "What's got you considering wanting to sell, where would you move to?",
        2: "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
        3: "How would you describe your home, would you say it's move-in ready or would it need some work?",
        4: "What price would incentivize you to sell?",
        5: "What is the property address?",
        6: "What type of property is it: single family, condo, townhome, or multi family?",
        7: "Do you have an estimated mortgage balance or any liens to account for?",
        8: "Do you have a rough repair estimate or expected renovation budget?",
        9: "Has the property been listed before, and if so what happened?",
        10: "Are all decision makers aligned on selling?",
        11: "What is your best contact method: SMS, call, or email?",
        12: "What days and times are best for a short consultation?",
    }

    # Question field mapping for data extraction
    QUESTION_FIELD_MAPPING = {
        1: {"field": "motivation", "secondary": "relocation_destination"},
        2: {"field": "timeline_acceptable", "secondary": "timeline_urgency"},
        3: {"field": "property_condition", "secondary": "repair_estimate"},
        4: {"field": "price_expectation", "secondary": "price_flexibility"},
        5: {"field": "property_address", "secondary": None},
        6: {"field": "property_type", "secondary": None},
        7: {"field": "mortgage_balance", "secondary": "lien_status"},
        8: {"field": "repair_estimate", "secondary": None},
        9: {"field": "prior_listing_history", "secondary": None},
        10: {"field": "decision_maker_confirmed", "secondary": None},
        11: {"field": "best_contact_method", "secondary": None},
        12: {"field": "availability_windows", "secondary": None},
    }

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

    # ========== HOT SELLER HANDOFF MESSAGES ==========
    HOT_SELLER_HANDOFF_MESSAGES = [
        "Based on what you've shared, it sounds like we can really help you achieve your goals. I'd love to schedule a time to discuss your options in detail. What would work better for you, morning or afternoon?",
        "Perfect. You're a great fit for our program. I'm connecting you with our team now. Are mornings or afternoons better for a quick call?",
        "You answered all my questions, which tells me you're serious. Let me get you scheduled with our team today. Morning or afternoon?",
    ]

    # ========== BUYER BOT SETTINGS ==========
    # Buyer follow-up schedule (mirrors seller pattern per spec)
    BUYER_FOLLOWUP_SCHEDULE = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]
    BUYER_LONGTERM_INTERVAL = 14
    BUYER_TEMPERATURE_TAGS = {"hot": "Hot-Buyer", "warm": "Warm-Buyer", "cold": "Cold-Buyer"}

    # ========== ANALYTICS & MONITORING ==========
    # Success metrics and KPIs
    SUCCESS_METRICS = {
        "qualification_completion_rate": 0.60,  # 60% complete all 4 questions
        "hot_lead_conversion_rate": 0.15,  # 15% become hot leads
        "agent_handoff_rate": 0.20,  # 20% advance to agent calls
        "followup_engagement_rate": 0.30,  # 30% engage with follow-ups
        "opt_out_rate": 0.05,  # <5% request no contact
    }

    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        "webhook_response_time": 2.0,  # Max 2 seconds
        "message_delivery_rate": 0.99,  # Min 99%
        "classification_accuracy": 0.90,  # Min 90% accuracy
        "sms_compliance_rate": 1.0,  # 100% SMS compliant
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
            "fail_on_missing_canonical_mapping": cls.should_fail_on_missing_canonical_mapping(),
            "followup_cadence_hot_days": int(
                os.getenv("FOLLOWUP_CADENCE_HOT_DAYS", str(cls.FOLLOWUP_CADENCE_DAYS["hot"]))
            ),
            "followup_cadence_warm_days": int(
                os.getenv("FOLLOWUP_CADENCE_WARM_DAYS", str(cls.FOLLOWUP_CADENCE_DAYS["warm"]))
            ),
            "followup_cadence_cold_days": int(
                os.getenv("FOLLOWUP_CADENCE_COLD_DAYS", str(cls.FOLLOWUP_CADENCE_DAYS["cold"]))
            ),
            "followup_retry_hot_ceiling": int(
                os.getenv("FOLLOWUP_RETRY_HOT_CEILING", str(cls.FOLLOWUP_RETRY_CEILING["hot"]))
            ),
            "followup_retry_warm_ceiling": int(
                os.getenv("FOLLOWUP_RETRY_WARM_CEILING", str(cls.FOLLOWUP_RETRY_CEILING["warm"]))
            ),
            "followup_retry_cold_ceiling": int(
                os.getenv("FOLLOWUP_RETRY_COLD_CEILING", str(cls.FOLLOWUP_RETRY_CEILING["cold"]))
            ),
            "followup_escalation_attempts": int(
                os.getenv("FOLLOWUP_ESCALATION_ATTEMPTS", str(cls.FOLLOWUP_ESCALATION_ATTEMPTS))
            ),
            "followup_high_value_escalation_attempts": int(
                os.getenv(
                    "FOLLOWUP_HIGH_VALUE_ESCALATION_ATTEMPTS",
                    str(cls.FOLLOWUP_HIGH_VALUE_ESCALATION_ATTEMPTS),
                )
            ),
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

        # Ensure SMS length compliance
        if len(message) > cls.MAX_SMS_LENGTH:
            message = message[: cls.MAX_SMS_LENGTH - 3] + "..."

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

    @staticmethod
    def _is_empty_value(value: Any) -> bool:
        """Return True for values that should not overwrite persisted seller state."""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip().lower() in {"", "unknown", "null", "n/a", "na"}
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) == 0
        return False

    @classmethod
    def get_canonical_data_contract(cls) -> Dict[str, List[str]]:
        """Canonical seller schema buckets used by runtime and validation tooling."""
        return {
            "required": list(cls.CANONICAL_REQUIRED_FIELDS),
            "preferred": list(cls.CANONICAL_PREFERRED_FIELDS),
        }

    @classmethod
    def should_fail_on_missing_canonical_mapping(cls) -> bool:
        """Whether missing required canonical->GHL mappings should hard-stop seller processing."""
        return os.getenv("FAIL_ON_MISSING_CANONICAL_MAPPING", "false").strip().lower() == "true"

    @classmethod
    def get_required_qualification_inputs(cls) -> List[str]:
        """Canonical fields required before qualification state can be computed."""
        return [field for field in cls.CANONICAL_REQUIRED_FIELDS if field != "qualification_complete"]

    @classmethod
    def is_intake_complete(cls, seller_data: Dict[str, Any]) -> bool:
        """Runtime gate for expanded qualification progression completion."""
        return all(not cls._is_empty_value(seller_data.get(field)) for field in cls.INTAKE_COMPLETION_REQUIRED_FIELDS)

    @classmethod
    def has_required_canonical_fields(cls, seller_data: Dict[str, Any]) -> bool:
        """True when required canonical inputs (excluding qualification flag) are all populated."""
        return all(
            not cls._is_empty_value(seller_data.get(field))
            for field in cls.get_required_qualification_inputs()
        )

    @classmethod
    def is_qualified_seller_record(cls, seller_data: Dict[str, Any]) -> bool:
        """Final qualification gate for canonical GHL record completeness."""
        return cls.has_required_canonical_fields(seller_data) and seller_data.get("qualification_complete") is True

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

    @classmethod
    def get_followup_lifecycle_policy(cls) -> Dict[str, Any]:
        """Return WS-4 lifecycle follow-up policy with env overrides."""

        def _safe_int(env_key: str, default: int) -> int:
            raw = os.getenv(env_key, str(default)).strip()
            try:
                value = int(raw)
                return max(1, value)
            except ValueError:
                logger.warning("Invalid %s=%s, falling back to %s", env_key, raw, default)
                return default

        cadence_days = {
            "hot": _safe_int("FOLLOWUP_CADENCE_HOT_DAYS", cls.FOLLOWUP_CADENCE_DAYS["hot"]),
            "warm": _safe_int("FOLLOWUP_CADENCE_WARM_DAYS", cls.FOLLOWUP_CADENCE_DAYS["warm"]),
            "cold": _safe_int("FOLLOWUP_CADENCE_COLD_DAYS", cls.FOLLOWUP_CADENCE_DAYS["cold"]),
        }
        retry_ceiling = {
            "hot": _safe_int("FOLLOWUP_RETRY_HOT_CEILING", cls.FOLLOWUP_RETRY_CEILING["hot"]),
            "warm": _safe_int("FOLLOWUP_RETRY_WARM_CEILING", cls.FOLLOWUP_RETRY_CEILING["warm"]),
            "cold": _safe_int("FOLLOWUP_RETRY_COLD_CEILING", cls.FOLLOWUP_RETRY_CEILING["cold"]),
        }
        deescalation_streak = {
            "hot": _safe_int("FOLLOWUP_DEESCALATE_HOT_STREAK", cls.FOLLOWUP_DEESCALATION_STREAK["hot"]),
            "warm": _safe_int("FOLLOWUP_DEESCALATE_WARM_STREAK", cls.FOLLOWUP_DEESCALATION_STREAK["warm"]),
        }
        suppression_tags_env = os.getenv("FOLLOWUP_SUPPRESSION_TAGS", "").strip()
        suppression_tags = (
            [tag.strip() for tag in suppression_tags_env.split(",") if tag.strip()]
            if suppression_tags_env
            else list(cls.FOLLOWUP_SUPPRESSION_TAGS)
        )

        return {
            "cadence_days": cadence_days,
            "retry_ceiling": retry_ceiling,
            "deescalation_streak": deescalation_streak,
            "escalation_attempts": _safe_int("FOLLOWUP_ESCALATION_ATTEMPTS", cls.FOLLOWUP_ESCALATION_ATTEMPTS),
            "high_value_escalation_attempts": _safe_int(
                "FOLLOWUP_HIGH_VALUE_ESCALATION_ATTEMPTS",
                cls.FOLLOWUP_HIGH_VALUE_ESCALATION_ATTEMPTS,
            ),
            "suppression_tags": suppression_tags,
        }

    # ========== GHL INTEGRATION HELPERS ==========
    @classmethod
    def get_ghl_custom_field_id(cls, field_name: str) -> Optional[str]:
        """Get GHL custom field ID for seller data field"""
        env_var = f"CUSTOM_FIELD_{field_name.upper()}"
        return os.getenv(env_var) or cls.CUSTOM_FIELDS.get(field_name)

    @classmethod
    def validate_custom_field_mapping(cls, field_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate that canonical fields map to concrete GHL custom field IDs.

        Returns a payload with missing + resolved mappings for operational checks.
        """
        fields_to_check = field_names or list(cls.CANONICAL_REQUIRED_FIELDS + cls.CANONICAL_PREFERRED_FIELDS)
        missing_fields: List[str] = []
        resolved_fields: Dict[str, str] = {}

        for field_name in fields_to_check:
            mapped_id = cls.get_ghl_custom_field_id(field_name)
            if cls._is_empty_value(mapped_id):
                missing_fields.append(field_name)
            else:
                resolved_fields[field_name] = str(mapped_id)

        return {
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "resolved_fields": resolved_fields,
        }

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
        self.followup_cadence_hot_days = int(
            os.getenv("FOLLOWUP_CADENCE_HOT_DAYS", str(JorgeSellerConfig.FOLLOWUP_CADENCE_DAYS["hot"]))
        )
        self.followup_cadence_warm_days = int(
            os.getenv("FOLLOWUP_CADENCE_WARM_DAYS", str(JorgeSellerConfig.FOLLOWUP_CADENCE_DAYS["warm"]))
        )
        self.followup_cadence_cold_days = int(
            os.getenv("FOLLOWUP_CADENCE_COLD_DAYS", str(JorgeSellerConfig.FOLLOWUP_CADENCE_DAYS["cold"]))
        )
        self.followup_retry_hot_ceiling = int(
            os.getenv("FOLLOWUP_RETRY_HOT_CEILING", str(JorgeSellerConfig.FOLLOWUP_RETRY_CEILING["hot"]))
        )
        self.followup_retry_warm_ceiling = int(
            os.getenv("FOLLOWUP_RETRY_WARM_CEILING", str(JorgeSellerConfig.FOLLOWUP_RETRY_CEILING["warm"]))
        )
        self.followup_retry_cold_ceiling = int(
            os.getenv("FOLLOWUP_RETRY_COLD_CEILING", str(JorgeSellerConfig.FOLLOWUP_RETRY_CEILING["cold"]))
        )

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
        self.fail_on_missing_canonical_mapping = (
            os.getenv("FAIL_ON_MISSING_CANONICAL_MAPPING", "false").strip().lower() == "true"
        )

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

    @property
    def FAIL_ON_MISSING_CANONICAL_MAPPING(self) -> bool:
        """Compatibility property for mapping gate behavior."""
        return self.fail_on_missing_canonical_mapping

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
        if next_action == "respond" and qualification_score >= self.ROUTING_QUALIFIED_THRESHOLD:
            return "respond"
        elif qualification_score >= self.ROUTING_SCHEDULE_THRESHOLD:
            return "schedule"
        return "end"


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
            listing_prep_qualification_threshold=float(
                os.getenv("SELLER_LISTING_PREP_THRESHOLD", "0.75")
            ),
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
