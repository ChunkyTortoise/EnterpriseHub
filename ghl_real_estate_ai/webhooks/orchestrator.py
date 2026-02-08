"""
Jorge's Real Estate AI Platform - Webhook Orchestration System
Central webhook management for real-time integrations and event processing

This module provides:
- Centralized webhook processing and routing
- Real-time event handling and distribution
- Cross-system synchronization automation
- Intelligent event correlation and deduplication
- Secure webhook validation and authentication
- Jorge-specific business rule execution
"""

import asyncio
import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import aiohttp
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..ghl_utils.jorge_config import JorgeConfig
from ..services.cache_service import CacheService
from ..services.claude_assistant import ClaudeAssistant
from .cascade_manager import CrossSystemCascadeManager
from .event_router import WebhookEventRouter
from .signature_validator import WebhookSignatureValidator

logger = logging.getLogger(__name__)


class WebhookSource(Enum):
    """Webhook source systems"""

    MLS_BRIGHT = "mls_bright"
    MLS_CALIFORNIA = "mls_california"
    CRM_CHIME = "crm_chime"
    CRM_TOP_PRODUCER = "crm_top_producer"
    MARKETING_MAILCHIMP = "marketing_mailchimp"
    MARKETING_FACEBOOK = "marketing_facebook"
    FINANCIAL_LENDING = "financial_lending"
    SERVICE_PROVIDERS = "service_providers"
    GHL_PLATFORM = "ghl_platform"
    JORGE_SYSTEM = "jorge_system"


class EventType(Enum):
    """Webhook event types"""

    PROPERTY_LISTING_NEW = "property.listing.new"
    PROPERTY_LISTING_UPDATED = "property.listing.updated"
    PROPERTY_STATUS_CHANGE = "property.status.change"
    PROPERTY_PRICE_CHANGE = "property.price.change"

    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    LEAD_STATUS_CHANGE = "lead.status.change"
    LEAD_TEMPERATURE_CHANGE = "lead.temperature.change"

    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_MESSAGE = "conversation.message"
    CONVERSATION_ENDED = "conversation.ended"

    CAMPAIGN_LAUNCHED = "campaign.launched"
    CAMPAIGN_ENGAGEMENT = "campaign.engagement"
    CAMPAIGN_CONVERSION = "campaign.conversion"

    LOAN_APPLICATION = "loan.application"
    LOAN_STATUS_UPDATE = "loan.status.update"

    SERVICE_SCHEDULED = "service.scheduled"
    SERVICE_COMPLETED = "service.completed"

    SYSTEM_ALERT = "system.alert"
    BOT_ESCALATION = "bot.escalation"


@dataclass
class WebhookEvent:
    """Webhook event structure"""

    event_id: str
    source: WebhookSource
    event_type: EventType
    timestamp: datetime
    payload: Dict[str, Any]
    signature: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    processed: bool = False
    correlation_id: Optional[str] = None
    priority: int = 5  # 1-10, 1 being highest priority


@dataclass
class ProcessingResult:
    """Webhook processing result"""

    success: bool
    event_id: str
    processing_time: float
    actions_triggered: List[str]
    systems_updated: List[str]
    errors: List[str] = field(default_factory=list)
    correlation_events: List[str] = field(default_factory=list)


@dataclass
class OrchestrationRule:
    """Business rule for webhook orchestration"""

    rule_id: str
    name: str
    description: str
    event_pattern: Dict[str, Any]  # JSON pattern to match events
    actions: List[Dict[str, Any]]  # Actions to execute
    conditions: List[str] = field(default_factory=list)  # Additional conditions
    priority: int = 5
    enabled: bool = True
    jorge_specific: bool = False


