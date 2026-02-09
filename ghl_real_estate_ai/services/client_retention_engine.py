"""
Advanced Client Retention & Referral Automation Engine for Jorge's Rancho Cucamonga Real Estate Platform

Provides comprehensive client lifecycle management including:
- Anniversary messaging system (closing anniversaries, home purchase dates)
- Property value update notifications (market appreciation alerts)
- Life event detection and relevant market outreach
- Referral request automation with perfect timing
- Past client re-engagement sequences
- Review and testimonial collection automation

This system transforms Jorge's client relationships into a continuous source of referrals
and repeat business, positioning him as the lifetime real estate advisor for IE families.
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.data.rancho_cucamonga_market_data import get_rancho_cucamonga_market_intelligence
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.automated_marketing_engine import get_automated_marketing_engine
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.rancho_cucamonga_ai_assistant import get_rancho_cucamonga_ai_assistant

logger = get_logger(__name__)


class ClientLifecycleStage(Enum):
    """Client lifecycle stages"""

    RECENT_BUYER = "recent_buyer"  # 0-6 months post-closing
    SETTLED_CLIENT = "settled_client"  # 6 months - 2 years
    ESTABLISHED_CLIENT = "established_client"  # 2-5 years
    LONG_TERM_CLIENT = "long_term_client"  # 5+ years
    INACTIVE_CLIENT = "inactive_client"  # No engagement in 2+ years


class EngagementType(Enum):
    """Types of client engagement"""

    ANNIVERSARY_MESSAGE = "anniversary_message"
    VALUE_UPDATE = "value_update"
    LIFE_EVENT_OUTREACH = "life_event_outreach"
    REFERRAL_REQUEST = "referral_request"
    REVIEW_REQUEST = "review_request"
    MARKET_UPDATE = "market_update"
    CHECK_IN = "check_in"
    SEASONAL_GREETING = "seasonal_greeting"


class LifeEventType(Enum):
    """Detected life events that trigger outreach"""

    JOB_CHANGE = "job_change"
    FAMILY_ADDITION = "family_addition"
    RETIREMENT = "retirement"
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    INHERITANCE = "inheritance"
    BUSINESS_SUCCESS = "business_success"
    RELOCATION = "relocation"


@dataclass
class ClientProfile:
    """Comprehensive client profile for retention system"""

    client_id: str
    name: str
    email: str
    phone: str

    # Property information
    property_address: str
    purchase_date: datetime
    purchase_price: float
    current_estimated_value: float
    neighborhood: str
    property_type: str

    # Personal details
    family_size: int = 2
    employment_industry: Optional[str] = None
    life_events: List[str] = None
    interests: List[str] = None
    communication_preference: str = "email"  # email, text, call

    # Engagement history
    last_contact_date: Optional[datetime] = None
    total_engagements: int = 0
    referrals_provided: int = 0
    reviews_given: int = 0

    # Lifecycle data
    lifecycle_stage: ClientLifecycleStage = ClientLifecycleStage.RECENT_BUYER
    engagement_score: float = 0.0
    referral_probability: float = 0.0
    repeat_business_probability: float = 0.0

    def __post_init__(self):
        if self.life_events is None:
            self.life_events = []
        if self.interests is None:
            self.interests = []


@dataclass
class EngagementPlan:
    """Planned engagement with client"""

    plan_id: str
    client_id: str
    engagement_type: EngagementType
    scheduled_date: datetime
    priority: str  # high, medium, low

    # Content details
    subject: str
    message_template: str
    personalization_data: Dict[str, Any]
    channel: str  # email, sms, call, mail

    # Tracking
    status: str = "planned"  # planned, sent, delivered, opened, responded
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    response_received: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ReferralOpportunity:
    """Potential referral opportunity"""

    opportunity_id: str
    referring_client_id: str
    potential_referral_name: str
    potential_referral_contact: str
    referral_context: str  # How they know each other
    property_need: str  # buying, selling, both
    timeline: str  # immediate, 3-6 months, future
    confidence_level: float  # 0-1 probability

    # Status tracking
    status: str = "identified"  # identified, approached, connected, closed
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


class ClientRetentionEngine:
    """
    Advanced Client Retention & Referral Automation Engine

    Features:
    - Automated lifecycle-based engagement
    - AI-powered personalization
    - Life event detection and response
    - Intelligent referral request timing
    - Review and testimonial automation
    - Property value tracking and notifications
    """

    def __init__(self):
        self.llm_client = LLMClient(provider="claude")
        self.rc_assistant = get_rancho_cucamonga_ai_assistant()
        self.marketing_engine = get_automated_marketing_engine()
        self.cache = get_cache_service()
        self.market_intelligence = get_rancho_cucamonga_market_intelligence()

        # Client database (in production, would be actual database)
        self.client_profiles: Dict[str, ClientProfile] = {}
        self.engagement_plans: Dict[str, EngagementPlan] = {}
        self.referral_opportunities: Dict[str, ReferralOpportunity] = {}

        # Engagement templates and rules
        self.engagement_templates = self._load_engagement_templates()
        self.lifecycle_rules = self._load_lifecycle_rules()
        self.personalization_data = self._load_personalization_data()

    def _load_engagement_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load engagement message templates"""
        return {
            "anniversary_message": {
                "subject_template": "Happy {anniversary_year} Year Anniversary in Your {neighborhood} Home!",
                "message_template": """
Hi {client_name},

Can you believe it's been {anniversary_year} year{s} since you purchased your beautiful home at {property_address}? Time flies when you're loving where you live!

I wanted to reach out and share some exciting news about your neighborhood and your home's value:

📈 **Your Home's Value**: Your property has appreciated approximately ${value_increase:,} since purchase (estimated current value: ${current_value:,})

🏘️ **{neighborhood} Market Update**: {neighborhood_update}

🎉 **Anniversary Reflection**: {personal_note}

I hope you and your family are continuing to love life in the Inland Empire. If you ever have questions about your property, the market, or know anyone looking to buy or sell in the area, I'm always here to help.

Warmest regards,
Jorge Martinez
Your Inland Empire Real Estate Partner

P.S. {ps_note}
""",
                "personalization_fields": [
                    "client_name",
                    "anniversary_year",
                    "property_address",
                    "neighborhood",
                    "value_increase",
                    "current_value",
                    "neighborhood_update",
                    "personal_note",
                    "ps_note",
                    "s",
                ],
            },
            "value_update": {
                "subject_template": "Great News About Your {neighborhood} Property Value!",
                "message_template": """
Hi {client_name},

I have some fantastic news to share about your property at {property_address}!

💰 **Value Increase**: Your home's estimated value has increased by ${value_increase:,} over the past {time_period}, bringing your estimated current value to ${current_value:,}.

📊 **Market Insights**: {market_analysis}

🏠 **What This Means for You**: {implications}

{action_items}

This is exactly why I stay on top of market trends for all my past clients - your success is my success! If you have any questions about your property's value or the current market, I'm always happy to discuss.

Best regards,
Jorge Martinez
Your Inland Empire Market Expert

{additional_note}
""",
                "personalization_fields": [
                    "client_name",
                    "property_address",
                    "neighborhood",
                    "value_increase",
                    "time_period",
                    "current_value",
                    "market_analysis",
                    "implications",
                    "action_items",
                    "additional_note",
                ],
            },
            "referral_request": {
                "subject_template": "Quick Favor - Anyone You Know Looking in the IE?",
                "message_template": """
Hi {client_name},

Hope you and {family_reference} are doing wonderful in your {neighborhood} home!

I'm reaching out because I'm getting a lot of inquiries from people looking to move to the Inland Empire, particularly {target_demographics}.

Given your positive experience {experience_reference}, I was wondering if you know anyone who might be considering a move to the area? Whether they're:

• {referral_scenarios}

I'd love the opportunity to help them the same way I helped you find the perfect home. Plus, as a thank you for any referrals, I have a special appreciation program for my past clients.

{personal_touch}

No pressure at all - just thought I'd ask since you've been such a great client!

Best,
Jorge Martinez

P.S. If YOU ever decide to make a move (whether upgrading, downsizing, or investing), I'm always here to help!
""",
                "personalization_fields": [
                    "client_name",
                    "family_reference",
                    "neighborhood",
                    "target_demographics",
                    "experience_reference",
                    "referral_scenarios",
                    "personal_touch",
                ],
            },
            "review_request": {
                "subject_template": "Would Love Your Quick Review - {client_name}",
                "message_template": """
Hi {client_name},

I hope you're absolutely loving life in your {neighborhood} home! It's been {time_since_purchase} since we closed on your property, and I wanted to reach out with a small request.

Your experience working with me means the world to me, and I'd be incredibly grateful if you could take 2 minutes to share a quick review about our experience together.

🌟 **Leave a Review**: {review_links}

A few words about:
• How I helped you navigate the IE market
• Your experience with my local expertise
• What made the difference in your home search

{personalized_reminder}

Reviews like yours help other families find the right agent for their Inland Empire journey, just like you found me!

Thanks so much for considering this, and as always, I'm here if you need anything.

Gratefully,
Jorge Martinez

P.S. {ps_note}
""",
                "personalization_fields": [
                    "client_name",
                    "neighborhood",
                    "time_since_purchase",
                    "review_links",
                    "personalized_reminder",
                    "ps_note",
                ],
            },
            "life_event_outreach": {
                "subject_template": "Congratulations on Your {life_event}!",
                "message_template": """
Hi {client_name},

{congratulations_opening}

I'm so happy for you and {family_reference}! {personal_note}

{life_event_specific_content}

{real_estate_relevance}

If there's ever anything I can do to help - whether real estate related or just as your friend in the business - please don't hesitate to reach out.

Warmest congratulations,
Jorge Martinez

{closing_note}
""",
                "personalization_fields": [
                    "client_name",
                    "life_event",
                    "congratulations_opening",
                    "family_reference",
                    "personal_note",
                    "life_event_specific_content",
                    "real_estate_relevance",
                    "closing_note",
                ],
            },
        }

    def _load_lifecycle_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load lifecycle-based engagement rules"""
        return {
            "recent_buyer": {
                "timeframe": "0-6 months post-closing",
                "engagement_frequency": "monthly",
                "focus": ["settling_in", "value_tracking", "referral_building"],
                "priority_engagements": ["check_in", "value_update", "review_request"],
                "referral_timing": "3-6 months post-closing",
            },
            "settled_client": {
                "timeframe": "6 months - 2 years",
                "engagement_frequency": "quarterly",
                "focus": ["market_updates", "referrals", "value_appreciation"],
                "priority_engagements": ["market_update", "referral_request", "anniversary_message"],
                "referral_timing": "ongoing",
            },
            "established_client": {
                "timeframe": "2-5 years",
                "focus": ["life_events", "investment_opportunities", "referrals"],
                "engagement_frequency": "quarterly",
                "priority_engagements": ["anniversary_message", "value_update", "life_event_outreach"],
                "referral_timing": "ongoing",
            },
            "long_term_client": {
                "timeframe": "5+ years",
                "engagement_frequency": "semi-annually",
                "focus": ["life_changes", "investment", "multi_generational"],
                "priority_engagements": ["anniversary_message", "life_event_outreach"],
                "referral_timing": "ongoing",
            },
        }

    def _load_personalization_data(self) -> Dict[str, Any]:
        """Load data for personalizing messages"""
        return {
            "neighborhood_updates": {
                "etiwanda": "The Etiwanda school district continues to be a major draw for families, with new developments adding value to the entire area.",
                "alta_loma": "Alta Loma's luxury market is showing strong appreciation, with mountain view properties particularly in demand.",
                "central_rc": "Central Rancho Cucamonga is benefiting from infrastructure improvements and proximity to the Victoria Gardens expansion.",
                "north_rc": "North RC's family-friendly communities continue to attract young professionals working in logistics and healthcare.",
            },
            "industry_insights": {
                "logistics": "The continued growth of e-commerce is creating excellent job security and advancement opportunities in the IE logistics sector.",
                "healthcare": "With Kaiser's expansion and the growing IE population, healthcare professionals are seeing strong career prospects in our area.",
                "education": "The IE's growing population means excellent opportunities for education professionals in our expanding school districts.",
                "technology": "More tech workers are discovering the IE's quality of life advantages and reverse commute benefits.",
            },
            "family_references": {1: "you", 2: "you both", 3: "your family", 4: "your family", 5: "your family"},
        }

    async def add_client_profile(self, client_data: Dict[str, Any]) -> ClientProfile:
        """Add new client profile to retention system"""

        client_id = client_data.get("client_id") or str(uuid.uuid4())

        profile = ClientProfile(
            client_id=client_id,
            name=client_data["name"],
            email=client_data["email"],
            phone=client_data.get("phone", ""),
            property_address=client_data["property_address"],
            purchase_date=datetime.fromisoformat(client_data["purchase_date"]),
            purchase_price=client_data["purchase_price"],
            current_estimated_value=client_data.get("current_estimated_value", client_data["purchase_price"]),
            neighborhood=client_data.get("neighborhood", "Rancho Cucamonga"),
            property_type=client_data.get("property_type", "single_family"),
            family_size=client_data.get("family_size", 2),
            employment_industry=client_data.get("employment_industry"),
            communication_preference=client_data.get("communication_preference", "email"),
        )

        # Determine lifecycle stage based on purchase date
        profile.lifecycle_stage = self._determine_lifecycle_stage(profile.purchase_date)

        # Calculate initial scores
        profile.engagement_score = await self._calculate_engagement_score(profile)
        profile.referral_probability = await self._calculate_referral_probability(profile)

        # Store profile
        self.client_profiles[client_id] = profile
        await self._cache_client_profile(profile)

        # Create initial engagement plan
        await self._create_initial_engagement_plan(profile)

        logger.info(f"Added client profile for {profile.name} at {profile.property_address}")
        return profile

    async def update_property_value(self, client_id: str, new_value: float, trigger_notification: bool = True):
        """Update client property value and trigger notification if significant change"""

        if client_id not in self.client_profiles:
            await self._load_client_profile(client_id)

        if client_id not in self.client_profiles:
            logger.warning(f"Client {client_id} not found")
            return

        profile = self.client_profiles[client_id]
        old_value = profile.current_estimated_value
        value_change = new_value - old_value
        change_percentage = (value_change / old_value) * 100

        profile.current_estimated_value = new_value

        # Trigger notification if value change is significant (>5% or >$25k)
        if trigger_notification and (abs(change_percentage) > 5 or abs(value_change) > 25000):
            await self._schedule_value_update_engagement(profile, value_change, change_percentage)

        await self._cache_client_profile(profile)
        logger.info(
            f"Updated property value for {profile.name}: ${old_value:,} → ${new_value:,} ({change_percentage:+.1f}%)"
        )

    async def detect_life_event(self, client_id: str, life_event: LifeEventType, context: Dict[str, Any]):
        """Detect and respond to client life events"""

        if client_id not in self.client_profiles:
            await self._load_client_profile(client_id)

        if client_id not in self.client_profiles:
            logger.warning(f"Client {client_id} not found")
            return

        profile = self.client_profiles[client_id]

        # Add life event to client profile
        event_description = f"{life_event.value}:{datetime.now().isoformat()}"
        if event_description not in profile.life_events:
            profile.life_events.append(event_description)

        # Schedule appropriate engagement
        await self._schedule_life_event_engagement(profile, life_event, context)

        # Update engagement and referral scores
        profile.engagement_score = await self._calculate_engagement_score(profile)
        profile.referral_probability = await self._calculate_referral_probability(profile)

        await self._cache_client_profile(profile)
        logger.info(f"Detected life event for {profile.name}: {life_event.value}")

    async def request_referral(self, client_id: str, target_demographics: List[str] = None) -> bool:
        """Request referral from client with optimal timing"""

        if client_id not in self.client_profiles:
            await self._load_client_profile(client_id)

        if client_id not in self.client_profiles:
            return False

        profile = self.client_profiles[client_id]

        # Check if timing is appropriate for referral request
        if not await self._is_good_referral_timing(profile):
            logger.info(f"Not optimal timing for referral request from {profile.name}")
            return False

        # Schedule referral request engagement
        await self._schedule_referral_request_engagement(profile, target_demographics)

        return True

    async def process_daily_engagements(self):
        """Process daily scheduled engagements"""

        today = datetime.now().date()
        processed_count = 0

        # Get all planned engagements for today
        today_engagements = [
            plan
            for plan in self.engagement_plans.values()
            if plan.scheduled_date.date() == today and plan.status == "planned"
        ]

        for engagement in today_engagements:
            try:
                await self._execute_engagement(engagement)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing engagement {engagement.plan_id}: {e}")

        # Generate new engagements for clients due for contact
        await self._generate_scheduled_engagements()

        logger.info(f"Processed {processed_count} daily engagements")
        return processed_count

    async def _execute_engagement(self, engagement: EngagementPlan):
        """Execute a scheduled engagement"""

        # Load client profile
        if engagement.client_id not in self.client_profiles:
            await self._load_client_profile(engagement.client_id)

        profile = self.client_profiles[engagement.client_id]

        # Generate personalized message
        personalized_content = await self._personalize_engagement(engagement, profile)

        # Send engagement (in production, would actually send email/SMS)
        await self._send_engagement(engagement, personalized_content)

        # Update engagement status
        engagement.status = "sent"
        engagement.sent_at = datetime.now()

        # Update client profile
        profile.last_contact_date = datetime.now()
        profile.total_engagements += 1

        await self._cache_engagement_plan(engagement)
        await self._cache_client_profile(profile)

        logger.info(f"Executed {engagement.engagement_type.value} engagement for {profile.name}")

    async def _personalize_engagement(self, engagement: EngagementPlan, profile: ClientProfile) -> Dict[str, str]:
        """Personalize engagement content using AI"""

        # Get base template
        template_data = self.engagement_templates.get(engagement.engagement_type.value, {})

        # Build personalization context
        context = {
            "client_name": profile.name.split()[0],  # First name
            "property_address": profile.property_address,
            "neighborhood": profile.neighborhood.replace("_", " ").title(),
            "purchase_date": profile.purchase_date,
            "current_value": int(profile.current_estimated_value),
            "purchase_price": int(profile.purchase_price),
            **engagement.personalization_data,
        }

        # Generate AI-enhanced content
        enhanced_content = await self._generate_enhanced_engagement_content(
            engagement.engagement_type, template_data, context, profile
        )

        return enhanced_content

    async def _generate_enhanced_engagement_content(
        self,
        engagement_type: EngagementType,
        template_data: Dict[str, Any],
        context: Dict[str, Any],
        profile: ClientProfile,
    ) -> Dict[str, str]:
        """Use AI to enhance engagement content with personal touches"""

        prompt = f"""
