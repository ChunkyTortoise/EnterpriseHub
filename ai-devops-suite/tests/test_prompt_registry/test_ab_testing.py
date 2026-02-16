"""Tests for ABTestingService: variant assignment, z-test, significance."""

import pytest

from devops_suite.prompt_registry.ab_testing import (
    ABTestingService,
    ExperimentConfig,
    Variant,
)


@pytest.fixture
def ab_service():
    return ABTestingService()


@pytest.fixture
def sample_experiment():
    return ExperimentConfig(
        experiment_id="exp-1",
        prompt_id="prompt-123",
        variants=[
            Variant(name="control", version_id=1, traffic_percentage=0.5),
            Variant(name="treatment", version_id=2, traffic_percentage=0.5),
        ],
        metric="latency",
        significance_threshold=0.95,
        min_samples=100,
    )


class TestABTestingService:
    def test_create_experiment(self, ab_service, sample_experiment):
        created = ab_service.create_experiment(sample_experiment)
        assert created.experiment_id == "exp-1"
        assert len(created.variants) == 2

    def test_create_experiment_invalid_traffic(self, ab_service):
        config = ExperimentConfig(
            experiment_id="exp-1",
            prompt_id="p1",
            variants=[
                Variant(name="a", version_id=1, traffic_percentage=0.4),
                Variant(name="b", version_id=2, traffic_percentage=0.4),
            ],
        )
        with pytest.raises(ValueError, match="must sum to 1.0"):
            ab_service.create_experiment(config)

    def test_get_experiment(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        fetched = ab_service.get_experiment("exp-1")
        assert fetched is not None
        assert fetched.prompt_id == "prompt-123"

    def test_get_nonexistent_experiment(self, ab_service):
        result = ab_service.get_experiment("fake-id")
        assert result is None

    def test_assign_variant_deterministic(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        # Same subject should always get same variant
        v1 = ab_service.assign_variant("exp-1", "user-123")
        v2 = ab_service.assign_variant("exp-1", "user-123")
        assert v1 == v2

    def test_assign_variant_distribution(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        assignments = {}
        for i in range(1000):
            variant = ab_service.assign_variant("exp-1", f"user-{i}")
            assignments[variant] = assignments.get(variant, 0) + 1
        # With 50/50 split, expect roughly equal distribution
        control_pct = assignments.get("control", 0) / 1000
        treatment_pct = assignments.get("treatment", 0) / 1000
        assert 0.45 < control_pct < 0.55
        assert 0.45 < treatment_pct < 0.55

    def test_assign_variant_nonexistent_experiment(self, ab_service):
        result = ab_service.assign_variant("fake-exp", "user-1")
        assert result is None

    def test_record_observation(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        success = ab_service.record_observation("exp-1", "control", 150.0)
        assert success is True
        exp = ab_service.get_experiment("exp-1")
        assert exp.variants[0].samples == 1
        assert exp.variants[0].metric_values == [150.0]

    def test_record_observation_nonexistent_experiment(self, ab_service):
        success = ab_service.record_observation("fake-exp", "control", 100.0)
        assert success is False

    def test_record_observation_nonexistent_variant(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        success = ab_service.record_observation("exp-1", "fake-variant", 100.0)
        assert success is False

    def test_compute_significance_insufficient_samples(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        ab_service.record_observation("exp-1", "control", 100.0)
        ab_service.record_observation("exp-1", "treatment", 90.0)
        result = ab_service.compute_significance("exp-1")
        assert result is not None
        assert result.is_significant is False
        assert result.confidence < 0.95

    def test_compute_significance_no_experiment(self, ab_service):
        result = ab_service.compute_significance("fake-exp")
        assert result is None

    def test_compute_significance_latency_metric(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        # Control: 200ms average with variance
        for i in range(100):
            ab_service.record_observation("exp-1", "control", 200.0 + (i % 10))
        # Treatment: 100ms average (50% improvement) with variance
        for i in range(100):
            ab_service.record_observation("exp-1", "treatment", 100.0 + (i % 10))

        result = ab_service.compute_significance("exp-1")
        assert result is not None
        assert result.is_significant is True
        assert result.winner == "treatment"  # Lower is better for latency
        assert 200.0 <= result.control_mean <= 210.0
        assert 100.0 <= result.variant_mean <= 110.0

    def test_compute_significance_quality_metric(self, ab_service):
        config = ExperimentConfig(
            experiment_id="exp-quality",
            prompt_id="p1",
            variants=[
                Variant(name="control", version_id=1, traffic_percentage=0.5),
                Variant(name="treatment", version_id=2, traffic_percentage=0.5),
            ],
            metric="quality",  # Higher is better
            min_samples=50,
        )
        ab_service.create_experiment(config)

        # Control: 70% quality with variance
        for i in range(50):
            ab_service.record_observation("exp-quality", "control", 70.0 + (i % 5))
        # Treatment: 90% quality with variance
        for i in range(50):
            ab_service.record_observation("exp-quality", "treatment", 90.0 + (i % 5))

        result = ab_service.compute_significance("exp-quality")
        assert result is not None
        assert result.winner == "treatment"  # Higher is better for quality

    def test_compute_significance_no_variance(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        # All samples identical
        for _ in range(100):
            ab_service.record_observation("exp-1", "control", 100.0)
            ab_service.record_observation("exp-1", "treatment", 100.0)

        result = ab_service.compute_significance("exp-1")
        assert result is not None
        # No variance means z-score calculation would divide by zero
        assert result.is_significant is False

    def test_list_experiments(self, ab_service):
        exp1 = ExperimentConfig(
            experiment_id="exp-1", prompt_id="p1",
            variants=[Variant(name="a", version_id=1, traffic_percentage=1.0)],
        )
        exp2 = ExperimentConfig(
            experiment_id="exp-2", prompt_id="p2",
            variants=[Variant(name="b", version_id=2, traffic_percentage=1.0)],
        )
        ab_service.create_experiment(exp1)
        ab_service.create_experiment(exp2)
        experiments = ab_service.list_experiments()
        assert len(experiments) == 2
        assert {e.experiment_id for e in experiments} == {"exp-1", "exp-2"}

    def test_uneven_traffic_split(self, ab_service):
        config = ExperimentConfig(
            experiment_id="exp-uneven",
            prompt_id="p1",
            variants=[
                Variant(name="control", version_id=1, traffic_percentage=0.7),
                Variant(name="treatment", version_id=2, traffic_percentage=0.3),
            ],
        )
        ab_service.create_experiment(config)

        assignments = {}
        for i in range(1000):
            variant = ab_service.assign_variant("exp-uneven", f"user-{i}")
            assignments[variant] = assignments.get(variant, 0) + 1

        control_pct = assignments.get("control", 0) / 1000
        treatment_pct = assignments.get("treatment", 0) / 1000
        assert 0.65 < control_pct < 0.75
        assert 0.25 < treatment_pct < 0.35

    def test_three_way_test(self, ab_service):
        config = ExperimentConfig(
            experiment_id="exp-3way",
            prompt_id="p1",
            variants=[
                Variant(name="a", version_id=1, traffic_percentage=0.33),
                Variant(name="b", version_id=2, traffic_percentage=0.33),
                Variant(name="c", version_id=3, traffic_percentage=0.34),
            ],
        )
        ab_service.create_experiment(config)

        assignments = {}
        for i in range(1000):
            variant = ab_service.assign_variant("exp-3way", f"user-{i}")
            assignments[variant] = assignments.get(variant, 0) + 1

        # Each variant should get roughly 1/3
        for variant_name in ["a", "b", "c"]:
            pct = assignments.get(variant_name, 0) / 1000
            assert 0.28 < pct < 0.38

    def test_confidence_calculation(self, ab_service, sample_experiment):
        ab_service.create_experiment(sample_experiment)
        # Minimal samples to check confidence < threshold
        for _ in range(10):
            ab_service.record_observation("exp-1", "control", 100.0)
            ab_service.record_observation("exp-1", "treatment", 110.0)

        result = ab_service.compute_significance("exp-1")
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0
        assert result.p_value == pytest.approx(1 - result.confidence)
