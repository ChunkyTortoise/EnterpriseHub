"""Unit tests for SDRMessagePersonalizer.

Tests Claude-powered SMS, email, and rebuttal personalization
with mocked LLMClient.agenerate().
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.sdr.message_personalizer import (
    SMS_MAX_CHARS,
    EmailContent,
    SDRMessagePersonalizer,
    _format_profile,
    _parse_email_response,
)

pytestmark = pytest.mark.unit


def _mock_llm(content: str) -> MagicMock:
    """Build a mock LLMClient whose agenerate returns the given content."""
    llm = MagicMock()
    response = MagicMock()
    response.content = content
    llm.agenerate = AsyncMock(return_value=response)
    return llm


@pytest.fixture
def lead_profile():
    return {
        "first_name": "Maria",
        "lead_type": "buyer",
        "source": "ghl_pipeline",
        "location": "Rancho Cucamonga",
        "frs_score": 72.5,
        "pcs_score": 65.0,
    }


# ---- personalize_sms ----


@pytest.mark.asyncio
async def test_personalize_sms_returns_under_limit(lead_profile):
    sms_text = "Hey Maria, curious if you're still exploring homes in RC? Happy to help!"
    llm = _mock_llm(sms_text)
    personalizer = SDRMessagePersonalizer(llm_client=llm)

    result = await personalizer.personalize_sms("day_1_sms", lead_profile)

    assert len(result) <= SMS_MAX_CHARS
    assert result == sms_text
    llm.agenerate.assert_awaited_once()


@pytest.mark.asyncio
async def test_personalize_sms_truncates_long_response(lead_profile):
    long_text = "A" * 200
    llm = _mock_llm(long_text)
    personalizer = SDRMessagePersonalizer(llm_client=llm)

    result = await personalizer.personalize_sms("day_1_sms", lead_profile)

    assert len(result) <= SMS_MAX_CHARS
    assert result.endswith("\u2026")


@pytest.mark.asyncio
async def test_personalize_sms_fallback_on_error(lead_profile):
    llm = MagicMock()
    llm.agenerate = AsyncMock(side_effect=RuntimeError("LLM down"))
    personalizer = SDRMessagePersonalizer(llm_client=llm)

    result = await personalizer.personalize_sms("day_1_sms", lead_profile)

    assert "Maria" in result
    assert len(result) <= SMS_MAX_CHARS


# ---- personalize_email ----


@pytest.mark.asyncio
async def test_personalize_email_parses_subject_and_body(lead_profile):
    email_text = "Subject: Your Rancho Cucamonga home search\n\nHi Maria,\n\nHope you're doing well!"
    llm = _mock_llm(email_text)
    personalizer = SDRMessagePersonalizer(llm_client=llm)

    result = await personalizer.personalize_email("day_3_email", lead_profile)

    assert isinstance(result, dict)
    assert result["subject"] == "Your Rancho Cucamonga home search"
    assert "Maria" in result["body"]


@pytest.mark.asyncio
async def test_personalize_email_fallback_on_error(lead_profile):
    llm = MagicMock()
    llm.agenerate = AsyncMock(side_effect=RuntimeError("LLM down"))
    personalizer = SDRMessagePersonalizer(llm_client=llm)

    result = await personalizer.personalize_email("day_3_email", lead_profile)

    assert isinstance(result, dict)
    assert "Maria" in result["body"]
    assert len(result["subject"]) > 0


# ---- personalize_rebuttal ----


@pytest.mark.asyncio
async def test_personalize_rebuttal_returns_text(lead_profile):
    rebuttal = "I totally understand, Maria. If things change, I'm always here to help!"
    llm = _mock_llm(rebuttal)
    personalizer = SDRMessagePersonalizer(llm_client=llm)

    result = await personalizer.personalize_rebuttal("timing", "maybe later", lead_profile)

    assert result == rebuttal
    llm.agenerate.assert_awaited_once()


# ---- helpers ----


def test_format_profile_empty():
    assert _format_profile({}) == "No profile data"


def test_parse_email_no_subject():
    content = "Just a plain body with no subject line."
    result = _parse_email_response(content)
    assert result.subject == "Following up on your real estate goals"
    assert "plain body" in result.body


@patch("ghl_real_estate_ai.services.sdr.message_personalizer.LLMClient")
def test_personalizer_creates_default_llm_client_when_none_provided(mock_llm_cls):
    """When no llm_client is passed, constructor creates a default LLMClient."""
    mock_instance = MagicMock()
    mock_llm_cls.return_value = mock_instance

    personalizer = SDRMessagePersonalizer()

    mock_llm_cls.assert_called_once()
    assert personalizer._llm is mock_instance
