"""
Advanced Conversation Intelligence API Endpoints - Phase 2 Enhancement

FastAPI endpoints for Claude's advanced conversation intelligence capabilities.
Provides emotional analysis, flow optimization, objection detection, and strategic recommendations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
import json

from ...services.advanced_conversation_intelligence import (
    get_advanced_conversation_intelligence,
    AdvancedConversationIntelligence,
    ConversationIntelligenceResult,
    EmotionalState,
    UrgencyLevel,
    ConversationStage,
    ConversationHealth,
    EmotionalAnalysis,
    ConversationFlowAnalysis,
    ObjectionAnalysis,
    FamilyDynamicsAnalysis
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/claude/conversation", tags=["conversation-intelligence"])


# Pydantic Models for API
class ConversationMessage(BaseModel):
    """Individual conversation message."""
    speaker: str = Field(..., description="Speaker identifier (agent, prospect, spouse, etc.)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    message_type: Optional[str] = Field("text", description="Message type (text, action, system)")


class ConversationAnalysisRequest(BaseModel):
    """Request model for conversation analysis."""
    conversation_history: List[ConversationMessage] = Field(..., description="Conversation messages")
    agent_id: str = Field(..., description="Agent ID requesting analysis")
    lead_context: Optional[Dict[str, Any]] = Field(None, description="Additional lead context")
    real_time_mode: bool = Field(False, description="Enable real-time processing optimizations")
    analysis_focus: Optional[str] = Field("comprehensive", description="Analysis focus area")


class EmotionalAnalysisRequest(BaseModel):
    """Request model for focused emotional analysis."""
    conversation_history: List[ConversationMessage] = Field(..., description="Conversation messages")
    lead_context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ObjectionDetectionRequest(BaseModel):
    """Request model for objection detection."""
    conversation_history: List[ConversationMessage] = Field(..., description="Conversation messages")
    sensitivity_level: str = Field("standard", description="Detection sensitivity (low, standard, high)")


class FlowOptimizationRequest(BaseModel):
    """Request model for conversation flow optimization."""
    conversation_history: List[ConversationMessage] = Field(..., description="Conversation messages")
    target_stage: Optional[ConversationStage] = Field(None, description="Target conversation stage")
    optimization_goal: str = Field("progression", description="Optimization goal")


class ConversationHealthResponse(BaseModel):
    """Response model for conversation health check."""
    conversation_id: str
    health_status: ConversationHealth
    health_score: float
    key_concerns: List[str]
    improvement_recommendations: List[str]
    immediate_actions: List[str]
    timestamp: datetime


class RealTimeInsightsResponse(BaseModel):
    """Response model for real-time conversation insights."""
    conversation_id: str
    current_emotional_state: EmotionalState
    conversation_stage: ConversationStage
    urgency_level: UrgencyLevel
    objection_alerts: List[str]
    recommended_responses: List[str]
    coaching_tips: List[str]
    confidence_score: float
    timestamp: datetime


class ConversationMetricsResponse(BaseModel):
    """Response model for conversation metrics."""
    agent_id: str
    date_range: str
    total_conversations: int
    average_health_score: float
    common_objections: List[Dict[str, Any]]
    emotional_state_distribution: Dict[str, float]
    stage_completion_rates: Dict[str, float]
    success_predictors: List[str]


@router.post("/analyze", response_model=ConversationIntelligenceResult)
async def analyze_conversation_intelligence(
    request: ConversationAnalysisRequest,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> ConversationIntelligenceResult:
    """
    Perform comprehensive conversation intelligence analysis.

    Analyzes emotional states, conversation flow, objections, family dynamics,
    and provides strategic recommendations for real estate conversations.

    - **conversation_history**: List of conversation messages with speaker and content
    - **agent_id**: Agent requesting the analysis
    - **lead_context**: Additional context about the lead/prospect
    - **real_time_mode**: Enable optimizations for real-time processing
    - **analysis_focus**: Specific focus area for analysis

    Returns complete conversation intelligence with actionable insights.
    """
    try:
        logger.info(f"Starting conversation intelligence analysis for agent {request.agent_id}")

        # Convert Pydantic messages to dict format
        conversation_history = [
            {
                "speaker": msg.speaker,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else datetime.now().isoformat(),
                "message_type": msg.message_type
            }
            for msg in request.conversation_history
        ]

        result = await intelligence_service.analyze_conversation_intelligence(
            conversation_history=conversation_history,
            agent_id=request.agent_id,
            lead_context=request.lead_context,
            real_time_mode=request.real_time_mode
        )

        logger.info(f"Conversation intelligence analysis completed: {result.conversation_id}")
        return result

    except Exception as e:
        logger.error(f"Error in conversation intelligence analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/emotional-analysis", response_model=EmotionalAnalysis)
async def analyze_emotional_state(
    request: EmotionalAnalysisRequest,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> EmotionalAnalysis:
    """
    Analyze emotional states in conversation.

    Focuses specifically on emotional intelligence analysis including:
    - Primary and secondary emotional states
    - Stress level detection
    - Decision readiness assessment
    - Motivation factors identification
    """
    try:
        # Convert messages to required format
        conversation_history = [
            {
                "speaker": msg.speaker,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else datetime.now().isoformat()
            }
            for msg in request.conversation_history
        ]

        emotional_analysis = await intelligence_service._analyze_emotional_state(
            conversation_history=conversation_history,
            lead_context=request.lead_context
        )

        return emotional_analysis

    except Exception as e:
        logger.error(f"Error in emotional analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Emotional analysis failed: {str(e)}")


@router.post("/objection-detection", response_model=ObjectionAnalysis)
async def detect_objections(
    request: ObjectionDetectionRequest,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> ObjectionAnalysis:
    """
    Detect and analyze objections in conversation.

    Provides advanced objection detection including:
    - Explicit and implicit objection identification
    - Root cause analysis
    - Severity assessment
    - Handling strategy recommendations
    """
    try:
        # Convert messages to required format
        conversation_history = [
            {
                "speaker": msg.speaker,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else datetime.now().isoformat()
            }
            for msg in request.conversation_history
        ]

        objection_analysis = await intelligence_service._detect_and_analyze_objections(
            conversation_history=conversation_history,
            lead_context=None
        )

        return objection_analysis

    except Exception as e:
        logger.error(f"Error in objection detection: {e}")
        raise HTTPException(status_code=500, detail=f"Objection detection failed: {str(e)}")


@router.post("/flow-optimization", response_model=ConversationFlowAnalysis)
async def optimize_conversation_flow(
    request: FlowOptimizationRequest,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> ConversationFlowAnalysis:
    """
    Analyze and optimize conversation flow.

    Provides conversation flow optimization including:
    - Current stage identification
    - Progression readiness assessment
    - Bottleneck identification
    - Acceleration opportunities
    """
    try:
        # Convert messages to required format
        conversation_history = [
            {
                "speaker": msg.speaker,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else datetime.now().isoformat()
            }
            for msg in request.conversation_history
        ]

        flow_analysis = await intelligence_service._analyze_conversation_flow(
            conversation_history=conversation_history,
            lead_context=None
        )

        return flow_analysis

    except Exception as e:
        logger.error(f"Error in flow optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Flow optimization failed: {str(e)}")


@router.get("/health/{conversation_id}", response_model=ConversationHealthResponse)
async def get_conversation_health(
    conversation_id: str,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> ConversationHealthResponse:
    """
    Get conversation health status for a specific conversation.

    Returns current health metrics, concerns, and improvement recommendations.
    """
    try:
        # Retrieve cached conversation analysis
        cached_result = await intelligence_service._get_cached_analysis(conversation_id)

        if not cached_result:
            raise HTTPException(
                status_code=404,
                detail="Conversation analysis not found. Please analyze the conversation first."
            )

        # Extract health information
        key_concerns = []
        improvement_recommendations = []
        immediate_actions = []

        # Determine concerns based on health score
        if cached_result.health_score < 0.5:
            key_concerns.extend([
                "Low overall conversation health detected",
                "Significant intervention may be required"
            ])
            immediate_actions.append("Schedule supervisor consultation")

        if cached_result.objection_analysis.objection_detected:
            key_concerns.append(f"Active {cached_result.objection_analysis.objection_category} objection")
            immediate_actions.extend(cached_result.objection_analysis.handling_strategies[:2])

        # Add recommendations
        improvement_recommendations.extend(cached_result.recommended_actions[:3])

        return ConversationHealthResponse(
            conversation_id=conversation_id,
            health_status=cached_result.conversation_health,
            health_score=cached_result.health_score,
            key_concerns=key_concerns,
            improvement_recommendations=improvement_recommendations,
            immediate_actions=immediate_actions,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/real-time-insights/{agent_id}", response_model=RealTimeInsightsResponse)
async def get_real_time_insights(
    agent_id: str,
    conversation_id: Optional[str] = Query(None, description="Specific conversation ID"),
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> RealTimeInsightsResponse:
    """
    Get real-time conversation insights for an agent.

    Provides immediate insights and coaching recommendations during active conversations.
    """
    try:
        # If conversation_id provided, get specific insights
        if conversation_id:
            cached_result = await intelligence_service._get_cached_analysis(conversation_id)

            if cached_result:
                return RealTimeInsightsResponse(
                    conversation_id=conversation_id,
                    current_emotional_state=cached_result.emotional_analysis.primary_emotion,
                    conversation_stage=cached_result.flow_analysis.current_stage,
                    urgency_level=cached_result.urgency_assessment,
                    objection_alerts=[cached_result.objection_analysis.objection_type] if cached_result.objection_analysis.objection_detected else [],
                    recommended_responses=cached_result.recommended_actions[:3],
                    coaching_tips=cached_result.coaching_suggestions[:3],
                    confidence_score=cached_result.emotional_analysis.confidence_score,
                    timestamp=datetime.now()
                )

        # Return default insights if no specific conversation found
        return RealTimeInsightsResponse(
            conversation_id=conversation_id or f"agent_{agent_id}_{int(datetime.now().timestamp())}",
            current_emotional_state=EmotionalState.NEUTRAL,
            conversation_stage=ConversationStage.NEEDS_DISCOVERY,
            urgency_level=UrgencyLevel.MODERATE,
            objection_alerts=[],
            recommended_responses=["Continue with needs discovery", "Build rapport and trust"],
            coaching_tips=["Listen actively", "Ask open-ended questions", "Maintain professional demeanor"],
            confidence_score=0.75,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error getting real-time insights: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time insights failed: {str(e)}")


@router.get("/metrics/{agent_id}", response_model=ConversationMetricsResponse)
async def get_conversation_metrics(
    agent_id: str,
    days: int = Query(30, description="Number of days for metrics calculation"),
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> ConversationMetricsResponse:
    """
    Get conversation performance metrics for an agent.

    Provides analytics on conversation performance, common patterns, and success factors.
    """
    try:
        # In a full implementation, this would query a database of conversation analyses
        # For now, return mock metrics
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return ConversationMetricsResponse(
            agent_id=agent_id,
            date_range=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            total_conversations=45,
            average_health_score=0.72,
            common_objections=[
                {"type": "price", "frequency": 0.35, "success_rate": 0.78},
                {"type": "timing", "frequency": 0.28, "success_rate": 0.65},
                {"type": "property", "frequency": 0.22, "success_rate": 0.82}
            ],
            emotional_state_distribution={
                "excited": 0.15,
                "confident": 0.25,
                "neutral": 0.30,
                "anxious": 0.20,
                "skeptical": 0.10
            },
            stage_completion_rates={
                "rapport_building": 0.95,
                "needs_discovery": 0.85,
                "qualification": 0.75,
                "property_presentation": 0.65,
                "closing": 0.45
            },
            success_predictors=[
                "High decision readiness in first 10 minutes",
                "Multiple family members engaged positively",
                "Clear timeline and budget established early",
                "Minimal objections during qualification stage"
            ]
        )

    except Exception as e:
        logger.error(f"Error getting conversation metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics calculation failed: {str(e)}")


@router.post("/batch-analysis")
async def start_batch_conversation_analysis(
    background_tasks: BackgroundTasks,
    agent_id: str,
    conversation_ids: List[str],
    analysis_type: str = "comprehensive",
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> Dict[str, Any]:
    """
    Start batch analysis of multiple conversations.

    Useful for analyzing historical conversations or processing multiple conversations in parallel.
    """
    try:
        batch_id = f"batch_conv_{int(datetime.now().timestamp())}"

        logger.info(f"Starting batch conversation analysis {batch_id} for {len(conversation_ids)} conversations")

        # Start background batch processing
        background_tasks.add_task(
            _background_batch_conversation_analysis,
            intelligence_service,
            conversation_ids,
            agent_id,
            batch_id,
            analysis_type
        )

        return {
            "batch_id": batch_id,
            "status": "started",
            "total_conversations": len(conversation_ids),
            "estimated_completion_minutes": len(conversation_ids) * 0.75,  # ~45 seconds per conversation
            "message": "Batch conversation analysis started"
        }

    except Exception as e:
        logger.error(f"Error starting batch conversation analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/batch-analysis/{batch_id}/status")
async def get_batch_analysis_status(
    batch_id: str,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> Dict[str, Any]:
    """
    Get status of batch conversation analysis.

    Returns progress information and estimated completion time.
    """
    try:
        # In a full implementation, this would check Redis for batch status
        # For now, return mock status
        return {
            "batch_id": batch_id,
            "status": "processing",
            "total_conversations": 25,
            "completed": 18,
            "failed": 1,
            "in_progress": 6,
            "estimated_completion": datetime.now() + timedelta(minutes=5),
            "results_available": 18,
            "message": "Batch analysis in progress"
        }

    except Exception as e:
        logger.error(f"Error getting batch analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Batch status check failed: {str(e)}")


@router.get("/conversation/{conversation_id}", response_model=ConversationIntelligenceResult)
async def get_conversation_analysis(
    conversation_id: str,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> ConversationIntelligenceResult:
    """
    Retrieve a previously completed conversation analysis.

    Returns cached analysis results if available.
    """
    try:
        cached_result = await intelligence_service._get_cached_analysis(conversation_id)

        if not cached_result:
            raise HTTPException(
                status_code=404,
                detail="Conversation analysis not found or expired"
            )

        return cached_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.delete("/conversation/{conversation_id}")
async def delete_conversation_analysis(
    conversation_id: str,
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> Dict[str, str]:
    """
    Delete a conversation analysis and its cached results.

    Use this to remove sensitive conversation analyses from the system.
    """
    try:
        if intelligence_service.redis_client:
            await intelligence_service.redis_client.delete(f"conv_intelligence:{conversation_id}")

        return {
            "conversation_id": conversation_id,
            "status": "deleted",
            "message": "Conversation analysis deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting conversation analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/health")
async def health_check(
    intelligence_service: AdvancedConversationIntelligence = Depends(get_advanced_conversation_intelligence)
) -> Dict[str, Any]:
    """
    Health check endpoint for conversation intelligence service.

    Verifies Claude API and Redis connectivity.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "claude_api": "unknown",
                "redis": "unknown"
            },
            "capabilities": {
                "emotional_analysis": True,
                "flow_optimization": True,
                "objection_detection": True,
                "real_time_processing": True,
                "batch_analysis": True
            }
        }

        # Check Redis
        if intelligence_service.redis_client:
            try:
                await intelligence_service.redis_client.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception:
                health_status["services"]["redis"] = "unhealthy"
        else:
            health_status["services"]["redis"] = "not_configured"

        # Check Claude API
        try:
            test_response = await intelligence_service.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            health_status["services"]["claude_api"] = "healthy" if test_response else "unhealthy"
        except Exception:
            health_status["services"]["claude_api"] = "unhealthy"

        # Overall status
        if all(status in ["healthy", "not_configured"] for status in health_status["services"].values()):
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# Background task functions
async def _background_batch_conversation_analysis(
    intelligence_service: AdvancedConversationIntelligence,
    conversation_ids: List[str],
    agent_id: str,
    batch_id: str,
    analysis_type: str
):
    """Background task for batch conversation analysis."""
    try:
        results = []
        for conversation_id in conversation_ids:
            try:
                # In a real implementation, this would retrieve conversation data
                # and perform analysis
                await asyncio.sleep(0.5)  # Simulate processing time
                results.append(f"Analysis completed for {conversation_id}")

            except Exception as e:
                logger.error(f"Error analyzing conversation {conversation_id}: {e}")

        logger.info(f"Batch conversation analysis {batch_id} completed: {len(results)} conversations processed")

    except Exception as e:
        logger.error(f"Batch conversation analysis {batch_id} failed: {e}")


