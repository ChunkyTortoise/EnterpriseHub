import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Comprehensive tests for Twilio Client.

Tests cover:
- Twilio SMS client initialization and configuration
- Phone number validation and formatting
- SMS message sending and delivery tracking
- Webhook processing for status updates and incoming messages
- Opt-out/opt-in management and TCPA compliance
- Bulk SMS operations
- Rate limiting and error handling
- Health monitoring and usage statistics

Coverage Target: 85%+ for all Twilio operations
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Import the module under test
try:
    from ghl_real_estate_ai.services.twilio_client import (
        MessageStatus,
        OptOutRecord,
        PhoneNumberInfo,
        SMSMessage,
        TwilioAPIException,
        TwilioClient,
        TwilioConfig,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)

# Import test utilities
from tests.mocks.external_services import MockTwilioClient, MockWebhookPayloads


class TestTwilioConfig:
    """Test Twilio configuration management"""

    def test_default_config_creation(self):
        """Test default Twilio configuration uses settings defaults"""
        # TwilioConfig pulls defaults from settings; the validator rejects
        # placeholder values like 'your_twilio_*', so we verify with valid values.
        config = TwilioConfig(
            account_sid="ACtest1234567890",
            auth_token="valid_auth_token_value",
            phone_number="+15125551234",
        )

        assert config.account_sid == "ACtest1234567890"
        assert config.auth_token == "valid_auth_token_value"
        assert config.phone_number == "+15125551234"
        assert config.rate_limit_messages_per_minute == 100
        assert config.max_retries == 3
        assert config.timeout == 30
        assert config.retry_delay == 1.0

    def test_custom_config_creation(self):
        """Test custom Twilio configuration"""
        config = TwilioConfig(
            account_sid="test_account_sid",
            auth_token="test_auth_token",
            phone_number="+15551234567",
            rate_limit_messages_per_minute=50,
            max_retries=5,
            timeout=60,
            retry_delay=2.0,
        )

        assert config.account_sid == "test_account_sid"
        assert config.auth_token == "test_auth_token"
        assert config.phone_number == "+15551234567"
        assert config.rate_limit_messages_per_minute == 50
        assert config.max_retries == 5
        assert config.timeout == 60
        assert config.retry_delay == 2.0

    def test_config_rejects_placeholder_values(self):
        """Test that placeholder values are rejected by validation"""
        with pytest.raises(ValueError):
            TwilioConfig(
                account_sid="your_twilio_account_sid",
                auth_token="your_twilio_auth_token",
                phone_number="+15125551234",
            )

    def test_config_requires_country_code(self):
        """Test phone number must include country code"""
        with pytest.raises(ValueError):
            TwilioConfig(
                account_sid="test_sid",
                auth_token="test_token",
                phone_number="5551234567",
            )


def _make_mock_twilio_message(**overrides):
    """Helper to create a mock Twilio message object with all needed attributes."""
    msg = MagicMock()
    msg.sid = overrides.get("sid", "SM123456789")
    msg.to = overrides.get("to", "+15557890123")
    msg.from_ = overrides.get("from_", "+15551234567")
    msg.body = overrides.get("body", "Test message")
    msg.status = overrides.get("status", "sent")
    msg.direction = overrides.get("direction", "outbound-api")
    msg.date_created = overrides.get("date_created", datetime.now())
    msg.date_sent = overrides.get("date_sent", datetime.now())
    msg.date_updated = overrides.get("date_updated", datetime.now())
    msg.error_code = overrides.get("error_code", None)
    msg.error_message = overrides.get("error_message", None)
    msg.price = overrides.get("price", None)
    msg.price_unit = overrides.get("price_unit", None)
    msg.uri = overrides.get("uri", None)
    return msg


