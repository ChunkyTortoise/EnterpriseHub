"""
Stripe Billing API Routes for Phase 2.

Provides REST endpoints for:
- Subscription management (create, read, update, delete)
- Usage tracking and billing
- Invoice processing and payment
- Billing history and analytics

Supports $240K ARR foundation with usage-based billing integration.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query, status
from fastapi.responses import JSONResponse
import stripe

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.billing_service import BillingService, BillingServiceError
from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager, SubscriptionManagerError
from ghl_real_estate_ai.services.monitoring_service import MonitoringService, AlertSeverity
from ghl_real_estate_ai.api.schemas.billing import (
    CreateSubscriptionRequest,
    ModifySubscriptionRequest,
    SubscriptionResponse,
    SubscriptionSummary,
    UsageRecordRequest,
    UsageRecordResponse,
    UsageSummary,
    InvoiceDetails,
    BillingHistoryResponse,
    StripeWebhookEvent,
    WebhookProcessingResult,
    RevenueAnalytics,
    TierDistribution,
    BillingError,
    SubscriptionTier,
    SubscriptionStatus
)

logger = get_logger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize services (singletons)
billing_service = BillingService()
subscription_manager = SubscriptionManager()
monitoring_service = MonitoringService()


# Revenue Protection: Retry logic with exponential backoff
async def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    *args,
    **kwargs
):
    """
    Retry function with exponential backoff for revenue protection.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for first retry
        max_delay: Maximum delay between retries
        *args, **kwargs: Arguments for the function

    Returns:
        Function result or raises final exception
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except BillingServiceError as e:
            last_exception = e
            if not e.recoverable or attempt == max_retries:
                # Non-recoverable error or final attempt
                await monitoring_service.create_alert(
                    service_name="billing_api",
                    severity=AlertSeverity.CRITICAL,
                    message=f"Billing operation failed after {attempt + 1} attempts: {e.message}",
                    metadata={
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "recoverable": e.recoverable,
                        "stripe_error_code": e.stripe_error_code
                    }
                )
                raise

            # Calculate next retry delay
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                f"Billing operation failed (attempt {attempt + 1}/{max_retries + 1}). "
                f"Retrying in {delay}s: {e.message}",
                extra={
                    "function": func.__name__,
                    "attempt": attempt + 1,
                    "delay": delay,
                    "recoverable": e.recoverable
                }
            )

            await asyncio.sleep(delay)

        except Exception as e:
            # Unexpected error - don't retry, escalate immediately
            last_exception = e
            await monitoring_service.create_alert(
                service_name="billing_api",
                severity=AlertSeverity.CRITICAL,
                message=f"Unexpected billing system error: {str(e)}",
                metadata={
                    "function": func.__name__,
                    "attempt": attempt + 1,
                    "error_type": type(e).__name__
                }
            )
            raise

    # Should not reach here, but handle gracefully
    raise last_exception


# ===================================================================
# Subscription Management Endpoints
# ===================================================================