You are Jorge Martinez, creating a personalized message for a past real estate client.

ENGAGEMENT TYPE: {engagement_type.value}
CLIENT PROFILE:
- Name: {profile.name}
- Property: {profile.property_address}
- Neighborhood: {profile.neighborhood}
- Purchase Date: {profile.purchase_date.strftime("%B %Y")}
- Family Size: {profile.family_size}
- Industry: {profile.employment_industry or "Unknown"}
- Time as Client: {(datetime.now() - profile.purchase_date).days} days

TEMPLATE TO ENHANCE:
Subject: {template_data.get("subject_template", "")}
Message: {template_data.get("message_template", "")}

PERSONALIZATION CONTEXT:
{json.dumps(context, indent=2, default=str)}

Enhance this template with:
1. Personal touches based on client history
2. Relevant Inland Empire market insights
3. Natural, conversational tone
4. Specific details that show you remember them
5. Jorge's warm but professional voice

Fill in all template variables and add personal elements. Return as JSON:
{{
  "subject": "Enhanced subject line",
  "message": "Enhanced message content",
  "personal_touches": ["touch1", "touch2"]
}}
"""

        try:
            response = await self.llm_client.agenerate(prompt=prompt, max_tokens=800, temperature=0.7)

            # Parse AI response
            enhanced = json.loads(response.content)
            return enhanced

        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
            # Return basic template with variable substitution
            return self._basic_template_substitution(template_data, context)

    def _basic_template_substitution(self, template_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, str]:
        """Basic template variable substitution as fallback"""

        subject_template = template_data.get("subject_template", "Update from Jorge")
        message_template = template_data.get("message_template", "Hope you're doing well!")

        try:
            subject = subject_template.format(**context)
            message = message_template.format(**context)
        except KeyError:
            # Handle missing variables gracefully
            subject = subject_template
            message = message_template

        return {"subject": subject, "message": message, "personal_touches": []}

    async def _send_engagement(self, engagement: EngagementPlan, content: Dict[str, str]):
        """Send engagement via appropriate channel"""

        # In production, this would actually send via email/SMS/etc.
        # For demo, we'll log and cache the sent message

        sent_message = {
            "engagement_id": engagement.plan_id,
            "client_id": engagement.client_id,
            "channel": engagement.channel,
            "subject": content["subject"],
            "message": content["message"],
            "sent_at": datetime.now().isoformat(),
        }

        # Cache sent message
        cache_key = f"sent_engagement:{engagement.plan_id}"
        await self.cache.set(cache_key, sent_message, ttl=365 * 24 * 3600)  # 1 year

        logger.info(
            f"Sent {engagement.engagement_type.value} via {engagement.channel} to client {engagement.client_id}"
        )

    def _determine_lifecycle_stage(self, purchase_date: datetime) -> ClientLifecycleStage:
        """Determine client lifecycle stage based on purchase date"""

        days_since_purchase = (datetime.now() - purchase_date).days

        if days_since_purchase <= 180:  # 6 months
            return ClientLifecycleStage.RECENT_BUYER
        elif days_since_purchase <= 730:  # 2 years
            return ClientLifecycleStage.SETTLED_CLIENT
        elif days_since_purchase <= 1825:  # 5 years
            return ClientLifecycleStage.ESTABLISHED_CLIENT
        else:
            return ClientLifecycleStage.LONG_TERM_CLIENT

    async def _calculate_engagement_score(self, profile: ClientProfile) -> float:
        """Calculate client engagement score (0-1)"""

        score = 0.0

        # Base score from lifecycle stage
        stage_scores = {
            ClientLifecycleStage.RECENT_BUYER: 0.8,
            ClientLifecycleStage.SETTLED_CLIENT: 0.6,
            ClientLifecycleStage.ESTABLISHED_CLIENT: 0.4,
            ClientLifecycleStage.LONG_TERM_CLIENT: 0.3,
        }
        score += stage_scores.get(profile.lifecycle_stage, 0.3)

        # Boost for recent engagement
        if profile.last_contact_date:
            days_since_contact = (datetime.now() - profile.last_contact_date).days
            if days_since_contact < 30:
                score += 0.1
            elif days_since_contact < 90:
                score += 0.05

        # Boost for referrals provided
        score += min(profile.referrals_provided * 0.1, 0.3)

        # Boost for reviews given
        score += min(profile.reviews_given * 0.05, 0.15)

        # Life events increase engagement
        score += min(len(profile.life_events) * 0.05, 0.2)

        return min(score, 1.0)

    async def _calculate_referral_probability(self, profile: ClientProfile) -> float:
        """Calculate probability that client will provide referrals"""

        probability = 0.0

        # Base probability by lifecycle stage
        stage_probabilities = {
            ClientLifecycleStage.RECENT_BUYER: 0.3,
            ClientLifecycleStage.SETTLED_CLIENT: 0.7,
            ClientLifecycleStage.ESTABLISHED_CLIENT: 0.8,
            ClientLifecycleStage.LONG_TERM_CLIENT: 0.6,
        }
        probability += stage_probabilities.get(profile.lifecycle_stage, 0.3)

        # History of referrals
        if profile.referrals_provided > 0:
            probability += 0.3

        # Recent life events (people talk about changes)
        recent_events = [
            event
            for event in profile.life_events
            if datetime.now() - datetime.fromisoformat(event.split(":")[1]) < timedelta(days=180)
        ]
        probability += min(len(recent_events) * 0.1, 0.2)

        # Positive market conditions (people excited about value)
        value_appreciation = profile.current_estimated_value / profile.purchase_price - 1
        if value_appreciation > 0.1:  # 10% appreciation
            probability += 0.1

        return min(probability, 1.0)

    async def _is_good_referral_timing(self, profile: ClientProfile) -> bool:
        """Determine if timing is good for referral request"""

        # Don't ask too frequently
        if profile.last_contact_date:
            days_since_contact = (datetime.now() - profile.last_contact_date).days
            if days_since_contact < 30:
                return False

        # Must be past recent buyer stage (let them settle in first)
        if profile.lifecycle_stage == ClientLifecycleStage.RECENT_BUYER:
            months_since_purchase = (datetime.now() - profile.purchase_date).days / 30
            return months_since_purchase >= 3

        # High referral probability is good timing
        return profile.referral_probability >= 0.5

    async def _schedule_value_update_engagement(
        self, profile: ClientProfile, value_change: float, change_percentage: float
    ):
        """Schedule value update engagement"""

        plan_id = str(uuid.uuid4())

        engagement = EngagementPlan(
            plan_id=plan_id,
            client_id=profile.client_id,
            engagement_type=EngagementType.VALUE_UPDATE,
            scheduled_date=datetime.now() + timedelta(days=1),
            priority="high",
            subject="Great news about your property value!",
            message_template="value_update",
            personalization_data={
                "value_increase": abs(value_change),
                "time_period": "recent months",
                "market_analysis": f"Your {profile.neighborhood} neighborhood is showing strong appreciation",
                "implications": "This represents excellent equity building in your IE investment",
            },
            channel=profile.communication_preference,
        )

        self.engagement_plans[plan_id] = engagement
        await self._cache_engagement_plan(engagement)

    async def _schedule_life_event_engagement(
        self, profile: ClientProfile, life_event: LifeEventType, context: Dict[str, Any]
    ):
        """Schedule life event congratulations engagement"""

        plan_id = str(uuid.uuid4())

        engagement = EngagementPlan(
            plan_id=plan_id,
            client_id=profile.client_id,
            engagement_type=EngagementType.LIFE_EVENT_OUTREACH,
            scheduled_date=datetime.now() + timedelta(days=2),
            priority="medium",
            subject=f"Congratulations on your {life_event.value.replace('_', ' ')}!",
            message_template="life_event_outreach",
            personalization_data={"life_event": life_event.value.replace("_", " "), **context},
            channel=profile.communication_preference,
        )

        self.engagement_plans[plan_id] = engagement
        await self._cache_engagement_plan(engagement)

    async def _schedule_referral_request_engagement(
        self, profile: ClientProfile, target_demographics: List[str] = None
    ):
        """Schedule referral request engagement"""

        plan_id = str(uuid.uuid4())

        demographics = target_demographics or ["logistics workers", "healthcare professionals", "young families"]

        engagement = EngagementPlan(
            plan_id=plan_id,
            client_id=profile.client_id,
            engagement_type=EngagementType.REFERRAL_REQUEST,
            scheduled_date=datetime.now() + timedelta(days=1),
            priority="high",
            subject="Quick favor - anyone you know looking in the IE?",
            message_template="referral_request",
            personalization_data={
                "target_demographics": ", ".join(demographics),
                "experience_reference": "and your successful home purchase",
            },
            channel=profile.communication_preference,
        )

        self.engagement_plans[plan_id] = engagement
        await self._cache_engagement_plan(engagement)

    async def _create_initial_engagement_plan(self, profile: ClientProfile):
        """Create initial engagement plan for new client"""

        # Welcome sequence for new clients
        welcome_engagements = [
            (7, EngagementType.CHECK_IN, "How are you settling into your new home?"),
            (30, EngagementType.VALUE_UPDATE, "Your first month market update"),
            (90, EngagementType.REVIEW_REQUEST, "Would love your review"),
            (180, EngagementType.REFERRAL_REQUEST, "Anyone you know looking to buy?"),
        ]

        for days_offset, engagement_type, subject in welcome_engagements:
            plan_id = str(uuid.uuid4())

            engagement = EngagementPlan(
                plan_id=plan_id,
                client_id=profile.client_id,
                engagement_type=engagement_type,
                scheduled_date=profile.purchase_date + timedelta(days=days_offset),
                priority="medium",
                subject=subject,
                message_template=engagement_type.value,
                personalization_data={},
                channel=profile.communication_preference,
            )

            self.engagement_plans[plan_id] = engagement
            await self._cache_engagement_plan(engagement)

    async def _generate_scheduled_engagements(self):
        """Generate new scheduled engagements for clients due for contact"""

        today = datetime.now()

        for profile in self.client_profiles.values():
            # Check if client is due for contact based on lifecycle rules
            lifecycle_rule = self.lifecycle_rules.get(profile.lifecycle_stage.value, {})
            frequency = lifecycle_rule.get("engagement_frequency", "quarterly")

            # Calculate days between contacts
            frequency_days = {"weekly": 7, "monthly": 30, "quarterly": 90, "semi-annually": 180, "annually": 365}

            days_between = frequency_days.get(frequency, 90)

            # Check if contact is due
            if profile.last_contact_date:
                days_since_contact = (today - profile.last_contact_date).days
                if days_since_contact < days_between:
                    continue

            # Schedule appropriate engagement type
            priority_engagements = lifecycle_rule.get("priority_engagements", ["check_in"])

            for engagement_type_str in priority_engagements:
                # Check if this type of engagement was recent
                if not await self._was_recent_engagement_type(profile.client_id, engagement_type_str):
                    await self._schedule_engagement(profile, EngagementType(engagement_type_str))
                    break

    async def _was_recent_engagement_type(self, client_id: str, engagement_type: str) -> bool:
        """Check if client had recent engagement of this type"""

        # Check last 90 days for this engagement type
        cutoff_date = datetime.now() - timedelta(days=90)

        for plan in self.engagement_plans.values():
            if (
                plan.client_id == client_id
                and plan.engagement_type.value == engagement_type
                and plan.sent_at
                and plan.sent_at >= cutoff_date
            ):
                return True

        return False

    async def _schedule_engagement(self, profile: ClientProfile, engagement_type: EngagementType):
        """Schedule a specific engagement type"""

        plan_id = str(uuid.uuid4())

        engagement = EngagementPlan(
            plan_id=plan_id,
            client_id=profile.client_id,
            engagement_type=engagement_type,
            scheduled_date=datetime.now() + timedelta(days=1),
            priority="medium",
            subject=f"{engagement_type.value.replace('_', ' ').title()} from Jorge",
            message_template=engagement_type.value,
            personalization_data={},
            channel=profile.communication_preference,
        )

        self.engagement_plans[plan_id] = engagement
        await self._cache_engagement_plan(engagement)

    async def get_retention_analytics(self, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
        """Get client retention analytics"""

        analytics = {
            "total_clients": len(self.client_profiles),
            "lifecycle_distribution": {},
            "engagement_metrics": {"total_engagements": 0, "engagements_last_30_days": 0, "avg_engagement_score": 0.0},
            "referral_metrics": {
                "total_referrals_received": 0,
                "avg_referral_probability": 0.0,
                "clients_likely_to_refer": 0,
            },
            "retention_trends": {"active_clients": 0, "at_risk_clients": 0, "high_value_clients": 0},
        }

        # Calculate metrics from client profiles
        total_engagement_score = 0
        total_referral_probability = 0

        for profile in self.client_profiles.values():
            # Lifecycle distribution
            stage = profile.lifecycle_stage.value
            analytics["lifecycle_distribution"][stage] = analytics["lifecycle_distribution"].get(stage, 0) + 1

            # Engagement metrics
            analytics["engagement_metrics"]["total_engagements"] += profile.total_engagements
            total_engagement_score += profile.engagement_score

            # Referral metrics
            analytics["referral_metrics"]["total_referrals_received"] += profile.referrals_provided
            total_referral_probability += profile.referral_probability

            if profile.referral_probability > 0.7:
                analytics["referral_metrics"]["clients_likely_to_refer"] += 1

            # Retention trends
            if profile.engagement_score > 0.6:
                analytics["retention_trends"]["active_clients"] += 1
            elif profile.engagement_score < 0.3:
                analytics["retention_trends"]["at_risk_clients"] += 1

            if profile.current_estimated_value > 800000 or profile.referrals_provided > 2:
                analytics["retention_trends"]["high_value_clients"] += 1

        # Calculate averages
        client_count = len(self.client_profiles)
        if client_count > 0:
            analytics["engagement_metrics"]["avg_engagement_score"] = total_engagement_score / client_count
            analytics["referral_metrics"]["avg_referral_probability"] = total_referral_probability / client_count

        return analytics

    async def _cache_client_profile(self, profile: ClientProfile):
        """Cache client profile"""
        cache_key = f"client_profile:{profile.client_id}"
        await self.cache.set(cache_key, asdict(profile), ttl=365 * 24 * 3600)  # 1 year

    async def _load_client_profile(self, client_id: str) -> Optional[ClientProfile]:
        """Load client profile from cache"""
        cache_key = f"client_profile:{client_id}"
        data = await self.cache.get(cache_key)
        if data:
            self.client_profiles[client_id] = ClientProfile(**data)
            return self.client_profiles[client_id]
        return None

    async def _cache_engagement_plan(self, plan: EngagementPlan):
        """Cache engagement plan"""
        cache_key = f"engagement_plan:{plan.plan_id}"
        await self.cache.set(cache_key, asdict(plan), ttl=90 * 24 * 3600)  # 90 days


# Singleton instance
_client_retention_engine = None


def get_client_retention_engine() -> ClientRetentionEngine:
    """Get singleton Client Retention Engine instance"""
    global _client_retention_engine
    if _client_retention_engine is None:
        _client_retention_engine = ClientRetentionEngine()
    return _client_retention_engine