class WebhookOrchestrator:
    """
    Central webhook orchestration system for Jorge's integrated platform
    Manages real-time event processing and cross-system automation
    """

    def __init__(self):
        self.config = JorgeConfig()
        self.claude = ClaudeAssistant()
        self.cache = CacheService()
        self.event_router = WebhookEventRouter()
        self.signature_validator = WebhookSignatureValidator()
        self.cascade_manager = CrossSystemCascadeManager()

        # Event processing
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.orchestration_rules: List[OrchestrationRule] = []
        self.event_queue = asyncio.Queue()
        self.processing_tasks: Set[asyncio.Task] = set()

        # Deduplication and correlation
        self.recent_events: Dict[str, WebhookEvent] = {}
        self.event_correlations: Dict[str, List[str]] = {}

        # Performance monitoring
        self.processing_metrics = {
            "events_processed": 0,
            "processing_errors": 0,
            "average_processing_time": 0.0,
            "last_processing_time": datetime.now(),
        }

        # Jorge-specific business rules
        self.jorge_rules = self._initialize_jorge_rules()

    async def initialize(self):
        """Initialize webhook orchestrator and processing systems"""
        try:
            logger.info("Initializing Webhook Orchestrator")

            # Initialize components
            await self.event_router.initialize()
            await self.signature_validator.initialize()
            await self.cascade_manager.initialize()

            # Load orchestration rules
            await self._load_orchestration_rules()

            # Start event processing workers
            for i in range(5):  # 5 processing workers
                task = asyncio.create_task(self._event_processing_worker(i))
                self.processing_tasks.add(task)

            # Start background maintenance
            asyncio.create_task(self._background_maintenance())

            logger.info("Webhook Orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Webhook Orchestrator: {str(e)}")
            raise

    async def process_webhook_event(
        self,
        source: str,
        event_type: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        signature: Optional[str] = None,
    ) -> ProcessingResult:
        """
        Process incoming webhook event with intelligent routing and orchestration

        Args:
            source: Event source system
            event_type: Type of webhook event
            payload: Event payload data
            headers: HTTP headers from webhook request
            signature: Webhook signature for validation

        Returns:
            ProcessingResult: Processing results and actions taken
        """
        try:
            # Generate event ID
            import uuid

            event_id = uuid.uuid4().hex

            logger.info(f"Processing webhook event: {event_id} from {source}")

            # Validate webhook signature
            if signature:
                is_valid = await self.signature_validator.validate_signature(source, payload, signature, headers or {})
                if not is_valid:
                    raise HTTPException(status_code=401, detail="Invalid webhook signature")

            # Create webhook event
            webhook_event = WebhookEvent(
                event_id=event_id,
                source=WebhookSource(source),
                event_type=EventType(event_type),
                timestamp=datetime.now(),
                payload=payload,
                signature=signature,
                headers=headers or {},
            )

            # Check for event deduplication
            dedup_key = self._generate_deduplication_key(webhook_event)
            if await self._is_duplicate_event(dedup_key, webhook_event):
                logger.info(f"Duplicate event detected, skipping: {event_id}")
                return ProcessingResult(
                    success=True,
                    event_id=event_id,
                    processing_time=0.0,
                    actions_triggered=["deduplication_skip"],
                    systems_updated=[],
                )

            # Add to processing queue
            await self.event_queue.put(webhook_event)

            # Store for deduplication
            self.recent_events[dedup_key] = webhook_event

            logger.info(f"Webhook event queued for processing: {event_id}")

            # For synchronous processing requirements, wait for result
            return ProcessingResult(
                success=True,
                event_id=event_id,
                processing_time=0.0,
                actions_triggered=["queued_for_processing"],
                systems_updated=[],
            )

        except Exception as e:
            logger.error(f"Webhook event processing failed: {str(e)}")
            raise

    async def orchestrate_cross_system_updates(self, primary_event: WebhookEvent) -> Dict[str, Any]:
        """
        Orchestrate cascading updates across integrated systems

        Args:
            primary_event: Primary webhook event that triggers cascade

        Returns:
            Dict containing orchestration results
        """
        try:
            logger.info(f"Orchestrating cross-system updates for event: {primary_event.event_id}")

            # Determine dependent systems and actions
            cascade_plan = await self.cascade_manager.create_cascade_plan(primary_event)

            # Execute cascade plan
            cascade_result = await self.cascade_manager.execute_cascade(primary_event, cascade_plan)

            # Apply Jorge-specific business rules
            jorge_actions = await self._apply_jorge_business_rules(primary_event, cascade_result)

            # Update correlation tracking
            await self._update_event_correlations(primary_event, cascade_result)

            orchestration_result = {
                "primary_event_id": primary_event.event_id,
                "cascade_plan": cascade_plan,
                "cascade_results": cascade_result,
                "jorge_actions": jorge_actions,
                "systems_affected": cascade_result.get("systems_updated", []),
                "processing_time": cascade_result.get("processing_time", 0.0),
                "success": cascade_result.get("success", False),
            }

            logger.info(f"Cross-system orchestration completed for {primary_event.event_id}")
            return orchestration_result

        except Exception as e:
            logger.error(f"Cross-system orchestration failed: {str(e)}")
            raise

    async def register_event_handler(self, event_type: EventType, handler: Callable[[WebhookEvent], Any]):
        """Register custom event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for {event_type.value}")

    async def add_orchestration_rule(self, rule: OrchestrationRule):
        """Add custom orchestration rule"""
        self.orchestration_rules.append(rule)

        # Sort by priority (lower number = higher priority)
        self.orchestration_rules.sort(key=lambda r: r.priority)

        logger.info(f"Added orchestration rule: {rule.name}")

    async def get_processing_metrics(self) -> Dict[str, Any]:
        """Get webhook processing performance metrics"""
        return {
            **self.processing_metrics,
            "queue_size": self.event_queue.qsize(),
            "active_workers": len(self.processing_tasks),
            "recent_events_count": len(self.recent_events),
            "correlation_tracking": len(self.event_correlations),
        }

    async def _event_processing_worker(self, worker_id: int):
        """Background worker for processing webhook events"""
        try:
            logger.info(f"Starting webhook processing worker {worker_id}")

            while True:
                try:
                    # Get next event from queue
                    event = await self.event_queue.get()
                    start_time = datetime.now()

                    # Process the event
                    result = await self._process_single_event(event)

                    # Update metrics
                    processing_time = (datetime.now() - start_time).total_seconds()
                    await self._update_processing_metrics(processing_time, result.success)

                    # Mark task as done
                    self.event_queue.task_done()

                    logger.debug(f"Worker {worker_id} processed event {event.event_id} in {processing_time:.2f}s")

                except asyncio.CancelledError:
                    logger.info(f"Processing worker {worker_id} cancelled")
                    break
                except Exception as e:
                    logger.error(f"Processing worker {worker_id} error: {str(e)}")
                    # Continue processing other events

        except Exception as e:
            logger.error(f"Processing worker {worker_id} failed: {str(e)}")

    async def _process_single_event(self, event: WebhookEvent) -> ProcessingResult:
        """Process a single webhook event"""
        try:
            start_time = datetime.now()
            actions_triggered = []
            systems_updated = []
            errors = []

            # Route event to appropriate handlers
            routing_result = await self.event_router.route_event(event)
            actions_triggered.extend(routing_result.get("actions", []))
            systems_updated.extend(routing_result.get("systems", []))

            # Execute registered event handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        await handler(event)
                        actions_triggered.append(f"handler_{handler.__name__}")
                    except Exception as e:
                        error_msg = f"Handler {handler.__name__} failed: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            # Apply orchestration rules
            rule_results = await self._apply_orchestration_rules(event)
            actions_triggered.extend(rule_results.get("actions", []))
            systems_updated.extend(rule_results.get("systems", []))

            # Execute cross-system orchestration if needed
            if self._should_orchestrate_cascade(event):
                cascade_result = await self.orchestrate_cross_system_updates(event)
                if cascade_result["success"]:
                    systems_updated.extend(cascade_result.get("systems_affected", []))
                    actions_triggered.append("cross_system_cascade")

            # Mark event as processed
            event.processed = True

            processing_time = (datetime.now() - start_time).total_seconds()

            return ProcessingResult(
                success=len(errors) == 0,
                event_id=event.event_id,
                processing_time=processing_time,
                actions_triggered=actions_triggered,
                systems_updated=list(set(systems_updated)),
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Single event processing failed for {event.event_id}: {str(e)}")
            return ProcessingResult(
                success=False,
                event_id=event.event_id,
                processing_time=0.0,
                actions_triggered=[],
                systems_updated=[],
                errors=[str(e)],
            )

    async def _apply_orchestration_rules(self, event: WebhookEvent) -> Dict[str, Any]:
        """Apply orchestration rules to webhook event"""
        try:
            actions_triggered = []
            systems_updated = []

            for rule in self.orchestration_rules:
                if not rule.enabled:
                    continue

                # Check if rule matches event
                if await self._rule_matches_event(rule, event):
                    logger.info(f"Applying orchestration rule: {rule.name}")

                    # Execute rule actions
                    for action in rule.actions:
                        try:
                            action_result = await self._execute_rule_action(action, event)
                            actions_triggered.append(f"rule_{rule.rule_id}")
                            systems_updated.extend(action_result.get("systems", []))

                        except Exception as e:
                            logger.error(f"Rule action failed for {rule.name}: {str(e)}")

            return {"actions": actions_triggered, "systems": systems_updated}

        except Exception as e:
            logger.error(f"Orchestration rules application failed: {str(e)}")
            return {"actions": [], "systems": []}

    async def _apply_jorge_business_rules(self, event: WebhookEvent, cascade_result: Dict[str, Any]) -> List[str]:
        """Apply Jorge-specific business rules"""
        try:
            jorge_actions = []

            # Hot lead alert rule
            if event.event_type == EventType.LEAD_TEMPERATURE_CHANGE:
                temperature = event.payload.get("temperature", 0)
                if temperature >= 75:  # Hot lead threshold
                    jorge_actions.append("hot_lead_alert_sent")
                    await self._send_hot_lead_alert(event)

            # Property price drop opportunity
            if event.event_type == EventType.PROPERTY_PRICE_CHANGE:
                price_change = event.payload.get("price_change_percent", 0)
                if price_change <= -5:  # 5% price drop
                    jorge_actions.append("price_drop_opportunity_identified")
                    await self._identify_price_drop_opportunity(event)

            # Commission optimization
            if event.event_type in [EventType.LEAD_CREATED, EventType.LEAD_UPDATED]:
                jorge_actions.extend(await self._optimize_commission_opportunity(event))

            # Market intelligence updates
            if event.source.value.startswith("mls_"):
                jorge_actions.extend(await self._update_market_intelligence(event))

            return jorge_actions

        except Exception as e:
            logger.error(f"Jorge business rules application failed: {str(e)}")
            return []

    def _initialize_jorge_rules(self) -> List[OrchestrationRule]:
        """Initialize Jorge-specific orchestration rules"""
        rules = []

        # Hot lead immediate response rule
        rules.append(
            OrchestrationRule(
                rule_id="jorge_hot_lead_response",
                name="Jorge Hot Lead Immediate Response",
                description="Immediate response system for hot leads (75%+ temperature)",
                event_pattern={"event_type": "lead.temperature.change", "payload.temperature": {"$gte": 75}},
                actions=[
                    {
                        "type": "notification",
                        "method": "push_sms_email",
                        "priority": "urgent",
                        "template": "hot_lead_alert",
                    },
                    {"type": "bot_escalation", "bot": "jorge_seller_bot", "priority": "immediate"},
                ],
                priority=1,
                jorge_specific=True,
            )
        )

        # Property opportunity identification
        rules.append(
            OrchestrationRule(
                rule_id="jorge_property_opportunity",
                name="Jorge Property Investment Opportunity",
                description="Identify undervalued properties and investment opportunities",
                event_pattern={"event_type": "property.price.change", "payload.price_change_percent": {"$lte": -10}},
                actions=[
                    {"type": "opportunity_analysis", "method": "ml_investment_scoring", "notify_jorge": True},
                    {"type": "client_matching", "criteria": "investment_properties"},
                ],
                priority=2,
                jorge_specific=True,
            )
        )

        # Commission optimization rule
        rules.append(
            OrchestrationRule(
                rule_id="jorge_commission_optimization",
                name="Jorge Commission Optimization",
                description="Optimize commission potential through strategic actions",
                event_pattern={"event_type": "lead.created", "payload.estimated_property_value": {"$gte": 300000}},
                actions=[
                    {"type": "strategic_analysis", "method": "commission_optimization", "calculate_6_percent": True},
                    {"type": "market_positioning", "method": "competitive_analysis"},
                ],
                priority=3,
                jorge_specific=True,
            )
        )

        return rules

    def _generate_deduplication_key(self, event: WebhookEvent) -> str:
        """Generate deduplication key for event"""
        key_data = f"{event.source.value}_{event.event_type.value}_{event.timestamp.isoformat()}"

        # Add payload-specific identifiers
        if "property_id" in event.payload:
            key_data += f"_{event.payload['property_id']}"
        elif "lead_id" in event.payload:
            key_data += f"_{event.payload['lead_id']}"
        elif "contact_id" in event.payload:
            key_data += f"_{event.payload['contact_id']}"

        return hashlib.md5(key_data.encode()).hexdigest()

    async def _is_duplicate_event(self, dedup_key: str, event: WebhookEvent) -> bool:
        """Check if event is duplicate within deduplication window"""
        if dedup_key not in self.recent_events:
            return False

        existing_event = self.recent_events[dedup_key]
        time_diff = (event.timestamp - existing_event.timestamp).total_seconds()

        # 5-minute deduplication window
        return time_diff < 300

    async def _background_maintenance(self):
        """Background maintenance tasks"""
        try:
            while True:
                # Wait 10 minutes between maintenance cycles
                await asyncio.sleep(10 * 60)

                try:
                    # Clean up old events (keep only last 2 hours)
                    cutoff_time = datetime.now() - timedelta(hours=2)
                    keys_to_remove = []

                    for key, event in self.recent_events.items():
                        if event.timestamp < cutoff_time:
                            keys_to_remove.append(key)

                    for key in keys_to_remove:
                        del self.recent_events[key]

                    # Clean up old correlations
                    correlation_keys_to_remove = []
                    for key, events in self.event_correlations.items():
                        if len(events) == 0:
                            correlation_keys_to_remove.append(key)

                    for key in correlation_keys_to_remove:
                        del self.event_correlations[key]

                    logger.debug(
                        f"Maintenance: Cleaned {len(keys_to_remove)} old events, "
                        f"{len(correlation_keys_to_remove)} empty correlations"
                    )

                except Exception as e:
                    logger.error(f"Background maintenance error: {str(e)}")

        except asyncio.CancelledError:
            logger.info("Background maintenance cancelled")

    async def cleanup(self):
        """Clean up webhook orchestrator resources"""
        try:
            # Cancel processing tasks
            for task in self.processing_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self.processing_tasks:
                await asyncio.gather(*self.processing_tasks, return_exceptions=True)

            # Cleanup components
            await self.event_router.cleanup()
            await self.cascade_manager.cleanup()

            logger.info("Webhook Orchestrator cleanup completed")

        except Exception as e:
            logger.error(f"Webhook Orchestrator cleanup failed: {str(e)}")

    # Additional helper methods would be implemented here...
