"""Unit tests for RecordingManager — consent logic, AI disclosure, opening sequence."""

from __future__ import annotations

import pytest

from voice_ai.telephony.recording import (
    TWO_PARTY_CONSENT_STATES,
    RecordingManager,
)


@pytest.fixture
def manager():
    return RecordingManager(agency_name="Test Realty")


class TestAIDisclosure:
    def test_disclosure_includes_agency_name(self, manager):
        disclosure = manager.get_ai_disclosure()
        assert "Test Realty" in disclosure

    def test_disclosure_mentions_ai(self, manager):
        disclosure = manager.get_ai_disclosure()
        assert "AI" in disclosure


class TestConsentPrompt:
    def test_needs_consent_in_california(self, manager):
        assert manager.needs_consent_prompt("CA") is True

    def test_needs_consent_in_florida(self, manager):
        assert manager.needs_consent_prompt("FL") is True

    def test_no_consent_in_texas(self, manager):
        assert manager.needs_consent_prompt("TX") is False

    def test_case_insensitive_state(self, manager):
        assert manager.needs_consent_prompt("ca") is True

    def test_none_state_defaults_to_consent_required(self, manager):
        assert manager.needs_consent_prompt(None) is True

    def test_all_two_party_states_require_consent(self, manager):
        for state in TWO_PARTY_CONSENT_STATES:
            assert manager.needs_consent_prompt(state) is True

    def test_consent_prompt_text(self, manager):
        prompt = manager.get_consent_prompt()
        assert "recorded" in prompt.lower()
        assert "consent" in prompt.lower()


class TestConsentEvaluation:
    @pytest.mark.parametrize("response", [
        "Yes", "sure", "okay", "ok", "yeah", "yep", "absolutely", "go ahead",
    ])
    def test_positive_consent(self, manager, response):
        assert manager.evaluate_consent_response(response) is True

    @pytest.mark.parametrize("response", [
        "No", "nope", "I don't want that", "do not record", "refuse", "decline",
    ])
    def test_negative_consent(self, manager, response):
        assert manager.evaluate_consent_response(response) is False

    def test_unclear_response_returns_none(self, manager):
        result = manager.evaluate_consent_response("I need to think about it")
        assert result is None

    def test_empty_response_returns_none(self, manager):
        result = manager.evaluate_consent_response("")
        assert result is None


class TestOpeningSequence:
    def test_outbound_in_consent_state(self, manager):
        messages = manager.get_opening_sequence("outbound", "CA")
        assert len(messages) == 2  # AI disclosure + consent prompt
        assert "AI" in messages[0]
        assert "consent" in messages[1].lower()

    def test_outbound_in_non_consent_state(self, manager):
        messages = manager.get_opening_sequence("outbound", "TX")
        assert len(messages) == 1  # Only AI disclosure
        assert "AI" in messages[0]

    def test_inbound_in_consent_state(self, manager):
        messages = manager.get_opening_sequence("inbound", "CA")
        assert len(messages) == 1  # Only consent prompt
        assert "consent" in messages[0].lower()

    def test_inbound_in_non_consent_state(self, manager):
        messages = manager.get_opening_sequence("inbound", "TX")
        assert len(messages) == 0
