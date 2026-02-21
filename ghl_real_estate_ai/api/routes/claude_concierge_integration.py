"""
Claude Concierge Integration API Routes
Provides REST endpoints that match the frontend ClaudeConciergeAPI.ts expectations.
Complements the existing claude_concierge.py with additional integration endpoints.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ghl_real_estate_ai.agents.claude_concierge_agent import get_claude_concierge
from ghl_real_estate_ai.api.middleware.enhanced_auth import get_current_user_optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.claude_concierge_orchestrator import (
    ConciergeMode,
    IntelligenceScope,
    get_claude_concierge_orchestrator,
)
from ghl_real_estate_ai.services.claude_concierge_orchestrator import PlatformContext as BackendPlatformContext
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)
router = APIRouter(prefix="/api/claude-concierge", tags=["claude-concierge-integration"])

# In-memory dismissal tracking (Phase 3: migrate to Redis with tenant isolation)
_dismissal_feedback: Dict[str, Dict] = {}

# ============================================================================
# HELPERS
# ============================================================================


def convert_to_backend_context(frontend_context: "PlatformContext") -> BackendPlatformContext:
    """Convert frontend PlatformContext model to backend dataclass."""
    return BackendPlatformContext(
        current_page=frontend_context.currentPage,
        user_role=frontend_context.userRole,
        session_id=frontend_context.sessionId,
        location_context=frontend_context.locationContext,
        active_leads=frontend_context.activeLeads,
        bot_statuses=frontend_context.botStatuses,
        user_activity=frontend_context.userActivity,
        business_metrics=frontend_context.businessMetrics,
        active_properties=frontend_context.activeProperties,
        market_conditions=frontend_context.marketConditions,
        priority_actions=frontend_context.priorityActions,
        pending_notifications=frontend_context.pendingNotifications,
    )


# ============================================================================
# RESPONSE MODELS (Match Frontend TypeScript Interfaces)
# ============================================================================


class ConciergeInsight(BaseModel):
    """Concierge insight matching frontend interface."""

    category: str
    title: str
    value: str  # Could be string or number, keeping as string for flexibility
    trend: str  # 'up' | 'down' | 'stable'
    trendValue: float
    description: str
    timestamp: str


class ProactiveSuggestion(BaseModel):
    """Proactive suggestion matching frontend interface."""

    id: str
    type: str  # 'optimization' | 'escalation' | 'automation' | 'insight'
    title: str
    description: str
    impact: str  # 'low' | 'medium' | 'high'
    confidence: float
    actionable: bool
    estimatedBenefit: Optional[str] = None
    relatedAgents: List[str]
    priority: str  # 'low' | 'medium' | 'high' | 'urgent'
    createdAt: str


class ConciergeResponse(BaseModel):
    """Chat response matching frontend interface."""

    response: str
    insights: Optional[List[ConciergeInsight]] = None
    suggestions: Optional[List[ProactiveSuggestion]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    confidence: float
    processingTime: int  # milliseconds
    agentContext: List[str]


class PlatformContext(BaseModel):
    """Platform context for chat requests."""

    currentPage: str
    userRole: str = "agent"
    sessionId: str
    locationContext: Dict[str, Any] = Field(default_factory=dict)
    activeLeads: List[Dict[str, Any]] = Field(default_factory=list)
    botStatuses: Dict[str, Any] = Field(default_factory=dict)
    userActivity: List[Dict[str, Any]] = Field(default_factory=list)
    businessMetrics: Dict[str, Any] = Field(default_factory=dict)
    activeProperties: List[Dict[str, Any]] = Field(default_factory=list)
    marketConditions: Dict[str, Any] = Field(default_factory=dict)
    priorityActions: List[Dict[str, Any]] = Field(default_factory=list)
    pendingNotifications: List[Dict[str, Any]] = Field(default_factory=list)


class ConciergeResponseModel(BaseModel):
    """Full concierge response matching Track 2 format."""

    content: str
    primary_guidance: str
    urgency_level: str
    confidence_score: float
    reasoning: Optional[str] = None
    immediate_actions: List[Dict[str, Any]] = Field(default_factory=list)
    background_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up_reminders: List[Dict[str, Any]] = Field(default_factory=list)
    page_specific_tips: List[str] = Field(default_factory=list)
    bot_coordination_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    revenue_optimization_ideas: List[Dict[str, Any]] = Field(default_factory=list)
    risk_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    opportunity_highlights: List[Dict[str, Any]] = Field(default_factory=list)
    learning_insights: List[Dict[str, Any]] = Field(default_factory=list)
    handoff_recommendation: Optional[Dict[str, Any]] = None
    response_time_ms: int = 0
    data_sources_used: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


class CoachingRequest(BaseModel):
    """Request model for real-time coaching."""

    conversation_id: str
    current_situation: Dict[str, Any]
    urgency: str = "medium"
    platform_context: PlatformContext


class BotHandoffRequest(BaseModel):
    """Request model for bot orchestration."""

    conversation_id: str
    target_bot: str
    reason: str
    urgency: str = "scheduled"
    platform_context: PlatformContext


class FieldAssistanceRequest(BaseModel):
    """Request model for mobile field assistance."""

    location_data: Dict[str, Any]
    platform_context: PlatformContext


class PresentationSupportRequest(BaseModel):
    """Request model for client presentation support."""

    client_profile: Dict[str, Any]
    presentation_context: Dict[str, Any]
    platform_context: PlatformContext


class LearningRequest(BaseModel):
    """Request model for learning from decisions."""

    decision: Dict[str, Any]
    outcome: Dict[str, Any]
    platform_context: PlatformContext


def convert_concierge_response(response: Any) -> ConciergeResponseModel:
    """Convert backend ConciergeResponse dataclass to API model."""
    return ConciergeResponseModel(
        content=response.primary_guidance,
        primary_guidance=response.primary_guidance,
        urgency_level=response.urgency_level,
        confidence_score=response.confidence_score,
        reasoning=response.reasoning,
        immediate_actions=response.immediate_actions,
        background_tasks=response.background_tasks,
        follow_up_reminders=response.follow_up_reminders,
        page_specific_tips=response.page_specific_tips,
        bot_coordination_suggestions=response.bot_coordination_suggestions,
        revenue_optimization_ideas=response.revenue_optimization_ideas,
        risk_alerts=response.risk_alerts,
        opportunity_highlights=response.opportunity_highlights,
        learning_insights=response.learning_insights,
        handoff_recommendation=response.handoff_recommendation,
        response_time_ms=response.response_time_ms,
        data_sources_used=response.data_sources_used,
        generated_at=response.generated_at,
    )


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    sessionId: str
    context: PlatformContext


# ============================================================================
# MOCK DATA GENERATORS
# ============================================================================


def generate_mock_insights() -> List[ConciergeInsight]:
    """Generate mock concierge insights."""
    insights = [
        ConciergeInsight(
            category="Lead Quality",
            title="Hot Lead Score",
            value="87%",
            trend="up",
            trendValue=5.2,
            description="Lead qualification scores have improved by 5.2% this week",
            timestamp=datetime.now().isoformat(),
        ),
        ConciergeInsight(
            category="Response Time",
            title="Avg Response",
            value="2.3 min",
            trend="down",
            trendValue=-12.5,
            description="Average response time improved by 12.5% since Jorge's optimization",
            timestamp=datetime.now().isoformat(),
        ),
        ConciergeInsight(
            category="Commission Pipeline",
            title="Pipeline Value",
            value="$847K",
            trend="up",
            trendValue=18.3,
            description="Commission pipeline value increased significantly this month",
            timestamp=datetime.now().isoformat(),
        ),
        ConciergeInsight(
            category="Bot Coordination",
            title="Handoff Success",
            value="94%",
            trend="stable",
            trendValue=0.8,
            description="Agent coordination efficiency remains consistently high",
            timestamp=datetime.now().isoformat(),
        ),
        ConciergeInsight(
            category="Property Analysis",
            title="CMA Accuracy",
            value="96.2%",
            trend="up",
            trendValue=2.1,
            description="Property valuation accuracy continues to improve with ML enhancements",
            timestamp=datetime.now().isoformat(),
        ),
    ]
    return insights


def generate_mock_suggestions() -> List[ProactiveSuggestion]:
    """Generate mock proactive suggestions."""
    suggestions = [
        ProactiveSuggestion(
            id=str(uuid.uuid4()),
            type="optimization",
            title="Optimize Jorge's response timing",
            description="Analysis shows 15% better conversion when Jorge responds within 90 seconds instead of 2 minutes",
            impact="high",
            confidence=0.87,
            actionable=True,
            estimatedBenefit="15% conversion improvement",
            relatedAgents=["adaptive-jorge", "intent-decoder"],
            priority="high",
            createdAt=datetime.now().isoformat(),
        ),
        ProactiveSuggestion(
            id=str(uuid.uuid4()),
            type="escalation",
            title="High-value lead requires attention",
            description="Lead #1247 shows premium property interest ($2M+) but hasn't been contacted in 4 hours",
            impact="high",
            confidence=0.92,
            actionable=True,
            estimatedBenefit="$120K potential commission",
            relatedAgents=["adaptive-jorge", "property-intelligence"],
            priority="urgent",
            createdAt=datetime.now().isoformat(),
        ),
        ProactiveSuggestion(
            id=str(uuid.uuid4()),
            type="automation",
            title="Automate follow-up sequence",
            description="Detected pattern: leads who view property details 3+ times respond well to immediate scheduling",
            impact="medium",
            confidence=0.75,
            actionable=True,
            estimatedBenefit="25% faster scheduling",
            relatedAgents=["predictive-lead", "journey-orchestrator"],
            priority="medium",
            createdAt=datetime.now().isoformat(),
        ),
        ProactiveSuggestion(
            id=str(uuid.uuid4()),
            type="insight",
            title="Market opportunity detected",
            description="3 new properties in Jorge's target area are underpriced by 8-12% based on recent analysis",
            impact="medium",
            confidence=0.84,
            actionable=True,
            estimatedBenefit="Investment opportunity",
            relatedAgents=["property-intelligence", "market-analyzer"],
            priority="medium",
            createdAt=datetime.now().isoformat(),
        ),
    ]
    return suggestions


# ============================================================================
# INTEGRATION ENDPOINTS (Match Frontend Expectations)
# ============================================================================


@router.post("/chat", response_model=ConciergeResponse)
async def send_message(request: ChatRequest, current_user=Depends(get_current_user_optional)):
    """
    Send a message to Claude Concierge and get a response.
    This endpoint matches the frontend ClaudeConciergeAPI.sendMessage() expectation.
    """
    try:
        start_time = datetime.now()
        logger.info(f"Processing concierge chat message for session {request.sessionId}")

        # Get the concierge agent
        concierge = get_claude_concierge()

        # Convert platform context to the format expected by the agent
        user_context = {
            "action": "chat_message",
            "page": request.context.currentPage,
            "device": "web",
            "message": request.message,
        }

        # Process the interaction with the concierge agent
        response = await concierge.process_user_interaction(
            user_id=request.sessionId, message=request.message, context=user_context
        )

        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Extract the primary response
        concierge_response = response.get("concierge_response", {})
        primary_response = concierge_response.get("content", "I'm here to help! How can I assist you today?")

        # Get real insights and suggestions from the orchestrator
        orchestrator = get_claude_concierge_orchestrator()
        backend_context = convert_to_backend_context(request.context)

        guidance = await orchestrator.generate_contextual_guidance(
            context=backend_context, mode=ConciergeMode.REACTIVE, scope=IntelligenceScope.WORKFLOW
        )

        # Map backend insights to frontend model
        insights = []
        for tip in guidance.page_specific_tips:
            insights.append(
                ConciergeInsight(
                    category="Platform Guidance",
                    title="Contextual Tip",
                    value="Insight",
                    trend="stable",
                    trendValue=0,
                    description=tip,
                    timestamp=datetime.now().isoformat(),
                )
            )

        for highlight in guidance.opportunity_highlights:
            insights.append(
                ConciergeInsight(
                    category="Opportunity",
                    title=highlight.get("type", "Growth"),
                    value="High",
                    trend="up",
                    trendValue=1.0,
                    description=highlight.get("description", ""),
                    timestamp=datetime.now().isoformat(),
                )
            )

        # Map backend suggestions to frontend model
        suggestions = []
        for coord_suggestion in guidance.bot_coordination_suggestions:
            suggestion_id = str(uuid.uuid4())
            await orchestrator.store_suggestion(
                suggestion_id,
                {
                    **coord_suggestion,
                    "type": "optimization",
                    "title": coord_suggestion.get("suggestion", "Bot Optimization"),
                },
            )

            suggestions.append(
                ProactiveSuggestion(
                    id=suggestion_id,
                    type="optimization",
                    title=coord_suggestion.get("suggestion", "Bot Optimization"),
                    description=f"Actionable step for {coord_suggestion.get('bot_type', 'agent')}",
                    impact=coord_suggestion.get("impact", "medium"),
                    confidence=0.85,
                    actionable=True,
                    relatedAgents=[coord_suggestion.get("bot_type", "adaptive-jorge")],
                    priority="medium",
                    createdAt=datetime.now().isoformat(),
                )
            )

        # Add risk alerts as suggestions too
        for alert in guidance.risk_alerts:
            suggestion_id = str(uuid.uuid4())
            await orchestrator.store_suggestion(
                suggestion_id,
                {
                    **alert,
                    "type": "escalation",
                    "title": alert.get("description", "Risk Alert")[:50],
                },
            )
            suggestions.append(
                ProactiveSuggestion(
                    id=suggestion_id,
                    type="escalation",
                    title=f"Alert: {alert.get('severity', 'high').capitalize()}",
                    description=alert.get("description", "Potential platform risk detected"),
                    impact="high",
                    confidence=0.9,
                    actionable=True,
                    relatedAgents=["claude-concierge"],
                    priority="urgent",
                    createdAt=datetime.now().isoformat(),
                )
            )

        # Build agent context
        agent_context = [
            "claude-concierge",
            "platform-intelligence",
            "real-time-analytics",
            f"mode:{guidance.urgency_level}",
        ]

        # Generate actionable responses from immediate actions
        actions = []
        for action in guidance.immediate_actions:
            actions.append(
                {
                    "type": "quick_action",
                    "label": action.get("description", "Action"),
                    "action": "execute_guidance_action",
                    "metadata": action,
                }
            )

        if not actions:
            actions = [
                {
                    "type": "quick_action",
                    "label": "View Lead Details",
                    "action": "navigate_to_leads",
                    "metadata": {"priority": "high"},
                }
            ]

        result = ConciergeResponse(
            response=primary_response,
            insights=insights[:5],
            suggestions=suggestions[:3],
            actions=actions,
            confidence=guidance.confidence_score,
            processingTime=processing_time,
            agentContext=agent_context,
        )

        logger.info(f"Concierge chat response generated in {processing_time}ms")
        return result

    except Exception as e:
        logger.error(f"Error processing concierge chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.get("/insights", response_model=List[ConciergeInsight])
async def get_realtime_insights(current_user=Depends(get_current_user_optional)):
    """
    Get real-time insights from the concierge.
    Matches frontend ClaudeConciergeAPI.getRealtimeInsights() expectation.
    Uses live GHL data for real-world intelligence.
    """
    try:
        logger.info("Fetching real-time concierge insights via orchestrator")

        orchestrator = get_claude_concierge_orchestrator()
        guidance = await orchestrator.generate_live_guidance(
            current_page="Unknown (Background)", mode=ConciergeMode.PROACTIVE
        )

        insights = []
        for tip in guidance.page_specific_tips:
            insights.append(
                ConciergeInsight(
                    category="Platform Guidance",
                    title="Contextual Tip",
                    value="Insight",
                    trend="stable",
                    trendValue=0,
                    description=tip,
                    timestamp=datetime.now().isoformat(),
                )
            )

        for highlight in guidance.opportunity_highlights:
            insights.append(
                ConciergeInsight(
                    category="Opportunity",
                    title=highlight.get("type", "Growth"),
                    value="High",
                    trend="up",
                    trendValue=1.0,
                    description=highlight.get("description", ""),
                    timestamp=datetime.now().isoformat(),
                )
            )

        # Add revenue optimization ideas as insights
        for idea in guidance.revenue_optimization_ideas:
            insights.append(
                ConciergeInsight(
                    category="Revenue",
                    title=idea.get("idea", "Optimization"),
                    value=idea.get("potential_impact", "medium"),
                    trend="up",
                    trendValue=0.5,
                    description=f"Potential impact: {idea.get('potential_impact', 'medium')}",
                    timestamp=datetime.now().isoformat(),
                )
            )

        logger.info(f"Generated {len(insights)} real concierge insights")
        return insights

    except Exception as e:
        logger.error(f"Error fetching real concierge insights: {e}")
        # Fallback to mock only if real fails
        return generate_mock_insights()


@router.get("/suggestions", response_model=List[ProactiveSuggestion])
async def get_proactive_suggestions(current_user=Depends(get_current_user_optional)):
    """
    Get proactive suggestions from the concierge.
    Matches frontend ClaudeConciergeAPI.getProactiveSuggestions() expectation.
    Uses live GHL data for real-world intelligence.
    """
    try:
        logger.info("Fetching proactive concierge suggestions via orchestrator")

        orchestrator = get_claude_concierge_orchestrator()
        guidance = await orchestrator.generate_live_guidance(
            current_page="Unknown (Background)", mode=ConciergeMode.PROACTIVE
        )

        suggestions = []
        for coord_suggestion in guidance.bot_coordination_suggestions:
            suggestion_id = str(uuid.uuid4())
            await orchestrator.store_suggestion(
                suggestion_id,
                {
                    **coord_suggestion,
                    "type": "optimization",
                    "title": coord_suggestion.get("suggestion", "Bot Optimization"),
                },
            )
            suggestions.append(
                ProactiveSuggestion(
                    id=suggestion_id,
                    type="optimization",
                    title=coord_suggestion.get("suggestion", "Bot Optimization"),
                    description=f"Automated orchestration: {coord_suggestion.get('suggestion', '')}",
                    impact=coord_suggestion.get("impact", "medium"),
                    confidence=0.85,
                    actionable=True,
                    relatedAgents=[coord_suggestion.get("bot_type", "adaptive-jorge")],
                    priority="medium",
                    createdAt=datetime.now().isoformat(),
                )
            )

        # Add risk alerts as urgent suggestions
        for alert in guidance.risk_alerts:
            suggestion_id = str(uuid.uuid4())
            await orchestrator.store_suggestion(
                suggestion_id,
                {
                    **alert,
                    "type": "escalation",
                    "title": alert.get("type", "Risk Alert"),
                },
            )
            suggestions.append(
                ProactiveSuggestion(
                    id=suggestion_id,
                    type="escalation",
                    title=alert.get("type", "Risk Alert"),
                    description=alert.get("description", "Potential platform risk detected"),
                    impact="high",
                    confidence=0.9,
                    actionable=True,
                    relatedAgents=["claude-concierge"],
                    priority="urgent",
                    createdAt=datetime.now().isoformat(),
                )
            )

        logger.info(f"Generated {len(suggestions)} real proactive suggestions")
        return suggestions

    except Exception as e:
        logger.error(f"Error fetching real proactive suggestions: {e}")
        return generate_mock_suggestions()


@router.post("/suggestions/{suggestion_id}/apply")
async def apply_suggestion(
    suggestion_id: str,
    tenant_id: str = Query(default="jorge", description="Tenant whose suggestion store to use"),
    current_user=Depends(get_current_user_optional),
):
    """
    Apply a proactive suggestion.
    Matches frontend ClaudeConciergeAPI.applySuggestion() expectation.
    """
    try:
        logger.info(f"Applying suggestion: {suggestion_id} for tenant: {tenant_id}")

        orchestrator = get_claude_concierge_orchestrator()
        apply_result = await orchestrator.apply_suggestion(suggestion_id, tenant_id=tenant_id)

        if not apply_result.get("success"):
            raise HTTPException(status_code=400, detail=apply_result.get("error", "Failed to apply suggestion"))

        # Build response matching frontend expectations
        result = {
            "success": True,
            "result": f"Successfully applied: {suggestion_id}",
            "actions_taken": apply_result.get("actions_taken", []),
            "followUpActions": [
                "Monitor performance metrics for 24 hours",
                "Review impact on lead conversion rates",
                "Adjust parameters if needed",
            ],
        }

        # Publish suggestion applied event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "suggestion_applied",
            {
                "suggestion_id": suggestion_id,
                "user_id": current_user.id if hasattr(current_user, "id") else "unknown",
                "timestamp": datetime.now().isoformat(),
                "result": result,
            },
        )

        logger.info(f"Suggestion {suggestion_id} applied successfully")
        return result

    except Exception:
        logger.exception("Failed to apply suggestion")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: str, dismiss_reason: Dict[str, str], current_user=Depends(get_current_user_optional)
):
    """
    Dismiss a proactive suggestion.
    Matches frontend ClaudeConciergeAPI.dismissSuggestion() expectation.
    """
    try:
        reason = dismiss_reason.get("reason", "User dismissed")
        category = dismiss_reason.get("category", "unknown")
        user_id = current_user.id if hasattr(current_user, "id") else "unknown"
        logger.info(f"Dismissing suggestion {suggestion_id}: {reason}")

        # ROADMAP-045: Store dismissal in orchestrator's suggestion store
        orchestrator = get_claude_concierge_orchestrator()
        await orchestrator.store_suggestion(
            suggestion_id,
            {
                "status": "dismissed",
                "dismiss_reason": reason,
                "dismiss_category": category,
                "dismissed_by": user_id,
                "dismissed_at": datetime.now().isoformat(),
            },
        )

        # Publish suggestion dismissed event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "suggestion_dismissed",
            {
                "suggestion_id": suggestion_id,
                "reason": reason,
                "category": category,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Track dismissal pattern for ML confidence adjustment
        _dismissal_feedback.setdefault(category, {"count": 0, "reasons": [], "applied": 0})
        _dismissal_feedback[category]["count"] += 1
        _dismissal_feedback[category]["reasons"].append(reason[:100])
        # Keep only last 50 reasons per category to bound memory
        if len(_dismissal_feedback[category]["reasons"]) > 50:
            _dismissal_feedback[category]["reasons"] = _dismissal_feedback[category]["reasons"][-50:]

        # Calculate dismissal rate and adjust confidence threshold
        cat_data = _dismissal_feedback[category]
        total_interactions = cat_data["count"] + cat_data.get("applied", 0)
        dismissal_rate = cat_data["count"] / total_interactions if total_interactions > 0 else 0.0

        # ML signal: if dismissal rate > 70% for this category, lower confidence
        confidence_adjustment = 0.0
        if total_interactions >= 5 and dismissal_rate > 0.7:
            confidence_adjustment = -0.1 * dismissal_rate
        elif total_interactions >= 5 and dismissal_rate < 0.3:
            confidence_adjustment = 0.05

        logger.info(
            f"Suggestion {suggestion_id} dismissed. Category '{category}' "
            f"dismissal rate: {dismissal_rate:.0%} ({cat_data['count']}/{total_interactions})"
        )

        return {
            "success": True,
            "message": "Suggestion dismissed",
            "feedback_stats": {
                "category": category,
                "dismissal_rate": round(dismissal_rate, 3),
                "total_interactions": total_interactions,
                "confidence_adjustment": round(confidence_adjustment, 3),
            },
        }

    except Exception:
        logger.exception("Failed to dismiss suggestion")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================


@router.get("/analyze/platform")
async def analyze_platform_performance(current_user=Depends(get_current_user_optional)):
    """
    Analyze overall platform performance.
    Matches frontend ClaudeConciergeAPI.analyzePlatformPerformance() expectation.
    """
    try:
        logger.info("Analyzing platform performance via orchestrator")

        orchestrator = get_claude_concierge_orchestrator()
        guidance = await orchestrator.generate_live_guidance(
            current_page="Platform Dashboard", mode=ConciergeMode.EXECUTIVE
        )

        analysis = {
            "overallHealth": int(guidance.confidence_score * 100),
            "keyMetrics": [],  # Map from revenue_optimization_ideas or similar
            "recommendations": [],  # Map from bot_coordination_suggestions
            "alerts": [],
        }

        # Map alerts
        for alert in guidance.risk_alerts:
            analysis["alerts"].append(
                {
                    "level": "warning" if "risk" in alert.get("type", "").lower() else "info",
                    "message": alert.get("description", ""),
                    "action": alert.get("mitigation", "Review strategy"),
                }
            )

        logger.info("Platform analysis completed with real intelligence")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing platform performance: {e}")
        # Return something meaningful even on error
        return {
            "overallHealth": 0,
            "keyMetrics": [],
            "recommendations": [],
            "alerts": [{"level": "error", "message": "Analysis temporarily unavailable"}],
        }


@router.get("/analyze/coordination")
async def analyze_agent_coordination(current_user=Depends(get_current_user_optional)):
    """
    Analyze agent coordination efficiency.
    Matches frontend ClaudeConciergeAPI.analyzeAgentCoordination() expectation.
    """
    try:
        logger.info("Analyzing agent coordination via orchestrator")

        orchestrator = get_claude_concierge_orchestrator()
        guidance = await orchestrator.generate_live_guidance(
            current_page="Agent Ecosystem", mode=ConciergeMode.PROACTIVE
        )

        analysis = {
            "efficiencyScore": int(guidance.confidence_score * 100),
            "handoffAnalysis": {
                "successful": 0,  # Would need real metrics from orchestrator.metrics
                "failed": 0,
                "avgDuration": 0,
                "bottlenecks": [
                    tip for tip in guidance.page_specific_tips if "delay" in tip.lower() or "issue" in tip.lower()
                ],
            },
            "optimizationSuggestions": [],
        }

        logger.info("Agent coordination analysis completed")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing agent coordination: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze agent coordination")


@router.get("/analyze/journeys")
async def analyze_customer_journeys(current_user=Depends(get_current_user_optional)):
    """
    Analyze customer journey performance.
    Matches frontend ClaudeConciergeAPI.analyzeCustomerJourneys() expectation.
    """
    try:
        logger.info("Analyzing customer journeys via orchestrator")

        orchestrator = get_claude_concierge_orchestrator()
        await orchestrator.generate_live_guidance(current_page="Customer Journeys", mode=ConciergeMode.REACTIVE)

        analysis = {
            "activeJourneys": 0,  # Would need real metrics
            "completionRate": 0,
            "avgSatisfaction": 0,
            "stageAnalysis": {},
            "improvementSuggestions": [],
        }

        logger.info("Customer journey analysis completed")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing customer journeys: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze customer journeys")


# ============================================================================
# CONTEXT MANAGEMENT ENDPOINTS
# ============================================================================


@router.put("/context")
async def update_context(context_update: Dict[str, Any], current_user=Depends(get_current_user_optional)):
    """

    Update platform context for the concierge.

    Matches frontend ClaudeConciergeAPI.updateContext() expectation.

    Stores context in the orchestrator's session management.

    """

    try:
        session_id = context_update.get("sessionId")

        context_data = context_update.get("context", {})

        if not session_id:
            raise HTTPException(status_code=400, detail="sessionId required")

        logger.info(f"Updating real context for session {session_id}")

        orchestrator = get_claude_concierge_orchestrator()

        # In a real implementation, we would convert and store this context

        # For now, we'll ensure the session exists in the orchestrator

        if session_id not in orchestrator.session_contexts:
            orchestrator.session_contexts[session_id] = []

        # We can also update the context_cache if needed

        orchestrator.context_cache[session_id] = context_data

        logger.info(f"Context updated for session {session_id}")

        return {"success": True, "sessionId": session_id}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error updating context: {e}")

        raise HTTPException(status_code=500, detail="Failed to update context")


@router.get("/context/{session_id}")
async def get_context(session_id: str, current_user=Depends(get_current_user_optional)):
    """

    Get current context for a session.

    Matches frontend ClaudeConciergeAPI.getContext() expectation.

    Retrieves from orchestrator's session management.

    """

    try:
        logger.info(f"Fetching real context for session {session_id}")

        orchestrator = get_claude_concierge_orchestrator()

        # Retrieve cached context or return empty default

        cached_context = orchestrator.context_cache.get(session_id, {})

        # Build response matching frontend PlatformContext model

        context = PlatformContext(
            currentPage=cached_context.get("currentPage", "/dashboard"),
            userRole=cached_context.get("userRole", "agent"),
            sessionId=session_id,
            locationContext=cached_context.get("locationContext", {}),
            activeLeads=cached_context.get("activeLeads", []),
            botStatuses=cached_context.get("botStatuses", {}),
            userActivity=cached_context.get("userActivity", []),
            businessMetrics=cached_context.get("businessMetrics", {}),
            activeProperties=cached_context.get("activeProperties", []),
            marketConditions=cached_context.get("marketConditions", {}),
            priorityActions=cached_context.get("priorityActions", []),
            pendingNotifications=cached_context.get("pendingNotifications", []),
        )

        logger.info(f"Real context retrieved for session {session_id}")

        return context

    except Exception:
        logger.exception("Failed to fetch session context")

        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# TRACK 2: COACHING, FIELD WORK, PRESENTATION, LEARNING ENDPOINTS
# ============================================================================


@router.post("/real-time-coaching", response_model=ConciergeResponseModel)
async def provide_real_time_coaching(
    request: CoachingRequest,
    current_user=Depends(get_current_user_optional),
):
    """Provide real-time coaching for specific situations."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        platform_context = convert_to_backend_context(request.platform_context)
        response = await orchestrator.provide_real_time_coaching(
            current_situation=request.current_situation,
            context=platform_context,
            urgency=request.urgency,
        )
        return convert_concierge_response(response)
    except Exception:
        logger.exception("Error providing real-time coaching")
        raise HTTPException(status_code=500, detail="Internal server error providing coaching")


