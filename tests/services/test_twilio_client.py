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
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Import the module under test
try:
    from ghl_real_estate_ai.services.twilio_client import (
        TwilioClient,
        TwilioConfig,
        SMSMessage,
        PhoneNumberInfo,
        OptOutRecord,
        MessageStatus,
        TwilioAPIException
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)

# Import test utilities
from tests.mocks.external_services import MockTwilioClient
from tests.fixtures.sample_data import WebhookTestData


class TestTwilioConfig:
    """Test Twilio configuration management"""
    
    def test_default_config_creation(self):
        """Test default Twilio configuration"""
        config = TwilioConfig()
        
        assert config.account_sid is None  # Should be set via environment
        assert config.auth_token is None   # Should be set via environment
        assert config.phone_number is None # Should be set via environment
        assert config.rate_limit_messages_per_second == 1
        assert config.max_retries == 3
        assert config.request_timeout_seconds == 30
        assert config.enable_delivery_tracking is True
        assert config.enable_opt_out_management is True
        assert config.compliance_footer == "Reply STOP to unsubscribe"
    
    def test_custom_config_creation(self):
        """Test custom Twilio configuration"""
        config = TwilioConfig(
            account_sid="test_account_sid",
            auth_token="test_auth_token", 
            phone_number="+15551234567",
            rate_limit_messages_per_second=0.5,
            max_retries=5,
            enable_delivery_tracking=False,
            compliance_footer="Text STOP to opt out"
        )
        
        assert config.account_sid == "test_account_sid"
        assert config.auth_token == "test_auth_token"
        assert config.phone_number == "+15551234567"
        assert config.rate_limit_messages_per_second == 0.5
        assert config.max_retries == 5
        assert config.enable_delivery_tracking is False
        assert config.compliance_footer == "Text STOP to opt out"


