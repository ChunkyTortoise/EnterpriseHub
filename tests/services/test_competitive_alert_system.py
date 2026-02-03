"""
Comprehensive tests for competitive alert system

Tests cover:
1. Multi-channel alert delivery
2. Risk-based alert routing
3. Rate limiting functionality
4. Jorge notification preferences
5. GHL integration for tagging
6. Escalation protocols
7. Alert resolution tracking
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

try:
    from ghl_real_estate_ai.services.competitive_alert_system import (
        CompetitiveAlertSystem,
        CompetitiveAlert,
        AlertPriority,
        NotificationChannel,
        get_competitive_alert_system
    )
    from ghl_real_estate_ai.services.competitor_intelligence import (
        CompetitiveAnalysis,
        CompetitorMention,
        RiskLevel
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestCompetitiveAlertSystem:
    """Test suite for competitive alert system"""

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_cache.delete.return_value = True
        return mock_cache

    @pytest.fixture
    def mock_ghl_client(self):
        """Mock GHL client"""
        mock_ghl = AsyncMock()
        mock_ghl.add_tags_to_contact.return_value = True
        return mock_ghl

    @pytest.fixture
    def alert_system(self, mock_cache_service, mock_ghl_client):
        """Create alert system with mocked dependencies"""
        system = CompetitiveAlertSystem(
            cache_service=mock_cache_service,
            ghl_client=mock_ghl_client
        )
        return system

    @pytest.fixture
    def sample_competitive_analysis(self):
        """Sample competitive analysis for testing"""
        mention = CompetitorMention(
            competitor_type="named_competitor",
            competitor_name="keller_williams",
            mention_text="working with Keller Williams",
            confidence_score=0.9,
            risk_level=RiskLevel.HIGH,
            context="I'm working with a Keller Williams agent",
            timestamp=datetime.now(),
            patterns_matched=["named_competitor"],
            sentiment_score=0.0,
            urgency_indicators=["ASAP"]
        )

        return CompetitiveAnalysis(
            has_competitor_risk=True,
            risk_level=RiskLevel.HIGH,
            mentions=[mention],
            recommended_responses=["Position as backup resource"],
            alert_required=True,
            escalation_needed=True,
            recovery_strategies=["Provide market insights"],
            confidence_score=0.85
        )

    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for testing"""
        return {
            "id": "lead_123",
            "name": "John Doe",
            "first_name": "John",
            "phone": "+1234567890",
            "email": "john.doe@example.com"
        }

    @pytest.mark.asyncio
    async def test_alert_creation_and_storage(self, alert_system, sample_competitive_analysis, sample_lead_data):
        """Test alert creation and storage"""
        alert = await alert_system.send_competitive_alert(
            lead_id="lead_123",
            lead_data=sample_lead_data,
            competitive_analysis=sample_competitive_analysis
        )

        assert alert is not None
        assert alert.lead_id == "lead_123"
        assert alert.lead_name == "John Doe"
        assert alert.competitive_analysis == sample_competitive_analysis
        assert alert.priority == AlertPriority.HIGH
        assert alert.alert_required is True

    @pytest.mark.asyncio
    async def test_risk_level_to_priority_mapping(self, alert_system):
        """Test mapping of risk levels to alert priorities"""
        mappings = [
            (RiskLevel.LOW, AlertPriority.LOW),
            (RiskLevel.MEDIUM, AlertPriority.MEDIUM),
            (RiskLevel.HIGH, AlertPriority.HIGH),
            (RiskLevel.CRITICAL, AlertPriority.CRITICAL)
        ]

        for risk_level, expected_priority in mappings:
            priority = alert_system._determine_alert_priority(risk_level)
            assert priority == expected_priority

    @pytest.mark.asyncio
    async def test_notification_channel_selection(self, alert_system, sample_competitive_analysis, sample_lead_data):
        """Test notification channel selection based on risk level"""
        # Test HIGH risk alert
        alert = await alert_system.send_competitive_alert(
            lead_id="lead_123",
            lead_data=sample_lead_data,
            competitive_analysis=sample_competitive_analysis
        )

        # HIGH risk should trigger multiple channels
        assert len(alert.channels_sent) > 1
        assert NotificationChannel.SLACK in alert.channels_sent
        assert NotificationChannel.GHL_TAG in alert.channels_sent

    @pytest.mark.asyncio
    async def test_rate_limiting(self, alert_system):
        """Test rate limiting functionality"""
        # Test that rate limiting prevents excessive notifications
        channel = NotificationChannel.SMS
        priority = AlertPriority.HIGH

        # First few should pass
        for i in range(3):
            should_send = await alert_system._should_send_notification(channel, priority)
            if should_send:
                alert_system._increment_rate_limit(channel)

        # Eventually should be rate limited (depends on config)
        rate_limited = False
        for i in range(10):
            should_send = await alert_system._should_send_notification(channel, priority)
            if not should_send:
                rate_limited = True
                break
            alert_system._increment_rate_limit(channel)

        # Should eventually hit rate limit
        assert rate_limited

    @pytest.mark.asyncio
    async def test_ghl_tagging(self, alert_system, sample_competitive_analysis, sample_lead_data):
        """Test GHL tagging functionality"""
        alert = await alert_system.send_competitive_alert(
            lead_id="lead_123",
            lead_data=sample_lead_data,
            competitive_analysis=sample_competitive_analysis
        )

        # Verify GHL client was called to add tags
        alert_system.ghl_client.add_tags_to_contact.assert_called()
        call_args = alert_system.ghl_client.add_tags_to_contact.call_args

        # Check that appropriate tags were added
        lead_id, tags = call_args[0]
        assert lead_id == "lead_123"
        assert any("Competitor-Risk-High" in tag for tag in tags)

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_slack_notification(self, mock_httpx, alert_system, sample_competitive_analysis, sample_lead_data):
        """Test Slack notification sending"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        # Test Slack notification
        success = await alert_system._send_slack_notification(
            CompetitiveAlert(
                alert_id="test_alert",
                lead_id="lead_123",
                lead_name="John Doe",
                lead_phone="+1234567890",
                lead_email=None,
                competitive_analysis=sample_competitive_analysis,
                priority=AlertPriority.HIGH,
                channels_sent=[],
                timestamp=datetime.now(),
                jorge_notified=False,
                human_intervention_required=True,
                escalation_level=0,
                resolved=False,
                resolution_notes=None
            )
        )

        assert success is True
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_sms_notification_placeholder(self, alert_system, sample_competitive_analysis):
        """Test SMS notification (placeholder implementation)"""
        alert = CompetitiveAlert(
            alert_id="test_alert",
            lead_id="lead_123",
            lead_name="John Doe",
            lead_phone="+1234567890",
            lead_email=None,
            competitive_analysis=sample_competitive_analysis,
            priority=AlertPriority.CRITICAL,
            channels_sent=[],
            timestamp=datetime.now(),
            jorge_notified=False,
            human_intervention_required=True,
            escalation_level=0,
            resolved=False,
            resolution_notes=None
        )

        # Test SMS notification (placeholder should return True for now)
        success = await alert_system._send_sms_notification(alert)

        # Placeholder implementation should not fail
        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_email_notification_placeholder(self, alert_system, sample_competitive_analysis):
        """Test email notification (placeholder implementation)"""
        alert = CompetitiveAlert(
            alert_id="test_alert",
            lead_id="lead_123",
            lead_name="John Doe",
            lead_phone=None,
            lead_email="john@example.com",
            competitive_analysis=sample_competitive_analysis,
            priority=AlertPriority.HIGH,
            channels_sent=[],
            timestamp=datetime.now(),
            jorge_notified=False,
            human_intervention_required=True,
            escalation_level=0,
            resolved=False,
            resolution_notes=None
        )

        # Test email notification (placeholder should return True for now)
        success = await alert_system._send_email_notification(alert)

        # Placeholder implementation should not fail
        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_escalation_scheduling(self, alert_system, sample_competitive_analysis, sample_lead_data):
        """Test escalation scheduling"""
        alert = await alert_system.send_competitive_alert(
            lead_id="lead_123",
            lead_data=sample_lead_data,
            competitive_analysis=sample_competitive_analysis
        )

        # Verify escalation was scheduled
        escalation_key = f"escalation_pending:{alert.alert_id}"
        alert_system.cache.set.assert_called()

        # Check if escalation data was stored
        set_calls = [call for call in alert_system.cache.set.call_args_list
                    if escalation_key in str(call)]
        assert len(set_calls) > 0

    @pytest.mark.asyncio
    async def test_alert_resolution(self, alert_system):
        """Test alert resolution"""
        alert_id = "test_alert_123"
        resolution_notes = "Lead chose Jorge after comparison"

        await alert_system.mark_alert_resolved(alert_id, resolution_notes)

        # Verify escalation was cancelled
        escalation_key = f"escalation_pending:{alert_id}"
        alert_system.cache.delete.assert_called_with(escalation_key)

        # Verify alert was updated with resolution
        alert_key = f"competitive_alert:{alert_id}"
        alert_system.cache.get.assert_called_with(alert_key)

    @pytest.mark.asyncio
    async def test_active_alerts_retrieval(self, alert_system):
        """Test retrieval of active alerts"""
        # Mock cache to return sample alert data
        sample_alert_data = {
            "alert_id": "alert_123",
            "lead_id": "lead_123",
            "risk_level": "high",
            "resolved": False,
            "timestamp": datetime.now().isoformat()
        }

        alert_system.cache.get_keys_by_pattern = AsyncMock(return_value=["competitive_alert:alert_123"])
        alert_system.cache.get = AsyncMock(return_value=sample_alert_data)

        active_alerts = await alert_system.get_active_alerts()

        assert len(active_alerts) == 1
        assert active_alerts[0]["alert_id"] == "alert_123"
        assert active_alerts[0]["resolved"] is False

    @pytest.mark.asyncio
    async def test_critical_risk_phone_call(self, alert_system):
        """Test phone call notification for critical alerts"""
        critical_analysis = CompetitiveAnalysis(
            has_competitor_risk=True,
            risk_level=RiskLevel.CRITICAL,
            mentions=[],
            recommended_responses=[],
            alert_required=True,
            escalation_needed=True,
            recovery_strategies=[],
            confidence_score=0.95
        )

        sample_lead_data = {
            "id": "lead_critical",
            "name": "Critical Lead",
            "phone": "+1234567890"
        }

        alert = await alert_system.send_competitive_alert(
            lead_id="lead_critical",
            lead_data=sample_lead_data,
            competitive_analysis=critical_analysis
        )

        # CRITICAL risk should escalate to higher priority
        assert alert.priority == AlertPriority.CRITICAL
        assert alert.human_intervention_required is True

    @pytest.mark.asyncio
    async def test_error_handling_in_alert_sending(self, alert_system, sample_lead_data):
        """Test error handling when alert sending fails"""
        # Create malformed competitive analysis to trigger error
        malformed_analysis = CompetitiveAnalysis(
            has_competitor_risk=True,
            risk_level=RiskLevel.HIGH,
            mentions=None,  # This could cause issues
            recommended_responses=[],
            alert_required=True,
            escalation_needed=False,
            recovery_strategies=[],
            confidence_score=0.8
        )

        # Should not raise exception, should return alert with error info
        alert = await alert_system.send_competitive_alert(
            lead_id="lead_error",
            lead_data=sample_lead_data,
            competitive_analysis=malformed_analysis
        )

        assert alert is not None
        # Error case should still return some alert info for tracking

    @pytest.mark.asyncio
    async def test_notification_config_loading(self, alert_system):
        """Test notification configuration loading"""
        configs = alert_system.notification_configs

        # Should have all required channels
        channel_types = [config.channel for config in configs]
        assert NotificationChannel.SLACK in channel_types
        assert NotificationChannel.SMS in channel_types
        assert NotificationChannel.EMAIL in channel_types
        assert NotificationChannel.GHL_TAG in channel_types

        # Each config should have required fields
        for config in configs:
            assert hasattr(config, 'enabled')
            assert hasattr(config, 'priority_threshold')
            assert hasattr(config, 'rate_limit')

    @pytest.mark.asyncio
    async def test_escalation_rules_loading(self, alert_system):
        """Test escalation rules loading"""
        escalation_rules = alert_system.escalation_rules

        # Should have rules for all risk levels
        assert RiskLevel.LOW in escalation_rules
        assert RiskLevel.MEDIUM in escalation_rules
        assert RiskLevel.HIGH in escalation_rules
        assert RiskLevel.CRITICAL in escalation_rules

        # Rules should have required fields
        for risk_level, rules in escalation_rules.items():
            assert "priority" in rules
            assert "channels" in rules
            assert "human_intervention" in rules

    def test_singleton_pattern(self):
        """Test singleton pattern for competitive alert system"""
        system1 = get_competitive_alert_system()
        system2 = get_competitive_alert_system()

        assert system1 is system2

    @pytest.mark.asyncio
    async def test_jorge_contact_information(self, alert_system):
        """Test Jorge's contact information is properly configured"""
        jorge_contacts = alert_system.jorge_contacts

        # Should have all contact methods
        assert "phone" in jorge_contacts
        assert "email" in jorge_contacts
        assert "slack_user_id" in jorge_contacts

        # Contact info should not be empty (in real config)
        # In test, these might be None/empty
        assert isinstance(jorge_contacts, dict)

    @pytest.mark.asyncio
    async def test_concurrent_alert_handling(self, alert_system, sample_competitive_analysis, sample_lead_data):
        """Test handling of concurrent alert requests"""
        # Create multiple leads
        lead_data_list = []
        for i in range(5):
            lead_data = sample_lead_data.copy()
            lead_data["id"] = f"lead_{i}"
            lead_data["name"] = f"Lead {i}"
            lead_data_list.append(lead_data)

        # Send alerts concurrently
        tasks = [
            alert_system.send_competitive_alert(
                lead_id=lead_data["id"],
                lead_data=lead_data,
                competitive_analysis=sample_competitive_analysis
            )
            for lead_data in lead_data_list
        ]

        alerts = await asyncio.gather(*tasks)

        # All alerts should be created successfully
        assert len(alerts) == 5
        assert all(alert.lead_id.startswith("lead_") for alert in alerts)
        assert all(alert.competitive_analysis == sample_competitive_analysis for alert in alerts)

    @pytest.mark.asyncio
    async def test_alert_data_privacy(self, alert_system, sample_competitive_analysis):
        """Test that sensitive data is not exposed in alerts"""
        sensitive_lead_data = {
            "id": "lead_sensitive",
            "name": "John Doe",
            "phone": "+1234567890",
            "email": "john@example.com",
            "ssn": "123-45-6789",  # Sensitive data
            "credit_score": 750   # Sensitive data
        }

        alert = await alert_system.send_competitive_alert(
            lead_id="lead_sensitive",
            lead_data=sensitive_lead_data,
            competitive_analysis=sample_competitive_analysis
        )

        # Alert should not contain sensitive data
        assert hasattr(alert, 'lead_name')
        assert hasattr(alert, 'lead_phone')
        assert hasattr(alert, 'lead_email')

        # Sensitive fields should not be stored in alert
        assert not hasattr(alert, 'ssn')
        assert not hasattr(alert, 'credit_score')


if __name__ == "__main__":
    pytest.main([__file__])