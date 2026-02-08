"""
Tests for Compliance Anomaly Detection

Tests statistical anomaly detection methods including z-scores, IQR bounds,
and trend analysis for compliance violations.
"""

from datetime import datetime, timedelta, timezone

import pytest

from ghl_real_estate_ai.compliance_platform.analytics.anomaly_detection import (
    AnomalyDetectionConfig,
    AnomalySeverity,
    AnomalyType,
    ComplianceAnomaly,
    ComplianceAnomalyDetector,
)


@pytest.fixture
def detector() -> ComplianceAnomalyDetector:
    """Create a detector with default config."""
    return ComplianceAnomalyDetector()


@pytest.fixture
def strict_detector() -> ComplianceAnomalyDetector:
    """Create a detector with stricter thresholds."""
    config = AnomalyDetectionConfig(
        z_score_threshold=2.0,
        violation_surge_threshold=2,
        assessment_gap_days=14,
        remediation_stall_days=7,
    )
    return ComplianceAnomalyDetector(config=config)


@pytest.fixture
def now() -> datetime:
    """Current timestamp for tests."""
    return datetime.now(timezone.utc)


class TestZScoreCalculation:
    """Tests for z-score calculation."""

    def test_z_score_normal_distribution(self, detector: ComplianceAnomalyDetector):
        """Test z-score with normal values."""
        values = [80.0, 82.0, 78.0, 81.0, 79.0, 80.0, 83.0, 77.0]
        z = detector._calculate_z_score(85.0, values)
        # 85 is above mean (~80), should be positive
        assert z > 0
        assert 1.5 < z < 3.0

    def test_z_score_below_mean(self, detector: ComplianceAnomalyDetector):
        """Test z-score for value below mean."""
        values = [80.0, 82.0, 78.0, 81.0, 79.0]
        z = detector._calculate_z_score(70.0, values)
        assert z < 0
        assert z < -3.0  # Far below mean

    def test_z_score_at_mean(self, detector: ComplianceAnomalyDetector):
        """Test z-score for value at mean."""
        values = [80.0, 80.0, 80.0, 80.0]
        z = detector._calculate_z_score(80.0, values)
        assert z == 0.0

    def test_z_score_insufficient_data(self, detector: ComplianceAnomalyDetector):
        """Test z-score with insufficient data."""
        z = detector._calculate_z_score(80.0, [75.0])
        assert z == 0.0

    def test_z_score_zero_variance(self, detector: ComplianceAnomalyDetector):
        """Test z-score with identical values (zero variance)."""
        values = [80.0, 80.0, 80.0, 80.0]
        z = detector._calculate_z_score(85.0, values)
        assert z == 0.0  # Can't compute with zero stdev


class TestIQRBounds:
    """Tests for IQR outlier detection."""

    def test_iqr_bounds_normal(self, detector: ComplianceAnomalyDetector):
        """Test IQR bounds with normal distribution."""
        values = [60, 65, 70, 75, 80, 85, 90, 95]
        lower, upper = detector._calculate_iqr_bounds(values)
        assert lower < 60
        assert upper > 95

    def test_iqr_bounds_insufficient_data(self, detector: ComplianceAnomalyDetector):
        """Test IQR bounds with insufficient data."""
        values = [80, 85, 90]
        lower, upper = detector._calculate_iqr_bounds(values)
        assert lower == float("-inf")
        assert upper == float("inf")

    def test_iqr_detects_outlier(self, detector: ComplianceAnomalyDetector):
        """Test that IQR correctly identifies outliers."""
        values = [80, 81, 79, 82, 78, 80, 81, 120]  # 120 is outlier
        lower, upper = detector._calculate_iqr_bounds(values[:-1])
        assert values[-1] > upper


class TestTrendBreakDetection:
    """Tests for trend break detection."""

    def test_detects_upward_to_downward_break(self, detector: ComplianceAnomalyDetector):
        """Test detection of trend reversal with clear pattern."""
        # Clear upward trend then clear downward trend with significant range
        values = [50, 55, 60, 65, 70, 75, 80, 72, 65, 58, 50]
        break_idx = detector._detect_trend_break(values)
        # Should detect break around index 6-8
        assert break_idx is not None
        assert 5 <= break_idx <= 9

    def test_no_break_in_stable_trend(self, detector: ComplianceAnomalyDetector):
        """Test no false positive for stable trend."""
        values = [70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90]
        break_idx = detector._detect_trend_break(values)
        # Consistent upward trend should not trigger
        assert break_idx is None

    def test_no_break_for_small_variance(self, detector: ComplianceAnomalyDetector):
        """Test no false positive for small variance data."""
        values = [80, 81, 79, 82, 78, 80, 81, 79, 82, 78]  # Small variance
        break_idx = detector._detect_trend_break(values)
        # Small variance should not trigger (range < 5)
        assert break_idx is None

    def test_insufficient_data(self, detector: ComplianceAnomalyDetector):
        """Test with insufficient data points."""
        values = [70, 75, 80, 85]
        break_idx = detector._detect_trend_break(values)
        assert break_idx is None


