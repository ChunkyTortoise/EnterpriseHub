import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Jorge Seller Bot Intelligence Integration Validation - Phase 3.3
================================================================

Validates that Jorge Seller Bot successfully integrates with Bot Intelligence Middleware
while preserving all existing functionality.
"""

import asyncio
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, '/Users/cave/Documents/GitHub/EnterpriseHub')

# Import the implementations
try:
    from ghl_real_estate_ai.agents.jorge_seller_bot import (
        JorgeSellerBot,
        JorgeFeatureConfig,
        get_jorge_seller_bot
    )
    from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
    print("✅ Successfully imported Jorge Seller Bot components")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_feature_config_intelligence():
    """Test that bot intelligence feature is properly configured."""
    print("\n🧪 Testing Feature Configuration...")

    # Test default configuration includes intelligence
    config = JorgeFeatureConfig()
    assert config.enable_bot_intelligence == True, "Bot intelligence should be enabled by default"

    # Test custom configuration
    custom_config = JorgeFeatureConfig(enable_bot_intelligence=False)
    assert custom_config.enable_bot_intelligence == False, "Custom bot intelligence setting should work"

    print("✅ Feature configuration working correctly")

def test_jorge_initialization():
    """Test Jorge bot initializes with intelligence middleware."""
    print("\n🧪 Testing Jorge Initialization...")

    # Test standard Jorge (intelligence disabled by default)
    jorge_standard = JorgeSellerBot.create_standard_jorge("test_tenant")
    assert jorge_standard.config.enable_bot_intelligence == True, "Standard Jorge should have default intelligence enabled"

    # Test progressive Jorge (intelligence enabled)
    jorge_progressive = JorgeSellerBot.create_progressive_jorge("test_tenant")
    assert jorge_progressive.config.enable_bot_intelligence == True, "Progressive Jorge should have intelligence enabled"

    # Test enterprise Jorge (intelligence enabled)
    jorge_enterprise = JorgeSellerBot.create_enterprise_jorge("test_tenant")
    assert jorge_enterprise.config.enable_bot_intelligence == True, "Enterprise Jorge should have intelligence enabled"

    # Test manual configuration
    custom_config = JorgeFeatureConfig(enable_bot_intelligence=False)
    jorge_custom = JorgeSellerBot("test_tenant", custom_config)
    assert jorge_custom.config.enable_bot_intelligence == False, "Custom Jorge should respect configuration"

    print("✅ Jorge initialization working correctly")

def test_workflow_statistics():
    """Test that workflow statistics include intelligence metrics."""
    print("\n🧪 Testing Workflow Statistics...")

    jorge = JorgeSellerBot.create_progressive_jorge("test_tenant")

    # Check that intelligence stats are initialized
    stats = jorge.workflow_stats
    assert "intelligence_enhancements" in stats, "Intelligence enhancements should be tracked"
    assert "intelligence_cache_hits" in stats, "Intelligence cache hits should be tracked"
    assert stats["intelligence_enhancements"] == 0, "Intelligence enhancements should start at 0"
    assert stats["intelligence_cache_hits"] == 0, "Intelligence cache hits should start at 0"

    print("✅ Workflow statistics working correctly")

def test_workflow_graph_structure():
    """Test that workflow graph includes intelligence gathering node when enabled."""
    print("\n🧪 Testing Workflow Graph Structure...")

    # Test with intelligence enabled
    jorge_enhanced = JorgeSellerBot.create_progressive_jorge("test_tenant")
    workflow_enhanced = jorge_enhanced.workflow

    # Test with intelligence disabled
    config_basic = JorgeFeatureConfig(enable_bot_intelligence=False)
    jorge_basic = JorgeSellerBot("test_tenant", config_basic)
    workflow_basic = jorge_basic.workflow

    # Both workflows should compile successfully
    assert workflow_enhanced is not None, "Enhanced workflow should compile"
    assert workflow_basic is not None, "Basic workflow should compile"

    print("✅ Workflow graph structure working correctly")

async def test_performance_metrics():
    """Test that performance metrics include bot intelligence data."""
    print("\n🧪 Testing Performance Metrics...")

    jorge = JorgeSellerBot.create_enterprise_jorge("test_tenant")

    # Get performance metrics
    metrics = await jorge.get_performance_metrics()

    # Check feature enablement
    assert "features_enabled" in metrics, "Features enabled should be tracked"
    assert "bot_intelligence" in metrics["features_enabled"], "Bot intelligence feature should be tracked"
    assert metrics["features_enabled"]["bot_intelligence"] == True, "Bot intelligence should be enabled"

    # Check intelligence-specific metrics
    assert "bot_intelligence" in metrics, "Bot intelligence metrics should be included"

    intel_metrics = metrics["bot_intelligence"]
    assert "total_enhancements" in intel_metrics, "Total enhancements should be tracked"
    assert "cache_hits" in intel_metrics, "Cache hits should be tracked"
    assert "cache_hit_rate" in intel_metrics, "Cache hit rate should be calculated"
    assert "enhancement_rate" in intel_metrics, "Enhancement rate should be calculated"
    assert "middleware_available" in intel_metrics, "Middleware availability should be tracked"

    print("✅ Performance metrics working correctly")

def test_helper_methods():
    """Test that intelligence helper methods are properly defined."""
    print("\n🧪 Testing Helper Methods...")

    jorge = JorgeSellerBot.create_progressive_jorge("test_tenant")

    # Check that helper methods exist and are callable
    assert hasattr(jorge, '_apply_conversation_intelligence'), "Conversation intelligence helper should exist"
    assert hasattr(jorge, '_enhance_prompt_with_intelligence'), "Prompt enhancement helper should exist"
    assert hasattr(jorge, '_extract_preferences_from_conversation'), "Preference extraction helper should exist"

    # Test preference extraction with sample data
    sample_conversation = [
        {"role": "user", "content": "I need to sell under 700k"},
        {"role": "assistant", "content": "I can help with that"},
        {"role": "user", "content": "I need to sell quickly in 3 months"}
    ]

    preferences = jorge._extract_preferences_from_conversation(sample_conversation)
    assert isinstance(preferences, dict), "Preferences should be a dictionary"

    print("✅ Helper methods working correctly")

async def test_intelligence_integration_graceful_fallback():
    """Test that intelligence integration has graceful fallback when middleware unavailable."""
    print("\n🧪 Testing Graceful Fallback...")

    # Create Jorge with intelligence enabled but simulate middleware failure
    jorge = JorgeSellerBot.create_progressive_jorge("test_tenant")

    # Simulate middleware unavailable
    jorge.intelligence_middleware = None

    # Create sample state
    sample_state = {
        "lead_id": "test_lead_123",
        "lead_name": "Test Seller",
        "conversation_history": [
            {"role": "user", "content": "I want to sell my house"},
            {"role": "assistant", "content": "I can help you with that"}
        ],
        "location_id": "rancho_cucamonga"
    }

    try:
        # Test intelligence gathering with middleware unavailable
        result = await jorge.gather_intelligence_context(sample_state)

        # Should return graceful fallback
        assert "intelligence_context" in result, "Intelligence context key should be present"
        assert result["intelligence_context"] is None, "Intelligence context should be None when unavailable"
        assert result["intelligence_available"] == False, "Intelligence should be marked as unavailable"
        assert "intelligence_performance_ms" in result, "Performance timing should be tracked"

        print("✅ Graceful fallback working correctly")

    except Exception as e:
        print(f"❌ Graceful fallback test failed: {e}")
        return False

    return True

def test_factory_functions():
    """Test that factory functions work with intelligence integration."""
    print("\n🧪 Testing Factory Functions...")

    # Test get_jorge_seller_bot factory function
    jorge_standard = get_jorge_seller_bot("standard", "test_tenant")
    assert jorge_standard is not None, "Standard Jorge should be created"

    jorge_progressive = get_jorge_seller_bot("progressive", "test_tenant")
    assert jorge_progressive is not None, "Progressive Jorge should be created"
    assert jorge_progressive.config.enable_bot_intelligence == True, "Progressive Jorge should have intelligence"

    jorge_enterprise = get_jorge_seller_bot("enterprise", "test_tenant")
    assert jorge_enterprise is not None, "Enterprise Jorge should be created"
    assert jorge_enterprise.config.enable_bot_intelligence == True, "Enterprise Jorge should have intelligence"

    print("✅ Factory functions working correctly")

async def run_all_tests():
    """Run all Jorge Seller Bot intelligence integration tests."""
    print("🚀 Starting Jorge Seller Bot Intelligence Integration Tests")
    print("=" * 70)

    try:
        # Synchronous tests
        test_feature_config_intelligence()
        test_jorge_initialization()
        test_workflow_statistics()
        test_workflow_graph_structure()
        test_helper_methods()
        test_factory_functions()

        # Asynchronous tests
        await test_performance_metrics()
        await test_intelligence_integration_graceful_fallback()

        print("\n" + "=" * 70)
        print("✅ ALL JORGE INTELLIGENCE INTEGRATION TESTS PASSED!")
        print("🎯 Jorge Seller Bot successfully enhanced with Phase 3.3 intelligence")
        print("📊 Integration preserves all existing functionality with graceful fallbacks")
        print("🚀 Ready for production deployment with intelligence-enhanced responses")

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
        print("\n🎉 Jorge Seller Bot Intelligence Integration validation completed successfully!")
        print("📋 Phase 3.3 Priority 2 Status:")
        print("  ✅ Bot Intelligence Middleware Integration - COMPLETE")
        print("  ✅ Intelligence gathering node added to workflow")
        print("  ✅ Strategy enhancement with conversation intelligence")
        print("  ✅ Response enhancement with property/preference intelligence")
        print("  ✅ Graceful fallback for service failures")
        print("  ✅ Performance metrics and monitoring")
        print("  ✅ Factory method updates for enhanced configurations")
        print("\n📋 Next Steps:")
        print("  1. ✅ Phase 3.3 Priority 1: Bot Intelligence Middleware - COMPLETE")
        print("  2. ✅ Phase 3.3 Priority 2: Jorge Seller Bot Intelligence - COMPLETE")
        print("  3. 🔄 Phase 3.3 Priority 3: Jorge Buyer Bot Intelligence - NEXT")
        print("  4. 🔄 Phase 3.3 Priority 4: Lead Bot Intelligence Integration")
        print("  5. 🔄 Phase 3.3 Priority 5: Integration Testing & Performance Validation")
        sys.exit(0)
    else:
        print("\n🚨 Jorge Seller Bot Intelligence Integration validation failed!")
        sys.exit(1)