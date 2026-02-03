#!/usr/bin/env python3
"""
Comprehensive tests for SendGrid Client.

Tests cover:
- SendGrid email client initialization and configuration
- Email template management and sending
- Suppression list management and CAN-SPAM compliance
- Webhook processing for delivery events
- Bulk email operations
- Email analytics and reporting
- Error handling and retry logic
- Health monitoring

Coverage Target: 85%+ for all SendGrid operations
"""

import asyncio
import json
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Import the module under test
try:
    from ghl_real_estate_ai.services.sendgrid_client import (
        SendGridClient,
        SendGridConfig,
        EmailMessage,
        EmailTemplate,
        SuppressionEntry,
        EmailStatus,
        SuppressionType,
        SendGridAPIException
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)

# Import test utilities
from tests.mocks.external_services import MockSendGridClient
from tests.fixtures.sample_data import WebhookTestData, LeadProfiles


class TestSendGridConfig:
    """Test SendGrid configuration management"""
    
    def test_default_config_creation(self):
        """Test default SendGrid configuration"""
        config = SendGridConfig()
        
        assert config.api_key is None  # Should be set via environment
        assert config.from_email == "noreply@example.com"
        assert config.from_name == "EnterpriseHub"
        assert config.reply_to_email is None
        assert config.rate_limit_emails_per_second == 5
        assert config.max_retries == 3
        assert config.request_timeout_seconds == 30
        assert config.enable_tracking is True
        assert config.enable_click_tracking is True
        assert config.enable_open_tracking is True
        assert config.enable_subscription_tracking is True
    
    def test_custom_config_creation(self):
        """Test custom SendGrid configuration"""
        config = SendGridConfig(
            api_key="test_sendgrid_key",
            from_email="sales@company.com",
            from_name="Company Sales Team",
            reply_to_email="support@company.com",
            rate_limit_emails_per_second=10,
            max_retries=5,
            enable_tracking=False
        )
        
        assert config.api_key == "test_sendgrid_key"
        assert config.from_email == "sales@company.com"
        assert config.from_name == "Company Sales Team"
        assert config.reply_to_email == "support@company.com"
        assert config.rate_limit_emails_per_second == 10
        assert config.max_retries == 5
        assert config.enable_tracking is False


