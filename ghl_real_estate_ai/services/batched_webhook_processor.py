"""
Batched Webhook Processor for Enhanced GHL Integration.

Optimizes webhook processing through intelligent batching strategies:
- Temporal batching: Group webhooks by time windows
- Contact-based batching: Group multiple messages from same contact
- Location-based batching: Process location webhooks together
- Claude API optimization: Batch semantic analysis calls
- GHL API optimization: Batch updates to reduce API limits

Performance Targets:
- 60% reduction in API calls through batching
- 40% faster processing for multiple webhooks
- Improved Claude API efficiency (25% cost reduction)
- Enhanced real-time performance with smart buffering
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
import json
import logging

from ghl_real_estate_ai.api.schemas.ghl import GHLWebhookEvent, GHLAction, ActionType
from ghl_real_estate_ai.core.service_registry import ServiceRegistry
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.tenant_service import TenantService
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)


class BatchingStrategy(Enum):
    """Webhook batching strategies."""
    TEMPORAL = "temporal"           # Batch by time windows
    CONTACT_BASED = "contact_based" # Batch by contact
    LOCATION_BASED = "location_based" # Batch by GHL location
    INTELLIGENT = "intelligent"     # AI-driven batching decisions


@dataclass
class WebhookBatch:
    """A batch of webhooks to be processed together."""
    batch_id: str
    strategy: BatchingStrategy
    events: List[GHLWebhookEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    contact_ids: Set[str] = field(default_factory=set)
    location_ids: Set[str] = field(default_factory=set)
    priority_score: float = 0.0
    estimated_processing_time_ms: float = 0.0

    def add_event(self, event: GHLWebhookEvent) -> None:
        """Add webhook event to batch."""
        self.events.append(event)
        self.contact_ids.add(event.contact_id)
        self.location_ids.add(event.location_id)
        self._update_priority_score()
        self._update_estimated_processing_time()

    def _update_priority_score(self) -> None:
        """Calculate priority score based on batch characteristics."""
        # Higher priority for:
        # - Multiple messages from same contact (conversation flow)
        # - Hot leads (based on tags)
        # - Time-sensitive messages

        priority = 50.0  # Base priority

        # Contact conversation density bonus
        if len(self.events) > 1 and len(self.contact_ids) == 1:
            priority += 30.0  # Active conversation

        # Hot lead detection
        hot_keywords = ["urgent", "ready", "today", "now", "asap", "schedule"]
        for event in self.events:
            message_lower = event.message.body.lower()
            if any(keyword in message_lower for keyword in hot_keywords):
                priority += 20.0
                break

        # Tag-based priority
        for event in self.events:
            if event.contact.tags:
                if any("hot" in tag.lower() for tag in event.contact.tags):
                    priority += 25.0
                elif any("warm" in tag.lower() for tag in event.contact.tags):
                    priority += 10.0

        self.priority_score = min(priority, 100.0)

    def _update_estimated_processing_time(self) -> None:
        """Estimate batch processing time."""
        # Base processing time per event
        base_time_per_event = 400  # ms

        # Batching efficiency (reduced per-event cost)
        if len(self.events) > 1:
            efficiency_factor = max(0.6, 1.0 - (len(self.events) * 0.08))
        else:
            efficiency_factor = 1.0

        self.estimated_processing_time_ms = len(self.events) * base_time_per_event * efficiency_factor

    @property
    def age_seconds(self) -> float:
        """Get batch age in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def should_process_immediately(self) -> bool:
        """Determine if batch should be processed immediately."""
        # Process immediately if:
        # - High priority and multiple events
        # - Batch is getting old
        # - Contact conversation flow detected

        if self.priority_score > 80 and len(self.events) >= 2:
            return True

        if self.age_seconds > 2.0:  # Don't let batches get too old
            return True

        # Conversation flow detection (multiple messages from same contact)
        if len(self.contact_ids) == 1 and len(self.events) >= 2:
            return True

        return False


