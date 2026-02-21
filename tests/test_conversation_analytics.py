from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

"""Tests for Conversation Analytics Service."""

import pytest

from ghl_real_estate_ai.services.conversation_analytics import (
    ConversationAnalytics,
    ConversationMetrics,
    HandoffEffectiveness,
    SentimentTrajectory,
)


@pytest.fixture
def analytics() -> ConversationAnalytics:
    return ConversationAnalytics()


def _msgs(*pairs: tuple[str, str]) -> list[dict[str, str]]:
    """Helper: create messages from (role, content) tuples."""
    return [{"role": r, "content": c} for r, c in pairs]


BASIC_CONVERSATION = _msgs(
    ("user", "Hi, I'm interested in buying a home in Rancho Cucamonga"),
    ("assistant", "Welcome! I'd love to help you find the perfect home. What's your budget range?"),
    ("user", "Around 500K. I'm pre-approved already."),
    (
        "assistant",
        "That's great news! With pre-approval and a 500K budget, you have excellent options. Let me show you some properties.",
    ),
    ("user", "That sounds wonderful, thank you so much!"),
)

NEGATIVE_CONVERSATION = _msgs(
    ("user", "This property is terrible"),
    ("assistant", "I'm sorry to hear that. What specifically disappointed you?"),
    ("user", "The price is awful and the condition is horrible"),
    ("assistant", "I understand your frustration. Let me find better options."),
    ("user", "I hate everything about this process"),
)

IMPROVING_CONVERSATION = _msgs(
    ("user", "I'm frustrated with the search"),
    ("assistant", "I understand. Let me refine our approach."),
    ("user", "Okay, that new listing looks decent"),
    ("assistant", "It has great features. Want to schedule a showing?"),
    ("user", "Yes! I love this house, it's perfect!"),
    ("assistant", "Wonderful! I'll set up a showing right away."),
)

TOPIC_DRIFT_CONVERSATION = _msgs(
    ("user", "I want to buy a house in Rancho Cucamonga"),
    ("assistant", "I can help you find a house in Rancho Cucamonga"),
    ("user", "Forget real estate. Tell me about quantum physics and black holes"),
    ("assistant", "Quantum mechanics involves subatomic particles and wave functions"),
    ("user", "Now I want pizza recipes with mozzarella and tomato sauce"),
)

FOCUSED_CONVERSATION = _msgs(
    ("user", "I want to buy a house in Rancho Cucamonga"),
    ("assistant", "I can help you buy a house in Rancho Cucamonga. What is your budget?"),
    ("user", "My budget for the house in Rancho Cucamonga is 500K"),
    ("assistant", "A 500K budget in Rancho Cucamonga gives you great house options"),
    ("user", "Show me houses in Rancho Cucamonga under 500K"),
    ("assistant", "Here are houses in Rancho Cucamonga within your 500K house budget"),
)

RESOLUTION_CONVERSATION = _msgs(
    ("user", "I need help finding a home"),
    ("assistant", "I'll help you find the perfect property."),
    ("user", "What about 123 Main Street?"),
    ("assistant", "That's a 4-bed, 2-bath home at $450K. Want to schedule a showing?"),
    ("user", "Yes, please schedule it. Thank you so much for your help!"),
    ("assistant", "You're welcome! Showing scheduled for Saturday at 2 PM. Goodbye!"),
)

NO_RESOLUTION_CONVERSATION = _msgs(
    ("user", "I want a house"),
    ("assistant", "What area?"),
    ("user", "Never mind"),
)


