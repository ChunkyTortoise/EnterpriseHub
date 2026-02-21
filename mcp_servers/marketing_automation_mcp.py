"""
Marketing Automation MCP Server
Exposes marketing automation tools for email campaigns, lead nurturing, and analytics.

NOTE: This is a reference implementation / API design demo.
All data returned is simulated. Replace mock handlers with
real API integrations before production use.

Environment Variables Required:
- HUBSPOT_API_KEY: HubSpot API key
- MAILCHIMP_API_KEY: Mailchimp API key
- MAILCHIMP_SERVER_PREFIX: Mailchimp server prefix (e.g., us1)
- SENDGRID_API_KEY: SendGrid API key
- LINKEDIN_API_KEY: LinkedIn API key
- FACEBOOK_API_KEY: Facebook/Meta API key

Usage:
    python -m mcp_servers.marketing_automation_mcp
"""

import json
import os
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Create the MCP server
mcp = FastMCP("MarketingAutomation")


# =============================================================================
# Data Models
# =============================================================================


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class CampaignType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SOCIAL = "social"
    MULTI_CHANNEL = "multi_channel"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSITION = "proposition"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


@dataclass
class EmailCampaign:
    """Email campaign definition"""

    campaign_id: str
    name: str
    subject: str
    preheader: str
    body_html: str
    body_text: str
    from_name: str
    from_email: str
    reply_to: str
    status: CampaignStatus
    campaign_type: CampaignType
    scheduled_at: Optional[str]
    sent_at: Optional[str]
    recipient_count: int
    open_count: int
    click_count: int
    bounce_count: int
    unsubscribe_count: int


@dataclass
class CampaignMetrics:
    """Campaign performance metrics"""

    campaign_id: str
    campaign_name: str
    sent_count: int
    delivered_count: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    unsubscribe_rate: float
    conversion_count: int
    revenue_generated: float
    roas: float  # Return on ad spend
    period_start: str
    period_end: str


@dataclass
class LeadNurtureSequence:
    """Lead nurturing sequence"""

    sequence_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    trigger_condition: str
    is_active: bool
    enrolled_count: int
    completed_count: int
    conversion_rate: float


@dataclass
class ContactRecord:
    """Contact/lead information"""

    contact_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    status: LeadStatus
    lead_score: float
    source: str
    tags: List[str]
    properties: Dict[str, Any]
    created_at: str
    last_updated: str
    last_contacted: Optional[str]


@dataclass
class AutomationWorkflow:
    """Marketing automation workflow"""

    workflow_id: str
    name: str
    description: str
    trigger_type: str
    actions: List[Dict[str, Any]]
    is_active: bool
    enrollment_count: int
    completion_rate: float


# =============================================================================
# Email Client (HubSpot/Mailchimp/SendGrid - Mock implementation)
# =============================================================================


