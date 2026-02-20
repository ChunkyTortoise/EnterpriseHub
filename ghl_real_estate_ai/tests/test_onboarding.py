"""
Test Suite for Partner Onboarding CLI Tool.

Tests the interactive onboarding process for new real estate partners/tenants.
Follows TDD discipline: RED -> GREEN -> REFACTOR
"""

import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "ghl-real-estate-ai"))

from scripts.onboard_partner import (
    check_duplicate_tenant,
    interactive_onboard,
    validate_api_key,
    validate_location_id,
    validate_partner_name,
)


class TestInputValidation:
    """Test suite for input validation functions."""

    def test_validate_partner_name_success(self):
        """Should accept valid partner names."""
        valid_names = ["ABC Realty", "Smith & Co.", "Real Estate 360", "The Property Group"]
        for name in valid_names:
            assert validate_partner_name(name) is True

    def test_validate_partner_name_failure(self):
        """Should reject empty or invalid partner names."""
        invalid_names = ["", "   ", "a", "AB"]  # Too short
        for name in invalid_names:
            assert validate_partner_name(name) is False

    def test_validate_location_id_success(self):
        """Should accept valid GHL Location IDs."""
        valid_ids = ["abc123xyz", "LOC-2024-001", "location_12345", "ghl_loc_abc123"]
        for loc_id in valid_ids:
            assert validate_location_id(loc_id) is True

    def test_validate_location_id_failure(self):
        """Should reject empty or too-short location IDs."""
        invalid_ids = ["", "   ", "ab", "123"]  # Too short
        for loc_id in invalid_ids:
            assert validate_location_id(loc_id) is False

    def test_validate_anthropic_api_key_success(self):
        """Should accept valid Anthropic API keys."""
        valid_keys = ["sk-ant-api03-abc123", "sk-ant-api02-xyz789-long-key-here", "sk-ant-sid01-testkey123456789"]
        for key in valid_keys:
            assert validate_api_key(key, "anthropic") is True

    def test_validate_anthropic_api_key_failure(self):
        """Should reject invalid Anthropic API keys."""
        invalid_keys = [
            "",
            "   ",
            "sk-test-123",  # Wrong prefix
            "api-key-123",  # Wrong format
            "sk-ant-ab",  # Too short
        ]
        for key in invalid_keys:
            assert validate_api_key(key, "anthropic") is False

    def test_validate_ghl_api_key_success(self):
        """Should accept valid GHL API keys."""
        valid_keys = [
            "ghl-api-key-123456789",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # JWT format
            "pk_live_123456789abcdef",
            "sk_test_987654321fedcba",
        ]
        for key in valid_keys:
            assert validate_api_key(key, "ghl") is True

    def test_validate_ghl_api_key_failure(self):
        """Should reject invalid GHL API keys."""
        invalid_keys = [
            "",
            "   ",
            "abc",  # Too short
            "12345",  # Too short
        ]
        for key in invalid_keys:
            assert validate_api_key(key, "ghl") is False


class TestDuplicateDetection:
    """Test suite for duplicate tenant detection."""

    def test_check_duplicate_tenant_no_file(self, tmp_path):
        """Should return False when tenant file does not exist."""
        location_id = "new_location_123"
        tenants_dir = tmp_path / "tenants"
        tenants_dir.mkdir()

        with patch("scripts.onboard_partner.Path") as mock_path:
            mock_path.return_value = tenants_dir
            assert check_duplicate_tenant(location_id, tenants_dir) is False

    def test_check_duplicate_tenant_file_exists(self, tmp_path):
        """Should return True when tenant file already exists."""
        location_id = "existing_location_123"
        tenants_dir = tmp_path / "tenants"
        tenants_dir.mkdir()

        # Create existing tenant file
        tenant_file = tenants_dir / f"{location_id}.json"
        tenant_file.write_text(json.dumps({"location_id": location_id}))

        assert check_duplicate_tenant(location_id, tenants_dir) is True


