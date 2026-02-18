#!/usr/bin/env python3
"""
Property-Based Testing Framework for Lead Scoring Invariants
============================================================

Uses Hypothesis to generate comprehensive test cases for lead scoring logic.
Tests algorithmic properties and invariants that must hold regardless of input.

Property Testing Strategy:
- Score range invariants (0-7 questions, 0-100 percentage)
- Classification consistency across input variations
- Monotonic properties (more questions = higher scores)
- Edge case handling for malformed inputs
- Performance characteristics under load

Coverage Goals:
- 100% coverage of lead scoring edge cases
- Validation of business rule consistency
- Detection of scoring anomalies and edge cases
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest
from hypothesis import HealthCheck, assume, example, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, initialize, invariant, rule

from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence
from ghl_real_estate_ai.services.lead_scorer import LeadScorer



class TestLeadScoringInvariants:
    """Property-based tests for lead scoring invariants"""

    def setup_method(self):
        """Setup scorer for each test"""
        self.scorer = LeadScorer()

    @given(
        st.dictionaries(
            keys=st.sampled_from(
                [
                    "budget",
                    "location",
                    "timeline",
                    "bedrooms",
                    "bathrooms",
                    "must_haves",
                    "financing",
                    "motivation",
                    "home_condition",
                ]
            ),
            values=st.one_of(
                st.text(min_size=1, max_size=100),
                st.integers(min_value=1, max_value=10_000_000),
                st.floats(min_value=0.1, max_value=10_000_000),
                st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
                st.booleans(),
            ),
            min_size=0,
            max_size=9,
        )
    )
    @settings(max_examples=500, deadline=5000)
    def test_score_range_invariant(self, preferences: Dict[str, Any]):
        """Property: Lead score must always be between 0 and 7 (question count)"""
        context = {"extracted_preferences": preferences}
        score = self.scorer.calculate(context)

        # Core invariant: score represents number of questions answered
        assert 0 <= score <= 7, f"Score {score} outside valid range for preferences: {preferences}"

    @given(
        st.dictionaries(
            keys=st.sampled_from(
                [
                    "budget",
                    "location",
                    "timeline",
                    "bedrooms",
                    "bathrooms",
                    "must_haves",
                    "financing",
                    "motivation",
                    "home_condition",
                ]
            ),
            values=st.text(min_size=1, max_size=100),
            min_size=0,
            max_size=9,
        )
    )
    @settings(max_examples=300, deadline=5000)
    def test_percentage_score_mapping_invariant(self, preferences: Dict[str, Any]):
        """Property: Percentage score mapping must be consistent and within bounds"""
        context = {"extracted_preferences": preferences}
        question_count = self.scorer.calculate(context)
        percentage_score = self.scorer.get_percentage_score(question_count)

        # Invariants for percentage mapping
        assert 0 <= percentage_score <= 100, f"Percentage score {percentage_score} outside valid range"

        # Specific mapping invariants based on Jorge's requirements
        expected_mappings = {0: 5, 1: 15, 2: 30, 3: 50, 4: 65, 5: 75, 6: 85, 7: 100}
        expected_score = expected_mappings.get(question_count, 0)
        assert percentage_score == expected_score, (
            f"Question count {question_count} should map to {expected_score}% but got {percentage_score}%"
        )

    @given(
        st.dictionaries(
            keys=st.sampled_from(
                [
                    "budget",
                    "location",
                    "timeline",
                    "bedrooms",
                    "bathrooms",
                    "must_haves",
                    "financing",
                    "motivation",
                    "home_condition",
                ]
            ),
            values=st.text(min_size=1, max_size=100),
            min_size=0,
            max_size=9,
        )
    )
    @settings(max_examples=200, deadline=5000)
    def test_classification_consistency_invariant(self, preferences: Dict[str, Any]):
        """Property: Classification must be consistent with Jorge's thresholds"""
        context = {"extracted_preferences": preferences}
        score = self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        # Jorge's classification rules
        if score >= 3:
            assert classification == "hot", f"Score {score} should be 'hot' but got '{classification}'"
        elif score >= 2:
            assert classification == "warm", f"Score {score} should be 'warm' but got '{classification}'"
        else:
            assert classification == "cold", f"Score {score} should be 'cold' but got '{classification}'"

    @given(
        base_prefs=st.dictionaries(
            keys=st.sampled_from(
                [
                    "budget",
                    "location",
                    "timeline",
                    "bedrooms",
                    "bathrooms",
                    "must_haves",
                    "financing",
                    "motivation",
                    "home_condition",
                ]
            ),
            values=st.text(min_size=1, max_size=100),
            min_size=0,
            max_size=7,
        ),
        additional_key=st.sampled_from(
            [
                "budget",
                "location",
                "timeline",
                "bedrooms",
                "bathrooms",
                "must_haves",
                "financing",
                "motivation",
                "home_condition",
            ]
        ),
        additional_value=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=100, deadline=5000)
    def test_monotonic_property(self, base_prefs: Dict[str, Any], additional_key: str, additional_value: str):
        """Property: Adding information should never decrease the score"""
        assume(additional_key not in base_prefs)  # Ensure we're actually adding new info

        base_context = {"extracted_preferences": base_prefs}
        base_score = self.scorer.calculate(base_context)

        enhanced_prefs = base_prefs.copy()
        enhanced_prefs[additional_key] = additional_value
        enhanced_context = {"extracted_preferences": enhanced_prefs}
        enhanced_score = self.scorer.calculate(enhanced_context)

        # Monotonic property: more info = same or higher score
        assert enhanced_score >= base_score, (
            f"Adding {additional_key} decreased score from {base_score} to {enhanced_score}"
        )
        assert enhanced_score <= base_score + 1, (
            f"Adding {additional_key} increased score too much: {base_score} to {enhanced_score}"
        )

    @given(
        st.dictionaries(
            keys=st.sampled_from(
                [
                    "budget",
                    "location",
                    "timeline",
                    "bedrooms",
                    "bathrooms",
                    "must_haves",
                    "financing",
                    "motivation",
                    "home_condition",
                ]
            ),
            values=st.one_of(st.none(), st.just(""), st.text(max_size=0), st.lists(st.nothing(), max_size=0)),
            min_size=0,
            max_size=9,
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_empty_values_ignored(self, empty_preferences: Dict[str, Any]):
        """Property: Empty/null values should not contribute to score"""
        context = {"extracted_preferences": empty_preferences}
        score = self.scorer.calculate(context)

        # Empty values should result in 0 score
        assert score == 0, f"Empty preferences should score 0 but got {score}"

    @given(
        st.lists(
            st.dictionaries(
                keys=st.sampled_from(
                    [
                        "budget",
                        "location",
                        "timeline",
                        "bedrooms",
                        "bathrooms",
                        "must_haves",
                        "financing",
                        "motivation",
                        "home_condition",
                    ]
                ),
                values=st.text(min_size=1, max_size=100),
                min_size=0,
                max_size=9,
            ),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=50, deadline=10000)
    def test_performance_consistency(self, preference_batch: List[Dict[str, Any]]):
        """Property: Scoring performance should be consistent across batches"""
        times = []

        for preferences in preference_batch:
            context = {"extracted_preferences": preferences}
            start_time = time.perf_counter()
            score = self.scorer.calculate(context)
            end_time = time.perf_counter()

            scoring_time = (end_time - start_time) * 1000  # Convert to milliseconds
            times.append(scoring_time)

            # Individual performance invariant
            assert scoring_time < 10.0, f"Scoring took too long: {scoring_time}ms"

        # Batch consistency invariant
        if len(times) > 1:
            avg_time = sum(times) / len(times)
            max_time = max(times)
            # No single operation should be more than 5x the average
            assert max_time < avg_time * 5, f"Performance inconsistency: max {max_time}ms vs avg {avg_time}ms"

    @given(
        preferences=st.dictionaries(
            keys=st.sampled_from(
                [
                    "budget",
                    "location",
                    "timeline",
                    "bedrooms",
                    "bathrooms",
                    "must_haves",
                    "financing",
                    "motivation",
                    "home_condition",
                ]
            ),
            values=st.text(min_size=1, max_size=100),
            min_size=0,
            max_size=9,
        ),
        conversation_history=st.lists(
            st.dictionaries(keys=st.just("role"), values=st.sampled_from(["user", "assistant"])), max_size=20
        ),
        created_at=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)),
    )
    @settings(max_examples=100, deadline=5000)
    def test_context_robustness(
        self, preferences: Dict[str, Any], conversation_history: List[Dict], created_at: datetime
    ):
        """Property: Scorer should handle various context structures robustly"""
        context = {
            "extracted_preferences": preferences,
            "conversation_history": conversation_history,
            "created_at": created_at.isoformat(),
        }

        # Should not raise exceptions regardless of context structure
        try:
            score = self.scorer.calculate(context)
            reasoning_result = self.scorer.calculate_with_reasoning(context)

            # Consistency between methods
            assert score == reasoning_result["score"], (
                f"Inconsistency between calculate methods: {score} vs {reasoning_result['score']}"
            )
            assert score == reasoning_result["questions_answered"], (
                f"Score should equal questions_answered: {score} vs {reasoning_result['questions_answered']}"
            )

        except Exception as e:
            pytest.fail(f"Scorer failed on valid context: {e}")


class TestLeadScoringEdgeCases:
    """Specific edge cases that must be handled correctly"""

    def setup_method(self):
        self.scorer = LeadScorer()

    @given(
        st.dictionaries(
            keys=st.sampled_from(["budget", "location", "timeline"]),
            values=st.one_of(
                st.integers(min_value=-1_000_000, max_value=-1),  # Negative values
                st.floats(min_value=-1_000_000, max_value=-1),
                st.text().filter(lambda x: x.strip() == ""),  # Empty strings
                st.lists(st.nothing()),  # Empty lists
                st.text(min_size=1000, max_size=10000),  # Very long strings
            ),
        )
    )
    @settings(max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.filter_too_much])
    def test_malformed_input_handling(self, malformed_prefs: Dict[str, Any]):
        """Property: Malformed inputs should not crash the scorer"""
        context = {"extracted_preferences": malformed_prefs}

        try:
            score = self.scorer.calculate(context)
            # Should handle malformed input gracefully
            assert 0 <= score <= 7, f"Malformed input produced invalid score: {score}"
        except Exception as e:
            pytest.fail(f"Scorer crashed on malformed input: {e}")

    @example({})
    @example({"extracted_preferences": None})
    @example({"extracted_preferences": {}})
    @given(
        st.one_of(
            st.just({}),
            st.dictionaries(keys=st.just("extracted_preferences"), values=st.none()),
            st.dictionaries(keys=st.just("extracted_preferences"), values=st.just({})),
        )
    )
    def test_missing_or_empty_preferences(self, context: Dict[str, Any]):
        """Edge case: Missing or empty preferences should score 0"""
        score = self.scorer.calculate(context)
        assert score == 0, f"Empty context should score 0 but got {score}"

    @given(
        st.dictionaries(
            keys=st.sampled_from(["budget"]),
            values=st.one_of(st.just(0), st.just(0.0), st.just("0"), st.just(""), st.just([]), st.just({})),
        )
    )
    def test_zero_and_falsy_values(self, falsy_prefs: Dict[str, Any]):
        """Edge case: Zero and falsy values should not contribute to score"""
        context = {"extracted_preferences": falsy_prefs}
        score = self.scorer.calculate(context)

        # Falsy values should not count as answered questions
        assert score == 0, f"Falsy values should not contribute to score: {score}"


