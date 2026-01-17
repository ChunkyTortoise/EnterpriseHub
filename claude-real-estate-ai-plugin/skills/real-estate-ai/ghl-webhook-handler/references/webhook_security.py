"""
GHL Webhook Security Patterns
Extracted from production real estate webhook service
"""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


class WebhookSecurityManager:
    """
    Manages webhook security verification and rate limiting.

    Based on patterns proven in production real estate systems.
    """

    def __init__(self, webhook_secret: str, rate_limit_per_minute: int = 60):
        self.webhook_secret = webhook_secret
        self.rate_limit = rate_limit_per_minute
        self.request_counts: Dict[str, list] = {}

    def verify_webhook_signature(self, request: Request, body: bytes) -> bool:
        """
        Verify GHL webhook signature for security.

        Critical for preventing webhook spoofing and ensuring
        requests actually come from GoHighLevel.
        """
        if not self.webhook_secret:
            logger.warning("GHL_WEBHOOK_SECRET not set - skipping verification in dev mode")
            return True

        signature = request.headers.get("X-GHL-Signature", "")
        if not signature:
            logger.error("Missing webhook signature header")
            return False

        # Compute expected signature
        computed = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, computed)

    def check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client is within rate limits.

        Prevents abuse while allowing legitimate webhook traffic.
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Clean old requests
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                req_time for req_time in self.request_counts[client_ip]
                if req_time > cutoff
            ]
        else:
            self.request_counts[client_ip] = []

        # Check current count
        if len(self.request_counts[client_ip]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            return False

        # Record this request
        self.request_counts[client_ip].append(now)
        return True

    def validate_payload(self, payload: Dict) -> bool:
        """
        Validate webhook payload structure.

        Ensures required fields are present before processing.
        """
        required_fields = ["contactId", "locationId"]

        for field in required_fields:
            if not payload.get(field):
                logger.error(f"Missing required field: {field}")
                return False

        # Additional validation
        contact_id = payload.get("contactId", "")
        if len(contact_id) < 10:  # GHL contact IDs are typically longer
            logger.error(f"Invalid contact ID format: {contact_id}")
            return False

        return True

    def sanitize_payload(self, payload: Dict) -> Dict:
        """
        Sanitize webhook payload to prevent injection attacks.

        Removes potentially dangerous content while preserving data.
        """
        # Remove HTML/script tags from string fields
        import re
        html_pattern = re.compile(r'<[^>]+>')

        def clean_string(value):
            if isinstance(value, str):
                # Remove HTML tags
                cleaned = html_pattern.sub('', value)
                # Remove control characters except newlines/tabs
                cleaned = ''.join(char for char in cleaned
                                if ord(char) >= 32 or char in '\n\t')
                return cleaned.strip()
            return value

        # Recursively clean the payload
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [clean_dict(item) for item in d]
            else:
                return clean_string(d)

        return clean_dict(payload)


class WebhookErrorHandler:
    """
    Handles webhook processing errors with appropriate responses.
    """

    @staticmethod
    def handle_security_error(error_type: str) -> HTTPException:
        """Return appropriate error for security violations."""
        error_responses = {
            "invalid_signature": HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            ),
            "rate_limit": HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            ),
            "invalid_payload": HTTPException(
                status_code=400,
                detail="Invalid payload structure"
            ),
            "missing_secret": HTTPException(
                status_code=500,
                detail="Webhook configuration error"
            )
        }

        return error_responses.get(error_type, HTTPException(
            status_code=400,
            detail="Webhook processing error"
        ))

    @staticmethod
    def log_security_event(event_type: str, details: Dict):
        """Log security events for monitoring and compliance."""
        logger.warning(f"Security event: {event_type}", extra={
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        })


# Usage patterns from production system
"""
# Initialize security manager
security = WebhookSecurityManager(
    webhook_secret=os.getenv("GHL_WEBHOOK_SECRET"),
    rate_limit_per_minute=60
)

# In webhook endpoint
@app.post("/webhook/ghl")
async def handle_webhook(request: Request):
    client_ip = request.client.host
    body = await request.body()

    # Rate limiting
    if not security.check_rate_limit(client_ip):
        raise WebhookErrorHandler.handle_security_error("rate_limit")

    # Signature verification
    if not security.verify_webhook_signature(request, body):
        WebhookErrorHandler.log_security_event("invalid_signature", {
            "ip": client_ip,
            "headers": dict(request.headers)
        })
        raise WebhookErrorHandler.handle_security_error("invalid_signature")

    # Parse and validate payload
    try:
        payload = await request.json()
    except Exception:
        raise WebhookErrorHandler.handle_security_error("invalid_payload")

    if not security.validate_payload(payload):
        raise WebhookErrorHandler.handle_security_error("invalid_payload")

    # Sanitize before processing
    clean_payload = security.sanitize_payload(payload)

    # Process webhook...
"""