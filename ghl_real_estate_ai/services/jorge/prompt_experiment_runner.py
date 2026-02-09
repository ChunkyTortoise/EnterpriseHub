"""
Jorge Prompt Experiment Runner

Systematic prompt A/B testing with statistical significance analysis.
Allows creating prompt experiments with multiple variants, deterministic
traffic assignment via hash bucketing, outcome tracking, z-test analysis,
and early stopping.

Usage:
    runner = PromptExperimentRunner()
    exp = runner.create_experiment(
        "greeting_test",
        [PromptVariant("formal", "Dear {name},...", "Formal greeting"),
         PromptVariant("casual", "Hey {name}!", "Casual greeting")],
    )
    variant = runner.assign_variant("greeting_test", "contact_123")
    runner.record_outcome("greeting_test", "contact_123", variant, score=0.8, success=True)
    result = runner.analyze("greeting_test")
"""

from __future__ import annotations

import hashlib
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PromptVariant:
    """A single prompt variant in an experiment."""

    name: str
    prompt_template: str
    description: str = ""


@dataclass
class PromptExperiment:
    """An active prompt experiment."""

    name: str
    variants: List[PromptVariant]
    traffic_split: Dict[str, float]
    metric: str = "conversion"
    created_at: float = field(default_factory=time.time)
    status: str = "active"


@dataclass
class VariantStats:
    """Aggregated statistics for a single variant."""

    variant_name: str
    sample_size: int = 0
    successes: int = 0
    mean_score: float = 0.0
    std_dev: float = 0.0


@dataclass
class ExperimentResult:
    """Result of experiment analysis."""

    experiment_name: str
    variant_stats: Dict[str, VariantStats]
    winner: Optional[str] = None
    p_value: float = 1.0
    confidence: float = 0.0
    is_significant: bool = False


@dataclass
class _Outcome:
    """A single recorded outcome."""

    contact_id: str
    variant_name: str
    score: float
    success: bool
    timestamp: float


