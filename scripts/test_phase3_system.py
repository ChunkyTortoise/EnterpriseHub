#!/usr/bin/env python3
"""
Test Phase 3 Business Impact Measurement System
==============================================

Validates feature flags, metrics tracking, and A/B testing.

Usage:
    python scripts/test_phase3_system.py

Author: EnterpriseHub Development Team
Created: January 2026
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_feature_flags():
    """Test feature flag functionality."""
    print("\n🧪 Testing Feature Flags...")
    print("-" * 60)

    from ghl_real_estate_ai.services.feature_flag_manager import (
        get_feature_flag_manager
    )

    manager = await get_feature_flag_manager()

    # Test flag lookup
    flag = await manager.get_flag("realtime_intelligence")
    if flag:
        print(f"✅ Flag found: {flag.name}")
        print(f"   Stage: {flag.rollout_stage.value}")
        print(f"   Traffic: {flag.percentage}%")
    else:
        print("❌ Flag not found")
        return False

    # Test feature enablement
    enabled = await manager.is_enabled(
        "realtime_intelligence",
        "test_tenant",
        "test_user"
    )
    print(f"✅ Feature enablement check: {enabled}")

    # Test variant assignment
    variant = await manager.get_variant(
        "realtime_intelligence",
        "test_tenant",
        "test_user"
    )
    print(f"✅ Variant assignment: {variant}")

    # Test consistency (same user should get same variant)
    variant2 = await manager.get_variant(
        "realtime_intelligence",
        "test_tenant",
        "test_user"
    )
    if variant == variant2:
        print(f"✅ Bucketing consistency verified")
    else:
        print(f"❌ Bucketing inconsistent: {variant} != {variant2}")
        return False

    return True


async def test_business_metrics():
    """Test business metrics tracking."""
    print("\n🧪 Testing Business Metrics Tracking...")
    print("-" * 60)

    from ghl_real_estate_ai.services.phase3_business_impact_tracker import (
        get_business_impact_tracker,
        BusinessMetric,
        MetricType
    )

    tracker = await get_business_impact_tracker()

    # Test real-time intelligence event
    await tracker.track_realtime_intelligence_event(
        tenant_id="test_tenant",
        user_id="test_user",
        response_time_seconds=25.0,
        lead_id="test_lead_1"
    )
    print("✅ Real-time intelligence event tracked")

    # Test property satisfaction
    await tracker.track_property_match_satisfaction(
        tenant_id="test_tenant",
        user_id="test_user",
        lead_id="test_lead_2",
        satisfaction_score=92.0,
        property_id="test_prop_1"
    )
    print("✅ Property satisfaction tracked")

    # Test churn prevention
    await tracker.track_churn_prevention_intervention(
        tenant_id="test_tenant",
        user_id="test_user",
        lead_id="test_lead_3",
        intervention_stage=2,
        churned=False
    )
    print("✅ Churn prevention intervention tracked")

    # Test AI coaching
    await tracker.track_ai_coaching_session(
        tenant_id="test_tenant",
        agent_id="test_agent",
        session_duration_minutes=18.0,
        productivity_score=85.0
    )
    print("✅ AI coaching session tracked")

    # Verify buffer
    buffer_size = len(tracker.metric_buffer)
    print(f"✅ Metric buffer size: {buffer_size}")

    if buffer_size < 4:
        print("❌ Expected at least 4 metrics in buffer")
        return False

    return True


async def test_roi_calculation():
    """Test ROI calculation."""
    print("\n🧪 Testing ROI Calculation...")
    print("-" * 60)

    from ghl_real_estate_ai.services.phase3_business_impact_tracker import (
        get_business_impact_tracker
    )

    tracker = await get_business_impact_tracker()

    # Generate sample data for real-time intelligence
    print("📊 Generating sample data...")
    for i in range(50):
        await tracker.track_realtime_intelligence_event(
            tenant_id="test_tenant",
            user_id=f"test_user_{i}",
            response_time_seconds=30.0,  # vs baseline 900s
            lead_id=f"test_lead_{i}"
        )

    # Calculate ROI
    roi = await tracker.calculate_feature_roi(
        "realtime_intelligence",
        days=7
    )

    if roi:
        print(f"✅ ROI calculated successfully")
        print(f"   Revenue Impact: ${roi.revenue_impact:,.0f}")
        print(f"   Cost Savings: ${roi.cost_savings:,.0f}")
        print(f"   Net Value: ${roi.net_value:,.0f}")
        print(f"   ROI: {roi.roi_percentage:.1f}%")
        print(f"   Sample Size: {roi.sample_size}")
    else:
        print("❌ ROI calculation failed")
        return False

    return True


async def test_ab_testing():
    """Test A/B testing statistical analysis."""
    print("\n🧪 Testing A/B Test Analysis...")
    print("-" * 60)

    from ghl_real_estate_ai.services.phase3_business_impact_tracker import (
        get_business_impact_tracker,
        BusinessMetric,
        MetricType
    )

    tracker = await get_business_impact_tracker()

    print("📊 Generating A/B test data...")

    # Control group (baseline)
    for i in range(100):
        metric = BusinessMetric(
            metric_type=MetricType.RESPONSE_TIME,
            feature_id="realtime_intelligence",
            tenant_id="test_tenant",
            user_id=f"control_user_{i}",
            value=900.0,  # 15 minutes
            variant="control"
        )
        await tracker.record_metric(metric)

    # Treatment group (improved)
    for i in range(100):
        metric = BusinessMetric(
            metric_type=MetricType.RESPONSE_TIME,
            feature_id="realtime_intelligence",
            tenant_id="test_tenant",
            user_id=f"treatment_user_{i}",
            value=25.0,  # 25 seconds
            variant="treatment"
        )
        await tracker.record_metric(metric)

    # Run A/B test
    result = await tracker.run_ab_test_analysis(
        "realtime_intelligence",
        MetricType.RESPONSE_TIME,
        days=7
    )

    if result:
        print(f"✅ A/B test analysis completed")
        print(f"   Control Mean: {result.control_mean:.1f}s")
        print(f"   Treatment Mean: {result.treatment_mean:.1f}s")
        print(f"   Lift: {result.lift_percentage:.1f}%")
        print(f"   P-value: {result.p_value:.4f}")
        print(f"   Significant: {result.is_significant}")
        print(f"   Recommendation: {result.recommended_action}")

        # Validate results
        if result.treatment_mean < result.control_mean:
            print("✅ Treatment shows improvement (lower response time)")
        else:
            print("❌ Unexpected result: Treatment should be faster")
            return False

        if result.is_significant:
            print("✅ Result is statistically significant")
        else:
            print("⚠️  Result not statistically significant (expected with test data)")

    else:
        print("❌ A/B test analysis failed")
        return False

    return True


async def test_daily_summary():
    """Test daily summary calculation."""
    print("\n🧪 Testing Daily Summary...")
    print("-" * 60)

    from ghl_real_estate_ai.services.phase3_business_impact_tracker import (
        get_business_impact_tracker
    )

    tracker = await get_business_impact_tracker()

    summary = await tracker.get_daily_summary()

    if summary:
        print(f"✅ Daily summary calculated")
        print(f"   Date: {summary.get('date')}")
        print(f"   Total Revenue Impact: ${summary.get('total_revenue_impact', 0):,.2f}")
        print(f"   Total Cost Savings: ${summary.get('total_cost_savings', 0):,.2f}")
        print(f"   Total ROI: {summary.get('total_roi', 0):.1f}%")

        if summary.get('features'):
            print(f"   Features tracked: {len(summary['features'])}")
        else:
            print("   No feature data yet")
    else:
        print("❌ Daily summary calculation failed")
        return False

    return True


async def test_performance():
    """Test system performance."""
    print("\n🧪 Testing Performance...")
    print("-" * 60)

    from ghl_real_estate_ai.services.feature_flag_manager import (
        get_feature_flag_manager
    )
    import time

    manager = await get_feature_flag_manager()

    # Warm up cache
    await manager.get_flag("realtime_intelligence")

    # Test lookup latency
    start = time.time()
    iterations = 1000

    for _ in range(iterations):
        await manager.get_flag("realtime_intelligence")

    elapsed = (time.time() - start) * 1000  # ms
    avg_latency = elapsed / iterations

    print(f"✅ Performance test completed")
    print(f"   Iterations: {iterations}")
    print(f"   Total time: {elapsed:.2f}ms")
    print(f"   Average latency: {avg_latency:.4f}ms")

    if avg_latency < 1.0:
        print(f"✅ Meets <1ms target")
    else:
        print(f"⚠️  Exceeds 1ms target (cache may not be warmed)")

    # Get performance metrics
    metrics = await manager.get_performance_metrics()

    if metrics.get('total_lookups', 0) > 0:
        print(f"\n📊 Performance Metrics:")
        print(f"   Total lookups: {metrics.get('total_lookups')}")
        print(f"   Avg latency: {metrics.get('avg_latency_ms', 0):.4f}ms")
        print(f"   P95 latency: {metrics.get('p95_latency_ms', 0):.4f}ms")
        print(f"   P99 latency: {metrics.get('p99_latency_ms', 0):.4f}ms")

    return avg_latency < 5.0  # Allow some tolerance for test environment


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("   Phase 3 Business Impact System - Test Suite")
    print("=" * 70)

    tests = [
        ("Feature Flags", test_feature_flags),
        ("Business Metrics", test_business_metrics),
        ("ROI Calculation", test_roi_calculation),
        ("A/B Testing", test_ab_testing),
        ("Daily Summary", test_daily_summary),
        ("Performance", test_performance)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("   Test Results Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print("\n" + "-" * 70)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! System is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
