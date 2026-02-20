"""
GHL Webhook Validators

Signature verification for GoHighLevel webhooks.
Supports HMAC-SHA256 and RSA signature schemes.
"""

import base64
import hashlib
import hmac
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WebhookValidator:
    """
    Webhook signature validator for GHL.
    
    Supports multiple signature schemes:
    - HMAC-SHA256 (standard)
    - RSA-SHA256 (enterprise)
    """

    def __init__(self):
        self.hmac_secret = os.getenv("GHL_WEBHOOK_SECRET")
        self.rsa_public_key = os.getenv("GHL_WEBHOOK_PUBLIC_KEY")
        self.skip_in_dev = os.getenv("GHL_SKIP_SIGNATURE_VERIFICATION", "false").lower() == "true"

    async def validate(
        self,
        payload: bytes,
        signature: Optional[str],
        headers: Dict[str, str],
        scheme: str = "auto"
    ) -> bool:
        """
        Validate webhook signature.
        
        Args:
            payload: Raw request body bytes
            signature: Signature from X-GHL-Signature header
            headers: All request headers
            scheme: 'hmac', 'rsa', or 'auto' to detect
        
        Returns:
            True if signature is valid
        """
        if not signature:
            if self.skip_in_dev:
                logger.warning("Signature missing but allowing (dev mode)")
                return True
            logger.error("No signature provided")
            return False

        # Detect scheme if auto
        if scheme == "auto":
            scheme = self._detect_scheme(signature, headers)

        if scheme == "hmac":
            return await self._validate_hmac(payload, signature)
        elif scheme == "rsa":
            return await self._validate_rsa(payload, signature)
        else:
            logger.error(f"Unknown signature scheme: {scheme}")
            return False

    def _detect_scheme(self, signature: str, headers: Dict[str, str]) -> str:
        """Detect signature scheme from format"""
        # RSA signatures are typically base64 encoded and longer
        if len(signature) > 100 and not signature.startswith("sha256="):
            return "rsa"
        return "hmac"

    async def _validate_hmac(self, payload: bytes, signature: str) -> bool:
        """Validate HMAC-SHA256 signature"""
        if not self.hmac_secret:
            logger.error("HMAC secret not configured")
            return False

        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith("sha256="):
                signature = signature[7:]

            # Compute expected signature
            expected = hmac.new(
                self.hmac_secret.encode("utf-8"),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            is_valid = hmac.compare_digest(expected, signature)
            
            if not is_valid:
                logger.warning(
                    f"HMAC validation failed: expected {expected[:16]}..., "
                    f"got {signature[:16]}..."
                )
            
            return is_valid

        except Exception as e:
            logger.error(f"HMAC validation error: {e}")
            return False

    async def _validate_rsa(self, payload: bytes, signature: str) -> bool:
        """Validate RSA signature (for enterprise accounts)"""
        if not self.rsa_public_key:
            logger.error("RSA public key not configured")
            return False

        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            # Load public key
            public_key = serialization.load_pem_public_key(
                self.rsa_public_key.encode()
            )

            # Decode base64 signature
            signature_bytes = base64.b64decode(signature)

            # Verify
            public_key.verify(
                signature_bytes,
                payload,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            return True

        except Exception as e:
            logger.error(f"RSA validation error: {e}")
            return False

    async def validate_timestamp(
        self,
        timestamp: Optional[str],
        max_age_seconds: int = 300
    ) -> bool:
        """
        Validate webhook timestamp to prevent replay attacks.
        
        Args:
            timestamp: ISO format timestamp from header
            max_age_seconds: Maximum allowed age (default 5 minutes)
        
        Returns:
            True if timestamp is valid and recent
        """
        if not timestamp:
            return True  # Allow if no timestamp

        try:
            from datetime import datetime, timezone

            # Parse timestamp
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + "+00:00"
            
            event_time = datetime.fromisoformat(timestamp)
            now = datetime.now(timezone.utc)
            
            # Calculate age
            age_seconds = (now - event_time).total_seconds()
            
            if age_seconds > max_age_seconds:
                logger.warning(f"Webhook too old: {age_seconds}s > {max_age_seconds}s")
                return False
            
            if age_seconds < -60:  # More than 1 minute in future
                logger.warning(f"Webhook from future: {age_seconds}s")
                return False
            
            return True

        except Exception as e:
            logger.error(f"Timestamp validation error: {e}")
            return True  # Allow on parse error (conservative)


class MultiValidator:
    """
    Multi-layer validation combining signature, timestamp, and source validation.
    """

    def __init__(self):
        self.signature_validator = WebhookValidator()
        self.allowed_ips: Optional[set] = None
        self._load_allowed_ips()

    def _load_allowed_ips(self):
        """Load allowed IP ranges for GHL webhooks"""
        # GHL webhook IPs (update as needed)
        ip_list = os.getenv("GHL_ALLOWED_IPS", "").split(",")
        if ip_list and ip_list[0]:
            self.allowed_ips = set(ip.strip() for ip in ip_list if ip.strip())

    async def validate(
        self,
        payload: bytes,
        signature: Optional[str],
        headers: Dict[str, str],
        client_ip: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Perform full validation.
        
        Returns:
            Dict with 'valid' bool and detailed results
        """
        results = {
            "signature_valid": False,
            "timestamp_valid": False,
            "source_valid": False,
            "valid": False,
            "errors": [],
        }

        # Validate signature
        results["signature_valid"] = await self.signature_validator.validate(
            payload, signature, headers
        )
        if not results["signature_valid"]:
            results["errors"].append("Invalid signature")

        # Validate timestamp
        timestamp = headers.get("X-GHL-Timestamp") or headers.get("x-ghl-timestamp")
        results["timestamp_valid"] = await self.signature_validator.validate_timestamp(timestamp)
        if not results["timestamp_valid"]:
            results["errors"].append("Invalid or expired timestamp")

        # Validate source IP (if configured)
        if self.allowed_ips and client_ip:
            results["source_valid"] = client_ip in self.allowed_ips
            if not results["source_valid"]:
                results["errors"].append(f"IP {client_ip} not in allowed list")
        else:
            results["source_valid"] = True  # Skip if not configured

        # Overall validity
        results["valid"] = (
            results["signature_valid"] and 
            results["timestamp_valid"] and 
            results["source_valid"]
        )

        return results


# Singleton instance
_validator: Optional[WebhookValidator] = None


def get_validator() -> WebhookValidator:
    """Get or create validator singleton"""
    global _validator
    if _validator is None:
        _validator = WebhookValidator()
    return _validator