class EmailClient:
    """Client for email marketing platforms"""

    def __init__(self):
        self.hubspot_key = os.getenv("HUBSPOT_API_KEY", "")
        self.mailchimp_key = os.getenv("MAILCHIMP_API_KEY", "")
        self.mailchimp_server = os.getenv("MAILCHIMP_SERVER_PREFIX", "us1")
        self.sendgrid_key = os.getenv("SENDGRID_API_KEY", "")

    async def create_campaign(
        self, name: str, subject: str, body_html: str, from_name: str, from_email: str, recipient_list: List[str]
    ) -> EmailCampaign:
        """Create an email campaign"""
        # Mock - would use HubSpot/Mailchimp API
        campaign_id = f"CMP{self._generate_id()}"

        return EmailCampaign(
            campaign_id=campaign_id,
            name=name,
            subject=subject,
            preheader="",
            body_html=body_html,
            body_text=self._html_to_text(body_html),
            from_name=from_name,
            from_email=from_email,
            reply_to=from_email,
            status=CampaignStatus.DRAFT,
            campaign_type=CampaignType.EMAIL,
            scheduled_at=None,
            sent_at=None,
            recipient_count=len(recipient_list),
            open_count=0,
            click_count=0,
            bounce_count=0,
            unsubscribe_count=0,
        )

    async def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Send or schedule a campaign"""
        return {"campaign_id": campaign_id, "status": "scheduled", "scheduled_at": datetime.now().isoformat()}

    async def get_campaign_metrics(self, campaign_id: str) -> CampaignMetrics:
        """Get campaign performance metrics"""
        return CampaignMetrics(
            campaign_id=campaign_id,
            campaign_name="Sample Campaign",
            sent_count=1000,
            delivered_count=950,
            open_rate=0.35,
            click_rate=0.12,
            bounce_rate=0.05,
            unsubscribe_rate=0.01,
            conversion_count=25,
            revenue_generated=15000.0,
            roas=4.5,
            period_start="2026-01-01",
            period_end="2026-01-31",
        )

    async def get_all_campaigns(self, status: Optional[CampaignStatus] = None, limit: int = 20) -> List[EmailCampaign]:
        """Get all campaigns"""
        # Mock - would fetch from API
        return []

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        import re

        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _generate_id(self) -> str:
        return secrets.token_hex(8)


# =============================================================================
# CRM Client for Contacts
# =============================================================================


class CRMClient:
    """Client for CRM/contact management"""

    def __init__(self):
        self.hubspot_key = os.getenv("HUBSPOT_API_KEY", "")

    async def create_contact(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> ContactRecord:
        """Create a new contact"""
        contact_id = f"CNT{self._generate_id()}"

        return ContactRecord(
            contact_id=contact_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            status=LeadStatus.NEW,
            lead_score=0.0,
            source="mcp_server",
            tags=[],
            properties=properties or {},
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            last_contacted=None,
        )

    async def get_contact(self, contact_id: str) -> Optional[ContactRecord]:
        """Get contact by ID"""
        return ContactRecord(
            contact_id=contact_id,
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            status=LeadStatus.QUALIFIED,
            lead_score=75.0,
            source="website",
            tags=["buyer", "active"],
            properties={"budget": 500000, "preferred_areas": ["Rancho Cucamonga"]},
            created_at="2026-01-15T10:00:00Z",
            last_updated="2026-02-10T14:30:00Z",
            last_contacted="2026-02-12T09:00:00Z",
        )

    async def update_contact(self, contact_id: str, properties: Dict[str, Any]) -> ContactRecord:
        """Update contact properties"""
        contact = await self.get_contact(contact_id)
        if contact:
            contact.properties.update(properties)
            contact.last_updated = datetime.now().isoformat()
        return contact

    async def search_contacts(
        self,
        query: Optional[str] = None,
        status: Optional[LeadStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[ContactRecord]:
        """Search contacts"""
        return []

    async def add_contact_to_sequence(self, contact_id: str, sequence_id: str) -> Dict[str, Any]:
        """Add contact to a nurture sequence"""
        return {
            "contact_id": contact_id,
            "sequence_id": sequence_id,
            "enrolled_at": datetime.now().isoformat(),
            "status": "active",
        }

    def _generate_id(self) -> str:
        return secrets.token_hex(8)


# =============================================================================
# Analytics Client
# =============================================================================


class AnalyticsClient:
    """Client for marketing analytics"""

    def __init__(self):
        pass

    async def get_dashboard_summary(self, date_range: str = "30d") -> Dict[str, Any]:
        """Get analytics dashboard summary"""
        return {
            "date_range": date_range,
            "total_sent": 15000,
            "total_delivered": 14250,
            "avg_open_rate": 0.32,
            "avg_click_rate": 0.11,
            "total_conversions": 125,
            "total_revenue": 87500.0,
            "top_performing_campaigns": [
                {"name": "February Newsletter", "open_rate": 0.45},
                {"name": "New Listing Alert", "open_rate": 0.42},
                {"name": "Market Update", "open_rate": 0.38},
            ],
            "channel_breakdown": {
                "email": {"sent": 12000, "conversions": 100},
                "sms": {"sent": 2000, "conversions": 15},
                "social": {"sent": 1000, "conversions": 10},
            },
        }

    async def get_lead_source_metrics(self) -> List[Dict[str, Any]]:
        """Get lead source performance metrics"""
        return [
            {"source": "Website", "leads": 150, "conversion_rate": 0.12, "revenue": 45000},
            {"source": "Google Ads", "leads": 80, "conversion_rate": 0.08, "revenue": 24000},
            {"source": "Facebook", "leads": 60, "conversion_rate": 0.10, "revenue": 18000},
            {"source": "Referral", "leads": 40, "conversion_rate": 0.25, "revenue": 35000},
            {"source": "Zillow", "leads": 100, "conversion_rate": 0.15, "revenue": 52000},
        ]

    async def get_conversion_timeline(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get conversion metrics over time"""
        data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "conversions": 3 + (i % 7),
                    "revenue": 2000 + (i * 100),
                    "leads": 10 + (i % 5),
                }
            )
        return data


