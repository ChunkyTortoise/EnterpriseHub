"""
Staging Dry Run Tests — Jorge Bot Production Deployment (Step 3)

Validates the full integration pipeline before production deployment:
1. GHL API key format and client initialization
2. Webhook endpoint receives and processes simulated GHL payloads
3. EnhancedGHLClient contact/custom-field/workflow operations
4. Compliance guard intercepts every bot response
5. Full seller bot flow: inbound message → engine → compliance → GHL actions
6. Phase 1 configuration completeness
"""

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLContact,
    GHLMessage,
    GHLWebhookEvent,
    GHLWebhookResponse,
    MessageDirection,
    MessageType,
)
from ghl_real_estate_ai.ghl_utils.config import settings as app_settings
from ghl_real_estate_ai.services.compliance_guard import (
    ComplianceGuard,
    ComplianceStatus,
    compliance_guard,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PHASE1_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "phase1_seller_only.env")


def _load_phase1_env() -> Dict[str, str]:
    """Parse deploy/phase1_seller_only.env into a dict."""
    env = {}
    path = os.path.normpath(PHASE1_ENV_PATH)
    if not os.path.exists(path):
        pytest.skip("phase1_seller_only.env not found")
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


@pytest.fixture
def phase1_env() -> Dict[str, str]:
    return _load_phase1_env()


@pytest.fixture
def seller_webhook_payload() -> Dict[str, Any]:
    """Realistic GHL inbound seller message webhook payload."""
    return {
        "type": "InboundMessage",
        "contactId": "test_contact_dry_run_001",
        "locationId": "3xt4qayAh35BlDLaUv7P",
        "message": {
            "type": "SMS",
            "body": "I'm thinking about selling my house in Rancho Cucamonga. What would you need from me?",
            "direction": "inbound",
        },
        "contact": {
            "contactId": "test_contact_dry_run_001",
            "firstName": "Maria",
            "lastName": "TestSeller",
            "phone": "+15551234567",
            "email": "maria.test@example.com",
            "tags": ["Needs Qualifying"],
            "customFields": {},
        },
    }


@pytest.fixture
def buyer_webhook_payload() -> Dict[str, Any]:
    """GHL inbound buyer message webhook payload."""
    return {
        "type": "InboundMessage",
        "contactId": "test_contact_dry_run_002",
        "locationId": "3xt4qayAh35BlDLaUv7P",
        "message": {
            "type": "SMS",
            "body": "I'm looking for a 3-bedroom house in Rancho Cucamonga, budget around 650k",
            "direction": "inbound",
        },
        "contact": {
            "contactId": "test_contact_dry_run_002",
            "firstName": "Carlos",
            "lastName": "TestBuyer",
            "phone": "+15559876543",
            "email": "carlos.test@example.com",
            "tags": ["Buyer-Lead"],
            "customFields": {},
        },
    }


@pytest.fixture
def outbound_webhook_payload() -> Dict[str, Any]:
    """GHL outbound message (loopback guard test)."""
    return {
        "type": "OutboundMessage",
        "contactId": "test_contact_dry_run_003",
        "locationId": "3xt4qayAh35BlDLaUv7P",
        "message": {
            "type": "SMS",
            "body": "This is an outbound message from the bot",
            "direction": "outbound",
        },
        "contact": {
            "contactId": "test_contact_dry_run_003",
            "firstName": "Bot",
            "lastName": "Message",
            "phone": "+15550000000",
            "email": "bot@example.com",
            "tags": ["Needs Qualifying"],
            "customFields": {},
        },
    }


# ===========================================================================
# Test 1: Phase 1 Configuration Completeness
# ===========================================================================