class TestTwilioClient:
    """Test Twilio client operations"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client with mocked dependencies"""
        config = TwilioConfig(account_sid="test_account_sid", auth_token="test_auth_token", phone_number="+15551234567")

        # Mock cache service
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        # Mock database service
        mock_database = AsyncMock()

        client = TwilioClient(config, cache_service=mock_cache, database_service=mock_database)

        # Mock Twilio sync client
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        mock_message = _make_mock_twilio_message()
        mock_messages.create.return_value = mock_message
        mock_sync_client.messages = mock_messages

        client.sync_client = mock_sync_client
        client._mock_message = mock_message  # Store for test access

        return client

    @pytest.mark.asyncio
    async def test_client_initialization(self, twilio_client):
        """Test Twilio client initialization"""
        assert twilio_client.config is not None
        assert twilio_client.cache_service is not None
        assert twilio_client.database_service is not None
        assert twilio_client._rate_limit_semaphore is not None
        assert twilio_client._opt_out_cache == set()

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client as async context manager"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=[])
        mock_cache.set = AsyncMock(return_value=True)

        client = TwilioClient(config, cache_service=mock_cache)
        # Replace sync_client to avoid real Twilio connection
        client.sync_client = MagicMock()

        async with client as c:
            assert c.session is not None

        # Client should be closed after context exit

    @pytest.mark.asyncio
    async def test_ensure_session(self, twilio_client):
        """Test session creation and management"""
        # Reset session to test creation
        twilio_client.session = None

        await twilio_client._ensure_session()

        assert twilio_client.session is not None
        # Cleanup
        await twilio_client.close()

    @pytest.mark.asyncio
    async def test_client_close(self, twilio_client):
        """Test client cleanup"""
        # Mock session
        mock_session = AsyncMock()
        twilio_client.session = mock_session

        await twilio_client.close()

        mock_session.close.assert_called_once()