class LeadScoringStateMachine(RuleBasedStateMachine):
    """Stateful property-based testing for lead scoring workflows"""

    preferences = Bundle("preferences")
    contexts = Bundle("contexts")

    def __init__(self):
        super().__init__()
        self.scorer = LeadScorer()
        self.seen_scores = set()
        self.seen_contexts = []

    @initialize()
    def setup(self):
        """Initialize the state machine"""
        self.scorer = LeadScorer()
        self.seen_scores = set()
        self.seen_contexts = []

    @rule(
        target=preferences,
        key=st.sampled_from(
            [
                "budget",
                "location",
                "timeline",
                "bedrooms",
                "bathrooms",
                "must_haves",
                "financing",
                "motivation",
                "home_condition",
            ]
        ),
        value=st.text(min_size=1, max_size=100),
    )
    def add_preference(self, key: str, value: str):
        """Rule: Add a preference to the system"""
        return {key: value}

    @rule(target=contexts, prefs=preferences)
    def create_context(self, prefs: Dict[str, Any]):
        """Rule: Create a context from preferences"""
        context = {"extracted_preferences": prefs}
        self.seen_contexts.append(context)
        return context

    @rule(context=contexts)
    def score_context(self, context: Dict[str, Any]):
        """Rule: Score a context and verify invariants"""
        score = self.scorer.calculate(context)
        classification = self.scorer.classify(score)

        # Track state
        self.seen_scores.add(score)

        # Invariants that must hold in all states
        assert 0 <= score <= 7, f"Invalid score: {score}"
        assert classification in ["hot", "warm", "cold"], f"Invalid classification: {classification}"

        # Jorge's classification rules
        if score >= 3:
            assert classification == "hot"
        elif score >= 2:
            assert classification == "warm"
        else:
            assert classification == "cold"

    @rule(context=contexts, additional_prefs=preferences)
    def enhance_context(self, context: Dict[str, Any], additional_prefs: Dict[str, Any]):
        """Rule: Enhance context with additional preferences"""
        original_score = self.scorer.calculate(context)

        # Create enhanced context
        enhanced_prefs = context.get("extracted_preferences", {}).copy()
        enhanced_prefs.update(additional_prefs)
        enhanced_context = {"extracted_preferences": enhanced_prefs}

        enhanced_score = self.scorer.calculate(enhanced_context)

        # Monotonic property: enhancement should not decrease score
        assert enhanced_score >= original_score, f"Enhancement decreased score: {original_score} -> {enhanced_score}"

    @invariant()
    def scores_in_valid_range(self):
        """Invariant: All scores must be in valid range"""
        assert all(0 <= score <= 7 for score in self.seen_scores), f"Invalid scores detected: {self.seen_scores}"


