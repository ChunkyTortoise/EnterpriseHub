"""
Agent Communication Automation Service

Advanced multi-channel communication automation system that optimizes agent follow-up
sequences, timing, and personalization using AI-powered insights and behavioral analytics.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)


class CommunicationChannel(Enum):
    """Communication channels available for automation."""
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    VOICEMAIL = "voicemail"
    LINKEDIN = "linkedin"
    DIRECT_MAIL = "direct_mail"
    VIDEO_MESSAGE = "video_message"


class MessageType(Enum):
    """Types of automated messages."""
    WELCOME_SEQUENCE = "welcome_sequence"
    FOLLOW_UP = "follow_up"
    NURTURING = "nurturing"
    APPOINTMENT_REMINDER = "appointment_reminder"
    MARKET_UPDATE = "market_update"
    PROPERTY_ALERT = "property_alert"
    BIRTHDAY_GREETING = "birthday_greeting"
    ANNIVERSARY = "anniversary"
    CHECK_IN = "check_in"
    RE_ENGAGEMENT = "re_engagement"
    REFERRAL_REQUEST = "referral_request"


class AutomationTrigger(Enum):
    """Triggers that initiate automated communications."""
    NEW_LEAD = "new_lead"
    LEAD_RESPONSE = "lead_response"
    NO_RESPONSE = "no_response"
    PROPERTY_VIEW = "property_view"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    APPOINTMENT_COMPLETED = "appointment_completed"
    CONTRACT_SIGNED = "contract_signed"
    CLOSING_DATE = "closing_date"
    TIME_BASED = "time_based"
    BEHAVIORAL = "behavioral"
    MANUAL = "manual"


class CommunicationStatus(Enum):
    """Status of communication attempts."""
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"


class EngagementLevel(Enum):
    """Lead engagement levels for communication optimization."""
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    ACTIVE = "active"
    DORMANT = "dormant"


@dataclass
class CommunicationTemplate:
    """Template for automated communications."""
    id: str
    name: str
    message_type: MessageType
    channel: CommunicationChannel
    subject_line: Optional[str] = None
    content_template: str = ""
    variables: List[str] = field(default_factory=list)
    personalization_fields: List[str] = field(default_factory=list)
    engagement_level: Optional[EngagementLevel] = None
    agent_experience_level: Optional[str] = None
    market_segment: Optional[str] = None
    language: str = "en"
    compliance_notes: Optional[str] = None
    effectiveness_score: float = 0.0
    usage_count: int = 0
    created_date: datetime = field(default_factory=datetime.utcnow)
    updated_date: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


@dataclass
class CommunicationSequence:
    """Multi-step communication sequence definition."""
    id: str
    name: str
    description: str
    trigger: AutomationTrigger
    steps: List[Dict[str, Any]]
    target_audience: Dict[str, Any]
    success_criteria: List[str]
    exit_conditions: List[str]
    optimization_rules: Dict[str, Any]
    is_active: bool = True
    created_date: datetime = field(default_factory=datetime.utcnow)
    success_rate: float = 0.0
    total_enrollments: int = 0
    completion_rate: float = 0.0


@dataclass
class CommunicationAttempt:
    """Individual communication attempt record."""
    id: str
    agent_id: str
    lead_id: str
    sequence_id: Optional[str] = None
    template_id: Optional[str] = None
    channel: CommunicationChannel = CommunicationChannel.EMAIL
    message_type: MessageType = MessageType.FOLLOW_UP
    trigger: AutomationTrigger = AutomationTrigger.MANUAL
    scheduled_time: datetime = field(default_factory=datetime.utcnow)
    sent_time: Optional[datetime] = None
    status: CommunicationStatus = CommunicationStatus.SCHEDULED
    subject_line: Optional[str] = None
    content: str = ""
    personalization_data: Dict[str, Any] = field(default_factory=dict)
    delivery_data: Dict[str, Any] = field(default_factory=dict)
    engagement_data: Dict[str, Any] = field(default_factory=dict)
    response_data: Optional[Dict[str, Any]] = None
    ai_optimization_score: float = 0.0
    manual_override: bool = False


@dataclass
class LeadCommunicationProfile:
    """Communication preferences and history for a lead."""
    lead_id: str
    preferred_channels: List[CommunicationChannel] = field(default_factory=list)
    optimal_contact_times: Dict[str, List[int]] = field(default_factory=dict)  # day -> hours
    engagement_level: EngagementLevel = EngagementLevel.WARM
    communication_frequency_preference: str = "moderate"  # low, moderate, high
    last_interaction_date: Optional[datetime] = None
    total_interactions: int = 0
    response_rate: float = 0.0
    preferred_content_type: Optional[str] = None
    unsubscribed_channels: List[CommunicationChannel] = field(default_factory=list)
    communication_history: List[str] = field(default_factory=list)  # attempt IDs
    behavioral_insights: Dict[str, Any] = field(default_factory=dict)
    ai_recommendations: List[str] = field(default_factory=list)


@dataclass
class TimingOptimization:
    """AI-powered timing optimization for communications."""
    lead_id: str
    agent_id: str
    channel: CommunicationChannel
    optimal_send_time: datetime
    confidence_score: float
    reasoning: str
    based_on_data: List[str]  # factors considered
    alternative_times: List[datetime] = field(default_factory=list)
    timezone: str = "UTC"
    day_of_week_preference: Optional[str] = None
    avoid_times: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CommunicationAnalytics:
    """Analytics for communication performance."""
    period_start: datetime
    period_end: datetime
    agent_id: Optional[str] = None
    sequence_id: Optional[str] = None
    channel_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    message_type_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timing_analysis: Dict[str, Any] = field(default_factory=dict)
    engagement_metrics: Dict[str, float] = field(default_factory=dict)
    conversion_metrics: Dict[str, float] = field(default_factory=dict)
    ai_optimization_impact: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class MultiChannelCampaign:
    """Coordinated multi-channel communication campaign."""
    id: str
    name: str
    description: str
    agent_id: str
    target_leads: List[str]
    channels: List[CommunicationChannel]
    campaign_timeline: Dict[str, Any]
    coordination_rules: Dict[str, Any]
    success_metrics: Dict[str, float]
    status: str = "draft"  # draft, active, paused, completed
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    ai_recommendations: List[str] = field(default_factory=list)


class AgentCommunicationAutomation:
    """Service for advanced agent communication automation with AI optimization."""

    def __init__(self):
        """Initialize the communication automation service."""
        self.templates: Dict[str, CommunicationTemplate] = {}
        self.sequences: Dict[str, CommunicationSequence] = {}
        self.attempts: Dict[str, CommunicationAttempt] = {}
        self.lead_profiles: Dict[str, LeadCommunicationProfile] = {}
        self.timing_optimizations: Dict[str, List[TimingOptimization]] = {}
        self.campaigns: Dict[str, MultiChannelCampaign] = {}

        # Initialize default templates and sequences
        self._initialize_default_templates()
        self._initialize_default_sequences()

    def _initialize_default_templates(self):
        """Initialize default communication templates."""
        templates = [
            CommunicationTemplate(
                id="welcome_new_lead",
                name="New Lead Welcome Email",
                message_type=MessageType.WELCOME_SEQUENCE,
                channel=CommunicationChannel.EMAIL,
                subject_line="Welcome to Your Real Estate Journey, {first_name}!",
                content_template="""Hi {first_name},

