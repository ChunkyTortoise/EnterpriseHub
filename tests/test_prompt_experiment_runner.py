from __future__ import annotations
import pytest
pytestmark = pytest.mark.integration

"""Tests for Jorge Prompt Experiment Runner."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from ghl_real_estate_ai.services.jorge.prompt_experiment_runner import (

    ExperimentResult,
    PromptExperiment,
    PromptExperimentRunner,
    PromptVariant,
    VariantStats,
)

# ---------------------------------------------------------------------------
# PromptVariant dataclass
# ---------------------------------------------------------------------------


class TestPromptVariant:
    def test_create_basic(self):
        v = PromptVariant(name="formal", prompt_template="Dear {name},", description="Formal")
        assert v.name == "formal"
        assert v.prompt_template == "Dear {name},"
        assert v.description == "Formal"

    def test_default_description(self):
        v = PromptVariant(name="test", prompt_template="Hi")
        assert v.description == ""


# ---------------------------------------------------------------------------
# PromptExperiment dataclass
# ---------------------------------------------------------------------------


class TestPromptExperiment:
    def test_create(self):
        variants = [
            PromptVariant("a", "template_a"),
            PromptVariant("b", "template_b"),
        ]
        exp = PromptExperiment(
            name="test_exp",
            variants=variants,
            traffic_split={"a": 0.5, "b": 0.5},
        )
        assert exp.name == "test_exp"
        assert exp.status == "active"
        assert exp.metric == "conversion"
        assert len(exp.variants) == 2

    def test_default_metric(self):
        exp = PromptExperiment(
            name="x", variants=[], traffic_split={}, metric="engagement"
        )
        assert exp.metric == "engagement"


# ---------------------------------------------------------------------------
# VariantStats and ExperimentResult dataclasses
# ---------------------------------------------------------------------------


class TestDataclasses:
    def test_variant_stats_defaults(self):
        vs = VariantStats(variant_name="control")
        assert vs.sample_size == 0
        assert vs.successes == 0
        assert vs.mean_score == 0.0
        assert vs.std_dev == 0.0

    def test_experiment_result_defaults(self):
        er = ExperimentResult(experiment_name="test", variant_stats={})
        assert er.winner is None
        assert er.p_value == 1.0
        assert er.confidence == 0.0
        assert er.is_significant is False


# ---------------------------------------------------------------------------
# Experiment creation
# ---------------------------------------------------------------------------


class TestCreateExperiment:
    def setup_method(self):
        self.runner = PromptExperimentRunner()

    def test_create_basic(self):
        variants = [
            PromptVariant("a", "template_a", "Variant A"),
            PromptVariant("b", "template_b", "Variant B"),
        ]
        exp = self.runner.create_experiment("test", variants)
        assert isinstance(exp, PromptExperiment)
        assert exp.name == "test"
        assert exp.status == "active"
        assert len(exp.variants) == 2

    def test_equal_traffic_split(self):
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        exp = self.runner.create_experiment("test", variants)
        assert abs(exp.traffic_split["a"] - 0.5) < 1e-9
        assert abs(exp.traffic_split["b"] - 0.5) < 1e-9

    def test_custom_traffic_split(self):
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        exp = self.runner.create_experiment(
            "test", variants, traffic_split={"a": 0.7, "b": 0.3}
        )
        assert exp.traffic_split["a"] == 0.7

    def test_duplicate_name_raises(self):
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        self.runner.create_experiment("test", variants)
        with pytest.raises(ValueError, match="already exists"):
            self.runner.create_experiment("test", variants)

    def test_fewer_than_two_variants_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            self.runner.create_experiment("test", [PromptVariant("a", "a")])

    def test_duplicate_variant_names_raises(self):
        variants = [PromptVariant("a", "t1"), PromptVariant("a", "t2")]
        with pytest.raises(ValueError, match="unique"):
            self.runner.create_experiment("test", variants)

    def test_bad_traffic_split_sum_raises(self):
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        with pytest.raises(ValueError, match="sum to 1.0"):
            self.runner.create_experiment(
                "test", variants, traffic_split={"a": 0.5, "b": 0.3}
            )

    def test_bad_traffic_split_keys_raises(self):
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        with pytest.raises(ValueError, match="must match"):
            self.runner.create_experiment(
                "test", variants, traffic_split={"a": 0.5, "c": 0.5}
            )

    def test_custom_metric(self):
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        exp = self.runner.create_experiment("test", variants, metric="engagement")
        assert exp.metric == "engagement"


# ---------------------------------------------------------------------------
# Variant assignment
# ---------------------------------------------------------------------------


class TestAssignVariant:
    def setup_method(self):
        self.runner = PromptExperimentRunner()
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        self.runner.create_experiment("test", variants)

    def test_returns_valid_variant(self):
        result = self.runner.assign_variant("test", "contact_1")
        assert result in ("a", "b")

    def test_deterministic(self):
        """Same contact + experiment always gets same variant."""
        v1 = self.runner.assign_variant("test", "contact_1")
        v2 = self.runner.assign_variant("test", "contact_1")
        assert v1 == v2

    def test_different_contacts_may_differ(self):
        """Different contacts can get different variants (statistical)."""
        assignments = set()
        for i in range(100):
            v = self.runner.assign_variant("test", f"contact_{i}")
            assignments.add(v)
        # With 100 contacts and 50/50 split, both variants should appear
        assert len(assignments) == 2

    def test_nonexistent_experiment_raises(self):
        with pytest.raises(KeyError, match="not found"):
            self.runner.assign_variant("nonexistent", "contact_1")

    def test_inactive_experiment_raises(self):
        self.runner._experiments["test"].status = "completed"
        with pytest.raises(ValueError, match="not active"):
            self.runner.assign_variant("test", "contact_1")


# ---------------------------------------------------------------------------
# Outcome recording
# ---------------------------------------------------------------------------


class TestRecordOutcome:
    def setup_method(self):
        self.runner = PromptExperimentRunner()
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        self.runner.create_experiment("test", variants)

    def test_record_basic(self):
        self.runner.record_outcome("test", "c1", "a", score=0.8, success=True)
        assert len(self.runner._outcomes["test"]) == 1

    def test_record_multiple(self):
        for i in range(10):
            self.runner.record_outcome("test", f"c{i}", "a", score=0.5)
        assert len(self.runner._outcomes["test"]) == 10

    def test_invalid_variant_raises(self):
        with pytest.raises(ValueError, match="Unknown variant"):
            self.runner.record_outcome("test", "c1", "nonexistent")

    def test_nonexistent_experiment_raises(self):
        with pytest.raises(KeyError, match="not found"):
            self.runner.record_outcome("nonexistent", "c1", "a")

    def test_default_values(self):
        self.runner.record_outcome("test", "c1", "a")
        outcome = self.runner._outcomes["test"][0]
        assert outcome.score == 1.0
        assert outcome.success is True


# ---------------------------------------------------------------------------
# Analysis (z-test)
# ---------------------------------------------------------------------------


class TestAnalyze:
    def setup_method(self):
        self.runner = PromptExperimentRunner()
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        self.runner.create_experiment("test", variants)

    def test_no_outcomes(self):
        result = self.runner.analyze("test")
        assert isinstance(result, ExperimentResult)
        assert result.winner is None
        assert result.is_significant is False
        assert result.p_value == 1.0

    def test_equal_outcomes_not_significant(self):
        for i in range(20):
            self.runner.record_outcome("test", f"c{i}", "a", success=True)
            self.runner.record_outcome("test", f"c{i}", "b", success=True)
        result = self.runner.analyze("test")
        assert result.is_significant is False
        assert result.winner is None

    def test_significant_difference(self):
        # Variant a: 90% success, variant b: 10% success
        for i in range(100):
            self.runner.record_outcome("test", f"a{i}", "a", success=(i < 90))
            self.runner.record_outcome("test", f"b{i}", "b", success=(i < 10))
        result = self.runner.analyze("test")
        assert result.is_significant is True
        assert result.winner == "a"
        assert result.p_value < 0.05

    def test_variant_stats_populated(self):
        self.runner.record_outcome("test", "c1", "a", score=0.9, success=True)
        self.runner.record_outcome("test", "c2", "b", score=0.5, success=False)
        result = self.runner.analyze("test")
        assert "a" in result.variant_stats
        assert "b" in result.variant_stats
        assert result.variant_stats["a"].sample_size == 1
        assert result.variant_stats["a"].successes == 1
        assert result.variant_stats["b"].successes == 0

    def test_mean_score_calculation(self):
        self.runner.record_outcome("test", "c1", "a", score=0.8)
        self.runner.record_outcome("test", "c2", "a", score=0.6)
        result = self.runner.analyze("test")
        assert abs(result.variant_stats["a"].mean_score - 0.7) < 0.01

    def test_nonexistent_experiment_raises(self):
        with pytest.raises(KeyError, match="not found"):
            self.runner.analyze("nonexistent")


# ---------------------------------------------------------------------------
# Early stopping
# ---------------------------------------------------------------------------


class TestShouldStopEarly:
    def setup_method(self):
        self.runner = PromptExperimentRunner()
        variants = [PromptVariant("a", "a"), PromptVariant("b", "b")]
        self.runner.create_experiment("test", variants)

    def test_insufficient_samples(self):
        for i in range(10):
            self.runner.record_outcome("test", f"c{i}", "a", success=True)
            self.runner.record_outcome("test", f"c{i}", "b", success=False)
        assert self.runner.should_stop_early("test") is False

    def test_sufficient_samples_significant(self):
        # Clear difference with enough samples
        for i in range(50):
            self.runner.record_outcome("test", f"a{i}", "a", success=True)
            self.runner.record_outcome("test", f"b{i}", "b", success=False)
        assert self.runner.should_stop_early("test") is True

    def test_sufficient_samples_not_significant(self):
        # Equal outcomes — should not stop
        for i in range(50):
            self.runner.record_outcome("test", f"a{i}", "a", success=True)
            self.runner.record_outcome("test", f"b{i}", "b", success=True)
        assert self.runner.should_stop_early("test") is False

    def test_nonexistent_experiment_raises(self):
        with pytest.raises(KeyError, match="not found"):
            self.runner.should_stop_early("nonexistent")