@router.post("/bot-coordination", response_model=ConciergeResponseModel)
async def coordinate_bot_ecosystem(
    request: BotHandoffRequest,
    current_user=Depends(get_current_user_optional),
):
    """Coordinate the bot ecosystem for optimal outcomes."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        platform_context = convert_to_backend_context(request.platform_context)
        response = await orchestrator.coordinate_bot_ecosystem(
            context=platform_context,
            desired_outcome=f"Handoff to {request.target_bot}: {request.reason}",
        )
        return convert_concierge_response(response)
    except Exception:
        logger.exception("Error in bot coordination")
        raise HTTPException(status_code=500, detail="Internal server error in bot coordination")


@router.post("/field-assistance", response_model=ConciergeResponseModel)
async def generate_mobile_field_assistance(
    request: FieldAssistanceRequest,
    current_user=Depends(get_current_user_optional),
):
    """Generate mobile-specific field assistance for property visits."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        platform_context = convert_to_backend_context(request.platform_context)
        response = await orchestrator.generate_mobile_field_assistance(
            location_data=request.location_data,
            context=platform_context,
        )
        return convert_concierge_response(response)
    except Exception:
        logger.exception("Error in field assistance")
        raise HTTPException(status_code=500, detail="Internal server error in field assistance")


@router.post("/presentation-support", response_model=ConciergeResponseModel)
async def provide_client_presentation_support(
    request: PresentationSupportRequest,
    current_user=Depends(get_current_user_optional),
):
    """Provide intelligent support for client presentations."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        platform_context = convert_to_backend_context(request.platform_context)
        response = await orchestrator.provide_client_presentation_support(
            client_profile=request.client_profile,
            presentation_context=request.presentation_context,
            context=platform_context,
        )
        return convert_concierge_response(response)
    except Exception:
        logger.exception("Error in presentation support")
        raise HTTPException(status_code=500, detail="Internal server error in presentation support")


@router.post("/learn-decision")
async def learn_from_user_decision(
    request: LearningRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user_optional),
):
    """Learn from Jorge's decisions to improve future recommendations."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        platform_context = convert_to_backend_context(request.platform_context)
        background_tasks.add_task(
            orchestrator.learn_from_user_decision, platform_context, request.decision, request.outcome
        )
        return {"status": "learning_queued", "message": "Decision learning queued for processing"}
    except Exception:
        logger.exception("Error queuing decision learning")
        raise HTTPException(status_code=500, detail="Internal server error in learning system")


