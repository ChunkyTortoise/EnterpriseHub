import pytest
pytestmark = pytest.mark.unit

"""Unit tests for the TokenAnalytics component.

Tests record usage, cost aggregation by bot/provider, daily trend,
demo data generation, and empty state handling.
"""


from datetime import datetime, timedelta, timezone

import pytest

from ghl_real_estate_ai.streamlit_demo.components.token_analytics import (

    TokenAnalytics,
    TokenUsageRecord,
    _generate_demo_data,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def analytics() -> TokenAnalytics:
    """Create a TokenAnalytics instance with no demo data."""
    ta = TokenAnalytics()
    ta._usage_records = []  # Clear any demo data loaded via env var
    return ta


@pytest.fixture
def analytics_with_records(analytics: TokenAnalytics) -> TokenAnalytics:
    """Create a TokenAnalytics instance with known records for testing."""
    analytics.record_usage("lead_bot", "claude", "claude-3-opus", 1000, 500, 0.0105)
    analytics.record_usage("lead_bot", "gemini", "gemini-1.5-flash", 2000, 800, 0.0065)
    analytics.record_usage("buyer_bot", "claude", "claude-3-opus", 1500, 600, 0.012)
    analytics.record_usage("seller_bot", "gpt-4o", "gpt-4o-2024", 800, 300, 0.005)
    return analytics


# ============================================================================
# Test: Record Usage
# ============================================================================


class TestRecordUsage:
    """Tests for recording token usage events."""

    def test_record_increases_count(self, analytics: TokenAnalytics):
        """Recording a usage event should increase the record count."""
        assert analytics.get_record_count() == 0
        analytics.record_usage("lead_bot", "claude", "claude-3-opus", 100, 50, 0.001)
        assert analytics.get_record_count() == 1

    def test_record_multiple(self, analytics: TokenAnalytics):
        """Multiple records should accumulate."""
        for i in range(5):
            analytics.record_usage("lead_bot", "claude", "model", 100, 50, 0.001)
        assert analytics.get_record_count() == 5

    def test_record_sets_timestamp(self, analytics: TokenAnalytics):
        """Recorded usage should have a recent timestamp."""
        analytics.record_usage("lead_bot", "claude", "model", 100, 50, 0.001)
        record = analytics._usage_records[0]
        now = datetime.now(tz=timezone.utc)
        assert (now - record.timestamp).total_seconds() < 5.0


# ============================================================================
# Test: Cost by Bot
# ============================================================================


class TestCostByBot:
    """Tests for get_cost_by_bot aggregation."""

    def test_empty_returns_empty(self, analytics: TokenAnalytics):
        """No records should return empty dict."""
        assert analytics.get_cost_by_bot() == {}

    def test_single_bot(self, analytics: TokenAnalytics):
        """Single bot should have its cost."""
        analytics.record_usage("lead_bot", "claude", "model", 100, 50, 0.005)
        result = analytics.get_cost_by_bot()
        assert "lead_bot" in result
        assert result["lead_bot"] == 0.005

    def test_multiple_bots(self, analytics_with_records: TokenAnalytics):
        """Multiple bots should each have their own cost sum."""
        result = analytics_with_records.get_cost_by_bot()
        assert len(result) == 3
        assert "lead_bot" in result
        assert "buyer_bot" in result
        assert "seller_bot" in result

    def test_costs_sum_correctly(self, analytics_with_records: TokenAnalytics):
        """Lead bot costs should sum correctly (two records)."""
        result = analytics_with_records.get_cost_by_bot()
        expected = round(0.0105 + 0.0065, 4)
        assert result["lead_bot"] == expected


# ============================================================================
# Test: Cost by Provider
# ============================================================================


class TestCostByProvider:
    """Tests for get_cost_by_provider aggregation."""

    def test_empty_returns_empty(self, analytics: TokenAnalytics):
        """No records should return empty dict."""
        assert analytics.get_cost_by_provider() == {}

    def test_multiple_providers(self, analytics_with_records: TokenAnalytics):
        """All three providers should be present."""
        result = analytics_with_records.get_cost_by_provider()
        assert "claude" in result
        assert "gemini" in result
        assert "gpt-4o" in result

    def test_provider_costs_sum(self, analytics_with_records: TokenAnalytics):
        """Claude costs should sum correctly (two records)."""
        result = analytics_with_records.get_cost_by_provider()
        expected = round(0.0105 + 0.012, 4)
        assert result["claude"] == expected


# ============================================================================
# Test: Daily Trend
# ============================================================================


class TestDailyTrend:
    """Tests for get_daily_trend method."""

    def test_empty_returns_empty(self, analytics: TokenAnalytics):
        """No records should return empty list."""
        assert analytics.get_daily_trend() == []

    def test_single_day_records(self, analytics_with_records: TokenAnalytics):
        """All records from the same day should aggregate into one entry."""
        trend = analytics_with_records.get_daily_trend()
        # All records were created now, so they should be in one day
        assert len(trend) == 1
        assert trend[0]["request_count"] == 4

    def test_trend_entry_keys(self, analytics_with_records: TokenAnalytics):
        """Each trend entry should have the expected keys."""
        trend = analytics_with_records.get_daily_trend()
        expected_keys = {"date", "total_cost", "input_tokens", "output_tokens", "request_count"}
        for entry in trend:
            assert expected_keys.issubset(entry.keys())

    def test_trend_total_tokens(self, analytics_with_records: TokenAnalytics):
        """Input tokens should sum correctly across the day."""
        trend = analytics_with_records.get_daily_trend()
        expected_input = 1000 + 2000 + 1500 + 800
        assert trend[0]["input_tokens"] == expected_input

    def test_trend_sorted_by_date(self, analytics: TokenAnalytics):
        """Trend entries should be sorted chronologically."""
        now = datetime.now(tz=timezone.utc)
        # Add records from different days
        analytics._usage_records.append(
            TokenUsageRecord(
                timestamp=now - timedelta(days=2),
                bot_name="lead_bot",
                provider="claude",
                model="model",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.001,
            )
        )
        analytics._usage_records.append(
            TokenUsageRecord(
                timestamp=now,
                bot_name="lead_bot",
                provider="claude",
                model="model",
                input_tokens=200,
                output_tokens=100,
                cost_usd=0.002,
            )
        )
        trend = analytics.get_daily_trend()
        assert len(trend) == 2
        assert trend[0]["date"] < trend[1]["date"]


# ============================================================================
# Test: Demo Data
# ============================================================================


class TestDemoData:
    """Tests for demo data generation."""

    def test_demo_data_not_empty(self):
        """Demo data should contain records."""
        data = _generate_demo_data()
        assert len(data) > 0

    def test_demo_data_has_multiple_providers(self):
        """Demo data should include multiple providers."""
        data = _generate_demo_data()
        providers = {r.provider for r in data}
        assert len(providers) >= 2

    def test_demo_data_has_multiple_bots(self):
        """Demo data should include multiple bots."""
        data = _generate_demo_data()
        bots = {r.bot_name for r in data}
        assert len(bots) >= 2

    def test_demo_data_spans_multiple_days(self):
        """Demo data should span more than one day."""
        data = _generate_demo_data()
        dates = {r.timestamp.strftime("%Y-%m-%d") for r in data}
        assert len(dates) >= 7

    def test_demo_data_cost_reduction_narrative(self):
        """Later days should have lower average costs than earlier days."""
        data = _generate_demo_data()
        # Split by median date
        dates = sorted({r.timestamp.strftime("%Y-%m-%d") for r in data})
        mid = len(dates) // 2
        early_dates = set(dates[:mid])
        late_dates = set(dates[mid:])

        early_cost = sum(r.cost_usd for r in data if r.timestamp.strftime("%Y-%m-%d") in early_dates)
        late_cost = sum(r.cost_usd for r in data if r.timestamp.strftime("%Y-%m-%d") in late_dates)

        # Late period should be cheaper due to Gemini migration
        assert late_cost < early_cost, f"Late cost {late_cost} should be < early cost {early_cost}"


# ============================================================================
# Test: Empty State
# ============================================================================


class TestEmptyState:
    """Tests for empty/initial state behavior."""

    def test_total_cost_zero(self, analytics: TokenAnalytics):
        """Empty analytics should report zero cost."""
        assert analytics.get_total_cost() == 0.0

    def test_total_tokens_zero(self, analytics: TokenAnalytics):
        """Empty analytics should report zero tokens."""
        result = analytics.get_total_tokens()
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0

    def test_record_count_zero(self, analytics: TokenAnalytics):
        """Empty analytics should have zero records."""
        assert analytics.get_record_count() == 0