class PromptExperimentRunner:
    """Manages prompt A/B experiments with statistical analysis."""

    def __init__(self) -> None:
        self._experiments: Dict[str, PromptExperiment] = {}
        self._outcomes: Dict[str, List[_Outcome]] = {}
        logger.info("PromptExperimentRunner initialized")

    # ── Experiment Management ──────────────────────────────────────────

    def create_experiment(
        self,
        name: str,
        variants: List[PromptVariant],
        traffic_split: Optional[Dict[str, float]] = None,
        metric: str = "conversion",
    ) -> PromptExperiment:
        """Create a new prompt experiment.

        Args:
            name: Unique experiment name.
            variants: List of prompt variants (minimum 2).
            traffic_split: Optional mapping of variant name -> fraction (must sum to 1.0).
                           Defaults to equal split.
            metric: Primary metric to optimize (default 'conversion').

        Returns:
            The created PromptExperiment.

        Raises:
            ValueError: On invalid inputs.
        """
        if name in self._experiments:
            raise ValueError(f"Experiment '{name}' already exists")

        if len(variants) < 2:
            raise ValueError("Experiments require at least 2 variants")

        variant_names = [v.name for v in variants]
        if len(set(variant_names)) != len(variant_names):
            raise ValueError("Variant names must be unique")

        if traffic_split is None:
            equal_share = 1.0 / len(variants)
            traffic_split = {v.name: equal_share for v in variants}
        else:
            if set(traffic_split.keys()) != set(variant_names):
                raise ValueError("traffic_split keys must match variant names")
            total = sum(traffic_split.values())
            if not math.isclose(total, 1.0, abs_tol=1e-6):
                raise ValueError(f"traffic_split must sum to 1.0, got {total:.6f}")

        experiment = PromptExperiment(
            name=name,
            variants=list(variants),
            traffic_split=dict(traffic_split),
            metric=metric,
        )
        self._experiments[name] = experiment
        self._outcomes[name] = []

        logger.info(
            "Created experiment '%s' with %d variants, metric='%s'",
            name, len(variants), metric,
        )
        return experiment

    # ── Variant Assignment ─────────────────────────────────────────────

    def assign_variant(self, experiment_name: str, contact_id: str) -> str:
        """Deterministically assign a contact to a variant via hash bucketing.

        Args:
            experiment_name: Target experiment.
            contact_id: Contact/user identifier.

        Returns:
            The assigned variant name.

        Raises:
            KeyError: If experiment does not exist.
            ValueError: If experiment is not active.
        """
        experiment = self._get_experiment(experiment_name)
        if experiment.status != "active":
            raise ValueError(f"Experiment '{experiment_name}' is not active")

        digest = hashlib.sha256(
            f"{contact_id}:{experiment_name}".encode()
        ).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF

        cumulative = 0.0
        variant_names = [v.name for v in experiment.variants]
        for vname in variant_names:
            cumulative += experiment.traffic_split[vname]
            if bucket <= cumulative:
                return vname

        return variant_names[-1]

    # ── Outcome Recording ──────────────────────────────────────────────

    def record_outcome(
        self,
        experiment_name: str,
        contact_id: str,
        variant_name: str,
        score: float = 1.0,
        success: bool = True,
    ) -> None:
        """Record an outcome for an experiment variant.

        Args:
            experiment_name: Target experiment.
            contact_id: Contact/user identifier.
            variant_name: Variant the outcome is for.
            score: Numeric score (default 1.0).
            success: Whether this counts as a success.

        Raises:
            KeyError: If experiment does not exist.
            ValueError: If variant_name is not in the experiment.
        """
        experiment = self._get_experiment(experiment_name)
        variant_names = {v.name for v in experiment.variants}
        if variant_name not in variant_names:
            raise ValueError(
                f"Unknown variant '{variant_name}' for experiment '{experiment_name}'"
            )

        self._outcomes[experiment_name].append(
            _Outcome(
                contact_id=contact_id,
                variant_name=variant_name,
                score=score,
                success=success,
                timestamp=time.time(),
            )
        )
        logger.debug(
            "Recorded outcome for %s/%s: score=%.2f, success=%s",
            experiment_name, variant_name, score, success,
        )

    # ── Statistical Analysis ───────────────────────────────────────────

    def analyze(self, experiment_name: str) -> ExperimentResult:
        """Analyze experiment results with z-test significance.

        Performs a two-proportion z-test between the two variants with
        the highest success rates.

        Args:
            experiment_name: Target experiment.

        Returns:
            ExperimentResult with per-variant stats and significance.

        Raises:
            KeyError: If experiment does not exist.
        """
        experiment = self._get_experiment(experiment_name)
        outcomes = self._outcomes.get(experiment_name, [])

        # Build per-variant stats
        variant_data: Dict[str, List[_Outcome]] = {}
        for v in experiment.variants:
            variant_data[v.name] = []
        for o in outcomes:
            if o.variant_name in variant_data:
                variant_data[o.variant_name].append(o)

        variant_stats: Dict[str, VariantStats] = {}
        for vname, v_outcomes in variant_data.items():
            n = len(v_outcomes)
            successes = sum(1 for o in v_outcomes if o.success)
            scores = [o.score for o in v_outcomes]

            if n > 0:
                mean_score = sum(scores) / n
                variance = sum((s - mean_score) ** 2 for s in scores) / n
                std_dev = math.sqrt(variance)
            else:
                mean_score = 0.0
                std_dev = 0.0

            variant_stats[vname] = VariantStats(
                variant_name=vname,
                sample_size=n,
                successes=successes,
                mean_score=round(mean_score, 4),
                std_dev=round(std_dev, 4),
            )

        # Z-test between top two variants by success rate
        sorted_variants = sorted(
            variant_stats.values(),
            key=lambda vs: vs.successes / max(vs.sample_size, 1),
            reverse=True,
        )

        p_value = 1.0
        winner = None
        is_significant = False

        if (
            len(sorted_variants) >= 2
            and sorted_variants[0].sample_size > 0
            and sorted_variants[1].sample_size > 0
        ):
            p_value = self._two_proportion_z_test(
                sorted_variants[0].successes,
                sorted_variants[0].sample_size,
                sorted_variants[1].successes,
                sorted_variants[1].sample_size,
            )
            is_significant = p_value < 0.05
            if is_significant:
                winner = sorted_variants[0].variant_name

        confidence = round(1.0 - p_value, 4)

        return ExperimentResult(
            experiment_name=experiment_name,
            variant_stats=variant_stats,
            winner=winner,
            p_value=round(p_value, 6),
            confidence=confidence,
            is_significant=is_significant,
        )

    # ── Early Stopping ─────────────────────────────────────────────────

    def should_stop_early(
        self,
        experiment_name: str,
        confidence_threshold: float = 0.95,
    ) -> bool:
        """Check if the experiment can be stopped early.

        Returns True if the z-test confidence exceeds the threshold
        and each variant has at least 30 samples.

        Args:
            experiment_name: Target experiment.
            confidence_threshold: Required confidence level (default 0.95).

        Returns:
            True if the experiment should stop early.

        Raises:
            KeyError: If experiment does not exist.
        """
        result = self.analyze(experiment_name)

        # Need minimum sample size per variant for reliable stopping
        min_sample = 30
        for vs in result.variant_stats.values():
            if vs.sample_size < min_sample:
                return False

        return result.confidence >= confidence_threshold

    # ── Internal Helpers ───────────────────────────────────────────────

    def _get_experiment(self, name: str) -> PromptExperiment:
        """Retrieve an experiment or raise KeyError."""
        try:
            return self._experiments[name]
        except KeyError:
            raise KeyError(f"Experiment '{name}' not found")

    @staticmethod
    def _two_proportion_z_test(k1: int, n1: int, k2: int, n2: int) -> float:
        """Two-proportion z-test returning a two-sided p-value.

        Args:
            k1: Successes in group 1.
            n1: Trials in group 1.
            k2: Successes in group 2.
            n2: Trials in group 2.

        Returns:
            Two-sided p-value (0.0 to 1.0).
        """
        if n1 == 0 or n2 == 0:
            return 1.0

        p1 = k1 / n1
        p2 = k2 / n2
        p_pool = (k1 + k2) / (n1 + n2)

        if p_pool == 0.0 or p_pool == 1.0:
            return 1.0

        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        if se == 0:
            return 1.0

        z = abs(p1 - p2) / se
        p_value = math.erfc(z / math.sqrt(2))
        return p_value
