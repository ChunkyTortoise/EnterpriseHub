"""
Real Estate Workflow Templates Library

Pre-built, industry-specific workflow templates for real estate automation.
Includes proven sequences for lead nurturing, client onboarding, and sales cycles.

Templates include:
- Lead nurturing sequences
- Buyer journey workflows
- Seller engagement flows
- Investor outreach campaigns
- Post-closing follow-up
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class WorkflowCategory(Enum):
    """Workflow template categories"""

    LEAD_NURTURING = "lead_nurturing"
    BUYER_JOURNEY = "buyer_journey"
    SELLER_ENGAGEMENT = "seller_engagement"
    INVESTOR_OUTREACH = "investor_outreach"
    POST_CLOSING = "post_closing"
    REFERRAL_GENERATION = "referral_generation"
    MARKET_UPDATE = "market_update"


class LeadType(Enum):
    """Lead type classifications"""

    FIRST_TIME_BUYER = "first_time_buyer"
    REPEAT_BUYER = "repeat_buyer"
    SELLER = "seller"
    INVESTOR = "investor"
    LUXURY_CLIENT = "luxury_client"
    COMMERCIAL = "commercial"


@dataclass
class WorkflowTemplate:
    """Workflow template definition"""

    template_id: str
    name: str
    description: str
    category: WorkflowCategory
    target_lead_types: List[LeadType]
    estimated_duration_days: int
    steps: List[Dict[str, Any]]
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    customization_options: Dict[str, Any] = field(default_factory=dict)
    is_premium: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class WorkflowTemplateLibrary:
    """Library of real estate workflow templates"""

    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize all workflow templates"""

        # Lead Nurturing Templates
        self._create_new_lead_welcome_sequence()
        self._create_long_term_nurture_sequence()
        self._create_hot_lead_acceleration()

        # Buyer Journey Templates
        self._create_first_time_buyer_education()
        self._create_luxury_buyer_experience()
        self._create_investor_opportunity_flow()

        # Seller Engagement Templates
        self._create_listing_preparation_sequence()
        self._create_price_reduction_campaign()
        self._create_expired_listing_revival()

        # Post-Closing Templates
        self._create_post_closing_satisfaction()
        self._create_referral_request_sequence()

        # Market Update Templates
        self._create_monthly_market_updates()

    def _create_new_lead_welcome_sequence(self):
        """Create new lead welcome sequence template"""

        steps = [
            {
                "id": "welcome_1",
                "name": "Immediate Welcome SMS",
                "type": "smart_sms",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "message": "Hi {{first_name}}! Thanks for your interest in {{property_type}}. I'm {{agent_name}}, your local real estate expert. I'll help you find the perfect property! 🏡",
                    "sender_id": "RealEstate",
                },
                "branches": [
                    {
                        "name": "SMS Delivered",
                        "conditions": [{"field": "sms_delivered", "operator": "is_true", "value": True}],
                        "next_step_id": "welcome_2",
                    }
                ],
            },
            {
                "id": "welcome_2",
                "name": "Welcome Email with Resources",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 1800},  # 30 minutes
                "config": {
                    "subject": "Welcome to your property search, {{first_name}}!",
                    "template_id": "new_lead_welcome",
                    "content_template": """
Hi {{first_name}},

Welcome to your property search journey! I'm excited to help you find your perfect {{property_type}} in {{location_preference}}.

**What's Next:**
🔍 I'm already searching for properties that match your criteria
📊 I'll send you a personalized market report
📞 Let's schedule a quick call to discuss your needs

**Your Search Criteria:**
• Budget: {{budget_range}}
• Location: {{location_preference}}
• Property Type: {{property_type}}

I'll be in touch soon with some great options!

Best regards,
{{agent_name}}
{{agent_phone}}
                    """,
                },
                "branches": [
                    {
                        "name": "Email Opened",
                        "conditions": [{"field": "email_opened", "operator": "is_true", "value": True}],
                        "next_step_id": "welcome_3_engaged",
                    },
                    {
                        "name": "Email Not Opened",
                        "conditions": [{"field": "hours_since_last_step", "operator": "greater_than", "value": 24}],
                        "next_step_id": "welcome_3_followup",
                    },
                ],
            },
            {
                "id": "welcome_3_engaged",
                "name": "Engaged Lead - Property Matches",
                "type": "property_matching",
                "delay_config": {"type": "fixed", "seconds": 3600},  # 1 hour
                "config": {"max_properties": 5, "include_new_listings": True, "personalization_level": "high"},
                "branches": [
                    {
                        "name": "Properties Found",
                        "conditions": [{"field": "property_matches.count", "operator": "greater_than", "value": 0}],
                        "next_step_id": "send_property_matches",
                    }
                ],
            },
            {
                "id": "welcome_3_followup",
                "name": "Follow-up SMS",
                "type": "smart_sms",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "message": "{{first_name}}, did you get my email? I have some great {{property_type}} options to show you. When's a good time to chat? 📱"
                },
                "branches": [
                    {
                        "name": "SMS Response",
                        "conditions": [{"field": "sms_replied", "operator": "is_true", "value": True}],
                        "next_step_id": "schedule_call",
                    }
                ],
            },
            {
                "id": "send_property_matches",
                "name": "Send Property Recommendations",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "subject": "{{property_matches.count}} perfect properties for you!",
                    "template_id": "property_recommendations",
                    "attach_property_details": True,
                },
            },
            {
                "id": "schedule_call",
                "name": "Schedule Consultation Call",
                "type": "create_task",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "title": "Schedule consultation call with {{first_name}} {{last_name}}",
                    "description": "Follow up on property search interest",
                    "priority": "high",
                    "due_date_offset_hours": 24,
                },
            },
        ]

        template = WorkflowTemplate(
            template_id="new_lead_welcome",
            name="New Lead Welcome Sequence",
            description="Comprehensive 3-step welcome sequence for new property leads with intelligent branching based on engagement",
            category=WorkflowCategory.LEAD_NURTURING,
            target_lead_types=[LeadType.FIRST_TIME_BUYER, LeadType.REPEAT_BUYER],
            estimated_duration_days=2,
            steps=steps,
            triggers=[
                {
                    "type": "lead_created",
                    "conditions": [
                        {"field": "source", "operator": "in", "value": ["website", "zillow", "realtor.com"]}
                    ],
                }
            ],
            success_metrics=["email_opened", "sms_response", "call_scheduled", "property_viewing_requested"],
            customization_options={
                "timing_adjustments": True,
                "message_personalization": True,
                "property_matching_criteria": True,
            },
        )

        self.templates[template.template_id] = template

    def _create_long_term_nurture_sequence(self):
        """Create long-term nurture sequence for leads not ready to buy immediately"""

        steps = [
            {
                "id": "nurture_1",
                "name": "Market Insights Email",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "subject": "{{location_preference}} Market Update - {{month_year}}",
                    "template_id": "market_insights",
                    "content_template": """
Hi {{first_name}},

Hope you're doing well! I wanted to share some interesting market trends in {{location_preference}} that might interest you.

**This Month's Highlights:**
📈 Median home price: ${{median_price}}
📊 Average days on market: {{avg_days_on_market}}
🏠 New listings: {{new_listings_count}}

**What This Means for You:**
{{market_analysis_summary}}

I'm always here when you're ready to take the next step in your property search.

Best,
{{agent_name}}
                    """,
                },
            },
            {
                "id": "nurture_2",
                "name": "Educational Content",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 604800},  # 1 week
                "config": {
                    "subject": "{{property_type}} buying guide for {{location_preference}}",
                    "template_id": "buyer_education",
                    "attach_pdf_guide": True,
                },
            },
            {
                "id": "nurture_3",
                "name": "Soft Check-in SMS",
                "type": "smart_sms",
                "delay_config": {"type": "fixed", "seconds": 1209600},  # 2 weeks
                "config": {
                    "message": "Hi {{first_name}}, any updates on your {{property_type}} search? I came across a few interesting properties that might fit your criteria 🏡"
                },
                "branches": [
                    {
                        "name": "Positive Response",
                        "conditions": [
                            {"field": "sms_replied", "operator": "is_true", "value": True},
                            {"field": "sentiment_analysis.positive", "operator": "is_true", "value": True},
                        ],
                        "next_step_id": "send_new_listings",
                    }
                ],
            },
            {
                "id": "send_new_listings",
                "name": "Send New Listings",
                "type": "property_matching",
                "delay_config": {"type": "fixed", "seconds": 3600},  # 1 hour
                "config": {"max_properties": 3, "only_new_listings": True, "days_back": 7},
            },
        ]

        template = WorkflowTemplate(
            template_id="long_term_nurture",
            name="Long-Term Lead Nurture",
            description="Monthly nurture sequence for leads in early research phase",
            category=WorkflowCategory.LEAD_NURTURING,
            target_lead_types=[LeadType.FIRST_TIME_BUYER, LeadType.REPEAT_BUYER],
            estimated_duration_days=90,
            steps=steps,
            triggers=[
                {
                    "type": "lead_score_based",
                    "conditions": [
                        {"field": "lead_score", "operator": "less_than", "value": 40},
                        {"field": "timeline", "operator": "contains", "value": "6 months"},
                    ],
                }
            ],
            success_metrics=["email_engagement", "property_inquiries", "lead_score_increase"],
            customization_options={
                "frequency_adjustment": True,
                "content_personalization": True,
                "market_focus_areas": True,
            },
        )

        self.templates[template.template_id] = template

    def _create_hot_lead_acceleration(self):
        """Create acceleration sequence for hot leads"""

        steps = [
            {
                "id": "hot_lead_1",
                "name": "Immediate Personal Outreach",
                "type": "create_task",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "title": "URGENT: Call hot lead {{first_name}} {{last_name}}",
                    "description": "Lead score: {{lead_score}} - High intent detected",
                    "priority": "urgent",
                    "assignee": "top_agent",
                    "due_date_offset_hours": 1,
                },
            },
            {
                "id": "hot_lead_2",
                "name": "Premium Properties Email",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 1800},  # 30 minutes
                "config": {
                    "subject": "Exclusive properties matching your criteria",
                    "template_id": "premium_listings",
                    "priority": "high",
                    "include_virtual_tours": True,
                },
            },
            {
                "id": "hot_lead_3",
                "name": "Direct Call Attempt",
                "type": "voice_call",
                "delay_config": {"type": "fixed", "seconds": 3600},  # 1 hour
                "config": {
                    "script_template": "personal_introduction",
                    "max_attempts": 3,
                    "attempt_interval": 1800,  # 30 minutes between attempts
                },
                "branches": [
                    {
                        "name": "Call Connected",
                        "conditions": [{"field": "call_connected", "operator": "is_true", "value": True}],
                        "next_step_id": "schedule_showing",
                    },
                    {
                        "name": "No Answer",
                        "conditions": [
                            {"field": "call_attempts", "operator": "equals", "value": 3},
                            {"field": "call_connected", "operator": "is_false", "value": False},
                        ],
                        "next_step_id": "voicemail_followup",
                    },
                ],
            },
            {
                "id": "schedule_showing",
                "name": "Schedule Property Showing",
                "type": "create_calendar_event",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "event_type": "property_showing",
                    "duration_minutes": 60,
                    "suggested_times": ["tomorrow_morning", "tomorrow_afternoon", "weekend"],
                },
            },
            {
                "id": "voicemail_followup",
                "name": "Voicemail Follow-up SMS",
                "type": "smart_sms",
                "delay_config": {"type": "fixed", "seconds": 1800},  # 30 minutes
                "config": {
                    "message": "{{first_name}}, I left you a voicemail about some amazing {{property_type}} options. Text me back for immediate access to exclusive listings! 🏠"
                },
            },
        ]

        template = WorkflowTemplate(
            template_id="hot_lead_acceleration",
            name="Hot Lead Acceleration",
            description="Rapid response sequence for high-intent leads requiring immediate attention",
            category=WorkflowCategory.LEAD_NURTURING,
            target_lead_types=[LeadType.REPEAT_BUYER, LeadType.LUXURY_CLIENT],
            estimated_duration_days=1,
            steps=steps,
            triggers=[
                {
                    "type": "score_based",
                    "conditions": [{"field": "lead_score", "operator": "greater_than", "value": 75}],
                },
                {
                    "type": "behavior_based",
                    "conditions": [
                        {"field": "property_views", "operator": "greater_than", "value": 5},
                        {"field": "last_activity_hours", "operator": "less_than", "value": 2},
                    ],
                },
            ],
            success_metrics=["call_connected", "showing_scheduled", "offer_submitted"],
            customization_options={
                "response_time_targets": True,
                "agent_assignment_rules": True,
                "priority_property_selection": True,
            },
            is_premium=True,
        )

        self.templates[template.template_id] = template

    def _create_first_time_buyer_education(self):
        """Create educational sequence for first-time buyers"""

        steps = [
            {
                "id": "ftb_1",
                "name": "First-Time Buyer Welcome",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "subject": "Your First Home Buying Journey Starts Here!",
                    "template_id": "first_time_buyer_welcome",
                    "attach_resources": ["first_time_buyer_guide.pdf", "mortgage_pre_approval_checklist.pdf"],
                },
            },
            {
                "id": "ftb_2",
                "name": "Mortgage Pre-Approval Education",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 172800},  # 2 days
                "config": {
                    "subject": "Step 1: Getting Pre-Approved for Your Mortgage",
                    "template_id": "mortgage_education",
                    "include_lender_contacts": True,
                },
            },
            {
                "id": "ftb_3",
                "name": "Neighborhood Research Guide",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 345600},  # 4 days
                "config": {
                    "subject": "How to Research {{location_preference}} Neighborhoods",
                    "template_id": "neighborhood_guide",
                    "include_local_data": True,
                },
            },
            {
                "id": "ftb_4",
                "name": "Home Inspection Basics",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 518400},  # 6 days
                "config": {
                    "subject": "What to Expect During Your Home Inspection",
                    "template_id": "inspection_guide",
                    "attach_inspection_checklist": True,
                },
            },
            {
                "id": "ftb_5",
                "name": "Ready to Start Looking SMS",
                "type": "smart_sms",
                "delay_config": {"type": "fixed", "seconds": 604800},  # 1 week
                "config": {
                    "message": "{{first_name}}, you've learned the basics! Ready to start looking at some {{property_type}} options in {{location_preference}}? Let me know! 🏠"
                },
            },
        ]

        template = WorkflowTemplate(
            template_id="first_time_buyer_education",
            name="First-Time Buyer Education Series",
            description="Educational sequence to guide first-time buyers through the home buying process",
            category=WorkflowCategory.BUYER_JOURNEY,
            target_lead_types=[LeadType.FIRST_TIME_BUYER],
            estimated_duration_days=7,
            steps=steps,
            triggers=[
                {
                    "type": "lead_profile",
                    "conditions": [
                        {"field": "buyer_type", "operator": "equals", "value": "first_time"},
                        {"field": "education_level", "operator": "in", "value": ["beginner", "researching"]},
                    ],
                }
            ],
            success_metrics=["email_engagement", "resource_downloads", "mortgage_pre_approval", "ready_to_view"],
            customization_options={"education_pace": True, "local_market_focus": True, "resource_selection": True},
        )

        self.templates[template.template_id] = template

    def _create_luxury_buyer_experience(self):
        """Create premium experience for luxury buyers"""

        steps = [
            {
                "id": "luxury_1",
                "name": "Personal Concierge Introduction",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "subject": "Welcome to Your Exclusive Property Search Experience",
                    "template_id": "luxury_welcome",
                    "personalization_level": "premium",
                    "include_agent_bio": True,
                    "include_testimonials": True,
                },
            },
            {
                "id": "luxury_2",
                "name": "Curated Property Portfolio",
                "type": "property_matching",
                "delay_config": {"type": "fixed", "seconds": 7200},  # 2 hours
                "config": {
                    "property_tier": "luxury",
                    "max_properties": 3,
                    "include_exclusive_listings": True,
                    "virtual_tour_required": True,
                },
            },
            {
                "id": "luxury_3",
                "name": "Personal Call from Top Agent",
                "type": "create_task",
                "delay_config": {"type": "fixed", "seconds": 10800},  # 3 hours
                "config": {
                    "title": "Personal call to luxury client {{first_name}} {{last_name}}",
                    "assignee": "luxury_specialist",
                    "priority": "urgent",
                    "call_type": "luxury_introduction",
                },
            },
            {
                "id": "luxury_4",
                "name": "Private Showing Coordination",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 86400},  # 1 day
                "config": {
                    "subject": "Your Private Property Viewing Experience",
                    "template_id": "luxury_showing_invite",
                    "include_concierge_services": True,
                },
            },
        ]

        template = WorkflowTemplate(
            template_id="luxury_buyer_experience",
            name="Luxury Buyer Concierge Experience",
            description="White-glove service sequence for high-end property buyers",
            category=WorkflowCategory.BUYER_JOURNEY,
            target_lead_types=[LeadType.LUXURY_CLIENT],
            estimated_duration_days=3,
            steps=steps,
            triggers=[
                {
                    "type": "budget_based",
                    "conditions": [{"field": "budget_min", "operator": "greater_than", "value": 1000000}],
                },
                {
                    "type": "property_based",
                    "conditions": [{"field": "property_interest", "operator": "contains", "value": "luxury"}],
                },
            ],
            success_metrics=["personal_call_completed", "private_showing_scheduled", "exclusive_access_granted"],
            customization_options={
                "concierge_service_level": True,
                "exclusive_listing_access": True,
                "personalized_market_reports": True,
            },
            is_premium=True,
        )

        self.templates[template.template_id] = template

    def _create_listing_preparation_sequence(self):
        """Create sequence for preparing sellers to list their property"""

        steps = [
            {
                "id": "prep_1",
                "name": "Listing Preparation Welcome",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "subject": "Let's Get Your Property Market-Ready!",
                    "template_id": "listing_prep_welcome",
                    "include_market_analysis": True,
                },
            },
            {
                "id": "prep_2",
                "name": "Home Staging Consultation",
                "type": "create_task",
                "delay_config": {"type": "fixed", "seconds": 86400},  # 1 day
                "config": {
                    "title": "Schedule home staging consultation for {{property_address}}",
                    "task_type": "staging_consultation",
                    "priority": "medium",
                },
            },
            {
                "id": "prep_3",
                "name": "Professional Photography Scheduling",
                "type": "create_task",
                "delay_config": {"type": "fixed", "seconds": 259200},  # 3 days
                "config": {
                    "title": "Schedule professional photography for {{property_address}}",
                    "task_type": "photography",
                    "depends_on": "staging_completed",
                },
            },
            {
                "id": "prep_4",
                "name": "Listing Strategy Review",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 432000},  # 5 days
                "config": {
                    "subject": "Your Listing Strategy & Pricing Recommendations",
                    "template_id": "listing_strategy",
                    "include_comparable_sales": True,
                },
            },
        ]

        template = WorkflowTemplate(
            template_id="listing_preparation",
            name="Listing Preparation Sequence",
            description="Comprehensive preparation sequence for sellers getting ready to list",
            category=WorkflowCategory.SELLER_ENGAGEMENT,
            target_lead_types=[LeadType.SELLER],
            estimated_duration_days=7,
            steps=steps,
            triggers=[
                {
                    "type": "intent_based",
                    "conditions": [
                        {"field": "intent", "operator": "equals", "value": "selling"},
                        {"field": "timeline", "operator": "contains", "value": "1-3 months"},
                    ],
                }
            ],
            success_metrics=["staging_completed", "photos_taken", "listing_live", "showing_requests"],
            customization_options={"staging_level": True, "photography_package": True, "marketing_channels": True},
        )

        self.templates[template.template_id] = template

    def _create_post_closing_satisfaction(self):
        """Create post-closing satisfaction and referral sequence"""

        steps = [
            {
                "id": "post_1",
                "name": "Congratulations & Thank You",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 86400},  # 1 day after closing
                "config": {
                    "subject": "Congratulations on Your New Home! 🏡",
                    "template_id": "post_closing_congrats",
                    "include_closing_gift": True,
                },
            },
            {
                "id": "post_2",
                "name": "Satisfaction Survey",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 604800},  # 1 week
                "config": {
                    "subject": "How Was Your Home Buying Experience?",
                    "template_id": "satisfaction_survey",
                    "include_survey_link": True,
                },
            },
            {
                "id": "post_3",
                "name": "Local Resources Guide",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 1209600},  # 2 weeks
                "config": {
                    "subject": "Your {{neighborhood}} Neighborhood Guide",
                    "template_id": "local_resources",
                    "include_vendor_recommendations": True,
                },
            },
            {
                "id": "post_4",
                "name": "First Month Check-in",
                "type": "smart_sms",
                "delay_config": {"type": "fixed", "seconds": 2592000},  # 1 month
                "config": {
                    "message": "{{first_name}}, how are you settling into your new home? Any questions about the neighborhood? Happy to help! 🏠"
                },
            },
            {
                "id": "post_5",
                "name": "Referral Request",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 5184000},  # 2 months
                "config": {
                    "subject": "Know Anyone Else Looking for a Great Agent?",
                    "template_id": "referral_request",
                    "include_referral_incentive": True,
                },
            },
        ]

        template = WorkflowTemplate(
            template_id="post_closing_satisfaction",
            name="Post-Closing Client Care",
            description="Comprehensive post-closing sequence for client satisfaction and referral generation",
            category=WorkflowCategory.POST_CLOSING,
            target_lead_types=[LeadType.FIRST_TIME_BUYER, LeadType.REPEAT_BUYER, LeadType.LUXURY_CLIENT],
            estimated_duration_days=60,
            steps=steps,
            triggers=[
                {
                    "type": "event_based",
                    "conditions": [{"field": "transaction_status", "operator": "equals", "value": "closed"}],
                }
            ],
            success_metrics=["survey_completed", "positive_review", "referral_received", "client_retention"],
            customization_options={"follow_up_frequency": True, "gift_selection": True, "local_vendor_network": True},
        )

        self.templates[template.template_id] = template

    def _create_monthly_market_updates(self):
        """Create monthly market update sequence"""

        steps = [
            {
                "id": "market_1",
                "name": "Monthly Market Report",
                "type": "smart_email",
                "delay_config": {"type": "fixed", "seconds": 0},
                "config": {
                    "subject": "{{location}} Real Estate Market Update - {{month}} {{year}}",
                    "template_id": "monthly_market_report",
                    "include_market_stats": True,
                    "include_price_trends": True,
                },
            },
            {
                "id": "market_2",
                "name": "Featured Listings",
                "type": "property_matching",
                "delay_config": {"type": "fixed", "seconds": 172800},  # 2 days
                "config": {
                    "property_selection": "featured_listings",
                    "max_properties": 4,
                    "include_market_analysis": True,
                },
            },
            {
                "id": "market_3",
                "name": "Market Insights SMS",
                "type": "smart_sms",
                "delay_config": {"type": "fixed", "seconds": 432000},  # 5 days
                "config": {
                    "message": "{{first_name}}, did you see this month's {{location}} market trends? Properties are {{market_trend}}. Great time to {{market_action}}! 📊"
                },
            },
        ]

        template = WorkflowTemplate(
            template_id="monthly_market_updates",
            name="Monthly Market Intelligence",
            description="Regular market updates to keep leads informed and engaged",
            category=WorkflowCategory.MARKET_UPDATE,
            target_lead_types=[LeadType.FIRST_TIME_BUYER, LeadType.REPEAT_BUYER, LeadType.INVESTOR],
            estimated_duration_days=7,
            steps=steps,
            triggers=[
                {
                    "type": "time_based",
                    "conditions": [
                        {"field": "schedule_type", "operator": "equals", "value": "monthly"},
                        {"field": "day_of_month", "operator": "equals", "value": 1},
                    ],
                }
            ],
            success_metrics=["email_opens", "property_inquiries", "market_engagement"],
            customization_options={
                "market_focus_areas": True,
                "report_detail_level": True,
                "property_selection_criteria": True,
            },
        )

        self.templates[template.template_id] = template

    # Template Management Methods

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: WorkflowCategory) -> List[WorkflowTemplate]:
        """Get all templates in a category"""
        return [t for t in self.templates.values() if t.category == category]

    def get_templates_for_lead_type(self, lead_type: LeadType) -> List[WorkflowTemplate]:
        """Get templates suitable for lead type"""
        return [t for t in self.templates.values() if lead_type in t.target_lead_types]

    def search_templates(self, query: str) -> List[WorkflowTemplate]:
        """Search templates by name or description"""
        query_lower = query.lower()
        return [
            t for t in self.templates.values() if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]

    def get_recommended_templates(
        self, lead_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get recommended templates for a lead"""

        recommendations = []

        # Determine lead type
        lead_type = self._determine_lead_type(lead_data)

        # Get lead score
        lead_score = lead_data.get("lead_score", 0)

        # Get applicable templates
        applicable_templates = self.get_templates_for_lead_type(lead_type)

        for template in applicable_templates:
            score = self._calculate_template_score(template, lead_data, lead_type, lead_score)

            if score > 0.5:  # Threshold for recommendation
                recommendations.append(
                    {
                        "template": template,
                        "score": score,
                        "reason": self._get_recommendation_reason(template, lead_data),
                    }
                )

        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return recommendations[:5]  # Top 5 recommendations

    def _determine_lead_type(self, lead_data: Dict[str, Any]) -> LeadType:
        """Determine lead type from lead data"""

        # Check explicit lead type field
        if "lead_type" in lead_data:
            try:
                return LeadType(lead_data["lead_type"])
            except ValueError:
                pass

        # Infer from other fields
        budget = lead_data.get("budget_max", 0)
        if budget > 1000000:
            return LeadType.LUXURY_CLIENT

        intent = lead_data.get("intent", "").lower()
        if "sell" in intent:
            return LeadType.SELLER
        elif "invest" in intent:
            return LeadType.INVESTOR

        # Check if first-time buyer
        if lead_data.get("first_time_buyer", False):
            return LeadType.FIRST_TIME_BUYER

        # Default to repeat buyer
        return LeadType.REPEAT_BUYER

    def _calculate_template_score(
        self, template: WorkflowTemplate, lead_data: Dict[str, Any], lead_type: LeadType, lead_score: float
    ) -> float:
        """Calculate relevance score for template"""

        score = 0.0

        # Lead type match (40% of score)
        if lead_type in template.target_lead_types:
            score += 0.4

        # Lead score alignment (30% of score)
        if template.template_id == "hot_lead_acceleration" and lead_score > 70:
            score += 0.3
        elif template.template_id == "long_term_nurture" and lead_score < 40:
            score += 0.3
        elif 40 <= lead_score <= 70:
            score += 0.2

        # Timeline alignment (20% of score)
        timeline = lead_data.get("timeline", "").lower()
        if "asap" in timeline or "immediate" in timeline:
            if template.estimated_duration_days <= 3:
                score += 0.2
        elif "month" in timeline:
            if template.estimated_duration_days <= 30:
                score += 0.2

        # Budget alignment for luxury templates (10% of score)
        budget = lead_data.get("budget_max", 0)
        if template.is_premium and budget > 500000:
            score += 0.1

        return min(score, 1.0)

    def _get_recommendation_reason(self, template: WorkflowTemplate, lead_data: Dict[str, Any]) -> str:
        """Get human-readable reason for recommendation"""

        reasons = []

        # Lead type match
        lead_type = self._determine_lead_type(lead_data)
        if lead_type in template.target_lead_types:
            reasons.append(f"Designed for {lead_type.value.replace('_', ' ')} leads")

        # Lead score
        lead_score = lead_data.get("lead_score", 0)
        if lead_score > 70 and "hot" in template.template_id:
            reasons.append("High engagement detected")
        elif lead_score < 40 and "nurture" in template.template_id:
            reasons.append("Ideal for long-term relationship building")

        # Timeline
        timeline = lead_data.get("timeline", "").lower()
        if "asap" in timeline and template.estimated_duration_days <= 3:
            reasons.append("Fast-track sequence for immediate needs")

        return "; ".join(reasons) if reasons else "Good general fit for your lead profile"

    def customize_template(
        self, template_id: str, customizations: Dict[str, Any], custom_name: Optional[str] = None
    ) -> Optional[WorkflowTemplate]:
        """Create customized version of template"""

        base_template = self.get_template(template_id)
        if not base_template:
            return None

        # Create copy
        customized_steps = []
        for step in base_template.steps:
            step_copy = step.copy()

            # Apply customizations
            if "timing_adjustments" in customizations:
                timing_mult = customizations["timing_adjustments"].get("multiplier", 1.0)
                if "delay_config" in step_copy:
                    step_copy["delay_config"]["seconds"] = int(step_copy["delay_config"]["seconds"] * timing_mult)

            if "message_personalization" in customizations:
                personalizations = customizations["message_personalization"]
                if "config" in step_copy:
                    for key, value in personalizations.items():
                        if key in step_copy["config"]:
                            step_copy["config"][key] = value

            customized_steps.append(step_copy)

        # Create new template
        new_template_id = f"{template_id}_custom_{datetime.now().timestamp()}"
        new_name = custom_name or f"{base_template.name} (Customized)"

        customized_template = WorkflowTemplate(
            template_id=new_template_id,
            name=new_name,
            description=f"Customized version of {base_template.name}",
            category=base_template.category,
            target_lead_types=base_template.target_lead_types,
            estimated_duration_days=base_template.estimated_duration_days,
            steps=customized_steps,
            triggers=base_template.triggers.copy(),
            success_metrics=base_template.success_metrics.copy(),
            customization_options=base_template.customization_options.copy(),
            is_premium=base_template.is_premium,
        )

        return customized_template

    def get_template_analytics(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for template usage (placeholder - would integrate with analytics service)"""

        template = self.get_template(template_id)
        if not template:
            return None

        # Mock analytics data
        return {
            "template_id": template_id,
            "usage_count": 150,
            "success_rate": 0.68,
            "avg_completion_rate": 0.72,
            "top_performing_steps": ["welcome_1", "property_matches"],
            "common_drop_off_points": ["welcome_3_followup"],
            "avg_lead_score_improvement": 15.2,
            "conversion_metrics": {"email_opens": 0.75, "sms_responses": 0.45, "calls_scheduled": 0.32},
        }

    def export_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Export template as JSON"""

        template = self.get_template(template_id)
        if not template:
            return None

        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "category": template.category.value,
            "target_lead_types": [lt.value for lt in template.target_lead_types],
            "estimated_duration_days": template.estimated_duration_days,
            "steps": template.steps,
            "triggers": template.triggers,
            "success_metrics": template.success_metrics,
            "customization_options": template.customization_options,
            "is_premium": template.is_premium,
            "exported_at": datetime.now().isoformat(),
        }

    def import_template(self, template_data: Dict[str, Any]) -> bool:
        """Import template from JSON"""

        try:
            template = WorkflowTemplate(
                template_id=template_data["template_id"],
                name=template_data["name"],
                description=template_data["description"],
                category=WorkflowCategory(template_data["category"]),
                target_lead_types=[LeadType(lt) for lt in template_data["target_lead_types"]],
                estimated_duration_days=template_data["estimated_duration_days"],
                steps=template_data["steps"],
                triggers=template_data["triggers"],
                success_metrics=template_data["success_metrics"],
                customization_options=template_data["customization_options"],
                is_premium=template_data.get("is_premium", False),
            )

            self.templates[template.template_id] = template
            return True

        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return False

    def get_all_templates_summary(self) -> Dict[str, Any]:
        """Get summary of all available templates"""

        by_category = defaultdict(list)
        by_lead_type = defaultdict(list)

        for template in self.templates.values():
            by_category[template.category.value].append(
                {
                    "id": template.template_id,
                    "name": template.name,
                    "duration_days": template.estimated_duration_days,
                    "is_premium": template.is_premium,
                }
            )

            for lead_type in template.target_lead_types:
                by_lead_type[lead_type.value].append(template.template_id)

        return {
            "total_templates": len(self.templates),
            "premium_templates": len([t for t in self.templates.values() if t.is_premium]),
            "by_category": dict(by_category),
            "by_lead_type": dict(by_lead_type),
            "avg_duration_days": statistics.mean([t.estimated_duration_days for t in self.templates.values()]),
            "categories": [c.value for c in WorkflowCategory],
            "lead_types": [lt.value for lt in LeadType],
        }