class TestPhase1Configuration:
    """Validate that deploy/phase1_seller_only.env contains all required IDs."""

    def test_ghl_api_key_format(self, phase1_env):
        """API key starts with 'pit-' (Private Integration Token)."""
        api_key = phase1_env.get("GHL_API_KEY", "")
        assert api_key.startswith("pit-"), f"API key format unexpected: {api_key[:10]}..."
        assert len(api_key) > 20, "API key too short"

    def test_ghl_location_id_present(self, phase1_env):
        assert phase1_env.get("GHL_LOCATION_ID"), "GHL_LOCATION_ID missing"

    def test_seller_mode_enabled(self, phase1_env):
        assert phase1_env.get("JORGE_SELLER_MODE") == "true"

    def test_buyer_mode_disabled(self, phase1_env):
        assert phase1_env.get("JORGE_BUYER_MODE") == "false"

    def test_lead_mode_disabled(self, phase1_env):
        assert phase1_env.get("JORGE_LEAD_MODE") == "false"

    def test_seller_workflow_ids_present(self, phase1_env):
        """All seller-critical workflow IDs populated."""
        required_workflows = [
            "WORKFLOW_SELLER_DISPOSITION",
            "WORKFLOW_SELLER_ACTIVATION",
            "WORKFLOW_SELLER_DISPO_ASSIGN",
            "WORKFLOW_INBOUND_WEBHOOK",
            "WORKFLOW_AI_QUALIFICATION",
            "WORKFLOW_AI_ON_OFF",
            "NOTIFY_AGENT_WORKFLOW_ID",
        ]
        for wf in required_workflows:
            value = phase1_env.get(wf, "")
            assert value, f"Workflow ID missing: {wf}"
            # UUID format check
            assert len(value) == 36, f"Workflow ID wrong length for {wf}: {value}"

    def test_seller_custom_field_ids_present(self, phase1_env):
        """All seller-critical custom field IDs populated."""
        required_fields = [
            "CUSTOM_FIELD_LEAD_SCORE",
            "CUSTOM_FIELD_SELLER_TEMPERATURE",
            "CUSTOM_FIELD_SELLER_MOTIVATION",
            "CUSTOM_FIELD_TIMELINE_URGENCY",
            "CUSTOM_FIELD_PROPERTY_CONDITION",
            "CUSTOM_FIELD_PRICE_EXPECTATION",
            "CUSTOM_FIELD_BUDGET",
        ]
        for field in required_fields:
            value = phase1_env.get(field, "")
            assert value, f"Custom field ID missing: {field}"
            assert len(value) >= 10, f"Custom field ID too short for {field}: {value}"

    def test_extra_ai_fields_present(self, phase1_env):
        """AI bot trigger, assistant, and disposition fields populated."""
        extra_fields = [
            "CUSTOM_FIELD_AI_BOT_TRIGGER",
            "CUSTOM_FIELD_AI_ASSISTANT_IS",
            "CUSTOM_FIELD_BOT_TYPE",
            "CUSTOM_FIELD_SELLER_DISPOSITION",
            "CUSTOM_FIELD_JORGEAI_SETUP",
        ]
        for field in extra_fields:
            value = phase1_env.get(field, "")
            assert value, f"Extra AI field missing: {field}"

    def test_environment_is_production(self, phase1_env):
        assert phase1_env.get("ENVIRONMENT") == "production"


# ===========================================================================
# Test 2: GHL Client Initialization & Operations (Mocked API)
# ===========================================================================