class TestScoreAnomalyDetection:
    """Tests for score anomaly detection."""

    @pytest.mark.asyncio
    async def test_detects_score_spike(self, detector: ComplianceAnomalyDetector):
        """Test detection of unusual score increase."""
        historical = [75.0, 76.0, 74.0, 75.0, 77.0, 73.0, 76.0]
        anomaly = await detector.detect_score_anomaly("model_123", 95.0, historical)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.SCORE_SPIKE
        assert anomaly.deviation is not None
        assert anomaly.deviation > 0

    @pytest.mark.asyncio
    async def test_detects_score_drop(self, detector: ComplianceAnomalyDetector):
        """Test detection of unusual score decrease."""
        historical = [85.0, 86.0, 84.0, 85.0, 87.0, 83.0, 86.0]
        anomaly = await detector.detect_score_anomaly("model_123", 50.0, historical)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.SCORE_DROP
        assert anomaly.deviation is not None
        assert anomaly.deviation < 0

    @pytest.mark.asyncio
    async def test_no_anomaly_for_normal_variance(self, detector: ComplianceAnomalyDetector):
        """Test no false positive for normal variance."""
        historical = [75.0, 76.0, 74.0, 75.0, 77.0, 73.0, 76.0]
        anomaly = await detector.detect_score_anomaly("model_123", 78.0, historical)
        assert anomaly is None

    @pytest.mark.asyncio
    async def test_insufficient_history(self, detector: ComplianceAnomalyDetector):
        """Test with insufficient history."""
        historical = [75.0, 76.0]
        anomaly = await detector.detect_score_anomaly("model_123", 50.0, historical)
        assert anomaly is None


class TestViolationSurgeDetection:
    """Tests for violation surge detection."""

    @pytest.mark.asyncio
    async def test_detects_surge(self, detector: ComplianceAnomalyDetector):
        """Test detection of violation surge."""
        violations = [
            {"severity": "high", "violation_id": "v1"},
            {"severity": "critical", "violation_id": "v2"},
            {"severity": "medium", "violation_id": "v3"},
            {"severity": "high", "violation_id": "v4"},
        ]
        anomaly = await detector.detect_violation_surge("model_123", violations, 1.0)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.VIOLATION_SURGE
        assert anomaly.actual_value == 4.0

    @pytest.mark.asyncio
    async def test_no_surge_below_threshold(self, detector: ComplianceAnomalyDetector):
        """Test no false positive below threshold."""
        violations = [{"severity": "low", "violation_id": "v1"}]
        anomaly = await detector.detect_violation_surge("model_123", violations, 1.0)
        assert anomaly is None

    @pytest.mark.asyncio
    async def test_surge_severity_escalation(self, detector: ComplianceAnomalyDetector):
        """Test severity escalation for critical violations."""
        violations = [
            {"severity": "critical", "violation_id": "v1"},
            {"severity": "critical", "violation_id": "v2"},
            {"severity": "high", "violation_id": "v3"},
        ]
        anomaly = await detector.detect_violation_surge("model_123", violations, 0.5)
        assert anomaly is not None
        assert anomaly.severity == AnomalySeverity.CRITICAL


