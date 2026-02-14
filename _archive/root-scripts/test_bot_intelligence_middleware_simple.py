import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Simple validation test for Bot Intelligence Middleware - Phase 3.3
==================================================================

Basic functionality testing without pytest dependency.
Validates core implementation meets requirements.
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, '/Users/cave/Documents/GitHub/EnterpriseHub')

# Import the implementations
try:
    from ghl_real_estate_ai.services.bot_intelligence_middleware import (
        BotIntelligenceMiddleware,
        get_bot_intelligence_middleware
    )
    from ghl_real_estate_ai.models.intelligence_context import (
        BotIntelligenceContext,
        PropertyIntelligence,
        ConversationIntelligence,
        PreferenceIntelligence,
        IntelligencePerformanceMetrics
    )
    print("✅ Successfully imported Bot Intelligence Middleware components")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_data_models():
    """Test intelligence context data models."""
    print("\n🧪 Testing Data Models...")

    # Test PropertyIntelligence
    prop_intel = PropertyIntelligence(
        top_matches=[{'property_id': 'prop_123', 'score': 0.9}],
        match_count=1,
        best_match_score=0.9
    )
    assert prop_intel.match_count == 1
    assert prop_intel.best_match_score == 0.9

    # Test serialization
    data = prop_intel.to_dict()
    reconstructed = PropertyIntelligence.from_dict(data)
    assert reconstructed.match_count == prop_intel.match_count

    # Test ConversationIntelligence
    conv_intel = ConversationIntelligence(
        objections_detected=[{'type': 'price', 'severity': 0.7}],
        overall_sentiment=0.6,
        sentiment_trend='improving'
    )
    assert conv_intel.overall_sentiment == 0.6
    assert conv_intel.sentiment_trend == 'improving'

    # Test PreferenceIntelligence
    pref_intel = PreferenceIntelligence(
        preference_profile={'budget_max': 600000},
        profile_completeness=0.75,
        urgency_level=0.7
    )
    assert pref_intel.profile_completeness == 0.75
    assert pref_intel.urgency_level == 0.7

    print("✅ Data models working correctly")

def test_bot_intelligence_context():
    """Test BotIntelligenceContext serialization and methods."""
    print("\n🧪 Testing BotIntelligenceContext...")

    # Test fallback context creation
    fallback_context = BotIntelligenceContext.create_fallback(
        lead_id="lead_123",
        location_id="rancho_cucamonga",
        bot_type="jorge-seller"
    )

    assert fallback_context.lead_id == "lead_123"
    assert fallback_context.location_id == "rancho_cucamonga"
    assert fallback_context.bot_type == "jorge-seller"
    assert fallback_context.property_intelligence.match_count == 0
    assert fallback_context.conversation_intelligence.overall_sentiment == 0.0
    assert fallback_context.preference_intelligence.profile_completeness == 0.0
    assert 'fallback_context_created' in fallback_context.performance_metrics.service_failures

    # Test JSON serialization
    json_str = fallback_context.to_json()
    deserialized = BotIntelligenceContext.from_json(json_str)

    assert deserialized.lead_id == fallback_context.lead_id
    assert deserialized.location_id == fallback_context.location_id
    assert deserialized.bot_type == fallback_context.bot_type

    # Test composite score calculation
    fallback_context.calculate_composite_scores()
    assert 0.0 <= fallback_context.composite_engagement_score <= 1.0
    assert fallback_context.recommended_approach is not None

    print("✅ BotIntelligenceContext working correctly")

def test_singleton_pattern():
    """Test singleton pattern implementation."""
    print("\n🧪 Testing Singleton Pattern...")

    instance1 = get_bot_intelligence_middleware()
    instance2 = get_bot_intelligence_middleware()

    assert instance1 is instance2
    assert isinstance(instance1, BotIntelligenceMiddleware)

    print("✅ Singleton pattern working correctly")

def test_metrics_tracking():
    """Test performance metrics tracking."""
    print("\n🧪 Testing Metrics Tracking...")

    middleware = get_bot_intelligence_middleware()
    initial_metrics = middleware.get_metrics()

    # Simulate metrics updates
    middleware._update_metrics(120.5)  # Within target
    middleware._update_metrics(250.0)  # Above target
    middleware._update_metrics(80.0)   # Within target

    updated_metrics = middleware.get_metrics()

    assert updated_metrics['total_enhancements'] >= initial_metrics['total_enhancements']
    assert 'performance_status' in updated_metrics
    assert updated_metrics['performance_status'] in ['excellent', 'good', 'degraded', 'unknown']

    print("✅ Metrics tracking working correctly")