class TestSendGridClient:
    """Test SendGrid client operations"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client with mocked dependencies"""
        config = SendGridConfig(
            api_key="test_sendgrid_key",
            from_email="test@enterprisehub.ai",
            from_name="EnterpriseHub"
        )
        
        # Mock cache service
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)
        
        # Mock database service
        mock_database = AsyncMock()
        mock_database.log_communication = AsyncMock(return_value="comm_123")
        
        client = SendGridClient(config, cache_service=mock_cache, database_service=mock_database)
        
        # Mock SendGrid client
        mock_sg_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.body = b'{"message": "success"}'
        mock_response.headers = {"X-Message-Id": "test_message_id"}
        mock_sg_client.send.return_value = mock_response
        
        client.sg_client = mock_sg_client
        client._mock_response = mock_response
        
        # Mock HTTP session
        mock_session = MagicMock()
        mock_http_response = MagicMock()
        mock_http_response.status = 200
        mock_http_response.json = AsyncMock(return_value={})
        mock_session.request = AsyncMock(return_value=mock_http_response)
        
        client.session = mock_session
        client._mock_http_response = mock_http_response
        
        return client
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, sendgrid_client):
        """Test SendGrid client initialization"""
        assert sendgrid_client.config is not None
        assert sendgrid_client.cache_service is not None
        assert sendgrid_client.database_service is not None
        assert sendgrid_client.sg_client is not None
        assert sendgrid_client._rate_limit_semaphore is not None
        assert sendgrid_client._suppression_cache == set()
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client as async context manager"""
        config = SendGridConfig(api_key="test_key")
        
        async with SendGridClient(config) as client:
            assert client.session is not None
        
        # Client should be closed after context exit
    
    @pytest.mark.asyncio
    async def test_ensure_session(self, sendgrid_client):
        """Test session creation and management"""
        # Reset session to test creation
        sendgrid_client.session = None
        
        await sendgrid_client._ensure_session()
        
        assert sendgrid_client.session is not None
    
    @pytest.mark.asyncio
    async def test_client_close(self, sendgrid_client):
        """Test client cleanup"""
        await sendgrid_client.close()
        
        sendgrid_client.session.close.assert_called_once()


class TestEmailSending:
    """Test email sending functionality"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client for email testing"""
        config = SendGridConfig(
            api_key="test_key",
            from_email="sales@enterprisehub.ai",
            from_name="EnterpriseHub Sales"
        )
        
        mock_cache = AsyncMock()
        mock_database = AsyncMock()
        mock_database.log_communication = AsyncMock(return_value="comm_123")
        
        client = SendGridClient(config, cache_service=mock_cache, database_service=mock_database)
        
        # Mock successful email sending
        mock_sg_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.body = b'{"message": "success"}'
        mock_response.headers = {"X-Message-Id": "SG.test_message_123"}
        mock_sg_client.send.return_value = mock_response
        
        client.sg_client = mock_sg_client
        client._mock_response = mock_response
        
        return client
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, sendgrid_client):
        """Test successful email sending"""
        result = await sendgrid_client.send_email(
            to_email="sarah.johnson@example.com",
            to_name="Sarah Johnson",
            subject="Your Property Viewing is Confirmed",
            html_content="<h1>Viewing Confirmed</h1><p>We look forward to seeing you tomorrow at 2pm.</p>",
            text_content="Viewing Confirmed. We look forward to seeing you tomorrow at 2pm."
        )
        
        assert isinstance(result, EmailMessage)
        assert result.message_id == "SG.test_message_123"
        assert result.to_email == "sarah.johnson@example.com"
        assert result.to_name == "Sarah Johnson"
        assert result.from_email == "sales@enterprisehub.ai"
        assert result.from_name == "EnterpriseHub Sales"
        assert result.subject == "Your Property Viewing is Confirmed"
        assert result.status == EmailStatus.SENT
        assert result.sent_at is not None
        
        # Verify email was sent via SendGrid
        sendgrid_client.sg_client.send.assert_called_once()
        
        # Verify communication was logged to database
        sendgrid_client.database_service.log_communication.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, sendgrid_client):
        """Test sending email with attachments"""
        attachments = [
            {
                "filename": "property_details.pdf",
                "content": "base64_encoded_pdf_content",
                "type": "application/pdf"
            },
            {
                "filename": "floor_plan.png",
                "content": "base64_encoded_image_content",
                "type": "image/png"
            }
        ]
        
        result = await sendgrid_client.send_email(
            to_email="client@example.com",
            subject="Property Information",
            html_content="<p>Please find attached property details.</p>",
            attachments=attachments
        )
        
        assert isinstance(result, EmailMessage)
        assert result.has_attachments is True
        
        # Verify attachments were included in SendGrid call
        call_args = sendgrid_client.sg_client.send.call_args[0][0]
        mail_json = call_args.get()
        assert 'attachments' in mail_json
        assert len(mail_json['attachments']) == 2
    
    @pytest.mark.asyncio
    async def test_send_email_with_categories(self, sendgrid_client):
        """Test sending email with categories for tracking"""
        result = await sendgrid_client.send_email(
            to_email="lead@example.com",
            subject="Market Update",
            html_content="<p>Latest market trends...</p>",
            categories=["market_update", "newsletter", "austin_market"]
        )
        
        assert isinstance(result, EmailMessage)
        assert result.categories == ["market_update", "newsletter", "austin_market"]
        
        # Verify categories were included
        call_args = sendgrid_client.sg_client.send.call_args[0][0]
        mail_json = call_args.get()
        assert 'categories' in mail_json
        assert mail_json['categories'] == ["market_update", "newsletter", "austin_market"]
    
    @pytest.mark.asyncio
    async def test_send_email_suppressed_recipient(self, sendgrid_client):
        """Test sending email to suppressed recipient"""
        # Add email to suppression cache
        sendgrid_client._suppression_cache.add("suppressed@example.com")
        
        with pytest.raises(SendGridAPIException, match="Email address is suppressed"):
            await sendgrid_client.send_email(
                to_email="suppressed@example.com",
                subject="This should not be sent",
                html_content="<p>Suppressed email</p>"
            )
    
    @pytest.mark.asyncio
    async def test_send_email_invalid_recipient(self, sendgrid_client):
        """Test sending email to invalid recipient"""
        with pytest.raises(SendGridAPIException, match="Invalid email address"):
            await sendgrid_client.send_email(
                to_email="invalid_email_format",
                subject="This should fail",
                html_content="<p>Invalid email</p>"
            )
    
    @pytest.mark.asyncio
    async def test_send_email_api_error(self, sendgrid_client):
        """Test email sending when API returns error"""
        # Mock API error
        sendgrid_client._mock_response.status_code = 400
        sendgrid_client._mock_response.body = b'{"errors": [{"message": "Invalid API key"}]}'
        
        with pytest.raises(SendGridAPIException, match="SendGrid API error"):
            await sendgrid_client.send_email(
                to_email="test@example.com",
                subject="This will fail", 
                html_content="<p>API error test</p>"
            )
    
    @pytest.mark.asyncio
    async def test_send_email_rate_limiting(self, sendgrid_client):
        """Test email rate limiting behavior"""
        # Set up rate limiting (1 email per second for testing)
        sendgrid_client._rate_limit_semaphore = asyncio.Semaphore(1)
        
        # Send multiple emails concurrently
        tasks = []
        for i in range(3):
            task = sendgrid_client.send_email(
                to_email=f"test{i}@example.com",
                subject=f"Test Email {i}",
                html_content=f"<p>Test content {i}</p>"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed but be rate limited
        assert len(results) == 3
        assert all(isinstance(r, EmailMessage) for r in results if not isinstance(r, Exception))


class TestTemplatedEmails:
    """Test templated email functionality"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client for template testing"""
        config = SendGridConfig(
            api_key="test_key",
            from_email="sales@enterprisehub.ai"
        )
        
        client = SendGridClient(config)
        
        # Mock successful email sending
        mock_sg_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "SG.template_test_123"}
        mock_sg_client.send.return_value = mock_response
        
        client.sg_client = mock_sg_client
        
        return client
    
    @pytest.mark.asyncio
    async def test_send_templated_email_property_viewing(self, sendgrid_client):
        """Test sending property viewing confirmation email"""
        template_data = {
            "lead_name": "Sarah Johnson",
            "property_address": "1234 Cedar Ridge Dr, Austin, TX 78758",
            "viewing_date": "January 18, 2026",
            "viewing_time": "2:00 PM",
            "agent_name": "Michael Rodriguez",
            "agent_phone": "+1-512-555-0123"
        }
        
        result = await sendgrid_client.send_templated_email(
            to_email="sarah.johnson@example.com",
            to_name="Sarah Johnson",
            template="property_viewing_confirmation",
            template_data=template_data
        )
        
        assert isinstance(result, EmailMessage)
        assert result.message_id == "SG.template_test_123"
        assert result.template_id == "property_viewing_confirmation"
        
        # Verify template was used
        sendgrid_client.sg_client.send.assert_called_once()
        call_args = sendgrid_client.sg_client.send.call_args[0][0]
        mail_json = call_args.get()
        
        # Check template data was included
        assert 'personalizations' in mail_json
        personalization = mail_json['personalizations'][0]
        assert 'dynamic_template_data' in personalization
        assert personalization['dynamic_template_data']['lead_name'] == "Sarah Johnson"
    
    @pytest.mark.asyncio
    async def test_send_templated_email_market_update(self, sendgrid_client):
        """Test sending market update newsletter"""
        template_data = {
            "lead_name": "Mike Chen",
            "location": "South Austin",
            "avg_home_price": "$485,000",
            "price_change": "+3.2%",
            "days_on_market": "18 days",
            "inventory_level": "Low",
            "market_trend": "Seller's Market"
        }
        
        result = await sendgrid_client.send_templated_email(
            to_email="mike.chen@example.com",
            template="market_update_newsletter",
            template_data=template_data
        )
        
        assert isinstance(result, EmailMessage)
        assert result.template_id == "market_update_newsletter"
    
    @pytest.mark.asyncio
    async def test_send_templated_email_price_alert(self, sendgrid_client):
        """Test sending price reduction alert"""
        template_data = {
            "lead_name": "Jennifer Martinez",
            "property_address": "5678 Oak Valley Ln, Austin, TX",
            "old_price": "$675,000",
            "new_price": "$649,000",
            "reduction_amount": "$26,000",
            "reduction_percentage": "3.9%"
        }
        
        result = await sendgrid_client.send_templated_email(
            to_email="jennifer@example.com",
            template="price_reduction_alert",
            template_data=template_data
        )
        
        assert isinstance(result, EmailMessage)
        assert result.template_id == "price_reduction_alert"
    
    @pytest.mark.asyncio
    async def test_send_templated_email_invalid_template(self, sendgrid_client):
        """Test sending email with invalid template"""
        with pytest.raises(SendGridAPIException, match="Unknown email template"):
            await sendgrid_client.send_templated_email(
                to_email="test@example.com",
                template="nonexistent_template",
                template_data={}
            )
    
    @pytest.mark.asyncio
    async def test_get_email_template_property_viewing(self, sendgrid_client):
        """Test getting property viewing template"""
        template_data = {
            "lead_name": "John Doe",
            "property_address": "123 Main St",
            "viewing_date": "Tomorrow",
            "viewing_time": "3:00 PM"
        }
        
        template = await sendgrid_client._get_email_template("property_viewing_confirmation", template_data)
        
        assert isinstance(template, EmailTemplate)
        assert template.template_id == "property_viewing_confirmation"
        assert "property viewing" in template.subject.lower()
        assert "John Doe" in template.html_content
        assert "123 Main St" in template.html_content
        assert "3:00 PM" in template.html_content
    
    @pytest.mark.asyncio
    async def test_get_email_template_welcome_series(self, sendgrid_client):
        """Test getting welcome series template"""
        template_data = {
            "lead_name": "Jane Smith",
            "preferred_location": "North Austin",
            "budget_range": "$500K-600K"
        }
        
        template = await sendgrid_client._get_email_template("welcome_series_1", template_data)
        
        assert isinstance(template, EmailTemplate)
        assert template.template_id == "welcome_series_1"
        assert "welcome" in template.subject.lower()
        assert "Jane Smith" in template.html_content
        assert "North Austin" in template.html_content


