"""
Enterprise Compliance Platform - Anomaly Detection

Statistical anomaly detection for compliance violations using z-scores,
IQR bounds, and trend analysis. No heavy ML dependencies.
"""

import statistics
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    """Types of compliance anomalies that can be detected"""

    SCORE_SPIKE = "score_spike"
    SCORE_DROP = "score_drop"
    VIOLATION_SURGE = "violation_surge"
    UNUSUAL_PATTERN = "unusual_pattern"
    ASSESSMENT_GAP = "assessment_gap"
    RISK_ESCALATION = "risk_escalation"
    REMEDIATION_STALL = "remediation_stall"


class AnomalySeverity(str, Enum):
    """Severity levels for detected anomalies"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceAnomaly(BaseModel):
    """A detected compliance anomaly with investigation recommendations"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    model_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    deviation: Optional[float] = None  # Standard deviations from mean
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    recommended_investigation: List[str] = Field(default_factory=list)
    related_events: List[str] = Field(default_factory=list)

    def to_alert_payload(self) -> Dict[str, Any]:
        """Format anomaly for alerting systems"""
        return {
            "anomaly_id": self.id,
            "model_id": self.model_id,
            "type": self.anomaly_type.value,
            "severity": self.severity.value,
            "timestamp": self.detected_at.isoformat(),
            "description": self.description,
            "deviation": self.deviation,
            "confidence": self.confidence,
            "actions": self.recommended_investigation,
        }


class AnomalyDetectionConfig(BaseModel):
    """Configuration for anomaly detection thresholds"""

    score_change_threshold: float = Field(default=15.0, description="% change to flag")
    violation_surge_threshold: int = Field(default=3, description="violations in period to flag")
    assessment_gap_days: int = Field(default=30, description="days without assessment to flag")
    z_score_threshold: float = Field(default=2.5, description="standard deviations for outlier")
    min_history_points: int = Field(default=5, description="minimum data points for statistics")
    remediation_stall_days: int = Field(default=14, description="days without progress to flag")
    risk_escalation_threshold: int = Field(default=2, description="risk level jumps to flag")
    iqr_multiplier: float = Field(default=1.5, description="IQR multiplier for outlier detection")