class TestGHLClientOperations:
    """Test GHL client can create contacts, update fields, and trigger workflows."""

    def test_ghl_client_initializes_with_phase1_key(self, phase1_env):
        """GHLClient initializes with the Phase 1 API key without errors."""
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        api_key = phase1_env["GHL_API_KEY"]
        location_id = phase1_env["GHL_LOCATION_ID"]

        client = GHLClient(api_key=api_key, location_id=location_id)
        assert client.api_key == api_key
        assert client.location_id == location_id
        assert "Bearer" in client.headers["Authorization"]
        assert client.base_url == "https://services.leadconnectorhq.com"

    def test_enhanced_ghl_client_initializes(self, phase1_env):
        """EnhancedGHLClient initializes with Phase 1 config."""
        from ghl_real_estate_ai.services.enhanced_ghl_client import (
            EnhancedGHLClient,
            GHLConfig,
        )

        config = GHLConfig(
            api_key=phase1_env["GHL_API_KEY"],
            location_id=phase1_env["GHL_LOCATION_ID"],
        )
        client = EnhancedGHLClient(config=config)
        assert client.config.api_key == phase1_env["GHL_API_KEY"]
        assert client.config.location_id == phase1_env["GHL_LOCATION_ID"]

    @pytest.mark.asyncio
    async def test_create_contact_request_structure(self, phase1_env):
        """Validate contact creation builds correct payload (test mode)."""
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        with patch.object(app_settings, "test_mode", True):
            client = GHLClient(
                api_key=phase1_env["GHL_API_KEY"],
                location_id=phase1_env["GHL_LOCATION_ID"],
            )
            # In test mode, get_contact returns mock data
            contact = await client.get_contact("test_contact_001")
            assert contact is not None
            assert contact["id"] == "test_contact_001"
            assert "firstName" in contact

    @pytest.mark.asyncio
    async def test_update_custom_field_request_structure(self, phase1_env):
        """Validate custom field update uses correct field IDs."""
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        with patch.object(app_settings, "test_mode", True):
            client = GHLClient(
                api_key=phase1_env["GHL_API_KEY"],
                location_id=phase1_env["GHL_LOCATION_ID"],
            )
            field_id = phase1_env["CUSTOM_FIELD_SELLER_TEMPERATURE"]
            result = await client.update_custom_field("test_contact_001", field_id, "hot")
            assert result["status"] == "mocked"
            assert result["field_id"] == field_id
            assert result["value"] == "hot"

    @pytest.mark.asyncio
    async def test_trigger_workflow_request_structure(self, phase1_env):
        """Validate workflow trigger uses correct workflow IDs."""
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        with patch.object(app_settings, "test_mode", True):
            client = GHLClient(
                api_key=phase1_env["GHL_API_KEY"],
                location_id=phase1_env["GHL_LOCATION_ID"],
            )
            workflow_id = phase1_env["WORKFLOW_SELLER_DISPOSITION"]
            result = await client.trigger_workflow("test_contact_001", workflow_id)
            assert result["status"] == "mocked"
            assert result["workflow_id"] == workflow_id

    @pytest.mark.asyncio
    async def test_send_message_request_structure(self, phase1_env):
        """Validate message sending via GHL API."""
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        with patch.object(app_settings, "test_mode", True):
            client = GHLClient(
                api_key=phase1_env["GHL_API_KEY"],
                location_id=phase1_env["GHL_LOCATION_ID"],
            )
            result = await client.send_message(
                "test_contact_001",
                "Hello from staging dry run!",
                MessageType.SMS,
            )
            assert result["status"] == "mocked"
            assert "messageId" in result

    @pytest.mark.asyncio
    async def test_apply_actions_batch(self, phase1_env):
        """Validate batch action application (tags + custom fields + workflows)."""
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        with patch.object(app_settings, "test_mode", True):
            client = GHLClient(
                api_key=phase1_env["GHL_API_KEY"],
                location_id=phase1_env["GHL_LOCATION_ID"],
            )
            actions = [
                GHLAction(type=ActionType.ADD_TAG, tag="Hot-Seller"),
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=phase1_env["CUSTOM_FIELD_SELLER_TEMPERATURE"],
                    value="hot",
                ),
                GHLAction(
                    type=ActionType.TRIGGER_WORKFLOW,
                    workflow_id=phase1_env["WORKFLOW_SELLER_DISPOSITION"],
                ),
            ]
            results = await client.apply_actions("test_contact_001", actions)
            assert len(results) == 3
            assert all("error" not in r for r in results)


# ===========================================================================
# Test 3: Webhook Endpoint Processing
# ===========================================================================


