"""Unit tests for the validators module.

Tests SchemaValidator, ConfidenceScorer, and ContradictionDetector classes
for data validation, quality scoring, and conflict detection.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd
import pytest

from utils.validators import (
    ConfidenceScorer,
    Conflict,
    ContradictionDetector,
    SchemaValidator,
    ValidationResult,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    # Use recent dates to ensure high freshness score
    dates = pd.date_range(end=datetime.now(), periods=252, freq="D")
    data = {
        "Close": [100.0 + i * 0.5 for i in range(252)],
        "Volume": [1000000 + i * 1000 for i in range(252)],
        "Open": [99.0 + i * 0.5 for i in range(252)],
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def sparse_dataframe() -> pd.DataFrame:
    """Create a DataFrame with missing values."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    data = {
        "Close": [100.0 if i % 3 == 0 else None for i in range(100)],
        "Volume": [1000000 if i % 2 == 0 else None for i in range(100)],
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def old_dataframe() -> pd.DataFrame:
    """Create a DataFrame with old data (45 days ago)."""
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=45),
        end=datetime.now() - timedelta(days=15),
        freq="D",
    )
    data = {"Close": [100.0] * len(dates)}
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def schema_validator() -> SchemaValidator:
    """Create a SchemaValidator instance."""
    return SchemaValidator()


@pytest.fixture
def confidence_scorer() -> ConfidenceScorer:
    """Create a ConfidenceScorer instance."""
    return ConfidenceScorer()


@pytest.fixture
def contradiction_detector() -> ContradictionDetector:
    """Create a ContradictionDetector instance."""
    return ContradictionDetector()


# ============================================================================
# SchemaValidator Tests
# ============================================================================