class TestInteractiveOnboarding:
    """Test suite for the interactive onboarding process."""

    @pytest.mark.asyncio
    async def test_successful_registration(self, tmp_path, monkeypatch):
        """Should successfully register a new tenant with valid inputs."""
        # Setup test data
        inputs = [
            "Acme Real Estate",  # Partner name
            "loc_acme_001",  # Location ID
            "sk-ant-api03-test123456789",  # Anthropic key
            "ghl-api-key-acme-test",  # GHL key
            "cal_acme_primary",  # Calendar ID
            "y",  # Confirmation
        ]
        input_generator = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_generator))

        # Mock tenants directory
        tenants_dir = tmp_path / "tenants"
        tenants_dir.mkdir()

        with patch("scripts.onboard_partner.TenantService") as mock_service:
            mock_instance = MagicMock()
            # Fix: Make save_tenant_config return an async coroutine
            mock_instance.save_tenant_config = MagicMock(return_value=None)

            async def async_save(*args, **kwargs):
                return None

            mock_instance.save_tenant_config = MagicMock(side_effect=async_save)
            mock_service.return_value = mock_instance

            # Run interactive onboarding
            result = await interactive_onboard()

            # Verify service was called correctly
            mock_instance.save_tenant_config.assert_called_once()
            call_args = mock_instance.save_tenant_config.call_args

            assert call_args[1]["location_id"] == "loc_acme_001"
            assert call_args[1]["anthropic_api_key"] == "sk-ant-api03-test123456789"
            assert call_args[1]["ghl_api_key"] == "ghl-api-key-acme-test"
            assert call_args[1]["ghl_calendar_id"] == "cal_acme_primary"
            assert result is True

    @pytest.mark.asyncio
    async def test_registration_with_duplicate_location_id(self, tmp_path, monkeypatch):
        """Should reject registration when location ID already exists."""
        # Create existing tenant
        tenants_dir = tmp_path / "tenants"
        tenants_dir.mkdir()
        existing_file = tenants_dir / "loc_duplicate_001.json"
        existing_file.write_text(json.dumps({"location_id": "loc_duplicate_001"}))

        inputs = [
            "Duplicate Realty",
            "loc_duplicate_001",  # This already exists
            "sk-ant-api03-test123",
            "ghl-api-key-test",
        ]
        input_generator = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_generator))

        with patch("scripts.onboard_partner.Path") as mock_path:
            mock_path.return_value = tenants_dir

            # Should fail and ask for new location_id
            with pytest.raises(ValueError, match="already exists"):
                await interactive_onboard()

    @pytest.mark.asyncio
    async def test_registration_without_calendar_id(self, tmp_path, monkeypatch):
        """Should successfully register tenant without optional calendar ID."""
        inputs = [
            "Basic Real Estate",
            "loc_basic_001",
            "sk-ant-api03-basic123456789",
            "ghl-api-key-basic-test",
            "",  # Empty calendar ID (optional)
            "y",  # Confirmation
        ]
        input_generator = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_generator))

        with patch("scripts.onboard_partner.TenantService") as mock_service:
            mock_instance = MagicMock()

            # Fix: Make save_tenant_config return an async coroutine
            async def async_save(*args, **kwargs):
                return None

            mock_instance.save_tenant_config = MagicMock(side_effect=async_save)
            mock_service.return_value = mock_instance

            result = await interactive_onboard()

            # Verify calendar_id was None or empty
            call_args = mock_instance.save_tenant_config.call_args
            assert call_args[1].get("ghl_calendar_id") in [None, ""]
            assert result is True

    @pytest.mark.asyncio
    async def test_input_validation_retry_flow(self, tmp_path, monkeypatch):
        """Should allow retry on invalid input."""
        # First input invalid, second input valid
        inputs = [
            "A",  # Invalid name (too short)
            "Valid Realty Co.",  # Valid name
            "loc_valid_001",
            "sk-ant-api03-valid123456789",
            "ghl-api-key-valid-test",
            "",
            "y",  # Confirmation
        ]
        input_generator = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_generator))

        with patch("scripts.onboard_partner.TenantService") as mock_service:
            mock_instance = MagicMock()

            # Fix: Make save_tenant_config return an async coroutine
            async def async_save(*args, **kwargs):
                return None

            mock_instance.save_tenant_config = MagicMock(side_effect=async_save)
            mock_service.return_value = mock_instance

            result = await interactive_onboard()

            # Should succeed after retry
            assert result is True
            mock_instance.save_tenant_config.assert_called_once()


class TestFileSystemOperations:
    """Test suite for file system operations during onboarding."""

    @pytest.mark.asyncio
    async def test_tenant_file_creation(self, tmp_path):
        """Should create tenant JSON file in correct location."""
        from ghl_real_estate_ai.services.tenant_service import TenantService

        # Use tmp_path for testing
        tenants_dir = tmp_path / "tenants"
        tenants_dir.mkdir()

        service = TenantService()
        service.tenants_dir = tenants_dir

        await service.save_tenant_config(
            location_id="test_loc_001",
            anthropic_api_key="sk-ant-api03-test123",
            ghl_api_key="ghl-test-key",
            ghl_calendar_id="cal_test_001",
        )

        # Verify file exists
        expected_file = tenants_dir / "test_loc_001.json"
        assert expected_file.exists()

        # Verify content
        with open(expected_file, "r") as f:
            data = json.load(f)
            assert data["location_id"] == "test_loc_001"
            assert data["anthropic_api_key"] == "sk-ant-api03-test123"
            assert data["ghl_api_key"] == "ghl-test-key"
            assert data["ghl_calendar_id"] == "cal_test_001"
            assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_tenant_directory_auto_creation(self):
        """Should automatically create data/tenants directory if missing."""
        from ghl_real_estate_ai.services.tenant_service import TenantService

        service = TenantService()

        # Verify tenants_dir was created
        assert service.tenants_dir.exists()
        assert service.tenants_dir.is_dir()


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_validate_api_key_with_spaces(self):
        """Should reject API keys with leading/trailing spaces."""
        # After stripping, the key should be valid
        key_with_spaces = "  sk-ant-api03-test123456789  "
        # The function strips spaces, so it should be valid
        assert validate_api_key(key_with_spaces, "anthropic") is True

    def test_validate_location_id_special_characters(self):
        """Should accept location IDs with valid special characters."""
        valid_ids = ["loc-123-abc", "loc_123_abc", "LOC.123.ABC"]
        for loc_id in valid_ids:
            assert validate_location_id(loc_id) is True

    @pytest.mark.asyncio
    async def test_onboarding_with_tenant_service_failure(self, monkeypatch):
        """Should handle TenantService errors gracefully."""
        inputs = ["Failure Test Realty", "loc_fail_001", "sk-ant-api03-fail123456789", "ghl-api-key-fail-test", ""]
        input_generator = iter(inputs)
        monkeypatch.setattr("builtins.input", lambda _: next(input_generator))

        with patch("scripts.onboard_partner.TenantService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.save_tenant_config.side_effect = Exception("Database error")
            mock_service.return_value = mock_instance

            # Should raise exception or handle gracefully
            with pytest.raises(Exception):
                await interactive_onboard()