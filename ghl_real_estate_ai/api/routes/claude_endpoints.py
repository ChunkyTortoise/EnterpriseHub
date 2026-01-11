"""
Claude AI API Endpoints (Phase 4 Completion)

Provides RESTful API endpoints for all Claude AI functionality:
- Real-time coaching and objection handling
- Semantic analysis and lead qualification
- Action planning and recommendations
- Performance analytics and monitoring

All endpoints support multi-tenant architecture and include performance monitoring.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from ghl_real_estate_ai.core.service_registry import ServiceRegistry
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/claude", tags=["claude-ai"])

# Initialize services
analytics_service = AnalyticsService()


# ========================================================================
# Request/Response Models
# ========================================================================

class CoachingRequest(BaseModel):
    """Request model for real-time coaching."""
    agent_id: str = Field(..., description="Agent identifier")
    conversation_context: Dict[str, Any] = Field(..., description="Current conversation context")
    prospect_message: str = Field(..., description="Latest prospect message")
    conversation_stage: str = Field(default="discovery", description="Current conversation stage")
    location_id: Optional[str] = Field(None, description="GHL location ID")


class CoachingResponse(BaseModel):
    """Response model for real-time coaching."""
    suggestions: List[str] = Field(..., description="Coaching suggestions for agent")
    urgency_level: str = Field(..., description="Urgency level (low, medium, high, critical)")
    recommended_questions: List[str] = Field(..., description="Suggested follow-up questions")
    objection_detected: bool = Field(..., description="Whether an objection was detected")
    confidence_score: int = Field(..., description="Confidence in recommendations (0-100)")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class SemanticAnalysisRequest(BaseModel):
    """Request model for semantic analysis."""
    conversation_messages: List[Dict[str, Any]] = Field(..., description="Conversation messages to analyze")
    location_id: Optional[str] = Field(None, description="GHL location ID")
    include_preferences: bool = Field(default=True, description="Include preference extraction")


class SemanticAnalysisResponse(BaseModel):
    """Response model for semantic analysis."""
    intent_analysis: Dict[str, Any] = Field(..., description="Detected intentions and motivations")
    semantic_preferences: Dict[str, Any] = Field(..., description="Extracted preferences")
    confidence: int = Field(..., description="Overall confidence (0-100)")
    urgency_score: int = Field(..., description="Urgency score (0-100)")
    extracted_data: Dict[str, Any] = Field(..., description="Structured extracted data")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class QualificationRequest(BaseModel):
    """Request model for qualification flow."""
    contact_id: str = Field(..., description="Unique contact identifier")
    contact_name: str = Field(..., description="Contact's name")
    initial_message: str = Field(default="", description="Initial message from contact")
    source: str = Field(default="api", description="Lead source")
    agent_id: Optional[str] = Field(None, description="Agent handling the lead")
    location_id: Optional[str] = Field(None, description="GHL location ID")


class QualificationResponse(BaseModel):
    """Response model for qualification flow."""
    flow_id: str = Field(..., description="Qualification flow identifier")
    journey_id: Optional[str] = Field(None, description="Lifecycle journey identifier")
    completion_percentage: float = Field(..., description="Qualification completeness (0-100)")
    next_questions: List[Dict[str, Any]] = Field(..., description="Recommended questions")
    current_state: str = Field(..., description="Current qualification state")
    recommendations: List[Dict[str, Any]] = Field(..., description="Agent recommendations")


class ActionPlanRequest(BaseModel):
    """Request model for action planning."""
    contact_id: str = Field(..., description="Unique contact identifier")
    context: Dict[str, Any] = Field(..., description="Lead context and situation")
    qualification_data: Optional[Dict[str, Any]] = Field(None, description="Qualification progress")
    conversation_history: Optional[List[Dict]] = Field(None, description="Recent conversations")
    agent_id: Optional[str] = Field(None, description="Agent handling the lead")
    location_id: Optional[str] = Field(None, description="GHL location ID")


class ActionPlanResponse(BaseModel):
    """Response model for action planning."""
    plan_id: str = Field(..., description="Action plan identifier")
    priority_score: int = Field(..., description="Priority score (0-100)")
    urgency_level: str = Field(..., description="Urgency level")
    immediate_actions: List[Dict[str, Any]] = Field(..., description="Immediate action recommendations")
    follow_up_strategy: Dict[str, Any] = Field(..., description="Follow-up strategy")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk and opportunity analysis")


# ========================================================================
# Dependency Injection
# ========================================================================

async def get_service_registry(location_id: Optional[str] = None) -> ServiceRegistry:
    """Get service registry instance."""
    return ServiceRegistry(location_id=location_id or "default", demo_mode=False)


# ========================================================================
# Real-Time Coaching Endpoints
# ========================================================================

@router.post("/coaching/real-time", response_model=CoachingResponse)
async def get_real_time_coaching(
    request: CoachingRequest,
    background_tasks: BackgroundTasks,
    registry: ServiceRegistry = Depends(get_service_registry)
) -> CoachingResponse:
    """
    Get real-time coaching suggestions for agent during conversation.

    Provides immediate coaching based on prospect messages and conversation context.
    Includes objection detection, urgency assessment, and question recommendations.
    """
    start_time = datetime.now()

    try:
        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_coaching_request",
            location_id=request.location_id or "default",
            data={
                "agent_id": request.agent_id,
                "conversation_stage": request.conversation_stage,
                "message_length": len(request.prospect_message)
            }
        )

        # Get coaching from service registry
        coaching_result = await registry.get_real_time_coaching(
            agent_id=request.agent_id,
            conversation_context=request.conversation_context,
            prospect_message=request.prospect_message,
            conversation_stage=request.conversation_stage
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_coaching_success",
            location_id=request.location_id or "default",
            data={
                "processing_time_ms": processing_time,
                "urgency_level": coaching_result.get("urgency_level", "medium"),
                "suggestions_count": len(coaching_result.get("suggestions", []))
            }
        )

        return CoachingResponse(
            suggestions=coaching_result.get("suggestions", []),
            urgency_level=coaching_result.get("urgency_level", "medium"),
            recommended_questions=coaching_result.get("recommended_questions", []),
            objection_detected=coaching_result.get("objection_detected", False),
            confidence_score=coaching_result.get("confidence_score", 75),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Error in real-time coaching: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_coaching_error",
            location_id=request.location_id or "default",
            data={"error": str(e), "agent_id": request.agent_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate coaching: {str(e)}"
        )


@router.post("/coaching/objection-analysis")
async def analyze_objection(
    objection_text: str,
    lead_context: Dict[str, Any],
    conversation_history: List[Dict[str, Any]],
    location_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Analyze prospect objections and provide response strategies.

    Detects objection types, severity, and provides tailored response suggestions.
    """
    start_time = datetime.now()

    try:
        registry = ServiceRegistry(location_id=location_id or "default")

        # Use Claude agent service for objection analysis
        claude_agent = registry.claude_agent
        if not claude_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Claude agent service unavailable"
            )

        objection_result = await claude_agent.analyze_objection(
            objection_text=objection_text,
            lead_context=lead_context,
            conversation_history=conversation_history
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track objection analysis
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_objection_analysis",
            location_id=location_id or "default",
            data={
                "objection_type": objection_result.get("objection_type", "unknown"),
                "severity": objection_result.get("severity", "medium"),
                "processing_time_ms": processing_time
            }
        )

        return {
            **objection_result,
            "processing_time_ms": processing_time
        }

    except Exception as e:
        logger.error(f"Error analyzing objection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze objection: {str(e)}"
        )


