from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus


@pytest.mark.asyncio
async def test_ws5_lead_compliance_fallback_applied_on_blocked(monkeypatch):
    bot = LeadBotWorkflow.__new__(LeadBotWorkflow)

    monkeypatch.setattr(
        "ghl_real_estate_ai.agents.lead_bot.compliance_guard.audit_message",
        AsyncMock(return_value=(ComplianceStatus.BLOCKED, "blocked", ["violation"])),
    )

    final_msg, meta = await bot._apply_outbound_compliance("This is your last chance", "lead-1")

    assert meta["compliance_fallback_applied"] is True
    assert meta["compliance_status"] == ComplianceStatus.BLOCKED.value
    assert "help" in final_msg.lower()
    assert len(final_msg) <= bot.SMS_MAX_LENGTH


@pytest.mark.asyncio
async def test_ws5_lead_compliance_keeps_consultative_message_when_passed(monkeypatch):
    bot = LeadBotWorkflow.__new__(LeadBotWorkflow)

    monkeypatch.setattr(
        "ghl_real_estate_ai.agents.lead_bot.compliance_guard.audit_message",
        AsyncMock(return_value=(ComplianceStatus.PASSED, "ok", [])),
    )

    final_msg, meta = await bot._apply_outbound_compliance("Happy to help with your goals.", "lead-2")

    assert meta["compliance_fallback_applied"] is False
    assert final_msg.startswith("Happy to help")


@pytest.mark.asyncio
async def test_ws5_buyer_compliance_fallback_applied_on_flagged(monkeypatch):
    bot = JorgeBuyerBot.__new__(JorgeBuyerBot)

    monkeypatch.setattr(
        "ghl_real_estate_ai.agents.jorge_buyer_bot.compliance_guard.audit_message",
        AsyncMock(return_value=(ComplianceStatus.FLAGGED, "flagged", ["implicit_bias"])),
    )

    payload = await bot._apply_outbound_compliance("Potentially risky message", "buyer-1")

    assert payload["compliance_fallback_applied"] is True
    assert payload["compliance_status"] == ComplianceStatus.FLAGGED.value
    assert "home" in payload["response_content"].lower() or "property" in payload["response_content"].lower()
    assert len(payload["response_content"]) <= bot.SMS_MAX_LENGTH


def test_ws5_buyer_sanitize_sms_response_removes_hyphen():
    bot = JorgeBuyerBot.__new__(JorgeBuyerBot)
    cleaned = bot._sanitize_sms_response("move-in ready option")

    assert "-" not in cleaned
    assert len(cleaned) <= bot.SMS_MAX_LENGTH