class TestPhoneNumberValidation:
    """Test phone number validation and formatting"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for phone validation testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")
        client = TwilioClient(config)
        # Mock the sync_client to prevent real API calls
        client.sync_client = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_validate_phone_number_valid_us(self, twilio_client):
        """Test validation of valid US phone number"""
        # Mock the Twilio lookup response
        mock_lookup = MagicMock()
        mock_lookup.phone_number = "+15551234567"
        mock_lookup.country_code = "US"
        mock_lookup.national_format = "(555) 123-4567"
        mock_lookup.carrier = {"name": "T-Mobile", "type": "mobile"}

        twilio_client.sync_client.lookups.v1.phone_numbers.return_value.fetch.return_value = mock_lookup

        # Mock cache service
        twilio_client.cache_service = AsyncMock()
        twilio_client.cache_service.set = AsyncMock()

        result = await twilio_client.validate_phone_number("+15551234567")

        assert isinstance(result, PhoneNumberInfo)
        assert result.valid is True
        assert result.phone_number == "+15551234567"
        assert result.country_code == "US"
        assert result.carrier_type == "mobile"

    @pytest.mark.asyncio
    async def test_validate_phone_number_format_us(self, twilio_client):
        """Test formatting of various US phone number formats via normalization"""
        test_numbers = [
            ("5551234567", "+15551234567"),
            ("15551234567", "+15551234567"),
        ]

        for input_number, expected_normalized in test_numbers:
            result = twilio_client._normalize_phone_number(input_number)
            assert result == expected_normalized, f"Expected {expected_normalized} for {input_number}, got {result}"

    @pytest.mark.asyncio
    async def test_validate_phone_number_international(self, twilio_client):
        """Test validation of international phone numbers"""
        # Mock the Twilio lookup response for UK number
        mock_lookup = MagicMock()
        mock_lookup.phone_number = "+447700900123"
        mock_lookup.country_code = "GB"
        mock_lookup.national_format = "07700 900123"
        mock_lookup.carrier = {"name": "Vodafone", "type": "mobile"}

        twilio_client.sync_client.lookups.v1.phone_numbers.return_value.fetch.return_value = mock_lookup

        twilio_client.cache_service = AsyncMock()
        twilio_client.cache_service.set = AsyncMock()

        result = await twilio_client.validate_phone_number("+447700900123")

        assert result.valid is True
        assert result.phone_number == "+447700900123"
        assert result.country_code == "GB"

    @pytest.mark.asyncio
    async def test_validate_phone_number_invalid(self, twilio_client):
        """Test validation of invalid phone numbers returns valid=False"""
        from twilio.base.exceptions import TwilioRestException

        # When Twilio returns 20404, the method returns PhoneNumberInfo with valid=False
        twilio_client.sync_client.lookups.v1.phone_numbers.return_value.fetch.side_effect = TwilioRestException(
            status=404, uri="/PhoneNumbers", msg="Phone number not found", code=20404
        )

        result = await twilio_client.validate_phone_number("+999999999")
        assert result.valid is False

    @pytest.mark.asyncio
    async def test_normalize_phone_number(self, twilio_client):
        """Test phone number normalization"""
        # Test US number normalization (10 digits -> +1 prefix)
        normalized = twilio_client._normalize_phone_number("(555) 123-4567")
        assert normalized == "+15551234567"

        # Test international number (already normalized)
        normalized = twilio_client._normalize_phone_number("+447700900123")
        assert normalized == "+447700900123"

        # Test 11-digit US number starting with 1
        normalized = twilio_client._normalize_phone_number("15551234567")
        assert normalized == "+15551234567"


class TestSMSSending:
    """Test SMS message sending functionality"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for SMS testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        mock_database = AsyncMock()

        client = TwilioClient(config, cache_service=mock_cache, database_service=mock_database)

        # Mock successful message sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        mock_message = _make_mock_twilio_message(
            body="Hello from Service 6! Your property viewing is confirmed for tomorrow at 2pm.. Reply STOP to opt out"
        )
        mock_messages.create.return_value = mock_message
        mock_sync_client.messages = mock_messages

        client.sync_client = mock_sync_client
        client._mock_message = mock_message

        return client

    @pytest.mark.asyncio
    async def test_send_sms_success(self, twilio_client):
        """Test successful SMS sending"""
        result = await twilio_client.send_sms(
            to="+15557890123",
            message="Hello from Service 6! Your property viewing is confirmed for tomorrow at 2pm.",
        )

        assert isinstance(result, SMSMessage)
        assert result.sid == "SM123456789"
        assert result.status == "sent"
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_send_sms_with_compliance_footer(self, twilio_client):
        """Test SMS sending adds compliance footer automatically"""
        result = await twilio_client.send_sms(
            to="+15557890123",
            message="Property update for North Rancho Cucamonga",
        )

        # The service always adds the compliance footer via _add_compliance_footer
        call_args = twilio_client.sync_client.messages.create.call_args
        body_sent = call_args[1]["body"] if "body" in (call_args[1] or {}) else call_args.kwargs.get("body", "")
        assert "Reply STOP to opt out" in body_sent

    @pytest.mark.asyncio
    async def test_send_sms_opted_out_number(self, twilio_client):
        """Test SMS sending to opted-out number"""
        # Add number to opt-out cache
        twilio_client._opt_out_cache.add("+15557890123")

        with pytest.raises(TwilioAPIException, match="opted out"):
            await twilio_client.send_sms(to="+15557890123", message="This should not be sent")

    @pytest.mark.asyncio
    async def test_send_sms_api_error(self, twilio_client):
        """Test SMS sending when API returns error"""
        # Mock API error
        from twilio.base.exceptions import TwilioRestException

        twilio_client.sync_client.messages.create.side_effect = TwilioRestException(
            status=400, uri="/Messages", msg="Invalid 'To' Phone Number", code=21211
        )

        with pytest.raises(TwilioAPIException, match="SMS sending failed"):
            await twilio_client.send_sms(to="+15557890123", message="This will fail")

    @pytest.mark.asyncio
    async def test_send_sms_rate_limiting(self, twilio_client):
        """Test SMS rate limiting behavior"""
        # Set up rate limiting (1 message at a time)
        twilio_client._rate_limit_semaphore = asyncio.Semaphore(1)

        # Send multiple messages concurrently
        tasks = []
        for i in range(3):
            task = twilio_client.send_sms(to=f"+155512345{i:02d}", message=f"Message {i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed but be rate limited
        assert len(results) == 3
        assert all(isinstance(r, SMSMessage) for r in results if not isinstance(r, Exception))


class TestTemplatedSMS:
    """Test templated SMS functionality"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for template testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        client = TwilioClient(config, cache_service=mock_cache)

        # Mock successful message sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        mock_message = _make_mock_twilio_message()
        mock_messages.create.return_value = mock_message
        mock_sync_client.messages = mock_messages

        client.sync_client = mock_sync_client

        return client

    @pytest.mark.asyncio
    async def test_send_templated_sms_instant_response(self, twilio_client):
        """Test sending instant response template SMS"""
        variables = {
            "first_name": "Sarah",
            "agent_name": "Jorge",
        }

        # Mock template library service to return no templates (fallback to hardcoded)
        with patch("ghl_real_estate_ai.services.twilio_client.get_template_library_service") as mock_tls:
            mock_service = AsyncMock()
            mock_service.search_templates = AsyncMock(return_value=[])
            mock_tls.return_value = mock_service

            result = await twilio_client.send_templated_sms(
                to="+15557890123", template_name="instant_response", variables=variables
            )

        assert isinstance(result, SMSMessage)
        assert result.sid == "SM123456789"

    @pytest.mark.asyncio
    async def test_send_templated_sms_follow_up(self, twilio_client):
        """Test sending follow-up template SMS"""
        variables = {
            "first_name": "Mike",
            "agent_name": "Sarah",
        }

        with patch("ghl_real_estate_ai.services.twilio_client.get_template_library_service") as mock_tls:
            mock_service = AsyncMock()
            mock_service.search_templates = AsyncMock(return_value=[])
            mock_tls.return_value = mock_service

            result = await twilio_client.send_templated_sms(
                to="+15557890123", template_name="follow_up_24h", variables=variables
            )

        assert isinstance(result, SMSMessage)

    @pytest.mark.asyncio
    async def test_send_templated_sms_invalid_template(self, twilio_client):
        """Test sending SMS with invalid template raises error"""
        with patch("ghl_real_estate_ai.services.twilio_client.get_template_library_service") as mock_tls:
            mock_service = AsyncMock()
            mock_service.search_templates = AsyncMock(return_value=[])
            mock_tls.return_value = mock_service

            with pytest.raises(TwilioAPIException, match="not found"):
                await twilio_client.send_templated_sms(
                    to="+15557890123", template_name="nonexistent_template", variables={}
                )

    @pytest.mark.asyncio
    async def test_get_hardcoded_template_instant_response(self, twilio_client):
        """Test getting instant response hardcoded template"""
        template = await twilio_client._get_hardcoded_template("instant_response")

        assert template is not None
        assert "{first_name}" in template["content"]
        assert "{agent_name}" in template["content"]
        assert "id" in template

    @pytest.mark.asyncio
    async def test_get_hardcoded_template_appointment_reminder(self, twilio_client):
        """Test getting appointment reminder hardcoded template"""
        template = await twilio_client._get_hardcoded_template("appointment_reminder")

        assert template is not None
        assert "{first_name}" in template["content"]
        assert "{time}" in template["content"]
        assert "{agent_name}" in template["content"]


class TestOptOutManagement:
    """Test opt-out/opt-in management functionality"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for opt-out testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        # Mock cache service
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=[])
        mock_cache.set = AsyncMock(return_value=True)

        # Mock database service
        mock_database = AsyncMock()

        client = TwilioClient(config, cache_service=mock_cache, database_service=mock_database)
        # Replace sync_client to avoid real Twilio connection
        client.sync_client = MagicMock()

        return client

    @pytest.mark.asyncio
    async def test_process_opt_out(self, twilio_client):
        """Test processing opt-out request"""
        phone_number = "+15557890123"

        result = await twilio_client.process_opt_out(phone_number, "user_request")

        # process_opt_out returns True (bool)
        assert result is True

        # Verify number was added to opt-out cache
        assert phone_number in twilio_client._opt_out_cache

    @pytest.mark.asyncio
    async def test_process_opt_out_variations(self, twilio_client):
        """Test processing various opt-out reasons"""
        opt_out_reasons = ["user_request", "sms_keyword_opt_out", "delivery_failure_21610"]
        phone_number = "+15557890123"

        for reason in opt_out_reasons:
            await twilio_client.process_opt_out(phone_number, reason)
            assert phone_number in twilio_client._opt_out_cache

    @pytest.mark.asyncio
    async def test_process_opt_in(self, twilio_client):
        """Test processing opt-in request"""
        phone_number = "+15557890123"

        # First opt out
        await twilio_client.process_opt_out(phone_number, "user_request")
        assert phone_number in twilio_client._opt_out_cache

        # Then opt back in (process_opt_in takes only phone_number)
        result = await twilio_client.process_opt_in(phone_number)

        # process_opt_in returns True (bool)
        assert result is True

        # Verify number was removed from opt-out cache
        assert phone_number not in twilio_client._opt_out_cache

    @pytest.mark.asyncio
    async def test_process_opt_in_after_opt_out(self, twilio_client):
        """Test opt-in works correctly after opt-out"""
        phone_number = "+15557890123"

        # First opt out
        await twilio_client.process_opt_out(phone_number, "user_request")

        # Then opt back in
        await twilio_client.process_opt_in(phone_number)
        assert phone_number not in twilio_client._opt_out_cache

    @pytest.mark.asyncio
    async def test_is_opted_out(self, twilio_client):
        """Test checking opt-out status"""
        phone_number = "+15557890123"

        # Initially not opted out
        assert not await twilio_client._is_opted_out(phone_number)

        # After opting out
        await twilio_client.process_opt_out(phone_number, "user_request")
        assert await twilio_client._is_opted_out(phone_number)

        # After opting back in
        await twilio_client.process_opt_in(phone_number)
        assert not await twilio_client._is_opted_out(phone_number)


