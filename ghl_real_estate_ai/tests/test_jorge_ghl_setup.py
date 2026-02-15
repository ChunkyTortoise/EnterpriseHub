"""Tests for GHL setup validation script."""

import os
from unittest.mock import patch

import pytest

from ghl_real_estate_ai.ghl_utils.jorge_ghl_setup import (
    CUSTOM_FIELDS,
    JORGE_FIELDS,
    WORKFLOW_IDS,
    CALENDAR_IDS,
    validate_ghl_config,
)


class TestValidateGhlConfig:
    """Tests for validate_ghl_config()."""

    def _all_critical_vars(self):
        """Build dict of all critical env vars with dummy values."""
        critical_vars = {}
        for env_var, _, _, critical in CUSTOM_FIELDS:
            if critical:
                critical_vars[env_var] = "field_abc123"
        for env_var, _, _, _, critical in JORGE_FIELDS:
            if critical:
                critical_vars[env_var] = "field_jorge_123"
        for env_var, _, critical in WORKFLOW_IDS:
            if critical:
                critical_vars[env_var] = "wf_abc123"
        for env_var, _, critical in CALENDAR_IDS:
            if critical:
                critical_vars[env_var] = "cal_abc123"
        return critical_vars

    def test_all_missing_returns_invalid(self):
        """With no env vars set, critical fields are missing and valid=False."""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_ghl_config()

        assert result["valid"] is False
        assert result["summary"]["critical_missing"]
        assert result["summary"]["missing_count"] > 0

    def test_all_critical_set_returns_valid(self):
        """When all critical env vars are set, valid=True."""
        critical_vars = self._all_critical_vars()

        with patch.dict(os.environ, critical_vars, clear=True):
            result = validate_ghl_config()

        assert result["valid"] is True
        assert len(result["summary"]["critical_missing"]) == 0

    def test_partial_critical_set_returns_invalid(self):
        """When only some critical vars are set, valid=False."""
        # Set just the first critical field
        partial = {}
        for env_var, _, _, critical in CUSTOM_FIELDS:
            if critical:
                partial[env_var] = "field_abc123"
                break

        with patch.dict(os.environ, partial, clear=True):
            result = validate_ghl_config()

        assert result["valid"] is False
        # At least workflow critical vars are still missing
        assert any(
            var.endswith("_WORKFLOW_ID")
            for var in result["summary"]["critical_missing"]
        )

    def test_whitespace_only_counts_as_missing(self):
        """Whitespace-only values should be treated as missing."""
        critical_vars = {}
        for env_var, _, _, critical in CUSTOM_FIELDS:
            if critical:
                critical_vars[env_var] = "   "
        for env_var, _, critical in WORKFLOW_IDS:
            if critical:
                critical_vars[env_var] = "  "

        with patch.dict(os.environ, critical_vars, clear=True):
            result = validate_ghl_config()

        assert result["valid"] is False

    def test_result_structure(self):
        """Result dict has expected keys and structure."""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_ghl_config()

        assert "fields" in result
        assert "workflows" in result
        assert "calendars" in result
        assert "summary" in result
        assert "valid" in result

        # Check field entry structure
        if result["fields"]:
            entry = result["fields"][0]
            assert "env_var" in entry
            assert "ghl_type" in entry
            assert "bot" in entry
            assert "critical" in entry
            assert entry["status"] in ("set", "missing")

    def test_counts_match(self):
        """Summary counts should match total items."""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_ghl_config()

        summary = result["summary"]
        total_items = (
            len(result["fields"])
            + len(result["workflows"])
            + len(result["calendars"])
        )
        assert summary["total"] == total_items
        assert summary["set_count"] + summary["missing_count"] == total_items

    def test_field_definitions_complete(self):
        """All field definitions should have valid bot and type values."""
        valid_bots = {"seller", "buyer", "lead", "general"}
        valid_types = {"dropdown", "text", "number", "currency", "boolean", "datetime"}

        for env_var, ghl_type, bot, critical in CUSTOM_FIELDS:
            assert bot in valid_bots, f"{env_var} has invalid bot: {bot}"
            assert ghl_type in valid_types, f"{env_var} has invalid type: {ghl_type}"
            assert isinstance(critical, bool)

        for env_var, bot, critical in WORKFLOW_IDS:
            assert bot in valid_bots, f"{env_var} has invalid bot: {bot}"
            assert isinstance(critical, bool)

    def test_jorge_fields_included(self):
        """Jorge-specific fields should be included in validation."""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_ghl_config()

        jorge_env_vars = {env_var for env_var, _, _, _, _ in JORGE_FIELDS}
        result_env_vars = {f["env_var"] for f in result["fields"]}
        assert jorge_env_vars.issubset(result_env_vars)

    def test_set_field_shows_as_set(self):
        """A single set field should appear with status 'set'."""
        env_var = CUSTOM_FIELDS[0][0]
        with patch.dict(os.environ, {env_var: "some_ghl_id"}, clear=True):
            result = validate_ghl_config()

        matching = [f for f in result["fields"] if f["env_var"] == env_var]
        assert len(matching) == 1
        assert matching[0]["status"] == "set"
