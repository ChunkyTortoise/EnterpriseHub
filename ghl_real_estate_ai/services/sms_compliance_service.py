"""
SMS Compliance Service

Tracks SMS opt-outs, send audit logs, and compliance violations.
Implements TCPA-style opt-out handling and frequency limits.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.database_service import get_database

try:
    from ghl_real_estate_ai.services.cache_service import get_cache_service
except Exception:  # pragma: no cover - optional dependency
    get_cache_service = None

try:
    from ghl_real_estate_ai.services.event_publisher import get_event_publisher
except Exception:  # pragma: no cover - optional dependency
    get_event_publisher = None

logger = get_logger(__name__)


class OptOutReason(str, Enum):
    USER_REQUEST = "user_request"
    STOP_KEYWORD = "stop_keyword"
    COMPLIANCE_VIOLATION = "compliance_violation"
    ADMIN_BLOCK = "admin_block"
    FREQUENCY_ABUSE = "frequency_abuse"


@dataclass
class SMSValidationResult:
    allowed: bool
    reason: Optional[str]
    daily_count: int
    monthly_count: int
    compliance_notes: List[str]
    last_sent: Optional[datetime] = None


class SMSComplianceService:
    """Service for SMS compliance checks and auditing."""

    STOP_KEYWORDS = {
        "STOP",
        "UNSUBSCRIBE",
        "QUIT",
        "CANCEL",
        "END",
        "REMOVE",
        "HALT",
        "OPT-OUT",
        "OPTOUT",
        "NO",
        "OFF",
        "STOPALL",
    }
    DAILY_LIMIT = 3
    MONTHLY_LIMIT = 20
    BUSINESS_HOURS_START = 8  # 8 AM local time
    BUSINESS_HOURS_END = 21  # 9 PM local time

    def __init__(self):
        self._tables_ready = False
        self._allow_ddl = os.getenv("SMS_COMPLIANCE_ALLOW_DDL", "false").lower() in {"1", "true", "yes"}
        self._use_db = os.getenv("SMS_COMPLIANCE_USE_DB", "true").lower() in {"1", "true", "yes"}
        self.cache = None
        self.event_publisher = None

    async def _ensure_tables(self) -> None:
        if self._tables_ready:
            return
        if not self._use_db:
            self._tables_ready = True
            return

        db = await get_database()
        async with db.get_connection() as conn:
            expected_tables = (
                "sms_opt_outs",
                "sms_send_audit_log",
                "sms_compliance_violations",
            )
            missing_tables = []
            for table in expected_tables:
                exists = await conn.fetchval("SELECT to_regclass($1)", f"public.{table}")
                if not exists:
                    missing_tables.append(table)

            if missing_tables:
                if not self._allow_ddl:
                    raise RuntimeError(
                        "SMS compliance tables are missing. "
                        f"Missing: {', '.join(missing_tables)}. "
                        "Run the migration to create them or set SMS_COMPLIANCE_ALLOW_DDL=true for dev."
                    )

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS sms_opt_outs (
                        phone_number VARCHAR(50) PRIMARY KEY,
                        opt_out_reason VARCHAR(50) NOT NULL,
                        opted_out_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        location_id VARCHAR(100),
                        message_content TEXT,
                        notes TEXT
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS sms_send_audit_log (
                        id BIGSERIAL PRIMARY KEY,
                        phone_number VARCHAR(50) NOT NULL,
                        message_content TEXT,
                        message_length INT,
                        success BOOLEAN NOT NULL DEFAULT TRUE,
                        error_message TEXT,
                        location_id VARCHAR(100),
                        sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS sms_compliance_violations (
                        id BIGSERIAL PRIMARY KEY,
                        phone_number VARCHAR(50) NOT NULL,
                        violation_type VARCHAR(50) NOT NULL,
                        violation_severity VARCHAR(20) DEFAULT 'warning',
                        violation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        location_id VARCHAR(100),
                        details JSONB DEFAULT '{}'::jsonb
                    )
                """)
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_audit_phone ON sms_send_audit_log(phone_number)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_audit_sent_at ON sms_send_audit_log(sent_at)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_sms_opt_outs_location ON sms_opt_outs(location_id)")
        self._tables_ready = True

    async def process_incoming_sms(
        self,
        phone_number: str,
        message_content: str,
        location_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process inbound SMS for STOP keywords and compliance actions."""
        try:
            await self._ensure_tables()

            normalized_phone = self._normalize_phone_number(phone_number)
            if self._contains_stop_keyword(message_content):
                keywords_detected = [kw for kw in self.STOP_KEYWORDS if kw in (message_content or "").upper()]
                await self.process_opt_out(
                    phone_number=normalized_phone,
                    reason=OptOutReason.STOP_KEYWORD,
                    message_content=message_content,
                    location_id=location_id,
                )
                return {
                    "action": "opt_out_processed",
                    "phone_number": normalized_phone,
                    "method": "stop_keyword",
                    "keywords_detected": keywords_detected,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            compliance_flags = self._check_compliance_flags(message_content)
            return {
                "action": "message_processed",
                "phone_number": normalized_phone,
                "compliance_flags": compliance_flags,
                "opt_out_status": "not_opted_out",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing incoming SMS from {phone_number}: {e}")
            return {
                "action": "processing_error",
                "phone_number": phone_number,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def validate_sms_send(
        self,
        phone_number: str,
        message_content: str,
        location_id: Optional[str] = None,
    ) -> SMSValidationResult:
        """Validate outbound SMS against opt-out and frequency rules."""
        try:
            await self._ensure_tables()

            normalized_phone = self._normalize_phone_number(phone_number)
            opted_out = await self._is_opted_out(normalized_phone)
            if opted_out:
                return SMSValidationResult(
                    allowed=False,
                    reason="opted_out",
                    daily_count=0,
                    monthly_count=0,
                    compliance_notes=["opted out"],
                    last_sent=None,
                )

            daily_count = await self._get_daily_sms_count(normalized_phone)
            monthly_count = await self._get_monthly_sms_count(normalized_phone)
            last_sent = await self._get_last_sent_timestamp(normalized_phone)

            compliance_notes: List[str] = []
            allowed = True
            reason: Optional[str] = None

            if daily_count >= self.DAILY_LIMIT:
                allowed = False
                reason = "daily_limit_exceeded"
                compliance_notes.append("Daily limit")
                publisher = self._get_event_publisher()
                if publisher:
                    await publisher.publish_sms_frequency_limit_hit(
                        phone_number=normalized_phone,
                        limit_type="daily",
                        current_count=daily_count,
                        limit_value=self.DAILY_LIMIT,
                        location_id=location_id,
                    )
            elif monthly_count >= self.MONTHLY_LIMIT:
                allowed = False
                reason = "monthly_limit_exceeded"
                compliance_notes.append("Monthly limit")
                publisher = self._get_event_publisher()
                if publisher:
                    await publisher.publish_sms_frequency_limit_hit(
                        phone_number=normalized_phone,
                        limit_type="monthly",
                        current_count=monthly_count,
                        limit_value=self.MONTHLY_LIMIT,
                        location_id=location_id,
                    )

            if len(message_content or "") > 160:
                compliance_notes.append("Message exceeds 160 characters (SMS length).")

            local_time = datetime.now(ZoneInfo("America/Los_Angeles"))
            if not (self.BUSINESS_HOURS_START <= local_time.hour <= self.BUSINESS_HOURS_END):
                compliance_notes.append("Outside business hours (PT).")

            return SMSValidationResult(
                allowed=allowed,
                reason=reason,
                daily_count=int(daily_count or 0),
                monthly_count=int(monthly_count or 0),
                compliance_notes=compliance_notes,
                last_sent=last_sent,
            )
        except Exception as e:
            logger.error(f"Error validating SMS send to {phone_number}: {e}")
            return SMSValidationResult(
                allowed=False,
                reason="validation_error",
                daily_count=0,
                monthly_count=0,
                compliance_notes=[f"validation error: {e}"],
                last_sent=None,
            )

    async def record_sms_sent(
        self,
        phone_number: str,
        message_content: str,
        success: bool,
        location_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record outbound SMS send results for compliance auditing."""
        await self._ensure_tables()

        normalized_phone = self._normalize_phone_number(phone_number)
        cache = self._get_cache()
        if cache:
            daily_key = f"sms_daily:{normalized_phone}:{datetime.now().strftime('%Y-%m-%d')}"
            monthly_key = f"sms_monthly:{normalized_phone}:{datetime.now().strftime('%Y-%m')}"
            await cache.incr(daily_key, ttl=86400)
            await cache.incr(monthly_key, ttl=86400 * 31)
            await cache.set(
                f"sms_last_sent:{normalized_phone}",
                datetime.now(timezone.utc).isoformat(),
                ttl=86400 * 7,
            )

        if self._use_db:
            db = await get_database()
            async with db.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO sms_send_audit_log
                    (phone_number, message_content, message_length, success, error_message, location_id, sent_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    """,
                    normalized_phone,
                    message_content,
                    len(message_content or ""),
                    success,
                    error_message,
                    location_id,
                )

                if len(message_content or "") > 160:
                    await self._record_violation(
                        conn,
                        phone_number,
                        violation_type="length_exceeded",
                        severity="warning",
                        location_id=location_id,
                        details={"length": len(message_content or "")},
                    )

                if not success:
                    await self._record_violation(
                        conn,
                        phone_number,
                        violation_type="send_failed",
                        severity="warning",
                        location_id=location_id,
                        details={"error": error_message or "unknown"},
                    )

        await self._store_sms_audit(normalized_phone, message_content, success, location_id)

    async def process_opt_out(
        self,
        phone_number: str,
        reason: OptOutReason,
        message_content: Optional[str] = None,
        location_id: Optional[str] = None,
    ) -> None:
        """Persist opt-out for a phone number."""
        await self._ensure_tables()

        normalized_phone = self._normalize_phone_number(phone_number)
        cache = self._get_cache()
        if cache:
            await cache.set(
                f"sms_opted_out:{normalized_phone}",
                {
                    "opted_out_at": datetime.now(timezone.utc).isoformat(),
                    "reason": reason.value,
                    "message_content": message_content,
                    "location_id": location_id,
                },
                ttl=86400 * 365 * 2,
            )

        if self._use_db:
            db = await get_database()
            async with db.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO sms_opt_outs (phone_number, opt_out_reason, opted_out_at, location_id, message_content)
                    VALUES ($1, $2, NOW(), $3, $4)
                    ON CONFLICT (phone_number)
                    DO UPDATE SET
                        opt_out_reason = EXCLUDED.opt_out_reason,
                        opted_out_at = EXCLUDED.opted_out_at,
                        location_id = EXCLUDED.location_id,
                        message_content = EXCLUDED.message_content
                    """,
                    normalized_phone,
                    reason.value,
                    location_id,
                    message_content,
                )

        await self._store_opt_out_audit(normalized_phone, reason, message_content, location_id)

        publisher = self._get_event_publisher()
        if publisher:
            await publisher.publish_sms_opt_out_processed(
                phone_number=normalized_phone,
                opt_out_method=reason.value,
                message_content=message_content,
                location_id=location_id,
            )
            await publisher.publish_sms_compliance_event(
                phone_number=normalized_phone,
                event_type="opt_out_processed",
                reason=reason.value,
                additional_data={"location_id": location_id},
                location_id=location_id,
            )

    async def get_compliance_status(self, phone_number: str) -> Dict[str, Any]:
        """Return compliance status for a phone number."""
        await self._ensure_tables()

        normalized_phone = self._normalize_phone_number(phone_number)
        cache = self._get_cache()
        opt_out = None
        opt_out_data = None
        daily_count = 0
        monthly_count = 0
        last_sent = None

        if cache:
            opt_out = await cache.exists(f"sms_opted_out:{normalized_phone}")
            if opt_out:
                opt_out_data = await cache.get(f"sms_opted_out:{normalized_phone}")
            daily_count = await cache.get(f"sms_daily:{normalized_phone}:{datetime.now().strftime('%Y-%m-%d')}") or 0
            monthly_count = await cache.get(f"sms_monthly:{normalized_phone}:{datetime.now().strftime('%Y-%m')}") or 0
            last_sent = await cache.get(f"sms_last_sent:{normalized_phone}")
        elif self._use_db:
            db = await get_database()
            async with db.get_connection() as conn:
                opt_out = await conn.fetchrow(
                    "SELECT phone_number, opt_out_reason, opted_out_at FROM sms_opt_outs WHERE phone_number = $1",
                    normalized_phone,
                )
                daily_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM sms_send_audit_log
                    WHERE phone_number = $1 AND sent_at > NOW() - INTERVAL '1 day'
                    """,
                    normalized_phone,
                )
                monthly_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM sms_send_audit_log
                    WHERE phone_number = $1 AND sent_at > NOW() - INTERVAL '30 days'
                    """,
                    normalized_phone,
                )
                last_sent = await conn.fetchval(
                    "SELECT MAX(sent_at) FROM sms_send_audit_log WHERE phone_number = $1",
                    normalized_phone,
                )

        compliance_status = "compliant"
        if opt_out or int(daily_count or 0) >= self.DAILY_LIMIT or int(monthly_count or 0) >= self.MONTHLY_LIMIT:
            compliance_status = "limited"

        opt_out_reason = None
        opted_out_at = None
        if opt_out_data:
            opt_out_reason = opt_out_data.get("reason")
            opted_out_at = opt_out_data.get("opted_out_at")
        elif opt_out:
            opt_out_reason = opt_out["opt_out_reason"]
            opted_out_at = opt_out["opted_out_at"].isoformat()

        return {
            "phone_number": normalized_phone,
            "opted_out": bool(opt_out),
            "opt_out_reason": opt_out_reason,
            "opted_out_at": opted_out_at,
            "opt_out_data": opt_out_data,
            "daily_count": int(daily_count or 0),
            "monthly_count": int(monthly_count or 0),
            "last_sent": last_sent.isoformat() if hasattr(last_sent, "isoformat") else last_sent,
            "compliance_status": compliance_status,
            "limits": {
                "daily": self.DAILY_LIMIT,
                "monthly": self.MONTHLY_LIMIT,
            },
        }

    def _get_cache(self):
        if self.cache is None and get_cache_service:
            use_cache = os.getenv("SMS_COMPLIANCE_USE_CACHE", "true").lower() in {"1", "true", "yes"}
            if use_cache:
                self.cache = get_cache_service()
        return self.cache

    def _get_event_publisher(self):
        if self.event_publisher is None and get_event_publisher:
            self.event_publisher = get_event_publisher()
        return self.event_publisher

    async def _is_opted_out(self, phone_number: str) -> bool:
        cache = self._get_cache()
        if cache:
            try:
                return bool(await cache.exists(f"sms_opted_out:{phone_number}"))
            except Exception as e:
                logger.warning(f"Cache opt-out check failed: {e}")
                raise

        if not self._use_db:
            return False

        # Cache not available: fall back to database
        db = await get_database()
        async with db.get_connection() as conn:
            opt_out = await conn.fetchval(
                "SELECT 1 FROM sms_opt_outs WHERE phone_number = $1",
                phone_number,
            )
        return bool(opt_out)

    async def _get_daily_sms_count(self, phone_number: str) -> int:
        cache = self._get_cache()
        if cache:
            count = await cache.get(f"sms_daily:{phone_number}:{datetime.now().strftime('%Y-%m-%d')}")
            return int(count) if count else 0

        if not self._use_db:
            return 0

        # Cache not available: fall back to database
        db = await get_database()
        async with db.get_connection() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM sms_send_audit_log
                WHERE phone_number = $1 AND sent_at > NOW() - INTERVAL '1 day'
                """,
                phone_number,
            )
        return int(count or 0)

    async def _get_monthly_sms_count(self, phone_number: str) -> int:
        cache = self._get_cache()
        if cache:
            count = await cache.get(f"sms_monthly:{phone_number}:{datetime.now().strftime('%Y-%m')}")
            return int(count) if count else 0

        if not self._use_db:
            return 0

        # Cache not available: fall back to database
        db = await get_database()
        async with db.get_connection() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM sms_send_audit_log
                WHERE phone_number = $1 AND sent_at > NOW() - INTERVAL '30 days'
                """,
                phone_number,
            )
        return int(count or 0)

    async def _get_last_sent_timestamp(self, phone_number: str) -> Optional[datetime]:
        cache = self._get_cache()
        if cache:
            timestamp_str = await cache.get(f"sms_last_sent:{phone_number}")
            if timestamp_str:
                try:
                    return datetime.fromisoformat(timestamp_str)
                except Exception:
                    return None
            return None

        if not self._use_db:
            return None

        # Cache not available: fall back to database
        db = await get_database()
        async with db.get_connection() as conn:
            return await conn.fetchval(
                "SELECT MAX(sent_at) FROM sms_send_audit_log WHERE phone_number = $1",
                phone_number,
            )

    def _check_compliance_flags(self, message_content: str) -> List[str]:
        flags: List[str] = []
        content_upper = (message_content or "").upper()

        aggressive_terms = ["MUST", "URGENT", "FINAL NOTICE", "ACT NOW", "LIMITED TIME"]
        if any(term in content_upper for term in aggressive_terms):
            flags.append("aggressive_language")

        financial_terms = ["MORTGAGE", "CREDIT", "DEBT", "LOAN", "PAYMENT"]
        if any(term in content_upper for term in financial_terms):
            flags.append("financial_content")

        return flags

    async def _store_opt_out_audit(
        self,
        phone_number: str,
        reason: OptOutReason,
        message_content: Optional[str],
        location_id: Optional[str],
    ) -> None:
        logger.info(f"Opt-out audit record: {phone_number} - {reason.value}")

    async def _store_sms_audit(
        self,
        phone_number: str,
        message_content: str,
        success: bool,
        location_id: Optional[str],
    ) -> None:
        logger.info(f"SMS audit record: {phone_number} - {'success' if success else 'failed'}")

    async def _log_compliance_violation(self, phone_number: str, violation_type: str, location_id: Optional[str]):
        publisher = self._get_event_publisher()
        if publisher:
            await publisher.publish_sms_compliance_event(
                phone_number=phone_number,
                event_type="compliance_violation",
                reason=violation_type,
                additional_data={"severity": "high"},
                location_id=location_id,
            )

    async def _record_violation(
        self,
        conn,
        phone_number: str,
        violation_type: str,
        severity: str,
        location_id: Optional[str],
        details: Dict[str, Any],
    ) -> None:
        if not self._use_db:
            return
        await conn.execute(
            """
            INSERT INTO sms_compliance_violations
            (phone_number, violation_type, violation_severity, violation_timestamp, location_id, details)
            VALUES ($1, $2, $3, NOW(), $4, $5)
            """,
            phone_number,
            violation_type,
            severity,
            location_id,
            details,
        )

    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone numbers to E.164 where possible."""
        digits = re.sub(r"\D+", "", phone_number or "")
        if len(digits) == 10:
            digits = "1" + digits
        if not digits:
            return phone_number
        return f"+{digits}"

    def _contains_stop_keyword(self, message_content: str) -> bool:
        """Detect STOP keywords in free-form messages."""
        message_upper = (message_content or "").upper()
        if not message_upper.strip():
            return False
        normalized_message = re.sub(r"[^A-Z0-9]+", "", message_upper)
        for keyword in self.STOP_KEYWORDS:
            normalized_keyword = re.sub(r"[^A-Z0-9]+", "", keyword.upper())
            if normalized_keyword and normalized_keyword in normalized_message:
                return True
        return False


_sms_compliance_service: Optional[SMSComplianceService] = None


def get_sms_compliance_service() -> SMSComplianceService:
    """Singleton accessor for SMSComplianceService."""
    global _sms_compliance_service
    if _sms_compliance_service is None:
        _sms_compliance_service = SMSComplianceService()
        logger.info("Initialized SMSComplianceService singleton")
    return _sms_compliance_service
