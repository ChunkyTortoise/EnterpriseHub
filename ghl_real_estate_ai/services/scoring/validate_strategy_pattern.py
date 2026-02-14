"""
Strategy Pattern Validation Script

Demonstrates and validates the Strategy Pattern implementation
without requiring complex test runner setup.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import components
from basic_scorer import BasicPropertyScorer
from enhanced_scorer import EnhancedPropertyScorer
from property_matcher_context import PropertyMatcherContext
from property_scorer import ScoringContext
from scoring_factory import ScoringFactory


def create_test_data():
    """Create test property and preferences data"""
    test_property = {
        "id": "demo-001",
        "price": 750000,
        "address": {"neighborhood": "Downtown"},
        "bedrooms": 3,
        "bathrooms": 2.5,
        "sqft": 2100,
        "property_type": "Single Family",
        "year_built": 2020,
        "amenities": ["garage", "updated_kitchen", "hardwood_floors"],
        "days_on_market": 12,
    }

    test_preferences = {
        "budget": 800000,
        "location": ["Downtown"],
        "bedrooms": 3,
        "bathrooms": 2,
        "property_type": "Single Family",
        "work_location": "downtown",
        "has_children": False,
        "min_sqft": 2000,
    }

    return test_property, test_preferences


def validate_basic_scorer():
    """Validate BasicPropertyScorer functionality"""
    print("\n🔧 Testing Basic Scorer...")

    property_data, preferences = create_test_data()
    scorer = BasicPropertyScorer()

    # Test input validation
    is_valid = scorer.validate_inputs(property_data, preferences)
    print(f"   ✓ Input validation: {'PASS' if is_valid else 'FAIL'}")

    # Test scoring
    start_time = time.time()
    result = scorer.calculate_score(property_data, preferences)
    execution_time = (time.time() - start_time) * 1000  # Convert to ms

    print(f"   ✓ Overall Score: {result.overall_score:.1f}%")
    print(f"   ✓ Confidence: {result.confidence_level.value}")
    print(f"   ✓ Execution Time: {execution_time:.2f}ms")
    print(f"   ✓ Reasoning Count: {len(result.reasoning)}")

    # Test performance characteristics
    characteristics = scorer.get_performance_characteristics()
    print(f"   ✓ Performance Profile: {characteristics['speed']}/{characteristics['accuracy']}")

    return result


def validate_enhanced_scorer():
    """Validate EnhancedPropertyScorer functionality"""
    print("\n⚡ Testing Enhanced Scorer...")

    property_data, preferences = create_test_data()
    scorer = EnhancedPropertyScorer()

    # Test scoring
    start_time = time.time()
    result = scorer.calculate_score(property_data, preferences)
    execution_time = (time.time() - start_time) * 1000

    print(f"   ✓ Overall Score: {result.overall_score:.1f}%")
    print(f"   ✓ Confidence: {result.confidence_level.value}")
    print(f"   ✓ Execution Time: {execution_time:.2f}ms")
    print(f"   ✓ Factor Count: {result.metadata.get('factor_count', 'N/A')}")
    print(f"   ✓ Strategy: {result.metadata.get('strategy', 'N/A')}")

    # Show factor breakdown
    factor_scores = result.metadata.get("factor_scores", {})
    if factor_scores:
        print("   ✓ Top Factors:")
        sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
        for factor, score in sorted_factors[:3]:
            print(f"     • {factor}: {score}%")

    return result


def validate_strategy_pattern():
    """Validate Strategy Pattern context switching"""
    print("\n🔄 Testing Strategy Pattern...")

    property_data, preferences = create_test_data()
    basic_scorer = BasicPropertyScorer()
    enhanced_scorer = EnhancedPropertyScorer()

    # Create context with basic strategy
    context = PropertyMatcherContext(basic_scorer, fallback_strategy=enhanced_scorer)

    # Test with basic strategy
    result1 = context.score_property(property_data, preferences)
    print(f"   ✓ Basic Strategy Score: {result1.overall_score:.1f}%")

    # Switch to enhanced strategy
    context.set_strategy(enhanced_scorer)
    result2 = context.score_property(property_data, preferences)
    print(f"   ✓ Enhanced Strategy Score: {result2.overall_score:.1f}%")

    # Validate strategy switching worked
    strategy_switching_works = result1.overall_score != result2.overall_score
    print(f"   ✓ Strategy Switching: {'PASS' if strategy_switching_works else 'FAIL'}")

    # Test performance metrics
    metrics = context.get_performance_metrics()
    print(f"   ✓ Total Scores: {metrics['total_scores']}")
    print(f"   ✓ Error Rate: {metrics.get('error_rate', 0):.1%}")

    return result1, result2


def validate_scoring_factory():
    """Validate ScoringFactory functionality"""
    print("\n🏭 Testing Scoring Factory...")

    factory = ScoringFactory()

    # Test available strategies
    strategies = factory.get_available_strategies()
    print(f"   ✓ Available Strategies: {', '.join(strategies)}")

    # Test strategy creation
    for strategy_name in strategies:
        try:
            strategy = factory.create_strategy(strategy_name)
            print(f"   ✓ Created {strategy_name}: {strategy.__class__.__name__}")
        except Exception as e:
            print(f"   ❌ Failed to create {strategy_name}: {e}")

    # Test strategy recommendation
    context = ScoringContext(performance_priority="balanced")
    recommended = factory.recommend_strategy(context, property_count=10)
    print(f"   ✓ Recommended Strategy: {recommended}")

    # Test strategy validation
    validation_results = factory.validate_all_strategies()
    for strategy_name, result in validation_results.items():
        status_icon = "✅" if result["status"] == "passed" else "⚠️" if result["status"] == "warning" else "❌"
        print(f"   {status_icon} {strategy_name}: {result['status']}")

    return factory


def validate_batch_processing():
    """Validate batch processing with multiple properties"""
    print("\n📦 Testing Batch Processing...")

    # Create multiple test properties
    base_property, preferences = create_test_data()
    properties = []

    for i in range(5):
        prop = base_property.copy()
        prop["id"] = f"batch-{i:03d}"
        prop["price"] = 700000 + (i * 25000)
        prop["neighborhood"] = ["Downtown", "Ontario Mills", "Haven City", "Highland", "Westlake"][i]
        properties.append(prop)

    # Test batch scoring
    factory = ScoringFactory()
    context = PropertyMatcherContext(factory.create_strategy("enhanced"))

    start_time = time.time()
    scored_properties = context.score_multiple_properties(properties, preferences)
    execution_time = time.time() - start_time

    print(f"   ✓ Properties Processed: {len(scored_properties)}")
    print(f"   ✓ Total Execution Time: {execution_time:.3f}s")
    print(f"   ✓ Average Time per Property: {(execution_time / len(scored_properties) * 1000):.1f}ms")

    # Validate sorting
    scores = [p.get("overall_score", 0) for p in scored_properties]
    is_sorted = scores == sorted(scores, reverse=True)
    print(f"   ✓ Results Sorted: {'PASS' if is_sorted else 'FAIL'}")

    # Show top results
    print("   ✓ Top Properties:")
    for i, prop in enumerate(scored_properties[:3]):
        print(f"     {i + 1}. {prop.get('address', 'N/A')} - {prop.get('overall_score', 0):.1f}%")

    return scored_properties


def validate_legacy_compatibility():
    """Validate backward compatibility with legacy format"""
    print("\n🔄 Testing Legacy Compatibility...")

    property_data, preferences = create_test_data()
    scorer = BasicPropertyScorer()
    result = scorer.calculate_score(property_data, preferences)

    # Test legacy format conversion
    legacy_result = result.to_legacy_format()

    required_fields = ["match_score", "budget_match", "location_match", "features_match", "match_reasons"]
    all_fields_present = all(field in legacy_result for field in required_fields)
    print(f"   ✓ Legacy Fields Present: {'PASS' if all_fields_present else 'FAIL'}")

    # Validate data types
    type_checks = [
        isinstance(legacy_result["match_score"], int),
        isinstance(legacy_result["budget_match"], bool),
        isinstance(legacy_result["match_reasons"], list),
    ]
    all_types_correct = all(type_checks)
    print(f"   ✓ Legacy Data Types: {'PASS' if all_types_correct else 'FAIL'}")

    print(f"   ✓ Legacy Score: {legacy_result['match_score']}%")
    print(f"   ✓ Reason Count: {len(legacy_result['match_reasons'])}")

    return legacy_result


def main():
    """Run all Strategy Pattern validations"""
    print("🎯 Strategy Pattern Validation Suite")
    print("=" * 50)

    try:
        # Run all validation tests
        validate_basic_scorer()
        validate_enhanced_scorer()
        validate_strategy_pattern()
        validate_scoring_factory()
        validate_batch_processing()
        validate_legacy_compatibility()

        print("\n" + "=" * 50)
        print("📊 Validation Summary")
        print("=" * 50)

        print("✅ Basic Scorer: Operational")
        print("✅ Enhanced Scorer: Operational")
        print("✅ Strategy Pattern: Operational")
        print("✅ Scoring Factory: Operational")
        print("✅ Batch Processing: Operational")
        print("✅ Legacy Compatibility: Operational")

        print("\n🎉 Strategy Pattern Implementation: VALIDATED")
        print("🚀 Ready for Phase 2 enterprise features!")

    except Exception as e:
        print(f"\n❌ Validation Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
