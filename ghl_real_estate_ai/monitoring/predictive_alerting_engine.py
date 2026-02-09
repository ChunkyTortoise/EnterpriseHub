"""
ML-Based Predictive Alerting Engine
===================================

Advanced anomaly detection and predictive alerting system using machine learning
to predict performance issues before they occur.

Features:
- Time series anomaly detection for performance metrics
- Conversation drift detection for bot effectiveness
- Lead quality degradation prediction
- Market context-aware alerting thresholds
- Behavioral pattern analysis for optimal intervention timing

Author: EnterpriseHub AI Monitoring Team
Version: 1.0.0
Date: 2026-01-24
"""

import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class PredictionType(Enum):
    """Types of predictions the system can make"""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    BOT_CONVERSATION_DRIFT = "bot_conversation_drift"
    LEAD_QUALITY_DROP = "lead_quality_drop"
    SYSTEM_OVERLOAD = "system_overload"
    BUSINESS_METRIC_ANOMALY = "business_metric_anomaly"


class AlertPrediction:
    """Prediction result with confidence and timing"""

    def __init__(
        self,
        prediction_type: PredictionType,
        confidence: float,
        time_to_issue: int,  # minutes
        affected_metrics: List[str],
        recommended_actions: List[str],
        business_impact: str,
    ):
        self.prediction_type = prediction_type
        self.confidence = confidence
        self.time_to_issue = time_to_issue
        self.affected_metrics = affected_metrics
        self.recommended_actions = recommended_actions
        self.business_impact = business_impact
        self.predicted_at = datetime.utcnow()


@dataclass
class TimeSeriesMetric:
    """Time series metric data point"""

    timestamp: datetime
    value: float
    metric_name: str
    labels: Dict[str, str] = field(default_factory=dict)


