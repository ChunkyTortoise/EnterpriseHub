"""
Mobile Coaching API Endpoints (Phase 4: Mobile Optimization)

REST API endpoints for mobile-optimized Claude coaching.
Designed for touch interfaces with quick actions and battery efficiency.

Features:
- Mobile coaching session management
- Quick action suggestions
- Offline coaching support
- Battery-optimized responses
- Touch-friendly interactions
- Data usage optimization
- Performance monitoring

Performance Targets:
- Coaching response: <150ms
- Touch interaction: <3 taps for any action
- Data usage: 70% reduction vs desktop
- Battery consumption: 50% reduction
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
import time
from datetime import datetime
import json

# Local imports
from ghl_real_estate_ai.services.claude.mobile.mobile_coaching_service import (
    MobileCoachingService,
    MobileCoachingMode,
    MobileCoachingContext,
    MobileCoachingSuggestion,
    CoachingPriority,
    MobileActionType
)
from ghl_real_estate_ai.services.claude.mobile.offline_sync_service import (
    OfflineSyncService,
    DataType,
    SyncPriority
)

logger = logging.getLogger(__name__)

# Initialize services
mobile_coaching_service = MobileCoachingService()
offline_sync_service = OfflineSyncService()

# Create router
mobile_coaching_router = APIRouter(prefix="/api/v1/mobile/coaching", tags=["Mobile Coaching"])


# Request/Response Models
class StartMobileCoachingRequest(BaseModel):
    agent_id: str = Field(..., description="Agent identifier")
    mode: str = Field(default="quick_insights", description="Coaching mode")
    client_info: Dict[str, Any] = Field(default_factory=dict, description="Client information")
    property_context: Optional[Dict[str, Any]] = Field(default=None, description="Property context")
    location_context: Optional[Dict[str, Any]] = Field(default=None, description="Location context")
    device_info: Optional[Dict[str, Any]] = Field(default=None, description="Device information")
    network_status: str = Field(default="wifi", description="Network connection")
    battery_level: Optional[float] = Field(default=None, description="Battery level (0.0-1.0)")


class GetCoachingSuggestionRequest(BaseModel):
    session_id: str = Field(..., description="Mobile coaching session ID")
    conversation_context: str = Field(..., description="Current conversation context")
    client_message: str = Field(..., description="Latest client message")
    urgency_level: str = Field(default="normal", description="Response urgency")


class ExecuteQuickActionRequest(BaseModel):
    session_id: str = Field(..., description="Mobile coaching session ID")
    action_type: str = Field(..., description="Quick action type")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Action context")


class UpdateSessionModeRequest(BaseModel):
    session_id: str = Field(..., description="Mobile coaching session ID")
    new_mode: str = Field(..., description="New coaching mode")
    reason: Optional[str] = Field(default=None, description="Reason for mode change")


class MobileCoachingSessionResponse(BaseModel):
    session_id: str
    agent_id: str
    mode: str
    start_time: str
    context: Dict[str, Any]
    success: bool
    message: Optional[str] = None


class CoachingSuggestionResponse(BaseModel):
    suggestion_id: str
    priority: str
    title: str
    message: str
    suggested_response: Optional[str] = None
    quick_actions: List[str]
    timing_sensitive: bool
    confidence: float
    tap_to_action: Optional[str] = None
    expires_at: Optional[str] = None
    processing_time_ms: int
    success: bool


class QuickActionResponse(BaseModel):
    action_type: str
    icon: str
    label: str
    suggested_text: str
    templates: List[str]
    success: bool
    message: Optional[str] = None


class MobilePerformanceResponse(BaseModel):
    active_mobile_sessions: int
    average_response_time_ms: float
    claude_integration_target_ms: int
    performance_target_met: bool
    cache_hit_rate: float
    offline_mode_ready: bool


# Mobile Coaching Session Management

@mobile_coaching_router.post("/sessions/start", response_model=MobileCoachingSessionResponse)
async def start_mobile_coaching_session(request: StartMobileCoachingRequest):
    """
    Start a new mobile coaching session

    Creates an optimized coaching session for mobile devices with
    battery and data usage considerations.
    """
    try:
        start_time = time.time()

        # Validate and convert mode
        try:
            mode = MobileCoachingMode(request.mode)
        except ValueError:
            mode = MobileCoachingMode.QUICK_INSIGHTS  # Default fallback

        # Create mobile coaching context
        context = MobileCoachingContext(
            agent_id=request.agent_id,
            session_id="",  # Will be set by service
            mode=mode,
            client_info=request.client_info,
            property_context=request.property_context,
            location_context=request.location_context,
            device_info=request.device_info,
            network_status=request.network_status,
            battery_level=request.battery_level
        )

        # Start mobile coaching session
        session = await mobile_coaching_service.start_mobile_coaching_session(
            agent_id=request.agent_id,
            context=context
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Mobile coaching session started: {session.session_id} in {processing_time_ms}ms")

        return MobileCoachingSessionResponse(
            session_id=session.session_id,
            agent_id=session.agent_id,
            mode=session.mode.value,
            start_time=session.start_time.isoformat(),
            context=session.context.__dict__,
            success=True
        )

    except Exception as e:
        logger.error(f"Error starting mobile coaching session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mobile_coaching_router.get("/sessions/{session_id}/status")
async def get_mobile_coaching_session_status(session_id: str):
    """Get current status of mobile coaching session"""
    try:
        session = mobile_coaching_service.active_sessions.get(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Mobile coaching session not found")

        # Calculate session metrics
        session_duration = (datetime.now() - session.start_time).total_seconds()

        return {
            "session_id": session_id,
            "agent_id": session.agent_id,
            "mode": session.mode.value,
            "is_active": session.is_active,
            "duration_seconds": session_duration,
            "suggestions_delivered": len(session.suggestions_delivered),
            "actions_taken": len(session.actions_taken),
            "performance_metrics": session.performance_metrics,
            "context": {
                "network_status": session.context.network_status,
                "battery_level": session.context.battery_level
            },
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mobile coaching session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mobile_coaching_router.post("/sessions/{session_id}/end")
async def end_mobile_coaching_session(session_id: str):
    """End mobile coaching session and provide summary"""
    try:
        summary = await mobile_coaching_service.end_mobile_coaching_session(session_id)

        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])

        return {
            "session_summary": summary,
            "session_ended": True,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending mobile coaching session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mobile Coaching Suggestions

@mobile_coaching_router.post("/suggestions", response_model=CoachingSuggestionResponse)
async def get_mobile_coaching_suggestion(request: GetCoachingSuggestionRequest):
    """
    Get mobile-optimized coaching suggestion

    Returns coaching suggestions optimized for mobile display with
    quick actions and touch-friendly interactions.
    """
    try:
        start_time = time.time()

        # Validate session
        session = mobile_coaching_service.active_sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Mobile coaching session not found")

        # Get coaching suggestion
        suggestion = await mobile_coaching_service.get_mobile_coaching_suggestion(
            session_id=request.session_id,
            conversation_context=request.conversation_context,
            client_message=request.client_message,
            urgency_level=request.urgency_level
        )

        processing_time_ms = int((time.time() - start_time) * 1000)

        if not suggestion:
            # Return helpful fallback
            return CoachingSuggestionResponse(
                suggestion_id="fallback",
                priority="medium",
                title="Continue Discovery",
                message="Keep learning about their needs and preferences",
                suggested_response="Tell me more about what you're looking for...",
                quick_actions=["ask_qualifying_question"],
                timing_sensitive=False,
                confidence=0.5,
                processing_time_ms=processing_time_ms,
                success=True
            )

        # Queue suggestion for offline sync if needed
        if session.context.network_status in ["cellular", "offline"]:
            await offline_sync_service.queue_for_sync(
                item_id=suggestion.id,
                data_type=DataType.COACHING_SUGGESTIONS,
                action="create",
                data=suggestion.__dict__,
                priority=SyncPriority.MEDIUM
            )

        logger.info(f"Mobile coaching suggestion generated: {suggestion.title} in {processing_time_ms}ms")

        return CoachingSuggestionResponse(
            suggestion_id=suggestion.id,
            priority=suggestion.priority.value,
            title=suggestion.title,
            message=suggestion.message,
            suggested_response=suggestion.suggested_response,
            quick_actions=[action.value for action in suggestion.quick_actions],
            timing_sensitive=suggestion.timing_sensitive,
            confidence=suggestion.confidence,
            tap_to_action=suggestion.tap_to_action,
            expires_at=suggestion.expires_at.isoformat() if suggestion.expires_at else None,
            processing_time_ms=processing_time_ms,
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mobile coaching suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mobile_coaching_router.get("/suggestions/offline/{session_id}")
async def get_offline_coaching_suggestions(session_id: str, context: str = ""):
    """
    Get coaching suggestions from offline cache

    Provides coaching suggestions when offline or in battery saver mode.
    """
    try:
        # Validate session
        session = mobile_coaching_service.active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Mobile coaching session not found")

        # Get offline suggestions
        suggestions = await offline_sync_service.get_offline_coaching_suggestions(context)

        return {
            "offline_suggestions": suggestions,
            "cache_source": "essential_cache",
            "total_suggestions": len(suggestions),
            "context_analyzed": context != "",
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting offline coaching suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Quick Actions

@mobile_coaching_router.post("/quick-actions", response_model=QuickActionResponse)
async def execute_mobile_quick_action(request: ExecuteQuickActionRequest):
    """
    Execute a quick action from mobile interface

    Provides one-tap actions for common coaching scenarios.
    """
    try:
        # Validate session
        session = mobile_coaching_service.active_sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Mobile coaching session not found")

        # Validate action type
        try:
            action_type = MobileActionType(request.action_type)
        except ValueError:
            available_actions = [action.value for action in MobileActionType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action type. Available: {available_actions}"
            )

        # Execute quick action
        result = await mobile_coaching_service.execute_quick_action(
            session_id=request.session_id,
            action_type=action_type,
            context=request.context
        )

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))

        # Queue action for offline sync
        await offline_sync_service.queue_for_sync(
            item_id=f"action_{int(time.time())}",
            data_type=DataType.QUICK_ACTIONS,
            action="create",
            data=result,
            priority=SyncPriority.LOW
        )

        logger.info(f"Quick action executed: {request.action_type} in session {request.session_id}")

        return QuickActionResponse(
            action_type=result["action_type"],
            icon=result["icon"],
            label=result["label"],
            suggested_text=result["suggested_text"],
            templates=result["templates"],
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing quick action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mobile_coaching_router.get("/quick-actions/available")
async def get_available_quick_actions():
    """Get list of available quick actions for mobile interface"""
    try:
        actions = []
        for action_type in MobileActionType:
            template = mobile_coaching_service.quick_action_templates.get(action_type, {})
            actions.append({
                "action_type": action_type.value,
                "icon": template.get("icon", "📱"),
                "label": template.get("label", action_type.value.replace('_', ' ').title()),
                "description": f"Quick action for {action_type.value.replace('_', ' ')}",
                "templates_count": len(template.get("templates", []))
            })

        return {
            "available_actions": actions,
            "total_actions": len(actions),
            "mobile_optimized": True,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error getting available quick actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Session Mode Management

@mobile_coaching_router.post("/sessions/{session_id}/mode")
async def update_coaching_mode(session_id: str, request: UpdateSessionModeRequest):
    """
    Update coaching mode for mobile session

    Allows switching between different coaching modes based on
    battery level, network conditions, or user preferences.
    """
    try:
        # Validate session
        session = mobile_coaching_service.active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Mobile coaching session not found")

        # Validate new mode
        try:
            new_mode = MobileCoachingMode(request.new_mode)
        except ValueError:
            available_modes = [mode.value for mode in MobileCoachingMode]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode. Available: {available_modes}"
            )

        old_mode = session.mode
        session.mode = new_mode

        # Optimize session for new mode
        await mobile_coaching_service._optimize_for_device(session)

        logger.info(f"Session {session_id} mode updated: {old_mode.value} → {new_mode.value}")

        return {
            "session_id": session_id,
            "old_mode": old_mode.value,
            "new_mode": new_mode.value,
            "reason": request.reason,
            "optimizations_applied": True,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating coaching mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mobile_coaching_router.get("/modes/available")
async def get_available_coaching_modes():
    """Get list of available coaching modes"""
    try:
        modes = []
        for mode in MobileCoachingMode:
            description_map = {
                MobileCoachingMode.FULL_COACHING: "Complete coaching with all features",
                MobileCoachingMode.QUICK_INSIGHTS: "Essential insights only for mobile",
                MobileCoachingMode.SILENT_MONITORING: "Background analysis without notifications",
                MobileCoachingMode.BATTERY_SAVER: "Minimal processing for battery conservation",
                MobileCoachingMode.OFFLINE_MODE: "Cached responses only, no network usage"
            }

            modes.append({
                "mode": mode.value,
                "description": description_map.get(mode, "Mobile coaching mode"),
                "battery_optimized": mode in [MobileCoachingMode.BATTERY_SAVER, MobileCoachingMode.OFFLINE_MODE],
                "data_optimized": mode in [MobileCoachingMode.QUICK_INSIGHTS, MobileCoachingMode.OFFLINE_MODE]
            })

        return {
            "available_modes": modes,
            "total_modes": len(modes),
            "default_mode": MobileCoachingMode.QUICK_INSIGHTS.value,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error getting available coaching modes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Performance and Monitoring

@mobile_coaching_router.get("/performance", response_model=MobilePerformanceResponse)
async def get_mobile_coaching_performance():
    """Get mobile coaching performance metrics"""
    try:
        metrics = mobile_coaching_service.get_mobile_performance_metrics()

        return MobilePerformanceResponse(
            active_mobile_sessions=metrics["active_mobile_sessions"],
            average_response_time_ms=metrics["average_response_time_ms"],
            claude_integration_target_ms=metrics["claude_integration_target_ms"],
            performance_target_met=metrics["performance_target_met"],
            cache_hit_rate=metrics["cache_hit_rate"],
            offline_mode_ready=metrics["offline_mode_ready"]
        )

    except Exception as e:
        logger.error(f"Error getting mobile coaching performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mobile_coaching_router.get("/health")
async def mobile_coaching_health_check():
    """Health check for mobile coaching services"""
    try:
        # Check mobile coaching service
        mobile_healthy = len(mobile_coaching_service.offline_coaching_cache) > 0

        # Check offline sync service
        offline_healthy = await _check_offline_sync_health()

        return {
            "mobile_coaching": {
                "healthy": mobile_healthy,
                "active_sessions": len(mobile_coaching_service.active_sessions),
                "offline_cache_ready": mobile_healthy
            },
            "offline_sync": {
                "healthy": offline_healthy,
                "sync_queue_size": len(offline_sync_service.sync_queue),
                "is_online": offline_sync_service.is_online
            },
            "overall_health": mobile_healthy and offline_healthy,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in mobile coaching health check: {e}")
        return {
            "mobile_coaching": {"healthy": False, "error": str(e)},
            "offline_sync": {"healthy": False},
            "overall_health": False,
            "timestamp": datetime.now().isoformat()
        }


# Utility Functions

async def _check_offline_sync_health() -> bool:
    """Check offline sync service health"""
    try:
        status = offline_sync_service.get_sync_status()
        return status.get("queue_size", 0) >= 0  # Basic health check
    except:
        return False


# Background Tasks

@mobile_coaching_router.post("/sessions/{session_id}/background-sync")
async def trigger_background_sync(session_id: str, background_tasks: BackgroundTasks):
    """Trigger background synchronization for session data"""
    try:
        # Validate session
        session = mobile_coaching_service.active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Mobile coaching session not found")

        # Add background sync task
        background_tasks.add_task(_background_sync_session_data, session_id)

        return {
            "sync_triggered": True,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering background sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _background_sync_session_data(session_id: str):
    """Background task to sync session data"""
    try:
        session = mobile_coaching_service.active_sessions.get(session_id)
        if not session:
            return

        # Queue session metrics for sync
        await offline_sync_service.queue_for_sync(
            item_id=f"session_metrics_{session_id}",
            data_type=DataType.PERFORMANCE_METRICS,
            action="update",
            data=session.performance_metrics,
            priority=SyncPriority.LOW
        )

        # Queue suggestions for sync
        for suggestion in session.suggestions_delivered[-5:]:  # Last 5 suggestions
            await offline_sync_service.queue_for_sync(
                item_id=suggestion.id,
                data_type=DataType.COACHING_SUGGESTIONS,
                action="create",
                data=suggestion.__dict__,
                priority=SyncPriority.MEDIUM
            )

        logger.info(f"Background sync completed for session {session_id}")

    except Exception as e:
        logger.error(f"Error in background sync for session {session_id}: {e}")


# Development and Testing Endpoints

@mobile_coaching_router.post("/test/simulate-suggestion")
async def simulate_mobile_coaching_suggestion(
    priority: str = "medium",
    scenario: str = "general"
):
    """Simulate mobile coaching suggestion for testing"""
    try:
        # Create test suggestion based on scenario
        test_suggestions = {
            "objection": {
                "title": "Address Price Concern",
                "message": "Client mentioned price - acknowledge and provide value",
                "suggested_response": "I understand price is important. Let's look at the value this offers...",
                "priority": "critical"
            },
            "interest": {
                "title": "Build on Interest",
                "message": "Client is engaged - provide more details",
                "suggested_response": "I can see this interests you. Would you like to know more about...",
                "priority": "high"
            },
            "general": {
                "title": "Continue Discovery",
                "message": "Keep learning about their needs",
                "suggested_response": "Tell me more about what you're looking for...",
                "priority": "medium"
            }
        }

        suggestion_data = test_suggestions.get(scenario, test_suggestions["general"])

        return CoachingSuggestionResponse(
            suggestion_id=f"test_{int(time.time())}",
            priority=suggestion_data["priority"],
            title=suggestion_data["title"],
            message=suggestion_data["message"],
            suggested_response=suggestion_data["suggested_response"],
            quick_actions=["respond_to_objection", "ask_qualifying_question"],
            timing_sensitive=suggestion_data["priority"] == "critical",
            confidence=0.85,
            tap_to_action="Use Suggestion",
            processing_time_ms=25,  # Simulated fast response
            success=True
        )

    except Exception as e:
        logger.error(f"Error simulating coaching suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))