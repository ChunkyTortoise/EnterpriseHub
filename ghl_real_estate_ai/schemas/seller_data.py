"""
Jorge's Seller Data Schema

This module defines the data structures for Jorge's 4-question seller qualification process.
Provides type safety, validation, and clear data contracts for the seller bot engine.

Author: Claude Code Assistant
Created: 2026-01-19
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TimelineUrgency(Enum):
    """Seller timeline urgency classifications"""

    URGENT_30_45_DAYS = "30-45 days"  # Jorge's target timeline
    FLEXIBLE = "flexible"  # Somewhat open timeline
    LONG_TERM = "long-term"  # No urgency (6+ months)
    UNKNOWN = "unknown"  # No timeline information


class PropertyCondition(Enum):
    """Property condition classifications for Jorge's question 3"""

    MOVE_IN_READY = "move-in ready"  # Perfect condition
    NEEDS_WORK = "needs work"  # Some repairs needed
    MAJOR_REPAIRS = "major repairs"  # Significant work required
    UNKNOWN = "unknown"  # Condition not specified


class MotivationType(Enum):
    """Seller motivation classifications"""

    RELOCATION = "relocation"  # Moving to another area
    DOWNSIZING = "downsizing"  # Smaller home needed
    UPSIZING = "upsizing"  # Larger home needed
    FINANCIAL = "financial"  # Need cash/debt relief
    DIVORCE = "divorce"  # Divorce-related sale
    INHERITED = "inherited"  # Inherited property
    INVESTMENT = "investment"  # Investor liquidating
    OTHER = "other"  # Other motivation
    UNKNOWN = "unknown"  # Not specified


class PriceFlexibility(Enum):
    """Price expectation flexibility"""

    FIRM = "firm"  # Non-negotiable price
    NEGOTIABLE = "negotiable"  # Open to negotiation
    FLEXIBLE = "flexible"  # Very flexible on price
    UNKNOWN = "unknown"  # Price flexibility not known