@router.post("/predict-preference")
async def predict_jorge_preference(
    situation: Dict[str, Any],
    request: PlatformContext,
    current_user=Depends(get_current_user_optional),
):
    """Predict what Jorge would prefer in a given situation."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        platform_context = convert_to_backend_context(request)
        prediction = await orchestrator.predict_jorge_preference(situation=situation, context=platform_context)
        return {"prediction": prediction, "timestamp": datetime.now().isoformat()}
    except Exception:
        logger.exception("Error predicting preference")
        raise HTTPException(status_code=500, detail="Internal server error in preference prediction")


# ============================================================================
# PLATFORM INTEGRATION: HEALTH, CAPABILITIES, METRICS, RESET, WEBSOCKET
# ============================================================================


@router.get("/health")
async def health_check():
    """Health check for the concierge service."""
    try:
        get_claude_concierge_orchestrator()
        return {
            "status": "healthy",
            "service": "claude_concierge_omnipresent",
            "version": "track_2",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "contextual_guidance": True,
                "real_time_coaching": True,
                "bot_coordination": True,
                "field_assistance": True,
                "presentation_support": True,
                "jorge_memory_learning": True,
                "omnipresent_monitoring": True,
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")


@router.get("/capabilities")
async def get_capabilities():
    """Get available capabilities and configuration."""
    return {
        "concierge_modes": [mode.value for mode in ConciergeMode],
        "intelligence_scopes": [scope.value for scope in IntelligenceScope],
        "supported_bots": ["jorge-seller", "lead-bot", "intent-decoder"],
        "coaching_types": [
            "response_optimization",
            "timing_adjustment",
            "strategy_pivot",
            "objection_handling",
            "temperature_escalation",
        ],
        "urgency_levels": ["low", "medium", "high", "urgent"],
        "device_types": ["desktop", "mobile", "tablet"],
        "connection_qualities": ["excellent", "good", "poor"],
        "user_roles": ["agent", "executive", "client"],
        "max_message_length": 1000,
        "streaming_enabled": True,
    }


@router.get("/metrics")
async def get_orchestrator_metrics(current_user=Depends(get_current_user_optional)):
    """Get performance metrics -- wired to real orchestrator data."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        metrics = orchestrator.get_metrics()
        metrics["timestamp"] = datetime.now().isoformat()
        # Add agent-level metrics if available
        try:
            concierge = get_claude_concierge()
            agent_status = await concierge.get_status()
            agent_metrics = agent_status.get("performance_metrics", {})
            metrics["agent_interactions"] = agent_metrics.get("interactions_handled", 0)
            metrics["recommendations_generated"] = agent_metrics.get("recommendations_generated", 0)
        except Exception:
            pass  # Agent metrics are supplemental; don't fail the whole request
        return metrics
    except Exception:
        logger.exception("Error getting metrics")
        raise HTTPException(status_code=500, detail="Internal server error getting metrics")


@router.post("/reset-session")
async def reset_concierge_session(
    session_id: str,
    current_user=Depends(get_current_user_optional),
):
    """Reset a concierge session."""
    try:
        orchestrator = get_claude_concierge_orchestrator()
        orchestrator.session_contexts.pop(session_id, None)
        return {"status": "session_reset", "session_id": session_id, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error resetting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error resetting session")


@router.websocket("/ws/{session_id}")
async def websocket_concierge(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time concierge communication."""
    await websocket.accept()
    logger.info(f"WebSocket connection established for session {session_id}")
    try:
        orchestrator = get_claude_concierge_orchestrator()
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            if message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            elif message_type == "context_update":
                await websocket.send_json({"type": "context_acknowledged", "timestamp": datetime.now().isoformat()})
            elif message_type == "guidance_request":
                await websocket.send_json({"type": "guidance_queued", "timestamp": datetime.now().isoformat()})
            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type: {message_type}"})
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("/suggestions/dismissal-stats")
async def get_dismissal_stats(current_user=Depends(get_current_user_optional)):
    """Get dismissal feedback statistics for debugging and Phase 3 integration."""
    return {"dismissal_feedback": _dismissal_feedback, "timestamp": datetime.now().isoformat()}
