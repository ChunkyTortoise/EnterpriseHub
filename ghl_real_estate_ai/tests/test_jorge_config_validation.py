"""Tests for jorge_config validation.

Tests for the validate_ghl_integration() method and related configuration
validation, environment variable overrides, and fallback behavior.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestJorgeConfigValidation:
    """Test cases for Jorge configuration validation."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Clean up environment variables before each test."""
        # Store original env and clear relevant vars
        self.original_env = os.environ.copy()
        yield
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self, 'original_env'):
            os.environ.clear()
            os.environ.update(self.original_env)

    def test_validate_ghl_integration_empty_workflow_ids_warns(self):
        """Test that empty workflow IDs produce warnings."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeEnvironmentSettings

        # Set seller mode but no workflow IDs
        with patch.dict(os.environ, {
            "JORGE_SELLER_MODE": "true",
            "JORGE_BUYER_MODE": "false",
            "HOT_SELLER_WORKFLOW_ID": "",
            "WARM_SELLER_WORKFLOW_ID": ""
        }, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

            # Verify warnings are emitted for missing workflow IDs
            workflow_warnings = [w for w in warnings if "WORKFLOW_ID" in w]
            assert len(workflow_warnings) >= 1, "Expected warning for HOT_SELLER_WORKFLOW_ID"

    def test_validate_ghl_integration_empty_custom_field_ids_warns(self):
        """Test that empty custom field IDs produce warnings."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeEnvironmentSettings

        # Clear custom field environment variables
        env_without_fields = {
            "CUSTOM_FIELD_LEAD_SCORE": "",
            "CUSTOM_FIELD_SELLER_TEMPERATURE": "",
            "CUSTOM_FIELD_BUDGET": ""
        }

        with patch.dict(os.environ, env_without_fields, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

            # Verify warnings about missing custom fields
            field_warnings = [w for w in warnings if "CUSTOM_FIELD_" in w]
            assert len(field_warnings) >= 1, "Expected warnings for missing custom fields"

    def test_validate_ghl_integration_missing_env_vars_warns(self):
        """Test that missing environment variables produce appropriate warnings."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeEnvironmentSettings

        # Clear all relevant env vars
        env_cleared = {
            "HOT_SELLER_WORKFLOW_ID": "",
            "WARM_SELLER_WORKFLOW_ID": "",
            "HOT_BUYER_WORKFLOW_ID": "",
            "WARM_BUYER_WORKFLOW_ID": "",
            "CUSTOM_FIELD_LEAD_SCORE": "",
            "CUSTOM_FIELD_SELLER_TEMPERATURE": "",
            "CUSTOM_FIELD_BUDGET": ""
        }

        with patch.dict(os.environ, env_cleared, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

            # Should have warnings for all missing configuration
            assert len(warnings) > 0, "Expected warnings when env vars are missing"

    def test_validate_ghl_integration_valid_config_returns_clean(self):
        """Test that valid configuration produces no warnings."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeEnvironmentSettings

        # Set all required workflow IDs and custom fields
        env_valid = {
            "JORGE_SELLER_MODE": "true",
            "JORGE_BUYER_MODE": "true",
            "HOT_SELLER_WORKFLOW_ID": "workflow-hot-123",
            "WARM_SELLER_WORKFLOW_ID": "workflow-warm-456",
            "HOT_BUYER_WORKFLOW_ID": "buyer-hot-789",
            "WARM_BUYER_WORKFLOW_ID": "buyer-warm-012",
            "CUSTOM_FIELD_LEAD_SCORE": "field_lead_123",
            "CUSTOM_FIELD_SELLER_TEMPERATURE": "field_temp_456",
            "CUSTOM_FIELD_BUDGET": "field_budget_789"
        }

        with patch.dict(os.environ, env_valid, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

            # No warnings should be produced
            workflow_warnings = [w for w in warnings if "WORKFLOW_ID" in w]
            field_warnings = [w for w in warnings if "CUSTOM_FIELD_" in w]

            assert len(workflow_warnings) == 0, "No workflow warnings expected with valid config"
            assert len(field_warnings) == 0, "No custom field warnings expected with valid config"

    def test_workflow_id_fallback_behavior(self):
        """Test that empty workflow IDs don't cause crashes and fallback works."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        # Test that get_workflow_id handles empty values gracefully
        with patch.dict(os.environ, {"HOT_SELLER_WORKFLOW_ID": ""}, clear=False):
            result = JorgeSellerConfig.get_workflow_id("hot")
            # Should not crash, should return None or empty string
            assert result is None or result == "", "Expected fallback for empty workflow ID"

        with patch.dict(os.environ, {"WARM_SELLER_WORKFLOW_ID": ""}, clear=False):
            result = JorgeSellerConfig.get_workflow_id("warm")
            assert result is None or result == "", "Expected fallback for empty workflow ID"

    def test_custom_field_id_fallback_behavior(self):
        """Test that empty custom field IDs don't cause crashes and fallback works."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        # Test get_ghl_custom_field_id handles empty values gracefully
        with patch.dict(os.environ, {"CUSTOM_FIELD_SELLER_TEMPERATURE": ""}, clear=False):
            result = JorgeSellerConfig.get_ghl_custom_field_id("seller_temperature")
            # Should return empty string from fallback, not crash
            assert result is not None, "Expected non-None result from custom field getter"
            assert isinstance(result, str), "Expected string result from custom field getter"

    def test_env_var_override_behavior(self):
        """Test that environment variable overrides are applied correctly."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeEnvironmentSettings

        # Test workflow ID override
        with patch.dict(os.environ, {
            "HOT_SELLER_WORKFLOW_ID": "override-workflow-id"
        }, clear=False):
            settings = JorgeEnvironmentSettings()
            # The setting should reflect the env var
            assert settings.hot_seller_workflow_id == "override-workflow-id"

        # Test threshold override
        with patch.dict(os.environ, {
            "HOT_SELLER_THRESHOLD": "0.85"
        }, clear=False):
            settings = JorgeEnvironmentSettings()
            assert settings.hot_seller_threshold == 0.85

        # Test mode override
        with patch.dict(os.environ, {
            "JORGE_SELLER_MODE": "true"
        }, clear=False):
            settings = JorgeEnvironmentSettings()
            assert settings.jorge_seller_mode is True

        with patch.dict(os.environ, {
            "JORGE_SELLER_MODE": "false"
        }, clear=False):
            settings = JorgeEnvironmentSettings()
            assert settings.jorge_seller_mode is False

    def test_validate_ghl_integration_buyer_mode_warnings(self):
        """Test that buyer mode workflow warnings are emitted correctly."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeEnvironmentSettings

        # Set buyer mode but no buyer workflow IDs
        with patch.dict(os.environ, {
            "JORGE_SELLER_MODE": "false",
            "JORGE_BUYER_MODE": "true",
            "HOT_BUYER_WORKFLOW_ID": "",
            "WARM_BUYER_WORKFLOW_ID": ""
        }, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

            # Verify warnings for missing buyer workflow IDs
            buyer_warnings = [w for w in warnings if "BUYER_WORKFLOW_ID" in w]
            assert len(buyer_warnings) >= 1, "Expected warnings for missing buyer workflow IDs"


class TestJorgeConfigEdgeCases:
    """Test edge cases for Jorge configuration."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Clean up environment variables before each test."""
        self.original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_validate_ghl_integration_mixed_mode_config(self):
        """Test validation with mixed seller/buyer mode configuration."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeEnvironmentSettings

        # Seller mode with workflows, buyer mode without
        with patch.dict(os.environ, {
            "JORGE_SELLER_MODE": "true",
            "JORGE_BUYER_MODE": "true",
            "HOT_SELLER_WORKFLOW_ID": "seller-hot-123",
            "WARM_SELLER_WORKFLOW_ID": "seller-warm-456",
            "HOT_BUYER_WORKFLOW_ID": "",
            "WARM_BUYER_WORKFLOW_ID": ""
        }, clear=False):
            settings = JorgeEnvironmentSettings()
            warnings = settings.validate_ghl_integration()

            # Should have buyer warnings but no seller warnings
            seller_warnings = [w for w in warnings if "SELLER_WORKFLOW_ID" in w]
            buyer_warnings = [w for w in warnings if "BUYER_WORKFLOW_ID" in w]

            assert len(seller_warnings) == 0, "Seller workflows are configured"
            assert len(buyer_warnings) >= 1, "Buyer workflows are missing"

    def test_get_workflow_id_unknown_temperature(self):
        """Test get_workflow_id with unknown temperature returns None."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        result = JorgeSellerConfig.get_workflow_id("unknown")
        assert result is None, "Expected None for unknown temperature"

    def test_get_environment_config_returns_dict(self):
        """Test that get_environment_config returns proper dictionary."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        config = JorgeSellerConfig.get_environment_config()

        assert isinstance(config, dict), "Expected dictionary return"
        assert "jorge_seller_mode" in config, "Expected jorge_seller_mode in config"
        assert "hot_seller_threshold" in config, "Expected hot_seller_threshold in config"
        assert "warm_seller_threshold" in config, "Expected warm_seller_threshold in config"

    def test_jorge_seller_config_defaults(self):
        """Test JorgeSellerConfig default values are reasonable."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        # Verify default thresholds
        assert JorgeSellerConfig.HOT_SELLER_THRESHOLD == 1.0
        assert JorgeSellerConfig.WARM_SELLER_THRESHOLD == 0.75
        assert JorgeSellerConfig.ACTIVE_FOLLOWUP_DAYS == 30
        assert JorgeSellerConfig.LONGTERM_FOLLOWUP_INTERVAL == 14

    def test_validate_seller_response_handles_empty(self):
        """Test validate_seller_response handles empty input gracefully."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        result = JorgeSellerConfig.validate_seller_response("")

        assert result["is_valid"] is True
        assert result["quality_score"] < 1.0
        assert len(result["issues"]) > 0

    def test_sanitize_message_length_compliance(self):
        """Test that sanitize_message enforces SMS length limits."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        long_message = "A" * 200
        sanitized = JorgeSellerConfig.sanitize_message(long_message)

        assert len(sanitized) <= JorgeSellerConfig.MAX_SMS_LENGTH