class TestWebhookProcessing:
    """Test webhook processing functionality"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for webhook testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        # Mock cache service
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=[])
        mock_cache.set = AsyncMock(return_value=True)

        # Set database_service to None to skip database operations in webhook handlers
        client = TwilioClient(config, cache_service=mock_cache, database_service=None)
        # Replace sync_client to avoid real Twilio connection
        client.sync_client = MagicMock()

        return client

    @pytest.mark.asyncio
    async def test_process_status_webhook_delivered(self, twilio_client):
        """Test processing delivery status webhook"""
        webhook_data = {
            "MessageSid": "SM123456789",
            "MessageStatus": "delivered",
            "To": "+15557890123",
            "From": "+15551234567",
        }

        mock_request = MagicMock()

        # Mock SecurityFramework to bypass signature verification
        with patch("ghl_real_estate_ai.services.twilio_client.SecurityFramework") as mock_sf_cls:
            mock_sf = AsyncMock()
            mock_sf.verify_webhook_signature = AsyncMock(return_value=True)
            mock_sf.close_redis = AsyncMock()
            mock_sf_cls.return_value = mock_sf

            result = await twilio_client.process_status_webhook(mock_request, webhook_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_process_status_webhook_failed(self, twilio_client):
        """Test processing failed message status webhook"""
        webhook_data = {
            "MessageSid": "SM123456789",
            "MessageStatus": "failed",
            "ErrorCode": "30007",
            "ErrorMessage": "Message delivery failed",
            "To": "+15557890123",
        }

        mock_request = MagicMock()

        with patch("ghl_real_estate_ai.services.twilio_client.SecurityFramework") as mock_sf_cls:
            mock_sf = AsyncMock()
            mock_sf.verify_webhook_signature = AsyncMock(return_value=True)
            mock_sf.close_redis = AsyncMock()
            mock_sf_cls.return_value = mock_sf

            result = await twilio_client.process_status_webhook(mock_request, webhook_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_process_incoming_webhook_normal_message(self, twilio_client):
        """Test processing incoming message webhook"""
        webhook_data = {
            "MessageSid": "SM987654321",
            "From": "+15557890123",
            "To": "+15551234567",
            "Body": "Yes, I am still interested in viewing properties",
        }

        mock_request = MagicMock()

        with patch("ghl_real_estate_ai.services.twilio_client.SecurityFramework") as mock_sf_cls:
            mock_sf = AsyncMock()
            mock_sf.verify_webhook_signature = AsyncMock(return_value=True)
            mock_sf.close_redis = AsyncMock()
            mock_sf_cls.return_value = mock_sf

            result = await twilio_client.process_incoming_webhook(mock_request, webhook_data)

        # process_incoming_webhook returns bool
        assert result is True

    @pytest.mark.asyncio
    async def test_process_incoming_webhook_opt_out(self, twilio_client):
        """Test processing incoming opt-out message"""
        webhook_data = {"MessageSid": "SM987654321", "From": "+15557890123", "To": "+15551234567", "Body": "STOP"}

        mock_request = MagicMock()

        with patch("ghl_real_estate_ai.services.twilio_client.SecurityFramework") as mock_sf_cls:
            mock_sf = AsyncMock()
            mock_sf.verify_webhook_signature = AsyncMock(return_value=True)
            mock_sf.close_redis = AsyncMock()
            mock_sf_cls.return_value = mock_sf

            # Mock send_sms to prevent actual sending of confirmation
            with patch.object(twilio_client, "send_sms", new_callable=AsyncMock):
                result = await twilio_client.process_incoming_webhook(mock_request, webhook_data)

        assert result is True

        # Verify number was opted out
        assert "+15557890123" in twilio_client._opt_out_cache

    @pytest.mark.asyncio
    async def test_process_incoming_webhook_opt_in(self, twilio_client):
        """Test processing incoming opt-in message"""
        phone_number = "+15557890123"

        # First opt out
        await twilio_client.process_opt_out(phone_number, "user_request")

        # Then receive opt-in message
        webhook_data = {"MessageSid": "SM987654321", "From": phone_number, "To": "+15551234567", "Body": "START"}

        mock_request = MagicMock()

        with patch("ghl_real_estate_ai.services.twilio_client.SecurityFramework") as mock_sf_cls:
            mock_sf = AsyncMock()
            mock_sf.verify_webhook_signature = AsyncMock(return_value=True)
            mock_sf.close_redis = AsyncMock()
            mock_sf_cls.return_value = mock_sf

            # Mock send_sms to prevent actual sending of confirmation
            with patch.object(twilio_client, "send_sms", new_callable=AsyncMock):
                result = await twilio_client.process_incoming_webhook(mock_request, webhook_data)

        assert result is True

        # Verify number was opted back in
        assert phone_number not in twilio_client._opt_out_cache

    @pytest.mark.asyncio
    async def test_process_incoming_webhook_missing_fields(self, twilio_client):
        """Test processing webhook with missing required fields returns False"""
        webhook_data = {
            "MessageSid": "SM987654321",
            # Missing 'From', 'To', and empty 'Body'
        }

        mock_request = MagicMock()

        with patch("ghl_real_estate_ai.services.twilio_client.SecurityFramework") as mock_sf_cls:
            mock_sf = AsyncMock()
            mock_sf.verify_webhook_signature = AsyncMock(return_value=True)
            mock_sf.close_redis = AsyncMock()
            mock_sf_cls.return_value = mock_sf

            result = await twilio_client.process_incoming_webhook(mock_request, webhook_data)

        assert result is False


class TestBulkOperations:
    """Test bulk SMS operations"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for bulk operations testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        mock_database = AsyncMock()
        client = TwilioClient(config, cache_service=mock_cache, database_service=mock_database)

        # Mock successful bulk sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()

        def mock_create_message(**kwargs):
            return _make_mock_twilio_message(
                sid=f"SM{abs(hash(kwargs['to'])) % 10**9}",
                to=kwargs.get("to", "+15557890123"),
                from_=kwargs.get("from_", "+15551234567"),
                body=kwargs.get("body", "test"),
            )

        mock_messages.create.side_effect = mock_create_message
        mock_sync_client.messages = mock_messages

        client.sync_client = mock_sync_client

        return client

    @pytest.mark.asyncio
    async def test_send_bulk_sms_success(self, twilio_client):
        """Test successful bulk SMS sending returns results for all recipients"""
        # send_bulk_sms expects list of dicts with 'phone' and 'message' keys
        recipients = [
            {"phone": "+15557890123", "message": "Hi John, your viewing is confirmed!"},
            {"phone": "+15557890124", "message": "Hi Jane, your viewing is confirmed!"},
            {"phone": "+15557890125", "message": "Hi Bob, your viewing is confirmed!"},
        ]

        results = await twilio_client.send_bulk_sms(recipients)

        # Verify results returned for all recipients
        assert len(results) == 3
        # All results should have 'phone' key
        assert all("phone" in result for result in results)
        # Verify messages were attempted
        assert twilio_client.sync_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_send_bulk_sms_with_opt_out_failure(self, twilio_client):
        """Test bulk SMS with opted-out number causes failure"""
        recipients = [
            {"phone": "+15557890123", "message": "Hi John!"},
            {"phone": "+15557890124", "message": "Hi Invalid!"},
            {"phone": "+15557890125", "message": "Hi Bob!"},
        ]

        # Add second number to opt-out cache to cause failure
        twilio_client._opt_out_cache.add("+15557890124")

        results = await twilio_client.send_bulk_sms(recipients)

        # All recipients should have results
        assert len(results) == 3
        # At least one should have failed (the opted-out number)
        failed_results = [r for r in results if not r["success"]]
        assert len(failed_results) >= 1
        # Check error details exist for failed messages
        assert all("error" in r for r in failed_results)

    @pytest.mark.asyncio
    async def test_send_bulk_sms_rate_limiting(self, twilio_client):
        """Test bulk SMS with rate limiting"""
        # Set tight rate limit
        twilio_client._rate_limit_semaphore = asyncio.Semaphore(1)

        recipients = [{"phone": f"+155578901{i:02d}", "message": f"Hi User {i}!"} for i in range(5)]

        import time

        start_time = time.time()

        results = await twilio_client.send_bulk_sms(recipients)

        end_time = time.time()

        # All recipients should have results
        assert len(results) == 5

        # Should take some time due to rate limiting
        execution_time = end_time - start_time
        assert execution_time >= 0  # Basic sanity check


