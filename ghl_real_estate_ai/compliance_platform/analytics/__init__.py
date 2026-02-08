"""
Enterprise Compliance Platform - Analytics Module

Statistical analysis, anomaly detection, and predictive scoring
for compliance monitoring and forecasting.
"""

# Predictive scoring (always available)
from ghl_real_estate_ai.compliance_platform.analytics.predictive_scoring import (
    CompliancePrediction,
    PredictionTimeframe,
    PredictiveComplianceEngine,
    PreventiveAction,
    RiskForecast,
    TrendDirection,
    ViolationProbability,
)

__all__ = [
    # Predictive scoring
    "CompliancePrediction",
    "PredictionTimeframe",
    "PredictiveComplianceEngine",
    "PreventiveAction",
    "RiskForecast",
    "TrendDirection",
    "ViolationProbability",
]

# Anomaly detection (optional - may not exist yet)
try:
    from ghl_real_estate_ai.compliance_platform.analytics.anomaly_detection import (
        AnomalyDetectionConfig,
        AnomalySeverity,
        AnomalyType,
        ComplianceAnomaly,
        ComplianceAnomalyDetector,
    )

    __all__.extend(
        [
            "AnomalyType",
            "AnomalySeverity",
            "ComplianceAnomaly",
            "AnomalyDetectionConfig",
            "ComplianceAnomalyDetector",
        ]
    )
except ImportError:
    # Anomaly detection module not yet implemented
    pass
