"""Tests for A/B Test Auto-Promotion Service."""

import math
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.ab_auto_promote import (
    ABAutoPromoter,
    CanaryStatus,
    PromotionCandidate,
)
from ghl_real_estate_ai.services.jorge.ab_testing_service import (
    ABTestingService,
    ExperimentResult,
    VariantStats,
)


@pytest.fixture
def ab_service():
    """Create ABTestingService instance."""
    service = ABTestingService()
    service.reset()
    return service


@pytest.fixture
def db_manager():
    """Create mock database manager."""
    manager = MagicMock()
    conn = AsyncMock()
    manager.get_connection.return_value.__aenter__.return_value = conn
    manager.get_connection.return_value.__aexit__.return_value = None
    return manager


@pytest.fixture
def promoter(ab_service, db_manager):
    """Create ABAutoPromoter instance."""
    return ABAutoPromoter(ab_service, db_manager)


@pytest.fixture
def winning_experiment(ab_service):
    """Create an experiment with a clear winner."""
    # Create experiment
    ab_service.create_experiment(
        "test_experiment",
        ["control", "variant_a", "variant_b"],
    )

    # Assign contacts and record outcomes
    # Control: 500 impressions, 50 conversions (10% CR)
    for i in range(500):
        contact_id = f"contact_control_{i}"
        ab_service._experiments["test_experiment"].assignments["control"].append(contact_id)
        if i < 50:
            ab_service._experiments["test_experiment"].outcomes["control"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    # Variant A (winner): 500 impressions, 75 conversions (15% CR, 50% lift)
    for i in range(500):
        contact_id = f"contact_variant_a_{i}"
        ab_service._experiments["test_experiment"].assignments["variant_a"].append(contact_id)
        if i < 75:
            ab_service._experiments["test_experiment"].outcomes["variant_a"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    # Variant B: 500 impressions, 52 conversions (10.4% CR)
    for i in range(500):
        contact_id = f"contact_variant_b_{i}"
        ab_service._experiments["test_experiment"].assignments["variant_b"].append(contact_id)
        if i < 52:
            ab_service._experiments["test_experiment"].outcomes["variant_b"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    # Set created_at to 8 days ago (meets runtime criterion)
    ab_service._experiments["test_experiment"].created_at = (
        datetime.utcnow() - timedelta(days=8)
    ).timestamp()

    return ab_service


# ── Promotion Candidate Detection Tests ───────────────────────────────


@pytest.mark.asyncio
async def test_check_experiments_for_promotion_finds_winners(winning_experiment, db_manager):
    """Test that winning experiments are detected."""
    promoter = ABAutoPromoter(winning_experiment, db_manager)

    # Mock database check for recent promotions
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: [0]))

    candidates = await promoter.check_experiments_for_promotion()

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.experiment_id == "test_experiment"
    assert candidate.winning_variant == "variant_a"
    assert candidate.p_value < 0.05
    assert candidate.lift_percent > 10.0
    assert candidate.sample_size >= 1000
    assert candidate.runtime_days >= 7.0


@pytest.mark.asyncio
async def test_check_experiments_skips_insufficient_runtime(ab_service, db_manager):
    """Test that experiments with insufficient runtime are skipped."""
    promoter = ABAutoPromoter(ab_service, db_manager)

    # Create experiment with clear winner but only 5 days runtime
    ab_service.create_experiment("short_experiment", ["control", "variant_a"])

    # Add data (same as winning_experiment)
    for i in range(600):
        contact_id = f"contact_control_{i}"
        ab_service._experiments["short_experiment"].assignments["control"].append(contact_id)
        if i < 60:
            ab_service._experiments["short_experiment"].outcomes["control"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    for i in range(600):
        contact_id = f"contact_variant_a_{i}"
        ab_service._experiments["short_experiment"].assignments["variant_a"].append(contact_id)
        if i < 90:
            ab_service._experiments["short_experiment"].outcomes["variant_a"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    # Set created_at to 5 days ago (insufficient)
    ab_service._experiments["short_experiment"].created_at = (
        datetime.utcnow() - timedelta(days=5)
    ).timestamp()

    # Mock database check
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: [0]))

    candidates = await promoter.check_experiments_for_promotion()

    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_check_experiments_skips_insufficient_sample_size(ab_service, db_manager):
    """Test that experiments with insufficient sample size are skipped."""
    promoter = ABAutoPromoter(ab_service, db_manager)

    # Create experiment with clear winner but only 800 impressions
    ab_service.create_experiment("small_experiment", ["control", "variant_a"])

    # Add data
    for i in range(400):
        contact_id = f"contact_control_{i}"
        ab_service._experiments["small_experiment"].assignments["control"].append(contact_id)
        if i < 40:
            ab_service._experiments["small_experiment"].outcomes["control"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    for i in range(400):
        contact_id = f"contact_variant_a_{i}"
        ab_service._experiments["small_experiment"].assignments["variant_a"].append(contact_id)
        if i < 60:
            ab_service._experiments["small_experiment"].outcomes["variant_a"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    # Set created_at to 8 days ago
    ab_service._experiments["small_experiment"].created_at = (
        datetime.utcnow() - timedelta(days=8)
    ).timestamp()

    # Mock database check
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: [0]))

    candidates = await promoter.check_experiments_for_promotion()

    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_check_experiments_skips_not_significant(ab_service, db_manager):
    """Test that non-significant experiments are skipped."""
    promoter = ABAutoPromoter(ab_service, db_manager)

    # Create experiment with no clear winner
    ab_service.create_experiment("no_winner", ["control", "variant_a"])

    # Add data with similar conversion rates
    for i in range(600):
        contact_id = f"contact_control_{i}"
        ab_service._experiments["no_winner"].assignments["control"].append(contact_id)
        if i < 60:
            ab_service._experiments["no_winner"].outcomes["control"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    for i in range(600):
        contact_id = f"contact_variant_a_{i}"
        ab_service._experiments["no_winner"].assignments["variant_a"].append(contact_id)
        if i < 61:  # Only 1 more conversion - not significant
            ab_service._experiments["no_winner"].outcomes["variant_a"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    # Set created_at to 8 days ago
    ab_service._experiments["no_winner"].created_at = (
        datetime.utcnow() - timedelta(days=8)
    ).timestamp()

    # Mock database check
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: [0]))

    candidates = await promoter.check_experiments_for_promotion()

    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_check_experiments_skips_insufficient_lift(ab_service, db_manager):
    """Test that experiments with insufficient lift are skipped."""
    promoter = ABAutoPromoter(ab_service, db_manager)

    # Create experiment with significant but small lift
    ab_service.create_experiment("small_lift", ["control", "variant_a"])

    # Add data with 5% lift (below 10% threshold)
    for i in range(1000):
        contact_id = f"contact_control_{i}"
        ab_service._experiments["small_lift"].assignments["control"].append(contact_id)
        if i < 200:
            ab_service._experiments["small_lift"].outcomes["control"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    for i in range(1000):
        contact_id = f"contact_variant_a_{i}"
        ab_service._experiments["small_lift"].assignments["variant_a"].append(contact_id)
        if i < 210:  # 21% vs 20%, only 5% lift
            ab_service._experiments["small_lift"].outcomes["variant_a"].append(
                {
                    "contact_id": contact_id,
                    "outcome": "conversion",
                    "value": 1.0,
                    "timestamp": datetime.utcnow().timestamp(),
                }
            )

    # Set created_at to 8 days ago
    ab_service._experiments["small_lift"].created_at = (
        datetime.utcnow() - timedelta(days=8)
    ).timestamp()

    # Mock database check
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: [0]))

    candidates = await promoter.check_experiments_for_promotion()

    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_check_experiments_skips_recently_promoted(winning_experiment, db_manager):
    """Test that recently promoted experiments are skipped."""
    promoter = ABAutoPromoter(winning_experiment, db_manager)

    # Mock database check to indicate recent promotion
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: [1]))

    candidates = await promoter.check_experiments_for_promotion()

    assert len(candidates) == 0


