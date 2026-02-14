#!/usr/bin/env python3
"""
Tiered Cache Service Demo

Demonstrates the performance benefits and usage patterns of the TieredCacheService.
Shows real-world scenarios like ML scoring, property matching, and lead intelligence.

Usage:
    python examples/tiered_cache_demo.py

Author: Claude Sonnet 4
Date: 2026-01-17
"""

import asyncio
import time
import random
from typing import Dict, Any, List

from ghl_real_estate_ai.services.tiered_cache_service import (
    TieredCacheService,
    tiered_cache,
    cache_metrics,
    TieredCacheContext
)


# Mock expensive operations that benefit from caching
@tiered_cache(ttl=3600, key_prefix="lead_score")
async def calculate_ml_lead_score(lead_id: str, model_version: str = "v2.1") -> float:
    """Simulate expensive ML lead scoring that takes 200ms."""
    print(f"🔥 Computing ML lead score for {lead_id} (model {model_version})...")

    # Simulate complex ML computation
    await asyncio.sleep(0.2)  # 200ms computation

    # Generate realistic lead score
    base_score = random.uniform(0.1, 0.9)
    adjustments = random.uniform(-0.1, 0.1)
    score = max(0.0, min(1.0, base_score + adjustments))

    print(f"  ✅ Lead {lead_id} scored: {score:.3f}")
    return score


