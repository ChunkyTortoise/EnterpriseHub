"""A/B testing service with deterministic variant assignment and z-test significance."""

from __future__ import annotations

import hashlib
import math
import statistics
from dataclasses import dataclass, field


@dataclass
class Variant:
    name: str
    version_id: int
    traffic_percentage: float  # 0.0-1.0
    samples: int = 0
    metric_values: list[float] = field(default_factory=list)


@dataclass
class ExperimentConfig:
    experiment_id: str
    prompt_id: str
    variants: list[Variant]
    metric: str = "latency"
    significance_threshold: float = 0.95
    min_samples: int = 100


@dataclass
class SignificanceResult:
    is_significant: bool
    p_value: float
    z_score: float
    winner: str | None
    control_mean: float
    variant_mean: float
    confidence: float


class ABTestingService:
    """Deterministic variant assignment with z-test statistical significance."""

    def __init__(self) -> None:
        self._experiments: dict[str, ExperimentConfig] = {}

    def create_experiment(self, config: ExperimentConfig) -> ExperimentConfig:
        total = sum(v.traffic_percentage for v in config.variants)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Variant traffic percentages must sum to 1.0, got {total}")
        self._experiments[config.experiment_id] = config
        return config

    def get_experiment(self, experiment_id: str) -> ExperimentConfig | None:
        return self._experiments.get(experiment_id)

    def assign_variant(self, experiment_id: str, subject_id: str) -> str | None:
        config = self._experiments.get(experiment_id)
        if not config:
            return None
        hash_input = f"{experiment_id}:{subject_id}"
        hash_val = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16) % 10000
        bucket = hash_val / 10000.0

        cumulative = 0.0
        for variant in config.variants:
            cumulative += variant.traffic_percentage
            if bucket < cumulative:
                return variant.name
        return config.variants[-1].name

    def record_observation(self, experiment_id: str, variant_name: str, value: float) -> bool:
        config = self._experiments.get(experiment_id)
        if not config:
            return False
        for v in config.variants:
            if v.name == variant_name:
                v.metric_values.append(value)
                v.samples += 1
                return True
        return False

    def compute_significance(self, experiment_id: str) -> SignificanceResult | None:
        config = self._experiments.get(experiment_id)
        if not config or len(config.variants) < 2:
            return None

        control = config.variants[0]
        treatment = config.variants[1]

        if control.samples < 2 or treatment.samples < 2:
            return SignificanceResult(
                is_significant=False, p_value=1.0, z_score=0.0,
                winner=None, control_mean=0.0, variant_mean=0.0, confidence=0.0,
            )

        c_mean = statistics.mean(control.metric_values)
        t_mean = statistics.mean(treatment.metric_values)
        c_var = statistics.variance(control.metric_values)
        t_var = statistics.variance(treatment.metric_values)

        se = math.sqrt(c_var / control.samples + t_var / treatment.samples)
        if se == 0:
            return SignificanceResult(
                is_significant=False, p_value=1.0, z_score=0.0,
                winner=None, control_mean=c_mean, variant_mean=t_mean, confidence=0.0,
            )

        z = (t_mean - c_mean) / se
        p_value = 2 * (1 - _norm_cdf(abs(z)))
        confidence = 1 - p_value
        is_sig = confidence >= config.significance_threshold and min(control.samples, treatment.samples) >= config.min_samples

        winner = None
        if is_sig:
            # Lower is better for latency, higher for quality
            if config.metric == "latency":
                winner = treatment.name if t_mean < c_mean else control.name
            else:
                winner = treatment.name if t_mean > c_mean else control.name

        return SignificanceResult(
            is_significant=is_sig, p_value=p_value, z_score=z,
            winner=winner, control_mean=c_mean, variant_mean=t_mean,
            confidence=confidence,
        )

    def list_experiments(self) -> list[ExperimentConfig]:
        return list(self._experiments.values())


def _norm_cdf(x: float) -> float:
    """Approximate the standard normal CDF using the error function."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
