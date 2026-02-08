"""
Test Suite for Property Scoring Strategy Pattern

Validates the Strategy Pattern implementation with unit and integration tests.
Ensures SOLID compliance and enterprise-grade functionality.
"""

import time
import unittest
from typing import Any, Dict

from .basic_scorer import BasicPropertyScorer
from .enhanced_scorer import EnhancedPropertyScorer
from .property_matcher_context import PropertyMatcherContext

# Import Strategy Pattern components
from .property_scorer import ConfidenceLevel, PropertyScorer, ScoringContext, ScoringResult
from .scoring_factory import ScoringFactory, get_scoring_factory


class TestPropertyScoringStrategies(unittest.TestCase):
    """Test suite for property scoring strategies"""

    def setUp(self):
        """Set up test data"""
        self.test_property = {
            "id": "test-001",
            "price": 500000,
            "address": {"neighborhood": "Downtown"},
            "bedrooms": 3,
            "bathrooms": 2.5,
            "sqft": 2000,
            "property_type": "Single Family",
            "year_built": 2020,
            "amenities": ["garage", "updated_kitchen"],
        }

        self.test_preferences = {
            "budget": 600000,
            "location": ["Downtown"],
            "bedrooms": 3,
            "bathrooms": 2,
            "property_type": "Single Family",
            "work_location": "downtown",
        }

    def test_basic_scorer_functionality(self):
        """Test BasicPropertyScorer implementation"""
        scorer = BasicPropertyScorer()

        # Test input validation
        self.assertTrue(scorer.validate_inputs(self.test_property, self.test_preferences))

        # Test scoring
        result = scorer.calculate_score(self.test_property, self.test_preferences)

        # Validate result structure
        self.assertIsInstance(result, ScoringResult)
        self.assertIsInstance(result.overall_score, float)
        self.assertTrue(0 <= result.overall_score <= 100)
        self.assertIsInstance(result.confidence_level, ConfidenceLevel)
        self.assertIsInstance(result.reasoning, list)
        self.assertGreater(len(result.reasoning), 0)

        # Test performance characteristics
        characteristics = scorer.get_performance_characteristics()
        self.assertIn("speed", characteristics)
        self.assertEqual(characteristics["speed"], "very_fast")

    def test_enhanced_scorer_functionality(self):
        """Test EnhancedPropertyScorer implementation"""
        scorer = EnhancedPropertyScorer()

        # Test input validation
        self.assertTrue(scorer.validate_inputs(self.test_property, self.test_preferences))

        # Test scoring
        result = scorer.calculate_score(self.test_property, self.test_preferences)

        # Validate result structure
        self.assertIsInstance(result, ScoringResult)
        self.assertTrue(0 <= result.overall_score <= 100)
        self.assertIn("strategy", result.metadata)
        self.assertEqual(result.metadata["strategy"], "enhanced")
        self.assertIn("factor_scores", result.metadata)

        # Test that enhanced scorer provides more sophisticated analysis
        self.assertGreaterEqual(len(result.reasoning), 3)

    def test_strategy_pattern_context(self):
        """Test PropertyMatcherContext Strategy Pattern implementation"""
        basic_scorer = BasicPropertyScorer()
        enhanced_scorer = EnhancedPropertyScorer()

        # Test with basic strategy
        context = PropertyMatcherContext(basic_scorer)
        result = context.score_property(self.test_property, self.test_preferences)
        self.assertIsInstance(result, ScoringResult)

        # Test strategy switching
        context.set_strategy(enhanced_scorer)
        result2 = context.score_property(self.test_property, self.test_preferences)
        self.assertIsInstance(result2, ScoringResult)

        # Strategies should produce different results (different algorithms)
        self.assertNotEqual(result.overall_score, result2.overall_score)

    def test_scoring_factory(self):
        """Test ScoringFactory Strategy Pattern factory"""
        factory = ScoringFactory()

        # Test strategy registration
        available_strategies = factory.get_available_strategies()
        self.assertIn("basic", available_strategies)
        self.assertIn("enhanced", available_strategies)

        # Test strategy creation
        basic_scorer = factory.create_strategy("basic")
        enhanced_scorer = factory.create_strategy("enhanced")

        self.assertIsInstance(basic_scorer, BasicPropertyScorer)
        self.assertIsInstance(enhanced_scorer, EnhancedPropertyScorer)

        # Test strategy info
        basic_info = factory.get_strategy_info("basic")
        self.assertIn("performance", basic_info)
        self.assertIn("speed", basic_info["performance"])

    def test_batch_scoring_performance(self):
        """Test batch scoring with multiple properties"""
        factory = get_scoring_factory()
        context = PropertyMatcherContext(factory.create_strategy("basic"))

        # Create multiple test properties
        properties = []
        for i in range(10):
            prop = self.test_property.copy()
            prop["id"] = f"test-{i:03d}"
            prop["price"] = 450000 + (i * 50000)
            properties.append(prop)

        # Test batch scoring
        start_time = time.time()
        scored_properties = context.score_multiple_properties(properties, self.test_preferences)
        execution_time = time.time() - start_time

        # Validate results
        self.assertEqual(len(scored_properties), 10)
        self.assertLess(execution_time, 2.0)  # Should be fast

        # Validate sorting (highest scores first)
        scores = [p.get("overall_score", 0) for p in scored_properties]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_error_handling_and_fallback(self):
        """Test error handling with fallback strategies"""

        # Create a mock failing scorer
        class FailingScorer(PropertyScorer):
            def calculate_score(self, property_data, lead_preferences):
                raise Exception("Intentional test failure")

            def validate_inputs(self, property_data, lead_preferences):
                return True

        failing_scorer = FailingScorer()
        fallback_scorer = BasicPropertyScorer()

        # Test fallback mechanism
        context = PropertyMatcherContext(
            strategy=failing_scorer, fallback_strategy=fallback_scorer, enable_performance_monitoring=True
        )

        # Should use fallback and succeed
        result = context.score_property(self.test_property, self.test_preferences)
        self.assertIsInstance(result, ScoringResult)

        # Check performance metrics show fallback was used
        metrics = context.get_performance_metrics()
        self.assertEqual(metrics["fallbacks_used"], 1)

    def test_legacy_format_compatibility(self):
        """Test backward compatibility with legacy format"""
        scorer = BasicPropertyScorer()
        result = scorer.calculate_score(self.test_property, self.test_preferences)

        # Test legacy format conversion
        legacy_result = result.to_legacy_format()

        self.assertIn("match_score", legacy_result)
        self.assertIn("budget_match", legacy_result)
        self.assertIn("location_match", legacy_result)
        self.assertIn("features_match", legacy_result)
        self.assertIn("match_reasons", legacy_result)

        # Validate data types
        self.assertIsInstance(legacy_result["match_score"], int)
        self.assertIsInstance(legacy_result["budget_match"], bool)
        self.assertIsInstance(legacy_result["match_reasons"], list)

    def test_strategy_recommendation(self):
        """Test strategy recommendation engine"""
        factory = ScoringFactory()

        # Test different scenario recommendations
        high_volume_context = ScoringContext(performance_priority="speed")
        accuracy_context = ScoringContext(performance_priority="accuracy")
        urgent_context = ScoringContext(urgency_level="urgent")

        high_volume_strategy = factory.recommend_strategy(high_volume_context, 500)
        accuracy_strategy = factory.recommend_strategy(accuracy_context, 10)
        urgent_strategy = factory.recommend_strategy(urgent_context, 5)

        # High volume should recommend basic for speed
        self.assertEqual(high_volume_strategy, "basic")

        # Accuracy focus should recommend enhanced
        self.assertEqual(accuracy_strategy, "enhanced")

        # Urgent should recommend basic for speed
        self.assertEqual(urgent_strategy, "basic")

    def test_solid_principles_compliance(self):
        """Test SOLID principles compliance"""

        # Single Responsibility: Each strategy handles only scoring
        basic_scorer = BasicPropertyScorer()
        enhanced_scorer = EnhancedPropertyScorer()

        # Both should implement the same interface
        self.assertTrue(hasattr(basic_scorer, "calculate_score"))
        self.assertTrue(hasattr(enhanced_scorer, "calculate_score"))
        self.assertTrue(hasattr(basic_scorer, "validate_inputs"))
        self.assertTrue(hasattr(enhanced_scorer, "validate_inputs"))

        # Open/Closed: Can extend without modifying existing code
        # (Demonstrated by ability to add new scorers to factory)
        factory = ScoringFactory()
        original_count = len(factory.get_available_strategies())

        # Could register a new strategy without modifying existing ones
        self.assertGreaterEqual(original_count, 2)

        # Liskov Substitution: Strategies are interchangeable
        context = PropertyMatcherContext(basic_scorer)
        result1 = context.score_property(self.test_property, self.test_preferences)

        context.set_strategy(enhanced_scorer)
        result2 = context.score_property(self.test_property, self.test_preferences)

        # Both should return ScoringResult (same interface)
        self.assertIsInstance(result1, ScoringResult)
        self.assertIsInstance(result2, ScoringResult)

        # Dependency Inversion: Context depends on interface, not implementation
        self.assertIsInstance(context._strategy, PropertyScorer)