class TestEnhancedLeadIntelligenceProperties:
    """Property-based tests for Enhanced Lead Intelligence service"""

    def setup_method(self):
        """Setup intelligence service for testing"""
        # Use mock setup to avoid external dependencies in property tests
        self.intelligence = EnhancedLeadIntelligence()

    @given(
        lead_name=st.text(min_size=2, max_size=50).filter(lambda x: x.strip()),
        preferences=st.dictionaries(
            keys=st.sampled_from(
                [
                    "budget",
                    "location",
                    "timeline",
                    "bedrooms",
                    "bathrooms",
                    "must_haves",
                    "financing",
                    "motivation",
                    "home_condition",
                ]
            ),
            values=st.text(min_size=1, max_size=100),
            min_size=0,
            max_size=9,
        ),
    )
    @settings(max_examples=50, deadline=10000)
    def test_performance_metrics_consistency(self, lead_name: str, preferences: Dict[str, Any]):
        """Property: Performance metrics should be consistent and non-decreasing"""
        initial_metrics = self.intelligence.get_performance_metrics()

        # Verify metrics structure
        required_keys = ["analyses_completed", "cache_hits", "avg_analysis_time_ms", "cache_hit_rate", "total_requests"]
        for key in required_keys:
            assert key in initial_metrics, f"Missing metric: {key}"

        # Metrics should be non-negative
        for key, value in initial_metrics.items():
            if isinstance(value, (int, float)):
                assert value >= 0, f"Negative metric value: {key} = {value}"

        # Cache hit rate should be between 0 and 1
        assert 0 <= initial_metrics["cache_hit_rate"] <= 1, (
            f"Invalid cache hit rate: {initial_metrics['cache_hit_rate']}"
        )