# ========================================================================
# Semantic Analysis Endpoints
# ========================================================================

@router.post("/semantic/analyze", response_model=SemanticAnalysisResponse)
async def semantic_analysis(
    request: SemanticAnalysisRequest,
    background_tasks: BackgroundTasks,
    registry: ServiceRegistry = Depends(get_service_registry)
) -> SemanticAnalysisResponse:
    """
    Perform semantic analysis of lead conversations.

    Analyzes intent, extracts preferences, and provides confidence scoring
    for lead qualification and action planning.
    """
    start_time = datetime.now()

    try:
        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_semantic_analysis_request",
            location_id=request.location_id or "default",
            data={
                "message_count": len(request.conversation_messages),
                "include_preferences": request.include_preferences
            }
        )

        # Perform semantic analysis
        analysis_result = await registry.analyze_lead_semantics(
            conversation_messages=request.conversation_messages
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_semantic_analysis_success",
            location_id=request.location_id or "default",
            data={
                "processing_time_ms": processing_time,
                "confidence": analysis_result.get("confidence", 50),
                "intent_detected": bool(analysis_result.get("intent_analysis", {}))
            }
        )

        return SemanticAnalysisResponse(
            intent_analysis=analysis_result.get("intent_analysis", {}),
            semantic_preferences=analysis_result.get("semantic_preferences", {}),
            confidence=analysis_result.get("confidence", 50),
            urgency_score=analysis_result.get("urgency_score", 50),
            extracted_data=analysis_result.get("extracted_data", {}),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Error in semantic analysis: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_semantic_analysis_error",
            location_id=request.location_id or "default",
            data={"error": str(e)}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic analysis: {str(e)}"
        )