class TestSchemaValidator:
    """Tests for SchemaValidator class."""

    def test_validate_success_all_fields_present(self, schema_validator: SchemaValidator) -> None:
        """Test validation succeeds when all required fields are present."""
        data = {"ticker": "AAPL", "period": "1y", "confidence": 0.85}
        schema = {
            "required": ["ticker", "period"],
            "types": {"ticker": str, "period": str, "confidence": float},
        }

        result = schema_validator.validate(data, schema)

        assert result.passed is True
        assert result.confidence == 1.0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_missing_required_field(self, schema_validator: SchemaValidator) -> None:
        """Test validation fails when required field is missing."""
        data = {"ticker": "AAPL"}
        schema = {"required": ["ticker", "period"]}

        result = schema_validator.validate(data, schema)

        assert result.passed is False
        assert "Missing required field: period" in result.errors
        assert result.confidence < 1.0

    def test_validate_none_value_counts_as_missing(self, schema_validator: SchemaValidator) -> None:
        """Test that None values are treated as missing fields."""
        data = {"ticker": "AAPL", "period": None}
        schema = {"required": ["ticker", "period"]}

        result = schema_validator.validate(data, schema)

        assert result.passed is False
        assert "Missing required field: period" in result.errors

    def test_validate_type_error(self, schema_validator: SchemaValidator) -> None:
        """Test validation detects type mismatches."""
        data = {"ticker": "AAPL", "confidence": "high"}  # Should be float
        schema = {"types": {"ticker": str, "confidence": float}}

        result = schema_validator.validate(data, schema)

        assert result.passed is False
        assert any("confidence" in err and "float" in err for err in result.errors)

    def test_validate_dataframe_type(self, schema_validator: SchemaValidator) -> None:
        """Test validation handles pandas DataFrame type correctly."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        data = {"df": df, "ticker": "AAPL"}
        schema = {"types": {"df": pd.DataFrame, "ticker": str}}

        result = schema_validator.validate(data, schema)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_validate_dataframe_type_error(self, schema_validator: SchemaValidator) -> None:
        """Test validation fails when DataFrame type is incorrect."""
        data = {"df": {"not": "a dataframe"}, "ticker": "AAPL"}
        schema = {"types": {"df": pd.DataFrame}}

        result = schema_validator.validate(data, schema)

        assert result.passed is False
        assert any("DataFrame" in err for err in result.errors)

    def test_validate_range_warning(self, schema_validator: SchemaValidator) -> None:
        """Test validation generates warnings for out-of-range values."""
        data = {"confidence": 1.5}  # Should be [0.0, 1.0]
        schema = {"ranges": {"confidence": (0.0, 1.0)}}

        result = schema_validator.validate(data, schema)

        assert result.passed is True  # Ranges only generate warnings
        assert len(result.warnings) > 0
        assert any("confidence" in warn and "range" in warn for warn in result.warnings)

    def test_validate_confidence_calculation(self, schema_validator: SchemaValidator) -> None:
        """Test confidence score calculation with errors and warnings."""
        data = {"ticker": "AAPL", "confidence": 1.5}
        schema = {
            "required": ["ticker", "period"],  # Missing 'period'
            "ranges": {"confidence": (0.0, 1.0)},  # Out of range
        }

        result = schema_validator.validate(data, schema)

        # 1 error (-0.3) + 1 warning (-0.1) = 0.6 confidence
        assert result.confidence == pytest.approx(0.6, abs=0.01)

    def test_check_required_fields_empty_list(self, schema_validator: SchemaValidator) -> None:
        """Test check_required_fields with no required fields."""
        data = {"ticker": "AAPL"}
        missing = schema_validator.check_required_fields(data, [])

        assert len(missing) == 0

    def test_check_types_none_value_allowed(self, schema_validator: SchemaValidator) -> None:
        """Test that None values pass type checking."""
        data = {"ticker": "AAPL", "optional_field": None}
        type_specs = {"ticker": str, "optional_field": float}

        errors = schema_validator.check_types(data, type_specs)

        assert len(errors) == 0

    def test_check_ranges_non_numeric_warning(self, schema_validator: SchemaValidator) -> None:
        """Test that non-numeric values generate range warnings."""
        data = {"confidence": "not_a_number"}
        ranges = {"confidence": (0.0, 1.0)}

        warnings = schema_validator.check_ranges(data, ranges)

        assert len(warnings) > 0
        assert any("numeric" in warn for warn in warnings)


# ============================================================================
# ConfidenceScorer Tests
# ============================================================================


class TestConfidenceScorer:
    """Tests for ConfidenceScorer class."""

    def test_score_data_quality_perfect(
        self, confidence_scorer: ConfidenceScorer, sample_dataframe: pd.DataFrame
    ) -> None:
        """Test quality score for perfect DataFrame (complete, fresh, full year)."""
        score = confidence_scorer.score_data_quality(sample_dataframe)

        assert score > 0.9  # Should be very high quality

    def test_score_data_quality_empty_dataframe(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test quality score for empty DataFrame."""
        df = pd.DataFrame()
        score = confidence_scorer.score_data_quality(df)

        assert score == 0.0

    def test_score_data_quality_none_dataframe(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test quality score for None DataFrame."""
        score = confidence_scorer.score_data_quality(None)

        assert score == 0.0

    def test_score_data_quality_sparse_data(
        self, confidence_scorer: ConfidenceScorer, sparse_dataframe: pd.DataFrame
    ) -> None:
        """Test quality score decreases with missing values."""
        complete_df = pd.DataFrame(
            {"Close": [100.0] * 100, "Volume": [1000000] * 100},
            index=pd.date_range(start="2024-01-01", periods=100, freq="D"),
        )

        sparse_score = confidence_scorer.score_data_quality(sparse_dataframe)
        complete_score = confidence_scorer.score_data_quality(complete_df)

        assert sparse_score < complete_score

    def test_score_data_quality_old_data(
        self, confidence_scorer: ConfidenceScorer, old_dataframe: pd.DataFrame
    ) -> None:
        """Test quality score decreases with old data."""
        score = confidence_scorer.score_data_quality(old_dataframe)

        # Old data (45 days) should have lower freshness score
        assert score < 0.9

    def test_score_data_quality_non_datetime_index(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test quality score with non-datetime index."""
        df = pd.DataFrame({"Close": [100.0] * 100})  # Default integer index

        score = confidence_scorer.score_data_quality(df)

        # Should still score reasonably well (defaults to 0.8 for freshness)
        assert score > 0.0

    def test_score_completeness_all_fields_present(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test completeness score when all fields are present."""
        data = {"ticker": "AAPL", "period": "1y", "optional_field": 123}
        schema = {"required": ["ticker", "period"], "optional": ["optional_field"]}

        score = confidence_scorer.score_completeness(data, schema)

        assert score == 1.0

    def test_score_completeness_missing_optional(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test completeness score with missing optional fields."""
        data = {"ticker": "AAPL", "period": "1y"}
        schema = {
            "required": ["ticker", "period"],
            "optional": ["field1", "field2", "field3"],
        }

        score = confidence_scorer.score_completeness(data, schema)

        # 2 present out of 5 total fields = 0.4
        assert score == pytest.approx(0.4, abs=0.01)

    def test_score_completeness_no_schema(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test completeness score with no schema defined."""
        data = {"ticker": "AAPL"}
        schema: Dict[str, Any] = {}

        score = confidence_scorer.score_completeness(data, schema)

        assert score == 1.0  # No schema means assume complete

    def test_score_freshness_recent_data(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test freshness score for very recent data."""
        timestamp = datetime.now() - timedelta(hours=1)
        score = confidence_scorer.score_freshness(timestamp, max_age_days=7)

        assert score > 0.9

    def test_score_freshness_old_data(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test freshness score for old data."""
        timestamp = datetime.now() - timedelta(days=10)
        score = confidence_scorer.score_freshness(timestamp, max_age_days=7)

        assert score == 0.0  # Older than max_age_days

    def test_score_freshness_halfway(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test freshness score for halfway through decay period."""
        timestamp = datetime.now() - timedelta(days=3.5)
        score = confidence_scorer.score_freshness(timestamp, max_age_days=7)

        # 3.5 days rounds to 3 days, so score = 1 - (3/7) = 0.571
        assert score == pytest.approx(0.571, abs=0.01)

    def test_score_source_reliability_known_sources(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test reliability scores for known data sources."""
        assert confidence_scorer.score_source_reliability("yfinance") == 0.9
        assert confidence_scorer.score_source_reliability("database") == 0.95
        assert confidence_scorer.score_source_reliability("manual") == 0.7
        assert confidence_scorer.score_source_reliability("user_input") == 0.6

    def test_score_source_reliability_unknown_source(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test reliability score for unknown data source."""
        score = confidence_scorer.score_source_reliability("random_source")

        assert score == 0.5  # Default for unknown

    def test_score_source_reliability_case_insensitive(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test that source reliability is case-insensitive."""
        assert confidence_scorer.score_source_reliability("YFINANCE") == 0.9
        assert confidence_scorer.score_source_reliability("YFinance") == 0.9

    def test_aggregate_confidence_harmonic_mean(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test harmonic mean aggregation of confidence scores."""
        scores = [0.9, 0.8, 0.7]
        aggregated = confidence_scorer.aggregate_confidence(scores)

        # Harmonic mean should be lower than arithmetic mean
        arithmetic_mean = sum(scores) / len(scores)
        assert aggregated < arithmetic_mean
        assert aggregated == pytest.approx(0.791, abs=0.01)

    def test_aggregate_confidence_empty_list(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test aggregation of empty score list."""
        aggregated = confidence_scorer.aggregate_confidence([])

        assert aggregated == 0.0

    def test_aggregate_confidence_with_zeros(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test aggregation filters out zero scores."""
        scores = [0.9, 0.0, 0.8]
        aggregated = confidence_scorer.aggregate_confidence(scores)

        # Should only aggregate non-zero scores [0.9, 0.8]
        assert aggregated > 0.0

    def test_aggregate_confidence_all_zeros(self, confidence_scorer: ConfidenceScorer) -> None:
        """Test aggregation of all zero scores."""
        scores = [0.0, 0.0, 0.0]
        aggregated = confidence_scorer.aggregate_confidence(scores)

        assert aggregated == 0.0


# ============================================================================
# ContradictionDetector Tests
# ============================================================================


class TestContradictionDetector:
    """Tests for ContradictionDetector class."""

    def test_compare_numeric_values_no_contradiction(self, contradiction_detector: ContradictionDetector) -> None:
        """Test numeric comparison with values within tolerance."""
        contradicts = contradiction_detector.compare_numeric_values(100.0, 105.0, 0.1)

        assert contradicts is False  # 5% difference, within 10% tolerance

    def test_compare_numeric_values_contradiction(self, contradiction_detector: ContradictionDetector) -> None:
        """Test numeric comparison with values exceeding tolerance."""
        contradicts = contradiction_detector.compare_numeric_values(100.0, 120.0, 0.1)

        assert contradicts is True  # 20% difference, exceeds 10% tolerance

    def test_compare_numeric_values_with_zero(self, contradiction_detector: ContradictionDetector) -> None:
        """Test numeric comparison when one value is zero."""
        contradicts = contradiction_detector.compare_numeric_values(0.0, 0.05, 0.1)

        assert contradicts is False  # Absolute difference 0.05 < 0.1

    def test_compare_sentiments_bullish_vs_bearish(self, contradiction_detector: ContradictionDetector) -> None:
        """Test sentiment contradiction between bullish and bearish."""
        contradicts = contradiction_detector.compare_sentiments("BULLISH", "BEARISH")

        assert contradicts is True

    def test_compare_sentiments_both_bullish(self, contradiction_detector: ContradictionDetector) -> None:
        """Test no contradiction when both sentiments are bullish."""
        contradicts = contradiction_detector.compare_sentiments("BULLISH", "BUY")

        assert contradicts is False

    def test_compare_sentiments_both_bearish(self, contradiction_detector: ContradictionDetector) -> None:
        """Test no contradiction when both sentiments are bearish."""
        contradicts = contradiction_detector.compare_sentiments("BEARISH", "SELL")

        assert contradicts is False

    def test_compare_sentiments_case_sensitive(self, contradiction_detector: ContradictionDetector) -> None:
        """Test sentiment comparison handles various cases."""
        assert contradiction_detector.compare_sentiments("Bullish", "Bearish") is True
        assert contradiction_detector.compare_sentiments("Positive", "Negative") is True

    def test_compare_recommendations(self, contradiction_detector: ContradictionDetector) -> None:
        """Test recommendation comparison uses sentiment logic."""
        assert contradiction_detector.compare_recommendations("STRONG BUY", "STRONG SELL") is True
        assert contradiction_detector.compare_recommendations("BUY", "HOLD") is False

    def test_detect_logical_conflicts_technical_sentiment_mismatch(
        self, contradiction_detector: ContradictionDetector
    ) -> None:
        """Test detection of technical vs sentiment contradiction."""
        results = {
            "technical": {"macd_signal": "BULLISH", "rsi_value": 75.0},
            "sentiment": {"verdict": "BEARISH", "confidence": 0.8},
        }

        conflicts = contradiction_detector.detect_logical_conflicts(results)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "TECHNICAL_SENTIMENT_MISMATCH"
        assert "tech_bot" in conflicts[0].agents
        assert "sentiment_bot" in conflicts[0].agents

    def test_detect_logical_conflicts_forecast_trend_mismatch(
        self, contradiction_detector: ContradictionDetector
    ) -> None:
        """Test detection of forecast vs technical trend contradiction."""
        results = {
            "forecast": {"trend": "BEARISH", "forecast_df": None},
            "technical": {"macd_signal": "BULLISH", "rsi_value": 65.0},
        }

        conflicts = contradiction_detector.detect_logical_conflicts(results)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "FORECAST_TREND_MISMATCH"

    def test_detect_logical_conflicts_quality_confidence_mismatch(
        self, contradiction_detector: ContradictionDetector
    ) -> None:
        """Test detection of low quality with high confidence."""
        results = {
            "data_quality": 0.3,  # Low quality
            "confidence": 0.9,  # High confidence
        }

        conflicts = contradiction_detector.detect_logical_conflicts(results)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "QUALITY_CONFIDENCE_MISMATCH"
        assert conflicts[0].severity == "WARNING"

    def test_detect_logical_conflicts_no_conflicts(self, contradiction_detector: ContradictionDetector) -> None:
        """Test no conflicts detected when all signals align."""
        results = {
            "technical": {"macd_signal": "BULLISH", "rsi_value": 65.0},
            "sentiment": {"verdict": "BULLISH", "confidence": 0.8},
            "data_quality": 0.9,
            "confidence": 0.85,
        }

        conflicts = contradiction_detector.detect_logical_conflicts(results)

        assert len(conflicts) == 0

    def test_detect_logical_conflicts_empty_results(self, contradiction_detector: ContradictionDetector) -> None:
        """Test no conflicts with empty results dict."""
        conflicts = contradiction_detector.detect_logical_conflicts({})

        assert len(conflicts) == 0


# ============================================================================
# ValidationResult Tests
# ============================================================================


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_creation(self) -> None:
        """Test ValidationResult can be created with all fields."""
        result = ValidationResult(
            passed=True,
            confidence=0.95,
            errors=["error1"],
            warnings=["warning1"],
            metadata={"key": "value"},
        )

        assert result.passed is True
        assert result.confidence == 0.95
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert result.metadata["key"] == "value"

    def test_validation_result_defaults(self) -> None:
        """Test ValidationResult default values."""
        result = ValidationResult(passed=False, confidence=0.5)

        assert result.errors == []
        assert result.warnings == []
        assert result.metadata == {}


# ============================================================================
# Conflict Tests
# ============================================================================


class TestConflict:
    """Tests for Conflict dataclass."""

    def test_conflict_creation(self) -> None:
        """Test Conflict can be created with all fields."""
        conflict = Conflict(
            conflict_type="TEST_CONFLICT",
            agents=["agent1", "agent2"],
            description="Test conflict description",
            severity="ERROR",
            details={"key": "value"},
        )

        assert conflict.conflict_type == "TEST_CONFLICT"
        assert len(conflict.agents) == 2
        assert conflict.severity == "ERROR"

    def test_conflict_defaults(self) -> None:
        """Test Conflict default values."""
        conflict = Conflict(
            conflict_type="TEST_CONFLICT",
            agents=["agent1"],
            description="Test",
        )

        assert conflict.severity == "WARNING"  # Default severity
        assert conflict.details == {}
