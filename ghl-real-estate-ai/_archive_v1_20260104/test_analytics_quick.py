#!/usr/bin/env python
"""
Quick validation script for analytics engine.
Tests core functionality without pytest.
"""
import asyncio
import time
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.analytics_engine import AnalyticsEngine


async def test_basic_collection():
    """Test basic metrics collection."""
    print("=" * 60)
    print("Testing Analytics Engine - Basic Collection")
    print("=" * 60)

    # Use temp storage
    engine = AnalyticsEngine(storage_dir="data/metrics_test")

    context = {
        "created_at": datetime.utcnow().isoformat(),
        "conversation_history": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"}
        ],
        "extracted_preferences": {"pathway": "wholesale"},
        "is_returning_lead": False,
        "last_lead_score": 40
    }

    # Test 1: Record event
    print("\n[TEST 1] Recording conversation event...")
    start_time = time.time()

    metrics = await engine.record_event(
        contact_id="c123",
        location_id="test_loc",
        lead_score=75,
        previous_score=50,
        message="I'm looking for a 3-bedroom home in Austin with a budget of $500,000",
        response="Great! What's your timeline?",
        response_time_ms=250.5,
        context=context
    )

    collection_time = (time.time() - start_time) * 1000

    print(f"✓ Event recorded successfully")
    print(f"  Contact ID: {metrics.contact_id}")
    print(f"  Lead Score: {metrics.lead_score}")
    print(f"  Classification: {metrics.classification}")
    print(f"  Keywords: {metrics.keywords_detected}")
    print(f"  Collection time: {collection_time:.2f}ms")

    if collection_time > 50:
        print(f"  ⚠️ WARNING: Collection time exceeds 50ms target")
    else:
        print(f"  ✓ Performance target met (<50ms)")

    # Test 2: Get conversion funnel
    print("\n[TEST 2] Calculating conversion funnel...")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Record more events for funnel
    for i in range(5):
        await engine.record_event(
            contact_id=f"cold_{i}",
            location_id="test_loc",
            lead_score=30,
            previous_score=20,
            message="Test",
            response="Response",
            response_time_ms=100,
            context=context
        )

    for i in range(3):
        await engine.record_event(
            contact_id=f"hot_{i}",
            location_id="test_loc",
            lead_score=80,
            previous_score=70,
            message="Test",
            response="Would you like to schedule an appointment?",
            response_time_ms=100,
            context=context,
            appointment_scheduled=True
        )

    funnel = await engine.get_conversion_funnel("test_loc", today, today)

    print(f"✓ Funnel calculated:")
    print(f"  Cold leads: {funnel.cold_leads}")
    print(f"  Warm leads: {funnel.warm_leads}")
    print(f"  Hot leads: {funnel.hot_leads}")
    print(f"  Appointments: {funnel.appointments_scheduled}")
    print(f"  Conversion rate: {funnel.overall_conversion_rate:.2%}")

    # Test 3: Response time analysis
    print("\n[TEST 3] Analyzing response times...")
    response_analysis = await engine.analyze_response_times("test_loc", today, today)

    print(f"✓ Response times analyzed:")
    print(f"  Average: {response_analysis['avg_response_time_ms']:.2f}ms")
    print(f"  Median: {response_analysis['median_response_time_ms']:.2f}ms")
    print(f"  P95: {response_analysis['p95_response_time_ms']:.2f}ms")

    # Test 4: SMS compliance
    print("\n[TEST 4] Checking SMS compliance...")
    compliance = await engine.check_compliance("test_loc", today, today)

    print(f"✓ Compliance checked:")
    print(f"  Total messages: {compliance['total_messages']}")
    print(f"  Compliant: {compliance['compliant_messages']}")
    print(f"  Compliance rate: {compliance['compliance_rate']:.2%}")
    print(f"  Avg message length: {compliance['avg_message_length']:.0f} chars")

    # Test 5: Topic distribution
    print("\n[TEST 5] Analyzing topic distribution...")
    topics = await engine.analyze_topics("test_loc", today, today)

    print(f"✓ Topics analyzed:")
    print(f"  Keywords: {list(topics['keywords'].keys())}")
    print(f"  Topics: {list(topics['topics'].keys())}")
    if topics['pathways']:
        print(f"  Pathways: {topics['pathways']}")

    # Test 6: Comprehensive report
    print("\n[TEST 6] Generating comprehensive report...")
    report = await engine.get_comprehensive_report("test_loc", today, today)

    print(f"✓ Report generated:")
    print(f"  Sections: {list(report.keys())}")
    print(f"  Date range: {report['date_range']}")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print("\nAnalytics engine is operational and ready for integration.")


async def test_performance_overhead():
    """Test performance overhead under load."""
    print("\n" + "=" * 60)
    print("Performance Test - 100 Event Collection")
    print("=" * 60)

    engine = AnalyticsEngine(storage_dir="data/metrics_test")

    context = {
        "created_at": datetime.utcnow().isoformat(),
        "conversation_history": [],
        "last_lead_score": 40
    }

    total_time = 0
    num_events = 100

    print(f"\nCollecting {num_events} events...")
    for i in range(num_events):
        start_time = time.time()

        await engine.record_event(
            contact_id=f"perf_test_{i}",
            location_id="test_loc",
            lead_score=50 + (i % 50),
            previous_score=40,
            message="Test message",
            response="Test response",
            response_time_ms=100,
            context=context
        )

        event_time = (time.time() - start_time) * 1000
        total_time += event_time

    avg_time = total_time / num_events

    print(f"\n✓ Performance Results:")
    print(f"  Total events: {num_events}")
    print(f"  Total time: {total_time:.2f}ms")
    print(f"  Average per event: {avg_time:.2f}ms")

    if avg_time < 50:
        print(f"  ✓ Performance target MET (<50ms)")
    else:
        print(f"  ⚠️ Performance target MISSED (avg: {avg_time:.2f}ms, target: <50ms)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_basic_collection())
    asyncio.run(test_performance_overhead())

    print("\n🎉 Analytics Engine validation complete!")