@dataclass
class SellerProfile:
    """
    Complete seller profile based on Jorge's 4-question qualification.

    Maps directly to Jorge's questions:
    1. Motivation & Relocation destination
    2. Timeline acceptance (30-45 days)
    3. Property condition assessment
    4. Price expectations
    """

    # Question 1: What's making you think about selling, and where would you move to?
    motivation: Optional[MotivationType] = None
    motivation_details: Optional[str] = None  # Free-form details about motivation
    relocation_destination: Optional[str] = None  # Where they want to move

    # Question 2: If our team sold your home within the next 30 to 45 days, would that work for you?
    timeline_urgency: Optional[TimelineUrgency] = None
    timeline_acceptable: Optional[bool] = None  # True if 30-45 days is okay
    timeline_details: Optional[str] = None  # Additional timeline info

    # Question 3: How would you describe your home, move-in ready or needs work?
    property_condition: Optional[PropertyCondition] = None
    repair_estimate: Optional[str] = None  # Estimated repair costs/needs
    condition_details: Optional[str] = None  # Additional condition info

    # Question 4: What price would make you feel good about selling?
    price_expectation: Optional[int] = None  # Dollar amount expected
    price_flexibility: Optional[PriceFlexibility] = None
    price_details: Optional[str] = None  # Additional price context

    # Quality and Progress Metrics
    questions_answered: int = 0  # Number of Jorge's 4 questions answered (0-4)
    response_quality: float = 0.0  # Quality of responses (0.0-1.0)
    responsiveness: float = 0.0  # How responsive to messages (0.0-1.0)

    # Conversation Tracking
    conversation_started_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None
    total_interactions: int = 0

    # Temperature and Classification
    seller_temperature: str = "cold"  # hot, warm, cold
    qualification_score: float = 0.0  # Overall qualification score

    # Follow-up and Scheduling
    last_followup_sent: Optional[datetime] = None
    followup_count: int = 0
    followup_phase: str = "active"  # active (2-3 days) or longterm (14 days)

    # Additional Context
    lead_source: Optional[str] = None
    ghl_contact_id: Optional[str] = None
    ghl_location_id: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage of Jorge's 4 questions"""
        return (self.questions_answered / 4) * 100

    @property
    def is_qualified(self) -> bool:
        """Check if seller meets basic qualification criteria"""
        return self.questions_answered >= 3 and self.response_quality > 0.5

    @property
    def is_hot_seller(self) -> bool:
        """Check if seller meets Jorge's hot seller criteria"""
        return (
            self.questions_answered == 4
            and self.timeline_acceptable is True
            and self.response_quality > 0.7
            and self.seller_temperature == "hot"
        )

    @property
    def next_question_needed(self) -> Optional[str]:
        """Get the next question that needs to be asked"""
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import SellerQuestions

        question_data = {
            "motivation": self.motivation is not None,
            "timeline_acceptable": self.timeline_acceptable is not None,
            "property_condition": self.property_condition is not None,
            "price_expectation": self.price_expectation is not None,
        }

        return SellerQuestions.get_next_question(question_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "motivation": self.motivation.value if self.motivation else None,
            "motivation_details": self.motivation_details,
            "relocation_destination": self.relocation_destination,
            "timeline_urgency": self.timeline_urgency.value if self.timeline_urgency else None,
            "timeline_acceptable": self.timeline_acceptable,
            "timeline_details": self.timeline_details,
            "property_condition": self.property_condition.value if self.property_condition else None,
            "repair_estimate": self.repair_estimate,
            "condition_details": self.condition_details,
            "price_expectation": self.price_expectation,
            "price_flexibility": self.price_flexibility.value if self.price_flexibility else None,
            "price_details": self.price_details,
            "questions_answered": self.questions_answered,
            "response_quality": self.response_quality,
            "responsiveness": self.responsiveness,
            "seller_temperature": self.seller_temperature,
            "qualification_score": self.qualification_score,
            "followup_count": self.followup_count,
            "followup_phase": self.followup_phase,
            "total_interactions": self.total_interactions,
            "custom_fields": self.custom_fields,
            # Convert datetime to ISO string
            "conversation_started_at": self.conversation_started_at.isoformat()
            if self.conversation_started_at
            else None,
            "last_interaction_at": self.last_interaction_at.isoformat() if self.last_interaction_at else None,
            "last_followup_sent": self.last_followup_sent.isoformat() if self.last_followup_sent else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SellerProfile":
        """Create SellerProfile from dictionary data"""

        # Handle enum conversions
        motivation = None
        if data.get("motivation"):
            try:
                motivation = MotivationType(data["motivation"])
            except ValueError:
                motivation = MotivationType.UNKNOWN

        timeline_urgency = None
        if data.get("timeline_urgency"):
            try:
                timeline_urgency = TimelineUrgency(data["timeline_urgency"])
            except ValueError:
                timeline_urgency = TimelineUrgency.UNKNOWN

        property_condition = None
        if data.get("property_condition"):
            try:
                property_condition = PropertyCondition(data["property_condition"])
            except ValueError:
                property_condition = PropertyCondition.UNKNOWN

        price_flexibility = None
        if data.get("price_flexibility"):
            try:
                price_flexibility = PriceFlexibility(data["price_flexibility"])
            except ValueError:
                price_flexibility = PriceFlexibility.UNKNOWN

        # Handle datetime conversions
        conversation_started_at = None
        if data.get("conversation_started_at"):
            try:
                conversation_started_at = datetime.fromisoformat(data["conversation_started_at"])
            except (ValueError, TypeError):
                pass

        last_interaction_at = None
        if data.get("last_interaction_at"):
            try:
                last_interaction_at = datetime.fromisoformat(data["last_interaction_at"])
            except (ValueError, TypeError):
                pass

        last_followup_sent = None
        if data.get("last_followup_sent"):
            try:
                last_followup_sent = datetime.fromisoformat(data["last_followup_sent"])
            except (ValueError, TypeError):
                pass

        return cls(
            motivation=motivation,
            motivation_details=data.get("motivation_details"),
            relocation_destination=data.get("relocation_destination"),
            timeline_urgency=timeline_urgency,
            timeline_acceptable=data.get("timeline_acceptable"),
            timeline_details=data.get("timeline_details"),
            property_condition=property_condition,
            repair_estimate=data.get("repair_estimate"),
            condition_details=data.get("condition_details"),
            price_expectation=data.get("price_expectation"),
            price_flexibility=price_flexibility,
            price_details=data.get("price_details"),
            questions_answered=data.get("questions_answered", 0),
            response_quality=data.get("response_quality", 0.0),
            responsiveness=data.get("responsiveness", 0.0),
            conversation_started_at=conversation_started_at,
            last_interaction_at=last_interaction_at,
            total_interactions=data.get("total_interactions", 0),
            seller_temperature=data.get("seller_temperature", "cold"),
            qualification_score=data.get("qualification_score", 0.0),
            last_followup_sent=last_followup_sent,
            followup_count=data.get("followup_count", 0),
            followup_phase=data.get("followup_phase", "active"),
            lead_source=data.get("lead_source"),
            ghl_contact_id=data.get("ghl_contact_id"),
            ghl_location_id=data.get("ghl_location_id"),
            custom_fields=data.get("custom_fields", {}),
        )

    def update_interaction_metrics(self, response_quality: float = None):
        """Update interaction tracking metrics"""
        self.last_interaction_at = datetime.now()
        self.total_interactions += 1

        if response_quality is not None:
            # Rolling average of response quality
            if self.response_quality == 0.0:
                self.response_quality = response_quality
            else:
                self.response_quality = (self.response_quality * 0.7) + (response_quality * 0.3)

        # Update responsiveness based on interaction frequency
        if self.conversation_started_at:
            hours_since_start = (datetime.now() - self.conversation_started_at).total_seconds() / 3600
            if hours_since_start > 0:
                self.responsiveness = min(1.0, self.total_interactions / max(1, hours_since_start / 24))

    def calculate_qualification_score(self) -> float:
        """Calculate overall qualification score based on Jorge's criteria"""
        score = 0.0

        # Questions completion (40% weight)
        score += (self.questions_answered / 4) * 0.4

        # Timeline urgency (30% weight - Jorge's priority)
        if self.timeline_acceptable is True:
            score += 0.3
        elif self.timeline_acceptable is False:
            score += 0.15  # Still answered but not ideal

        # Response quality (20% weight)
        score += self.response_quality * 0.2

        # Responsiveness (10% weight)
        score += self.responsiveness * 0.1

        self.qualification_score = min(1.0, score)
        return self.qualification_score


@dataclass
class SellerInteraction:
    """Individual seller interaction record for analytics"""

    contact_id: str
    location_id: str
    interaction_type: str  # 'question_asked', 'data_extracted', 'temperature_change'
    question_number: Optional[int] = None  # 1-4 for Jorge's questions
    temperature: Optional[str] = None  # 'hot', 'warm', 'cold'
    response_quality: Optional[float] = None
    message_content: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "contact_id": self.contact_id,
            "location_id": self.location_id,
            "interaction_type": self.interaction_type,
            "question_number": self.question_number,
            "temperature": self.temperature,
            "response_quality": self.response_quality,
            "message_content": self.message_content,
            "extracted_data": self.extracted_data,
            "created_at": self.created_at.isoformat(),
        }