class ComplianceAnomalyDetector:
    """
    Detects anomalies in compliance data using statistical methods.
    No heavy ML dependencies - uses z-scores, IQR, and trend analysis.
    """

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        self.config = config or AnomalyDetectionConfig()
        self._baselines: Dict[str, Dict[str, float]] = {}  # model_id -> metric baselines

    async def detect_anomalies(
        self,
        model_id: str,
        current_metrics: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
    ) -> List[ComplianceAnomaly]:
        """
        Run all anomaly detection checks for a model.

        Args:
            model_id: The ID of the model being analyzed
            current_metrics: Current compliance metrics for the model
            historical_data: List of historical metric snapshots

        Returns:
            List of detected anomalies
        """
        anomalies: List[ComplianceAnomaly] = []

        # Extract historical scores for score anomaly detection
        historical_scores = [
            h.get("compliance_score", h.get("score", 0.0))
            for h in historical_data
            if "compliance_score" in h or "score" in h
        ]
        current_score = current_metrics.get("compliance_score", current_metrics.get("score", 0.0))

        # 1. Score anomaly detection
        if historical_scores:
            score_anomaly = await self.detect_score_anomaly(model_id, current_score, historical_scores)
            if score_anomaly:
                anomalies.append(score_anomaly)

        # 2. Violation surge detection
        recent_violations = current_metrics.get("recent_violations", [])
        historical_violation_counts = [len(h.get("violations", [])) for h in historical_data if "violations" in h]
        if historical_violation_counts:
            avg_violation_rate = statistics.mean(historical_violation_counts) if historical_violation_counts else 0.0
            violation_anomaly = await self.detect_violation_surge(model_id, recent_violations, avg_violation_rate)
            if violation_anomaly:
                anomalies.append(violation_anomaly)

        # 3. Assessment gap detection
        last_assessment = current_metrics.get("last_assessment")
        if last_assessment:
            if isinstance(last_assessment, str):
                last_assessment = datetime.fromisoformat(last_assessment.replace("Z", "+00:00"))
            gap_anomaly = await self.detect_assessment_gap(model_id, last_assessment)
            if gap_anomaly:
                anomalies.append(gap_anomaly)

        # 4. Risk escalation detection
        risk_history = [
            {"risk_level": h.get("risk_level"), "timestamp": h.get("timestamp")}
            for h in historical_data
            if "risk_level" in h
        ]
        if risk_history:
            current_risk = current_metrics.get("risk_level")
            if current_risk:
                risk_history.append({"risk_level": current_risk, "timestamp": datetime.now(timezone.utc)})
            risk_anomaly = await self.detect_risk_escalation(model_id, risk_history)
            if risk_anomaly:
                anomalies.append(risk_anomaly)

        # 5. Remediation stall detection
        open_remediations = current_metrics.get("open_remediations", [])
        if open_remediations:
            stall_anomaly = await self.detect_remediation_stall(model_id, open_remediations)
            if stall_anomaly:
                anomalies.append(stall_anomaly)

        # 6. Pattern anomaly detection on key metrics
        for metric_name in ["fairness_score", "transparency_score", "robustness_score"]:
            values = [h.get(metric_name, 0.0) for h in historical_data if metric_name in h]
            timestamps = [h.get("timestamp", datetime.now(timezone.utc)) for h in historical_data if metric_name in h]
            if values and len(values) >= self.config.min_history_points:
                # Parse timestamps if they're strings
                parsed_timestamps = []
                for ts in timestamps:
                    if isinstance(ts, str):
                        parsed_timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                    else:
                        parsed_timestamps.append(ts)

                pattern_anomaly = await self.detect_pattern_anomaly(model_id, metric_name, values, parsed_timestamps)
                if pattern_anomaly:
                    anomalies.append(pattern_anomaly)

        return anomalies

    async def detect_score_anomaly(
        self,
        model_id: str,
        current_score: float,
        historical_scores: List[float],
    ) -> Optional[ComplianceAnomaly]:
        """
        Detect unusual score changes using z-score analysis.

        Args:
            model_id: The ID of the model
            current_score: Current compliance score
            historical_scores: List of historical compliance scores

        Returns:
            ComplianceAnomaly if anomaly detected, None otherwise
        """
        if len(historical_scores) < self.config.min_history_points:
            return None

        z_score = self._calculate_z_score(current_score, historical_scores)
        mean_score = statistics.mean(historical_scores)

        # Check for significant deviation
        if abs(z_score) < self.config.z_score_threshold:
            return None

        # Determine if it's a spike or drop
        if current_score > mean_score:
            anomaly_type = AnomalyType.SCORE_SPIKE
            description = (
                f"Compliance score spiked to {current_score:.1f}% "
                f"(expected around {mean_score:.1f}%, {abs(z_score):.1f} std devs above)"
            )
        else:
            anomaly_type = AnomalyType.SCORE_DROP
            description = (
                f"Compliance score dropped to {current_score:.1f}% "
                f"(expected around {mean_score:.1f}%, {abs(z_score):.1f} std devs below)"
            )

        severity = self._classify_severity(abs(z_score), anomaly_type)
        confidence = min(0.99, 0.5 + (abs(z_score) - self.config.z_score_threshold) * 0.1)

        investigation_steps = self._generate_investigation_steps_for_score(anomaly_type, current_score, mean_score)

        return ComplianceAnomaly(
            model_id=model_id,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            expected_value=mean_score,
            actual_value=current_score,
            deviation=z_score,
            confidence=confidence,
            recommended_investigation=investigation_steps,
        )

    async def detect_violation_surge(
        self,
        model_id: str,
        recent_violations: List[Dict[str, Any]],
        historical_rate: float,
    ) -> Optional[ComplianceAnomaly]:
        """
        Detect unusual increase in violations.

        Args:
            model_id: The ID of the model
            recent_violations: List of recent violation records
            historical_rate: Historical average violation rate

        Returns:
            ComplianceAnomaly if surge detected, None otherwise
        """
        current_count = len(recent_violations)

        # Check if violations exceed threshold and are significantly above historical rate
        if current_count < self.config.violation_surge_threshold:
            return None

        # If there's no historical baseline, any surge above threshold is notable
        if historical_rate == 0:
            multiplier = float("inf")
        else:
            multiplier = current_count / historical_rate

        # Need at least 2x historical rate or absolute threshold
        if multiplier < 2.0 and current_count < self.config.violation_surge_threshold * 2:
            return None

        # Analyze violation severities
        severity_counts: Dict[str, int] = {}
        for v in recent_violations:
            sev = v.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        critical_count = severity_counts.get("critical", 0)
        high_count = severity_counts.get("high", 0)

        description = (
            f"Violation surge detected: {current_count} violations "
            f"(historical average: {historical_rate:.1f}). "
            f"Includes {critical_count} critical and {high_count} high severity."
        )

        # Severity based on violation types
        if critical_count >= 2:
            severity = AnomalySeverity.CRITICAL
        elif critical_count >= 1 or high_count >= 3:
            severity = AnomalySeverity.HIGH
        elif multiplier > 3.0:
            severity = AnomalySeverity.HIGH
        else:
            severity = AnomalySeverity.MEDIUM

        confidence = min(0.99, 0.7 + (multiplier - 2.0) * 0.05)

        investigation_steps = [
            "Review all new violations and categorize by root cause",
            "Check for recent system changes or deployments",
            "Verify data quality and monitoring systems are functioning correctly",
            "Assess if violations are correlated or independent events",
            f"Prioritize {critical_count + high_count} critical/high severity violations",
        ]

        return ComplianceAnomaly(
            model_id=model_id,
            anomaly_type=AnomalyType.VIOLATION_SURGE,
            severity=severity,
            description=description,
            expected_value=historical_rate,
            actual_value=float(current_count),
            deviation=multiplier if historical_rate > 0 else None,
            confidence=confidence,
            recommended_investigation=investigation_steps,
            related_events=[v.get("violation_id", str(i)) for i, v in enumerate(recent_violations[:5])],
        )

    async def detect_assessment_gap(
        self,
        model_id: str,
        last_assessment: datetime,
    ) -> Optional[ComplianceAnomaly]:
        """
        Detect models that haven't been assessed recently.

        Args:
            model_id: The ID of the model
            last_assessment: Datetime of the last compliance assessment

        Returns:
            ComplianceAnomaly if gap exceeds threshold, None otherwise
        """
        now = datetime.now(timezone.utc)

        # Ensure last_assessment is timezone-aware
        if last_assessment.tzinfo is None:
            last_assessment = last_assessment.replace(tzinfo=timezone.utc)

        days_since = (now - last_assessment).days

        if days_since < self.config.assessment_gap_days:
            return None

        # Severity escalates with gap length
        if days_since >= self.config.assessment_gap_days * 3:
            severity = AnomalySeverity.CRITICAL
        elif days_since >= self.config.assessment_gap_days * 2:
            severity = AnomalySeverity.HIGH
        elif days_since >= self.config.assessment_gap_days * 1.5:
            severity = AnomalySeverity.MEDIUM
        else:
            severity = AnomalySeverity.LOW

        description = (
            f"Model has not been assessed for {days_since} days "
            f"(threshold: {self.config.assessment_gap_days} days). "
            f"Last assessment: {last_assessment.strftime('%Y-%m-%d')}."
        )

        confidence = min(0.99, 0.8 + (days_since / self.config.assessment_gap_days - 1) * 0.05)

        investigation_steps = [
            "Schedule immediate compliance assessment",
            "Review any changes made since last assessment",
            "Check if model is still in active use",
            "Verify assessment scheduling system is operational",
            "Update risk profile based on assessment gap",
        ]

        return ComplianceAnomaly(
            model_id=model_id,
            anomaly_type=AnomalyType.ASSESSMENT_GAP,
            severity=severity,
            description=description,
            expected_value=float(self.config.assessment_gap_days),
            actual_value=float(days_since),
            deviation=days_since / self.config.assessment_gap_days,
            confidence=confidence,
            recommended_investigation=investigation_steps,
        )

    async def detect_risk_escalation(
        self,
        model_id: str,
        risk_history: List[Dict[str, Any]],
    ) -> Optional[ComplianceAnomaly]:
        """
        Detect rapid risk level increases.

        Args:
            model_id: The ID of the model
            risk_history: List of historical risk level records with timestamps

        Returns:
            ComplianceAnomaly if rapid escalation detected, None otherwise
        """
        if len(risk_history) < 2:
            return None

        # Define risk level ordering (lower is better)
        risk_order = {
            "minimal": 0,
            "limited": 1,
            "low": 1,
            "medium": 2,
            "high": 3,
            "unacceptable": 4,
            "critical": 4,
            "unknown": 2,
        }

        # Sort by timestamp and get recent history
        def parse_timestamp(ts: Any) -> datetime:
            """Parse timestamp that may be string or datetime."""
            if ts is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            if isinstance(ts, str):
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    return ts.replace(tzinfo=timezone.utc)
                return ts
            return datetime.min.replace(tzinfo=timezone.utc)

        sorted_history = sorted(
            risk_history,
            key=lambda x: parse_timestamp(x.get("timestamp")),
        )

        # Check the last few entries for escalation
        recent = sorted_history[-3:] if len(sorted_history) >= 3 else sorted_history

        risk_levels = [risk_order.get(str(r.get("risk_level", "unknown")).lower(), 2) for r in recent]

        # Check for significant jump
        if len(risk_levels) < 2:
            return None

        max_jump = max(risk_levels[i] - risk_levels[i - 1] for i in range(1, len(risk_levels)))

        if max_jump < self.config.risk_escalation_threshold:
            return None

        current_level = recent[-1].get("risk_level", "unknown")
        previous_level = recent[-2].get("risk_level", "unknown")

        # Severity based on current risk level
        if current_level in ["unacceptable", "critical"]:
            severity = AnomalySeverity.CRITICAL
        elif current_level == "high":
            severity = AnomalySeverity.HIGH
        else:
            severity = AnomalySeverity.MEDIUM

        description = (
            f"Rapid risk escalation detected: {previous_level} -> {current_level} "
            f"(jumped {max_jump} level(s) in recent period)."
        )

        confidence = min(0.95, 0.7 + max_jump * 0.1)

        investigation_steps = [
            f"Identify root cause of risk escalation from {previous_level} to {current_level}",
            "Review recent changes to model or data sources",
            "Assess compliance controls that may have degraded",
            "Evaluate if risk escalation impacts downstream systems",
            "Consider temporary risk mitigation measures",
        ]

        return ComplianceAnomaly(
            model_id=model_id,
            anomaly_type=AnomalyType.RISK_ESCALATION,
            severity=severity,
            description=description,
            expected_value=float(risk_order.get(str(previous_level).lower(), 2)),
            actual_value=float(risk_order.get(str(current_level).lower(), 2)),
            deviation=float(max_jump),
            confidence=confidence,
            recommended_investigation=investigation_steps,
        )

    async def detect_remediation_stall(
        self,
        model_id: str,
        open_remediations: List[Dict[str, Any]],
    ) -> Optional[ComplianceAnomaly]:
        """
        Detect stalled remediation efforts.

        Args:
            model_id: The ID of the model
            open_remediations: List of open remediation action records

        Returns:
            ComplianceAnomaly if stalled remediations detected, None otherwise
        """
        now = datetime.now(timezone.utc)
        stalled_items: List[Dict[str, Any]] = []

        for remediation in open_remediations:
            status = remediation.get("status", "").lower()

            # Skip completed or verified items
            if status in ["completed", "verified"]:
                continue

            # Check for stalled items
            last_update = remediation.get("last_updated") or remediation.get("assigned_at")
            if not last_update:
                continue

            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update.replace("Z", "+00:00"))

            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)

            days_stalled = (now - last_update).days

            if days_stalled >= self.config.remediation_stall_days:
                stalled_items.append(
                    {
                        **remediation,
                        "days_stalled": days_stalled,
                    }
                )

        if not stalled_items:
            return None

        # Check for overdue items
        overdue_items = [
            r
            for r in stalled_items
            if r.get("due_date")
            and (
                datetime.fromisoformat(str(r["due_date"]).replace("Z", "+00:00"))
                if isinstance(r["due_date"], str)
                else r["due_date"]
            )
            < now
        ]

        # Severity based on overdue count and severity of stalled items
        critical_stalled = sum(
            1 for r in stalled_items if r.get("priority", 5) <= 1 or r.get("severity", "").lower() == "critical"
        )

        if critical_stalled >= 2 or len(overdue_items) >= 3:
            severity = AnomalySeverity.CRITICAL
        elif critical_stalled >= 1 or len(overdue_items) >= 1:
            severity = AnomalySeverity.HIGH
        elif len(stalled_items) >= 3:
            severity = AnomalySeverity.MEDIUM
        else:
            severity = AnomalySeverity.LOW

        max_stall_days = max(r.get("days_stalled", 0) for r in stalled_items)

        description = (
            f"{len(stalled_items)} remediation action(s) stalled for "
            f"{self.config.remediation_stall_days}+ days. "
            f"{len(overdue_items)} are overdue. Longest stall: {max_stall_days} days."
        )

        confidence = min(0.95, 0.75 + len(stalled_items) * 0.05)

        investigation_steps = [
            "Review resource allocation for stalled remediations",
            "Identify and escalate blockers preventing progress",
            f"Prioritize {len(overdue_items)} overdue items for immediate attention",
            "Consider reassigning items if assignees are unavailable",
            "Update remediation timelines with realistic estimates",
        ]

        return ComplianceAnomaly(
            model_id=model_id,
            anomaly_type=AnomalyType.REMEDIATION_STALL,
            severity=severity,
            description=description,
            expected_value=float(self.config.remediation_stall_days),
            actual_value=float(max_stall_days),
            deviation=max_stall_days / self.config.remediation_stall_days,
            confidence=confidence,
            recommended_investigation=investigation_steps,
            related_events=[r.get("action_id", str(i)) for i, r in enumerate(stalled_items[:5])],
        )

    async def detect_pattern_anomaly(
        self,
        model_id: str,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
    ) -> Optional[ComplianceAnomaly]:
        """
        Detect unusual patterns in time series data using IQR and trend analysis.

        Args:
            model_id: The ID of the model
            metric_name: Name of the metric being analyzed
            values: List of metric values
            timestamps: List of timestamps corresponding to values

        Returns:
            ComplianceAnomaly if unusual pattern detected, None otherwise
        """
        if len(values) < self.config.min_history_points:
            return None

        # Check for outliers using IQR
        lower_bound, upper_bound = self._calculate_iqr_bounds(values)
        latest_value = values[-1]

        is_outlier = latest_value < lower_bound or latest_value > upper_bound

        # Check for trend break
        trend_break_idx = self._detect_trend_break(values)

        if not is_outlier and trend_break_idx is None:
            return None

        mean_value = statistics.mean(values)
        z_score = self._calculate_z_score(latest_value, values[:-1]) if len(values) > 1 else 0

        if is_outlier:
            if latest_value < lower_bound:
                description = (
                    f"Unusual low value detected for {metric_name}: {latest_value:.2f} "
                    f"(IQR bounds: {lower_bound:.2f} - {upper_bound:.2f})"
                )
            else:
                description = (
                    f"Unusual high value detected for {metric_name}: {latest_value:.2f} "
                    f"(IQR bounds: {lower_bound:.2f} - {upper_bound:.2f})"
                )
        else:
            description = (
                f"Trend break detected in {metric_name} at index {trend_break_idx}. "
                f"Current value: {latest_value:.2f}, historical mean: {mean_value:.2f}"
            )

        severity = self._classify_severity(abs(z_score) if is_outlier else 2.0, AnomalyType.UNUSUAL_PATTERN)
        confidence = min(0.90, 0.6 + abs(z_score) * 0.1) if is_outlier else 0.7

        investigation_steps = [
            f"Review recent changes affecting {metric_name}",
            "Check data quality and collection processes",
            "Compare with other related metrics for correlation",
            "Assess if pattern indicates systemic issue",
            "Document findings and update baseline if pattern is valid",
        ]

        return ComplianceAnomaly(
            model_id=model_id,
            anomaly_type=AnomalyType.UNUSUAL_PATTERN,
            severity=severity,
            description=description,
            expected_value=mean_value,
            actual_value=latest_value,
            deviation=z_score,
            confidence=confidence,
            recommended_investigation=investigation_steps,
        )

    # Statistical methods

    def _calculate_z_score(self, value: float, values: List[float]) -> float:
        """
        Calculate z-score for a value relative to a distribution.

        Args:
            value: The value to calculate z-score for
            values: The reference distribution

        Returns:
            Z-score (standard deviations from mean)
        """
        if len(values) < 2:
            return 0.0

        mean = statistics.mean(values)
        try:
            stdev = statistics.stdev(values)
        except statistics.StatisticsError:
            return 0.0

        if stdev == 0:
            return 0.0

        return (value - mean) / stdev

    def _calculate_iqr_bounds(self, values: List[float]) -> Tuple[float, float]:
        """
        Calculate IQR-based outlier bounds.

        Args:
            values: List of values

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if len(values) < 4:
            # Not enough data for meaningful IQR
            return float("-inf"), float("inf")

        sorted_values = sorted(values)
        n = len(sorted_values)

        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = (3 * n) // 4

        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]

        iqr = q3 - q1

        lower_bound = q1 - self.config.iqr_multiplier * iqr
        upper_bound = q3 + self.config.iqr_multiplier * iqr

        return lower_bound, upper_bound

    def _detect_trend_break(self, values: List[float]) -> Optional[int]:
        """
        Detect point where trend significantly changes using simple slope analysis.

        Args:
            values: List of values in chronological order

        Returns:
            Index where trend breaks, or None if no significant break
        """
        if len(values) < 8:
            return None

        # Need significant data range to detect meaningful breaks
        value_range = max(values) - min(values)
        if value_range < 5.0:  # Less than 5 units of variation - no significant pattern
            return None

        # Calculate rolling slopes over a larger window
        window = 3
        slopes = []

        for i in range(len(values) - window + 1):
            window_values = values[i : i + window]
            # Simple slope as last - first
            slope = (window_values[-1] - window_values[0]) / (window - 1)
            slopes.append(slope)

        if len(slopes) < 4:
            return None

        # Require sustained trend before and after break
        # Find significant slope reversals where both before and after are substantial
        for i in range(2, len(slopes) - 1):
            # Check for sign reversal with significant magnitude
            before_slopes = slopes[max(0, i - 2) : i]
            after_slopes = slopes[i : min(len(slopes), i + 2)]

            # Both periods need consistent direction
            before_avg = statistics.mean(before_slopes)
            after_avg = statistics.mean(after_slopes)

            # Sign change with meaningful magnitudes
            if before_avg * after_avg < 0:  # Sign change
                # Both need substantial slopes (not just noise)
                min_slope_threshold = value_range * 0.1  # At least 10% of range per point
                if abs(before_avg) > min_slope_threshold and abs(after_avg) > min_slope_threshold:
                    # Significant reversal
                    magnitude_change = abs(after_avg - before_avg)
                    if magnitude_change > value_range * 0.15:  # At least 15% of range
                        return i + window - 1  # Return index in original values

        return None

    def _calculate_baseline(self, model_id: str, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate baseline metrics for a model from historical data.

        Args:
            model_id: The ID of the model
            historical_data: List of historical metric snapshots

        Returns:
            Dictionary of baseline metric values
        """
        baseline: Dict[str, float] = {}

        metric_keys = [
            "compliance_score",
            "score",
            "fairness_score",
            "transparency_score",
            "robustness_score",
            "privacy_score",
            "security_score",
            "risk_score",
        ]

        for key in metric_keys:
            values = [h.get(key, 0.0) for h in historical_data if key in h]
            if values:
                baseline[key] = statistics.mean(values)
                baseline[f"{key}_stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0

        # Cache the baseline
        self._baselines[model_id] = baseline

        return baseline

    # Severity classification

    def _classify_severity(self, deviation: float, anomaly_type: AnomalyType) -> AnomalySeverity:
        """
        Classify anomaly severity based on deviation and type.

        Args:
            deviation: Statistical deviation (z-score or multiplier)
            anomaly_type: Type of anomaly detected

        Returns:
            Appropriate severity level
        """
        # Type-specific severity multipliers
        type_severity_boost = {
            AnomalyType.SCORE_DROP: 1.2,  # Score drops are more concerning
            AnomalyType.VIOLATION_SURGE: 1.3,
            AnomalyType.RISK_ESCALATION: 1.4,
            AnomalyType.ASSESSMENT_GAP: 0.8,  # Less immediately critical
            AnomalyType.REMEDIATION_STALL: 0.9,
            AnomalyType.SCORE_SPIKE: 0.7,  # Improvements are less urgent
            AnomalyType.UNUSUAL_PATTERN: 1.0,
        }

        adjusted_deviation = deviation * type_severity_boost.get(anomaly_type, 1.0)

        if adjusted_deviation >= 4.0:
            return AnomalySeverity.CRITICAL
        elif adjusted_deviation >= 3.0:
            return AnomalySeverity.HIGH
        elif adjusted_deviation >= 2.0:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def _generate_investigation_steps(self, anomaly: ComplianceAnomaly) -> List[str]:
        """
        Generate recommended investigation steps based on anomaly.

        Args:
            anomaly: The detected anomaly

        Returns:
            List of investigation steps
        """
        base_steps = [
            "Review recent changes to the model or system",
            "Check data quality and input validity",
            "Verify monitoring and alerting systems",
        ]

        type_specific_steps: Dict[AnomalyType, List[str]] = {
            AnomalyType.SCORE_SPIKE: [
                "Verify score calculation methodology",
                "Check for false positives in compliance checks",
            ],
            AnomalyType.SCORE_DROP: [
                "Identify specific compliance controls that degraded",
                "Review recent policy or configuration changes",
            ],
            AnomalyType.VIOLATION_SURGE: [
                "Categorize violations by root cause",
                "Assess impact and prioritize remediation",
            ],
            AnomalyType.ASSESSMENT_GAP: [
                "Schedule immediate compliance assessment",
                "Review assessment scheduling process",
            ],
            AnomalyType.RISK_ESCALATION: [
                "Identify root cause of risk increase",
                "Evaluate risk mitigation options",
            ],
            AnomalyType.REMEDIATION_STALL: [
                "Identify blockers for stalled items",
                "Reassess resource allocation",
            ],
            AnomalyType.UNUSUAL_PATTERN: [
                "Correlate with other metrics",
                "Document and investigate root cause",
            ],
        }

        return base_steps + type_specific_steps.get(anomaly.anomaly_type, [])

    def _generate_investigation_steps_for_score(
        self,
        anomaly_type: AnomalyType,
        current_score: float,
        expected_score: float,
    ) -> List[str]:
        """Generate investigation steps specific to score anomalies."""
        steps = []

        if anomaly_type == AnomalyType.SCORE_DROP:
            steps = [
                "Identify which compliance controls or metrics degraded",
                "Review recent system changes, deployments, or configuration updates",
                "Check for data quality issues affecting score calculation",
                "Assess impact of score drop on regulatory compliance status",
                f"Develop remediation plan to restore score above {expected_score:.1f}%",
            ]
        else:  # SCORE_SPIKE
            steps = [
                "Verify score calculation is accurate (rule out false positive)",
                "Document improvements that led to score increase",
                "Review if new baseline should be established",
                "Share best practices with other teams if improvements are valid",
                "Update compliance documentation to reflect improvements",
            ]

        return steps

    def get_baseline(self, model_id: str) -> Optional[Dict[str, float]]:
        """Get cached baseline for a model, if available."""
        return self._baselines.get(model_id)

    def clear_baseline(self, model_id: str) -> None:
        """Clear cached baseline for a model."""
        if model_id in self._baselines:
            del self._baselines[model_id]

    def clear_all_baselines(self) -> None:
        """Clear all cached baselines."""
        self._baselines.clear()