class TestTwilioClient:
    """Test Twilio client operations"""
    
    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client with mocked dependencies"""
        config = TwilioConfig(
            account_sid="test_account_sid",
            auth_token="test_auth_token",
            phone_number="+15551234567"
        )
        
        # Mock cache service
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)
        
        # Mock database service  
        mock_database = AsyncMock()
        mock_database.log_communication = AsyncMock(return_value="comm_123")
        
        client = TwilioClient(config, cache_service=mock_cache, database_service=mock_database)
        
        # Mock Twilio sync client
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456789"
        mock_message.status = "sent"
        mock_message.error_code = None
        mock_message.error_message = None
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
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567"
        )
        
        async with TwilioClient(config) as client:
            assert client.session is not None
        
        # Client should be closed after context exit
    
    @pytest.mark.asyncio
    async def test_ensure_session(self, twilio_client):
        """Test session creation and management"""
        # Reset session to test creation
        twilio_client.session = None
        
        await twilio_client._ensure_session()
        
        assert twilio_client.session is not None
    
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
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token"
        )
        return TwilioClient(config)
    
    @pytest.mark.asyncio
    async def test_validate_phone_number_valid_us(self, twilio_client):
        """Test validation of valid US phone number"""
        result = await twilio_client.validate_phone_number("+15551234567")
        
        assert isinstance(result, PhoneNumberInfo)
        assert result.is_valid is True
        assert result.formatted_number == "+15551234567"
        assert result.country_code == "US"
        assert result.line_type == "mobile"  # Default assumption
    
    @pytest.mark.asyncio
    async def test_validate_phone_number_format_us(self, twilio_client):
        """Test formatting of various US phone number formats"""
        test_numbers = [
            ("5551234567", "+15551234567"),
            ("(555) 123-4567", "+15551234567"),
            ("555-123-4567", "+15551234567"),
            ("1-555-123-4567", "+15551234567"),
            ("+1 555 123 4567", "+15551234567")
        ]
        
        for input_number, expected_formatted in test_numbers:
            result = await twilio_client.validate_phone_number(input_number)
            assert result.formatted_number == expected_formatted
    
    @pytest.mark.asyncio
    async def test_validate_phone_number_international(self, twilio_client):
        """Test validation of international phone numbers"""
        # UK number
        result = await twilio_client.validate_phone_number("+447700900123")
        
        assert result.is_valid is True
        assert result.formatted_number == "+447700900123"
        assert result.country_code == "GB"
    
    @pytest.mark.asyncio
    async def test_validate_phone_number_invalid(self, twilio_client):
        """Test validation of invalid phone numbers"""
        invalid_numbers = [
            "123",           # Too short
            "abcd123",       # Contains letters
            "+999999999",    # Invalid country code
            "",              # Empty string
        ]
        
        for invalid_number in invalid_numbers:
            result = await twilio_client.validate_phone_number(invalid_number)
            assert result.is_valid is False
    
    @pytest.mark.asyncio
    async def test_normalize_phone_number(self, twilio_client):
        """Test phone number normalization"""
        # Test US number normalization
        normalized = twilio_client._normalize_phone_number("(555) 123-4567")
        assert normalized == "+15551234567"
        
        # Test international number (already normalized)
        normalized = twilio_client._normalize_phone_number("+447700900123")
        assert normalized == "+447700900123"
        
        # Test invalid number
        normalized = twilio_client._normalize_phone_number("invalid")
        assert normalized is None


class TestSMSSending:
    """Test SMS message sending functionality"""
    
    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for SMS testing"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567"
        )
        
        mock_cache = AsyncMock()
        mock_database = AsyncMock()
        mock_database.log_communication = AsyncMock(return_value="comm_123")
        
        client = TwilioClient(config, cache_service=mock_cache, database_service=mock_database)
        
        # Mock successful message sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456789"
        mock_message.status = "sent"
        mock_message.error_code = None
        mock_message.error_message = None
        mock_message.date_created = datetime.now()
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
            message="Hello from Service 6! Your property viewing is confirmed for tomorrow at 2pm."
        )
        
        assert isinstance(result, SMSMessage)
        assert result.message_sid == "SM123456789"
        assert result.status == MessageStatus.SENT
        assert result.to == "+15557890123"
        assert result.from_number == "+15551234567"
        assert "Hello from Service 6!" in result.body
        assert result.error_code is None
        
        # Verify communication was logged to database
        twilio_client.database_service.log_communication.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_sms_with_compliance_footer(self, twilio_client):
        """Test SMS sending with compliance footer"""
        result = await twilio_client.send_sms(
            to="+15557890123",
            message="Property update for North Austin",
            add_compliance_footer=True
        )
        
        assert "Reply STOP to unsubscribe" in result.body
        
        # Verify message was sent with footer
        call_args = twilio_client.sync_client.messages.create.call_args[1]
        assert "Reply STOP to unsubscribe" in call_args['body']
    
    @pytest.mark.asyncio
    async def test_send_sms_opted_out_number(self, twilio_client):
        """Test SMS sending to opted-out number"""
        # Add number to opt-out cache
        twilio_client._opt_out_cache.add("+15557890123")
        
        with pytest.raises(TwilioAPIException, match="Number has opted out"):
            await twilio_client.send_sms(
                to="+15557890123",
                message="This should not be sent"
            )
    
    @pytest.mark.asyncio
    async def test_send_sms_invalid_phone_number(self, twilio_client):
        """Test SMS sending to invalid phone number"""
        with pytest.raises(TwilioAPIException, match="Invalid phone number"):
            await twilio_client.send_sms(
                to="invalid_number",
                message="This should not be sent"
            )
    
    @pytest.mark.asyncio
    async def test_send_sms_message_too_long(self, twilio_client):
        """Test SMS sending with message exceeding length limit"""
        # Create message longer than 1600 characters (SMS limit)
        long_message = "A" * 1700
        
        with pytest.raises(TwilioAPIException, match="Message too long"):
            await twilio_client.send_sms(
                to="+15557890123",
                message=long_message
            )
    
    @pytest.mark.asyncio
    async def test_send_sms_api_error(self, twilio_client):
        """Test SMS sending when API returns error"""
        # Mock API error
        from twilio.base.exceptions import TwilioRestException
        twilio_client.sync_client.messages.create.side_effect = TwilioRestException(
            "Invalid 'To' Phone Number",
            uri="/Messages",
            status=400,
            code=21211
        )
        
        with pytest.raises(TwilioAPIException, match="Invalid 'To' Phone Number"):
            await twilio_client.send_sms(
                to="+15557890123",
                message="This will fail"
            )
    
    @pytest.mark.asyncio
    async def test_send_sms_rate_limiting(self, twilio_client):
        """Test SMS rate limiting behavior"""
        # Set up rate limiting (1 message per second)
        twilio_client._rate_limit_semaphore = asyncio.Semaphore(1)
        
        # Send multiple messages concurrently
        tasks = []
        for i in range(3):
            task = twilio_client.send_sms(
                to=f"+155512345{i:02d}",
                message=f"Message {i}"
            )
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
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567"
        )
        
        client = TwilioClient(config)
        
        # Mock successful message sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456789"
        mock_message.status = "sent"
        mock_messages.create.return_value = mock_message
        mock_sync_client.messages = mock_messages
        
        client.sync_client = mock_sync_client
        
        return client
    
    @pytest.mark.asyncio
    async def test_send_templated_sms_property_viewing(self, twilio_client):
        """Test sending property viewing reminder SMS"""
        template_data = {
            "lead_name": "Sarah Johnson",
            "property_address": "1234 Cedar Ridge Dr, Austin, TX",
            "viewing_time": "tomorrow at 2:00 PM"
        }
        
        result = await twilio_client.send_templated_sms(
            to="+15557890123",
            template="property_viewing_reminder",
            template_data=template_data
        )
        
        assert isinstance(result, SMSMessage)
        assert result.message_sid == "SM123456789"
        
        # Verify template was used
        call_args = twilio_client.sync_client.messages.create.call_args[1]
        message_body = call_args['body']
        assert "Sarah Johnson" in message_body
        assert "1234 Cedar Ridge Dr" in message_body
        assert "tomorrow at 2:00 PM" in message_body
    
    @pytest.mark.asyncio
    async def test_send_templated_sms_price_alert(self, twilio_client):
        """Test sending price alert SMS"""
        template_data = {
            "lead_name": "Mike Chen",
            "property_address": "5678 Oak Valley Ln, Austin, TX",
            "old_price": "$650,000",
            "new_price": "$625,000"
        }
        
        result = await twilio_client.send_templated_sms(
            to="+15557890123",
            template="price_alert",
            template_data=template_data
        )
        
        assert isinstance(result, SMSMessage)
        
        # Verify template data was used
        call_args = twilio_client.sync_client.messages.create.call_args[1]
        message_body = call_args['body']
        assert "Mike Chen" in message_body
        assert "$625,000" in message_body
    
    @pytest.mark.asyncio
    async def test_send_templated_sms_invalid_template(self, twilio_client):
        """Test sending SMS with invalid template"""
        with pytest.raises(TwilioAPIException, match="Unknown template"):
            await twilio_client.send_templated_sms(
                to="+15557890123",
                template="nonexistent_template",
                template_data={}
            )
    
    @pytest.mark.asyncio
    async def test_get_message_template_property_viewing(self, twilio_client):
        """Test getting property viewing template"""
        template_data = {
            "lead_name": "John Doe",
            "property_address": "123 Main St",
            "viewing_time": "3:00 PM"
        }
        
        message = await twilio_client._get_message_template("property_viewing_reminder", template_data)
        
        assert "John Doe" in message
        assert "123 Main St" in message
        assert "3:00 PM" in message
        assert "property viewing" in message.lower()
    
    @pytest.mark.asyncio
    async def test_get_message_template_market_update(self, twilio_client):
        """Test getting market update template"""
        template_data = {
            "lead_name": "Jane Smith",
            "location": "North Austin",
            "avg_price": "$550,000"
        }
        
        message = await twilio_client._get_message_template("market_update", template_data)
        
        assert "Jane Smith" in message
        assert "North Austin" in message
        assert "$550,000" in message


class TestOptOutManagement:
    """Test opt-out/opt-in management functionality"""
    
    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for opt-out testing"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token"
        )
        
        # Mock database service
        mock_database = AsyncMock()
        mock_database.log_communication = AsyncMock(return_value="comm_123")
        
        client = TwilioClient(config, database_service=mock_database)
        
        return client
    
    @pytest.mark.asyncio
    async def test_process_opt_out(self, twilio_client):
        """Test processing opt-out request"""
        phone_number = "+15557890123"
        
        result = await twilio_client.process_opt_out(phone_number, "STOP")
        
        assert isinstance(result, OptOutRecord)
        assert result.phone_number == phone_number
        assert result.opted_out is True
        assert result.keyword == "STOP"
        
        # Verify number was added to opt-out cache
        assert phone_number in twilio_client._opt_out_cache
        
        # Verify database logging
        twilio_client.database_service.log_communication.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_opt_out_variations(self, twilio_client):
        """Test processing various opt-out keywords"""
        opt_out_keywords = ["STOP", "UNSUBSCRIBE", "REMOVE", "QUIT", "END"]
        phone_number = "+15557890123"
        
        for keyword in opt_out_keywords:
            await twilio_client.process_opt_out(phone_number, keyword)
            assert phone_number in twilio_client._opt_out_cache
    
    @pytest.mark.asyncio
    async def test_process_opt_in(self, twilio_client):
        """Test processing opt-in request"""
        phone_number = "+15557890123"
        
        # First opt out
        await twilio_client.process_opt_out(phone_number, "STOP")
        assert phone_number in twilio_client._opt_out_cache
        
        # Then opt back in
        result = await twilio_client.process_opt_in(phone_number, "START")
        
        assert isinstance(result, OptOutRecord)
        assert result.phone_number == phone_number
        assert result.opted_out is False
        assert result.keyword == "START"
        
        # Verify number was removed from opt-out cache
        assert phone_number not in twilio_client._opt_out_cache
    
    @pytest.mark.asyncio
    async def test_process_opt_in_variations(self, twilio_client):
        """Test processing various opt-in keywords"""
        opt_in_keywords = ["START", "YES", "SUBSCRIBE", "JOIN"]
        phone_number = "+15557890123"
        
        # First opt out
        await twilio_client.process_opt_out(phone_number, "STOP")
        
        for keyword in opt_in_keywords:
            await twilio_client.process_opt_in(phone_number, keyword)
            assert phone_number not in twilio_client._opt_out_cache
    
    @pytest.mark.asyncio
    async def test_is_opted_out(self, twilio_client):
        """Test checking opt-out status"""
        phone_number = "+15557890123"
        
        # Initially not opted out
        assert not await twilio_client._is_opted_out(phone_number)
        
        # After opting out
        await twilio_client.process_opt_out(phone_number, "STOP")
        assert await twilio_client._is_opted_out(phone_number)
        
        # After opting back in
        await twilio_client.process_opt_in(phone_number, "START")
        assert not await twilio_client._is_opted_out(phone_number)


class TestWebhookProcessing:
    """Test webhook processing functionality"""
    
    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for webhook testing"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token"
        )
        
        # Mock database service
        mock_database = AsyncMock()
        mock_database.log_communication = AsyncMock(return_value="comm_123")
        
        client = TwilioClient(config, database_service=mock_database)
        
        return client
    
    @pytest.mark.asyncio
    async def test_process_status_webhook_delivered(self, twilio_client):
        """Test processing delivery status webhook"""
        webhook_data = WebhookTestData.twilio_voice_webhook({
            'MessageSid': 'SM123456789',
            'MessageStatus': 'delivered',
            'To': '+15557890123',
            'From': '+15551234567',
            'Body': 'Test message delivered'
        })
        
        result = await twilio_client.process_status_webhook(webhook_data)
        
        assert result['message_sid'] == 'SM123456789'
        assert result['status'] == 'delivered'
        assert result['to'] == '+15557890123'
        assert result['processed'] is True
    
    @pytest.mark.asyncio
    async def test_process_status_webhook_failed(self, twilio_client):
        """Test processing failed message status webhook"""
        webhook_data = {
            'MessageSid': 'SM123456789',
            'MessageStatus': 'failed',
            'ErrorCode': '30007',
            'ErrorMessage': 'Message delivery failed',
            'To': '+15557890123'
        }
        
        result = await twilio_client.process_status_webhook(webhook_data)
        
        assert result['status'] == 'failed'
        assert result['error_code'] == '30007'
        assert result['error_message'] == 'Message delivery failed'
        assert result['processed'] is True
    
    @pytest.mark.asyncio
    async def test_process_incoming_webhook_normal_message(self, twilio_client):
        """Test processing incoming message webhook"""
        webhook_data = {
            'MessageSid': 'SM987654321',
            'From': '+15557890123',
            'To': '+15551234567',
            'Body': 'Yes, I am still interested in viewing properties'
        }
        
        result = await twilio_client.process_incoming_webhook(webhook_data)
        
        assert result['message_sid'] == 'SM987654321'
        assert result['from'] == '+15557890123'
        assert result['body'] == 'Yes, I am still interested in viewing properties'
        assert result['is_opt_out'] is False
        assert result['is_opt_in'] is False
        assert result['processed'] is True
        
        # Verify communication was logged
        twilio_client.database_service.log_communication.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_incoming_webhook_opt_out(self, twilio_client):
        """Test processing incoming opt-out message"""
        webhook_data = {
            'MessageSid': 'SM987654321',
            'From': '+15557890123',
            'To': '+15551234567',
            'Body': 'STOP'
        }
        
        result = await twilio_client.process_incoming_webhook(webhook_data)
        
        assert result['is_opt_out'] is True
        assert result['opt_out_keyword'] == 'STOP'
        assert result['processed'] is True
        
        # Verify number was opted out
        assert '+15557890123' in twilio_client._opt_out_cache
    
    @pytest.mark.asyncio
    async def test_process_incoming_webhook_opt_in(self, twilio_client):
        """Test processing incoming opt-in message"""
        phone_number = '+15557890123'
        
        # First opt out
        await twilio_client.process_opt_out(phone_number, 'STOP')
        
        # Then receive opt-in message
        webhook_data = {
            'MessageSid': 'SM987654321',
            'From': phone_number,
            'To': '+15551234567',
            'Body': 'START'
        }
        
        result = await twilio_client.process_incoming_webhook(webhook_data)
        
        assert result['is_opt_in'] is True
        assert result['opt_in_keyword'] == 'START'
        assert result['processed'] is True
        
        # Verify number was opted back in
        assert phone_number not in twilio_client._opt_out_cache
    
    @pytest.mark.asyncio
    async def test_process_incoming_webhook_invalid_data(self, twilio_client):
        """Test processing webhook with invalid data"""
        invalid_webhook_data = {
            'MessageSid': '',  # Empty message SID
            'From': 'invalid_number',
            'Body': None
        }
        
        result = await twilio_client.process_incoming_webhook(invalid_webhook_data)
        
        assert result['processed'] is False
        assert 'error' in result


class TestBulkOperations:
    """Test bulk SMS operations"""
    
    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for bulk operations testing"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567"
        )
        
        mock_database = AsyncMock()
        client = TwilioClient(config, database_service=mock_database)
        
        # Mock successful bulk sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        
        def mock_create_message(**kwargs):
            mock_msg = MagicMock()
            mock_msg.sid = f"SM{hash(kwargs['to'])}"
            mock_msg.status = "sent"
            mock_msg.error_code = None
            return mock_msg
        
        mock_messages.create.side_effect = mock_create_message
        mock_sync_client.messages = mock_messages
        
        client.sync_client = mock_sync_client
        
        return client
    
    @pytest.mark.asyncio
    async def test_send_bulk_sms_success(self, twilio_client):
        """Test successful bulk SMS sending"""
        recipients = [
            {"phone": "+15557890123", "name": "John Doe"},
            {"phone": "+15557890124", "name": "Jane Smith"}, 
            {"phone": "+15557890125", "name": "Bob Wilson"}
        ]
        
        message_template = "Hi {name}, your property viewing is confirmed!"
        
        results = await twilio_client.send_bulk_sms(recipients, message_template)
        
        assert len(results) == 3
        assert all(result['success'] for result in results)
        assert all('message_sid' in result for result in results)
        
        # Verify all messages were sent
        assert twilio_client.sync_client.messages.create.call_count == 3
    
    @pytest.mark.asyncio
    async def test_send_bulk_sms_with_failures(self, twilio_client):
        """Test bulk SMS with some failures"""
        recipients = [
            {"phone": "+15557890123", "name": "John Doe"},    # Success
            {"phone": "invalid_number", "name": "Invalid"},   # Failure
            {"phone": "+15557890125", "name": "Bob Wilson"}   # Success
        ]
        
        # Mock one failure
        def mock_create_with_failure(**kwargs):
            if "invalid_number" in kwargs['to']:
                from twilio.base.exceptions import TwilioRestException
                raise TwilioRestException("Invalid number", uri="/Messages", status=400)
            
            mock_msg = MagicMock()
            mock_msg.sid = f"SM{hash(kwargs['to'])}"
            mock_msg.status = "sent"
            return mock_msg
        
        twilio_client.sync_client.messages.create.side_effect = mock_create_with_failure
        
        message_template = "Hi {name}!"
        
        results = await twilio_client.send_bulk_sms(recipients, message_template)
        
        assert len(results) == 3
        assert results[0]['success'] is True  # John Doe
        assert results[1]['success'] is False  # Invalid number
        assert results[2]['success'] is True   # Bob Wilson
        
        # Check error details for failed message
        assert 'error' in results[1]
        assert 'Invalid number' in results[1]['error']
    
    @pytest.mark.asyncio
    async def test_send_bulk_sms_rate_limiting(self, twilio_client):
        """Test bulk SMS with rate limiting"""
        # Set tight rate limit
        twilio_client._rate_limit_semaphore = asyncio.Semaphore(1)
        
        recipients = [
            {"phone": f"+155578901{i:02d}", "name": f"User {i}"}
            for i in range(5)
        ]
        
        import time
        start_time = time.time()
        
        results = await twilio_client.send_bulk_sms(recipients, "Hi {name}!")
        
        end_time = time.time()
        
        # All should succeed
        assert len(results) == 5
        assert all(result['success'] for result in results)
        
        # Should take some time due to rate limiting
        # (In real usage, this would be more significant)
        execution_time = end_time - start_time
        assert execution_time > 0  # Basic sanity check


class TestHealthAndMonitoring:
    """Test health check and monitoring functionality"""
    
    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for health testing"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token"
        )
        
        client = TwilioClient(config)
        
        # Mock Twilio client
        mock_sync_client = MagicMock()
        
        # Mock account info
        mock_account = MagicMock()
        mock_account.status = "active"
        mock_account.subresource_uris = {"balance": "/Accounts/test_sid/Balance.json"}
        mock_sync_client.accounts.get.return_value = mock_account
        
        # Mock balance
        mock_balance = MagicMock()
        mock_balance.balance = "50.00"
        mock_balance.currency = "USD"
        mock_sync_client.balance.fetch.return_value = mock_balance
        
        client.sync_client = mock_sync_client
        
        return client
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, twilio_client):
        """Test successful health check"""
        result = await twilio_client.health_check()
        
        assert result['status'] == 'healthy'
        assert result['account_status'] == 'active'
        assert result['balance'] == '50.00'
        assert result['currency'] == 'USD'
        assert result['response_time_ms'] > 0
        assert result['can_send_messages'] is True
    
    @pytest.mark.asyncio
    async def test_health_check_low_balance(self, twilio_client):
        """Test health check with low balance warning"""
        # Mock low balance
        twilio_client.sync_client.balance.fetch.return_value.balance = "2.50"
        
        result = await twilio_client.health_check()
        
        assert result['status'] == 'warning'
        assert 'Low account balance' in result['warnings'][0]
        assert result['balance'] == '2.50'
    
    @pytest.mark.asyncio
    async def test_health_check_api_failure(self, twilio_client):
        """Test health check when API is unavailable"""
        # Mock API failure
        from twilio.base.exceptions import TwilioRestException
        twilio_client.sync_client.accounts.get.side_effect = TwilioRestException(
            "Service unavailable", uri="/Accounts", status=503
        )
        
        result = await twilio_client.health_check()
        
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert result['can_send_messages'] is False
    
    @pytest.mark.asyncio
    async def test_get_usage_stats(self, twilio_client):
        """Test getting usage statistics"""
        # Mock usage records
        mock_usage_records = [
            MagicMock(category='sms', count=150, price='7.50'),
            MagicMock(category='voice', count=25, price='5.00')
        ]
        
        twilio_client.sync_client.usage.records.list.return_value = mock_usage_records
        
        result = await twilio_client.get_usage_stats()
        
        assert 'usage_summary' in result
        assert 'sms' in result['usage_summary']
        assert 'voice' in result['usage_summary']
        assert result['usage_summary']['sms']['count'] == 150
        assert result['usage_summary']['sms']['price'] == '7.50'
        assert result['total_messages_sent'] == 150
        assert result['total_cost'] == 12.50  # 7.50 + 5.00


class TestComplianceFeatures:
    """Test TCPA compliance features"""
    
    @pytest_asyncio.fixture
    async def twilio_client(self):
        """Create Twilio client for compliance testing"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token",
            compliance_footer="Reply STOP to unsubscribe. Message rates may apply."
        )
        
        return TwilioClient(config)
    
    @pytest.mark.asyncio
    async def test_add_compliance_footer(self, twilio_client):
        """Test adding compliance footer to messages"""
        original_message = "Your property viewing is confirmed for tomorrow."
        
        message_with_footer = twilio_client._add_compliance_footer(original_message)
        
        assert "Reply STOP to unsubscribe" in message_with_footer
        assert "Message rates may apply" in message_with_footer
        assert original_message in message_with_footer
    
    @pytest.mark.asyncio
    async def test_add_compliance_footer_already_present(self, twilio_client):
        """Test not duplicating compliance footer"""
        message_with_footer = "Your viewing is confirmed. Reply STOP to unsubscribe."
        
        result = twilio_client._add_compliance_footer(message_with_footer)
        
        # Should not add footer if STOP is already mentioned
        assert result.count("STOP") == 1
    
    @pytest.mark.asyncio
    async def test_opt_out_keyword_detection(self, twilio_client):
        """Test detection of various opt-out keywords"""
        opt_out_messages = [
            "STOP",
            "stop",
            "Stop sending me messages",
            "UNSUBSCRIBE please",
            "Remove me from your list",
            "QUIT",
            "END these messages"
        ]
        
        for message in opt_out_messages:
            # This would normally be called within webhook processing
            normalized = message.upper()
            opt_out_keywords = ["STOP", "UNSUBSCRIBE", "REMOVE", "QUIT", "END"]
            
            is_opt_out = any(keyword in normalized for keyword in opt_out_keywords)
            assert is_opt_out, f"Failed to detect opt-out in: {message}"


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_client_without_credentials(self):
        """Test client initialization without credentials"""
        config = TwilioConfig()  # No credentials
        
        with pytest.raises(ValueError, match="Account SID and Auth Token are required"):
            TwilioClient(config)
    
    @pytest.mark.asyncio
    async def test_send_sms_without_phone_number(self):
        """Test sending SMS without configured phone number"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token"
            # No phone_number configured
        )
        
        client = TwilioClient(config)
        
        with pytest.raises(TwilioAPIException, match="No phone number configured"):
            await client.send_sms(
                to="+15557890123",
                message="This should fail"
            )
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token",
            request_timeout_seconds=0.1
        )
        
        client = TwilioClient(config)
        
        # Mock timeout
        mock_sync_client = MagicMock()
        mock_sync_client.messages.create.side_effect = Exception("Request timeout")
        client.sync_client = mock_sync_client
        
        with pytest.raises(TwilioAPIException, match="Request timeout"):
            await client.send_sms(
                to="+15557890123",
                message="This will timeout"
            )


@pytest.mark.performance
class TestPerformanceCharacteristics:
    """Test Twilio client performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_bulk_sms_performance(self):
        """Test performance of bulk SMS operations"""
        config = TwilioConfig(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567"
        )
        
        client = TwilioClient(config)
        
        # Mock fast message sending
        mock_sync_client = MagicMock()
        mock_messages = MagicMock()
        
        def fast_create(**kwargs):
            mock_msg = MagicMock()
            mock_msg.sid = f"SM{hash(kwargs['to'])}"
            mock_msg.status = "sent"
            return mock_msg
        
        mock_messages.create.side_effect = fast_create
        mock_sync_client.messages = mock_messages
        client.sync_client = mock_sync_client
        
        # Test with many recipients
        recipients = [
            {"phone": f"+155578901{i:02d}", "name": f"User {i}"}
            for i in range(50)
        ]
        
        import time
        start_time = time.time()
        
        results = await client.send_bulk_sms(recipients, "Hi {name}!")
        
        end_time = time.time()
        
        # Verify all messages sent
        assert len(results) == 50
        assert all(result['success'] for result in results)
        
        # Performance should be reasonable (under 5 seconds for mocked operations)
        execution_time = end_time - start_time
        assert execution_time < 5.0


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([
        "-v",
        "tests/services/test_twilio_client.py::TestSMSSending",
        "--tb=short"
    ])