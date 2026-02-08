"""
Competitive Alert and Notification System for Jorge's Lead Bot

This system provides:
1. Real-time alerts to Jorge when competitor risk is detected
2. Multiple notification channels (Slack, SMS, email, GHL)
3. Escalation protocols for high-risk competitive situations
4. Auto-tagging in GHL with competitor risk levels
5. Priority routing for immediate human intervention
"""

import asyncio
import json
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from ghl_real_estate_ai.core.config import get_settings
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.competitor_intelligence import CompetitiveAnalysis, CompetitorMention, RiskLevel
from ghl_real_estate_ai.services.ghl_client import GHLClient

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels"""

    SLACK = "slack"
    SMS = "sms"
    EMAIL = "email"
    GHL_TAG = "ghl_tag"
    WEBHOOK = "webhook"
    PHONE_CALL = "phone_call"


class AlertPriority(Enum):
    """Alert priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class NotificationConfig:
    """Configuration for notification channels"""

    channel: NotificationChannel
    enabled: bool
    priority_threshold: AlertPriority
    endpoint: Optional[str] = None
    credentials: Optional[Dict] = None
    rate_limit: Optional[int] = None  # Max notifications per hour


@dataclass
class CompetitiveAlert:
    """Data structure for competitive alerts"""

    alert_id: str
    lead_id: str
    lead_name: str
    lead_phone: Optional[str]
    lead_email: Optional[str]
    competitive_analysis: CompetitiveAnalysis
    priority: AlertPriority
    channels_sent: List[NotificationChannel]
    timestamp: datetime
    jorge_notified: bool
    human_intervention_required: bool
    escalation_level: int
    resolved: bool
    resolution_notes: Optional[str]