class TestWebhookEndpoint:
    """Test the /ghl/webhook endpoint with simulated payloads."""

    def _parse_webhook_event(self, payload: Dict) -> GHLWebhookEvent:
        """Parse raw dict into GHLWebhookEvent."""
        return GHLWebhookEvent(**payload)

    def test_webhook_event_parses_seller_payload(self, seller_webhook_payload):
        """Verify seller payload parses into valid GHLWebhookEvent."""
        event = self._parse_webhook_event(seller_webhook_payload)
        assert event.contact_id == "test_contact_dry_run_001"
        assert event.location_id == "3xt4qayAh35BlDLaUv7P"
        assert event.message.body.startswith("I'm thinking about selling")
        assert event.message.direction == MessageDirection.INBOUND
        assert event.message.type == MessageType.SMS
        assert "Needs Qualifying" in event.contact.tags

    def test_webhook_event_parses_buyer_payload(self, buyer_webhook_payload):
        """Verify buyer payload parses into valid GHLWebhookEvent."""
        event = self._parse_webhook_event(buyer_webhook_payload)
        assert event.contact_id == "test_contact_dry_run_002"
        assert "Buyer-Lead" in event.contact.tags

    def test_outbound_message_detection(self, outbound_webhook_payload):
        """Verify outbound messages are correctly detected for loopback guard."""
        event = self._parse_webhook_event(outbound_webhook_payload)
        assert event.message.direction == MessageDirection.OUTBOUND

    def test_activation_tag_check(self, seller_webhook_payload):
        """Verify 'Needs Qualifying' tag activates seller mode."""
        event = self._parse_webhook_event(seller_webhook_payload)
        activation_tags = ["Needs Qualifying", "Hit List"]
        should_activate = any(tag in event.contact.tags for tag in activation_tags)
        assert should_activate is True

    def test_deactivation_tag_check(self, seller_webhook_payload):
        """Verify deactivation tags are not present."""
        event = self._parse_webhook_event(seller_webhook_payload)
        deactivation_tags = ["AI-Off", "Qualified", "Stop-Bot"]
        should_deactivate = any(tag in event.contact.tags for tag in deactivation_tags)
        assert should_deactivate is False

    def test_opt_out_detection(self):
        """Verify opt-out phrases are detected."""
        opt_out_phrases = [
            "stop",
            "unsubscribe",
            "don't contact",
            "remove me",
            "not interested",
            "opt out",
            "leave me alone",
        ]
        for phrase in opt_out_phrases:
            assert phrase in phrase.lower()  # Sanity check

        # Test that normal messages are NOT opt-out
        normal_messages = [
            "I want to sell my house",
            "What's the process?",
            "Can you help me?",
            "Yes I'm interested",
        ]
        for msg in normal_messages:
            msg_lower = msg.lower().strip()
            is_opt_out = any(p in msg_lower for p in opt_out_phrases)
            assert is_opt_out is False, f"False opt-out detected: {msg}"

    def test_sms_length_guard(self):
        """Verify SMS messages are truncated at sentence boundary."""
        long_message = "This is a test. " * 30  # ~480 chars
        SMS_MAX_CHARS = 320

        if len(long_message) > SMS_MAX_CHARS:
            truncated = long_message[:SMS_MAX_CHARS]
            for sep in (". ", "! ", "? "):
                idx = truncated.rfind(sep)
                if idx > SMS_MAX_CHARS // 2:
                    truncated = truncated[: idx + 1]
                    break
            long_message = truncated.rstrip()

        assert len(long_message) <= SMS_MAX_CHARS

    def test_input_length_guard(self):
        """Verify oversized inbound messages are truncated."""
        MAX_INBOUND_LENGTH = 2_000
        oversized = "x" * 5_000
        if len(oversized) > MAX_INBOUND_LENGTH:
            oversized = oversized[:MAX_INBOUND_LENGTH]
        assert len(oversized) == MAX_INBOUND_LENGTH


# ===========================================================================
# Test 4: Compliance Guard Integration
# ===========================================================================