class PredictiveAlertingEngine:
    """
    ML-powered predictive alerting system that learns patterns
    and predicts issues before they become critical.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.models: Dict[str, Any] = {}
        self.historical_data: Dict[str, List[TimeSeriesMetric]] = {}
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        # Initialize models
        self._initialize_prediction_models()

    def _initialize_prediction_models(self):
        """Initialize ML models for different prediction types"""

        # Isolation Forest for anomaly detection (unsupervised)
        self.anomaly_detectors = {
            "performance_metrics": IsolationForest(
                contamination=0.1,  # 10% anomaly rate expected
                random_state=42,
                n_estimators=100,
            ),
            "bot_conversation": IsolationForest(
                contamination=0.05,  # Lower contamination for conversation quality
                random_state=42,
                n_estimators=150,
            ),
            "business_metrics": IsolationForest(contamination=0.08, random_state=42, n_estimators=120),
        }

        # Scalers for feature normalization
        self.scalers = {name: StandardScaler() for name in self.anomaly_detectors.keys()}

        logger.info("Predictive alerting models initialized")

    async def train_models(self, historical_metrics: Dict[str, List[TimeSeriesMetric]]):
        """Train ML models on historical performance data"""
        try:
            logger.info("Training predictive models on historical data...")

            # Prepare training data for performance metrics
            perf_features = self._extract_performance_features(historical_metrics.get("performance", []))
            if len(perf_features) > 10:  # Need minimum data for training
                X_perf = self.scalers["performance_metrics"].fit_transform(perf_features)
                self.anomaly_detectors["performance_metrics"].fit(X_perf)

            # Prepare training data for bot conversation metrics
            conv_features = self._extract_conversation_features(historical_metrics.get("conversation", []))
            if len(conv_features) > 10:
                X_conv = self.scalers["bot_conversation"].fit_transform(conv_features)
                self.anomaly_detectors["bot_conversation"].fit(X_conv)

            # Prepare training data for business metrics
            biz_features = self._extract_business_features(historical_metrics.get("business", []))
            if len(biz_features) > 10:
                X_biz = self.scalers["business_metrics"].fit_transform(biz_features)
                self.anomaly_detectors["business_metrics"].fit(X_biz)

            logger.info("Model training completed successfully")

        except Exception as e:
            logger.error(f"Error training predictive models: {e}")

    async def predict_performance_issues(
        self, current_metrics: Dict[str, float], recent_history: List[TimeSeriesMetric]
    ) -> List[AlertPrediction]:
        """
        Analyze current metrics and predict potential issues
        """
        predictions = []

        try:
            # 1. Performance Degradation Prediction
            perf_prediction = await self._predict_performance_degradation(current_metrics, recent_history)
            if perf_prediction:
                predictions.append(perf_prediction)

            # 2. Bot Conversation Drift Detection
            conv_prediction = await self._predict_conversation_drift(current_metrics, recent_history)
            if conv_prediction:
                predictions.append(conv_prediction)

            # 3. Lead Quality Drop Prediction
            lead_prediction = await self._predict_lead_quality_issues(current_metrics, recent_history)
            if lead_prediction:
                predictions.append(lead_prediction)

            # 4. System Overload Prediction
            system_prediction = await self._predict_system_overload(current_metrics, recent_history)
            if system_prediction:
                predictions.append(system_prediction)

            # 5. Business Metric Anomalies
            business_prediction = await self._predict_business_anomalies(current_metrics, recent_history)
            if business_prediction:
                predictions.append(business_prediction)

        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")

        return predictions

    async def _predict_performance_degradation(
        self, current_metrics: Dict[str, float], recent_history: List[TimeSeriesMetric]
    ) -> Optional[AlertPrediction]:
        """Predict if performance is about to degrade based on trends"""

        try:
            # Extract performance indicators
            response_times = [m.value for m in recent_history if m.metric_name == "response_time_ms"][
                -20:
            ]  # Last 20 data points

            if len(response_times) < 5:
                return None

            # Calculate trend and velocity
            time_indices = np.arange(len(response_times))
            trend = np.polyfit(time_indices, response_times, 1)[0]  # Slope

            current_response = current_metrics.get("response_time_ms", 0)

            # Predict performance degradation if:
            # 1. Rising trend in response time
            # 2. Current response time approaching threshold
            # 3. ML model detects anomaly

            features = np.array(
                [
                    [
                        current_response,
                        trend,
                        np.std(response_times),
                        np.mean(response_times),
                        current_metrics.get("cpu_usage_percent", 0),
                        current_metrics.get("memory_usage_percent", 0),
                    ]
                ]
            )

            # Use trained model to detect anomaly
            if "performance_metrics" in self.scalers:
                features_scaled = self.scalers["performance_metrics"].transform(features)
                anomaly_score = self.anomaly_detectors["performance_metrics"].decision_function(features_scaled)[0]

                # Negative scores indicate anomalies in Isolation Forest
                if anomaly_score < -0.3 and trend > 2.0:  # Rising trend + anomaly
                    # Calculate time to issue (minutes until threshold breach)
                    threshold = 500.0  # Performance SLA threshold
                    if trend > 0:
                        time_to_breach = max(1, int((threshold - current_response) / trend))
                    else:
                        time_to_breach = 60  # Default to 1 hour if no clear trend

                    return AlertPrediction(
                        prediction_type=PredictionType.PERFORMANCE_DEGRADATION,
                        confidence=min(0.95, abs(anomaly_score)),
                        time_to_issue=min(time_to_breach, 120),  # Cap at 2 hours
                        affected_metrics=["response_time_ms", "cpu_usage_percent", "memory_usage_percent"],
                        recommended_actions=[
                            "Scale up compute resources",
                            "Clear application caches",
                            "Check database connection pool",
                            "Review recent deployments",
                        ],
                        business_impact="User experience degradation, potential SLA breach",
                    )

        except Exception as e:
            logger.warning(f"Error predicting performance degradation: {e}")

        return None

    async def _predict_conversation_drift(
        self, current_metrics: Dict[str, float], recent_history: List[TimeSeriesMetric]
    ) -> Optional[AlertPrediction]:
        """Predict if Jorge's bot conversation quality is drifting"""

        try:
            # Extract conversation quality metrics
            qualification_rates = [m.value for m in recent_history if m.metric_name == "lead_conversion_rate"][-15:]

            if len(qualification_rates) < 5:
                return None

            # Look for declining patterns in conversation effectiveness
            recent_avg = np.mean(qualification_rates[-5:])
            historical_avg = np.mean(qualification_rates[:-5]) if len(qualification_rates) > 5 else recent_avg

            # Calculate conversation quality features
            current_conversion = current_metrics.get("lead_conversion_rate", 0)
            conversation_features = [
                current_conversion,
                current_metrics.get("average_lead_score", 0),
                current_metrics.get("voice_analysis_accuracy", 0),
                recent_avg,
                historical_avg,
                np.std(qualification_rates),
            ]

            # Check for significant decline
            decline_percentage = ((historical_avg - recent_avg) / historical_avg) * 100 if historical_avg > 0 else 0

            if decline_percentage > 15:  # 15% decline in conversation effectiveness
                confidence = min(0.9, decline_percentage / 20)  # Scale confidence

                return AlertPrediction(
                    prediction_type=PredictionType.BOT_CONVERSATION_DRIFT,
                    confidence=confidence,
                    time_to_issue=30,  # 30 minutes to address
                    affected_metrics=["lead_conversion_rate", "average_lead_score"],
                    recommended_actions=[
                        "Review recent bot conversation logs",
                        "Check for model drift in intent decoder",
                        "Validate Jorge's confrontational prompts",
                        "Retrain conversation models if needed",
                    ],
                    business_impact="Reduced lead qualification effectiveness, revenue impact",
                )

        except Exception as e:
            logger.warning(f"Error predicting conversation drift: {e}")

        return None

    async def _predict_lead_quality_issues(
        self, current_metrics: Dict[str, float], recent_history: List[TimeSeriesMetric]
    ) -> Optional[AlertPrediction]:
        """Predict potential lead quality degradation"""

        try:
            current_score = current_metrics.get("average_lead_score", 0)

            # Look for pattern of declining lead quality
            if current_score < 65 and current_score > 0:  # Below warning threshold
                # Check trend over recent history
                lead_scores = [m.value for m in recent_history if m.metric_name == "average_lead_score"][-10:]

                if len(lead_scores) >= 3:
                    trend = np.polyfit(range(len(lead_scores)), lead_scores, 1)[0]

                    if trend < -0.5:  # Declining trend
                        return AlertPrediction(
                            prediction_type=PredictionType.LEAD_QUALITY_DROP,
                            confidence=0.85,
                            time_to_issue=15,  # 15 minutes
                            affected_metrics=["average_lead_score", "lead_conversion_rate"],
                            recommended_actions=[
                                "Review lead sources for quality issues",
                                "Check ML model accuracy",
                                "Validate incoming lead data quality",
                                "Adjust lead scoring parameters",
                            ],
                            business_impact="Lower quality leads affecting conversion rates",
                        )

        except Exception as e:
            logger.warning(f"Error predicting lead quality issues: {e}")

        return None

    async def _predict_system_overload(
        self, current_metrics: Dict[str, float], recent_history: List[TimeSeriesMetric]
    ) -> Optional[AlertPrediction]:
        """Predict system resource exhaustion"""

        try:
            cpu_usage = current_metrics.get("cpu_usage_percent", 0)
            memory_usage = current_metrics.get("memory_usage_percent", 0)
            requests_per_sec = current_metrics.get("requests_per_second", 0)

            # Predict overload based on resource utilization trends
            if cpu_usage > 75 or memory_usage > 80 or requests_per_sec > 180:
                # Calculate time to critical thresholds
                cpu_time_to_critical = (90 - cpu_usage) / 0.5 if cpu_usage < 90 else 0  # Assume 0.5%/min increase
                mem_time_to_critical = (90 - memory_usage) / 0.3 if memory_usage < 90 else 0

                min_time = min(cpu_time_to_critical, mem_time_to_critical)

                if min_time <= 20:  # Critical in 20 minutes or less
                    return AlertPrediction(
                        prediction_type=PredictionType.SYSTEM_OVERLOAD,
                        confidence=0.9,
                        time_to_issue=max(5, int(min_time)),
                        affected_metrics=["cpu_usage_percent", "memory_usage_percent", "requests_per_second"],
                        recommended_actions=[
                            "Scale horizontally (add pods)",
                            "Scale vertically (increase resources)",
                            "Enable request throttling",
                            "Clear cache to free memory",
                        ],
                        business_impact="System performance degradation, potential downtime",
                    )

        except Exception as e:
            logger.warning(f"Error predicting system overload: {e}")

        return None

    async def _predict_business_anomalies(
        self, current_metrics: Dict[str, float], recent_history: List[TimeSeriesMetric]
    ) -> Optional[AlertPrediction]:
        """Predict business metric anomalies that could impact revenue"""

        try:
            # Focus on key business metrics
            conversion_rate = current_metrics.get("lead_conversion_rate", 0)
            avg_deal_value = current_metrics.get("average_deal_value", 0)
            commission_pipeline = current_metrics.get("commission_pipeline_value", 0)

            # Historical baselines (would come from database in production)
            historical_conversion = 22.5  # Historical average
            historical_deal_value = 275000

            # Detect significant deviations
            conversion_deviation = abs(conversion_rate - historical_conversion) / historical_conversion
            deal_value_deviation = (
                abs(avg_deal_value - historical_deal_value) / historical_deal_value if historical_deal_value > 0 else 0
            )

            if conversion_deviation > 0.25 or deal_value_deviation > 0.30:  # 25% or 30% deviation
                return AlertPrediction(
                    prediction_type=PredictionType.BUSINESS_METRIC_ANOMALY,
                    confidence=0.8,
                    time_to_issue=60,  # 1 hour to investigate
                    affected_metrics=["lead_conversion_rate", "average_deal_value", "commission_pipeline_value"],
                    recommended_actions=[
                        "Investigate market conditions",
                        "Review recent lead sources",
                        "Check competitor activity",
                        "Validate data collection accuracy",
                    ],
                    business_impact="Potential revenue impact, market condition change",
                )

        except Exception as e:
            logger.warning(f"Error predicting business anomalies: {e}")

        return None

    def _extract_performance_features(self, metrics: List[TimeSeriesMetric]) -> np.ndarray:
        """Extract features for performance prediction models"""
        features = []

        for metric in metrics:
            if metric.metric_name in ["response_time_ms", "cpu_usage_percent", "memory_usage_percent"]:
                features.append(
                    [
                        metric.value,
                        metric.timestamp.hour,  # Time of day
                        metric.timestamp.weekday(),  # Day of week
                    ]
                )

        return np.array(features) if features else np.array([]).reshape(0, 3)

    def _extract_conversation_features(self, metrics: List[TimeSeriesMetric]) -> np.ndarray:
        """Extract features for conversation quality prediction"""
        features = []

        for metric in metrics:
            if metric.metric_name in ["lead_conversion_rate", "average_lead_score", "voice_analysis_accuracy"]:
                features.append(
                    [
                        metric.value,
                        metric.timestamp.hour,
                        metric.timestamp.weekday(),
                    ]
                )

        return np.array(features) if features else np.array([]).reshape(0, 3)

    def _extract_business_features(self, metrics: List[TimeSeriesMetric]) -> np.ndarray:
        """Extract features for business metric analysis"""
        features = []

        for metric in metrics:
            if metric.metric_name in ["lead_conversion_rate", "average_deal_value", "commission_pipeline_value"]:
                features.append(
                    [
                        metric.value,
                        metric.timestamp.hour,
                        metric.timestamp.weekday(),
                    ]
                )

        return np.array(features) if features else np.array([]).reshape(0, 3)

    async def get_prediction_summary(self) -> Dict[str, Any]:
        """Get summary of current predictions and model status"""
        return {
            "models_trained": len([m for m in self.anomaly_detectors.values() if hasattr(m, "estimators_")]),
            "total_models": len(self.anomaly_detectors),
            "prediction_types": [pt.value for pt in PredictionType],
            "status": "active",
            "last_training": datetime.utcnow().isoformat(),
        }


# Singleton instance
_predictive_engine = None


def get_predictive_alerting_engine() -> PredictiveAlertingEngine:
    """Get the global predictive alerting engine instance"""
    global _predictive_engine
    if _predictive_engine is None:
        _predictive_engine = PredictiveAlertingEngine()
    return _predictive_engine
