"""
Enterprise Compliance Notification Service

Multi-channel notification delivery for compliance alerts with support for:
- Email (SMTP or API-based)
- Slack (Webhook or Bot API)
- Custom Webhooks
- SMS (future implementation)

Features:
- Priority-based delivery with configurable timeouts
- Recipient preference management
- Async queue processing for non-blocking sends
- Professional HTML email templates
- Slack Block Kit formatting
- Retry logic with exponential backoff
- Rate limiting per channel
- Comprehensive delivery tracking and logging
"""

import asyncio
import hashlib
import html
import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# Simple email regex pattern for validation when email-validator is not installed
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class NotificationChannel(str, Enum):
    """Supported notification delivery channels."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"  # Future implementation


class NotificationPriority(str, Enum):
    """Notification priority levels with delivery timeframes."""

    CRITICAL = "critical"  # Immediate delivery
    HIGH = "high"  # Within 15 minutes
    MEDIUM = "medium"  # Within 1 hour
    LOW = "low"  # Batched daily


class DeliveryStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationRecipient(BaseModel):
    """Notification recipient with channel-specific contact information."""

    id: str
    name: str
    email: Optional[str] = None  # Email address (validated in field_validator)
    slack_user_id: Optional[str] = None
    slack_channel: Optional[str] = None
    webhook_url: Optional[str] = None
    phone_number: Optional[str] = None  # For future SMS
    preferences: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: Any) -> Optional[str]:
        """Validate email format."""
        if v is None or v == "":
            return None
        if isinstance(v, str) and EMAIL_REGEX.match(v):
            return v.lower()
        raise ValueError(f"Invalid email format: {v}")

    @model_validator(mode="after")
    def set_default_preferences(self) -> "NotificationRecipient":
        """Set default notification preferences after model creation."""
        defaults = {
            "channels": [NotificationChannel.EMAIL.value, NotificationChannel.SLACK.value],
            "alert_types": ["violation", "threshold_breach", "certification_expiry"],
            "quiet_hours": {"enabled": False, "start": "22:00", "end": "08:00"},
            "batch_low_priority": True,
        }
        # Handle None, empty dict, or missing value
        if self.preferences is None or len(self.preferences) == 0:
            self.preferences = defaults
        else:
            # Merge user preferences with defaults (user prefs take precedence)
            self.preferences = {**defaults, **self.preferences}
        return self

    def accepts_channel(self, channel: NotificationChannel) -> bool:
        """Check if recipient accepts notifications on the given channel."""
        accepted_channels = self.preferences.get("channels", [])
        return channel.value in accepted_channels

    def accepts_alert_type(self, alert_type: str) -> bool:
        """Check if recipient accepts the given alert type."""
        accepted_types = self.preferences.get("alert_types", [])
        # Empty list means accept all
        return not accepted_types or alert_type in accepted_types


class ComplianceNotification(BaseModel):
    """Compliance notification payload."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    message: str
    priority: NotificationPriority
    alert_type: str
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    regulation: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = Field(default_factory=dict)
    channels: List[NotificationChannel] = Field(default_factory=list)
    recipients: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_severity_emoji(self) -> str:
        """Get emoji indicator for notification priority."""
        return {
            NotificationPriority.CRITICAL: "\u26a0\ufe0f",  # Warning sign
            NotificationPriority.HIGH: "\U0001f534",  # Red circle
            NotificationPriority.MEDIUM: "\U0001f7e1",  # Yellow circle
            NotificationPriority.LOW: "\U0001f7e2",  # Green circle
        }.get(self.priority, "\U0001f535")  # Blue circle default

    def get_regulation_badge(self) -> str:
        """Get regulatory framework badge."""
        badges = {
            "eu_ai_act": "[EU AI Act]",
            "sec_ai_guidance": "[SEC]",
            "hipaa": "[HIPAA]",
            "gdpr": "[GDPR]",
            "soc2": "[SOC 2]",
            "iso_27001": "[ISO 27001]",
        }
        return badges.get(self.regulation, f"[{self.regulation}]" if self.regulation else "")


@dataclass
class DeliveryResult:
    """Result of a notification delivery attempt."""

    notification_id: str
    recipient_id: str
    channel: NotificationChannel
    status: DeliveryStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    retry_count: int = 0


