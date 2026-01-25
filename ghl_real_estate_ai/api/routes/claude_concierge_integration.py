"""
Claude Concierge Integration API Routes
Provides REST endpoints that match the frontend ClaudeConciergeAPI.ts expectations.
Complements the existing claude_concierge.py with additional integration endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid

from ghl_real_estate_ai.agents.claude_concierge_agent import get_claude_concierge
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.api.middleware.enhanced_auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/claude-concierge", tags=["claude-concierge-integration"])

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
            timestamp=datetime.now().isoformat()
        ),
        ConciergeInsight(
            category="Response Time",
            title="Avg Response",
            value="2.3 min",
            trend="down",
            trendValue=-12.5,
            description="Average response time improved by 12.5% since Jorge's optimization",
            timestamp=datetime.now().isoformat()
        ),
        ConciergeInsight(
            category="Commission Pipeline",
            title="Pipeline Value",
            value="$847K",
            trend="up",
            trendValue=18.3,
            description="Commission pipeline value increased significantly this month",
            timestamp=datetime.now().isoformat()
        ),
        ConciergeInsight(
            category="Bot Coordination",
            title="Handoff Success",
            value="94%",
            trend="stable",
            trendValue=0.8,
            description="Agent coordination efficiency remains consistently high",
            timestamp=datetime.now().isoformat()
        ),
        ConciergeInsight(
            category="Property Analysis",
            title="CMA Accuracy",
            value="96.2%",
            trend="up",
            trendValue=2.1,
            description="Property valuation accuracy continues to improve with ML enhancements",
            timestamp=datetime.now().isoformat()
        )
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
            createdAt=datetime.now().isoformat()
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
            createdAt=datetime.now().isoformat()
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
            createdAt=datetime.now().isoformat()
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
            createdAt=datetime.now().isoformat()
        )
    ]
    return suggestions

# ============================================================================
# INTEGRATION ENDPOINTS (Match Frontend Expectations)
# ============================================================================

@router.post("/chat", response_model=ConciergeResponse)
async def send_message(
    request: ChatRequest,
    current_user = Depends(get_current_user)
):
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
            "message": request.message
        }

        # Process the interaction with the concierge agent
        response = await concierge.process_user_interaction(
            user_id=request.sessionId,
            message=request.message,
            context=user_context
        )

        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Extract the primary response
        concierge_response = response.get("concierge_response", {})
        primary_response = concierge_response.get("content", "I'm here to help! How can I assist you today?")

        # Get insights and suggestions
        insights = generate_mock_insights()[:3]  # Limit to 3 for chat response
        suggestions = generate_mock_suggestions()[:2]  # Limit to 2 for chat response

        # Build agent context
        agent_context = [
            "claude-concierge",
            "platform-intelligence",
            "real-time-analytics"
        ]

        # Generate actionable responses
        actions = [
            {
                "type": "quick_action",
                "label": "View Lead Details",
                "action": "navigate_to_leads",
                "metadata": {"priority": "high"}
            },
            {
                "type": "suggestion",
                "label": "Optimize Jorge Settings",
                "action": "open_jorge_config",
                "metadata": {"impact": "medium"}
            }
        ]

        result = ConciergeResponse(
            response=primary_response,
            insights=insights,
            suggestions=suggestions,
            actions=actions,
            confidence=0.89,
            processingTime=processing_time,
            agentContext=agent_context
        )

        logger.info(f"Concierge chat response generated in {processing_time}ms")
        return result

    except Exception as e:
        logger.error(f"Error processing concierge chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@router.get("/insights", response_model=List[ConciergeInsight])
async def get_realtime_insights(
    current_user = Depends(get_current_user)
):
    """
    Get real-time insights from the concierge.
    Matches frontend ClaudeConciergeAPI.getRealtimeInsights() expectation.
    """
    try:
        logger.info("Fetching real-time concierge insights")

        # Generate insights (in production, this would analyze real platform data)
        insights = generate_mock_insights()

        logger.info(f"Generated {len(insights)} concierge insights")
        return insights

    except Exception as e:
        logger.error(f"Error fetching concierge insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch insights")

@router.get("/suggestions", response_model=List[ProactiveSuggestion])
async def get_proactive_suggestions(
    current_user = Depends(get_current_user)
):
    """
    Get proactive suggestions from the concierge.
    Matches frontend ClaudeConciergeAPI.getProactiveSuggestions() expectation.
    """
    try:
        logger.info("Fetching proactive concierge suggestions")

        # Generate suggestions (in production, this would analyze patterns and opportunities)
        suggestions = generate_mock_suggestions()

        logger.info(f"Generated {len(suggestions)} proactive suggestions")
        return suggestions

    except Exception as e:
        logger.error(f"Error fetching proactive suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch suggestions")

@router.post("/suggestions/{suggestion_id}/apply")
async def apply_suggestion(
    suggestion_id: str,
    current_user = Depends(get_current_user)
):
    """
    Apply a proactive suggestion.
    Matches frontend ClaudeConciergeAPI.applySuggestion() expectation.
    """
    try:
        logger.info(f"Applying suggestion: {suggestion_id}")

        # TODO: Implement actual suggestion application logic
        # This would vary based on suggestion type (optimization, automation, etc.)

        # Mock successful application
        result = {
            "success": True,
            "result": f"Suggestion {suggestion_id} applied successfully",
            "followUpActions": [
                "Monitor performance metrics for 24 hours",
                "Review impact on lead conversion rates",
                "Adjust parameters if needed"
            ]
        }

        # Publish suggestion applied event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event("suggestion_applied", {
            "suggestion_id": suggestion_id,
            "user_id": current_user.id if hasattr(current_user, 'id') else 'unknown',
            "timestamp": datetime.now().isoformat(),
            "result": result
        })

        logger.info(f"Suggestion {suggestion_id} applied successfully")
        return result

    except Exception as e:
        logger.error(f"Error applying suggestion {suggestion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply suggestion {suggestion_id}")

@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: str,
    dismiss_reason: Dict[str, str],
    current_user = Depends(get_current_user)
):
    """
    Dismiss a proactive suggestion.
    Matches frontend ClaudeConciergeAPI.dismissSuggestion() expectation.
    """
    try:
        reason = dismiss_reason.get("reason", "User dismissed")
        logger.info(f"Dismissing suggestion {suggestion_id}: {reason}")

        # TODO: Implement suggestion dismissal logic
        # This would remove the suggestion and potentially learn from the dismissal

        # Publish suggestion dismissed event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event("suggestion_dismissed", {
            "suggestion_id": suggestion_id,
            "reason": reason,
            "user_id": current_user.id if hasattr(current_user, 'id') else 'unknown',
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Suggestion {suggestion_id} dismissed")
        return {"success": True, "message": "Suggestion dismissed"}

    except Exception as e:
        logger.error(f"Error dismissing suggestion {suggestion_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to dismiss suggestion {suggestion_id}")

# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/analyze/platform")
async def analyze_platform_performance(
    current_user = Depends(get_current_user)
):
    """
    Analyze overall platform performance.
    Matches frontend ClaudeConciergeAPI.analyzePlatformPerformance() expectation.
    """
    try:
        logger.info("Analyzing platform performance")

        # Mock platform analysis
        analysis = {
            "overallHealth": 94,
            "keyMetrics": generate_mock_insights()[:4],
            "recommendations": generate_mock_suggestions()[:3],
            "alerts": [
                {
                    "level": "info",
                    "message": "Jorge's response optimization is performing well",
                    "action": "Continue monitoring"
                },
                {
                    "level": "warning",
                    "message": "3 leads haven't been contacted in 6+ hours",
                    "action": "Review lead assignment"
                }
            ]
        }

        logger.info("Platform analysis completed")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing platform performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze platform performance")

@router.get("/analyze/coordination")
async def analyze_agent_coordination(
    current_user = Depends(get_current_user)
):
    """
    Analyze agent coordination efficiency.
    Matches frontend ClaudeConciergeAPI.analyzeAgentCoordination() expectation.
    """
    try:
        logger.info("Analyzing agent coordination")

        # Mock coordination analysis
        analysis = {
            "efficiencyScore": 91,
            "handoffAnalysis": {
                "successful": 847,
                "failed": 23,
                "avgDuration": 3200,
                "bottlenecks": [
                    "Intent decoder sometimes delays handoffs by 5-10 seconds",
                    "Property intelligence agent occasionally requires manual intervention"
                ]
            },
            "optimizationSuggestions": generate_mock_suggestions()[:2]
        }

        logger.info("Agent coordination analysis completed")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing agent coordination: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze agent coordination")

@router.get("/analyze/journeys")
async def analyze_customer_journeys(
    current_user = Depends(get_current_user)
):
    """
    Analyze customer journey performance.
    Matches frontend ClaudeConciergeAPI.analyzeCustomerJourneys() expectation.
    """
    try:
        logger.info("Analyzing customer journeys")

        # Mock journey analysis
        analysis = {
            "activeJourneys": 45,
            "completionRate": 78.5,
            "avgSatisfaction": 4.3,
            "stageAnalysis": {
                "initial_contact": {
                    "count": 67,
                    "avgDuration": 1800,
                    "dropoffRate": 12.2
                },
                "qualification": {
                    "count": 59,
                    "avgDuration": 2400,
                    "dropoffRate": 8.5
                },
                "property_matching": {
                    "count": 54,
                    "avgDuration": 4200,
                    "dropoffRate": 15.7
                },
                "negotiation": {
                    "count": 42,
                    "avgDuration": 7200,
                    "dropoffRate": 19.0
                }
            },
            "improvementSuggestions": generate_mock_suggestions()[:2]
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
async def update_context(
    context_update: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """
    Update platform context for the concierge.
    Matches frontend ClaudeConciergeAPI.updateContext() expectation.
    """
    try:
        session_id = context_update.get("sessionId")
        context = context_update.get("context", {})

        if not session_id:
            raise HTTPException(status_code=400, detail="sessionId required")

        logger.info(f"Updating context for session {session_id}")

        # TODO: Store context update in session management
        # This would update the concierge's awareness of the user's current state

        logger.info(f"Context updated for session {session_id}")
        return {"success": True, "sessionId": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating context: {e}")
        raise HTTPException(status_code=500, detail="Failed to update context")

@router.get("/context/{session_id}")
async def get_context(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get current context for a session.
    Matches frontend ClaudeConciergeAPI.getContext() expectation.
    """
    try:
        logger.info(f"Fetching context for session {session_id}")

        # Mock context data
        context = PlatformContext(
            currentPage="/dashboard",
            userRole="agent",
            sessionId=session_id,
            locationContext={"timezone": "America/New_York"},
            activeLeads=[
                {"id": "lead-1", "name": "John Doe", "status": "hot"},
                {"id": "lead-2", "name": "Jane Smith", "status": "warm"}
            ],
            botStatuses={
                "jorge": "active",
                "property-intelligence": "processing",
                "journey-orchestrator": "active"
            }
        )

        logger.info(f"Context retrieved for session {session_id}")
        return context

    except Exception as e:
        logger.error(f"Error fetching context for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch context for session {session_id}")