# =============================================================================
# Initialize clients
# =============================================================================

email_client = EmailClient()
crm_client = CRMClient()
analytics_client = AnalyticsClient()


def _sanitize_html(html: str) -> str:
    """Strip script tags from HTML to prevent XSS."""
    return re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)


# =============================================================================
# MCP Tools - Campaign Management
# =============================================================================


@mcp.tool()
async def create_email_campaign(
    name: str,
    subject: str,
    body_html: str,
    from_name: str,
    from_email: str,
    recipient_list: List[str],
    preheader: Optional[str] = None,
) -> str:
    """
    Create a new email campaign.

    Args:
        name: Campaign name
        subject: Email subject line
        body_html: HTML email body
        from_name: Sender display name
        from_email: Sender email address
        recipient_list: List of recipient email addresses
        preheader: Email preheader text

    Returns:
        JSON string containing campaign details
    """
    try:
        body_html = _sanitize_html(body_html)
        campaign = await email_client.create_campaign(
            name=name,
            subject=subject,
            body_html=body_html,
            from_name=from_name,
            from_email=from_email,
            recipient_list=recipient_list,
        )

        if preheader:
            campaign.preheader = preheader

        return json.dumps(asdict(campaign), indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def schedule_campaign(
    campaign_id: str,
    scheduled_at: str,  # ISO format
) -> str:
    """
    Schedule a campaign for sending.

    Args:
        campaign_id: The campaign ID
        scheduled_at: When to send (ISO 8601 format)

    Returns:
        JSON string confirming the scheduling
    """
    try:
        result = await email_client.send_campaign(campaign_id)
        result["scheduled_at"] = scheduled_at
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "campaign_id": campaign_id})


@mcp.tool()
async def send_campaign_now(campaign_id: str) -> str:
    """
    Send a campaign immediately.

    Args:
        campaign_id: The campaign ID

    Returns:
        JSON string confirming the send
    """
    try:
        result = await email_client.send_campaign(campaign_id)
        result["status"] = "sending"
        result["sent_at"] = datetime.now().isoformat()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "campaign_id": campaign_id})


@mcp.tool()
async def get_campaign_details(campaign_id: str) -> str:
    """
    Get detailed information about a campaign.

    Args:
        campaign_id: The campaign ID

    Returns:
        JSON string containing campaign details
    """
    try:
        campaigns = await email_client.get_all_campaigns(limit=100)
        for campaign in campaigns:
            if campaign.campaign_id == campaign_id:
                return json.dumps(asdict(campaign), indent=2, default=str)

        return json.dumps({"error": "Campaign not found", "campaign_id": campaign_id})
    except Exception as e:
        return json.dumps({"error": str(e), "campaign_id": campaign_id})


@mcp.tool()
async def get_campaign_performance(campaign_id: str) -> str:
    """
    Get performance metrics for a campaign.

    Args:
        campaign_id: The campaign ID

    Returns:
        JSON string containing performance metrics
    """
    try:
        metrics = await email_client.get_campaign_metrics(campaign_id)
        return json.dumps(asdict(metrics), indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "campaign_id": campaign_id})


