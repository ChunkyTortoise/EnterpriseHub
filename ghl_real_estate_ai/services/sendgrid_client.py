"""
Production SendGrid Client for Service 6 Lead Recovery & Nurture Engine.

Provides real SendGrid API integration for email communications:
- Email sending with templates and personalization
- Delivery tracking and engagement analytics
- Suppression list management
- CAN-SPAM compliance features
- Batch sending and automation
- Webhook event processing
"""

import asyncio
import base64
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientTimeout
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.database_service import DatabaseService, log_communication
from ghl_real_estate_ai.services.security_framework import SecurityFramework
from ghl_real_estate_ai.services.template_library_service import get_template_library_service

logger = get_logger(__name__)


class EmailStatus(Enum):
    """Email delivery status enumeration."""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    DROPPED = "dropped"
    SPAM_REPORT = "spamreport"
    UNSUBSCRIBE = "unsubscribe"
    GROUP_UNSUBSCRIBE = "group_unsubscribe"
    GROUP_RESUBSCRIBE = "group_resubscribe"


class SuppressionType(Enum):
    """Suppression list types."""
    BOUNCE = "bounces"
    BLOCK = "blocks"
    INVALID_EMAIL = "invalid_emails"
    SPAM_REPORT = "spam_reports"
    UNSUBSCRIBE = "global_unsubscribes"
    GROUP_UNSUBSCRIBE = "group_unsubscribes"


class SendGridConfig(BaseModel):
    """SendGrid client configuration."""
    
    api_key: str = Field(default_factory=lambda: settings.sendgrid_api_key)
    sender_email: str = Field(default_factory=lambda: settings.sendgrid_sender_email)
    sender_name: str = Field(default_factory=lambda: settings.sendgrid_sender_name)
    webhook_base_url: str = Field(default_factory=lambda: settings.webhook_base_url)
    template_ids: Dict[str, str] = {}
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_emails_per_minute: int = 1000
    
    @field_validator('api_key', 'sender_email')
    @classmethod
    def validate_required_fields(cls, v: str, info: ValidationInfo):
        if not v or v.startswith("your_sendgrid_"):
            raise ValueError(f"Valid SendGrid {info.field_name} is required")
        return v
    
    @field_validator('sender_email')
    @classmethod
    def validate_email_format(cls, v: str):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid sender email format")
        return v


class EmailMessage(BaseModel):
    """Email message model."""
    
    message_id: str
    to_email: str
    subject: str
    content: str
    status: EmailStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    template_id: Optional[str] = None
    campaign_id: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class EmailTemplate(BaseModel):
    """Email template model."""
    
    id: str
    name: str
    subject: str
    html_content: str
    plain_content: str
    variables: List[str] = []
    
    model_config = ConfigDict(extra="allow")


class SuppressionEntry(BaseModel):
    """Suppression list entry."""
    
    email: str
    created: datetime
    reason: Optional[str] = None
    suppression_type: SuppressionType
    
    model_config = ConfigDict(use_enum_values=True)