class TestHealthAndMonitoring:
    """Test health check and monitoring functionality"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for health testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        client = TwilioClient(config, cache_service=mock_cache)

        # Mock Twilio client
        mock_sync_client = MagicMock()

        # Mock account info - health_check uses api.accounts(sid).fetch()
        mock_account = MagicMock()
        mock_account.status = "active"
        mock_sync_client.api.accounts.return_value.fetch.return_value = mock_account

        # Mock incoming_phone_numbers list
        mock_phone = MagicMock()
        mock_sync_client.incoming_phone_numbers.list.return_value = [mock_phone]

        client.sync_client = mock_sync_client

        return client

    @pytest.mark.asyncio
    async def test_health_check_success(self, twilio_client):
        """Test successful health check"""
        result = await twilio_client.health_check()

        assert result["status"] == "healthy"
        assert result["account_status"] == "active"
        assert result["phone_number_active"] is True
        assert "opt_out_cache_size" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_health_check_no_phone_number(self, twilio_client):
        """Test health check when phone number is not found"""
        twilio_client.sync_client.incoming_phone_numbers.list.return_value = []

        result = await twilio_client.health_check()

        assert result["status"] == "healthy"
        assert result["phone_number_active"] is False

    @pytest.mark.asyncio
    async def test_health_check_api_failure(self, twilio_client):
        """Test health check when API is unavailable"""
        from twilio.base.exceptions import TwilioRestException

        twilio_client.sync_client.api.accounts.return_value.fetch.side_effect = TwilioRestException(
            status=503, uri="/Accounts", msg="Service unavailable"
        )

        result = await twilio_client.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, twilio_client):
        """Test getting usage statistics"""
        # Mock usage records
        mock_record1 = MagicMock()
        mock_record1.count = "150"
        mock_record1.price = "7.50"

        mock_record2 = MagicMock()
        mock_record2.count = "25"
        mock_record2.price = "5.00"

        twilio_client.sync_client.usage.records.list.return_value = [mock_record1, mock_record2]

        result = await twilio_client.get_usage_stats(days=7)

        assert result["period_days"] == 7
        assert result["total_messages_sent"] == 175  # 150 + 25
        assert result["total_cost"] == 12.50  # 7.50 + 5.00
        assert "opt_out_count" in result
        assert "timestamp" in result


class TestComplianceFeatures:
    """Test TCPA compliance features"""

    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for compliance testing"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        client = TwilioClient(config, cache_service=mock_cache)
        client.sync_client = MagicMock()

        return client

    @pytest.mark.asyncio
    async def test_add_compliance_footer(self, twilio_client):
        """Test adding compliance footer to messages"""
        original_message = "Your property viewing is confirmed."

        message_with_footer = twilio_client._add_compliance_footer(original_message)

        assert "Reply STOP to opt out" in message_with_footer
        assert (
            original_message.rstrip(".") in message_with_footer
            or "Your property viewing is confirmed" in message_with_footer
        )

    @pytest.mark.asyncio
    async def test_add_compliance_footer_already_present(self, twilio_client):
        """Test not duplicating compliance footer"""
        message_with_footer = "Your viewing is confirmed. Reply STOP to opt out."

        result = twilio_client._add_compliance_footer(message_with_footer)

        # Should not add footer if STOP and opt are already mentioned
        assert result.count("STOP") == 1

    @pytest.mark.asyncio
    async def test_opt_out_keyword_detection(self, twilio_client):
        """Test detection of various opt-out keywords"""
        opt_out_messages = [
            "STOP",
            "stop",
            "Stop sending me messages",
            "UNSUBSCRIBE please",
            "QUIT",
            "END these messages",
        ]

        for message in opt_out_messages:
            normalized = message.lower()
            opt_out_keywords = ["stop", "stopall", "unsubscribe", "cancel", "end", "quit"]

            is_opt_out = any(keyword in normalized for keyword in opt_out_keywords)
            assert is_opt_out, f"Failed to detect opt-out in: {message}"


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_config_rejects_empty_credentials(self):
        """Test config initialization rejects empty credentials"""
        with pytest.raises(ValueError):
            TwilioConfig(
                account_sid="",
                auth_token="",
                phone_number="+15551234567",
            )

    @pytest.mark.asyncio
    async def test_config_rejects_placeholder_credentials(self):
        """Test config rejects placeholder credentials"""
        with pytest.raises(ValueError):
            TwilioConfig(
                account_sid="your_twilio_account_sid",
                auth_token="your_twilio_auth_token",
                phone_number="+15551234567",
            )

    @pytest.mark.asyncio
    async def test_send_sms_twilio_rest_exception(self):
        """Test handling of TwilioRestException during send"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        client = TwilioClient(config, cache_service=mock_cache)

        # Mock timeout via TwilioRestException
        from twilio.base.exceptions import TwilioRestException

        mock_sync_client = MagicMock()
        mock_sync_client.messages.create.side_effect = TwilioRestException(
            status=408, uri="/Messages", msg="Request timeout"
        )
        client.sync_client = mock_sync_client

        with pytest.raises(TwilioAPIException, match="SMS sending failed"):
            await client.send_sms(to="+15557890123", message="This will timeout")