async def test_mock_services():
    """Test mock service functionality for graceful fallback."""
    print("\n🧪 Testing Mock Services...")

    middleware = BotIntelligenceMiddleware()

    # Test mock cache
    cache = middleware._create_mock_cache()
    result = await cache.get("test_key")
    assert result is None

    success = await cache.set("test_key", "test_value")
    assert success is True

    # Test mock event publisher
    event_publisher = middleware._create_mock_event_publisher()
    await event_publisher.publish_lead_update(lead_id="test", event_type="test")

    # Test mock property matcher
    property_matcher = middleware._create_mock_property_matcher()
    matches = await property_matcher.find_behavioral_matches()
    assert matches == []

    print("✅ Mock services working correctly")

async def test_cache_operations():
    """Test cache key generation and operations."""
    print("\n🧪 Testing Cache Operations...")

    middleware = BotIntelligenceMiddleware()

    # Test cache key generation
    cache_key1 = middleware._create_cache_key("lead_123", "rancho_cucamonga", "jorge-seller")
    cache_key2 = middleware._create_cache_key("lead_123", "rancho_cucamonga", "jorge-seller")
    cache_key3 = middleware._create_cache_key("lead_456", "rancho_cucamonga", "jorge-seller")

    assert cache_key1 == cache_key2  # Same inputs should generate same key
    assert cache_key1 != cache_key3  # Different inputs should generate different keys
    assert isinstance(cache_key1, str)
    assert len(cache_key1) == 32  # MD5 hash length

    print("✅ Cache operations working correctly")

async def test_intelligence_aggregation():
    """Test intelligence result aggregation with fallbacks."""
    print("\n🧪 Testing Intelligence Aggregation...")

    middleware = BotIntelligenceMiddleware()

    # Test with empty results (all services failed)
    performance_metrics = IntelligencePerformanceMetrics()
    empty_results = {
        'property_matching': None,
        'conversation_analysis': None,
        'preference_learning': None
    }

    context = middleware._aggregate_intelligence(
        "jorge-seller",
        "lead_123",
        "rancho_cucamonga",
        empty_results,
        performance_metrics
    )

    assert isinstance(context, BotIntelligenceContext)
    assert context.lead_id == "lead_123"
    assert context.property_intelligence.match_count == 0  # Fallback values

    # Test with partial results (some services succeeded)
    partial_results = {
        'property_matching': PropertyIntelligence(match_count=2, best_match_score=0.8),
        'conversation_analysis': None,  # Failed
        'preference_learning': PreferenceIntelligence(profile_completeness=0.6)
    }

    context = middleware._aggregate_intelligence(
        "jorge-buyer",
        "lead_456",
        "rancho_cucamonga",
        partial_results,
        performance_metrics
    )

    assert context.property_intelligence.match_count == 2  # From successful service
    assert context.conversation_intelligence.overall_sentiment == 0.0  # Fallback
    assert context.preference_intelligence.profile_completeness == 0.6  # From successful service

    print("✅ Intelligence aggregation working correctly")

async def run_all_tests():
    """Run all validation tests."""
    print("🚀 Starting Bot Intelligence Middleware Validation Tests")
    print("=" * 60)

    try:
        # Synchronous tests
        test_data_models()
        test_bot_intelligence_context()
        test_singleton_pattern()
        test_metrics_tracking()

        # Asynchronous tests
        await test_mock_services()
        await test_cache_operations()
        await test_intelligence_aggregation()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("🎯 Bot Intelligence Middleware implementation is working correctly")
        print("📊 Ready for bot integration (Jorge Seller/Buyer/Lead bots)")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        return False

    return True

if __name__ == "__main__":
    # Run validation tests
    success = asyncio.run(run_all_tests())

    if success:
        print("\n🎉 Implementation validation completed successfully!")
        print("📋 Next Steps:")
        print("  1. ✅ Bot Intelligence Middleware - COMPLETE")
        print("  2. 🔄 Jorge Seller Bot Integration - NEXT")
        print("  3. 🔄 Jorge Buyer Bot Integration")
        print("  4. 🔄 Lead Bot Integration")
        print("  5. 🔄 Integration Testing & Performance Validation")
        sys.exit(0)
    else:
        print("\n🚨 Implementation validation failed!")
        sys.exit(1)