class TestAssessmentGapDetection:
    """Tests for assessment gap detection."""

    @pytest.mark.asyncio
    async def test_detects_gap(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test detection of assessment gap."""
        old_assessment = now - timedelta(days=45)
        anomaly = await detector.detect_assessment_gap("model_123", old_assessment)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.ASSESSMENT_GAP
        assert anomaly.actual_value >= 45

    @pytest.mark.asyncio
    async def test_no_gap_recent_assessment(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test no false positive for recent assessment."""
        recent = now - timedelta(days=10)
        anomaly = await detector.detect_assessment_gap("model_123", recent)
        assert anomaly is None

    @pytest.mark.asyncio
    async def test_severity_escalation_with_gap_length(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test severity increases with gap length."""
        # 30 days - low
        low_gap = now - timedelta(days=35)
        anomaly_low = await detector.detect_assessment_gap("model_123", low_gap)

        # 60 days - medium
        med_gap = now - timedelta(days=65)
        anomaly_med = await detector.detect_assessment_gap("model_123", med_gap)

        # 90 days - critical
        crit_gap = now - timedelta(days=95)
        anomaly_crit = await detector.detect_assessment_gap("model_123", crit_gap)

        assert anomaly_low is not None
        assert anomaly_med is not None
        assert anomaly_crit is not None
        assert anomaly_crit.severity.value <= anomaly_med.severity.value


class TestRiskEscalationDetection:
    """Tests for risk escalation detection."""

    @pytest.mark.asyncio
    async def test_detects_escalation(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test detection of risk level escalation."""
        risk_history = [
            {"risk_level": "minimal", "timestamp": now - timedelta(days=3)},
            {"risk_level": "limited", "timestamp": now - timedelta(days=2)},
            {"risk_level": "high", "timestamp": now - timedelta(days=1)},
        ]
        anomaly = await detector.detect_risk_escalation("model_123", risk_history)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.RISK_ESCALATION

    @pytest.mark.asyncio
    async def test_no_escalation_stable_risk(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test no false positive for stable risk."""
        risk_history = [
            {"risk_level": "limited", "timestamp": now - timedelta(days=3)},
            {"risk_level": "limited", "timestamp": now - timedelta(days=2)},
            {"risk_level": "medium", "timestamp": now - timedelta(days=1)},
        ]
        anomaly = await detector.detect_risk_escalation("model_123", risk_history)
        # Single level jump is below threshold
        assert anomaly is None

    @pytest.mark.asyncio
    async def test_critical_severity_for_unacceptable(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test critical severity when reaching unacceptable."""
        risk_history = [
            {"risk_level": "limited", "timestamp": now - timedelta(days=2)},
            {"risk_level": "unacceptable", "timestamp": now - timedelta(days=1)},
        ]
        anomaly = await detector.detect_risk_escalation("model_123", risk_history)
        assert anomaly is not None
        assert anomaly.severity == AnomalySeverity.CRITICAL


class TestRemediationStallDetection:
    """Tests for remediation stall detection."""

    @pytest.mark.asyncio
    async def test_detects_stall(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test detection of stalled remediation."""
        remediations = [
            {
                "action_id": "a1",
                "status": "in_progress",
                "last_updated": (now - timedelta(days=20)).isoformat(),
                "due_date": (now - timedelta(days=5)).isoformat(),
                "priority": 2,
            }
        ]
        anomaly = await detector.detect_remediation_stall("model_123", remediations)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.REMEDIATION_STALL

    @pytest.mark.asyncio
    async def test_no_stall_active_remediation(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test no false positive for active remediation."""
        remediations = [
            {
                "action_id": "a1",
                "status": "in_progress",
                "last_updated": (now - timedelta(days=3)).isoformat(),
                "priority": 2,
            }
        ]
        anomaly = await detector.detect_remediation_stall("model_123", remediations)
        assert anomaly is None

    @pytest.mark.asyncio
    async def test_ignores_completed(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test completed remediations are ignored."""
        remediations = [
            {
                "action_id": "a1",
                "status": "completed",
                "last_updated": (now - timedelta(days=30)).isoformat(),
                "priority": 1,
            }
        ]
        anomaly = await detector.detect_remediation_stall("model_123", remediations)
        assert anomaly is None


class TestPatternAnomalyDetection:
    """Tests for pattern anomaly detection."""

    @pytest.mark.asyncio
    async def test_detects_outlier_pattern(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test detection of outlier in metric pattern."""
        values = [80.0, 82.0, 79.0, 81.0, 80.0, 78.0, 120.0]  # 120 is outlier
        timestamps = [now - timedelta(days=i) for i in range(len(values), 0, -1)]

        anomaly = await detector.detect_pattern_anomaly("model_123", "fairness_score", values, timestamps)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.UNUSUAL_PATTERN

    @pytest.mark.asyncio
    async def test_no_anomaly_stable_pattern(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test no false positive for stable pattern."""
        values = [80.0, 82.0, 79.0, 81.0, 80.0, 78.0, 81.0]
        timestamps = [now - timedelta(days=i) for i in range(len(values), 0, -1)]

        anomaly = await detector.detect_pattern_anomaly("model_123", "fairness_score", values, timestamps)
        assert anomaly is None


class TestComprehensiveDetection:
    """Tests for comprehensive anomaly detection."""

    @pytest.mark.asyncio
    async def test_detect_multiple_anomalies(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test detection of multiple anomalies."""
        current_metrics = {
            "compliance_score": 50.0,  # Low (anomaly)
            "last_assessment": (now - timedelta(days=60)).isoformat(),  # Gap (anomaly)
            "recent_violations": [
                {"severity": "critical", "violation_id": "v1"},
                {"severity": "high", "violation_id": "v2"},
                {"severity": "high", "violation_id": "v3"},
            ],  # Surge (anomaly)
            "risk_level": "high",
        }

        historical_data = [
            {
                "compliance_score": 85.0,
                "violations": [],
                "risk_level": "limited",
                "timestamp": (now - timedelta(days=7)).isoformat(),
            },
            {
                "compliance_score": 86.0,
                "violations": [],
                "risk_level": "limited",
                "timestamp": (now - timedelta(days=14)).isoformat(),
            },
            {
                "compliance_score": 84.0,
                "violations": [{"severity": "low"}],
                "risk_level": "limited",
                "timestamp": (now - timedelta(days=21)).isoformat(),
            },
            {
                "compliance_score": 87.0,
                "violations": [],
                "risk_level": "limited",
                "timestamp": (now - timedelta(days=28)).isoformat(),
            },
            {
                "compliance_score": 83.0,
                "violations": [],
                "risk_level": "limited",
                "timestamp": (now - timedelta(days=35)).isoformat(),
            },
        ]

        anomalies = await detector.detect_anomalies("model_123", current_metrics, historical_data)

        # Should detect at least score drop and assessment gap
        assert len(anomalies) >= 2
        anomaly_types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.SCORE_DROP in anomaly_types
        assert AnomalyType.ASSESSMENT_GAP in anomaly_types

    @pytest.mark.asyncio
    async def test_no_anomalies_healthy_system(self, detector: ComplianceAnomalyDetector, now: datetime):
        """Test no false positives for healthy system."""
        current_metrics = {
            "compliance_score": 87.0,
            "last_assessment": (now - timedelta(days=5)).isoformat(),
            "recent_violations": [],
            "risk_level": "limited",
            "open_remediations": [],
        }

        historical_data = [
            {
                "compliance_score": 85.0 + i,
                "violations": [],
                "risk_level": "limited",
                "timestamp": (now - timedelta(days=7 * (i + 1))).isoformat(),
            }
            for i in range(6)
        ]

        anomalies = await detector.detect_anomalies("model_123", current_metrics, historical_data)

        assert len(anomalies) == 0


class TestAnomalyModel:
    """Tests for ComplianceAnomaly model."""

    def test_to_alert_payload(self):
        """Test alert payload generation."""
        anomaly = ComplianceAnomaly(
            model_id="model_123",
            anomaly_type=AnomalyType.SCORE_DROP,
            severity=AnomalySeverity.HIGH,
            description="Test anomaly",
            expected_value=85.0,
            actual_value=50.0,
            deviation=-3.5,
            confidence=0.9,
            recommended_investigation=["Step 1", "Step 2"],
        )

        payload = anomaly.to_alert_payload()

        assert payload["model_id"] == "model_123"
        assert payload["type"] == "score_drop"
        assert payload["severity"] == "high"
        assert payload["deviation"] == -3.5
        assert payload["confidence"] == 0.9
        assert len(payload["actions"]) == 2


class TestConfigurationOptions:
    """Tests for configuration options."""

    @pytest.mark.asyncio
    async def test_stricter_thresholds(self, strict_detector: ComplianceAnomalyDetector, now: datetime):
        """Test stricter detection with custom config."""
        # With default config, this wouldn't trigger assessment gap
        last_assessment = now - timedelta(days=20)
        anomaly = await strict_detector.detect_assessment_gap("model_123", last_assessment)
        assert anomaly is not None  # Should trigger with 14-day threshold

    def test_baseline_caching(self, detector: ComplianceAnomalyDetector):
        """Test baseline calculation and caching."""
        historical = [
            {"compliance_score": 80.0, "fairness_score": 75.0},
            {"compliance_score": 82.0, "fairness_score": 77.0},
            {"compliance_score": 79.0, "fairness_score": 74.0},
        ]

        baseline = detector._calculate_baseline("model_123", historical)

        assert "compliance_score" in baseline
        assert baseline["compliance_score"] == pytest.approx(80.33, rel=0.01)
        assert detector.get_baseline("model_123") is not None

        detector.clear_baseline("model_123")
        assert detector.get_baseline("model_123") is None


class TestSeverityClassification:
    """Tests for severity classification."""

    def test_critical_for_high_deviation(self, detector: ComplianceAnomalyDetector):
        """Test critical severity for high deviations."""
        severity = detector._classify_severity(5.0, AnomalyType.SCORE_DROP)
        assert severity == AnomalySeverity.CRITICAL

    def test_low_for_minor_deviation(self, detector: ComplianceAnomalyDetector):
        """Test low severity for minor deviations."""
        severity = detector._classify_severity(1.5, AnomalyType.SCORE_SPIKE)
        assert severity == AnomalySeverity.LOW

    def test_type_specific_boost(self, detector: ComplianceAnomalyDetector):
        """Test that violation surge gets severity boost."""
        # Same deviation, different types
        surge_severity = detector._classify_severity(2.5, AnomalyType.VIOLATION_SURGE)
        spike_severity = detector._classify_severity(2.5, AnomalyType.SCORE_SPIKE)

        # Violation surge should be more severe
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3,
        }
        assert severity_order[surge_severity] <= severity_order[spike_severity]