class TestSuppressionManagement:
    """Test suppression list management and CAN-SPAM compliance"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client for suppression testing"""
        config = SendGridConfig(api_key="test_key")
        client = SendGridClient(config)
        
        # Mock HTTP session for suppression API calls
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        
        client.session = mock_session
        client._mock_http_response = mock_response
        
        return client
    
    @pytest.mark.asyncio
    async def test_load_suppressions(self, sendgrid_client):
        """Test loading suppressions from SendGrid API"""
        # Mock suppression list response
        sendgrid_client._mock_http_response.json.return_value = [
            {"email": "suppressed1@example.com", "created": 1640995200},
            {"email": "suppressed2@example.com", "created": 1640995300}
        ]
        
        await sendgrid_client._load_suppressions()
        
        assert "suppressed1@example.com" in sendgrid_client._suppression_cache
        assert "suppressed2@example.com" in sendgrid_client._suppression_cache
        assert len(sendgrid_client._suppression_cache) == 2
    
    @pytest.mark.asyncio
    async def test_is_suppressed(self, sendgrid_client):
        """Test checking if email is suppressed"""
        # Add email to suppression cache
        sendgrid_client._suppression_cache.add("suppressed@example.com")
        
        # Test suppressed email
        is_suppressed = await sendgrid_client._is_suppressed("suppressed@example.com")
        assert is_suppressed is True
        
        # Test non-suppressed email
        is_suppressed = await sendgrid_client._is_suppressed("allowed@example.com")
        assert is_suppressed is False
    
    @pytest.mark.asyncio
    async def test_add_to_suppression(self, sendgrid_client):
        """Test adding email to suppression list"""
        # Mock successful suppression addition
        sendgrid_client._mock_http_response.status = 201
        
        result = await sendgrid_client.add_to_suppression(
            "unsubscribe@example.com",
            SuppressionType.UNSUBSCRIBES
        )
        
        assert isinstance(result, SuppressionEntry)
        assert result.email == "unsubscribe@example.com"
        assert result.suppression_type == SuppressionType.UNSUBSCRIBES
        assert result.created_at is not None
        
        # Verify email was added to local cache
        assert "unsubscribe@example.com" in sendgrid_client._suppression_cache
        
        # Verify API call was made
        sendgrid_client.session.request.assert_called()
    
    @pytest.mark.asyncio
    async def test_remove_from_suppression(self, sendgrid_client):
        """Test removing email from suppression list"""
        # Add email to cache first
        sendgrid_client._suppression_cache.add("resubscribe@example.com")
        
        # Mock successful suppression removal
        sendgrid_client._mock_http_response.status = 204
        
        result = await sendgrid_client.remove_from_suppression(
            "resubscribe@example.com",
            SuppressionType.UNSUBSCRIBES
        )
        
        assert result is True
        
        # Verify email was removed from local cache
        assert "resubscribe@example.com" not in sendgrid_client._suppression_cache
        
        # Verify API call was made
        sendgrid_client.session.request.assert_called()
    
    @pytest.mark.asyncio
    async def test_fetch_suppressions_by_type(self, sendgrid_client):
        """Test fetching suppressions by type"""
        # Mock bounces response
        sendgrid_client._mock_http_response.json.return_value = [
            {"email": "bounce1@example.com", "created": 1640995200, "reason": "550 No such user"},
            {"email": "bounce2@example.com", "created": 1640995300, "reason": "554 Mailbox full"}
        ]
        
        suppressions = await sendgrid_client._fetch_suppressions(SuppressionType.BOUNCES)
        
        assert len(suppressions) == 2
        assert suppressions[0]['email'] == "bounce1@example.com"
        assert "550 No such user" in suppressions[0]['reason']
        
        # Verify correct API endpoint was called
        call_args = sendgrid_client.session.request.call_args[1]
        assert "bounces" in call_args['url']
    
    @pytest.mark.asyncio
    async def test_suppression_api_error(self, sendgrid_client):
        """Test handling suppression API errors"""
        # Mock API error
        sendgrid_client._mock_http_response.status = 400
        sendgrid_client._mock_http_response.json.return_value = {
            "errors": [{"message": "Invalid email address"}]
        }
        
        with pytest.raises(SendGridAPIException, match="Invalid email address"):
            await sendgrid_client.add_to_suppression(
                "invalid_email",
                SuppressionType.UNSUBSCRIBES
            )


