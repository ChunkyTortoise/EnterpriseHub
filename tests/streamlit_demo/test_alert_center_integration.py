"""
Test suite for Jorge Alert Rules Panel integration.

Tests the Streamlit alert rules panel's interaction with the
Jorge Alerting API, including API fetch, demo fallback, and
rule toggle behavior.
"""

from unittest.mock import MagicMock, patch

import pytest

@pytest.mark.integration


class TestFetchRules:
    """Tests for _fetch_rules API integration."""

    def test_fetch_rules_api_success(self):
        """Returns rules from API when available."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _fetch_rules,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "sla_violation",
                "severity": "critical",
                "cooldown_seconds": 300,
                "channels": ["email", "slack", "webhook"],
                "description": "P95 latency exceeds SLA target",
                "active": True,
            },
        ]

        with patch("requests.get", return_value=mock_response) as mock_get:
            rules = _fetch_rules()

        assert len(rules) == 1
        assert rules[0]["name"] == "sla_violation"
        mock_get.assert_called_once()

    def test_fetch_rules_api_error_falls_back_to_demo(self):
        """Falls back to demo data when API returns error status."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _DEMO_RULES,
            _fetch_rules,
        )

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("requests.get", return_value=mock_response):
            rules = _fetch_rules()

        assert len(rules) == len(_DEMO_RULES)
        assert rules[0]["name"] == "sla_violation"

    def test_fetch_rules_connection_error_falls_back_to_demo(self):
        """Falls back to demo data when API is unreachable."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _DEMO_RULES,
            _fetch_rules,
        )

        with patch("requests.get", side_effect=ConnectionError("refused")):
            rules = _fetch_rules()

        assert len(rules) == len(_DEMO_RULES)

    def test_fetch_rules_timeout_falls_back_to_demo(self):
        """Falls back to demo data on API timeout."""
        import requests

        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _DEMO_RULES,
            _fetch_rules,
        )

        with patch("requests.get", side_effect=requests.Timeout("timeout")):
            rules = _fetch_rules()

        assert len(rules) == len(_DEMO_RULES)


class TestToggleRule:
    """Tests for _toggle_rule API integration."""

    def test_toggle_rule_success(self):
        """Returns True when API accepts the toggle."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _toggle_rule,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("requests.patch", return_value=mock_response) as mock_patch:
            result = _toggle_rule("sla_violation", False)

        assert result is True
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        assert "sla_violation" in call_args[0][0]
        assert call_args[1]["json"] == {"active": False}

    def test_toggle_rule_api_error(self):
        """Returns False when API returns error status."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _toggle_rule,
        )

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("requests.patch", return_value=mock_response):
            result = _toggle_rule("nonexistent_rule", True)

        assert result is False

    def test_toggle_rule_connection_error(self):
        """Returns False when API is unreachable."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _toggle_rule,
        )

        with patch("requests.patch", side_effect=ConnectionError("refused")):
            result = _toggle_rule("sla_violation", False)

        assert result is False


class TestDemoRules:
    """Tests for demo data consistency."""

    def test_demo_rules_has_seven_rules(self):
        """Demo data matches the 7 default alerting service rules."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _DEMO_RULES,
        )

        assert len(_DEMO_RULES) == 7

    def test_demo_rules_names_match_service(self):
        """Demo rule names match the AlertingService defaults."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _DEMO_RULES,
        )

        expected_names = {
            "sla_violation",
            "high_error_rate",
            "low_cache_hit_rate",
            "handoff_failure",
            "bot_unresponsive",
            "circular_handoff_spike",
            "rate_limit_breach",
        }
        actual_names = {r["name"] for r in _DEMO_RULES}
        assert actual_names == expected_names

    def test_demo_rules_all_have_required_fields(self):
        """Each demo rule has all required fields."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _DEMO_RULES,
        )

        required_fields = {"name", "severity", "cooldown_seconds", "channels", "description", "active"}
        for rule in _DEMO_RULES:
            assert required_fields.issubset(rule.keys()), f"Rule '{rule.get('name')}' missing fields"

    def test_demo_rules_all_active_by_default(self):
        """All demo rules are active by default."""
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _DEMO_RULES,
        )

        for rule in _DEMO_RULES:
            assert rule["active"] is True, f"Rule '{rule['name']}' should be active"


class TestFormatCooldown:
    """Tests for the _format_cooldown helper."""

    def test_format_seconds(self):
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _format_cooldown,
        )

        assert _format_cooldown(30) == "30s"

    def test_format_minutes(self):
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _format_cooldown,
        )

        assert _format_cooldown(300) == "5m"
        assert _format_cooldown(600) == "10m"

    def test_format_hours(self):
        from ghl_real_estate_ai.streamlit_demo.components.jorge_alert_rules_panel import (
            _format_cooldown,
        )

        assert _format_cooldown(3600) == "1h 0m"
        assert _format_cooldown(5400) == "1h 30m"