# ── Winner Promotion Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_promote_winner_creates_promotion_record(winning_experiment, db_manager):
    """Test that promoting a winner creates a database record."""
    promoter = ABAutoPromoter(winning_experiment, db_manager)

    # Mock database operations
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: [123]))
    conn.commit = AsyncMock()

    result = await promoter.promote_winner(
        "test_experiment",
        "variant_a",
        promoted_by="test_user",
        promotion_type="manual",
    )

    assert result["promotion_id"] == 123
    assert result["experiment_id"] == "test_experiment"
    assert result["promoted_variant"] == "variant_a"
    assert result["promotion_type"] == "manual"
    assert result["canary_status"] == CanaryStatus.CANARY

    # Verify database calls
    assert conn.execute.call_count == 2  # INSERT + UPDATE for canary start
    assert conn.commit.call_count == 2


@pytest.mark.asyncio
async def test_promote_winner_validates_experiment(promoter):
    """Test that promoting validates experiment existence."""
    with pytest.raises(KeyError, match="Experiment 'nonexistent' not found"):
        await promoter.promote_winner("nonexistent", "variant_a")


@pytest.mark.asyncio
async def test_promote_winner_validates_variant(winning_experiment, db_manager):
    """Test that promoting validates variant exists."""
    promoter = ABAutoPromoter(winning_experiment, db_manager)

    with pytest.raises(ValueError, match="Unknown variant 'invalid'"):
        await promoter.promote_winner("test_experiment", "invalid")


