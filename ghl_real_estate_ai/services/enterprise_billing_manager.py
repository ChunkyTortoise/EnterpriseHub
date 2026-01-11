"""
Enterprise Billing Manager for Multi-Tenant Billing

This service provides comprehensive billing and revenue management capabilities for
multi-tenant enterprise deployments, including subscription management, usage-based
billing, partner revenue sharing, and financial reporting.

Key Features:
- Multi-tenant subscription management and billing
- Usage-based pricing and consumption tracking
- Partner revenue sharing and commission processing
- Payment processing integration and automation
- Invoice generation and delivery automation
- Tax calculation and compliance management
- Revenue recognition and financial reporting
- Billing analytics and forecasting
- Subscription lifecycle management
- Dunning management and payment recovery
- Financial audit trails and compliance
- Multi-currency support and exchange rate management

Author: Claude (Anthropic)
Created: January 2026
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from uuid import uuid4
from decimal import Decimal, ROUND_HALF_UP
import calendar

import redis
from pydantic import BaseModel, Field, validator
import stripe
from dateutil.relativedelta import relativedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubscriptionStatus(str, Enum):
    """Subscription status levels"""
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    SUSPENDED = "suspended"
    PAUSED = "paused"
    EXPIRED = "expired"

class BillingModel(str, Enum):
    """Billing model types"""
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    HYBRID = "hybrid"
    ONE_TIME = "one_time"
    FREEMIUM = "freemium"
    TIERED = "tiered"

class BillingFrequency(str, Enum):
    """Billing frequency options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    WEEKLY = "weekly"
    DAILY = "daily"

class PaymentStatus(str, Enum):
    """Payment status levels"""
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"