Thank you for your interest in {inquiry_type}! I'm {agent_name}, your dedicated real estate professional.

I've received your inquiry about {property_details} and I'm excited to help you find your perfect home.

Here's what happens next:
• I'll send you a personalized property analysis within 24 hours
• We'll schedule a consultation to understand your needs better
• I'll keep you updated on new properties that match your criteria

Quick question: What's the best time to reach you? I prefer to work around your schedule.

Best regards,
{agent_name}
{agent_contact_info}

P.S. I've helped over {deals_completed} families find their dream homes. Let's make you the next success story!""",
                variables=["first_name", "inquiry_type", "property_details", "agent_name", "agent_contact_info", "deals_completed"],
                personalization_fields=["first_name", "inquiry_type", "property_details"],
                engagement_level=EngagementLevel.WARM,
                effectiveness_score=0.85
            ),
            CommunicationTemplate(
                id="follow_up_no_response",
                name="Follow-up for No Response",
                message_type=MessageType.FOLLOW_UP,
                channel=CommunicationChannel.EMAIL,
                subject_line="Quick question about your home search",
                content_template="""Hi {first_name},

I wanted to follow up on the property information I sent earlier.

I know you're busy, so I'll keep this brief:

The market is moving fast, especially for properties in {preferred_area} within your budget range of {budget_range}.

I have 2 new listings that just came on the market that might interest you:
• {property_1_brief}
• {property_2_brief}

Should I send you the details, or would you prefer a quick call to discuss?

If now isn't the right time for your home search, just let me know and I'll check back in a few months.

{agent_name}
{agent_phone}""",
                variables=["first_name", "preferred_area", "budget_range", "property_1_brief", "property_2_brief", "agent_name", "agent_phone"],
                personalization_fields=["first_name", "preferred_area", "budget_range"],
                engagement_level=EngagementLevel.COLD,
                effectiveness_score=0.65
            ),
            CommunicationTemplate(
                id="market_update_nurture",
                name="Monthly Market Update",
                message_type=MessageType.MARKET_UPDATE,
                channel=CommunicationChannel.EMAIL,
                subject_line="Market Update: {area_name} Real Estate Trends",
                content_template="""Hi {first_name},

Your monthly {area_name} market update is here!

📊 Key Market Stats for {area_name}:
• Median Home Price: ${median_price} (${price_change} from last month)
• Average Days on Market: {days_on_market} days
• Inventory Level: {inventory_level}

🏡 What This Means for You:
{market_interpretation}

🔍 New Properties in Your Price Range:
I'm tracking {matching_properties_count} properties that match your criteria.

Would you like me to send you the top 3 options this week?

Stay informed,
{agent_name}

P.S. Interest rates are currently at {interest_rate}% - a great time to explore your options!""",
                variables=["first_name", "area_name", "median_price", "price_change", "days_on_market", "inventory_level", "market_interpretation", "matching_properties_count", "agent_name", "interest_rate"],
                personalization_fields=["first_name", "area_name", "matching_properties_count"],
                engagement_level=EngagementLevel.WARM,
                effectiveness_score=0.72
            ),
            CommunicationTemplate(
                id="appointment_reminder_sms",
                name="Appointment Reminder SMS",
                message_type=MessageType.APPOINTMENT_REMINDER,
                channel=CommunicationChannel.SMS,
                content_template="""Hi {first_name}! This is {agent_name} reminding you about our appointment tomorrow at {appointment_time} to view properties.

Meeting location: {meeting_location}

Excited to show you some great options! Reply CONFIRM if you're all set or call me at {agent_phone} if you need to reschedule.