class TestAnalyze:
    def test_basic_conversation(self, analytics: ConversationAnalytics) -> None:
        metrics = analytics.analyze(BASIC_CONVERSATION)
        assert isinstance(metrics, ConversationMetrics)
        assert metrics.message_count == 5
        assert 0 < metrics.avg_response_length
        assert 0 < metrics.user_message_ratio <= 1.0
        assert -1 <= metrics.avg_sentiment <= 1
        assert 0 <= metrics.topic_drift_score <= 1
        assert 0 <= metrics.engagement_score <= 1

    def test_user_message_ratio(self, analytics: ConversationAnalytics) -> None:
        msgs = _msgs(("user", "Hello"), ("assistant", "Hi"), ("user", "Bye"))
        metrics = analytics.analyze(msgs)
        assert metrics.user_message_ratio == pytest.approx(2 / 3, abs=0.01)

    def test_empty_conversation(self, analytics: ConversationAnalytics) -> None:
        metrics = analytics.analyze([])
        assert metrics.message_count == 0
        assert metrics.avg_response_length == 0.0
        assert metrics.avg_sentiment == 0.0

    def test_single_message(self, analytics: ConversationAnalytics) -> None:
        msgs = _msgs(("user", "Hello"))
        metrics = analytics.analyze(msgs)
        assert metrics.message_count == 1


class TestSentiment:
    def test_positive_sentiment(self, analytics: ConversationAnalytics) -> None:
        traj = analytics.sentiment_trajectory(BASIC_CONVERSATION)
        assert isinstance(traj, SentimentTrajectory)
        assert traj.overall > 0

    def test_negative_sentiment(self, analytics: ConversationAnalytics) -> None:
        traj = analytics.sentiment_trajectory(NEGATIVE_CONVERSATION)
        assert traj.overall < 0

    def test_improving_trajectory(self, analytics: ConversationAnalytics) -> None:
        traj = analytics.sentiment_trajectory(IMPROVING_CONVERSATION)
        assert traj.trend == "improving"
        assert len(traj.scores) == len(IMPROVING_CONVERSATION)

    def test_declining_trajectory(self, analytics: ConversationAnalytics) -> None:
        declining = _msgs(
            ("user", "I love this property, it's wonderful!"),
            ("assistant", "Glad you like it!"),
            ("user", "Wait, the inspection found problems"),
            ("assistant", "Let me review the report."),
            ("user", "This is terrible, I'm very disappointed and angry"),
        )
        traj = analytics.sentiment_trajectory(declining)
        assert traj.trend == "declining"

    def test_stable_trajectory(self, analytics: ConversationAnalytics) -> None:
        stable = _msgs(
            ("user", "Tell me about the property"),
            ("assistant", "It has 3 bedrooms"),
            ("user", "What about parking?"),
            ("assistant", "It has a 2-car garage"),
        )
        traj = analytics.sentiment_trajectory(stable)
        assert traj.trend == "stable"

    def test_empty_sentiment(self, analytics: ConversationAnalytics) -> None:
        traj = analytics.sentiment_trajectory([])
        assert traj.scores == []
        assert traj.trend == "stable"
        assert traj.overall == 0.0


class TestTopicDrift:
    def test_high_drift(self, analytics: ConversationAnalytics) -> None:
        score = analytics.detect_topic_drift(TOPIC_DRIFT_CONVERSATION)
        assert score > 0.3

    def test_low_drift(self, analytics: ConversationAnalytics) -> None:
        score = analytics.detect_topic_drift(FOCUSED_CONVERSATION)
        # Focused conversation should have less drift than topic-drifting one
        high_drift = analytics.detect_topic_drift(TOPIC_DRIFT_CONVERSATION)
        assert score < high_drift

    def test_drift_range(self, analytics: ConversationAnalytics) -> None:
        score = analytics.detect_topic_drift(BASIC_CONVERSATION)
        assert 0 <= score <= 1

    def test_empty_drift(self, analytics: ConversationAnalytics) -> None:
        assert analytics.detect_topic_drift([]) == 0.0

    def test_single_message_drift(self, analytics: ConversationAnalytics) -> None:
        assert analytics.detect_topic_drift(_msgs(("user", "Hello"))) == 0.0


