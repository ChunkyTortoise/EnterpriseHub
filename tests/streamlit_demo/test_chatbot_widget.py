from __future__ import annotations
"""Tests for the chatbot widget component.

Uses unittest.mock.patch to replace the ``st`` reference inside the widget
module so that Streamlit session-state can be exercised without a running
Streamlit server -- and without polluting ``sys.modules`` for other tests.
"""

from unittest.mock import MagicMock, patch

import pytest

from streamlit_cloud.components.chatbot_widget import (

    MOCK_RESPONSES,
    SCORE_TRIGGERS,
    ChatbotWidget,
    QualificationScores,
)

# ---------------------------------------------------------------------------
# Shared mock for the ``st`` module reference used by chatbot_widget
# ---------------------------------------------------------------------------

_TARGET = "streamlit_cloud.components.chatbot_widget.st"


@pytest.fixture(autouse=True)
def mock_st():
    """Patch ``st`` inside the widget module for every test."""
    _mock = MagicMock()
    _mock.session_state = {}
    with patch(_TARGET, _mock):
        yield _mock


# ── QualificationScores ──────────────────────────────────────────────────────


class TestQualificationScores:
    def test_default_scores(self):
        scores = QualificationScores()
        assert scores.temperature == "Cold"
        assert scores.lead_score == 0
        assert scores.urgency == 0.0
        assert scores.motivation == 0.0
        assert scores.financial_readiness == 0.0
        assert scores.engagement_level == 0.0

    def test_temperature_color_hot(self):
        scores = QualificationScores(temperature="Hot")
        assert scores.temperature_color == "#FF4B4B"

    def test_temperature_color_warm(self):
        scores = QualificationScores(temperature="Warm")
        assert scores.temperature_color == "#FFA500"

    def test_temperature_color_cold(self):
        scores = QualificationScores(temperature="Cold")
        assert scores.temperature_color == "#4B9CD3"

    def test_temperature_emoji_hot(self):
        scores = QualificationScores(temperature="Hot")
        assert scores.temperature_emoji == "\U0001f525"

    def test_temperature_emoji_warm(self):
        scores = QualificationScores(temperature="Warm")
        assert scores.temperature_emoji == "\U0001f321\ufe0f"

    def test_temperature_emoji_cold(self):
        scores = QualificationScores(temperature="Cold")
        assert scores.temperature_emoji == "\u2744\ufe0f"

    def test_unknown_temperature_defaults(self):
        scores = QualificationScores(temperature="Unknown")
        assert scores.temperature_color == "#4B9CD3"
        assert scores.temperature_emoji == "\u2744\ufe0f"


# ── ChatbotWidget ────────────────────────────────────────────────────────────