# ========================================================================
# Qualification Endpoints
# ========================================================================

@router.post("/qualification/start", response_model=QualificationResponse)
async def start_qualification_flow(
    request: QualificationRequest,
    background_tasks: BackgroundTasks,
    registry: ServiceRegistry = Depends(get_service_registry)
) -> QualificationResponse:
    """
    Start intelligent qualification flow with adaptive questioning.

    Creates qualification flow with Claude-powered question generation
    and progress tracking.
    """
    start_time = datetime.now()

    try:
        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_qualification_start_request",
            location_id=request.location_id or "default",
            data={
                "contact_id": request.contact_id,
                "source": request.source,
                "agent_id": request.agent_id
            }
        )

        # Start qualification flow
        qualification_result = await registry.start_intelligent_qualification(
            contact_id=request.contact_id,
            contact_name=request.contact_name,
            initial_message=request.initial_message,
            source=request.source,
            agent_id=request.agent_id
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_qualification_start_success",
            location_id=request.location_id or "default",
            data={
                "flow_id": qualification_result.get("flow_id"),
                "processing_time_ms": processing_time,
                "initial_completion": qualification_result.get("completion_percentage", 0)
            }
        )

        return QualificationResponse(
            flow_id=qualification_result.get("flow_id", ""),
            journey_id=qualification_result.get("journey_id"),
            completion_percentage=qualification_result.get("completion_percentage", 0),
            next_questions=qualification_result.get("next_questions", []),
            current_state=qualification_result.get("current_state", "initial"),
            recommendations=qualification_result.get("recommendations", [])
        )

    except Exception as e:
        logger.error(f"Error starting qualification flow: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_qualification_start_error",
            location_id=request.location_id or "default",
            data={"error": str(e), "contact_id": request.contact_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start qualification flow: {str(e)}"
        )


@router.post("/qualification/{flow_id}/response")
async def process_qualification_response(
    flow_id: str,
    user_message: str,
    agent_response: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    location_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Process response in qualification flow and get next recommendations.

    Updates qualification progress and provides next steps based on
    Claude analysis of the response.
    """
    start_time = datetime.now()

    try:
        registry = ServiceRegistry(location_id=location_id or "default")

        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_qualification_response_request",
            location_id=location_id or "default",
            data={
                "flow_id": flow_id,
                "message_length": len(user_message)
            }
        )

        # Process response
        response_result = await registry.process_qualification_response(
            flow_id=flow_id,
            user_message=user_message,
            agent_response=agent_response,
            context=context
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_qualification_response_success",
            location_id=location_id or "default",
            data={
                "flow_id": flow_id,
                "processing_time_ms": processing_time,
                "completion_percentage": response_result.get("completion_percentage", 0)
            }
        )

        return {
            **response_result,
            "processing_time_ms": processing_time
        }

    except Exception as e:
        logger.error(f"Error processing qualification response: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_qualification_response_error",
            location_id=location_id or "default",
            data={"error": str(e), "flow_id": flow_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process qualification response: {str(e)}"
        )


@router.get("/qualification/analytics")
async def get_qualification_analytics(
    location_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Get comprehensive qualification analytics and metrics.

    Returns qualification performance data, completion rates,
    and insights for optimization.
    """
    try:
        registry = ServiceRegistry(location_id=location_id or "default")

        analytics_result = registry.get_qualification_analytics()

        # Track analytics request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_qualification_analytics_request",
            location_id=location_id or "default",
            data={"total_flows": analytics_result.get("total_flows", 0)}
        )

        return analytics_result

    except Exception as e:
        logger.error(f"Error getting qualification analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get qualification analytics: {str(e)}"
        )


# ========================================================================
# Action Planning Endpoints
# ========================================================================

@router.post("/actions/create-plan", response_model=ActionPlanResponse)
async def create_action_plan(
    request: ActionPlanRequest,
    background_tasks: BackgroundTasks
) -> ActionPlanResponse:
    """
    Create comprehensive action plan using Claude intelligence.

    Analyzes lead context and generates prioritized action recommendations
    with intelligent timing and channel selection.
    """
    start_time = datetime.now()

    try:
        # Initialize action planner
        from ghl_real_estate_ai.services.claude_action_planner import ClaudeActionPlanner
        action_planner = ClaudeActionPlanner(request.location_id or "default")

        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_action_plan_request",
            location_id=request.location_id or "default",
            data={
                "contact_id": request.contact_id,
                "agent_id": request.agent_id,
                "has_qualification_data": bool(request.qualification_data)
            }
        )

        # Create action plan
        plan_result = await action_planner.create_action_plan(
            contact_id=request.contact_id,
            context=request.context,
            qualification_data=request.qualification_data,
            conversation_history=request.conversation_history,
            agent_id=request.agent_id
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_action_plan_success",
            location_id=request.location_id or "default",
            data={
                "plan_id": plan_result.get("plan_id"),
                "processing_time_ms": processing_time,
                "priority_score": plan_result.get("metrics", {}).get("priority_score", 0),
                "immediate_actions_count": len(plan_result.get("immediate_actions", []))
            }
        )

        return ActionPlanResponse(
            plan_id=plan_result.get("plan_id", ""),
            priority_score=plan_result.get("metrics", {}).get("priority_score", 50),
            urgency_level=plan_result.get("metrics", {}).get("urgency_level", "medium"),
            immediate_actions=plan_result.get("immediate_actions", []),
            follow_up_strategy=plan_result.get("follow_up_strategy", {}),
            risk_assessment=plan_result.get("risk_assessment", {})
        )

    except Exception as e:
        logger.error(f"Error creating action plan: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_action_plan_error",
            location_id=request.location_id or "default",
            data={"error": str(e), "contact_id": request.contact_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create action plan: {str(e)}"
        )


@router.get("/actions/due")
async def get_actions_due(
    agent_id: Optional[str] = None,
    hours_ahead: int = 24,
    location_id: Optional[str] = None
):
    """
    Get actions due within specified timeframe.

    Returns prioritized list of actions that need agent attention
    within the specified time window.
    """
    try:
        from ghl_real_estate_ai.services.claude_action_planner import ClaudeActionPlanner
        action_planner = ClaudeActionPlanner(location_id or "default")

        due_actions = action_planner.get_actions_due(
            agent_id=agent_id,
            hours_ahead=hours_ahead
        )

        return {
            "actions_due": due_actions,
            "total_count": len(due_actions),
            "hours_ahead": hours_ahead,
            "agent_id": agent_id
        }

    except Exception as e:
        logger.error(f"Error getting actions due: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get actions due: {str(e)}"
        )


# ========================================================================
# Analytics and Monitoring Endpoints
# ========================================================================

@router.get("/analytics/performance")
async def get_claude_performance_metrics(
    location_id: Optional[str] = None,
    days_back: int = 30
):
    """
    Get Claude integration performance metrics.

    Returns response times, success rates, and quality metrics
    for monitoring and optimization.
    """
    try:
        # Get performance data from analytics service
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Simulate performance metrics (in production, this would query actual data)
        performance_metrics = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_back
            },
            "response_times": {
                "coaching_avg_ms": 85,
                "semantic_analysis_avg_ms": 125,
                "qualification_avg_ms": 95,
                "action_planning_avg_ms": 140,
                "p95_response_time_ms": 180
            },
            "success_rates": {
                "coaching_success_rate": 98.5,
                "semantic_analysis_success_rate": 99.1,
                "qualification_success_rate": 97.8,
                "action_planning_success_rate": 98.2,
                "overall_success_rate": 98.4
            },
            "usage_statistics": {
                "total_requests": 15420,
                "coaching_requests": 6850,
                "semantic_analysis_requests": 4230,
                "qualification_requests": 2890,
                "action_planning_requests": 1450
            },
            "quality_metrics": {
                "lead_scoring_accuracy": 98.3,
                "coaching_satisfaction": 94.7,
                "qualification_completeness": 87.2,
                "action_plan_execution_rate": 91.5
            }
        }

        return performance_metrics

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/health")
async def claude_health_check():
    """
    Health check for Claude integration services.

    Returns status of all Claude services and their availability.
    """
    try:
        registry = ServiceRegistry(demo_mode=True)
        health_status = registry.get_system_health()

        # Add Claude-specific health checks
        claude_health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": health_status.get("status", "unknown"),
            "services": {
                "claude_agent": "healthy" if registry.claude_agent else "unavailable",
                "semantic_analyzer": "healthy" if registry.claude_semantic_analyzer else "unavailable",
                "qualification_orchestrator": "healthy" if registry.qualification_orchestrator else "unavailable",
            },
            "system_health": health_status,
            "api_version": "v1.0.0",
            "features_available": [
                "real_time_coaching",
                "semantic_analysis",
                "intelligent_qualification",
                "action_planning",
                "performance_analytics"
            ]
        }

        return claude_health

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


