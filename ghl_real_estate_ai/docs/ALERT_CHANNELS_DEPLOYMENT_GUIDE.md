# Alert Channels Deployment Guide

This guide covers the configuration and deployment of alert notification channels for Jorge Bot.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Configuration](#configuration)
   - [Email (SMTP)](#email-smtp)
   - [Slack Webhook](#slack-webhook)
   - [Custom Webhooks](#custom-webhooks)
4. [Testing](#testing)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## Overview

Jorge Bot supports three alert notification channels:

| Channel | Purpose | Use Case |
|---------|---------|----------|
| **Email** | SMTP-based email notifications | Primary notifications, on-call rotation |
| **Slack** | Slack webhook messages | Real-time team alerts, incident channels |
| **Webhook** | Custom HTTP webhooks | PagerDuty, Opsgenie, custom integrations |

---

## Prerequisites

Before configuring alert channels, ensure:

1. **Jorge Bot v8.1+** is installed
2. **Python 3.9+** with dependencies:
   ```bash
   pip install aiohttp pyyaml
   ```
3. **Environment variables** configured in `.env`
4. **Network access** to SMTP servers, Slack, and webhook endpoints

---

## Configuration

### Email (SMTP)

#### Environment Variables

Add to your `.env` file:

```bash
# Enable/disable email alerts
ALERT_EMAIL_ENABLED=true

# SMTP Server Configuration
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com          # Your SMTP server
ALERT_EMAIL_SMTP_PORT=587                       # Port (587 for TLS, 465 for SSL)
ALERT_EMAIL_SMTP_USER=your-email@gmail.com     # SMTP username
ALERT_EMAIL_SMTP_PASSWORD=your-app-password   # App-specific password

# Email Content
ALERT_EMAIL_FROM=alerts@yourdomain.com         # From address
ALERT_EMAIL_FROM_NAME="Jorge Bot Alerts"       # From name
ALERT_EMAIL_REPLY_TO=admin@yourdomain.com      # Reply-to address

# Recipients (comma-separated)
ALERT_EMAIL_TO=admin@yourdomain.com,ops@yourdomain.com
```

#### Common SMTP Providers

| Provider | Host | Port | Notes |
|----------|------|------|-------|
| Gmail | `smtp.gmail.com` | 587 | Requires app password |
| Outlook | `smtp-mail.outlook.com` | 587 | Use Microsoft account |
| Office 365 | `smtp.office365.com` | 587 | Exchange Online |
| SendGrid | `smtp.sendgrid.net` | 587 | Use API key as password |
| AWS SES | `email-smtp.us-east-1.amazonaws.com` | 587 | SMTP credentials from SES |

#### Gmail App Password Setup

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate password for "Mail" app
5. Use generated password in `ALERT_EMAIL_SMTP_PASSWORD`

---

### Slack Webhook

#### Environment Variables

```bash
# Enable/disable Slack alerts
ALERT_SLACK_ENABLED=true

# Webhook URL (required)
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Channel Configuration
ALERT_SLACK_CHANNEL=#jorge-alerts           # Default channel
ALERT_SLACK_USERNAME="Jorge Bot Alert"       # Bot username
ALERT_SLACK_ICON_EMOJI=:rotating_light:     # Bot icon
```

#### Setting Up Slack Webhook

1. **Create Slack App**:
   - Go to [Slack API](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name: "Jorge Bot Alerts"
   - Select workspace

2. **Enable Incoming Webhooks**:
   - Go to "Incoming Webhooks" in sidebar
   - Toggle "Activate Incoming Webhooks" to ON
   - Click "Add New Webhook to Workspace"
   - Select channel (e.g., #jorge-alerts)
   - Copy webhook URL

3. **Configure Bot**:
   - Copy webhook URL to `ALERT_SLACK_WEBHOOK_URL`

#### Sample Slack Message

```
🚨 [CRITICAL] sla_violation

Description:
P95 latency exceeds SLA target (Lead: 2000ms, Buyer/Seller: 2500ms)

Details:
Error Rate: 6.5%
Cache Hit Rate: 45%
Blocked Handoffs (1h): 12

Alert ID: abc12345
Environment: PRODUCTION
Time: 2026-02-07T11:30:00Z
```

---

### Custom Webhooks

#### Environment Variables

```bash
# Enable/disable custom webhooks
ALERT_WEBHOOK_ENABLED=true

# Generic Webhook
ALERT_WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
ALERT_WEBHOOK_HEADERS='{"Authorization": "Bearer YOUR_TOKEN", "Content-Type": "application/json"}'

# PagerDuty Integration
ALERT_WEBHOOK_PAGERDUTY_URL=https://events.pagerduty.com/v2/enqueue
ALERT_WEBHOOK_PAGERDUTY_API_KEY=your-pagerduty-integration-key

# OpsGenie Integration
ALERT_WEBHOOK_OPSGENIE_URL=https://api.opsgenie.com/v2/alerts
ALERT_WEBHOOK_OPSGENIE_API_KEY=your-opsgenie-api-key
```

#### PagerDuty Setup

1. **Create PagerDuty Integration**:
   - Go to Configuration → Integrations
   - Click "Add Integration"
   - Select "Events API v2"
   - Copy integration key

2. **Configure Alert Routing** (optional):
   - Create Service for Jorge Bot
   - Add escalation policy
   - Configure notification rules

#### OpsGenie Setup

1. **Create OpsGenie API Key**:
   - Go to Settings → API Key Management
   - Click "Add New API Key"
   - Copy API key

2. **Configure Alert Rules** (optional):
   - Create Alert policy
   - Configure notification rules

#### Webhook Payload Format

**Generic Webhook**:
```json
{
  "version": "1.0",
  "type": "alert",
  "timestamp": "2026-02-07T11:30:00Z",
  "service": "jorge-bot",
  "environment": "production",
  "alert": {
    "id": "abc12345",
    "rule_name": "sla_violation",
    "severity": "critical",
    "message": "P95 latency exceeded",
    "status": "firing"
  },
  "metrics": {
    "error_rate": 0.065,
    "cache_hit_rate": 0.45
  }
}
```

**PagerDuty**:
```json
{
  "routing_key": "YOUR_INTEGRATION_KEY",
  "event_action": "trigger",
  "dedup_key": "jorge_sla_violation_123456",
  "payload": {
    "summary": "[CRITICAL] sla_violation - Jorge Bot Alert",
    "severity": "critical",
    "source": "jorge-bot-production",
    "component": "jorge-bot",
    "custom_details": {
      "alert_id": "abc12345",
      "rule_name": "sla_violation"
    }
  }
}
```

---

## Testing

### Run All Channel Tests

```bash
cd /path/to/EnterpriseHub

# Test all channels (mock mode)
python ghl_real_estate_ai/tests/jorge/test_all_channels.py --mock

# Test specific channel
python ghl_real_estate_ai/tests/jorge/test_smtp_email.py --mock
python ghl_real_estate_ai/tests/jorge/test_slack_webhook.py --mock
python ghl_real_estate_ai/tests/jorge/test_webhook.py --mock
```

### Live Test (Send Actual Notifications)

```bash
# CAUTION: Will send real notifications
python ghl_real_estate_ai/tests/jorge/test_all_channels.py --no-mock
```

### Expected Test Output

```
============================================================
COMPREHENSIVE ALERT CHANNEL TESTS
============================================================
Mode: MOCK
Channels: all

============================================================
TESTING: Email (SMTP) Configuration
============================================================
  ✓ ALERT_EMAIL_SMTP_HOST: smtp.gmail.com
  ✓ ALERT_EMAIL_SMTP_PORT: 587
  ✓ ALERT_EMAIL_FROM: alerts@yourdomain.com
  ✓ ALERT_EMAIL_TO: admin@yourdomain.com
  ✓ ALERT_EMAIL_SMTP_USER: your-email@gmail.com

============================================================
TESTING: Alert Rules Configuration
============================================================
  Found 7 configured alert rules:
    ✓ sla_violation (severity=critical, cooldown=300s)
    ✓ high_error_rate (severity=critical, cooldown=300s)
    ✓ low_cache_hit_rate (severity=warning, cooldown=600s)
    ...

============================================================
FINAL SUMMARY
============================================================

CONFIG:
  Passed: 8
  Failed: 0

...

============================================================
✅ ALL TESTS PASSED
============================================================
```

---

## Troubleshooting

### Email Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Check SMTP host/port, firewall |
| "Authentication failed" | Verify username/app password |
| "Sender address rejected" | Use verified sender domain |
| No emails received | Check spam folder, verify recipients |

### Slack Issues

| Issue | Solution |
|-------|----------|
| "Webhook URL invalid" | Re-copy webhook URL from Slack |
| "Channel not found" | Verify channel exists, bot has access |
| Messages not appearing | Check channel permissions |

### Webhook Issues

| Issue | Solution |
|-------|----------|
| "Connection timeout" | Check endpoint URL, network access |
| "401 Unauthorized" | Verify API key/token |
| "429 Too Many Requests" | Rate limiting - increase cooldown |
| PagerDuty not triggering | Verify integration key, event action |

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Configuration

```python
from ghl_real_estate_ai.config.alert_channel_config import AlertChannelConfig

config = AlertChannelConfig.load()
print(f"Email enabled: {config.email.enabled}")
print(f"Slack enabled: {config.slack.enabled}")
print(f"Webhook enabled: {config.webhook.enabled}")
```

---

## Best Practices

### 1. Use Separate Channels for Different Severities

```python
# In alerting_service.py - Example customization
rule.channels = ["email"]  # Critical: email only
rule.channels = ["slack"]  # Warning: slack only
rule.channels = ["email", "slack"]  # Both
```

### 2. Set Appropriate Cooldowns

| Alert Type | Recommended Cooldown |
|------------|---------------------|
| Critical | 5 minutes (300s) |
| Warning | 10 minutes (600s) |
| Info | 30 minutes (1800s) |

### 3. Use Environment-Specific Channels

```bash
# Development
ALERT_SLACK_CHANNEL=#dev-alerts

# Production  
ALERT_SLACK_CHANNEL=#jorge-alerts-prod
```

### 4. Monitor Alert Volume

Track alert volume to avoid fatigue:

```python
# Log alert counts
logger.info(f"Alerts triggered: {len(triggered)}")
```

### 5. Rotate Credentials

- Rotate SMTP passwords quarterly
- Rotate webhook API keys bi-annually
- Use secrets management in production

### 6. Test in Staging First

Always test alert configuration in staging before production:

```bash
ALERT_ENVIRONMENT=staging
ALERT_SLACK_CHANNEL=#staging-alerts
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/alert_channels.yaml` | Main alert configuration |
| `config/alert_channel_config.py` | Configuration loader |
| `config/templates/email_template.j2` | Email alert template |
| `config/templates/slack_template.j2` | Slack message template |
| `config/templates/webhook_template.j2` | Webhook payload template |

---

## Support

- **Documentation**: See [Alerting Service](../services/jorge/alerting_service.py)
- **Issues**: Report via GitHub issues
- **Logs**: Check application logs for error details

---

## Changelog

| Version | Date | Changes |
|----------|------|---------|
| 8.1 | Feb 2026 | Initial alert channel implementation |
| 8.1.1 | Feb 2026 | Added PagerDuty/Opsgenie support |
| 8.1.2 | Feb 2026 | Added template-based rendering |
