"""Tests for Temporal Processor module."""

from datetime import datetime, timedelta

import pytest
from src.query.temporal_processor import (
    RecencyBoostConfig,
    TemporalConstraint,
    TemporalConstraintType,
    TemporalProcessor,
    TimeAwareRetriever,
)


@pytest.mark.unit


class TestTemporalConstraint:
    """Test TemporalConstraint class."""

    def test_constraint_creation(self):
        """Test creating a temporal constraint."""
        constraint = TemporalConstraint(
            constraint_type=TemporalConstraintType.ABSOLUTE_DATE,
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 1, 15),
            raw_text="January 15, 2024",
            confidence=0.95,
        )

        assert constraint.constraint_type == TemporalConstraintType.ABSOLUTE_DATE
        assert constraint.start_date == datetime(2024, 1, 15)
        assert constraint.raw_text == "January 15, 2024"

    def test_constraint_to_dict(self):
        """Test constraint serialization."""
        constraint = TemporalConstraint(
            constraint_type=TemporalConstraintType.RELATIVE,
            raw_text="last week",
            confidence=0.85,
        )

        d = constraint.to_dict()
        assert d["constraint_type"] == "relative"
        assert d["raw_text"] == "last week"
        assert d["confidence"] == 0.85

    def test_constraint_satisfaction(self):
        """Test constraint satisfaction checking."""
        constraint = TemporalConstraint(
            constraint_type=TemporalConstraintType.ABSOLUTE_RANGE,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        assert constraint.is_satisfied_by(datetime(2024, 1, 15)) is True
        assert constraint.is_satisfied_by(datetime(2024, 2, 15)) is False
        assert constraint.is_satisfied_by(datetime(2023, 12, 15)) is False

    def test_constraint_satisfaction_open_ended(self):
        """Test constraint with open-ended dates."""
        constraint = TemporalConstraint(
            constraint_type=TemporalConstraintType.RELATIVE,
            start_date=datetime(2024, 1, 1),
            end_date=None,
        )

        assert constraint.is_satisfied_by(datetime(2024, 6, 15)) is True
        assert constraint.is_satisfied_by(datetime(2023, 6, 15)) is False


class TestTemporalProcessor:
    """Test TemporalProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create a temporal processor."""
        return TemporalProcessor(reference_date=datetime(2024, 6, 15))

    def test_processor_initialization(self, processor):
        """Test processor initialization."""
        assert processor.reference_date == datetime(2024, 6, 15)
        assert len(processor._patterns) > 0

    def test_extract_absolute_date_us(self, processor):
        """Test extraction of US format dates."""
        context = processor.extract_temporal_context("Show listings from 01/15/2024")

        assert len(context.constraints) > 0
        assert any(c.constraint_type == TemporalConstraintType.ABSOLUTE_DATE for c in context.constraints)

    def test_extract_absolute_date_iso(self, processor):
        """Test extraction of ISO format dates."""
        context = processor.extract_temporal_context("Show listings from 2024-01-15")

        assert len(context.constraints) > 0

    def test_extract_relative_last_week(self, processor):
        """Test extraction of 'last week'."""
        context = processor.extract_temporal_context("Show me houses listed last week")

        assert len(context.constraints) > 0
        relative_constraints = [c for c in context.constraints if c.constraint_type == TemporalConstraintType.RELATIVE]
        assert len(relative_constraints) > 0

    def test_extract_relative_days_ago(self, processor):
        """Test extraction of 'X days ago'."""
        context = processor.extract_temporal_context("Show listings from 5 days ago")

        relative_constraints = [c for c in context.constraints if c.constraint_type == TemporalConstraintType.RELATIVE]
        assert len(relative_constraints) > 0

        # Check date calculation
        constraint = relative_constraints[0]
        expected_start = datetime(2024, 6, 10)  # 5 days before 6/15
        assert constraint.start_date.date() == expected_start.date()

    def test_extract_recency_indicators(self, processor):
        """Test extraction of recency indicators."""
        context = processor.extract_temporal_context("Show me recent listings")

        recency_constraints = [c for c in context.constraints if c.constraint_type == TemporalConstraintType.RECENCY]
        assert len(recency_constraints) > 0
        assert context.recency_preference > 0.7

    def test_extract_historical_indicators(self, processor):
        """Test extraction of historical indicators."""
        context = processor.extract_temporal_context("Show all historical data")

        historical_constraints = [
            c for c in context.constraints if c.constraint_type == TemporalConstraintType.HISTORICAL
        ]
        assert len(historical_constraints) > 0
        assert context.recency_preference < 0.5

    def test_extract_seasonal(self, processor):
        """Test extraction of seasonal references."""
        context = processor.extract_temporal_context("Show listings from summer 2023")

        seasonal_constraints = [c for c in context.constraints if c.constraint_type == TemporalConstraintType.SEASONAL]
        assert len(seasonal_constraints) > 0

    def test_extract_multiple_constraints(self, processor):
        """Test extraction of multiple constraints."""
        context = processor.extract_temporal_context("Show me recent houses in Rancho Cucamonga listed last month")

        assert len(context.constraints) >= 2
        assert len(context.time_keywords) > 0

    def test_temporal_focus_past(self, processor):
        """Test detection of past temporal focus."""
        context = processor.extract_temporal_context("Show me past listings from last year")
        assert context.temporal_focus == "past"

    def test_temporal_focus_future(self, processor):
        """Test detection of future temporal focus."""
        context = processor.extract_temporal_context("Show me upcoming open houses next week")
        assert context.temporal_focus == "future"

    def test_temporal_focus_present(self, processor):
        """Test detection of present temporal focus."""
        context = processor.extract_temporal_context("Show me current listings")
        assert context.temporal_focus == "present"

    def test_recency_preference_calculation(self, processor):
        """Test recency preference calculation."""
        context_recent = processor.extract_temporal_context("Show recent listings")
        assert context_recent.recency_preference > 0.8

        context_historical = processor.extract_temporal_context("Show historical archive")
        assert context_historical.recency_preference < 0.3

        context_neutral = processor.extract_temporal_context("Show me houses")
        assert 0.4 <= context_neutral.recency_preference <= 0.6

    def test_context_to_dict(self, processor):
        """Test context serialization."""
        context = processor.extract_temporal_context("Show listings from last week")
        d = context.to_dict()

        assert "constraints" in d
        assert "recency_preference" in d
        assert "temporal_focus" in d
        assert "time_keywords" in d

    def test_update_reference_date(self, processor):
        """Test updating reference date."""
        new_date = datetime(2024, 12, 1)
        processor.update_reference_date(new_date)

        assert processor.reference_date == new_date


class TestRecencyBoostConfig:
    """Test RecencyBoostConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = RecencyBoostConfig()

        assert config.enabled is True
        assert config.decay_function == "exponential"
        assert config.half_life_days == 30.0
        assert config.max_boost == 2.0
        assert config.min_boost == 0.5

    def test_get_reference_date_default(self):
        """Test getting default reference date."""
        config = RecencyBoostConfig()
        ref_date = config.get_reference_date()

        # Should be close to now
        now = datetime.now()
        assert abs((now - ref_date).total_seconds()) < 5

    def test_get_reference_date_custom(self):
        """Test getting custom reference date."""
        custom_date = datetime(2024, 1, 15)
        config = RecencyBoostConfig(reference_date=custom_date)

        assert config.get_reference_date() == custom_date


class TestTimeAwareRetriever:
    """Test TimeAwareRetriever functionality."""

    @pytest.fixture
    def retriever(self):
        """Create a time-aware retriever."""
        return TimeAwareRetriever()

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents with timestamps."""
        now = datetime.now()
        return [
            {"id": 1, "score": 1.0, "created_at": now - timedelta(days=1)},
            {"id": 2, "score": 1.0, "created_at": now - timedelta(days=10)},
            {"id": 3, "score": 1.0, "created_at": now - timedelta(days=30)},
            {"id": 4, "score": 1.0, "created_at": now - timedelta(days=60)},
            {"id": 5, "score": 1.0, "created_at": now - timedelta(days=90)},
        ]

    def test_apply_recency_boost_exponential(self, retriever, sample_documents):
        """Test exponential recency boosting."""
        config = RecencyBoostConfig(
            decay_function="exponential",
            half_life_days=30.0,
            max_boost=2.0,
            min_boost=0.5,
        )

        boosted = retriever.apply_recency_boost(sample_documents, config)

        # Check that scores are boosted
        assert all("recency_boost" in doc for doc in boosted)
        assert all("original_score" in doc for doc in boosted)

        # More recent documents should have higher boosts
        boosts = [doc["recency_boost"] for doc in boosted]
        assert boosts[0] > boosts[2]  # 1 day vs 30 days
        assert boosts[2] > boosts[4]  # 30 days vs 90 days

    def test_apply_recency_boost_linear(self, retriever, sample_documents):
        """Test linear recency boosting."""
        config = RecencyBoostConfig(
            decay_function="linear",
            half_life_days=30.0,
            max_boost=2.0,
            min_boost=0.5,
        )

        boosted = retriever.apply_recency_boost(sample_documents, config)

        assert len(boosted) == len(sample_documents)
        assert all(doc["score"] > 0 for doc in boosted)

    def test_apply_recency_boost_gaussian(self, retriever, sample_documents):
        """Test Gaussian recency boosting."""
        config = RecencyBoostConfig(
            decay_function="gaussian",
            half_life_days=30.0,
            max_boost=2.0,
            min_boost=0.5,
        )

        boosted = retriever.apply_recency_boost(sample_documents, config)

        assert len(boosted) == len(sample_documents)

    def test_apply_recency_boost_disabled(self, retriever, sample_documents):
        """Test that disabled boosting returns original scores."""
        config = RecencyBoostConfig(enabled=False)

        boosted = retriever.apply_recency_boost(sample_documents, config)

        # Should return documents as-is
        assert boosted == sample_documents

    def test_filter_by_constraints(self, retriever):
        """Test filtering documents by temporal constraints."""
        now = datetime.now()
        documents = [
            {"id": 1, "created_at": now - timedelta(days=5)},
            {"id": 2, "created_at": now - timedelta(days=15)},
            {"id": 3, "created_at": now - timedelta(days=45)},
        ]

        constraint = TemporalConstraint(
            constraint_type=TemporalConstraintType.RELATIVE,
            start_date=now - timedelta(days=30),
            end_date=now,
        )

        filtered = retriever.filter_by_constraints(documents, [constraint])

        assert len(filtered) == 2
        assert all(doc["id"] in [1, 2] for doc in filtered)

    def test_filter_by_multiple_constraints(self, retriever):
        """Test filtering with multiple constraints."""
        now = datetime.now()
        documents = [
            {"id": 1, "created_at": now - timedelta(days=10)},
            {"id": 2, "created_at": now - timedelta(days=20)},
            {"id": 3, "created_at": now - timedelta(days=40)},
        ]

        constraints = [
            TemporalConstraint(
                constraint_type=TemporalConstraintType.RELATIVE,
                start_date=now - timedelta(days=30),
                end_date=None,
            ),
            TemporalConstraint(
                constraint_type=TemporalConstraintType.RELATIVE,
                start_date=None,
                end_date=now - timedelta(days=5),
            ),
        ]

        filtered = retriever.filter_by_constraints(documents, constraints)

        # Should satisfy both constraints
        assert len(filtered) == 2
        assert all(doc["id"] in [2, 3] for doc in filtered)

    def test_get_temporal_stats(self, retriever):
        """Test getting temporal statistics."""
        now = datetime.now()
        documents = [
            {"id": 1, "created_at": now - timedelta(days=10)},
            {"id": 2, "created_at": now - timedelta(days=20)},
            {"id": 3, "created_at": now - timedelta(days=30)},
        ]

        stats = retriever.get_temporal_stats(documents)

        assert stats["count"] == 3
        assert "oldest" in stats
        assert "newest" in stats
        assert "median_age_days" in stats
        assert "mean_age_days" in stats

    def test_get_temporal_stats_empty(self, retriever):
        """Test temporal stats with empty document list."""
        stats = retriever.get_temporal_stats([])

        assert stats["count"] == 0

    def test_get_temporal_stats_no_dates(self, retriever):
        """Test temporal stats with documents lacking dates."""
        documents = [{"id": 1}, {"id": 2}]
        stats = retriever.get_temporal_stats(documents)

        assert stats["count"] == 0