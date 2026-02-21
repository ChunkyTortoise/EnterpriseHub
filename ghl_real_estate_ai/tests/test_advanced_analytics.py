"""
Tests for Advanced Analytics Engine (Agent C3)
"""

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.advanced_analytics import ABTestManager, ConversationOptimizer, PerformanceAnalyzer


class TestABTestManager:
    """Test A/B testing functionality."""

    def test_create_experiment(self):
        """Test creating a new A/B test experiment."""
        manager = ABTestManager("test_location")

        exp_id = manager.create_experiment(
            name="Test Experiment",
            variant_a={"message": "Hello!"},
            variant_b={"message": "Hi there!"},
            metric="conversion_rate",
        )

        assert exp_id.startswith("exp_")
        assert exp_id in manager.experiments["active"]

        exp = manager.experiments["active"][exp_id]
        assert exp["name"] == "Test Experiment"
        assert exp["metric"] == "conversion_rate"
        assert "a" in exp["variants"]
        assert "b" in exp["variants"]

    def test_assign_variant(self):
        """Test consistent variant assignment."""
        manager = ABTestManager("test_location")

        exp_id = manager.create_experiment(name="Test", variant_a={}, variant_b={})

        # Same contact should always get same variant
        contact_id = "test_contact_123"
        variant1 = manager.assign_variant(exp_id, contact_id)
        variant2 = manager.assign_variant(exp_id, contact_id)

        assert variant1 == variant2
        assert variant1 in ["a", "b"]

    def test_record_result(self):
        """Test recording experiment results."""
        manager = ABTestManager("test_location")

        exp_id = manager.create_experiment(name="Test", variant_a={}, variant_b={})

        # Record result for variant A
        manager.record_result(exp_id, "a", {"contact_id": "c1", "conversion": True, "lead_score": 80})

        results = manager.experiments["active"][exp_id]["variants"]["a"]["results"]
        assert len(results) == 1
        assert results[0]["conversion"] is True
        assert results[0]["lead_score"] == 80

    def test_analyze_experiment(self):
        """Test experiment analysis."""
        manager = ABTestManager("test_location")

        exp_id = manager.create_experiment(name="Test", variant_a={}, variant_b={}, metric="lead_score")

        # Add results for both variants
        for i in range(10):
            manager.record_result(exp_id, "a", {"contact_id": f"c{i}", "lead_score": 60 + i})
            manager.record_result(exp_id, "b", {"contact_id": f"c{i + 10}", "lead_score": 70 + i})

        analysis = manager.analyze_experiment(exp_id)

        assert "variant_a" in analysis
        assert "variant_b" in analysis
        assert analysis["variant_a"]["count"] == 10
        assert analysis["variant_b"]["count"] == 10
        assert analysis["variant_b"]["mean"] > analysis["variant_a"]["mean"]

    def test_list_active_experiments(self):
        """Test listing active experiments."""
        # Use unique location to avoid interference from other tests
        import time

        unique_loc = f"test_location_list_{int(time.time() * 1000)}"
        manager = ABTestManager(unique_loc)

        # Create multiple experiments
        exp1 = manager.create_experiment("Exp 1", {}, {})
        exp2 = manager.create_experiment("Exp 2", {}, {})

        active = manager.list_active_experiments()

        # Should return exactly 2 experiments for this location
        assert len(active) == 2
        assert any(e["name"] == "Exp 1" for e in active)
        assert any(e["name"] == "Exp 2" for e in active)

    def test_complete_experiment(self):
        """Test completing an experiment."""
        manager = ABTestManager("test_location")

        exp_id = manager.create_experiment("Test", {}, {})

        # Complete the experiment
        manager.complete_experiment(exp_id)

        assert exp_id not in manager.experiments["active"]
        assert exp_id in manager.experiments["completed"]
        assert manager.experiments["completed"][exp_id]["status"] == "completed"


class TestPerformanceAnalyzer:
    """Test performance analysis functionality."""

    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = PerformanceAnalyzer("test_location")

        assert analyzer.location_id == "test_location"
        assert analyzer.memory_dir.name == "test_location"

    def test_analyze_conversation_patterns_empty(self):
        """Test analysis with no conversations."""
        analyzer = PerformanceAnalyzer("nonexistent_location")

        result = analyzer.analyze_conversation_patterns()

        assert "error" in result or "total_conversations" in result

    def test_categorize_question(self):
        """Test question categorization."""
        analyzer = PerformanceAnalyzer("test_location")

        # Test different question types
        assert analyzer._categorize_question("What's your budget?") == "budget"
        assert analyzer._categorize_question("Which area do you prefer?") == "location"
        assert analyzer._categorize_question("When do you need to move?") == "timeline"
        assert analyzer._categorize_question("How many bedrooms?") == "property_requirements"
        assert analyzer._categorize_question("Are you pre-approved?") == "financing"

    def test_generate_performance_report(self):
        """Test report generation."""
        analyzer = PerformanceAnalyzer("test_location")

        report = analyzer.generate_performance_report()

        assert isinstance(report, str)
        assert "PERFORMANCE ANALYSIS REPORT" in report or "No data" in report


