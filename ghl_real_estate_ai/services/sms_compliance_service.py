"""
TCPA-compliant SMS management service.
Handles opt-outs, frequency caps, and compliance tracking for Jorge's Real Estate AI.

Features:
- TCPA compliance validation for all SMS sends
- Automatic opt-out processing with audit trails
- Frequency capping (daily/monthly limits)
- Compliance event publishing for monitoring
- Fast Redis-backed opt-out lookup
"""

import asyncio
import hashlib
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class SMSValidationResult:
    """Result of SMS send validation."""
    allowed: bool
    reason: Optional[str] = None
    daily_count: int = 0
    monthly_count: int = 0
    last_sent: Optional[datetime] = None
    compliance_notes: Optional[str] = None

class OptOutReason(Enum):
    """Reasons for SMS opt-out."""
    USER_REQUEST = "user_request"
    STOP_KEYWORD = "stop_keyword"
    COMPLIANCE_VIOLATION = "compliance_violation"
    ADMIN_BLOCK = "admin_block"
    FREQUENCY_ABUSE = "frequency_abuse"

class SMSComplianceService:
    """
    TCPA compliance management for SMS communications.

    Implements industry-standard SMS compliance patterns:
    - Daily limit: 3 messages max
    - Monthly limit: 20 messages max
    - Automatic STOP keyword processing
    - Audit trail for all compliance events
    - Fast Redis-backed validation
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.event_publisher = get_event_publisher()

        # Compliance limits (industry standard)
        self.DAILY_LIMIT = 3
        self.MONTHLY_LIMIT = 20

        # STOP keywords (TCPA standard)
        self.STOP_KEYWORDS = {
            "STOP", "UNSUBSCRIBE", "QUIT", "CANCEL", "END",
            "REMOVE", "HALT", "OPT-OUT", "OPTOUT", "NO", "OFF"
        }

        # Time zones for compliance
        self.BUSINESS_HOURS_START = 8  # 8 AM
        self.BUSINESS_HOURS_END = 21   # 9 PM

    async def validate_sms_send(self, phone_number: str, message_content: str,
                               location_id: Optional[str] = None) -> SMSValidationResult:
        """
        Validate SMS send against all TCPA compliance rules.

        Args:
            phone_number: Target phone number
            message_content: SMS message content
            location_id: GHL location ID for tenant isolation

        Returns:
            SMSValidationResult: Validation result with compliance details
        """
        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone_number(phone_number)

            # Check opt-out status first (critical)
            if await self._is_opted_out(normalized_phone):
                await self._log_compliance_violation(
                    normalized_phone, "attempted_send_to_opted_out", location_id
                )
                return SMSValidationResult(
                    allowed=False,
                    reason="opted_out",
                    compliance_notes="Contact has opted out of SMS communications"
                )

            # Check frequency caps
            daily_count = await self._get_daily_sms_count(normalized_phone)
            monthly_count = await self._get_monthly_sms_count(normalized_phone)

            if daily_count >= self.DAILY_LIMIT:
                await self.event_publisher.publish_sms_frequency_limit_hit(
                    phone_number=normalized_phone,
                    limit_type="daily",
                    current_count=daily_count,
                    limit_value=self.DAILY_LIMIT,
                    location_id=location_id
                )
                return SMSValidationResult(
                    allowed=False,
                    reason="daily_limit_exceeded",
                    daily_count=daily_count,
                    compliance_notes=f"Daily limit of {self.DAILY_LIMIT} messages exceeded"
                )

            if monthly_count >= self.MONTHLY_LIMIT:
                await self.event_publisher.publish_sms_frequency_limit_hit(
                    phone_number=normalized_phone,
                    limit_type="monthly",
                    current_count=monthly_count,
                    limit_value=self.MONTHLY_LIMIT,
                    location_id=location_id
                )
                return SMSValidationResult(
                    allowed=False,
                    reason="monthly_limit_exceeded",
                    monthly_count=monthly_count,
                    compliance_notes=f"Monthly limit of {self.MONTHLY_LIMIT} messages exceeded"
                )

            # Check business hours (optional warning)
            current_hour = datetime.now().hour
            business_hours_compliant = self.BUSINESS_HOURS_START <= current_hour <= self.BUSINESS_HOURS_END

            # Get last sent timestamp
            last_sent = await self._get_last_sent_timestamp(normalized_phone)

            # All checks passed
            return SMSValidationResult(
                allowed=True,
                daily_count=daily_count,
                monthly_count=monthly_count,
                last_sent=last_sent,
                compliance_notes="Outside business hours" if not business_hours_compliant else None
            )

        except Exception as e:
            logger.error(f"Error validating SMS send to {phone_number}: {str(e)}")
            return SMSValidationResult(
                allowed=False,
                reason="validation_error",
                compliance_notes=f"Validation error: {str(e)}"
            )

    async def process_incoming_sms(self, phone_number: str, message_content: str,
                                 location_id: Optional[str] = None) -> Dict[str, any]:
        """
        Process incoming SMS for opt-out keywords and compliance actions.

        Args:
            phone_number: Sender's phone number
            message_content: Incoming message content
            location_id: GHL location ID

        Returns:
            Dict with processing results and actions taken
        """
        try:
            normalized_phone = self._normalize_phone_number(phone_number)
            message_upper = message_content.upper().strip()

            # Check for STOP keywords
            contains_stop = any(keyword in message_upper for keyword in self.STOP_KEYWORDS)

            if contains_stop:
                # Process opt-out immediately
                await self.process_opt_out(
                    phone_number=normalized_phone,
                    reason=OptOutReason.STOP_KEYWORD,
                    message_content=message_content,
                    location_id=location_id
                )

                return {
                    "action": "opt_out_processed",
                    "phone_number": normalized_phone,
                    "method": "stop_keyword",
                    "keywords_detected": [kw for kw in self.STOP_KEYWORDS if kw in message_upper],
                    "timestamp": datetime.now().isoformat()
                }

            # Check for other compliance-related content
            compliance_flags = self._check_compliance_flags(message_content)

            return {
                "action": "message_processed",
                "phone_number": normalized_phone,
                "compliance_flags": compliance_flags,
                "opt_out_status": "not_opted_out",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing incoming SMS from {phone_number}: {str(e)}")
            return {
                "action": "processing_error",
                "phone_number": phone_number,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def process_opt_out(self, phone_number: str, reason: OptOutReason,
                             message_content: Optional[str] = None,
                             location_id: Optional[str] = None):
        """
        Process opt-out request with complete audit trail.

        Args:
            phone_number: Phone number to opt out
            reason: Reason for opt-out
            message_content: Original message content (optional)
            location_id: GHL location ID
        """
        try:
            normalized_phone = self._normalize_phone_number(phone_number)

            # Store opt-out in Redis (fast lookup)
            opt_out_key = f"sms_opted_out:{normalized_phone}"
            opt_out_data = {
                "opted_out_at": datetime.now().isoformat(),
                "reason": reason.value,
                "message_content": message_content,
                "location_id": location_id
            }

            await self.cache.set(opt_out_key, opt_out_data, ttl=86400*365*2)  # 2 years

            # Store in persistent database (audit trail)
            await self._store_opt_out_audit(
                normalized_phone, reason, message_content, location_id
            )

            # Publish compliance events
            await self.event_publisher.publish_sms_opt_out_processed(
                phone_number=normalized_phone,
                opt_out_method=reason.value,
                message_content=message_content,
                location_id=location_id
            )

            await self.event_publisher.publish_sms_compliance_event(
                phone_number=normalized_phone,
                event_type="opt_out_processed",
                reason=reason.value,
                additional_data={"location_id": location_id},
                location_id=location_id
            )

            logger.info(f"Processed SMS opt-out: {reason.value} for {normalized_phone}")

        except Exception as e:
            logger.error(f"Error processing opt-out for {phone_number}: {str(e)}")
            raise

    async def record_sms_sent(self, phone_number: str, message_content: str,
                             success: bool, location_id: Optional[str] = None):
        """
        Record SMS send for frequency tracking and compliance.

        Args:
            phone_number: Target phone number
            message_content: Message content
            success: Whether send was successful
            location_id: GHL location ID
        """
        try:
            normalized_phone = self._normalize_phone_number(phone_number)

            # Increment daily counter
            daily_key = f"sms_daily:{normalized_phone}:{datetime.now().strftime('%Y-%m-%d')}"
            await self.cache.incr(daily_key, ttl=86400)  # 24 hours

            # Increment monthly counter
            monthly_key = f"sms_monthly:{normalized_phone}:{datetime.now().strftime('%Y-%m')}"
            await self.cache.incr(monthly_key, ttl=86400*31)  # 31 days

            # Record last sent timestamp
            timestamp_key = f"sms_last_sent:{normalized_phone}"
            await self.cache.set(timestamp_key, datetime.now().isoformat(), ttl=86400*7)  # 7 days

            # Store audit record
            await self._store_sms_audit(
                normalized_phone, message_content, success, location_id
            )

            if success:
                logger.info(f"Recorded SMS send to {normalized_phone}")
            else:
                logger.warning(f"Recorded failed SMS send to {normalized_phone}")

        except Exception as e:
            logger.error(f"Error recording SMS send to {phone_number}: {str(e)}")

    async def get_compliance_status(self, phone_number: str) -> Dict[str, any]:
        """
        Get complete compliance status for a phone number.

        Args:
            phone_number: Phone number to check

        Returns:
            Dict with complete compliance information
        """
        try:
            normalized_phone = self._normalize_phone_number(phone_number)

            # Check opt-out status
            opted_out = await self._is_opted_out(normalized_phone)
            opt_out_data = None
            if opted_out:
                opt_out_key = f"sms_opted_out:{normalized_phone}"
                opt_out_data = await self.cache.get(opt_out_key)

            # Get frequency counts
            daily_count = await self._get_daily_sms_count(normalized_phone)
            monthly_count = await self._get_monthly_sms_count(normalized_phone)
            last_sent = await self._get_last_sent_timestamp(normalized_phone)

            return {
                "phone_number": normalized_phone,
                "opted_out": opted_out,
                "opt_out_data": opt_out_data,
                "daily_count": daily_count,
                "monthly_count": monthly_count,
                "daily_limit": self.DAILY_LIMIT,
                "monthly_limit": self.MONTHLY_LIMIT,
                "last_sent": last_sent.isoformat() if last_sent else None,
                "compliance_status": "compliant" if not opted_out and daily_count < self.DAILY_LIMIT and monthly_count < self.MONTHLY_LIMIT else "limited",
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting compliance status for {phone_number}: {str(e)}")
            return {
                "phone_number": phone_number,
                "error": str(e),
                "compliance_status": "error"
            }

    # === PRIVATE HELPER METHODS ===

    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number to E.164 format."""
        # Remove all non-digits
        digits_only = re.sub(r'[^\d]', '', phone_number)

        # Add country code if missing
        if len(digits_only) == 10:
            digits_only = '1' + digits_only  # US/Canada default
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            pass  # Already has country code
        else:
            # International or invalid - keep as is for now
            pass

        return f"+{digits_only}"

    async def _is_opted_out(self, phone_number: str) -> bool:
        """Check if phone number is opted out."""
        opt_out_key = f"sms_opted_out:{phone_number}"
        return await self.cache.exists(opt_out_key)

    async def _get_daily_sms_count(self, phone_number: str) -> int:
        """Get daily SMS count for phone number."""
        daily_key = f"sms_daily:{phone_number}:{datetime.now().strftime('%Y-%m-%d')}"
        count = await self.cache.get(daily_key)
        return int(count) if count else 0

    async def _get_monthly_sms_count(self, phone_number: str) -> int:
        """Get monthly SMS count for phone number."""
        monthly_key = f"sms_monthly:{phone_number}:{datetime.now().strftime('%Y-%m')}"
        count = await self.cache.get(monthly_key)
        return int(count) if count else 0

    async def _get_last_sent_timestamp(self, phone_number: str) -> Optional[datetime]:
        """Get timestamp of last SMS sent."""
        timestamp_key = f"sms_last_sent:{phone_number}"
        timestamp_str = await self.cache.get(timestamp_key)
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)
        return None

    def _check_compliance_flags(self, message_content: str) -> List[str]:
        """Check message content for compliance red flags."""
        flags = []
        content_upper = message_content.upper()

        # Aggressive language
        aggressive_terms = ["MUST", "URGENT", "FINAL NOTICE", "ACT NOW", "LIMITED TIME"]
        if any(term in content_upper for term in aggressive_terms):
            flags.append("aggressive_language")

        # Financial pressure
        financial_terms = ["MORTGAGE", "CREDIT", "DEBT", "LOAN", "PAYMENT"]
        if any(term in content_upper for term in financial_terms):
            flags.append("financial_content")

        return flags

    async def _store_opt_out_audit(self, phone_number: str, reason: OptOutReason,
                                  message_content: Optional[str], location_id: Optional[str]):
        """Store opt-out in database for audit trail."""
        # TODO: Implement database storage
        # This would typically store in PostgreSQL for permanent audit trail
        logger.info(f"Opt-out audit record: {phone_number} - {reason.value}")

    async def _store_sms_audit(self, phone_number: str, message_content: str,
                              success: bool, location_id: Optional[str]):
        """Store SMS send in database for audit trail."""
        # TODO: Implement database storage
        # This would typically store in PostgreSQL for permanent audit trail
        logger.info(f"SMS audit record: {phone_number} - {'success' if success else 'failed'}")

    async def _log_compliance_violation(self, phone_number: str, violation_type: str,
                                       location_id: Optional[str]):
        """Log compliance violation for monitoring."""
        await self.event_publisher.publish_sms_compliance_event(
            phone_number=phone_number,
            event_type="compliance_violation",
            reason=violation_type,
            additional_data={"severity": "high"},
            location_id=location_id
        )


# === FACTORY FUNCTIONS ===

_sms_compliance_service = None

def get_sms_compliance_service() -> SMSComplianceService:
    """Get singleton SMS compliance service."""
    global _sms_compliance_service
    if _sms_compliance_service is None:
        _sms_compliance_service = SMSComplianceService()
    return _sms_compliance_service