"""
Jorge-Specific Validation Schemas and Validators.

Provides custom validators for Jorge's Real Estate AI platform business logic,
including commission rates, property criteria, lead qualification, and more.

Features:
- Commission rate validation (5%-8% range)
- Property value and type validation
- Lead scoring criteria validation
- Phone number and email formatting
- Geographic market validation
- Custom error messages with actionable guidance
"""

import re
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator, root_validator
try:
    from pydantic.types import EmailStr
except ImportError:
    from pydantic import EmailStr

try:
    from pydantic.types import UUID4
except ImportError:
    from pydantic import UUID4


class JorgeCommissionValidator:
    """Validator for Jorge's commission rates and calculations."""

    STANDARD_RATE = Decimal("0.06")  # 6%
    MIN_RATE = Decimal("0.05")       # 5%
    MAX_RATE = Decimal("0.08")       # 8%

    @classmethod
    def validate_commission_rate(cls, rate: Union[float, Decimal, str]) -> Decimal:
        """Validate commission rate is within Jorge's acceptable range."""
        try:
            decimal_rate = Decimal(str(rate))

            if decimal_rate < cls.MIN_RATE:
                raise ValueError(
                    f"Commission rate {rate} is below Jorge's minimum of {cls.MIN_RATE * 100}%. "
                    f"Standard rate is {cls.STANDARD_RATE * 100}%."
                )

            if decimal_rate > cls.MAX_RATE:
                raise ValueError(
                    f"Commission rate {rate} exceeds Jorge's maximum of {cls.MAX_RATE * 100}%. "
                    f"Standard rate is {cls.STANDARD_RATE * 100}%."
                )

            return decimal_rate

        except (ValueError, TypeError) as e:
            if "Commission rate" not in str(e):
                raise ValueError(
                    f"Invalid commission rate format: '{rate}'. "
                    f"Must be a decimal between {cls.MIN_RATE} and {cls.MAX_RATE}."
                )
            raise


class JorgePropertyValidator:
    """Validator for Jorge's property criteria and requirements."""

    MIN_VALUE = 100_000      # $100K
    MAX_VALUE = 2_000_000    # $2M
    SUPPORTED_TYPES = ["single_family", "condo", "townhouse", "duplex"]
    SUPPORTED_MARKETS = ["rancho_cucamonga", "san_antonio", "houston", "dallas"]

    @classmethod
    def validate_property_value(cls, value: Union[int, float, Decimal]) -> int:
        """Validate property value is within Jorge's criteria."""
        try:
            int_value = int(value)

            if int_value < cls.MIN_VALUE:
                raise ValueError(
                    f"Property value ${int_value:,} is below Jorge's minimum of ${cls.MIN_VALUE:,}. "
                    f"Jorge focuses on properties between ${cls.MIN_VALUE:,} and ${cls.MAX_VALUE:,}."
                )

            if int_value > cls.MAX_VALUE:
                raise ValueError(
                    f"Property value ${int_value:,} exceeds Jorge's maximum of ${cls.MAX_VALUE:,}. "
                    f"Jorge focuses on properties between ${cls.MIN_VALUE:,} and ${cls.MAX_VALUE:,}."
                )

            return int_value

        except (ValueError, TypeError) as e:
            if "Property value" not in str(e):
                raise ValueError(
                    f"Invalid property value: '{value}'. Must be a number between "
                    f"${cls.MIN_VALUE:,} and ${cls.MAX_VALUE:,}."
                )
            raise

    @classmethod
    def validate_property_type(cls, property_type: str) -> str:
        """Validate property type is supported by Jorge."""
        normalized_type = property_type.lower().strip().replace("-", "_").replace(" ", "_")

        if normalized_type not in cls.SUPPORTED_TYPES:
            raise ValueError(
                f"Property type '{property_type}' is not supported. "
                f"Jorge handles: {', '.join(cls.SUPPORTED_TYPES)}."
            )

        return normalized_type

    @classmethod
    def validate_market(cls, market: str) -> str:
        """Validate market is in Jorge's service area."""
        normalized_market = market.lower().strip().replace(" ", "_")

        if normalized_market not in cls.SUPPORTED_MARKETS:
            raise ValueError(
                f"Market '{market}' is outside Jorge's service area. "
                f"Supported markets: {', '.join(cls.SUPPORTED_MARKETS)}."
            )

        return normalized_market


