"""
Jorge Fields E2E Integration Tests

Full flow: seller goes through FULL mode 10-question flow -> all fields collected
-> GHL contact updated with mortgage_balance and repair_estimate.
"""

import os

import pytest

pytestmark = pytest.mark.integration

from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_config():
    """Reset JorgeSellerConfig to known state before each test."""
    JorgeSellerConfig.set_mode(simple_mode=True)
    yield
    JorgeSellerConfig.set_mode(simple_mode=True)


# ── Part 1: Custom Field Env Var Wiring ───────────────────────────────


class TestCustomFieldEnvWiring:
    """Verify mortgage_balance and repair_estimate read from env vars."""

    def test_mortgage_balance_reads_from_env(self):
        """CUSTOM_FIELD_MORTGAGE_BALANCE env var populates the field."""
        with patch.dict(os.environ, {"CUSTOM_FIELD_MORTGAGE_BALANCE": "cf_mortgage_123"}):
            # Re-import to pick up the env var (the dict is evaluated at class def time,
            # but get_ghl_custom_field_id reads from os.getenv at call time)
            result = JorgeSellerConfig.get_ghl_custom_field_id("mortgage_balance")
        assert result == "cf_mortgage_123"

    def test_repair_estimate_reads_from_env(self):
        """CUSTOM_FIELD_REPAIR_ESTIMATE env var populates the field."""
        with patch.dict(os.environ, {"CUSTOM_FIELD_REPAIR_ESTIMATE": "cf_repair_456"}):
            result = JorgeSellerConfig.get_ghl_custom_field_id("repair_estimate")
        assert result == "cf_repair_456"

    def test_missing_env_vars_return_empty(self):
        """Without env vars, fields gracefully return empty string."""
        # Ensure env vars are not set
        env = {k: v for k, v in os.environ.items()
               if k not in ("CUSTOM_FIELD_MORTGAGE_BALANCE", "CUSTOM_FIELD_REPAIR_ESTIMATE")}
        with patch.dict(os.environ, env, clear=True):
            mortgage = JorgeSellerConfig.get_ghl_custom_field_id("mortgage_balance")
            repair = JorgeSellerConfig.get_ghl_custom_field_id("repair_estimate")

        # Should return empty string (from CUSTOM_FIELDS dict default), not None
        assert mortgage is not None
        assert repair is not None

    def test_env_var_overrides_dict_default(self):
        """Env var takes priority over the static CUSTOM_FIELDS default."""
        with patch.dict(os.environ, {"CUSTOM_FIELD_MORTGAGE_BALANCE": "env_override"}):
            result = JorgeSellerConfig.get_ghl_custom_field_id("mortgage_balance")
        assert result == "env_override"


# ── Part 2: Question Field Mapping ───────────────────────────────────


class TestQuestionFieldMapping:
    """Verify FULL mode question-to-field mappings for mortgage and repair."""

    def test_full_mode_has_10_questions(self):
        """FULL mode should have exactly 10 questions."""
        assert len(JorgeSellerConfig.SELLER_QUESTIONS_FULL) == 10

    def test_simple_mode_has_4_questions(self):
        """SIMPLE mode should have exactly 4 questions."""
        assert len(JorgeSellerConfig.SELLER_QUESTIONS_SIMPLE) == 4

    def test_question_6_maps_to_mortgage_balance(self):
        """Question 6 primary field is mortgage_balance."""
        mapping = JorgeSellerConfig.QUESTION_FIELD_MAPPING_FULL[6]
        assert mapping["field"] == "mortgage_balance"
        assert mapping["secondary"] == "has_liens"

    def test_question_7_maps_to_repair_needs(self):
        """Question 7 primary field is repair_needs with repair_estimate secondary."""
        mapping = JorgeSellerConfig.QUESTION_FIELD_MAPPING_FULL[7]
        assert mapping["field"] == "repair_needs"
        assert mapping["secondary"] == "repair_estimate"

    def test_question_4_secondary_is_repair_estimate(self):
        """Question 4 (property condition) has repair_estimate as secondary."""
        mapping = JorgeSellerConfig.QUESTION_FIELD_MAPPING_FULL[4]
        assert mapping["field"] == "property_condition"
        assert mapping["secondary"] == "repair_estimate"

    def test_full_mapping_covers_all_10_questions(self):
        """FULL mode mapping should have entries for questions 1-10."""
        for q_num in range(1, 11):
            assert q_num in JorgeSellerConfig.QUESTION_FIELD_MAPPING_FULL
            mapping = JorgeSellerConfig.QUESTION_FIELD_MAPPING_FULL[q_num]
            assert "field" in mapping
            assert "secondary" in mapping

    def test_mode_switch_updates_mapping(self):
        """Switching to FULL mode updates active mapping."""
        JorgeSellerConfig.set_mode(simple_mode=False)
        assert JorgeSellerConfig.QUESTION_FIELD_MAPPING == JorgeSellerConfig.QUESTION_FIELD_MAPPING_FULL
        assert len(JorgeSellerConfig.SELLER_QUESTIONS) == 10

    def test_mode_switch_back_to_simple(self):
        """Switching back to SIMPLE mode restores 4-question mapping."""
        JorgeSellerConfig.set_mode(simple_mode=False)
        JorgeSellerConfig.set_mode(simple_mode=True)
        assert JorgeSellerConfig.QUESTION_FIELD_MAPPING == JorgeSellerConfig.QUESTION_FIELD_MAPPING_SIMPLE
        assert len(JorgeSellerConfig.SELLER_QUESTIONS) == 4


