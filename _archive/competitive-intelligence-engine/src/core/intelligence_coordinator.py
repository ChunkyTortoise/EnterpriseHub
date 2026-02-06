"""
Enhanced Competitive Intelligence Engine - Intelligence Coordinator

This module coordinates intelligence processing across the three main pipelines:
- AI/ML Enhancement Pipeline
- Advanced Analytics Pipeline  
- Integration Distribution Pipeline

The coordinator ensures data flows correctly between systems and maintains
the overall intelligence state and orchestration.

Author: Claude
Date: January 2026
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .event_bus import (
    EventBus, EventHandler, EventType, EventPriority, 
    get_event_bus, publish_intelligence_insight
)


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class IntelligenceSession:
    """
    Represents a coordinated intelligence processing session.
    
    A session tracks related intelligence activities across all three
    enhancement pipelines and ensures proper coordination.
    """
    
    id: str
    correlation_id: str
    created_at: datetime
    updated_at: datetime
    status: str  # active, completed, failed
    
    # Pipeline states
    ai_ml_status: Optional[str] = None
    analytics_status: Optional[str] = None
    integration_status: Optional[str] = None
    
    # Data tracking
    competitor_ids: Set[str] = None
    prediction_results: Dict[str, Any] = None
    analytics_results: Dict[str, Any] = None
    integration_results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.competitor_ids is None:
            self.competitor_ids = set()
        if self.prediction_results is None:
            self.prediction_results = {}
        if self.analytics_results is None:
            self.analytics_results = {}
        if self.integration_results is None:
            self.integration_results = {}


class IntelligenceCoordinator(EventHandler):
    """
    Coordinates intelligence processing across all enhancement pipelines.
    
    The coordinator:
    1. Manages intelligence sessions and correlations
    2. Routes data between AI/ML, Analytics, and Integration systems
    3. Triggers cross-system workflows
    4. Maintains system state consistency
    5. Orchestrates complex multi-step intelligence operations
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        session_timeout_minutes: int = 60
    ):
        super().__init__(
            name="intelligence_coordinator",
            event_types=[
                # Core intelligence events
                EventType.INTELLIGENCE_INSIGHT_CREATED,
                EventType.COMPETITOR_ACTIVITY_DETECTED,
                EventType.THREAT_LEVEL_CHANGED,
                EventType.OPPORTUNITY_IDENTIFIED,
                
                # AI/ML pipeline events
                EventType.PREDICTION_GENERATED,
                EventType.DEEP_LEARNING_PREDICTION,
                EventType.COMPUTER_VISION_DETECTED,
                EventType.ANOMALY_DETECTED,
                
                # Analytics pipeline events
                EventType.EXECUTIVE_SUMMARY_CREATED,
                EventType.LANDSCAPE_MAPPED,
                EventType.STRATEGIC_PATTERN_IDENTIFIED,
                
                # Integration pipeline events
                EventType.CRM_SYNC_COMPLETED,
                EventType.WEBHOOK_TRIGGERED,
                EventType.SLACK_NOTIFICATION_SENT,
            ]
        )
        
        self.event_bus = event_bus or get_event_bus()
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # Session tracking
        self.active_sessions: Dict[str, IntelligenceSession] = {}
        self.correlation_to_session: Dict[str, str] = {}
        
        # Processing queues
        self.pending_ai_ml_requests: List[Dict[str, Any]] = []
        self.pending_analytics_requests: List[Dict[str, Any]] = []
        self.pending_integration_requests: List[Dict[str, Any]] = []
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("IntelligenceCoordinator initialized")
    
    async def start(self):
        """Start the intelligence coordinator."""
        await super().start()
        
        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_sessions())
        
        logger.info("IntelligenceCoordinator started")
    
    async def stop(self):
        """Stop the intelligence coordinator."""
        await super().stop()
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("IntelligenceCoordinator stopped")
    
    async def handle(self, event) -> bool:
        """Handle intelligence coordination events."""
        try:
            # Route event based on type
            if event.type == EventType.INTELLIGENCE_INSIGHT_CREATED:
                return await self._handle_intelligence_insight(event)
            elif event.type == EventType.COMPETITOR_ACTIVITY_DETECTED:
                return await self._handle_competitor_activity(event)
            elif event.type == EventType.PREDICTION_GENERATED:
                return await self._handle_prediction_result(event)
            elif event.type == EventType.EXECUTIVE_SUMMARY_CREATED:
                return await self._handle_analytics_result(event)
            elif event.type == EventType.CRM_SYNC_COMPLETED:
                return await self._handle_integration_result(event)
            else:
                return await self._handle_generic_pipeline_event(event)
                
        except Exception as e:
            logger.error(f"Error handling event {event.id}: {e}")
            return False
    
    async def start_intelligence_session(
        self,
        competitor_ids: List[str],
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Start a new coordinated intelligence session.
        
        Args:
            competitor_ids: List of competitor IDs to analyze
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            str: Session ID
        """
        session_id = str(uuid4())
        if not correlation_id:
            correlation_id = f"intel_session_{session_id[:8]}"
        
        session = IntelligenceSession(
            id=session_id,
            correlation_id=correlation_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status="active",
            competitor_ids=set(competitor_ids)
        )
        
        self.active_sessions[session_id] = session
        self.correlation_to_session[correlation_id] = session_id
        
        logger.info(
            f"Started intelligence session {session_id} for competitors: "
            f"{competitor_ids}"
        )
        
        # Trigger initial intelligence gathering
        await self._trigger_intelligence_gathering(session)
        
        return session_id
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an intelligence session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "id": session.id,
            "correlation_id": session.correlation_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "status": session.status,
            "ai_ml_status": session.ai_ml_status,
            "analytics_status": session.analytics_status,
            "integration_status": session.integration_status,
            "competitor_count": len(session.competitor_ids),
            "results_available": {
                "predictions": bool(session.prediction_results),
                "analytics": bool(session.analytics_results),
                "integrations": bool(session.integration_results)
            }
        }
    
    async def _handle_intelligence_insight(self, event) -> bool:
        """Handle a new intelligence insight."""
        try:
            correlation_id = event.correlation_id
            if not correlation_id:
                logger.warning(f"Intelligence insight {event.id} has no correlation_id")
                return True
            
            session_id = self.correlation_to_session.get(correlation_id)
            if not session_id:
                logger.debug(f"No session found for correlation {correlation_id}")
                return True
            
            session = self.active_sessions[session_id]
            session.updated_at = datetime.now(timezone.utc)
            
            # Extract insight data
            insight_data = event.data
            
            # Trigger coordinated analysis across all pipelines
            await self._coordinate_insight_analysis(session, insight_data)
            
            logger.info(f"Processed intelligence insight for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling intelligence insight: {e}")
            return False
    
    async def _handle_competitor_activity(self, event) -> bool:
        """Handle detected competitor activity."""
        try:
            # Extract competitor information
            activity_data = event.data
            competitor_id = activity_data.get("competitor_id")
            
            if not competitor_id:
                logger.warning("Competitor activity event missing competitor_id")
                return True
            
            # Find relevant sessions
            relevant_sessions = [
                session for session in self.active_sessions.values()
                if competitor_id in session.competitor_ids
            ]
            
            # Process activity for each relevant session
            for session in relevant_sessions:
                await self._process_competitor_activity(session, activity_data)
            
            logger.info(f"Processed competitor activity for {competitor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling competitor activity: {e}")
            return False
    
    async def _handle_prediction_result(self, event) -> bool:
        """Handle AI/ML prediction results."""
        try:
            correlation_id = event.correlation_id
            if correlation_id:
                session_id = self.correlation_to_session.get(correlation_id)
                if session_id:
                    session = self.active_sessions[session_id]
                    session.prediction_results.update(event.data)
                    session.ai_ml_status = "completed"
                    session.updated_at = datetime.now(timezone.utc)
                    
                    # Check if we can trigger analytics
                    await self._check_analytics_triggers(session)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling prediction result: {e}")
            return False
    
    async def _handle_analytics_result(self, event) -> bool:
        """Handle analytics pipeline results."""
        try:
            correlation_id = event.correlation_id
            if correlation_id:
                session_id = self.correlation_to_session.get(correlation_id)
                if session_id:
                    session = self.active_sessions[session_id]
                    session.analytics_results.update(event.data)
                    session.analytics_status = "completed"
                    session.updated_at = datetime.now(timezone.utc)
                    
                    # Check if we can trigger integrations
                    await self._check_integration_triggers(session)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling analytics result: {e}")
            return False
    
    async def _handle_integration_result(self, event) -> bool:
        """Handle integration pipeline results."""
        try:
            correlation_id = event.correlation_id
            if correlation_id:
                session_id = self.correlation_to_session.get(correlation_id)
                if session_id:
                    session = self.active_sessions[session_id]
                    session.integration_results.update(event.data)
                    session.integration_status = "completed"
                    session.updated_at = datetime.now(timezone.utc)
                    
                    # Check if session is complete
                    await self._check_session_completion(session)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling integration result: {e}")
            return False
    
    async def _handle_generic_pipeline_event(self, event) -> bool:
        """Handle other pipeline events."""
        try:
            # Log event for coordination tracking
            logger.debug(f"Processing pipeline event {event.type.name} from {event.source_system}")
            
            # Update relevant session status if correlation exists
            correlation_id = event.correlation_id
            if correlation_id:
                session_id = self.correlation_to_session.get(correlation_id)
                if session_id:
                    session = self.active_sessions[session_id]
                    session.updated_at = datetime.now(timezone.utc)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling generic pipeline event: {e}")
            return False
    
    async def _trigger_intelligence_gathering(self, session: IntelligenceSession):
        """Trigger intelligence gathering for a session."""
        try:
            # Trigger AI/ML pipeline
            await self.event_bus.publish(
                event_type=EventType.PREDICTION_GENERATED,
                data={
                    "competitor_ids": list(session.competitor_ids),
                    "session_id": session.id,
                    "request_type": "comprehensive_analysis"
                },
                source_system="intelligence_coordinator",
                correlation_id=session.correlation_id
            )
            
            session.ai_ml_status = "requested"
            
            logger.info(f"Triggered intelligence gathering for session {session.id}")
            
        except Exception as e:
            logger.error(f"Error triggering intelligence gathering: {e}")
    
    async def _coordinate_insight_analysis(
        self, 
        session: IntelligenceSession, 
        insight_data: Dict[str, Any]
    ):
        """Coordinate analysis of a new intelligence insight."""
        try:
            # Trigger deep learning analysis
            await self.event_bus.publish(
                event_type=EventType.DEEP_LEARNING_PREDICTION,
                data={
                    "insight_data": insight_data,
                    "competitor_ids": list(session.competitor_ids),
                    "analysis_type": "strategic_impact"
                },
                source_system="intelligence_coordinator",
                priority=EventPriority.HIGH,
                correlation_id=session.correlation_id
            )
            
            # Trigger executive analytics
            await self.event_bus.publish(
                event_type=EventType.EXECUTIVE_SUMMARY_CREATED,
                data={
                    "insight_data": insight_data,
                    "session_context": session.id
                },
                source_system="intelligence_coordinator",
                priority=EventPriority.HIGH,
                correlation_id=session.correlation_id
            )
            
            logger.info(f"Coordinated insight analysis for session {session.id}")
            
        except Exception as e:
            logger.error(f"Error coordinating insight analysis: {e}")
    
    async def _process_competitor_activity(
        self,
        session: IntelligenceSession,
        activity_data: Dict[str, Any]
    ):
        """Process competitor activity within a session."""
        try:
            # Trigger computer vision analysis if it's website activity
            if activity_data.get("activity_type") == "website_change":
                await self.event_bus.publish(
                    event_type=EventType.COMPUTER_VISION_DETECTED,
                    data=activity_data,
                    source_system="intelligence_coordinator",
                    correlation_id=session.correlation_id
                )
            
            # Trigger strategic pattern analysis
            await self.event_bus.publish(
                event_type=EventType.STRATEGIC_PATTERN_IDENTIFIED,
                data={
                    "activity_data": activity_data,
                    "session_context": session.id
                },
                source_system="intelligence_coordinator",
                correlation_id=session.correlation_id
            )
            
            logger.debug(f"Processed activity for session {session.id}")
            
        except Exception as e:
            logger.error(f"Error processing competitor activity: {e}")
    
    async def _check_analytics_triggers(self, session: IntelligenceSession):
        """Check if analytics can be triggered based on available data."""
        if session.prediction_results and session.analytics_status != "completed":
            await self.event_bus.publish(
                event_type=EventType.LANDSCAPE_MAPPED,
                data={
                    "prediction_data": session.prediction_results,
                    "competitor_ids": list(session.competitor_ids)
                },
                source_system="intelligence_coordinator",
                correlation_id=session.correlation_id
            )
            
            session.analytics_status = "triggered"
    
    async def _check_integration_triggers(self, session: IntelligenceSession):
        """Check if integrations can be triggered based on available data."""
        if (session.analytics_results and 
            session.integration_status not in ["completed", "triggered"]):
            
            await self.event_bus.publish(
                event_type=EventType.CRM_SYNC_REQUESTED,
                data={
                    "analytics_data": session.analytics_results,
                    "prediction_data": session.prediction_results
                },
                source_system="intelligence_coordinator",
                correlation_id=session.correlation_id
            )
            
            session.integration_status = "triggered"
    
    async def _check_session_completion(self, session: IntelligenceSession):
        """Check if a session is complete and can be finalized."""
        if (session.ai_ml_status == "completed" and
            session.analytics_status == "completed" and
            session.integration_status == "completed"):
            
            session.status = "completed"
            
            # Publish final intelligence summary
            await publish_intelligence_insight(
                insight_data={
                    "session_summary": {
                        "session_id": session.id,
                        "competitor_ids": list(session.competitor_ids),
                        "prediction_results": session.prediction_results,
                        "analytics_results": session.analytics_results,
                        "integration_results": session.integration_results,
                        "completion_time": session.updated_at.isoformat()
                    }
                },
                source_system="intelligence_coordinator",
                priority=EventPriority.HIGH,
                correlation_id=session.correlation_id
            )
            
            logger.info(f"Session {session.id} completed successfully")
    
    async def _cleanup_sessions(self):
        """Background task to clean up expired sessions."""
        while self.is_running:
            try:
                now = datetime.now(timezone.utc)
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if now - session.updated_at > self.session_timeout:
                        expired_sessions.append(session_id)
                
                # Clean up expired sessions
                for session_id in expired_sessions:
                    session = self.active_sessions.pop(session_id)
                    self.correlation_to_session.pop(session.correlation_id, None)
                    logger.info(f"Cleaned up expired session {session_id}")
                
                # Wait before next cleanup
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute
    
    def get_coordinator_metrics(self) -> Dict[str, Any]:
        """Get intelligence coordinator metrics."""
        active_count = len([s for s in self.active_sessions.values() if s.status == "active"])
        completed_count = len([s for s in self.active_sessions.values() if s.status == "completed"])
        
        return {
            "active_sessions": active_count,
            "completed_sessions": completed_count,
            "total_sessions": len(self.active_sessions),
            "pending_ai_ml_requests": len(self.pending_ai_ml_requests),
            "pending_analytics_requests": len(self.pending_analytics_requests),
            "pending_integration_requests": len(self.pending_integration_requests),
            "is_running": self.is_running
        }


# Global coordinator instance
_intelligence_coordinator: Optional[IntelligenceCoordinator] = None


def get_intelligence_coordinator() -> IntelligenceCoordinator:
    """Get the global intelligence coordinator instance."""
    global _intelligence_coordinator
    if _intelligence_coordinator is None:
        _intelligence_coordinator = IntelligenceCoordinator()
    return _intelligence_coordinator


# Export public API
__all__ = [
    "IntelligenceSession",
    "IntelligenceCoordinator",
    "get_intelligence_coordinator"
]