@dataclass
class RateLimitState:
    """Rate limiting state for a channel."""

    requests_in_window: int = 0
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    max_requests: int = 100
    window_seconds: int = 60


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    def __init__(self, mock_mode: bool = True):
        """
        Initialize provider.

        Args:
            mock_mode: If True, log notifications instead of actually sending them.
                      This allows testing without actual credentials.
        """
        self.mock_mode = mock_mode
        self.rate_limit = RateLimitState()
        self._delivery_log: List[DeliveryResult] = []

    @abstractmethod
    async def send(
        self,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
    ) -> DeliveryResult:
        """
        Send a notification to a recipient.

        Args:
            notification: The notification to send
            recipient: The recipient to send to

        Returns:
            DeliveryResult with status and any error information
        """
        pass

    @abstractmethod
    def validate_recipient(self, recipient: NotificationRecipient) -> bool:
        """
        Validate that the recipient has required contact information for this channel.

        Args:
            recipient: The recipient to validate

        Returns:
            True if recipient can receive notifications on this channel
        """
        pass

    def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.

        Returns:
            True if within limits, False if rate limited
        """
        now = datetime.now(timezone.utc)
        window_elapsed = (now - self.rate_limit.window_start).total_seconds()

        if window_elapsed > self.rate_limit.window_seconds:
            # Reset window
            self.rate_limit.window_start = now
            self.rate_limit.requests_in_window = 0
            return True

        return self.rate_limit.requests_in_window < self.rate_limit.max_requests

    def record_request(self) -> None:
        """Record a request for rate limiting."""
        self.rate_limit.requests_in_window += 1

    def get_delivery_history(self) -> List[DeliveryResult]:
        """Get delivery history for this provider."""
        return self._delivery_log.copy()


class EmailNotificationProvider(NotificationProvider):
    """Send notifications via email using SMTP or external API."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        from_address: str = "compliance@company.com",
        from_name: str = "Compliance Platform",
        mock_mode: bool = True,
    ):
        """
        Initialize email provider.

        Supports both SMTP and API-based email services (SendGrid, Mailgun, etc.)
        """
        super().__init__(mock_mode=mock_mode)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.api_key = api_key
        self.api_url = api_url
        self.from_address = from_address
        self.from_name = from_name

        # Rate limit: 100 emails per minute
        self.rate_limit.max_requests = 100
        self.rate_limit.window_seconds = 60

        # Check configuration
        self._configured = bool(smtp_host or api_key) and not mock_mode

    def validate_recipient(self, recipient: NotificationRecipient) -> bool:
        """Check recipient has valid email."""
        return recipient.email is not None and recipient.active

    async def send(
        self,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
    ) -> DeliveryResult:
        """Send email notification."""
        result = DeliveryResult(
            notification_id=notification.id,
            recipient_id=recipient.id,
            channel=NotificationChannel.EMAIL,
            status=DeliveryStatus.PENDING,
        )

        try:
            if not self.validate_recipient(recipient):
                result.status = DeliveryStatus.FAILED
                result.error_message = "Recipient has no valid email address"
                return result

            if not self.check_rate_limit():
                result.status = DeliveryStatus.FAILED
                result.error_message = "Rate limit exceeded"
                return result

            # Format email
            html_content = self._format_email_html(notification)
            text_content = self._format_email_text(notification)

            if self.mock_mode:
                # Mock mode - log instead of sending
                logger.info(
                    f"[MOCK EMAIL] To: {recipient.email}, Subject: {notification.title}\n"
                    f"Priority: {notification.priority.value}\n"
                    f"Message: {notification.message[:200]}..."
                )
                result.status = DeliveryStatus.DELIVERED
                result.response_data = {
                    "mock": True,
                    "to": recipient.email,
                    "subject": notification.title,
                }
            elif self.api_key:
                # Send via API (e.g., SendGrid)
                result = await self._send_via_api(notification, recipient, html_content, text_content, result)
            elif self.smtp_host:
                # Send via SMTP
                result = await self._send_via_smtp(notification, recipient, html_content, text_content, result)
            else:
                result.status = DeliveryStatus.FAILED
                result.error_message = "No email provider configured"

            self.record_request()
            self._delivery_log.append(result)
            return result

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            result.status = DeliveryStatus.FAILED
            result.error_message = str(e)
            self._delivery_log.append(result)
            return result

    async def _send_via_api(
        self,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
        html_content: str,
        text_content: str,
        result: DeliveryResult,
    ) -> DeliveryResult:
        """Send email via external API."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "from": {"email": self.from_address, "name": self.from_name},
                    "to": [{"email": recipient.email, "name": recipient.name}],
                    "subject": f"{notification.get_severity_emoji()} {notification.title}",
                    "html": html_content,
                    "text": text_content,
                }

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                async with session.post(
                    self.api_url or "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status in (200, 201, 202):
                        result.status = DeliveryStatus.DELIVERED
                        result.response_data = {"status_code": response.status}
                    else:
                        result.status = DeliveryStatus.FAILED
                        result.error_message = f"API returned {response.status}"
                        result.response_data = {"status_code": response.status}

        except asyncio.TimeoutError:
            result.status = DeliveryStatus.FAILED
            result.error_message = "API request timed out"
        except aiohttp.ClientError as e:
            result.status = DeliveryStatus.FAILED
            result.error_message = f"API request failed: {e}"

        return result

    async def _send_via_smtp(
        self,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
        html_content: str,
        text_content: str,
        result: DeliveryResult,
    ) -> DeliveryResult:
        """Send email via SMTP."""
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            import aiosmtplib

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{notification.get_severity_emoji()} {notification.title}"
            msg["From"] = f"{self.from_name} <{self.from_address}>"
            msg["To"] = recipient.email

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            result.status = DeliveryStatus.DELIVERED
            result.response_data = {"method": "smtp"}

        except ImportError:
            result.status = DeliveryStatus.FAILED
            result.error_message = "aiosmtplib not installed"
        except Exception as e:
            result.status = DeliveryStatus.FAILED
            result.error_message = f"SMTP send failed: {e}"

        return result

    def _format_email_html(self, notification: ComplianceNotification) -> str:
        """Generate professional HTML email template."""
        priority_colors = {
            NotificationPriority.CRITICAL: "#DC2626",
            NotificationPriority.HIGH: "#EA580C",
            NotificationPriority.MEDIUM: "#CA8A04",
            NotificationPriority.LOW: "#16A34A",
        }
        color = priority_colors.get(notification.priority, "#2563EB")

        # Escape HTML in user-provided content
        safe_title = html.escape(notification.title)
        safe_message = html.escape(notification.message)
        safe_model = html.escape(notification.model_name or "N/A")

        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <tr>
            <td style="background-color: {color}; padding: 24px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">
                    {notification.get_severity_emoji()} Compliance Alert
                </h1>
                <p style="color: #ffffff; margin: 8px 0 0 0; opacity: 0.9;">
                    Priority: {notification.priority.value.upper()}
                    {notification.get_regulation_badge()}
                </p>
            </td>
        </tr>

        <!-- Main Content -->
        <tr>
            <td style="padding: 32px 24px;">
                <h2 style="color: #1f2937; margin: 0 0 16px 0; font-size: 20px;">
                    {safe_title}
                </h2>
                <p style="color: #4b5563; margin: 0 0 24px 0; font-size: 16px; line-height: 1.5;">
                    {safe_message}
                </p>

                <!-- Alert Details -->
                <table width="100%" style="background-color: #f9fafb; border-radius: 8px; padding: 16px;">
                    <tr>
                        <td style="padding: 8px 16px;">
                            <strong style="color: #374151;">Alert Type:</strong>
                            <span style="color: #6b7280;">{html.escape(notification.alert_type)}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 16px;">
                            <strong style="color: #374151;">AI Model:</strong>
                            <span style="color: #6b7280;">{safe_model}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 16px;">
                            <strong style="color: #374151;">Timestamp:</strong>
                            <span style="color: #6b7280;">{notification.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</span>
                        </td>
                    </tr>
                </table>

                <!-- CTA Button -->
                <table width="100%" style="margin-top: 24px;">
                    <tr>
                        <td style="text-align: center;">
                            <a href="#" style="display: inline-block; background-color: {color}; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: 600;">
                                View in Dashboard
                            </a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <!-- Footer -->
        <tr>
            <td style="background-color: #f3f4f6; padding: 24px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; margin: 0; font-size: 14px;">
                    This is an automated message from the Compliance Platform.
                </p>
                <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 12px;">
                    Notification ID: {notification.id}
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        return html_template

    def _format_email_text(self, notification: ComplianceNotification) -> str:
        """Generate plain text email content."""
        text = f"""
