"""
Pydantic models for billing integration.

Defines request/response schemas for subscription management,
usage tracking, and Stripe webhook processing.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_serializer, field_validator

# ===================================================================
# Enums
# ===================================================================


class SubscriptionTier(str, Enum):
    """Subscription tier options with usage allowances."""

    STARTER = "starter"  # $99/month, 50 leads
    PROFESSIONAL = "professional"  # $249/month, 150 leads
    ENTERPRISE = "enterprise"  # $499/month, 500 leads


class SubscriptionStatus(str, Enum):
    """Stripe subscription status values."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class InvoiceStatus(str, Enum):
    """Invoice payment status."""

    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    MARKED_UNCOLLECTIBLE = "marked_uncollectible"


# ===================================================================
# Base Models
# ===================================================================


class BaseModelWithTimestamp(BaseModel):
    """Base model with automatic timestamp handling."""

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @field_serializer("created_at", "updated_at")
    @classmethod
    def serialize_datetime(cls, v: Optional[datetime]) -> Optional[str]:
        return v.isoformat() if v else None


# ===================================================================
# Subscription Models
# ===================================================================


class CreateSubscriptionRequest(BaseModel):
    """Request to create a new subscription."""

    location_id: str = Field(..., description="GHL location ID")
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    payment_method_id: str = Field(..., description="Stripe payment method ID")
    trial_days: int = Field(default=14, ge=0, le=30, description="Free trial period in days")
    email: Optional[str] = Field(None, description="Customer email for billing")
    name: Optional[str] = Field(None, description="Customer name for billing")
    currency: str = Field(default="usd", description="Billing currency (usd, eur, gbp, etc.)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v


class ModifySubscriptionRequest(BaseModel):
    """Request to modify an existing subscription."""

    tier: Optional[SubscriptionTier] = Field(None, description="New tier (for upgrades/downgrades)")
    payment_method_id: Optional[str] = Field(None, description="New payment method")
    cancel_at_period_end: Optional[bool] = Field(None, description="Schedule cancellation")
    currency: Optional[str] = Field(None, description="New currency (if changing location/market)")


class SubscriptionResponse(BaseModel):
    """Detailed subscription information."""

    id: int
    location_id: str
    stripe_subscription_id: str
    stripe_customer_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    currency: str = Field(default="usd", description="Billing currency")
    current_period_start: datetime
    current_period_end: datetime
    usage_allowance: int = Field(..., description="Leads included in tier")
    usage_current: int = Field(..., description="Leads used this period")
    usage_percentage: float = Field(..., description="Percentage of allowance used")
    overage_rate: Decimal = Field(..., description="Cost per overage lead")
    base_price: Decimal = Field(..., description="Monthly subscription price")
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    next_invoice_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator("usage_percentage", mode="before")
    @classmethod
    def calculate_usage_percentage(cls, v, info: ValidationInfo):
        """Auto-calculate usage percentage from current/allowance."""
        data = info.data
        if "usage_allowance" in data and data["usage_allowance"] > 0:
            return round((data.get("usage_current", 0) / data["usage_allowance"]) * 100, 2)
        return 0.0

    model_config = ConfigDict(from_attributes=True)


class SubscriptionSummary(BaseModel):
    """Lightweight subscription summary for dashboards."""

    id: int
    location_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    currency: str = "usd"
    usage_current: int
    usage_allowance: int
    usage_percentage: float
    next_invoice_date: Optional[datetime]
    amount_due_next: Decimal


# ===================================================================
# Usage Tracking Models
# ===================================================================


class UsageRecordRequest(BaseModel):
    """Request to record lead usage."""

    subscription_id: int
    lead_id: str = Field(..., description="GHL lead ID")
    contact_id: str = Field(..., description="GHL contact ID")
    amount: Decimal = Field(..., description="Calculated lead price")
    tier: str = Field(..., description="Lead quality tier (hot/warm/cold)")
    pricing_multiplier: Optional[Decimal] = Field(None, description="Dynamic pricing multiplier")
    billing_period_start: datetime
    billing_period_end: datetime

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return round(v, 2)


class UsageRecordResponse(BaseModel):
    """Usage record with billing details."""

    id: int
    subscription_id: int
    stripe_usage_record_id: Optional[str]
    lead_id: str
    contact_id: str
    quantity: int
    amount: Decimal
    tier: str
    pricing_multiplier: Optional[Decimal]
    timestamp: datetime
    billing_period_start: datetime
    billing_period_end: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageSummary(BaseModel):
    """Current period usage summary."""

    subscription_id: int
    period_start: datetime
    period_end: datetime
    usage_allowance: int
    usage_current: int
    usage_remaining: int
    overage_count: int
    base_cost: Decimal
    overage_cost: Decimal
    total_cost: Decimal
    usage_by_tier: Dict[str, int] = Field(default_factory=dict)  # hot/warm/cold counts


# ===================================================================
# Invoice Models
# ===================================================================


class InvoiceDetails(BaseModel):
    """Invoice information for billing history."""

    id: int
    stripe_invoice_id: str
    subscription_id: int
    amount_due: Decimal
    amount_paid: Decimal
    status: InvoiceStatus
    period_start: datetime
    period_end: datetime
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    hosted_invoice_url: Optional[str]
    invoice_pdf: Optional[str]
    line_items: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BillingHistoryResponse(BaseModel):
    """Billing history for a customer."""

    location_id: str
    invoices: List[InvoiceDetails]
    total_spent: Decimal
    period_start: datetime
    period_end: datetime
    payment_methods: List[Dict[str, Any]] = Field(default_factory=list)


# ===================================================================
# Stripe Webhook Models
# ===================================================================


class StripeWebhookEvent(BaseModel):
    """Stripe webhook event payload."""

    id: str
    type: str
    data: Dict[str, Any]
    created: int
    livemode: bool
    api_version: str
    request: Optional[Dict[str, Any]] = None


class WebhookProcessingResult(BaseModel):
    """Result of webhook processing."""

    event_id: str
    event_type: str
    processed: bool
    processing_time_ms: float
    error_message: Optional[str] = None
    actions_taken: List[str] = Field(default_factory=list)


# ===================================================================
# Analytics Models
# ===================================================================


class RevenueAnalytics(BaseModel):
    """Revenue metrics for analytics dashboard."""

    total_arr: Decimal = Field(..., description="Annual Recurring Revenue")
    monthly_revenue: Decimal = Field(..., description="Monthly Recurring Revenue")
    average_arpu: Decimal = Field(..., description="Average Revenue Per User")
    churn_rate: float = Field(..., description="Monthly churn rate percentage")
    upgrade_rate: float = Field(..., description="Tier upgrade rate percentage")
    usage_revenue_percentage: float = Field(..., description="% of revenue from usage overages")
    top_tier_customers: int = Field(..., description="Count of enterprise tier customers")
    total_active_subscriptions: int


class TierDistribution(BaseModel):
    """Subscription tier distribution analytics."""

    starter_count: int = 0
    professional_count: int = 0
    enterprise_count: int = 0
    starter_percentage: float = 0.0
    professional_percentage: float = 0.0
    enterprise_percentage: float = 0.0
    total_subscriptions: int = 0


# ===================================================================
# Error Response Models
# ===================================================================


class BillingError(BaseModel):
    """Standardized billing error response."""

    error_code: str = Field(..., description="Machine-readable error code")
    error_message: str = Field(..., description="Human-readable error description")
    error_type: str = Field(..., description="Error category (validation, payment, stripe, etc.)")
    recoverable: bool = Field(..., description="Whether the error can be retried")
    suggested_action: Optional[str] = Field(None, description="Suggested user action")
    stripe_error_code: Optional[str] = Field(None, description="Original Stripe error code")


# ===================================================================
# Configuration Models
# ===================================================================


class TierConfiguration(BaseModel):
    """Subscription tier configuration."""

    name: str
    price_monthly: Decimal
    usage_allowance: int
    overage_rate: Decimal
    features: List[str]
    stripe_price_id: str
    currency: str = "usd"

    @field_validator("price_monthly", "overage_rate")
    @classmethod
    def validate_positive_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v


# Pre-defined tier configurations
SUBSCRIPTION_TIERS = {
    SubscriptionTier.STARTER: TierConfiguration(
        name="Starter",
        price_monthly=Decimal("99.00"),
        usage_allowance=50,
        overage_rate=Decimal("1.00"),
        features=["Basic lead scoring", "Email support", "Standard analytics"],
        stripe_price_id="price_starter_monthly",
    ),
    SubscriptionTier.PROFESSIONAL: TierConfiguration(
        name="Professional",
        price_monthly=Decimal("249.00"),
        usage_allowance=150,
        overage_rate=Decimal("1.50"),
        features=["Advanced lead scoring", "Phone support", "Real-time analytics", "Custom integrations"],
        stripe_price_id="price_professional_monthly",
    ),
    SubscriptionTier.ENTERPRISE: TierConfiguration(
        name="Enterprise",
        price_monthly=Decimal("499.00"),
        usage_allowance=500,
        overage_rate=Decimal("0.75"),
        features=[
            "Premium lead scoring",
            "24/7 support",
            "Advanced analytics",
            "White-label options",
            "Priority processing",
        ],
        stripe_price_id="price_enterprise_monthly",
    ),
}
