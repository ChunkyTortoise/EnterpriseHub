from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.compliance_guard import ComplianceGuard, ComplianceStatus


@pytest.fixture
def guard():
    with patch("ghl_real_estate_ai.services.compliance_guard.LLMClient"):
        instance = ComplianceGuard()
    instance.llm_client = MagicMock()
    instance.llm_client.agenerate = AsyncMock()
    return instance


def test_ws5_fallback_messages_are_consultative_and_sms_safe(guard):
    seller = guard.get_safe_fallback_message("seller")
    buyer = guard.get_safe_fallback_message("buyer")
    lead = guard.get_safe_fallback_message("lead")

    assert "price" in seller.lower()
    assert "home" in buyer.lower() or "property" in buyer.lower()
    assert "help" in lead.lower()

    for message in (seller, buyer, lead):
        assert len(message) <= guard.SMS_MAX_LENGTH
        assert "-" not in message


@pytest.mark.asyncio
async def test_ws5_aggressive_tone_is_blocked_without_llm(guard):
    status, reason, violations = await guard.audit_message("Last chance. Take it or leave it.")

    assert status == ComplianceStatus.BLOCKED
    assert "tone" in reason.lower() or "pattern" in reason.lower()
    assert any("Aggressive tone match" in violation for violation in violations)
    guard.llm_client.agenerate.assert_not_called()


def test_ws5_sanitize_for_sms_removes_emoji_hyphen_and_truncates(guard):
    raw = "move-in ready! \U0001f3e0 " + ("Very long context sentence. " * 30)
    cleaned = guard.sanitize_for_sms(raw, max_length=160)

    assert len(cleaned) <= 160
    assert "\U0001f3e0" not in cleaned
    assert "-" not in cleaned


@pytest.mark.asyncio
async def test_ws5_empty_message_passes(guard):
    status, reason, violations = await guard.audit_message("   ")

    assert status == ComplianceStatus.PASSED
    assert violations == []