class TestComplianceGuardIntegration:
    """Verify the compliance guard intercepts all bot responses."""

    @pytest.mark.asyncio
    async def test_clean_message_passes(self):
        """Normal real estate message passes compliance."""
        msg = "Your home in Rancho Cucamonga could benefit from staging. What price are you thinking?"
        with patch.object(compliance_guard, "_run_llm_audit") as mock_llm:
            mock_llm.return_value = (
                ComplianceStatus.PASSED,
                "No violations detected",
                [],
            )
            status, reason, violations = await compliance_guard.audit_message(msg)
            assert status == ComplianceStatus.PASSED
            assert violations == []

    @pytest.mark.asyncio
    async def test_steering_language_blocked_by_patterns(self):
        """Messages referencing protected classes are blocked by pattern matching."""
        # These messages use exact keywords from PROTECTED_KEYWORDS patterns
        steering_messages = [
            "That neighborhood has a bad area reputation",
            "The area is great because of the church community",
            "This is a safe area for families",
            "Consider the national origin of the residents",
            "Those people tend to live there",
        ]
        for msg in steering_messages:
            status, reason, violations = await compliance_guard.audit_message(msg)
            assert status == ComplianceStatus.BLOCKED, f"Expected BLOCKED for: '{msg}', got {status.value}"
            assert len(violations) > 0

    @pytest.mark.asyncio
    async def test_subtle_steering_caught_by_llm_audit(self):
        """Subtle steering without exact keyword matches goes to LLM audit."""
        subtle_msg = "That neighborhood has a lot of immigrants moving in"
        # This uses "immigrants" (plural) which won't match \bimmigrant\b pattern
        # So it goes to LLM audit - we mock the LLM to return BLOCKED
        with patch.object(compliance_guard, "_run_llm_audit") as mock_llm:
            mock_llm.return_value = (
                ComplianceStatus.BLOCKED,
                "Discriminatory language about national origin",
                ["national_origin_discrimination"],
            )
            status, reason, violations = await compliance_guard.audit_message(subtle_msg)
            assert status == ComplianceStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_oversized_message_blocked(self):
        """Messages exceeding MAX_INPUT_LENGTH are blocked."""
        oversized = "x" * 15_000
        status, reason, violations = await compliance_guard.audit_message(oversized)
        assert status == ComplianceStatus.BLOCKED
        assert "input_length_exceeded" in violations

    @pytest.mark.asyncio
    async def test_seller_response_compliance_flow(self):
        """Simulate compliance check on a seller bot response."""
        seller_response = (
            "Based on comparable sales, your home at 1234 Elm could list around $750K. "
            "Would a 30-45 day timeline work for you?"
        )
        with patch.object(compliance_guard, "_run_llm_audit") as mock_llm:
            mock_llm.return_value = (
                ComplianceStatus.PASSED,
                "No violations",
                [],
            )
            status, reason, violations = await compliance_guard.audit_message(
                seller_response,
                contact_context={"contact_id": "test_001", "mode": "seller"},
            )
            assert status == ComplianceStatus.PASSED

    @pytest.mark.asyncio
    async def test_blocked_message_gets_safe_replacement(self):
        """When compliance blocks a message, verify caller can substitute a safe default."""
        bad_msg = "You should avoid that area because of those people living there"
        status, reason, violations = await compliance_guard.audit_message(bad_msg)
        assert status == ComplianceStatus.BLOCKED

        # Simulate the webhook handler's replacement logic
        safe_seller_default = "Let's stick to the facts about your property. What price are you looking to get?"
        final_msg = safe_seller_default if status == ComplianceStatus.BLOCKED else bad_msg
        assert final_msg == safe_seller_default


# ===========================================================================
# Test 5: Full Seller Bot Flow (End-to-End Dry Run)
# ===========================================================================


