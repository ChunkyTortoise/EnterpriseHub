"""
Validation framework for agent outputs and workflow results.

Provides schema validation, confidence scoring, and contradiction detection
to ensure data quality and logical consistency across agent outputs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd

from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ValidationResult:
    """Result from validation check."""

    passed: bool
    confidence: float  # 0.0 - 1.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conflict:
    """Detected conflict between agent results."""

    conflict_type: str  # e.g., "SENTIMENT_MISMATCH", "VALUE_CONFLICT"
    agents: List[str]  # Agent IDs involved
    description: str
    severity: str = "WARNING"  # ERROR, WARNING, INFO
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Schema Validator
# ============================================================================


class SchemaValidator:
    """
    Validates data against predefined schemas.

    Checks required fields, type correctness, and value ranges.
    """

    def __init__(self) -> None:
        logger.info("SchemaValidator initialized")

    def validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            schema: Schema definition with keys:
                - required: List[str] - Required field names
                - types: Dict[str, type] - Field type specifications
                - ranges: Dict[str, Tuple[float, float]] - Numeric value ranges

        Returns:
            ValidationResult with pass/fail status and confidence score
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check required fields
        required = schema.get("required", [])
        missing_fields = self.check_required_fields(data, required)
        if missing_fields:
            errors.extend([f"Missing required field: {field}" for field in missing_fields])

        # Check types
        types = schema.get("types", {})
        type_errors = self.check_types(data, types)
        if type_errors:
            errors.extend(type_errors)

        # Check ranges
        ranges = schema.get("ranges", {})
        range_warnings = self.check_ranges(data, ranges)
        if range_warnings:
            warnings.extend(range_warnings)

        # Calculate confidence score
        # Perfect = 1.0, each error reduces by 0.3, each warning by 0.1
        confidence = 1.0 - (len(errors) * 0.3 + len(warnings) * 0.1)
        confidence = max(0.0, min(1.0, confidence))

        passed = len(errors) == 0

        logger.info(
            f"Validation: passed={passed}, confidence={confidence:.2f}, "
            f"errors={len(errors)}, warnings={len(warnings)}"
        )

        return ValidationResult(
            passed=passed,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            metadata={"checked_fields": len(data)},
        )

    def check_required_fields(self, data: Dict[str, Any], required: List[str]) -> List[str]:
        """
        Check for missing required fields.

        Args:
            data: Data to check
            required: List of required field names

        Returns:
            List of missing field names
        """
        missing = []
        for field_name in required:
            if field_name not in data:
                missing.append(field_name)
            elif data[field_name] is None:
                missing.append(field_name)  # None values count as missing
        return missing

    def check_types(self, data: Dict[str, Any], type_specs: Dict[str, type]) -> List[str]:
        """
        Check field types against expected types.

        Args:
            data: Data to check
            type_specs: Dict mapping field names to expected types

        Returns:
            List of type error messages
        """
        errors = []
        for field_name, expected_type in type_specs.items():
            if field_name not in data:
                continue  # Skip missing fields (handled by required check)

            value = data[field_name]
            if value is None:
                continue  # None is valid for any type

            # Special handling for pandas DataFrames
            if expected_type == pd.DataFrame:
                if not isinstance(value, pd.DataFrame):
                    errors.append(
                        f"Field '{field_name}' expected DataFrame, " f"got {type(value).__name__}"
                    )
            # Standard type checking
            elif not isinstance(value, expected_type):
                errors.append(
                    f"Field '{field_name}' expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

        return errors

    def check_ranges(
        self, data: Dict[str, Any], ranges: Dict[str, Tuple[float, float]]
    ) -> List[str]:
        """
        Check numeric values are within expected ranges.

        Args:
            data: Data to check
            ranges: Dict mapping field names to (min, max) tuples

        Returns:
            List of range warning messages
        """
        warnings = []
        for field_name, (min_val, max_val) in ranges.items():
            if field_name not in data:
                continue

            value = data[field_name]
            if value is None:
                continue

            # Try to convert to float for comparison
            try:
                numeric_value = float(value)
                if not (min_val <= numeric_value <= max_val):
                    warnings.append(
                        f"Field '{field_name}' value {numeric_value:.2f} outside "
                        f"expected range [{min_val}, {max_val}]"
                    )
            except (ValueError, TypeError):
                warnings.append(f"Field '{field_name}' cannot be validated as numeric")

        return warnings


# ============================================================================
# Confidence Scorer
# ============================================================================


class ConfidenceScorer:
    """
    Calculates confidence scores for data quality and completeness.

    Scores are in range [0.0, 1.0] where 1.0 = perfect confidence.
    """

    def __init__(self) -> None:
        logger.info("ConfidenceScorer initialized")

    def score_data_quality(self, df: pd.DataFrame) -> float:
        """
        Score DataFrame quality based on completeness, freshness, and size.

        Args:
            df: DataFrame to score

        Returns:
            Quality score [0.0, 1.0]
        """
        if df is None or df.empty:
            return 0.0

        scores = []

        # 1. Completeness: % of non-null values
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.notna().sum().sum()
        completeness = non_null_cells / total_cells if total_cells > 0 else 0.0
        scores.append(completeness)

        # 2. Freshness: recency of data (for time-indexed data)
        if isinstance(df.index, pd.DatetimeIndex) and len(df) > 0:
            days_old = (datetime.now() - df.index.max()).days
            # Decay over 30 days: 0 days = 1.0, 30 days = 0.0
            freshness = max(0.0, 1.0 - (days_old / 30.0))
            scores.append(freshness)
        else:
            scores.append(0.8)  # Default score if no timestamp

        # 3. Size: more data generally better (up to 252 rows = 1 trading year)
        row_score = min(1.0, len(df) / 252.0)
        scores.append(row_score)

        # Aggregate: average of all scores
        quality_score = sum(scores) / len(scores)

        logger.info(
            f"Data quality score: {quality_score:.3f} "
            f"(completeness={completeness:.2f}, rows={len(df)})"
        )

        return quality_score

    def score_completeness(self, data: Dict[str, Any], schema: Dict[str, Any]) -> float:
        """
        Score how complete the data is relative to expected schema.

        Args:
            data: Data to score
            schema: Expected schema with 'required' and optional 'optional' fields

        Returns:
            Completeness score [0.0, 1.0]
        """
        required_fields = schema.get("required", [])
        optional_fields = schema.get("optional", [])
        all_fields = required_fields + optional_fields

        if not all_fields:
            return 1.0  # No schema defined, assume complete

        # Count present fields
        present_count = sum(1 for field in all_fields if field in data and data[field] is not None)
        completeness = present_count / len(all_fields)

        logger.info(
            f"Completeness score: {completeness:.3f} "
            f"({present_count}/{len(all_fields)} fields present)"
        )

        return completeness

    def score_freshness(self, timestamp: datetime, max_age_days: int = 7) -> float:
        """
        Score data freshness based on age.

        Args:
            timestamp: When data was generated
            max_age_days: Maximum age before score = 0.0

        Returns:
            Freshness score [0.0, 1.0]
        """
        age_days = (datetime.now() - timestamp).days
        freshness = max(0.0, 1.0 - (age_days / max_age_days))

        logger.info(f"Freshness score: {freshness:.3f} (age={age_days} days)")

        return freshness

    def score_source_reliability(self, source: str) -> float:
        """
        Score source reliability based on known sources.

        Args:
            source: Data source identifier (e.g., 'yfinance', 'manual', 'api')

        Returns:
            Reliability score [0.0, 1.0]
        """
        # Reliability rankings
        reliability_map = {
            "yfinance": 0.9,
            "yahoo_finance": 0.9,
            "api": 0.85,
            "database": 0.95,
            "manual": 0.7,
            "user_input": 0.6,
            "unknown": 0.5,
        }

        source_lower = source.lower()
        score = reliability_map.get(source_lower, 0.5)

        logger.info(f"Source reliability score: {score:.2f} (source={source})")

        return score

    def aggregate_confidence(self, scores: List[float]) -> float:
        """
        Aggregate multiple confidence scores into single score.

        Uses harmonic mean to be sensitive to low scores.

        Args:
            scores: List of confidence scores [0.0, 1.0]

        Returns:
            Aggregated confidence score [0.0, 1.0]
        """
        if not scores:
            return 0.0

        # Filter out zero scores to avoid division by zero
        non_zero_scores = [s for s in scores if s > 0]

        if not non_zero_scores:
            return 0.0

        # Harmonic mean: n / sum(1/x_i)
        # More sensitive to low values than arithmetic mean
        harmonic_mean = len(non_zero_scores) / sum(1 / s for s in non_zero_scores)

        logger.info(f"Aggregated confidence: {harmonic_mean:.3f} from {len(scores)} scores")

        return harmonic_mean


# ============================================================================
# Contradiction Detector
# ============================================================================


class ContradictionDetector:
    """
    Detects logical contradictions and conflicts between agent results.

    Identifies cases where different agents provide conflicting signals or recommendations.
    """

    def __init__(self) -> None:
        self.bullish_terms = ["BULLISH", "Bullish", "Positive", "BUY", "STRONG BUY"]
        self.bearish_terms = ["BEARISH", "Bearish", "Negative", "SELL", "STRONG SELL"]
        logger.info("ContradictionDetector initialized")

    def compare_numeric_values(self, val1: float, val2: float, tolerance: float = 0.1) -> bool:
        """
        Compare two numeric values with tolerance.

        Args:
            val1: First value
            val2: Second value
            tolerance: Relative tolerance (0.1 = 10% difference)

        Returns:
            True if values contradict (differ by more than tolerance)
        """
        if val1 == 0 or val2 == 0:
            return abs(val1 - val2) > tolerance  # Absolute difference for zeros

        relative_diff = abs(val1 - val2) / max(abs(val1), abs(val2))
        contradicts = relative_diff > tolerance

        if contradicts:
            logger.warning(
                f"Numeric contradiction: {val1:.2f} vs {val2:.2f} " f"(diff={relative_diff:.1%})"
            )

        return contradicts

    def compare_sentiments(self, sent1: str, sent2: str) -> bool:
        """
        Check if two sentiment signals contradict.

        Args:
            sent1: First sentiment (e.g., "BULLISH", "Positive")
            sent2: Second sentiment (e.g., "BEARISH", "Negative")

        Returns:
            True if sentiments contradict
        """
        is_sent1_bullish = any(term in sent1 for term in self.bullish_terms)
        is_sent1_bearish = any(term in sent1 for term in self.bearish_terms)
        is_sent2_bullish = any(term in sent2 for term in self.bullish_terms)
        is_sent2_bearish = any(term in sent2 for term in self.bearish_terms)

        # Contradiction if one is bullish and other is bearish
        contradicts = (is_sent1_bullish and is_sent2_bearish) or (
            is_sent1_bearish and is_sent2_bullish
        )

        if contradicts:
            logger.warning(f"Sentiment contradiction: '{sent1}' vs '{sent2}'")

        return contradicts

    def compare_recommendations(self, rec1: str, rec2: str) -> bool:
        """
        Check if two recommendations contradict.

        Args:
            rec1: First recommendation
            rec2: Second recommendation

        Returns:
            True if recommendations contradict
        """
        # Use same logic as sentiment comparison
        return self.compare_sentiments(rec1, rec2)

    def detect_logical_conflicts(self, results: Dict[str, Any]) -> List[Conflict]:
        """
        Detect logical conflicts across all agent results.

        Args:
            results: Dict of agent results keyed by agent_id or result type

        Returns:
            List of detected conflicts
        """
        conflicts: List[Conflict] = []

        # 1. Check technical vs sentiment agreement
        if "technical" in results and "sentiment" in results:
            tech = results["technical"]
            sent = results["sentiment"]

            # Compare MACD signal with sentiment verdict
            tech_signal = tech.get("macd_signal", "")
            sent_verdict = sent.get("verdict", "")

            if tech_signal and sent_verdict:
                if self.compare_sentiments(tech_signal, sent_verdict):
                    conflicts.append(
                        Conflict(
                            conflict_type="TECHNICAL_SENTIMENT_MISMATCH",
                            agents=["tech_bot", "sentiment_bot"],
                            description=(
                                f"Technical indicator ({tech_signal}) contradicts "
                                f"news sentiment ({sent_verdict})"
                            ),
                            severity="WARNING",
                            details={
                                "technical_signal": tech_signal,
                                "sentiment_verdict": sent_verdict,
                            },
                        )
                    )

        # 2. Check forecast vs current trend
        if "forecast" in results and "technical" in results:
            forecast = results["forecast"]
            tech = results["technical"]

            forecast_trend = forecast.get("trend", "")
            tech_signal = tech.get("macd_signal", "")

            if forecast_trend and tech_signal:
                if self.compare_sentiments(forecast_trend, tech_signal):
                    conflicts.append(
                        Conflict(
                            conflict_type="FORECAST_TREND_MISMATCH",
                            agents=["forecast_bot", "tech_bot"],
                            description=(
                                f"Forecast trend ({forecast_trend}) contradicts "
                                f"current technical signal ({tech_signal})"
                            ),
                            severity="INFO",
                            details={
                                "forecast_trend": forecast_trend,
                                "technical_signal": tech_signal,
                            },
                        )
                    )

        # 3. Check data quality vs confidence
        if "data_quality" in results and "confidence" in results:
            quality = results["data_quality"]
            confidence = results["confidence"]

            # Low quality with high confidence is suspicious
            if quality < 0.5 and confidence > 0.8:
                conflicts.append(
                    Conflict(
                        conflict_type="QUALITY_CONFIDENCE_MISMATCH",
                        agents=["data_bot", "synthesis_bot"],
                        description=(
                            f"Low data quality ({quality:.2f}) but high "
                            f"confidence ({confidence:.2f})"
                        ),
                        severity="WARNING",
                        details={"quality": quality, "confidence": confidence},
                    )
                )

        logger.info(f"Detected {len(conflicts)} conflicts across agent results")

        return conflicts
