"""Tests for Multi-Channel Sentiment Analysis Engine."""

import pytest

from ghl_real_estate_ai.services.sentiment_analysis_engine import (
    SentimentAnalysisEngine,
    Emotion,
    SentimentTrend,
    Channel,
)


@pytest.fixture
def engine():
    return SentimentAnalysisEngine()


# -------------------------------------------------------------------------
# Polarity detection
# -------------------------------------------------------------------------

class TestPolarity:
    @pytest.mark.asyncio
    async def test_positive_message(self, engine):
        r = await engine.analyze_message("c1", "I love that house, it's perfect!", "sms")
        assert r.polarity > 0.3

    @pytest.mark.asyncio
    async def test_negative_message(self, engine):
        r = await engine.analyze_message("c2", "That place is terrible and too expensive", "sms")
        assert r.polarity < -0.3

    @pytest.mark.asyncio
    async def test_neutral_message(self, engine):
        r = await engine.analyze_message("c3", "What time is the showing?", "sms")
        assert -0.3 <= r.polarity <= 0.3

    @pytest.mark.asyncio
    async def test_negation_flips_positive(self, engine):
        r = await engine.analyze_message("c4", "I don't love it", "sms")
        assert r.polarity < 0

    @pytest.mark.asyncio
    async def test_negation_flips_negative(self, engine):
        r = await engine.analyze_message("c5", "It's not terrible", "sms")
        assert r.polarity > 0 or r.polarity == 0  # at least not negative

    @pytest.mark.asyncio
    async def test_polarity_bounded(self, engine):
        r = await engine.analyze_message(
            "c6", "I love love love this amazing perfect wonderful fantastic beautiful house!", "sms"
        )
        assert -1.0 <= r.polarity <= 1.0


# -------------------------------------------------------------------------
# Emotion classification
# -------------------------------------------------------------------------

class TestEmotionClassification:
    @pytest.mark.asyncio
    async def test_excited_emotion(self, engine):
        r = await engine.analyze_message("c7", "I'm so excited!! Can't wait to see it!", "sms")
        assert r.emotion == Emotion.EXCITED

    @pytest.mark.asyncio
    async def test_frustrated_emotion(self, engine):
        r = await engine.analyze_message("c8", "I'm frustrated, stop calling me", "sms")
        assert r.emotion == Emotion.FRUSTRATED

    @pytest.mark.asyncio
    async def test_hesitant_emotion(self, engine):
        r = await engine.analyze_message("c9", "I'm not sure, I need to think about it", "sms")
        assert r.emotion == Emotion.HESITANT

    @pytest.mark.asyncio
    async def test_confident_emotion(self, engine):
        r = await engine.analyze_message("c10", "I've decided, let's do it!", "sms")
        assert r.emotion == Emotion.CONFIDENT

    @pytest.mark.asyncio
    async def test_anxious_emotion(self, engine):
        r = await engine.analyze_message("c11", "I'm worried about the mortgage, kind of scared", "sms")
        assert r.emotion == Emotion.ANXIOUS


# -------------------------------------------------------------------------
# Intent detection
# -------------------------------------------------------------------------

class TestIntentDetection:
    @pytest.mark.asyncio
    async def test_schedule_showing_intent(self, engine):
        r = await engine.analyze_message("c12", "Can I schedule a tour?", "sms")
        assert "schedule_showing" in r.intent_signals

    @pytest.mark.asyncio
    async def test_price_inquiry_intent(self, engine):
        r = await engine.analyze_message("c13", "How much is that house?", "sms")
        assert "price_inquiry" in r.intent_signals

    @pytest.mark.asyncio
    async def test_make_offer_intent(self, engine):
        r = await engine.analyze_message("c14", "I want to make an offer", "sms")
        assert "make_offer" in r.intent_signals

    @pytest.mark.asyncio
    async def test_no_intent_on_generic_message(self, engine):
        r = await engine.analyze_message("c15", "Thanks for the info", "sms")
        assert len(r.intent_signals) == 0


# -------------------------------------------------------------------------
# Key phrase extraction
# -------------------------------------------------------------------------

