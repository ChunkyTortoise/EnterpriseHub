"""
Event Handlers for Customer Intelligence Platform.

Handles events across all three development tracks:
- Track 1: AI Features (multimodal, workflow, memory)
- Track 2: Enterprise Integrations (CRM, auth, audit)
- Track 3: Advanced Analytics (scoring, journeys, segments)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from .event_bus import Event, EventType, EventBus, customer_event_handler, analytics_event_handler

logger = logging.getLogger(__name__)

class CustomerIntelligenceEventHandlers:
    """Core event handlers for the Customer Intelligence Platform."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.metrics = {
            "events_processed": 0,
            "last_processed": None,
            "errors": 0
        }

    async def setup_handlers(self) -> None:
        """Set up all event handlers with the event bus."""

        # Track 1: AI Features Event Handlers
        await self.event_bus.subscribe(
            event_types=[
                EventType.AI_MULTIMODAL_ANALYZED,
                EventType.AI_WORKFLOW_EXECUTED,
                EventType.AI_MEMORY_UPDATED
            ],
            handler=self.handle_ai_events,
            consumer_group="ai_features",
            consumer_name="ai_processor"
        )

        # Track 2: Enterprise Integration Event Handlers
        await self.event_bus.subscribe(
            event_types=[
                EventType.CRM_CONTACT_SYNCED,
                EventType.CRM_DEAL_UPDATED,
                EventType.AUTH_SESSION_CREATED,
                EventType.SSO_LOGIN_COMPLETED
            ],
            handler=self.handle_enterprise_events,
            consumer_group="enterprise_integrations",
            consumer_name="integration_processor"
        )

        # Track 3: Analytics Event Handlers
        await self.event_bus.subscribe(
            event_types=[
                EventType.ANALYTICS_EVENT_PROCESSED,
                EventType.ANALYTICS_SEGMENT_CHANGED,
                EventType.ANALYTICS_JOURNEY_PREDICTED,
                EventType.LEAD_SCORED
            ],
            handler=self.handle_analytics_events,
            consumer_group="analytics_engine",
            consumer_name="analytics_processor"
        )

        # Core Platform Event Handlers
        await self.event_bus.subscribe(
            event_types=[
                EventType.CUSTOMER_CREATED,
                EventType.CUSTOMER_UPDATED,
                EventType.CONVERSATION_STARTED,
                EventType.CONVERSATION_MESSAGE_SENT
            ],
            handler=self.handle_core_events,
            consumer_group="core_platform",
            consumer_name="core_processor"
        )

        logger.info("Event handlers registered successfully")

    # Track 1: AI Features Event Handlers
    async def handle_ai_events(self, event: Event) -> None:
        """Handle AI-related events from Track 1."""
        try:
            if event.event_type == EventType.AI_MULTIMODAL_ANALYZED:
                await self._handle_multimodal_analyzed(event)
            elif event.event_type == EventType.AI_WORKFLOW_EXECUTED:
                await self._handle_workflow_executed(event)
            elif event.event_type == EventType.AI_MEMORY_UPDATED:
                await self._handle_memory_updated(event)

            self._update_metrics()

        except Exception as e:
            logger.error(f"Error handling AI event {event.event_id}: {e}")
            self.metrics["errors"] += 1

    async def _handle_multimodal_analyzed(self, event: Event) -> None:
        """Handle multimodal analysis completion."""
        customer_id = event.payload.get("customer_id")
        analysis_results = event.payload.get("analysis_results", {})

        logger.info(f"Multimodal analysis completed for customer {customer_id}")

        # Trigger follow-up actions based on analysis
        if analysis_results.get("requires_human_review"):
            await self.event_bus.publish(
                EventType.CUSTOMER_UPDATED,
                {
                    "customer_id": customer_id,
                    "requires_review": True,
                    "analysis_id": event.payload.get("analysis_id")
                },
                correlation_id=event.correlation_id
            )

        # Update customer intelligence score
        if analysis_results.get("intelligence_score"):
            await self.event_bus.publish(
                EventType.LEAD_SCORED,
                {
                    "customer_id": customer_id,
                    "score_type": "intelligence",
                    "score": analysis_results["intelligence_score"],
                    "source": "multimodal_analysis"
                },
                correlation_id=event.correlation_id
            )

    async def _handle_workflow_executed(self, event: Event) -> None:
        """Handle workflow execution completion."""
        workflow_id = event.payload.get("workflow_id")
        customer_id = event.payload.get("customer_id")
        execution_result = event.payload.get("result")

        logger.info(f"Workflow {workflow_id} executed for customer {customer_id}")

        # Log workflow metrics for analytics
        await self.event_bus.publish(
            EventType.ANALYTICS_EVENT_PROCESSED,
            {
                "event_category": "workflow",
                "customer_id": customer_id,
                "workflow_id": workflow_id,
                "execution_time": event.payload.get("execution_time"),
                "success": execution_result.get("success", False)
            },
            correlation_id=event.correlation_id
        )

    async def _handle_memory_updated(self, event: Event) -> None:
        """Handle conversation memory updates."""
        customer_id = event.payload.get("customer_id")
        memory_changes = event.payload.get("memory_changes", {})

        # Check if customer segment should be updated based on memory changes
        if memory_changes.get("significant_change"):
            await self.event_bus.publish(
                EventType.ANALYTICS_SEGMENT_CHANGED,
                {
                    "customer_id": customer_id,
                    "trigger": "memory_update",
                    "changes": memory_changes
                },
                correlation_id=event.correlation_id
            )

    # Track 2: Enterprise Integration Event Handlers
    async def handle_enterprise_events(self, event: Event) -> None:
        """Handle enterprise integration events from Track 2."""
        try:
            if event.event_type == EventType.CRM_CONTACT_SYNCED:
                await self._handle_crm_contact_synced(event)
            elif event.event_type == EventType.CRM_DEAL_UPDATED:
                await self._handle_crm_deal_updated(event)
            elif event.event_type == EventType.AUTH_SESSION_CREATED:
                await self._handle_auth_session_created(event)
            elif event.event_type == EventType.SSO_LOGIN_COMPLETED:
                await self._handle_sso_login_completed(event)

            self._update_metrics()

        except Exception as e:
            logger.error(f"Error handling enterprise event {event.event_id}: {e}")
            self.metrics["errors"] += 1

    async def _handle_crm_contact_synced(self, event: Event) -> None:
        """Handle CRM contact synchronization."""
        crm_type = event.payload.get("crm_type")
        contact_id = event.payload.get("contact_id")
        sync_direction = event.payload.get("direction", "bidirectional")

        logger.info(f"CRM contact synced: {contact_id} from {crm_type}")

        # Update customer record with CRM data
        await self.event_bus.publish(
            EventType.CUSTOMER_UPDATED,
            {
                "customer_id": contact_id,
                "crm_sync": {
                    "crm_type": crm_type,
                    "synced_at": datetime.utcnow().isoformat(),
                    "direction": sync_direction
                }
            },
            correlation_id=event.correlation_id
        )

        # Log sync metrics
        await self.event_bus.publish(
            EventType.ANALYTICS_EVENT_PROCESSED,
            {
                "event_category": "crm_sync",
                "crm_type": crm_type,
                "contact_id": contact_id,
                "direction": sync_direction
            },
            correlation_id=event.correlation_id
        )

    async def _handle_crm_deal_updated(self, event: Event) -> None:
        """Handle CRM deal updates."""
        deal_id = event.payload.get("deal_id")
        customer_id = event.payload.get("customer_id")
        deal_stage = event.payload.get("stage")
        deal_value = event.payload.get("value")

        # Update customer intelligence based on deal progression
        if deal_stage in ["closed_won", "proposal", "negotiation"]:
            await self.event_bus.publish(
                EventType.LEAD_SCORED,
                {
                    "customer_id": customer_id,
                    "score_type": "deal_progression",
                    "score": self._calculate_deal_score(deal_stage, deal_value),
                    "source": "crm_deal_update"
                },
                correlation_id=event.correlation_id
            )

    async def _handle_auth_session_created(self, event: Event) -> None:
        """Handle new authentication sessions."""
        user_id = event.payload.get("user_id")
        session_type = event.payload.get("session_type")

        # Log security event
        await self.event_bus.publish(
            EventType.AUDIT_EVENT_LOGGED,
            {
                "action": "session_created",
                "user_id": user_id,
                "session_type": session_type,
                "ip_address": event.payload.get("ip_address"),
                "user_agent": event.payload.get("user_agent")
            },
            correlation_id=event.correlation_id
        )

    async def _handle_sso_login_completed(self, event: Event) -> None:
        """Handle SSO login completions."""
        user_email = event.payload.get("user_email")
        provider = event.payload.get("sso_provider")

        logger.info(f"SSO login completed: {user_email} via {provider}")

        # Update user last login timestamp
        # In production, this would update the database

    # Track 3: Analytics Event Handlers
    @analytics_event_handler
    async def handle_analytics_events(self, event: Event) -> None:
        """Handle analytics events from Track 3."""
        try:
            if event.event_type == EventType.ANALYTICS_EVENT_PROCESSED:
                await self._handle_analytics_processed(event)
            elif event.event_type == EventType.ANALYTICS_SEGMENT_CHANGED:
                await self._handle_segment_changed(event)
            elif event.event_type == EventType.ANALYTICS_JOURNEY_PREDICTED:
                await self._handle_journey_predicted(event)
            elif event.event_type == EventType.LEAD_SCORED:
                await self._handle_lead_scored(event)

            self._update_metrics()

        except Exception as e:
            logger.error(f"Error handling analytics event {event.event_id}: {e}")
            self.metrics["errors"] += 1

    async def _handle_analytics_processed(self, event: Event) -> None:
        """Handle processed analytics events."""
        event_category = event.payload.get("event_category")
        customer_id = event.payload.get("customer_id")

        # Aggregate analytics data
        # In production, this would update analytics dashboards and metrics

    async def _handle_segment_changed(self, event: Event) -> None:
        """Handle customer segment changes."""
        customer_id = event.payload.get("customer_id")
        old_segment = event.payload.get("old_segment")
        new_segment = event.payload.get("new_segment")

        logger.info(f"Customer {customer_id} moved from {old_segment} to {new_segment}")

        # Trigger personalization updates
        await self.event_bus.publish(
            EventType.CUSTOMER_UPDATED,
            {
                "customer_id": customer_id,
                "segment": new_segment,
                "segment_changed_at": datetime.utcnow().isoformat()
            },
            correlation_id=event.correlation_id
        )

    async def _handle_journey_predicted(self, event: Event) -> None:
        """Handle customer journey predictions."""
        customer_id = event.payload.get("customer_id")
        predicted_journey = event.payload.get("predicted_journey")
        confidence = event.payload.get("confidence")

        # Update customer record with journey prediction
        await self.event_bus.publish(
            EventType.CUSTOMER_UPDATED,
            {
                "customer_id": customer_id,
                "journey_prediction": {
                    "predicted_path": predicted_journey,
                    "confidence": confidence,
                    "predicted_at": datetime.utcnow().isoformat()
                }
            },
            correlation_id=event.correlation_id
        )

    async def _handle_lead_scored(self, event: Event) -> None:
        """Handle lead scoring updates."""
        customer_id = event.payload.get("customer_id")
        score_type = event.payload.get("score_type")
        score = event.payload.get("score")

        # Check if score indicates high-value customer
        if score > 0.8 and score_type == "conversion_probability":
            await self.event_bus.publish(
                EventType.CUSTOMER_UPDATED,
                {
                    "customer_id": customer_id,
                    "high_value_customer": True,
                    "priority_level": "high"
                },
                correlation_id=event.correlation_id
            )

    # Core Platform Event Handlers
    @customer_event_handler
    async def handle_core_events(self, event: Event) -> None:
        """Handle core platform events."""
        try:
            if event.event_type == EventType.CUSTOMER_CREATED:
                await self._handle_customer_created(event)
            elif event.event_type == EventType.CUSTOMER_UPDATED:
                await self._handle_customer_updated(event)
            elif event.event_type == EventType.CONVERSATION_STARTED:
                await self._handle_conversation_started(event)
            elif event.event_type == EventType.CONVERSATION_MESSAGE_SENT:
                await self._handle_conversation_message_sent(event)

            self._update_metrics()

        except Exception as e:
            logger.error(f"Error handling core event {event.event_id}: {e}")
            self.metrics["errors"] += 1

    async def _handle_customer_created(self, event: Event) -> None:
        """Handle new customer creation."""
        customer_id = event.payload.get("customer_id")
        customer_data = event.payload.get("customer_data", {})

        logger.info(f"New customer created: {customer_id}")

        # Initialize customer analytics
        await self.event_bus.publish(
            EventType.ANALYTICS_EVENT_PROCESSED,
            {
                "event_category": "customer_lifecycle",
                "customer_id": customer_id,
                "lifecycle_stage": "created",
                "customer_data": customer_data
            },
            correlation_id=event.correlation_id
        )

        # Trigger initial lead scoring
        await self.event_bus.publish(
            EventType.LEAD_SCORED,
            {
                "customer_id": customer_id,
                "score_type": "initial",
                "score": 0.5,  # Default initial score
                "source": "customer_creation"
            },
            correlation_id=event.correlation_id
        )

    async def _handle_customer_updated(self, event: Event) -> None:
        """Handle customer updates."""
        customer_id = event.payload.get("customer_id")
        changes = event.payload.get("changes", {})

        # Check if significant changes warrant re-scoring
        significant_fields = ["company", "industry", "budget", "requirements"]
        if any(field in changes for field in significant_fields):
            await self.event_bus.publish(
                EventType.LEAD_SCORED,
                {
                    "customer_id": customer_id,
                    "score_type": "profile_update",
                    "score": 0.7,  # Higher score for profile completion
                    "source": "customer_update"
                },
                correlation_id=event.correlation_id
            )

    async def _handle_conversation_started(self, event: Event) -> None:
        """Handle conversation start."""
        customer_id = event.payload.get("customer_id")
        conversation_id = event.payload.get("conversation_id")

        # Log conversation analytics
        await self.event_bus.publish(
            EventType.ANALYTICS_EVENT_PROCESSED,
            {
                "event_category": "conversation",
                "customer_id": customer_id,
                "conversation_id": conversation_id,
                "action": "started"
            },
            correlation_id=event.correlation_id
        )

    async def _handle_conversation_message_sent(self, event: Event) -> None:
        """Handle conversation messages."""
        customer_id = event.payload.get("customer_id")
        message_type = event.payload.get("message_type")
        engagement_score = event.payload.get("engagement_score")

        # Update customer engagement based on message interaction
        if engagement_score and engagement_score > 80:
            await self.event_bus.publish(
                EventType.ANALYTICS_SEGMENT_CHANGED,
                {
                    "customer_id": customer_id,
                    "trigger": "high_engagement",
                    "engagement_score": engagement_score
                },
                correlation_id=event.correlation_id
            )

    # Utility methods
    def _calculate_deal_score(self, stage: str, value: float) -> float:
        """Calculate deal progression score."""
        stage_multipliers = {
            "lead": 0.2,
            "qualified": 0.4,
            "proposal": 0.6,
            "negotiation": 0.8,
            "closed_won": 1.0,
            "closed_lost": 0.0
        }

        base_score = stage_multipliers.get(stage, 0.3)

        # Adjust score based on deal value
        if value:
            if value > 100000:
                base_score += 0.2
            elif value > 50000:
                base_score += 0.1

        return min(1.0, base_score)

    def _update_metrics(self) -> None:
        """Update handler metrics."""
        self.metrics["events_processed"] += 1
        self.metrics["last_processed"] = datetime.utcnow()

    async def get_metrics(self) -> Dict[str, Any]:
        """Get event handler metrics."""
        return {
            **self.metrics,
            "last_processed": self.metrics["last_processed"].isoformat() if self.metrics["last_processed"] else None
        }

# Factory function to set up event handlers
async def setup_event_handlers(event_bus: EventBus) -> CustomerIntelligenceEventHandlers:
    """Set up and configure all event handlers."""
    handlers = CustomerIntelligenceEventHandlers(event_bus)
    await handlers.setup_handlers()
    return handlers