# ── Canary Monitoring Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_monitor_canary_rollouts_completes_healthy_promotions(promoter, db_manager):
    """Test that healthy canary rollouts are promoted to 100%."""
    # Mock database to return canary rollouts ready for evaluation
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    canary_start = datetime.utcnow() - timedelta(hours=25)
    conn.execute = AsyncMock(
        return_value=MagicMock(
            fetchall=lambda: [
                (1, "test_experiment", "variant_a", canary_start),
            ]
        )
    )
    conn.commit = AsyncMock()

    result = await promoter.monitor_canary_rollouts()

    assert result["promotions_completed"] == 1
    assert result["rollbacks"] == 0
    assert "test_experiment" in result["experiments_promoted"]


@pytest.mark.asyncio
async def test_monitor_canary_rollouts_handles_errors_gracefully(promoter, db_manager):
    """Test that monitoring handles database errors gracefully."""
    # Mock database to raise error
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(side_effect=Exception("Database error"))

    result = await promoter.monitor_canary_rollouts()

    assert result["promotions_completed"] == 0
    assert result["rollbacks"] == 0
    assert len(result["error_details"]) > 0


# ── Manual Rollback Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_manual_rollback_succeeds(promoter, db_manager):
    """Test manual rollback of a promotion."""
    # Mock database to return valid canary promotion
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(
        return_value=MagicMock(
            fetchone=lambda: ("test_experiment", "variant_a", CanaryStatus.CANARY)
        )
    )
    conn.commit = AsyncMock()

    result = await promoter.manual_rollback(1, "Performance degradation detected")

    assert result["promotion_id"] == 1
    assert result["experiment_id"] == "test_experiment"
    assert result["canary_status"] == CanaryStatus.ROLLED_BACK
    assert result["rollback_reason"] == "Performance degradation detected"


@pytest.mark.asyncio
async def test_manual_rollback_rejects_nonexistent_promotion(promoter, db_manager):
    """Test that rollback rejects non-existent promotion."""
    # Mock database to return None
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(return_value=MagicMock(fetchone=lambda: None))

    with pytest.raises(ValueError, match="Promotion ID 999 not found"):
        await promoter.manual_rollback(999, "Test reason")


