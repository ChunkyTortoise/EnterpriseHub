import pytest
pytestmark = pytest.mark.integration

"""Tests for Phase 2: Configurable GHL IDs — jorge_config.py validation."""

import os
from unittest.mock import patch

import pytest

from ghl_real_estate_ai.ghl_utils.jorge_config import (

@pytest.mark.integration
    JorgeEnvironmentSettings,
    JorgeSellerConfig,
)


class TestValidateGHLIntegration:
    """Tests for JorgeEnvironmentSettings.validate_ghl_integration()."""

    @patch.dict(
        os.environ,
        {
            "JORGE_SELLER_MODE": "true",
            "JORGE_BUYER_MODE": "true",
        },
        clear=False,
    )
    def test_validate_warns_on_missing_workflow_ids(self):
        """validate_ghl_integration() returns warnings when workflow env vars are absent."""
        # Remove any workflow env vars that might be set
        env_overrides = {
            "JORGE_SELLER_MODE": "true",
            "JORGE_BUYER_MODE": "true",
        }
        for key in (
            "HOT_SELLER_WORKFLOW_ID",
            "WARM_SELLER_WORKFLOW_ID",
            "HOT_BUYER_WORKFLOW_ID",
            "WARM_BUYER_WORKFLOW_ID",
            "CUSTOM_FIELD_LEAD_SCORE",
            "CUSTOM_FIELD_SELLER_TEMPERATURE",
            "CUSTOM_FIELD_BUDGET",
        ):
            env_overrides[key] = ""

        with patch.dict(os.environ, env_overrides, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

        assert any("HOT_SELLER_WORKFLOW_ID" in w for w in warnings)
        assert any("WARM_SELLER_WORKFLOW_ID" in w for w in warnings)
        assert any("HOT_BUYER_WORKFLOW_ID" in w for w in warnings)
        assert any("WARM_BUYER_WORKFLOW_ID" in w for w in warnings)
        assert any("CUSTOM_FIELD_LEAD_SCORE" in w for w in warnings)
        assert any("CUSTOM_FIELD_SELLER_TEMPERATURE" in w for w in warnings)
        assert any("CUSTOM_FIELD_BUDGET" in w for w in warnings)

    @patch.dict(
        os.environ,
        {
            "JORGE_SELLER_MODE": "true",
            "JORGE_BUYER_MODE": "true",
            "HOT_SELLER_WORKFLOW_ID": "wf_hot_seller_123",
            "WARM_SELLER_WORKFLOW_ID": "wf_warm_seller_456",
            "HOT_BUYER_WORKFLOW_ID": "wf_hot_buyer_789",
            "WARM_BUYER_WORKFLOW_ID": "wf_warm_buyer_abc",
            "CUSTOM_FIELD_LEAD_SCORE": "cf_lead_score",
            "CUSTOM_FIELD_SELLER_TEMPERATURE": "cf_seller_temp",
            "CUSTOM_FIELD_BUDGET": "cf_budget",
        },
        clear=False,
    )
    def test_validate_clean_when_all_set(self):
        """No warnings when all env vars are properly configured."""
        settings = JorgeEnvironmentSettings()
        warnings = settings.validate_ghl_integration()
        assert warnings == []

    @patch.dict(
        os.environ,
        {
            "JORGE_SELLER_MODE": "false",
            "JORGE_BUYER_MODE": "false",
        },
        clear=False,
    )
    def test_seller_mode_disabled_skips_seller_validation(self):
        """No seller/buyer workflow warnings when modes are disabled."""
        env_overrides = {
            "JORGE_SELLER_MODE": "false",
            "JORGE_BUYER_MODE": "false",
            "CUSTOM_FIELD_LEAD_SCORE": "cf_lead_score",
            "CUSTOM_FIELD_SELLER_TEMPERATURE": "cf_seller_temp",
            "CUSTOM_FIELD_BUDGET": "cf_budget",
        }
        with patch.dict(os.environ, env_overrides, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

        assert not any("HOT_SELLER_WORKFLOW_ID" in w for w in warnings)
        assert not any("WARM_SELLER_WORKFLOW_ID" in w for w in warnings)
        assert not any("HOT_BUYER_WORKFLOW_ID" in w for w in warnings)
        assert warnings == []


class TestGetWorkflowId:
    """Tests for JorgeSellerConfig.get_workflow_id()."""

    @patch.dict(os.environ, {"HOT_SELLER_WORKFLOW_ID": "env_wf_hot_123"}, clear=False)
    def test_get_workflow_id_returns_env_over_default(self):
        """Env var takes priority over dataclass default."""
        result = JorgeSellerConfig.get_workflow_id("hot")
        assert result == "env_wf_hot_123"

    def test_get_workflow_id_returns_none_when_empty(self):
        """Empty default + no env var = falsy (empty string)."""
        env_overrides = {}
        for key in ("HOT_SELLER_WORKFLOW_ID", "WARM_SELLER_WORKFLOW_ID"):
            env_overrides[key] = ""
        with patch.dict(os.environ, env_overrides, clear=False):
            hot_result = JorgeSellerConfig.get_workflow_id("hot")
            warm_result = JorgeSellerConfig.get_workflow_id("warm")

        # Empty string is falsy — callers using `if workflow_id:` will skip
        assert not hot_result
        assert not warm_result


class TestGetCustomFieldId:
    """Tests for JorgeSellerConfig.get_ghl_custom_field_id()."""

    @patch.dict(os.environ, {"CUSTOM_FIELD_SELLER_TEMPERATURE": "cf_real_uuid_123"}, clear=False)
    def test_get_custom_field_id_env_override(self):
        """CUSTOM_FIELD_X env var overrides static mapping."""
        result = JorgeSellerConfig.get_ghl_custom_field_id("seller_temperature")
        assert result == "cf_real_uuid_123"

    def test_get_custom_field_id_fallback(self):
        """Returns empty string (from CUSTOM_FIELDS dict) when env var not set."""
        env_overrides = {"CUSTOM_FIELD_SELLER_TEMPERATURE": ""}
        with patch.dict(os.environ, env_overrides, clear=False):
            result = JorgeSellerConfig.get_ghl_custom_field_id("seller_temperature")
        # With empty env var and empty default, result should be falsy
        assert not result