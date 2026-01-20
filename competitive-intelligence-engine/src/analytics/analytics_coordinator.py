"""
Enhanced Competitive Intelligence Engine - Analytics Coordinator

This module coordinates all analytics components and integrates them with the event bus
architecture for seamless operation within the Enhanced Competitive Intelligence Engine.

Features:
- Unified analytics orchestration
- Event-driven analytics triggering
- Cross-component data flow coordination
- Performance monitoring and optimization
- Error handling and resilience

Author: Claude
Date: January 2026
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from ..core.event_bus import (
    EventBus, EventHandler, EventType, EventPriority,
    get_event_bus, publish_intelligence_insight
)

from .executive_analytics_engine import (
    ExecutiveAnalyticsEngine, StakeholderType, CompetitiveIntelligence, 
    PredictionData, ExecutiveSummary
)
from .landscape_mapper import (
    LandscapeMapper, CompetitorProfile, MarketSegment, LandscapeAnalysis
)
from .market_share_analytics import (
    MarketShareAnalytics, MarketShareDataPoint, MarketShareAnalysis, ForecastHorizon
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AnalyticsSession:
    """Analytics processing session tracking."""
    session_id: str
    correlation_id: str
    started_at: datetime
    components_active: Set[str]
    executive_summary_completed: bool = False
    landscape_analysis_completed: bool = False
    market_share_analysis_completed: bool = False
    final_results: Dict[str, Any] = None


@dataclass 
class AnalyticsConfiguration:
    """Configuration for analytics components."""
    executive_analytics_enabled: bool = True
    landscape_mapping_enabled: bool = True
    market_share_analytics_enabled: bool = True
    
    # Executive Analytics config
    default_stakeholder: StakeholderType = StakeholderType.CEO
    claude_model: str = "claude-3-5-sonnet-20241022"
    summary_cache_minutes: int = 15
    
    # Landscape Mapping config
    min_competitors_for_clustering: int = 3
    analysis_cache_minutes: int = 30
    
    # Market Share Analytics config
    min_data_points: int = 12
    forecast_horizon: ForecastHorizon = ForecastHorizon.MEDIUM_TERM
    forecast_confidence: float = 0.95


class AnalyticsCoordinator(EventHandler):
    """
    Analytics Coordinator - Unified Analytics Orchestration
    
    This coordinator manages all analytics components and provides a unified
    interface for executive-grade competitive intelligence analytics.
    
    Key Responsibilities:
    - Coordinate analytics components lifecycle
    - Handle event-driven analytics triggering
    - Manage cross-component data dependencies
    - Optimize performance and resource usage
    - Provide unified analytics API
    """
    
    def __init__(
        self,
        config: Optional[AnalyticsConfiguration] = None,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize the Analytics Coordinator.
        
        Args:
            config: Analytics configuration
            event_bus: Event bus for coordination
        """
        super().__init__(
            name="analytics_coordinator",
            event_types=[
                # Intelligence events that trigger analytics
                EventType.INTELLIGENCE_INSIGHT_CREATED,
                EventType.COMPETITOR_ACTIVITY_DETECTED,
                EventType.PREDICTION_GENERATED,
                EventType.DEEP_LEARNING_PREDICTION,
                
                # Analytics events for coordination
                EventType.EXECUTIVE_SUMMARY_CREATED,
                EventType.LANDSCAPE_MAPPED,
                EventType.MARKET_SHARE_CALCULATED,
                EventType.STRATEGIC_PATTERN_IDENTIFIED,
            ]
        )
        
        self.config = config or AnalyticsConfiguration()
        self.event_bus = event_bus or get_event_bus()
        
        # Initialize analytics components
        self.executive_engine: Optional[ExecutiveAnalyticsEngine] = None
        self.landscape_mapper: Optional[LandscapeMapper] = None
        self.market_share_analytics: Optional[MarketShareAnalytics] = None
        
        # Session tracking
        self.active_sessions: Dict[str, AnalyticsSession] = {}
        
        # Performance metrics
        self.sessions_completed = 0
        self.analytics_triggered = 0
        self.average_session_time = 0.0
        self.error_count = 0
        
        logger.info("Analytics Coordinator initialized")
    
    async def start(self):
        """Start the analytics coordinator and all components."""
        try:
            await super().start()
            
            # Initialize analytics components based on configuration
            if self.config.executive_analytics_enabled:
                self.executive_engine = ExecutiveAnalyticsEngine(
                    claude_model=self.config.claude_model,
                    event_bus=self.event_bus,
                    cache_ttl_minutes=self.config.summary_cache_minutes
                )
                logger.info("Executive Analytics Engine initialized")
            
            if self.config.landscape_mapping_enabled:
                self.landscape_mapper = LandscapeMapper(
                    event_bus=self.event_bus,
                    analysis_cache_minutes=self.config.analysis_cache_minutes,
                    min_competitors_for_clustering=self.config.min_competitors_for_clustering
                )
                logger.info("Landscape Mapper initialized")
            
            if self.config.market_share_analytics_enabled:
                self.market_share_analytics = MarketShareAnalytics(
                    event_bus=self.event_bus,
                    min_data_points=self.config.min_data_points,
                    forecast_confidence=self.config.forecast_confidence
                )
                logger.info("Market Share Analytics initialized")
            
            logger.info("Analytics Coordinator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Analytics Coordinator: {e}")
            raise
    
    async def stop(self):
        """Stop the analytics coordinator and clean up resources."""
        try:
            # Complete any active sessions
            for session_id in list(self.active_sessions.keys()):
                await self._cleanup_session(session_id)
            
            # Reset component references
            self.executive_engine = None
            self.landscape_mapper = None
            self.market_share_analytics = None
            
            await super().stop()
            logger.info("Analytics Coordinator stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Analytics Coordinator: {e}")
    
    async def handle(self, event) -> bool:
        """Handle incoming events and trigger analytics as appropriate."""
        try:
            self.analytics_triggered += 1
            
            if event.type == EventType.INTELLIGENCE_INSIGHT_CREATED:
                await self._handle_intelligence_insight(event)
            elif event.type == EventType.COMPETITOR_ACTIVITY_DETECTED:
                await self._handle_competitor_activity(event)
            elif event.type in [EventType.PREDICTION_GENERATED, EventType.DEEP_LEARNING_PREDICTION]:
                await self._handle_prediction_event(event)
            elif event.type in [
                EventType.EXECUTIVE_SUMMARY_CREATED,
                EventType.LANDSCAPE_MAPPED,
                EventType.MARKET_SHARE_CALCULATED
            ]:
                await self._handle_analytics_completion(event)
            
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error handling event {event.type}: {e}")
            return False
    
    async def generate_comprehensive_analytics(
        self,
        intelligence_data: List[CompetitiveIntelligence],
        prediction_data: Optional[List[PredictionData]] = None,
        competitor_profiles: Optional[List[CompetitorProfile]] = None,
        market_segments: Optional[List[MarketSegment]] = None,
        market_share_data: Optional[List[MarketShareDataPoint]] = None,
        stakeholder_type: StakeholderType = StakeholderType.CEO,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analytics across all components.
        
        Args:
            intelligence_data: Competitive intelligence insights
            prediction_data: ML prediction results
            competitor_profiles: Competitor profiles for landscape analysis
            market_segments: Market segments for analysis
            market_share_data: Historical market share data
            stakeholder_type: Target stakeholder perspective
            correlation_id: Event correlation tracking
            
        Returns:
            Comprehensive analytics results
        """
        session_id = str(uuid4())
        correlation_id = correlation_id or str(uuid4())
        start_time = datetime.now()
        
        try:
            # Create analytics session
            session = AnalyticsSession(
                session_id=session_id,
                correlation_id=correlation_id,
                started_at=start_time,
                components_active=set()
            )
            
            self.active_sessions[session_id] = session
            
            # Run analytics components in parallel where possible
            tasks = []
            results = {}
            
            # Executive Analytics
            if self.executive_engine and intelligence_data:
                session.components_active.add("executive_analytics")
                executive_task = asyncio.create_task(
                    self.executive_engine.generate_executive_summary(
                        intelligence_data, prediction_data, stakeholder_type, correlation_id
                    )
                )
                tasks.append(("executive_summary", executive_task))
            
            # Landscape Mapping
            if self.landscape_mapper and competitor_profiles and market_segments:
                session.components_active.add("landscape_mapping") 
                landscape_task = asyncio.create_task(
                    self.landscape_mapper.map_competitive_positions(
                        competitor_profiles, market_segments, 12, correlation_id
                    )
                )
                tasks.append(("landscape_analysis", landscape_task))
            
            # Market Share Analytics
            if self.market_share_analytics and market_share_data:
                session.components_active.add("market_share_analytics")
                market_task = asyncio.create_task(
                    self.market_share_analytics.generate_comprehensive_analysis(
                        market_share_data, self.config.forecast_horizon, correlation_id
                    )
                )
                tasks.append(("market_share_analysis", market_task))
            
            # Execute tasks and collect results
            for task_name, task in tasks:
                try:
                    result = await task
                    results[task_name] = result
                    logger.info(f"Completed {task_name} for session {session_id}")
                    
                except Exception as e:
                    logger.error(f"Failed {task_name} in session {session_id}: {e}")
                    results[task_name] = None
            
            # Mark session components as completed
            if "executive_summary" in results:
                session.executive_summary_completed = True
            if "landscape_analysis" in results:
                session.landscape_analysis_completed = True
            if "market_share_analysis" in results:
                session.market_share_analysis_completed = True
            
            # Combine results
            combined_results = {
                "session_id": session_id,
                "correlation_id": correlation_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stakeholder_type": stakeholder_type.value,
                "components_executed": list(session.components_active),
                "executive_summary": results.get("executive_summary"),
                "landscape_analysis": results.get("landscape_analysis"),
                "market_share_analysis": results.get("market_share_analysis"),
                "session_performance": {
                    "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
                    "components_successful": len([r for r in results.values() if r is not None]),
                    "components_failed": len([r for r in results.values() if r is None])
                }
            }
            
            session.final_results = combined_results
            
            # Update performance metrics
            self.sessions_completed += 1
            session_time = (datetime.now() - start_time).total_seconds()
            self._update_average_session_time(session_time)
            
            # Publish comprehensive analytics event
            await self._publish_comprehensive_analytics_event(combined_results)
            
            logger.info(
                f"Completed comprehensive analytics session {session_id} "
                f"in {session_time:.2f} seconds"
            )
            
            return combined_results
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed comprehensive analytics session {session_id}: {e}")
            raise
        finally:
            # Clean up session
            await self._cleanup_session(session_id)
    
    async def get_analytics_status(self) -> Dict[str, Any]:
        """Get current analytics coordinator status and metrics."""
        status = {
            "coordinator_status": "running" if self.is_running else "stopped",
            "active_sessions": len(self.active_sessions),
            "components_status": {
                "executive_analytics": self.executive_engine is not None,
                "landscape_mapping": self.landscape_mapper is not None,
                "market_share_analytics": self.market_share_analytics is not None
            },
            "performance_metrics": {
                "sessions_completed": self.sessions_completed,
                "analytics_triggered": self.analytics_triggered,
                "average_session_time": self.average_session_time,
                "error_count": self.error_count,
                "error_rate": self.error_count / max(1, self.analytics_triggered)
            }
        }
        
        # Add component-specific metrics
        if self.executive_engine:
            status["executive_analytics_metrics"] = self.executive_engine.get_performance_metrics()
        
        if self.landscape_mapper:
            status["landscape_mapping_metrics"] = self.landscape_mapper.get_performance_metrics()
        
        if self.market_share_analytics:
            status["market_share_analytics_metrics"] = self.market_share_analytics.get_performance_metrics()
        
        return status
    
    async def _handle_intelligence_insight(self, event):
        """Handle intelligence insight events for analytics triggering."""
        try:
            # Extract intelligence data from event
            insight_data = event.data
            
            # Convert to CompetitiveIntelligence format if needed
            intelligence = CompetitiveIntelligence(
                competitor_id=insight_data.get("competitor_id", "unknown"),
                competitor_name=insight_data.get("competitor_name", "Unknown"),
                activity_type=insight_data.get("activity_type", "general"),
                activity_data=insight_data.get("activity_data", {}),
                timestamp=datetime.now(timezone.utc),
                confidence_score=insight_data.get("confidence_score", 0.7),
                source=event.source_system
            )
            
            # Trigger executive summary if significant insight
            if (intelligence.confidence_score > 0.8 and 
                self.executive_engine and 
                self.config.executive_analytics_enabled):
                
                try:
                    summary = await self.executive_engine.generate_executive_summary(
                        [intelligence],
                        stakeholder_type=self.config.default_stakeholder,
                        correlation_id=event.correlation_id
                    )
                    logger.info(f"Generated executive summary from insight: {summary.summary_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate executive summary from insight: {e}")
            
        except Exception as e:
            logger.error(f"Error handling intelligence insight: {e}")
    
    async def _handle_competitor_activity(self, event):
        """Handle competitor activity detection for landscape updates."""
        try:
            if not (self.landscape_mapper and self.config.landscape_mapping_enabled):
                return
            
            activity_data = event.data
            
            # If this is a significant competitive move, trigger landscape analysis
            if activity_data.get("significance_score", 0) > 0.7:
                logger.info(f"Significant competitor activity detected, considering landscape update")
                # In a full implementation, this would trigger landscape refresh
                # For now, we log the event
            
        except Exception as e:
            logger.error(f"Error handling competitor activity: {e}")
    
    async def _handle_prediction_event(self, event):
        """Handle prediction events for market share analysis."""
        try:
            if not (self.market_share_analytics and self.config.market_share_analytics_enabled):
                return
            
            prediction_data = event.data
            
            # If this is a market share prediction, integrate with analytics
            if prediction_data.get("prediction_type") == "market_share":
                logger.info("Market share prediction received, considering analytics update")
                # In a full implementation, this would update forecasting models
            
        except Exception as e:
            logger.error(f"Error handling prediction event: {e}")
    
    async def _handle_analytics_completion(self, event):
        """Handle completion of individual analytics components."""
        try:
            # Find active session for this correlation ID
            correlation_id = event.correlation_id
            if not correlation_id:
                return
            
            for session in self.active_sessions.values():
                if session.correlation_id == correlation_id:
                    # Update session completion status
                    if event.type == EventType.EXECUTIVE_SUMMARY_CREATED:
                        session.executive_summary_completed = True
                    elif event.type == EventType.LANDSCAPE_MAPPED:
                        session.landscape_analysis_completed = True
                    elif event.type == EventType.MARKET_SHARE_CALCULATED:
                        session.market_share_analysis_completed = True
                    
                    # Check if all components are complete
                    if self._is_session_complete(session):
                        await self._finalize_session(session)
                    
                    break
            
        except Exception as e:
            logger.error(f"Error handling analytics completion: {e}")
    
    def _is_session_complete(self, session: AnalyticsSession) -> bool:
        """Check if an analytics session is complete."""
        required_components = set()
        
        if "executive_analytics" in session.components_active:
            required_components.add("executive_summary_completed")
        if "landscape_mapping" in session.components_active:
            required_components.add("landscape_analysis_completed") 
        if "market_share_analytics" in session.components_active:
            required_components.add("market_share_analysis_completed")
        
        completed_components = set()
        if session.executive_summary_completed:
            completed_components.add("executive_summary_completed")
        if session.landscape_analysis_completed:
            completed_components.add("landscape_analysis_completed")
        if session.market_share_analysis_completed:
            completed_components.add("market_share_analysis_completed")
        
        return required_components.issubset(completed_components)
    
    async def _finalize_session(self, session: AnalyticsSession):
        """Finalize a completed analytics session."""
        try:
            logger.info(f"Finalizing analytics session {session.session_id}")
            
            # Publish session completion event
            await self.event_bus.publish(
                event_type=EventType.DASHBOARD_UPDATED,
                data={
                    "session_id": session.session_id,
                    "correlation_id": session.correlation_id,
                    "components_completed": list(session.components_active),
                    "execution_time": (datetime.now() - session.started_at).total_seconds(),
                    "finalized_at": datetime.now(timezone.utc).isoformat()
                },
                source_system="analytics_coordinator",
                priority=EventPriority.MEDIUM,
                correlation_id=session.correlation_id
            )
            
        except Exception as e:
            logger.error(f"Error finalizing session {session.session_id}: {e}")
    
    async def _cleanup_session(self, session_id: str):
        """Clean up an analytics session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.debug(f"Cleaned up analytics session {session_id}")
    
    def _update_average_session_time(self, session_time: float):
        """Update average session time metric."""
        if self.average_session_time == 0:
            self.average_session_time = session_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.average_session_time = (
                alpha * session_time + 
                (1 - alpha) * self.average_session_time
            )
    
    async def _publish_comprehensive_analytics_event(self, results: Dict[str, Any]):
        """Publish comprehensive analytics completion event."""
        try:
            await self.event_bus.publish(
                event_type=EventType.DASHBOARD_UPDATED,
                data={
                    "analytics_type": "comprehensive",
                    "session_id": results["session_id"],
                    "correlation_id": results["correlation_id"],
                    "stakeholder_type": results["stakeholder_type"],
                    "components_executed": results["components_executed"],
                    "execution_time": results["session_performance"]["execution_time_seconds"],
                    "success_rate": results["session_performance"]["components_successful"] / 
                                   (results["session_performance"]["components_successful"] + 
                                    results["session_performance"]["components_failed"]),
                    "generated_at": results["generated_at"]
                },
                source_system="analytics_coordinator",
                priority=EventPriority.HIGH,
                correlation_id=results["correlation_id"]
            )
            
        except Exception as e:
            logger.error(f"Failed to publish comprehensive analytics event: {e}")


# Export public API
__all__ = [
    "AnalyticsCoordinator",
    "AnalyticsConfiguration",
    "AnalyticsSession"
]