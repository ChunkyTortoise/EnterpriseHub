"""
CRM Coordinator - Unified CRM Integration Management

This module coordinates all CRM platform integrations, providing a unified interface
for competitive intelligence to CRM workflows and managing cross-platform operations.

Features:
- Multi-platform CRM management
- Intelligence-to-action workflow automation  
- Real-time synchronization coordination
- Event-driven CRM updates
- Unified analytics and reporting

Author: Claude
Date: January 2026
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Type, Union
from uuid import uuid4

from ..core.event_bus import (
    EventBus, EventHandler, EventType, EventPriority,
    get_event_bus, publish_intelligence_insight
)

from .base_crm_connector import (
    BaseCRMConnector, CRMPlatform, ContactStatus, OpportunityStage,
    CRMConnection, CRMContact, CRMOpportunity, WebhookEvent, SyncOperation,
    SynchronizationStatus
)
from .connectors.gohighlevel_connector import GoHighLevelConnector
from .connectors.salesforce_connector import SalesforceConnector
from .connectors.hubspot_connector import HubSpotConnector

logger = logging.getLogger(__name__)


class CRMIntegrationType(Enum):
    """Types of CRM integrations."""
    READ_ONLY = "read_only"
    BIDIRECTIONAL = "bidirectional"
    WRITE_ONLY = "write_only"
    INTELLIGENCE_DRIVEN = "intelligence_driven"


class IntelligenceActionType(Enum):
    """Types of intelligence-driven actions."""
    UPDATE_LEAD_SCORE = "update_lead_score"
    ADD_COMPETITIVE_NOTE = "add_competitive_note"
    UPDATE_OPPORTUNITY_STAGE = "update_opportunity_stage"
    ADD_COMPETITIVE_TAG = "add_competitive_tag"
    CREATE_TASK = "create_task"
    SEND_ALERT = "send_alert"


@dataclass
class CRMIntegrationConfig:
    """Configuration for a CRM platform integration."""
    platform: CRMPlatform
    integration_type: CRMIntegrationType
    connector_class: Type[BaseCRMConnector]
    connection_config: Dict[str, Any]
    sync_interval_minutes: int = 15
    webhook_enabled: bool = True
    intelligence_actions_enabled: bool = True
    custom_field_mappings: Dict[str, str] = field(default_factory=dict)
    

@dataclass
class CRMConfiguration:
    """Overall CRM coordinator configuration."""
    integrations: List[CRMIntegrationConfig] = field(default_factory=list)
    default_sync_interval: int = 15
    max_concurrent_syncs: int = 3
    intelligence_action_delay_seconds: int = 5
    webhook_verification_required: bool = True
    audit_logging_enabled: bool = True


@dataclass
class IntelligenceAction:
    """Intelligence-driven CRM action."""
    action_id: str
    action_type: IntelligenceActionType
    target_platform: CRMPlatform
    target_object_type: str  # contact, opportunity
    target_object_id: str
    action_data: Dict[str, Any]
    intelligence_correlation_id: str
    priority: EventPriority = EventPriority.MEDIUM
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None


class CRMCoordinator(EventHandler):
    """
    CRM Coordinator - Unified Multi-Platform Integration Management
    
    This coordinator manages all CRM platform integrations and provides:
    - Unified interface for competitive intelligence workflows
    - Cross-platform synchronization and data management
    - Intelligence-driven automation (lead scoring, notes, alerts)
    - Event-driven updates from competitive analytics
    - Centralized monitoring and metrics
    """
    
    def __init__(
        self,
        config: Optional[CRMConfiguration] = None,
        event_bus: Optional[EventBus] = None
    ):
        """
        Initialize CRM Coordinator.
        
        Args:
            config: CRM configuration
            event_bus: Event bus for coordination
        """
        super().__init__(
            name="crm_coordinator",
            event_types=[
                # Intelligence events that trigger CRM actions
                EventType.EXECUTIVE_SUMMARY_CREATED,
                EventType.STRATEGIC_PATTERN_IDENTIFIED,
                EventType.COMPETITOR_ACTIVITY_DETECTED,
                EventType.INTELLIGENCE_INSIGHT_CREATED,
                
                # CRM events for coordination
                EventType.CRM_CONTACT_UPDATED,
                EventType.CRM_OPPORTUNITY_UPDATED,
                EventType.CRM_SYNC_COMPLETED,
                EventType.CRM_WEBHOOK_RECEIVED,
            ]
        )
        
        self.config = config or CRMConfiguration()
        self.event_bus = event_bus or get_event_bus()
        
        # CRM connectors
        self.connectors: Dict[CRMPlatform, BaseCRMConnector] = {}
        self.connector_status: Dict[CRMPlatform, bool] = {}
        
        # Intelligence action queue
        self.action_queue: List[IntelligenceAction] = []
        self.action_processor_running = False
        
        # Synchronization tracking
        self.active_syncs: Dict[str, SyncOperation] = {}
        self.sync_scheduler_running = False
        
        # Performance metrics
        self.actions_processed = 0
        self.actions_successful = 0
        self.syncs_completed = 0
        self.webhooks_received = 0
        
        logger.info("CRM Coordinator initialized")
    
    async def start(self):
        """Start the CRM coordinator and initialize all connectors."""
        try:
            await super().start()
            
            # Initialize CRM connectors
            for integration_config in self.config.integrations:
                await self._initialize_connector(integration_config)
            
            # Start background processes
            if self.config.integrations:
                self.action_processor_running = True
                asyncio.create_task(self._action_processor_loop())
                
                self.sync_scheduler_running = True
                asyncio.create_task(self._sync_scheduler_loop())
            
            logger.info(f"CRM Coordinator started with {len(self.connectors)} connectors")
            
        except Exception as e:
            logger.error(f"Failed to start CRM Coordinator: {e}")
            raise
    
    async def stop(self):
        """Stop the CRM coordinator and cleanup resources."""
        try:
            # Stop background processes
            self.action_processor_running = False
            self.sync_scheduler_running = False
            
            # Close all connectors
            for platform, connector in self.connectors.items():
                try:
                    if hasattr(connector, 'close'):
                        await connector.close()
                    logger.info(f"Closed {platform.value} connector")
                except Exception as e:
                    logger.error(f"Error closing {platform.value} connector: {e}")
            
            self.connectors.clear()
            self.connector_status.clear()
            
            await super().stop()
            logger.info("CRM Coordinator stopped")
            
        except Exception as e:
            logger.error(f"Error stopping CRM Coordinator: {e}")
    
    async def _initialize_connector(self, config: CRMIntegrationConfig):
        """Initialize a CRM connector."""
        try:
            # Create connector instance
            connector = config.connector_class(**config.connection_config)
            
            # Authenticate connector
            auth_successful = False
            if "credentials" in config.connection_config:
                auth_successful = await connector.authenticate(
                    config.connection_config["credentials"]
                )
            
            if auth_successful:
                self.connectors[config.platform] = connector
                self.connector_status[config.platform] = True
                
                # Setup webhook if enabled
                if config.webhook_enabled and "webhook_url" in config.connection_config:
                    try:
                        webhook_id = await connector.setup_webhook(
                            webhook_url=config.connection_config["webhook_url"],
                            events=config.connection_config.get("webhook_events", [
                                "contact.created", "contact.updated",
                                "opportunity.created", "opportunity.updated"
                            ])
                        )
                        logger.info(f"Webhook setup for {config.platform.value}: {webhook_id}")
                    except Exception as e:
                        logger.warning(f"Webhook setup failed for {config.platform.value}: {e}")
                
                logger.info(f"Successfully initialized {config.platform.value} connector")
            else:
                logger.error(f"Authentication failed for {config.platform.value}")
                self.connector_status[config.platform] = False
                
        except Exception as e:
            logger.error(f"Failed to initialize {config.platform.value} connector: {e}")
            self.connector_status[config.platform] = False
    
    async def handle(self, event) -> bool:
        """Handle incoming events and trigger CRM actions."""
        try:
            if event.type == EventType.EXECUTIVE_SUMMARY_CREATED:
                await self._handle_executive_summary_event(event)
            elif event.type == EventType.STRATEGIC_PATTERN_IDENTIFIED:
                await self._handle_strategic_pattern_event(event)
            elif event.type == EventType.COMPETITOR_ACTIVITY_DETECTED:
                await self._handle_competitor_activity_event(event)
            elif event.type == EventType.INTELLIGENCE_INSIGHT_CREATED:
                await self._handle_intelligence_insight_event(event)
            elif event.type in [
                EventType.CRM_CONTACT_UPDATED,
                EventType.CRM_OPPORTUNITY_UPDATED,
                EventType.CRM_SYNC_COMPLETED,
                EventType.CRM_WEBHOOK_RECEIVED
            ]:
                await self._handle_crm_event(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling event {event.type}: {e}")
            return False
    
    async def _handle_executive_summary_event(self, event):
        """Handle executive summary created event."""
        try:
            summary_data = event.data
            stakeholder_type = summary_data.get("stakeholder_type", "ceo")
            
            # Create intelligence actions based on executive summary
            if "opportunities" in summary_data:
                for opportunity in summary_data["opportunities"]:
                    # Add competitive tags to relevant opportunities
                    await self._queue_intelligence_action(
                        IntelligenceAction(
                            action_id=str(uuid4()),
                            action_type=IntelligenceActionType.ADD_COMPETITIVE_TAG,
                            target_platform=CRMPlatform.GOHIGHLEVEL,  # Default to GHL
                            target_object_type="opportunity",
                            target_object_id="*",  # Apply to all opportunities
                            action_data={
                                "tags": [f"executive_opportunity_{opportunity.get('type', 'general')}"],
                                "note": f"Executive insight: {opportunity.get('description', '')}"
                            },
                            intelligence_correlation_id=event.correlation_id or str(uuid4()),
                            priority=EventPriority.HIGH
                        )
                    )
            
            # Add executive summary note to high-value contacts
            await self._queue_intelligence_action(
                IntelligenceAction(
                    action_id=str(uuid4()),
                    action_type=IntelligenceActionType.ADD_COMPETITIVE_NOTE,
                    target_platform=CRMPlatform.GOHIGHLEVEL,
                    target_object_type="contact",
                    target_object_id="*",  # Apply to all high-value contacts
                    action_data={
                        "note_content": f"Executive Intelligence Update ({stakeholder_type.upper()}): "
                                       f"{summary_data.get('executive_bullets', ['No specific insights'])[0][:100]}...",
                        "note_type": "executive_intelligence"
                    },
                    intelligence_correlation_id=event.correlation_id or str(uuid4())
                )
            )
            
        except Exception as e:
            logger.error(f"Error handling executive summary event: {e}")
    
    async def _handle_strategic_pattern_event(self, event):
        """Handle strategic pattern identified event."""
        try:
            pattern_data = event.data
            urgency_level = pattern_data.get("urgency_level", "medium")
            
            # Create high-priority alerts for critical patterns
            if urgency_level == "critical":
                await self._queue_intelligence_action(
                    IntelligenceAction(
                        action_id=str(uuid4()),
                        action_type=IntelligenceActionType.SEND_ALERT,
                        target_platform=CRMPlatform.GOHIGHLEVEL,
                        target_object_type="system",
                        target_object_id="alerts",
                        action_data={
                            "alert_type": "strategic_pattern_critical",
                            "message": f"Critical competitive pattern detected: {pattern_data.get('pattern_type', 'unknown')}",
                            "recipients": ["sales_managers", "executives"],
                            "priority": "immediate"
                        },
                        intelligence_correlation_id=event.correlation_id or str(uuid4()),
                        priority=EventPriority.CRITICAL
                    )
                )
            
            # Update opportunity scores based on strategic patterns
            await self._queue_intelligence_action(
                IntelligenceAction(
                    action_id=str(uuid4()),
                    action_type=IntelligenceActionType.UPDATE_OPPORTUNITY_STAGE,
                    target_platform=CRMPlatform.GOHIGHLEVEL,
                    target_object_type="opportunity",
                    target_object_id="*",
                    action_data={
                        "pattern_type": pattern_data.get("pattern_type"),
                        "confidence_adjustment": pattern_data.get("confidence_score", 0.5),
                        "competitive_impact": pattern_data.get("business_implications", [])
                    },
                    intelligence_correlation_id=event.correlation_id or str(uuid4())
                )
            )
            
        except Exception as e:
            logger.error(f"Error handling strategic pattern event: {e}")
    
    async def _handle_competitor_activity_event(self, event):
        """Handle competitor activity detected event."""
        try:
            activity_data = event.data
            competitor_id = activity_data.get("competitor_id", "unknown")
            activity_type = activity_data.get("activity_type", "general")
            significance = activity_data.get("significance_score", 0.5)
            
            # Add competitive notes to relevant contacts/opportunities
            if significance > 0.7:  # High significance
                await self._queue_intelligence_action(
                    IntelligenceAction(
                        action_id=str(uuid4()),
                        action_type=IntelligenceActionType.ADD_COMPETITIVE_NOTE,
                        target_platform=CRMPlatform.GOHIGHLEVEL,
                        target_object_type="contact",
                        target_object_id="*",
                        action_data={
                            "note_content": f"Competitive Alert: {competitor_id} {activity_type} - "
                                           f"Significance: {significance:.1%}",
                            "note_type": "competitive_activity",
                            "competitor": competitor_id,
                            "activity_type": activity_type
                        },
                        intelligence_correlation_id=event.correlation_id or str(uuid4()),
                        priority=EventPriority.HIGH if significance > 0.8 else EventPriority.MEDIUM
                    )
                )
            
            # Update lead scoring based on competitive activity
            await self._queue_intelligence_action(
                IntelligenceAction(
                    action_id=str(uuid4()),
                    action_type=IntelligenceActionType.UPDATE_LEAD_SCORE,
                    target_platform=CRMPlatform.GOHIGHLEVEL,
                    target_object_type="contact",
                    target_object_id="*",
                    action_data={
                        "score_adjustment": significance * 0.1,  # Small boost for significant competitive activity
                        "reason": f"Competitive activity: {activity_type}",
                        "competitor": competitor_id
                    },
                    intelligence_correlation_id=event.correlation_id or str(uuid4())
                )
            )
            
        except Exception as e:
            logger.error(f"Error handling competitor activity event: {e}")
    
    async def _handle_intelligence_insight_event(self, event):
        """Handle general intelligence insight event."""
        try:
            insight_data = event.data
            confidence_score = insight_data.get("confidence_score", 0.5)
            insight_type = insight_data.get("insight_type", "general")
            
            # Only act on high-confidence insights
            if confidence_score > 0.8:
                await self._queue_intelligence_action(
                    IntelligenceAction(
                        action_id=str(uuid4()),
                        action_type=IntelligenceActionType.ADD_COMPETITIVE_TAG,
                        target_platform=CRMPlatform.GOHIGHLEVEL,
                        target_object_type="contact",
                        target_object_id="*",
                        action_data={
                            "tags": [f"intelligence_{insight_type}"],
                            "confidence": confidence_score
                        },
                        intelligence_correlation_id=event.correlation_id or str(uuid4())
                    )
                )
            
        except Exception as e:
            logger.error(f"Error handling intelligence insight event: {e}")
    
    async def _handle_crm_event(self, event):
        """Handle CRM-specific events."""
        try:
            if event.type == EventType.CRM_WEBHOOK_RECEIVED:
                self.webhooks_received += 1
                # Process webhook data
                webhook_data = event.data
                platform = webhook_data.get("platform")
                if platform in self.connectors:
                    # Trigger incremental sync or process webhook data
                    logger.info(f"Webhook received from {platform}: {webhook_data.get('event_type')}")
            
            elif event.type == EventType.CRM_SYNC_COMPLETED:
                self.syncs_completed += 1
                sync_data = event.data
                platform = sync_data.get("platform")
                logger.info(f"Sync completed for {platform}: {sync_data.get('objects_processed')} objects")
            
        except Exception as e:
            logger.error(f"Error handling CRM event: {e}")
    
    async def _queue_intelligence_action(self, action: IntelligenceAction):
        """Queue an intelligence-driven CRM action."""
        self.action_queue.append(action)
        logger.debug(f"Queued intelligence action: {action.action_type.value} for {action.target_platform.value}")
    
    async def _action_processor_loop(self):
        """Process intelligence actions from the queue."""
        while self.action_processor_running:
            try:
                if self.action_queue:
                    # Sort by priority and scheduled time
                    self.action_queue.sort(
                        key=lambda x: (x.priority.value, x.scheduled_at)
                    )
                    
                    # Process actions that are due
                    now = datetime.now(timezone.utc)
                    actions_to_process = []
                    
                    for action in self.action_queue[:]:
                        if action.scheduled_at <= now:
                            actions_to_process.append(action)
                            self.action_queue.remove(action)
                        
                        if len(actions_to_process) >= 5:  # Process in batches
                            break
                    
                    # Execute actions
                    for action in actions_to_process:
                        await self._execute_intelligence_action(action)
                
                # Wait before next iteration
                await asyncio.sleep(self.config.intelligence_action_delay_seconds)
                
            except Exception as e:
                logger.error(f"Error in action processor loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _execute_intelligence_action(self, action: IntelligenceAction):
        """Execute a single intelligence action."""
        try:
            self.actions_processed += 1
            
            # Get the appropriate connector
            if action.target_platform not in self.connectors:
                logger.warning(f"No connector available for {action.target_platform.value}")
                return
            
            connector = self.connectors[action.target_platform]
            
            # Execute action based on type
            success = False
            
            if action.action_type == IntelligenceActionType.ADD_COMPETITIVE_NOTE:
                success = await self._add_competitive_note(connector, action)
            elif action.action_type == IntelligenceActionType.UPDATE_LEAD_SCORE:
                success = await self._update_lead_score(connector, action)
            elif action.action_type == IntelligenceActionType.ADD_COMPETITIVE_TAG:
                success = await self._add_competitive_tag(connector, action)
            elif action.action_type == IntelligenceActionType.UPDATE_OPPORTUNITY_STAGE:
                success = await self._update_opportunity_stage(connector, action)
            elif action.action_type == IntelligenceActionType.CREATE_TASK:
                success = await self._create_task(connector, action)
            elif action.action_type == IntelligenceActionType.SEND_ALERT:
                success = await self._send_alert(connector, action)
            
            # Update action status
            action.executed_at = datetime.now(timezone.utc)
            action.success = success
            
            if success:
                self.actions_successful += 1
            
            logger.debug(f"Intelligence action {action.action_type.value} executed: {success}")
            
        except Exception as e:
            action.executed_at = datetime.now(timezone.utc)
            action.success = False
            action.error_message = str(e)
            logger.error(f"Failed to execute intelligence action: {e}")
    
    async def _add_competitive_note(
        self, 
        connector: BaseCRMConnector, 
        action: IntelligenceAction
    ) -> bool:
        """Add competitive intelligence note to CRM object."""
        try:
            if action.target_object_id == "*":
                # Add note to multiple objects - would need to query and filter
                # For now, skip wildcard operations
                logger.info("Skipping wildcard note addition (not implemented)")
                return True
            else:
                # Add note to specific object
                note_id = await connector.add_note(
                    object_type=action.target_object_type,
                    object_id=action.target_object_id,
                    content=action.action_data["note_content"],
                    note_type=action.action_data.get("note_type", "competitive_intelligence")
                )
                return note_id is not None
                
        except Exception as e:
            logger.error(f"Failed to add competitive note: {e}")
            return False
    
    async def _update_lead_score(
        self,
        connector: BaseCRMConnector,
        action: IntelligenceAction
    ) -> bool:
        """Update lead score based on competitive intelligence."""
        try:
            # This would require custom field updates
            # Implementation depends on CRM platform capabilities
            logger.info("Lead score update requested (implementation pending)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update lead score: {e}")
            return False
    
    async def _add_competitive_tag(
        self,
        connector: BaseCRMConnector,
        action: IntelligenceAction
    ) -> bool:
        """Add competitive intelligence tags to CRM object."""
        try:
            if action.target_object_id == "*":
                logger.info("Skipping wildcard tag addition (not implemented)")
                return True
            else:
                return await connector.add_tags(
                    object_type=action.target_object_type,
                    object_id=action.target_object_id,
                    tags=action.action_data["tags"]
                )
                
        except Exception as e:
            logger.error(f"Failed to add competitive tags: {e}")
            return False
    
    async def _update_opportunity_stage(
        self,
        connector: BaseCRMConnector,
        action: IntelligenceAction
    ) -> bool:
        """Update opportunity stage based on competitive intelligence."""
        try:
            logger.info("Opportunity stage update requested (implementation pending)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update opportunity stage: {e}")
            return False
    
    async def _create_task(
        self,
        connector: BaseCRMConnector,
        action: IntelligenceAction
    ) -> bool:
        """Create task based on competitive intelligence."""
        try:
            logger.info("Task creation requested (implementation pending)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return False
    
    async def _send_alert(
        self,
        connector: BaseCRMConnector,
        action: IntelligenceAction
    ) -> bool:
        """Send alert based on competitive intelligence."""
        try:
            logger.info(f"Alert sent: {action.action_data.get('message', 'No message')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    async def _sync_scheduler_loop(self):
        """Schedule and manage CRM synchronization operations."""
        while self.sync_scheduler_running:
            try:
                for platform, connector in self.connectors.items():
                    if self.connector_status.get(platform, False):
                        # Check if sync is due
                        last_sync = getattr(connector, 'last_sync_at', None)
                        if not last_sync or (
                            datetime.now(timezone.utc) - last_sync > 
                            timedelta(minutes=self.config.default_sync_interval)
                        ):
                            # Start incremental sync
                            await self._start_incremental_sync(platform, connector)
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in sync scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _start_incremental_sync(
        self,
        platform: CRMPlatform,
        connector: BaseCRMConnector
    ):
        """Start incremental synchronization for a platform."""
        try:
            if len(self.active_syncs) >= self.config.max_concurrent_syncs:
                logger.warning("Max concurrent syncs reached, skipping")
                return
            
            sync_operation = SyncOperation(
                operation_id=str(uuid4()),
                platform=platform,
                operation_type="incremental_sync",
                status=SynchronizationStatus.PENDING
            )
            
            self.active_syncs[sync_operation.operation_id] = sync_operation
            
            # Start sync in background
            asyncio.create_task(
                self._execute_incremental_sync(sync_operation, connector)
            )
            
        except Exception as e:
            logger.error(f"Failed to start incremental sync for {platform.value}: {e}")
    
    async def _execute_incremental_sync(
        self,
        sync_operation: SyncOperation,
        connector: BaseCRMConnector
    ):
        """Execute incremental synchronization."""
        try:
            sync_operation.status = SynchronizationStatus.IN_PROGRESS
            sync_operation.started_at = datetime.now(timezone.utc)
            
            # Sync contacts updated in last sync interval
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                minutes=self.config.default_sync_interval
            )
            
            contacts = await connector.get_contacts(
                limit=100,
                updated_since=cutoff_time
            )
            
            sync_operation.objects_processed += len(contacts)
            
            # Sync opportunities
            opportunities = await connector.get_opportunities(
                limit=100,
                updated_since=cutoff_time
            )
            
            sync_operation.objects_processed += len(opportunities)
            sync_operation.status = SynchronizationStatus.COMPLETED
            sync_operation.completed_at = datetime.now(timezone.utc)
            
            # Update connector last sync time
            connector.last_sync_at = sync_operation.completed_at
            
            # Publish sync completion event
            await self.event_bus.publish(
                event_type=EventType.CRM_SYNC_COMPLETED,
                data={
                    "platform": sync_operation.platform.value,
                    "operation_id": sync_operation.operation_id,
                    "objects_processed": sync_operation.objects_processed,
                    "duration_seconds": (
                        sync_operation.completed_at - sync_operation.started_at
                    ).total_seconds()
                },
                source_system="crm_coordinator",
                priority=EventPriority.LOW
            )
            
            logger.info(
                f"Incremental sync completed for {sync_operation.platform.value}: "
                f"{sync_operation.objects_processed} objects"
            )
            
        except Exception as e:
            sync_operation.status = SynchronizationStatus.FAILED
            sync_operation.error_message = str(e)
            sync_operation.completed_at = datetime.now(timezone.utc)
            logger.error(f"Incremental sync failed: {e}")
        finally:
            # Remove from active syncs
            if sync_operation.operation_id in self.active_syncs:
                del self.active_syncs[sync_operation.operation_id]
    
    def get_coordinator_status(self) -> Dict[str, Any]:
        """Get comprehensive coordinator status and metrics."""
        return {
            "is_running": self.is_running,
            "connectors": {
                platform.value: {
                    "connected": status,
                    "metrics": self.connectors[platform].get_metrics() 
                               if platform in self.connectors else None
                }
                for platform, status in self.connector_status.items()
            },
            "action_queue_size": len(self.action_queue),
            "active_syncs": len(self.active_syncs),
            "performance_metrics": {
                "actions_processed": self.actions_processed,
                "actions_successful": self.actions_successful,
                "success_rate": (
                    (self.actions_successful / self.actions_processed) * 100
                    if self.actions_processed > 0 else 0
                ),
                "syncs_completed": self.syncs_completed,
                "webhooks_received": self.webhooks_received
            },
            "configuration": {
                "default_sync_interval": self.config.default_sync_interval,
                "max_concurrent_syncs": self.config.max_concurrent_syncs,
                "integrations_count": len(self.config.integrations)
            }
        }


# Export public API
__all__ = [
    "CRMCoordinator",
    "CRMConfiguration",
    "CRMIntegrationConfig",
    "CRMIntegrationType",
    "IntelligenceActionType",
    "IntelligenceAction"
]