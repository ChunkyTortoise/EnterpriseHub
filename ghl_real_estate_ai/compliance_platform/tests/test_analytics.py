"""
Comprehensive Test Suite for Compliance Analytics - Predictive Scoring & Anomaly Detection

Tests cover:
- Predictive Scoring: score prediction, risk forecasting, violation probability, recommendations
- Statistical Methods: linear regression, exponential smoothing
- Anomaly Detection: score anomalies, violation surges, assessment gaps, risk escalation
- Statistical Analysis: z-score calculation, IQR bounds, severity classification

Following TDD principles: RED -> GREEN -> REFACTOR
"""

import math
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

import pytest

from ghl_real_estate_ai.compliance_platform.models.compliance_models import (
    AIModelRegistration,
    ComplianceStatus,
    RegulationType,
    RiskLevel,
)
from ghl_real_estate_ai.compliance_platform.models.risk_models import (
    RiskCategory,
    RiskIndicator,
)

# ============================================================================
# FIXTURES - Sample data for analytics tests
# ============================================================================


@pytest.fixture
def sample_compliance_history() -> List[Dict[str, Any]]:
    """Sample compliance score history over time"""
    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    return [
        {
            "timestamp": base_time + timedelta(days=i),
            "score": 75 + (i * 0.5) + ((-1) ** i * 2),  # Upward trend with noise
            "status": "compliant" if 75 + (i * 0.5) > 80 else "partially_compliant",
        }
        for i in range(30)
    ]


@pytest.fixture
def sample_violation_history() -> List[Dict[str, Any]]:
    """Sample violation history over time"""
    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    violations = []

    # Normal pattern: 1-2 violations per week
    for week in range(4):
        for _ in range(2):
            violations.append(
                {
                    "timestamp": base_time + timedelta(days=week * 7 + (week % 3)),
                    "severity": "medium",
                    "regulation": "gdpr",
                }
            )

    # Surge in last 3 days: 5 violations
    for i in range(5):
        violations.append(
            {
                "timestamp": base_time + timedelta(days=28 + i % 3),
                "severity": "high" if i % 2 == 0 else "medium",
                "regulation": "eu_ai_act",
            }
        )

    return violations


@pytest.fixture
def sample_risk_indicators() -> List[RiskIndicator]:
    """Sample risk indicators for trend analysis"""
    return [
        RiskIndicator(
            category=RiskCategory.ALGORITHMIC_BIAS,
            name="Bias Detection Score",
            description="Measure of algorithmic bias in model outputs",
            value=35.0,
            threshold_warning=40.0,
            threshold_critical=60.0,
            trend="improving",
            trend_percentage=-5.2,
        ),
        RiskIndicator(
            category=RiskCategory.DATA_PROTECTION,
            name="Data Protection Score",
            description="GDPR compliance indicator",
            value=72.0,
            threshold_warning=60.0,
            threshold_critical=80.0,
            trend="stable",
            trend_percentage=0.5,
        ),
        RiskIndicator(
            category=RiskCategory.TRANSPARENCY,
            name="Model Transparency Score",
            description="Explainability and documentation completeness",
            value=58.0,
            threshold_warning=50.0,
            threshold_critical=70.0,
            trend="declining",
            trend_percentage=8.3,
        ),
    ]


@pytest.fixture
def sample_ai_model() -> AIModelRegistration:
    """Sample AI model for analytics"""
    return AIModelRegistration(
        model_id="model_analytics_001",
        name="Analytics Test Model",
        version="1.0.0",
        description="Model for analytics testing",
        model_type="classification",
        provider="internal",
        deployment_location="cloud",
        data_residency=["us"],
        intended_use="Lead scoring",
        use_case_category="crm_automation",
        risk_level=RiskLevel.HIGH,
        personal_data_processed=True,
        compliance_status=ComplianceStatus.PARTIALLY_COMPLIANT,
        applicable_regulations=[RegulationType.EU_AI_ACT, RegulationType.GDPR],
        registered_by="analytics_team",
    )