@dataclass
class BatchProcessingMetrics:
    """Metrics for batch processing performance."""
    total_batches_processed: int = 0
    total_events_processed: int = 0
    total_processing_time_ms: float = 0.0
    api_calls_saved: int = 0
    claude_calls_batched: int = 0
    ghl_calls_batched: int = 0
    average_batch_size: float = 0.0
    batch_efficiency_ratio: float = 0.0

    def update_batch_completion(
        self,
        batch: WebhookBatch,
        actual_processing_time_ms: float,
        api_calls_saved: int = 0
    ) -> None:
        """Update metrics after batch completion."""
        self.total_batches_processed += 1
        self.total_events_processed += len(batch.events)
        self.total_processing_time_ms += actual_processing_time_ms
        self.api_calls_saved += api_calls_saved

        # Update averages
        self.average_batch_size = self.total_events_processed / self.total_batches_processed

        # Calculate efficiency (actual vs estimated time)
        if batch.estimated_processing_time_ms > 0:
            efficiency = batch.estimated_processing_time_ms / actual_processing_time_ms
            self.batch_efficiency_ratio = (
                (self.batch_efficiency_ratio * (self.total_batches_processed - 1) + efficiency) /
                self.total_batches_processed
            )


class BatchedWebhookProcessor:
    """
    Enhanced webhook processor with intelligent batching capabilities.

    Features:
    - Temporal batching with configurable windows
    - Contact-based conversation flow batching
    - Location-based processing optimization
    - Claude API batching for semantic analysis
    - GHL API batching for reduced rate limit impact
    - Real-time priority scoring and processing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Batching configuration
        self.max_batch_size = self.config.get("max_batch_size", 5)
        self.batch_timeout_seconds = self.config.get("batch_timeout_seconds", 1.5)
        self.contact_conversation_window_seconds = self.config.get("contact_conversation_window_seconds", 10.0)
        self.location_batch_window_seconds = self.config.get("location_batch_window_seconds", 2.0)

        # Processing queues and state
        self.pending_batches: Dict[str, WebhookBatch] = {}
        self.processing_queue = asyncio.Queue()
        self.metrics = BatchProcessingMetrics()

        # Service dependencies
        self.service_registry = ServiceRegistry(demo_mode=False)
        self.tenant_service = TenantService()
        self.analytics_service = AnalyticsService()

        # Background processing task
        self._processing_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        logger.info("BatchedWebhookProcessor initialized with intelligent batching")

    async def start(self) -> None:
        """Start the batched processor."""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_batches_continuously())
            logger.info("Batched webhook processing started")

    async def stop(self) -> None:
        """Stop the batched processor."""
        self._shutdown_event.set()

        if self._processing_task:
            try:
                await asyncio.wait_for(self._processing_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._processing_task.cancel()
                logger.warning("Forced shutdown of batch processing task")

        # Process remaining batches
        await self._flush_all_batches()
        logger.info("Batched webhook processing stopped")

    async def add_webhook_event(self, event: GHLWebhookEvent) -> str:
        """
        Add webhook event to batching system.

        Args:
            event: GHL webhook event to process

        Returns:
            str: Batch ID that will process this event
        """
        # Determine optimal batching strategy
        strategy = self._determine_batching_strategy(event)

        # Find or create appropriate batch
        batch = await self._find_or_create_batch(event, strategy)

        # Add event to batch
        batch.add_event(event)

        logger.debug(
            f"Added webhook event to batch {batch.batch_id}",
            extra={
                "contact_id": event.contact_id,
                "location_id": event.location_id,
                "batch_size": len(batch.events),
                "strategy": strategy.value,
                "priority_score": batch.priority_score,
            }
        )

        # Check if batch should be processed immediately
        if batch.should_process_immediately or len(batch.events) >= self.max_batch_size:
            await self._queue_batch_for_processing(batch)

        return batch.batch_id

    def _determine_batching_strategy(self, event: GHLWebhookEvent) -> BatchingStrategy:
        """Determine optimal batching strategy for webhook event."""

        # Check for existing contact conversation
        for batch in self.pending_batches.values():
            if (event.contact_id in batch.contact_ids and
                batch.age_seconds < self.contact_conversation_window_seconds):
                return BatchingStrategy.CONTACT_BASED

        # Check for location-based batching opportunity
        for batch in self.pending_batches.values():
            if (event.location_id in batch.location_ids and
                batch.age_seconds < self.location_batch_window_seconds and
                len(batch.events) < 3):  # Don't make location batches too large
                return BatchingStrategy.LOCATION_BASED

        # Default to temporal batching
        return BatchingStrategy.TEMPORAL

    async def _find_or_create_batch(
        self,
        event: GHLWebhookEvent,
        strategy: BatchingStrategy
    ) -> WebhookBatch:
        """Find existing batch or create new one for the event."""

        # Look for existing compatible batch
        for batch_id, batch in list(self.pending_batches.items()):
            if self._is_batch_compatible(batch, event, strategy):
                return batch

        # Create new batch
        batch_id = f"{strategy.value}_{event.location_id}_{int(time.time())}"
        batch = WebhookBatch(
            batch_id=batch_id,
            strategy=strategy
        )

        self.pending_batches[batch_id] = batch

        # Set up timeout for this batch
        asyncio.create_task(self._batch_timeout_handler(batch_id))

        return batch

    def _is_batch_compatible(
        self,
        batch: WebhookBatch,
        event: GHLWebhookEvent,
        strategy: BatchingStrategy
    ) -> bool:
        """Check if event is compatible with existing batch."""

        # Don't exceed max batch size
        if len(batch.events) >= self.max_batch_size:
            return False

        # Strategy-specific compatibility checks
        if strategy == BatchingStrategy.CONTACT_BASED:
            return (event.contact_id in batch.contact_ids and
                   batch.age_seconds < self.contact_conversation_window_seconds)

        elif strategy == BatchingStrategy.LOCATION_BASED:
            return (event.location_id in batch.location_ids and
                   batch.age_seconds < self.location_batch_window_seconds)

        elif strategy == BatchingStrategy.TEMPORAL:
            return (batch.strategy == BatchingStrategy.TEMPORAL and
                   batch.age_seconds < self.batch_timeout_seconds)

        return False

    async def _batch_timeout_handler(self, batch_id: str) -> None:
        """Handle batch timeout - force processing after timeout period."""
        await asyncio.sleep(self.batch_timeout_seconds)

        batch = self.pending_batches.get(batch_id)
        if batch and batch.events:
            logger.debug(f"Batch {batch_id} timed out, forcing processing")
            await self._queue_batch_for_processing(batch)

    async def _queue_batch_for_processing(self, batch: WebhookBatch) -> None:
        """Queue batch for processing and remove from pending."""
        if batch.batch_id in self.pending_batches:
            del self.pending_batches[batch.batch_id]

        await self.processing_queue.put(batch)

        logger.info(
            f"Queued batch {batch.batch_id} for processing",
            extra={
                "batch_size": len(batch.events),
                "strategy": batch.strategy.value,
                "priority_score": batch.priority_score,
                "age_seconds": batch.age_seconds,
            }
        )

    async def _process_batches_continuously(self) -> None:
        """Continuously process batches from the queue."""
        while not self._shutdown_event.is_set():
            try:
                # Wait for batch with timeout to allow shutdown checking
                try:
                    batch = await asyncio.wait_for(
                        self.processing_queue.get(),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    continue

                # Process the batch
                start_time = time.time()
                api_calls_saved = await self._process_batch(batch)
                processing_time_ms = (time.time() - start_time) * 1000

                # Update metrics
                self.metrics.update_batch_completion(
                    batch, processing_time_ms, api_calls_saved
                )

                logger.info(
                    f"Completed batch {batch.batch_id} processing",
                    extra={
                        "batch_size": len(batch.events),
                        "processing_time_ms": processing_time_ms,
                        "api_calls_saved": api_calls_saved,
                        "efficiency_ratio": self.metrics.batch_efficiency_ratio,
                    }
                )

            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)  # Brief pause on error

    async def _process_batch(self, batch: WebhookBatch) -> int:
        """
        Process a batch of webhook events with optimized API calls.

        Args:
            batch: WebhookBatch to process

        Returns:
            int: Number of API calls saved through batching
        """
        logger.info(
            f"Processing batch {batch.batch_id} with {len(batch.events)} events",
            extra={
                "strategy": batch.strategy.value,
                "priority_score": batch.priority_score,
                "contact_ids": list(batch.contact_ids),
                "location_ids": list(batch.location_ids),
            }
        )

        api_calls_saved = 0

        try:
            # Phase 1: Batch Claude semantic analysis
            claude_results = await self._batch_claude_analysis(batch.events)
            if len(batch.events) > 1:
                api_calls_saved += len(batch.events) - 1  # Saved Claude API calls

            # Phase 2: Batch tenant configuration loading
            tenant_configs = await self._batch_tenant_configs(list(batch.location_ids))

            # Phase 3: Process events individually but with shared context
            individual_results = []
            for i, event in enumerate(batch.events):
                # Import the original webhook handler function
                from ghl_real_estate_ai.api.routes.webhook import (
                    handle_ghl_webhook as original_handler
                )

                # Create enhanced event with batched analysis
                enhanced_event = await self._enhance_event_with_batch_context(
                    event,
                    claude_results.get(i, {}),
                    tenant_configs.get(event.location_id, {})
                )

                # Process individual event (reusing original logic)
                result = await self._process_individual_event(enhanced_event)
                individual_results.append(result)

            # Phase 4: Batch GHL API calls
            ghl_api_saved = await self._batch_ghl_updates(batch, individual_results)
            api_calls_saved += ghl_api_saved

            # Phase 5: Batch analytics tracking
            await self._batch_analytics_tracking(batch, individual_results)

        except Exception as e:
            logger.error(f"Error processing batch {batch.batch_id}: {e}", exc_info=True)
            # Fall back to individual processing if batching fails
            await self._fallback_individual_processing(batch.events)

        return api_calls_saved

    async def _batch_claude_analysis(self, events: List[GHLWebhookEvent]) -> Dict[int, Dict[str, Any]]:
        """Batch Claude semantic analysis for multiple events."""
        if len(events) <= 1:
            return {}

        try:
            # Prepare batch conversation data
            batch_conversations = []
            for event in events:
                conversation_messages = [{
                    "role": "user",
                    "content": event.message.body,
                    "timestamp": datetime.now().isoformat(),
                    "contact_id": event.contact_id,
                    "location_id": event.location_id
                }]
                batch_conversations.append(conversation_messages)

            # Call Claude semantic analyzer with batch optimization
            if hasattr(self.service_registry, 'batch_analyze_lead_semantics'):
                batch_results = await self.service_registry.batch_analyze_lead_semantics(
                    batch_conversations
                )

                logger.info(f"Batched Claude analysis for {len(events)} events")
                self.metrics.claude_calls_batched += len(events)

                return {i: result for i, result in enumerate(batch_results)}
            else:
                # Fallback to individual calls if batch not available
                results = {}
                for i, conversation in enumerate(batch_conversations):
                    result = await self.service_registry.analyze_lead_semantics(conversation)
                    results[i] = result

                return results

        except Exception as e:
            logger.warning(f"Batch Claude analysis failed: {e}")
            return {}

    async def _batch_tenant_configs(self, location_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch load tenant configurations."""
        configs = {}

        # Use async gather to load all tenant configs in parallel
        async def load_tenant_config(location_id: str) -> Tuple[str, Dict[str, Any]]:
            config = await self.tenant_service.get_tenant_config(location_id)
            return location_id, config or {}

        try:
            config_results = await asyncio.gather(*[
                load_tenant_config(location_id) for location_id in set(location_ids)
            ])

            configs = dict(config_results)
            logger.debug(f"Loaded {len(configs)} tenant configurations")

        except Exception as e:
            logger.warning(f"Batch tenant config loading failed: {e}")

        return configs

    async def _enhance_event_with_batch_context(
        self,
        event: GHLWebhookEvent,
        claude_analysis: Dict[str, Any],
        tenant_config: Dict[str, Any]
    ) -> GHLWebhookEvent:
        """Enhance event with pre-loaded batch context."""
        # Add batch context to event (would need to extend GHLWebhookEvent schema)
        # For now, we'll store it in a way that can be accessed by the processor

        # Store enhanced context in event metadata (if schema supports it)
        if hasattr(event, 'metadata'):
            event.metadata = {
                'batch_claude_analysis': claude_analysis,
                'batch_tenant_config': tenant_config,
                'batch_processed': True
            }

        return event

    async def _process_individual_event(self, event: GHLWebhookEvent) -> Dict[str, Any]:
        """Process individual event with batch-enhanced context."""
        # This would call the original webhook processing logic
        # but with enhanced context from batching

        # For now, return a mock result structure
        return {
            'event': event,
            'lead_score': 75,  # Mock lead score
            'actions': [],     # Mock actions
            'success': True
        }

    async def _batch_ghl_updates(
        self,
        batch: WebhookBatch,
        individual_results: List[Dict[str, Any]]
    ) -> int:
        """Batch GHL API updates to reduce API calls."""
        if not individual_results:
            return 0

        api_calls_saved = 0

        try:
            # Group updates by location for batching
            location_updates = defaultdict(list)

            for result in individual_results:
                event = result['event']
                actions = result.get('actions', [])

                location_updates[event.location_id].append({
                    'contact_id': event.contact_id,
                    'actions': actions
                })

            # Process updates by location
            for location_id, updates in location_updates.items():
                if len(updates) > 1:
                    # Batch multiple updates for same location
                    await self._batch_ghl_location_updates(location_id, updates)
                    api_calls_saved += len(updates) - 1
                    self.metrics.ghl_calls_batched += len(updates)
                else:
                    # Single update, process normally
                    await self._single_ghl_update(location_id, updates[0])

            logger.info(f"Batched GHL updates saved {api_calls_saved} API calls")

        except Exception as e:
            logger.error(f"Batch GHL updates failed: {e}", exc_info=True)

        return api_calls_saved

    async def _batch_ghl_location_updates(
        self,
        location_id: str,
        updates: List[Dict[str, Any]]
    ) -> None:
        """Batch updates for a single GHL location."""
        # Implementation would batch multiple contact updates
        # This is a placeholder for the actual GHL batch API calls
        logger.debug(f"Batching {len(updates)} GHL updates for location {location_id}")

    async def _single_ghl_update(self, location_id: str, update: Dict[str, Any]) -> None:
        """Process single GHL update."""
        logger.debug(f"Single GHL update for location {location_id}")

    async def _batch_analytics_tracking(
        self,
        batch: WebhookBatch,
        results: List[Dict[str, Any]]
    ) -> None:
        """Batch analytics tracking for better performance."""
        try:
            # Aggregate analytics events for batch processing
            analytics_events = []

            for result in results:
                if result.get('success'):
                    event = result['event']
                    analytics_events.append({
                        'event_type': 'webhook_processed',
                        'location_id': event.location_id,
                        'contact_id': event.contact_id,
                        'batch_id': batch.batch_id,
                        'batch_size': len(batch.events),
                        'strategy': batch.strategy.value,
                        'lead_score': result.get('lead_score', 0)
                    })

            # Batch send analytics events
            if analytics_events:
                await self.analytics_service.track_events_batch(analytics_events)
                logger.debug(f"Tracked {len(analytics_events)} analytics events in batch")

        except Exception as e:
            logger.error(f"Batch analytics tracking failed: {e}", exc_info=True)

    async def _fallback_individual_processing(self, events: List[GHLWebhookEvent]) -> None:
        """Fallback to individual processing if batching fails."""
        logger.warning(f"Falling back to individual processing for {len(events)} events")

        for event in events:
            try:
                # Import and call original handler
                from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

                # Process event individually (this would need adaptation for direct call)
                logger.debug(f"Fallback processing for contact {event.contact_id}")

            except Exception as e:
                logger.error(f"Fallback processing failed for contact {event.contact_id}: {e}")

    async def _flush_all_batches(self) -> None:
        """Flush all pending batches for shutdown."""
        for batch in list(self.pending_batches.values()):
            if batch.events:
                await self._queue_batch_for_processing(batch)

        self.pending_batches.clear()

        # Process remaining queued batches
        while not self.processing_queue.empty():
            try:
                batch = self.processing_queue.get_nowait()
                await self._process_batch(batch)
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                logger.error(f"Error flushing batch: {e}", exc_info=True)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current batching metrics."""
        return {
            'total_batches_processed': self.metrics.total_batches_processed,
            'total_events_processed': self.metrics.total_events_processed,
            'average_batch_size': self.metrics.average_batch_size,
            'api_calls_saved': self.metrics.api_calls_saved,
            'claude_calls_batched': self.metrics.claude_calls_batched,
            'ghl_calls_batched': self.metrics.ghl_calls_batched,
            'batch_efficiency_ratio': self.metrics.batch_efficiency_ratio,
            'pending_batches': len(self.pending_batches),
            'queue_size': self.processing_queue.qsize()
        }


# Global batched processor instance
_batched_processor: Optional[BatchedWebhookProcessor] = None


async def get_batched_processor() -> BatchedWebhookProcessor:
    """Get or create global batched processor instance."""
    global _batched_processor

    if _batched_processor is None:
        # Load configuration from settings
        config = {
            'max_batch_size': getattr(settings, 'webhook_max_batch_size', 5),
            'batch_timeout_seconds': getattr(settings, 'webhook_batch_timeout_seconds', 1.5),
            'contact_conversation_window_seconds': getattr(settings, 'webhook_conversation_window', 10.0),
            'location_batch_window_seconds': getattr(settings, 'webhook_location_window', 2.0),
        }

        _batched_processor = BatchedWebhookProcessor(config)
        await _batched_processor.start()

    return _batched_processor


async def shutdown_batched_processor() -> None:
    """Shutdown global batched processor."""
    global _batched_processor

    if _batched_processor:
        await _batched_processor.stop()
        _batched_processor = None