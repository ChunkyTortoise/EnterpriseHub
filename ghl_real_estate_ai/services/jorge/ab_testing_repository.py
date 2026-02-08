"""Repository for persistent A/B testing data.

Uses asyncpg via DatabaseConnectionManager for all database operations.
Tables: ab_experiments, ab_variants, ab_assignments, ab_metrics.

This repository is the persistence layer only — all business logic
(hash bucketing, z-test significance, traffic split validation) lives
in ABTestingService.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ABTestingRepository:
    """Persistence layer for A/B testing experiments and outcomes.

    All methods use parameterized queries via asyncpg. Requires an
    initialized DatabaseConnectionManager instance.
    """

    def __init__(self, db_manager) -> None:
        """Initialize with a DatabaseConnectionManager instance.

        Args:
            db_manager: An initialized DatabaseConnectionManager with
                        asyncpg connection pool.
        """
        self._db = db_manager

    # ── Experiments ─────────────────────────────────────────────────────

    async def create_experiment(
        self,
        experiment_name: str,
        variants: List[str],
        traffic_split: Dict[str, float],
        *,
        description: Optional[str] = None,
        target_bot: Optional[str] = None,
        metric_type: str = "conversion",
        minimum_sample_size: int = 100,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an experiment with its variants in a single transaction.

        Returns:
            Dict with experiment_id, experiment_name, variants, status.
        """
        experiment_id = uuid.uuid4()

        async with self._db.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO ab_experiments (
                    id, experiment_name, description, target_bot,
                    metric_type, minimum_sample_size, status, started_at,
                    default_traffic_split, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, 'active', NOW(), $7, $8)
                """,
                experiment_id,
                experiment_name,
                description,
                target_bot,
                metric_type,
                minimum_sample_size,
                json.dumps(traffic_split),
                created_by,
            )

            for i, variant_name in enumerate(variants):
                await conn.execute(
                    """
                    INSERT INTO ab_variants (
                        id, experiment_id, variant_name, traffic_weight,
                        is_control
                    ) VALUES ($1, $2, $3, $4, $5)
                    """,
                    uuid.uuid4(),
                    experiment_id,
                    variant_name,
                    traffic_split.get(variant_name, 1.0 / len(variants)),
                    i == 0,
                )

        logger.info(
            "Persisted experiment '%s' with %d variants",
            experiment_name,
            len(variants),
        )
        return {
            "experiment_id": str(experiment_id),
            "experiment_name": experiment_name,
            "variants": variants,
            "traffic_split": traffic_split,
            "status": "active",
        }

    async def get_experiment(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """Load an experiment with its variants by name.

        Returns:
            Dict with experiment data and nested variants list, or None.
        """
        row = await self._db.execute_fetchrow(
            """
            SELECT id, experiment_name, description, target_bot,
                   metric_type, minimum_sample_size, status, started_at,
                   completed_at, default_traffic_split, winner_variant,
                   statistical_significance, created_at, created_by
            FROM ab_experiments
            WHERE experiment_name = $1
            """,
            experiment_name,
        )
        if row is None:
            return None

        experiment = dict(row)
        experiment["id"] = str(experiment["id"])

        variant_rows = await self._db.execute_query(
            """
            SELECT id, variant_name, traffic_weight, impressions,
                   conversions, conversion_rate, total_value,
                   confidence_interval_lower, confidence_interval_upper,
                   is_control
            FROM ab_variants
            WHERE experiment_id = $1
            ORDER BY created_at
            """,
            row["id"],
        )
        experiment["variants"] = [{**dict(v), "id": str(v["id"])} for v in variant_rows]
        return experiment

    async def list_active_experiments(self) -> List[Dict[str, Any]]:
        """List all active experiments with assignment counts."""
        rows = await self._db.execute_query(
            """
            SELECT e.id, e.experiment_name, e.status, e.started_at,
                   e.default_traffic_split, e.created_at,
                   COUNT(a.id) AS total_assignments
            FROM ab_experiments e
            LEFT JOIN ab_assignments a ON a.experiment_id = e.id
            WHERE e.status = 'active'
            GROUP BY e.id
            ORDER BY e.created_at
            """,
        )
        return [dict(r) for r in rows]

    async def deactivate_experiment(
        self,
        experiment_name: str,
        winner: Optional[str] = None,
        significance: Optional[float] = None,
    ) -> bool:
        """Mark an experiment as completed.

        Returns:
            True if the experiment was updated.
        """
        result = await self._db.execute_command(
            """
            UPDATE ab_experiments
            SET status = 'completed',
                completed_at = NOW(),
                winner_variant = $2,
                statistical_significance = $3,
                updated_at = NOW()
            WHERE experiment_name = $1 AND status = 'active'
            """,
            experiment_name,
            winner,
            significance,
        )
        return "UPDATE 1" in result

    # ── Assignments ────────────────────────────────────────────────────

    async def get_or_create_assignment(
        self,
        experiment_name: str,
        user_id: str,
        variant_name: str,
        bucket_value: float,
    ) -> Dict[str, Any]:
        """Get existing assignment or create a new one (idempotent).

        Uses ON CONFLICT to handle concurrent assignment attempts.
        """
        exp_row = await self._db.execute_fetchrow(
            "SELECT id FROM ab_experiments WHERE experiment_name = $1",
            experiment_name,
        )
        if exp_row is None:
            raise KeyError(f"Experiment '{experiment_name}' not found in DB")

        var_row = await self._db.execute_fetchrow(
            """
            SELECT id FROM ab_variants
            WHERE experiment_id = $1 AND variant_name = $2
            """,
            exp_row["id"],
            variant_name,
        )
        if var_row is None:
            raise KeyError(f"Variant '{variant_name}' not found in experiment '{experiment_name}'")

        assignment_id = uuid.uuid4()
        await self._db.execute_command(
            """
            INSERT INTO ab_assignments (
                id, experiment_id, variant_id, user_id, bucket_value
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (experiment_id, user_id) DO NOTHING
            """,
            assignment_id,
            exp_row["id"],
            var_row["id"],
            user_id,
            bucket_value,
        )

        # Update variant impression count
        await self._db.execute_command(
            """
            UPDATE ab_variants
            SET impressions = (
                SELECT COUNT(*) FROM ab_assignments WHERE variant_id = $1
            ),
            updated_at = NOW()
            WHERE id = $1
            """,
            var_row["id"],
        )

        return {
            "experiment_name": experiment_name,
            "user_id": user_id,
            "variant_name": variant_name,
            "bucket_value": bucket_value,
        }

    # ── Outcomes / Metrics ─────────────────────────────────────────────

    async def record_outcome(
        self,
        experiment_name: str,
        user_id: str,
        variant_name: str,
        event_type: str,
        value: float = 1.0,
        *,
        source: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a conversion/outcome event for a variant."""
        assignment_row = await self._db.execute_fetchrow(
            """
            SELECT a.id AS assignment_id, a.experiment_id, a.variant_id
            FROM ab_assignments a
            JOIN ab_experiments e ON e.id = a.experiment_id
            WHERE e.experiment_name = $1 AND a.user_id = $2
            """,
            experiment_name,
            user_id,
        )
        if assignment_row is None:
            raise KeyError(f"No assignment found for user '{user_id}' in experiment '{experiment_name}'")

        metric_id = uuid.uuid4()
        await self._db.execute_command(
            """
            INSERT INTO ab_metrics (
                id, experiment_id, variant_id, assignment_id,
                event_type, event_value, event_data, source
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            metric_id,
            assignment_row["experiment_id"],
            assignment_row["variant_id"],
            assignment_row["assignment_id"],
            event_type,
            value,
            json.dumps(event_data) if event_data else None,
            source,
        )

        # Update variant stats
        await self._db.execute_command(
            """
            UPDATE ab_variants SET
                conversions = (
                    SELECT COUNT(*) FROM ab_metrics
                    WHERE variant_id = $1
                ),
                total_value = (
                    SELECT COALESCE(SUM(event_value), 0) FROM ab_metrics
                    WHERE variant_id = $1
                ),
                conversion_rate = CASE
                    WHEN impressions > 0 THEN
                        (SELECT COUNT(*)::float FROM ab_metrics
                         WHERE variant_id = $1) / impressions
                    ELSE 0
                END,
                updated_at = NOW()
            WHERE id = $1
            """,
            assignment_row["variant_id"],
        )

        # Mark assignment as converted
        await self._db.execute_command(
            """
            UPDATE ab_assignments
            SET has_converted = true, converted_at = NOW()
            WHERE id = $1 AND has_converted = false
            """,
            assignment_row["assignment_id"],
        )

        return {
            "metric_id": str(metric_id),
            "experiment_name": experiment_name,
            "user_id": user_id,
            "event_type": event_type,
            "value": value,
        }

    async def get_experiment_results(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive results with per-variant stats from DB."""
        exp = await self.get_experiment(experiment_name)
        if exp is None:
            return None

        variant_rows = await self._db.execute_query(
            """
            SELECT
                v.variant_name,
                v.impressions,
                v.conversions,
                v.total_value,
                v.conversion_rate,
                v.confidence_interval_lower,
                v.confidence_interval_upper,
                v.is_control
            FROM ab_variants v
            WHERE v.experiment_id = $1
            ORDER BY v.conversion_rate DESC
            """,
            uuid.UUID(exp["id"]),
        )
        variants = [dict(r) for r in variant_rows]
        total_impressions = sum(v["impressions"] for v in variants)
        total_conversions = sum(v["conversions"] for v in variants)

        return {
            "experiment_name": experiment_name,
            "status": exp["status"],
            "started_at": exp.get("started_at"),
            "winner_variant": exp.get("winner_variant"),
            "statistical_significance": exp.get("statistical_significance"),
            "total_impressions": total_impressions,
            "total_conversions": total_conversions,
            "variants": variants,
        }

    # ── Seed Data ──────────────────────────────────────────────────────

    async def seed_default_experiments(self) -> List[str]:
        """Create the 4 default experiments if they don't already exist.

        Returns:
            List of experiment names that were created.
        """
        defaults = [
            {
                "experiment_name": "response_tone",
                "variants": ["formal", "casual", "empathetic"],
                "description": "Test different response tones",
            },
            {
                "experiment_name": "followup_timing",
                "variants": ["1hr", "4hr", "24hr"],
                "description": "Test optimal follow-up timing",
            },
            {
                "experiment_name": "cta_style",
                "variants": ["direct", "soft", "question"],
                "description": "Test different call-to-action styles",
            },
            {
                "experiment_name": "greeting_style",
                "variants": ["name", "title", "casual"],
                "description": "Test different greeting approaches",
            },
        ]

        created = []
        for exp_def in defaults:
            existing = await self.get_experiment(exp_def["experiment_name"])
            if existing is None:
                n = len(exp_def["variants"])
                split = {v: 1.0 / n for v in exp_def["variants"]}
                await self.create_experiment(
                    experiment_name=exp_def["experiment_name"],
                    variants=exp_def["variants"],
                    traffic_split=split,
                    description=exp_def["description"],
                )
                created.append(exp_def["experiment_name"])
                logger.info("Seeded default experiment: %s", exp_def["experiment_name"])

        return created
