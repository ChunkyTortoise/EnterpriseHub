"""Unit tests for Pydantic analytics models and Call enum values."""

from __future__ import annotations

from datetime import datetime

import pytest

from voice_ai.models.call import CallStatus, CallDirection
from voice_ai.models.call_analytics import (
    CallMetrics,
    SentimentSummary,
    CostBreakdown,
    CallAnalyticsResponse,
)


class TestCallEnums:
    def test_call_status_values(self):
        assert CallStatus.INITIATED.value == "initiated"
        assert CallStatus.RINGING.value == "ringing"
        assert CallStatus.IN_PROGRESS.value == "in_progress"
        assert CallStatus.COMPLETED.value == "completed"
        assert CallStatus.FAILED.value == "failed"
        assert CallStatus.NO_ANSWER.value == "no_answer"

    def test_call_direction_values(self):
        assert CallDirection.INBOUND.value == "inbound"
        assert CallDirection.OUTBOUND.value == "outbound"


class TestCallMetrics:
    def test_defaults(self):
        m = CallMetrics()
        assert m.total_calls == 0
        assert m.completed_calls == 0
        assert m.avg_duration_seconds == 0.0
        assert m.avg_lead_score is None

    def test_with_values(self):
        m = CallMetrics(total_calls=10, completed_calls=8, avg_duration_seconds=120.5)
        assert m.total_calls == 10
        assert m.completed_calls == 8


class TestSentimentSummary:
    def test_defaults(self):
        s = SentimentSummary()
        assert s.positive_count == 0
        assert s.avg_sentiment == 0.0


class TestCostBreakdown:
    def test_defaults(self):
        c = CostBreakdown()
        assert c.total_cost == 0.0
        assert c.gross_margin == 0.0


class TestCallAnalyticsResponse:
    def test_full_response(self):
        now = datetime.utcnow()
        r = CallAnalyticsResponse(
            period="daily",
            start_date=now,
            end_date=now,
            calls_by_bot_type={"lead": 5, "buyer": 3},
            calls_by_direction={"inbound": 6, "outbound": 2},
        )
        assert r.period == "daily"
        assert r.calls_by_bot_type["lead"] == 5
        assert r.metrics.total_calls == 0  # default
