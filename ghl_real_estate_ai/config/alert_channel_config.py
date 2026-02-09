"""
Alert Channel Configuration Loader

Loads alert channel configuration from YAML file and environment variables.
Supports email (SMTP), Slack webhooks, and custom webhooks (PagerDuty/Opsgenie).

Usage:
    from config.alert_channel_config import AlertChannelConfig

    config = AlertChannelConfig.load()
    if config.email.enabled:
        print(f"SMTP Host: {config.email.smtp.host}")
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    """SMTP configuration for email alerts."""

    host: str = "localhost"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    connection_timeout: int = 10


@dataclass
class EmailConfig:
    """Email alert channel configuration."""

    enabled: bool = False
    provider: str = "smtp"
    smtp: SMTPConfig = field(default_factory=SMTPConfig)
    from_address: str = "alerts@enterprisehub.com"
    from_name: str = "Jorge Bot Alerts"
    reply_to: str = ""
    recipients: str = ""

    def get_recipients_list(self) -> List[str]:
        """Get recipients as a list."""
        if not self.recipients:
            return []
        return [r.strip() for r in self.recipients.split(",") if r.strip()]


@dataclass
class SlackConfig:
    """Slack webhook configuration."""

    enabled: bool = False
    webhook_url: str = ""
    channel: str = "#jorge-alerts"
    username: str = "Jorge Bot Alert"
    icon_emoji: str = ":rotating_light:"
    timeout: int = 10


@dataclass
class WebhookEndpointConfig:
    """Custom webhook endpoint configuration."""

    name: str = ""
    url: str = ""
    type: str = "custom"
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class WebhookConfig:
    """Custom webhook configuration for PagerDuty/Opsgenie."""

    enabled: bool = False
    endpoints: List[WebhookEndpointConfig] = field(default_factory=list)
    timeout: int = 30
    verify_ssl: bool = True


@dataclass
class AlertChannelConfig:
    """Main alert channel configuration."""

    enabled: bool = True
    environment: str = "development"
    service_name: str = "Jorge Bot"
    email: EmailConfig = field(default_factory=EmailConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AlertChannelConfig":
        """Load configuration from YAML file and environment variables.

        Args:
            config_path: Optional path to config file. Defaults to alert_channels.yaml.

        Returns:
            AlertChannelConfig instance.
        """
        if config_path is None:
            # Default to alert_channels.yaml in config directory
            config_path = os.environ.get(
                "ALERT_CHANNELS_CONFIG_PATH", str(Path(__file__).parent / "alert_channels.yaml")
            )

        config = cls._load_from_file(config_path)
        config._apply_env_overrides()

        logger.info(
            "AlertChannelConfig loaded: email=%s, slack=%s, webhook=%s",
            config.email.enabled,
            config.slack.enabled,
            config.webhook.enabled,
        )

        return config

    @classmethod
    def _load_from_file(cls, config_path: str) -> "AlertChannelConfig":
        """Load configuration from YAML file."""
        path = Path(config_path)

        if not path.exists():
            logger.warning("Alert config file not found: %s", config_path)
            return cls()

        try:
            with open(path, "r") as f:
                raw_config = yaml.safe_load(f)
        except Exception as e:
            logger.error("Failed to parse alert config: %s", e)
            return cls()

        if not raw_config:
            return cls()

        # Parse alert settings
        alerting = raw_config.get("alerting", {})

        # Parse email config
        email_raw = raw_config.get("email", {})
        email_config = EmailConfig(
            enabled=email_raw.get("enabled", False),
            provider=email_raw.get("provider", "smtp"),
            from_address=email_raw.get("from_address", "alerts@enterprisehub.com"),
            from_name=email_raw.get("from_name", "Jorge Bot Alerts"),
            reply_to=email_raw.get("reply_to", ""),
            recipients=email_raw.get("recipients", ""),
        )

        # Parse SMTP config
        smtp_raw = email_raw.get("smtp", {})
        email_config.smtp = SMTPConfig(
            host=smtp_raw.get("host", "localhost"),
            port=smtp_raw.get("port", 587),
            username=smtp_raw.get("username", ""),
            password=smtp_raw.get("password", ""),
            use_tls=smtp_raw.get("use_tls", True),
            connection_timeout=smtp_raw.get("connection_timeout", 10),
        )

        # Parse Slack config
        slack_raw = raw_config.get("slack", {})
        slack_config = SlackConfig(
            enabled=slack_raw.get("enabled", False),
            webhook_url=slack_raw.get("webhook", {}).get("url", ""),
            channel=slack_raw.get("channel", "#jorge-alerts"),
            username=slack_raw.get("username", "Jorge Bot Alert"),
            icon_emoji=slack_raw.get("icon_emoji", ":rotating_light:"),
            timeout=slack_raw.get("webhook", {}).get("timeout", 10),
        )

        # Parse webhook config
        webhook_raw = raw_config.get("webhook", {})
        webhook_config = WebhookConfig(
            enabled=webhook_raw.get("enabled", False),
            timeout=webhook_raw.get("request", {}).get("timeout", 30),
            verify_ssl=webhook_raw.get("request", {}).get("verify_ssl", True),
        )

        # Parse webhook endpoints
        for endpoint_raw in webhook_raw.get("endpoints", []):
            endpoint = WebhookEndpointConfig(
                name=endpoint_raw.get("name", ""),
                url=endpoint_raw.get("url", ""),
                type=endpoint_raw.get("type", "custom"),
                headers=endpoint_raw.get("headers", {}),
            )
            webhook_config.endpoints.append(endpoint)

        return cls(
            enabled=alerting.get("enabled", True),
            environment=alerting.get("environment", "development"),
            service_name=alerting.get("service_name", "Jorge Bot"),
            email=email_config,
            slack=slack_config,
            webhook=webhook_config,
        )

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Email overrides
        email_enabled = os.environ.get("ALERT_EMAIL_ENABLED", "").lower()
        if email_enabled in ("true", "1", "yes"):
            self.email.enabled = True

        if "ALERT_EMAIL_SMTP_HOST" in os.environ:
            self.email.smtp.host = os.environ["ALERT_EMAIL_SMTP_HOST"]

        smtp_port = os.environ.get("ALERT_EMAIL_SMTP_PORT", "")
        if smtp_port:
            self.email.smtp.port = int(smtp_port)

        if "ALERT_EMAIL_SMTP_USER" in os.environ:
            self.email.smtp.username = os.environ["ALERT_EMAIL_SMTP_USER"]

        if "ALERT_EMAIL_SMTP_PASSWORD" in os.environ:
            self.email.smtp.password = os.environ["ALERT_EMAIL_SMTP_PASSWORD"]

        if "ALERT_EMAIL_FROM" in os.environ:
            self.email.from_address = os.environ["ALERT_EMAIL_FROM"]

        if "ALERT_EMAIL_TO" in os.environ:
            self.email.recipients = os.environ["ALERT_EMAIL_TO"]

        # Slack overrides
        slack_enabled = os.environ.get("ALERT_SLACK_ENABLED", "").lower()
        if slack_enabled in ("true", "1", "yes"):
            self.slack.enabled = True

        if "ALERT_SLACK_WEBHOOK_URL" in os.environ:
            self.slack.webhook_url = os.environ["ALERT_SLACK_WEBHOOK_URL"]

        if "ALERT_SLACK_CHANNEL" in os.environ:
            self.slack.channel = os.environ["ALERT_SLACK_CHANNEL"]

        # Webhook overrides
        webhook_enabled = os.environ.get("ALERT_WEBHOOK_ENABLED", "").lower()
        if webhook_enabled in ("true", "1", "yes"):
            self.webhook.enabled = True

        if "ALERT_WEBHOOK_URL" in os.environ:
            self.webhook.endpoints = [
                WebhookEndpointConfig(
                    name="custom",
                    url=os.environ["ALERT_WEBHOOK_URL"],
                    type="custom",
                    headers=self._parse_webhook_headers(),
                )
            ]

        if "ALERT_WEBHOOK_PAGERDUTY_URL" in os.environ:
            self.webhook.endpoints.append(
                WebhookEndpointConfig(
                    name="pagerduty",
                    url=os.environ["ALERT_WEBHOOK_PAGERDUTY_URL"],
                    type="pagerduty",
                    headers={
                        "Authorization": f"Bearer {os.environ.get('ALERT_WEBHOOK_PAGERDUTY_API_KEY', '')}",
                        "Content-Type": "application/json",
                    },
                )
            )

        if "ALERT_WEBHOOK_OPSGENIE_URL" in os.environ:
            self.webhook.endpoints.append(
                WebhookEndpointConfig(
                    name="opsgenie",
                    url=os.environ["ALERT_WEBHOOK_OPSGENIE_URL"],
                    type="opsgenie",
                    headers={
                        "Authorization": f"Bearer {os.environ.get('ALERT_WEBHOOK_OPSGENIE_API_KEY', '')}",
                        "Content-Type": "application/json",
                    },
                )
            )

    def _parse_webhook_headers(self) -> Dict[str, str]:
        """Parse webhook headers from environment variable."""
        headers_str = os.environ.get("ALERT_WEBHOOK_HEADERS", '{"Content-Type": "application/json"}')
        try:
            return json.loads(headers_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse ALERT_WEBHOOK_HEADERS, using defaults")
            return {"Content-Type": "application/json"}

    def get_webhook_endpoint(self, endpoint_type: str) -> Optional[WebhookEndpointConfig]:
        """Get a webhook endpoint by type."""
        for endpoint in self.webhook.endpoints:
            if endpoint.type == endpoint_type:
                return endpoint
        return None


# Convenience function for loading config
def load_alert_config(config_path: Optional[str] = None) -> AlertChannelConfig:
    """Load alert channel configuration."""
    return AlertChannelConfig.load(config_path)