@mcp.tool()
async def list_campaigns(status: Optional[str] = None, limit: int = 20) -> str:
    """
    List all email campaigns with optional filtering.

    Args:
        status: Filter by status (draft, scheduled, sent, etc.)
        limit: Maximum number of campaigns to return

    Returns:
        JSON string containing campaign list
    """
    try:
        status_enum = CampaignStatus(status) if status else None
        campaigns = await email_client.get_all_campaigns(status=status_enum, limit=limit)
        result = [asdict(c) for c in campaigns]
        return json.dumps({"campaigns": result, "count": len(result), "filter_status": status}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# MCP Tools - Contact Management
# =============================================================================


@mcp.tool()
async def create_contact(
    email: str,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a new contact in the CRM.

    Args:
        email: Contact email address
        first_name: First name
        last_name: Last name
        phone: Phone number
        properties: Additional properties

    Returns:
        JSON string containing contact details
    """
    try:
        contact = await crm_client.create_contact(
            email=email, first_name=first_name, last_name=last_name, phone=phone, properties=properties
        )
        return json.dumps(asdict(contact), indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_contact(contact_id: str) -> str:
    """
    Get contact details.

    Args:
        contact_id: The contact ID

    Returns:
        JSON string containing contact details
    """
    try:
        contact = await crm_client.get_contact(contact_id)
        if contact:
            return json.dumps(asdict(contact), indent=2, default=str)
        return json.dumps({"error": "Contact not found", "contact_id": contact_id})
    except Exception as e:
        return json.dumps({"error": str(e), "contact_id": contact_id})


@mcp.tool()
async def update_contact_properties(contact_id: str, properties: Dict[str, Any]) -> str:
    """
    Update contact properties.

    Args:
        contact_id: The contact ID
        properties: Properties to update

    Returns:
        JSON string containing updated contact
    """
    try:
        contact = await crm_client.update_contact(contact_id, properties)
        return json.dumps(asdict(contact), indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "contact_id": contact_id})


@mcp.tool()
async def search_contacts(
    query: Optional[str] = None, status: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 20
) -> str:
    """
    Search for contacts with filters.

    Args:
        query: Search query
        status: Filter by lead status
        tags: Filter by tags
        limit: Maximum results

    Returns:
        JSON string containing matching contacts
    """
    try:
        status_enum = LeadStatus(status) if status else None
        contacts = await crm_client.search_contacts(query=query, status=status_enum, tags=tags, limit=limit)
        result = [asdict(c) for c in contacts]
        return json.dumps({"contacts": result, "count": len(result)}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# MCP Tools - Lead Nurturing
# =============================================================================


@mcp.tool()
async def enroll_in_sequence(contact_id: str, sequence_name: str) -> str:
    """
    Enroll a contact in a lead nurturing sequence.

    Args:
        contact_id: The contact ID
        sequence_name: Name of the sequence

    Returns:
        JSON string confirming enrollment
    """
    try:
        # Get sequence ID from name
        sequences = {
            "welcome": "SEQ_WELCOME",
            "new_lead": "SEQ_NEW_LEAD",
            "follow_up": "SEQ_FOLLOW_UP",
            "reactivation": "SEQ_REACT",
            "post_showing": "SEQ_POST_SHOWING",
            "closing": "SEQ_CLOSING",
        }

        sequence_id = sequences.get(sequence_name.lower().replace(" ", "_"))
        if not sequence_id:
            return json.dumps(
                {"error": f"Unknown sequence: {sequence_name}", "available_sequences": list(sequences.keys())}
            )

        result = await crm_client.add_contact_to_sequence(contact_id, sequence_id)
        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_available_sequences() -> str:
    """
    Get list of available lead nurturing sequences.

    Returns:
        JSON string containing sequence definitions
    """
    sequences = [
        {
            "id": "SEQ_WELCOME",
            "name": "Welcome Series",
            "description": "Onboarding sequence for new leads",
            "steps": [
                {"day": 0, "action": "send_email", "template": "welcome"},
                {"day": 2, "action": "send_email", "template": "introductions"},
                {"day": 5, "action": "check_in", "template": "questions"},
            ],
            "is_active": True,
        },
        {
            "id": "SEQ_NEW_LEAD",
            "name": "New Lead Nurture",
            "description": "For leads from website/ads",
            "steps": [
                {"day": 0, "action": "send_email", "template": "thank_you"},
                {"day": 1, "action": "send_sms", "template": "quick_followup"},
                {"day": 3, "action": "send_email", "template": "market_info"},
                {"day": 7, "action": "task", "template": "call_schedule"},
            ],
            "is_active": True,
        },
        {
            "id": "SEQ_POST_SHOWING",
            "name": "Post-Showing Follow-up",
            "description": "Follow up after property showings",
            "steps": [
                {"day": 0, "action": "send_email", "template": "thank_you_showing"},
                {"day": 1, "action": "send_email", "template": "property_details"},
                {"day": 3, "action": "check_in", "template": "feedback"},
            ],
            "is_active": True,
        },
    ]

    return json.dumps({"sequences": sequences}, indent=2, default=str)


# =============================================================================
# MCP Tools - Analytics & Reporting
# =============================================================================


@mcp.tool()
async def get_analytics_dashboard(date_range: str = "30d") -> str:
    """
    Get marketing analytics dashboard summary.

    Args:
        date_range: Time period (7d, 30d, 90d, 1y)

    Returns:
        JSON string containing dashboard metrics
    """
    try:
        summary = await analytics_client.get_dashboard_summary(date_range)
        return json.dumps(summary, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_lead_source_performance() -> str:
    """
    Get performance metrics by lead source.

    Returns:
        JSON string containing source breakdown
    """
    try:
        metrics = await analytics_client.get_lead_source_metrics()
        return json.dumps(
            {
                "sources": metrics,
                "total_leads": sum(m["leads"] for m in metrics),
                "total_revenue": sum(m["revenue"] for m in metrics),
            },
            indent=2,
            default=str,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_conversion_timeline(days: int = 30) -> str:
    """
    Get conversion data over time.

    Args:
        days: Number of days to look back

    Returns:
        JSON string containing timeline data
    """
    try:
        timeline = await analytics_client.get_conversion_timeline(days)
        return json.dumps(
            {
                "timeline": timeline,
                "period_days": days,
                "total_conversions": sum(d["conversions"] for d in timeline),
                "total_revenue": sum(d["revenue"] for d in timeline),
            },
            indent=2,
            default=str,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# MCP Tools - Templates
# =============================================================================


@mcp.tool()
async def create_campaign_template(template_name: str, subject: str, body_html: str, category: str = "general") -> str:
    """
    Save a campaign template for reuse.

    Args:
        template_name: Name for the template
        subject: Default subject line
        body_html: HTML body
        category: Template category

    Returns:
        JSON string confirming template creation
    """
    body_html = _sanitize_html(body_html)
    template_id = "TPL" + secrets.token_hex(8)

    return json.dumps(
        {
            "template_id": template_id,
            "template_name": template_name,
            "subject": subject,
            "category": category,
            "created_at": datetime.now().isoformat(),
        }
    )


# =============================================================================
# MCP Resources
# =============================================================================


@mcp.resource("marketing://campaign-types")
async def get_campaign_types() -> str:
    """Get available campaign types"""
    return json.dumps(
        {
            "campaign_types": [
                {"value": ct.value, "description": desc}
                for ct, desc in [
                    (CampaignType.EMAIL, "Email marketing campaign"),
                    (CampaignType.SMS, "SMS text message campaign"),
                    (CampaignType.SOCIAL, "Social media campaign"),
                    (CampaignType.MULTI_CHANNEL, "Multi-channel campaign"),
                ]
            ]
        }
    )


@mcp.resource("marketing://lead-statuses")
async def get_lead_statuses() -> str:
    """Get available lead statuses"""
    return json.dumps(
        {
            "lead_statuses": [
                {"value": ls.value, "description": desc}
                for ls, desc in [
                    (LeadStatus.NEW, "New lead - not yet contacted"),
                    (LeadStatus.CONTACTED, "Initial contact made"),
                    (LeadStatus.QUALIFIED, "Lead has been qualified"),
                    (LeadStatus.PROPOSITION, "Proposal or offer made"),
                    (LeadStatus.NEGOTIATION, "In negotiation phase"),
                    (LeadStatus.CLOSED_WON, "Successfully closed"),
                    (LeadStatus.CLOSED_LOST, "Lost lead"),
                ]
            ]
        }
    )


# =============================================================================
# MCP Prompts
# =============================================================================


@mcp.prompt()
def generate_campaign_report() -> str:
    """Prompt for generating a campaign performance report"""
    return """
    Generate a detailed performance report for the following campaign:
    
    Campaign: {campaign_name}
    Period: {date_range}
    
    Include:
    1. Executive summary
    2. Key metrics (opens, clicks, conversions)
    3. Comparison to previous campaigns
    4. Recommendations for optimization
    5. ROI analysis
    """


@mcp.prompt()
def generate_lead_engagement_strategy() -> str:
    """Prompt for generating a lead engagement strategy"""
    return """
    Create a personalized lead engagement strategy for:
    
    Lead: {lead_name}
    Status: {lead_status}
    Lead Score: {lead_score}
    Interests: {interests}
    Budget: {budget}
    
    Include:
    1. Recommended communication channels
    2. Optimal contact frequency
    3. Content recommendations
    4. Next steps
    """


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import asyncio

        async def test():
            result = await get_analytics_dashboard("30d")
            print(result)

        asyncio.run(test())
    else:
        mcp.run()