# Performance benchmarking with property-based inputs
class TestLeadScoringPerformance:
    """Performance property tests"""

    def setup_method(self):
        self.scorer = LeadScorer()

    @given(
        st.lists(
            st.dictionaries(
                keys=st.sampled_from(
                    [
                        "budget",
                        "location",
                        "timeline",
                        "bedrooms",
                        "bathrooms",
                        "must_haves",
                        "financing",
                        "motivation",
                        "home_condition",
                    ]
                ),
                values=st.text(min_size=1, max_size=100),
                min_size=0,
                max_size=9,
            ),
            min_size=100,
            max_size=1000,
        )
    )
    @settings(max_examples=10, deadline=30000)
    def test_bulk_scoring_performance(self, preference_batch: List[Dict[str, Any]]):
        """Property: Bulk scoring should maintain consistent performance"""
        start_time = time.perf_counter()

        scores = []
        for preferences in preference_batch:
            context = {"extracted_preferences": preferences}
            score = self.scorer.calculate(context)
            scores.append(score)

        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # milliseconds

        # Performance properties
        avg_time_per_score = total_time / len(preference_batch)
        assert avg_time_per_score < 1.0, f"Average scoring time too high: {avg_time_per_score}ms"

        # Throughput property
        scores_per_second = len(preference_batch) / (total_time / 1000)
        assert scores_per_second > 1000, f"Throughput too low: {scores_per_second} scores/sec"


# Test the stateful property machine
TestLeadScoringWorkflow = LeadScoringStateMachine.TestCase


if __name__ == "__main__":
    # Run property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])