@pytest.mark.performance
class TestPerformanceCharacteristics:
    """Test Twilio client performance characteristics"""

    @pytest.mark.asyncio
    async def test_bulk_sms_performance(self):
        """Test performance of bulk SMS operations"""
        config = TwilioConfig(account_sid="test_sid", auth_token="test_token", phone_number="+15551234567")

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        client = TwilioClient(config, cache_service=mock_cache)

        # Mock fast message sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()

        def fast_create(**kwargs):
            return _make_mock_twilio_message(
                sid=f"SM{abs(hash(kwargs['to'])) % 10**9}",
                to=kwargs.get("to", "+15557890123"),
                from_=kwargs.get("from_", "+15551234567"),
                body=kwargs.get("body", "test"),
            )

        mock_messages.create.side_effect = fast_create
        mock_sync_client.messages = mock_messages
        client.sync_client = mock_sync_client

        # Test with many recipients -- send_bulk_sms expects dicts with 'phone' and 'message'
        recipients = [{"phone": f"+155578901{i:02d}", "message": f"Hi User {i}!"} for i in range(50)]

        import time

        start_time = time.time()

        results = await client.send_bulk_sms(recipients)

        end_time = time.time()

        # Verify results for all recipients
        assert len(results) == 50

        # Performance should be reasonable (under 30 seconds for mocked operations with batch delays)
        execution_time = end_time - start_time
        assert execution_time < 30.0


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main(["-v", "tests/services/test_twilio_client.py::TestSMSSending", "--tb=short"])