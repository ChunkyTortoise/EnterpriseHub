"""Tests for the interactive chatbot demo widget."""

from __future__ import annotations

import pytest

from ghl_real_estate_ai.streamlit_demo.components.interactive_chatbot_demo import (
    BOT_TYPES,
    CANNED_RESPONSES,
    DEFAULT_RESPONSE,
    DEMO_QUESTIONS,
    InteractiveChatbotDemo,
    add_message,
    clear_messages,
    get_canned_response,
    get_demo_questions,
    init_session_state,
)

# ------------------------------------------------------------------
# Canned response lookup
# ------------------------------------------------------------------


class TestCannedResponseLookup:
    """Test the trigger-based canned response matching."""

    def test_exact_trigger_match(self):
        resp = get_canned_response("Lead Bot", "I'm looking to buy a home")
        assert "budget" in resp.lower() or "dream home" in resp.lower()

    def test_case_insensitive_match(self):
        resp = get_canned_response("Seller Bot", "What's My Home Worth?")
        assert "CMA" in resp

    def test_no_trigger_returns_default(self):
        resp = get_canned_response("Lead Bot", "random gibberish xyz")
        assert resp == DEFAULT_RESPONSE

    def test_unknown_bot_type_returns_default(self):
        resp = get_canned_response("Unknown Bot", "hello")
        assert resp == DEFAULT_RESPONSE

    def test_all_bot_types_have_responses(self):
        for bot_type in BOT_TYPES:
            assert bot_type in CANNED_RESPONSES
            assert len(CANNED_RESPONSES[bot_type]) > 0


# ------------------------------------------------------------------
# Message history management
# ------------------------------------------------------------------


class TestMessageHistory:
    """Test message history via session state helpers."""

    def test_add_message(self):
        session: dict = {}
        add_message(session, "user", "Hello")
        assert len(session["chatbot_messages"]) == 1
        assert session["chatbot_messages"][0] == {
            "role": "user",
            "content": "Hello",
        }

    def test_add_multiple_messages(self):
        session: dict = {}
        add_message(session, "user", "Hi")
        add_message(session, "assistant", "Hello!")
        add_message(session, "user", "How are you?")
        assert len(session["chatbot_messages"]) == 3
        assert session["chatbot_messages"][1]["role"] == "assistant"

    def test_clear_messages(self):
        session: dict = {}
        add_message(session, "user", "Hi")
        add_message(session, "assistant", "Hello!")
        clear_messages(session)
        assert session["chatbot_messages"] == []


# ------------------------------------------------------------------
# Bot type selection logic
# ------------------------------------------------------------------


class TestBotTypeSelection:
    """Test bot type selection and its effect on responses."""

    def test_bot_types_list(self):
        assert BOT_TYPES == ["Lead Bot", "Buyer Bot", "Seller Bot"]

    def test_different_bots_give_different_responses(self):
        msg = "I'm looking to buy a home"
        lead_resp = get_canned_response("Lead Bot", msg)
        buyer_resp = get_canned_response("Buyer Bot", msg)
        # Both should respond but with different text
        assert lead_resp != DEFAULT_RESPONSE
        assert buyer_resp != DEFAULT_RESPONSE
        assert lead_resp != buyer_resp

    def test_seller_bot_responds_to_seller_triggers(self):
        resp = get_canned_response("Seller Bot", "I want to sell my house")
        assert resp != DEFAULT_RESPONSE
        assert "sell" in resp.lower() or "timeline" in resp.lower()


# ------------------------------------------------------------------
# Demo question presets
# ------------------------------------------------------------------


class TestDemoQuestionPresets:
    """Test preset demo questions for each bot type."""

    def test_each_bot_has_presets(self):
        for bot_type in BOT_TYPES:
            questions = get_demo_questions(bot_type)
            assert len(questions) >= 3

    def test_unknown_bot_falls_back_to_lead(self):
        questions = get_demo_questions("Nonexistent Bot")
        assert questions == DEMO_QUESTIONS["Lead Bot"]

    def test_presets_are_strings(self):
        for bot_type in BOT_TYPES:
            for q in get_demo_questions(bot_type):
                assert isinstance(q, str)
                assert len(q) > 0


# ------------------------------------------------------------------
# Session state initialization
# ------------------------------------------------------------------


class TestSessionStateInit:
    """Test session state initialization."""

    def test_init_empty_session(self):
        session: dict = {}
        result = init_session_state(session)
        assert result is session
        assert session["chatbot_messages"] == []
        assert session["chatbot_bot_type"] == BOT_TYPES[0]
        assert session["chatbot_live_mode"] is False

    def test_init_preserves_existing_values(self):
        session: dict = {
            "chatbot_messages": [{"role": "user", "content": "Hi"}],
            "chatbot_bot_type": "Seller Bot",
            "chatbot_live_mode": True,
        }
        init_session_state(session)
        assert len(session["chatbot_messages"]) == 1
        assert session["chatbot_bot_type"] == "Seller Bot"
        assert session["chatbot_live_mode"] is True

    def test_interactive_chatbot_demo_defaults(self):
        demo = InteractiveChatbotDemo()
        assert demo.live_mode is False

    def test_interactive_chatbot_demo_live_mode(self):
        demo = InteractiveChatbotDemo(live_mode=True)
        assert demo.live_mode is True