@pytest.mark.asyncio
async def test_manual_rollback_rejects_completed_promotion(promoter, db_manager):
    """Test that rollback rejects already completed promotion."""
    # Mock database to return completed promotion
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(
        return_value=MagicMock(
            fetchone=lambda: ("test_experiment", "variant_a", CanaryStatus.COMPLETED)
        )
    )

    with pytest.raises(ValueError, match="Cannot rollback.*already completed"):
        await promoter.manual_rollback(1, "Test reason")


@pytest.mark.asyncio
async def test_manual_rollback_rejects_already_rolled_back(promoter, db_manager):
    """Test that rollback rejects already rolled back promotion."""
    # Mock database to return rolled back promotion
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(
        return_value=MagicMock(
            fetchone=lambda: ("test_experiment", "variant_a", CanaryStatus.ROLLED_BACK)
        )
    )

    with pytest.raises(ValueError, match="Cannot rollback.*already rolled back"):
        await promoter.manual_rollback(1, "Test reason")


# ── Integration Tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_promotion_workflow(winning_experiment, db_manager):
    """Test complete promotion workflow from detection to promotion."""
    promoter = ABAutoPromoter(winning_experiment, db_manager)

    # Mock database operations
    conn = db_manager.get_connection.return_value.__aenter__.return_value
    conn.execute = AsyncMock(
        side_effect=[
            MagicMock(fetchone=lambda: [0]),  # Not recently promoted
            MagicMock(fetchone=lambda: [456]),  # INSERT returns ID
            None,  # UPDATE for canary start
        ]
    )
    conn.commit = AsyncMock()

    # 1. Check for candidates
    candidates = await promoter.check_experiments_for_promotion()
    assert len(candidates) == 1
    candidate = candidates[0]

    # 2. Promote winner
    result = await promoter.promote_winner(
        candidate.experiment_id,
        candidate.winning_variant,
    )

    assert result["promotion_id"] == 456
    assert result["experiment_id"] == "test_experiment"
    assert result["promoted_variant"] == "variant_a"
    assert result["canary_status"] == CanaryStatus.CANARY


# ── ABTestingService Enhancement Tests ────────────────────────────────


def test_get_promotion_candidates_basic(winning_experiment):
    """Test get_promotion_candidates method."""
    candidates = winning_experiment.get_promotion_candidates()

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["experiment_id"] == "test_experiment"
    assert candidate["winning_variant"] == "variant_a"
    assert candidate["p_value"] < 0.05
    assert candidate["lift_percent"] > 10.0
    assert candidate["sample_size"] >= 1000
    assert candidate["runtime_days"] >= 7.0


def test_get_promotion_candidates_custom_thresholds(winning_experiment):
    """Test get_promotion_candidates with custom thresholds."""
    # Use stricter thresholds
    candidates = winning_experiment.get_promotion_candidates(
        min_p_value=0.01,  # Very strict
        min_lift_percent=20.0,  # High lift required
        min_sample_size=2000,  # Very large sample
        min_runtime_days=14.0,  # Long runtime
    )

    # Should find no candidates with these strict thresholds
    assert len(candidates) == 0


def test_get_experiment_metrics(winning_experiment):
    """Test get_experiment_metrics method."""
    metrics = winning_experiment.get_experiment_metrics("test_experiment")

    assert metrics["experiment_id"] == "test_experiment"
    assert metrics["status"] == "active"
    assert metrics["runtime_days"] >= 7.0
    assert metrics["total_impressions"] >= 1000
    assert metrics["is_significant"] is True
    assert metrics["p_value"] < 0.05
    assert metrics["winner"] == "variant_a"
    assert metrics["lift_percent"] > 10.0
    assert len(metrics["variants"]) == 3


def test_get_experiment_metrics_nonexistent(ab_service):
    """Test get_experiment_metrics with non-existent experiment."""
    with pytest.raises(KeyError, match="Experiment 'nonexistent' not found"):
        ab_service.get_experiment_metrics("nonexistent")
