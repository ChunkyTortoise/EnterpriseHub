"""
Comprehensive tests for SMS Compliance Service
Tests TCPA compliance, opt-out handling, and frequency caps.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ghl_real_estate_ai.services.sms_compliance_service import (
    SMSComplianceService, SMSValidationResult, OptOutReason, get_sms_compliance_service
)

class TestSMSComplianceService:
    """Test suite for SMS Compliance Service implementation."""

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service for testing."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_cache.incr.return_value = 1
        mock_cache.exists.return_value = False
        return mock_cache

    @pytest.fixture
    def mock_event_publisher(self):
        """Mock event publisher for testing."""
        mock_publisher = AsyncMock()
        mock_publisher.publish_sms_frequency_limit_hit.return_value = None
        mock_publisher.publish_sms_opt_out_processed.return_value = None
        mock_publisher.publish_sms_compliance_event.return_value = None
        return mock_publisher

    @pytest.fixture
    def sms_compliance_service(self, mock_cache_service, mock_event_publisher):
        """Create SMS compliance service with mocked dependencies."""
        service = SMSComplianceService()
        service.cache = mock_cache_service
        service.event_publisher = mock_event_publisher
        return service

    def test_normalize_phone_number(self, sms_compliance_service):
        """Test phone number normalization to E.164 format."""
        service = sms_compliance_service

        # Test 10-digit US number
        result = service._normalize_phone_number("(555) 123-4567")
        assert result == "+15551234567"

        # Test 11-digit with country code
        result = service._normalize_phone_number("1-555-123-4567")
        assert result == "+15551234567"

        # Test already normalized
        result = service._normalize_phone_number("+15551234567")
        assert result == "+15551234567"

        # Test with spaces and special characters
        result = service._normalize_phone_number("+1 (555) 123-4567")
        assert result == "+15551234567"

    @pytest.mark.asyncio
    async def test_validate_sms_send_allowed(self, sms_compliance_service, mock_cache_service):
        """Test SMS validation when send is allowed."""
        mock_cache_service.exists.return_value = False  # Not opted out
        mock_cache_service.get.side_effect = [None, None, None]  # No frequency counts, no last sent

        result = await sms_compliance_service.validate_sms_send(
            phone_number="+15551234567",
            message_content="Your property showing is confirmed for tomorrow."
        )

        assert result.allowed == True
        assert result.reason is None
        assert result.daily_count == 0
        assert result.monthly_count == 0

    @pytest.mark.asyncio
    async def test_validate_sms_send_opted_out(self, sms_compliance_service, mock_cache_service):
        """Test SMS validation when number is opted out."""
        mock_cache_service.exists.return_value = True  # Opted out

        result = await sms_compliance_service.validate_sms_send(
            phone_number="+15551234567",
            message_content="Your property showing is confirmed."
        )

        assert result.allowed == False
        assert result.reason == "opted_out"
        assert "opted out" in result.compliance_notes

    @pytest.mark.asyncio
    async def test_validate_sms_send_daily_limit_exceeded(self, sms_compliance_service, mock_cache_service):
        """Test SMS validation when daily limit is exceeded."""
        mock_cache_service.exists.return_value = False  # Not opted out
        mock_cache_service.get.side_effect = ["3", None, None]  # Daily count at limit, no monthly, no last sent

        result = await sms_compliance_service.validate_sms_send(
            phone_number="+15551234567",
            message_content="Another message"
        )

        assert result.allowed == False
        assert result.reason == "daily_limit_exceeded"
        assert result.daily_count == 3
        assert "Daily limit" in result.compliance_notes

    @pytest.mark.asyncio
    async def test_validate_sms_send_monthly_limit_exceeded(self, sms_compliance_service, mock_cache_service):
        """Test SMS validation when monthly limit is exceeded."""
        mock_cache_service.exists.return_value = False  # Not opted out
        mock_cache_service.get.side_effect = ["2", "20", None]  # Under daily, at monthly limit

        result = await sms_compliance_service.validate_sms_send(
            phone_number="+15551234567",
            message_content="Another message"
        )

        assert result.allowed == False
        assert result.reason == "monthly_limit_exceeded"
        assert result.monthly_count == 20
        assert "Monthly limit" in result.compliance_notes

    @pytest.mark.asyncio
    async def test_process_incoming_sms_stop_keyword(self, sms_compliance_service):
        """Test processing incoming SMS with STOP keyword."""
        with patch.object(sms_compliance_service, 'process_opt_out', new_callable=AsyncMock) as mock_opt_out:
            result = await sms_compliance_service.process_incoming_sms(
                phone_number="+15551234567",
                message_content="STOP sending me messages",
                location_id="test_location"
            )

            # Verify opt-out was processed
            mock_opt_out.assert_called_once_with(
                phone_number="+15551234567",
                reason=OptOutReason.STOP_KEYWORD,
                message_content="STOP sending me messages",
                location_id="test_location"
            )

            assert result["action"] == "opt_out_processed"
            assert result["method"] == "stop_keyword"
            assert "STOP" in result["keywords_detected"]

    @pytest.mark.asyncio
    async def test_process_incoming_sms_no_stop_keyword(self, sms_compliance_service):
        """Test processing incoming SMS without STOP keyword."""
        result = await sms_compliance_service.process_incoming_sms(
            phone_number="+15551234567",
            message_content="Yes, I'm interested in the property",
            location_id="test_location"
        )

        assert result["action"] == "message_processed"
        assert result["opt_out_status"] == "not_opted_out"
        assert "compliance_flags" in result

    def test_stop_keywords_detection(self, sms_compliance_service):
        """Test various STOP keywords are detected."""
        service = sms_compliance_service

        stop_messages = [
            "STOP",
            "Please UNSUBSCRIBE me",
            "QUIT sending messages",
            "CANCEL this service",
            "END these notifications",
            "REMOVE me from list"
        ]

        for message in stop_messages:
            message_upper = message.upper()
            contains_stop = any(keyword in message_upper for keyword in service.STOP_KEYWORDS)
            assert contains_stop, f"Should detect STOP keyword in: {message}"

    @pytest.mark.asyncio
    async def test_process_opt_out(self, sms_compliance_service, mock_cache_service, mock_event_publisher):
        """Test opt-out processing with audit trail."""
        phone_number = "+15551234567"
        reason = OptOutReason.STOP_KEYWORD
        message_content = "STOP"

        await sms_compliance_service.process_opt_out(
            phone_number=phone_number,
            reason=reason,
            message_content=message_content,
            location_id="test_location"
        )

        # Verify cache was updated
        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert call_args[0][0] == f"sms_opted_out:{phone_number}"
        assert call_args[1]["ttl"] == 86400*365*2  # 2 years

        # Verify events were published
        mock_event_publisher.publish_sms_opt_out_processed.assert_called_once()
        mock_event_publisher.publish_sms_compliance_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_sms_sent(self, sms_compliance_service, mock_cache_service):
        """Test SMS send recording for frequency tracking."""
        phone_number = "+15551234567"
        message_content = "Your showing is confirmed"

        await sms_compliance_service.record_sms_sent(
            phone_number=phone_number,
            message_content=message_content,
            success=True,
            location_id="test_location"
        )

        # Verify cache increments were called
        assert mock_cache_service.incr.call_count >= 2  # Daily and monthly counters
        assert mock_cache_service.set.call_count >= 1  # Last sent timestamp

    @pytest.mark.asyncio
    async def test_get_compliance_status(self, sms_compliance_service, mock_cache_service):
        """Test getting complete compliance status."""
        phone_number = "+15551234567"

        # Mock return values
        mock_cache_service.exists.return_value = False  # Not opted out
        mock_cache_service.get.side_effect = [
            None,  # No opt-out data
            "2",   # Daily count
            "15",  # Monthly count
            datetime.now().isoformat()  # Last sent timestamp
        ]

        status = await sms_compliance_service.get_compliance_status(phone_number)

        assert status["phone_number"] == phone_number
        assert status["opted_out"] == False
        assert status["daily_count"] == 2
        assert status["monthly_count"] == 15
        assert status["compliance_status"] == "compliant"

    @pytest.mark.asyncio
    async def test_get_compliance_status_opted_out(self, sms_compliance_service, mock_cache_service):
        """Test compliance status for opted-out number."""
        phone_number = "+15551234567"

        mock_cache_service.exists.return_value = True  # Opted out
        mock_cache_service.get.side_effect = [
            {"opted_out_at": datetime.now().isoformat(), "reason": "stop_keyword"},
            "0", "0", None
        ]

        status = await sms_compliance_service.get_compliance_status(phone_number)

        assert status["opted_out"] == True
        assert status["opt_out_data"]["reason"] == "stop_keyword"

    def test_check_compliance_flags(self, sms_compliance_service):
        """Test compliance flag detection in message content."""
        service = sms_compliance_service

        # Test aggressive language
        aggressive_message = "YOU MUST ACT NOW! URGENT FINAL NOTICE!"
        flags = service._check_compliance_flags(aggressive_message)
        assert "aggressive_language" in flags

        # Test financial content
        financial_message = "Information about your mortgage and debt payments"
        flags = service._check_compliance_flags(financial_message)
        assert "financial_content" in flags

        # Test clean message
        clean_message = "Your property showing is scheduled for tomorrow at 2 PM"
        flags = service._check_compliance_flags(clean_message)
        assert len(flags) == 0

    @pytest.mark.asyncio
    async def test_validate_sms_send_error_handling(self, sms_compliance_service, mock_cache_service):
        """Test error handling in SMS validation."""
        mock_cache_service.exists.side_effect = Exception("Cache error")

        result = await sms_compliance_service.validate_sms_send(
            phone_number="+15551234567",
            message_content="Test message"
        )

        assert result.allowed == False
        assert result.reason == "validation_error"
        assert "validation error" in result.compliance_notes.lower()

    @pytest.mark.asyncio
    async def test_process_incoming_sms_error_handling(self, sms_compliance_service):
        """Test error handling in incoming SMS processing."""
        with patch.object(sms_compliance_service, '_normalize_phone_number', side_effect=Exception("Normalization error")):
            result = await sms_compliance_service.process_incoming_sms(
                phone_number="invalid",
                message_content="test",
                location_id="test"
            )

            assert result["action"] == "processing_error"
            assert "error" in result


class TestSMSComplianceServiceLimits:
    """Test SMS compliance limits and thresholds."""

    @pytest.fixture
    def service(self):
        return SMSComplianceService()

    def test_compliance_limits(self, service):
        """Test compliance limit constants."""
        assert service.DAILY_LIMIT == 3
        assert service.MONTHLY_LIMIT == 20
        assert service.BUSINESS_HOURS_START == 8
        assert service.BUSINESS_HOURS_END == 21

    def test_stop_keywords_comprehensive(self, service):
        """Test comprehensive STOP keywords list."""
        expected_keywords = {
            "STOP", "UNSUBSCRIBE", "QUIT", "CANCEL", "END",
            "REMOVE", "HALT", "OPT-OUT", "OPTOUT", "NO", "OFF"
        }

        for keyword in expected_keywords:
            assert keyword in service.STOP_KEYWORDS, f"Missing STOP keyword: {keyword}"


class TestSMSComplianceIntegration:
    """Integration tests for SMS compliance with other services."""

    @pytest.mark.asyncio
    async def test_event_publishing_integration(self):
        """Test SMS compliance events are properly published."""
        # This would test real event publisher integration
        pass

    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test SMS compliance with real Redis cache."""
        # This would test real cache integration
        pass

    @pytest.mark.asyncio
    async def test_webhook_endpoint_integration(self):
        """Test SMS compliance webhook endpoints."""
        # This would test the FastAPI endpoints
        pass


def test_get_sms_compliance_service_singleton():
    """Test that the service factory returns singleton instance."""
    service1 = get_sms_compliance_service()
    service2 = get_sms_compliance_service()

    assert service1 is service2
    assert isinstance(service1, SMSComplianceService)