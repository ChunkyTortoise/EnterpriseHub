"""
Dashboard Orchestrator - Unified Intelligence Coordination

Orchestrates all dashboard components for seamless lead intelligence experience:
- Coordinates between dashboard components and real-time data
- Manages user sessions and preferences
- Handles data synchronization and caching
- Provides unified API for dashboard operations
- Manages performance optimization and analytics

This service acts as the central coordination layer for the unified intelligence dashboard.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Import real-time connector
from .realtime_intelligence_connector import get_realtime_connector, RealTimeIntelligenceConnector

# Import dashboard models
try:
    from ..streamlit_components.advanced_intelligence_visualizations import (
        LeadJourneyStage,
        SentimentAnalysis,
        CompetitiveIntelligence,
        ContentRecommendation
    )
    DASHBOARD_MODELS_AVAILABLE = True
except ImportError:
    DASHBOARD_MODELS_AVAILABLE = False

# Import service registry
try:
    from .service_registry import ServiceRegistry
    SERVICE_REGISTRY_AVAILABLE = True
except ImportError:
    SERVICE_REGISTRY_AVAILABLE = False


class DashboardMode(Enum):
    """Dashboard operation modes."""
    OVERVIEW = "overview"
    REAL_TIME_COACHING = "real_time_coaching"
    LEAD_JOURNEY = "lead_journey"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    COMPETITIVE_INTEL = "competitive_intel"
    CONTENT_ENGINE = "content_engine"
    PERFORMANCE_ANALYTICS = "performance_analytics"
    UNIFIED_VIEW = "unified_view"


class DataSyncStatus(Enum):
    """Data synchronization status."""
    SYNCED = "synced"
    SYNCING = "syncing"
    OUT_OF_SYNC = "out_of_sync"
    ERROR = "error"


@dataclass
class DashboardSession:
    """Dashboard user session data."""
    session_id: str
    agent_id: str
    location_id: str
    active_lead_id: Optional[str]
    dashboard_mode: DashboardMode
    preferences: Dict[str, Any]
    last_activity: datetime
    real_time_enabled: bool
    filters: Dict[str, Any]
    performance_metrics: Dict[str, float]


@dataclass
class IntelligenceSnapshot:
    """Complete intelligence data snapshot for a lead."""
    lead_id: str
    timestamp: datetime
    coaching_data: Optional[Dict[str, Any]]
    sentiment_data: Optional[List[SentimentAnalysis]]
    journey_data: Optional[List[LeadJourneyStage]]
    content_recommendations: Optional[List[ContentRecommendation]]
    competitive_data: Optional[CompetitiveIntelligence]
    sync_status: DataSyncStatus
    confidence_score: float


class DashboardOrchestrator:
    """
    Central orchestrator for unified intelligence dashboard.

    Manages all aspects of dashboard operation including data coordination,
    user sessions, performance optimization, and real-time synchronization.
    """

    def __init__(self, location_id: Optional[str] = None):
        """
        Initialize dashboard orchestrator.

        Args:
            location_id: GHL location ID for multi-tenant operation
        """
        self.location_id = location_id
        self.logger = logging.getLogger(__name__)

        # Session management
        self.active_sessions: Dict[str, DashboardSession] = {}
        self.intelligence_cache: Dict[str, IntelligenceSnapshot] = {}

        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "avg_response_time": 0.0,
            "cache_hit_rate": 0.0,
            "active_sessions": 0,
            "data_sync_rate": 0.0,
            "error_rate": 0.0
        }

        # Service instances
        self.realtime_connector: Optional[RealTimeIntelligenceConnector] = None
        self.service_registry: Optional[ServiceRegistry] = None

        # Background task handles
        self.background_tasks: List[asyncio.Task] = []

        # Initialize services
        asyncio.create_task(self._initialize_services())

    async def _initialize_services(self):
        """Initialize required services and background tasks."""
        try:
            # Initialize real-time connector
            self.realtime_connector = await get_realtime_connector()

            # Initialize service registry if available
            if SERVICE_REGISTRY_AVAILABLE:
                self.service_registry = ServiceRegistry(
                    location_id=self.location_id,
                    demo_mode=False
                )

            # Start background tasks
            self.background_tasks = [
                asyncio.create_task(self._session_cleanup_task()),
                asyncio.create_task(self._data_sync_task()),
                asyncio.create_task(self._performance_monitoring_task())
            ]

            self.logger.info("Dashboard orchestrator initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing orchestrator: {e}")

    async def create_session(
        self,
        agent_id: str,
        location_id: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new dashboard session.

        Args:
            agent_id: Agent identifier
            location_id: Optional location ID override
            preferences: User preferences for dashboard

        Returns:
            Session ID for the created session
        """
        session_id = f"session_{int(time.time() * 1000)}_{agent_id}"

        default_preferences = {
            "theme": "professional",
            "layout": "tabbed",
            "auto_refresh": True,
            "refresh_interval": 5,
            "notifications": True,
            "coaching_frequency": "medium",
            "analytics_depth": "detailed",
            "real_time_updates": True
        }

        session = DashboardSession(
            session_id=session_id,
            agent_id=agent_id,
            location_id=location_id or self.location_id or "default",
            active_lead_id=None,
            dashboard_mode=DashboardMode.OVERVIEW,
            preferences={**default_preferences, **(preferences or {})},
            last_activity=datetime.now(),
            real_time_enabled=True,
            filters={},
            performance_metrics={}
        )

        self.active_sessions[session_id] = session
        self.performance_metrics["active_sessions"] = len(self.active_sessions)

        self.logger.info(f"Created dashboard session: {session_id} for agent {agent_id}")

        return session_id

    async def get_session(self, session_id: str) -> Optional[DashboardSession]:
        """Get dashboard session by ID."""
        return self.active_sessions.get(session_id)

    async def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update dashboard session data."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]

            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            session.last_activity = datetime.now()
            self.logger.debug(f"Updated session {session_id}: {updates}")

    async def close_session(self, session_id: str):
        """Close dashboard session and cleanup resources."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.performance_metrics["active_sessions"] = len(self.active_sessions)
            self.logger.info(f"Closed dashboard session: {session_id}")

    async def get_complete_intelligence(
        self,
        session_id: str,
        lead_id: str,
        force_refresh: bool = False
    ) -> IntelligenceSnapshot:
        """
        Get complete intelligence snapshot for a lead.

        Args:
            session_id: Dashboard session ID
            lead_id: Lead identifier
            force_refresh: Force refresh from source services

        Returns:
            Complete intelligence snapshot
        """
        start_time = time.time()
        self.performance_metrics["total_requests"] += 1

        # Check session validity
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Invalid session ID: {session_id}")

        cache_key = f"{session.location_id}:{lead_id}"

        # Check cache unless force refresh
        if not force_refresh and cache_key in self.intelligence_cache:
            cached_snapshot = self.intelligence_cache[cache_key]
            age = datetime.now() - cached_snapshot.timestamp
            if age.total_seconds() < 60:  # Cache for 1 minute
                self._update_response_time_metric(time.time() - start_time)
                return cached_snapshot

        try:
            # Get lead profile
            lead_profile = await self._get_lead_profile(lead_id, session)

            # Gather intelligence data in parallel
            tasks = [
                self._get_coaching_intelligence(lead_id, session, lead_profile),
                self._get_sentiment_intelligence(lead_id, session),
                self._get_journey_intelligence(lead_id, session),
                self._get_content_intelligence(lead_id, session, lead_profile),
                self._get_competitive_intelligence(session)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            coaching_data, sentiment_data, journey_data, content_data, competitive_data = results

            # Handle any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Intelligence gathering error for task {i}: {result}")
                    results[i] = None

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(results)

            # Create intelligence snapshot
            snapshot = IntelligenceSnapshot(
                lead_id=lead_id,
                timestamp=datetime.now(),
                coaching_data=coaching_data if not isinstance(coaching_data, Exception) else None,
                sentiment_data=sentiment_data if not isinstance(sentiment_data, Exception) else None,
                journey_data=journey_data if not isinstance(journey_data, Exception) else None,
                content_recommendations=content_data if not isinstance(content_data, Exception) else None,
                competitive_data=competitive_data if not isinstance(competitive_data, Exception) else None,
                sync_status=DataSyncStatus.SYNCED,
                confidence_score=confidence_score
            )

            # Cache the snapshot
            self.intelligence_cache[cache_key] = snapshot

            # Update metrics
            self._update_response_time_metric(time.time() - start_time)

            return snapshot

        except Exception as e:
            self.logger.error(f"Error getting complete intelligence: {e}")

            # Return error snapshot
            error_snapshot = IntelligenceSnapshot(
                lead_id=lead_id,
                timestamp=datetime.now(),
                coaching_data=None,
                sentiment_data=None,
                journey_data=None,
                content_recommendations=None,
                competitive_data=None,
                sync_status=DataSyncStatus.ERROR,
                confidence_score=0.0
            )

            self._update_response_time_metric(time.time() - start_time)
            self.performance_metrics["error_rate"] = self.performance_metrics.get("error_rate", 0) + 0.01

            return error_snapshot

    async def get_dashboard_configuration(
        self,
        session_id: str,
        dashboard_mode: DashboardMode
    ) -> Dict[str, Any]:
        """
        Get dashboard configuration for specific mode.

        Args:
            session_id: Dashboard session ID
            dashboard_mode: Requested dashboard mode

        Returns:
            Dashboard configuration and layout settings
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Invalid session ID: {session_id}")

        base_config = {
            "session_id": session_id,
            "mode": dashboard_mode.value,
            "preferences": session.preferences,
            "real_time_enabled": session.real_time_enabled,
            "active_lead_id": session.active_lead_id,
            "location_id": session.location_id
        }

        # Mode-specific configurations
        mode_configs = {
            DashboardMode.OVERVIEW: {
                "components": ["metrics_overview", "activity_feed", "quick_insights"],
                "refresh_interval": session.preferences.get("refresh_interval", 5),
                "layout": "grid"
            },
            DashboardMode.REAL_TIME_COACHING: {
                "components": ["coaching_panel", "objection_assistant", "question_guide"],
                "refresh_interval": 2,  # More frequent for real-time
                "layout": "vertical"
            },
            DashboardMode.LEAD_JOURNEY: {
                "components": ["journey_map", "stage_insights", "progression_timeline"],
                "refresh_interval": session.preferences.get("refresh_interval", 5),
                "layout": "timeline"
            },
            DashboardMode.SENTIMENT_ANALYSIS: {
                "components": ["sentiment_dashboard", "emotion_radar", "conversation_flow"],
                "refresh_interval": 3,
                "layout": "analysis"
            },
            DashboardMode.COMPETITIVE_INTEL: {
                "components": ["positioning_matrix", "threat_analysis", "opportunity_map"],
                "refresh_interval": 30,  # Less frequent for competitive data
                "layout": "strategic"
            },
            DashboardMode.CONTENT_ENGINE: {
                "components": ["content_recommendations", "relevance_scoring", "engagement_prediction"],
                "refresh_interval": 10,
                "layout": "content_grid"
            },
            DashboardMode.PERFORMANCE_ANALYTICS: {
                "components": ["performance_metrics", "trend_analysis", "system_health"],
                "refresh_interval": 15,
                "layout": "analytics"
            },
            DashboardMode.UNIFIED_VIEW: {
                "components": ["live_intelligence", "deep_analytics", "action_center"],
                "refresh_interval": 3,
                "layout": "unified_tabs"
            }
        }

        config = {**base_config, **mode_configs.get(dashboard_mode, {})}

        return config

    async def sync_intelligence_data(
        self,
        session_id: str,
        lead_id: str,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, DataSyncStatus]:
        """
        Synchronize specific intelligence data types.

        Args:
            session_id: Dashboard session ID
            lead_id: Lead identifier
            data_types: Optional list of data types to sync

        Returns:
            Sync status for each data type
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Invalid session ID: {session_id}")

        if data_types is None:
            data_types = ["coaching", "sentiment", "journey", "content", "competitive"]

        sync_results = {}

        for data_type in data_types:
            try:
                sync_results[data_type] = DataSyncStatus.SYNCING

                if data_type == "coaching":
                    await self._sync_coaching_data(lead_id, session)
                elif data_type == "sentiment":
                    await self._sync_sentiment_data(lead_id, session)
                elif data_type == "journey":
                    await self._sync_journey_data(lead_id, session)
                elif data_type == "content":
                    await self._sync_content_data(lead_id, session)
                elif data_type == "competitive":
                    await self._sync_competitive_data(session)

                sync_results[data_type] = DataSyncStatus.SYNCED

            except Exception as e:
                self.logger.error(f"Error syncing {data_type} data: {e}")
                sync_results[data_type] = DataSyncStatus.ERROR

        return sync_results

    async def get_performance_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive performance analytics.

        Args:
            session_id: Dashboard session ID

        Returns:
            Performance analytics data
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Invalid session ID: {session_id}")

        # Get connector metrics
        connector_metrics = {}
        if self.realtime_connector:
            connector_metrics = self.realtime_connector.get_performance_metrics()

        # Calculate dashboard-specific metrics
        dashboard_metrics = {
            "active_sessions": len(self.active_sessions),
            "intelligence_cache_size": len(self.intelligence_cache),
            "avg_session_duration": self._calculate_avg_session_duration(),
            "data_freshness": self._calculate_data_freshness(),
            "user_engagement": self._calculate_user_engagement()
        }

        return {
            "dashboard_metrics": dashboard_metrics,
            "connector_metrics": connector_metrics,
            "orchestrator_metrics": self.performance_metrics,
            "timestamp": datetime.now().isoformat()
        }

    # Private helper methods

    async def _get_lead_profile(self, lead_id: str, session: DashboardSession) -> Dict[str, Any]:
        """Get lead profile data."""
        # This would typically fetch from GHL or lead database
        # For now, return sample profile data
        return {
            "lead_id": lead_id,
            "name": "Sample Lead",
            "age_range": "30-40",
            "interests": ["Modern design", "Urban living"],
            "communication_style": "Direct",
            "income_level": "High",
            "location_preference": "Downtown"
        }

    async def _get_coaching_intelligence(
        self,
        lead_id: str,
        session: DashboardSession,
        lead_profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get coaching intelligence data."""
        if self.realtime_connector:
            conversation_context = {
                "lead_profile": lead_profile,
                "stage": "discovery",
                "latest_message": "I'm interested in finding a property"
            }

            return await self.realtime_connector.get_real_time_coaching(
                lead_id=lead_id,
                agent_id=session.agent_id,
                conversation_context=conversation_context,
                use_cache=True
            )
        return None

    async def _get_sentiment_intelligence(
        self,
        lead_id: str,
        session: DashboardSession
    ) -> Optional[List[SentimentAnalysis]]:
        """Get sentiment intelligence data."""
        if self.realtime_connector:
            # Sample conversation messages
            conversation_messages = [
                {"speaker": "prospect", "message": "I'm looking for a new home"},
                {"speaker": "agent", "message": "I'd love to help you find the perfect place"},
                {"speaker": "prospect", "message": "That sounds great!"}
            ]

            return await self.realtime_connector.get_sentiment_analysis(
                lead_id=lead_id,
                conversation_messages=conversation_messages,
                use_cache=True
            )
        return None

    async def _get_journey_intelligence(
        self,
        lead_id: str,
        session: DashboardSession
    ) -> Optional[List[LeadJourneyStage]]:
        """Get journey intelligence data."""
        if self.realtime_connector:
            return await self.realtime_connector.get_lead_journey_progress(
                lead_id=lead_id,
                agent_id=session.agent_id,
                use_cache=True
            )
        return None

    async def _get_content_intelligence(
        self,
        lead_id: str,
        session: DashboardSession,
        lead_profile: Dict[str, Any]
    ) -> Optional[List[ContentRecommendation]]:
        """Get content intelligence data."""
        if self.realtime_connector:
            return await self.realtime_connector.get_content_recommendations(
                lead_id=lead_id,
                lead_profile=lead_profile,
                use_cache=True
            )
        return None

    async def _get_competitive_intelligence(self, session: DashboardSession) -> Optional[CompetitiveIntelligence]:
        """Get competitive intelligence data."""
        if DASHBOARD_MODELS_AVAILABLE:
            # This would typically come from market analysis service
            # For now, return sample competitive data
            return CompetitiveIntelligence(
                market_segment="Real Estate - Residential",
                competitive_position="Challenger",
                market_share=0.185,
                key_differentiators=[
                    "AI-powered lead intelligence",
                    "Real-time coaching platform",
                    "Advanced sentiment analysis"
                ],
                competitive_threats=["Tech-enabled competitors", "Market consolidation"],
                market_opportunities=["AI adoption", "First-time buyer growth"],
                pricing_position="Premium",
                recommendation="Leverage AI capabilities as key differentiator"
            )
        return None

    def _calculate_confidence_score(self, results: List[Any]) -> float:
        """Calculate overall confidence score for intelligence data."""
        valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        total_results = len(results)

        if total_results == 0:
            return 0.0

        return len(valid_results) / total_results

    def _update_response_time_metric(self, response_time: float):
        """Update average response time metric."""
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["avg_response_time"]

        # Calculate running average
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.performance_metrics["avg_response_time"] = new_avg

    def _calculate_avg_session_duration(self) -> float:
        """Calculate average session duration in minutes."""
        if not self.active_sessions:
            return 0.0

        total_duration = 0.0
        current_time = datetime.now()

        for session in self.active_sessions.values():
            # Estimate session start time (this would be tracked properly in production)
            estimated_start = session.last_activity - timedelta(minutes=30)
            duration = (current_time - estimated_start).total_seconds() / 60
            total_duration += duration

        return total_duration / len(self.active_sessions)

    def _calculate_data_freshness(self) -> float:
        """Calculate data freshness score."""
        if not self.intelligence_cache:
            return 1.0

        current_time = datetime.now()
        total_freshness = 0.0

        for snapshot in self.intelligence_cache.values():
            age_minutes = (current_time - snapshot.timestamp).total_seconds() / 60
            # Freshness score: 1.0 for fresh data (0 min), decreasing to 0.0 at 60 min
            freshness = max(0.0, 1.0 - (age_minutes / 60))
            total_freshness += freshness

        return total_freshness / len(self.intelligence_cache)

    def _calculate_user_engagement(self) -> float:
        """Calculate user engagement score."""
        if not self.active_sessions:
            return 0.0

        current_time = datetime.now()
        active_sessions = 0

        for session in self.active_sessions.values():
            # Consider session active if last activity was within 5 minutes
            if (current_time - session.last_activity).total_seconds() < 300:
                active_sessions += 1

        return active_sessions / len(self.active_sessions)

    # Background tasks

    async def _session_cleanup_task(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                current_time = datetime.now()
                expired_sessions = []

                for session_id, session in self.active_sessions.items():
                    # Consider session expired if inactive for more than 1 hour
                    if (current_time - session.last_activity).total_seconds() > 3600:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    await self.close_session(session_id)

                if expired_sessions:
                    self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

            except Exception as e:
                self.logger.error(f"Session cleanup error: {e}")

    async def _data_sync_task(self):
        """Background task to sync intelligence data."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                # Sync intelligence cache
                current_time = datetime.now()
                for cache_key, snapshot in list(self.intelligence_cache.items()):
                    age = current_time - snapshot.timestamp
                    if age.total_seconds() > 300:  # Refresh data older than 5 minutes
                        try:
                            # Trigger refresh for active leads
                            if any(session.active_lead_id == snapshot.lead_id
                                   for session in self.active_sessions.values()):
                                # This would trigger a background refresh
                                pass
                        except Exception as e:
                            self.logger.warning(f"Data sync error for {cache_key}: {e}")

            except Exception as e:
                self.logger.error(f"Data sync task error: {e}")

    async def _performance_monitoring_task(self):
        """Background task to monitor performance."""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds

                # Update performance metrics
                self.performance_metrics.update({
                    "active_sessions": len(self.active_sessions),
                    "cache_size": len(self.intelligence_cache),
                    "uptime_seconds": time.time() - getattr(self, '_start_time', time.time())
                })

                # Log performance alerts
                if self.performance_metrics["avg_response_time"] > 1.0:  # 1 second threshold
                    self.logger.warning("High response time detected")

                if self.performance_metrics["error_rate"] > 0.1:  # 10% error rate
                    self.logger.warning("High error rate detected")

            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")

    # Sync helper methods
    async def _sync_coaching_data(self, lead_id: str, session: DashboardSession):
        """Sync coaching data for lead."""
        # Implementation would refresh coaching data
        pass

    async def _sync_sentiment_data(self, lead_id: str, session: DashboardSession):
        """Sync sentiment data for lead."""
        # Implementation would refresh sentiment data
        pass

    async def _sync_journey_data(self, lead_id: str, session: DashboardSession):
        """Sync journey data for lead."""
        # Implementation would refresh journey data
        pass

    async def _sync_content_data(self, lead_id: str, session: DashboardSession):
        """Sync content data for lead."""
        # Implementation would refresh content data
        pass

    async def _sync_competitive_data(self, session: DashboardSession):
        """Sync competitive data."""
        # Implementation would refresh competitive data
        pass


# Singleton instance
_dashboard_orchestrator: Optional[DashboardOrchestrator] = None


async def get_dashboard_orchestrator(location_id: Optional[str] = None) -> DashboardOrchestrator:
    """Get singleton dashboard orchestrator."""
    global _dashboard_orchestrator
    if _dashboard_orchestrator is None:
        _dashboard_orchestrator = DashboardOrchestrator(location_id=location_id)
        _dashboard_orchestrator._start_time = time.time()
    return _dashboard_orchestrator


# Factory function for testing
def create_dashboard_orchestrator(location_id: Optional[str] = None) -> DashboardOrchestrator:
    """Create a new dashboard orchestrator instance."""
    return DashboardOrchestrator(location_id=location_id)