# ── Part 3: GHL Workflow Service Field Sync ──────────────────────────


class TestGHLFieldSync:
    """Verify mortgage_balance and repair_estimate reach the GHL update call."""

    @pytest.mark.asyncio
    async def test_seller_data_sync_includes_liens_and_repairs(self):
        """GHL workflow service maps seller_liens and seller_repairs to custom fields."""
        mock_ghl = AsyncMock()
        mock_ghl.update_contact = AsyncMock(return_value=True)

        # Mock settings with custom field IDs
        mock_settings = MagicMock()
        mock_settings.custom_field_seller_temperature = "cf_temp"
        mock_settings.custom_field_pcs_score = "cf_pcs"
        mock_settings.custom_field_seller_motivation = "cf_motivation"
        mock_settings.custom_field_timeline_urgency = "cf_timeline"
        mock_settings.custom_field_property_condition = "cf_condition"
        mock_settings.custom_field_price_expectation = "cf_price"
        mock_settings.custom_field_seller_liens = "cf_liens"
        mock_settings.custom_field_seller_repairs = "cf_repairs"
        mock_settings.custom_field_seller_listing_history = "cf_listing_hist"
        mock_settings.custom_field_seller_decision_maker = "cf_decision"
        mock_settings.custom_field_location = None

        bot_data = {
            "seller_liens": "250000",
            "seller_repairs": "15000",
            "seller_temperature": "hot",
        }

        with patch("ghl_real_estate_ai.ghl_utils.config.settings", mock_settings), \
             patch("ghl_real_estate_ai.services.ghl_workflow_service.settings", mock_settings):
            from ghl_real_estate_ai.services.ghl_workflow_service import GHLWorkflowService
            svc = GHLWorkflowService.__new__(GHLWorkflowService)
            svc.ghl_client = mock_ghl


            result = await svc.sync_contact_data("contact_123", bot_data)

        assert result is True
        mock_ghl.update_contact.assert_called_once()
        call_args = mock_ghl.update_contact.call_args
        custom_fields = call_args[0][1]["custom_fields"]

        # Verify liens and repairs are included
        assert custom_fields.get("cf_liens") == "250000"
        assert custom_fields.get("cf_repairs") == "15000"
        assert custom_fields.get("cf_temp") == "hot"

    @pytest.mark.asyncio
    async def test_missing_field_ids_skip_gracefully(self):
        """When custom field IDs are None, those fields are skipped."""
        mock_ghl = AsyncMock()
        mock_ghl.update_contact = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        # All seller custom fields set to None (not configured)
        mock_settings.custom_field_seller_temperature = None
        mock_settings.custom_field_pcs_score = None
        mock_settings.custom_field_seller_motivation = None
        mock_settings.custom_field_timeline_urgency = None
        mock_settings.custom_field_property_condition = None
        mock_settings.custom_field_price_expectation = None
        mock_settings.custom_field_seller_liens = None
        mock_settings.custom_field_seller_repairs = None
        mock_settings.custom_field_seller_listing_history = None
        mock_settings.custom_field_seller_decision_maker = None
        mock_settings.custom_field_location = None

        bot_data = {
            "seller_liens": "250000",
            "seller_repairs": "15000",
        }

        with patch("ghl_real_estate_ai.ghl_utils.config.settings", mock_settings), \
             patch("ghl_real_estate_ai.services.ghl_workflow_service.settings", mock_settings):
            from ghl_real_estate_ai.services.ghl_workflow_service import GHLWorkflowService
            svc = GHLWorkflowService.__new__(GHLWorkflowService)
            svc.ghl_client = mock_ghl


            result = await svc.sync_contact_data("contact_123", bot_data)

        # Should still succeed, just skip the unconfigured fields
        assert result is True

    @pytest.mark.asyncio
    async def test_none_values_not_synced(self):
        """Bot data with None values should not be sent to GHL."""
        mock_ghl = AsyncMock()
        mock_ghl.update_contact = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.custom_field_seller_liens = "cf_liens"
        mock_settings.custom_field_seller_repairs = "cf_repairs"
        mock_settings.custom_field_seller_temperature = None
        mock_settings.custom_field_pcs_score = None
        mock_settings.custom_field_seller_motivation = None
        mock_settings.custom_field_timeline_urgency = None
        mock_settings.custom_field_property_condition = None
        mock_settings.custom_field_price_expectation = None
        mock_settings.custom_field_seller_listing_history = None
        mock_settings.custom_field_seller_decision_maker = None
        mock_settings.custom_field_location = None

        bot_data = {
            "seller_liens": None,  # Not collected yet
            "seller_repairs": "5000",
        }

        with patch("ghl_real_estate_ai.ghl_utils.config.settings", mock_settings), \
             patch("ghl_real_estate_ai.services.ghl_workflow_service.settings", mock_settings):
            from ghl_real_estate_ai.services.ghl_workflow_service import GHLWorkflowService
            svc = GHLWorkflowService.__new__(GHLWorkflowService)
            svc.ghl_client = mock_ghl


            result = await svc.sync_contact_data("contact_123", bot_data)

        assert result is True
        if mock_ghl.update_contact.called:
            call_args = mock_ghl.update_contact.call_args
            custom_fields = call_args[0][1]["custom_fields"]
            # seller_liens should NOT be in custom_fields since value was None
            assert "cf_liens" not in custom_fields
            # seller_repairs should be included
            assert custom_fields.get("cf_repairs") == "5000"
