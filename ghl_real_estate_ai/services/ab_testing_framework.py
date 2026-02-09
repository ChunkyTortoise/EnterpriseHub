#!/usr/bin/env python3
"""
🧪 A/B Testing Framework for Predictive Lead Scoring
==================================================

Comprehensive A/B testing framework for continuous optimization
of the lead scoring system with statistical significance testing.

Features:
- Multi-variate A/B testing
- Statistical significance calculation
- Performance metric tracking
- Automated experiment management
- Real-time result monitoring
- Gradual rollout capabilities

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

import asyncio
import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class ExperimentStatus(Enum):
    """Experiment status types"""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentType(Enum):
    """Types of experiments"""

    MODEL_COMPARISON = "model_comparison"
    ALGORITHM_VARIANT = "algorithm_variant"
    FEATURE_FLAG = "feature_flag"
    ROUTING_STRATEGY = "routing_strategy"
    SIGNAL_WEIGHTING = "signal_weighting"
    UI_VARIANT = "ui_variant"


class MetricType(Enum):
    """Types of metrics to track"""

    CONVERSION_RATE = "conversion_rate"
    RESPONSE_TIME = "response_time"
    ACCURACY = "accuracy"
    AGENT_EFFICIENCY = "agent_efficiency"
    LEAD_QUALITY = "lead_quality"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class ExperimentVariant:
    """Experiment variant definition"""

    variant_id: str
    name: str
    description: str
    traffic_percentage: float  # 0-100
    configuration: Dict[str, Any]
    is_control: bool = False


@dataclass
class ExperimentMetric:
    """Metric definition for experiments"""

    metric_name: str
    metric_type: MetricType
    target_improvement: float  # % improvement expected
    statistical_power: float = 0.8
    significance_level: float = 0.05
    minimum_sample_size: int = 100


@dataclass
class ExperimentResult:
    """Results for a specific variant"""

    variant_id: str
    sample_size: int
    conversions: int
    conversion_rate: float
    confidence_interval: Tuple[float, float]
    statistical_significance: Optional[float]
    metric_values: Dict[str, List[float]]


@dataclass
class Experiment:
    """Complete experiment definition and state"""

    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    status: ExperimentStatus

    # Configuration
    variants: List[ExperimentVariant]
    metrics: List[ExperimentMetric]
    target_audience: Dict[str, Any]  # Targeting criteria

    # Timeline
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    # Results tracking
    results: Dict[str, ExperimentResult] = field(default_factory=dict)

    # Metadata
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)


class StatisticalAnalyzer:
    """Statistical analysis for A/B test results"""

    @staticmethod
    def calculate_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        significance_level: float = 0.05,
        statistical_power: float = 0.8,
    ) -> int:
        """Calculate minimum sample size needed for statistical significance"""

        # Z-scores for two-tailed test
        z_alpha = 1.96 if significance_level == 0.05 else 2.576  # α = 0.05 or 0.01
        z_beta = 0.842 if statistical_power == 0.8 else 1.036  # Power = 0.8 or 0.9

        # Expected conversion rates
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)

        # Pooled probability
        p_pooled = (p1 + p2) / 2

        # Sample size calculation
        numerator = (
            z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
        ) ** 2
        denominator = (p2 - p1) ** 2

        sample_size_per_group = math.ceil(numerator / denominator)

        return sample_size_per_group

    @staticmethod
    def calculate_confidence_interval(
        successes: int, total: int, confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for conversion rate"""

        if total == 0:
            return (0.0, 0.0)

        rate = successes / total
        z_score = 1.96 if confidence_level == 0.95 else 2.576

        # Wilson score interval (more accurate for small samples)
        n = total
        p_hat = rate

        center = (p_hat + z_score**2 / (2 * n)) / (1 + z_score**2 / n)
        margin = z_score * math.sqrt((p_hat * (1 - p_hat) + z_score**2 / (4 * n)) / n) / (1 + z_score**2 / n)

        lower_bound = max(0, center - margin)
        upper_bound = min(1, center + margin)

        return (lower_bound, upper_bound)

    @staticmethod
    def calculate_statistical_significance(
        control_successes: int, control_total: int, variant_successes: int, variant_total: int
    ) -> float:
        """Calculate p-value for statistical significance"""

        if control_total == 0 or variant_total == 0:
            return 1.0

        # Proportions
        p1 = control_successes / control_total
        p2 = variant_successes / variant_total

        # Pooled proportion
        p_pooled = (control_successes + variant_successes) / (control_total + variant_total)

        # Standard error
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / control_total + 1 / variant_total))

        if se == 0:
            return 1.0

        # Z-score
        z_score = (p2 - p1) / se

        # Two-tailed p-value approximation
        p_value = 2 * (1 - StatisticalAnalyzer._normal_cdf(abs(z_score)))

        return p_value

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximation of normal cumulative distribution function"""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


class ExperimentTracker:
    """Tracks experiment participation and results"""

    def __init__(self):
        self.cache = get_cache_service()

    async def record_participation(
        self, experiment_id: str, variant_id: str, user_id: str, lead_id: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Record user participation in an experiment"""
        participation = {
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "user_id": user_id,
            "lead_id": lead_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        # Store in cache for quick access
        cache_key = f"experiment_participation:{experiment_id}:{user_id}:{lead_id}"
        await self.cache.set(cache_key, participation, ttl=86400 * 7)  # 7 days

        # Also append to experiment log
        log_key = f"experiment_log:{experiment_id}:{variant_id}"
        existing_log = await self.cache.get(log_key) or []
        existing_log.append(participation)

        # Keep only recent entries (last 1000)
        if len(existing_log) > 1000:
            existing_log = existing_log[-1000:]

        await self.cache.set(log_key, existing_log, ttl=86400 * 30)  # 30 days

    async def record_conversion(
        self,
        experiment_id: str,
        variant_id: str,
        user_id: str,
        lead_id: str,
        conversion_type: str,
        conversion_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a conversion event"""
        conversion = {
            "experiment_id": experiment_id,
            "variant_id": variant_id,
            "user_id": user_id,
            "lead_id": lead_id,
            "conversion_type": conversion_type,
            "conversion_value": conversion_value,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        cache_key = f"experiment_conversion:{experiment_id}:{variant_id}"
        existing_conversions = await self.cache.get(cache_key) or []
        existing_conversions.append(conversion)

        # Keep only recent conversions
        if len(existing_conversions) > 1000:
            existing_conversions = existing_conversions[-1000:]

        await self.cache.set(cache_key, existing_conversions, ttl=86400 * 30)

    async def get_experiment_stats(self, experiment_id: str, variant_id: str) -> Dict[str, Any]:
        """Get current statistics for an experiment variant"""
        # Get participations
        log_key = f"experiment_log:{experiment_id}:{variant_id}"
        participations = await self.cache.get(log_key) or []

        # Get conversions
        conversion_key = f"experiment_conversion:{experiment_id}:{variant_id}"
        conversions = await self.cache.get(conversion_key) or []

        # Calculate stats
        total_participants = len(participations)
        total_conversions = len(conversions)
        conversion_rate = total_conversions / max(total_participants, 1)

        # Get recent performance (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_participations = [p for p in participations if datetime.fromisoformat(p["timestamp"]) > recent_cutoff]
        recent_conversions = [c for c in conversions if datetime.fromisoformat(c["timestamp"]) > recent_cutoff]

        return {
            "total_participants": total_participants,
            "total_conversions": total_conversions,
            "conversion_rate": conversion_rate,
            "recent_participants_24h": len(recent_participations),
            "recent_conversions_24h": len(recent_conversions),
            "last_updated": datetime.now().isoformat(),
        }


class ABTestingFramework:
    """Main A/B testing framework coordinator"""

    def __init__(self):
        self.cache = get_cache_service()
        self.tracker = ExperimentTracker()
        self.analyzer = StatisticalAnalyzer()
        self.active_experiments: Dict[str, Experiment] = {}

        logger.info("ABTestingFramework initialized")

    async def create_experiment(
        self,
        name: str,
        description: str,
        experiment_type: ExperimentType,
        variants: List[ExperimentVariant],
        metrics: List[ExperimentMetric],
        target_audience: Optional[Dict[str, Any]] = None,
        duration_days: int = 14,
    ) -> Experiment:
        """Create a new A/B test experiment"""

        # Validate variants sum to 100%
        total_traffic = sum(v.traffic_percentage for v in variants)
        if abs(total_traffic - 100.0) > 0.1:
            raise ValueError(f"Variant traffic percentages must sum to 100%, got {total_traffic}")

        # Ensure exactly one control variant
        control_variants = [v for v in variants if v.is_control]
        if len(control_variants) != 1:
            raise ValueError("Experiment must have exactly one control variant")

        experiment_id = f"exp_{int(datetime.now().timestamp())}_{hash(name) % 10000}"

        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            status=ExperimentStatus.DRAFT,
            variants=variants,
            metrics=metrics,
            target_audience=target_audience or {},
            end_date=datetime.now() + timedelta(days=duration_days),
        )

        # Store experiment
        await self._store_experiment(experiment)

        logger.info(f"Created experiment '{name}' with {len(variants)} variants")
        return experiment

    async def start_experiment(self, experiment_id: str) -> bool:
        """Start a running experiment"""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Can only start experiments in DRAFT status, got {experiment.status}")

        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.now()

        await self._store_experiment(experiment)
        self.active_experiments[experiment_id] = experiment

        logger.info(f"Started experiment {experiment_id}")
        return True

    async def stop_experiment(self, experiment_id: str, reason: str = "Manual stop") -> bool:
        """Stop a running experiment"""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            return False

        experiment.status = ExperimentStatus.COMPLETED

        await self._store_experiment(experiment)
        if experiment_id in self.active_experiments:
            del self.active_experiments[experiment_id]

        logger.info(f"Stopped experiment {experiment_id}: {reason}")
        return True

    async def assign_variant(
        self, experiment_id: str, user_id: str, lead_id: str, user_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[ExperimentVariant]:
        """Assign a user to an experiment variant"""

        experiment = await self.get_experiment(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None

        # Check if user matches target audience
        if not self._matches_target_audience(user_attributes or {}, experiment.target_audience):
            return None

        # Deterministic assignment based on user_id and experiment_id
        assignment_hash = hashlib.md5(f"{user_id}:{experiment_id}".encode()).hexdigest()
        hash_value = int(assignment_hash[:8], 16) % 10000

        # Assign based on traffic percentages
        cumulative_percentage = 0
        for variant in experiment.variants:
            cumulative_percentage += variant.traffic_percentage
            if hash_value < (cumulative_percentage * 100):  # Convert to 0-10000 scale
                # Record participation
                await self.tracker.record_participation(
                    experiment_id, variant.variant_id, user_id, lead_id, {"user_attributes": user_attributes}
                )
                return variant

        # Fallback to control variant
        control_variant = next((v for v in experiment.variants if v.is_control), None)
        if control_variant:
            await self.tracker.record_participation(
                experiment_id,
                control_variant.variant_id,
                user_id,
                lead_id,
                {"user_attributes": user_attributes, "fallback": True},
            )

        return control_variant

    async def record_conversion(
        self,
        experiment_id: str,
        user_id: str,
        lead_id: str,
        conversion_type: str = "lead_conversion",
        conversion_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a conversion for experiment tracking"""

        # Get user's variant assignment
        variant = await self._get_user_variant(experiment_id, user_id, lead_id)
        if not variant:
            return

        await self.tracker.record_conversion(
            experiment_id, variant.variant_id, user_id, lead_id, conversion_type, conversion_value, metadata
        )

    async def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Get comprehensive experiment results with statistical analysis"""

        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        results = {}
        variant_stats = {}

        # Get stats for each variant
        for variant in experiment.variants:
            stats = await self.tracker.get_experiment_stats(experiment_id, variant.variant_id)
            variant_stats[variant.variant_id] = stats

            # Calculate confidence intervals
            ci = self.analyzer.calculate_confidence_interval(stats["total_conversions"], stats["total_participants"])

            results[variant.variant_id] = ExperimentResult(
                variant_id=variant.variant_id,
                sample_size=stats["total_participants"],
                conversions=stats["total_conversions"],
                conversion_rate=stats["conversion_rate"],
                confidence_interval=ci,
                statistical_significance=None,
                metric_values={},
            )

        # Calculate statistical significance vs control
        control_variant = next((v for v in experiment.variants if v.is_control), None)
        if control_variant and control_variant.variant_id in results:
            control_result = results[control_variant.variant_id]

            for variant_id, result in results.items():
                if variant_id != control_variant.variant_id:
                    p_value = self.analyzer.calculate_statistical_significance(
                        control_result.conversions, control_result.sample_size, result.conversions, result.sample_size
                    )
                    result.statistical_significance = p_value

        # Overall experiment summary
        total_participants = sum(r.sample_size for r in results.values())
        total_conversions = sum(r.conversions for r in results.values())
        overall_conversion_rate = total_conversions / max(total_participants, 1)

        # Determine winner
        winner = self._determine_winner(results, control_variant.variant_id if control_variant else None)

        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.name,
            "status": experiment.status.value,
            "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
            "total_participants": total_participants,
            "total_conversions": total_conversions,
            "overall_conversion_rate": overall_conversion_rate,
            "variant_results": {
                variant_id: {
                    "variant_name": next(v.name for v in experiment.variants if v.variant_id == variant_id),
                    "sample_size": result.sample_size,
                    "conversions": result.conversions,
                    "conversion_rate": result.conversion_rate,
                    "confidence_interval": result.confidence_interval,
                    "statistical_significance": result.statistical_significance,
                    "is_control": any(v.variant_id == variant_id and v.is_control for v in experiment.variants),
                }
                for variant_id, result in results.items()
            },
            "winner": winner,
            "recommendation": self._generate_recommendation(results, experiment),
            "last_updated": datetime.now().isoformat(),
        }

    async def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        if experiment_id in self.active_experiments:
            return self.active_experiments[experiment_id]

        # Load from cache/storage
        cache_key = f"experiment:{experiment_id}"
        experiment_data = await self.cache.get(cache_key)

        if experiment_data:
            # Reconstruct experiment object
            experiment = Experiment(**experiment_data)
            if experiment.status == ExperimentStatus.RUNNING:
                self.active_experiments[experiment_id] = experiment
            return experiment

        return None

    async def list_experiments(
        self, status_filter: Optional[ExperimentStatus] = None, experiment_type_filter: Optional[ExperimentType] = None
    ) -> List[Dict[str, Any]]:
        """List all experiments with optional filtering"""

        # In a production system, this would query a database
        # For this implementation, we'll use cache keys
        all_experiments = []

        # This is a simplified implementation
        # In production, you'd want proper database queries
        for experiment_id, experiment in self.active_experiments.items():
            if status_filter and experiment.status != status_filter:
                continue
            if experiment_type_filter and experiment.experiment_type != experiment_type_filter:
                continue

            summary = {
                "experiment_id": experiment_id,
                "name": experiment.name,
                "status": experiment.status.value,
                "experiment_type": experiment.experiment_type.value,
                "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
                "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
                "variant_count": len(experiment.variants),
                "created_at": experiment.created_at.isoformat(),
            }
            all_experiments.append(summary)

        return sorted(all_experiments, key=lambda x: x["created_at"], reverse=True)

    # Private helper methods

    async def _store_experiment(self, experiment: Experiment):
        """Store experiment in cache/storage"""
        cache_key = f"experiment:{experiment.experiment_id}"

        # Convert to dict for storage
        experiment_data = {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "description": experiment.description,
            "experiment_type": experiment.experiment_type.value,
            "status": experiment.status.value,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "description": v.description,
                    "traffic_percentage": v.traffic_percentage,
                    "configuration": v.configuration,
                    "is_control": v.is_control,
                }
                for v in experiment.variants
            ],
            "metrics": [
                {
                    "metric_name": m.metric_name,
                    "metric_type": m.metric_type.value,
                    "target_improvement": m.target_improvement,
                    "statistical_power": m.statistical_power,
                    "significance_level": m.significance_level,
                    "minimum_sample_size": m.minimum_sample_size,
                }
                for m in experiment.metrics
            ],
            "target_audience": experiment.target_audience,
            "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
            "created_at": experiment.created_at.isoformat(),
            "created_by": experiment.created_by,
            "tags": experiment.tags,
        }

        await self.cache.set(cache_key, experiment_data, ttl=86400 * 90)  # 90 days

    def _matches_target_audience(self, user_attributes: Dict[str, Any], target_criteria: Dict[str, Any]) -> bool:
        """Check if user matches experiment target audience"""
        if not target_criteria:
            return True

        for criterion, expected_value in target_criteria.items():
            user_value = user_attributes.get(criterion)

            if isinstance(expected_value, list):
                if user_value not in expected_value:
                    return False
            elif isinstance(expected_value, dict):
                # Range criteria (e.g., {"min": 100, "max": 1000})
                if "min" in expected_value and user_value < expected_value["min"]:
                    return False
                if "max" in expected_value and user_value > expected_value["max"]:
                    return False
            else:
                if user_value != expected_value:
                    return False

        return True

    async def _get_user_variant(self, experiment_id: str, user_id: str, lead_id: str) -> Optional[ExperimentVariant]:
        """Get user's assigned variant from participation records"""
        cache_key = f"experiment_participation:{experiment_id}:{user_id}:{lead_id}"
        participation = await self.cache.get(cache_key)

        if participation:
            experiment = await self.get_experiment(experiment_id)
            if experiment:
                return next((v for v in experiment.variants if v.variant_id == participation["variant_id"]), None)

        return None

    def _determine_winner(
        self, results: Dict[str, ExperimentResult], control_variant_id: Optional[str]
    ) -> Optional[str]:
        """Determine experiment winner based on statistical significance"""

        if not control_variant_id or control_variant_id not in results:
            # No control variant, pick highest conversion rate with sufficient sample size
            best_variant = None
            best_rate = 0

            for variant_id, result in results.items():
                if result.sample_size >= 100 and result.conversion_rate > best_rate:
                    best_rate = result.conversion_rate
                    best_variant = variant_id

            return best_variant

        control_result = results[control_variant_id]

        # Look for statistically significant improvement over control
        for variant_id, result in results.items():
            if (
                variant_id != control_variant_id
                and result.statistical_significance
                and result.statistical_significance < 0.05  # 95% confidence
                and result.conversion_rate > control_result.conversion_rate
                and result.sample_size >= 100
            ):  # Minimum sample size
                return variant_id

        return None  # No clear winner yet

    def _generate_recommendation(self, results: Dict[str, ExperimentResult], experiment: Experiment) -> str:
        """Generate recommendation based on experiment results"""

        total_participants = sum(r.sample_size for r in results.values())

        if total_participants < 200:
            return "Continue experiment - insufficient sample size for reliable conclusions"

        control_variant = next((v for v in experiment.variants if v.is_control), None)
        if not control_variant:
            return "Unable to provide recommendation - no control variant found"

        control_result = results.get(control_variant.variant_id)
        if not control_result:
            return "Unable to provide recommendation - control variant has no data"

        # Find best performing variant
        best_variant_id = None
        best_improvement = 0
        significant_improvement = False

        for variant_id, result in results.items():
            if variant_id == control_variant.variant_id:
                continue

            improvement = (
                (result.conversion_rate - control_result.conversion_rate) / control_result.conversion_rate * 100
            )

            if (
                result.statistical_significance
                and result.statistical_significance < 0.05
                and improvement > best_improvement
            ):
                best_variant_id = variant_id
                best_improvement = improvement
                significant_improvement = True

        if significant_improvement and best_variant_id:
            variant_name = next(v.name for v in experiment.variants if v.variant_id == best_variant_id)
            return (
                f"Recommend implementing '{variant_name}' - "
                f"shows {best_improvement:.1f}% improvement with statistical significance"
            )
        elif best_improvement > 5:  # 5% improvement threshold
            variant_name = next(v.name for v in experiment.variants if v.variant_id == best_variant_id)
            return (
                f"Consider implementing '{variant_name}' - "
                f"shows {best_improvement:.1f}% improvement but needs more data for significance"
            )
        else:
            return "No significant improvement detected - consider keeping current implementation"


# Example experiment definitions
def create_model_comparison_experiment() -> Dict[str, Any]:
    """Create an experiment to compare different scoring models"""
    return {
        "name": "Predictive Model Comparison v2.1",
        "description": "Compare new behavioral signal weighting against current production model",
        "experiment_type": ExperimentType.MODEL_COMPARISON,
        "variants": [
            ExperimentVariant(
                variant_id="control_v2_0",
                name="Current Production Model",
                description="Current v2.0 model with standard signal weighting",
                traffic_percentage=50.0,
                configuration={"model_version": "v2.0", "signal_weights": "standard"},
                is_control=True,
            ),
            ExperimentVariant(
                variant_id="enhanced_v2_1",
                name="Enhanced Behavioral Model",
                description="New model with enhanced behavioral signal weighting",
                traffic_percentage=50.0,
                configuration={"model_version": "v2.1", "signal_weights": "enhanced"},
                is_control=False,
            ),
        ],
        "metrics": [
            ExperimentMetric(
                metric_name="lead_conversion_rate",
                metric_type=MetricType.CONVERSION_RATE,
                target_improvement=15.0,  # 15% improvement target
                minimum_sample_size=500,
            ),
            ExperimentMetric(
                metric_name="prediction_accuracy",
                metric_type=MetricType.ACCURACY,
                target_improvement=5.0,  # 5% accuracy improvement
                minimum_sample_size=1000,
            ),
        ],
        "target_audience": {
            "market_segment": ["tech_hub", "energy_sector"],
            "lead_score_range": {"min": 50, "max": 100},
        },
    }


# Example usage
if __name__ == "__main__":

    async def demo():
        framework = ABTestingFramework()

        # Create experiment
        experiment_config = create_model_comparison_experiment()

        experiment = await framework.create_experiment(**experiment_config)
        print(f"Created experiment: {experiment.name}")

        # Start experiment
        await framework.start_experiment(experiment.experiment_id)
        print(f"Started experiment: {experiment.experiment_id}")

        # Simulate user assignment
        variant = await framework.assign_variant(
            experiment.experiment_id, "user_123", "lead_456", {"market_segment": "tech_hub", "lead_score": 85}
        )

        if variant:
            print(f"Assigned to variant: {variant.name}")

            # Simulate conversion
            await framework.record_conversion(experiment.experiment_id, "user_123", "lead_456", "lead_conversion")
            print("Recorded conversion")

        # Get results
        results = await framework.get_experiment_results(experiment.experiment_id)
        print(f"Experiment results: {json.dumps(results, indent=2)}")

    asyncio.run(demo())