# Utility Functions for Jorge's Seller Bot


def validate_seller_data(data: Dict[str, Any]) -> List[str]:
    """Validate seller data and return list of validation errors"""
    errors = []

    # Validate price expectation is reasonable
    if data.get("price_expectation"):
        try:
            price = int(data["price_expectation"])
            if price < 10000 or price > 50000000:
                errors.append("Price expectation seems unrealistic")
        except (ValueError, TypeError):
            errors.append("Price expectation must be a valid number")

    # Validate timeline consistency
    if data.get("timeline_acceptable") is True and data.get("timeline_urgency") == TimelineUrgency.LONG_TERM.value:
        errors.append("Timeline acceptance inconsistent with urgency")

    # Validate response quality is in valid range
    response_quality = data.get("response_quality", 0.0)
    if not 0.0 <= response_quality <= 1.0:
        errors.append("Response quality must be between 0.0 and 1.0")

    return errors


def merge_seller_data(current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge new seller data with current data, preserving existing values"""
    merged = current.copy()

    # Only update fields that have new values
    for key, value in new.items():
        if value is not None and value != "":
            merged[key] = value

    # Always update quality metrics and timestamps
    merged["response_quality"] = new.get("response_quality", current.get("response_quality", 0.0))
    merged["responsiveness"] = new.get("responsiveness", current.get("responsiveness", 0.0))

    # Count questions answered
    question_fields = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]
    questions_answered = sum(1 for field in question_fields if merged.get(field) is not None)
    merged["questions_answered"] = questions_answered

    return merged


def create_ghl_custom_fields_mapping() -> Dict[str, str]:
    """Create mapping of seller data fields to GHL custom field IDs"""
    return {
        "seller_temperature": "custom_field_seller_temperature",
        "motivation": "custom_field_seller_motivation",
        "relocation_destination": "custom_field_relocation_destination",
        "timeline_urgency": "custom_field_timeline_urgency",
        "property_condition": "custom_field_property_condition",
        "price_expectation": "custom_field_price_expectation",
        "questions_answered": "custom_field_questions_answered",
        "qualification_score": "custom_field_qualification_score",
    }


# Export main classes for easy importing
__all__ = [
    "SellerProfile",
    "SellerInteraction",
    "TimelineUrgency",
    "PropertyCondition",
    "MotivationType",
    "PriceFlexibility",
    "validate_seller_data",
    "merge_seller_data",
    "create_ghl_custom_fields_mapping",
]