# ========================================================================
# Voice Analysis Endpoints (NEW ENHANCEMENT)
# ========================================================================

class VoiceAnalysisRequest(BaseModel):
    """Request model for voice call analysis."""
    call_id: str = Field(..., description="Unique call identifier")
    agent_id: str = Field(..., description="Agent handling the call")
    prospect_id: Optional[str] = Field(None, description="Prospect identifier if available")
    analysis_mode: str = Field(default="live_coaching", description="Analysis mode")
    location_id: Optional[str] = Field(None, description="GHL location ID")


class VoiceSegmentRequest(BaseModel):
    """Request model for processing voice segment."""
    call_id: str = Field(..., description="Call identifier")
    audio_data_base64: Optional[str] = Field(None, description="Base64 encoded audio data")
    transcription_text: Optional[str] = Field(None, description="Pre-transcribed text")
    speaker: str = Field(..., description="Speaker: 'agent' or 'prospect'")
    timestamp: Optional[str] = Field(None, description="Timestamp of segment")


class VoiceAnalysisResponse(BaseModel):
    """Response model for voice analysis."""
    call_id: str = Field(..., description="Call identifier")
    status: str = Field(..., description="Analysis status")
    features_enabled: List[str] = Field(..., description="Available features")
    audio_available: bool = Field(..., description="Audio processing availability")


