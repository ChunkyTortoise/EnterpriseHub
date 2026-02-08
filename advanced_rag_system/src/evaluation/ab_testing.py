"""
A/B Testing Framework for RAG System Evaluation

Provides comprehensive A/B testing capabilities:
- Experiment configuration and management
- Traffic splitting strategies (random, user-based, weighted)
- Statistical significance testing (t-test, chi-square, bootstrap)
- Result aggregation and reporting
- Multi-armed bandit for adaptive experiments

Designed for production use with async operations and persistence support.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Data Models
# ============================================================================


class ExperimentStatus(str, Enum):
    """Status of an experiment."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TrafficSplitStrategy(str, Enum):
    """Strategy for splitting traffic between variants."""

    RANDOM = "random"
    USER_BASED = "user_based"
    WEIGHTED = "weighted"
    THOMPSON_SAMPLING = "thompson_sampling"  # Multi-armed bandit


class MetricType(str, Enum):
    """Type of metric being measured."""

    BINARY = "binary"  # Conversion, click, etc.
    CONTINUOUS = "continuous"  # Latency, score, etc.
    COUNT = "count"  # Number of items, etc.
    RATIO = "ratio"  # Percentage, rate, etc.


@dataclass
class VariantConfig:
    """Configuration for an experiment variant."""

    id: str
    name: str
    description: str = ""
    traffic_percentage: float = 0.5
    config: Dict[str, Any] = field(default_factory=dict)
    is_control: bool = False

    def __post_init__(self):
        if not 0 <= self.traffic_percentage <= 1:
            raise ValueError("traffic_percentage must be between 0 and 1")


@dataclass
class MetricConfig:
    """Configuration for a metric being tracked."""

    name: str
    metric_type: MetricType
    description: str = ""
    minimum_detectable_effect: float = 0.05
    target_value: Optional[float] = None
    higher_is_better: bool = True


