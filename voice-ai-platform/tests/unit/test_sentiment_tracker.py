"""Unit tests for SentimentTracker — exercises real analysis code."""

from __future__ import annotations

import pytest

from voice_ai.services.sentiment_tracker import SentimentTracker, SentimentScore


class TestSentimentAnalyze:
    """Test individual text analysis."""

    def test_positive_text(self):
        tracker = SentimentTracker()
        result = tracker.analyze("This is a great and amazing experience!")
        assert result.score > 0
        assert result.label == "positive"
        assert result.positive_count >= 2

    def test_negative_text(self):
        tracker = SentimentTracker()
        result = tracker.analyze("This is terrible and awful, I hate it.")
        assert result.score < 0
        assert result.label == "negative"
        assert result.negative_count >= 2

    def test_neutral_text(self):
        tracker = SentimentTracker()
        result = tracker.analyze("The meeting is scheduled for Tuesday at 3pm.")
        assert result.label == "neutral"
        assert result.score == 0.0
        assert result.positive_count == 0
        assert result.negative_count == 0

    def test_mixed_text_equal_positive_negative(self):
        tracker = SentimentTracker()
        result = tracker.analyze("I love the area but hate the price.")
        # 1 positive (love) + 1 negative (hate) = 0 score
        assert abs(result.score) <= 0.1
        assert result.label == "neutral"

    def test_empty_text(self):
        tracker = SentimentTracker()
        result = tracker.analyze("")
        assert result.score == 0.0
        assert result.label == "neutral"

    def test_case_insensitive(self):
        tracker = SentimentTracker()
        result = tracker.analyze("GREAT EXCELLENT PERFECT")
        assert result.label == "positive"

    def test_score_range(self):
        tracker = SentimentTracker()
        r1 = tracker.analyze("excellent amazing wonderful fantastic")
        assert -1.0 <= r1.score <= 1.0
        r2 = tracker.analyze("terrible awful bad worst")
        assert -1.0 <= r2.score <= 1.0


class TestSentimentTrackerAggregation:
    """Test rolling sentiment aggregation."""

    def test_average_sentiment_empty(self):
        tracker = SentimentTracker()
        assert tracker.average_sentiment == 0.0

    def test_average_sentiment_single(self):
        tracker = SentimentTracker()
        tracker.analyze("This is great!")
        assert tracker.average_sentiment > 0

    def test_average_across_multiple_segments(self):
        tracker = SentimentTracker()
        tracker.analyze("This is amazing and wonderful!")  # positive
        tracker.analyze("What a terrible experience.")       # negative
        # Average should be somewhere in between
        avg = tracker.average_sentiment
        assert -1.0 <= avg <= 1.0

    def test_sentiment_distribution(self):
        tracker = SentimentTracker()
        tracker.analyze("This is great!")
        tracker.analyze("This is awful!")
        tracker.analyze("Meeting at 3pm.")

        dist = tracker.sentiment_distribution
        assert dist["positive"] == 1
        assert dist["negative"] == 1
        assert dist["neutral"] == 1

    def test_get_summary(self):
        tracker = SentimentTracker()
        tracker.analyze("Great!")
        tracker.analyze("Terrible!")

        summary = tracker.get_summary()
        assert summary["total_segments"] == 2
        assert "average" in summary
        assert "distribution" in summary

    def test_reset_clears_state(self):
        tracker = SentimentTracker()
        tracker.analyze("Great!")
        tracker.analyze("Awful!")
        assert tracker.get_summary()["total_segments"] == 2

        tracker.reset()
        assert tracker.average_sentiment == 0.0
        assert tracker.get_summary()["total_segments"] == 0