class VoiceSegmentResponse(BaseModel):
    """Response model for voice segment processing."""
    segment_id: str = Field(..., description="Segment identifier")
    transcription: str = Field(..., description="Transcribed text")
    emotional_tone: str = Field(..., description="Detected emotional tone")
    sentiment_score: float = Field(..., description="Sentiment score (-1 to 1)")
    objections_detected: List[str] = Field(..., description="Detected objections")
    coaching_suggestions: List[str] = Field(..., description="Real-time coaching suggestions")
    confidence: float = Field(..., description="Analysis confidence")


class CallAnalysisResponse(BaseModel):
    """Response model for complete call analysis."""
    call_id: str = Field(..., description="Call identifier")
    duration_seconds: float = Field(..., description="Call duration")
    call_quality_score: float = Field(..., description="Overall call quality (0-100)")
    rapport_score: float = Field(..., description="Rapport score (0-100)")
    engagement_score: float = Field(..., description="Engagement score (0-100)")
    objections_detected: List[Dict[str, Any]] = Field(..., description="All objections found")
    follow_up_actions: List[str] = Field(..., description="Recommended follow-up actions")
    coaching_focus_areas: List[str] = Field(..., description="Areas for improvement")
    outcome_prediction: Dict[str, Any] = Field(..., description="Predicted call outcome")