@router.get("/templates/analysis-prompts")
async def get_analysis_templates() -> Dict[str, str]:
    """
    Get conversation analysis prompt templates for different scenarios.

    Useful for understanding how the analysis works and for custom implementations.
    """
    try:
        return {
            "emotional_analysis": """
            Analyze the emotional state in this real estate conversation focusing on:
            1. Primary emotional state (excited, confident, neutral, anxious, etc.)
            2. Decision readiness level
            3. Stress indicators
            4. Motivation factors

            Provide specific evidence from the conversation to support your analysis.
            """,

            "objection_detection": """
            Identify and analyze any objections in this real estate conversation:
            1. Explicit objections directly stated
            2. Implicit resistance or hesitation
            3. Underlying concerns causing objections
            4. Recommended handling strategies

            Focus on both verbal and contextual cues that indicate objections.
            """,

            "flow_optimization": """
            Analyze the conversation flow and progression:
            1. Current conversation stage
            2. Readiness to advance to next stage
            3. Bottlenecks preventing progression
            4. Opportunities to accelerate the conversation

            Consider natural sales progression and prospect readiness.
            """
        }

    except Exception as e:
        logger.error(f"Error retrieving analysis templates: {e}")
        raise HTTPException(status_code=500, detail=f"Template retrieval failed: {str(e)}")