class TestKeyPhrases:
    @pytest.mark.asyncio
    async def test_price_extraction(self, engine):
        r = await engine.analyze_message("c16", "My budget is around $650,000", "sms")
        assert any("$" in p for p in r.key_phrases)

    @pytest.mark.asyncio
    async def test_location_extraction(self, engine):
        r = await engine.analyze_message("c17", "I love the Victoria area", "sms")
        assert any("victoria" in p.lower() for p in r.key_phrases)

    @pytest.mark.asyncio
    async def test_bedroom_extraction(self, engine):
        r = await engine.analyze_message("c18", "Looking for a 3 bedroom place", "sms")
        assert any("3" in p and "bed" in p.lower() for p in r.key_phrases)


# -------------------------------------------------------------------------
# Conversation sentiment
# -------------------------------------------------------------------------

class TestConversationSentiment:
    @pytest.mark.asyncio
    async def test_improving_trend(self, engine):
        msgs = [
            "I'm not interested",
            "Well maybe I could look",
            "Actually that sounds good",
            "Yes I love it!",
            "I'm excited, let's schedule a showing!",
        ]
        for msg in msgs:
            await engine.analyze_message("trend_up", msg, "sms")
        conv = await engine.get_conversation_sentiment("trend_up")
        assert conv.trend == SentimentTrend.IMPROVING

    @pytest.mark.asyncio
    async def test_declining_trend(self, engine):
        msgs = [
            "I love this place!",
            "It's great but expensive",
            "I'm not sure anymore",
            "Too expensive for me",
            "I'm disappointed with the options",
        ]
        for msg in msgs:
            await engine.analyze_message("trend_down", msg, "sms")
        conv = await engine.get_conversation_sentiment("trend_down")
        assert conv.trend == SentimentTrend.DECLINING

    @pytest.mark.asyncio
    async def test_emotion_distribution(self, engine):
        await engine.analyze_message("dist", "I'm so excited!!", "sms")
        await engine.analyze_message("dist", "Not sure about this", "sms")
        conv = await engine.get_conversation_sentiment("dist")
        assert len(conv.emotion_distribution) >= 2
        total = sum(conv.emotion_distribution.values())
        assert abs(total - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_escalation_risk_high_on_negativity(self, engine):
        for _ in range(5):
            await engine.analyze_message("esc", "This is terrible, stop contacting me", "sms")
        conv = await engine.get_conversation_sentiment("esc")
        assert conv.escalation_risk > 0.3

    @pytest.mark.asyncio
    async def test_engagement_score_grows(self, engine):
        for i in range(8):
            await engine.analyze_message("eng", f"Tell me more about property {i}, how much?", "sms")
        conv = await engine.get_conversation_sentiment("eng")
        assert conv.engagement_score > 0.3

    @pytest.mark.asyncio
    async def test_empty_conversation(self, engine):
        conv = await engine.get_conversation_sentiment("empty")
        assert conv.message_count == 0
        assert conv.dominant_emotion == Emotion.NEUTRAL


# -------------------------------------------------------------------------
# Channel handling
# -------------------------------------------------------------------------

class TestChannels:
    @pytest.mark.asyncio
    async def test_voice_channel(self, engine):
        r = await engine.analyze_message("ch1", "I love it", "voice")
        assert r.channel == Channel.VOICE

    @pytest.mark.asyncio
    async def test_unknown_channel_defaults_sms(self, engine):
        r = await engine.analyze_message("ch2", "Hello", "pigeon_carrier")
        assert r.channel == Channel.SMS


# -------------------------------------------------------------------------
# History management
# -------------------------------------------------------------------------

class TestHistoryManagement:
    @pytest.mark.asyncio
    async def test_clear_specific_contact(self, engine):
        await engine.analyze_message("clear_me", "Hello", "sms")
        engine.clear_history("clear_me")
        conv = await engine.get_conversation_sentiment("clear_me")
        assert conv.message_count == 0

    @pytest.mark.asyncio
    async def test_clear_all(self, engine):
        await engine.analyze_message("a", "Hello", "sms")
        await engine.analyze_message("b", "Hi", "sms")
        engine.clear_history()
        assert len(engine._conversation_history) == 0
