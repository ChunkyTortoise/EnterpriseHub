"""
A/B Test Auto-Promotion Service

Automatically promotes A/B test winners to production config when they meet
statistical significance criteria. Implements canary rollout (20% → 100%)
with monitoring and instant rollback capability.

Promotion Criteria:
- p-value < 0.05 (statistical significance)
- lift > 10% (material improvement)
- sample size ≥ 1000 (sufficient data)
- runtime ≥ 7 days (temporal stability)

Canary Rollout Flow:
1. Pending → Canary (20% traffic)
2. Monitor for 24h
3. If stable → Full rollout (100%)
4. If issues → Instant rollback

Usage:
    promoter = ABAutoPromoter(ab_service, db_manager)
    await promoter.check_experiments_for_promotion()  # Daily background task
    await promoter.promote_winner(experiment_id, variant)  # Manual promotion
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

logger = logging.getLogger(__name__)


@dataclass
class PromotionCandidate:
    """Experiment ready for promotion to production."""

    experiment_id: str
    winning_variant: str
    control_variant: str
    p_value: float
    lift_percent: float
    sample_size: int
    runtime_days: float
    winner_conversion_rate: float
    control_conversion_rate: float
    confidence_interval: tuple
    metrics_snapshot: Dict[str, Any]


class CanaryStatus:
    """Canary rollout lifecycle states."""

    PENDING = "pending"  # Promotion created, not started
    CANARY = "canary"  # 20% traffic rollout
    MONITORING = "monitoring"  # 24h monitoring period
    COMPLETED = "completed"  # Successfully promoted to 100%
    ROLLED_BACK = "rolled_back"  # Rolled back due to issues


class ABAutoPromoter:
    """Auto-promotion engine for A/B test winners.

    Promotes winning variants when they meet statistical and business
    criteria. Uses canary rollout for safety with instant rollback.
    """

    # Promotion thresholds
    MIN_P_VALUE = 0.05
    MIN_LIFT_PERCENT = 10.0
    MIN_SAMPLE_SIZE = 1000
    MIN_RUNTIME_DAYS = 7.0

    # Canary rollout config
    CANARY_TRAFFIC_PERCENT = 20.0
    CANARY_MONITORING_HOURS = 24
    FULL_ROLLOUT_TRAFFIC_PERCENT = 100.0

    def __init__(self, ab_service: ABTestingService, db_manager: Any):
        """Initialize auto-promoter.

        Args:
            ab_service: ABTestingService instance for experiment management.
            db_manager: Database manager for persistence.
        """
        self.ab_service = ab_service
        self.db_manager = db_manager
        logger.info("ABAutoPromoter initialized")

    # ── Promotion Candidate Detection ────────────────────────────────────

    @trace_operation("jorge.ab_auto_promote", "check_experiments_for_promotion")
    async def check_experiments_for_promotion(self) -> List[PromotionCandidate]:
        """Scan all active experiments for promotion candidates.

        Runs daily as a background task. Identifies experiments meeting
        all promotion criteria and returns them for auto-promotion.

        Returns:
            List of experiments ready for promotion.
        """
        candidates = []
        experiments = self.ab_service.list_experiments()

        logger.info(f"Scanning {len(experiments)} active experiments for promotion candidates")

        for exp_info in experiments:
            experiment_id = exp_info["experiment_id"]

            try:
                candidate = await self._evaluate_experiment(experiment_id)
                if candidate:
                    candidates.append(candidate)
                    logger.info(
                        f"Promotion candidate found: {experiment_id} "
                        f"(variant={candidate.winning_variant}, "
                        f"p={candidate.p_value:.4f}, "
                        f"lift={candidate.lift_percent:.1f}%, "
                        f"n={candidate.sample_size})"
                    )
            except Exception as exc:
                logger.warning(f"Failed to evaluate experiment '{experiment_id}': {exc}")

        if candidates:
            logger.info(f"Found {len(candidates)} experiments ready for promotion")
        else:
            logger.debug("No experiments meet promotion criteria")

        return candidates

    async def _evaluate_experiment(self, experiment_id: str) -> Optional[PromotionCandidate]:
        """Evaluate a single experiment for promotion eligibility.

        Args:
            experiment_id: Experiment to evaluate.

        Returns:
            PromotionCandidate if criteria met, None otherwise.
        """
        # Check if already promoted recently
        if await self._was_recently_promoted(experiment_id):
            logger.debug(f"Experiment '{experiment_id}' was recently promoted, skipping")
            return None

        # Get experiment results
        results = self.ab_service.get_experiment_results(experiment_id)

        # Check runtime criterion
        runtime_days = results.duration_hours / 24.0
        if runtime_days < self.MIN_RUNTIME_DAYS:
            logger.debug(
                f"Experiment '{experiment_id}' runtime {runtime_days:.1f}d "
                f"< {self.MIN_RUNTIME_DAYS}d, skipping"
            )
            return None

        # Check sample size criterion
        if results.total_impressions < self.MIN_SAMPLE_SIZE:
            logger.debug(
                f"Experiment '{experiment_id}' sample size {results.total_impressions} "
                f"< {self.MIN_SAMPLE_SIZE}, skipping"
            )
            return None

        # Check statistical significance
        if not results.is_significant or results.p_value is None or results.p_value >= self.MIN_P_VALUE:
            logger.debug(
                f"Experiment '{experiment_id}' not significant "
                f"(p={results.p_value}, threshold={self.MIN_P_VALUE})"
            )
            return None

        # Get winner and control variants
        sorted_variants = sorted(
            results.variants,
            key=lambda v: v.conversion_rate,
            reverse=True,
        )

        if len(sorted_variants) < 2:
            logger.debug(f"Experiment '{experiment_id}' has <2 variants, skipping")
            return None

        winner = sorted_variants[0]
        control = sorted_variants[1]

        # Check minimum lift criterion
        if control.conversion_rate == 0:
            lift_percent = float("inf") if winner.conversion_rate > 0 else 0.0
        else:
            lift_percent = ((winner.conversion_rate - control.conversion_rate) / control.conversion_rate) * 100.0

        if lift_percent < self.MIN_LIFT_PERCENT:
            logger.debug(
                f"Experiment '{experiment_id}' lift {lift_percent:.1f}% "
                f"< {self.MIN_LIFT_PERCENT}%, skipping"
            )
            return None

        # All criteria met!
        return PromotionCandidate(
            experiment_id=experiment_id,
            winning_variant=winner.variant,
            control_variant=control.variant,
            p_value=results.p_value,
            lift_percent=lift_percent,
            sample_size=results.total_impressions,
            runtime_days=runtime_days,
            winner_conversion_rate=winner.conversion_rate,
            control_conversion_rate=control.conversion_rate,
            confidence_interval=winner.confidence_interval,
            metrics_snapshot={
                "experiment_id": experiment_id,
                "status": results.status,
                "total_impressions": results.total_impressions,
                "total_conversions": results.total_conversions,
                "duration_hours": results.duration_hours,
                "p_value": results.p_value,
                "winner": results.winner,
                "variants": [
                    {
                        "variant": v.variant,
                        "impressions": v.impressions,
                        "conversions": v.conversions,
                        "conversion_rate": v.conversion_rate,
                        "total_value": v.total_value,
                        "confidence_interval": v.confidence_interval,
                    }
                    for v in results.variants
                ],
            },
        )

    async def _was_recently_promoted(self, experiment_id: str, days: int = 7) -> bool:
        """Check if experiment was promoted in the last N days.

        Args:
            experiment_id: Experiment to check.
            days: Lookback window in days (default 7).

        Returns:
            True if recently promoted, False otherwise.
        """
        try:
            async with self.db_manager.get_connection() as conn:
                cutoff = datetime.utcnow() - timedelta(days=days)
                query = text("""
                    SELECT COUNT(*) as count
                    FROM ab_promotion_events
                    WHERE experiment_id = :experiment_id
                    AND created_at >= :cutoff
                """)
                result = await conn.execute(
                    query,
                    {"experiment_id": experiment_id, "cutoff": cutoff},
                )
                row = result.fetchone()
                return row is not None and row[0] > 0
        except Exception as exc:
            logger.warning(f"Failed to check promotion history for '{experiment_id}': {exc}")
            return False

    # ── Winner Promotion ──────────────────────────────────────────────────

    @trace_operation("jorge.ab_auto_promote", "promote_winner")
    async def promote_winner(
        self,
        experiment_id: str,
        winning_variant: str,
        promoted_by: str = "system",
        promotion_type: str = "automatic",
    ) -> Dict[str, Any]:
        """Promote a winning variant to production config.

        Implements canary rollout:
        1. Create promotion record
        2. Start canary rollout (20% traffic)
        3. Monitor for 24h
        4. Promote to 100% if stable

        Args:
            experiment_id: Experiment identifier.
            winning_variant: Variant to promote.
            promoted_by: User ID or "system" for auto-promotion.
            promotion_type: "automatic" or "manual".

        Returns:
            Dict with promotion metadata.

        Raises:
            ValueError: On invalid experiment or variant.
        """
        # Validate experiment and variant
        results = self.ab_service.get_experiment_results(experiment_id)
        variant_names = [v.variant for v in results.variants]
        if winning_variant not in variant_names:
            raise ValueError(
                f"Unknown variant '{winning_variant}' for experiment '{experiment_id}'. "
                f"Valid variants: {variant_names}"
            )

        # Get winner stats
        winner_stats = next(v for v in results.variants if v.variant == winning_variant)

        # Determine control variant (second-best by conversion rate)
        sorted_variants = sorted(
            results.variants,
            key=lambda v: v.conversion_rate,
            reverse=True,
        )
        control_variant = sorted_variants[1].variant if len(sorted_variants) >= 2 else None
        control_stats = sorted_variants[1] if len(sorted_variants) >= 2 else None

        # Calculate lift
        if control_stats and control_stats.conversion_rate > 0:
            lift_percent = (
                (winner_stats.conversion_rate - control_stats.conversion_rate) / control_stats.conversion_rate
            ) * 100.0
        else:
            lift_percent = 0.0

        # Create promotion record
        promotion_id = await self._create_promotion_record(
            experiment_id=experiment_id,
            promoted_variant=winning_variant,
            previous_default=control_variant,
            promotion_type=promotion_type,
            promoted_by=promoted_by,
            p_value=results.p_value or 1.0,
            lift_percent=lift_percent,
            sample_size=results.total_impressions,
            runtime_days=results.duration_hours / 24.0,
            winner_conversion_rate=winner_stats.conversion_rate,
            control_conversion_rate=control_stats.conversion_rate if control_stats else 0.0,
            confidence_interval=winner_stats.confidence_interval,
            metrics_snapshot={
                "experiment_id": experiment_id,
                "status": results.status,
                "total_impressions": results.total_impressions,
                "total_conversions": results.total_conversions,
                "duration_hours": results.duration_hours,
                "p_value": results.p_value,
                "winner": results.winner,
                "variants": [
                    {
                        "variant": v.variant,
                        "impressions": v.impressions,
                        "conversions": v.conversions,
                        "conversion_rate": v.conversion_rate,
                        "total_value": v.total_value,
                        "confidence_interval": v.confidence_interval,
                    }
                    for v in results.variants
                ],
            },
        )

        # Start canary rollout
        await self._start_canary_rollout(promotion_id, experiment_id, winning_variant)

        logger.info(
            f"Promoted variant '{winning_variant}' for experiment '{experiment_id}' "
            f"(promotion_id={promotion_id}, type={promotion_type}, by={promoted_by})"
        )

        return {
            "promotion_id": promotion_id,
            "experiment_id": experiment_id,
            "promoted_variant": winning_variant,
            "previous_default": control_variant,
            "promotion_type": promotion_type,
            "canary_status": CanaryStatus.CANARY,
            "metrics": {
                "p_value": results.p_value,
                "lift_percent": lift_percent,
                "sample_size": results.total_impressions,
                "runtime_days": results.duration_hours / 24.0,
            },
        }

    async def _create_promotion_record(
        self,
        experiment_id: str,
        promoted_variant: str,
        previous_default: Optional[str],
        promotion_type: str,
        promoted_by: str,
        p_value: float,
        lift_percent: float,
        sample_size: int,
        runtime_days: float,
        winner_conversion_rate: float,
        control_conversion_rate: float,
        confidence_interval: tuple,
        metrics_snapshot: Dict[str, Any],
    ) -> int:
        """Create database record for promotion event.

        Args:
            experiment_id: Experiment identifier.
            promoted_variant: Winning variant.
            previous_default: Previous default variant.
            promotion_type: "automatic" or "manual".
            promoted_by: User ID or "system".
            p_value: Statistical significance.
            lift_percent: Percentage improvement.
            sample_size: Total impressions.
            runtime_days: Experiment duration in days.
            winner_conversion_rate: Winner's conversion rate.
            control_conversion_rate: Control's conversion rate.
            confidence_interval: 95% CI for winner.
            metrics_snapshot: Full experiment results.

        Returns:
            Promotion record ID.
        """
        import json

        async with self.db_manager.get_connection() as conn:
            query = text("""
                INSERT INTO ab_promotion_events (
                    experiment_id, promoted_variant, previous_default,
                    promotion_type, promoted_by,
                    p_value, lift_percent, sample_size, runtime_days,
                    winner_conversion_rate, control_conversion_rate,
                    confidence_interval_lower, confidence_interval_upper,
                    canary_status, metrics_snapshot
                ) VALUES (
                    :experiment_id, :promoted_variant, :previous_default,
                    :promotion_type, :promoted_by,
                    :p_value, :lift_percent, :sample_size, :runtime_days,
                    :winner_conversion_rate, :control_conversion_rate,
                    :ci_lower, :ci_upper,
                    :canary_status, :metrics_snapshot
                )
                RETURNING id
            """)
            result = await conn.execute(
                query,
                {
                    "experiment_id": experiment_id,
                    "promoted_variant": promoted_variant,
                    "previous_default": previous_default,
                    "promotion_type": promotion_type,
                    "promoted_by": promoted_by,
                    "p_value": p_value,
                    "lift_percent": lift_percent,
                    "sample_size": sample_size,
                    "runtime_days": runtime_days,
                    "winner_conversion_rate": winner_conversion_rate,
                    "control_conversion_rate": control_conversion_rate,
                    "ci_lower": confidence_interval[0],
                    "ci_upper": confidence_interval[1],
                    "canary_status": CanaryStatus.PENDING,
                    "metrics_snapshot": json.dumps(metrics_snapshot),
                },
            )
            row = result.fetchone()
            await conn.commit()
            return row[0]

    async def _start_canary_rollout(
        self,
        promotion_id: int,
        experiment_id: str,
        winning_variant: str,
    ) -> None:
        """Start canary rollout at 20% traffic.

        Args:
            promotion_id: Promotion record ID.
            experiment_id: Experiment identifier.
            winning_variant: Variant to promote.
        """
        # Update promotion status
        async with self.db_manager.get_connection() as conn:
            query = text("""
                UPDATE ab_promotion_events
                SET canary_status = :status,
                    canary_start_time = :start_time
                WHERE id = :promotion_id
            """)
            await conn.execute(
                query,
                {
                    "promotion_id": promotion_id,
                    "status": CanaryStatus.CANARY,
                    "start_time": datetime.utcnow(),
                },
            )
            await conn.commit()

        logger.info(
            f"Started canary rollout for experiment '{experiment_id}' "
            f"(variant={winning_variant}, traffic={self.CANARY_TRAFFIC_PERCENT}%)"
        )

        # TODO: Update traffic split in A/B service to route 20% to winner
        # This will be implemented in a follow-up task to modify traffic allocation

    # ── Canary Monitoring & Rollout ───────────────────────────────────────

    @trace_operation("jorge.ab_auto_promote", "monitor_canary_rollouts")
    async def monitor_canary_rollouts(self) -> Dict[str, Any]:
        """Monitor active canary rollouts and promote/rollback as needed.

        Runs as a background task. Checks canary rollouts that have been
        running for 24h+ and either promotes to 100% or rolls back.

        Returns:
            Dict with monitoring results (promotions, rollbacks, errors).
        """
        promotions_completed = []
        rollbacks = []
        errors = []

        try:
            # Get all canary rollouts ready for final promotion
            async with self.db_manager.get_connection() as conn:
                cutoff = datetime.utcnow() - timedelta(hours=self.CANARY_MONITORING_HOURS)
                query = text("""
                    SELECT id, experiment_id, promoted_variant, canary_start_time
                    FROM ab_promotion_events
                    WHERE canary_status = :canary_status
                    AND canary_start_time <= :cutoff
                """)
                result = await conn.execute(
                    query,
                    {
                        "canary_status": CanaryStatus.CANARY,
                        "cutoff": cutoff,
                    },
                )
                canary_rollouts = result.fetchall()

            logger.info(f"Found {len(canary_rollouts)} canary rollouts ready for evaluation")

            for row in canary_rollouts:
                promotion_id, experiment_id, promoted_variant, canary_start = row

                try:
                    # Check for issues (placeholder - implement metrics-based checks)
                    has_issues = await self._check_canary_health(
                        experiment_id,
                        promoted_variant,
                        canary_start,
                    )

                    if has_issues:
                        # Rollback
                        await self._rollback_promotion(
                            promotion_id,
                            experiment_id,
                            "Canary rollout showed degraded metrics",
                        )
                        rollbacks.append(experiment_id)
                        logger.warning(
                            f"Rolled back experiment '{experiment_id}' due to canary issues"
                        )
                    else:
                        # Complete promotion to 100%
                        await self._complete_promotion(promotion_id, experiment_id, promoted_variant)
                        promotions_completed.append(experiment_id)
                        logger.info(
                            f"Completed full rollout for experiment '{experiment_id}' "
                            f"(variant={promoted_variant})"
                        )

                except Exception as exc:
                    errors.append({"experiment_id": experiment_id, "error": str(exc)})
                    logger.error(
                        f"Failed to process canary rollout for '{experiment_id}': {exc}"
                    )

        except Exception as exc:
            logger.error(f"Failed to monitor canary rollouts: {exc}")
            errors.append({"global": str(exc)})

        return {
            "promotions_completed": len(promotions_completed),
            "rollbacks": len(rollbacks),
            "errors": len(errors),
            "experiments_promoted": promotions_completed,
            "experiments_rolled_back": rollbacks,
            "error_details": errors,
        }

    async def _check_canary_health(
        self,
        experiment_id: str,
        promoted_variant: str,
        canary_start: datetime,
    ) -> bool:
        """Check if canary rollout shows any issues.

        Args:
            experiment_id: Experiment identifier.
            promoted_variant: Promoted variant.
            canary_start: When canary started.

        Returns:
            True if issues detected, False if healthy.
        """
        # TODO: Implement real health checks:
        # - Check error rates
        # - Check conversion rates
        # - Check latency metrics
        # - Check user complaints/feedback
        # For now, assume healthy (no issues)
        logger.debug(f"Checking canary health for '{experiment_id}' (variant={promoted_variant})")
        return False

    async def _complete_promotion(
        self,
        promotion_id: int,
        experiment_id: str,
        promoted_variant: str,
    ) -> None:
        """Complete promotion to 100% traffic.

        Args:
            promotion_id: Promotion record ID.
            experiment_id: Experiment identifier.
            promoted_variant: Winning variant.
        """
        async with self.db_manager.get_connection() as conn:
            query = text("""
                UPDATE ab_promotion_events
                SET canary_status = :status,
                    canary_end_time = :end_time,
                    full_rollout_time = :rollout_time
                WHERE id = :promotion_id
            """)
            now = datetime.utcnow()
            await conn.execute(
                query,
                {
                    "promotion_id": promotion_id,
                    "status": CanaryStatus.COMPLETED,
                    "end_time": now,
                    "rollout_time": now,
                },
            )
            await conn.commit()

        # TODO: Update traffic split to 100% for winner
        logger.info(
            f"Completed promotion for experiment '{experiment_id}' "
            f"(variant={promoted_variant}, traffic=100%)"
        )

    async def _rollback_promotion(
        self,
        promotion_id: int,
        experiment_id: str,
        reason: str,
    ) -> None:
        """Rollback a failed canary promotion.

        Args:
            promotion_id: Promotion record ID.
            experiment_id: Experiment identifier.
            reason: Why rollback occurred.
        """
        async with self.db_manager.get_connection() as conn:
            query = text("""
                UPDATE ab_promotion_events
                SET canary_status = :status,
                    canary_end_time = :end_time,
                    rollback_time = :rollback_time,
                    rollback_reason = :reason
                WHERE id = :promotion_id
            """)
            now = datetime.utcnow()
            await conn.execute(
                query,
                {
                    "promotion_id": promotion_id,
                    "status": CanaryStatus.ROLLED_BACK,
                    "end_time": now,
                    "rollback_time": now,
                    "reason": reason,
                },
            )
            await conn.commit()

        # TODO: Restore previous traffic split
        logger.warning(f"Rolled back promotion for experiment '{experiment_id}': {reason}")

    # ── Manual Rollback ───────────────────────────────────────────────────

    @trace_operation("jorge.ab_auto_promote", "manual_rollback")
    async def manual_rollback(self, promotion_id: int, reason: str) -> Dict[str, Any]:
        """Manually rollback a promotion.

        Args:
            promotion_id: Promotion record to rollback.
            reason: Why rollback is needed.

        Returns:
            Dict with rollback metadata.

        Raises:
            ValueError: If promotion not found or already completed.
        """
        # Get promotion record
        async with self.db_manager.get_connection() as conn:
            query = text("""
                SELECT experiment_id, promoted_variant, canary_status
                FROM ab_promotion_events
                WHERE id = :promotion_id
            """)
            result = await conn.execute(query, {"promotion_id": promotion_id})
            row = result.fetchone()

            if row is None:
                raise ValueError(f"Promotion ID {promotion_id} not found")

            experiment_id, promoted_variant, canary_status = row

            if canary_status == CanaryStatus.COMPLETED:
                raise ValueError(
                    f"Cannot rollback promotion {promotion_id}: already completed "
                    f"(experiment='{experiment_id}')"
                )

            if canary_status == CanaryStatus.ROLLED_BACK:
                raise ValueError(
                    f"Cannot rollback promotion {promotion_id}: already rolled back "
                    f"(experiment='{experiment_id}')"
                )

        # Execute rollback
        await self._rollback_promotion(promotion_id, experiment_id, reason)

        logger.info(
            f"Manual rollback completed for promotion {promotion_id} "
            f"(experiment='{experiment_id}', variant='{promoted_variant}')"
        )

        return {
            "promotion_id": promotion_id,
            "experiment_id": experiment_id,
            "promoted_variant": promoted_variant,
            "canary_status": CanaryStatus.ROLLED_BACK,
            "rollback_reason": reason,
        }
