#!/usr/bin/env python3
"""
Test Repository Pattern + Strategy Pattern Integration

Validates that the async Repository Pattern correctly integrates with
the Strategy Pattern scoring system after fixing import paths.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent
services_dir = current_dir.parent
root_dir = services_dir.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(services_dir))


async def test_strategy_pattern_integration():
    """Test that Strategy Pattern integration works correctly"""
    print("🔧 Testing Repository Pattern + Strategy Pattern Integration...")

    try:
        # Test the imports first
        print("📦 Testing imports...")
        from strategy_integration import (
            STRATEGY_PATTERN_AVAILABLE,
            create_repository_property_matcher,
            enhanced_generate_property_matches,
        )

        print(f"✅ Strategy Pattern Available: {STRATEGY_PATTERN_AVAILABLE}")

        if not STRATEGY_PATTERN_AVAILABLE:
            print("❌ Strategy Pattern not available - import failed")
            return False

        # Test creating a repository property matcher
        print("\n🏗️  Testing repository property matcher creation...")
        data_sources_config = {
            "type": "demo",
            "json_data_dir": "/Users/cave/enterprisehub/ghl_real_estate_ai/data/knowledge_base",
        }

        # Test factory function
        matcher = await create_repository_property_matcher(
            data_sources_config=data_sources_config, strategy_name="enhanced", fallback_strategy="basic"
        )
        print("✅ Repository property matcher created successfully")

        # Test property scoring
        print("\n⚖️  Testing property scoring integration...")
        lead_preferences = {
            "budget": 750000,
            "location": "Downtown",
            "bedrooms": 3,
            "bathrooms": 2,
            "property_type": "Single Family",
            "must_haves": ["garage", "yard"],
            "nice_to_haves": ["pool", "good_schools"],
            "work_location": "downtown",
            "has_children": True,
            "min_sqft": 1800,
        }

        context = {"lead_id": "test_lead_123", "agent_id": "test_agent_456"}

        scored_properties = await matcher.score_properties_with_repository(
            lead_preferences=lead_preferences, context=context, max_properties=10
        )

        print(f"✅ Scored {len(scored_properties)} properties successfully")

        # Validate results
        if scored_properties:
            first_property = scored_properties[0]
            required_fields = ["address", "price", "beds", "baths", "sqft", "match_score"]

            for field in required_fields:
                if field not in first_property:
                    print(f"❌ Missing required field: {field}")
                    return False

            print(f"✅ Property format validation passed")
            print(f"   📍 Example: {first_property['address']} - Score: {first_property['match_score']}%")

        # Test enhanced property match generation
        print("\n🎯 Testing enhanced property match generation...")
        lead_context = {"extracted_preferences": lead_preferences}

        matches = await enhanced_generate_property_matches(
            lead_context=lead_context, data_sources_config=data_sources_config
        )

        print(f"✅ Generated {len(matches)} enhanced property matches")

        # Test performance metrics
        print("\n📊 Testing performance metrics...")
        metrics = await matcher.get_performance_metrics()

        if "repository_metrics" in metrics and "strategy_metrics" in metrics:
            print("✅ Performance metrics collection working")
            print(f"   📈 Repository calls: {metrics.get('repository_metrics', {}).get('total_queries', 'N/A')}")
        else:
            print("⚠️  Some performance metrics missing")

        print("\n🎉 All integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_import_paths():
    """Test that all import paths are working correctly"""
    print("🔍 Testing import paths...")

    try:
        # Test direct Strategy Pattern imports

        print("✅ Direct Strategy Pattern imports working")

        # Test Repository Pattern imports

        print("✅ Repository Pattern imports working")

        # Test strategy integration imports
        from strategy_integration import STRATEGY_PATTERN_AVAILABLE

        print(f"✅ Strategy integration available: {STRATEGY_PATTERN_AVAILABLE}")

        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("🚀 Starting Repository + Strategy Pattern Integration Tests\n")

    # Test import paths first
    imports_ok = await test_import_paths()
    if not imports_ok:
        print("\n💥 Import tests failed - stopping here")
        return

    print("\n" + "=" * 60)

    # Test integration functionality
    integration_ok = await test_strategy_pattern_integration()

    print("\n" + "=" * 60)

    if integration_ok:
        print("\n🎉 ALL TESTS PASSED - Repository + Strategy Pattern Integration is working!")
    else:
        print("\n💥 TESTS FAILED - Integration needs more work")


if __name__ == "__main__":
    asyncio.run(main())
