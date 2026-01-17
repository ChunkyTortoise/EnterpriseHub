"""
Production Twilio Client for Service 6 Lead Recovery & Nurture Engine.

Provides real Twilio API integration for SMS communications:
- SMS sending and delivery tracking
- Phone number validation
- Message status webhooks
- Opt-out and compliance management
- Rate limiting and error handling
- TCPA compliance features
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientTimeout, BasicAuth
from pydantic import BaseModel, validator
from twilio.rest import Client as TwilioSyncClient
from twilio.base.exceptions import TwilioRestException

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.database_service import DatabaseService, log_communication

logger = get_logger(__name__)


class MessageStatus(Enum):
    """Twilio message status enumeration."""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    UNDELIVERED = "undelivered"
    FAILED = "failed"
    RECEIVED = "received"


class TwilioConfig(BaseModel):
    """Twilio client configuration."""
    
    account_sid: str = settings.twilio_account_sid
    auth_token: str = settings.twilio_auth_token
    phone_number: str = settings.twilio_phone_number
    webhook_base_url: str = settings.webhook_base_url
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_messages_per_minute: int = 100
    
    @validator('account_sid', 'auth_token', 'phone_number')
    def validate_required_fields(cls, v, field):
        if not v or v.startswith("your_twilio_"):
            raise ValueError(f"Valid Twilio {field.name} is required")
        return v
    
    @validator('phone_number')
    def validate_phone_format(cls, v):
        if not v.startswith('+'):
            raise ValueError("Phone number must include country code (e.g., +1234567890)")
        return v


class SMSMessage(BaseModel):
    """SMS message model."""
    
    sid: str
    to: str
    from_: str
    body: str
    status: MessageStatus
    direction: str
    date_created: datetime
    date_sent: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    price: Optional[str] = None
    price_unit: Optional[str] = None
    uri: Optional[str] = None
    
    class Config:
        use_enum_values = True


class PhoneNumberInfo(BaseModel):
    """Phone number validation information."""
    
    phone_number: str
    country_code: str
    national_format: str
    valid: bool
    line_type: Optional[str] = None  # mobile, landline, voip, etc.
    carrier_name: Optional[str] = None
    carrier_type: Optional[str] = None  # mobile, landline, voip
    
    class Config:
        extra = "allow"


class OptOutRecord(BaseModel):
    """Opt-out record for compliance."""
    
    phone_number: str
    opted_out_at: datetime
    reason: str = "user_request"
    method: str = "sms"  # sms, voice, email
    
    class Config:
        extra = "allow"


class TwilioAPIException(Exception):
    """Twilio API specific exception."""
    
    def __init__(self, message: str, error_code: int = None, 
                 status_code: int = None, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class TwilioClient:
    """
    Production Twilio SMS client.
    
    Provides comprehensive SMS functionality with:
    - Message sending and delivery tracking
    - Phone number validation and formatting
    - Webhook processing for status updates
    - Opt-out management and compliance
    - Rate limiting and error handling
    - TCPA compliance features
    """
    
    def __init__(self, config: TwilioConfig = None, 
                 cache_service: CacheService = None,
                 database_service: DatabaseService = None):
        """Initialize Twilio client."""
        self.config = config or TwilioConfig()
        self.cache_service = cache_service or CacheService()
        self.database_service = database_service
        self.sync_client = TwilioSyncClient(self.config.account_sid, self.config.auth_token)
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_semaphore = asyncio.Semaphore(self.config.rate_limit_messages_per_minute)
        
        # In-memory opt-out cache
        self._opt_out_cache = set()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        await self._load_opt_outs()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if not self.session:
            timeout = ClientTimeout(total=self.config.timeout)
            
            # Basic auth for Twilio API
            auth = BasicAuth(self.config.account_sid, self.config.auth_token)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                auth=auth,
                connector=aiohttp.TCPConnector(limit=50, ttl_dns_cache=300)
            )
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _load_opt_outs(self):
        """Load opt-out phone numbers into memory cache."""
        try:
            if self.database_service:
                # Load from database
                db = await self.database_service.get_service()
                async with db.get_connection() as conn:
                    opt_outs = await conn.fetch("""
                        SELECT DISTINCT phone_number 
                        FROM sms_opt_outs 
                        WHERE opted_out = true
                    """)
                    
                    self._opt_out_cache = {row['phone_number'] for row in opt_outs}
            else:
                # Load from cache service
                cached_opt_outs = await self.cache_service.get("sms_opt_outs", default=[])
                self._opt_out_cache = set(cached_opt_outs)
                
            logger.info(f"Loaded {len(self._opt_out_cache)} opt-out phone numbers")
            
        except Exception as e:
            logger.error(f"Failed to load opt-outs: {e}")
            self._opt_out_cache = set()
    
    # ============================================================================
    # Phone Number Management
    # ============================================================================
    
    async def validate_phone_number(self, phone_number: str) -> PhoneNumberInfo:
        """Validate and get information about a phone number."""
        try:
            # Use sync client for phone number validation
            lookup = self.sync_client.lookups.v1.phone_numbers(phone_number).fetch(
                type=['carrier']
            )
            
            result = PhoneNumberInfo(
                phone_number=lookup.phone_number,
                country_code=lookup.country_code,
                national_format=lookup.national_format,
                valid=True,
                carrier_name=lookup.carrier.get('name') if lookup.carrier else None,
                carrier_type=lookup.carrier.get('type') if lookup.carrier else None
            )
            
            # Cache the result
            await self.cache_service.set(
                f"phone_validation:{phone_number}", 
                result.dict(), 
                ttl=86400  # 24 hours
            )
            
            logger.info(f"Validated phone number {phone_number}: {result.carrier_type}")
            return result
            
        except TwilioRestException as e:
            if e.code == 20404:  # Invalid phone number
                return PhoneNumberInfo(
                    phone_number=phone_number,
                    country_code="",
                    national_format="",
                    valid=False
                )
            else:
                raise TwilioAPIException(f"Phone validation failed: {e.msg}", e.code)
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number to E.164 format."""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if missing (assume US)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif not phone_number.startswith('+'):
            return f"+{digits_only}"
        else:
            return phone_number
    
    # ============================================================================
    # SMS Sending
    # ============================================================================
    
    async def send_sms(self, to: str, message: str, 
                      lead_id: str = None,
                      campaign_id: str = None,
                      template_id: str = None) -> SMSMessage:
        """
        Send SMS message with opt-out checking and compliance.
        
        Args:
            to: Recipient phone number
            message: Message content
            lead_id: Associated lead ID for tracking
            campaign_id: Associated campaign ID
            template_id: Message template ID
            
        Returns:
            SMSMessage object with delivery status
        """
        # Normalize phone number
        to_normalized = self._normalize_phone_number(to)
        
        # Check opt-out status
        if await self._is_opted_out(to_normalized):
            raise TwilioAPIException(f"Phone number {to_normalized} has opted out")
        
        # Rate limiting
        async with self._rate_limit_semaphore:
            try:
                # Add compliance footer if not present
                compliance_message = self._add_compliance_footer(message)
                
                # Send message using sync client
                twilio_message = self.sync_client.messages.create(
                    body=compliance_message,
                    from_=self.config.phone_number,
                    to=to_normalized,
                    status_callback=f"{self.config.webhook_base_url}/webhooks/twilio/sms-status"
                )
                
                # Convert to our message model
                sms_message = SMSMessage(
                    sid=twilio_message.sid,
                    to=twilio_message.to,
                    from_=twilio_message.from_,
                    body=twilio_message.body,
                    status=MessageStatus(twilio_message.status),
                    direction=twilio_message.direction,
                    date_created=twilio_message.date_created,
                    date_sent=twilio_message.date_sent,
                    date_updated=twilio_message.date_updated,
                    error_code=twilio_message.error_code,
                    error_message=twilio_message.error_message,
                    price=twilio_message.price,
                    price_unit=twilio_message.price_unit,
                    uri=twilio_message.uri
                )
                
                # Log communication to database
                if self.database_service and lead_id:
                    await log_communication({
                        "lead_id": lead_id,
                        "channel": "sms",
                        "direction": "outbound",
                        "content": compliance_message,
                        "status": sms_message.status.value,
                        "campaign_id": campaign_id,
                        "template_id": template_id,
                        "metadata": {
                            "twilio_sid": sms_message.sid,
                            "recipient": to_normalized,
                            "price": sms_message.price,
                            "price_unit": sms_message.price_unit
                        }
                    })
                
                logger.info(f"SMS sent successfully to {to_normalized}, SID: {sms_message.sid}")
                return sms_message
                
            except TwilioRestException as e:
                logger.error(f"Twilio SMS sending failed: {e.msg} (Code: {e.code})")
                raise TwilioAPIException(f"SMS sending failed: {e.msg}", e.code)
    
    def _add_compliance_footer(self, message: str) -> str:
        """Add compliance footer to message if not present."""
        opt_out_text = "Reply STOP to opt out"
        
        # Check if opt-out text already present
        if "stop" in message.lower() and "opt" in message.lower():
            return message
        
        # Add footer
        if len(message) + len(opt_out_text) + 2 <= 160:  # SMS character limit
            return f"{message}. {opt_out_text}"
        else:
            # Truncate message to fit compliance footer
            max_message_length = 160 - len(opt_out_text) - 2
            truncated = message[:max_message_length].rstrip()
            return f"{truncated}. {opt_out_text}"
    
    # ============================================================================
    # Message Templates
    # ============================================================================
    
    async def send_templated_sms(self, to: str, template_name: str, 
                               variables: Dict[str, Any] = None,
                               lead_id: str = None,
                               campaign_id: str = None) -> SMSMessage:
        """Send SMS using predefined template."""
        template = await self._get_message_template(template_name)
        
        if not template:
            raise TwilioAPIException(f"Template '{template_name}' not found")
        
        # Replace variables in template
        message = template["content"]
        if variables:
            for key, value in variables.items():
                message = message.replace(f"{{{key}}}", str(value))
        
        return await self.send_sms(
            to=to,
            message=message,
            lead_id=lead_id,
            campaign_id=campaign_id,
            template_id=template.get("id")
        )
    
    async def _get_message_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get message template by name."""
        # Check cache first
        cached_template = await self.cache_service.get(f"sms_template:{template_name}")
        if cached_template:
            return cached_template
        
        # Predefined templates for Service 6
        templates = {
            "instant_response": {
                "id": "template_instant_response",
                "content": "Hi {first_name}! Thanks for your interest. I'm {agent_name} and I'll be helping you. What's the best time to chat? Reply STOP to opt out."
            },
            "follow_up_24h": {
                "id": "template_follow_up_24h", 
                "content": "Hi {first_name}, just checking in! Did you have a chance to review the information I sent? Any questions? - {agent_name}"
            },
            "follow_up_48h": {
                "id": "template_follow_up_48h",
                "content": "{first_name}, I have some great options that match your criteria. When would be a good time for a quick 10-min call? - {agent_name}"
            },
            "follow_up_72h": {
                "id": "template_follow_up_72h",
                "content": "Hi {first_name}, I don't want you to miss out on the current market opportunities. Are you still looking? Let me know! - {agent_name}"
            },
            "appointment_reminder": {
                "id": "template_appointment_reminder",
                "content": "Hi {first_name}, this is a reminder about our call tomorrow at {time}. Looking forward to speaking with you! - {agent_name}"
            },
            "hot_lead_alert": {
                "id": "template_hot_lead_alert",
                "content": "Hi {first_name}! I see you're actively looking. I have some exclusive listings that aren't public yet. Can we chat today? - {agent_name}"
            }
        }
        
        template = templates.get(template_name)
        if template:
            # Cache for future use
            await self.cache_service.set(
                f"sms_template:{template_name}",
                template,
                ttl=3600  # 1 hour
            )
        
        return template
    
    # ============================================================================
    # Opt-Out Management
    # ============================================================================
    
    async def _is_opted_out(self, phone_number: str) -> bool:
        """Check if phone number has opted out."""
        normalized = self._normalize_phone_number(phone_number)
        return normalized in self._opt_out_cache
    
    async def process_opt_out(self, phone_number: str, reason: str = "user_request") -> bool:
        """Process opt-out request."""
        normalized = self._normalize_phone_number(phone_number)
        
        # Add to cache
        self._opt_out_cache.add(normalized)
        
        # Store in database if available
        if self.database_service:
            try:
                db = await self.database_service.get_service()
                async with db.transaction() as conn:
                    await conn.execute("""
                        INSERT INTO sms_opt_outs (phone_number, opted_out, opted_out_at, reason)
                        VALUES ($1, true, NOW(), $2)
                        ON CONFLICT (phone_number) 
                        DO UPDATE SET opted_out = true, opted_out_at = NOW(), reason = $2
                    """, normalized, reason)
            except Exception as e:
                logger.error(f"Failed to store opt-out in database: {e}")
        
        # Update cache service
        try:
            cached_opt_outs = await self.cache_service.get("sms_opt_outs", default=[])
            if normalized not in cached_opt_outs:
                cached_opt_outs.append(normalized)
                await self.cache_service.set("sms_opt_outs", cached_opt_outs, ttl=86400 * 7)  # 1 week
        except Exception as e:
            logger.error(f"Failed to update opt-out cache: {e}")
        
        logger.info(f"Processed opt-out for {normalized}, reason: {reason}")
        return True
    
    async def process_opt_in(self, phone_number: str) -> bool:
        """Process opt-in request (re-subscribe)."""
        normalized = self._normalize_phone_number(phone_number)
        
        # Remove from cache
        self._opt_out_cache.discard(normalized)
        
        # Update database if available
        if self.database_service:
            try:
                db = await self.database_service.get_service()
                async with db.transaction() as conn:
                    await conn.execute("""
                        INSERT INTO sms_opt_outs (phone_number, opted_out, opted_out_at, reason)
                        VALUES ($1, false, NOW(), 'user_opt_in')
                        ON CONFLICT (phone_number) 
                        DO UPDATE SET opted_out = false, opted_out_at = NOW(), reason = 'user_opt_in'
                    """, normalized)
            except Exception as e:
                logger.error(f"Failed to store opt-in in database: {e}")
        
        # Update cache service
        try:
            cached_opt_outs = await self.cache_service.get("sms_opt_outs", default=[])
            if normalized in cached_opt_outs:
                cached_opt_outs.remove(normalized)
                await self.cache_service.set("sms_opt_outs", cached_opt_outs, ttl=86400 * 7)
        except Exception as e:
            logger.error(f"Failed to update opt-in cache: {e}")
        
        logger.info(f"Processed opt-in for {normalized}")
        return True
    
    # ============================================================================
    # Webhook Processing
    # ============================================================================
    
    async def process_status_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process Twilio status webhook."""
        try:
            message_sid = webhook_data.get("MessageSid")
            message_status = webhook_data.get("MessageStatus")
            error_code = webhook_data.get("ErrorCode")
            error_message = webhook_data.get("ErrorMessage")
            
            if not message_sid:
                logger.warning("Webhook missing MessageSid")
                return False
            
            # Update message status in database
            if self.database_service:
                db = await self.database_service.get_service()
                async with db.transaction() as conn:
                    # Find communication record by Twilio SID
                    comm_record = await conn.fetchrow("""
                        SELECT id FROM communication_logs 
                        WHERE metadata->>'twilio_sid' = $1
                    """, message_sid)
                    
                    if comm_record:
                        # Update status
                        await conn.execute("""
                            UPDATE communication_logs 
                            SET status = $1, 
                                delivered_at = CASE WHEN $1 = 'delivered' THEN NOW() ELSE delivered_at END,
                                metadata = metadata || $2
                            WHERE id = $3
                        """, 
                            message_status,
                            json.dumps({
                                "error_code": error_code,
                                "error_message": error_message,
                                "updated_at": datetime.utcnow().isoformat()
                            }),
                            comm_record['id']
                        )
                        
                        logger.info(f"Updated message status for SID {message_sid}: {message_status}")
                    else:
                        logger.warning(f"No communication record found for SID {message_sid}")
            
            # Handle delivery failures
            if message_status in ["failed", "undelivered"]:
                logger.error(f"Message delivery failed - SID: {message_sid}, Error: {error_code} - {error_message}")
                
                # Check if it's a permanent failure (opt-out, invalid number, etc.)
                if error_code in [21610, 21614, 21211]:  # Blacklisted, invalid number, etc.
                    phone_number = webhook_data.get("To")
                    if phone_number:
                        await self.process_opt_out(phone_number, f"delivery_failure_{error_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process status webhook: {e}")
            return False
    
    async def process_incoming_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming SMS webhook."""
        try:
            from_number = webhook_data.get("From")
            to_number = webhook_data.get("To")
            body = webhook_data.get("Body", "").strip().lower()
            message_sid = webhook_data.get("MessageSid")
            
            if not all([from_number, to_number, body]):
                logger.warning("Incoming webhook missing required fields")
                return False
            
            # Check for opt-out keywords
            opt_out_keywords = ["stop", "stopall", "unsubscribe", "cancel", "end", "quit"]
            opt_in_keywords = ["start", "yes", "unstop", "subscribe"]
            
            if any(keyword in body for keyword in opt_out_keywords):
                await self.process_opt_out(from_number, "sms_keyword_opt_out")
                
                # Send confirmation
                try:
                    await self.send_sms(
                        to=from_number,
                        message="You've been unsubscribed. Reply START to resubscribe."
                    )
                except Exception as e:
                    logger.error(f"Failed to send opt-out confirmation: {e}")
                
            elif any(keyword in body for keyword in opt_in_keywords):
                await self.process_opt_in(from_number)
                
                # Send confirmation  
                try:
                    await self.send_sms(
                        to=from_number,
                        message="Welcome back! You're now subscribed to receive messages."
                    )
                except Exception as e:
                    logger.error(f"Failed to send opt-in confirmation: {e}")
            
            # Log incoming message
            if self.database_service:
                # Try to find associated lead
                db = await self.database_service.get_service()
                async with db.get_connection() as conn:
                    lead = await conn.fetchrow("""
                        SELECT id FROM leads WHERE phone = $1
                    """, from_number)
                    
                    lead_id = lead['id'] if lead else None
                    
                    await log_communication({
                        "lead_id": lead_id,
                        "channel": "sms",
                        "direction": "inbound",
                        "content": webhook_data.get("Body", ""),
                        "status": "received",
                        "metadata": {
                            "twilio_sid": message_sid,
                            "sender": from_number,
                            "recipient": to_number
                        }
                    })
            
            logger.info(f"Processed incoming SMS from {from_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process incoming webhook: {e}")
            return False
    
    # ============================================================================
    # Batch Operations
    # ============================================================================
    
    async def send_bulk_sms(self, recipients: List[Dict[str, Any]], 
                           batch_size: int = 10) -> List[Dict[str, Any]]:
        """Send SMS to multiple recipients in batches."""
        results = []
        
        # Process in batches to respect rate limits
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            # Create sending tasks
            tasks = []
            for recipient in batch:
                task = self.send_sms(
                    to=recipient["phone"],
                    message=recipient["message"],
                    lead_id=recipient.get("lead_id"),
                    campaign_id=recipient.get("campaign_id")
                )
                tasks.append(task)
            
            # Execute batch
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    recipient_result = {
                        "phone": batch[j]["phone"],
                        "lead_id": batch[j].get("lead_id"),
                        "success": not isinstance(result, Exception)
                    }
                    
                    if isinstance(result, Exception):
                        recipient_result["error"] = str(result)
                    else:
                        recipient_result["message_sid"] = result.sid
                        recipient_result["status"] = result.status.value
                    
                    results.append(recipient_result)
                
            except Exception as e:
                logger.error(f"Batch SMS sending failed: {e}")
                # Add failed results for the batch
                for recipient in batch:
                    results.append({
                        "phone": recipient["phone"],
                        "lead_id": recipient.get("lead_id"),
                        "success": False,
                        "error": str(e)
                    })
            
            # Delay between batches
            if i + batch_size < len(recipients):
                await asyncio.sleep(1)  # 1 second delay
        
        logger.info(f"Completed bulk SMS sending to {len(recipients)} recipients")
        return results
    
    # ============================================================================
    # Health Check & Monitoring
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Twilio service connectivity and status."""
        try:
            # Test account balance and account status
            account = self.sync_client.api.accounts(self.config.account_sid).fetch()
            
            # Test phone number capabilities
            phone_number = self.sync_client.incoming_phone_numbers.list(
                phone_number=self.config.phone_number
            )
            
            return {
                "status": "healthy",
                "account_status": account.status,
                "account_balance": account.balance if hasattr(account, 'balance') else None,
                "phone_number_active": len(phone_number) > 0,
                "opt_out_cache_size": len(self._opt_out_cache),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except TwilioRestException as e:
            return {
                "status": "unhealthy",
                "error": e.msg,
                "error_code": e.code,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get SMS usage statistics."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get usage records from Twilio
            usage_records = self.sync_client.usage.records.list(
                category='sms',
                start_date=start_date.date(),
                end_date=end_date.date()
            )
            
            total_messages = sum(int(record.count) for record in usage_records)
            total_cost = sum(float(record.price) for record in usage_records)
            
            return {
                "period_days": days,
                "total_messages_sent": total_messages,
                "total_cost": total_cost,
                "average_cost_per_message": total_cost / total_messages if total_messages > 0 else 0,
                "opt_out_count": len(self._opt_out_cache),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def test_twilio_client():
        """Test Twilio client functionality."""
        async with TwilioClient() as twilio:
            try:
                # Test phone validation
                phone_info = await twilio.validate_phone_number("+1234567890")
                print(f"Phone validation: {phone_info.valid} - {phone_info.carrier_type}")
                
                # Test SMS sending (be careful with real numbers!)
                # sms_result = await twilio.send_sms(
                #     to="+1234567890",
                #     message="Test message from Service 6",
                #     lead_id="test-lead-123"
                # )
                # print(f"SMS sent: {sms_result.sid}")
                
                # Test templated SMS
                # template_result = await twilio.send_templated_sms(
                #     to="+1234567890",
                #     template_name="instant_response",
                #     variables={"first_name": "John", "agent_name": "Sarah"}
                # )
                # print(f"Template SMS sent: {template_result.sid}")
                
                # Health check
                health = await twilio.health_check()
                print(f"Health: {health['status']}")
                
                # Usage stats
                usage = await twilio.get_usage_stats(days=7)
                print(f"Usage: {usage.get('total_messages_sent', 0)} messages")
                
            except Exception as e:
                print(f"Test failed: {e}")
    
    # Run test
    asyncio.run(test_twilio_client())