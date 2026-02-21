import pytest

pytestmark = pytest.mark.integration

"""Tests for BotMetricsCollector.

Covers interaction recording, input validation, handoff recording,
bot and system summaries, alerting integration, and singleton reset.
"""

from unittest.mock import MagicMock

import pytest

from ghl_real_estate_ai.services.jorge.bot_metrics_collector import (
    VALID_BOT_TYPES,
    BotMetricsCollector,
)


@pytest.fixture(autouse=True)
def reset_collector():
    """Reset BotMetricsCollector singleton before and after each test."""
    BotMetricsCollector.reset()
    yield
    BotMetricsCollector.reset()


class TestBotMetricsCollector:
    """Tests for BotMetricsCollector."""

    # ── 1. Record valid bot interaction ────────────────────────────────

    def test_record_bot_interaction_valid(self):
        """Recording a valid interaction stores it in the collector."""
        collector = BotMetricsCollector()
        collector.record_bot_interaction(bot_type="lead", duration_ms=250.0, success=True, cache_hit=True)

        assert len(collector._interactions) == 1
        interaction = collector._interactions[0]
        assert interaction.bot_type == "lead"
        assert interaction.duration_ms == 250.0
        assert interaction.success is True
        assert interaction.cache_hit is True

    # ── 2. Invalid bot type raises ValueError ──────────────────────────

    def test_record_bot_interaction_invalid_type_raises(self):
        """Recording with an unrecognized bot_type raises ValueError."""
        collector = BotMetricsCollector()
        with pytest.raises(ValueError, match="Invalid bot_type 'unknown'"):
            collector.record_bot_interaction(bot_type="unknown", duration_ms=100.0, success=True)

    # ── 3. Record handoff ──────────────────────────────────────────────

    def test_record_handoff(self):
        """Recording a handoff stores source, target, success, and duration."""
        collector = BotMetricsCollector()
        collector.record_handoff(source="lead", target="buyer", success=True, duration_ms=120.0)

        assert len(collector._handoffs) == 1
        handoff = collector._handoffs[0]
        assert handoff.source == "lead"
        assert handoff.target == "buyer"
        assert handoff.success is True
        assert handoff.duration_ms == 120.0

    # ── 4. Bot summary with data ───────────────────────────────────────

    def test_get_bot_summary_with_data(self):
        """get_bot_summary returns correct aggregates for recorded interactions."""
        collector = BotMetricsCollector()

        # Record 4 interactions: 3 success, 1 failure; 2 cache hits
        collector.record_bot_interaction("buyer", 100.0, True, cache_hit=True)
        collector.record_bot_interaction("buyer", 200.0, True, cache_hit=True)
        collector.record_bot_interaction("buyer", 300.0, True, cache_hit=False)
        collector.record_bot_interaction("buyer", 400.0, False, cache_hit=False)

        summary = collector.get_bot_summary("buyer")

        assert summary["total_interactions"] == 4
        assert summary["success_rate"] == 0.75
        assert summary["error_rate"] == 0.25
        assert summary["cache_hit_rate"] == 0.5
        # avg = (100+200+300+400)/4 = 250
        assert summary["avg_duration_ms"] == 250.0
        # p95 should be a numeric value derived from the 4 durations
        assert summary["p95_duration_ms"] > 0

    # ── 5. Bot summary empty ───────────────────────────────────────────

    def test_get_bot_summary_empty(self):
        """get_bot_summary returns zero defaults when no interactions exist."""
        collector = BotMetricsCollector()
        summary = collector.get_bot_summary("seller")

        assert summary["total_interactions"] == 0
        assert summary["success_rate"] == 0.0
        assert summary["avg_duration_ms"] == 0.0
        assert summary["p95_duration_ms"] == 0.0
        assert summary["error_rate"] == 0.0
        assert summary["cache_hit_rate"] == 0.0

    # ── 6. System summary ──────────────────────────────────────────────

    def test_get_system_summary(self):
        """get_system_summary returns per-bot, handoff, and overall sections."""
        collector = BotMetricsCollector()

        # Record interactions across two bot types
        collector.record_bot_interaction("lead", 150.0, True)
        collector.record_bot_interaction("buyer", 250.0, True)
        collector.record_bot_interaction("buyer", 350.0, False)

        # Record a handoff
        collector.record_handoff("lead", "buyer", True, 80.0)
        collector.record_handoff("lead", "buyer", False, 200.0)

        summary = collector.get_system_summary()

        # Top-level keys
        assert "bots" in summary
        assert "handoffs" in summary
        assert "overall" in summary

        # Per-bot breakdown includes all valid bot types
        assert set(summary["bots"].keys()) == VALID_BOT_TYPES

        # Lead had 1 interaction
        assert summary["bots"]["lead"]["total_interactions"] == 1

        # Buyer had 2 interactions
        assert summary["bots"]["buyer"]["total_interactions"] == 2

        # Seller had 0 interactions
        assert summary["bots"]["seller"]["total_interactions"] == 0

        # Handoffs
        assert summary["handoffs"]["total_handoffs"] == 2
        assert summary["handoffs"]["success_rate"] == 0.5
        assert summary["handoffs"]["failure_rate"] == 0.5

        # Overall covers all 3 interactions
        assert summary["overall"]["total_interactions"] == 3

    # ── 7. Feed to alerting ────────────────────────────────────────────

    def test_feed_to_alerting(self):
        """feed_to_alerting calls record_metric 7 times on the alerting service."""
        collector = BotMetricsCollector()

        # Seed some data so summaries are non-trivial
        collector.record_bot_interaction("lead", 100.0, True, cache_hit=True)
        collector.record_bot_interaction("buyer", 200.0, True)
        collector.record_bot_interaction("seller", 300.0, False)
        collector.record_handoff("lead", "buyer", True, 50.0)

        mock_alerting = MagicMock()
        collector.feed_to_alerting(mock_alerting)

        # Should have called record_metric exactly 7 times
        assert mock_alerting.record_metric.call_count == 7

        # Collect the metric names that were recorded
        recorded_names = {call.args[0] for call in mock_alerting.record_metric.call_args_list}
        expected_names = {
            "error_rate",
            "cache_hit_rate",
            "lead_bot.response_time_p95",
            "buyer_bot.response_time_p95",
            "seller_bot.response_time_p95",
            "handoff.response_time_p95",
            "handoff.failure_rate",
        }
        assert recorded_names == expected_names

    # ── 8. Reset clears data ───────────────────────────────────────────

    def test_reset_clears_data(self):
        """reset() clears all stored interactions, handoffs, and singleton."""
        collector = BotMetricsCollector()
        collector.record_bot_interaction("lead", 100.0, True)
        collector.record_handoff("lead", "buyer", True, 50.0)

        assert len(collector._interactions) == 1
        assert len(collector._handoffs) == 1

        BotMetricsCollector.reset()

        # After reset, a new instance should be created with empty data
        new_collector = BotMetricsCollector()
        assert len(new_collector._interactions) == 0
        assert len(new_collector._handoffs) == 0
        # Confirm it is a new instance (old one was cleared)
        assert new_collector is not collector or len(new_collector._interactions) == 0
