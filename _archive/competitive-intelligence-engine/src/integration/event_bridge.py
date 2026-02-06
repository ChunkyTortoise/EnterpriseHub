"""
Event Bridge for Cross-Track Coordination

Unified event coordination system that bridges CRM Integration, Advanced Analytics,
and Real-Time Dashboard components for seamless data flow and workflow automation.

Features:
- Cross-track event routing and transformation
- Intelligence-to-dashboard real-time streaming
- CRM action triggering from analytics insights
- ML model retraining triggers
- Dashboard update coordination
- Event replay and audit logging

Author: Claude
Date: January 2026
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Set
from uuid import uuid4

# Import components from all tracks
from ..core.event_bus import EventBus, EventHandler, EventType, EventPriority
from ..analytics.executive_analytics_engine import ExecutiveSummary, StakeholderType
from ..crm.crm_coordinator import CRMCoordinator, IntelligenceAction, IntelligenceActionType
from ..crm.base_crm_connector import CRMPlatform
from ..dashboard.real_time.websocket_manager import WebSocketManager, WebSocketEvent, MessageType

logger = logging.getLogger(__name__)


class IntegrationEventType(Enum):
    """Types of integration events across tracks."""
    # Cross-track coordination
    INTELLIGENCE_TO_CRM = "intelligence_to_crm"
    ANALYTICS_TO_DASHBOARD = "analytics_to_dashboard" 
    CRM_TO_DASHBOARD = "crm_to_dashboard"
    ML_MODEL_UPDATE = "ml_model_update"
    
    # Workflow events
    WORKFLOW_TRIGGER = "workflow_trigger"
    ACTION_CHAIN_STARTED = "action_chain_started"
    ACTION_CHAIN_COMPLETED = "action_chain_completed"
    
    # System events
    INTEGRATION_STATUS_CHANGE = "integration_status_change"
    PERFORMANCE_METRICS_UPDATE = "performance_metrics_update"


@dataclass
class CrossTrackEvent:
    """Event that spans multiple system tracks."""
    event_id: str
    integration_event_type: IntegrationEventType
    source_track: str  # analytics, crm, dashboard
    target_tracks: List[str]
    original_event_type: str
    event_data: Dict[str, Any]
    transformation_rules: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.MEDIUM
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    processing_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationMetrics:
    """Integration performance metrics."""
    events_processed: int = 0
    cross_track_events: int = 0
    successful_transformations: int = 0
    failed_transformations: int = 0
    average_processing_time_ms: float = 0.0
    dashboard_updates_sent: int = 0
    crm_actions_triggered: int = 0
    ml_model_updates: int = 0


class EventBridge(EventHandler):
    """
    Event Bridge for Cross-Track Coordination
    
    Coordinates events across CRM, Analytics, and Dashboard tracks to provide
    unified enterprise-grade competitive intelligence workflows.
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        crm_coordinator: Optional[CRMCoordinator] = None,
        websocket_manager: Optional[WebSocketManager] = None,
        enable_event_replay: bool = True,
        max_event_history: int = 10000
    ):
        """
        Initialize Event Bridge.
        
        Args:
            event_bus: Core event bus
            crm_coordinator: CRM coordinator instance
            websocket_manager: WebSocket manager for real-time updates
            enable_event_replay: Enable event replay functionality
            max_event_history: Maximum events to keep in history
        """
        super().__init__(
            name="event_bridge",
            event_types=[
                # Analytics events to coordinate
                EventType.EXECUTIVE_SUMMARY_CREATED,
                EventType.STRATEGIC_PATTERN_IDENTIFIED,
                EventType.LANDSCAPE_MAPPED,
                EventType.MARKET_SHARE_CALCULATED,
                EventType.INTELLIGENCE_INSIGHT_CREATED,
                
                # CRM events to coordinate  
                EventType.CRM_CONTACT_UPDATED,
                EventType.CRM_OPPORTUNITY_UPDATED,
                EventType.CRM_SYNC_COMPLETED,
                
                # Dashboard events
                EventType.DASHBOARD_UPDATED,
                
                # ML/Prediction events
                EventType.PREDICTION_GENERATED,
                EventType.DEEP_LEARNING_PREDICTION,
                
                # M&A Intelligence events (Ultra-High-Value Integration)
                EventType.MA_THREAT_DETECTED,
                EventType.MA_DEFENSE_EXECUTED,
                EventType.MA_OPPORTUNITY_IDENTIFIED,
                EventType.MA_VALUATION_ANALYSIS_COMPLETED,
                EventType.MA_ACQUISITION_APPROACH_PREDICTED,
                
                # Enhancement Engine Coordination events
                EventType.AUTONOMOUS_STRATEGY_EXECUTED,
                EventType.REGULATORY_VIOLATION_PREVENTED,
                EventType.CUSTOMER_DEFECTION_PREVENTED,
                
                # Cross-Enhancement Integration events
                EventType.MULTI_ENGINE_COORDINATION_REQUIRED,
                EventType.ENTERPRISE_RESPONSE_COORDINATED,
                EventType.ULTRA_HIGH_VALUE_EVENT,
            ]
        )
        
        self.event_bus = event_bus
        self.crm_coordinator = crm_coordinator
        self.websocket_manager = websocket_manager
        self.enable_event_replay = enable_event_replay
        self.max_event_history = max_event_history
        
        # Event processing
        self.cross_track_events: List[CrossTrackEvent] = []
        self.event_transformers: Dict[IntegrationEventType, Callable] = {}
        self.integration_rules: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self.metrics = IntegrationMetrics()
        
        # Event history for replay
        self.event_history: List[CrossTrackEvent] = []
        
        # Initialize transformation rules
        self._setup_default_transformations()
        
        logger.info("Event Bridge initialized for cross-track coordination")
    
    async def start(self):
        """Start the event bridge."""
        try:
            await super().start()
            
            # Start background processors
            asyncio.create_task(self._cross_track_event_processor())
            asyncio.create_task(self._metrics_reporter())
            
            logger.info("Event Bridge started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Event Bridge: {e}")
            raise
    
    async def handle(self, event) -> bool:
        """Handle events and coordinate cross-track actions."""
        try:
            # Update metrics
            self.metrics.events_processed += 1
            
            # Process based on event type
            if event.type == EventType.EXECUTIVE_SUMMARY_CREATED:
                await self._handle_executive_summary_event(event)
            elif event.type == EventType.STRATEGIC_PATTERN_IDENTIFIED:
                await self._handle_strategic_pattern_event(event)
            elif event.type == EventType.INTELLIGENCE_INSIGHT_CREATED:
                await self._handle_intelligence_insight_event(event)
            elif event.type in [EventType.LANDSCAPE_MAPPED, EventType.MARKET_SHARE_CALCULATED]:
                await self._handle_analytics_completion_event(event)
            elif event.type in [EventType.CRM_CONTACT_UPDATED, EventType.CRM_OPPORTUNITY_UPDATED]:
                await self._handle_crm_data_event(event)
            elif event.type == EventType.CRM_SYNC_COMPLETED:
                await self._handle_crm_sync_event(event)
            elif event.type in [EventType.PREDICTION_GENERATED, EventType.DEEP_LEARNING_PREDICTION]:
                await self._handle_ml_prediction_event(event)
            elif event.type == EventType.MA_THREAT_DETECTED:
                await self._handle_ma_threat_event(event)
            elif event.type == EventType.MA_DEFENSE_EXECUTED:
                await self._handle_ma_defense_event(event)
            elif event.type == EventType.MA_OPPORTUNITY_IDENTIFIED:
                await self._handle_ma_opportunity_event(event)
            elif event.type in [EventType.AUTONOMOUS_STRATEGY_EXECUTED, EventType.REGULATORY_VIOLATION_PREVENTED, EventType.CUSTOMER_DEFECTION_PREVENTED]:
                await self._handle_enhancement_engine_coordination_event(event)
            elif event.type == EventType.ENTERPRISE_RESPONSE_COORDINATED:
                await self._handle_enterprise_coordination_event(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling event in Event Bridge: {e}")
            self.metrics.failed_transformations += 1
            return False
    
    async def _handle_executive_summary_event(self, event):
        """Handle executive summary creation and coordinate cross-track actions."""
        try:
            summary_data = event.data
            
            # Create cross-track event for dashboard update
            dashboard_event = CrossTrackEvent(
                event_id=str(uuid4()),
                integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,
                source_track="analytics",
                target_tracks=["dashboard"],
                original_event_type="executive_summary_created",
                event_data={
                    "summary_id": summary_data.get("summary_id"),
                    "stakeholder_type": summary_data.get("stakeholder_type"),
                    "threat_level": summary_data.get("threat_level"),
                    "opportunity_count": summary_data.get("opportunity_count"),
                    "action_count": summary_data.get("action_count"),
                    "business_impact": summary_data.get("business_impact", {}),
                    "dashboard_update_type": "executive_summary",
                    "priority": "high"
                },
                correlation_id=event.correlation_id,
                priority=EventPriority.HIGH
            )\n            \n            await self._queue_cross_track_event(dashboard_event)\n            \n            # Create cross-track event for CRM actions\n            crm_event = CrossTrackEvent(\n                event_id=str(uuid4()),\n                integration_event_type=IntegrationEventType.INTELLIGENCE_TO_CRM,\n                source_track=\"analytics\",\n                target_tracks=[\"crm\"],\n                original_event_type=\"executive_summary_created\",\n                event_data={\n                    \"summary_id\": summary_data.get(\"summary_id\"),\n                    \"stakeholder_type\": summary_data.get(\"stakeholder_type\"),\n                    \"opportunities\": summary_data.get(\"business_impact\", {}).get(\"quantitative_analysis\", {}).get(\"roi_analyses\", []),\n                    \"recommended_actions\": summary_data.get(\"business_impact\", {}),\n                    \"crm_action_type\": \"executive_intelligence_update\"\n                },\n                correlation_id=event.correlation_id,\n                priority=EventPriority.HIGH\n            )\n            \n            await self._queue_cross_track_event(crm_event)\n            \n            logger.info(f\"Coordinated executive summary event across tracks: {event.correlation_id}\")\n            \n        except Exception as e:\n            logger.error(f\"Error handling executive summary event: {e}\")\n    \n    async def _handle_strategic_pattern_event(self, event):\n        \"\"\"Handle strategic pattern identification and trigger real-time alerts.\"\"\"\n        try:\n            pattern_data = event.data\n            urgency_level = pattern_data.get(\"urgency_level\", \"medium\")\n            \n            # High-priority dashboard update for critical patterns\n            if urgency_level in [\"critical\", \"high\"]:\n                dashboard_event = CrossTrackEvent(\n                    event_id=str(uuid4()),\n                    integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,\n                    source_track=\"analytics\",\n                    target_tracks=[\"dashboard\"],\n                    original_event_type=\"strategic_pattern_identified\",\n                    event_data={\n                        \"pattern_id\": pattern_data.get(\"pattern_id\"),\n                        \"pattern_type\": pattern_data.get(\"pattern_type\"),\n                        \"urgency_level\": urgency_level,\n                        \"confidence_score\": pattern_data.get(\"confidence_score\"),\n                        \"business_implications\": pattern_data.get(\"business_implications\", []),\n                        \"dashboard_update_type\": \"strategic_alert\",\n                        \"alert_priority\": \"critical\" if urgency_level == \"critical\" else \"high\"\n                    },\n                    correlation_id=event.correlation_id,\n                    priority=EventPriority.CRITICAL if urgency_level == \"critical\" else EventPriority.HIGH\n                )\n                \n                await self._queue_cross_track_event(dashboard_event)\n            \n            # CRM action for customer-facing implications\n            crm_event = CrossTrackEvent(\n                event_id=str(uuid4()),\n                integration_event_type=IntegrationEventType.INTELLIGENCE_TO_CRM,\n                source_track=\"analytics\",\n                target_tracks=[\"crm\"],\n                original_event_type=\"strategic_pattern_identified\",\n                event_data={\n                    \"pattern_type\": pattern_data.get(\"pattern_type\"),\n                    \"business_implications\": pattern_data.get(\"business_implications\", []),\n                    \"recommended_response\": pattern_data.get(\"recommended_response\"),\n                    \"crm_action_type\": \"strategic_pattern_alert\",\n                    \"urgency_level\": urgency_level\n                },\n                correlation_id=event.correlation_id\n            )\n            \n            await self._queue_cross_track_event(crm_event)\n            \n        except Exception as e:\n            logger.error(f\"Error handling strategic pattern event: {e}\")\n    \n    async def _handle_intelligence_insight_event(self, event):\n        \"\"\"Handle general intelligence insights.\"\"\"\n        try:\n            insight_data = event.data\n            confidence_score = insight_data.get(\"confidence_score\", 0.5)\n            \n            # Only coordinate high-confidence insights\n            if confidence_score > 0.8:\n                # Dashboard update\n                dashboard_event = CrossTrackEvent(\n                    event_id=str(uuid4()),\n                    integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,\n                    source_track=\"analytics\",\n                    target_tracks=[\"dashboard\"],\n                    original_event_type=\"intelligence_insight_created\",\n                    event_data={\n                        \"insight_id\": insight_data.get(\"insight_id\"),\n                        \"insight_type\": insight_data.get(\"insight_type\"),\n                        \"confidence_score\": confidence_score,\n                        \"competitor_id\": insight_data.get(\"competitor_id\"),\n                        \"dashboard_update_type\": \"intelligence_insight\"\n                    },\n                    correlation_id=event.correlation_id\n                )\n                \n                await self._queue_cross_track_event(dashboard_event)\n        \n        except Exception as e:\n            logger.error(f\"Error handling intelligence insight event: {e}\")\n    \n    async def _handle_analytics_completion_event(self, event):\n        \"\"\"Handle completion of analytics processes.\"\"\"\n        try:\n            # Dashboard update for analytics completion\n            dashboard_event = CrossTrackEvent(\n                event_id=str(uuid4()),\n                integration_event_type=IntegrationEventType.ANALYTICS_TO_DASHBOARD,\n                source_track=\"analytics\",\n                target_tracks=[\"dashboard\"],\n                original_event_type=event.type.value,\n                event_data={\n                    \"analytics_type\": event.type.value,\n                    \"completion_data\": event.data,\n                    \"dashboard_update_type\": \"analytics_completion\"\n                },\n                correlation_id=event.correlation_id\n            )\n            \n            await self._queue_cross_track_event(dashboard_event)\n            \n        except Exception as e:\n            logger.error(f\"Error handling analytics completion event: {e}\")\n    \n    async def _handle_crm_data_event(self, event):\n        \"\"\"Handle CRM data updates.\"\"\"\n        try:\n            # Dashboard update for CRM changes\n            dashboard_event = CrossTrackEvent(\n                event_id=str(uuid4()),\n                integration_event_type=IntegrationEventType.CRM_TO_DASHBOARD,\n                source_track=\"crm\",\n                target_tracks=[\"dashboard\"],\n                original_event_type=event.type.value,\n                event_data={\n                    \"crm_object_type\": event.data.get(\"object_type\", \"unknown\"),\n                    \"object_id\": event.data.get(\"object_id\"),\n                    \"change_type\": event.data.get(\"action\", \"updated\"),\n                    \"dashboard_update_type\": \"crm_data_change\"\n                },\n                correlation_id=event.correlation_id\n            )\n            \n            await self._queue_cross_track_event(dashboard_event)\n            \n        except Exception as e:\n            logger.error(f\"Error handling CRM data event: {e}\")\n    \n    async def _handle_crm_sync_event(self, event):\n        \"\"\"Handle CRM synchronization completion.\"\"\"\n        try:\n            sync_data = event.data\n            \n            # Dashboard update for sync status\n            dashboard_event = CrossTrackEvent(\n                event_id=str(uuid4()),\n                integration_event_type=IntegrationEventType.CRM_TO_DASHBOARD,\n                source_track=\"crm\",\n                target_tracks=[\"dashboard\"],\n                original_event_type=\"crm_sync_completed\",\n                event_data={\n                    \"platform\": sync_data.get(\"platform\"),\n                    \"objects_processed\": sync_data.get(\"objects_processed\", 0),\n                    \"duration_seconds\": sync_data.get(\"duration_seconds\", 0),\n                    \"dashboard_update_type\": \"crm_sync_status\"\n                },\n                correlation_id=event.correlation_id\n            )\n            \n            await self._queue_cross_track_event(dashboard_event)\n            \n        except Exception as e:\n            logger.error(f\"Error handling CRM sync event: {e}\")\n    \n    async def _handle_ml_prediction_event(self, event):\n        \"\"\"Handle ML prediction events.\"\"\"\n        try:\n            prediction_data = event.data\n            \n            # Dashboard update for new predictions\n            dashboard_event = CrossTrackEvent(\n                event_id=str(uuid4()),\n                integration_event_type=IntegrationEventType.ML_MODEL_UPDATE,\n                source_track=\"analytics\",\n                target_tracks=[\"dashboard\"],\n                original_event_type=event.type.value,\n                event_data={\n                    \"prediction_type\": prediction_data.get(\"prediction_type\"),\n                    \"confidence\": prediction_data.get(\"confidence_score\"),\n                    \"model_name\": prediction_data.get(\"model_name\"),\n                    \"predictions\": prediction_data.get(\"predictions\"),\n                    \"dashboard_update_type\": \"ml_prediction\"\n                },\n                correlation_id=event.correlation_id\n            )\n            \n            await self._queue_cross_track_event(dashboard_event)\n            \n        except Exception as e:\n            logger.error(f\"Error handling ML prediction event: {e}\")\n    \n    async def _queue_cross_track_event(self, cross_track_event: CrossTrackEvent):\n        \"\"\"Queue cross-track event for processing.\"\"\"\n        self.cross_track_events.append(cross_track_event)\n        self.metrics.cross_track_events += 1\n        \n        # Add to history if enabled\n        if self.enable_event_replay:\n            self.event_history.append(cross_track_event)\n            \n            # Trim history if needed\n            if len(self.event_history) > self.max_event_history:\n                self.event_history = self.event_history[-self.max_event_history:]\n    \n    async def _cross_track_event_processor(self):\n        \"\"\"Process queued cross-track events.\"\"\"\n        while self.is_running:\n            try:\n                if self.cross_track_events:\n                    # Process events in batches\n                    events_to_process = self.cross_track_events[:10]\n                    self.cross_track_events = self.cross_track_events[10:]\n                    \n                    for event in events_to_process:\n                        await self._process_cross_track_event(event)\n                \n                await asyncio.sleep(0.1)  # 100ms processing interval\n                \n            except Exception as e:\n                logger.error(f\"Error in cross-track event processor: {e}\")\n                await asyncio.sleep(1)\n    \n    async def _process_cross_track_event(self, event: CrossTrackEvent):\n        \"\"\"Process individual cross-track event.\"\"\"\n        try:\n            start_time = datetime.now()\n            \n            # Process for each target track\n            for target_track in event.target_tracks:\n                if target_track == \"dashboard\" and self.websocket_manager:\n                    await self._send_to_dashboard(event)\n                elif target_track == \"crm\" and self.crm_coordinator:\n                    await self._send_to_crm(event)\n                elif target_track == \"analytics\":\n                    await self._send_to_analytics(event)\n            \n            # Update processing metrics\n            event.processed_at = datetime.now(timezone.utc)\n            processing_time = (datetime.now() - start_time).total_seconds() * 1000\n            \n            # Update average processing time\n            if self.metrics.average_processing_time_ms == 0:\n                self.metrics.average_processing_time_ms = processing_time\n            else:\n                self.metrics.average_processing_time_ms = (\n                    self.metrics.average_processing_time_ms * 0.9 + \n                    processing_time * 0.1\n                )\n            \n            self.metrics.successful_transformations += 1\n            \n        except Exception as e:\n            logger.error(f\"Error processing cross-track event {event.event_id}: {e}\")\n            self.metrics.failed_transformations += 1\n    \n    async def _send_to_dashboard(self, event: CrossTrackEvent):\n        \"\"\"Send event to dashboard via WebSocket.\"\"\"\n        try:\n            if not self.websocket_manager:\n                return\n            \n            # Transform event data for dashboard\n            dashboard_data = self._transform_for_dashboard(event)\n            \n            # Create WebSocket event\n            ws_event = WebSocketEvent(\n                event_id=event.event_id,\n                message_type=MessageType.DATA_UPDATE,\n                event_type=event.integration_event_type.value,\n                data=dashboard_data,\n                timestamp=datetime.now(timezone.utc),\n                correlation_id=event.correlation_id,\n                priority=\"high\" if event.priority == EventPriority.HIGH else \"normal\"\n            )\n            \n            # Determine topic for subscription filtering\n            topic = self._get_dashboard_topic(event)\n            \n            # Broadcast to subscribed clients\n            await self.websocket_manager.broadcast_event(ws_event, topic)\n            \n            self.metrics.dashboard_updates_sent += 1\n            \n        except Exception as e:\n            logger.error(f\"Error sending to dashboard: {e}\")\n    \n    async def _send_to_crm(self, event: CrossTrackEvent):\n        \"\"\"Send event to CRM coordinator.\"\"\"\n        try:\n            if not self.crm_coordinator:\n                return\n            \n            # Transform event data for CRM actions\n            crm_actions = self._transform_for_crm(event)\n            \n            # Queue CRM actions\n            for action in crm_actions:\n                await self.crm_coordinator._queue_intelligence_action(action)\n            \n            self.metrics.crm_actions_triggered += len(crm_actions)\n            \n        except Exception as e:\n            logger.error(f\"Error sending to CRM: {e}\")\n    \n    async def _send_to_analytics(self, event: CrossTrackEvent):\n        \"\"\"Send event to analytics components.\"\"\"\n        try:\n            # Publish back to event bus for analytics components\n            if self.event_bus:\n                await self.event_bus.publish(\n                    event_type=EventType.INTELLIGENCE_INSIGHT_CREATED,\n                    data=event.event_data,\n                    source_system=\"event_bridge\",\n                    correlation_id=event.correlation_id\n                )\n            \n        except Exception as e:\n            logger.error(f\"Error sending to analytics: {e}\")\n    \n    def _transform_for_dashboard(self, event: CrossTrackEvent) -> Dict[str, Any]:\n        \"\"\"Transform event data for dashboard consumption.\"\"\"\n        dashboard_data = {\n            \"event_id\": event.event_id,\n            \"source_track\": event.source_track,\n            \"original_event_type\": event.original_event_type,\n            \"timestamp\": event.created_at.isoformat(),\n            \"correlation_id\": event.correlation_id\n        }\n        \n        # Add transformed data based on integration event type\n        if event.integration_event_type == IntegrationEventType.ANALYTICS_TO_DASHBOARD:\n            dashboard_data.update({\n                \"analytics_data\": event.event_data,\n                \"visualization_type\": event.event_data.get(\"dashboard_update_type\", \"general\"),\n                \"priority\": event.event_data.get(\"priority\", \"normal\")\n            })\n        \n        elif event.integration_event_type == IntegrationEventType.CRM_TO_DASHBOARD:\n            dashboard_data.update({\n                \"crm_data\": event.event_data,\n                \"object_type\": event.event_data.get(\"crm_object_type\"),\n                \"change_type\": event.event_data.get(\"change_type\")\n            })\n        \n        return dashboard_data\n    \n    def _transform_for_crm(self, event: CrossTrackEvent) -> List[IntelligenceAction]:\n        \"\"\"Transform event data for CRM actions.\"\"\"\n        actions = []\n        \n        try:\n            if event.integration_event_type == IntegrationEventType.INTELLIGENCE_TO_CRM:\n                crm_action_type = event.event_data.get(\"crm_action_type\", \"general\")\n                \n                if crm_action_type == \"executive_intelligence_update\":\n                    # Create note-adding action\n                    action = IntelligenceAction(\n                        action_id=str(uuid4()),\n                        action_type=IntelligenceActionType.ADD_COMPETITIVE_NOTE,\n                        target_platform=event.event_data.get(\"target_platform\", \"CRMPlatform.GOHIGHLEVEL.value\"),\n                        target_object_type=\"contact\",\n                        target_object_id=\"*\",  # Apply to all high-value contacts\n                        action_data={\n                            \"note_content\": f\"Executive Intelligence Update: {event.original_event_type}\",\n                            \"note_type\": \"executive_intelligence\",\n                            \"stakeholder_type\": event.event_data.get(\"stakeholder_type\")\n                        },\n                        intelligence_correlation_id=event.correlation_id or str(uuid4())\n                    )\n                    actions.append(action)\n                \n                elif crm_action_type == \"strategic_pattern_alert\":\n                    # Create alert action\n                    action = IntelligenceAction(\n                        action_id=str(uuid4()),\n                        action_type=IntelligenceActionType.ADD_COMPETITIVE_TAG,\n                        target_platform=event.event_data.get(\"target_platform\", \"CRMPlatform.GOHIGHLEVEL.value\"),\n                        target_object_type=\"opportunity\",\n                        target_object_id=\"*\",\n                        action_data={\n                            \"tags\": [f\"strategic_pattern_{event.event_data.get('pattern_type', 'general')}\"],\n                            \"urgency_level\": event.event_data.get(\"urgency_level\")\n                        },\n                        intelligence_correlation_id=event.correlation_id or str(uuid4())\n                    )\n                    actions.append(action)\n        \n        except Exception as e:\n            logger.error(f\"Error transforming event for CRM: {e}\")\n        \n        return actions\n    \n    def _get_dashboard_topic(self, event: CrossTrackEvent) -> str:\n        \"\"\"Get dashboard subscription topic for event.\"\"\"\n        if \"executive\" in event.original_event_type:\n            return \"executive_summary\"\n        elif \"pattern\" in event.original_event_type:\n            return \"strategic_patterns\" \n        elif \"alert\" in event.event_data.get(\"dashboard_update_type\", \"\"):\n            return \"competitive_alerts\"\n        elif event.integration_event_type == IntegrationEventType.ML_MODEL_UPDATE:\n            return \"analytics_updates\"\n        else:\n            return \"real_time_metrics\"\n    \n    def _setup_default_transformations(self):\n        \"\"\"Setup default event transformation rules.\"\"\"\n        # Default transformation rules for different event types\n        self.integration_rules = {\n            \"executive_summary_to_dashboard\": {\n                \"extract_fields\": [\"stakeholder_type\", \"threat_level\", \"opportunity_count\"],\n                \"dashboard_visualization\": \"executive_summary_card\",\n                \"real_time_update\": True\n            },\n            \"strategic_pattern_to_crm\": {\n                \"action_mapping\": {\n                    \"critical\": \"immediate_alert\",\n                    \"high\": \"priority_tag\",\n                    \"medium\": \"competitive_note\"\n                }\n            },\n            \"crm_sync_to_dashboard\": {\n                \"metrics_update\": True,\n                \"status_indicator\": True\n            }\n        }\n    \n    async def _metrics_reporter(self):\n        \"\"\"Report integration metrics periodically.\"\"\"\n        while self.is_running:\n            try:\n                # Report metrics every 5 minutes\n                await asyncio.sleep(300)\n                \n                metrics_data = {\n                    \"integration_metrics\": {\n                        \"events_processed\": self.metrics.events_processed,\n                        \"cross_track_events\": self.metrics.cross_track_events,\n                        \"successful_transformations\": self.metrics.successful_transformations,\n                        \"failed_transformations\": self.metrics.failed_transformations,\n                        \"average_processing_time_ms\": self.metrics.average_processing_time_ms,\n                        \"dashboard_updates_sent\": self.metrics.dashboard_updates_sent,\n                        \"crm_actions_triggered\": self.metrics.crm_actions_triggered\n                    },\n                    \"timestamp\": datetime.now(timezone.utc).isoformat()\n                }\n                \n                # Publish metrics event\n                if self.event_bus:\n                    await self.event_bus.publish(\n                        event_type=EventType.DASHBOARD_UPDATED,\n                        data=metrics_data,\n                        source_system=\"event_bridge\"\n                    )\n                \n                logger.debug(f\"Integration metrics reported: {self.metrics.events_processed} events processed\")\n                \n            except Exception as e:\n                logger.error(f\"Error reporting metrics: {e}\")\n    \n    # Public API methods\n    \n    def get_integration_status(self) -> Dict[str, Any]:\n        \"\"\"Get current integration status and metrics.\"\"\"\n        return {\n            \"is_running\": self.is_running,\n            \"components_connected\": {\n                \"event_bus\": self.event_bus is not None,\n                \"crm_coordinator\": self.crm_coordinator is not None,\n                \"websocket_manager\": self.websocket_manager is not None\n            },\n            \"metrics\": {\n                \"events_processed\": self.metrics.events_processed,\n                \"cross_track_events\": self.metrics.cross_track_events,\n                \"successful_transformations\": self.metrics.successful_transformations,\n                \"failed_transformations\": self.metrics.failed_transformations,\n                \"success_rate\": (\n                    (self.metrics.successful_transformations / \n                     max(1, self.metrics.successful_transformations + self.metrics.failed_transformations)) * 100\n                ),\n                \"average_processing_time_ms\": self.metrics.average_processing_time_ms,\n                \"dashboard_updates_sent\": self.metrics.dashboard_updates_sent,\n                \"crm_actions_triggered\": self.metrics.crm_actions_triggered\n            },\n            \"queued_events\": len(self.cross_track_events),\n            \"event_history_size\": len(self.event_history)\n        }\n    \n    async def replay_events(\n        self, \n        from_time: datetime, \n        to_time: Optional[datetime] = None,\n        event_types: Optional[List[IntegrationEventType]] = None\n    ) -> int:\n        \"\"\"Replay events from history for recovery or testing.\"\"\"\n        if not self.enable_event_replay:\n            return 0\n        \n        replayed_count = 0\n        to_time = to_time or datetime.now(timezone.utc)\n        \n        try:\n            for event in self.event_history:\n                if from_time <= event.created_at <= to_time:\n                    if event_types is None or event.integration_event_type in event_types:\n                        await self._queue_cross_track_event(event)\n                        replayed_count += 1\n            \n            logger.info(f\"Replayed {replayed_count} events from {from_time} to {to_time}\")\n            \n        except Exception as e:\n            logger.error(f\"Error replaying events: {e}\")\n        \n        return replayed_count\n\n\n# Export public API\n__all__ = [\n    \"EventBridge\",\n    \"CrossTrackEvent\", \n    \"IntegrationEventType\",\n    \"IntegrationMetrics\"\n]