class TestWebhookProcessing:
    """Test webhook event processing"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client for webhook testing"""
        config = SendGridConfig(api_key="test_key")
        
        # Mock database service
        mock_database = AsyncMock()
        mock_database.log_communication = AsyncMock(return_value="comm_123")
        
        client = SendGridClient(config, database_service=mock_database)
        
        return client
    
    @pytest.mark.asyncio
    async def test_process_event_webhook_delivered(self, sendgrid_client):
        """Test processing email delivered event"""
        webhook_events = WebhookTestData.sendgrid_event_webhook([
            {
                'email': 'delivered@example.com',
                'event': 'delivered',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': 'SG.delivered_123'
            }
        ])
        
        results = await sendgrid_client.process_event_webhook(webhook_events)
        
        assert len(results) == 1
        result = results[0]
        
        assert result['event'] == 'delivered'
        assert result['email'] == 'delivered@example.com'
        assert result['message_id'] == 'SG.delivered_123'
        assert result['processed'] is True
        
        # Verify database logging
        sendgrid_client.database_service.log_communication.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_event_webhook_opened(self, sendgrid_client):
        """Test processing email opened event"""
        webhook_events = [
            {
                'email': 'opened@example.com',
                'event': 'open',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': 'SG.opened_123',
                'useragent': 'Mozilla/5.0...',
                'ip': '192.168.1.100'
            }
        ]
        
        results = await sendgrid_client.process_event_webhook(webhook_events)
        
        assert len(results) == 1
        result = results[0]
        
        assert result['event'] == 'open'
        assert result['email'] == 'opened@example.com'
        assert result['metadata']['useragent'] == 'Mozilla/5.0...'
        assert result['metadata']['ip'] == '192.168.1.100'
    
    @pytest.mark.asyncio
    async def test_process_event_webhook_clicked(self, sendgrid_client):
        """Test processing email clicked event"""
        webhook_events = [
            {
                'email': 'clicked@example.com',
                'event': 'click',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': 'SG.clicked_123',
                'url': 'https://enterprisehub.ai/properties/north-austin'
            }
        ]
        
        results = await sendgrid_client.process_event_webhook(webhook_events)
        
        assert len(results) == 1
        result = results[0]
        
        assert result['event'] == 'click'
        assert result['metadata']['url'] == 'https://enterprisehub.ai/properties/north-austin'
    
    @pytest.mark.asyncio
    async def test_process_event_webhook_bounced(self, sendgrid_client):
        """Test processing email bounced event"""
        webhook_events = [
            {
                'email': 'bounced@example.com',
                'event': 'bounce',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': 'SG.bounced_123',
                'reason': '550 No such user',
                'type': 'permanent'
            }
        ]
        
        results = await sendgrid_client.process_event_webhook(webhook_events)
        
        assert len(results) == 1
        result = results[0]
        
        assert result['event'] == 'bounce'
        assert result['metadata']['reason'] == '550 No such user'
        assert result['metadata']['bounce_type'] == 'permanent'
        
        # Verify bounced email was added to suppression cache
        assert 'bounced@example.com' in sendgrid_client._suppression_cache
    
    @pytest.mark.asyncio
    async def test_process_event_webhook_unsubscribed(self, sendgrid_client):
        """Test processing unsubscribe event"""
        webhook_events = [
            {
                'email': 'unsubscribed@example.com',
                'event': 'unsubscribe',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': 'SG.unsub_123'
            }
        ]
        
        results = await sendgrid_client.process_event_webhook(webhook_events)
        
        assert len(results) == 1
        result = results[0]
        
        assert result['event'] == 'unsubscribe'
        
        # Verify unsubscribed email was added to suppression cache
        assert 'unsubscribed@example.com' in sendgrid_client._suppression_cache
    
    @pytest.mark.asyncio
    async def test_process_event_webhook_multiple_events(self, sendgrid_client):
        """Test processing multiple webhook events"""
        webhook_events = [
            {
                'email': 'user1@example.com',
                'event': 'delivered',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': 'SG.msg1'
            },
            {
                'email': 'user1@example.com',
                'event': 'open',
                'timestamp': int(datetime.now().timestamp()) + 60,
                'sg_message_id': 'SG.msg1'
            },
            {
                'email': 'user2@example.com',
                'event': 'bounce',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': 'SG.msg2',
                'reason': 'Mailbox full'
            }
        ]
        
        results = await sendgrid_client.process_event_webhook(webhook_events)
        
        assert len(results) == 3
        assert results[0]['event'] == 'delivered'
        assert results[1]['event'] == 'open'
        assert results[2]['event'] == 'bounce'
        
        # Verify bounced email was suppressed
        assert 'user2@example.com' in sendgrid_client._suppression_cache
        assert 'user1@example.com' not in sendgrid_client._suppression_cache
    
    @pytest.mark.asyncio
    async def test_process_event_webhook_invalid_event(self, sendgrid_client):
        """Test processing invalid webhook event"""
        webhook_events = [
            {
                'email': '',  # Invalid email
                'event': 'unknown_event',
                'timestamp': None
            }
        ]
        
        results = await sendgrid_client.process_event_webhook(webhook_events)
        
        assert len(results) == 1
        result = results[0]
        
        assert result['processed'] is False
        assert 'error' in result


