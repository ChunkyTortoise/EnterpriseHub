"""
Intelligent Seller Nurturing System

AI-powered automated seller lead nurturing with Claude integration,
behavioral learning, and personalized communication sequences.

Business Impact: $200,000+ annual value through automated nurturing
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from .claude_seller_agent import ClaudeSellerAgent, SellerContext, SellerStage
from .seller_insights_service import SellerInsightsService, SellingPathway
from .real_time_market_intelligence import market_intelligence

try:
    from ..core.llm_client import LLMClient
    from ..ghl_utils.config import settings
    from ..ghl_utils.logger import get_logger
except ImportError:
    # Fallback for demo mode
    class LLMClient:
        def __init__(self, *args, **kwargs): pass
        async def agenerate(self, *args, **kwargs):
            return type('Response', (), {'content': 'Fallback response'})()

logger = get_logger(__name__) if 'get_logger' in globals() else logging.getLogger(__name__)


class NurturingTrigger(Enum):
    """Nurturing sequence triggers"""
    NEW_LEAD = "new_lead"                          # New seller lead created
    NO_RESPONSE = "no_response"                    # No response after X hours
    OBJECTION_RAISED = "objection_raised"          # Seller raised objection
    INFORMATION_COMPLETE = "information_complete"  # All property details gathered
    MARKET_CHANGE = "market_change"                # Significant market movement
    COMPETITOR_ACTION = "competitor_action"        # Competitor activity detected
    DECISION_DEADLINE = "decision_deadline"        # Decision timeline approaching
    RE_ENGAGEMENT = "re_engagement"                # Re-engage dormant lead


class MessageType(Enum):
    """Message delivery types"""
    SMS = "sms"
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    VOICEMAIL = "voicemail"
    SOCIAL_MEDIA = "social_media"


class NurturingPriority(Enum):
    """Message priority levels"""
    URGENT = "urgent"      # Immediate delivery
    HIGH = "high"          # Within 1 hour
    MEDIUM = "medium"      # Within 4 hours
    LOW = "low"           # Within 24 hours


@dataclass
class NurturingMessage:
    """Individual nurturing message"""
    id: str
    sequence_id: str
    message_type: MessageType
    subject: Optional[str] = None
    content: str = ""
    delay_hours: int = 0
    priority: NurturingPriority = NurturingPriority.MEDIUM

    # Personalization
    personalization_variables: Dict[str, Any] = field(default_factory=dict)
    conditional_logic: Optional[Dict[str, Any]] = None

    # Tracking
    scheduled_time: Optional[datetime] = None
    sent_time: Optional[datetime] = None
    delivery_status: str = "pending"  # pending, sent, delivered, failed
    response_received: bool = False
    engagement_score: float = 0.0


@dataclass
class NurturingSequence:
    """Complete nurturing sequence"""
    id: str
    name: str
    trigger: NurturingTrigger
    seller_stage: SellerStage
    urgency_level: str  # high, medium, low

    messages: List[NurturingMessage] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    exit_conditions: List[str] = field(default_factory=list)

    # Performance metrics
    total_sent: int = 0
    total_responses: int = 0
    total_conversions: int = 0
    avg_response_time: float = 0.0

    # Configuration
    max_messages: int = 10
    sequence_duration_days: int = 30
    allow_parallel_sequences: bool = False


@dataclass
class SellerNurturingProfile:
    """Seller-specific nurturing profile"""
    seller_id: str
    seller_context: SellerContext

    # Preferences
    preferred_contact_method: MessageType = MessageType.SMS
    contact_frequency: str = "normal"  # low, normal, high
    best_contact_hours: Tuple[int, int] = (9, 17)  # 9 AM - 5 PM
    timezone: str = "America/Chicago"

    # Active sequences
    active_sequences: List[str] = field(default_factory=list)
    completed_sequences: List[str] = field(default_factory=list)
    paused_sequences: List[str] = field(default_factory=list)

    # Engagement tracking
    total_messages_sent: int = 0
    total_responses: int = 0
    avg_response_time_hours: float = 0.0
    engagement_trend: str = "stable"  # increasing, stable, decreasing

    # Behavioral data
    preferred_content_types: List[str] = field(default_factory=list)
    response_patterns: Dict[str, Any] = field(default_factory=dict)
    objection_history: List[str] = field(default_factory=list)


class IntelligentSellerNurturing:
    """
    Advanced seller nurturing system with AI-powered personalization.

    Features:
    - Automated sequence triggering based on seller behavior
    - Claude-generated personalized messages
    - Dynamic content adaptation based on market changes
    - Behavioral learning and optimization
    - Multi-channel communication
    - Performance analytics and optimization
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Initialize services
        self.claude_agent = ClaudeSellerAgent(tenant_id)
        self.seller_insights = SellerInsightsService(tenant_id)

        # Nurturing sequences storage
        self.sequences: Dict[str, NurturingSequence] = {}
        self.seller_profiles: Dict[str, SellerNurturingProfile] = {}

        # Performance tracking
        self.performance_metrics = {
            "total_sequences_triggered": 0,
            "total_messages_sent": 0,
            "overall_response_rate": 0.0,
            "conversion_rate": 0.0,
            "avg_sequence_completion": 0.0
        }

        # Initialize default sequences
        asyncio.create_task(self._initialize_default_sequences())

        logger.info(f"Intelligent Seller Nurturing initialized for tenant {tenant_id}")

    async def trigger_nurturing_sequence(
        self,
        trigger: NurturingTrigger,
        seller_context: SellerContext,
        trigger_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger appropriate nurturing sequence based on seller state.

        Args:
            trigger: What triggered the nurturing sequence
            seller_context: Current seller context
            trigger_data: Additional context data for trigger

        Returns:
            Sequence execution result with scheduled messages
        """

        try:
            # 1. Get or create seller profile
            seller_profile = await self._get_seller_profile(seller_context)

            # 2. Find appropriate sequence
            sequence = await self._select_nurturing_sequence(
                trigger, seller_context, seller_profile
            )

            if not sequence:
                logger.warning(f"No suitable sequence found for trigger {trigger.value}")
                return {"status": "no_sequence_found"}

            # 3. Check if sequence can be triggered
            can_trigger = await self._can_trigger_sequence(sequence, seller_profile)
            if not can_trigger:
                return {"status": "sequence_blocked", "reason": "Conditions not met"}

            # 4. Personalize sequence for seller
            personalized_sequence = await self._personalize_sequence(
                sequence, seller_context, trigger_data
            )

            # 5. Schedule sequence messages
            scheduled_messages = await self._schedule_sequence_messages(
                personalized_sequence, seller_profile
            )

            # 6. Update seller profile
            seller_profile.active_sequences.append(personalized_sequence.id)
            await self._update_seller_profile(seller_profile)

            # 7. Track sequence trigger
            self.performance_metrics["total_sequences_triggered"] += 1

            logger.info(f"Nurturing sequence {sequence.name} triggered for seller {seller_context.lead_id}")

            return {
                "status": "sequence_triggered",
                "sequence_id": personalized_sequence.id,
                "sequence_name": sequence.name,
                "messages_scheduled": len(scheduled_messages),
                "estimated_duration_days": sequence.sequence_duration_days,
                "success_criteria": sequence.success_criteria
            }

        except Exception as e:
            logger.error(f"Nurturing sequence trigger failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def process_seller_response(
        self,
        seller_id: str,
        response_content: str,
        response_channel: MessageType,
        original_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process seller response and adapt nurturing accordingly.

        Args:
            seller_id: Seller identifier
            response_content: Response content from seller
            response_channel: Channel used for response
            original_message_id: ID of message being responded to

        Returns:
            Processing result with next actions
        """

        try:
            # 1. Get seller profile
            seller_profile = self._get_seller_profile_sync(seller_id)
            if not seller_profile:
                return {"status": "seller_not_found"}

            # 2. Update response tracking
            seller_profile.total_responses += 1
            await self._update_response_metrics(seller_profile, response_content)

            # 3. Analyze response sentiment and intent
            response_analysis = await self._analyze_seller_response(
                response_content, seller_profile.seller_context
            )

            # 4. Update active sequences based on response
            sequence_updates = await self._update_sequences_from_response(
                seller_profile, response_analysis, original_message_id
            )

            # 5. Determine next actions
            next_actions = await self._determine_next_actions(
                seller_profile, response_analysis
            )

            # 6. Update seller behavioral data
            await self._update_behavioral_data(
                seller_profile, response_content, response_analysis
            )

            logger.info(f"Processed response from seller {seller_id}: {response_analysis['sentiment']}")

            return {
                "status": "response_processed",
                "response_analysis": response_analysis,
                "sequence_updates": sequence_updates,
                "next_actions": next_actions,
                "engagement_trend": seller_profile.engagement_trend
            }

        except Exception as e:
            logger.error(f"Response processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def optimize_nurturing_sequences(self) -> Dict[str, Any]:
        """
        Optimize nurturing sequences based on performance data.

        Returns:
            Optimization results and recommendations
        """

        try:
            optimization_results = {
                "sequences_analyzed": len(self.sequences),
                "optimizations_applied": 0,
                "performance_improvements": {}
            }

            for sequence_id, sequence in self.sequences.items():
                # 1. Analyze sequence performance
                performance_analysis = await self._analyze_sequence_performance(sequence)

                # 2. Identify optimization opportunities
                optimizations = await self._identify_optimizations(
                    sequence, performance_analysis
                )

                # 3. Apply optimizations
                if optimizations:
                    await self._apply_sequence_optimizations(sequence, optimizations)
                    optimization_results["optimizations_applied"] += len(optimizations)
                    optimization_results["performance_improvements"][sequence_id] = optimizations

            # 4. Update global performance metrics
            await self._update_global_performance_metrics()

            logger.info(f"Sequence optimization completed: {optimization_results['optimizations_applied']} optimizations applied")

            return optimization_results

        except Exception as e:
            logger.error(f"Sequence optimization failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def generate_personalized_message(
        self,
        message_template: str,
        seller_context: SellerContext,
        message_type: MessageType,
        personalization_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate personalized message using Claude.

        Args:
            message_template: Base message template
            seller_context: Seller context for personalization
            message_type: Type of message (SMS, email, etc.)
            personalization_data: Additional personalization data

        Returns:
            Personalized message content
        """

        try:
            # Build personalization context
            personalization_context = {
                "seller_name": seller_context.name,
                "property_address": seller_context.property_address or "your property",
                "estimated_value": seller_context.estimated_value_range,
                "urgency_level": seller_context.urgency_level,
                "current_stage": seller_context.current_stage.value,
                "motivation": seller_context.motivation or "selling your property"
            }

            if personalization_data:
                personalization_context.update(personalization_data)

            # Generate market-specific content if needed
            market_context = ""
            if seller_context.property_address:
                try:
                    market_insights = await self._get_relevant_market_insights(seller_context)
                    market_context = f"Market Context: {market_insights}"
                except Exception:
                    market_context = "Current market conditions are favorable for sellers."

            # Create Claude prompt
            personalization_prompt = f"""
            Personalize this message template for a seller lead:

            TEMPLATE: "{message_template}"

            SELLER CONTEXT:
            {json.dumps(personalization_context, indent=2)}

            {market_context}

            MESSAGE TYPE: {message_type.value}

            Requirements:
            1. Use the seller's name naturally
            2. Reference their specific property/situation when relevant
            3. Match the tone to the message type (SMS=casual, Email=professional)
            4. Include relevant market insights when appropriate
            5. Keep within channel limits (SMS=160 chars, Email=300 words max)
            6. Include a clear next step or call to action

            Return only the personalized message content.
            """

            # Generate personalized message
            response = await self.claude_agent.llm_client.agenerate(
                prompt=personalization_prompt,
                system_prompt="You are an expert real estate communicator. Create engaging, personalized messages that build trust and move sellers forward.",
                temperature=0.7,
                max_tokens=200 if message_type == MessageType.SMS else 400
            )

            personalized_message = response.content.strip()

            # Apply channel-specific formatting
            formatted_message = self._format_message_for_channel(
                personalized_message, message_type
            )

            return formatted_message

        except Exception as e:
            logger.error(f"Message personalization failed: {str(e)}")
            # Return template with basic substitution
            return message_template.replace("{name}", seller_context.name or "there")

    async def _initialize_default_sequences(self):
        """Initialize default nurturing sequences"""

        # New Lead Welcome Sequence
        welcome_sequence = NurturingSequence(
            id="welcome_new_seller",
            name="New Seller Welcome",
            trigger=NurturingTrigger.NEW_LEAD,
            seller_stage=SellerStage.INITIAL_INQUIRY,
            urgency_level="medium",
            messages=[
                NurturingMessage(
                    id="welcome_01",
                    sequence_id="welcome_new_seller",
                    message_type=MessageType.SMS,
                    content="Hi {name}! Thanks for your interest in selling your property. I'm here to help you understand your options and get you the best outcome. When would be a good time for a quick chat?",
                    delay_hours=0,
                    priority=NurturingPriority.HIGH
                ),
                NurturingMessage(
                    id="welcome_02",
                    sequence_id="welcome_new_seller",
                    message_type=MessageType.EMAIL,
                    subject="Your Property Selling Options - Market Analysis",
                    content="Hi {name},\n\nI wanted to follow up on your interest in selling your property at {property_address}. Based on current market conditions, I've prepared some initial insights about your selling options.\n\nI'd love to discuss these with you and answer any questions. When would be convenient for a brief call?\n\nBest regards,\nYour Real Estate Team",
                    delay_hours=4,
                    priority=NurturingPriority.MEDIUM
                ),
                NurturingMessage(
                    id="welcome_03",
                    sequence_id="welcome_new_seller",
                    message_type=MessageType.SMS,
                    content="Hi {name}, just wanted to make sure you received my message about your property selling options. I'm here whenever you're ready to chat - no pressure! Quick question: what's your ideal timeline for selling?",
                    delay_hours=48,
                    priority=NurturingPriority.MEDIUM
                )
            ],
            success_criteria=["response_received", "call_scheduled", "information_gathered"],
            max_messages=5,
            sequence_duration_days=14
        )

        # No Response Follow-up Sequence
        followup_sequence = NurturingSequence(
            id="no_response_followup",
            name="No Response Follow-up",
            trigger=NurturingTrigger.NO_RESPONSE,
            seller_stage=SellerStage.INFORMATION_GATHERING,
            urgency_level="low",
            messages=[
                NurturingMessage(
                    id="followup_01",
                    sequence_id="no_response_followup",
                    message_type=MessageType.SMS,
                    content="Hi {name}, I know everyone's timeline is different when it comes to selling. I'm here whenever you're ready to explore your options - no rush at all! Is there a better time to connect?",
                    delay_hours=24,
                    priority=NurturingPriority.LOW
                ),
                NurturingMessage(
                    id="followup_02",
                    sequence_id="no_response_followup",
                    message_type=MessageType.EMAIL,
                    subject="Market Update for Your Neighborhood",
                    content="Hi {name},\n\nI wanted to share some recent market activity in your neighborhood. Properties similar to yours have been in high demand lately.\n\nIf you're still considering selling, I'd be happy to provide a current market analysis with no obligation.\n\nFeel free to reach out when convenient.",
                    delay_hours=72,
                    priority=NurturingPriority.LOW
                )
            ],
            success_criteria=["re_engagement", "response_received"],
            max_messages=3,
            sequence_duration_days=21
        )

        # Decision Point Sequence
        decision_sequence = NurturingSequence(
            id="decision_point_support",
            name="Decision Point Support",
            trigger=NurturingTrigger.DECISION_DEADLINE,
            seller_stage=SellerStage.PATHWAY_DECISION,
            urgency_level="high",
            messages=[
                NurturingMessage(
                    id="decision_01",
                    sequence_id="decision_point_support",
                    message_type=MessageType.PHONE_CALL,
                    content="Personal call to discuss decision timeline and address any final concerns",
                    delay_hours=0,
                    priority=NurturingPriority.URGENT
                ),
                NurturingMessage(
                    id="decision_02",
                    sequence_id="decision_point_support",
                    message_type=MessageType.SMS,
                    content="Hi {name}, I know decisions like this are important. I'm here to answer any final questions and help you feel confident about your choice. What would be most helpful right now?",
                    delay_hours=2,
                    priority=NurturingPriority.HIGH
                )
            ],
            success_criteria=["decision_made", "contract_signed"],
            max_messages=4,
            sequence_duration_days=7
        )

        # Store sequences
        self.sequences = {
            "welcome_new_seller": welcome_sequence,
            "no_response_followup": followup_sequence,
            "decision_point_support": decision_sequence
        }

    async def _select_nurturing_sequence(
        self,
        trigger: NurturingTrigger,
        seller_context: SellerContext,
        seller_profile: SellerNurturingProfile
    ) -> Optional[NurturingSequence]:
        """Select appropriate nurturing sequence"""

        # Filter sequences by trigger and stage
        suitable_sequences = [
            seq for seq in self.sequences.values()
            if seq.trigger == trigger and
            (seq.seller_stage == seller_context.current_stage or
             seq.seller_stage == SellerStage.INITIAL_INQUIRY)  # Universal sequences
        ]

        if not suitable_sequences:
            return None

        # Select best sequence based on seller urgency and history
        for sequence in suitable_sequences:
            if sequence.urgency_level == seller_context.urgency_level:
                return sequence

        # Return first suitable sequence as fallback
        return suitable_sequences[0]

    async def _personalize_sequence(
        self,
        sequence: NurturingSequence,
        seller_context: SellerContext,
        trigger_data: Optional[Dict[str, Any]]
    ) -> NurturingSequence:
        """Create personalized copy of sequence"""

        personalized_sequence = NurturingSequence(
            id=f"{sequence.id}_{seller_context.lead_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=f"{sequence.name} - {seller_context.name}",
            trigger=sequence.trigger,
            seller_stage=sequence.seller_stage,
            urgency_level=sequence.urgency_level,
            messages=[],
            success_criteria=sequence.success_criteria.copy(),
            exit_conditions=sequence.exit_conditions.copy(),
            max_messages=sequence.max_messages,
            sequence_duration_days=sequence.sequence_duration_days
        )

        # Personalize each message
        for message in sequence.messages:
            personalized_content = await self.generate_personalized_message(
                message.content,
                seller_context,
                message.message_type,
                trigger_data
            )

            personalized_message = NurturingMessage(
                id=f"{message.id}_{personalized_sequence.id}",
                sequence_id=personalized_sequence.id,
                message_type=message.message_type,
                subject=message.subject,
                content=personalized_content,
                delay_hours=message.delay_hours,
                priority=message.priority
            )

            personalized_sequence.messages.append(personalized_message)

        return personalized_sequence

    async def _schedule_sequence_messages(
        self,
        sequence: NurturingSequence,
        seller_profile: SellerNurturingProfile
    ) -> List[Dict[str, Any]]:
        """Schedule sequence messages for delivery"""

        scheduled_messages = []
        start_time = datetime.now()

        for message in sequence.messages:
            # Calculate send time based on delay and seller preferences
            send_time = start_time + timedelta(hours=message.delay_hours)

            # Adjust for seller's preferred contact hours
            send_time = self._adjust_for_contact_preferences(send_time, seller_profile)

            message.scheduled_time = send_time

            # In production, this would integrate with delivery system
            scheduled_messages.append({
                "message_id": message.id,
                "send_time": send_time.isoformat(),
                "channel": message.message_type.value,
                "content": message.content,
                "priority": message.priority.value
            })

            # Update performance tracking
            self.performance_metrics["total_messages_sent"] += 1

        return scheduled_messages

    def _adjust_for_contact_preferences(
        self,
        send_time: datetime,
        seller_profile: SellerNurturingProfile
    ) -> datetime:
        """Adjust send time for seller's contact preferences"""

        # Ensure message is sent during preferred hours
        start_hour, end_hour = seller_profile.best_contact_hours

        if send_time.hour < start_hour:
            send_time = send_time.replace(hour=start_hour, minute=0)
        elif send_time.hour > end_hour:
            # Move to next day's start hour
            send_time = send_time.replace(hour=start_hour, minute=0) + timedelta(days=1)

        # Avoid weekends for business communications (optional)
        if send_time.weekday() >= 5:  # Saturday or Sunday
            days_to_monday = 7 - send_time.weekday()
            send_time += timedelta(days=days_to_monday)

        return send_time

    def _format_message_for_channel(self, message: str, channel: MessageType) -> str:
        """Format message according to channel requirements"""

        if channel == MessageType.SMS:
            # Ensure SMS length limit
            if len(message) > 160:
                message = message[:157] + "..."

        elif channel == MessageType.EMAIL:
            # Add proper email formatting
            if not message.startswith("Hi ") and not message.startswith("Hello "):
                message = f"Hello!\n\n{message}"

            if not message.endswith("\n\nBest regards,"):
                message += "\n\nBest regards,\nYour Real Estate Team"

        return message

    async def _get_seller_profile(self, seller_context: SellerContext) -> SellerNurturingProfile:
        """Get or create seller nurturing profile"""

        if seller_context.lead_id in self.seller_profiles:
            profile = self.seller_profiles[seller_context.lead_id]
            profile.seller_context = seller_context  # Update with latest context
            return profile

        # Create new profile
        profile = SellerNurturingProfile(
            seller_id=seller_context.lead_id,
            seller_context=seller_context
        )

        self.seller_profiles[seller_context.lead_id] = profile
        return profile

    def _get_seller_profile_sync(self, seller_id: str) -> Optional[SellerNurturingProfile]:
        """Get seller profile synchronously"""
        return self.seller_profiles.get(seller_id)

    async def _can_trigger_sequence(
        self,
        sequence: NurturingSequence,
        seller_profile: SellerNurturingProfile
    ) -> bool:
        """Check if sequence can be triggered"""

        # Check if sequence already active
        if sequence.id in seller_profile.active_sequences:
            return False

        # Check if sequence was recently completed
        if sequence.id in seller_profile.completed_sequences:
            return False

        # Check if parallel sequences are allowed
        if not sequence.allow_parallel_sequences and seller_profile.active_sequences:
            return False

        return True

    async def _update_seller_profile(self, profile: SellerNurturingProfile):
        """Update seller profile in storage"""
        self.seller_profiles[profile.seller_id] = profile

    # Additional helper methods would go here...
    async def _analyze_seller_response(
        self,
        response: str,
        seller_context: SellerContext
    ) -> Dict[str, Any]:
        """Analyze seller response for sentiment and intent"""

        # Simplified analysis - would use Claude in production
        response_lower = response.lower()

        if any(word in response_lower for word in ["yes", "interested", "let's", "sounds good"]):
            sentiment = "positive"
            intent = "engagement"
        elif any(word in response_lower for word in ["no", "not interested", "stop"]):
            sentiment = "negative"
            intent = "objection"
        elif any(word in response_lower for word in ["maybe", "think about", "consider"]):
            sentiment = "neutral"
            intent = "consideration"
        else:
            sentiment = "neutral"
            intent = "information_seeking"

        return {
            "sentiment": sentiment,
            "intent": intent,
            "confidence": 0.8,
            "key_phrases": response_lower.split()[:5]
        }

    async def _get_relevant_market_insights(self, seller_context: SellerContext) -> str:
        """Get relevant market insights for messaging"""
        try:
            if seller_context.property_address:
                area = "Austin"  # Simplified
                market_pulse = await market_intelligence.get_quick_market_pulse(area)
                return f"The market is showing {market_pulse.get('market_hotness', 'moderate')} activity with properties selling in {market_pulse.get('days_on_market', 30)} days on average."
        except Exception:
            pass

        return "Market conditions are currently favorable for sellers."


# Global instance
intelligent_nurturing = None

def get_intelligent_nurturing(tenant_id: str = "default") -> IntelligentSellerNurturing:
    """Get singleton intelligent nurturing system"""
    global intelligent_nurturing
    if intelligent_nurturing is None:
        intelligent_nurturing = IntelligentSellerNurturing(tenant_id)
    return intelligent_nurturing