class SendGridAPIException(Exception):
    """SendGrid API specific exception."""
    
    def __init__(self, message: str, status_code: int = None, 
                 errors: List[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(self.message)


class SendGridClient:
    """
    Production SendGrid email client.
    
    Provides comprehensive email functionality with:
    - Template-based email sending
    - Personalization and dynamic content
    - Delivery tracking and analytics
    - Suppression list management
    - CAN-SPAM compliance
    - Batch operations and automation
    """
    
    def __init__(self, config: SendGridConfig = None,
                 cache_service: CacheService = None,
                 database_service: DatabaseService = None):
        """Initialize SendGrid client."""
        self.config = config or SendGridConfig()
        self.cache_service = cache_service or CacheService()
        self.database_service = database_service
        self.sg_client = sendgrid.SendGridAPIClient(api_key=self.config.api_key)
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_semaphore = asyncio.Semaphore(self.config.rate_limit_emails_per_minute)
        
        # In-memory suppression cache
        self._suppression_cache = {
            SuppressionType.UNSUBSCRIBE: set(),
            SuppressionType.BOUNCE: set(),
            SuppressionType.SPAM_REPORT: set(),
            SuppressionType.INVALID_EMAIL: set()
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        await self._load_suppressions()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if not self.session:
            timeout = ClientTimeout(total=self.config.timeout)
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            )
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _load_suppressions(self):
        """Load suppression lists into memory cache."""
        try:
            # Load critical suppressions for fast checking
            for suppression_type in [SuppressionType.UNSUBSCRIBE, SuppressionType.BOUNCE]:
                suppressions = await self._fetch_suppressions(suppression_type)
                self._suppression_cache[suppression_type] = {
                    entry.email for entry in suppressions
                }
            
            total_suppressions = sum(
                len(emails) for emails in self._suppression_cache.values()
            )
            logger.info(f"Loaded {total_suppressions} suppressed email addresses")
            
        except Exception as e:
            logger.error(f"Failed to load suppressions: {e}")
    
    async def _make_request(self, method: str, endpoint: str,
                          data: Dict[str, Any] = None,
                          params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to SendGrid API."""
        await self._ensure_session()
        
        url = f"https://api.sendgrid.com/v3/{endpoint.lstrip('/')}"
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if method.upper() == "GET":
                    async with self.session.get(url, params=params) as response:
                        return await self._handle_response(response)
                elif method.upper() == "POST":
                    async with self.session.post(url, json=data, params=params) as response:
                        return await self._handle_response(response)
                elif method.upper() == "DELETE":
                    async with self.session.delete(url, json=data, params=params) as response:
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"SendGrid API request failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise SendGridAPIException(f"Network error after {self.config.max_retries} retries: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error in SendGrid API request: {e}")
                raise SendGridAPIException(f"Unexpected error: {e}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle SendGrid API response."""
        try:
            if response.content_type == 'application/json':
                response_data = await response.json()
            else:
                response_text = await response.text()
                response_data = {"message": response_text}
        except Exception:
            response_data = {}
        
        if response.status in [200, 201, 202]:
            return response_data
        elif response.status == 429:
            raise SendGridAPIException("Rate limit exceeded", response.status)
        elif response.status in [401, 403]:
            raise SendGridAPIException("Authentication failed", response.status)
        else:
            error_msg = response_data.get("errors", [{}])[0].get("message", f"HTTP {response.status}")
            raise SendGridAPIException(error_msg, response.status, response_data.get("errors", []))
    
    # ============================================================================
    # Email Sending
    # ============================================================================
    
    async def send_email(self, to_email: str, subject: str, 
                        html_content: str = None, plain_content: str = None,
                        template_id: str = None, dynamic_template_data: Dict[str, Any] = None,
                        lead_id: str = None, campaign_id: str = None,
                        attachments: List[Dict[str, Any]] = None) -> EmailMessage:
        """
        Send email with optional template and tracking.
        
        Args:
            to_email: Recipient email address
            subject: Email subject (ignored if using template)
            html_content: HTML email content
            plain_content: Plain text email content
            template_id: SendGrid template ID
            dynamic_template_data: Variables for template
            lead_id: Associated lead ID
            campaign_id: Associated campaign ID
            attachments: List of attachment dictionaries
            
        Returns:
            EmailMessage with delivery status
        """
        # Check suppression status
        if await self._is_suppressed(to_email):
            raise SendGridAPIException(f"Email {to_email} is suppressed")
        
        # Rate limiting
        async with self._rate_limit_semaphore:
            try:
                # Build email message
                message = Mail()
                message.from_email = Email(self.config.sender_email, self.config.sender_name)
                message.to = To(to_email)
                
                if template_id:
                    # Use dynamic template
                    message.template_id = template_id
                    if dynamic_template_data:
                        message.dynamic_template_data = dynamic_template_data
                else:
                    # Use content directly
                    message.subject = subject
                    if html_content:
                        message.content = Content("text/html", html_content)
                    elif plain_content:
                        message.content = Content("text/plain", plain_content)
                    else:
                        raise ValueError("Either template_id or content must be provided")
                
                # Add attachments
                if attachments:
                    for attachment_data in attachments:
                        attachment = Attachment()
                        attachment.file_content = FileContent(attachment_data["content"])
                        attachment.file_name = FileName(attachment_data["filename"])
                        attachment.file_type = FileType(attachment_data.get("type", "application/octet-stream"))
                        message.attachment = attachment
                
                # Configure tracking
                message.tracking_settings = {
                    "click_tracking": {"enable": True, "enable_text": False},
                    "open_tracking": {"enable": True, "substitution_tag": "%open_track%"},
                    "subscription_tracking": {
                        "enable": True,
                        "text": "Unsubscribe",
                        "html": "<a href='%unsubscribe_url%'>Unsubscribe</a>",
                        "substitution_tag": "%unsubscribe_url%"
                    }
                }
                
                # Send email
                response = self.sg_client.send(message)
                
                # Extract message ID from headers
                message_id = response.headers.get('X-Message-Id', '')
                
                # Create email message object
                email_message = EmailMessage(
                    message_id=message_id,
                    to_email=to_email,
                    subject=subject or f"Template {template_id}",
                    content=html_content or plain_content or f"Dynamic template {template_id}",
                    status=EmailStatus.QUEUED if response.status_code == 202 else EmailStatus.SENT,
                    sent_at=datetime.utcnow(),
                    template_id=template_id,
                    campaign_id=campaign_id
                )
                
                # Log to database
                if self.database_service and lead_id:
                    await log_communication({
                        "lead_id": lead_id,
                        "channel": "email",
                        "direction": "outbound",
                        "content": subject or f"Template {template_id}",
                        "status": email_message.status if isinstance(email_message.status, str) else email_message.status.value,
                        "campaign_id": campaign_id,
                        "template_id": template_id,
                        "metadata": {
                            "sendgrid_message_id": message_id,
                            "recipient": to_email,
                            "template_data": dynamic_template_data
                        }
                    })
                
                masked_email = f"{to_email[:3]}***@{to_email.split('@')[-1]}" if '@' in to_email else "***"
                logger.info(f"Email sent to {masked_email}, Message ID: {message_id}")
                return email_message
                
            except Exception as e:
                logger.error(f"SendGrid email sending failed: {e}")
                raise SendGridAPIException(f"Email sending failed: {e}")
    
    async def send_templated_email(self, to_email: str, template_name: str,
                                 variables: Dict[str, Any] = None,
                                 lead_id: str = None,
                                 campaign_id: str = None) -> EmailMessage:
        """Send email using predefined template from TemplateLibraryService."""
        template_service = await get_template_library_service()
        
        # Search for template by name
        templates = await template_service.search_templates({"name": template_name, "type": "email"})
        
        if not templates:
            # Fallback to hardcoded templates (deprecated)
            template = await self._get_hardcoded_template(template_name)
            if not template:
                raise SendGridAPIException(f"Template '{template_name}' not found")
            
            # Use template ID if available, otherwise use content
            if template.get("sendgrid_id"):
                return await self.send_email(
                    to_email=to_email,
                    subject="",  # Template handles subject
                    template_id=template["sendgrid_id"],
                    dynamic_template_data=variables or {},
                    lead_id=lead_id,
                    campaign_id=campaign_id
                )
            else:
                # Use template content with variable substitution
                html_content = template["html_content"]
                plain_content = template["plain_content"]
                subject = template["subject"]
                
                if variables:
                    for key, value in variables.items():
                        html_content = html_content.replace(f"{{{{{key}}}}}", str(value))
                        plain_content = plain_content.replace(f"{{{{{key}}}}}", str(value))
                        subject = subject.replace(f"{{{{{key}}}}}", str(value))
                
                return await self.send_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    plain_content=plain_content,
                    lead_id=lead_id,
                    campaign_id=campaign_id
                )
        else:
            # Use matching template from database
            template = templates[0]
            rendered = await template_service.render_template(template.id, variables or {})
            
            return await self.send_email(
                to_email=to_email,
                subject=rendered.get("subject", ""),
                html_content=rendered["content"],
                lead_id=lead_id,
                campaign_id=campaign_id,
                template_id=template.id
            )
    
    async def _get_hardcoded_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get hardcoded email template (deprecated)."""
        # Predefined templates for Service 6
        templates = {
            "welcome": {
                "id": "template_welcome",
                "sendgrid_id": self.config.template_ids.get("welcome"),
                "subject": "Welcome {{first_name}}! Let's find your perfect property",
                "html_content": "<html><body><h2>Hi {{first_name}}!</h2><p>Welcome to our service.</p></body></html>",
                "plain_content": "Hi {{first_name}}! Welcome to our service.",
                "variables": ["first_name"]
            }
        }
        return templates.get(template_name)
    
    # ============================================================================
    # Suppression Management
    # ============================================================================
    
    async def _is_suppressed(self, email: str) -> bool:
        """Check if email is on any suppression list."""
        email_lower = email.lower()
        
        for suppression_type, emails in self._suppression_cache.items():
            if email_lower in emails:
                masked_email = f"{email[:3]}***@{email.split('@')[-1]}" if '@' in email else "***"
                logger.info(f"Email {masked_email} is suppressed: {suppression_type.value}")
                return True
        
        return False
    
    async def _fetch_suppressions(self, suppression_type: SuppressionType) -> List[SuppressionEntry]:
        """Fetch suppression list from SendGrid."""
        try:
            response = await self._make_request("GET", f"/suppression/{suppression_type.value}")
            
            suppressions = []
            for item in response:
                suppressions.append(SuppressionEntry(
                    email=item["email"],
                    created=datetime.fromtimestamp(item["created"]),
                    reason=item.get("reason"),
                    suppression_type=suppression_type
                ))
            
            return suppressions
            
        except Exception as e:
            logger.error(f"Failed to fetch {suppression_type.value} suppressions: {e}")
            return []
    
    async def add_to_suppression(self, emails: List[str], 
                               suppression_type: SuppressionType,
                               reason: str = None) -> bool:
        """Add emails to suppression list."""
        try:
            # Prepare data for API
            suppression_data = []
            for email in emails:
                entry = {"email": email.lower()}
                if reason:
                    entry["reason"] = reason
                suppression_data.append(entry)
            
            # Add to SendGrid suppression list
            await self._make_request("POST", f"/suppression/{suppression_type.value}", 
                                   data=suppression_data)
            
            # Update local cache
            self._suppression_cache[suppression_type].update(email.lower() for email in emails)
            
            logger.info(f"Added {len(emails)} emails to {suppression_type.value} suppression list")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add suppressions: {e}")
            return False
    
    async def remove_from_suppression(self, emails: List[str],
                                    suppression_type: SuppressionType) -> bool:
        """Remove emails from suppression list."""
        try:
            # Remove from SendGrid
            for email in emails:
                await self._make_request("DELETE", f"/suppression/{suppression_type.value}/{email.lower()}")
            
            # Update local cache
            for email in emails:
                self._suppression_cache[suppression_type].discard(email.lower())
            
            logger.info(f"Removed {len(emails)} emails from {suppression_type.value} suppression list")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove suppressions: {e}")
            return False
    
    # ============================================================================
    # Webhook Processing
    # ============================================================================
    
    async def process_event_webhook(self, request: Request, events: List[Dict[str, Any]]) -> bool:
        """Process SendGrid event webhook with signature verification."""
        # Step 1: Verify webhook signature BEFORE processing
        security = SecurityFramework()
        try:
            if not await security.verify_webhook_signature(request, "sendgrid"):
                logger.error("Invalid SendGrid event webhook signature")
                raise HTTPException(401, "Invalid signature")
        finally:
            await security.close_redis()

        # Step 2: Continue with existing logic
        try:
            for event in events:
                event_type = event.get("event")
                email = event.get("email")
                timestamp = datetime.fromtimestamp(event.get("timestamp", 0))
                sg_message_id = event.get("sg_message_id")
                
                if not all([event_type, email, sg_message_id]):
                    logger.warning(f"Incomplete webhook event: {event}")
                    continue
                
                # Update database record
                if self.database_service:
                    db = await self.database_service.get_service()
                    async with db.transaction() as conn:
                        # Find communication record
                        comm_record = await conn.fetchrow("""
                            SELECT id FROM communication_logs 
                            WHERE metadata->>'sendgrid_message_id' = $1
                        """, sg_message_id)
                        
                        if comm_record:
                            # Update status and timestamps
                            update_data = {"status": event_type}
                            
                            if event_type == "delivered":
                                update_data["delivered_at"] = timestamp
                            elif event_type == "opened":
                                update_data["metadata"] = json.dumps({
                                    "opened_at": timestamp.isoformat(),
                                    "user_agent": event.get("useragent"),
                                    "ip": event.get("ip")
                                })
                            elif event_type == "click":
                                update_data["metadata"] = json.dumps({
                                    "clicked_at": timestamp.isoformat(),
                                    "clicked_url": event.get("url"),
                                    "user_agent": event.get("useragent")
                                })
                            elif event_type in ["bounce", "dropped", "spamreport"]:
                                update_data["metadata"] = json.dumps({
                                    "failed_at": timestamp.isoformat(),
                                    "reason": event.get("reason"),
                                    "bounce_type": event.get("type"),
                                    "smtp_id": event.get("smtp-id")
                                })
                            
                            # Build update query
                            set_clauses = ["updated_at = NOW()"]
                            values = []
                            param_count = 1
                            
                            for field, value in update_data.items():
                                if field == "metadata":
                                    set_clauses.append(f"metadata = metadata || ${param_count}")
                                else:
                                    set_clauses.append(f"{field} = ${param_count}")
                                values.append(value)
                                param_count += 1
                            
                            values.append(comm_record['id'])
                            
                            await conn.execute(f"""
                                UPDATE communication_logs 
                                SET {', '.join(set_clauses)}
                                WHERE id = ${param_count}
                            """, *values)
                
                # Handle automatic suppression events
                if event_type in ["unsubscribe", "spamreport", "bounce"]:
                    if event_type == "unsubscribe":
                        suppression_type = SuppressionType.UNSUBSCRIBE
                    elif event_type == "spamreport":
                        suppression_type = SuppressionType.SPAM_REPORT
                    elif event_type == "bounce" and event.get("type") == "block":
                        suppression_type = SuppressionType.BOUNCE
                    else:
                        continue  # Skip soft bounces
                    
                    await self.add_to_suppression([email], suppression_type, 
                                                event.get("reason", f"auto_{event_type}"))
                
                masked_email = f"{email[:3]}***@{email.split('@')[-1]}" if '@' in email else "***"
                logger.debug(f"Processed {event_type} event for {masked_email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process event webhook: {e}")
            raise  # Re-raise to propagate error to caller
    
    # ============================================================================
    # Analytics & Reporting
    # ============================================================================
    
    async def get_email_stats(self, start_date: datetime = None, 
                            end_date: datetime = None) -> Dict[str, Any]:
        """Get email delivery and engagement statistics."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get stats from SendGrid
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "aggregated_by": "day"
            }
            
            stats = await self._make_request("GET", "/stats", params=params)
            
            # Aggregate statistics
            total_stats = {
                "requests": 0,
                "delivered": 0,
                "bounces": 0,
                "opens": 0,
                "unique_opens": 0,
                "clicks": 0,
                "unique_clicks": 0,
                "unsubscribes": 0,
                "spam_reports": 0
            }
            
            for day_stats in stats:
                for metric in day_stats.get("stats", []):
                    for key in total_stats.keys():
                        total_stats[key] += metric.get(key, 0)
            
            # Calculate rates
            delivered = total_stats["delivered"]
            if delivered > 0:
                open_rate = (total_stats["unique_opens"] / delivered) * 100
                click_rate = (total_stats["unique_clicks"] / delivered) * 100
                unsubscribe_rate = (total_stats["unsubscribes"] / delivered) * 100
            else:
                open_rate = click_rate = unsubscribe_rate = 0.0
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "totals": total_stats,
                "rates": {
                    "delivery_rate": (delivered / total_stats["requests"] * 100) if total_stats["requests"] > 0 else 0,
                    "bounce_rate": (total_stats["bounces"] / total_stats["requests"] * 100) if total_stats["requests"] > 0 else 0,
                    "open_rate": open_rate,
                    "click_rate": click_rate,
                    "unsubscribe_rate": unsubscribe_rate
                },
                "suppression_counts": {
                    suppression_type.value: len(emails) 
                    for suppression_type, emails in self._suppression_cache.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get email stats: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # Batch Operations
    # ============================================================================
    
    async def send_bulk_emails(self, emails: List[Dict[str, Any]], 
                             batch_size: int = 100) -> List[Dict[str, Any]]:
        """Send emails in batches to respect rate limits."""
        results = []
        
        # Process in batches
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            
            # Create sending tasks
            tasks = []
            for email_data in batch:
                if email_data.get("template_name"):
                    task = self.send_templated_email(
                        to_email=email_data["to_email"],
                        template_name=email_data["template_name"],
                        variables=email_data.get("variables", {}),
                        lead_id=email_data.get("lead_id"),
                        campaign_id=email_data.get("campaign_id")
                    )
                else:
                    task = self.send_email(
                        to_email=email_data["to_email"],
                        subject=email_data["subject"],
                        html_content=email_data.get("html_content"),
                        plain_content=email_data.get("plain_content"),
                        template_id=email_data.get("template_id"),
                        dynamic_template_data=email_data.get("dynamic_template_data"),
                        lead_id=email_data.get("lead_id"),
                        campaign_id=email_data.get("campaign_id")
                    )
                tasks.append(task)
            
            # Execute batch
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    email_result = {
                        "to_email": batch[j]["to_email"],
                        "lead_id": batch[j].get("lead_id"),
                        "success": not isinstance(result, Exception)
                    }
                    
                    if isinstance(result, Exception):
                        email_result["error"] = str(result)
                    else:
                        email_result["message_id"] = result.message_id
                        email_result["status"] = result.status if isinstance(result.status, str) else result.status.value
                    
                    results.append(email_result)
                
            except Exception as e:
                logger.error(f"Batch email sending failed: {e}")
                # Add failed results for the batch
                for email_data in batch:
                    results.append({
                        "to_email": email_data["to_email"],
                        "lead_id": email_data.get("lead_id"),
                        "success": False,
                        "error": str(e)
                    })
            
            # Delay between batches
            if i + batch_size < len(emails):
                await asyncio.sleep(0.1)  # 100ms delay
        
        logger.info(f"Completed bulk email sending to {len(emails)} recipients")
        return results
    
    # ============================================================================
    # Health Check
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SendGrid service connectivity and status."""
        try:
            # Test API connectivity
            response = await self._make_request("GET", "/user/profile")
            
            # Check suppression cache status
            total_suppressions = sum(len(emails) for emails in self._suppression_cache.values())
            
            return {
                "status": "healthy",
                "api_accessible": True,
                "user_profile": response.get("username"),
                "suppression_cache_loaded": total_suppressions > 0,
                "total_suppressions": total_suppressions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except SendGridAPIException as e:
            return {
                "status": "unhealthy",
                "api_accessible": e.status_code not in [401, 403],
                "error": e.message,
                "status_code": e.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def test_sendgrid_client():
        """Test SendGrid client functionality."""
        async with SendGridClient() as sg:
            try:
                # Test templated email
                # email_result = await sg.send_templated_email(
                #     to_email="test@example.com",
                #     template_name="welcome",
                #     variables={"first_name": "John", "agent_name": "Sarah", "agent_phone": "555-1234"},
                #     lead_id="test-lead-123"
                # )
                # print(f"Email sent: {email_result.message_id}")
                
                # Get email stats
                stats = await sg.get_email_stats(days=7)
                print(f"Email stats: {stats.get('rates', {}).get('open_rate', 0):.2f}% open rate")
                
                # Health check
                health = await sg.health_check()
                print(f"Health: {health['status']}")
                
            except Exception as e:
                print(f"Test failed: {e}")
    
    # Run test
    asyncio.run(test_sendgrid_client())