See you tomorrow!""",
                variables=["first_name", "agent_name", "appointment_time", "meeting_location", "agent_phone"],
                personalization_fields=["first_name", "appointment_time", "meeting_location"],
                engagement_level=EngagementLevel.HOT,
                effectiveness_score=0.95
            ),
            CommunicationTemplate(
                id="property_alert_instant",
                name="Instant Property Alert",
                message_type=MessageType.PROPERTY_ALERT,
                channel=CommunicationChannel.EMAIL,
                subject_line="🚨 NEW LISTING: Perfect match in {neighborhood}",
                content_template="""🏡 NEW PROPERTY ALERT for {first_name}!

A property just hit the market that matches your criteria:

📍 {property_address}
💰 ${property_price} ({price_vs_budget})
🏠 {bedrooms} bed, {bathrooms} bath, {square_feet} sq ft
✨ Key Features: {key_features}

📊 Why This is Perfect for You:
{ai_matching_reasoning}

⏰ TIMING: This type of property typically receives {expected_offers} offers within {typical_days} days.

Want to see it? I can arrange a showing as early as today.

Call/Text me: {agent_phone}

{agent_name}

[VIEW FULL LISTING] [SCHEDULE SHOWING] [UNSUBSCRIBE]""",
                variables=["first_name", "neighborhood", "property_address", "property_price", "price_vs_budget", "bedrooms", "bathrooms", "square_feet", "key_features", "ai_matching_reasoning", "expected_offers", "typical_days", "agent_phone", "agent_name"],
                personalization_fields=["first_name", "property_address", "ai_matching_reasoning"],
                engagement_level=EngagementLevel.HOT,
                effectiveness_score=0.88
            )
        ]

        for template in templates:
            self.templates[template.id] = template

    def _initialize_default_sequences(self):
        """Initialize default communication sequences."""
        sequences = [
            CommunicationSequence(
                id="new_lead_nurture_sequence",
                name="New Lead Nurturing Sequence",
                description="7-step sequence for nurturing new leads to first appointment",
                trigger=AutomationTrigger.NEW_LEAD,
                steps=[
                    {
                        "step": 1,
                        "delay_hours": 0,
                        "template_id": "welcome_new_lead",
                        "channel": "email",
                        "conditions": []
                    },
                    {
                        "step": 2,
                        "delay_hours": 24,
                        "template_id": "follow_up_no_response",
                        "channel": "email",
                        "conditions": ["no_response_to_step_1"]
                    },
                    {
                        "step": 3,
                        "delay_hours": 72,
                        "template_id": "appointment_reminder_sms",
                        "channel": "sms",
                        "conditions": ["no_response_to_step_2"]
                    },
                    {
                        "step": 4,
                        "delay_hours": 168,  # 1 week
                        "template_id": "property_alert_instant",
                        "channel": "email",
                        "conditions": ["no_appointment_scheduled"]
                    },
                    {
                        "step": 5,
                        "delay_hours": 336,  # 2 weeks
                        "template_id": "market_update_nurture",
                        "channel": "email",
                        "conditions": ["still_engaged"]
                    }
                ],
                target_audience={
                    "lead_sources": ["website", "zillow", "realtor_com"],
                    "price_range": "any",
                    "engagement_level": "warm"
                },
                success_criteria=[
                    "appointment_scheduled",
                    "lead_response",
                    "phone_call_completed"
                ],
                exit_conditions=[
                    "unsubscribed",
                    "appointment_completed",
                    "contract_signed",
                    "do_not_contact"
                ],
                optimization_rules={
                    "timing_optimization": True,
                    "channel_preference": True,
                    "content_personalization": True,
                    "ai_optimization": True
                },
                success_rate=0.35,
                total_enrollments=0,
                completion_rate=0.78
            ),
            CommunicationSequence(
                id="post_appointment_follow_up",
                name="Post-Appointment Follow-up",
                description="Follow-up sequence after property showing appointments",
                trigger=AutomationTrigger.APPOINTMENT_COMPLETED,
                steps=[
                    {
                        "step": 1,
                        "delay_hours": 2,
                        "template_id": "post_showing_thank_you",
                        "channel": "email",
                        "conditions": []
                    },
                    {
                        "step": 2,
                        "delay_hours": 24,
                        "template_id": "feedback_request",
                        "channel": "sms",
                        "conditions": ["no_immediate_offer"]
                    },
                    {
                        "step": 3,
                        "delay_hours": 72,
                        "template_id": "additional_properties",
                        "channel": "email",
                        "conditions": ["interested_but_not_perfect"]
                    }
                ],
                target_audience={
                    "appointment_type": ["showing", "consultation"],
                    "engagement_level": "hot"
                },
                success_criteria=[
                    "offer_submitted",
                    "additional_showings_scheduled",
                    "referral_generated"
                ],
                exit_conditions=[
                    "offer_accepted",
                    "client_switched_agents",
                    "buying_timeline_changed"
                ],
                optimization_rules={
                    "timing_optimization": True,
                    "sentiment_analysis": True,
                    "urgency_detection": True
                },
                success_rate=0.45,
                completion_rate=0.82
            )
        ]

        for sequence in sequences:
            self.sequences[sequence.id] = sequence

    async def enroll_lead_in_sequence(
        self,
        agent_id: str,
        lead_id: str,
        sequence_id: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enroll a lead in an automated communication sequence."""
        try:
            sequence = self.sequences.get(sequence_id)
            if not sequence:
                raise ValueError(f"Sequence {sequence_id} not found")

            # Check if lead is already enrolled
            existing_attempts = [
                attempt for attempt in self.attempts.values()
                if (attempt.lead_id == lead_id and
                    attempt.sequence_id == sequence_id and
                    attempt.status in [CommunicationStatus.SCHEDULED, CommunicationStatus.SENT])
            ]

            if existing_attempts:
                logger.warning(f"Lead {lead_id} already enrolled in sequence {sequence_id}")
                return existing_attempts[0].id

            # Get or create lead communication profile
            lead_profile = await self.get_lead_communication_profile(lead_id)

            # Schedule all steps in the sequence
            enrollment_id = f"enrollment_{uuid.uuid4().hex[:8]}"
            base_time = datetime.utcnow()

            for step in sequence.steps:
                # Calculate scheduled time
                delay = timedelta(hours=step.get("delay_hours", 0))
                scheduled_time = base_time + delay

                # Apply AI timing optimization
                if sequence.optimization_rules.get("timing_optimization"):
                    optimized_time = await self._optimize_send_timing(
                        lead_id, agent_id, step.get("channel", "email"), scheduled_time
                    )
                    scheduled_time = optimized_time or scheduled_time

                # Create communication attempt
                attempt = CommunicationAttempt(
                    id=f"attempt_{uuid.uuid4().hex[:8]}",
                    agent_id=agent_id,
                    lead_id=lead_id,
                    sequence_id=sequence_id,
                    template_id=step.get("template_id"),
                    channel=CommunicationChannel(step.get("channel", "email")),
                    trigger=sequence.trigger,
                    scheduled_time=scheduled_time,
                    personalization_data=custom_data or {}
                )

                self.attempts[attempt.id] = attempt
                lead_profile.communication_history.append(attempt.id)

            # Update sequence enrollment count
            sequence.total_enrollments += 1

            # Update lead profile
            self.lead_profiles[lead_id] = lead_profile

            logger.info(f"Enrolled lead {lead_id} in sequence {sequence_id} with {len(sequence.steps)} steps")
            return enrollment_id

        except Exception as e:
            logger.error(f"Error enrolling lead in sequence: {str(e)}")
            raise

    async def send_scheduled_communications(self) -> List[str]:
        """Process and send all scheduled communications that are due."""
        try:
            current_time = datetime.utcnow()
            sent_attempt_ids = []

            # Find due communications
            due_attempts = [
                attempt for attempt in self.attempts.values()
                if (attempt.status == CommunicationStatus.SCHEDULED and
                    attempt.scheduled_time <= current_time)
            ]

            for attempt in due_attempts:
                try:
                    # Check sequence exit conditions
                    if attempt.sequence_id:
                        should_exit = await self._check_exit_conditions(attempt)
                        if should_exit:
                            attempt.status = CommunicationStatus.FAILED
                            continue

                    # Check step conditions
                    conditions_met = await self._check_step_conditions(attempt)
                    if not conditions_met:
                        # Skip this step but don't fail the sequence
                        attempt.status = CommunicationStatus.FAILED
                        continue

                    # Personalize content
                    personalized_content = await self._personalize_content(attempt)

                    # Send communication
                    success = await self._send_communication(attempt, personalized_content)

                    if success:
                        attempt.status = CommunicationStatus.SENT
                        attempt.sent_time = current_time
                        sent_attempt_ids.append(attempt.id)

                        # Update lead profile
                        await self._update_lead_interaction(attempt)
                    else:
                        attempt.status = CommunicationStatus.FAILED

                except Exception as e:
                    logger.error(f"Error sending communication {attempt.id}: {str(e)}")
                    attempt.status = CommunicationStatus.FAILED

            logger.info(f"Processed {len(due_attempts)} due communications, sent {len(sent_attempt_ids)}")
            return sent_attempt_ids

        except Exception as e:
            logger.error(f"Error processing scheduled communications: {str(e)}")
            raise

    async def optimize_communication_timing(
        self,
        agent_id: str,
        lead_id: str,
        channel: CommunicationChannel,
        preferred_time: Optional[datetime] = None
    ) -> TimingOptimization:
        """Use AI to optimize communication timing for maximum engagement."""
        try:
            # Get lead communication profile
            lead_profile = await self.get_lead_communication_profile(lead_id)

            # Analyze historical engagement patterns
            engagement_analysis = await self._analyze_engagement_patterns(lead_id, channel)

            # Consider lead's timezone and preferences
            timezone_info = await self._get_lead_timezone(lead_id)

            # AI-powered timing recommendation
            optimal_time = await self._calculate_optimal_send_time(
                lead_profile, engagement_analysis, timezone_info, preferred_time
            )

            # Generate reasoning and alternatives
            reasoning = await self._generate_timing_reasoning(
                lead_profile, engagement_analysis, optimal_time
            )

            alternatives = await self._generate_alternative_times(optimal_time, engagement_analysis)

            optimization = TimingOptimization(
                lead_id=lead_id,
                agent_id=agent_id,
                channel=channel,
                optimal_send_time=optimal_time,
                confidence_score=engagement_analysis.get("confidence", 0.7),
                reasoning=reasoning,
                based_on_data=[
                    "historical_engagement",
                    "lead_behavior_patterns",
                    "channel_preferences",
                    "timezone_analysis"
                ],
                alternative_times=alternatives,
                timezone=timezone_info.get("timezone", "UTC"),
                day_of_week_preference=engagement_analysis.get("best_day_of_week")
            )

            # Store optimization
            if lead_id not in self.timing_optimizations:
                self.timing_optimizations[lead_id] = []
            self.timing_optimizations[lead_id].append(optimization)

            logger.info(f"Generated timing optimization for lead {lead_id}, channel {channel.value}")
            return optimization

        except Exception as e:
            logger.error(f"Error optimizing communication timing: {str(e)}")
            raise

    async def create_multi_channel_campaign(
        self,
        agent_id: str,
        campaign_name: str,
        target_leads: List[str],
        channels: List[CommunicationChannel],
        campaign_config: Dict[str, Any]
    ) -> MultiChannelCampaign:
        """Create coordinated multi-channel communication campaign."""
        try:
            campaign = MultiChannelCampaign(
                id=f"campaign_{uuid.uuid4().hex[:8]}",
                name=campaign_name,
                description=campaign_config.get("description", ""),
                agent_id=agent_id,
                target_leads=target_leads,
                channels=channels,
                campaign_timeline=campaign_config.get("timeline", {}),
                coordination_rules=campaign_config.get("coordination_rules", {}),
                success_metrics=campaign_config.get("success_metrics", {})
            )

            # Generate AI-powered campaign recommendations
            campaign.ai_recommendations = await self._generate_campaign_recommendations(
                target_leads, channels, campaign_config
            )

            # Set up channel coordination
            await self._setup_channel_coordination(campaign)

            # Schedule campaign communications
            await self._schedule_campaign_communications(campaign)

            self.campaigns[campaign.id] = campaign

            logger.info(f"Created multi-channel campaign {campaign_name} with {len(target_leads)} leads")
            return campaign

        except Exception as e:
            logger.error(f"Error creating multi-channel campaign: {str(e)}")
            raise

    async def track_communication_response(
        self,
        attempt_id: str,
        response_type: str,
        response_data: Dict[str, Any]
    ):
        """Track and analyze communication responses for optimization."""
        try:
            attempt = self.attempts.get(attempt_id)
            if not attempt:
                raise ValueError(f"Communication attempt {attempt_id} not found")

            # Update attempt status based on response
            status_mapping = {
                "delivered": CommunicationStatus.DELIVERED,
                "opened": CommunicationStatus.OPENED,
                "clicked": CommunicationStatus.CLICKED,
                "replied": CommunicationStatus.REPLIED,
                "bounced": CommunicationStatus.BOUNCED,
                "unsubscribed": CommunicationStatus.UNSUBSCRIBED
            }

            if response_type in status_mapping:
                attempt.status = status_mapping[response_type]

            # Store response data
            attempt.response_data = response_data
            attempt.engagement_data.update({
                "response_type": response_type,
                "response_time": datetime.utcnow(),
                "response_details": response_data
            })

            # Update lead profile with engagement data
            lead_profile = await self.get_lead_communication_profile(attempt.lead_id)
            lead_profile.last_interaction_date = datetime.utcnow()
            lead_profile.total_interactions += 1

            # Calculate response rate
            total_attempts = len([a for a in self.attempts.values() if a.lead_id == attempt.lead_id])
            responded_attempts = len([
                a for a in self.attempts.values()
                if a.lead_id == attempt.lead_id and a.status in [
                    CommunicationStatus.REPLIED, CommunicationStatus.CLICKED
                ]
            ])
            lead_profile.response_rate = responded_attempts / max(total_attempts, 1)

            # Update engagement level based on response
            await self._update_engagement_level(lead_profile, response_type, response_data)

            # Learn from response for AI optimization
            await self._learn_from_response(attempt, response_type, response_data)

            self.lead_profiles[attempt.lead_id] = lead_profile

            logger.info(f"Tracked {response_type} response for attempt {attempt_id}")

        except Exception as e:
            logger.error(f"Error tracking communication response: {str(e)}")
            raise

    async def get_lead_communication_profile(
        self,
        lead_id: str
    ) -> LeadCommunicationProfile:
        """Get or create communication profile for a lead."""
        if lead_id not in self.lead_profiles:
            # Create default profile
            profile = LeadCommunicationProfile(
                lead_id=lead_id,
                preferred_channels=[CommunicationChannel.EMAIL],
                optimal_contact_times={
                    "monday": [9, 10, 14, 15],
                    "tuesday": [9, 10, 14, 15],
                    "wednesday": [9, 10, 14, 15],
                    "thursday": [9, 10, 14, 15],
                    "friday": [9, 10, 14, 15]
                },
                communication_frequency_preference="moderate"
            )
            self.lead_profiles[lead_id] = profile

        return self.lead_profiles[lead_id]

    async def generate_communication_analytics(
        self,
        agent_id: Optional[str] = None,
        period_days: int = 30
    ) -> CommunicationAnalytics:
        """Generate comprehensive communication analytics."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)

            # Filter attempts by agent and date range
            filtered_attempts = [
                attempt for attempt in self.attempts.values()
                if (not agent_id or attempt.agent_id == agent_id) and
                start_date <= attempt.scheduled_time <= end_date
            ]

            analytics = CommunicationAnalytics(
                period_start=start_date,
                period_end=end_date,
                agent_id=agent_id
            )

            # Channel breakdown analysis
            analytics.channel_breakdown = await self._analyze_channel_performance(filtered_attempts)

            # Message type performance
            analytics.message_type_performance = await self._analyze_message_type_performance(filtered_attempts)

            # Timing analysis
            analytics.timing_analysis = await self._analyze_optimal_timing(filtered_attempts)

            # Engagement metrics
            analytics.engagement_metrics = await self._calculate_engagement_metrics(filtered_attempts)

            # Conversion metrics
            analytics.conversion_metrics = await self._calculate_conversion_metrics(filtered_attempts)

            # AI optimization impact
            analytics.ai_optimization_impact = await self._measure_ai_optimization_impact(filtered_attempts)

            # Generate recommendations
            analytics.recommendations = await self._generate_analytics_recommendations(analytics)

            logger.info(f"Generated communication analytics for {len(filtered_attempts)} attempts")
            return analytics

        except Exception as e:
            logger.error(f"Error generating communication analytics: {str(e)}")
            raise

    # Helper methods

    async def _optimize_send_timing(
        self,
        lead_id: str,
        agent_id: str,
        channel: str,
        default_time: datetime
    ) -> Optional[datetime]:
        """Optimize send timing using AI analysis."""
        try:
            # Get recent optimization for this lead and channel
            optimizations = self.timing_optimizations.get(lead_id, [])
            recent_optimization = next(
                (opt for opt in optimizations
                 if opt.channel.value == channel and
                 opt.optimal_send_time > datetime.utcnow()),
                None
            )

            if recent_optimization:
                return recent_optimization.optimal_send_time

            # Generate new optimization
            optimization = await self.optimize_communication_timing(
                agent_id, lead_id, CommunicationChannel(channel)
            )

            return optimization.optimal_send_time

        except Exception as e:
            logger.error(f"Error optimizing send timing: {str(e)}")
            return None

    async def _check_exit_conditions(self, attempt: CommunicationAttempt) -> bool:
        """Check if sequence should exit based on conditions."""
        if not attempt.sequence_id:
            return False

        sequence = self.sequences.get(attempt.sequence_id)
        if not sequence:
            return False

        lead_profile = await self.get_lead_communication_profile(attempt.lead_id)

        # Check common exit conditions
        for condition in sequence.exit_conditions:
            if condition == "unsubscribed":
                if attempt.channel in lead_profile.unsubscribed_channels:
                    return True
            elif condition == "do_not_contact":
                if "do_not_contact" in lead_profile.behavioral_insights:
                    return True
            # Add more exit condition checks as needed

        return False

    async def _check_step_conditions(self, attempt: CommunicationAttempt) -> bool:
        """Check if step conditions are met for sending communication."""
        # This would check conditions like "no_response_to_previous_step"
        # For now, return True (conditions met)
        return True

    async def _personalize_content(self, attempt: CommunicationAttempt) -> str:
        """Personalize communication content using AI and lead data."""
        try:
            template = self.templates.get(attempt.template_id) if attempt.template_id else None
            if not template:
                return attempt.content

            # Get lead data for personalization
            lead_data = attempt.personalization_data.copy()

            # Add default personalization data
            lead_data.update({
                "first_name": lead_data.get("first_name", "Valued Client"),
                "agent_name": lead_data.get("agent_name", "Your Real Estate Agent"),
                "agent_phone": lead_data.get("agent_phone", "(555) 123-4567"),
                "agent_contact_info": lead_data.get("agent_contact_info", "Contact me anytime!")
            })

            # Apply template variables
            content = template.content_template
            for variable in template.variables:
                placeholder = "{" + variable + "}"
                value = lead_data.get(variable, f"[{variable}]")
                content = content.replace(placeholder, str(value))

            # AI-enhanced personalization could be added here
            # For now, return the template-based personalized content
            return content

        except Exception as e:
            logger.error(f"Error personalizing content: {str(e)}")
            return attempt.content

    async def _send_communication(
        self,
        attempt: CommunicationAttempt,
        content: str
    ) -> bool:
        """Send the actual communication through the specified channel."""
        try:
            # In a real implementation, this would integrate with:
            # - Email service (SendGrid, Mailgun, etc.)
            # - SMS service (Twilio, etc.)
            # - Phone system for calls
            # - LinkedIn API for social messages

            # For now, simulate sending
            attempt.content = content
            attempt.delivery_data = {
                "provider": f"{attempt.channel.value}_service",
                "delivery_id": f"delivery_{uuid.uuid4().hex[:8]}",
                "delivery_status": "sent"
            }

            logger.info(f"Simulated sending {attempt.channel.value} to lead {attempt.lead_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending communication: {str(e)}")
            return False

    async def _update_lead_interaction(self, attempt: CommunicationAttempt):
        """Update lead profile after communication."""
        lead_profile = await self.get_lead_communication_profile(attempt.lead_id)
        lead_profile.last_interaction_date = datetime.utcnow()
        lead_profile.total_interactions += 1

        # Update channel preferences based on engagement
        if attempt.status == CommunicationStatus.SENT:
            if attempt.channel not in lead_profile.preferred_channels:
                lead_profile.preferred_channels.append(attempt.channel)

    async def _analyze_engagement_patterns(
        self,
        lead_id: str,
        channel: CommunicationChannel
    ) -> Dict[str, Any]:
        """Analyze historical engagement patterns for timing optimization."""
        # Get lead's communication history
        lead_attempts = [
            attempt for attempt in self.attempts.values()
            if attempt.lead_id == lead_id and attempt.channel == channel
        ]

        if not lead_attempts:
            return {"confidence": 0.3, "best_day_of_week": "tuesday"}

        # Analyze engagement by day of week and time
        engagement_by_day = {}
        engagement_by_hour = {}

        for attempt in lead_attempts:
            if attempt.sent_time and attempt.status in [CommunicationStatus.OPENED, CommunicationStatus.REPLIED]:
                day = attempt.sent_time.strftime('%A').lower()
                hour = attempt.sent_time.hour

                engagement_by_day[day] = engagement_by_day.get(day, 0) + 1
                engagement_by_hour[hour] = engagement_by_hour.get(hour, 0) + 1

        # Find best day and hour
        best_day = max(engagement_by_day, key=engagement_by_day.get) if engagement_by_day else "tuesday"
        best_hour = max(engagement_by_hour, key=engagement_by_hour.get) if engagement_by_hour else 14

        return {
            "confidence": min(len(lead_attempts) / 10, 1.0),
            "best_day_of_week": best_day,
            "best_hour": best_hour,
            "engagement_by_day": engagement_by_day,
            "engagement_by_hour": engagement_by_hour
        }

    async def _get_lead_timezone(self, lead_id: str) -> Dict[str, Any]:
        """Get lead's timezone information."""
        # In real implementation, this would query lead data
        return {"timezone": "America/New_York", "utc_offset": -5}

    async def _calculate_optimal_send_time(
        self,
        lead_profile: LeadCommunicationProfile,
        engagement_analysis: Dict[str, Any],
        timezone_info: Dict[str, Any],
        preferred_time: Optional[datetime] = None
    ) -> datetime:
        """Calculate optimal send time using AI analysis."""
        # Start with preferred time or default
        base_time = preferred_time or datetime.utcnow() + timedelta(hours=1)

        # Apply engagement pattern insights
        best_day = engagement_analysis.get("best_day_of_week", "tuesday")
        best_hour = engagement_analysis.get("best_hour", 14)

        # Calculate next occurrence of best day at best hour
        current_weekday = base_time.weekday()
        target_weekday = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }.get(best_day, 1)

        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0 and base_time.hour >= best_hour:
            days_ahead = 7

        optimal_date = base_time + timedelta(days=days_ahead)
        optimal_time = optimal_date.replace(hour=best_hour, minute=0, second=0, microsecond=0)

        # Adjust for timezone
        # In real implementation, apply timezone conversion here

        return optimal_time

    async def _generate_timing_reasoning(
        self,
        lead_profile: LeadCommunicationProfile,
        engagement_analysis: Dict[str, Any],
        optimal_time: datetime
    ) -> str:
        """Generate human-readable reasoning for timing recommendation."""
        best_day = engagement_analysis.get("best_day_of_week", "tuesday")
        best_hour = engagement_analysis.get("best_hour", 14)
        confidence = engagement_analysis.get("confidence", 0.5)

        reasoning = f"Recommended send time based on lead's historical engagement patterns. "
        reasoning += f"Best day: {best_day.title()}, best hour: {best_hour}:00. "
        reasoning += f"Confidence: {confidence:.1%} based on {len(engagement_analysis.get('engagement_by_day', {}))} previous interactions."

        return reasoning

    async def _generate_alternative_times(
        self,
        optimal_time: datetime,
        engagement_analysis: Dict[str, Any]
    ) -> List[datetime]:
        """Generate alternative send times."""
        alternatives = []

        # Add times 2 hours before and after optimal
        alternatives.append(optimal_time - timedelta(hours=2))
        alternatives.append(optimal_time + timedelta(hours=2))

        # Add same time next day
        alternatives.append(optimal_time + timedelta(days=1))

        return alternatives

    async def _generate_campaign_recommendations(
        self,
        target_leads: List[str],
        channels: List[CommunicationChannel],
        campaign_config: Dict[str, Any]
    ) -> List[str]:
        """Generate AI-powered campaign recommendations."""
        recommendations = [
            "Start with email to gauge interest, then follow up with SMS for engaged leads",
            "Schedule communications during business hours for better engagement",
            "Personalize content based on lead source and preferences",
            "Monitor response rates and adjust timing accordingly"
        ]

        return recommendations

    async def _setup_channel_coordination(self, campaign: MultiChannelCampaign):
        """Set up coordination rules between communication channels."""
        # Set up rules for channel coordination
        # e.g., don't send SMS within 2 hours of email
        campaign.coordination_rules.update({
            "email_to_sms_delay": 120,  # minutes
            "max_daily_touches": 2,
            "channel_priority": ["email", "sms", "phone_call"]
        })

    async def _schedule_campaign_communications(self, campaign: MultiChannelCampaign):
        """Schedule communications for campaign."""
        # This would create scheduled communication attempts
        # for all leads in the campaign across all channels
        pass

    async def _update_engagement_level(
        self,
        lead_profile: LeadCommunicationProfile,
        response_type: str,
        response_data: Dict[str, Any]
    ):
        """Update lead engagement level based on response."""
        current_level = lead_profile.engagement_level

        # Engagement level progression logic
        if response_type in ["replied", "clicked"]:
            if current_level == EngagementLevel.COLD:
                lead_profile.engagement_level = EngagementLevel.WARM
            elif current_level == EngagementLevel.WARM:
                lead_profile.engagement_level = EngagementLevel.HOT
        elif response_type == "opened":
            if current_level == EngagementLevel.COLD:
                lead_profile.engagement_level = EngagementLevel.WARM
        elif response_type in ["bounced", "unsubscribed"]:
            lead_profile.engagement_level = EngagementLevel.DORMANT

    async def _learn_from_response(
        self,
        attempt: CommunicationAttempt,
        response_type: str,
        response_data: Dict[str, Any]
    ):
        """Learn from response to improve future AI optimization."""
        # Update template effectiveness
        if attempt.template_id:
            template = self.templates.get(attempt.template_id)
            if template:
                # Simple effectiveness scoring
                if response_type in ["replied", "clicked"]:
                    template.effectiveness_score = min(template.effectiveness_score + 0.01, 1.0)
                elif response_type in ["bounced", "unsubscribed"]:
                    template.effectiveness_score = max(template.effectiveness_score - 0.02, 0.0)

                template.usage_count += 1

    async def _analyze_channel_performance(self, attempts: List[CommunicationAttempt]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by communication channel."""
        channel_stats = {}

        for attempt in attempts:
            channel = attempt.channel.value
            if channel not in channel_stats:
                channel_stats[channel] = {
                    "total_sent": 0,
                    "delivered": 0,
                    "opened": 0,
                    "clicked": 0,
                    "replied": 0,
                    "bounced": 0
                }

            channel_stats[channel]["total_sent"] += 1

            if attempt.status == CommunicationStatus.DELIVERED:
                channel_stats[channel]["delivered"] += 1
            elif attempt.status == CommunicationStatus.OPENED:
                channel_stats[channel]["opened"] += 1
            elif attempt.status == CommunicationStatus.CLICKED:
                channel_stats[channel]["clicked"] += 1
            elif attempt.status == CommunicationStatus.REPLIED:
                channel_stats[channel]["replied"] += 1
            elif attempt.status == CommunicationStatus.BOUNCED:
                channel_stats[channel]["bounced"] += 1

        # Calculate rates
        for channel, stats in channel_stats.items():
            total = stats["total_sent"]
            if total > 0:
                stats["delivery_rate"] = stats["delivered"] / total
                stats["open_rate"] = stats["opened"] / total
                stats["click_rate"] = stats["clicked"] / total
                stats["response_rate"] = stats["replied"] / total
                stats["bounce_rate"] = stats["bounced"] / total

        return channel_stats

    async def _analyze_message_type_performance(self, attempts: List[CommunicationAttempt]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by message type."""
        # Similar to channel analysis but grouped by message type
        return {}

    async def _analyze_optimal_timing(self, attempts: List[CommunicationAttempt]) -> Dict[str, Any]:
        """Analyze optimal timing patterns."""
        return {
            "best_day_of_week": "Tuesday",
            "best_hour_of_day": 14,
            "worst_day_of_week": "Friday",
            "worst_hour_of_day": 22
        }

    async def _calculate_engagement_metrics(self, attempts: List[CommunicationAttempt]) -> Dict[str, float]:
        """Calculate overall engagement metrics."""
        if not attempts:
            return {}

        total = len(attempts)
        opened = len([a for a in attempts if a.status == CommunicationStatus.OPENED])
        clicked = len([a for a in attempts if a.status == CommunicationStatus.CLICKED])
        replied = len([a for a in attempts if a.status == CommunicationStatus.REPLIED])

        return {
            "open_rate": opened / total if total > 0 else 0,
            "click_rate": clicked / total if total > 0 else 0,
            "response_rate": replied / total if total > 0 else 0
        }

    async def _calculate_conversion_metrics(self, attempts: List[CommunicationAttempt]) -> Dict[str, float]:
        """Calculate conversion metrics."""
        # This would calculate lead-to-appointment, appointment-to-sale rates
        return {
            "lead_to_appointment_rate": 0.15,
            "appointment_to_sale_rate": 0.35
        }

    async def _measure_ai_optimization_impact(self, attempts: List[CommunicationAttempt]) -> Dict[str, float]:
        """Measure impact of AI optimization features."""
        return {
            "timing_optimization_improvement": 0.12,
            "personalization_improvement": 0.08,
            "channel_optimization_improvement": 0.06
        }

    async def _generate_analytics_recommendations(self, analytics: CommunicationAnalytics) -> List[str]:
        """Generate recommendations based on analytics."""
        recommendations = []

        # Analyze engagement rates
        engagement = analytics.engagement_metrics
        if engagement.get("open_rate", 0) < 0.20:
            recommendations.append("Consider improving email subject lines to increase open rates")

        if engagement.get("click_rate", 0) < 0.05:
            recommendations.append("Add more compelling call-to-action buttons and links")

        if engagement.get("response_rate", 0) < 0.10:
            recommendations.append("Increase personalization and relevance of content")

        return recommendations


# Global service instance
communication_automation = AgentCommunicationAutomation()


# Convenience functions for easy import
async def enroll_lead_in_communication_sequence(
    agent_id: str,
    lead_id: str,
    sequence_id: str,
    custom_data: Optional[Dict[str, Any]] = None
) -> str:
    """Enroll a lead in an automated communication sequence."""
    return await communication_automation.enroll_lead_in_sequence(
        agent_id, lead_id, sequence_id, custom_data
    )


async def send_due_communications() -> List[str]:
    """Process and send all scheduled communications that are due."""
    return await communication_automation.send_scheduled_communications()


async def optimize_send_timing(
    agent_id: str,
    lead_id: str,
    channel: CommunicationChannel,
    preferred_time: Optional[datetime] = None
) -> TimingOptimization:
    """Optimize communication timing for maximum engagement."""
    return await communication_automation.optimize_communication_timing(
        agent_id, lead_id, channel, preferred_time
    )


async def track_response(
    attempt_id: str,
    response_type: str,
    response_data: Dict[str, Any]
):
    """Track and analyze communication responses."""
    await communication_automation.track_communication_response(
        attempt_id, response_type, response_data
    )


async def get_communication_analytics(
    agent_id: Optional[str] = None,
    period_days: int = 30
) -> CommunicationAnalytics:
    """Generate communication analytics for agent or system."""
    return await communication_automation.generate_communication_analytics(
        agent_id, period_days
    )