class TestChatbotWidget:
    def test_init_session_state(self, mock_st):
        ChatbotWidget(industry="real_estate")
        assert "messages" in mock_st.session_state
        assert "bot_type" in mock_st.session_state
        assert "scores" in mock_st.session_state
        assert mock_st.session_state["bot_type"] == "lead"

    def test_industry_stored(self, mock_st):
        widget = ChatbotWidget(industry="dental")
        assert widget.industry == "dental"

    def test_default_industry(self, mock_st):
        widget = ChatbotWidget()
        assert widget.industry == "real_estate"

    def test_update_scores_hot_keyword(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores("I'm pre-approved and ready to buy this week")
        scores = mock_st.session_state["scores"]
        assert scores.lead_score > 0
        assert scores.temperature in ("Warm", "Hot")

    def test_update_scores_warm_keyword(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores("I'm interested and looking at my budget")
        scores = mock_st.session_state["scores"]
        assert scores.lead_score > 0

    def test_update_scores_financial_keyword(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores("I have a mortgage pre-approval for my down payment")
        scores = mock_st.session_state["scores"]
        assert scores.financial_readiness > 0.0

    def test_update_scores_urgency_keyword(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores("I need something urgent, relocating asap")
        scores = mock_st.session_state["scores"]
        assert scores.urgency > 0.0

    def test_update_scores_motivation_keyword(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores("We have a growing family and need our dream home")
        scores = mock_st.session_state["scores"]
        assert scores.motivation > 0.0

    def test_update_scores_buyer_detection(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores("I want to buy a house, I have pre-approval")
        assert mock_st.session_state["bot_type"] == "buyer"

    def test_update_scores_seller_detection(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores("I want to sell my home and need a CMA")
        assert mock_st.session_state["bot_type"] == "seller"

    def test_get_mock_response_real_estate(self, mock_st):
        widget = ChatbotWidget(industry="real_estate")
        mock_st.session_state["message_count"] = 0
        mock_st.session_state["industry"] = "real_estate"
        response = widget._get_mock_response()
        assert isinstance(response, str)
        assert len(response) > 0

    def test_get_mock_response_dental(self, mock_st):
        widget = ChatbotWidget(industry="dental")
        mock_st.session_state["message_count"] = 0
        mock_st.session_state["industry"] = "dental"
        response = widget._get_mock_response()
        assert "dental" in response.lower() or "Bright Smile" in response

    def test_get_mock_response_hvac(self, mock_st):
        widget = ChatbotWidget(industry="hvac")
        mock_st.session_state["message_count"] = 0
        mock_st.session_state["industry"] = "hvac"
        response = widget._get_mock_response()
        assert "HVAC" in response or "ComfortAir" in response

    def test_get_mock_response_fallback_to_lead(self, mock_st):
        """When bot_type has no responses, falls back to lead responses."""
        widget = ChatbotWidget(industry="dental")
        mock_st.session_state["message_count"] = 0
        mock_st.session_state["industry"] = "dental"
        mock_st.session_state["bot_type"] = "buyer"  # dental has empty buyer list
        response = widget._get_mock_response()
        assert isinstance(response, str)
        assert len(response) > 0

    def test_get_mock_response_unknown_industry_fallback(self, mock_st):
        """Unknown industry falls back to real_estate responses."""
        widget = ChatbotWidget(industry="unknown_industry")
        mock_st.session_state["message_count"] = 0
        mock_st.session_state["industry"] = "unknown_industry"
        response = widget._get_mock_response()
        assert isinstance(response, str)
        assert len(response) > 0

    def test_reset_clears_state(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["messages"] = [
            {"role": "user", "content": "hi"}
        ]
        mock_st.session_state["message_count"] = 5
        mock_st.session_state["scores"].lead_score = 80
        widget.reset()
        assert mock_st.session_state["messages"] == []
        assert mock_st.session_state["message_count"] == 0
        assert mock_st.session_state["scores"].lead_score == 0

    def test_score_caps_at_100(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        widget._update_scores(
            "pre-approved ready to buy schedule showing urgent "
            "immediately offer this week cash buyer"
        )
        scores = mock_st.session_state["scores"]
        assert scores.lead_score <= 100
        assert scores.urgency <= 1.0
        assert scores.financial_readiness <= 1.0
        assert scores.motivation <= 1.0

    def test_temperature_transitions(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 1
        scores = mock_st.session_state["scores"]

        # Start cold
        assert scores.temperature == "Cold"

        # Push into warm range
        widget._update_scores("I'm interested and looking with a budget")
        assert scores.temperature == "Cold" or scores.temperature == "Warm"

        # Push into hot range
        widget._update_scores(
            "pre-approved ready to buy schedule showing urgent immediately offer"
        )
        assert scores.temperature in ("Warm", "Hot")

    def test_engagement_level_from_message_count(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 5
        widget._update_scores("hello")
        scores = mock_st.session_state["scores"]
        assert scores.engagement_level == pytest.approx(0.5)

    def test_engagement_level_capped_at_1(self, mock_st):
        widget = ChatbotWidget()
        mock_st.session_state["message_count"] = 15
        widget._update_scores("hello")
        scores = mock_st.session_state["scores"]
        assert scores.engagement_level <= 1.0


# ── Data Structure Validation ────────────────────────────────────────────────


class TestMockData:
    def test_mock_responses_all_industries(self):
        for industry in ["real_estate", "dental", "hvac"]:
            assert industry in MOCK_RESPONSES
            assert "lead" in MOCK_RESPONSES[industry]

    def test_mock_responses_lead_not_empty(self):
        for industry in MOCK_RESPONSES:
            assert len(MOCK_RESPONSES[industry]["lead"]) > 0

    def test_score_triggers_defined(self):
        assert "hot_keywords" in SCORE_TRIGGERS
        assert "warm_keywords" in SCORE_TRIGGERS
        assert "financial_keywords" in SCORE_TRIGGERS
        assert "urgency_keywords" in SCORE_TRIGGERS
        assert "motivation_keywords" in SCORE_TRIGGERS

    def test_score_triggers_not_empty(self):
        for key, keywords in SCORE_TRIGGERS.items():
            assert len(keywords) > 0, f"{key} should have at least one keyword"

    def test_real_estate_has_all_bot_types(self):
        re_responses = MOCK_RESPONSES["real_estate"]
        assert "lead" in re_responses
        assert "buyer" in re_responses
        assert "seller" in re_responses
        assert len(re_responses["buyer"]) > 0
        assert len(re_responses["seller"]) > 0