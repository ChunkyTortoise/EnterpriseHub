import pytest

pytestmark = pytest.mark.integration

"""
A/B Testing Workflow Integration Tests

End-to-end tests for the ABTestingService covering:
- Deterministic variant assignment consistency across sessions
- Outcome recording and aggregation
- Statistical significance calculation via two-proportion z-test
- Winning variant identification with skewed conversion data
- Bot-level variant assignment and outcome recording
"""

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService


@pytest.fixture(autouse=True)
def reset_ab():
    """Reset ABTestingService singleton before and after each test."""
    ABTestingService.reset()
    yield
    ABTestingService.reset()


class TestABTestingWorkflow:
    """End-to-end A/B testing workflow integration tests."""

    @pytest.mark.asyncio
    async def test_consistent_variant_across_sessions(self):
        """Create an experiment, get the variant for the same contact 10 times,
        and verify that the assignment is identical every time (deterministic
        hash-based bucketing)."""
        service = ABTestingService()

        service.create_experiment(
            "greeting_style",
            ["formal", "casual", "empathetic"],
        )

        contact_id = "contact_abc123"
        first_variant = await service.get_variant("greeting_style", contact_id)

        # Call get_variant 9 more times for the same contact
        for i in range(9):
            variant = await service.get_variant("greeting_style", contact_id)
            assert variant == first_variant, (
                f"Variant changed on call {i + 2}: expected '{first_variant}', got '{variant}'"
            )

        # Verify the contact appears exactly once in the assignments
        # (get_variant deduplicates assignment tracking)
        results = service.get_experiment_results("greeting_style")
        assert results.total_impressions == 1, f"Expected 1 unique impression, got {results.total_impressions}"

    @pytest.mark.asyncio
    async def test_outcomes_recorded_correctly(self):
        """Create an experiment, assign variants to 5 contacts, record
        outcomes for each, and verify total_impressions and total_conversions
        in get_experiment_results."""
        service = ABTestingService()

        service.create_experiment(
            "cta_test",
            ["direct", "soft"],
            traffic_split={"direct": 0.5, "soft": 0.5},
        )

        contacts = [f"contact_{i}" for i in range(5)]
        assignments = {}

        # Assign variants and record outcomes
        for contact_id in contacts:
            variant = await service.get_variant("cta_test", contact_id)
            assignments[contact_id] = variant

            await service.record_outcome(
                "cta_test",
                contact_id,
                variant,
                "conversion",
                value=1.0,
            )

        results = service.get_experiment_results("cta_test")

        # 5 contacts assigned, 5 outcomes recorded
        assert results.total_impressions == 5, f"Expected 5 impressions, got {results.total_impressions}"
        assert results.total_conversions == 5, f"Expected 5 conversions, got {results.total_conversions}"

        # Verify per-variant data is consistent
        variant_map = {}
        for vs in results.variants:
            variant_map[vs.variant] = vs

        for contact_id, variant in assignments.items():
            assert variant in variant_map, f"Variant '{variant}' not found in results"

        # Each variant should have at least 1 impression
        for vs in results.variants:
            if vs.impressions > 0:
                assert vs.conversions > 0, f"Variant '{vs.variant}' has {vs.impressions} impressions but 0 conversions"
                assert vs.conversion_rate > 0.0

    @pytest.mark.asyncio
    async def test_significance_calculation(self):
        """Create an experiment with 2 variants. Assign 100 contacts using
        deterministic bucketing, then record many conversions for the
        higher-performing variant and few for the other. Verify statistical
        significance is detected and the correct winner is identified."""
        service = ABTestingService()

        service.create_experiment(
            "response_tone",
            ["variant_a", "variant_b"],
            traffic_split={"variant_a": 0.5, "variant_b": 0.5},
        )

        # Assign 100 contacts -- hash bucketing will split them roughly 50/50
        contacts = [f"contact_{i:04d}" for i in range(100)]
        contact_variants = {}

        for contact_id in contacts:
            variant = await service.get_variant("response_tone", contact_id)
            contact_variants[contact_id] = variant

        # Count assignments per variant
        variant_a_contacts = [c for c, v in contact_variants.items() if v == "variant_a"]
        variant_b_contacts = [c for c, v in contact_variants.items() if v == "variant_b"]

        # Record conversions: ~90% for variant_a, ~10% for variant_b
        # This creates a strong signal for significance detection
        for contact_id in variant_a_contacts:
            # 90% of variant_a contacts convert
            if hash(contact_id) % 10 != 0:
                await service.record_outcome(
                    "response_tone",
                    contact_id,
                    "variant_a",
                    "conversion",
                    value=1.0,
                )

        for contact_id in variant_b_contacts:
            # 10% of variant_b contacts convert
            if hash(contact_id) % 10 == 0:
                await service.record_outcome(
                    "response_tone",
                    contact_id,
                    "variant_b",
                    "conversion",
                    value=1.0,
                )

        results = service.get_experiment_results("response_tone")

        # With ~45 contacts per variant and 90% vs 10% conversion rates,
        # the z-test should detect significance
        assert results.is_significant is True, f"Expected significance=True, got False (p_value={results.p_value})"
        assert results.winner == "variant_a", f"Expected winner='variant_a', got '{results.winner}'"
        assert results.p_value is not None
        assert results.p_value < 0.05, f"Expected p_value < 0.05, got {results.p_value}"

        # Also verify via the convenience method
        assert service.is_significant("response_tone") is True

    @pytest.mark.asyncio
    async def test_winning_variant_identification(self):
        """Create an experiment with highly skewed outcomes (one variant
        at ~90% conversion, the other at ~10%) and verify
        get_experiment_results identifies the correct winner."""
        service = ABTestingService()

        service.create_experiment(
            "handoff_style",
            ["aggressive", "gentle"],
            traffic_split={"aggressive": 0.5, "gentle": 0.5},
        )

        # Manually assign and record outcomes with extreme skew.
        # We record outcomes directly (contacts still need variant assignment).
        aggressive_contacts = [f"agg_{i}" for i in range(50)]
        gentle_contacts = [f"gen_{i}" for i in range(50)]

        # Assign all contacts to their intended variant by getting their
        # actual assigned variant first, then recording outcomes accordingly.
        # To guarantee placement, we assign all contacts and then record
        # outcomes based on whichever variant they actually land in.
        all_contacts = aggressive_contacts + gentle_contacts
        variant_a_ids = []
        variant_b_ids = []

        for contact_id in all_contacts:
            variant = await service.get_variant("handoff_style", contact_id)
            if variant == "aggressive":
                variant_a_ids.append(contact_id)
            else:
                variant_b_ids.append(contact_id)

        # Record 90% conversion for "aggressive" variant
        conversions_a = int(len(variant_a_ids) * 0.9)
        for contact_id in variant_a_ids[:conversions_a]:
            await service.record_outcome(
                "handoff_style",
                contact_id,
                "aggressive",
                "conversion",
                value=1.0,
            )

        # Record 10% conversion for "gentle" variant
        conversions_b = max(1, int(len(variant_b_ids) * 0.1))
        for contact_id in variant_b_ids[:conversions_b]:
            await service.record_outcome(
                "handoff_style",
                contact_id,
                "gentle",
                "conversion",
                value=1.0,
            )

        results = service.get_experiment_results("handoff_style")

        # Find the variant stats
        variant_stats = {vs.variant: vs for vs in results.variants}

        # The "aggressive" variant should have a much higher conversion rate
        agg_rate = variant_stats["aggressive"].conversion_rate
        gen_rate = variant_stats["gentle"].conversion_rate
        assert agg_rate > gen_rate, f"Expected {agg_rate} > {gen_rate}"

        # With 50+ contacts per variant and 90% vs 10%, significance should hold
        assert results.is_significant is True, f"Expected significance=True (p_value={results.p_value})"
        assert results.winner == "aggressive", f"Expected winner='aggressive', got '{results.winner}'"

        # Verify total impressions match
        assert results.total_impressions == len(all_contacts)

        # Verify total conversions match what we recorded
        assert results.total_conversions == conversions_a + conversions_b


