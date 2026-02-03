"""
Phase 2 Intelligence Layer API Routes
Advanced Property Matching, Conversation Intelligence, and Client Preference Learning

Performance Targets:
- Property Matching: <100ms with caching
- Conversation Analysis: <500ms processing
- Preference Learning: <50ms updates
- Real-time Events: <10ms latency

Integration Points:
- Advanced Property Matching Engine (Phase 2.2)
- Conversation Intelligence Service (Phase 2.3)
- Client Preference Learning Engine (Phase 2.4)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Query, Path, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from ghl_real_estate_ai.api.deps import get_current_user, get_location_access
from ghl_real_estate_ai.services.advanced_property_matching_engine import get_advanced_property_matching_engine
from ghl_real_estate_ai.services.conversation_intelligence_service import get_conversation_intelligence_service
from ghl_real_estate_ai.services.client_preference_learning_engine import get_client_preference_learning_engine
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.jorge_config import get_jorge_config

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/phase2-intelligence",
    tags=["phase2-intelligence"],
    responses={404: {"description": "Not found"}}
)

# =====================================================================================
# Request/Response Models for Phase 2 Intelligence APIs
# =====================================================================================

class PropertyMatchRequest(BaseModel):
    """Request model for property matching analysis."""
    lead_id: str = Field(..., description="Lead ID for matching")
    preferences: Dict[str, Any] = Field(..., description="Lead preferences")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Recent conversations")
    max_results: int = Field(10, ge=1, le=50, description="Maximum matches to return")
    min_score: float = Field(0.6, ge=0.0, le=1.0, description="Minimum match score threshold")


class ConversationAnalysisRequest(BaseModel):
    """Request model for conversation intelligence analysis."""
    conversation_id: str = Field(..., description="Conversation ID")
    lead_id: str = Field(..., description="Lead ID")
    conversation_history: List[Dict[str, Any]] = Field(..., description="Conversation messages")
    enable_preference_learning: bool = Field(True, description="Enable background preference learning")


class PreferenceLearningRequest(BaseModel):
    """Request model for preference learning analysis."""
    client_id: str = Field(..., description="Client ID")
    source_type: str = Field(..., description="Learning source: conversation, property_interaction")
    conversation_data: Optional[List[Dict[str, Any]]] = Field(None, description="Conversation data")
    conversation_analysis: Optional[Dict[str, Any]] = Field(None, description="Conversation analysis results")
    property_id: Optional[str] = Field(None, description="Property ID for interaction learning")
    interaction_data: Optional[Dict[str, Any]] = Field(None, description="Property interaction data")


class CrossTrackHandoffRequest(BaseModel):
    """Request model for cross-track handoff coordination."""
    lead_id: str = Field(..., description="Lead ID transitioning")
    client_id: str = Field(..., description="Client ID after transition")
    qualification_score: float = Field(..., ge=0.0, le=1.0, description="Lead qualification score")
    handoff_reason: str = Field(..., description="Reason for handoff")
    agent_notes: Optional[str] = Field(None, description="Agent transition notes")


# =====================================================================================
# Phase 2.2: Advanced Property Matching Endpoints
# =====================================================================================

@router.post("/{location_id}/property-matching/analyze")
async def analyze_property_matches(
    location_id: str = Path(..., description="GHL Location ID"),
    request: PropertyMatchRequest = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access),
    force_refresh: bool = Query(False, description="Force cache refresh for analysis")
) -> Dict[str, Any]:
    """
    Advanced behavioral property matching with ML-enhanced scoring.

    **Performance Target**: <100ms with caching
    **Features**:
    - Behavioral weight adaptation based on conversation history
    - Engagement prediction scoring
    - Presentation strategy recommendations
    - Real-time cache optimization

    **Use Cases**:
    - Real-time property recommendations during conversations
    - Automated lead nurturing with relevant properties
    - Agent coaching with match reasoning
    """
    try:
        start_time = datetime.now()
        matching_engine = get_advanced_property_matching_engine()

        # Enhanced property matching with behavioral analysis
        matches = await matching_engine.find_behavioral_matches(
            lead_id=request.lead_id,
            location_id=location_id,
            preferences=request.preferences,
            conversation_history=request.conversation_history,
            max_results=request.max_results,
            min_score=request.min_score,
            force_refresh=force_refresh
        )

        # Get behavioral insights for transparency
        behavioral_weights = await matching_engine.get_behavioral_weights(
            lead_id=request.lead_id,
            location_id=location_id,
            conversation_history=request.conversation_history
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Publish matching event for analytics
        event_publisher = get_event_publisher()
        await event_publisher.publish_property_match_generated(
            lead_id=request.lead_id,
            location_id=location_id,
            property_id=matches[0].property_id if matches else "none",
            match_score=matches[0].overall_score if matches else 0.0,
            behavioral_fit=matches[0].behavioral_fit if matches else 0.0,
            engagement_prediction=matches[0].engagement_prediction if matches else 0.0,
            rank=1,
            presentation_strategy=matches[0].presentation_strategy if matches else "standard",
            reasoning=matches[0].match_reasoning if matches else "no_matches_found",
            user_id=current_user.get("user_id")
        )

        logger.info(
            "property_matching_completed",
            location_id=location_id,
            lead_id=request.lead_id,
            matches_found=len(matches),
            processing_time_ms=processing_time_ms,
            user_id=current_user.get("user_id")
        )

        return {
            "matches": matches,
            "total_found": len(matches),
            "behavioral_weights": behavioral_weights,
            "processing_time_ms": processing_time_ms,
            "cache_used": not force_refresh and processing_time_ms < 50,
            "analysis_timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(
            "property_matching_failed",
            location_id=location_id,
            lead_id=request.lead_id,
            error=str(e),
            user_id=current_user.get("user_id")
        )
        raise HTTPException(
            status_code=500,
            detail=f"Property matching analysis failed: {str(e)}"
        )


@router.get("/{location_id}/property-matching/{lead_id}/behavioral-weights")
async def get_behavioral_matching_weights(
    location_id: str = Path(..., description="GHL Location ID"),
    lead_id: str = Path(..., description="Lead ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access),
    include_conversation_history: bool = Query(True, description="Include conversation analysis")
) -> Dict[str, Any]:
    """
    Get current behavioral matching weights for lead.

    **Performance Target**: <50ms retrieval
    **Use Cases**:
    - Understanding matching algorithm decisions
    - Agent coaching on lead preferences
    - Debugging match quality issues
    """
    try:
        matching_engine = get_advanced_property_matching_engine()

        conversation_history = None
        if include_conversation_history:
            # Get recent conversation data for context
            conversation_service = get_conversation_intelligence_service()
            recent_insights = await conversation_service.get_conversation_insights(
                lead_id=lead_id,
                location_id=location_id,
                limit=5
            )
            conversation_history = [insight.conversation_data for insight in recent_insights if hasattr(insight, 'conversation_data')]

        weights = await matching_engine.get_behavioral_weights(
            lead_id=lead_id,
            location_id=location_id,
            conversation_history=conversation_history
        )

        return {"behavioral_weights": weights, "lead_id": lead_id, "location_id": location_id}

    except Exception as e:
        logger.error(
            "behavioral_weights_retrieval_failed",
            location_id=location_id,
            lead_id=lead_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve behavioral weights: {str(e)}"
        )


@router.put("/{location_id}/property-matching/{lead_id}/feedback")
async def record_matching_feedback(
    location_id: str = Path(..., description="GHL Location ID"),
    lead_id: str = Path(..., description="Lead ID"),
    property_id: str = Query(..., description="Property ID that received feedback"),
    feedback_type: str = Query(..., description="Feedback type: viewed, liked, disliked, inquired"),
    engagement_score: Optional[float] = Query(None, description="Engagement score 0.0-1.0"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access)
) -> Dict[str, Any]:
    """
    Record lead feedback on property matches for algorithm learning.

    **Performance Target**: <100ms processing
    **Use Cases**:
    - Improving future match quality
    - Training behavioral prediction models
    - Personalizing property recommendations
    """
    try:
        matching_engine = get_advanced_property_matching_engine()

        # Process feedback for algorithm improvement
        improvement_data = await matching_engine.process_matching_feedback(
            lead_id=lead_id,
            location_id=location_id,
            property_id=property_id,
            feedback_type=feedback_type,
            engagement_score=engagement_score
        )

        # Publish feedback event for learning
        event_publisher = get_event_publisher()
        await event_publisher.publish_behavioral_match_improvement(
            lead_id=lead_id,
            location_id=location_id,
            property_id=property_id,
            feedback_type=feedback_type,
            previous_score=improvement_data.get("previous_score", 0.0),
            new_score=improvement_data.get("new_score", 0.0),
            learning_impact=improvement_data.get("learning_impact", 0.0),
            user_id=current_user.get("user_id")
        )

        return {
            "status": "feedback_recorded",
            "lead_id": lead_id,
            "property_id": property_id,
            "improvement_impact": improvement_data.get("learning_impact", 0.0),
            "next_matches_updated": improvement_data.get("cache_updated", False)
        }

    except Exception as e:
        logger.error(
            "matching_feedback_failed",
            location_id=location_id,
            lead_id=lead_id,
            property_id=property_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record matching feedback: {str(e)}"
        )


# =====================================================================================
# Phase 2.3: Conversation Intelligence Endpoints
# =====================================================================================

@router.post("/{location_id}/conversation-intelligence/analyze")
async def analyze_conversation(
    location_id: str = Path(..., description="GHL Location ID"),
    request: ConversationAnalysisRequest = ...,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access),
    force_refresh: bool = Query(False, description="Force re-analysis")
) -> Dict[str, Any]:
    """
    Real-time conversation intelligence with objection detection and coaching opportunities.

    **Performance Target**: <500ms processing
    **Features**:
    - Real-time sentiment analysis with timeline tracking
    - 8-category objection detection with response recommendations
    - Coaching opportunity identification for agent improvement
    - Engagement and rapport scoring for next-step recommendations

    **Use Cases**:
    - Live conversation coaching during calls
    - Post-call analysis and improvement recommendations
    - Manager coaching workflow integration
    """
    try:
        start_time = datetime.now()
        conversation_service = get_conversation_intelligence_service()

        # Comprehensive conversation analysis
        insights = await conversation_service.analyze_conversation_with_insights(
            conversation_id=request.conversation_id,
            lead_id=request.lead_id,
            location_id=location_id,
            conversation_history=request.conversation_history,
            force_refresh=force_refresh
        )

        # Detect objections and generate responses
        objections = await conversation_service.detect_objections_and_recommend_responses(
            conversation_id=request.conversation_id,
            location_id=location_id,
            conversation_history=request.conversation_history
        )

        # Identify coaching opportunities
        coaching_opportunities = await conversation_service.identify_coaching_opportunities(
            conversation_id=request.conversation_id,
            lead_id=request.lead_id,
            location_id=location_id,
            conversation_history=request.conversation_history,
            agent_user_id=current_user.get("user_id")
        )

        # Get sentiment timeline for detailed analysis
        sentiment_timeline = await conversation_service.track_sentiment_timeline(
            conversation_id=request.conversation_id,
            location_id=location_id,
            conversation_history=request.conversation_history
        )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Publish analysis event
        event_publisher = get_event_publisher()
        await event_publisher.publish_conversation_insight_generated(
            conversation_id=request.conversation_id,
            lead_id=request.lead_id,
            location_id=location_id,
            engagement_score=insights.overall_engagement_score,
            objection_count=len(objections),
            coaching_opportunities_count=len(coaching_opportunities),
            analysis_type="real_time",
            processing_duration_ms=processing_time_ms,
            user_id=current_user.get("user_id")
        )

        # Schedule background preference learning if enabled
        if request.enable_preference_learning:
            background_tasks.add_task(
                _update_preferences_from_conversation,
                request.lead_id,
                location_id,
                request.conversation_history,
                insights
            )

        logger.info(
            "conversation_analysis_completed",
            conversation_id=request.conversation_id,
            lead_id=request.lead_id,
            location_id=location_id,
            processing_time_ms=processing_time_ms,
            objections_found=len(objections),
            coaching_opportunities=len(coaching_opportunities),
            user_id=current_user.get("user_id")
        )

        return {
            "insights": insights,
            "objections": objections,
            "coaching_opportunities": coaching_opportunities,
            "sentiment_timeline": sentiment_timeline,
            "processing_time_ms": processing_time_ms,
            "analysis_timestamp": datetime.now(),
            "recommendations": _generate_next_step_recommendations(insights, objections)
        }

    except Exception as e:
        logger.error(
            "conversation_analysis_failed",
            conversation_id=request.conversation_id,
            lead_id=request.lead_id,
            location_id=location_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Conversation analysis failed: {str(e)}"
        )


@router.get("/{location_id}/conversation-intelligence/{conversation_id}/insights")
async def get_conversation_insights(
    location_id: str = Path(..., description="GHL Location ID"),
    conversation_id: str = Path(..., description="Conversation ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access),
    include_timeline: bool = Query(True, description="Include sentiment timeline"),
    include_objections: bool = Query(True, description="Include objection analysis")
) -> Dict[str, Any]:
    """
    Retrieve cached conversation insights with optional detailed analysis.

    **Performance Target**: <100ms retrieval
    **Use Cases**:
    - Dashboard display of conversation metrics
    - Historical conversation analysis
    - Manager review workflows
    """
    try:
        conversation_service = get_conversation_intelligence_service()

        # Get core insights
        insights = await conversation_service.get_conversation_insights(
            conversation_id=conversation_id,
            location_id=location_id
        )

        response_data = {
            "insights": insights[0] if insights else None,
            "conversation_id": conversation_id,
            "location_id": location_id
        }

        # Add optional detailed data
        if include_timeline and insights:
            timeline = await conversation_service.get_sentiment_timeline(
                conversation_id=conversation_id,
                location_id=location_id
            )
            response_data["sentiment_timeline"] = timeline

        if include_objections and insights:
            objections = await conversation_service.get_objection_detections(
                conversation_id=conversation_id,
                location_id=location_id
            )
            response_data["objections"] = objections

        return response_data

    except Exception as e:
        logger.error(
            "conversation_insights_retrieval_failed",
            conversation_id=conversation_id,
            location_id=location_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation insights: {str(e)}"
        )


@router.get("/{location_id}/conversation-intelligence/coaching-opportunities")
async def get_coaching_opportunities(
    location_id: str = Path(..., description="GHL Location ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access),
    agent_user_id: Optional[str] = Query(None, description="Filter by agent ID"),
    priority_level: Optional[int] = Query(None, ge=1, le=5, description="Filter by priority level"),
    status: Optional[str] = Query("identified", description="Coaching opportunity status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
) -> Dict[str, Any]:
    """
    Get coaching opportunities for agents with filtering.

    **Performance Target**: <200ms retrieval
    **Use Cases**:
    - Manager coaching dashboard
    - Agent performance review
    - Training needs identification
    """
    try:
        conversation_service = get_conversation_intelligence_service()

        opportunities = await conversation_service.get_coaching_opportunities(
            location_id=location_id,
            agent_user_id=agent_user_id,
            priority_level=priority_level,
            status=status,
            limit=limit
        )

        return {"coaching_opportunities": opportunities, "total_found": len(opportunities)}

    except Exception as e:
        logger.error(
            "coaching_opportunities_retrieval_failed",
            location_id=location_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve coaching opportunities: {str(e)}"
        )


# =====================================================================================
# Phase 2.4: Client Preference Learning Endpoints
# =====================================================================================

@router.post("/{location_id}/preference-learning/analyze")
async def analyze_preferences_from_conversation(
    location_id: str = Path(..., description="GHL Location ID"),
    request: PreferenceLearningRequest = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access)
) -> Dict[str, Any]:
    """
    Learn and update client preferences from conversation or interaction data.

    **Performance Target**: <50ms updates
    **Features**:
    - Multi-modal learning from conversations, property interactions, behavior
    - Confidence-weighted preference updates with drift detection
    - Automatic preference conflict resolution
    - Real-time profile completeness tracking

    **Use Cases**:
    - Automated preference learning during conversations
    - Property interaction behavior analysis
    - Preference evolution tracking over time
    """
    try:
        start_time = datetime.now()
        learning_engine = get_client_preference_learning_engine()

        # Learn preferences based on input type
        if request.source_type == "conversation":
            profile = await learning_engine.learn_from_conversation(
                client_id=request.client_id,
                location_id=location_id,
                conversation_data=request.conversation_data,
                conversation_analysis=request.conversation_analysis
            )
        elif request.source_type == "property_interaction":
            profile = await learning_engine.learn_from_property_interaction(
                client_id=request.client_id,
                location_id=location_id,
                property_id=request.property_id,
                interaction_data=request.interaction_data
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported source type: {request.source_type}"
            )

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Publish learning event
        event_publisher = get_event_publisher()
        await event_publisher.publish_preference_learning_update(
            client_id=request.client_id,
            location_id=location_id,
            source_type=request.source_type,
            preferences_learned=len(request.conversation_data) if request.conversation_data else 1,
            confidence_improvement=profile.overall_confidence_score,
            profile_completeness=profile.profile_completeness_percentage,
            user_id=current_user.get("user_id")
        )

        logger.info(
            "preference_learning_completed",
            client_id=request.client_id,
            location_id=location_id,
            source_type=request.source_type,
            processing_time_ms=processing_time_ms,
            new_confidence=profile.overall_confidence_score,
            completeness=profile.profile_completeness_percentage
        )

        return {"profile": profile, "processing_time_ms": processing_time_ms}

    except Exception as e:
        logger.error(
            "preference_learning_failed",
            client_id=request.client_id,
            location_id=location_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Preference learning failed: {str(e)}"
        )


@router.get("/{location_id}/preference-learning/{client_id}/profile")
async def get_client_preference_profile(
    location_id: str = Path(..., description="GHL Location ID"),
    client_id: str = Path(..., description="Client ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access),
    include_confidence_history: bool = Query(False, description="Include confidence evolution"),
    include_learning_events: bool = Query(False, description="Include recent learning events")
) -> Dict[str, Any]:
    """
    Get comprehensive client preference profile with optional history.

    **Performance Target**: <100ms retrieval
    **Use Cases**:
    - Agent preparation before client meetings
    - Property matching algorithm inputs
    - Preference evolution analysis
    """
    try:
        learning_engine = get_client_preference_learning_engine()

        # Get core preference profile
        profile = await learning_engine.get_preference_profile(
            client_id=client_id,
            location_id=location_id
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Preference profile not found for client {client_id}"
            )

        response_data = {
            "profile": profile,
            "client_id": client_id,
            "location_id": location_id
        }

        # Add optional historical data
        if include_confidence_history:
            history = await learning_engine.get_confidence_history(
                client_id=client_id,
                location_id=location_id,
                limit=20
            )
            response_data["confidence_history"] = history

        if include_learning_events:
            events = await learning_engine.get_recent_learning_events(
                client_id=client_id,
                location_id=location_id,
                limit=10
            )
            response_data["recent_learning_events"] = events

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "preference_profile_retrieval_failed",
            client_id=client_id,
            location_id=location_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve preference profile: {str(e)}"
        )


@router.post("/{location_id}/preference-learning/{client_id}/predict-match")
async def predict_preference_match(
    location_id: str = Path(..., description="GHL Location ID"),
    client_id: str = Path(..., description="Client ID"),
    property_data: Dict[str, Any] = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access)
) -> Dict[str, Any]:
    """
    Predict how well a property matches client preferences.

    **Performance Target**: <100ms prediction
    **Use Cases**:
    - Property recommendation scoring
    - Agent preparation for property showings
    - Automated property filtering
    """
    try:
        learning_engine = get_client_preference_learning_engine()

        # Get prediction with confidence and reasoning
        match_prediction = await learning_engine.predict_preference_match(
            client_id=client_id,
            location_id=location_id,
            property_data=property_data
        )

        return match_prediction

    except Exception as e:
        logger.error(
            "preference_match_prediction_failed",
            client_id=client_id,
            location_id=location_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Preference match prediction failed: {str(e)}"
        )


# =====================================================================================
# Cross-Track Coordination Endpoints
# =====================================================================================

@router.post("/{location_id}/coordination/lead-to-client-handoff")
async def coordinate_lead_to_client_handoff(
    location_id: str = Path(..., description="GHL Location ID"),
    request: CrossTrackHandoffRequest = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access)
) -> Dict[str, Any]:
    """
    Coordinate transition from lead intelligence to client experience tracking.

    **Performance Target**: <200ms handoff
    **Features**:
    - Context preservation across tracks
    - Preference migration to client experience
    - Conversation insights handoff
    - Timeline and milestone initialization

    **Use Cases**:
    - Lead qualification to client onboarding
    - Bot ecosystem handoff coordination
    - Context continuity preservation
    """
    try:
        start_time = datetime.now()

        # Initialize services for handoff
        conversation_service = get_conversation_intelligence_service()
        learning_engine = get_client_preference_learning_engine()
        event_publisher = get_event_publisher()

        # Gather context from lead intelligence track
        conversation_insights = await conversation_service.get_conversation_insights(
            lead_id=request.lead_id,
            location_id=location_id,
            limit=10
        )

        # Get current preference profile
        preference_profile = await learning_engine.get_preference_profile(
            client_id=request.client_id,
            location_id=location_id
        )

        # Create transition context
        transition_context = {
            "lead_id": request.lead_id,
            "client_id": request.client_id,
            "qualification_score": request.qualification_score,
            "conversation_history": conversation_insights,
            "preference_snapshot": preference_profile,
            "handoff_timestamp": datetime.now(),
            "handoff_reason": request.handoff_reason,
            "agent_notes": request.agent_notes
        }

        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Publish cross-track handoff event
        await event_publisher.publish_cross_track_handoff(
            lead_id=request.lead_id,
            client_id=request.client_id,
            location_id=location_id,
            from_track="lead_intelligence",
            to_track="client_experience",
            context_data=transition_context,
            user_id=current_user.get("user_id")
        )

        logger.info(
            "cross_track_handoff_completed",
            lead_id=request.lead_id,
            client_id=request.client_id,
            location_id=location_id,
            processing_time_ms=processing_time_ms,
            qualification_score=request.qualification_score
        )

        return {
            "transition_id": str(uuid4()),
            "lead_id": request.lead_id,
            "client_id": request.client_id,
            "location_id": location_id,
            "transition_timestamp": datetime.now(),
            "context_preserved": True,
            "preferences_migrated": preference_profile is not None,
            "conversation_insights_count": len(conversation_insights),
            "processing_time_ms": processing_time_ms,
            "next_steps": _generate_client_experience_next_steps(transition_context)
        }

    except Exception as e:
        logger.error(
            "cross_track_handoff_failed",
            lead_id=request.lead_id,
            client_id=request.client_id,
            location_id=location_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Cross-track handoff failed: {str(e)}"
        )


# =====================================================================================
# Health Check and Performance Monitoring
# =====================================================================================

@router.get("/{location_id}/health")
async def get_phase2_intelligence_health(
    location_id: str = Path(..., description="GHL Location ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    location_access: bool = Depends(get_location_access)
) -> Dict[str, Any]:
    """
    Get health status and performance metrics for Phase 2 intelligence services.

    **Performance Target**: <100ms health check
    **Metrics**:
    - Service availability and response times
    - Cache hit rates and performance
    - Processing queue status
    - Error rates and patterns
    """
    try:
        # Check service health
        services_health = {}

        # Property matching health
        matching_engine = get_advanced_property_matching_engine()
        matching_health = await matching_engine.get_health_status()
        services_health["property_matching"] = matching_health

        # Conversation intelligence health
        conversation_service = get_conversation_intelligence_service()
        conversation_health = await conversation_service.get_health_status()
        services_health["conversation_intelligence"] = conversation_health

        # Preference learning health
        learning_engine = get_client_preference_learning_engine()
        learning_health = await learning_engine.get_health_status()
        services_health["preference_learning"] = learning_health

        # Overall health assessment
        all_healthy = all(
            health.get("status") == "healthy"
            for health in services_health.values()
        )

        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "location_id": location_id,
            "services": services_health,
            "timestamp": datetime.now(),
            "performance_targets": {
                "property_matching_ms": 100,
                "conversation_analysis_ms": 500,
                "preference_learning_ms": 50
            }
        }

    except Exception as e:
        logger.error(
            "health_check_failed",
            location_id=location_id,
            error=str(e)
        )
        return {
            "overall_status": "error",
            "location_id": location_id,
            "error": str(e),
            "timestamp": datetime.now()
        }


# =====================================================================================
# Helper Functions
# =====================================================================================

async def _update_preferences_from_conversation(
    lead_id: str,
    location_id: str,
    conversation_history: List[Dict[str, Any]],
    insights: Dict[str, Any]
) -> None:
    """Background task to update preferences based on conversation analysis."""
    try:
        learning_engine = get_client_preference_learning_engine()
        await learning_engine.learn_from_conversation(
            client_id=lead_id,  # Using lead_id as client_id for preference learning
            location_id=location_id,
            conversation_data=conversation_history,
            conversation_analysis=insights
        )
    except Exception as e:
        logger.error(
            "background_preference_learning_failed",
            lead_id=lead_id,
            location_id=location_id,
            error=str(e)
        )


def _generate_next_step_recommendations(
    insights: Dict[str, Any],
    objections: List[Dict[str, Any]]
) -> List[str]:
    """Generate next-step recommendations based on conversation analysis."""
    recommendations = []

    overall_engagement = insights.get("overall_engagement_score", 0.0)
    next_step_clarity = insights.get("next_step_clarity_score", 0.0)
    rapport_quality = insights.get("rapport_quality_score", 0.0)

    # High engagement recommendations
    if overall_engagement >= 0.7:
        recommendations.append("Schedule property viewing within 24-48 hours")
        if next_step_clarity < 0.6:
            recommendations.append("Clarify specific next steps and timeline")

    # Address unresolved objections
    unresolved_objections = [obj for obj in objections if not obj.get("objection_resolved", False)]
    if unresolved_objections:
        recommendations.append(f"Address {len(unresolved_objections)} unresolved objections before proceeding")

    # Rapport building for low scores
    if rapport_quality < 0.5:
        recommendations.append("Focus on relationship building and trust establishment")

    return recommendations[:5]  # Limit to top 5 recommendations


def _generate_client_experience_next_steps(transition_context: Dict[str, Any]) -> List[str]:
    """Generate next steps for client experience track after handoff."""
    next_steps = []

    qualification_score = transition_context.get("qualification_score", 0.0)

    if qualification_score >= 0.8:
        next_steps.append("Initialize pre-approved client journey with expedited timeline")
        next_steps.append("Schedule comprehensive needs assessment within 24 hours")
    elif qualification_score >= 0.6:
        next_steps.append("Standard client onboarding with verification steps")
        next_steps.append("Property preferences confirmation and refinement")
    else:
        next_steps.append("Enhanced qualification and needs discovery required")
        next_steps.append("Additional conversation intelligence gathering recommended")

    next_steps.append("Set up automated milestone tracking and progress notifications")
    next_steps.append("Initialize personalized property alert system")

    return next_steps