@tiered_cache(ttl=1800, key_prefix="property_match")
async def find_property_matches(lead_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Simulate property matching algorithm that takes 150ms."""
    print(f"🏠 Finding property matches for preferences: {lead_preferences['location']}")

    # Simulate property search and matching
    await asyncio.sleep(0.15)  # 150ms computation

    # Generate mock property matches
    num_matches = random.randint(3, 12)
    matches = []

    for i in range(num_matches):
        matches.append({
            "property_id": f"prop_{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 999)} Main St",
            "price": random.randint(200000, 800000),
            "bedrooms": random.randint(2, 5),
            "match_score": random.uniform(0.6, 0.95)
        })

    # Sort by match score
    matches.sort(key=lambda x: x["match_score"], reverse=True)

    print(f"  ✅ Found {len(matches)} property matches")
    return matches


@tiered_cache(ttl=900, key_prefix="market_analysis")
async def get_market_analysis(location: str, property_type: str) -> Dict[str, Any]:
    """Simulate market analysis that takes 100ms."""
    print(f"📊 Analyzing market for {property_type} in {location}")

    # Simulate market data aggregation
    await asyncio.sleep(0.1)  # 100ms computation

    analysis = {
        "location": location,
        "property_type": property_type,
        "avg_price": random.randint(250000, 750000),
        "price_trend": random.choice(["increasing", "stable", "decreasing"]),
        "days_on_market": random.randint(15, 120),
        "inventory_level": random.choice(["low", "medium", "high"]),
        "demand_score": random.uniform(0.3, 0.9)
    }

    print(f"  ✅ Market analysis complete: {analysis['avg_price']:,} avg price")
    return analysis


async def simulate_lead_processing_without_cache():
    """Simulate lead processing without cache (baseline performance)."""
    print("🚫 Running WITHOUT cache (baseline performance)")

    leads = [f"lead_{i:03d}" for i in range(1, 11)]
    preferences = [
        {"location": "Rancho Cucamonga, CA", "max_price": 500000, "min_bedrooms": 3},
        {"location": "Seattle, WA", "max_price": 700000, "min_bedrooms": 2},
        {"location": "Miami, FL", "max_price": 600000, "min_bedrooms": 4}
    ]

    start_time = time.perf_counter()

    for i, lead_id in enumerate(leads):
        pref = preferences[i % len(preferences)]

        # Direct function calls (no caching)
        await asyncio.sleep(0.2)  # ML scoring
        await asyncio.sleep(0.15)  # Property matching
        await asyncio.sleep(0.1)   # Market analysis

    total_time = time.perf_counter() - start_time

    print(f"⏱️  Total time without cache: {total_time:.2f} seconds")
    print(f"📈 Average per lead: {total_time/len(leads)*1000:.0f}ms")

    return total_time


async def simulate_lead_processing_with_cache():
    """Simulate lead processing with tiered cache."""
    print("\n✅ Running WITH tiered cache")

    leads = [f"lead_{i:03d}" for i in range(1, 11)]
    preferences = [
        {"location": "Rancho Cucamonga, CA", "max_price": 500000, "min_bedrooms": 3},
        {"location": "Seattle, WA", "max_price": 700000, "min_bedrooms": 2},
        {"location": "Miami, FL", "max_price": 600000, "min_bedrooms": 4}
    ]

    start_time = time.perf_counter()

    async with TieredCacheContext() as cache:
        for i, lead_id in enumerate(leads):
            pref = preferences[i % len(preferences)]

            # These calls will be cached automatically
            score = await calculate_ml_lead_score(lead_id)
            matches = await find_property_matches(pref)
            analysis = await get_market_analysis(pref["location"], "single_family")

            print(f"  Lead {lead_id}: Score {score:.2f}, {len(matches)} matches")

    total_time = time.perf_counter() - start_time

    print(f"⏱️  Total time with cache: {total_time:.2f} seconds")
    print(f"📈 Average per lead: {total_time/len(leads)*1000:.0f}ms")

    return total_time


async def demonstrate_cache_promotion():
    """Demonstrate L2 → L1 cache promotion."""
    print("\n🔄 Demonstrating cache promotion (L2 → L1)")

    async with TieredCacheContext() as cache:
        lead_id = "demo_lead_001"

        # First access: Populates both L1 and L2
        print("1️⃣ First access - populating cache")
        start = time.perf_counter()
        score1 = await calculate_ml_lead_score(lead_id)
        time1 = (time.perf_counter() - start) * 1000
        print(f"   Time: {time1:.1f}ms (function execution)")

        # Clear L1 cache to simulate it was evicted
        cache.l1_cache.clear()
        print("   Cleared L1 cache (simulating eviction)")

        # Second access: L1 miss, L2 hit (but not promoted yet)
        print("2️⃣ Second access - L2 hit, no promotion")
        start = time.perf_counter()
        score2 = await calculate_ml_lead_score(lead_id)
        time2 = (time.perf_counter() - start) * 1000
        print(f"   Time: {time2:.1f}ms (L2 cache hit)")

        # Third access: L1 miss, L2 hit WITH promotion
        cache.l1_cache.clear()
        print("3️⃣ Third access - L2 hit with L1 promotion")
        start = time.perf_counter()
        score3 = await calculate_ml_lead_score(lead_id)
        time3 = (time.perf_counter() - start) * 1000
        print(f"   Time: {time3:.1f}ms (L2 hit + promotion)")

        # Fourth access: L1 hit (super fast)
        print("4️⃣ Fourth access - L1 hit")
        start = time.perf_counter()
        score4 = await calculate_ml_lead_score(lead_id)
        time4 = (time.perf_counter() - start) * 1000
        print(f"   Time: {time4:.1f}ms (L1 hit - fastest)")

        print(f"\n💡 Performance progression:")
        print(f"   Function execution: {time1:.1f}ms")
        print(f"   L2 cache hit:       {time2:.1f}ms")
        print(f"   L2 hit + promotion: {time3:.1f}ms")
        print(f"   L1 cache hit:       {time4:.1f}ms (🚀 Fastest)")


async def show_comprehensive_metrics():
    """Show comprehensive cache performance metrics."""
    print("\n📊 Comprehensive Performance Metrics")

    metrics = await cache_metrics()

    print(f"""
🎯 Overall Performance:
   Hit Ratio: {metrics['performance']['hit_ratio_percent']}%
   Average Latency: {metrics['performance']['average_latency_ms']:.2f}ms
   Total Requests: {metrics['performance']['total_requests']}
   Performance Gain: {metrics['performance']['performance_improvement']}

💾 L1 Memory Cache:
   Hits: {metrics['l1_memory_cache']['hits']}
   Misses: {metrics['l1_memory_cache']['misses']}
   Hit Ratio: {metrics['l1_memory_cache']['hit_ratio_percent']}%
   Current Size: {metrics['l1_memory_cache']['current_size']}/{metrics['l1_memory_cache']['max_size']}
   Utilization: {metrics['l1_memory_cache']['utilization_percent']}%
   Evictions: {metrics['l1_memory_cache']['evictions']}
   Avg Latency: {metrics['l1_memory_cache']['average_latency_ms']:.3f}ms

🌐 L2 Redis Cache:
   Hits: {metrics['l2_redis_cache']['hits']}
   Misses: {metrics['l2_redis_cache']['misses']}
   Hit Ratio: {metrics['l2_redis_cache']['hit_ratio_percent']}%
   Promotions to L1: {metrics['l2_redis_cache']['promotions_to_l1']}
   Avg Latency: {metrics['l2_redis_cache']['average_latency_ms']:.3f}ms
   Enabled: {metrics['l2_redis_cache']['enabled']}

🧹 Background Maintenance:
   Cleanup Runs: {metrics['background_tasks']['cleanup_runs']}
   Expired Items Cleaned: {metrics['background_tasks']['expired_items_cleaned']}
   Last Cleanup: {metrics['background_tasks']['last_cleanup']}
""")


async def main():
    """Run the comprehensive demo."""
    print("🚀 Tiered Cache Service Demo")
    print("=" * 60)

    # Baseline performance without cache
    baseline_time = await simulate_lead_processing_without_cache()

    # Performance with cache
    cached_time = await simulate_lead_processing_with_cache()

    # Calculate improvement
    improvement_percent = ((baseline_time - cached_time) / baseline_time) * 100
    speedup = baseline_time / cached_time

    print(f"\n🎯 Performance Summary:")
    print(f"   Baseline (no cache): {baseline_time:.2f}s")
    print(f"   With tiered cache:   {cached_time:.2f}s")
    print(f"   Improvement:         {improvement_percent:.1f}% faster")
    print(f"   Speedup:            {speedup:.1f}x")

    # Demonstrate promotion mechanism
    await demonstrate_cache_promotion()

    # Show detailed metrics
    await show_comprehensive_metrics()

    print("\n✨ Demo complete! The tiered cache provides:")
    print("   • Sub-millisecond L1 cache hits")
    print("   • Automatic L2 → L1 promotion based on access patterns")
    print("   • Comprehensive performance metrics")
    print("   • Zero-configuration setup")
    print("   • Graceful degradation if Redis unavailable")
    print("   • Background maintenance for optimal performance")


if __name__ == "__main__":
    """Run the demo."""
    asyncio.run(main())