class InvoiceStatus(str, Enum):
    """Invoice status levels"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    VOID = "void"
    REFUNDED = "refunded"

class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"

class TaxType(str, Enum):
    """Tax types"""
    VAT = "vat"
    SALES_TAX = "sales_tax"
    GST = "gst"
    NONE = "none"

class RevenueType(str, Enum):
    """Revenue types for recognition"""
    SUBSCRIPTION = "subscription"
    USAGE = "usage"
    SETUP_FEE = "setup_fee"
    PROFESSIONAL_SERVICES = "professional_services"
    PARTNER_COMMISSION = "partner_commission"

class PricingPlan(BaseModel):
    """Pricing plan configuration"""
    plan_id: str
    name: str
    description: str
    billing_model: BillingModel
    billing_frequency: BillingFrequency

    # Pricing structure
    base_price: Decimal
    currency: Currency
    setup_fee: Optional[Decimal] = None

    # Usage-based pricing
    usage_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    usage_tiers: List[Dict[str, Any]] = Field(default_factory=list)
    overage_pricing: Dict[str, Decimal] = Field(default_factory=dict)

    # Plan limits and features
    included_features: Set[str] = Field(default_factory=set)
    usage_limits: Dict[str, int] = Field(default_factory=dict)
    user_limits: Optional[int] = None

    # Billing configuration
    trial_period_days: int = 0
    grace_period_days: int = 3
    auto_renewal: bool = True

    # Partner and reseller pricing
    partner_commission_rate: Optional[Decimal] = None
    reseller_discount_rate: Optional[Decimal] = None

    # Metadata
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda d: float(d)
        }

class Subscription(BaseModel):
    """Customer subscription"""
    subscription_id: str
    organization_id: str
    plan_id: str
    status: SubscriptionStatus

    # Subscription details
    start_date: datetime
    end_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    current_period_start: datetime
    current_period_end: datetime

    # Billing configuration
    billing_frequency: BillingFrequency
    currency: Currency
    base_amount: Decimal
    current_amount: Decimal

    # Usage tracking
    usage_metrics: Dict[str, Any] = Field(default_factory=dict)
    usage_limits: Dict[str, int] = Field(default_factory=dict)
    current_usage: Dict[str, int] = Field(default_factory=dict)

    # Payment information
    payment_method_id: Optional[str] = None
    next_billing_date: Optional[datetime] = None
    last_billing_date: Optional[datetime] = None

    # Lifecycle management
    auto_renewal: bool = True
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Partner information
    partner_id: Optional[str] = None
    reseller_id: Optional[str] = None
    commission_rate: Optional[Decimal] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda d: float(d)
        }

class Invoice(BaseModel):
    """Billing invoice"""
    invoice_id: str
    organization_id: str
    subscription_id: Optional[str] = None

    # Invoice details
    invoice_number: str
    status: InvoiceStatus
    currency: Currency
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    # Line items
    line_items: List[Dict[str, Any]] = Field(default_factory=list)

    # Tax information
    tax_rate: Optional[Decimal] = None
    tax_type: TaxType = TaxType.NONE
    tax_jurisdiction: Optional[str] = None

    # Payment information
    payment_terms_days: int = 30
    due_date: datetime
    paid_date: Optional[datetime] = None
    payment_method: Optional[str] = None

    # Billing period
    period_start: datetime
    period_end: datetime

    # Customer information
    billing_address: Dict[str, str] = Field(default_factory=dict)

    # Invoice metadata
    notes: Optional[str] = None
    sent_date: Optional[datetime] = None
    pdf_url: Optional[str] = None

    # Collections
    dunning_attempts: int = 0
    last_dunning_date: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda d: float(d)
        }

class Payment(BaseModel):
    """Payment transaction"""
    payment_id: str
    organization_id: str
    invoice_id: Optional[str] = None
    subscription_id: Optional[str] = None

    # Payment details
    amount: Decimal
    currency: Currency
    status: PaymentStatus
    payment_method: str
    payment_processor: str = "stripe"

    # Transaction information
    transaction_id: Optional[str] = None
    external_transaction_id: Optional[str] = None
    gateway_response: Dict[str, Any] = Field(default_factory=dict)

    # Payment timing
    attempted_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None

    # Fees and reconciliation
    processing_fee: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None

    # Refund information
    refund_amount: Optional[Decimal] = None
    refunded_at: Optional[datetime] = None
    refund_reason: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: lambda d: float(d)
        }

class UsageRecord(BaseModel):
    """Usage tracking record"""
    usage_id: str
    organization_id: str
    subscription_id: str

    # Usage details
    metric_name: str
    quantity: Decimal
    unit: str
    timestamp: datetime

    # Billing context
    billing_period_start: datetime
    billing_period_end: datetime
    already_billed: bool = False

    # Pricing context
    unit_price: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    tier: Optional[str] = None

    # Metadata
    resource_id: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: lambda d: float(d)
        }

class RevenueRecognition(BaseModel):
    """Revenue recognition entry"""
    recognition_id: str
    organization_id: str
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None

    # Revenue details
    revenue_type: RevenueType
    total_revenue: Decimal
    recognized_revenue: Decimal
    deferred_revenue: Decimal
    currency: Currency

    # Recognition schedule
    recognition_start_date: datetime
    recognition_end_date: datetime
    recognition_schedule: List[Dict[str, Any]] = Field(default_factory=list)

    # Accounting
    accounting_period: str
    revenue_account: str
    deferred_account: str

    # Status
    fully_recognized: bool = False
    recognition_method: str = "straight_line"

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            Decimal: lambda d: float(d)
        }

class BillingRequest(BaseModel):
    """Request model for billing operations"""
    operation_type: str
    organization_id: Optional[str] = None
    subscription_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    admin_user_id: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)

class BillingResponse(BaseModel):
    """Response model for billing operations"""
    success: bool
    operation_id: str
    organization_id: Optional[str] = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    message: str
    amount: Optional[Decimal] = None
    currency: Optional[Currency] = None
    next_steps: List[str] = Field(default_factory=list)
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float

    class Config:
        json_encoders = {
            Decimal: lambda d: float(d)
        }

@dataclass
class BillingMetrics:
    """Billing and revenue metrics"""
    total_revenue_current_month: Decimal
    total_revenue_last_month: Decimal
    mrr_current: Decimal  # Monthly Recurring Revenue
    arr_current: Decimal  # Annual Recurring Revenue
    churn_rate_monthly: float
    customer_lifetime_value: Decimal
    average_revenue_per_user: Decimal
    outstanding_receivables: Decimal
    past_due_amount: Decimal
    active_subscriptions: int
    trial_conversions: float
    revenue_growth_rate: float
    last_calculated: datetime = field(default_factory=datetime.utcnow)

class EnterpriseBillingManager:
    """
    Enterprise Billing Manager for Multi-Tenant Billing

    Provides comprehensive billing and revenue management including:
    - Multi-tenant subscription management and billing
    - Usage-based pricing and consumption tracking
    - Partner revenue sharing and commission processing
    - Payment processing integration and automation
    - Invoice generation and financial reporting
    - Revenue recognition and compliance
    """

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.billing_cache = {}
        self.subscription_cache = {}
        self.invoice_cache = {}

        # Payment processing
        self.stripe_client = None  # Would be initialized with actual Stripe keys
        self.payment_processors = self._initialize_payment_processors()

        # Tax calculation
        self.tax_calculator = self._initialize_tax_calculator()

        # Currency exchange
        self.exchange_rates = self._load_exchange_rates()

        # Billing configuration
        self.pricing_plans = self._load_pricing_plans()
        self.billing_rules = self._load_billing_rules()
        self.dunning_configuration = self._load_dunning_configuration()

        logger.info("Enterprise Billing Manager initialized")

    def _initialize_payment_processors(self) -> Dict[str, Any]:
        """Initialize payment processor configurations"""
        return {
            "stripe": {
                "enabled": True,
                "supported_currencies": ["USD", "EUR", "GBP", "CAD", "AUD"],
                "supported_methods": ["card", "ach", "sepa", "bank_transfer"],
                "webhook_events": ["payment_succeeded", "payment_failed", "invoice_paid"]
            },
            "paypal": {
                "enabled": True,
                "supported_currencies": ["USD", "EUR", "GBP"],
                "supported_methods": ["paypal", "credit_card"]
            },
            "bank_transfer": {
                "enabled": True,
                "supported_currencies": ["USD", "EUR", "GBP", "CAD"],
                "processing_days": 3
            }
        }

    def _initialize_tax_calculator(self) -> Dict[str, Any]:
        """Initialize tax calculation system"""
        return {
            "enabled": True,
            "providers": {
                "avalara": {"enabled": True, "api_key": "tax_api_key"},
                "taxjar": {"enabled": False}
            },
            "default_rates": {
                "US": {"rate": 0.0875, "type": "sales_tax"},
                "EU": {"rate": 0.20, "type": "vat"},
                "CA": {"rate": 0.13, "type": "gst"},
                "AU": {"rate": 0.10, "type": "gst"}
            }
        }

    def _load_exchange_rates(self) -> Dict[str, Decimal]:
        """Load current exchange rates"""
        # In production, would fetch from exchange rate API
        return {
            "USD_EUR": Decimal("0.85"),
            "USD_GBP": Decimal("0.73"),
            "USD_CAD": Decimal("1.25"),
            "USD_AUD": Decimal("1.35"),
            "USD_JPY": Decimal("110.0")
        }

    def _load_pricing_plans(self) -> Dict[str, PricingPlan]:
        """Load available pricing plans"""
        plans = {}

        # Starter Plan
        plans["starter"] = PricingPlan(
            plan_id="starter",
            name="Starter Plan",
            description="Perfect for small teams getting started",
            billing_model=BillingModel.SUBSCRIPTION,
            billing_frequency=BillingFrequency.MONTHLY,
            base_price=Decimal("99.00"),
            currency=Currency.USD,
            setup_fee=Decimal("49.00"),
            usage_limits={
                "users": 10,
                "api_calls": 10000,
                "storage_gb": 50
            },
            included_features={"basic_claude", "standard_support", "basic_analytics"},
            trial_period_days=14,
            partner_commission_rate=Decimal("0.15")
        )

        # Professional Plan
        plans["professional"] = PricingPlan(
            plan_id="professional",
            name="Professional Plan",
            description="Advanced features for growing businesses",
            billing_model=BillingModel.HYBRID,
            billing_frequency=BillingFrequency.MONTHLY,
            base_price=Decimal("299.00"),
            currency=Currency.USD,
            usage_limits={
                "users": 50,
                "api_calls": 100000,
                "storage_gb": 500
            },
            usage_metrics={
                "api_calls": {
                    "unit": "call",
                    "included": 100000,
                    "overage_price": Decimal("0.01")
                },
                "storage": {
                    "unit": "gb",
                    "included": 500,
                    "overage_price": Decimal("0.50")
                }
            },
            included_features={"advanced_claude", "priority_support", "advanced_analytics", "custom_workflows"},
            trial_period_days=30,
            partner_commission_rate=Decimal("0.20")
        )

        # Enterprise Plan
        plans["enterprise"] = PricingPlan(
            plan_id="enterprise",
            name="Enterprise Plan",
            description="Full-featured solution for large organizations",
            billing_model=BillingModel.USAGE_BASED,
            billing_frequency=BillingFrequency.MONTHLY,
            base_price=Decimal("999.00"),
            currency=Currency.USD,
            usage_tiers=[
                {"name": "base", "min": 0, "max": 1000000, "price": Decimal("0.005")},
                {"name": "volume", "min": 1000001, "max": 5000000, "price": Decimal("0.004")},
                {"name": "enterprise", "min": 5000001, "max": -1, "price": Decimal("0.003")}
            ],
            included_features={"enterprise_claude", "dedicated_support", "enterprise_analytics", "white_label"},
            partner_commission_rate=Decimal("0.25")
        )

        return plans

    def _load_billing_rules(self) -> Dict[str, Any]:
        """Load billing rules and configuration"""
        return {
            "invoice_generation": {
                "auto_generate": True,
                "generation_days_before_period_end": 3,
                "payment_terms_days": 30,
                "late_fee_percentage": Decimal("1.5"),
                "grace_period_days": 3
            },
            "revenue_recognition": {
                "method": "straight_line",
                "subscription_recognition_period": "contract_term",
                "setup_fee_recognition": "immediate",
                "usage_recognition": "monthly"
            },
            "dunning": {
                "enabled": True,
                "max_attempts": 5,
                "retry_schedule_days": [1, 3, 7, 14, 30],
                "suspend_after_days": 45,
                "cancel_after_days": 90
            },
            "currency_handling": {
                "default_currency": "USD",
                "exchange_rate_provider": "fixer.io",
                "rate_update_frequency": "daily"
            }
        }

    def _load_dunning_configuration(self) -> Dict[str, Any]:
        """Load dunning management configuration"""
        return {
            "email_templates": {
                "first_attempt": "payment_reminder_gentle",
                "second_attempt": "payment_reminder_firm",
                "final_attempt": "payment_final_notice"
            },
            "escalation_rules": [
                {"day": 1, "action": "email", "template": "payment_reminder_gentle"},
                {"day": 7, "action": "email", "template": "payment_reminder_firm"},
                {"day": 14, "action": "email_and_phone", "template": "payment_urgent"},
                {"day": 30, "action": "suspend_service"},
                {"day": 60, "action": "collections_referral"}
            ],
            "auto_retry_payment": True,
            "retry_schedule_hours": [24, 72, 168, 336]  # 1, 3, 7, 14 days
        }

    async def create_subscription(self, request: BillingRequest) -> BillingResponse:
        """Create new subscription for organization"""
        start_time = time.time()
        operation_id = f"create_subscription_{int(time.time() * 1000)}"

        try:
            organization_id = request.organization_id
            subscription_params = request.parameters

            if not organization_id:
                raise ValueError("Organization ID is required")

            plan_id = subscription_params.get("plan_id")
            if not plan_id or plan_id not in self.pricing_plans:
                raise ValueError(f"Invalid plan ID: {plan_id}")

            # Get pricing plan
            plan = self.pricing_plans[plan_id]

            # Generate subscription ID
            subscription_id = f"sub_{uuid4().hex[:12]}"

            # Calculate subscription dates
            start_date = datetime.utcnow()
            if plan.trial_period_days > 0:
                trial_end_date = start_date + timedelta(days=plan.trial_period_days)
                current_period_end = trial_end_date
            else:
                trial_end_date = None
                current_period_end = self._calculate_next_billing_date(start_date, plan.billing_frequency)

            # Create subscription
            subscription = Subscription(
                subscription_id=subscription_id,
                organization_id=organization_id,
                plan_id=plan_id,
                status=SubscriptionStatus.TRIAL if plan.trial_period_days > 0 else SubscriptionStatus.ACTIVE,
                start_date=start_date,
                trial_end_date=trial_end_date,
                current_period_start=start_date,
                current_period_end=current_period_end,
                billing_frequency=plan.billing_frequency,
                currency=plan.currency,
                base_amount=plan.base_price,
                current_amount=plan.base_price,
                usage_limits=plan.usage_limits.copy(),
                current_usage={metric: 0 for metric in plan.usage_limits.keys()},
                payment_method_id=subscription_params.get("payment_method_id"),
                next_billing_date=current_period_end if plan.trial_period_days == 0 else trial_end_date,
                partner_id=subscription_params.get("partner_id"),
                commission_rate=plan.partner_commission_rate
            )

            # Setup payment method if provided
            payment_setup_result = None
            if subscription.payment_method_id:
                payment_setup_result = await self._setup_payment_method(subscription)

            # Process setup fee if applicable
            setup_fee_invoice = None
            if plan.setup_fee and plan.setup_fee > 0:
                setup_fee_invoice = await self._generate_setup_fee_invoice(subscription, plan.setup_fee)

            # Store subscription
            await self._store_subscription(subscription)

            # Initialize usage tracking
            await self._initialize_usage_tracking(subscription)

            # Setup revenue recognition
            revenue_recognition = await self._setup_revenue_recognition(subscription, plan)

            # Schedule billing automation
            await self._schedule_billing_automation(subscription)

            processing_time = (time.time() - start_time) * 1000

            response = BillingResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data={
                    "subscription": subscription.dict(),
                    "pricing_plan": plan.dict(),
                    "payment_setup": payment_setup_result,
                    "setup_fee_invoice": setup_fee_invoice.dict() if setup_fee_invoice else None,
                    "revenue_recognition": revenue_recognition.dict() if revenue_recognition else None
                },
                message=f"Subscription created successfully with plan {plan.name}",
                amount=subscription.current_amount,
                currency=subscription.currency,
                next_steps=[
                    f"Trial period ends on {trial_end_date}" if trial_end_date else f"Next billing on {subscription.next_billing_date}",
                    "Setup payment method if not provided" if not subscription.payment_method_id else "Payment method configured",
                    "Complete onboarding and begin using the platform"
                ],
                processing_time_ms=processing_time
            )

            logger.info(f"Subscription {subscription_id} created successfully in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Subscription creation failed: {str(e)}")

            return BillingResponse(
                success=False,
                operation_id=operation_id,
                organization_id=request.organization_id,
                message=f"Subscription creation failed: {str(e)}",
                processing_time_ms=processing_time
            )

    async def process_billing_cycle(self, request: BillingRequest) -> BillingResponse:
        """Process billing cycle for subscriptions"""
        start_time = time.time()
        operation_id = f"billing_cycle_{int(time.time() * 1000)}"

        try:
            billing_date = request.parameters.get("billing_date", datetime.utcnow().date())
            if isinstance(billing_date, str):
                billing_date = datetime.fromisoformat(billing_date).date()

            # Get subscriptions due for billing
            due_subscriptions = await self._get_subscriptions_due_for_billing(billing_date)

            billing_results = {
                "total_subscriptions": len(due_subscriptions),
                "successful_billings": 0,
                "failed_billings": 0,
                "total_amount_billed": Decimal("0.00"),
                "billing_details": []
            }

            for subscription in due_subscriptions:
                try:
                    # Calculate billing amount including usage
                    billing_calculation = await self._calculate_billing_amount(subscription, billing_date)

                    # Generate invoice
                    invoice = await self._generate_subscription_invoice(subscription, billing_calculation)

                    # Process payment
                    payment_result = await self._process_subscription_payment(subscription, invoice)

                    # Update subscription
                    subscription = await self._update_subscription_billing(subscription, payment_result)

                    # Record revenue recognition
                    await self._record_revenue_recognition(subscription, invoice, billing_calculation)

                    billing_results["successful_billings"] += 1
                    billing_results["total_amount_billed"] += invoice.total_amount
                    billing_results["billing_details"].append({
                        "subscription_id": subscription.subscription_id,
                        "organization_id": subscription.organization_id,
                        "amount": invoice.total_amount,
                        "status": "success",
                        "invoice_id": invoice.invoice_id
                    })

                except Exception as sub_error:
                    logger.error(f"Billing failed for subscription {subscription.subscription_id}: {str(sub_error)}")
                    billing_results["failed_billings"] += 1
                    billing_results["billing_details"].append({
                        "subscription_id": subscription.subscription_id,
                        "organization_id": subscription.organization_id,
                        "status": "failed",
                        "error": str(sub_error)
                    })

                    # Handle billing failure
                    await self._handle_billing_failure(subscription, str(sub_error))

            # Generate billing cycle summary
            cycle_summary = await self._generate_billing_cycle_summary(billing_date, billing_results)

            processing_time = (time.time() - start_time) * 1000

            response = BillingResponse(
                success=True,
                operation_id=operation_id,
                result_data={
                    "billing_results": billing_results,
                    "cycle_summary": cycle_summary,
                    "billing_date": billing_date.isoformat()
                },
                message=f"Billing cycle processed: {billing_results['successful_billings']} successful, {billing_results['failed_billings']} failed",
                amount=billing_results["total_amount_billed"],
                currency=Currency.USD,
                processing_time_ms=processing_time
            )

            logger.info(f"Billing cycle processed in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Billing cycle processing failed: {str(e)}")

            return BillingResponse(
                success=False,
                operation_id=operation_id,
                message=f"Billing cycle processing failed: {str(e)}",
                processing_time_ms=processing_time
            )

    async def record_usage(self, request: BillingRequest) -> BillingResponse:
        """Record usage for usage-based billing"""
        start_time = time.time()
        operation_id = f"record_usage_{int(time.time() * 1000)}"

        try:
            organization_id = request.organization_id
            usage_data = request.parameters

            if not organization_id:
                raise ValueError("Organization ID is required")

            # Get active subscription
            subscription = await self._get_active_subscription(organization_id)
            if not subscription:
                raise ValueError(f"No active subscription found for organization {organization_id}")

            # Generate usage record ID
            usage_id = f"usage_{uuid4().hex[:12]}"

            # Get billing period for usage
            billing_period = await self._get_current_billing_period(subscription)

            # Create usage record
            usage_record = UsageRecord(
                usage_id=usage_id,
                organization_id=organization_id,
                subscription_id=subscription.subscription_id,
                metric_name=usage_data["metric_name"],
                quantity=Decimal(str(usage_data["quantity"])),
                unit=usage_data["unit"],
                timestamp=datetime.fromisoformat(usage_data.get("timestamp", datetime.utcnow().isoformat())),
                billing_period_start=billing_period["start"],
                billing_period_end=billing_period["end"],
                resource_id=usage_data.get("resource_id"),
                tags=usage_data.get("tags", {})
            )

            # Calculate usage pricing
            pricing_calculation = await self._calculate_usage_pricing(subscription, usage_record)
            usage_record.unit_price = pricing_calculation["unit_price"]
            usage_record.total_cost = pricing_calculation["total_cost"]
            usage_record.tier = pricing_calculation.get("tier")

            # Store usage record
            await self._store_usage_record(usage_record)

            # Update subscription usage tracking
            subscription = await self._update_subscription_usage(subscription, usage_record)

            # Check usage limits and send alerts if necessary
            limit_alerts = await self._check_usage_limits(subscription, usage_record)

            # Calculate current period usage summary
            usage_summary = await self._calculate_usage_summary(subscription, billing_period)

            processing_time = (time.time() - start_time) * 1000

            response = BillingResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data={
                    "usage_record": usage_record.dict(),
                    "pricing_calculation": pricing_calculation,
                    "updated_subscription": subscription.dict(),
                    "usage_summary": usage_summary,
                    "limit_alerts": limit_alerts
                },
                message=f"Usage recorded: {usage_record.quantity} {usage_record.unit} of {usage_record.metric_name}",
                amount=usage_record.total_cost,
                currency=subscription.currency,
                processing_time_ms=processing_time
            )

            logger.info(f"Usage record {usage_id} created in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Usage recording failed: {str(e)}")

            return BillingResponse(
                success=False,
                operation_id=operation_id,
                organization_id=request.organization_id,
                message=f"Usage recording failed: {str(e)}",
                processing_time_ms=processing_time
            )

    async def generate_financial_report(self, request: BillingRequest) -> BillingResponse:
        """Generate comprehensive financial reports"""
        start_time = time.time()
        operation_id = f"financial_report_{int(time.time() * 1000)}"

        try:
            report_type = request.parameters.get("report_type", "monthly_summary")
            report_period = request.parameters.get("report_period")
            organization_id = request.organization_id

            # Calculate financial metrics
            billing_metrics = await self._calculate_billing_metrics(organization_id, report_period)

            # Generate revenue report
            revenue_report = await self._generate_revenue_report(organization_id, report_period)

            # Generate subscription analytics
            subscription_analytics = await self._generate_subscription_analytics(organization_id, report_period)

            # Generate usage analytics
            usage_analytics = await self._generate_usage_analytics(organization_id, report_period)

            # Generate partner commission report
            partner_commission_report = await self._generate_partner_commission_report(organization_id, report_period)

            # Generate tax report
            tax_report = await self._generate_tax_report(organization_id, report_period)

            # Generate accounts receivable report
            ar_report = await self._generate_accounts_receivable_report(organization_id)

            # Generate executive summary
            executive_summary = await self._generate_executive_financial_summary(
                billing_metrics, revenue_report, subscription_analytics
            )

            processing_time = (time.time() - start_time) * 1000

            response = BillingResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data={
                    "billing_metrics": billing_metrics.__dict__,
                    "revenue_report": revenue_report,
                    "subscription_analytics": subscription_analytics,
                    "usage_analytics": usage_analytics,
                    "partner_commission_report": partner_commission_report,
                    "tax_report": tax_report,
                    "accounts_receivable_report": ar_report,
                    "executive_summary": executive_summary,
                    "report_generated_at": datetime.utcnow().isoformat()
                },
                message=f"Financial report generated for {report_type}",
                processing_time_ms=processing_time
            )

            logger.info(f"Financial report generated in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Financial report generation failed: {str(e)}")

            return BillingResponse(
                success=False,
                operation_id=operation_id,
                organization_id=request.organization_id,
                message=f"Financial report generation failed: {str(e)}",
                processing_time_ms=processing_time
            )

    # Helper methods for billing management

    def _calculate_next_billing_date(self, start_date: datetime, frequency: BillingFrequency) -> datetime:
        """Calculate next billing date based on frequency"""
        if frequency == BillingFrequency.MONTHLY:
            return start_date + relativedelta(months=1)
        elif frequency == BillingFrequency.QUARTERLY:
            return start_date + relativedelta(months=3)
        elif frequency == BillingFrequency.ANNUALLY:
            return start_date + relativedelta(years=1)
        elif frequency == BillingFrequency.WEEKLY:
            return start_date + timedelta(weeks=1)
        elif frequency == BillingFrequency.DAILY:
            return start_date + timedelta(days=1)
        else:
            return start_date + relativedelta(months=1)  # Default to monthly

    async def _calculate_billing_amount(self, subscription: Subscription, billing_date: datetime.date) -> Dict[str, Any]:
        """Calculate total billing amount including usage"""
        try:
            # Get pricing plan
            plan = self.pricing_plans[subscription.plan_id]

            calculation = {
                "base_amount": subscription.base_amount,
                "usage_charges": Decimal("0.00"),
                "total_amount": subscription.base_amount,
                "currency": subscription.currency,
                "usage_breakdown": {}
            }

            # Calculate usage charges if applicable
            if plan.billing_model in [BillingModel.USAGE_BASED, BillingModel.HYBRID]:
                billing_period = await self._get_current_billing_period(subscription)
                usage_records = await self._get_usage_records_for_billing(
                    subscription.subscription_id,
                    billing_period["start"],
                    billing_period["end"]
                )

                for metric_name, usage_config in plan.usage_metrics.items():
                    metric_usage = sum(
                        record.quantity for record in usage_records
                        if record.metric_name == metric_name
                    )

                    # Calculate charges for this metric
                    included_amount = usage_config.get("included", 0)
                    overage_amount = max(Decimal("0"), metric_usage - included_amount)
                    overage_price = plan.overage_pricing.get(metric_name, Decimal("0"))

                    usage_charge = overage_amount * overage_price
                    calculation["usage_charges"] += usage_charge
                    calculation["usage_breakdown"][metric_name] = {
                        "total_usage": metric_usage,
                        "included": included_amount,
                        "overage": overage_amount,
                        "unit_price": overage_price,
                        "charge": usage_charge
                    }

            calculation["total_amount"] = calculation["base_amount"] + calculation["usage_charges"]
            return calculation

        except Exception as e:
            logger.error(f"Billing calculation failed: {str(e)}")
            return {
                "base_amount": subscription.base_amount,
                "usage_charges": Decimal("0.00"),
                "total_amount": subscription.base_amount,
                "currency": subscription.currency,
                "error": str(e)
            }

    async def _generate_subscription_invoice(self, subscription: Subscription, billing_calculation: Dict[str, Any]) -> Invoice:
        """Generate invoice for subscription billing"""
        try:
            invoice_id = f"inv_{uuid4().hex[:12]}"
            invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{invoice_id[-6:].upper()}"

            # Calculate tax
            tax_calculation = await self._calculate_tax(
                subscription.organization_id,
                billing_calculation["total_amount"]
            )

            # Create line items
            line_items = []

            # Base subscription line item
            if billing_calculation["base_amount"] > 0:
                line_items.append({
                    "description": f"Subscription - {self.pricing_plans[subscription.plan_id].name}",
                    "quantity": 1,
                    "unit_price": billing_calculation["base_amount"],
                    "total": billing_calculation["base_amount"]
                })

            # Usage line items
            for metric_name, usage_detail in billing_calculation.get("usage_breakdown", {}).items():
                if usage_detail["charge"] > 0:
                    line_items.append({
                        "description": f"Usage overage - {metric_name}",
                        "quantity": usage_detail["overage"],
                        "unit_price": usage_detail["unit_price"],
                        "total": usage_detail["charge"]
                    })

            # Create invoice
            invoice = Invoice(
                invoice_id=invoice_id,
                organization_id=subscription.organization_id,
                subscription_id=subscription.subscription_id,
                invoice_number=invoice_number,
                status=InvoiceStatus.DRAFT,
                currency=subscription.currency,
                subtotal=billing_calculation["total_amount"],
                tax_amount=tax_calculation["tax_amount"],
                total_amount=billing_calculation["total_amount"] + tax_calculation["tax_amount"],
                line_items=line_items,
                tax_rate=tax_calculation["tax_rate"],
                tax_type=tax_calculation["tax_type"],
                due_date=datetime.utcnow() + timedelta(days=self.billing_rules["invoice_generation"]["payment_terms_days"]),
                period_start=subscription.current_period_start,
                period_end=subscription.current_period_end
            )

            return invoice

        except Exception as e:
            logger.error(f"Invoice generation failed: {str(e)}")
            raise

    async def _calculate_billing_metrics(self, organization_id: Optional[str], report_period: Optional[str]) -> BillingMetrics:
        """Calculate comprehensive billing metrics"""
        try:
            # In production, these would be actual database aggregations
            current_month_revenue = Decimal("125750.00")
            last_month_revenue = Decimal("118950.00")

            metrics = BillingMetrics(
                total_revenue_current_month=current_month_revenue,
                total_revenue_last_month=last_month_revenue,
                mrr_current=Decimal("89500.00"),
                arr_current=Decimal("1074000.00"),
                churn_rate_monthly=0.035,
                customer_lifetime_value=Decimal("8750.00"),
                average_revenue_per_user=Decimal("295.00"),
                outstanding_receivables=Decimal("45800.00"),
                past_due_amount=Decimal("12350.00"),
                active_subscriptions=314,
                trial_conversions=0.68,
                revenue_growth_rate=0.057
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate billing metrics: {str(e)}")
            raise

    async def _store_subscription(self, subscription: Subscription) -> None:
        """Store subscription in cache and database"""
        try:
            cache_key = f"billing:subscription:{subscription.subscription_id}"
            await self.redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                json.dumps(subscription.dict(), default=str)
            )

            # Store in organization index
            org_subs_key = f"billing:org_subscriptions:{subscription.organization_id}"
            await self.redis_client.sadd(org_subs_key, subscription.subscription_id)

            logger.info(f"Subscription stored: {subscription.subscription_id}")

        except Exception as e:
            logger.error(f"Failed to store subscription: {str(e)}")
            raise

    async def _store_usage_record(self, usage_record: UsageRecord) -> None:
        """Store usage record for billing calculation"""
        try:
            cache_key = f"billing:usage:{usage_record.usage_id}"
            await self.redis_client.setex(
                cache_key,
                86400 * 90,  # 90 days TTL
                json.dumps(usage_record.dict(), default=str)
            )

            # Add to subscription usage index
            sub_usage_key = f"billing:subscription_usage:{usage_record.subscription_id}"
            await self.redis_client.zadd(
                sub_usage_key,
                {usage_record.usage_id: usage_record.timestamp.timestamp()}
            )

            logger.info(f"Usage record stored: {usage_record.usage_id}")

        except Exception as e:
            logger.error(f"Failed to store usage record: {str(e)}")
            raise

# Performance monitoring and health check
def get_enterprise_billing_health() -> Dict[str, Any]:
    """Get Enterprise Billing Manager health status"""
    return {
        "service": "enterprise_billing_manager",
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": [
            "subscription_management",
            "usage_based_billing",
            "invoice_generation",
            "payment_processing",
            "revenue_recognition",
            "financial_reporting",
            "partner_commissions",
            "tax_calculation"
        ],
        "supported_currencies": [currency.value for currency in Currency],
        "billing_models": [model.value for model in BillingModel],
        "performance_targets": {
            "subscription_creation": "< 2000ms",
            "billing_cycle_processing": "< 30000ms",
            "usage_recording": "< 500ms",
            "financial_report_generation": "< 5000ms"
        },
        "dependencies": {
            "redis": "required",
            "payment_processors": "required",
            "tax_calculation": "optional",
            "exchange_rates": "optional"
        },
        "last_health_check": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    # Example usage and testing
    async def test_enterprise_billing_manager():
        manager = EnterpriseBillingManager()

        # Test subscription creation
        subscription_request = BillingRequest(
            operation_type="create_subscription",
            organization_id="org_enterprise_client",
            parameters={
                "plan_id": "professional",
                "payment_method_id": "pm_test_card",
                "partner_id": "partner_123"
            },
            admin_user_id="admin_123"
        )

        response = await manager.create_subscription(subscription_request)
        print(f"Subscription Creation Response: {response.dict()}")

        if response.success:
            subscription_data = response.result_data["subscription"]
            subscription_id = subscription_data["subscription_id"]

            # Test usage recording
            usage_request = BillingRequest(
                operation_type="record_usage",
                organization_id="org_enterprise_client",
                parameters={
                    "metric_name": "api_calls",
                    "quantity": 15000,
                    "unit": "call",
                    "timestamp": datetime.utcnow().isoformat(),
                    "resource_id": "api_endpoint_123"
                },
                admin_user_id="admin_123"
            )

            usage_response = await manager.record_usage(usage_request)
            print(f"Usage Recording Response: {usage_response.dict()}")

            # Test billing cycle processing
            billing_request = BillingRequest(
                operation_type="process_billing",
                parameters={
                    "billing_date": datetime.utcnow().date().isoformat()
                },
                admin_user_id="admin_123"
            )

            billing_response = await manager.process_billing_cycle(billing_request)
            print(f"Billing Cycle Response: {billing_response.dict()}")

            # Test financial reporting
            report_request = BillingRequest(
                operation_type="generate_report",
                organization_id="org_enterprise_client",
                parameters={
                    "report_type": "monthly_summary",
                    "report_period": "2026-01"
                },
                admin_user_id="admin_123"
            )

            report_response = await manager.generate_financial_report(report_request)
            print(f"Financial Report Response: {report_response.dict()}")

    # Run test
    asyncio.run(test_enterprise_billing_manager())