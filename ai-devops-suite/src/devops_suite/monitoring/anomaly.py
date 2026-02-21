"""Anomaly detection using z-score with configurable thresholds."""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class AnomalyResult:
    metric: str
    value: float
    expected: float
    z_score: float
    is_anomaly: bool
    severity: str  # "warning" or "critical"


class AnomalyDetector:
    """Z-score based anomaly detection for metric time series."""

    def __init__(self, sensitivity: float = 2.5):
        self.sensitivity = sensitivity

    def detect(self, metric_name: str, current_value: float, history: list[float]) -> AnomalyResult:
        if len(history) < 2:
            return AnomalyResult(
                metric=metric_name,
                value=current_value,
                expected=current_value,
                z_score=0.0,
                is_anomaly=False,
                severity="none",
            )
        mean = statistics.mean(history)
        stdev = statistics.stdev(history)
        if stdev == 0:
            z_score = 0.0
        else:
            z_score = (current_value - mean) / stdev

        is_anomaly = abs(z_score) > self.sensitivity
        if abs(z_score) > 3.5:
            severity = "critical"
        elif is_anomaly:
            severity = "warning"
        else:
            severity = "none"

        return AnomalyResult(
            metric=metric_name,
            value=current_value,
            expected=mean,
            z_score=z_score,
            is_anomaly=is_anomaly,
            severity=severity,
        )

    def detect_batch(
        self, metric_name: str, values: list[float], window: int = 20
    ) -> list[AnomalyResult]:
        results = []
        for i, val in enumerate(values):
            start = max(0, i - window)
            history = values[start:i]
            results.append(self.detect(metric_name, val, history))
        return results