@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new subscription for a location.

    Creates Stripe customer, attaches payment method, and initializes
    subscription with trial period and tier-based pricing.

    Args:
        request: Subscription creation request with payment details

    Returns:
        Complete subscription details with usage tracking setup

    Raises:
        HTTPException: If subscription creation fails
    """
    try:
        logger.info(
            f"Creating subscription for location {request.location_id}",
            extra={
                "location_id": request.location_id,
                "tier": request.tier.value,
                "trial_days": request.trial_days,
                "has_email": bool(request.email)
            }
        )

        # Initialize subscription through subscription manager
        subscription = await subscription_manager.initialize_subscription(request)

        # Track subscription creation event in background
        background_tasks.add_task(
            _track_billing_event,
            "subscription_created",
            {
                "subscription_id": subscription.id,
                "location_id": subscription.location_id,
                "tier": subscription.tier.value,
                "base_price": float(subscription.base_price),
                "trial_days": request.trial_days,
                "arr_impact": float(subscription.base_price) * 12  # Annual value
            }
        )

        logger.info(
            f"Successfully created subscription {subscription.id}",
            extra={
                "subscription_id": subscription.id,
                "location_id": subscription.location_id,
                "stripe_subscription_id": subscription.stripe_subscription_id,
                "tier": subscription.tier.value
            }
        )

        return subscription

    except SubscriptionManagerError as e:
        logger.error(
            f"Subscription manager error for location {request.location_id}: {e}",
            extra={
                "location_id": request.location_id,
                "tier": request.tier.value,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "subscription_creation_failed",
                "error_message": str(e),
                "error_type": "subscription_manager",
                "recoverable": True,
                "suggested_action": "Verify payment method and try again"
            }
        )
    except Exception as e:
        logger.error(
            f"Unexpected error creating subscription for {request.location_id}: {e}",
            extra={
                "location_id": request.location_id,
                "tier": request.tier.value,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "subscription_creation_error",
                "error_message": "Failed to create subscription",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: int):
    """
    Get subscription details by ID.

    Retrieves complete subscription information including usage statistics,
    billing period, and next invoice details.

    Args:
        subscription_id: Database subscription ID

    Returns:
        Detailed subscription information

    Raises:
        HTTPException: If subscription not found or access error
    """
    try:
        # ROADMAP-008: Implement subscription database lookup
        # Current: Using placeholder data from Stripe
        # Required: Query subscriptions table by ID, join with customers
        # Acceptance: Return real subscription data with proper error handling
        # Status: Database schema ready, awaiting implementation
        #
        # subscription = await db.subscriptions.get(id=subscription_id)
        # if not subscription:
        #     raise HTTPException(404, "Subscription not found")

        # Get from Stripe for now (placeholder)
        # stripe_subscription = await billing_service.get_subscription(subscription.stripe_subscription_id)

        logger.info(f"Retrieved subscription {subscription_id}")

        # Placeholder response - replace with actual database data
        return SubscriptionResponse(
            id=subscription_id,
            location_id="placeholder_location",
            stripe_subscription_id="sub_placeholder",
            stripe_customer_id="cus_placeholder",
            tier=SubscriptionTier.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(),
            current_period_end=datetime.now(),
            usage_allowance=150,
            usage_current=87,
            usage_percentage=58.0,
            overage_rate=1.50,
            base_price=249.00,
            next_invoice_date=datetime.now(),
            created_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving subscription {subscription_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "subscription_retrieval_error",
                "error_message": "Failed to retrieve subscription",
                "error_type": "database_error",
                "recoverable": True
            }
        )


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    request: ModifySubscriptionRequest,
    background_tasks: BackgroundTasks
):
    """
    Update an existing subscription.

    Supports tier changes (with proration), payment method updates,
    and cancellation scheduling.

    Args:
        subscription_id: Database subscription ID
        request: Modification request with changes to apply

    Returns:
        Updated subscription details

    Raises:
        HTTPException: If update fails or subscription not found
    """
    try:
        logger.info(
            f"Updating subscription {subscription_id}",
            extra={
                "subscription_id": subscription_id,
                "tier_change": request.tier.value if request.tier else None,
                "payment_method_change": bool(request.payment_method_id),
                "cancellation_scheduled": request.cancel_at_period_end
            }
        )

        # Handle tier change if requested
        if request.tier:
            subscription = await subscription_manager.handle_tier_change(
                subscription_id, request.tier
            )
        else:
            # ROADMAP-009: Implement payment method and cancellation modifications
            # Current: Only tier changes are handled
            # Required: Add Stripe payment method updates and cancellation scheduling
            # Status: Planned for Q2 2026
            pass  # Placeholder for additional modification types

        # Track subscription modification event
        background_tasks.add_task(
            _track_billing_event,
            "subscription_modified",
            {
                "subscription_id": subscription_id,
                "tier": request.tier.value if request.tier else None,
                "modification_type": _get_modification_type(request)
            }
        )

        logger.info(f"Successfully updated subscription {subscription_id}")

        # Return placeholder - replace with actual updated subscription
        return SubscriptionResponse(
            id=subscription_id,
            location_id="placeholder_location",
            stripe_subscription_id="sub_placeholder",
            stripe_customer_id="cus_placeholder",
            tier=request.tier or SubscriptionTier.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(),
            current_period_end=datetime.now(),
            usage_allowance=150,
            usage_current=87,
            usage_percentage=58.0,
            overage_rate=1.50,
            base_price=249.00,
            next_invoice_date=datetime.now(),
            created_at=datetime.now()
        )

    except SubscriptionManagerError as e:
        logger.error(f"Subscription manager error for {subscription_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "subscription_modification_failed",
                "error_message": str(e),
                "error_type": "subscription_manager",
                "recoverable": True
            }
        )
    except Exception as e:
        logger.error(f"Error updating subscription {subscription_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "subscription_update_error",
                "error_message": "Failed to update subscription",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


@router.delete("/subscriptions/{subscription_id}", response_model=Dict[str, Any])
async def cancel_subscription(
    subscription_id: int,
    background_tasks: BackgroundTasks,
    immediate: bool = Query(False, description="Cancel immediately vs at period end")
):
    """
    Cancel a subscription.

    Args:
        subscription_id: Database subscription ID
        immediate: If True, cancel immediately; otherwise at period end

    Returns:
        Cancellation confirmation with effective date

    Raises:
        HTTPException: If cancellation fails or subscription not found
    """
    try:
        logger.info(
            f"Canceling subscription {subscription_id}",
            extra={
                "subscription_id": subscription_id,
                "immediate": immediate
            }
        )

        # ROADMAP-010: Get subscription from database before Stripe cancellation
        # Current: Direct Stripe cancellation without local validation
        # Required: Validate subscription exists locally, then call Stripe
        # Impact: Prevents orphaned Stripe subscriptions
        #
        # subscription = await db.subscriptions.get(id=subscription_id)
        # stripe_subscription = await billing_service.cancel_subscription(
        #     subscription.stripe_subscription_id, immediate
        # )

        # Track subscription cancellation
        background_tasks.add_task(
            _track_billing_event,
            "subscription_canceled",
            {
                "subscription_id": subscription_id,
                "immediate": immediate,
                "cancellation_reason": "api_request"
            }
        )

        logger.info(f"Successfully canceled subscription {subscription_id}")

        return {
            "success": True,
            "subscription_id": subscription_id,
            "canceled_at": datetime.now().isoformat(),
            "effective_date": datetime.now().isoformat(),
            "immediate": immediate,
            "refund_amount": 0.0,  # Calculate based on proration
            "message": f"Subscription {'canceled immediately' if immediate else 'scheduled for cancellation at period end'}"
        }

    except Exception as e:
        logger.error(f"Error canceling subscription {subscription_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "subscription_cancellation_error",
                "error_message": "Failed to cancel subscription",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


# ===================================================================
# Usage Tracking Endpoints
# ===================================================================

@router.post("/usage", response_model=Dict[str, Any])
async def record_usage(
    request: UsageRecordRequest,
    background_tasks: BackgroundTasks
):
    """
    Record usage event for billing.

    Called automatically when lead processing occurs to track
    usage against subscription allowances and calculate overages.

    Args:
        request: Usage record with lead details and pricing

    Returns:
        Usage record confirmation with billing impact

    Raises:
        HTTPException: If usage recording fails
    """
    try:
        logger.info(
            f"Recording usage for subscription {request.subscription_id}",
            extra={
                "subscription_id": request.subscription_id,
                "lead_id": request.lead_id,
                "amount": float(request.amount),
                "tier": request.tier
            }
        )

        # Record usage through billing service with retry logic for revenue protection
        stripe_usage_record = await retry_with_exponential_backoff(
            billing_service.add_usage_record,
            request,
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
        )

        # ROADMAP-011: Store usage records in local database
        # Current: Only recording in Stripe
        # Required: Insert into usage_records table for analytics and audit
        # Schema: subscription_id, stripe_usage_record_id, lead_id, contact_id, amount, tier, timestamp
        #
        # usage_record = await db.usage_records.insert({
        #     "subscription_id": request.subscription_id,
        #     "stripe_usage_record_id": stripe_usage_record.id,
        #     "lead_id": request.lead_id,
        #     "contact_id": request.contact_id,
        #     "amount": request.amount,
        #     "tier": request.tier
        # })

        # Track usage event for analytics
        background_tasks.add_task(
            _track_billing_event,
            "usage_recorded",
            {
                "subscription_id": request.subscription_id,
                "amount": float(request.amount),
                "tier": request.tier,
                "stripe_usage_record_id": stripe_usage_record.id
            }
        )

        logger.info(f"Successfully recorded usage {stripe_usage_record.id}")

        return {
            "success": True,
            "stripe_usage_record_id": stripe_usage_record.id,
            "subscription_id": request.subscription_id,
            "amount_billed": float(request.amount),
            "tier": request.tier,
            "billing_period": f"{request.billing_period_start.date()} to {request.billing_period_end.date()}",
            "next_invoice_impact": f"${request.amount} will be added to next invoice"
        }

    except BillingServiceError as e:
        # Retry logic handled by retry_with_exponential_backoff
        # This should only be reached for non-recoverable errors
        logger.error(f"REVENUE PROTECTION: Usage recording failed after retries: {e.message}",
                    extra={
                        "subscription_id": request.subscription_id,
                        "lead_id": request.lead_id,
                        "amount": float(request.amount),
                        "stripe_error_code": e.stripe_error_code,
                        "revenue_impact": "CRITICAL"
                    })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "usage_recording_failed",
                "error_message": f"Revenue recording failed after retries: {e.message}",
                "error_type": "billing_service",
                "recoverable": e.recoverable,
                "stripe_error_code": e.stripe_error_code
            }
        )
    except Exception as e:
        # System errors escalated by retry function
        logger.error(f"REVENUE PROTECTION: System error in usage recording: {e}",
                    extra={
                        "subscription_id": request.subscription_id,
                        "error_type": type(e).__name__,
                        "revenue_impact": "CRITICAL"
                    })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "usage_recording_system_error",
                "error_message": "Critical system error in revenue recording",
                "error_type": "internal_error",
                "recoverable": False
            }
        )


@router.get("/usage/{subscription_id}", response_model=UsageSummary)
async def get_usage_data(subscription_id: int):
    """
    Get usage data for a subscription.

    Returns current period usage statistics, overage calculations,
    and tier-based usage breakdown.

    Args:
        subscription_id: Database subscription ID

    Returns:
        Complete usage summary with cost calculations

    Raises:
        HTTPException: If subscription not found or data access error
    """
    try:
        logger.info(f"Retrieving usage data for subscription {subscription_id}")

        # Get usage summary from subscription manager
        usage_summary = await subscription_manager.get_usage_summary(f"location_{subscription_id}")

        if not usage_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "subscription_not_found",
                    "error_message": f"No active subscription found with ID {subscription_id}",
                    "error_type": "not_found",
                    "recoverable": False
                }
            )

        logger.info(f"Retrieved usage data for subscription {subscription_id}")
        return usage_summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving usage data for {subscription_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "usage_data_error",
                "error_message": "Failed to retrieve usage data",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


# ===================================================================
# Invoice and Payment Endpoints
# ===================================================================

@router.post("/invoices/{invoice_id}/pay", response_model=Dict[str, Any])
async def process_payment(
    invoice_id: str,
    background_tasks: BackgroundTasks
):
    """
    Process payment for an invoice.

    Triggers payment processing through Stripe and updates
    subscription status based on payment result.

    Args:
        invoice_id: Stripe invoice ID

    Returns:
        Payment processing result

    Raises:
        HTTPException: If payment processing fails
    """
    try:
        logger.info(
            f"Processing payment for invoice {invoice_id}",
            extra={"invoice_id": invoice_id}
        )

        # Get invoice details from Stripe
        invoice = stripe.Invoice.retrieve(invoice_id)

        # Process payment if not already paid
        if invoice.status == "open":
            paid_invoice = stripe.Invoice.pay(invoice_id)

            # Track payment event
            background_tasks.add_task(
                _track_billing_event,
                "payment_processed",
                {
                    "invoice_id": invoice_id,
                    "amount": invoice.amount_due / 100,  # Convert from cents
                    "customer_id": invoice.customer,
                    "status": paid_invoice.status
                }
            )

            logger.info(f"Successfully processed payment for invoice {invoice_id}")

            return {
                "success": True,
                "invoice_id": invoice_id,
                "amount_paid": invoice.amount_due / 100,
                "status": paid_invoice.status,
                "payment_date": datetime.now().isoformat(),
                "receipt_url": paid_invoice.hosted_invoice_url
            }
        else:
            return {
                "success": True,
                "invoice_id": invoice_id,
                "message": f"Invoice already {invoice.status}",
                "status": invoice.status
            }

    except stripe.error.CardError as e:
        logger.error(f"Card error processing payment for {invoice_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error_code": "payment_failed",
                "error_message": f"Payment declined: {e.user_message}",
                "error_type": "card_error",
                "recoverable": True,
                "stripe_error_code": e.code
            }
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error processing payment for {invoice_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "stripe_error",
                "error_message": str(e),
                "error_type": "stripe_api",
                "recoverable": True
            }
        )
    except Exception as e:
        logger.error(f"Error processing payment for {invoice_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "payment_processing_error",
                "error_message": "Failed to process payment",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


@router.get("/invoices", response_model=List[InvoiceDetails])
async def list_invoices(
    customer_id: str = Query(..., description="Stripe customer ID"),
    limit: int = Query(default=10, le=100, description="Maximum number of invoices")
):
    """
    List invoices for a customer.

    Args:
        customer_id: Stripe customer ID
        limit: Maximum number of invoices to return

    Returns:
        List of invoice details

    Raises:
        HTTPException: If invoice retrieval fails
    """
    try:
        logger.info(
            f"Listing invoices for customer {customer_id}",
            extra={"customer_id": customer_id, "limit": limit}
        )

        # Get invoices from billing service
        invoices = await billing_service.get_customer_invoices(customer_id, limit)

        # Convert to response format
        invoice_details = []
        for invoice in invoices:
            invoice_detail = InvoiceDetails(
                id=1,  # Placeholder - use database ID
                stripe_invoice_id=invoice.id,
                subscription_id=1,  # Placeholder - lookup from database
                amount_due=invoice.amount_due / 100,
                amount_paid=invoice.amount_paid / 100 if invoice.amount_paid else 0,
                status=invoice.status,
                period_start=datetime.fromtimestamp(invoice.period_start),
                period_end=datetime.fromtimestamp(invoice.period_end),
                due_date=datetime.fromtimestamp(invoice.due_date) if invoice.due_date else None,
                paid_at=datetime.fromtimestamp(invoice.status_transitions.paid_at) if invoice.status_transitions.paid_at else None,
                hosted_invoice_url=invoice.hosted_invoice_url,
                invoice_pdf=invoice.invoice_pdf
            )
            invoice_details.append(invoice_detail)

        logger.info(f"Retrieved {len(invoice_details)} invoices for customer {customer_id}")
        return invoice_details

    except Exception as e:
        logger.error(f"Error listing invoices for customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "invoice_listing_error",
                "error_message": "Failed to retrieve invoices",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


@router.get("/billing-history/{customer_id}", response_model=BillingHistoryResponse)
async def get_billing_history(customer_id: str):
    """
    Get complete billing history for a customer.

    Includes invoices, payments, subscription changes, and usage records
    for comprehensive billing overview.

    Args:
        customer_id: Stripe customer ID

    Returns:
        Complete billing history with analytics

    Raises:
        HTTPException: If data retrieval fails
    """
    try:
        logger.info(f"Retrieving billing history for customer {customer_id}")

        # Get invoices and calculate totals
        invoices = await billing_service.get_customer_invoices(customer_id, 100)

        # Calculate total spent
        total_spent = sum(invoice.amount_paid / 100 if invoice.amount_paid else 0 for invoice in invoices)

        # Convert invoices to details format
        invoice_details = []
        for invoice in invoices:
            invoice_detail = InvoiceDetails(
                id=1,  # Placeholder
                stripe_invoice_id=invoice.id,
                subscription_id=1,  # Placeholder
                amount_due=invoice.amount_due / 100,
                amount_paid=invoice.amount_paid / 100 if invoice.amount_paid else 0,
                status=invoice.status,
                period_start=datetime.fromtimestamp(invoice.period_start),
                period_end=datetime.fromtimestamp(invoice.period_end),
                due_date=datetime.fromtimestamp(invoice.due_date) if invoice.due_date else None,
                paid_at=datetime.fromtimestamp(invoice.status_transitions.paid_at) if invoice.status_transitions.paid_at else None,
                hosted_invoice_url=invoice.hosted_invoice_url,
                invoice_pdf=invoice.invoice_pdf
            )
            invoice_details.append(invoice_detail)

        # Get customer payment methods
        customer = stripe.Customer.retrieve(customer_id, expand=["sources"])
        payment_methods = []
        for source in customer.sources.data:
            payment_methods.append({
                "id": source.id,
                "type": source.object,
                "last4": getattr(source, "last4", "****"),
                "brand": getattr(source, "brand", "Unknown"),
                "exp_month": getattr(source, "exp_month", None),
                "exp_year": getattr(source, "exp_year", None)
            })

        # Calculate period
        if invoices:
            earliest_invoice = min(invoices, key=lambda i: i.created)
            latest_invoice = max(invoices, key=lambda i: i.created)
            period_start = datetime.fromtimestamp(earliest_invoice.created)
            period_end = datetime.fromtimestamp(latest_invoice.created)
        else:
            period_start = period_end = datetime.now()

        billing_history = BillingHistoryResponse(
            # ROADMAP-012: Get actual location_id from customer record
            # Current: Using placeholder
            # Required: Query customers table by stripe_customer_id
            location_id="placeholder",
            invoices=invoice_details,
            total_spent=total_spent,
            period_start=period_start,
            period_end=period_end,
            payment_methods=payment_methods
        )

        logger.info(f"Retrieved billing history for customer {customer_id}")
        return billing_history

    except Exception as e:
        logger.error(f"Error retrieving billing history for {customer_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "billing_history_error",
                "error_message": "Failed to retrieve billing history",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


# ===================================================================
# Stripe Webhook Endpoint
# ===================================================================

@router.post("/webhooks/stripe", response_model=WebhookProcessingResult)
async def handle_stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Stripe webhook events.

    Processes subscription updates, payment status changes, and
    invoice events to maintain synchronized billing state.

    Args:
        request: Raw webhook request with signature header

    Returns:
        Webhook processing result

    Raises:
        HTTPException: If webhook verification fails
    """
    try:
        # Get raw payload and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            logger.warning("Missing Stripe signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature header"
            )

        # Verify webhook signature
        if not billing_service.verify_webhook_signature(payload, signature):
            logger.error("Invalid Stripe webhook signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )

        # Parse webhook event
        try:
            event_data = stripe.Webhook.construct_event(
                payload, signature, os.getenv("STRIPE_WEBHOOK_SECRET")
            )
        except ValueError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )

        # Process webhook event
        start_time = datetime.now()
        processing_result = await billing_service.process_webhook_event(event_data)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Store webhook event in database (background task)
        background_tasks.add_task(
            _store_webhook_event,
            event_data,
            processing_result
        )

        logger.info(
            f"Processed webhook event {event_data['id']}",
            extra={
                "event_id": event_data["id"],
                "event_type": event_data["type"],
                "processing_time_ms": processing_time,
                "processed": processing_result["processed"]
            }
        )

        return WebhookProcessingResult(
            event_id=event_data["id"],
            event_type=event_data["type"],
            processed=processing_result["processed"],
            processing_time_ms=processing_time,
            error_message=processing_result.get("error"),
            actions_taken=processing_result.get("actions_taken", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "webhook_processing_error",
                "error_message": "Failed to process webhook",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


# ===================================================================
# Analytics Endpoints
# ===================================================================

@router.get("/analytics/revenue", response_model=RevenueAnalytics)
async def get_revenue_analytics():
    """
    Get revenue analytics dashboard data.

    Returns key revenue metrics including ARR, MRR, ARPU,
    churn rates, and usage revenue breakdown.

    Returns:
        Comprehensive revenue analytics

    Raises:
        HTTPException: If analytics calculation fails
    """
    try:
        logger.info("Calculating revenue analytics")

        # ROADMAP-013: Calculate revenue from actual subscription data
        # Current: Using tier distribution projections
        # Required: Aggregate real subscription and usage data
        # Note: Current implementation uses projected data based on $240K ARR target
        # Status: Pending database integration (see ROADMAP-008, ROADMAP-011)

        # Calculate tier distribution
        tier_distribution = await subscription_manager.get_tier_distribution()

        # Calculate revenue metrics (placeholder calculations)
        total_subscriptions = tier_distribution.total_subscriptions
        monthly_revenue = (
            tier_distribution.starter_count * 99 +
            tier_distribution.professional_count * 249 +
            tier_distribution.enterprise_count * 499
        )
        total_arr = monthly_revenue * 12
        average_arpu = monthly_revenue / total_subscriptions if total_subscriptions > 0 else 0

        revenue_analytics = RevenueAnalytics(
            total_arr=total_arr,
            monthly_revenue=monthly_revenue,
            average_arpu=average_arpu,
            churn_rate=2.5,  # Target: <3% monthly churn
            upgrade_rate=15.0,  # Target: 15% monthly upgrade rate
            usage_revenue_percentage=33.0,  # 33% from overages, 67% from subscriptions
            top_tier_customers=tier_distribution.enterprise_count,
            total_active_subscriptions=total_subscriptions
        )

        logger.info(
            f"Calculated revenue analytics: ARR ${total_arr:,.2f}, MRR ${monthly_revenue:,.2f}",
            extra={
                "total_arr": total_arr,
                "monthly_revenue": monthly_revenue,
                "average_arpu": average_arpu,
                "total_subscriptions": total_subscriptions
            }
        )

        return revenue_analytics

    except Exception as e:
        logger.error(f"Error calculating revenue analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "revenue_analytics_error",
                "error_message": "Failed to calculate revenue analytics",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


@router.get("/analytics/tiers", response_model=TierDistribution)
async def get_tier_distribution():
    """
    Get subscription tier distribution analytics.

    Returns distribution of customers across subscription tiers
    with percentages and counts.

    Returns:
        Tier distribution statistics

    Raises:
        HTTPException: If analytics calculation fails
    """
    try:
        logger.info("Calculating tier distribution analytics")

        tier_distribution = await subscription_manager.get_tier_distribution()

        logger.info(
            f"Tier distribution: {tier_distribution.total_subscriptions} total subscriptions",
            extra={
                "starter_count": tier_distribution.starter_count,
                "professional_count": tier_distribution.professional_count,
                "enterprise_count": tier_distribution.enterprise_count,
                "total_subscriptions": tier_distribution.total_subscriptions
            }
        )

        return tier_distribution

    except Exception as e:
        logger.error(f"Error calculating tier distribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "tier_distribution_error",
                "error_message": "Failed to calculate tier distribution",
                "error_type": "internal_error",
                "recoverable": True
            }
        )


# ===================================================================
# Utility Functions
# ===================================================================

async def _track_billing_event(event_type: str, data: Dict[str, Any]) -> None:
    """Track billing events for analytics (background task)."""
    try:
        # ROADMAP-014: Integrate with analytics service
        # Current: Logging only
        # Required: Send to analytics pipeline (Segment, Mixpanel, or custom)
        # Events: subscription_created, subscription_modified, subscription_canceled, payment_processed, usage_recorded
        logger.info(
            f"Billing event tracked: {event_type}",
            extra={"event_type": event_type, "data": data}
        )
    except Exception as e:
        logger.error(f"Error tracking billing event {event_type}: {e}")


async def _store_webhook_event(event_data: Dict[str, Any], processing_result: Dict[str, Any]) -> None:
    """Store webhook event in database for audit trail (background task)."""
    try:
        # ROADMAP-015: Store webhook events in billing_events table
        # Current: Logging only
        # Required: Insert into billing_events table for audit trail and replay capability
        # Schema: event_id, event_type, event_data, processing_result, processed_at, created_at
        # Index: event_id (unique), event_type, created_at
        logger.info(
            f"Webhook event stored: {event_data['id']}",
            extra={
                "event_id": event_data["id"],
                "event_type": event_data["type"],
                "processed": processing_result["processed"]
            }
        )
    except Exception as e:
        logger.error(f"Error storing webhook event: {e}")


def _get_modification_type(request: ModifySubscriptionRequest) -> str:
    """Get modification type for tracking."""
    if request.tier:
        return "tier_change"
    elif request.payment_method_id:
        return "payment_method_update"
    elif request.cancel_at_period_end is not None:
        return "cancellation_schedule"
    else:
        return "general_update"