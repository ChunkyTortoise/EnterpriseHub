import pytest

pytestmark = pytest.mark.integration

"""Tests for Jorge A/B Testing Service.

Covers experiment lifecycle, deterministic variant assignment, outcome recording,
statistical significance analysis, and edge cases.
"""

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_service import (
    ABTestingService,
    ExperimentResult,
)


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the ABTestingService singleton before and after each test."""
    ABTestingService.reset()
    yield
    ABTestingService.reset()


class TestABTestingService:
    """Tests for ABTestingService."""

    # ── 1. Experiment creation ────────────────────────────────────────

    def test_create_experiment_valid(self):
        """A valid experiment with 2+ variants is created successfully."""
        service = ABTestingService()
        result = service.create_experiment("greeting_style", ["formal", "casual", "empathetic"])

        assert result["experiment_id"] == "greeting_style"
        assert result["variants"] == ["formal", "casual", "empathetic"]
        assert result["status"] == "active"
        # Default equal split
        for variant in result["variants"]:
            assert pytest.approx(result["traffic_split"][variant], abs=1e-6) == 1 / 3

    def test_create_experiment_duplicate_raises(self):
        """Creating an experiment with an existing id raises ValueError."""
        service = ABTestingService()
        service.create_experiment("dup_test", ["a", "b"])

        with pytest.raises(ValueError, match="already exists"):
            service.create_experiment("dup_test", ["c", "d"])

    def test_create_experiment_single_variant_raises(self):
        """Creating an experiment with fewer than 2 variants raises ValueError."""
        service = ABTestingService()

        with pytest.raises(ValueError, match="at least 2 variants"):
            service.create_experiment("solo", ["only_one"])

    def test_create_experiment_bad_split_raises(self):
        """A traffic_split that does not sum to 1.0 raises ValueError."""
        service = ABTestingService()

        with pytest.raises(ValueError, match="sum to 1.0"):
            service.create_experiment(
                "bad_split",
                ["a", "b"],
                traffic_split={"a": 0.3, "b": 0.3},
            )

    # ── 5. Deterministic assignment ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_variant_deterministic(self):
        """The same contact+experiment always returns the same variant."""
        service = ABTestingService()
        service.create_experiment("det_test", ["x", "y"])

        variant_first = await service.get_variant("det_test", "contact_123")
        variant_second = await service.get_variant("det_test", "contact_123")
        variant_third = await service.get_variant("det_test", "contact_123")

        assert variant_first == variant_second == variant_third

    @pytest.mark.asyncio
    async def test_get_variant_distribution(self):
        """With enough contacts, all variants are eventually assigned."""
        service = ABTestingService()
        service.create_experiment("dist_test", ["alpha", "beta"])

        assigned_variants = set()
        for i in range(200):
            variant = await service.get_variant("dist_test", f"contact_{i}")
            assigned_variants.add(variant)

        assert assigned_variants == {"alpha", "beta"}

    # ── 7. Outcome recording ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_record_outcome_valid(self):
        """Recording a valid outcome returns a confirmation dict."""
        service = ABTestingService()
        service.create_experiment("outcome_test", ["a", "b"])
        variant = await service.get_variant("outcome_test", "contact_1")

        result = await service.record_outcome("outcome_test", "contact_1", variant, "conversion", value=2.5)

        assert result["experiment_id"] == "outcome_test"
        assert result["contact_id"] == "contact_1"
        assert result["variant"] == variant
        assert result["outcome"] == "conversion"
        assert result["value"] == 2.5

    @pytest.mark.asyncio
    async def test_record_outcome_invalid_outcome_raises(self):
        """An invalid outcome type raises ValueError."""
        service = ABTestingService()
        service.create_experiment("bad_outcome", ["a", "b"])
        variant = await service.get_variant("bad_outcome", "contact_1")

        with pytest.raises(ValueError, match="Invalid outcome"):
            await service.record_outcome("bad_outcome", "contact_1", variant, "not_a_real_outcome")

    # ── 9. Experiment results ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_experiment_results(self):
        """get_experiment_results returns an ExperimentResult with per-variant stats."""
        service = ABTestingService()
        service.create_experiment("results_test", ["a", "b"])

        # Assign contacts and record some outcomes
        for i in range(20):
            variant = await service.get_variant("results_test", f"c_{i}")
            if i % 3 == 0:
                await service.record_outcome("results_test", f"c_{i}", variant, "conversion")

        results = service.get_experiment_results("results_test")

        assert isinstance(results, ExperimentResult)
        assert results.experiment_id == "results_test"
        assert results.status == "active"
        assert results.total_impressions == 20
        assert results.total_conversions > 0
        assert len(results.variants) == 2
        for vs in results.variants:
            assert vs.impressions >= 0
            assert 0.0 <= vs.conversion_rate <= 1.0

    # ── 10. Statistical significance (true) ───────────────────────────

    @pytest.mark.asyncio
    async def test_is_significant_true(self):
        """With a large enough effect size and sample, significance is detected."""
        service = ABTestingService()
        service.create_experiment(
            "sig_test",
            ["winner", "loser"],
            traffic_split={"winner": 0.5, "loser": 0.5},
        )

        # Assign contacts deterministically and manufacture skewed outcomes
        winner_contacts = []
        loser_contacts = []
        for i in range(500):
            variant = await service.get_variant("sig_test", f"sig_c_{i}")
            if variant == "winner":
                winner_contacts.append(f"sig_c_{i}")
            else:
                loser_contacts.append(f"sig_c_{i}")

        # Record high conversion for winner, low for loser
        for cid in winner_contacts[: int(len(winner_contacts) * 0.8)]:
            await service.record_outcome("sig_test", cid, "winner", "conversion")
        for cid in loser_contacts[: int(len(loser_contacts) * 0.1)]:
            await service.record_outcome("sig_test", cid, "loser", "conversion")

        assert service.is_significant("sig_test") is True

    # ── 11. Statistical significance (false) ──────────────────────────

    @pytest.mark.asyncio
    async def test_is_significant_false(self):
        """With too little data, significance is not reached."""
        service = ABTestingService()
        service.create_experiment("insig_test", ["a", "b"])

        # Only 2 contacts, 1 outcome each -- not enough data
        va = await service.get_variant("insig_test", "c_only_1")
        vb_cid = "c_only_2"
        vb = await service.get_variant("insig_test", vb_cid)
        await service.record_outcome("insig_test", "c_only_1", va, "conversion")
        await service.record_outcome("insig_test", vb_cid, vb, "conversion")

        assert service.is_significant("insig_test") is False

    # ── 12. Deactivate experiment ─────────────────────────────────────

    def test_deactivate_experiment(self):
        """Deactivating an experiment sets its status to completed."""
        service = ABTestingService()
        service.create_experiment("deact_test", ["a", "b"])

        result = service.deactivate_experiment("deact_test")

        assert result["status"] == "completed"
        assert result["experiment_id"] == "deact_test"
        assert "duration_hours" in result

    # ── 13. List experiments ──────────────────────────────────────────

    def test_list_experiments(self):
        """list_experiments returns only active experiments."""
        service = ABTestingService()
        service.create_experiment("active_1", ["a", "b"])
        service.create_experiment("active_2", ["x", "y"])
        service.create_experiment("to_deact", ["m", "n"])
        service.deactivate_experiment("to_deact")

        active = service.list_experiments()
        active_ids = {e["experiment_id"] for e in active}

        assert active_ids == {"active_1", "active_2"}
        assert "to_deact" not in active_ids

    # ── 14. Hash determinism ──────────────────────────────────────────

    def test_hash_determinism(self):
        """The internal hash assignment produces the same result across calls."""
        variants = ["a", "b", "c"]
        split = {"a": 1 / 3, "b": 1 / 3, "c": 1 / 3}

        result_1 = ABTestingService._hash_assign("contact_42", "exp_7", variants, split)
        result_2 = ABTestingService._hash_assign("contact_42", "exp_7", variants, split)
        result_3 = ABTestingService._hash_assign("contact_42", "exp_7", variants, split)

        assert result_1 == result_2 == result_3
        assert result_1 in variants

    # ── 15. Get variant on inactive experiment ────────────────────────

    @pytest.mark.asyncio
    async def test_get_variant_inactive_raises(self):
        """Getting a variant from a deactivated experiment raises ValueError."""
        service = ABTestingService()
        service.create_experiment("inactive_test", ["a", "b"])
        service.deactivate_experiment("inactive_test")

        with pytest.raises(ValueError, match="not active"):
            await service.get_variant("inactive_test", "contact_1")