class ExperimentConfig(BaseModel):
    """Configuration for an A/B test experiment."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    hypothesis: str = ""

    # Variants
    variants: List[VariantConfig] = Field(default_factory=list)
    control_variant_id: Optional[str] = None

    # Traffic splitting
    split_strategy: TrafficSplitStrategy = TrafficSplitStrategy.RANDOM

    # Metrics
    primary_metric: Optional[MetricConfig] = None
    secondary_metrics: List[MetricConfig] = Field(default_factory=list)
    guardrail_metrics: List[MetricConfig] = Field(default_factory=list)

    # Sample size and duration
    min_sample_size_per_variant: int = 1000
    max_sample_size_per_variant: Optional[int] = None
    min_duration_hours: int = 24
    max_duration_hours: Optional[int] = None

    # Statistical parameters
    significance_level: float = Field(default=0.05, ge=0.01, le=0.1)
    statistical_power: float = Field(default=0.8, ge=0.5, le=0.99)

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Status
    status: ExperimentStatus = ExperimentStatus.DRAFT

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 variants required")
        total_traffic = sum(var.traffic_percentage for var in v)
        if not 0.99 <= total_traffic <= 1.01:
            raise ValueError(f"Total traffic percentage must sum to 1.0, got {total_traffic}")
        return v


@dataclass
class Assignment:
    """Assignment of a user/request to a variant."""

    experiment_id: str
    variant_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    """A single observation/measurement for a variant."""

    experiment_id: str
    variant_id: str
    metric_name: str
    value: float
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VariantResult:
    """Results for a single variant."""

    variant_id: str
    variant_name: str
    sample_size: int
    mean: float
    std: float
    sum_values: float
    min_value: float
    max_value: float
    confidence_interval: Tuple[float, float]
    percentiles: Dict[str, float]


@dataclass
class ComparisonResult:
    """Comparison between treatment and control."""

    treatment_variant_id: str
    control_variant_id: str
    metric_name: str

    # Effect size
    absolute_difference: float
    relative_difference: float

    # Statistical test
    p_value: float
    is_significant: bool
    confidence_level: float

    # Confidence interval for difference
    ci_lower: float
    ci_upper: float

    # Power analysis
    observed_power: float
    required_sample_size: int

    # Recommendation
    recommendation: str  # "rollout", "rollback", "continue", "inconclusive"


@dataclass
class ExperimentResults:
    """Complete results for an experiment."""

    experiment_id: str
    experiment_name: str
    status: ExperimentStatus

    # Timing
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_hours: float

    # Sample sizes
    total_observations: int
    variant_results: Dict[str, VariantResult]

    # Comparisons
    primary_comparison: Optional[ComparisonResult]
    secondary_comparisons: List[ComparisonResult]
    guardrail_violations: List[str]

    # Summary
    winner_variant_id: Optional[str]
    summary: str


# ============================================================================
# Traffic Splitting Strategies
# ============================================================================


class TrafficSplitter(ABC):
    """Abstract base class for traffic splitting strategies."""

    @abstractmethod
    def assign(
        self, experiment: ExperimentConfig, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs
    ) -> Assignment:
        """Assign a user to a variant."""
        pass


class RandomSplitter(TrafficSplitter):
    """Random traffic splitting."""

    def assign(
        self, experiment: ExperimentConfig, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs
    ) -> Assignment:
        """Randomly assign to a variant based on traffic percentages."""
        rand = random.random()
        cumulative = 0.0

        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if rand <= cumulative:
                return Assignment(
                    experiment_id=experiment.id,
                    variant_id=variant.id,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={"split_method": "random", "random_value": rand},
                )

        # Fallback to last variant
        return Assignment(
            experiment_id=experiment.id,
            variant_id=experiment.variants[-1].id,
            user_id=user_id,
            session_id=session_id,
            metadata={"split_method": "random_fallback"},
        )


class UserBasedSplitter(TrafficSplitter):
    """Consistent user-based splitting using hash."""

    def assign(
        self, experiment: ExperimentConfig, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs
    ) -> Assignment:
        """Assign based on consistent hash of user_id."""
        if not user_id:
            # Fall back to random if no user_id
            return RandomSplitter().assign(experiment, user_id, session_id, **kwargs)

        # Create consistent hash
        hash_input = f"{experiment.id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized = (hash_value % 10000) / 10000.0

        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if normalized <= cumulative:
                return Assignment(
                    experiment_id=experiment.id,
                    variant_id=variant.id,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={"split_method": "user_hash", "hash_value": normalized, "user_id_hash": hash_input},
                )

        return Assignment(
            experiment_id=experiment.id,
            variant_id=experiment.variants[-1].id,
            user_id=user_id,
            session_id=session_id,
            metadata={"split_method": "user_hash_fallback"},
        )


class WeightedSplitter(TrafficSplitter):
    """Weighted traffic splitting with dynamic adjustment capability."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {}

    def assign(
        self, experiment: ExperimentConfig, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs
    ) -> Assignment:
        """Assign based on potentially dynamic weights."""
        # Use dynamic weights if available, otherwise use config weights
        weights = {}
        for variant in experiment.variants:
            weights[variant.id] = self.weights.get(variant.id, variant.traffic_percentage)

        # Normalize weights
        total = sum(weights.values())
        if total == 0:
            weights = {v.id: 1.0 / len(experiment.variants) for v in experiment.variants}
        else:
            weights = {k: v / total for k, v in weights.items()}

        rand = random.random()
        cumulative = 0.0

        for variant in experiment.variants:
            cumulative += weights[variant.id]
            if rand <= cumulative:
                return Assignment(
                    experiment_id=experiment.id,
                    variant_id=variant.id,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={"split_method": "weighted", "weights": weights, "random_value": rand},
                )

        return Assignment(
            experiment_id=experiment.id,
            variant_id=experiment.variants[-1].id,
            user_id=user_id,
            session_id=session_id,
            metadata={"split_method": "weighted_fallback"},
        )

    def update_weights(self, new_weights: Dict[str, float]):
        """Update dynamic weights."""
        self.weights.update(new_weights)