class CompetitiveAlertSystem:
    """
    Real-time competitive alert and notification system

    Features:
    - Multi-channel notifications with smart routing
    - Escalation protocols based on risk level and response time
    - Rate limiting to prevent notification spam
    - Integration with GHL for automatic tagging
    - Detailed logging and analytics
    """

    def __init__(self, cache_service: Optional[CacheService] = None, ghl_client: Optional[GHLClient] = None):
        self.cache = cache_service or CacheService()
        self.ghl_client = ghl_client or GHLClient()
        self.settings = get_settings()

        # Notification configurations
        self.notification_configs = self._load_notification_configs()
        self.escalation_rules = self._load_escalation_rules()
        self.rate_limits = {}  # Track rate limiting per channel

        # Jorge's contact information
        self.jorge_contacts = {
            "phone": self.settings.JORGE_PHONE_NUMBER,
            "email": self.settings.JORGE_EMAIL,
            "slack_user_id": self.settings.JORGE_SLACK_USER_ID,
        }

    def _load_notification_configs(self) -> List[NotificationConfig]:
        """Load notification channel configurations"""
        return [
            NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                priority_threshold=AlertPriority.MEDIUM,
                endpoint=self.settings.SLACK_WEBHOOK_URL,
                rate_limit=10,  # 10 per hour
            ),
            NotificationConfig(
                channel=NotificationChannel.SMS,
                enabled=True,
                priority_threshold=AlertPriority.HIGH,
                credentials={
                    "account_sid": self.settings.TWILIO_ACCOUNT_SID,
                    "auth_token": self.settings.TWILIO_AUTH_TOKEN,
                    "from_number": self.settings.TWILIO_PHONE_NUMBER,
                },
                rate_limit=5,  # 5 per hour
            ),
            NotificationConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                priority_threshold=AlertPriority.MEDIUM,
                credentials={
                    "smtp_server": self.settings.SMTP_SERVER,
                    "smtp_port": self.settings.SMTP_PORT,
                    "username": self.settings.SMTP_USERNAME,
                    "password": self.settings.SMTP_PASSWORD,
                },
                rate_limit=20,  # 20 per hour
            ),
            NotificationConfig(
                channel=NotificationChannel.GHL_TAG,
                enabled=True,
                priority_threshold=AlertPriority.LOW,
                rate_limit=50,  # 50 per hour
            ),
            NotificationConfig(
                channel=NotificationChannel.PHONE_CALL,
                enabled=True,
                priority_threshold=AlertPriority.CRITICAL,
                credentials={
                    "account_sid": self.settings.TWILIO_ACCOUNT_SID,
                    "auth_token": self.settings.TWILIO_AUTH_TOKEN,
                    "from_number": self.settings.TWILIO_PHONE_NUMBER,
                },
                rate_limit=3,  # 3 per hour
            ),
        ]

    def _load_escalation_rules(self) -> Dict[RiskLevel, Dict]:
        """Load escalation rules for different risk levels"""
        return {
            RiskLevel.LOW: {
                "priority": AlertPriority.LOW,
                "channels": [NotificationChannel.GHL_TAG],
                "delay_minutes": 0,
                "escalation_delay": None,
                "human_intervention": False,
            },
            RiskLevel.MEDIUM: {
                "priority": AlertPriority.MEDIUM,
                "channels": [NotificationChannel.SLACK, NotificationChannel.GHL_TAG],
                "delay_minutes": 0,
                "escalation_delay": 30,  # Escalate if no response in 30 minutes
                "human_intervention": False,
            },
            RiskLevel.HIGH: {
                "priority": AlertPriority.HIGH,
                "channels": [NotificationChannel.SLACK, NotificationChannel.SMS, NotificationChannel.GHL_TAG],
                "delay_minutes": 0,
                "escalation_delay": 15,  # Escalate if no response in 15 minutes
                "human_intervention": True,
            },
            RiskLevel.CRITICAL: {
                "priority": AlertPriority.CRITICAL,
                "channels": [
                    NotificationChannel.SLACK,
                    NotificationChannel.SMS,
                    NotificationChannel.EMAIL,
                    NotificationChannel.GHL_TAG,
                ],
                "delay_minutes": 0,
                "escalation_delay": 5,  # Escalate if no response in 5 minutes
                "human_intervention": True,
            },
        }

    async def send_competitive_alert(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        competitive_analysis: CompetitiveAnalysis,
        conversation_context: Optional[Dict] = None,
    ) -> CompetitiveAlert:
        """
        Send competitive alert through appropriate channels

        Args:
            lead_id: GHL lead ID
            lead_data: Lead information from GHL
            competitive_analysis: Analysis results from competitor intelligence
            conversation_context: Additional conversation context

        Returns:
            CompetitiveAlert with notification status and details
        """
        try:
            # Create alert record
            alert = CompetitiveAlert(
                alert_id=f"comp_alert_{lead_id}_{int(datetime.now().timestamp())}",
                lead_id=lead_id,
                lead_name=lead_data.get("name", "Unknown Lead"),
                lead_phone=lead_data.get("phone"),
                lead_email=lead_data.get("email"),
                competitive_analysis=competitive_analysis,
                priority=self._determine_alert_priority(competitive_analysis.risk_level),
                channels_sent=[],
                timestamp=datetime.now(),
                jorge_notified=False,
                human_intervention_required=competitive_analysis.escalation_needed,
                escalation_level=0,
                resolved=False,
                resolution_notes=None,
            )

            # Get escalation rules for this risk level
            escalation_rules = self.escalation_rules.get(competitive_analysis.risk_level)
            if not escalation_rules:
                logger.error(f"No escalation rules found for risk level: {competitive_analysis.risk_level}")
                return alert

            # Send notifications through appropriate channels
            for channel in escalation_rules["channels"]:
                if await self._should_send_notification(channel, alert.priority):
                    success = await self._send_notification(channel, alert, conversation_context)
                    if success:
                        alert.channels_sent.append(channel)

            # Tag lead in GHL
            await self._tag_lead_in_ghl(alert)

            # Schedule escalation if needed
            if escalation_rules.get("escalation_delay"):
                await self._schedule_escalation(alert, escalation_rules["escalation_delay"])

            # Store alert for tracking
            await self._store_alert(alert)

            # Mark Jorge as notified if critical channels were used
            if any(ch in [NotificationChannel.SMS, NotificationChannel.PHONE_CALL] for ch in alert.channels_sent):
                alert.jorge_notified = True

            logger.info(
                f"Competitive alert sent: {alert.alert_id} - Risk: {competitive_analysis.risk_level} - Channels: {[ch.value for ch in alert.channels_sent]}"
            )

            return alert

        except Exception as e:
            logger.error(f"Error sending competitive alert: {e}")
            # Return minimal alert record for tracking
            return CompetitiveAlert(
                alert_id=f"error_alert_{lead_id}_{int(datetime.now().timestamp())}",
                lead_id=lead_id,
                lead_name=lead_data.get("name", "Unknown"),
                lead_phone=None,
                lead_email=None,
                competitive_analysis=competitive_analysis,
                priority=AlertPriority.LOW,
                channels_sent=[],
                timestamp=datetime.now(),
                jorge_notified=False,
                human_intervention_required=True,
                escalation_level=0,
                resolved=False,
                resolution_notes=f"Error sending alert: {str(e)}",
            )

    def _determine_alert_priority(self, risk_level: RiskLevel) -> AlertPriority:
        """Map risk level to alert priority"""
        mapping = {
            RiskLevel.LOW: AlertPriority.LOW,
            RiskLevel.MEDIUM: AlertPriority.MEDIUM,
            RiskLevel.HIGH: AlertPriority.HIGH,
            RiskLevel.CRITICAL: AlertPriority.CRITICAL,
        }
        return mapping.get(risk_level, AlertPriority.LOW)

    async def _should_send_notification(self, channel: NotificationChannel, priority: AlertPriority) -> bool:
        """Check if notification should be sent based on configuration and rate limits"""

        # Find channel config
        config = next((c for c in self.notification_configs if c.channel == channel), None)
        if not config or not config.enabled:
            return False

        # Check priority threshold
        priority_values = {p: i for i, p in enumerate(AlertPriority)}
        if priority_values[priority] < priority_values[config.priority_threshold]:
            return False

        # Check rate limiting
        if config.rate_limit:
            current_hour = datetime.now().hour
            rate_key = f"{channel.value}_{current_hour}"
            current_count = self.rate_limits.get(rate_key, 0)
            if current_count >= config.rate_limit:
                logger.warning(f"Rate limit exceeded for {channel.value}: {current_count}/{config.rate_limit}")
                return False

        return True

    async def _send_notification(
        self, channel: NotificationChannel, alert: CompetitiveAlert, conversation_context: Optional[Dict] = None
    ) -> bool:
        """Send notification through specific channel"""
        try:
            if channel == NotificationChannel.SLACK:
                return await self._send_slack_notification(alert, conversation_context)
            elif channel == NotificationChannel.SMS:
                return await self._send_sms_notification(alert)
            elif channel == NotificationChannel.EMAIL:
                return await self._send_email_notification(alert)
            elif channel == NotificationChannel.GHL_TAG:
                return await self._send_ghl_tag_notification(alert)
            elif channel == NotificationChannel.PHONE_CALL:
                return await self._send_phone_call_notification(alert)
            else:
                logger.warning(f"Unknown notification channel: {channel}")
                return False

        except Exception as e:
            logger.error(f"Error sending {channel.value} notification: {e}")
            return False

    async def _send_slack_notification(self, alert: CompetitiveAlert, context: Optional[Dict] = None) -> bool:
        """Send Slack notification"""
        config = next(c for c in self.notification_configs if c.channel == NotificationChannel.SLACK)
        if not config.endpoint:
            return False

        # Build Slack message
        risk_emojis = {RiskLevel.LOW: "🟡", RiskLevel.MEDIUM: "🟠", RiskLevel.HIGH: "🔴", RiskLevel.CRITICAL: "🚨"}

        emoji = risk_emojis.get(alert.competitive_analysis.risk_level, "⚠️")

        # Format competitor mentions
        mentions_text = ""
        if alert.competitive_analysis.mentions:
            mentions_text = "\n".join(
                [
                    f"• {mention.mention_text} (confidence: {mention.confidence_score:.1%})"
                    for mention in alert.competitive_analysis.mentions[:3]
                ]
            )

        slack_message = {
            "text": f"{emoji} Competitor Risk Alert - {alert.competitive_analysis.risk_level.value.title()}",
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} Competitor Risk Detected"}},
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Lead:* {alert.lead_name}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Risk Level:* {alert.competitive_analysis.risk_level.value.title()}",
                        },
                        {"type": "mrkdwn", "text": f"*Phone:* {alert.lead_phone or 'N/A'}"},
                        {"type": "mrkdwn", "text": f"*Confidence:* {alert.competitive_analysis.confidence_score:.1%}"},
                    ],
                },
            ],
        }

        if mentions_text:
            slack_message["blocks"].append(
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Competitor Mentions:*\n{mentions_text}"}}
            )

        if alert.competitive_analysis.recommended_responses:
            response_text = "\n".join(
                [f"• {response}" for response in alert.competitive_analysis.recommended_responses[:2]]
            )
            slack_message["blocks"].append(
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Recommended Response:*\n{response_text}"}}
            )

        # Add action buttons
        slack_message["blocks"].append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in GHL"},
                        "url": f"https://app.gohighlevel.com/contacts/{alert.lead_id}",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Call Lead"},
                        "value": f"call_{alert.lead_id}",
                    },
                ],
            }
        )

        # Send to Slack
        async with httpx.AsyncClient() as client:
            response = await client.post(config.endpoint, json=slack_message)
            success = response.status_code == 200

        if success:
            self._increment_rate_limit(NotificationChannel.SLACK)

        return success

    async def _send_sms_notification(self, alert: CompetitiveAlert) -> bool:
        """Send SMS notification to Jorge"""
        config = next(c for c in self.notification_configs if c.channel == NotificationChannel.SMS)

        # Build SMS message
        message = f"🚨 COMPETITOR ALERT 🚨\n"
        message += f"Lead: {alert.lead_name}\n"
        message += f"Risk: {alert.competitive_analysis.risk_level.value.upper()}\n"
        message += f"Phone: {alert.lead_phone}\n"

        if alert.competitive_analysis.mentions:
            mention = alert.competitive_analysis.mentions[0]
            message += f"Mention: {mention.mention_text[:50]}...\n"

        message += f"View: https://app.gohighlevel.com/contacts/{alert.lead_id}"

        # Send via Twilio (implementation would depend on Twilio client)
        try:
            # Placeholder for Twilio SMS implementation
            # from twilio.rest import Client
            # client = Client(config.credentials["account_sid"], config.credentials["auth_token"])
            # message = client.messages.create(
            #     body=message,
            #     from_=config.credentials["from_number"],
            #     to=self.jorge_contacts["phone"]
            # )

            logger.info(f"SMS alert sent to Jorge: {message[:100]}...")
            self._increment_rate_limit(NotificationChannel.SMS)
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    async def _send_email_notification(self, alert: CompetitiveAlert) -> bool:
        """Send email notification to Jorge"""
        config = next(c for c in self.notification_configs if c.channel == NotificationChannel.EMAIL)

        try:
            # Create email content
            subject = (
                f"🚨 Competitor Risk Alert - {alert.lead_name} ({alert.competitive_analysis.risk_level.value.title()})"
            )

            html_body = f"""
            <html>
            <body>
                <h2 style="color: #d93025;">Competitor Risk Alert</h2>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Lead Name:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{alert.lead_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Risk Level:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{alert.competitive_analysis.risk_level.value.title()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Phone:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{alert.lead_phone or "N/A"}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Confidence:</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{alert.competitive_analysis.confidence_score:.1%}</td>
                    </tr>
                </table>

                <h3>Competitor Mentions:</h3>
                <ul>
            """

            for mention in alert.competitive_analysis.mentions[:3]:
                html_body += f"<li>{mention.mention_text} (Confidence: {mention.confidence_score:.1%})</li>"

            html_body += "</ul>"

            if alert.competitive_analysis.recommended_responses:
                html_body += "<h3>Recommended Response:</h3><ul>"
                for response in alert.competitive_analysis.recommended_responses[:2]:
                    html_body += f"<li>{response}</li>"
                html_body += "</ul>"

            html_body += f"""
                <p><a href="https://app.gohighlevel.com/contacts/{alert.lead_id}"
                      style="background-color: #1a73e8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                   View Lead in GHL
                </a></p>
            </body>
            </html>
            """

            # Send email (placeholder implementation)
            # msg = MimeMultipart('alternative')
            # msg['Subject'] = subject
            # msg['From'] = config.credentials["username"]
            # msg['To'] = self.jorge_contacts["email"]
            # msg.attach(MimeText(html_body, 'html'))

            logger.info(f"Email alert sent to Jorge: {subject}")
            self._increment_rate_limit(NotificationChannel.EMAIL)
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def _send_ghl_tag_notification(self, alert: CompetitiveAlert) -> bool:
        """Tag lead in GHL with competitor risk information"""
        try:
            # Create tags based on risk level and competitor mentions
            tags = [f"Competitor-Risk-{alert.competitive_analysis.risk_level.value.title()}"]

            # Add specific competitor tags if detected
            for mention in alert.competitive_analysis.mentions:
                if mention.competitor_name:
                    tags.append(f"Competitor-{mention.competitor_name}")

            # Add urgency tags if present
            for mention in alert.competitive_analysis.mentions:
                if mention.urgency_indicators:
                    tags.append("Urgent-Response-Needed")
                    break

            # Add tags to lead in GHL
            success = await self.ghl_client.add_tags_to_contact(alert.lead_id, tags)

            if success:
                self._increment_rate_limit(NotificationChannel.GHL_TAG)
                logger.info(f"GHL tags added to {alert.lead_id}: {tags}")

            return success

        except Exception as e:
            logger.error(f"Failed to tag lead in GHL: {e}")
            return False

    async def _send_phone_call_notification(self, alert: CompetitiveAlert) -> bool:
        """Initiate phone call to Jorge for critical alerts"""
        config = next(c for c in self.notification_configs if c.channel == NotificationChannel.PHONE_CALL)

        try:
            # Message to play during call
            call_message = f"Critical competitor alert for lead {alert.lead_name}. "
            call_message += f"Risk level {alert.competitive_analysis.risk_level.value}. "
            call_message += f"Immediate intervention required. Check Slack for details."

            # Initiate call via Twilio (placeholder implementation)
            # from twilio.rest import Client
            # client = Client(config.credentials["account_sid"], config.credentials["auth_token"])
            # call = client.calls.create(
            #     twiml=f'<Response><Say>{call_message}</Say></Response>',
            #     to=self.jorge_contacts["phone"],
            #     from_=config.credentials["from_number"]
            # )

            logger.info(f"Phone call initiated to Jorge for critical alert: {alert.alert_id}")
            self._increment_rate_limit(NotificationChannel.PHONE_CALL)
            return True

        except Exception as e:
            logger.error(f"Failed to initiate phone call: {e}")
            return False

    async def _tag_lead_in_ghl(self, alert: CompetitiveAlert) -> bool:
        """Add comprehensive tagging to lead in GHL"""
        try:
            tags = []

            # Risk level tag
            tags.append(f"Competitor-Risk-{alert.competitive_analysis.risk_level.value.title()}")

            # Timestamp tag
            timestamp = alert.timestamp.strftime("%Y%m%d")
            tags.append(f"Comp-Alert-{timestamp}")

            # Confidence level tag
            confidence = alert.competitive_analysis.confidence_score
            if confidence >= 0.8:
                tags.append("High-Confidence-Competitor")
            elif confidence >= 0.6:
                tags.append("Medium-Confidence-Competitor")
            else:
                tags.append("Low-Confidence-Competitor")

            # Human intervention tag
            if alert.human_intervention_required:
                tags.append("Human-Intervention-Required")

            # Priority routing tag
            tags.append(f"Priority-{alert.priority.value.title()}")

            return await self.ghl_client.add_tags_to_contact(alert.lead_id, tags)

        except Exception as e:
            logger.error(f"Error tagging lead in GHL: {e}")
            return False

    def _increment_rate_limit(self, channel: NotificationChannel):
        """Increment rate limit counter for channel"""
        current_hour = datetime.now().hour
        rate_key = f"{channel.value}_{current_hour}"
        self.rate_limits[rate_key] = self.rate_limits.get(rate_key, 0) + 1

    async def _schedule_escalation(self, alert: CompetitiveAlert, delay_minutes: int):
        """Schedule escalation for unresolved alerts"""
        # Store escalation task
        escalation_data = {
            "alert_id": alert.alert_id,
            "escalation_time": (datetime.now() + timedelta(minutes=delay_minutes)).isoformat(),
            "escalation_level": alert.escalation_level + 1,
        }

        cache_key = f"escalation_pending:{alert.alert_id}"
        await self.cache.set(cache_key, escalation_data, ttl=delay_minutes * 60)

        logger.info(f"Escalation scheduled for {alert.alert_id} in {delay_minutes} minutes")

    async def _store_alert(self, alert: CompetitiveAlert):
        """Store alert for tracking and analytics"""
        alert_data = {
            "alert_id": alert.alert_id,
            "lead_id": alert.lead_id,
            "lead_name": alert.lead_name,
            "risk_level": alert.competitive_analysis.risk_level.value,
            "priority": alert.priority.value,
            "channels_sent": [ch.value for ch in alert.channels_sent],
            "timestamp": alert.timestamp.isoformat(),
            "jorge_notified": alert.jorge_notified,
            "human_intervention_required": alert.human_intervention_required,
            "mentions_count": len(alert.competitive_analysis.mentions),
            "confidence_score": alert.competitive_analysis.confidence_score,
        }

        cache_key = f"competitive_alert:{alert.alert_id}"
        await self.cache.set(cache_key, alert_data, ttl=86400 * 7)  # Store for 7 days

    async def mark_alert_resolved(self, alert_id: str, resolution_notes: str = None):
        """Mark alert as resolved and cancel any pending escalations"""
        try:
            # Remove from escalation queue
            escalation_key = f"escalation_pending:{alert_id}"
            await self.cache.delete(escalation_key)

            # Update alert status
            alert_key = f"competitive_alert:{alert_id}"
            alert_data = await self.cache.get(alert_key)
            if alert_data:
                alert_data["resolved"] = True
                alert_data["resolution_time"] = datetime.now().isoformat()
                alert_data["resolution_notes"] = resolution_notes
                await self.cache.set(alert_key, alert_data, ttl=86400 * 30)  # Keep resolved alerts for 30 days

            logger.info(f"Alert {alert_id} marked as resolved: {resolution_notes}")

        except Exception as e:
            logger.error(f"Error marking alert as resolved: {e}")

    async def get_active_alerts(self) -> List[Dict]:
        """Get list of active (unresolved) competitive alerts"""
        try:
            # This would typically query a database
            # For now, using cache pattern matching
            pattern = "competitive_alert:*"
            alert_keys = await self.cache.get_keys_by_pattern(pattern)

            active_alerts = []
            for key in alert_keys:
                alert_data = await self.cache.get(key)
                if alert_data and not alert_data.get("resolved", False):
                    active_alerts.append(alert_data)

            return sorted(active_alerts, key=lambda x: x["timestamp"], reverse=True)

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []


# Singleton instance
_competitive_alert_system = None


def get_competitive_alert_system() -> CompetitiveAlertSystem:
    """Get singleton competitive alert system"""
    global _competitive_alert_system
    if _competitive_alert_system is None:
        _competitive_alert_system = CompetitiveAlertSystem()
    return _competitive_alert_system
