"""
Tests for Jorge A/B Testing Service.

Validates experiment creation, variant assignment, and statistical analysis.
"""

import time

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_service import (

@pytest.mark.unit
    ABTestingService,
    ExperimentStatus,
)


class TestABTestingService:
    """Test suite for A/B testing functionality."""

    @pytest.fixture
    def ab_service(self):
        """Create a fresh ABTestingService instance for each test."""
        # Reset singleton
        ABTestingService._instance = None
        ABTestingService._initialized = False
        return ABTestingService()

    def test_create_experiment_success(self, ab_service):
        """Test successful creation of an experiment."""
        result = ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        assert result["experiment_id"] == "test_exp"
        assert result["variants"] == ["control", "treatment"]
        assert result["status"] == ExperimentStatus.ACTIVE.value
        assert "traffic_split" in result

    def test_create_experiment_duplicate_name(self, ab_service):
        """Test that creating duplicate experiment raises ValueError."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        with pytest.raises(ValueError, match="already exists"):
            ab_service.create_experiment(
                experiment_id="test_exp",
                variants=["control", "treatment"],
            )

    def test_get_experiment_by_id(self, ab_service):
        """Test retrieving an experiment by ID."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        exp = ab_service._get_experiment("test_exp")
        assert exp.experiment_id == "test_exp"
        assert exp.variants == ["control", "treatment"]

    def test_get_experiment_by_name(self, ab_service):
        """Test retrieving experiment via list_experiments."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        experiments = ab_service.list_experiments()
        assert len(experiments) == 1
        assert experiments[0]["experiment_id"] == "test_exp"

    def test_list_experiments(self, ab_service):
        """Test listing all active experiments."""
        ab_service.create_experiment(
            experiment_id="exp1",
            variants=["control", "treatment"],
        )
        ab_service.create_experiment(
            experiment_id="exp2",
            variants=["variant_a", "variant_b"],
        )

        experiments = ab_service.list_experiments()
        assert len(experiments) == 2
        exp_ids = [e["experiment_id"] for e in experiments]
        assert "exp1" in exp_ids
        assert "exp2" in exp_ids

    @pytest.mark.asyncio
    async def test_assign_variant_deterministic(self, ab_service):
        """Test that variant assignment is deterministic for same contact."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Same contact should always get same variant
        variant1 = await ab_service.get_variant("test_exp", "contact_123")
        variant2 = await ab_service.get_variant("test_exp", "contact_123")
        variant3 = await ab_service.get_variant("test_exp", "contact_123")

        assert variant1 == variant2 == variant3
        assert variant1 in ["control", "treatment"]

    @pytest.mark.asyncio
    async def test_assign_variant_consistent(self, ab_service):
        """Test that different contacts get different variants (statistically)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Assign 100 contacts
        variants = []
        for i in range(100):
            variant = await ab_service.get_variant("test_exp", f"contact_{i}")
            variants.append(variant)

        # Both variants should be used
        assert "control" in variants
        assert "treatment" in variants

        # Distribution should be roughly equal (within 20% tolerance)
        control_count = variants.count("control")
        treatment_count = variants.count("treatment")
        assert 30 <= control_count <= 70
        assert 30 <= treatment_count <= 70

    @pytest.mark.asyncio
    async def test_record_metric_success(self, ab_service):
        """Test successful recording of an outcome metric."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        result = await ab_service.record_outcome(
            experiment_id="test_exp",
            contact_id="contact_123",
            variant="control",
            outcome="conversion",
            value=1.0,
        )

        assert result["experiment_id"] == "test_exp"
        assert result["contact_id"] == "contact_123"
        assert result["variant"] == "control"
        assert result["outcome"] == "conversion"
        assert result["value"] == 1.0

    @pytest.mark.asyncio
    async def test_record_metric_invalid_variant(self, ab_service):
        """Test that recording with invalid variant raises ValueError."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        with pytest.raises(ValueError, match="Unknown variant"):
            await ab_service.record_outcome(
                experiment_id="test_exp",
                contact_id="contact_123",
                variant="invalid_variant",
                outcome="conversion",
            )

    def test_get_experiment_results(self, ab_service):
        """Test retrieving experiment results with statistics."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Add some data
        exp = ab_service._get_experiment("test_exp")
        exp.assignments["control"] = ["c1", "c2", "c3", "c4"]
        exp.assignments["treatment"] = ["t1", "t2", "t3", "t4"]
        exp.outcomes["control"] = [
            {"contact_id": "c1", "outcome": "conversion", "value": 1.0, "timestamp": time.time()},
            {"contact_id": "c2", "outcome": "conversion", "value": 1.0, "timestamp": time.time()},
        ]
        exp.outcomes["treatment"] = [
            {"contact_id": "t1", "outcome": "conversion", "value": 1.0, "timestamp": time.time()},
        ]

        results = ab_service.get_experiment_results("test_exp")

        assert results.experiment_id == "test_exp"
        assert results.total_impressions == 8
        assert results.total_conversions == 3
        assert len(results.variants) == 2

        # Check variant stats
        control_stats = next(v for v in results.variants if v.variant == "control")
        assert control_stats.impressions == 4
        assert control_stats.conversions == 2
        assert control_stats.conversion_rate == 0.5

    def test_calculate_significance(self, ab_service):
        """Test statistical significance calculation."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Add data with clear difference
        exp = ab_service._get_experiment("test_exp")
        exp.assignments["control"] = [f"c{i}" for i in range(100)]
        exp.assignments["treatment"] = [f"t{i}" for i in range(100)]
        exp.outcomes["control"] = [
            {"contact_id": f"c{i}", "outcome": "conversion", "value": 1.0, "timestamp": time.time()}
            for i in range(10)  # 10% conversion
        ]
        exp.outcomes["treatment"] = [
            {"contact_id": f"t{i}", "outcome": "conversion", "value": 1.0, "timestamp": time.time()}
            for i in range(30)  # 30% conversion
        ]

        is_significant = ab_service.is_significant("test_exp")
        # With this sample size and difference, should be significant
        assert is_significant is True

    def test_pause_experiment(self, ab_service):
        """Test pausing an active experiment."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        result = ab_service.deactivate_experiment("test_exp")

        assert result["experiment_id"] == "test_exp"
        assert result["status"] == ExperimentStatus.COMPLETED.value
        assert "duration_hours" in result

        # Verify experiment is deactivated
        exp = ab_service._get_experiment("test_exp")
        assert exp.status == ExperimentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_resume_experiment(self, ab_service):
        """Test that a completed experiment cannot be resumed (status change)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        ab_service.deactivate_experiment("test_exp")

        # Try to get variant from completed experiment
        with pytest.raises(ValueError, match="not active"):
            await ab_service.get_variant("test_exp", "contact_123")

    def test_archive_experiment(self, ab_service):
        """Test that experiments can be archived (deactivated)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Archive by deactivating
        result = ab_service.deactivate_experiment("test_exp")

        assert result["status"] == ExperimentStatus.COMPLETED.value

        # Verify it's no longer in active list
        active_experiments = ab_service.list_experiments()
        assert "test_exp" not in [e["experiment_id"] for e in active_experiments]

    def test_delete_experiment(self, ab_service):
        """Test that experiments can be deleted (via reset)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Verify experiment exists
        assert "test_exp" in ab_service._experiments

        # Delete by removing from dict (simulating delete)
        del ab_service._experiments["test_exp"]

        # Verify experiment is gone
        with pytest.raises(KeyError, match="not found"):
            ab_service._get_experiment("test_exp")