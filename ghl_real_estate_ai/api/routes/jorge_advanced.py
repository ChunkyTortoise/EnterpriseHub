"""
Jorge's Advanced Features API Routes.

Provides endpoints for the four advanced AI modules:
- Voice AI Phone Integration
- Automated Marketing Campaign Generator
- Client Retention & Referral Automation
- Advanced Market Prediction Analytics

These endpoints expose the advanced functionality through the dashboard interface.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.automated_marketing_engine import (
    AutomatedMarketingEngine,
    CampaignBrief,
    CampaignTrigger,
    ContentFormat,
)
from ghl_real_estate_ai.services.client_retention_engine import (
    ClientRetentionEngine,
    LifeEventType,
)
from ghl_real_estate_ai.services.jorge_advanced_integration import (
    EventType,
    IntegrationEvent,
    JorgeAdvancedIntegration,
)
from ghl_real_estate_ai.services.market_prediction_engine import (
    MarketPredictionEngine,
    PredictionResult,
    TimeHorizon,
)
from ghl_real_estate_ai.services.voice_ai_handler import (
    CallPriority,
    CallType,
    VoiceResponse,
    get_voice_ai_handler,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/jorge-advanced", tags=["jorge-advanced"])


# ================== REQUEST/RESPONSE MODELS ==================


# Voice AI Models
class VoiceCallStartRequest(BaseModel):
    """Request to start a voice AI call."""

    phone_number: str = Field(..., min_length=1, description="Caller's phone number")
    caller_name: Optional[str] = Field(None, description="Caller's name if known")
    call_type: Optional[CallType] = Field(CallType.NEW_LEAD, description="Type of call")
    priority: Optional[CallPriority] = Field(CallPriority.NORMAL, description="Call priority")


class VoiceInputRequest(BaseModel):
    """Request to process voice input."""

    call_id: str = Field(..., description="Active call ID")
    speech_text: str = Field(..., description="Transcribed speech text")
    audio_confidence: float = Field(..., ge=0.0, le=1.0, description="Speech recognition confidence")


class VoiceCallAnalytics(BaseModel):
    """Voice call analytics response."""

    call_id: str
    duration_seconds: int
    qualification_score: int
    transfer_to_jorge: bool
    lead_quality: str
    key_information: Dict[str, Any]
    conversation_summary: str


# Marketing Campaign Models
class CampaignCreationRequest(BaseModel):
    """Request to create automated marketing campaign."""

    trigger_type: CampaignTrigger | str
    target_audience: Dict[str, Any] = Field(..., description="Target audience criteria")
    campaign_objectives: List[str] = Field(..., description="Campaign objectives")
    content_formats: List[ContentFormat | str] = Field(..., description="Desired content formats")
    budget_range: Optional[tuple[float, float] | List[float]] = Field(None, description="Budget range (min, max)")
    timeline: Optional[str] = Field(None, description="Campaign timeline")


class CampaignPerformanceMetrics(BaseModel):
    """Campaign performance metrics."""

    campaign_id: str
    impressions: int
    clicks: int
    conversions: int
    ctr: float  # Click-through rate
    conversion_rate: float
    roi: float
    cost_per_lead: float
    lead_quality_score: float


# Client Retention Models
class ClientLifecycleUpdate(BaseModel):
    """Update client lifecycle information."""

    client_id: str
    life_event: LifeEventType
    event_context: Dict[str, Any]
    detected_date: Optional[datetime] = None


class ReferralTracking(BaseModel):
    """Referral tracking information."""

    referrer_client_id: str
    referred_contact_info: Dict[str, str]
    referral_source: str
    context: Dict[str, Any]


class ClientEngagementSummary(BaseModel):
    """Client engagement summary."""

    client_id: str
    total_interactions: int
    last_interaction_date: datetime
    engagement_score: float
    referrals_made: int
    lifetime_value: float
    retention_probability: float


# Market Prediction Models
class MarketAnalysisRequest(BaseModel):
    """Request for market prediction analysis."""

    neighborhood: str = Field(..., description="Neighborhood to analyze")
    time_horizon: TimeHorizon | str = Field(..., description="Prediction time horizon")
    property_type: Optional[str] = Field(None, description="Property type filter")
    price_range: Optional[tuple[float, float]] = Field(None, description="Price range filter")


class InvestmentOpportunityRequest(BaseModel):
    """Request for investment opportunity analysis."""

    client_budget: float = Field(..., description="Client's investment budget")
    risk_tolerance: str = Field(..., description="Risk tolerance: low, medium, high")
    investment_goals: List[str] = Field(..., description="Investment objectives")
    time_horizon: TimeHorizon | str = Field(..., description="Investment time horizon")


# Integration Models
class DashboardMetrics(BaseModel):
    """Unified dashboard metrics from all modules."""

    voice_ai: Dict[str, Any]
    marketing: Dict[str, Any]
    client_retention: Dict[str, Any]
    market_predictions: Dict[str, Any]
    integration_health: Dict[str, Any]
    last_updated: datetime


class ModuleHealthStatus(BaseModel):
    """Health status of individual modules."""

    module_name: str
    status: str  # healthy, degraded, down
    last_check: datetime
    performance_metrics: Dict[str, Any]
    issues: List[str]


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _coerce_time_horizon(value: TimeHorizon | str) -> TimeHorizon:
    if isinstance(value, TimeHorizon):
        return value

    raw = str(value).strip().lower()
    horizon_map = {
        "3_months": TimeHorizon.THREE_MONTHS,
        "6_months": TimeHorizon.SIX_MONTHS,
        "1_year": TimeHorizon.ONE_YEAR,
        "2_years": TimeHorizon.TWO_YEARS,
        "short_term": TimeHorizon.SHORT_TERM,
        "medium_term": TimeHorizon.MEDIUM_TERM,
        "long_term": TimeHorizon.LONG_TERM,
    }
    return horizon_map.get(raw, TimeHorizon.MEDIUM_TERM)


def _get_field(payload: Any, *names: str, default: Any = None) -> Any:
    if isinstance(payload, dict):
        for name in names:
            if name in payload:
                return payload[name]
        return default
    for name in names:
        if hasattr(payload, name):
            return getattr(payload, name)
    return default


# ================== VOICE AI ENDPOINTS ==================


@router.post("/voice/start-call", response_model=Dict[str, str])
async def start_voice_call(request: VoiceCallStartRequest):
    """
    Start a new voice AI call session.

    Initiates Jorge's AI voice handler for incoming phone calls.
    """
    try:
        voice_handler = get_voice_ai_handler()

        context = await voice_handler.handle_incoming_call(
            phone_number=request.phone_number, caller_name=request.caller_name
        )

        logger.info(f"Started voice call {context.call_id} from {request.phone_number}")

        return {"call_id": context.call_id, "status": "active", "message": "Voice AI call started successfully"}

    except Exception as e:
        logger.error(f"Error starting voice call: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.post("/voice/process-input", response_model=VoiceResponse)
async def process_voice_input(request: VoiceInputRequest):
    """
    Process voice input from active call.

    Handles speech-to-text input and generates Jorge's AI response.
    """
    try:
        voice_handler = get_voice_ai_handler()

        response = await voice_handler.process_voice_input(
            call_id=request.call_id, speech_text=request.speech_text, audio_confidence=request.audio_confidence
        )

        return response

    except Exception as e:
        logger.error(f"Error processing voice input: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/voice/end-call/{call_id}", response_model=VoiceCallAnalytics)
async def end_voice_call(call_id: str):
    """
    End voice call and generate analytics.

    Completes the call session and returns comprehensive analytics.
    """
    try:
        voice_handler = get_voice_ai_handler()

        analytics = await voice_handler.handle_call_completion(call_id)

        return VoiceCallAnalytics(
            call_id=analytics.get("call_id", call_id),
            duration_seconds=analytics.get("duration", 0),
            qualification_score=analytics.get("qualification_score", 0),
            transfer_to_jorge=analytics.get("transfer_to_jorge", False),
            lead_quality=analytics.get("lead_quality", "unknown"),
            key_information=analytics.get("extracted_info", {}),
            conversation_summary=analytics.get("summary", ""),
        )

    except Exception as e:
        logger.error(f"Error ending voice call: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.get("/voice/analytics")
async def get_voice_analytics(days: int = Query(default=7, description="Number of days to analyze")):
    """
    Get voice AI system analytics.

    Returns comprehensive analytics for voice call handling performance.
    """
    try:
        voice_handler = get_voice_ai_handler()
        analytics = await voice_handler.get_call_analytics()

        return {"period_days": days, "analytics": analytics, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error fetching voice analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ================== MARKETING AUTOMATION ENDPOINTS ==================


@router.post("/marketing/create-campaign")
async def create_automated_campaign(request: CampaignCreationRequest):
    """
    Create automated marketing campaign.

    Generates AI-powered marketing campaigns based on triggers and objectives.
    """
    try:
        marketing_engine = AutomatedMarketingEngine()

        trigger_type = _enum_value(request.trigger_type)
        content_formats = [_enum_value(fmt) for fmt in request.content_formats]

        campaign = await marketing_engine.create_campaign_from_trigger(
            trigger_type=trigger_type,
            trigger_data={
                "target_audience": request.target_audience,
                "objectives": request.campaign_objectives,
                "formats": content_formats,
                "budget_range": request.budget_range,
                "timeline": request.timeline,
            },
        )

        campaign_id = _get_field(campaign, "campaign_id")
        name = _get_field(campaign, "name")
        if not name:
            campaign_type = _get_field(campaign, "campaign_type")
            campaign_type_value = _enum_value(campaign_type) if campaign_type else "campaign"
            name = str(campaign_type_value).replace("_", " ").title()

        logger.info(f"Created automated campaign {campaign_id}")

        objectives = _get_field(campaign, "objectives")
        if not objectives:
            objective = _get_field(campaign, "objective")
            objectives = [objective] if objective else request.campaign_objectives

        return {
            "campaign_id": campaign_id,
            "name": name,
            "trigger": _enum_value(_get_field(campaign, "trigger", default=trigger_type)),
            "target_audience": _get_field(campaign, "target_audience", default=request.target_audience),
            "objectives": objectives,
            "status": _get_field(campaign, "status", default="draft"),
        }

    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketing/campaigns/{campaign_id}/content")
async def get_campaign_content(campaign_id: str):
    """
    Get generated content for a campaign.

    Returns all AI-generated content pieces for the specified campaign.
    """
    try:
        marketing_engine = AutomatedMarketingEngine()

        content = await marketing_engine.get_campaign_content(campaign_id)

        if not content:
            return JSONResponse(status_code=404, content={"detail": "Campaign not found"})

        return {"campaign_id": campaign_id, "content": content}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign content: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/marketing/campaigns/{campaign_id}/performance")
async def get_campaign_performance(campaign_id: str):
    """
    Get campaign performance metrics.

    Returns detailed performance analytics for the specified campaign.
    """
    try:
        marketing_engine = AutomatedMarketingEngine()

        performance = await marketing_engine.get_campaign_performance(campaign_id)

        if not performance:
            raise HTTPException(status_code=404, detail="Campaign performance data not found")

        return CampaignPerformanceMetrics(
            campaign_id=campaign_id,
            impressions=performance.get("impressions", 0),
            clicks=performance.get("clicks", 0),
            conversions=performance.get("conversions", 0),
            ctr=performance.get("ctr", 0.0),
            conversion_rate=performance.get("conversion_rate", 0.0),
            roi=performance.get("roi", 0.0),
            cost_per_lead=performance.get("cost_per_lead", 0.0),
            lead_quality_score=performance.get("lead_quality_score", 0.0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign performance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/marketing/ab-test/{campaign_id}")
async def start_ab_test(campaign_id: str, test_config: Dict[str, Any] = Body(...)):
    """
    Start A/B test for campaign.

    Initiates A/B testing for campaign optimization.
    """
    try:
        marketing_engine = AutomatedMarketingEngine()

        test_id = await marketing_engine.start_ab_test(campaign_id, test_config)

        return {
            "campaign_id": campaign_id,
            "test_id": test_id,
            "status": "active",
            "message": "A/B test started successfully",
        }

    except Exception as e:
        logger.error(f"Error starting A/B test: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ================== CLIENT RETENTION ENDPOINTS ==================


@router.post("/retention/update-lifecycle")
async def update_client_lifecycle(request: ClientLifecycleUpdate):
    """
    Update client lifecycle information.

    Records life events and triggers appropriate retention actions.
    """
    try:
        retention_engine = ClientRetentionEngine()

        await retention_engine.detect_life_event(
            client_id=request.client_id, life_event=request.life_event, context=request.event_context
        )

        logger.info(f"Updated lifecycle for client {request.client_id}: {request.life_event}")

        return {
            "client_id": request.client_id,
            "life_event": request.life_event.value,
            "status": "processed",
            "message": "Lifecycle update processed successfully",
        }

    except Exception as e:
        logger.error(f"Error updating client lifecycle: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/retention/track-referral")
async def track_referral(request: ReferralTracking):
    """
    Track new referral opportunity.

    Records referral and initiates appropriate follow-up actions.
    """
    try:
        retention_engine = ClientRetentionEngine()

        referral_id = await retention_engine.process_referral(
            referrer_id=request.referrer_client_id,
            referred_contact=request.referred_contact_info,
            context=request.context,
        )

        logger.info(f"Tracked referral {referral_id} from client {request.referrer_client_id}")

        return {
            "referral_id": referral_id,
            "referrer_id": request.referrer_client_id,
            "status": "tracked",
            "message": "Referral tracked successfully",
        }

    except Exception as e:
        logger.error(f"Error tracking referral: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/retention/client/{client_id}/engagement")
async def get_client_engagement(client_id: str):
    """
    Get client engagement summary.

    Returns comprehensive engagement analytics for a client.
    """
    try:
        retention_engine = ClientRetentionEngine()

        profile = await retention_engine.get_client_profile(client_id)

        if not profile:
            return JSONResponse(status_code=404, content={"detail": "Client not found"})

        engagement = await retention_engine.calculate_engagement_score(client_id)

        return ClientEngagementSummary(
            client_id=_get_field(profile, "client_id", default=client_id),
            total_interactions=_get_field(profile, "total_interactions", "total_engagements", default=0),
            last_interaction_date=_get_field(profile, "last_interaction", "last_contact_date", default=datetime.now()),
            engagement_score=_get_field(engagement, "score", default=0.0),
            referrals_made=_get_field(profile, "referrals_made", "referrals_provided", default=0),
            lifetime_value=_get_field(profile, "lifetime_value", "current_estimated_value", default=0.0),
            retention_probability=_get_field(engagement, "retention_probability", default=0.0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client engagement: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/retention/analytics")
async def get_retention_analytics(days: int = Query(default=30, description="Number of days to analyze")):
    """
    Get retention system analytics.

    Returns comprehensive retention and referral analytics.
    """
    try:
        retention_engine = ClientRetentionEngine()
        analytics = await retention_engine.get_retention_analytics(days)

        return {"period_days": days, "analytics": analytics, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error fetching retention analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ================== MARKET PREDICTION ENDPOINTS ==================


@router.post("/market/analyze")
async def analyze_market(request: MarketAnalysisRequest):
    """
    Analyze market trends and predictions.

    Provides AI-powered market analysis and price predictions.
    """
    try:
        market_engine = MarketPredictionEngine()

        prediction = await market_engine.predict_price_appreciation(
            neighborhood=request.neighborhood, time_horizon=_coerce_time_horizon(request.time_horizon)
        )

        logger.info(f"Generated market analysis for {request.neighborhood}")

        confidence_level = _get_field(prediction, "confidence_level")
        if hasattr(confidence_level, "value"):
            confidence_level = confidence_level.value
        if isinstance(confidence_level, (int, float)):
            confidence_score = float(confidence_level)
        else:
            confidence_score = _get_field(prediction, "confidence_score", default=0.0)

        predicted_appreciation = _get_field(prediction, "predicted_appreciation")
        if predicted_appreciation is None:
            change_percentage = _get_field(prediction, "change_percentage", default=0.0)
            predicted_appreciation = change_percentage / 100 if abs(change_percentage) > 1 else change_percentage

        return {
            "neighborhood": _get_field(prediction, "neighborhood", "target", default=request.neighborhood),
            "time_horizon": _enum_value(_get_field(prediction, "time_horizon", default=request.time_horizon)),
            "predicted_appreciation": predicted_appreciation,
            "confidence_level": confidence_score,
            "supporting_factors": _get_field(prediction, "supporting_factors", "key_factors", default=[]),
        }

    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market/investment-opportunities")
async def find_investment_opportunities(request: InvestmentOpportunityRequest):
    """
    Find investment opportunities.

    Identifies potential investment properties based on client criteria.
    """
    try:
        market_engine = MarketPredictionEngine()

        opportunities = await market_engine.identify_investment_opportunities(
            client_budget=request.client_budget,
            risk_tolerance=request.risk_tolerance,
            investment_goals=request.investment_goals,
            time_horizon=_coerce_time_horizon(request.time_horizon),
        )

        return {
            "opportunities": opportunities,
            "analysis_date": datetime.now().isoformat(),
            "criteria": {
                "budget": request.client_budget,
                "risk_tolerance": request.risk_tolerance,
                "goals": request.investment_goals,
                "time_horizon": _enum_value(request.time_horizon),
            },
        }

    except Exception as e:
        logger.error(f"Error finding investment opportunities: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/trends/{neighborhood}")
async def get_market_trends(
    neighborhood: str, months: int = Query(default=12, description="Number of months of trend data")
):
    """
    Get market trend data for neighborhood.

    Returns historical and predicted market trends.
    """
    try:
        market_engine = MarketPredictionEngine()

        trends = await market_engine.get_market_trends(neighborhood, months)

        return {
            "neighborhood": neighborhood,
            "period_months": months,
            "trends": trends,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching market trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ================== INTEGRATION & DASHBOARD ENDPOINTS ==================


@router.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """
    Get unified dashboard metrics from all modules.

    Returns comprehensive metrics from voice AI, marketing, retention, and market prediction.
    """
    try:
        integration_hub = JorgeAdvancedIntegration()

        metrics = await integration_hub.get_unified_dashboard()

        if isinstance(metrics, dict):
            return {
                "voice_ai": metrics.get("voice_ai", {}),
                "marketing": metrics.get("marketing", {}),
                "client_retention": metrics.get("client_retention", {}),
                "market_predictions": metrics.get("market_predictions", {}),
                "integration_health": metrics.get("integration_health", {}),
                "last_updated": datetime.now().isoformat(),
            }

        return {
            "voice_ai": metrics.voice_ai_stats,
            "marketing": metrics.marketing_stats,
            "client_retention": metrics.retention_stats,
            "market_predictions": metrics.prediction_stats,
            "integration_health": metrics.performance_summary,
            "last_updated": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/modules")
async def get_module_health():
    """
    Get health status of all advanced modules.

    Returns health check results for each module.
    """
    try:
        integration_hub = JorgeAdvancedIntegration()

        health_status = await integration_hub.check_module_health()

        return {
            "overall_status": health_status["overall_status"],
            "modules": [
                ModuleHealthStatus(
                    module_name=module["name"],
                    status=module["status"],
                    last_check=datetime.now(),
                    performance_metrics=module.get("metrics", {}),
                    issues=module.get("issues", []),
                )
                for module in health_status["modules"]
            ],
            "last_check": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking module health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/integration/trigger-event")
async def trigger_integration_event(event_type: EventType, event_data: Dict[str, Any] = Body(...)):
    """
    Trigger cross-module integration event.

    Manually trigger events for testing or special scenarios.
    """
    try:
        integration_hub = JorgeAdvancedIntegration()

        event = IntegrationEvent(
            event_id=f"manual_{event_type.value}_{int(datetime.now().timestamp())}",
            event_type=event_type,
            source_module="manual",
            data=event_data,
            timestamp=datetime.now(),
        )

        await integration_hub.handle_integration_event(event)

        return {
            "event_type": event_type.value,
            "status": "processed",
            "message": "Integration event triggered successfully",
        }

    except Exception as e:
        logger.error(f"Error triggering integration event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ================== SYSTEM ENDPOINTS ==================


@router.get("/health")
async def advanced_features_health():
    """Health check for Jorge's advanced features."""
    return {
        "status": "healthy",
        "service": "jorge-advanced-features",
        "modules": ["voice-ai", "marketing-automation", "client-retention", "market-prediction"],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/config")
async def get_configuration():
    """Get configuration information for advanced modules."""
    return {
        "voice_ai": {
            "qualification_questions": 7,
            "supported_languages": ["en-US"],
            "max_call_duration": 1800,  # 30 minutes
        },
        "marketing": {
            "supported_formats": ["email", "sms", "social_media", "direct_mail"],
            "ab_test_duration": 14,  # days
            "min_audience_size": 50,
        },
        "retention": {
            "lifecycle_stages": ["prospect", "client", "past_client", "referral_source"],
            "engagement_tracking_period": 365,  # days
            "referral_reward_system": True,
        },
        "market_prediction": {
            "prediction_horizons": ["3_months", "6_months", "1_year", "2_years"],
            "supported_markets": ["rancho_cucamonga", "inland_empire"],
            "ml_model_version": "v2.1",
        },
        "last_updated": datetime.now().isoformat(),
    }