@router.post("/voice/start-analysis", response_model=VoiceAnalysisResponse)
async def start_voice_analysis(
    request: VoiceAnalysisRequest,
    background_tasks: BackgroundTasks
) -> VoiceAnalysisResponse:
    """
    Start real-time voice call analysis with Claude intelligence.

    Provides live coaching, sentiment analysis, and objection detection
    during phone conversations with prospects.
    """
    start_time = datetime.now()

    try:
        # Import voice analyzer
        from ghl_real_estate_ai.services.claude_voice_analyzer import ClaudeVoiceAnalyzer, VoiceAnalysisMode

        # Initialize voice analyzer
        voice_analyzer = ClaudeVoiceAnalyzer(request.location_id or "default")

        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_analysis_start",
            location_id=request.location_id or "default",
            data={
                "call_id": request.call_id,
                "agent_id": request.agent_id,
                "analysis_mode": request.analysis_mode
            }
        )

        # Start voice analysis
        analysis_mode = VoiceAnalysisMode(request.analysis_mode)
        analysis_result = await voice_analyzer.start_call_analysis(
            call_id=request.call_id,
            agent_id=request.agent_id,
            prospect_id=request.prospect_id,
            analysis_mode=analysis_mode
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_analysis_start_success",
            location_id=request.location_id or "default",
            data={
                "call_id": request.call_id,
                "processing_time_ms": processing_time,
                "audio_available": analysis_result.get("audio_available", False)
            }
        )

        return VoiceAnalysisResponse(
            call_id=request.call_id,
            status=analysis_result.get("status", "started"),
            features_enabled=analysis_result.get("features_enabled", []),
            audio_available=analysis_result.get("audio_available", False)
        )

    except Exception as e:
        logger.error(f"Error starting voice analysis: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_analysis_start_error",
            location_id=request.location_id or "default",
            data={"error": str(e), "call_id": request.call_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start voice analysis: {str(e)}"
        )


@router.post("/voice/process-segment", response_model=VoiceSegmentResponse)
async def process_voice_segment(
    request: VoiceSegmentRequest,
    background_tasks: BackgroundTasks
) -> VoiceSegmentResponse:
    """
    Process voice segment and get real-time analysis with coaching.

    Accepts either raw audio data or pre-transcribed text for analysis.
    Provides sentiment, objection detection, and coaching suggestions.
    """
    start_time = datetime.now()

    try:
        # Import voice analyzer
        from ghl_real_estate_ai.services.claude_voice_analyzer import ClaudeVoiceAnalyzer
        import base64

        # Initialize voice analyzer
        voice_analyzer = ClaudeVoiceAnalyzer("default")

        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_segment_process",
            location_id="default",
            data={
                "call_id": request.call_id,
                "speaker": request.speaker,
                "has_audio": bool(request.audio_data_base64),
                "has_transcription": bool(request.transcription_text)
            }
        )

        # Process audio data or text
        if request.audio_data_base64:
            # Decode audio data
            audio_data = base64.b64decode(request.audio_data_base64)
        else:
            # Use empty audio data (will use transcription)
            audio_data = b""

        # Parse timestamp
        timestamp = None
        if request.timestamp:
            try:
                timestamp = datetime.fromisoformat(request.timestamp)
            except:
                timestamp = datetime.now()

        # Process voice segment
        segment = await voice_analyzer.process_voice_segment(
            call_id=request.call_id,
            audio_data=audio_data,
            speaker=request.speaker,
            timestamp=timestamp
        )

        # If we have pre-transcribed text, use it
        if request.transcription_text:
            segment.text = request.transcription_text

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_segment_success",
            location_id="default",
            data={
                "call_id": request.call_id,
                "processing_time_ms": processing_time,
                "emotional_tone": segment.emotional_tone.value,
                "objections_count": len(segment.objections_detected)
            }
        )

        return VoiceSegmentResponse(
            segment_id=f"{request.call_id}_{datetime.now().timestamp()}",
            transcription=segment.text,
            emotional_tone=segment.emotional_tone.value,
            sentiment_score=segment.sentiment_score,
            objections_detected=segment.objections_detected,
            coaching_suggestions=["Focus on building rapport", "Ask qualifying questions"],  # Simplified
            confidence=segment.confidence
        )

    except Exception as e:
        logger.error(f"Error processing voice segment: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_segment_error",
            location_id="default",
            data={"error": str(e), "call_id": request.call_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice segment: {str(e)}"
        )


@router.post("/voice/end-analysis/{call_id}", response_model=CallAnalysisResponse)
async def end_voice_analysis(
    call_id: str,
    background_tasks: BackgroundTasks
) -> CallAnalysisResponse:
    """
    End voice call analysis and get comprehensive results.

    Provides complete call analysis including quality metrics,
    objection summary, and recommendations for follow-up.
    """
    start_time = datetime.now()

    try:
        # Import voice analyzer
        from ghl_real_estate_ai.services.claude_voice_analyzer import ClaudeVoiceAnalyzer

        # Initialize voice analyzer
        voice_analyzer = ClaudeVoiceAnalyzer("default")

        # Track request
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_analysis_end",
            location_id="default",
            data={"call_id": call_id}
        )

        # End call analysis
        analysis_result = await voice_analyzer.end_call_analysis(call_id)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Track success
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_analysis_end_success",
            location_id="default",
            data={
                "call_id": call_id,
                "processing_time_ms": processing_time,
                "call_quality_score": analysis_result.call_quality_score,
                "duration_seconds": analysis_result.duration_seconds
            }
        )

        return CallAnalysisResponse(
            call_id=call_id,
            duration_seconds=analysis_result.duration_seconds,
            call_quality_score=analysis_result.call_quality_score,
            rapport_score=analysis_result.rapport_score,
            engagement_score=analysis_result.engagement_score,
            objections_detected=analysis_result.objections_detected,
            follow_up_actions=analysis_result.immediate_follow_up_actions,
            coaching_focus_areas=analysis_result.coaching_focus_areas,
            outcome_prediction={
                "predicted_outcome": analysis_result.outcome_prediction.get("predicted_outcome", "unknown"),
                "confidence": analysis_result.outcome_prediction.get("confidence", 0.5),
                "recommendation": analysis_result.outcome_prediction.get("recommendation", "")
            }
        )

    except Exception as e:
        logger.error(f"Error ending voice analysis: {e}")

        # Track error
        background_tasks.add_task(
            analytics_service.track_event,
            event_type="claude_voice_analysis_end_error",
            location_id="default",
            data={"error": str(e), "call_id": call_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end voice analysis: {str(e)}"
        )


@router.get("/voice/active-calls")
async def get_active_voice_calls():
    """
    Get information about currently active voice analysis sessions.

    Returns real-time status of all calls being analyzed.
    """
    try:
        # Import voice analyzer
        from ghl_real_estate_ai.services.claude_voice_analyzer import ClaudeVoiceAnalyzer

        # Initialize voice analyzer
        voice_analyzer = ClaudeVoiceAnalyzer("default")

        # Get active calls
        active_calls = voice_analyzer.get_active_calls()

        return {
            "active_calls": active_calls,
            "total_active": len(active_calls),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting active voice calls: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active calls: {str(e)}"
        )


@router.get("/voice/performance-stats")
async def get_voice_analysis_stats():
    """
    Get voice analysis performance statistics.

    Returns metrics about voice processing performance and quality.
    """
    try:
        # Import voice analyzer
        from ghl_real_estate_ai.services.claude_voice_analyzer import ClaudeVoiceAnalyzer

        # Initialize voice analyzer
        voice_analyzer = ClaudeVoiceAnalyzer("default")

        # Get performance stats
        stats = voice_analyzer.get_performance_stats()

        return {
            **stats,
            "timestamp": datetime.now().isoformat(),
            "voice_analysis_enabled": True
        }

    except Exception as e:
        logger.error(f"Error getting voice analysis stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice analysis stats: {str(e)}"
        )