class JorgeLeadValidator:
    """Validator for Jorge's lead qualification criteria."""

    MIN_CREDIT_SCORE = 580
    MIN_INCOME = 40_000
    PHONE_PATTERN = re.compile(r"^(\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$")

    @classmethod
    def validate_phone_number(cls, phone: str) -> str:
        """Validate and normalize US phone number."""
        if not phone:
            raise ValueError("Phone number is required for lead qualification.")

        cleaned = re.sub(r"[^\d+]", "", phone)

        if not cls.PHONE_PATTERN.match(phone):
            raise ValueError(
                f"Invalid phone number format: '{phone}'. "
                "Please provide a valid US phone number (e.g., 555-123-4567)."
            )

        # Extract digits only for storage
        digits_only = re.sub(r"[^\d]", "", phone)
        if len(digits_only) == 11 and digits_only.startswith("1"):
            digits_only = digits_only[1:]  # Remove country code
        elif len(digits_only) != 10:
            raise ValueError(
                f"Phone number must be 10 digits: '{phone}'. "
                "Format: (555) 123-4567 or 555-123-4567."
            )

        # Return formatted version
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"

    @classmethod
    def validate_credit_score(cls, score: Optional[int]) -> Optional[int]:
        """Validate credit score for Jorge's qualification."""
        if score is None:
            return None

        if not isinstance(score, int) or score < 300 or score > 850:
            raise ValueError(
                f"Invalid credit score: {score}. Must be between 300 and 850."
            )

        if score < cls.MIN_CREDIT_SCORE:
            raise ValueError(
                f"Credit score {score} is below Jorge's minimum of {cls.MIN_CREDIT_SCORE}. "
                "Consider credit improvement programs before requalifying."
            )

        return score

    @classmethod
    def validate_annual_income(cls, income: Optional[int]) -> Optional[int]:
        """Validate annual income for Jorge's qualification."""
        if income is None:
            return None

        if not isinstance(income, int) or income < 0:
            raise ValueError(f"Invalid income amount: {income}. Must be a positive number.")

        if income < cls.MIN_INCOME:
            raise ValueError(
                f"Annual income ${income:,} is below Jorge's minimum qualification of ${cls.MIN_INCOME:,}. "
                "Consider alternative financing options."
            )

        return income


# Pydantic Models with Jorge Validators

class JorgePropertyRequest(BaseModel):
    """Property request with Jorge's business validation."""

    address: str = Field(..., min_length=10, max_length=200)
    property_type: str
    market: str
    estimated_value: int
    commission_rate: Optional[Decimal] = Field(default=JorgeCommissionValidator.STANDARD_RATE)

    # Validation
    @validator("property_type")
    def validate_property_type(cls, v):
        return JorgePropertyValidator.validate_property_type(v)

    @validator("market")
    def validate_market(cls, v):
        return JorgePropertyValidator.validate_market(v)

    @validator("estimated_value")
    def validate_value(cls, v):
        return JorgePropertyValidator.validate_property_value(v)

    @validator("commission_rate")
    def validate_commission(cls, v):
        return JorgeCommissionValidator.validate_commission_rate(v)

    class Config:
        json_schema_extra = {
            "example": {
                "address": "123 Main St, Rancho Cucamonga, CA 78701",
                "property_type": "single_family",
                "market": "rancho_cucamonga",
                "estimated_value": 450000,
                "commission_rate": 0.06
            }
        }


class JorgeLeadRequest(BaseModel):
    """Lead request with Jorge's qualification validation."""

    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    phone: str
    annual_income: Optional[int] = None
    credit_score: Optional[int] = None
    preapproval_amount: Optional[int] = None
    lead_source: str = Field(default="website")

    # Validation
    @validator("phone")
    def validate_phone(cls, v):
        return JorgeLeadValidator.validate_phone_number(v)

    @validator("credit_score")
    def validate_credit_score(cls, v):
        return JorgeLeadValidator.validate_credit_score(v)

    @validator("annual_income")
    def validate_income(cls, v):
        return JorgeLeadValidator.validate_annual_income(v)

    @validator("preapproval_amount")
    def validate_preapproval(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Preapproval amount must be positive")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
                "phone": "(555) 123-4567",
                "annual_income": 75000,
                "credit_score": 720,
                "preapproval_amount": 400000,
                "lead_source": "website"
            }
        }


