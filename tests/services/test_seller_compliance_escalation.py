import pytest

pytestmark = pytest.mark.integration

"""Tests for structured compliance escalation service (seller bot integration)."""

from unittest.mock import AsyncMock, Mock

import pytest

from ghl_real_estate_ai.services.compliance_escalation import (
    ComplianceEscalationService,
    ViolationSeverity,
    ViolationType,
)


@pytest.mark.asyncio
async def test_fair_housing_violation_pauses_bot():
    """FAIR_HOUSING -> severity=CRITICAL, 'bot_paused' in actions."""
    service = ComplianceEscalationService()

    violation = await service.handle_violation(
        violation_type=ViolationType.FAIR_HOUSING,
        description="Discriminatory language detected in seller conversation",
        evidence="Message contained protected-class references",
        contact_id="seller_001",
        bot_type="seller",
    )

    assert violation.severity == ViolationSeverity.CRITICAL
    assert "bot_paused" in violation.actions_taken


@pytest.mark.asyncio
async def test_privacy_violation_logs_audit_trail():
    """PRIVACY -> logged, evidence preserved in violation object."""
    service = ComplianceEscalationService()

    violation = await service.handle_violation(
        violation_type=ViolationType.PRIVACY,
        description="PII exposed in seller communication",
        evidence="SSN found in message body",
        contact_id="seller_002",
        bot_type="seller",
    )

    assert "logged_violation" in violation.actions_taken
    assert violation.evidence == "SSN found in message body"
    assert violation.description == "PII exposed in seller communication"


@pytest.mark.asyncio
async def test_critical_severity_notifies_compliance_officer():
    """CRITICAL severity -> 'compliance_officer_notified' in actions."""
    service = ComplianceEscalationService()

    violation = await service.handle_violation(
        violation_type=ViolationType.FAIR_HOUSING,
        description="Fair housing violation requiring officer review",
        evidence="Steering language detected",
        contact_id="seller_003",
        bot_type="seller",
    )

    assert violation.severity == ViolationSeverity.CRITICAL
    assert "compliance_officer_notified" in violation.actions_taken


@pytest.mark.asyncio
async def test_crm_flagging_adds_tag():
    """Mock ghl_client, verify add_tags called with 'Compliance-Flagged'."""
    mock_ghl = AsyncMock()
    service = ComplianceEscalationService(ghl_client=mock_ghl)

    violation = await service.handle_violation(
        violation_type=ViolationType.FINANCIAL_REGULATION,
        description="Financial regulation concern",
        evidence="Unlicensed mortgage advice detected",
        contact_id="seller_004",
        bot_type="seller",
    )

    mock_ghl.add_tags.assert_awaited_once_with(
        "seller_004", ["Compliance-Flagged"]
    )
    assert "crm_flagged" in violation.actions_taken


@pytest.mark.asyncio
async def test_violation_evidence_preserved():
    """Evidence string stored in violation object unchanged."""
    service = ComplianceEscalationService()
    evidence_text = "Detailed evidence: seller disclosed protected info about neighbors"

    violation = await service.handle_violation(
        violation_type=ViolationType.LICENSING,
        description="Licensing issue in seller flow",
        evidence=evidence_text,
        contact_id="seller_005",
        bot_type="seller",
    )

    assert violation.evidence == evidence_text
    assert violation.contact_id == "seller_005"
    assert violation.bot_type == "seller"
    assert violation.violation_type == ViolationType.LICENSING
    assert violation.severity == ViolationSeverity.MEDIUM