class TestBotABIntegration:
    """Tests verifying A/B testing integration in bot process workflows."""

    @pytest.mark.asyncio
    async def test_response_tone_experiment_registered_by_bots(self):
        """All bots register the response_tone experiment on init.

        Simulate the registration that happens in each bot's _init_ab_experiments()
        and verify the experiment is queryable.
        """
        service = ABTestingService()

        # Replicate what each bot does in _init_ab_experiments()
        try:
            service.create_experiment(
                ABTestingService.RESPONSE_TONE_EXPERIMENT,
                ["formal", "casual", "empathetic"],
            )
        except ValueError:
            pass  # Already exists

        # Verify variants are the expected set
        results = service.get_experiment_results(ABTestingService.RESPONSE_TONE_EXPERIMENT)
        variant_names = {vs.variant for vs in results.variants}
        assert variant_names == {"formal", "casual", "empathetic"}

    @pytest.mark.asyncio
    async def test_variant_assignment_deterministic_per_contact(self):
        """Same contact always gets the same variant for response_tone."""
        service = ABTestingService()
        service.create_experiment(
            ABTestingService.RESPONSE_TONE_EXPERIMENT,
            ["formal", "casual", "empathetic"],
        )

        contact = "contact-buyer-001"
        first = await service.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, contact)
        for _ in range(5):
            assert await service.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, contact) == first

    @pytest.mark.asyncio
    async def test_outcome_recording_matches_variant(self):
        """record_outcome with 'response' outcome accumulates correctly."""
        service = ABTestingService()
        service.create_experiment(
            ABTestingService.RESPONSE_TONE_EXPERIMENT,
            ["formal", "casual", "empathetic"],
        )

        contacts = [f"contact-{i}" for i in range(10)]
        for contact_id in contacts:
            variant = await service.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, contact_id)
            await service.record_outcome(
                ABTestingService.RESPONSE_TONE_EXPERIMENT,
                contact_id,
                variant,
                "response",
            )

        results = service.get_experiment_results(ABTestingService.RESPONSE_TONE_EXPERIMENT)
        # All 10 contacts should be impressions
        assert results.total_impressions == 10
        # All 10 contacts recorded an outcome (response counts as conversion)
        assert results.total_conversions == 10

    @pytest.mark.asyncio
    async def test_multiple_bots_share_experiment(self):
        """When multiple bots (lead, buyer, seller) use the same singleton
        experiment, outcomes aggregate across all bots."""
        service = ABTestingService()
        service.create_experiment(
            ABTestingService.RESPONSE_TONE_EXPERIMENT,
            ["formal", "casual", "empathetic"],
        )

        # Simulate 3 bots each processing 5 contacts
        for bot in ["lead", "buyer", "seller"]:
            for i in range(5):
                contact_id = f"{bot}-contact-{i}"
                variant = await service.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, contact_id)
                await service.record_outcome(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT,
                    contact_id,
                    variant,
                    "response",
                )

        results = service.get_experiment_results(ABTestingService.RESPONSE_TONE_EXPERIMENT)
        assert results.total_impressions == 15
        assert results.total_conversions == 15