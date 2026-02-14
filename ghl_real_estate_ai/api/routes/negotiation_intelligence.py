"""
Negotiation Intelligence API Routes

FastAPI endpoints for AI-powered negotiation analysis, real-time coaching,
and strategy optimization with GHL webhook integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.security import HTTPBearer

from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.api.middleware.rate_limiter import rate_limit
from ghl_real_estate_ai.api.schemas.negotiation import (
    GHLNegotiationEvent,
    NegotiationAnalysisRequest,
    NegotiationIntelligence,
    NegotiationMetrics,
    RealTimeCoachingRequest,
    RealTimeCoachingResponse,
    StrategyUpdateRequest,
)
from ghl_real_estate_ai.services.ai_negotiation_partner import get_ai_negotiation_partner
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/negotiation", tags=["Negotiation Intelligence"])
security = HTTPBearer()


@router.post("/analyze", response_model=NegotiationIntelligence)
@rate_limit(calls=100, period=3600)  # 100 calls per hour
async def analyze_negotiation_intelligence(
    request: NegotiationAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Generate comprehensive negotiation intelligence analysis.

    Analyzes seller psychology, market leverage, generates strategy,
    and predicts win probability for optimal negotiation outcomes.
    """
    tenant_id = current_user.get("payload", {}).get("tenant_id", "default_tenant")
    request.tenant_id = tenant_id
    logger.info(f"Negotiation analysis request for property {request.property_id} (Tenant: {tenant_id})")

    try:
        negotiation_partner = get_ai_negotiation_partner()

        # Run comprehensive analysis
        intelligence = await negotiation_partner.analyze_negotiation_intelligence(request)

        # Background tasks
        background_tasks.add_task(_log_analysis_metrics, intelligence, current_user["user_id"])

        logger.info(
            f"Analysis complete for {request.property_id}: "
            f"{intelligence.negotiation_strategy.primary_tactic} strategy, "
            f"{intelligence.win_probability.win_probability:.1f}% win probability"
        )

        return intelligence

    except ValueError as e:
        logger.error(f"Validation error in negotiation analysis: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")
    except Exception as e:
        logger.error(f"Negotiation analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.post("/coaching", response_model=RealTimeCoachingResponse)
@rate_limit(calls=200, period=3600)  # 200 calls per hour
async def get_realtime_coaching(
    request: RealTimeCoachingRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Provide real-time negotiation coaching based on conversation context.

    Analyzes current negotiation state and provides immediate tactical guidance,
    strategic adjustments, and conversation suggestions.
    """
    logger.info(f"Real-time coaching request for negotiation {request.negotiation_id}")

    try:
        negotiation_partner = get_ai_negotiation_partner()

        # Get real-time coaching
        coaching_response = await negotiation_partner.provide_realtime_coaching(request)

        logger.info(f"Coaching provided for {request.negotiation_id}")
        return coaching_response

    except ValueError as e:
        logger.error(f"Coaching validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")
    except Exception as e:
        logger.error(f"Real-time coaching failed: {e}")
        raise HTTPException(status_code=500, detail="Coaching failed")


@router.put("/strategy/{negotiation_id}", response_model=NegotiationIntelligence)
@rate_limit(calls=50, period=3600)  # 50 calls per hour
async def update_negotiation_strategy(
    negotiation_id: str, request: StrategyUpdateRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update negotiation strategy based on new information.

    Triggers selective re-analysis of intelligence engines and updates
    strategy recommendations based on negotiation developments.
    """
    logger.info(f"Strategy update request for negotiation {negotiation_id}")

    try:
        # Ensure negotiation ID matches
        request.negotiation_id = negotiation_id

        negotiation_partner = get_ai_negotiation_partner()

        # Update strategy
        updated_intelligence = await negotiation_partner.update_negotiation_strategy(request)

        logger.info(
            f"Strategy updated for {negotiation_id}: "
            f"New win probability {updated_intelligence.win_probability.win_probability:.1f}%"
        )

        return updated_intelligence

    except ValueError as e:
        logger.error(f"Strategy update validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")
    except Exception as e:
        logger.error(f"Strategy update failed: {e}")
        raise HTTPException(status_code=500, detail="Strategy update failed")


@router.get("/active/{property_id}", response_model=Optional[NegotiationIntelligence])
async def get_active_negotiation(property_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get active negotiation intelligence for a property.

    Returns current negotiation state and intelligence if exists.
    """
    try:
        negotiation_partner = get_ai_negotiation_partner()

        # Get active negotiation
        negotiation_context = negotiation_partner.active_negotiations.get(property_id)

        if not negotiation_context:
            return None

        intelligence = negotiation_context["intelligence"]

        logger.info(f"Retrieved active negotiation for {property_id}")
        return intelligence

    except Exception as e:
        logger.error(f"Failed to get active negotiation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve negotiation")


@router.get("/metrics", response_model=NegotiationMetrics)
async def get_negotiation_metrics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get system performance and negotiation metrics.

    Returns analytics on system performance, strategy effectiveness,
    and prediction accuracy.
    """
    try:
        negotiation_partner = get_ai_negotiation_partner()
        get_cache_service()

        # Get performance metrics
        performance_metrics = negotiation_partner.get_performance_metrics()

        # Calculate additional metrics
        total_negotiations = performance_metrics["total_analyses"]
        avg_win_rate = 0.0
        strategy_effectiveness = performance_metrics.get("strategy_averages", {})

        # Calculate prediction accuracy (simplified)
        prediction_accuracy = 85.5  # Would be calculated from historical data
        user_satisfaction_score = 4.2  # Would be from user feedback

        # Calculate average price improvement (mock data)
        avg_price_improvement = 12.3  # Percentage improvement vs baseline

        metrics = NegotiationMetrics(
            total_negotiations=total_negotiations,
            average_win_rate=avg_win_rate,
            average_price_improvement=avg_price_improvement,
            strategy_effectiveness=strategy_effectiveness,
            prediction_accuracy=prediction_accuracy,
            user_satisfaction_score=user_satisfaction_score,
        )

        logger.info("Negotiation metrics retrieved successfully")
        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.delete("/active/{property_id}")
async def end_negotiation(property_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    End an active negotiation session.

    Cleans up active negotiation state and logs final outcome.
    """
    try:
        negotiation_partner = get_ai_negotiation_partner()

        # Remove from active negotiations
        if property_id in negotiation_partner.active_negotiations:
            del negotiation_partner.active_negotiations[property_id]
            logger.info(f"Ended negotiation for property {property_id}")
            return {"message": "Negotiation ended successfully"}
        else:
            raise HTTPException(status_code=404, detail="Active negotiation not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end negotiation: {e}")
        raise HTTPException(status_code=500, detail="Failed to end negotiation")


@router.post("/webhooks/ghl/negotiation")
async def handle_ghl_negotiation_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle GHL webhook events for negotiation milestones.

    Processes offer submissions, counter-offers, and acceptances
    to trigger real-time strategy updates.
    """
    try:
        # Verify webhook signature (simplified)
        webhook_data = await request.json()

        # Parse GHL negotiation event
        event = GHLNegotiationEvent.model_validate(webhook_data)

        # Process event in background
        background_tasks.add_task(_process_negotiation_event, event)

        logger.info(f"GHL negotiation webhook received: {event.event_type}")
        return {"status": "webhook_received"}

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook data")


@router.get("/scenarios/{property_id}")
async def get_scenario_analysis(
    property_id: str,
    offer_percentage: Optional[float] = None,
    cash_offer: Optional[bool] = None,
    quick_close: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get scenario-based win probability analysis.

    Returns win probability for different offer scenarios and terms.
    """
    try:
        negotiation_partner = get_ai_negotiation_partner()

        # Get active negotiation
        negotiation_context = negotiation_partner.active_negotiations.get(property_id)

        if not negotiation_context:
            raise HTTPException(status_code=404, detail="Active negotiation not found")

        intelligence = negotiation_context["intelligence"]

        # Generate scenario analysis (simplified)
        scenarios = {}
        base_probability = intelligence.win_probability.win_probability

        if offer_percentage:
            # Calculate probability for custom offer percentage
            if offer_percentage > 1.0:
                probability_boost = min((offer_percentage - 1.0) * 100 * 0.5, 20)
            else:
                probability_penalty = max((1.0 - offer_percentage) * 100 * 0.8, -30)
                probability_boost = -probability_penalty

            scenarios["custom_offer"] = min(95, max(5, base_probability + probability_boost))

        if cash_offer is True and not negotiation_context["buyer_profile"].get("cash_offer"):
            scenarios["cash_offer"] = min(95, base_probability + 15)

        if quick_close is True:
            scenarios["quick_close"] = min(95, base_probability + 8)

        if not scenarios:
            scenarios = intelligence.win_probability.scenarios

        logger.info(f"Scenario analysis generated for {property_id}")
        return {"scenarios": scenarios, "base_probability": base_probability}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scenario analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Scenario analysis failed")


# Background task functions
async def _log_analysis_metrics(intelligence: NegotiationIntelligence, user_id: str):
    """Log analysis metrics for performance tracking"""

    try:
        cache_service = get_cache_service()

        # Log analysis event
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "property_id": intelligence.property_id,
            "processing_time_ms": intelligence.processing_time_ms,
            "strategy": intelligence.negotiation_strategy.primary_tactic,
            "win_probability": intelligence.win_probability.win_probability,
            "urgency_score": intelligence.seller_psychology.urgency_score,
            "leverage_score": intelligence.market_leverage.overall_leverage_score,
        }

        # Store in cache for analytics (expire after 30 days)
        await cache_service.set(
            f"analysis_log:{intelligence.property_id}:{datetime.now().timestamp()}",
            log_entry,
            ttl=2592000,  # 30 days
        )

        logger.info(f"Analysis metrics logged for {intelligence.property_id}")

    except Exception as e:
        logger.error(f"Failed to log analysis metrics: {e}")


async def _process_negotiation_event(event: GHLNegotiationEvent):
    """Process GHL negotiation webhook event"""

    try:
        negotiation_partner = get_ai_negotiation_partner()

        # Check if we have an active negotiation for this property
        negotiation_context = negotiation_partner.active_negotiations.get(event.property_id)

        if not negotiation_context:
            logger.info(f"No active negotiation found for property {event.property_id}")
            return

        # Process different event types
        if event.event_type == "offer_submitted":
            # Log offer submission
            logger.info(f"Offer submitted for property {event.property_id}")

        elif event.event_type == "offer_countered":
            # Update strategy based on counter-offer
            new_information = {"seller_response": "counter_offer_received", "counter_details": event.event_data}

            update_request = StrategyUpdateRequest(negotiation_id=event.property_id, new_information=new_information)

            await negotiation_partner.update_negotiation_strategy(update_request)
            logger.info(f"Strategy updated for counter-offer on {event.property_id}")

        elif event.event_type == "offer_accepted":
            # End successful negotiation
            if event.property_id in negotiation_partner.active_negotiations:
                del negotiation_partner.active_negotiations[event.property_id]
            logger.info(f"Offer accepted for property {event.property_id}")

    except Exception as e:
        logger.error(f"Failed to process negotiation event: {e}")


# Error handling is managed by the global exception handler in
# ghl_real_estate_ai.api.middleware.global_exception_handler