def run_strategy_pattern_tests():
    """
    Run all Strategy Pattern tests and return results.

    Returns:
        Dict with test results and performance metrics
    """
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPropertyScoringStrategies)

    # Run tests with detailed output
    import io

    test_output = io.StringIO()
    runner = unittest.TextTestRunner(stream=test_output, verbosity=2)

    start_time = time.time()
    result = runner.run(suite)
    execution_time = time.time() - start_time

    # Compile results
    test_results = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100,
        "execution_time": round(execution_time, 3),
        "output": test_output.getvalue(),
    }

    return test_results


if __name__ == "__main__":
    # Run tests when script is executed directly
    print("🧪 Running Strategy Pattern Test Suite...")
    results = run_strategy_pattern_tests()

    print(f"\n📊 Test Results:")
    print(f"   Tests Run: {results['tests_run']}")
    print(f"   Success Rate: {results['success_rate']:.1f}%")
    print(f"   Execution Time: {results['execution_time']}s")

    if results["failures"] > 0 or results["errors"] > 0:
        print(f"   ❌ Failures: {results['failures']}")
        print(f"   ❌ Errors: {results['errors']}")
        print("\n📝 Detailed Output:")
        print(results["output"])
    else:
        print("   ✅ All tests passed!")

    print("\n🎉 Strategy Pattern validation complete!")