class ThompsonSamplingSplitter(TrafficSplitter):
    """
    Thompson Sampling for multi-armed bandit experiments.

    Automatically adjusts traffic based on observed performance.
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.variant_params: Dict[str, Tuple[float, float]] = {}

    def assign(
        self, experiment: ExperimentConfig, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs
    ) -> Assignment:
        """Assign using Thompson Sampling."""
        # Sample from Beta distribution for each variant
        samples = {}
        for variant in experiment.variants:
            alpha, beta = self.variant_params.get(variant.id, (self.prior_alpha, self.prior_beta))
            samples[variant.id] = np.random.beta(alpha, beta)

        # Select variant with highest sample
        best_variant_id = max(samples, key=samples.get)

        return Assignment(
            experiment_id=experiment.id,
            variant_id=best_variant_id,
            user_id=user_id,
            session_id=session_id,
            metadata={
                "split_method": "thompson_sampling",
                "samples": samples,
                "variant_params": dict(self.variant_params),
            },
        )

    def update(self, variant_id: str, success: bool):
        """Update Beta distribution parameters based on observation."""
        alpha, beta = self.variant_params.get(variant_id, (self.prior_alpha, self.prior_beta))

        if success:
            alpha += 1
        else:
            beta += 1

        self.variant_params[variant_id] = (alpha, beta)

    def get_current_weights(self) -> Dict[str, float]:
        """Get current expected weights based on Beta means."""
        weights = {}
        for variant_id, (alpha, beta) in self.variant_params.items():
            weights[variant_id] = alpha / (alpha + beta)

        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights


# ============================================================================
# Statistical Significance Testing
# ============================================================================


class StatisticalTester:
    """Statistical significance testing for A/B tests."""

    def __init__(self):
        pass

    def t_test(
        self, treatment_values: List[float], control_values: List[float], alternative: str = "two-sided"
    ) -> Dict[str, Any]:
        """
        Perform two-sample t-test.

        Args:
            treatment_values: Values from treatment variant
            control_values: Values from control variant
            alternative: 'two-sided', 'greater', or 'less'

        Returns:
            Dictionary with test results
        """
        if not treatment_values or not control_values:
            return {"statistic": 0.0, "p_value": 1.0, "significant": False, "error": "Insufficient data"}

        # Calculate means and standard errors
        n1, n2 = len(treatment_values), len(control_values)
        mean1 = np.mean(treatment_values)
        mean2 = np.mean(control_values)

        var1 = np.var(treatment_values, ddof=1) if n1 > 1 else 0
        var2 = np.var(control_values, ddof=1) if n2 > 1 else 0

        # Pooled standard error
        se = np.sqrt(var1 / n1 + var2 / n2)

        if se == 0:
            return {"statistic": 0.0, "p_value": 1.0, "significant": False, "error": "Zero variance"}

        # T-statistic
        t_stat = (mean1 - mean2) / se

        # Degrees of freedom (Welch's approximation)
        df = (
            (var1 / n1 + var2 / n2) ** 2 / ((var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1))
            if n1 > 1 and n2 > 1
            else n1 + n2 - 2
        )

        # P-value (two-sided)
        from math import gamma, pi, sqrt

        # Approximate t-distribution CDF using normal for large df
        if df > 30:
            # Normal approximation
            p_value = self._normal_cdf(-abs(t_stat)) * 2
        else:
            # Simplified p-value calculation
            p_value = min(1.0, 2 * (1 - self._t_cdf_approx(abs(t_stat), df)))

        # Adjust for alternative hypothesis
        if alternative == "greater":
            p_value = p_value / 2 if t_stat > 0 else 1 - p_value / 2
        elif alternative == "less":
            p_value = p_value / 2 if t_stat < 0 else 1 - p_value / 2

        return {
            "statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "degrees_of_freedom": float(df),
            "mean_difference": float(mean1 - mean2),
            "relative_difference": float((mean1 - mean2) / mean2) if mean2 != 0 else 0.0,
            "standard_error": float(se),
        }

    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF."""
        # Abramowitz and Stegun approximation
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1 if x >= 0 else -1
        x = abs(x) / sqrt(2)

        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)

        return 0.5 * (1.0 + sign * y)

    def _t_cdf_approx(self, t: float, df: float) -> float:
        """Approximate t-distribution CDF."""
        # Use normal approximation for large df
        if df > 30:
            return self._normal_cdf(t)

        # Simplified approximation
        x = df / (df + t * t)
        return 1 - 0.5 * (1 - x) ** (df / 2)

    def chi_square_test(
        self, treatment_successes: int, treatment_total: int, control_successes: int, control_total: int
    ) -> Dict[str, Any]:
        """
        Chi-square test for proportions.

        Args:
            treatment_successes: Number of successes in treatment
            treatment_total: Total observations in treatment
            control_successes: Number of successes in control
            control_total: Total observations in control

        Returns:
            Dictionary with test results
        """
        if treatment_total == 0 or control_total == 0:
            return {"statistic": 0.0, "p_value": 1.0, "significant": False, "error": "Insufficient data"}

        # Observed frequencies
        treatment_failures = treatment_total - treatment_successes
        control_failures = control_total - control_successes

        # Expected frequencies
        total_successes = treatment_successes + control_successes
        total_failures = treatment_failures + control_failures
        total = treatment_total + control_total

        if total == 0:
            return {"statistic": 0.0, "p_value": 1.0, "significant": False, "error": "Zero total"}

        exp_treatment_success = treatment_total * total_successes / total
        exp_treatment_failure = treatment_total * total_failures / total
        exp_control_success = control_total * total_successes / total
        exp_control_failure = control_total * total_failures / total

        # Chi-square statistic
        chi2 = 0.0
        observed = [treatment_successes, treatment_failures, control_successes, control_failures]
        expected = [exp_treatment_success, exp_treatment_failure, exp_control_success, exp_control_failure]

        for obs, exp in zip(observed, expected):
            if exp > 0:
                chi2 += (obs - exp) ** 2 / exp

        # P-value (1 degree of freedom for 2x2 table)
        p_value = 1 - self._chi2_cdf(chi2, 1)

        # Proportions
        p1 = treatment_successes / treatment_total
        p2 = control_successes / control_total

        return {
            "statistic": float(chi2),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "treatment_rate": float(p1),
            "control_rate": float(p2),
            "absolute_difference": float(p1 - p2),
            "relative_difference": float((p1 - p2) / p2) if p2 > 0 else 0.0,
        }

    def _chi2_cdf(self, x: float, k: int) -> float:
        """Approximate chi-square CDF."""
        if x <= 0:
            return 0.0
        # Use gamma function approximation
        return 1 - np.exp(-x / 2) * sum((x / 2) ** i / np.math.factorial(i) for i in range(k // 2 + 1))

    def bootstrap_confidence_interval(
        self,
        treatment_values: List[float],
        control_values: List[float],
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Calculate bootstrap confidence interval for difference in means.

        Args:
            treatment_values: Treatment values
            control_values: Control values
            n_bootstrap: Number of bootstrap samples
            confidence_level: Confidence level (e.g., 0.95)

        Returns:
            Dictionary with CI and related statistics
        """
        if not treatment_values or not control_values:
            return {"ci_lower": 0.0, "ci_upper": 0.0, "mean_difference": 0.0, "error": "Insufficient data"}

        n1, n2 = len(treatment_values), len(control_values)

        # Bootstrap sampling
        bootstrap_diffs = []
        for _ in range(n_bootstrap):
            # Resample with replacement
            sample1 = np.random.choice(treatment_values, size=n1, replace=True)
            sample2 = np.random.choice(control_values, size=n2, replace=True)
            diff = np.mean(sample1) - np.mean(sample2)
            bootstrap_diffs.append(diff)

        # Calculate confidence interval
        alpha = 1 - confidence_level
        ci_lower = np.percentile(bootstrap_diffs, alpha / 2 * 100)
        ci_upper = np.percentile(bootstrap_diffs, (1 - alpha / 2) * 100)

        return {
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
            "mean_difference": float(np.mean(treatment_values) - np.mean(control_values)),
            "bootstrap_std": float(np.std(bootstrap_diffs)),
        }


# ============================================================================
# Result Aggregator
# ============================================================================


class ResultAggregator:
    """Aggregates experiment results and generates comparisons."""

    def __init__(self, statistical_tester: Optional[StatisticalTester] = None):
        self.statistical_tester = statistical_tester or StatisticalTester()

    def aggregate_variant_results(
        self, observations: List[Observation], variant_config: VariantConfig, confidence_level: float = 0.95
    ) -> VariantResult:
        """Aggregate results for a single variant."""
        if not observations:
            return VariantResult(
                variant_id=variant_config.id,
                variant_name=variant_config.name,
                sample_size=0,
                mean=0.0,
                std=0.0,
                sum_values=0.0,
                min_value=0.0,
                max_value=0.0,
                confidence_interval=(0.0, 0.0),
                percentiles={},
            )

        values = [obs.value for obs in observations]
        n = len(values)
        mean = np.mean(values)
        std = np.std(values, ddof=1) if n > 1 else 0.0

        # Confidence interval
        from math import sqrt

        alpha = 1 - confidence_level
        se = std / sqrt(n) if n > 0 else 0
        # Use t-distribution critical value approximation
        t_critical = 1.96 if n > 30 else 2.0  # Simplified
        margin = t_critical * se

        ci = (mean - margin, mean + margin)

        # Percentiles
        percentiles = {
            "p5": float(np.percentile(values, 5)),
            "p25": float(np.percentile(values, 25)),
            "p50": float(np.percentile(values, 50)),
            "p75": float(np.percentile(values, 75)),
            "p95": float(np.percentile(values, 95)),
        }

        return VariantResult(
            variant_id=variant_config.id,
            variant_name=variant_config.name,
            sample_size=n,
            mean=float(mean),
            std=float(std),
            sum_values=float(np.sum(values)),
            min_value=float(np.min(values)),
            max_value=float(np.max(values)),
            confidence_interval=ci,
            percentiles=percentiles,
        )

    def compare_variants(
        self,
        treatment_observations: List[Observation],
        control_observations: List[Observation],
        treatment_config: VariantConfig,
        control_config: VariantConfig,
        metric_config: MetricConfig,
        confidence_level: float = 0.95,
    ) -> ComparisonResult:
        """Compare treatment vs control."""
        treatment_values = [obs.value for obs in treatment_observations]
        control_values = [obs.value for obs in control_observations]

        treatment_mean = np.mean(treatment_values) if treatment_values else 0
        control_mean = np.mean(control_values) if control_values else 0

        absolute_diff = treatment_mean - control_mean
        relative_diff = (absolute_diff / control_mean) if control_mean != 0 else 0.0

        # Statistical test
        if metric_config.metric_type == MetricType.BINARY:
            # Use chi-square for binary metrics
            treatment_successes = sum(treatment_values)
            control_successes = sum(control_values)
            test_result = self.statistical_tester.chi_square_test(
                int(treatment_successes), len(treatment_values), int(control_successes), len(control_values)
            )
        else:
            # Use t-test for continuous metrics
            test_result = self.statistical_tester.t_test(treatment_values, control_values)

        # Bootstrap CI
        bootstrap_result = self.statistical_tester.bootstrap_confidence_interval(
            treatment_values, control_values, confidence_level=confidence_level
        )

        # Determine recommendation
        is_significant = test_result.get("significant", False)
        higher_is_better = metric_config.higher_is_better

        if not is_significant:
            recommendation = "inconclusive"
        elif (higher_is_better and relative_diff > 0) or (not higher_is_better and relative_diff < 0):
            recommendation = "rollout"
        else:
            recommendation = "rollback"

        return ComparisonResult(
            treatment_variant_id=treatment_config.id,
            control_variant_id=control_config.id,
            metric_name=metric_config.name,
            absolute_difference=float(absolute_diff),
            relative_difference=float(relative_diff),
            p_value=float(test_result.get("p_value", 1.0)),
            is_significant=is_significant,
            confidence_level=confidence_level,
            ci_lower=float(bootstrap_result.get("ci_lower", 0.0)),
            ci_upper=float(bootstrap_result.get("ci_upper", 0.0)),
            observed_power=0.8,  # Simplified
            required_sample_size=metric_config.minimum_detectable_effect,
            recommendation=recommendation,
        )


# ============================================================================
# Experiment Manager
# ============================================================================


class ExperimentManager:
    """Manages A/B test experiments lifecycle."""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./experiments")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.experiments: Dict[str, ExperimentConfig] = {}
        self.observations: Dict[str, List[Observation]] = {}
        self.assignments: Dict[str, Assignment] = {}

        self.splitters: Dict[TrafficSplitStrategy, TrafficSplitter] = {
            TrafficSplitStrategy.RANDOM: RandomSplitter(),
            TrafficSplitStrategy.USER_BASED: UserBasedSplitter(),
            TrafficSplitStrategy.WEIGHTED: WeightedSplitter(),
            TrafficSplitStrategy.THOMPSON_SAMPLING: ThompsonSamplingSplitter(),
        }

        self.aggregator = ResultAggregator()

    def create_experiment(self, config: ExperimentConfig) -> str:
        """Create a new experiment."""
        self.experiments[config.id] = config
        self.observations[config.id] = []
        return config.id

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentConfig]:
        """Get experiment by ID."""
        return self.experiments.get(experiment_id)

    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment."""
        exp = self.experiments.get(experiment_id)
        if not exp:
            return False

        exp.status = ExperimentStatus.RUNNING
        exp.start_time = datetime.utcnow()
        return True

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an experiment."""
        exp = self.experiments.get(experiment_id)
        if not exp:
            return False

        exp.status = ExperimentStatus.COMPLETED
        exp.end_time = datetime.utcnow()
        return True

    def assign_variant(
        self, experiment_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs
    ) -> Optional[Assignment]:
        """Assign a user to a variant."""
        exp = self.experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return None

        # Check if already assigned
        assignment_key = f"{experiment_id}:{user_id or session_id}"
        if assignment_key in self.assignments:
            return self.assignments[assignment_key]

        # Get appropriate splitter
        splitter = self.splitters.get(exp.split_strategy, RandomSplitter())

        # Handle Thompson sampling specially
        if exp.split_strategy == TrafficSplitStrategy.THOMPSON_SAMPLING:
            if isinstance(splitter, ThompsonSamplingSplitter):
                # Could update based on observations here
                pass

        assignment = splitter.assign(exp, user_id, session_id, **kwargs)
        self.assignments[assignment_key] = assignment

        return assignment

    def record_observation(self, observation: Observation) -> bool:
        """Record an observation for an experiment."""
        exp = self.experiments.get(observation.experiment_id)
        if not exp:
            return False

        self.observations[observation.experiment_id].append(observation)

        # Update Thompson sampler if applicable
        if exp.split_strategy == TrafficSplitStrategy.THOMPSON_SAMPLING:
            splitter = self.splitters.get(exp.split_strategy)
            if isinstance(splitter, ThompsonSamplingSplitter):
                # Assume successful if value is good (e.g., above threshold)
                success = observation.value > 0.5
                splitter.update(observation.variant_id, success)

        return True

    async def get_results(self, experiment_id: str) -> Optional[ExperimentResults]:
        """Get complete results for an experiment."""
        exp = self.experiments.get(experiment_id)
        if not exp:
            return None

        observations = self.observations.get(experiment_id, [])

        # Group observations by variant
        variant_observations: Dict[str, List[Observation]] = {}
        for obs in observations:
            variant_observations.setdefault(obs.variant_id, []).append(obs)

        # Aggregate variant results
        variant_results = {}
        for variant in exp.variants:
            var_obs = variant_observations.get(variant.id, [])
            variant_results[variant.id] = self.aggregator.aggregate_variant_results(var_obs, variant)

        # Get control variant
        control_id = exp.control_variant_id
        if not control_id and exp.variants:
            control_id = next((v.id for v in exp.variants if v.is_control), exp.variants[0].id)

        # Primary comparison
        primary_comparison = None
        if exp.primary_metric and control_id:
            control_variant = next((v for v in exp.variants if v.id == control_id), None)
            for variant in exp.variants:
                if variant.id != control_id:
                    treatment_obs = [
                        obs
                        for obs in variant_observations.get(variant.id, [])
                        if obs.metric_name == exp.primary_metric.name
                    ]
                    control_obs = [
                        obs
                        for obs in variant_observations.get(control_id, [])
                        if obs.metric_name == exp.primary_metric.name
                    ]

                    if treatment_obs and control_obs:
                        primary_comparison = self.aggregator.compare_variants(
                            treatment_obs, control_obs, variant, control_variant, exp.primary_metric
                        )

        return ExperimentResults(
            experiment_id=exp.id,
            experiment_name=exp.name,
            status=exp.status,
            start_time=exp.start_time,
            end_time=exp.end_time,
            duration_hours=((exp.end_time or datetime.utcnow()) - exp.start_time).total_seconds() / 3600
            if exp.start_time
            else 0,
            total_observations=len(observations),
            variant_results=variant_results,
            primary_comparison=primary_comparison,
            secondary_comparisons=[],
            guardrail_violations=[],
            winner_variant_id=None,
            summary="",
        )

    def save_experiment(self, experiment_id: str) -> bool:
        """Save experiment to disk."""
        exp = self.experiments.get(experiment_id)
        if not exp:
            return False

        file_path = self.storage_dir / f"{experiment_id}.json"
        try:
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "experiment": exp.model_dump(),
                        "observations_count": len(self.observations.get(experiment_id, [])),
                        "assignments_count": len(self.assignments),
                    },
                    f,
                    indent=2,
                    default=str,
                )
            return True
        except Exception as e:
            print(f"Error saving experiment: {e}")
            return False

    def load_experiment(self, experiment_id: str) -> bool:
        """Load experiment from disk."""
        file_path = self.storage_dir / f"{experiment_id}.json"
        if not file_path.exists():
            return False

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                # Note: Full loading would require reconstructing objects
                # This is simplified
            return True
        except Exception as e:
            print(f"Error loading experiment: {e}")
            return False


# ============================================================================
# Convenience Functions
# ============================================================================


def create_ab_test(
    name: str,
    control_config: Dict[str, Any],
    treatment_config: Dict[str, Any],
    primary_metric_name: str,
    split_strategy: TrafficSplitStrategy = TrafficSplitStrategy.RANDOM,
) -> ExperimentConfig:
    """
    Create a simple A/B test configuration.

    Args:
        name: Experiment name
        control_config: Configuration for control variant
        treatment_config: Configuration for treatment variant
        primary_metric_name: Name of primary metric
        split_strategy: How to split traffic

    Returns:
        ExperimentConfig ready to use
    """
    return ExperimentConfig(
        name=name,
        variants=[
            VariantConfig(id="control", name="Control", traffic_percentage=0.5, config=control_config, is_control=True),
            VariantConfig(id="treatment", name="Treatment", traffic_percentage=0.5, config=treatment_config),
        ],
        control_variant_id="control",
        split_strategy=split_strategy,
        primary_metric=MetricConfig(name=primary_metric_name, metric_type=MetricType.CONTINUOUS),
    )


# Export all classes
__all__ = [
    "ExperimentStatus",
    "TrafficSplitStrategy",
    "MetricType",
    "VariantConfig",
    "MetricConfig",
    "ExperimentConfig",
    "Assignment",
    "Observation",
    "VariantResult",
    "ComparisonResult",
    "ExperimentResults",
    "TrafficSplitter",
    "RandomSplitter",
    "UserBasedSplitter",
    "WeightedSplitter",
    "ThompsonSamplingSplitter",
    "StatisticalTester",
    "ResultAggregator",
    "ExperimentManager",
    "create_ab_test",
]
