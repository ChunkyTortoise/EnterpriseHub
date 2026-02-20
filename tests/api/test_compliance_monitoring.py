"""
Tests for compliance monitoring background scanners (ROADMAP-041–044).
Validates real-time compliance scanning, security anomaly detection,
privacy request processing, and audit trail archival.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Stub heavy compliance sub-modules BEFORE importing the routes module.
# This must happen at module-load time so pytest collection succeeds.
# ---------------------------------------------------------------------------
_STUBS_APPLIED = False
_STUB_MODS = [
    "ghl_real_estate_ai.compliance",
    "ghl_real_estate_ai.compliance.audit_documentation_system",
    "ghl_real_estate_ai.compliance.compliance_automation_engine",
    "ghl_real_estate_ai.compliance.privacy_protection_system",
    "ghl_real_estate_ai.compliance.security_framework",
    "ghl_real_estate_ai.services.auth_service",
    "ghl_real_estate_ai.services.websocket_manager",
]

for _mod_name in _STUB_MODS:
    if _mod_name not in sys.modules:
        _m = MagicMock()
        _m.AuditEventType = MagicMock()
        _m.AuditSeverity = MagicMock()
        _m.DocumentType = MagicMock(side_effect=lambda x: x)
        _m.PrivacyRight = MagicMock(side_effect=lambda x: x)
        _m.PrivacyRegulation = MagicMock(side_effect=lambda x: x)
        sys.modules[_mod_name] = _m
        _STUBS_APPLIED = True

# Also clear any failed partial import of compliance routes
_compliance_route_key = "ghl_real_estate_ai.api.routes.compliance"
if _compliance_route_key in sys.modules and not hasattr(sys.modules[_compliance_route_key], "_check_tcpa_compliance"):
    del sys.modules[_compliance_route_key]

try:
    from ghl_real_estate_ai.api.routes.compliance import (
        _aggregate_and_archive_audit_trail,
        _check_dre_compliance,
        _check_fair_housing_compliance,
        _check_tcpa_compliance,
        _process_privacy_requests,
        _scan_compliance_violations,
        _scan_security_anomalies,
    )
except Exception as _e:
    pytest.skip(f"Cannot import compliance module: {_e}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Fake audit record
# ---------------------------------------------------------------------------
@dataclass
class FakeAuditRecord:
    record_id: str = "rec_001"
    timestamp: datetime = None
    event_type: str = "test"
    severity: str = "info"
    user_id: str = "user_1"
    action: str = "test_action"
    resource: str = "test_resource"
    result: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_audit():
    system = AsyncMock()
    system.search_audit_records = AsyncMock(return_value=[])
    system.log_audit_event = AsyncMock()
    system.create_compliance_document = AsyncMock()
    return system


@pytest.fixture
def mock_ws():
    mgr = AsyncMock()
    mgr.broadcast_to_group = AsyncMock()
    return mgr


@pytest.fixture
def mock_privacy():
    system = AsyncMock()
    system.process_privacy_request = AsyncMock()
    return system


# ===== ROADMAP-041: Compliance Violation Scanner =====

class TestTCPAComplianceCheck:

    async def test_no_violations_below_threshold(self, mock_audit):
        mock_audit.search_audit_records.side_effect = [
            [FakeAuditRecord()],
            [FakeAuditRecord()] * 100,
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            violations = await _check_tcpa_compliance()
        assert len(violations) == 0

    async def test_violation_above_threshold(self, mock_audit):
        mock_audit.search_audit_records.side_effect = [
            [FakeAuditRecord()] * 5,
            [FakeAuditRecord()] * 100,
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            violations = await _check_tcpa_compliance()
        assert len(violations) == 1
        assert violations[0]["type"] == "tcpa_opt_out_rate"
        assert violations[0]["rate_pct"] == 5.0

    async def test_no_division_error_zero_sent(self, mock_audit):
        mock_audit.search_audit_records.side_effect = [[], []]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            violations = await _check_tcpa_compliance()
        assert len(violations) == 0


class TestFairHousingCheck:

    async def test_clean_messages_no_violations(self, mock_audit):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(details={"content": "Great property at 123 Main St"})
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            violations = await _check_fair_housing_compliance()
        assert len(violations) == 0

    async def test_keyword_violation(self, mock_audit):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(details={"content": "great neighborhood for a specific race"})
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            violations = await _check_fair_housing_compliance()
        assert len(violations) == 1
        assert "race" in violations[0]["keywords"]


class TestDRECheck:

    async def test_human_agent_no_violation(self, mock_audit):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(user_id="agent_john")
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            violations = await _check_dre_compliance()
        assert len(violations) == 0

    async def test_bot_violation(self, mock_audit):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(user_id="bot_seller")
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            violations = await _check_dre_compliance()
        assert len(violations) >= 1
        assert violations[0]["type"] == "dre_unlicensed_action"


# ===== ROADMAP-042: Security Anomaly Detection =====

class TestSecurityAnomalies:

    async def test_below_threshold_no_alert(self, mock_audit, mock_ws):
        mock_audit.search_audit_records.side_effect = [
            [FakeAuditRecord()] * 3,
            [],
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit), \
             patch("ghl_real_estate_ai.api.routes.compliance.ws_manager", mock_ws):
            await _scan_security_anomalies()
        mock_ws.broadcast_to_group.assert_not_called()

    async def test_auth_failure_spike_alert(self, mock_audit, mock_ws):
        mock_audit.search_audit_records.side_effect = [
            [FakeAuditRecord()] * 10,
            [],
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit), \
             patch("ghl_real_estate_ai.api.routes.compliance.ws_manager", mock_ws):
            await _scan_security_anomalies()
        mock_ws.broadcast_to_group.assert_called_once()
        event = mock_ws.broadcast_to_group.call_args[0][1]["event"]
        assert event["type"] == "auth_failure_spike"

    async def test_pii_access_anomaly(self, mock_audit, mock_ws):
        mock_audit.search_audit_records.side_effect = [
            [],
            [FakeAuditRecord()] * 60,
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit), \
             patch("ghl_real_estate_ai.api.routes.compliance.ws_manager", mock_ws):
            await _scan_security_anomalies()
        assert mock_audit.log_audit_event.call_count >= 1


# ===== ROADMAP-043: Privacy Request Processing =====

class TestPrivacyRequests:

    async def test_no_pending_requests(self, mock_audit, mock_privacy):
        mock_audit.search_audit_records.return_value = []
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit), \
             patch("ghl_real_estate_ai.api.routes.compliance.privacy_system", mock_privacy):
            await _process_privacy_requests()
        mock_privacy.process_privacy_request.assert_not_called()

    async def test_deletion_request(self, mock_audit, mock_privacy):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(details={
                "request_type": "deletion",
                "subject_identifiers": {"email": "test@example.com"},
                "regulation": "gdpr",
            })
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit), \
             patch("ghl_real_estate_ai.api.routes.compliance.privacy_system", mock_privacy):
            await _process_privacy_requests()
        mock_privacy.process_privacy_request.assert_called_once()

    async def test_export_request(self, mock_audit, mock_privacy):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(details={
                "request_type": "export",
                "subject_identifiers": {"email": "export@example.com"},
                "regulation": "ccpa",
            })
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit), \
             patch("ghl_real_estate_ai.api.routes.compliance.privacy_system", mock_privacy):
            await _process_privacy_requests()
        mock_privacy.process_privacy_request.assert_called_once()


# ===== ROADMAP-044: Audit Trail Archival =====

class TestAuditArchival:

    async def test_no_old_records_nothing_archived(self, mock_audit):
        mock_audit.search_audit_records.return_value = []
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            await _aggregate_and_archive_audit_trail()
        mock_audit.create_compliance_document.assert_not_called()

    async def test_old_records_archived(self, mock_audit):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(record_id="old_001", timestamp=datetime.now() - timedelta(days=100)),
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            await _aggregate_and_archive_audit_trail()
        mock_audit.create_compliance_document.assert_called_once()
        assert mock_audit.log_audit_event.call_count >= 1

    async def test_multiple_records_archived(self, mock_audit):
        mock_audit.search_audit_records.return_value = [
            FakeAuditRecord(record_id=f"old_{i}") for i in range(3)
        ]
        with patch("ghl_real_estate_ai.api.routes.compliance.audit_system", mock_audit):
            await _aggregate_and_archive_audit_trail()
        assert mock_audit.create_compliance_document.call_count == 3
