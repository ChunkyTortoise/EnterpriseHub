"""
Event Bus Integration - Usage Examples

Demonstrates how to use the Event Bus for real-time lead intelligence processing.

Features Demonstrated:
- Publishing lead events
- Processing with parallel ML inference
- Subscribing to intelligence updates
- WebSocket broadcasting
- Performance monitoring
- Error handling
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from ghl_real_estate_ai.services.event_bus import (
    EventBus,
    EventType,
    EventPriority,
    MLEvent,
    get_event_bus,
    publish_lead_event,
    process_lead_intelligence,
    subscribe_to_intelligence_events
)
from ghl_real_estate_ai.services.optimized_ml_lead_intelligence_engine import (
    OptimizedLeadIntelligence,
    ProcessingPriority
)


# Example 1: Basic Event Publishing
async def example_basic_event_publishing():
    """Example: Publish a basic lead event"""
    print("\n=== Example 1: Basic Event Publishing ===")

    # Get Event Bus instance
    event_bus = await get_event_bus()

    # Publish lead created event
    event_id = await event_bus.publish_event(
        event_type=EventType.LEAD_CREATED,
        tenant_id="tenant_123",
        lead_id="lead_456",
        event_data={
            "contact_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "source": "website_form",
            "budget": 500000,
            "location_preference": "downtown"
        },
        priority=EventPriority.HIGH
    )

    print(f"Event published: {event_id}")

    # Check event status
    status = await event_bus.get_event_status(event_id)
    print(f"Event status: {status}")


# Example 2: Synchronous Lead Processing with ML
async def example_synchronous_processing():
    """Example: Process lead event synchronously with ML inference"""
    print("\n=== Example 2: Synchronous Lead Processing ===")

    # Get Event Bus instance
    event_bus = await get_event_bus()

    # Process lead event with ML inference
    intelligence = await event_bus.process_lead_event(
        lead_id="lead_789",
        tenant_id="tenant_123",
        event_data={
            "contact_name": "Jane Smith",
            "email": "jane@example.com",
            "interactions": [
                {"type": "email_open", "timestamp": "2026-01-10T10:00:00Z"},
                {"type": "property_view", "timestamp": "2026-01-10T10:05:00Z"},
                {"type": "form_submission", "timestamp": "2026-01-10T10:10:00Z"}
            ],
            "budget": 750000,
            "property_preferences": {
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "condo"
            }
        },
        priority=ProcessingPriority.HIGH,
        broadcast=True  # Broadcast to WebSocket subscribers
    )

    if intelligence:
        print(f"Intelligence generated for lead {intelligence.lead_id}")
        print(f"  Processing time: {intelligence.processing_time_ms:.1f}ms")
        print(f"  Cache hit rate: {intelligence.cache_hit_rate:.1%}")
        print(f"  Overall health score: {intelligence.overall_health_score:.2f}")

        if intelligence.lead_score:
            print(f"  Lead score: {intelligence.lead_score.score:.2f} ({intelligence.lead_score.score_tier})")

        if intelligence.churn_prediction:
            print(f"  Churn risk: {intelligence.churn_prediction.risk_level.value}")

        if intelligence.property_matches:
            print(f"  Property matches found: {len(intelligence.property_matches)}")


# Example 3: Event Handler Subscription
async def example_event_subscription():
    """Example: Subscribe to ML event results"""
    print("\n=== Example 3: Event Handler Subscription ===")

    # Define custom event handler
    async def handle_high_score_lead(event: MLEvent, intelligence: OptimizedLeadIntelligence):
        """Custom handler for high-scoring leads"""
        if intelligence.lead_score and intelligence.lead_score.score > 0.7:
            print(f"🔥 High-value lead detected!")
            print(f"   Lead ID: {event.lead_id}")
            print(f"   Score: {intelligence.lead_score.score:.2f}")
            print(f"   Confidence: {intelligence.lead_score.confidence.value}")

            # Could trigger additional actions here:
            # - Send notification to sales team
            # - Update CRM with priority flag
            # - Trigger immediate follow-up workflow

    # Subscribe to lead events
    await subscribe_to_intelligence_events(
        event_types=[EventType.LEAD_CREATED, EventType.LEAD_UPDATED],
        handler=handle_high_score_lead
    )

    print("Subscribed to lead events with custom handler")


# Example 4: Batch Event Processing
async def example_batch_processing():
    """Example: Process multiple lead events in batch"""
    print("\n=== Example 4: Batch Event Processing ===")

    event_bus = await get_event_bus()

    # Process multiple leads
    leads = [
        {
            "lead_id": f"lead_{i}",
            "tenant_id": "tenant_123",
            "data": {
                "contact_name": f"Contact {i}",
                "email": f"contact{i}@example.com",
                "budget": 300000 + (i * 50000)
            }
        }
        for i in range(10)
    ]

    # Process in parallel
    tasks = [
        event_bus.process_lead_event(
            lead_id=lead["lead_id"],
            tenant_id=lead["tenant_id"],
            event_data=lead["data"],
            priority=ProcessingPriority.MEDIUM
        )
        for lead in leads
    ]

    results = await asyncio.gather(*tasks)

    successful = sum(1 for r in results if r is not None)
    print(f"Processed {successful}/{len(leads)} leads successfully")

    # Get performance metrics
    metrics = await event_bus.get_performance_metrics()
    print(f"Average processing time: {metrics['avg_processing_time_ms']:.1f}ms")
    print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")


# Example 5: WebSocket Integration
async def example_websocket_integration():
    """Example: Real-time WebSocket broadcasting"""
    print("\n=== Example 5: WebSocket Integration ===")

    event_bus = await get_event_bus()

    # Process event with real-time broadcasting
    intelligence = await process_lead_intelligence(
        lead_id="lead_websocket_test",
        tenant_id="tenant_123",
        event_data={
            "contact_name": "WebSocket Test",
            "email": "test@example.com",
            "interactions": [
                {"type": "chat_started", "timestamp": datetime.now().isoformat()}
            ]
        }
    )

    if intelligence:
        print(f"Intelligence broadcasted to WebSocket subscribers")
        print(f"  Broadcast would reach all connected clients for tenant_123")
        print(f"  Real-time updates include:")
        print(f"    - Lead score updates")
        print(f"    - Churn risk alerts")
        print(f"    - Property match notifications")


# Example 6: Performance Monitoring
async def example_performance_monitoring():
    """Example: Monitor Event Bus performance"""
    print("\n=== Example 6: Performance Monitoring ===")

    event_bus = await get_event_bus()

    # Get comprehensive performance metrics
    metrics = await event_bus.get_performance_metrics()

    print("Event Bus Performance Metrics:")
    print(f"  Total events processed: {metrics['total_events_processed']}")
    print(f"  Success rate: {metrics['successful_events'] / max(metrics['total_events_processed'], 1):.1%}")
    print(f"  Average processing time: {metrics['avg_processing_time_ms']:.1f}ms")
    print(f"  Average ML coordination: {metrics['avg_ml_coordination_ms']:.1f}ms")
    print(f"  Average broadcast latency: {metrics['avg_broadcast_latency_ms']:.1f}ms")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']:.1%}")
    print(f"  Current queue depth: {metrics['current_queue_depth']}")
    print(f"  Events per second: {metrics['events_per_second']:.1f}")

    print("\nPerformance Status:")
    status = metrics.get('performance_status', {})
    print(f"  Processing time OK: {status.get('processing_time_ok', False)}")
    print(f"  ML coordination OK: {status.get('ml_coordination_ok', False)}")
    print(f"  Broadcast latency OK: {status.get('broadcast_latency_ok', False)}")
    print(f"  Queue healthy: {status.get('queue_healthy', False)}")
    print(f"  Overall healthy: {status.get('overall_healthy', False)}")

    print("\nHealth Status:")
    print(f"  Redis: {'✓' if metrics['redis_healthy'] else '✗'}")
    print(f"  WebSocket: {'✓' if metrics['websocket_healthy'] else '✗'}")
    print(f"  ML Engine: {'✓' if metrics['ml_engine_healthy'] else '✗'}")


# Example 7: Error Handling
async def example_error_handling():
    """Example: Proper error handling"""
    print("\n=== Example 7: Error Handling ===")

    event_bus = await get_event_bus()

    try:
        # Process event with potential error
        intelligence = await event_bus.process_lead_event(
            lead_id="lead_error_test",
            tenant_id="tenant_123",
            event_data={
                "invalid_data": True  # Might cause processing error
            },
            priority=ProcessingPriority.MEDIUM
        )

        if intelligence:
            print("Event processed successfully")
        else:
            print("Event processing returned None (likely an error)")

    except Exception as e:
        print(f"Error processing event: {e}")
        print("Event Bus handles errors gracefully and continues processing")


# Example 8: Priority-Based Processing
async def example_priority_processing():
    """Example: Process events with different priorities"""
    print("\n=== Example 8: Priority-Based Processing ===")

    event_bus = await get_event_bus()

    # Critical priority event (hot lead)
    critical_event = await publish_lead_event(
        event_type=EventType.LEAD_CREATED,
        tenant_id="tenant_123",
        lead_id="lead_critical",
        event_data={
            "contact_name": "VIP Lead",
            "budget": 2000000,
            "timeline": "immediate",
            "referral_source": "existing_client"
        },
        priority=EventPriority.CRITICAL
    )
    print(f"Critical priority event: {critical_event}")

    # High priority event (engaged lead)
    high_event = await publish_lead_event(
        event_type=EventType.INTERACTION_RECORDED,
        tenant_id="tenant_123",
        lead_id="lead_high",
        event_data={
            "interaction_type": "property_viewing_scheduled"
        },
        priority=EventPriority.HIGH
    )
    print(f"High priority event: {high_event}")

    # Medium priority event (standard lead)
    medium_event = await publish_lead_event(
        event_type=EventType.LEAD_UPDATED,
        tenant_id="tenant_123",
        lead_id="lead_medium",
        event_data={
            "profile_updated": True
        },
        priority=EventPriority.MEDIUM
    )
    print(f"Medium priority event: {medium_event}")

    print("\nEvents will be processed based on priority (CRITICAL → HIGH → MEDIUM → LOW)")


# Main execution
async def main():
    """Run all examples"""
    print("=" * 60)
    print("Event Bus Integration - Usage Examples")
    print("=" * 60)

    try:
        # Run examples
        await example_basic_event_publishing()
        await example_synchronous_processing()
        await example_event_subscription()
        await example_batch_processing()
        await example_websocket_integration()
        await example_performance_monitoring()
        await example_error_handling()
        await example_priority_processing()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
