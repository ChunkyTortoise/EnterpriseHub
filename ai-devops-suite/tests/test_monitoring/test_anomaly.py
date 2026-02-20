"""Unit tests for AnomalyDetector — z-score based anomaly detection."""

from __future__ import annotations

import pytest

from devops_suite.monitoring.anomaly import AnomalyDetector


@pytest.fixture
def detector():
    return AnomalyDetector(sensitivity=2.5)


class TestAnomalyDetection:
    def test_normal_value_not_anomaly(self, detector):
        history = [10, 12, 11, 10, 13, 11, 12, 10]
        result = detector.detect("latency", 11, history)
        assert result.is_anomaly is False
        assert result.severity == "none"

    def test_extreme_value_is_anomaly(self, detector):
        history = [10, 12, 11, 10, 13, 11, 12, 10]
        result = detector.detect("latency", 100, history)
        assert result.is_anomaly is True
        assert result.severity in ("warning", "critical")

    def test_critical_severity_for_extreme_z_score(self, detector):
        history = [10, 11, 10, 11, 10, 11, 10, 11]
        result = detector.detect("latency", 50, history)
        # z-score > 3.5 should be critical
        assert result.severity == "critical"

    def test_insufficient_history(self, detector):
        result = detector.detect("latency", 10, [5])
        assert result.is_anomaly is False
        assert result.z_score == 0.0

    def test_empty_history(self, detector):
        result = detector.detect("latency", 10, [])
        assert result.is_anomaly is False

    def test_zero_stdev(self, detector):
        history = [10, 10, 10, 10]
        result = detector.detect("latency", 10, history)
        assert result.z_score == 0.0
        assert result.is_anomaly is False

    def test_negative_anomaly(self, detector):
        history = [100, 105, 98, 102, 100, 103]
        result = detector.detect("latency", 10, history)
        assert result.is_anomaly is True
        assert result.z_score < 0

    def test_result_contains_metric_name(self, detector):
        result = detector.detect("cpu_usage", 50, [40, 45, 42, 43])
        assert result.metric == "cpu_usage"

    def test_custom_sensitivity(self):
        strict = AnomalyDetector(sensitivity=1.0)
        lenient = AnomalyDetector(sensitivity=5.0)
        history = [10, 12, 11, 10, 13, 11]

        r_strict = strict.detect("m", 20, history)
        r_lenient = lenient.detect("m", 20, history)

        # Same value, stricter detector more likely to flag
        assert r_strict.z_score == r_lenient.z_score
        # Strict may flag while lenient may not
        if r_strict.is_anomaly:
            assert abs(r_strict.z_score) > 1.0


class TestDetectBatch:
    def test_batch_returns_results_for_each_value(self, detector):
        values = [10, 12, 11, 50, 10, 12]
        results = detector.detect_batch("metric", values, window=5)
        assert len(results) == len(values)

    def test_batch_detects_spike(self, detector):
        values = [10, 11, 9, 12, 10, 11, 9, 100, 10, 11]
        results = detector.detect_batch("metric", values, window=5)
        # The spike at index 7 should be flagged
        spike_result = results[7]
        assert spike_result.is_anomaly is True