@pytest.fixture
def sample_assessment_dates() -> List[datetime]:
    """Sample assessment dates showing gaps"""
    base_time = datetime.now(timezone.utc) - timedelta(days=60)
    dates = [
        base_time,
        base_time + timedelta(days=7),
        base_time + timedelta(days=14),
        base_time + timedelta(days=21),
        # Gap: no assessment from day 21 to day 45
        base_time + timedelta(days=45),
        base_time + timedelta(days=52),
    ]
    return dates


# ============================================================================
# MOCK ANALYTICS SERVICE
# ============================================================================


class MockPredictiveScorer:
    """Mock implementation of predictive scoring analytics"""

    def __init__(self):
        self._model_cache = {}
        self._prediction_cache = {}

    async def predict_compliance_score(
        self,
        model_id: str,
        history: List[Dict[str, Any]],
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """Predict future compliance score using historical data"""
        if len(history) < 5:
            raise ValueError("Insufficient historical data (minimum 5 data points)")

        scores = [h["score"] for h in history]
        current_score = scores[-1]

        # Simple linear extrapolation
        trend = self._calculate_trend(scores)
        predicted_score = min(100, max(0, current_score + (trend * horizon_days)))

        # Confidence based on data stability
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
        confidence = max(0.5, 1 - (std_dev / 50))

        return {
            "model_id": model_id,
            "current_score": current_score,
            "predicted_score": round(predicted_score, 2),
            "prediction_horizon_days": horizon_days,
            "confidence": round(confidence, 3),
            "trend_direction": "improving" if trend > 0 else "declining" if trend < 0 else "stable",
            "trend_magnitude": abs(round(trend, 4)),
        }

    async def forecast_risk_level(
        self,
        model_id: str,
        indicators: List[RiskIndicator],
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """Forecast risk level based on current indicators"""
        # Calculate weighted risk score
        weights = {
            RiskCategory.ALGORITHMIC_BIAS: 1.5,
            RiskCategory.DATA_PROTECTION: 1.3,
            RiskCategory.TRANSPARENCY: 1.0,
            RiskCategory.REGULATORY_VIOLATION: 2.0,
            RiskCategory.SECURITY_VULNERABILITY: 1.8,
        }

        total_weight = 0
        weighted_score = 0

        for indicator in indicators:
            weight = weights.get(indicator.category, 1.0)
            weighted_score += indicator.value * weight
            total_weight += weight

        current_risk_score = weighted_score / total_weight if total_weight > 0 else 0

        # Apply trend adjustments
        trend_adjustments = sum(i.trend_percentage for i in indicators if i.trend == "declining")
        projected_score = min(100, current_risk_score + trend_adjustments)

        # Determine risk level
        risk_level = self._score_to_risk_level(projected_score)

        return {
            "model_id": model_id,
            "current_risk_score": round(current_risk_score, 2),
            "projected_risk_score": round(projected_score, 2),
            "horizon_days": horizon_days,
            "current_risk_level": self._score_to_risk_level(current_risk_score),
            "projected_risk_level": risk_level,
            "risk_factors": [i.name for i in indicators if i.value >= i.threshold_warning],
            "improving_factors": [i.name for i in indicators if i.trend == "improving"],
        }

    async def calculate_violation_probability(
        self,
        model_id: str,
        violation_history: List[Dict[str, Any]],
        risk_score: float,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """Calculate probability of compliance violation"""
        # Base probability from historical frequency
        if violation_history:
            violations_per_day = len(violation_history) / 30  # Assuming 30-day history
            base_probability = 1 - math.exp(-violations_per_day * horizon_days)
        else:
            base_probability = 0.1  # Low base probability if no history

        # Adjust for current risk score
        risk_adjustment = risk_score / 100
        adjusted_probability = min(0.95, base_probability + (risk_adjustment * 0.3))

        # Severity distribution based on history
        severity_dist = self._calculate_severity_distribution(violation_history)

        return {
            "model_id": model_id,
            "violation_probability": round(adjusted_probability, 3),
            "horizon_days": horizon_days,
            "expected_violations": round(violations_per_day * horizon_days, 1) if violation_history else 0,
            "severity_distribution": severity_dist,
            "risk_factors": [
                "High historical violation rate" if violations_per_day > 0.2 else None,
                "Elevated risk score" if risk_score > 60 else None,
            ],
            "confidence": 0.75 if len(violation_history) >= 10 else 0.5,
        }

    async def recommend_preventive_actions(
        self,
        model_id: str,
        predictions: Dict[str, Any],
        indicators: List[RiskIndicator],
    ) -> List[Dict[str, Any]]:
        """Recommend actions to prevent predicted issues"""
        recommendations = []

        # Based on declining indicators
        for indicator in indicators:
            if indicator.trend == "declining":
                recommendations.append(
                    {
                        "category": indicator.category.value,
                        "action": f"Address declining {indicator.name}",
                        "priority": "high" if indicator.value >= indicator.threshold_critical else "medium",
                        "expected_impact": f"Reduce {indicator.category.value} risk by {indicator.trend_percentage:.1f}%",
                        "estimated_effort": "2-4 weeks",
                    }
                )

        # Based on violation probability
        if predictions.get("violation_probability", 0) > 0.5:
            recommendations.append(
                {
                    "category": "compliance",
                    "action": "Conduct immediate compliance review",
                    "priority": "critical" if predictions["violation_probability"] > 0.7 else "high",
                    "expected_impact": "Reduce violation probability by 30-50%",
                    "estimated_effort": "1-2 weeks",
                }
            )

        # Based on risk score trend
        if predictions.get("trend_direction") == "declining":
            recommendations.append(
                {
                    "category": "risk_management",
                    "action": "Implement enhanced monitoring",
                    "priority": "high",
                    "expected_impact": "Early detection of compliance drift",
                    "estimated_effort": "1 week",
                }
            )

        return sorted(
            recommendations, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["priority"], 4)
        )

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend using simple linear regression"""
        n = len(values)
        if n < 2:
            return 0.0

        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    def _score_to_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level"""
        if score >= 80:
            return "high"
        elif score >= 60:
            return "limited"
        elif score >= 40:
            return "limited"
        return "minimal"

    def _calculate_severity_distribution(self, violations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate severity distribution from violation history"""
        if not violations:
            return {"critical": 0.05, "high": 0.15, "medium": 0.5, "low": 0.3}

        total = len(violations)
        distribution = {}

        for severity in ["critical", "high", "medium", "low"]:
            count = len([v for v in violations if v.get("severity") == severity])
            distribution[severity] = count / total

        return distribution


class MockAnomalyDetector:
    """Mock implementation of anomaly detection analytics"""

    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Z-score threshold
        self._baseline_cache = {}

    async def detect_score_anomaly(
        self,
        model_id: str,
        current_score: float,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Detect if current score is anomalous"""
        scores = [h["score"] for h in history]

        if len(scores) < 5:
            return {
                "is_anomaly": False,
                "reason": "Insufficient data for anomaly detection",
                "confidence": 0.0,
            }

        mean = statistics.mean(scores)
        std_dev = statistics.stdev(scores)

        z_score = (current_score - mean) / std_dev if std_dev > 0 else 0

        is_anomaly = abs(z_score) > self.sensitivity

        return {
            "model_id": model_id,
            "current_score": current_score,
            "is_anomaly": is_anomaly,
            "z_score": round(z_score, 3),
            "mean": round(mean, 2),
            "std_dev": round(std_dev, 2),
            "severity": self._classify_anomaly_severity(abs(z_score)),
            "direction": "improvement" if z_score > 0 else "decline" if z_score < 0 else "neutral",
            "confidence": min(0.95, 0.5 + (len(scores) / 100)),
        }

    async def detect_violation_surge(
        self,
        model_id: str,
        violations: List[Dict[str, Any]],
        window_days: int = 7,
    ) -> Dict[str, Any]:
        """Detect sudden surge in violations"""
        now = datetime.now(timezone.utc)
        recent_window = now - timedelta(days=window_days)
        historical_window = recent_window - timedelta(days=window_days * 3)

        recent_violations = [v for v in violations if v["timestamp"] >= recent_window]
        historical_violations = [v for v in violations if historical_window <= v["timestamp"] < recent_window]

        recent_rate = len(recent_violations) / window_days
        historical_rate = len(historical_violations) / (window_days * 3) if historical_violations else 0.1

        # Detect surge using ratio
        surge_ratio = recent_rate / historical_rate if historical_rate > 0 else recent_rate

        is_surge = surge_ratio > 2.0  # More than 2x increase

        return {
            "model_id": model_id,
            "is_surge": is_surge,
            "recent_count": len(recent_violations),
            "historical_avg": round(historical_rate * window_days, 1),
            "surge_ratio": round(surge_ratio, 2),
            "severity": self._classify_surge_severity(surge_ratio),
            "window_days": window_days,
            "recent_severities": self._aggregate_severities(recent_violations),
            "alert_recommended": is_surge and surge_ratio > 3.0,
        }

    async def detect_assessment_gap(
        self,
        model_id: str,
        assessment_dates: List[datetime],
        expected_frequency_days: int = 14,
    ) -> Dict[str, Any]:
        """Detect gaps in compliance assessments"""
        if len(assessment_dates) < 2:
            return {
                "is_gap": True,
                "reason": "Insufficient assessment history",
                "gap_days": None,
            }

        sorted_dates = sorted(assessment_dates)
        gaps = []

        for i in range(1, len(sorted_dates)):
            gap = (sorted_dates[i] - sorted_dates[i - 1]).days
            if gap > expected_frequency_days:
                gaps.append(
                    {
                        "start": sorted_dates[i - 1].isoformat(),
                        "end": sorted_dates[i].isoformat(),
                        "gap_days": gap,
                    }
                )

        # Check current gap
        days_since_last = (datetime.now(timezone.utc) - sorted_dates[-1]).days
        current_gap = days_since_last > expected_frequency_days

        return {
            "model_id": model_id,
            "is_gap": bool(gaps) or current_gap,
            "historical_gaps": gaps,
            "current_gap_days": days_since_last,
            "expected_frequency_days": expected_frequency_days,
            "is_overdue": current_gap,
            "overdue_by_days": max(0, days_since_last - expected_frequency_days),
            "severity": self._classify_gap_severity(days_since_last, expected_frequency_days),
            "recommendation": "Schedule immediate assessment" if current_gap else "Maintain current schedule",
        }

    async def detect_risk_escalation(
        self,
        model_id: str,
        risk_history: List[Dict[str, Any]],
        window_days: int = 7,
    ) -> Dict[str, Any]:
        """Detect rapid risk escalation"""
        if len(risk_history) < 3:
            return {
                "is_escalation": False,
                "reason": "Insufficient risk history",
            }

        now = datetime.now(timezone.utc)
        recent = [r for r in risk_history if r["timestamp"] >= now - timedelta(days=window_days)]
        older = [r for r in risk_history if r["timestamp"] < now - timedelta(days=window_days)]

        if not recent or not older:
            return {
                "is_escalation": False,
                "reason": "Insufficient data in time windows",
            }

        recent_avg = statistics.mean([r["risk_score"] for r in recent])
        older_avg = statistics.mean([r["risk_score"] for r in older])

        escalation = recent_avg - older_avg
        escalation_pct = (escalation / older_avg * 100) if older_avg > 0 else 0

        is_escalation = escalation_pct > 20  # More than 20% increase

        return {
            "model_id": model_id,
            "is_escalation": is_escalation,
            "recent_avg_risk": round(recent_avg, 2),
            "historical_avg_risk": round(older_avg, 2),
            "escalation_points": round(escalation, 2),
            "escalation_percentage": round(escalation_pct, 1),
            "severity": self._classify_escalation_severity(escalation_pct),
            "window_days": window_days,
            "alert_recommended": is_escalation and escalation_pct > 30,
        }

    def calculate_z_score(self, value: float, mean: float, std_dev: float) -> float:
        """Calculate z-score for a value"""
        if std_dev == 0:
            return 0.0
        return (value - mean) / std_dev

    def calculate_iqr_bounds(self, values: List[float]) -> Tuple[float, float, float, float]:
        """Calculate IQR-based anomaly bounds"""
        if len(values) < 4:
            raise ValueError("Need at least 4 values for IQR calculation")

        sorted_values = sorted(values)
        n = len(sorted_values)

        q1_idx = n // 4
        q3_idx = (3 * n) // 4

        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        return q1, q3, lower_bound, upper_bound

    def _classify_anomaly_severity(self, z_score: float) -> str:
        """Classify anomaly severity based on z-score magnitude"""
        if z_score > 3.0:
            return "critical"
        elif z_score > 2.5:
            return "high"
        elif z_score > 2.0:
            return "medium"
        return "low"

    def _classify_surge_severity(self, ratio: float) -> str:
        """Classify surge severity based on ratio"""
        if ratio > 5.0:
            return "critical"
        elif ratio > 3.0:
            return "high"
        elif ratio > 2.0:
            return "medium"
        return "low"

    def _classify_gap_severity(self, gap_days: int, expected: int) -> str:
        """Classify assessment gap severity"""
        ratio = gap_days / expected
        if ratio > 3.0:
            return "critical"
        elif ratio > 2.0:
            return "high"
        elif ratio > 1.0:
            return "medium"
        return "low"

    def _classify_escalation_severity(self, escalation_pct: float) -> str:
        """Classify risk escalation severity"""
        if escalation_pct > 50:
            return "critical"
        elif escalation_pct > 30:
            return "high"
        elif escalation_pct > 20:
            return "medium"
        return "low"

    def _aggregate_severities(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Aggregate violation counts by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in violations:
            severity = v.get("severity", "medium")
            if severity in counts:
                counts[severity] += 1
        return counts


# ============================================================================
# TEST CLASS: Predictive Scoring
# ============================================================================


class TestPredictiveScoring:
    """Test suite for predictive compliance scoring"""

    @pytest.fixture
    def predictor(self) -> MockPredictiveScorer:
        """Create predictive scorer instance"""
        return MockPredictiveScorer()

    @pytest.mark.asyncio
    async def test_predict_compliance_score(
        self,
        predictor: MockPredictiveScorer,
        sample_compliance_history: List[Dict[str, Any]],
    ):
        """Test compliance score prediction"""
        # Act
        result = await predictor.predict_compliance_score(
            model_id="model_001",
            history=sample_compliance_history,
            horizon_days=30,
        )

        # Assert
        assert "predicted_score" in result
        assert 0 <= result["predicted_score"] <= 100
        assert result["trend_direction"] in ["improving", "declining", "stable"]
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_predict_compliance_score_insufficient_data(
        self,
        predictor: MockPredictiveScorer,
    ):
        """Test prediction with insufficient historical data"""
        # Arrange
        short_history = [{"timestamp": datetime.now(timezone.utc), "score": 80}]

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await predictor.predict_compliance_score(
                model_id="model_001",
                history=short_history,
                horizon_days=30,
            )

        assert "Insufficient" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_forecast_risk_level(
        self,
        predictor: MockPredictiveScorer,
        sample_risk_indicators: List[RiskIndicator],
    ):
        """Test risk level forecasting"""
        # Act
        result = await predictor.forecast_risk_level(
            model_id="model_001",
            indicators=sample_risk_indicators,
            horizon_days=30,
        )

        # Assert
        assert "current_risk_level" in result
        assert "projected_risk_level" in result
        assert result["current_risk_level"] in ["minimal", "limited", "high", "unacceptable"]
        assert "risk_factors" in result
        assert isinstance(result["risk_factors"], list)

    @pytest.mark.asyncio
    async def test_calculate_violation_probability(
        self,
        predictor: MockPredictiveScorer,
        sample_violation_history: List[Dict[str, Any]],
    ):
        """Test violation probability calculation"""
        # Act
        result = await predictor.calculate_violation_probability(
            model_id="model_001",
            violation_history=sample_violation_history,
            risk_score=65.0,
            horizon_days=30,
        )

        # Assert
        assert "violation_probability" in result
        assert 0 <= result["violation_probability"] <= 1
        assert "expected_violations" in result
        assert "severity_distribution" in result
        assert sum(result["severity_distribution"].values()) == pytest.approx(1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_calculate_violation_probability_no_history(
        self,
        predictor: MockPredictiveScorer,
    ):
        """Test violation probability with no history"""
        # Act
        result = await predictor.calculate_violation_probability(
            model_id="model_001",
            violation_history=[],
            risk_score=30.0,
            horizon_days=30,
        )

        # Assert
        assert result["expected_violations"] == 0
        assert result["violation_probability"] < 0.5  # Should be low without history

    @pytest.mark.asyncio
    async def test_recommend_preventive_actions(
        self,
        predictor: MockPredictiveScorer,
        sample_risk_indicators: List[RiskIndicator],
    ):
        """Test preventive action recommendations"""
        # Arrange
        predictions = {
            "violation_probability": 0.65,
            "trend_direction": "declining",
        }

        # Act
        result = await predictor.recommend_preventive_actions(
            model_id="model_001",
            predictions=predictions,
            indicators=sample_risk_indicators,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("priority" in r for r in result)
        assert all("action" in r for r in result)
        # Should be sorted by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        priorities = [priority_order.get(r["priority"], 4) for r in result]
        assert priorities == sorted(priorities)

    def test_linear_regression_predict(
        self,
        predictor: MockPredictiveScorer,
    ):
        """Test linear regression trend calculation"""
        # Arrange - clear upward trend
        values = [10.0, 12.0, 14.0, 16.0, 18.0]

        # Act
        trend = predictor._calculate_trend(values)

        # Assert
        assert trend > 0  # Positive trend
        assert trend == pytest.approx(2.0, abs=0.1)  # ~2 units per period

    def test_linear_regression_predict_downward(
        self,
        predictor: MockPredictiveScorer,
    ):
        """Test linear regression with downward trend"""
        # Arrange - clear downward trend
        values = [100.0, 95.0, 90.0, 85.0, 80.0]

        # Act
        trend = predictor._calculate_trend(values)

        # Assert
        assert trend < 0  # Negative trend
        assert trend == pytest.approx(-5.0, abs=0.1)

    def test_exponential_smoothing(
        self,
        predictor: MockPredictiveScorer,
    ):
        """Test exponential smoothing (via trend calculation with noisy data)"""
        # Arrange - trend with noise
        values = [50.0, 52.0, 48.0, 54.0, 51.0, 55.0, 53.0, 57.0]

        # Act
        trend = predictor._calculate_trend(values)

        # Assert - should detect overall upward trend despite noise
        assert trend > 0


# ============================================================================
# TEST CLASS: Anomaly Detection
# ============================================================================


class TestAnomalyDetection:
    """Test suite for anomaly detection"""

    @pytest.fixture
    def detector(self) -> MockAnomalyDetector:
        """Create anomaly detector instance"""
        return MockAnomalyDetector(sensitivity=2.0)

    @pytest.mark.asyncio
    async def test_detect_score_anomaly(
        self,
        detector: MockAnomalyDetector,
        sample_compliance_history: List[Dict[str, Any]],
    ):
        """Test score anomaly detection"""
        # Arrange - normal score within expected range
        scores = [h["score"] for h in sample_compliance_history]
        mean_score = statistics.mean(scores)

        # Act
        result = await detector.detect_score_anomaly(
            model_id="model_001",
            current_score=mean_score,  # Should not be anomaly
            history=sample_compliance_history,
        )

        # Assert
        assert result["is_anomaly"] is False
        assert "z_score" in result
        assert abs(result["z_score"]) < 2.0

    @pytest.mark.asyncio
    async def test_detect_score_anomaly_outlier(
        self,
        detector: MockAnomalyDetector,
        sample_compliance_history: List[Dict[str, Any]],
    ):
        """Test score anomaly detection with outlier"""
        # Arrange - extreme score
        outlier_score = 20.0  # Very low compared to history (around 75-90)

        # Act
        result = await detector.detect_score_anomaly(
            model_id="model_001",
            current_score=outlier_score,
            history=sample_compliance_history,
        )

        # Assert
        assert result["is_anomaly"] is True
        assert abs(result["z_score"]) > 2.0
        assert result["direction"] == "decline"

    @pytest.mark.asyncio
    async def test_detect_violation_surge(
        self,
        detector: MockAnomalyDetector,
        sample_violation_history: List[Dict[str, Any]],
    ):
        """Test violation surge detection"""
        # Act
        result = await detector.detect_violation_surge(
            model_id="model_001",
            violations=sample_violation_history,
            window_days=7,
        )

        # Assert
        assert "is_surge" in result
        assert "surge_ratio" in result
        assert result["severity"] in ["critical", "high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_detect_violation_surge_no_surge(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test violation surge detection with stable pattern"""
        # Arrange - consistent violations over time
        base_time = datetime.now(timezone.utc) - timedelta(days=30)
        stable_violations = [
            {"timestamp": base_time + timedelta(days=i * 7), "severity": "medium"}
            for i in range(5)  # One per week, consistent
        ]

        # Act
        result = await detector.detect_violation_surge(
            model_id="model_001",
            violations=stable_violations,
            window_days=7,
        )

        # Assert
        assert result["surge_ratio"] < 2.0  # No significant surge

    @pytest.mark.asyncio
    async def test_detect_assessment_gap(
        self,
        detector: MockAnomalyDetector,
        sample_assessment_dates: List[datetime],
    ):
        """Test assessment gap detection"""
        # Act
        result = await detector.detect_assessment_gap(
            model_id="model_001",
            assessment_dates=sample_assessment_dates,
            expected_frequency_days=14,
        )

        # Assert
        assert result["is_gap"] is True
        assert "historical_gaps" in result
        assert len(result["historical_gaps"]) > 0  # Should detect the gap

    @pytest.mark.asyncio
    async def test_detect_assessment_gap_none(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test assessment gap detection with regular assessments"""
        # Arrange - regular weekly assessments
        base_time = datetime.now(timezone.utc) - timedelta(days=28)
        regular_dates = [base_time + timedelta(days=i * 7) for i in range(5)]

        # Act
        result = await detector.detect_assessment_gap(
            model_id="model_001",
            assessment_dates=regular_dates,
            expected_frequency_days=14,  # Bi-weekly expectation
        )

        # Assert
        assert len(result["historical_gaps"]) == 0

    @pytest.mark.asyncio
    async def test_detect_risk_escalation(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test risk escalation detection"""
        # Arrange - escalating risk scores
        now = datetime.now(timezone.utc)
        risk_history = [
            {"timestamp": now - timedelta(days=20), "risk_score": 40},
            {"timestamp": now - timedelta(days=15), "risk_score": 45},
            {"timestamp": now - timedelta(days=10), "risk_score": 50},
            {"timestamp": now - timedelta(days=5), "risk_score": 65},  # Jump
            {"timestamp": now - timedelta(days=2), "risk_score": 72},  # Another jump
        ]

        # Act
        result = await detector.detect_risk_escalation(
            model_id="model_001",
            risk_history=risk_history,
            window_days=7,
        )

        # Assert
        assert result["is_escalation"] is True
        assert result["escalation_percentage"] > 20

    @pytest.mark.asyncio
    async def test_detect_risk_escalation_stable(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test risk escalation detection with stable scores"""
        # Arrange - stable risk scores
        now = datetime.now(timezone.utc)
        risk_history = [{"timestamp": now - timedelta(days=i * 3), "risk_score": 50 + (i % 3)} for i in range(10)]

        # Act
        result = await detector.detect_risk_escalation(
            model_id="model_001",
            risk_history=risk_history,
            window_days=7,
        )

        # Assert
        assert result["escalation_percentage"] < 20  # Below escalation threshold

    def test_z_score_calculation(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test z-score calculation"""
        # Arrange
        value = 85.0
        mean = 75.0
        std_dev = 5.0

        # Act
        z_score = detector.calculate_z_score(value, mean, std_dev)

        # Assert
        assert z_score == pytest.approx(2.0, abs=0.01)

    def test_z_score_calculation_zero_std(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test z-score calculation with zero standard deviation"""
        # Arrange
        value = 75.0
        mean = 75.0
        std_dev = 0.0

        # Act
        z_score = detector.calculate_z_score(value, mean, std_dev)

        # Assert
        assert z_score == 0.0

    def test_iqr_bounds(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test IQR bounds calculation"""
        # Arrange
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

        # Act
        q1, q3, lower, upper = detector.calculate_iqr_bounds(values)

        # Assert
        assert q1 < q3
        assert lower < q1
        assert upper > q3

    def test_iqr_bounds_insufficient_data(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test IQR bounds with insufficient data"""
        # Arrange
        values = [10, 20, 30]  # Only 3 values

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            detector.calculate_iqr_bounds(values)

        assert "at least 4" in str(exc_info.value)

    def test_severity_classification(
        self,
        detector: MockAnomalyDetector,
    ):
        """Test anomaly severity classification"""
        # Test various z-scores
        assert detector._classify_anomaly_severity(3.5) == "critical"
        assert detector._classify_anomaly_severity(2.7) == "high"
        assert detector._classify_anomaly_severity(2.2) == "medium"
        assert detector._classify_anomaly_severity(1.5) == "low"


# ============================================================================
# TEST CLASS: Analytics Integration
# ============================================================================


class TestAnalyticsIntegration:
    """Integration tests for analytics components"""

    @pytest.fixture
    def predictor(self) -> MockPredictiveScorer:
        return MockPredictiveScorer()

    @pytest.fixture
    def detector(self) -> MockAnomalyDetector:
        return MockAnomalyDetector()

    @pytest.mark.asyncio
    async def test_full_analytics_workflow(
        self,
        predictor: MockPredictiveScorer,
        detector: MockAnomalyDetector,
        sample_compliance_history: List[Dict[str, Any]],
        sample_violation_history: List[Dict[str, Any]],
        sample_risk_indicators: List[RiskIndicator],
    ):
        """Test complete analytics workflow"""
        model_id = "model_integration_001"

        # Step 1: Predict compliance score
        score_prediction = await predictor.predict_compliance_score(
            model_id=model_id,
            history=sample_compliance_history,
        )

        # Step 2: Forecast risk
        risk_forecast = await predictor.forecast_risk_level(
            model_id=model_id,
            indicators=sample_risk_indicators,
        )

        # Step 3: Calculate violation probability
        violation_prob = await predictor.calculate_violation_probability(
            model_id=model_id,
            violation_history=sample_violation_history,
            risk_score=risk_forecast["current_risk_score"],
        )

        # Step 4: Get recommendations
        recommendations = await predictor.recommend_preventive_actions(
            model_id=model_id,
            predictions=violation_prob,
            indicators=sample_risk_indicators,
        )

        # Step 5: Check for anomalies
        score_anomaly = await detector.detect_score_anomaly(
            model_id=model_id,
            current_score=score_prediction["current_score"],
            history=sample_compliance_history,
        )

        violation_surge = await detector.detect_violation_surge(
            model_id=model_id,
            violations=sample_violation_history,
        )

        # Assert complete workflow executed
        assert score_prediction["predicted_score"] is not None
        assert risk_forecast["projected_risk_level"] is not None
        assert violation_prob["violation_probability"] is not None
        assert len(recommendations) > 0
        assert "is_anomaly" in score_anomaly
        assert "is_surge" in violation_surge

    @pytest.mark.asyncio
    async def test_analytics_with_degraded_data(
        self,
        predictor: MockPredictiveScorer,
        detector: MockAnomalyDetector,
    ):
        """Test analytics behavior with minimal/degraded data"""
        # Arrange - minimal data
        minimal_history = [
            {"timestamp": datetime.now(timezone.utc) - timedelta(days=i), "score": 70 + i} for i in range(5)
        ]

        # Act
        prediction = await predictor.predict_compliance_score(
            model_id="model_minimal",
            history=minimal_history,
        )

        anomaly_result = await detector.detect_score_anomaly(
            model_id="model_minimal",
            current_score=75.0,
            history=minimal_history,
        )

        # Assert - should still produce results, but with lower confidence
        assert prediction["confidence"] < 0.8  # Lower confidence with less data
        assert anomaly_result["confidence"] < 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