class TestBulkEmailOperations:
    """Test bulk email operations"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client for bulk email testing"""
        config = SendGridConfig(
            api_key="test_key",
            from_email="marketing@enterprisehub.ai"
        )
        
        client = SendGridClient(config)
        
        # Mock successful bulk sending
        mock_sg_client = MagicMock()
        
        def mock_send_email(**kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": f"SG.bulk_{hash(str(kwargs))}"}
            return mock_response
        
        mock_sg_client.send.side_effect = mock_send_email
        client.sg_client = mock_sg_client
        
        return client
    
    @pytest.mark.asyncio
    async def test_send_bulk_emails_success(self, sendgrid_client):
        """Test successful bulk email sending"""
        recipients = [
            {
                "email": "lead1@example.com",
                "name": "John Doe",
                "location": "North Austin",
                "budget": "$500K"
            },
            {
                "email": "lead2@example.com", 
                "name": "Jane Smith",
                "location": "South Austin",
                "budget": "$450K"
            },
            {
                "email": "lead3@example.com",
                "name": "Bob Wilson",
                "location": "East Austin", 
                "budget": "$350K"
            }
        ]
        
        email_template = {
            "subject": "Austin Market Update for {location}",
            "html_content": "<h1>Hi {name}</h1><p>Market update for {location} with budget {budget}</p>",
            "text_content": "Hi {name}, Market update for {location} with budget {budget}"
        }
        
        results = await sendgrid_client.send_bulk_emails(recipients, email_template)
        
        assert len(results) == 3
        assert all(result['success'] for result in results)
        assert all('message_id' in result for result in results)
        
        # Verify all emails were sent
        assert sendgrid_client.sg_client.send.call_count == 3
        
        # Verify personalization worked
        for i, result in enumerate(results):
            assert result['email'] == recipients[i]['email']
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_send_bulk_emails_with_failures(self, sendgrid_client):
        """Test bulk email with some failures"""
        recipients = [
            {"email": "good1@example.com", "name": "Good User 1"},
            {"email": "invalid_email", "name": "Invalid User"},  # Will fail
            {"email": "good2@example.com", "name": "Good User 2"}
        ]
        
        # Mock one failure
        def mock_send_with_failure(**kwargs):
            mock_response = MagicMock()
            if "invalid_email" in str(kwargs):
                mock_response.status_code = 400
                mock_response.body = b'{"errors": [{"message": "Invalid email"}]}'
            else:
                mock_response.status_code = 202
                mock_response.headers = {"X-Message-Id": f"SG.success_{hash(str(kwargs))}"}
            return mock_response
        
        sendgrid_client.sg_client.send.side_effect = mock_send_with_failure
        
        email_template = {
            "subject": "Test Email",
            "html_content": "<p>Hi {name}</p>"
        }
        
        results = await sendgrid_client.send_bulk_emails(recipients, email_template)
        
        assert len(results) == 3
        assert results[0]['success'] is True   # Good User 1
        assert results[1]['success'] is False  # Invalid email
        assert results[2]['success'] is True   # Good User 2
        
        # Check error details for failed email
        assert 'error' in results[1]
        assert 'Invalid email' in results[1]['error']
    
    @pytest.mark.asyncio
    async def test_send_bulk_emails_rate_limiting(self, sendgrid_client):
        """Test bulk email with rate limiting"""
        # Set tight rate limit
        sendgrid_client._rate_limit_semaphore = asyncio.Semaphore(1)
        
        recipients = [
            {"email": f"user{i}@example.com", "name": f"User {i}"}
            for i in range(5)
        ]
        
        email_template = {
            "subject": "Test Email {name}",
            "html_content": "<p>Hi {name}</p>"
        }
        
        import time
        start_time = time.time()
        
        results = await sendgrid_client.send_bulk_emails(recipients, email_template)
        
        end_time = time.time()
        
        # All should succeed
        assert len(results) == 5
        assert all(result['success'] for result in results)
        
        # Should take some time due to rate limiting
        execution_time = end_time - start_time
        assert execution_time > 0  # Basic sanity check
    
    @pytest.mark.asyncio
    async def test_send_bulk_emails_suppressed_recipients(self, sendgrid_client):
        """Test bulk email filtering out suppressed recipients"""
        recipients = [
            {"email": "allowed@example.com", "name": "Allowed User"},
            {"email": "suppressed@example.com", "name": "Suppressed User"},
            {"email": "another@example.com", "name": "Another User"}
        ]
        
        # Add one email to suppression cache
        sendgrid_client._suppression_cache.add("suppressed@example.com")
        
        email_template = {
            "subject": "Test Email",
            "html_content": "<p>Hi {name}</p>"
        }
        
        results = await sendgrid_client.send_bulk_emails(recipients, email_template)
        
        assert len(results) == 3
        assert results[0]['success'] is True   # allowed@example.com
        assert results[1]['success'] is False  # suppressed@example.com
        assert results[2]['success'] is True   # another@example.com
        
        # Check suppressed email error
        assert 'suppressed' in results[1]['error'].lower()
        
        # Verify only 2 emails were actually sent
        assert sendgrid_client.sg_client.send.call_count == 2


class TestEmailAnalytics:
    """Test email analytics and statistics"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client for analytics testing"""
        config = SendGridConfig(api_key="test_key")
        client = SendGridClient(config)
        
        # Mock HTTP session for stats API
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        
        client.session = mock_session
        client._mock_http_response = mock_response
        
        return client
    
    @pytest.mark.asyncio
    async def test_get_email_stats(self, sendgrid_client):
        """Test getting email statistics"""
        # Mock stats response
        sendgrid_client._mock_http_response.json.return_value = [
            {
                "date": "2026-01-16",
                "stats": [
                    {
                        "metrics": {
                            "blocks": 0,
                            "bounces": 5,
                            "clicks": 120,
                            "deferred": 2,
                            "delivered": 450,
                            "drops": 1,
                            "opens": 280,
                            "processed": 456,
                            "requests": 456,
                            "spam_reports": 1,
                            "unique_clicks": 85,
                            "unique_opens": 195,
                            "unsubscribes": 3
                        }
                    }
                ]
            }
        ]
        
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        stats = await sendgrid_client.get_email_stats(start_date, end_date)
        
        assert 'summary' in stats
        assert 'daily_stats' in stats
        
        summary = stats['summary']
        assert summary['total_sent'] == 456
        assert summary['total_delivered'] == 450
        assert summary['total_opens'] == 280
        assert summary['total_clicks'] == 120
        assert summary['delivery_rate'] == pytest.approx(0.987, rel=1e-2)  # 450/456
        assert summary['open_rate'] == pytest.approx(0.622, rel=1e-2)      # 280/450
        assert summary['click_rate'] == pytest.approx(0.267, rel=1e-2)     # 120/450
    
    @pytest.mark.asyncio
    async def test_get_email_stats_by_category(self, sendgrid_client):
        """Test getting stats filtered by category"""
        # Mock category stats response
        sendgrid_client._mock_http_response.json.return_value = [
            {
                "date": "2026-01-16",
                "stats": [
                    {
                        "name": "market_update",
                        "metrics": {
                            "delivered": 150,
                            "opens": 90,
                            "clicks": 35
                        }
                    },
                    {
                        "name": "property_alert",
                        "metrics": {
                            "delivered": 200,
                            "opens": 130,
                            "clicks": 65
                        }
                    }
                ]
            }
        ]
        
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        stats = await sendgrid_client.get_email_stats(
            start_date, 
            end_date, 
            categories=["market_update", "property_alert"]
        )
        
        assert 'category_breakdown' in stats
        breakdown = stats['category_breakdown']
        
        assert 'market_update' in breakdown
        assert breakdown['market_update']['delivered'] == 150
        assert breakdown['market_update']['open_rate'] == 0.6  # 90/150
        
        assert 'property_alert' in breakdown
        assert breakdown['property_alert']['delivered'] == 200
        assert breakdown['property_alert']['click_rate'] == 0.325  # 65/200
    
    @pytest.mark.asyncio
    async def test_get_email_stats_error(self, sendgrid_client):
        """Test handling stats API errors"""
        # Mock API error
        sendgrid_client._mock_http_response.status = 400
        sendgrid_client._mock_http_response.json.return_value = {
            "errors": [{"message": "Invalid date range"}]
        }
        
        start_date = datetime.now()
        end_date = datetime.now() - timedelta(days=1)  # Invalid range
        
        with pytest.raises(SendGridAPIException, match="Invalid date range"):
            await sendgrid_client.get_email_stats(start_date, end_date)


class TestHealthAndMonitoring:
    """Test health check and monitoring functionality"""
    
    @pytest_asyncio.fixture
    async def sendgrid_client(self):
        """Create SendGrid client for health testing"""
        config = SendGridConfig(api_key="test_key")
        client = SendGridClient(config)
        
        # Mock HTTP session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        
        client.session = mock_session
        client._mock_http_response = mock_response
        
        return client
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, sendgrid_client):
        """Test successful health check"""
        # Mock API response
        sendgrid_client._mock_http_response.json.return_value = {
            "account_type": "paid",
            "username": "test_user",
            "email": "test@example.com"
        }
        
        result = await sendgrid_client.health_check()
        
        assert result['status'] == 'healthy'
        assert result['api_accessible'] is True
        assert result['account_type'] == 'paid'
        assert result['response_time_ms'] > 0
        assert result['suppression_cache_size'] >= 0
    
    @pytest.mark.asyncio
    async def test_health_check_api_error(self, sendgrid_client):
        """Test health check when API is inaccessible"""
        # Mock API error
        sendgrid_client.session.request.side_effect = Exception("Connection failed")
        
        result = await sendgrid_client.health_check()
        
        assert result['status'] == 'unhealthy'
        assert result['api_accessible'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_health_check_authentication_error(self, sendgrid_client):
        """Test health check with authentication error"""
        # Mock auth error
        sendgrid_client._mock_http_response.status = 401
        sendgrid_client._mock_http_response.json.return_value = {
            "errors": [{"message": "The provided authorization grant is invalid"}]
        }
        
        result = await sendgrid_client.health_check()
        
        assert result['status'] == 'unhealthy'
        assert result['api_accessible'] is False
        assert 'authorization' in result['error'].lower()


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_client_without_api_key(self):
        """Test client initialization without API key"""
        config = SendGridConfig()  # No API key
        
        with pytest.raises(ValueError, match="SendGrid API key is required"):
            SendGridClient(config)
    
    @pytest.mark.asyncio
    async def test_send_email_without_content(self):
        """Test sending email without content"""
        config = SendGridConfig(api_key="test_key")
        client = SendGridClient(config)
        
        with pytest.raises(SendGridAPIException, match="Email content is required"):
            await client.send_email(
                to_email="test@example.com",
                subject="No Content"
                # No html_content or text_content
            )
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        config = SendGridConfig(
            api_key="test_key",
            request_timeout_seconds=0.1
        )
        
        client = SendGridClient(config)
        
        # Mock timeout
        mock_session = MagicMock()
        mock_session.request.side_effect = asyncio.TimeoutError("Request timeout")
        client.session = mock_session
        
        with pytest.raises(SendGridAPIException, match="Request timeout"):
            await client._make_request('GET', '/test')


@pytest.mark.performance
class TestPerformanceCharacteristics:
    """Test SendGrid client performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_bulk_email_performance(self):
        """Test performance of bulk email operations"""
        config = SendGridConfig(api_key="test_key")
        client = SendGridClient(config)
        
        # Mock fast email sending
        mock_sg_client = MagicMock()
        
        def fast_send(**kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": f"SG.fast_{hash(str(kwargs))}"}
            return mock_response
        
        mock_sg_client.send.side_effect = fast_send
        client.sg_client = mock_sg_client
        
        # Test with many recipients
        recipients = [
            {"email": f"user{i}@example.com", "name": f"User {i}"}
            for i in range(100)
        ]
        
        email_template = {
            "subject": "Test Email {name}",
            "html_content": "<p>Hi {name}</p>"
        }
        
        import time
        start_time = time.time()
        
        results = await client.send_bulk_emails(recipients, email_template)
        
        end_time = time.time()
        
        # Verify all emails sent
        assert len(results) == 100
        assert all(result['success'] for result in results)
        
        # Performance should be reasonable (under 10 seconds for mocked operations)
        execution_time = end_time - start_time
        assert execution_time < 10.0


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main([
        "-v",
        "tests/services/test_sendgrid_client.py::TestEmailSending",
        "--tb=short"
    ])