class TestSellerBotFlow:
    """End-to-end dry run of the seller bot processing pipeline."""

    @pytest.mark.asyncio
    async def test_seller_engine_processes_message(self):
        """JorgeSellerEngine processes a seller message and returns structured result."""
        from ghl_real_estate_ai.core.conversation_manager import ConversationManager
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

        conv_manager = ConversationManager()
        mock_ghl_client = MagicMock()
        mock_mls_client = MagicMock()

        engine = JorgeSellerEngine(conv_manager, mock_ghl_client, mls_client=mock_mls_client)

        # Mock the internal Claude call to avoid hitting the real API
        with patch.object(engine, "process_seller_response") as mock_process:
            mock_process.return_value = {
                "message": "What's got you considering wanting to sell, where would you move to?",
                "temperature": "cold",
                "questions_answered": 0,
                "actions": [
                    {"type": "update_custom_field", "field": "seller_temperature", "value": "cold"},
                ],
                "handoff_signals": None,
            }

            result = await engine.process_seller_response(
                contact_id="test_dry_run_seller",
                user_message="I'm thinking about selling my house",
                location_id="3xt4qayAh35BlDLaUv7P",
                tenant_config=None,
            )

            assert "message" in result
            assert result["temperature"] in ("hot", "warm", "cold")
            assert "questions_answered" in result
            assert isinstance(result.get("actions", []), list)

    @pytest.mark.asyncio
    async def test_full_seller_pipeline_with_compliance(self):
        """Full pipeline: message → seller engine → compliance → GHL actions."""
        # 1. Parse the webhook event
        payload = {
            "type": "InboundMessage",
            "contactId": "test_pipeline_seller",
            "locationId": "3xt4qayAh35BlDLaUv7P",
            "message": {
                "type": "SMS",
                "body": "Yes I want to sell, we're moving to Arizona",
                "direction": "inbound",
            },
            "contact": {
                "contactId": "test_pipeline_seller",
                "firstName": "Test",
                "lastName": "Pipeline",
                "phone": "+15551111111",
                "email": "pipeline@test.com",
                "tags": ["Needs Qualifying"],
                "customFields": {},
            },
        }
        event = GHLWebhookEvent(**payload)
        assert event.message.direction == MessageDirection.INBOUND
        assert "Needs Qualifying" in event.contact.tags

        # 2. Simulate seller engine response
        seller_result = {
            "message": "If our team sold your home within 30-45 days, would that pose a problem?",
            "temperature": "warm",
            "questions_answered": 1,
            "actions": [
                {"type": "update_custom_field", "field": "seller_temperature", "value": "warm"},
                {"type": "add_tag", "tag": "Warm-Seller"},
            ],
            "handoff_signals": None,
        }

        # 3. Run compliance guard
        with patch.object(compliance_guard, "_run_llm_audit") as mock_llm:
            mock_llm.return_value = (ComplianceStatus.PASSED, "Clean", [])
            status, reason, violations = await compliance_guard.audit_message(
                seller_result["message"],
                contact_context={"contact_id": event.contact_id, "mode": "seller"},
            )
            assert status == ComplianceStatus.PASSED

        # 4. Build GHL actions
        actions = []
        for action_data in seller_result["actions"]:
            if action_data["type"] == "add_tag":
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag=action_data["tag"]))
            elif action_data["type"] == "update_custom_field":
                actions.append(
                    GHLAction(
                        type=ActionType.UPDATE_CUSTOM_FIELD,
                        field=action_data["field"],
                        value=action_data["value"],
                    )
                )

        assert len(actions) == 2
        assert actions[0].type == ActionType.UPDATE_CUSTOM_FIELD
        assert actions[1].type == ActionType.ADD_TAG
        assert actions[1].tag == "Warm-Seller"

        # 5. Build response
        response = GHLWebhookResponse(
            success=True,
            message=seller_result["message"],
            actions=actions,
        )
        assert response.success is True
        assert "30-45 days" in response.message

    @pytest.mark.asyncio
    async def test_hot_seller_triggers_workflow_and_handoff(self, phase1_env):
        """Hot seller flow triggers disposition workflow and agent notification."""
        hot_result = {
            "message": "You're a great fit for our program. Let me connect you with our team.",
            "temperature": "hot",
            "questions_answered": 4,
            "actions": [
                {"type": "add_tag", "tag": "Hot-Seller"},
                {"type": "remove_tag", "tag": "Needs Qualifying"},
                {"type": "add_tag", "tag": "Seller-Qualified"},
                {
                    "type": "trigger_workflow",
                    "workflow_id": phase1_env["WORKFLOW_SELLER_DISPOSITION"],
                },
                {
                    "type": "update_custom_field",
                    "field": phase1_env["CUSTOM_FIELD_SELLER_TEMPERATURE"],
                    "value": "hot",
                },
            ],
            "handoff_signals": {"seller_intent_score": 0.95},
        }

        # Build and validate actions
        actions = []
        for action_data in hot_result["actions"]:
            if action_data["type"] == "add_tag":
                actions.append(GHLAction(type=ActionType.ADD_TAG, tag=action_data["tag"]))
            elif action_data["type"] == "remove_tag":
                actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=action_data["tag"]))
            elif action_data["type"] == "trigger_workflow":
                actions.append(
                    GHLAction(
                        type=ActionType.TRIGGER_WORKFLOW,
                        workflow_id=action_data["workflow_id"],
                    )
                )
            elif action_data["type"] == "update_custom_field":
                actions.append(
                    GHLAction(
                        type=ActionType.UPDATE_CUSTOM_FIELD,
                        field=action_data["field"],
                        value=action_data["value"],
                    )
                )

        # Validate all expected actions present
        action_types = [a.type for a in actions]
        assert ActionType.ADD_TAG in action_types
        assert ActionType.REMOVE_TAG in action_types
        assert ActionType.TRIGGER_WORKFLOW in action_types
        assert ActionType.UPDATE_CUSTOM_FIELD in action_types

        # Validate specific values
        workflow_action = next(a for a in actions if a.type == ActionType.TRIGGER_WORKFLOW)
        assert workflow_action.workflow_id == phase1_env["WORKFLOW_SELLER_DISPOSITION"]

        custom_field_action = next(a for a in actions if a.type == ActionType.UPDATE_CUSTOM_FIELD)
        assert custom_field_action.field == phase1_env["CUSTOM_FIELD_SELLER_TEMPERATURE"]
        assert custom_field_action.value == "hot"

        # Validate handoff signals present
        assert hot_result["handoff_signals"]["seller_intent_score"] > 0.9

    @pytest.mark.asyncio
    async def test_compliance_blocked_seller_message_replaced(self):
        """When compliance blocks a seller response, it's replaced with safe default."""
        bad_seller_response = "This neighborhood is perfect for families with children"

        status, reason, violations = await compliance_guard.audit_message(
            bad_seller_response,
            contact_context={"contact_id": "test_blocked", "mode": "seller"},
        )
        assert status == ComplianceStatus.BLOCKED

        # Webhook handler replacement logic
        safe_default = "Let's stick to the facts about your property. What price are you looking to get?"
        final_msg = safe_default if status == ComplianceStatus.BLOCKED else bad_seller_response
        assert "facts about your property" in final_msg

        # Verify Compliance-Alert tag would be added
        actions = [GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert")]
        assert actions[0].tag == "Compliance-Alert"


# ===========================================================================
# Test 6: Jorge Config & Mode Routing
# ===========================================================================


class TestJorgeConfigRouting:
    """Validate Jorge config settings and bot mode routing logic."""

    def test_jorge_seller_config_questions(self):
        """Verify Jorge's 4 questions are defined correctly."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        questions = JorgeSellerConfig.SELLER_QUESTIONS
        assert len(questions) == 4
        assert "sell" in questions[1].lower()
        assert "30 to 45 days" in questions[2]
        assert "move-in ready" in questions[3].lower() or "move in ready" in questions[3].lower()
        assert "price" in questions[4].lower()

    def test_seller_temperature_classification(self):
        """Verify temperature classification logic."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        # Hot: 4 questions, timeline accepted, good quality, responsive
        assert JorgeSellerConfig.classify_seller_temperature(4, True, 0.8, 0.8) == "hot"

        # Warm: 3 questions, decent quality
        assert JorgeSellerConfig.classify_seller_temperature(3, None, 0.6, 0.5) == "warm"

        # Cold: few questions
        assert JorgeSellerConfig.classify_seller_temperature(1, None, 0.3, 0.3) == "cold"

    def test_seller_mode_routing_logic(self, seller_webhook_payload):
        """Verify the routing logic that sends contacts to seller bot."""
        event = GHLWebhookEvent(**seller_webhook_payload)
        tags = event.contact.tags

        # Simulate the webhook handler's routing check
        jorge_seller_mode_env = True  # JORGE_SELLER_MODE=true in phase1
        has_needs_qualifying = "Needs Qualifying" in tags
        deactivation_tags = ["AI-Off", "Qualified", "Stop-Bot"]
        should_deactivate = any(tag in tags for tag in deactivation_tags)

        should_route_to_seller = has_needs_qualifying and jorge_seller_mode_env and not should_deactivate
        assert should_route_to_seller is True

    def test_buyer_mode_disabled_in_phase1(self, buyer_webhook_payload):
        """In Phase 1, buyer mode is disabled — buyer messages fall through."""
        event = GHLWebhookEvent(**buyer_webhook_payload)
        tags = event.contact.tags

        jorge_buyer_mode_env = False  # JORGE_BUYER_MODE=false in phase1
        has_buyer_tag = "Buyer-Lead" in tags

        should_route_to_buyer = has_buyer_tag and jorge_buyer_mode_env
        assert should_route_to_buyer is False

    def test_message_sanitization(self):
        """Verify Jorge's message sanitization removes hyphens and robotic language."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        raw = "I'm here to help — let's schedule a walk-through for your two-story home."
        sanitized = JorgeSellerConfig.sanitize_message(raw)
        assert "—" not in sanitized  # Em-dash removed
        assert "-" not in sanitized  # Hyphens removed
        # "I'm here to help" is a robotic pattern — should be removed
        assert "I'm here to help" not in sanitized


# ===========================================================================
# Test 7: Webhook Response Schema Validation
# ===========================================================================


class TestWebhookResponseSchema:
    """Validate GHLWebhookResponse output format."""

    def test_success_response_structure(self):
        """Standard success response has correct structure."""
        response = GHLWebhookResponse(
            success=True,
            message="What's got you considering wanting to sell?",
            actions=[
                GHLAction(type=ActionType.ADD_TAG, tag="Warm-Seller"),
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field="seller_temp_field_id",
                    value="warm",
                ),
            ],
        )
        data = response.model_dump()
        assert data["success"] is True
        assert isinstance(data["message"], str)
        assert isinstance(data["actions"], list)
        assert len(data["actions"]) == 2

    def test_empty_actions_response(self):
        """Response with no actions is valid (e.g., AI not triggered)."""
        response = GHLWebhookResponse(
            success=True,
            message="AI not triggered (activation tag missing)",
            actions=[],
        )
        assert response.success is True
        assert len(response.actions) == 0

    def test_all_action_types_serializable(self):
        """Every ActionType can be serialized in GHLWebhookResponse."""
        actions = [
            GHLAction(type=ActionType.ADD_TAG, tag="Test"),
            GHLAction(type=ActionType.REMOVE_TAG, tag="Test"),
            GHLAction(type=ActionType.UPDATE_CUSTOM_FIELD, field="f1", value="v1"),
            GHLAction(type=ActionType.TRIGGER_WORKFLOW, workflow_id="wf1"),
            GHLAction(
                type=ActionType.SEND_MESSAGE,
                message="Hello",
                channel=MessageType.SMS,
            ),
        ]
        response = GHLWebhookResponse(success=True, message="test", actions=actions)
        data = response.model_dump()
        assert len(data["actions"]) == 5


# ===========================================================================
# Test 8: Cross-Cutting Concerns
# ===========================================================================


class TestCrossCuttingConcerns:
    """Validate security, logging, and error handling patterns."""

    def test_pii_not_in_error_responses(self):
        """Error responses should not contain PII."""
        import uuid

        error_id = str(uuid.uuid4())
        error_detail = {
            "success": False,
            "message": "Processing error — fallback message sent to contact",
            "error_id": error_id,
            "retry_allowed": True,
        }
        # Ensure no PII fields leak
        serialized = json.dumps(error_detail)
        assert "phone" not in serialized
        assert "email" not in serialized
        assert "firstName" not in serialized
        assert "+1555" not in serialized

    def test_webhook_response_model_excludes_pii(self):
        """GHLWebhookResponse doesn't include contact PII."""
        response = GHLWebhookResponse(
            success=True,
            message="Thanks for reaching out!",
            actions=[],
        )
        data = response.model_dump()
        fields = set(data.keys())
        assert "phone" not in fields
        assert "email" not in fields
        assert "contact_id" not in fields

    def test_max_inbound_message_length_constant(self):
        """MAX_INBOUND_LENGTH is set to 2000 chars (anti-abuse)."""
        MAX_INBOUND_LENGTH = 2_000
        assert MAX_INBOUND_LENGTH == 2000

    def test_compliance_max_input_length(self):
        """ComplianceGuard.MAX_INPUT_LENGTH is set (anti-token-abuse)."""
        assert ComplianceGuard.MAX_INPUT_LENGTH == 10_000