class TestConversationOptimizer:
    """Test conversation optimization suggestions."""

    def test_suggest_next_question_cold_lead(self):
        """Test question suggestion for cold lead."""
        optimizer = ConversationOptimizer()

        suggestion = optimizer.suggest_next_question(
            conversation_history=["Hi!", "Hello!"], current_lead_score=20, questions_answered=[]
        )

        assert "suggested_question" in suggestion
        assert "reasoning" in suggestion
        assert "expected_impact" in suggestion
        assert "budget" in suggestion["suggested_question"].lower()

    def test_suggest_next_question_warm_lead(self):
        """Test question suggestion for warm lead."""
        optimizer = ConversationOptimizer()

        suggestion = optimizer.suggest_next_question(
            conversation_history=["Hi!", "Looking for homes", "Budget is $500k"],
            current_lead_score=55,
            questions_answered=["budget"],
        )

        assert "suggested_question" in suggestion
        assert suggestion["reasoning"]

    def test_suggest_next_question_hot_lead(self):
        """Test question suggestion for hot lead."""
        optimizer = ConversationOptimizer()

        suggestion = optimizer.suggest_next_question(
            conversation_history=["Hi!", "Budget $500k", "Need in 2 months", "Rancho Cucamonga area"],
            current_lead_score=75,
            questions_answered=["budget", "timeline", "location"],
        )

        assert "suggested_question" in suggestion
        # Should suggest appointment/viewing for hot leads
        assert any(
            word in suggestion["suggested_question"].lower() for word in ["schedule", "viewing", "appointment", "see"]
        )

    def test_suggestion_has_alternatives(self):
        """Test that suggestions include alternatives."""
        optimizer = ConversationOptimizer()

        suggestion = optimizer.suggest_next_question(
            conversation_history=[], current_lead_score=30, questions_answered=[]
        )

        assert "alternatives" in suggestion
        assert isinstance(suggestion["alternatives"], list)


class TestABTestStatistics:
    """Test statistical analysis of A/B tests."""

    def test_variant_stats_calculation(self):
        """Test calculation of variant statistics."""
        manager = ABTestManager("test_location")

        results = [{"lead_score": 70}, {"lead_score": 80}, {"lead_score": 75}, {"lead_score": 85}, {"lead_score": 78}]

        stats = manager._calculate_variant_stats(results, "lead_score")

        assert stats["count"] == 5
        assert stats["mean"] == 77.6
        assert stats["min"] == 70
        assert stats["max"] == 85
        assert stats["std_dev"] > 0

    def test_conversion_rate_calculation(self):
        """Test conversion rate metric calculation."""
        manager = ABTestManager("test_location")

        results = [
            {"conversion": True},
            {"conversion": False},
            {"conversion": True},
            {"conversion": True},
            {"conversion": False},
        ]

        stats = manager._calculate_variant_stats(results, "conversion_rate")

        assert stats["count"] == 5
        assert stats["mean"] == 0.6  # 3 out of 5 converted

    def test_winner_determination(self):
        """Test determining experiment winner."""
        manager = ABTestManager("test_location")

        exp_id = manager.create_experiment(name="Winner Test", variant_a={}, variant_b={}, metric="lead_score")

        # Make B clearly better than A
        for i in range(35):
            manager.record_result(exp_id, "a", {"lead_score": 60})
            manager.record_result(exp_id, "b", {"lead_score": 80})

        analysis = manager.analyze_experiment(exp_id)

        assert analysis["winner"] == "b"
        assert analysis["confidence"] > 0


class TestPerformanceOptimization:
    """Test performance optimization features."""

    def test_identify_opportunities_structure(self):
        """Test that opportunities are structured correctly."""
        analyzer = PerformanceAnalyzer("test_location")

        opportunities = analyzer._identify_opportunities([], {}, {})

        assert isinstance(opportunities, list)
        for opp in opportunities:
            assert "type" in opp
            assert "priority" in opp
            assert "recommendation" in opp
            assert "expected_impact" in opp

    def test_flow_analysis_structure(self):
        """Test conversation flow analysis structure."""
        analyzer = PerformanceAnalyzer("test_location")

        flow = analyzer._analyze_flow([])

        assert "optimal_length" in flow
        assert "quick_wins" in flow
        assert "long_conversions" in flow


class TestDataPersistence:
    """Test that A/B test data persists correctly."""

    def test_experiments_saved_to_file(self, tmp_path):
        """Test that experiments are saved to file."""
        manager = ABTestManager("test_location")

        exp_id = manager.create_experiment("Test", {}, {})

        # Verify file was created
        assert manager.experiments_file.exists()

        # Verify can reload
        manager2 = ABTestManager("test_location")
        assert exp_id in manager2.experiments["active"]

    def test_results_persist_across_sessions(self):
        """Test that results persist across manager instances."""
        manager1 = ABTestManager("test_location")

        exp_id = manager1.create_experiment("Persist Test", {}, {})
        manager1.record_result(exp_id, "a", {"lead_score": 75})

        # Create new manager instance
        manager2 = ABTestManager("test_location")

        results = manager2.experiments["active"][exp_id]["variants"]["a"]["results"]
        assert len(results) == 1
        assert results[0]["lead_score"] == 75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