class JorgeCommissionCalculation(BaseModel):
    """Commission calculation with Jorge's rates."""

    property_value: int
    commission_rate: Optional[Decimal] = Field(default=JorgeCommissionValidator.STANDARD_RATE)
    split_percentage: Optional[Decimal] = Field(default=Decimal("1.0"))  # 100% to Jorge by default

    @validator("property_value")
    def validate_property_value(cls, v):
        return JorgePropertyValidator.validate_property_value(v)

    @validator("commission_rate")
    def validate_commission_rate(cls, v):
        return JorgeCommissionValidator.validate_commission_rate(v)

    @validator("split_percentage")
    def validate_split(cls, v):
        decimal_v = Decimal(str(v))
        if decimal_v < 0 or decimal_v > 1:
            raise ValueError("Split percentage must be between 0 and 1 (0% to 100%)")
        return decimal_v

    @property
    def total_commission(self) -> Decimal:
        """Calculate total commission amount."""
        return Decimal(self.property_value) * self.commission_rate

    @property
    def jorge_commission(self) -> Decimal:
        """Calculate Jorge's commission amount."""
        return self.total_commission * self.split_percentage

    class Config:
        json_schema_extra = {
            "example": {
                "property_value": 700000,
                "commission_rate": 0.06,
                "split_percentage": 1.0
            }
        }


class JorgeBotMessage(BaseModel):
    """Bot message with Jorge's communication standards."""

    message_type: str = Field(..., pattern="^(sms|email|call|chat)$")
    content: str = Field(..., min_length=10, max_length=1600)  # SMS limit
    lead_id: UUID4
    bot_type: str = Field(..., pattern="^(seller|buyer|lead|claude)$")
    temperature: str = Field(default="warm", pattern="^(hot|warm|lukewarm|cold|ice_cold)$")

    @validator("content")
    def validate_content(cls, v, values):
        """Validate content based on message type."""
        message_type = values.get("message_type")

        if message_type == "sms" and len(v) > 160:
            raise ValueError(
                f"SMS content too long ({len(v)} chars). "
                "Maximum 160 characters for SMS compliance."
            )

        # Check for professional tone
        unprofessional_words = ["dude", "bro", "whatever", "wtf", "omg"]
        if any(word in v.lower() for word in unprofessional_words):
            raise ValueError(
                "Message content must maintain professional tone. "
                "Jorge requires professional communication standards."
            )

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "sms",
                "content": "Hi John! Jorge here. Saw your interest in Rancho Cucamonga properties. Free to chat about your home search? Quick 5-min call.",
                "lead_id": "123e4567-e89b-12d3-a456-426614174000",
                "bot_type": "buyer",
                "temperature": "warm"
            }
        }


class JorgeAnalyticsQuery(BaseModel):
    """Analytics query with Jorge's reporting requirements."""

    timeframe: str = Field(default="24h", pattern="^(1h|24h|7d|30d|90d|1y)$")
    metrics: List[str] = Field(default=["revenue", "leads", "conversion"])
    location_id: str = Field(default="default")
    include_commission: bool = Field(default=True)

    @validator("metrics")
    def validate_metrics(cls, v):
        """Validate metrics are supported."""
        supported_metrics = [
            "revenue", "leads", "conversion", "commission", "properties",
            "bot_performance", "response_time", "qualification_rate"
        ]

        invalid_metrics = [m for m in v if m not in supported_metrics]
        if invalid_metrics:
            raise ValueError(
                f"Unsupported metrics: {invalid_metrics}. "
                f"Supported: {supported_metrics}"
            )

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "timeframe": "7d",
                "metrics": ["revenue", "leads", "conversion", "commission"],
                "location_id": "jorge_rancho_cucamonga",
                "include_commission": True
            }
        }


# Error response models

class JorgeValidationError(BaseModel):
    """Jorge-specific validation error response."""

    success: bool = False
    error: Dict[str, Any]
    field_errors: List[str]
    guidance: str
    correlation_id: str
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "type": "validation_error",
                    "message": "Commission rate validation failed",
                    "retryable": False
                },
                "field_errors": ["commission_rate: Commission rate 0.12 exceeds Jorge's maximum of 8%"],
                "guidance": "Jorge's commission rate must be between 5% and 8%. Standard rate is 6%.",
                "correlation_id": "jorge_1234567890_abc123",
                "timestamp": "2026-01-25T12:00:00Z"
            }
        }


# Convenience functions for validation

def validate_jorge_commission(rate: Union[float, str, Decimal]) -> Decimal:
    """Standalone commission validation function."""
    return JorgeCommissionValidator.validate_commission_rate(rate)


def validate_jorge_property_value(value: Union[int, float]) -> int:
    """Standalone property value validation function."""
    return JorgePropertyValidator.validate_property_value(value)


def validate_jorge_phone(phone: str) -> str:
    """Standalone phone number validation function."""
    return JorgeLeadValidator.validate_phone_number(phone)