COMPLIANCE ALERT - {notification.priority.value.upper()}
{notification.get_regulation_badge()}
{"=" * 50}

{notification.title}

{notification.message}

DETAILS
-------
Alert Type: {notification.alert_type}
AI Model: {notification.model_name or "N/A"}
Model ID: {notification.model_id or "N/A"}
Timestamp: {notification.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

---
Notification ID: {notification.id}
This is an automated message from the Compliance Platform.
        """
        return text.strip()


class SlackNotificationProvider(NotificationProvider):
    """Send notifications to Slack channels or users."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: str = "#compliance-alerts",
        mock_mode: bool = True,
    ):
        """
        Initialize Slack provider.

        Can use either incoming webhooks or Bot API token.
        """
        super().__init__(mock_mode=mock_mode)
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.default_channel = default_channel

        # Rate limit: 1 request per second (Slack limit)
        self.rate_limit.max_requests = 60
        self.rate_limit.window_seconds = 60

        self._configured = bool(webhook_url or bot_token) and not mock_mode

    def validate_recipient(self, recipient: NotificationRecipient) -> bool:
        """Check recipient has Slack info or we have a default channel."""
        return recipient.active and (recipient.slack_channel or recipient.slack_user_id or self.default_channel)

    async def send(
        self,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
    ) -> DeliveryResult:
        """Send Slack notification."""
        result = DeliveryResult(
            notification_id=notification.id,
            recipient_id=recipient.id,
            channel=NotificationChannel.SLACK,
            status=DeliveryStatus.PENDING,
        )

        try:
            if not self.validate_recipient(recipient):
                result.status = DeliveryStatus.FAILED
                result.error_message = "Recipient has no Slack channel/user configured"
                return result

            if not self.check_rate_limit():
                result.status = DeliveryStatus.FAILED
                result.error_message = "Rate limit exceeded"
                return result

            # Determine target
            target = recipient.slack_channel or recipient.slack_user_id or self.default_channel

            # Format Slack message
            blocks = self._format_slack_blocks(notification)

            if self.mock_mode:
                # Mock mode - log instead of sending
                logger.info(
                    f"[MOCK SLACK] To: {target}\n"
                    f"Title: {notification.title}\n"
                    f"Priority: {notification.priority.value}\n"
                    f"Blocks: {len(blocks)} blocks"
                )
                result.status = DeliveryStatus.DELIVERED
                result.response_data = {"mock": True, "target": target, "blocks": len(blocks)}
            elif self.webhook_url:
                result = await self._send_via_webhook(notification, target, blocks, result)
            elif self.bot_token:
                result = await self._send_via_bot_api(notification, target, blocks, result)
            else:
                result.status = DeliveryStatus.FAILED
                result.error_message = "No Slack credentials configured"

            self.record_request()
            self._delivery_log.append(result)
            return result

        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            result.status = DeliveryStatus.FAILED
            result.error_message = str(e)
            self._delivery_log.append(result)
            return result

    async def _send_via_webhook(
        self,
        notification: ComplianceNotification,
        target: str,
        blocks: List[Dict[str, Any]],
        result: DeliveryResult,
    ) -> DeliveryResult:
        """Send via incoming webhook."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "channel": target,
                    "blocks": blocks,
                    "text": f"{notification.get_severity_emoji()} {notification.title}",  # Fallback
                }

                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response_text = await response.text()

                    if response.status == 200 and response_text == "ok":
                        result.status = DeliveryStatus.DELIVERED
                        result.response_data = {"method": "webhook"}
                    else:
                        result.status = DeliveryStatus.FAILED
                        result.error_message = f"Webhook returned: {response_text}"

        except asyncio.TimeoutError:
            result.status = DeliveryStatus.FAILED
            result.error_message = "Webhook request timed out"
        except aiohttp.ClientError as e:
            result.status = DeliveryStatus.FAILED
            result.error_message = f"Webhook request failed: {e}"

        return result

    async def _send_via_bot_api(
        self,
        notification: ComplianceNotification,
        target: str,
        blocks: List[Dict[str, Any]],
        result: DeliveryResult,
    ) -> DeliveryResult:
        """Send via Slack Bot API."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "channel": target,
                    "blocks": blocks,
                    "text": f"{notification.get_severity_emoji()} {notification.title}",
                }

                headers = {
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json",
                }

                async with session.post(
                    "https://slack.com/api/chat.postMessage",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response_data = await response.json()

                    if response_data.get("ok"):
                        result.status = DeliveryStatus.DELIVERED
                        result.response_data = {
                            "method": "bot_api",
                            "ts": response_data.get("ts"),
                        }
                    else:
                        result.status = DeliveryStatus.FAILED
                        result.error_message = response_data.get("error", "Unknown error")

        except asyncio.TimeoutError:
            result.status = DeliveryStatus.FAILED
            result.error_message = "Bot API request timed out"
        except aiohttp.ClientError as e:
            result.status = DeliveryStatus.FAILED
            result.error_message = f"Bot API request failed: {e}"

        return result

    def _format_slack_blocks(self, notification: ComplianceNotification) -> List[Dict[str, Any]]:
        """Generate Slack Block Kit message."""
        priority_colors = {
            NotificationPriority.CRITICAL: "danger",
            NotificationPriority.HIGH: "warning",
            NotificationPriority.MEDIUM: "#CA8A04",
            NotificationPriority.LOW: "good",
        }

        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{notification.get_severity_emoji()} Compliance Alert",
                    "emoji": True,
                },
            },
            # Title and context
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{notification.title}*\n{notification.get_regulation_badge()}",
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Details"},
                    "style": "primary"
                    if notification.priority in (NotificationPriority.CRITICAL, NotificationPriority.HIGH)
                    else None,
                    "action_id": f"view_alert_{notification.id}",
                },
            },
            # Message
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": notification.message,
                },
            },
            # Divider
            {"type": "divider"},
            # Details
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{notification.priority.value.upper()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Alert Type:*\n{notification.alert_type}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*AI Model:*\n{notification.model_name or 'N/A'}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Model ID:*\n`{notification.model_id or 'N/A'}`",
                    },
                ],
            },
            # Context footer
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Notification ID: `{notification.id}` | {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    }
                ],
            },
        ]

        # Remove None style from button if not high priority
        if blocks[1]["accessory"].get("style") is None:
            del blocks[1]["accessory"]["style"]

        return blocks


