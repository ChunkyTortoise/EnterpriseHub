"""
Predictive Compliance Scoring Engine

ML-powered predictive analytics for compliance scoring using simple statistical
methods (linear regression, exponential smoothing) - no heavy ML dependencies.

Provides:
- Future compliance score predictions with confidence intervals
- Risk level forecasting
- Violation probability calculations
- Preventive action recommendations
- Remediation impact estimation
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from ghl_real_estate_ai.compliance_platform.models.compliance_models import (
    ComplianceStatus,
    RegulationType,
    RiskLevel,
    ViolationSeverity,
)

logger = logging.getLogger(__name__)


class PredictionTimeframe(str, Enum):
    """Supported prediction timeframes"""

    ONE_WEEK = "1w"
    TWO_WEEKS = "2w"
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"

    @property
    def days(self) -> int:
        """Convert timeframe to days"""
        mapping = {
            "1w": 7,
            "2w": 14,
            "1m": 30,
            "3m": 90,
            "6m": 180,
        }
        return mapping[self.value]


class TrendDirection(str, Enum):
    """Compliance trend directions"""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    CRITICAL = "critical"


class CompliancePrediction(BaseModel):
    """Predicted compliance score with confidence intervals"""

    prediction_id: str = Field(default_factory=lambda: str(uuid4()))
    model_id: str
    current_score: float = Field(..., ge=0, le=100)
    predicted_score: float = Field(..., ge=0, le=100)
    prediction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeframe: PredictionTimeframe
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence 0-1")
    confidence_interval_lower: float = Field(default=0.0, ge=0, le=100)
    confidence_interval_upper: float = Field(default=100.0, ge=0, le=100)
    risk_factors: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    trend: TrendDirection = Field(default=TrendDirection.STABLE)
    trend_velocity: float = Field(default=0.0, description="Score change per week")

    # Feature contributions
    feature_impacts: Dict[str, float] = Field(default_factory=dict)

    @property
    def score_change(self) -> float:
        """Predicted score change from current"""
        return self.predicted_score - self.current_score

    @property
    def is_declining(self) -> bool:
        """Check if prediction indicates decline"""
        return self.trend in (TrendDirection.DECLINING, TrendDirection.CRITICAL)


class RiskForecast(BaseModel):
    """Forecasted risk level changes"""

    forecast_id: str = Field(default_factory=lambda: str(uuid4()))
    model_id: str
    current_risk_level: RiskLevel
    predicted_risk_level: RiskLevel
    probability: float = Field(..., ge=0, le=1)
    forecast_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeframe: PredictionTimeframe = Field(default=PredictionTimeframe.ONE_MONTH)

    # Contributing factors with weights
    contributing_factors: List[Dict[str, Any]] = Field(default_factory=list)

    # Mitigation impact estimates
    mitigation_impact: Dict[str, float] = Field(
        default_factory=dict, description="action -> estimated score improvement"
    )

    # Confidence metrics
    confidence: float = Field(default=0.7, ge=0, le=1)
    uncertainty_factors: List[str] = Field(default_factory=list)

    @property
    def is_risk_increasing(self) -> bool:
        """Check if risk is predicted to increase"""
        risk_order = [RiskLevel.MINIMAL, RiskLevel.LIMITED, RiskLevel.HIGH, RiskLevel.UNACCEPTABLE]
        try:
            current_idx = risk_order.index(self.current_risk_level)
            predicted_idx = risk_order.index(self.predicted_risk_level)
            return predicted_idx > current_idx
        except ValueError:
            return False


class ViolationProbability(BaseModel):
    """Probability of compliance violations"""

    model_id: str
    regulation: RegulationType
    probability: float = Field(..., ge=0, le=1)
    severity_distribution: Dict[str, float] = Field(default_factory=dict)
    contributing_factors: List[str] = Field(default_factory=list)
    time_to_violation_days: Optional[int] = None
    confidence: float = Field(default=0.7, ge=0, le=1)


class PreventiveAction(BaseModel):
    """Recommended preventive action"""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    priority: int = Field(..., ge=1, le=5, description="1 = highest priority")
    estimated_impact: float = Field(..., ge=0, description="Expected score improvement")
    effort_hours: float = Field(default=0.0)
    target_risk_factors: List[str] = Field(default_factory=list)
    deadline_days: int = Field(default=30)
    action_type: str = Field(default="technical")  # technical, procedural, documentation


class PredictiveComplianceEngine:
    """
    ML-powered predictive compliance scoring engine.

    Uses simple statistical methods (linear regression, exponential smoothing)
    to forecast compliance trends and risks without heavy ML dependencies.
    """

    def __init__(self, history_days: int = 90):
        """
        Initialize the predictive compliance engine.

        Args:
            history_days: Number of days of historical data to consider
        """
        self.history_days = history_days
        self._model_cache: Dict[str, Any] = {}

        # Feature weights for prediction model
        self._feature_weights: Dict[str, float] = {
            "score_trend": 0.25,
            "violation_frequency": 0.20,
            "remediation_velocity": 0.15,
            "assessment_regularity": 0.10,
            "risk_dimension_stability": 0.15,
            "regulatory_changes": 0.10,
            "industry_benchmark": 0.05,
        }

        # Risk level thresholds
        self._risk_thresholds = {
            RiskLevel.MINIMAL: 85,
            RiskLevel.LIMITED: 70,
            RiskLevel.HIGH: 50,
            RiskLevel.UNACCEPTABLE: 0,
        }

        # Severity weights for violation probability
        self._severity_weights = {
            ViolationSeverity.CRITICAL: 1.0,
            ViolationSeverity.HIGH: 0.8,
            ViolationSeverity.MEDIUM: 0.5,
            ViolationSeverity.LOW: 0.3,
            ViolationSeverity.INFORMATIONAL: 0.1,
        }

        logger.info(f"PredictiveComplianceEngine initialized with {history_days} days history")

    async def predict_compliance_score(
        self,
        model_id: str,
        timeframe: PredictionTimeframe,
        historical_scores: List[Dict[str, Any]],
    ) -> CompliancePrediction:
        """
        Predict future compliance score based on historical trends.

        Args:
            model_id: AI model identifier
            timeframe: Prediction timeframe
            historical_scores: List of historical score records with 'score' and 'timestamp'

        Returns:
            CompliancePrediction with forecasted score and confidence
        """
        if not historical_scores:
            raise ValueError("Historical scores required for prediction")

        # Extract and sort scores by timestamp
        sorted_scores = sorted(historical_scores, key=lambda x: x.get("timestamp", datetime.min))

        scores = [s.get("score", 0.0) for s in sorted_scores]
        timestamps = [s.get("timestamp", datetime.now(timezone.utc)) for s in sorted_scores]

        current_score = scores[-1] if scores else 0.0

        # Calculate trend features
        trend_features = self._extract_trend_features(scores)

        # Determine prediction approach based on data availability
        if len(scores) >= 5:
            # Use linear regression for prediction
            x_values = list(range(len(scores)))
            predicted_value, confidence = self._linear_regression_predict(
                x_values, scores, len(scores) + (timeframe.days // 7)
            )
        elif len(scores) >= 2:
            # Use exponential smoothing for limited data
            predicted_value = self._exponential_smoothing(scores, alpha=0.3)
            confidence = 0.5  # Lower confidence with less data
        else:
            # Single data point - no reliable prediction
            predicted_value = current_score
            confidence = 0.3

        # Clamp prediction to valid range
        predicted_score = max(0.0, min(100.0, predicted_value))

        # Calculate confidence interval
        std_dev = self._calculate_std_dev(scores) if len(scores) >= 2 else 10.0
        margin = std_dev * (1.96 / math.sqrt(max(1, len(scores))))  # 95% CI

        # Wider intervals for longer timeframes
        timeframe_multiplier = 1.0 + (timeframe.days / 180)
        margin *= timeframe_multiplier

        # Determine trend direction
        velocity = self._calculate_velocity(scores, timestamps)
        trend = self._determine_trend(velocity, predicted_score)

        # Identify risk factors
        risk_factors = self._identify_risk_factors(current_score, predicted_score, trend_features, trend)

        # Generate recommendations
        recommended_actions = self._generate_recommendations(risk_factors, trend, current_score, predicted_score)

        # Calculate feature impacts
        feature_impacts = self._calculate_feature_impacts(trend_features)

        return CompliancePrediction(
            model_id=model_id,
            current_score=current_score,
            predicted_score=predicted_score,
            timeframe=timeframe,
            confidence=confidence,
            confidence_interval_lower=max(0.0, predicted_score - margin),
            confidence_interval_upper=min(100.0, predicted_score + margin),
            risk_factors=risk_factors,
            recommended_actions=recommended_actions,
            trend=trend,
            trend_velocity=velocity,
            feature_impacts=feature_impacts,
        )

    async def forecast_risk_level(
        self,
        model_id: str,
        current_assessment: Dict[str, Any],
        historical_assessments: List[Dict[str, Any]],
    ) -> RiskForecast:
        """
        Forecast future risk level changes based on assessment history.

        Args:
            model_id: AI model identifier
            current_assessment: Current risk assessment data
            historical_assessments: List of historical assessments

        Returns:
            RiskForecast with predicted risk level and contributing factors
        """
        current_risk = RiskLevel(current_assessment.get("risk_level", RiskLevel.UNKNOWN.value))
        current_score = current_assessment.get("risk_score", 50.0)

        # Extract historical risk scores
        if historical_assessments:
            historical_scores = [a.get("risk_score", 50.0) for a in historical_assessments]

            # Calculate trend
            if len(historical_scores) >= 2:
                trend_slope = self._calculate_slope(historical_scores)
                predicted_score = current_score + (trend_slope * 4)  # 4 weeks ahead
            else:
                trend_slope = 0.0
                predicted_score = current_score
        else:
            trend_slope = 0.0
            predicted_score = current_score

        # Determine predicted risk level from score
        predicted_risk = self._score_to_risk_level(predicted_score)

        # Calculate probability of risk level change
        probability = self._calculate_risk_change_probability(current_score, predicted_score, trend_slope)

        # Identify contributing factors
        contributing_factors = self._identify_contributing_factors(current_assessment, historical_assessments)

        # Calculate mitigation impact
        mitigation_impact = await self._estimate_mitigation_impact(current_assessment, predicted_score)

        # Identify uncertainty factors
        uncertainty_factors = self._identify_uncertainty_factors(len(historical_assessments), current_assessment)

        # Adjust confidence based on data quality
        base_confidence = 0.7
        if len(historical_assessments) < 3:
            base_confidence *= 0.7
        if "regulatory_changes" in str(current_assessment):
            base_confidence *= 0.9

        return RiskForecast(
            model_id=model_id,
            current_risk_level=current_risk,
            predicted_risk_level=predicted_risk,
            probability=probability,
            contributing_factors=contributing_factors,
            mitigation_impact=mitigation_impact,
            confidence=min(0.95, base_confidence),
            uncertainty_factors=uncertainty_factors,
        )

    async def calculate_violation_probability(
        self,
        model_id: str,
        regulation: str,
        historical_violations: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Calculate probability of future violations by regulation.

        Args:
            model_id: AI model identifier
            regulation: Regulation type
            historical_violations: List of historical violations

        Returns:
            Dict with violation probabilities by severity
        """
        # Filter violations for this regulation
        reg_violations = [v for v in historical_violations if v.get("regulation") == regulation]

        # Calculate base probability from violation frequency
        if not reg_violations:
            # No historical violations - use base rate
            base_probability = 0.05
        else:
            # Calculate violations per month
            now = datetime.now(timezone.utc)
            recent_violations = [v for v in reg_violations if (now - v.get("detected_at", now)).days <= 90]
            violations_per_month = len(recent_violations) / 3.0

            # Convert to probability (saturating function)
            base_probability = 1 - math.exp(-violations_per_month * 0.5)

        # Calculate severity-weighted probability
        severity_distribution: Dict[str, float] = {}
        total_violations = len(reg_violations) if reg_violations else 1

        for severity in ViolationSeverity:
            count = len([v for v in reg_violations if v.get("severity") == severity.value])
            proportion = count / total_violations if reg_violations else 0.2
            severity_distribution[severity.value] = base_probability * proportion * self._severity_weights[severity]

        # Identify contributing factors
        contributing_factors = []
        if base_probability > 0.3:
            contributing_factors.append("High historical violation rate")
        if len(recent_violations) > 2:
            contributing_factors.append("Recent violation cluster detected")

        # Estimate time to next violation
        time_to_violation = None
        if reg_violations and base_probability > 0.1:
            avg_days_between = 90 / max(1, len(recent_violations))
            time_to_violation = int(avg_days_between * (1 - base_probability))

        return {
            "overall_probability": base_probability,
            "severity_distribution": severity_distribution,
            "contributing_factors": contributing_factors,
            "time_to_violation_days": time_to_violation,
            "confidence": 0.7 if len(reg_violations) >= 5 else 0.5,
            "regulation": regulation,
            "model_id": model_id,
        }

    async def recommend_preventive_actions(
        self,
        model_id: str,
        prediction: CompliancePrediction,
    ) -> List[Dict[str, Any]]:
        """
        Generate preventive action recommendations based on prediction.

        Args:
            model_id: AI model identifier
            prediction: Compliance prediction to generate actions for

        Returns:
            List of preventive actions with estimated impacts
        """
        actions: List[Dict[str, Any]] = []

        # Priority 1: Address critical declining trends
        if prediction.trend == TrendDirection.CRITICAL:
            actions.append(
                PreventiveAction(
                    title="Emergency Compliance Review",
                    description="Conduct immediate compliance assessment to identify critical gaps",
                    priority=1,
                    estimated_impact=15.0,
                    effort_hours=16.0,
                    target_risk_factors=["Rapid score decline", "Critical threshold breach"],
                    deadline_days=7,
                    action_type="technical",
                ).model_dump()
            )

        # Priority 2: Address specific risk factors
        for i, risk_factor in enumerate(prediction.risk_factors[:5]):
            action = self._create_action_for_risk_factor(risk_factor, i + 2)
            if action:
                actions.append(action.model_dump())

        # Priority 3: General recommendations based on predicted score
        if prediction.predicted_score < 70:
            actions.append(
                PreventiveAction(
                    title="Comprehensive Policy Review",
                    description="Review and update compliance policies to address identified gaps",
                    priority=3,
                    estimated_impact=10.0,
                    effort_hours=24.0,
                    target_risk_factors=["Policy gaps", "Outdated procedures"],
                    deadline_days=14,
                    action_type="procedural",
                ).model_dump()
            )

        if prediction.trend == TrendDirection.DECLINING:
            actions.append(
                PreventiveAction(
                    title="Compliance Training Program",
                    description="Implement targeted training to address declining compliance areas",
                    priority=3,
                    estimated_impact=8.0,
                    effort_hours=40.0,
                    target_risk_factors=["Knowledge gaps", "Process adherence"],
                    deadline_days=30,
                    action_type="documentation",
                ).model_dump()
            )

        # Sort by priority and estimated impact
        actions.sort(key=lambda x: (x["priority"], -x["estimated_impact"]))

        return actions

    async def calculate_remediation_impact(
        self,
        model_id: str,
        proposed_actions: List[str],
    ) -> Dict[str, float]:
        """
        Estimate score improvement from proposed remediations.

        Args:
            model_id: AI model identifier
            proposed_actions: List of proposed remediation actions

        Returns:
            Dict mapping actions to estimated score improvements
        """
        impact_estimates: Dict[str, float] = {}

        # Action type impact baselines
        action_impacts = {
            "training": 5.0,
            "policy": 8.0,
            "technical": 12.0,
            "documentation": 4.0,
            "audit": 10.0,
            "certification": 15.0,
            "monitoring": 6.0,
            "remediation": 10.0,
        }

        for action in proposed_actions:
            action_lower = action.lower()

            # Find matching action type
            base_impact = 5.0  # Default
            for action_type, impact in action_impacts.items():
                if action_type in action_lower:
                    base_impact = impact
                    break

            # Adjust based on specificity
            if "critical" in action_lower or "urgent" in action_lower:
                base_impact *= 1.3
            if "comprehensive" in action_lower or "full" in action_lower:
                base_impact *= 1.2

            # Add some variance for realism
            variance = base_impact * 0.1
            impact_estimates[action] = round(base_impact + (hash(action) % 10 - 5) * variance / 5, 1)

        # Calculate cumulative impact (diminishing returns)
        cumulative = 0.0
        sorted_impacts = sorted(impact_estimates.values(), reverse=True)
        for i, impact in enumerate(sorted_impacts):
            # Each subsequent action has diminishing returns
            diminishing_factor = 0.8**i
            cumulative += impact * diminishing_factor

        impact_estimates["_cumulative_impact"] = round(min(40.0, cumulative), 1)
        impact_estimates["_model_id"] = model_id  # type: ignore

        return impact_estimates

    # ==================== Feature Extraction Methods ====================

    def _extract_trend_features(self, scores: List[float]) -> Dict[str, float]:
        """
        Extract trend-based features from score history.

        Args:
            scores: List of historical scores

        Returns:
            Dict of extracted features
        """
        if not scores:
            return {
                "mean": 0.0,
                "std": 0.0,
                "trend_slope": 0.0,
                "volatility": 0.0,
                "recent_change": 0.0,
                "momentum": 0.0,
            }

        features: Dict[str, float] = {}

        # Basic statistics
        features["mean"] = sum(scores) / len(scores)
        features["std"] = self._calculate_std_dev(scores)

        # Trend slope (linear regression coefficient)
        if len(scores) >= 2:
            x = list(range(len(scores)))
            features["trend_slope"] = self._calculate_slope(scores)
        else:
            features["trend_slope"] = 0.0

        # Volatility (coefficient of variation)
        if features["mean"] > 0:
            features["volatility"] = features["std"] / features["mean"]
        else:
            features["volatility"] = 0.0

        # Recent change (last value vs mean of previous)
        if len(scores) >= 2:
            recent = scores[-1]
            previous_mean = sum(scores[:-1]) / len(scores[:-1])
            features["recent_change"] = recent - previous_mean
        else:
            features["recent_change"] = 0.0

        # Momentum (rate of change acceleration)
        if len(scores) >= 3:
            recent_changes = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
            if len(recent_changes) >= 2:
                features["momentum"] = recent_changes[-1] - recent_changes[-2]
            else:
                features["momentum"] = recent_changes[-1] if recent_changes else 0.0
        else:
            features["momentum"] = 0.0

        return features

    def _calculate_velocity(self, values: List[float], timestamps: List[datetime]) -> float:
        """
        Calculate rate of change (score change per week).

        Args:
            values: List of score values
            timestamps: Corresponding timestamps

        Returns:
            Score change per week
        """
        if len(values) < 2 or len(timestamps) < 2:
            return 0.0

        # Calculate time span in weeks
        time_span = (timestamps[-1] - timestamps[0]).days / 7.0
        if time_span <= 0:
            return 0.0

        # Calculate score change
        score_change = values[-1] - values[0]

        return score_change / time_span

    def _detect_seasonality(self, values: List[float]) -> Optional[int]:
        """
        Detect seasonal patterns in compliance data.

        Args:
            values: List of values to analyze

        Returns:
            Detected period in data points, or None if no seasonality
        """
        if len(values) < 8:
            return None

        # Simple autocorrelation-based detection
        mean = sum(values) / len(values)
        centered = [v - mean for v in values]

        best_period = None
        best_correlation = 0.3  # Minimum threshold

        for period in range(2, len(values) // 2):
            correlation = self._autocorrelation(centered, period)
            if correlation > best_correlation:
                best_correlation = correlation
                best_period = period

        return best_period

    def _autocorrelation(self, values: List[float], lag: int) -> float:
        """Calculate autocorrelation at given lag."""
        n = len(values)
        if lag >= n:
            return 0.0

        numerator = sum(values[i] * values[i + lag] for i in range(n - lag))
        denominator = sum(v * v for v in values)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    # ==================== Prediction Methods ====================

    def _linear_regression_predict(self, x: List[float], y: List[float], future_x: float) -> Tuple[float, float]:
        """
        Simple linear regression prediction with confidence.

        Args:
            x: Independent variable values
            y: Dependent variable values (scores)
            future_x: X value to predict for

        Returns:
            Tuple of (predicted_value, confidence)
        """
        n = len(x)
        if n < 2:
            return y[-1] if y else 0.0, 0.3

        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        # Calculate slope and intercept
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return y_mean, 0.5

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Predict future value
        prediction = slope * future_x + intercept

        # Calculate R-squared for confidence
        y_pred = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))

        if ss_tot == 0:
            r_squared = 1.0
        else:
            r_squared = max(0.0, 1 - (ss_res / ss_tot))

        # Confidence based on R-squared and data points
        confidence = r_squared * min(1.0, n / 10)

        return prediction, confidence

    def _exponential_smoothing(self, values: List[float], alpha: float = 0.3) -> float:
        """
        Exponential smoothing for trend prediction.

        Args:
            values: Historical values
            alpha: Smoothing factor (0-1)

        Returns:
            Smoothed prediction
        """
        if not values:
            return 0.0

        smoothed = values[0]
        for value in values[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed

        # Project one step ahead using trend
        if len(values) >= 2:
            trend = values[-1] - values[-2]
            return smoothed + alpha * trend

        return smoothed

    def _calculate_confidence(self, predictions: List[float], actuals: List[float]) -> float:
        """
        Calculate prediction confidence based on historical accuracy.

        Args:
            predictions: Historical predictions
            actuals: Actual values

        Returns:
            Confidence score (0-1)
        """
        if not predictions or not actuals or len(predictions) != len(actuals):
            return 0.5

        # Calculate MAPE (Mean Absolute Percentage Error)
        errors = []
        for pred, actual in zip(predictions, actuals):
            if actual != 0:
                errors.append(abs(pred - actual) / abs(actual))

        if not errors:
            return 0.5

        mape = sum(errors) / len(errors)

        # Convert MAPE to confidence (inverse relationship)
        confidence = max(0.0, min(1.0, 1 - mape))

        return confidence

    # ==================== Helper Methods ====================

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate linear trend slope."""
        if len(values) < 2:
            return 0.0

        x = list(range(len(values)))
        x_mean = sum(x) / len(x)
        y_mean = sum(values) / len(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(len(values)))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(len(values)))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _determine_trend(self, velocity: float, predicted_score: float) -> TrendDirection:
        """Determine trend direction from velocity and predicted score."""
        if predicted_score < 50:
            return TrendDirection.CRITICAL
        elif velocity < -2.0:
            return TrendDirection.DECLINING
        elif velocity > 2.0:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.STABLE

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert compliance score to risk level."""
        if score >= 85:
            return RiskLevel.MINIMAL
        elif score >= 70:
            return RiskLevel.LIMITED
        elif score >= 50:
            return RiskLevel.HIGH
        else:
            return RiskLevel.UNACCEPTABLE

    def _identify_risk_factors(
        self,
        current_score: float,
        predicted_score: float,
        trend_features: Dict[str, float],
        trend: TrendDirection,
    ) -> List[str]:
        """Identify risk factors based on analysis."""
        risk_factors: List[str] = []

        if predicted_score < current_score:
            risk_factors.append(f"Predicted score decline of {current_score - predicted_score:.1f} points")

        if trend_features.get("volatility", 0) > 0.15:
            risk_factors.append("High score volatility indicates instability")

        if trend_features.get("trend_slope", 0) < -1.0:
            risk_factors.append("Consistent downward trend in recent assessments")

        if trend_features.get("momentum", 0) < -2.0:
            risk_factors.append("Accelerating decline in compliance scores")

        if predicted_score < 70:
            risk_factors.append("Below acceptable compliance threshold")

        if trend == TrendDirection.CRITICAL:
            risk_factors.append("Critical risk level - immediate attention required")

        return risk_factors

    def _generate_recommendations(
        self,
        risk_factors: List[str],
        trend: TrendDirection,
        current_score: float,
        predicted_score: float,
    ) -> List[str]:
        """Generate action recommendations."""
        recommendations: List[str] = []

        if trend == TrendDirection.CRITICAL:
            recommendations.append("Schedule emergency compliance review")
            recommendations.append("Engage compliance officer for immediate assessment")

        if trend == TrendDirection.DECLINING:
            recommendations.append("Increase monitoring frequency")
            recommendations.append("Review recent policy changes for impact")

        if predicted_score < current_score:
            recommendations.append("Implement preventive controls for identified gaps")

        if any("volatility" in rf.lower() for rf in risk_factors):
            recommendations.append("Standardize compliance processes to reduce variability")

        if predicted_score < 70:
            recommendations.append("Prioritize high-impact remediation actions")
            recommendations.append("Consider external compliance audit")

        return recommendations[:5]  # Limit to top 5

    def _calculate_feature_impacts(self, trend_features: Dict[str, float]) -> Dict[str, float]:
        """Calculate feature contribution to prediction."""
        impacts: Dict[str, float] = {}

        for feature, value in trend_features.items():
            weight = self._feature_weights.get(feature, 0.1)
            impacts[feature] = round(value * weight, 3)

        return impacts

    def _identify_contributing_factors(
        self,
        current_assessment: Dict[str, Any],
        historical_assessments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify factors contributing to risk forecast."""
        factors: List[Dict[str, Any]] = []

        # Check dimension scores
        dimensions = [
            "transparency_score",
            "fairness_score",
            "accountability_score",
            "robustness_score",
            "privacy_score",
            "security_score",
        ]

        for dim in dimensions:
            current_val = current_assessment.get(dim, 0)
            if current_val < 70:
                factors.append(
                    {
                        "factor": dim.replace("_score", "").title(),
                        "current_value": current_val,
                        "threshold": 70,
                        "impact": "high" if current_val < 50 else "medium",
                        "weight": 0.15,
                    }
                )

        # Check for recent violations
        if current_assessment.get("recent_violations", 0) > 0:
            factors.append(
                {
                    "factor": "Recent Violations",
                    "current_value": current_assessment.get("recent_violations"),
                    "impact": "high",
                    "weight": 0.20,
                }
            )

        return factors

    async def _estimate_mitigation_impact(
        self,
        current_assessment: Dict[str, Any],
        predicted_score: float,
    ) -> Dict[str, float]:
        """Estimate impact of mitigation actions."""
        impacts: Dict[str, float] = {}

        # Common mitigation actions and their estimated impacts
        if predicted_score < 70:
            impacts["Comprehensive compliance audit"] = 15.0
            impacts["Staff training program"] = 8.0
            impacts["Process automation"] = 12.0

        if predicted_score < 50:
            impacts["External compliance consultant"] = 20.0
            impacts["Emergency remediation plan"] = 18.0

        # Dimension-specific improvements
        dimensions = ["transparency", "fairness", "accountability", "robustness", "privacy", "security"]
        for dim in dimensions:
            score = current_assessment.get(f"{dim}_score", 100)
            if score < 70:
                impacts[f"Improve {dim} controls"] = min(15.0, (70 - score) * 0.3)

        return impacts

    def _identify_uncertainty_factors(
        self,
        data_points: int,
        current_assessment: Dict[str, Any],
    ) -> List[str]:
        """Identify factors that increase prediction uncertainty."""
        factors: List[str] = []

        if data_points < 5:
            factors.append("Limited historical data available")

        if current_assessment.get("pending_regulatory_changes", False):
            factors.append("Pending regulatory changes may affect compliance")

        if current_assessment.get("recent_system_changes", False):
            factors.append("Recent system changes not yet fully assessed")

        return factors

    def _create_action_for_risk_factor(self, risk_factor: str, priority: int) -> Optional[PreventiveAction]:
        """Create preventive action for a specific risk factor."""
        risk_lower = risk_factor.lower()

        if "decline" in risk_lower or "downward" in risk_lower:
            return PreventiveAction(
                title="Reverse Compliance Decline",
                description=f"Address identified trend: {risk_factor}",
                priority=min(5, priority),
                estimated_impact=8.0,
                effort_hours=16.0,
                target_risk_factors=[risk_factor],
                deadline_days=14,
                action_type="technical",
            )

        if "volatility" in risk_lower or "instability" in risk_lower:
            return PreventiveAction(
                title="Stabilize Compliance Processes",
                description="Implement standardized procedures to reduce variability",
                priority=min(5, priority),
                estimated_impact=6.0,
                effort_hours=24.0,
                target_risk_factors=[risk_factor],
                deadline_days=21,
                action_type="procedural",
            )

        if "threshold" in risk_lower or "below" in risk_lower:
            return PreventiveAction(
                title="Threshold Recovery Plan",
                description="Execute targeted improvements to restore compliance level",
                priority=min(5, priority),
                estimated_impact=12.0,
                effort_hours=32.0,
                target_risk_factors=[risk_factor],
                deadline_days=14,
                action_type="technical",
            )

        if "critical" in risk_lower:
            return PreventiveAction(
                title="Critical Risk Mitigation",
                description="Immediate action required to address critical compliance risk",
                priority=1,
                estimated_impact=15.0,
                effort_hours=40.0,
                target_risk_factors=[risk_factor],
                deadline_days=7,
                action_type="technical",
            )

        return None

    def _calculate_risk_change_probability(
        self,
        current_score: float,
        predicted_score: float,
        trend_slope: float,
    ) -> float:
        """Calculate probability of risk level change."""
        # Base probability on score difference
        score_diff = abs(predicted_score - current_score)

        # Higher probability if crossing a threshold
        thresholds = [85, 70, 50]
        crossing_threshold = any(
            (current_score > t >= predicted_score) or (current_score < t <= predicted_score) for t in thresholds
        )

        base_prob = min(0.95, score_diff / 20)  # 20 point change = ~100% probability

        if crossing_threshold:
            base_prob = min(0.95, base_prob * 1.5)

        # Adjust for trend consistency
        if abs(trend_slope) > 2:
            base_prob = min(0.95, base_prob * 1.2)

        return round(base_prob, 2)
