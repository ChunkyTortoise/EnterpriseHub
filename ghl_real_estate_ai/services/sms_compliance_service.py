"""
SMS Compliance Service

Tracks SMS opt-outs, send audit logs, and compliance violations.
Implements TCPA-style opt-out handling and frequency limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import os
import re
from typing import Optional, Dict, Any, List
from zoneinfo import ZoneInfo

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.database_service import get_database

logger = get_logger(__name__)


class OptOutReason(str, Enum):
    USER_REQUEST = "user_request"
    COMPLIANCE_VIOLATION = "compliance_violation"
    ADMIN_BLOCK = "admin_block"
    FREQUENCY_ABUSE = "frequency_abuse"


@dataclass
class SMSValidationResult:
    allowed: bool
    reason: str
    daily_count: int
    monthly_count: int
    compliance_notes: List[str]
    last_sent: Optional[datetime] = None


class SMSComplianceService:
    """Service for SMS compliance checks and auditing."""

    STOP_KEYWORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}
    DAILY_LIMIT = 3
    MONTHLY_LIMIT = 20
    BUSINESS_HOURS_START = 8   # 8 AM local time
    BUSINESS_HOURS_END = 20    # 8 PM local time

    def __init__(self):
        self._tables_ready = False
        self._allow_ddl = os.getenv("SMS_COMPLIANCE_ALLOW_DDL", "false").lower() in {"1", "true", "yes"}

    async def _ensure_tables(self) -> None:
        if self._tables_ready:
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
        await self._ensure_tables()

        normalized_phone = self._normalize_phone_number(phone_number)
        if self._contains_stop_keyword(message_content):
            await self.process_opt_out(
                phone_number=normalized_phone,
                reason=OptOutReason.USER_REQUEST,
                message_content=message_content,
                location_id=location_id,
            )
            action = "opt_out"
        else:
            action = "none"

        return {
            "action": action,
            "phone_number": normalized_phone,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def validate_sms_send(
        self,
        phone_number: str,
        message_content: str,
        location_id: Optional[str] = None,
    ) -> SMSValidationResult:
        """Validate outbound SMS against opt-out and frequency rules."""
        await self._ensure_tables()

        normalized_phone = self._normalize_phone_number(phone_number)
        db = await get_database()
        async with db.get_connection() as conn:
            opt_out = await conn.fetchrow(
                "SELECT phone_number, opt_out_reason, opted_out_at FROM sms_opt_outs WHERE phone_number = $1",
                normalized_phone,
            )
            if opt_out:
                return SMSValidationResult(
                    allowed=False,
                    reason="opted_out",
                    daily_count=0,
                    monthly_count=0,
                    compliance_notes=["Recipient has opted out of SMS."],
                    last_sent=None,
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

        compliance_notes = []
        allowed = True
        reason = "ok"

        if daily_count >= self.DAILY_LIMIT:
            allowed = False
            reason = "daily_limit_exceeded"
            compliance_notes.append("Daily SMS limit exceeded.")

        if monthly_count >= self.MONTHLY_LIMIT:
            allowed = False
            reason = "monthly_limit_exceeded"
            compliance_notes.append("Monthly SMS limit exceeded.")

        if len(message_content or "") > 160:
            compliance_notes.append("Message exceeds 160 characters (SMS length).")

        local_time = datetime.now(ZoneInfo("America/Los_Angeles"))
        if not (self.BUSINESS_HOURS_START <= local_time.hour < self.BUSINESS_HOURS_END):
            compliance_notes.append("Outside business hours (PT).")

        return SMSValidationResult(
            allowed=allowed,
            reason=reason,
            daily_count=int(daily_count or 0),
            monthly_count=int(monthly_count or 0),
            compliance_notes=compliance_notes,
            last_sent=last_sent,
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

    async def get_compliance_status(self, phone_number: str) -> Dict[str, Any]:
        """Return compliance status for a phone number."""
        await self._ensure_tables()

        normalized_phone = self._normalize_phone_number(phone_number)
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

        return {
            "phone_number": normalized_phone,
            "opted_out": bool(opt_out),
            "opt_out_reason": opt_out["opt_out_reason"] if opt_out else None,
            "opted_out_at": opt_out["opted_out_at"].isoformat() if opt_out else None,
            "daily_count": int(daily_count or 0),
            "monthly_count": int(monthly_count or 0),
            "last_sent": last_sent.isoformat() if last_sent else None,
            "limits": {
                "daily": self.DAILY_LIMIT,
                "monthly": self.MONTHLY_LIMIT,
            },
        }

    async def _record_violation(
        self,
        conn,
        phone_number: str,
        violation_type: str,
        severity: str,
        location_id: Optional[str],
        details: Dict[str, Any],
    ) -> None:
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
        cleaned = re.sub(r"[^A-Z0-9]+", " ", (message_content or "").upper()).strip()
        if not cleaned:
            return False
        tokens = cleaned.split()
        return any(token in self.STOP_KEYWORDS for token in tokens)


_sms_compliance_service: Optional[SMSComplianceService] = None


def get_sms_compliance_service() -> SMSComplianceService:
    """Singleton accessor for SMSComplianceService."""
    global _sms_compliance_service
    if _sms_compliance_service is None:
        _sms_compliance_service = SMSComplianceService()
        logger.info("Initialized SMSComplianceService singleton")
    return _sms_compliance_service