class WebhookNotificationProvider(NotificationProvider):
    """Send notifications to custom webhooks."""

    def __init__(
        self,
        default_url: Optional[str] = None,
        auth_header: Optional[str] = None,
        auth_value: Optional[str] = None,
        mock_mode: bool = True,
    ):
        """
        Initialize webhook provider.

        Args:
            default_url: Default webhook URL if recipient doesn't have one
            auth_header: Authentication header name (e.g., "Authorization", "X-API-Key")
            auth_value: Authentication header value
            mock_mode: If True, log instead of sending
        """
        super().__init__(mock_mode=mock_mode)
        self.default_url = default_url
        self.auth_header = auth_header
        self.auth_value = auth_value

        # Rate limit: 100 requests per minute
        self.rate_limit.max_requests = 100
        self.rate_limit.window_seconds = 60

    def validate_recipient(self, recipient: NotificationRecipient) -> bool:
        """Check recipient has webhook URL or we have a default."""
        return recipient.active and (recipient.webhook_url or self.default_url)

    async def send(
        self,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
    ) -> DeliveryResult:
        """Send webhook notification."""
        result = DeliveryResult(
            notification_id=notification.id,
            recipient_id=recipient.id,
            channel=NotificationChannel.WEBHOOK,
            status=DeliveryStatus.PENDING,
        )

        try:
            webhook_url = recipient.webhook_url or self.default_url

            if not webhook_url:
                result.status = DeliveryStatus.FAILED
                result.error_message = "No webhook URL configured"
                return result

            if not self.check_rate_limit():
                result.status = DeliveryStatus.FAILED
                result.error_message = "Rate limit exceeded"
                return result

            # Prepare payload
            payload = self._format_webhook_payload(notification, recipient)

            if self.mock_mode:
                logger.info(
                    f"[MOCK WEBHOOK] URL: {webhook_url}\n"
                    f"Notification: {notification.id}\n"
                    f"Payload size: {len(json.dumps(payload))} bytes"
                )
                result.status = DeliveryStatus.DELIVERED
                result.response_data = {"mock": True, "url": webhook_url}
            else:
                result = await self._send_webhook(webhook_url, payload, result)

            self.record_request()
            self._delivery_log.append(result)
            return result

        except Exception as e:
            logger.error(f"Webhook send failed: {e}")
            result.status = DeliveryStatus.FAILED
            result.error_message = str(e)
            self._delivery_log.append(result)
            return result

    async def _send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        result: DeliveryResult,
    ) -> DeliveryResult:
        """Send HTTP POST to webhook."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json"}

                if self.auth_header and self.auth_value:
                    headers[self.auth_header] = self.auth_value

                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status in (200, 201, 202, 204):
                        result.status = DeliveryStatus.DELIVERED
                        result.response_data = {"status_code": response.status}
                    else:
                        result.status = DeliveryStatus.FAILED
                        result.error_message = f"Webhook returned {response.status}"
                        result.response_data = {"status_code": response.status}

        except asyncio.TimeoutError:
            result.status = DeliveryStatus.FAILED
            result.error_message = "Webhook request timed out"
        except aiohttp.ClientError as e:
            result.status = DeliveryStatus.FAILED
            result.error_message = f"Webhook request failed: {e}"

        return result

    def _format_webhook_payload(
        self,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
    ) -> Dict[str, Any]:
        """Format webhook payload."""
        return {
            "notification_id": notification.id,
            "timestamp": notification.timestamp.isoformat(),
            "priority": notification.priority.value,
            "alert_type": notification.alert_type,
            "title": notification.title,
            "message": notification.message,
            "model_id": notification.model_id,
            "model_name": notification.model_name,
            "regulation": notification.regulation,
            "data": notification.data,
            "recipient": {
                "id": recipient.id,
                "name": recipient.name,
            },
        }


class NotificationService:
    """
    Orchestrates notification delivery across multiple channels.

    Features:
    - Multi-channel delivery (email, Slack, webhook)
    - Priority-based processing
    - Async queue for non-blocking sends
    - Retry logic with exponential backoff
    - Recipient preference management
    - Delivery tracking and logging
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        mock_mode: bool = True,
    ):
        """
        Initialize notification service.

        Args:
            config: Configuration dictionary
            mock_mode: If True, providers will log instead of sending
        """
        self.config = config or {}
        self.mock_mode = mock_mode

        # Providers
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}

        # Recipients registry
        self.recipients: Dict[str, NotificationRecipient] = {}

        # Async queue
        self._queue: asyncio.Queue[ComplianceNotification] = asyncio.Queue()
        self._running: bool = False
        self._worker_task: Optional[asyncio.Task] = None

        # Delivery tracking
        self._delivery_results: List[DeliveryResult] = []
        self._delivery_callbacks: List[Callable[[DeliveryResult], None]] = []

        # Retry configuration
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay_base = self.config.get("retry_delay_base", 1.0)  # seconds
        self.retry_delay_max = self.config.get("retry_delay_max", 60.0)  # seconds

        # Batch processing for low priority
        self._low_priority_batch: List[ComplianceNotification] = []
        self._batch_size = self.config.get("batch_size", 10)
        self._batch_interval = self.config.get("batch_interval", 3600)  # 1 hour

        # Initialize default providers
        self._initialize_default_providers()

    def _initialize_default_providers(self) -> None:
        """Initialize default notification providers."""
        # Email provider
        email_config = self.config.get("email", {})
        self.providers[NotificationChannel.EMAIL] = EmailNotificationProvider(
            smtp_host=email_config.get("smtp_host"),
            smtp_port=email_config.get("smtp_port", 587),
            smtp_user=email_config.get("smtp_user"),
            smtp_password=email_config.get("smtp_password"),
            api_key=email_config.get("api_key"),
            api_url=email_config.get("api_url"),
            from_address=email_config.get("from_address", "compliance@company.com"),
            from_name=email_config.get("from_name", "Compliance Platform"),
            mock_mode=self.mock_mode,
        )

        # Slack provider
        slack_config = self.config.get("slack", {})
        self.providers[NotificationChannel.SLACK] = SlackNotificationProvider(
            webhook_url=slack_config.get("webhook_url"),
            bot_token=slack_config.get("bot_token"),
            default_channel=slack_config.get("default_channel", "#compliance-alerts"),
            mock_mode=self.mock_mode,
        )

        # Webhook provider
        webhook_config = self.config.get("webhook", {})
        self.providers[NotificationChannel.WEBHOOK] = WebhookNotificationProvider(
            default_url=webhook_config.get("default_url"),
            auth_header=webhook_config.get("auth_header"),
            auth_value=webhook_config.get("auth_value"),
            mock_mode=self.mock_mode,
        )

        logger.info(f"Initialized notification providers: {list(self.providers.keys())}")

    def register_provider(
        self,
        channel: NotificationChannel,
        provider: NotificationProvider,
    ) -> None:
        """
        Register a notification provider.

        Args:
            channel: The channel this provider handles
            provider: The provider instance
        """
        self.providers[channel] = provider
        logger.info(f"Registered provider for {channel.value}")

    def register_recipient(self, recipient: NotificationRecipient) -> None:
        """
        Register a notification recipient.

        Args:
            recipient: The recipient to register
        """
        self.recipients[recipient.id] = recipient
        logger.info(f"Registered recipient: {recipient.id} ({recipient.name})")

    def unregister_recipient(self, recipient_id: str) -> bool:
        """
        Unregister a notification recipient.

        Args:
            recipient_id: ID of recipient to remove

        Returns:
            True if removed, False if not found
        """
        if recipient_id in self.recipients:
            del self.recipients[recipient_id]
            logger.info(f"Unregistered recipient: {recipient_id}")
            return True
        return False

    def get_recipient(self, recipient_id: str) -> Optional[NotificationRecipient]:
        """Get recipient by ID."""
        return self.recipients.get(recipient_id)

    def add_delivery_callback(self, callback: Callable[[DeliveryResult], None]) -> None:
        """Add callback to be called on each delivery result."""
        self._delivery_callbacks.append(callback)

    async def send_notification(
        self,
        notification: ComplianceNotification,
    ) -> Dict[str, Any]:
        """
        Send notification to all recipients via configured channels.

        Args:
            notification: The notification to send

        Returns:
            Dictionary with delivery results per recipient and channel
        """
        results: Dict[str, Dict[str, Any]] = {}

        # Determine channels to use
        channels = notification.channels or [
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
        ]

        # Determine recipients
        recipient_ids = notification.recipients or list(self.recipients.keys())

        for recipient_id in recipient_ids:
            recipient = self.recipients.get(recipient_id)
            if not recipient:
                logger.warning(f"Recipient not found: {recipient_id}")
                results[recipient_id] = {"error": "Recipient not found"}
                continue

            if not recipient.active:
                logger.info(f"Skipping inactive recipient: {recipient_id}")
                continue

            if not recipient.accepts_alert_type(notification.alert_type):
                logger.info(f"Recipient {recipient_id} does not accept alert type: {notification.alert_type}")
                continue

            results[recipient_id] = {}

            for channel in channels:
                # Check recipient accepts this channel
                if not recipient.accepts_channel(channel):
                    results[recipient_id][channel.value] = {
                        "status": "skipped",
                        "reason": "Channel not accepted by recipient",
                    }
                    continue

                # Get provider
                provider = self.providers.get(channel)
                if not provider:
                    results[recipient_id][channel.value] = {
                        "status": "failed",
                        "error": f"No provider for {channel.value}",
                    }
                    continue

                # Validate recipient for this channel
                if not provider.validate_recipient(recipient):
                    results[recipient_id][channel.value] = {
                        "status": "skipped",
                        "reason": f"Invalid recipient for {channel.value}",
                    }
                    continue

                # Send with retry
                delivery_result = await self._send_with_retry(
                    provider,
                    notification,
                    recipient,
                )

                self._delivery_results.append(delivery_result)

                # Trigger callbacks
                for callback in self._delivery_callbacks:
                    try:
                        callback(delivery_result)
                    except Exception as e:
                        logger.error(f"Delivery callback error: {e}")

                results[recipient_id][channel.value] = {
                    "status": delivery_result.status.value,
                    "error": delivery_result.error_message,
                    "retries": delivery_result.retry_count,
                }

        return {
            "notification_id": notification.id,
            "timestamp": notification.timestamp.isoformat(),
            "results": results,
        }

    async def _send_with_retry(
        self,
        provider: NotificationProvider,
        notification: ComplianceNotification,
        recipient: NotificationRecipient,
    ) -> DeliveryResult:
        """Send notification with exponential backoff retry."""
        result: Optional[DeliveryResult] = None
        retry_count = 0

        while retry_count <= self.max_retries:
            result = await provider.send(notification, recipient)

            if result.status == DeliveryStatus.DELIVERED:
                break

            if retry_count >= self.max_retries:
                break

            # Exponential backoff
            delay = min(
                self.retry_delay_base * (2**retry_count),
                self.retry_delay_max,
            )
            logger.info(
                f"Retry {retry_count + 1}/{self.max_retries} for {notification.id} "
                f"in {delay:.1f}s (error: {result.error_message})"
            )
            await asyncio.sleep(delay)

            retry_count += 1
            result.retry_count = retry_count
            result.status = DeliveryStatus.RETRYING

        return result

    async def queue_notification(self, notification: ComplianceNotification) -> str:
        """
        Queue notification for async processing.

        Args:
            notification: The notification to queue

        Returns:
            Notification ID
        """
        # Handle low priority batching
        if notification.priority == NotificationPriority.LOW and self.config.get("batch_low_priority", True):
            self._low_priority_batch.append(notification)
            if len(self._low_priority_batch) >= self._batch_size:
                # Process batch
                for n in self._low_priority_batch:
                    await self._queue.put(n)
                self._low_priority_batch.clear()
            return notification.id

        await self._queue.put(notification)
        logger.debug(f"Queued notification: {notification.id}")
        return notification.id

    async def start_worker(self) -> None:
        """Start background worker for queued notifications."""
        if self._running:
            logger.warning("Worker already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info("Notification worker started")

    async def stop_worker(self) -> None:
        """Stop the background worker."""
        self._running = False

        # Process remaining low priority batch
        if self._low_priority_batch:
            for notification in self._low_priority_batch:
                await self._queue.put(notification)
            self._low_priority_batch.clear()

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        logger.info("Notification worker stopped")

    async def _process_queue(self) -> None:
        """Process queued notifications."""
        while self._running:
            try:
                # Get notification with timeout
                try:
                    notification = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                # Process based on priority
                if notification.priority == NotificationPriority.CRITICAL:
                    # Immediate processing
                    await self.send_notification(notification)
                elif notification.priority == NotificationPriority.HIGH:
                    # Process with slight delay to allow batching
                    await asyncio.sleep(0.1)
                    await self.send_notification(notification)
                else:
                    # Standard processing
                    await self.send_notification(notification)

                self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {e}")

    async def send_violation_alert(
        self,
        model_id: str,
        model_name: str,
        violation: Dict[str, Any],
        recipients: List[str],
    ) -> Dict[str, Any]:
        """
        Convenience method for sending violation alerts.

        Args:
            model_id: ID of the AI model
            model_name: Name of the AI model
            violation: Violation details
            recipients: List of recipient IDs
        """
        severity = violation.get("severity", "medium")
        priority_map = {
            "critical": NotificationPriority.CRITICAL,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.MEDIUM,
            "low": NotificationPriority.LOW,
            "informational": NotificationPriority.LOW,
        }

        notification = ComplianceNotification(
            title=f"Compliance Violation: {violation.get('title', 'Policy Violation')}",
            message=violation.get("description", "A compliance violation has been detected."),
            priority=priority_map.get(severity, NotificationPriority.MEDIUM),
            alert_type="violation",
            model_id=model_id,
            model_name=model_name,
            regulation=violation.get("regulation"),
            data=violation,
            recipients=recipients,
        )

        return await self.send_notification(notification)

    async def send_threshold_breach_alert(
        self,
        model_id: str,
        model_name: str,
        metric: str,
        value: float,
        threshold: float,
        recipients: List[str],
        regulation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method for threshold breach alerts.

        Args:
            model_id: ID of the AI model
            model_name: Name of the AI model
            metric: Name of the metric that breached
            value: Current value
            threshold: Threshold that was breached
            recipients: List of recipient IDs
            regulation: Optional regulation framework
        """
        breach_pct = abs(value - threshold) / threshold * 100 if threshold != 0 else 100

        # Higher breach = higher priority
        if breach_pct >= 50:
            priority = NotificationPriority.CRITICAL
        elif breach_pct >= 25:
            priority = NotificationPriority.HIGH
        elif breach_pct >= 10:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW

        notification = ComplianceNotification(
            title=f"Threshold Breach: {metric}",
            message=(
                f"The metric '{metric}' has breached its threshold.\n\n"
                f"Current Value: {value:.2f}\n"
                f"Threshold: {threshold:.2f}\n"
                f"Breach: {breach_pct:.1f}%"
            ),
            priority=priority,
            alert_type="threshold_breach",
            model_id=model_id,
            model_name=model_name,
            regulation=regulation,
            data={
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "breach_percentage": breach_pct,
            },
            recipients=recipients,
        )

        return await self.send_notification(notification)

    async def send_certification_expiry_alert(
        self,
        certification_name: str,
        expiry_date: datetime,
        days_remaining: int,
        recipients: List[str],
        regulation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send alert for upcoming certification expiry.

        Args:
            certification_name: Name of the certification
            expiry_date: Expiry date
            days_remaining: Days until expiry
            recipients: List of recipient IDs
            regulation: Optional regulation framework
        """
        # Priority based on urgency
        if days_remaining <= 7:
            priority = NotificationPriority.CRITICAL
        elif days_remaining <= 30:
            priority = NotificationPriority.HIGH
        elif days_remaining <= 60:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW

        notification = ComplianceNotification(
            title=f"Certification Expiring: {certification_name}",
            message=(
                f"The certification '{certification_name}' will expire in {days_remaining} days.\n\n"
                f"Expiry Date: {expiry_date.strftime('%Y-%m-%d')}\n\n"
                "Please initiate renewal process to maintain compliance."
            ),
            priority=priority,
            alert_type="certification_expiry",
            regulation=regulation,
            data={
                "certification_name": certification_name,
                "expiry_date": expiry_date.isoformat(),
                "days_remaining": days_remaining,
            },
            recipients=recipients,
        )

        return await self.send_notification(notification)

    def get_delivery_history(
        self,
        notification_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        channel: Optional[NotificationChannel] = None,
        status: Optional[DeliveryStatus] = None,
        limit: int = 100,
    ) -> List[DeliveryResult]:
        """
        Get delivery history with optional filters.

        Args:
            notification_id: Filter by notification ID
            recipient_id: Filter by recipient ID
            channel: Filter by channel
            status: Filter by status
            limit: Maximum results to return

        Returns:
            List of matching delivery results
        """
        results = self._delivery_results.copy()

        if notification_id:
            results = [r for r in results if r.notification_id == notification_id]
        if recipient_id:
            results = [r for r in results if r.recipient_id == recipient_id]
        if channel:
            results = [r for r in results if r.channel == channel]
        if status:
            results = [r for r in results if r.status == status]

        return results[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get notification service statistics."""
        results = self._delivery_results

        status_counts = defaultdict(int)
        channel_counts = defaultdict(int)

        for result in results:
            status_counts[result.status.value] += 1
            channel_counts[result.channel.value] += 1

        return {
            "total_notifications": len(results),
            "queue_size": self._queue.qsize(),
            "low_priority_batch_size": len(self._low_priority_batch),
            "worker_running": self._running,
            "registered_recipients": len(self.recipients),
            "registered_providers": list(self.providers.keys()),
            "mock_mode": self.mock_mode,
            "status_breakdown": dict(status_counts),
            "channel_breakdown": dict(channel_counts),
        }


# Global service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(
    config: Optional[Dict[str, Any]] = None,
    mock_mode: bool = True,
) -> NotificationService:
    """
    Get the global notification service instance.

    Args:
        config: Optional configuration (only used on first call)
        mock_mode: If True, providers will log instead of sending

    Returns:
        NotificationService instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(config=config, mock_mode=mock_mode)
    return _notification_service


def reset_notification_service() -> None:
    """Reset the global notification service instance (for testing)."""
    global _notification_service
    _notification_service = None