class TestEngagement:
    def test_high_engagement(self, analytics: ConversationAnalytics) -> None:
        active = _msgs(
            ("user", "I'd love to see properties in Rancho Cucamonga with at least 3 bedrooms"),
            ("assistant", "Great, here are some options."),
            (
                "user",
                "The second one looks amazing! Can we schedule a tour this weekend? I'm very excited about the pool and the spacious kitchen.",
            ),
            ("assistant", "Absolutely! Saturday works."),
            (
                "user",
                "Perfect! Also, could you send me the HOA details and the recent comparable sales in the neighborhood?",
            ),
        )
        score = analytics.engagement_score(active)
        assert score > 0.5

    def test_low_engagement(self, analytics: ConversationAnalytics) -> None:
        passive = _msgs(
            ("user", "ok"),
            ("assistant", "Would you like to see more properties?"),
            ("user", "no"),
            ("assistant", "Is there anything else?"),
            ("user", "no"),
        )
        score = analytics.engagement_score(passive)
        assert score < 0.5

    def test_empty_engagement(self, analytics: ConversationAnalytics) -> None:
        assert analytics.engagement_score([]) == 0.0


class TestResolution:
    def test_resolution_detected(self, analytics: ConversationAnalytics) -> None:
        assert analytics.detect_resolution(RESOLUTION_CONVERSATION) is True

    def test_thank_you_resolution(self, analytics: ConversationAnalytics) -> None:
        msgs = _msgs(
            ("user", "Help me find a home"),
            ("assistant", "Sure!"),
            ("user", "Thanks for all your help, goodbye!"),
        )
        assert analytics.detect_resolution(msgs) is True

    def test_no_resolution(self, analytics: ConversationAnalytics) -> None:
        assert analytics.detect_resolution(NO_RESOLUTION_CONVERSATION) is False

    def test_empty_resolution(self, analytics: ConversationAnalytics) -> None:
        assert analytics.detect_resolution([]) is False


class TestHandoffEffectiveness:
    def test_handoff_effectiveness(self, analytics: ConversationAnalytics) -> None:
        conv1 = _msgs(
            ("user", "I want to buy"),
            ("assistant", "Transferring to buyer bot"),
            ("assistant", "Hi, I'm the buyer bot. How can I help?"),
            ("user", "Great, thank you!"),
        )
        conv2 = _msgs(
            ("user", "Sell my house"),
            ("assistant", "Transferring to seller bot"),
            ("assistant", "Hi, I'm the seller bot."),
            ("user", "Thanks for the help!"),
        )
        result = analytics.handoff_effectiveness(
            conversations=[conv1, conv2],
            handoff_indices=[1, 1],
        )
        assert isinstance(result, HandoffEffectiveness)
        assert result.total_handoffs == 2
        assert result.successful_resolutions >= 0
        assert result.effectiveness_rate >= 0

    def test_empty_handoff(self, analytics: ConversationAnalytics) -> None:
        result = analytics.handoff_effectiveness([], [])
        assert result.total_handoffs == 0
        assert result.effectiveness_rate == 0.0


class TestQualityScore:
    def test_quality_range(self, analytics: ConversationAnalytics) -> None:
        score = analytics.quality_score(BASIC_CONVERSATION)
        assert 0 <= score <= 1

    def test_good_conversation_quality(self, analytics: ConversationAnalytics) -> None:
        score = analytics.quality_score(RESOLUTION_CONVERSATION)
        assert score > 0.3

    def test_empty_quality(self, analytics: ConversationAnalytics) -> None:
        assert analytics.quality_score([]) == 0.0


class TestBatchAnalysis:
    def test_batch(self, analytics: ConversationAnalytics) -> None:
        results = analytics.batch_analyze([BASIC_CONVERSATION, NEGATIVE_CONVERSATION, FOCUSED_CONVERSATION])
        assert len(results) == 3
        assert all(isinstance(m, ConversationMetrics) for m in results)

    def test_batch_empty(self, analytics: ConversationAnalytics) -> None:
        assert analytics.batch_analyze([]) == []

    def test_very_long_conversation(self, analytics: ConversationAnalytics) -> None:
        long_conv = _msgs(
            *[(("user" if i % 2 == 0 else "assistant"), f"Message number {i} about real estate") for i in range(100)]
        )
        metrics = analytics.analyze(long_conv)
        assert metrics.message_count == 100
