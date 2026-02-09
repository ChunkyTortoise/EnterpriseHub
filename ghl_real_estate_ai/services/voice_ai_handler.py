"""
Advanced Voice AI Phone Integration System for Jorge's Rancho Cucamonga Real Estate Platform

Provides comprehensive voice AI functionality for phone call handling including:
- Natural conversation AI for inbound calls
- Real-time speech-to-text with conversation state management
- Jorge's voice tone replication and Rancho Cucamonga market expertise
- Intelligent call routing (qualified leads → Jorge, basic info → AI handles completely)
- Integration with existing 7-question qualification system via voice
- Auto-scheduling from voice calls with calendar integration
- Call analytics and conversation quality scoring

This system transforms Jorge from local agent to AI-powered real estate empire
with capabilities no competitor in the Inland Empire can match.
"""

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.data.rancho_cucamonga_market_data import get_rancho_cucamonga_market_intelligence
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler
from ghl_real_estate_ai.services.rancho_cucamonga_ai_assistant import (
    get_rancho_cucamonga_ai_assistant,
)

logger = get_logger(__name__)


class CallType(Enum):
    """Types of incoming calls"""

    NEW_LEAD = "new_lead"
    EXISTING_CLIENT = "existing_client"
    VENDOR_INQUIRY = "vendor_inquiry"
    SCHEDULING_REQUEST = "scheduling_request"
    EMERGENCY = "emergency"
    SPAM = "spam"


class CallPriority(Enum):
    """Call priority levels for routing decisions"""

    URGENT = "urgent"  # Route to Jorge immediately
    HIGH = "high"  # Route to Jorge if available
    NORMAL = "normal"  # Standard priority
    MEDIUM = "medium"  # AI handles, Jorge backup
    LOW = "low"  # AI handles completely
    AUTOMATED = "automated"  # Full AI automation


class ConversationStage(Enum):
    """Voice conversation stages"""

    GREETING = "greeting"
    QUALIFICATION = "qualification"
    DISCOVERY = "discovery"
    SCHEDULING = "scheduling"
    INFORMATION = "information"
    TRANSFER = "transfer"
    CLOSING = "closing"


@dataclass
class VoiceCallContext:
    """Voice call context and state management"""

    call_id: str
    phone_number: str
    caller_name: Optional[str] = None
    call_type: CallType = CallType.NEW_LEAD
    priority: CallPriority = CallPriority.MEDIUM
    conversation_stage: ConversationStage = ConversationStage.GREETING

    # Lead qualification data
    employer: Optional[str] = None
    timeline: Optional[str] = None
    budget_range: Optional[Tuple[int, int]] = None
    property_type: Optional[str] = None
    neighborhood_preferences: List[str] = None
    commute_requirements: Optional[str] = None

    # Call metadata
    start_time: datetime = None
    duration_seconds: int = 0
    sentiment_score: float = 0.0
    confidence_score: float = 0.0
    qualification_score: int = 0  # 0-100 based on 7-question system

    # Conversation history
    transcript: List[Dict[str, str]] = None
    ai_responses: List[str] = None
    detected_intent: List[str] = None

    # Routing decisions
    should_transfer_to_jorge: bool = False
    transfer_reason: Optional[str] = None
    automated_actions_taken: List[str] = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.neighborhood_preferences is None:
            self.neighborhood_preferences = []
        if self.transcript is None:
            self.transcript = []
        if self.ai_responses is None:
            self.ai_responses = []
        if self.detected_intent is None:
            self.detected_intent = []
        if self.automated_actions_taken is None:
            self.automated_actions_taken = []


@dataclass
class VoiceResponse:
    """Structured voice AI response"""

    text: str
    audio_url: Optional[str] = None
    emotion: str = "neutral"  # neutral, enthusiastic, empathetic, urgent
    pace: str = "normal"  # slow, normal, fast
    confidence: float = 1.0
    next_expected_input: Optional[str] = None
    suggested_actions: List[str] = None

    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


class VoiceAIHandler:
    """
    Advanced Voice AI Handler for Jorge's Real Estate Platform

    Features:
    - Natural conversation with Rancho Cucamonga market expertise
    - Intelligent call routing and qualification
    - Real-time sentiment and intent analysis
    - Automated scheduling and follow-up
    - Jorge's voice tone and personality replication
    """

    def __init__(self):
        self.llm_client = LLMClient(provider="claude")
        self.rc_assistant = get_rancho_cucamonga_ai_assistant()
        self.cache = get_cache_service()
        self.scheduler = get_smart_scheduler()
        self.market_intelligence = get_rancho_cucamonga_market_intelligence()

        # Jorge's voice characteristics for AI replication
        self.jorge_voice_profile = self._load_jorge_voice_profile()

        # Qualification questions for voice interaction
        self.qualification_questions = self._load_qualification_questions()

        # Active call contexts
        self.active_calls: Dict[str, VoiceCallContext] = {}

    def _load_jorge_voice_profile(self) -> Dict[str, Any]:
        """Load Jorge's voice characteristics for AI replication"""
        return {
            "personality_traits": [
                "Warm and professional",
                "Knowledgeable about Inland Empire",
                "Logistics/healthcare industry expertise",
                "Results-oriented but personable",
                "Speaks with confidence about RC market",
            ],
            "speech_patterns": {
                "greeting_style": "Friendly but professional introduction",
                "information_delivery": "Clear, benefit-focused explanations",
                "question_style": "Open-ended to encourage conversation",
                "closing_style": "Clear next steps with urgency",
            },
            "market_expertise": {
                "key_phrases": [
                    "Inland Empire specialist",
                    "Logistics and healthcare relocations",
                    "Rancho Cucamonga expert",
                    "Amazon/Kaiser proximity advantages",
                ],
                "value_propositions": [
                    "Deep local knowledge of IE market",
                    "Industry-specific relocation expertise",
                    "AI-powered market analysis",
                    "24/7 availability and rapid response",
                ],
            },
            "emotion_mapping": {
                "new_lead": "enthusiastic",
                "qualification": "professional",
                "scheduling": "accommodating",
                "problem_solving": "empathetic",
                "urgency": "confident",
            },
        }

    def _load_qualification_questions(self) -> List[Dict[str, Any]]:
        """Load the 7-question qualification system for voice interaction"""
        return [
            {
                "id": 1,
                "question": "Are you currently working with another real estate agent?",
                "intent": "exclusivity_check",
                "follow_up": "What's your experience been like so far?",
                "disqualify_answers": ["yes", "working with someone", "have an agent"],
                "weight": 20,
            },
            {
                "id": 2,
                "question": "What brings you to the Inland Empire? Are you relocating for work?",
                "intent": "motivation_discovery",
                "follow_up": "Which company? I specialize in logistics and healthcare relocations.",
                "qualify_indicators": ["amazon", "kaiser", "ups", "fedex", "relocating", "new job"],
                "weight": 15,
            },
            {
                "id": 3,
                "question": "What's your timeline for finding a home?",
                "intent": "urgency_assessment",
                "follow_up": "That's great timing with current market conditions.",
                "qualify_indicators": ["immediately", "30 days", "60 days", "asap", "urgent"],
                "disqualify_answers": ["just looking", "no rush", "maybe next year"],
                "weight": 25,
            },
            {
                "id": 4,
                "question": "Have you been pre-approved for financing?",
                "intent": "financial_readiness",
                "follow_up": "I can connect you with excellent lenders familiar with IE market.",
                "qualify_indicators": ["yes", "pre-approved", "cash", "ready"],
                "weight": 20,
            },
            {
                "id": 5,
                "question": "What price range are you considering?",
                "intent": "budget_qualification",
                "follow_up": "That budget gives you excellent options in Rancho Cucamonga.",
                "qualify_threshold": 400000,  # Minimum budget
                "weight": 15,
            },
            {
                "id": 6,
                "question": "Any specific neighborhoods or areas you're interested in?",
                "intent": "location_preferences",
                "follow_up": "I have deep expertise in that area. Let me share some insights.",
                "qualify_indicators": ["etiwanda", "alta loma", "central", "victoria gardens"],
                "weight": 5,
            },
            {
                "id": 7,
                "question": "What's prompting the move? Why are you looking to buy or sell right now?",
                "intent": "motivation_discovery",
                "follow_up": "I understand. Knowing the 'why' helps me find the perfect strategy for you.",
                "qualify_indicators": ["upsizing", "downsizing", "investment", "school district", "work"],
                "weight": 10,
            },
        ]

    async def handle_incoming_call(self, phone_number: str, caller_name: Optional[str] = None) -> VoiceCallContext:
        """Initialize handling of incoming call"""
        call_id = str(uuid.uuid4())

        # Create call context
        context = VoiceCallContext(call_id=call_id, phone_number=phone_number, caller_name=caller_name)

        # Check if returning client
        existing_context = await self._check_existing_client(phone_number)
        if existing_context:
            context.call_type = CallType.EXISTING_CLIENT
            context.priority = CallPriority.HIGH

        # Store active call
        self.active_calls[call_id] = context

        logger.info(f"Incoming call initialized: {call_id} from {phone_number}")
        return context

    async def process_voice_input(self, call_id: str, speech_text: str, audio_confidence: float = 1.0) -> VoiceResponse:
        """Process voice input and generate intelligent response"""

        if call_id not in self.active_calls:
            return VoiceResponse(
                text="I'm sorry, I don't have a record of this call. Let me transfer you to Jorge.",
                emotion="empathetic",
            )

        context = self.active_calls[call_id]

        try:
            # Update transcript
            context.transcript.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "speaker": "caller",
                    "text": speech_text,
                    "confidence": audio_confidence,
                }
            )

            # Analyze intent and sentiment
            intent_analysis = await self._analyze_intent(speech_text, context)
            sentiment = await self._analyze_sentiment(speech_text)

            context.detected_intent.extend(intent_analysis.get("intents", []))
            context.sentiment_score = sentiment.get("score", 0.0)
            context.confidence_score = audio_confidence

            # Determine conversation stage and routing
            routing_decision = await self._make_routing_decision(context, speech_text)

            if routing_decision["should_transfer"]:
                context.should_transfer_to_jorge = True
                context.transfer_reason = routing_decision["reason"]
                return await self._generate_transfer_response(context)

            # Generate AI response based on conversation stage
            ai_response = await self._generate_contextual_response(context, speech_text, intent_analysis, sentiment)

            # Update conversation context
            await self._update_conversation_context(context, speech_text, ai_response)

            # Store response in context
            context.ai_responses.append(ai_response.text)
            context.transcript.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "speaker": "ai_jorge",
                    "text": ai_response.text,
                    "confidence": 1.0,
                }
            )

            # Cache conversation state
            await self._cache_conversation_state(context)

            return ai_response

        except Exception as e:
            logger.error(f"Error processing voice input for call {call_id}: {e}")
            return VoiceResponse(
                text="I apologize for the technical difficulty. Let me connect you with Jorge right away.",
                emotion="empathetic",
            )

    async def _analyze_intent(self, speech_text: str, context: VoiceCallContext) -> Dict[str, Any]:
        """Analyze speaker intent using Claude"""

        cache_key = f"intent_analysis:{hash(speech_text)}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result

        prompt = f"""
Analyze this caller's intent in a real estate phone conversation:

Caller said: "{speech_text}"

Current conversation stage: {context.conversation_stage.value}
Call type: {context.call_type.value}

Identify:
1. Primary intent (information, scheduling, qualification, objection, etc.)
2. Emotional state (excited, concerned, frustrated, neutral)
3. Urgency level (high, medium, low)
4. Qualification indicators (budget mentions, timeline, location preferences)
5. Red flags (already working with agent, just browsing, etc.)

Return JSON with: intents, emotion, urgency, qualification_signals, red_flags
"""

        try:
            response = await self.llm_client.agenerate(prompt=prompt, max_tokens=500, temperature=0.3)

            # Parse JSON response
            result = json.loads(response.content)
            await self.cache.set(cache_key, result, ttl=300)
            return result

        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}")
            return {
                "intents": ["general_inquiry"],
                "emotion": "neutral",
                "urgency": "medium",
                "qualification_signals": [],
                "red_flags": [],
            }

    async def _analyze_sentiment(self, speech_text: str) -> Dict[str, float]:
        """Analyze sentiment of speech input"""

        # Simple sentiment analysis - can be enhanced with more sophisticated models
        positive_words = [
            "excited",
            "interested",
            "love",
            "perfect",
            "amazing",
            "great",
            "excellent",
            "ready",
            "definitely",
            "absolutely",
            "fantastic",
            "wonderful",
        ]

        negative_words = [
            "concerned",
            "worried",
            "expensive",
            "problem",
            "issue",
            "disappointed",
            "frustrated",
            "difficult",
            "complicated",
            "unsure",
            "hesitant",
        ]

        text_lower = speech_text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        # Calculate sentiment score (-1 to 1)
        total_words = len(speech_text.split())
        if total_words == 0:
            return {"score": 0.0, "confidence": 0.0}

        score = (positive_count - negative_count) / max(total_words / 10, 1)
        score = max(-1.0, min(1.0, score))

        return {"score": score, "confidence": min((positive_count + negative_count) / total_words, 1.0)}

    async def _make_routing_decision(self, context: VoiceCallContext, current_input: str) -> Dict[str, Any]:
        """Make intelligent routing decision based on conversation context"""

        # High-priority transfer triggers
        transfer_triggers = [
            "speak to jorge",
            "talk to the agent",
            "human agent",
            "real person",
            "not satisfied",
            "complaint",
            "problem with",
            "emergency",
            "urgent matter",
        ]

        # Check for explicit transfer requests
        current_lower = current_input.lower()
        for trigger in transfer_triggers:
            if trigger in current_lower:
                return {
                    "should_transfer": True,
                    "reason": f"Explicit request: {trigger}",
                    "priority": CallPriority.URGENT,
                }

        # Qualification-based routing
        qualification_score = await self._calculate_qualification_score(context)
        context.qualification_score = qualification_score

        # Transfer high-value qualified leads
        if qualification_score >= 70:
            return {
                "should_transfer": True,
                "reason": f"High qualification score: {qualification_score}",
                "priority": CallPriority.HIGH,
            }

        # Continue with AI for medium/low qualified leads
        return {
            "should_transfer": False,
            "reason": f"Continuing AI conversation (score: {qualification_score})",
            "priority": CallPriority.MEDIUM,
        }

    async def _calculate_qualification_score(self, context: VoiceCallContext) -> int:
        """Calculate lead qualification score based on conversation data"""

        score = 0
        max_score = 100

        # Timeline urgency (25 points)
        if context.timeline:
            if any(urgent in context.timeline.lower() for urgent in ["immediately", "asap", "30 days", "urgent"]):
                score += 25
            elif any(medium in context.timeline.lower() for medium in ["60 days", "2 months", "soon"]):
                score += 15

        # Budget qualification (20 points)
        if context.budget_range and context.budget_range[0] >= 400000:
            score += 20

        # Employment/relocation (20 points)
        if context.employer:
            if any(employer in context.employer.lower() for employer in ["amazon", "kaiser", "ups", "fedex"]):
                score += 20
            else:
                score += 10

        # Pre-approval/financing readiness (15 points)
        financing_indicators = []
        for transcript_item in context.transcript:
            if any(
                indicator in transcript_item["text"].lower()
                for indicator in ["pre-approved", "pre-qualification", "cash", "financing ready", "loan approved"]
            ):
                score += 15
                break

        # Exclusivity (15 points deduction if working with another agent)
        for transcript_item in context.transcript:
            if any(
                exclusive in transcript_item["text"].lower()
                for exclusive in ["working with", "have an agent", "another agent"]
            ):
                score -= 15
                break

        # Engagement level (5 points)
        if len(context.transcript) >= 4:  # At least 2 back-and-forth exchanges
            score += 5

        return max(0, min(score, max_score))

    async def _generate_contextual_response(
        self, context: VoiceCallContext, user_input: str, intent_analysis: Dict[str, Any], sentiment: Dict[str, float]
    ) -> VoiceResponse:
        """Generate contextual AI response using Jorge's voice profile"""

        # Determine conversation stage progression
        next_stage = await self._determine_next_conversation_stage(context, user_input, intent_analysis)
        context.conversation_stage = next_stage

        # Build Jorge-specific prompt
        jorge_prompt = await self._build_jorge_voice_prompt(context, user_input, intent_analysis, sentiment)

        # Generate response using Claude
        response = await self.rc_assistant.generate_response(
            jorge_prompt,
            conversation_history=[
                {"role": "user" if i % 2 == 0 else "assistant", "content": item["text"]}
                for i, item in enumerate(context.transcript[-6:])  # Last 6 exchanges
            ],
        )

        # Determine emotional tone and pace
        emotion = self._determine_response_emotion(context, intent_analysis, sentiment)
        pace = self._determine_response_pace(context, intent_analysis)

        # Generate suggested actions
        suggested_actions = await self._generate_suggested_actions(context, response)

        return VoiceResponse(
            text=response,
            emotion=emotion,
            pace=pace,
            confidence=0.9,
            next_expected_input=self._predict_next_input(context, response),
            suggested_actions=suggested_actions,
        )

    async def _build_jorge_voice_prompt(
        self, context: VoiceCallContext, user_input: str, intent_analysis: Dict[str, Any], sentiment: Dict[str, float]
    ) -> str:
        """Build Jorge-specific voice prompt with market expertise"""

        base_prompt = f"""
You are Jorge Martinez, speaking on the phone as a top Inland Empire real estate agent. You're having a natural phone conversation with a potential client.

JORGE'S VOICE CHARACTERISTICS:
- Warm, professional, and confident
- Deep expertise in Rancho Cucamonga/Inland Empire
- Specializes in logistics and healthcare worker relocations
- Speaks with authority about local market conditions
- Always benefit-focused in explanations
- Creates urgency through market knowledge

CURRENT CONTEXT:
- Conversation stage: {context.conversation_stage.value}
- Caller sentiment: {sentiment.get("score", 0):.2f} (positive if >0)
- Detected intent: {", ".join(intent_analysis.get("intents", []))}
- Qualification score: {context.qualification_score}/100

CALLER INFORMATION:
- Phone: {context.phone_number}
- Name: {context.caller_name or "Not provided"}
- Employer: {context.employer or "Unknown"}
- Timeline: {context.timeline or "Not specified"}
- Budget: {f"${context.budget_range[0]:,}-${context.budget_range[1]:,}" if context.budget_range else "Not specified"}

CONVERSATION GUIDELINES FOR THIS STAGE:
"""

        # Add stage-specific guidance
        stage_guidance = {
            ConversationStage.GREETING: """
- Warmly introduce yourself as Jorge Martinez
- Immediately establish IE expertise
- Ask how you can help with their real estate needs
- Listen for employer/relocation indicators
""",
            ConversationStage.QUALIFICATION: """
- Use the 7-question qualification system naturally
- Focus on timeline, budget, and current agent status
- Probe for employer details (Amazon, Kaiser, etc.)
- Identify urgency and motivation
""",
            ConversationStage.DISCOVERY: """
- Dive deeper into their specific needs
- Share relevant IE market insights
- Connect their employer to neighborhood benefits
- Build value through local expertise
""",
            ConversationStage.SCHEDULING: """
- Propose specific meeting times
- Create urgency through market conditions
- Offer virtual or in-person options
- Confirm contact information
""",
            ConversationStage.INFORMATION: """
- Provide valuable market insights
- Share neighborhood expertise
- Discuss current opportunities
- Position yourself as the IE expert
""",
        }

        base_prompt += stage_guidance.get(context.conversation_stage, "Provide helpful, expert guidance.")

        # Add current user input
        base_prompt += f'\n\nCaller just said: "{user_input}"\n\n'

        # Add market intelligence if relevant
        if context.neighborhood_preferences:
            base_prompt += f"Neighborhoods of interest: {', '.join(context.neighborhood_preferences)}\n"

        base_prompt += """
Respond naturally as Jorge would on a phone call. Be conversational, not scripted.
Keep responses under 50 words for natural phone conversation flow.
End with a question or clear next step when appropriate.
"""

        return base_prompt

    def _determine_response_emotion(
        self, context: VoiceCallContext, intent_analysis: Dict[str, Any], sentiment: Dict[str, float]
    ) -> str:
        """Determine appropriate emotional tone for response"""

        # Map context to emotions
        if "objection" in intent_analysis.get("intents", []):
            return "empathetic"
        elif context.qualification_score >= 70:
            return "enthusiastic"
        elif sentiment.get("score", 0) < -0.3:
            return "empathetic"
        elif "urgent" in intent_analysis.get("urgency", "").lower():
            return "confident"
        else:
            return "professional"

    def _determine_response_pace(self, context: VoiceCallContext, intent_analysis: Dict[str, Any]) -> str:
        """Determine appropriate speaking pace"""

        if "urgent" in intent_analysis.get("urgency", "").lower():
            return "normal"  # Don't rush urgent callers
        elif context.conversation_stage == ConversationStage.QUALIFICATION:
            return "normal"
        elif "confused" in intent_analysis.get("emotion", "").lower():
            return "slow"
        else:
            return "normal"

    async def _determine_next_conversation_stage(
        self, context: VoiceCallContext, user_input: str, intent_analysis: Dict[str, Any]
    ) -> ConversationStage:
        """Determine next conversation stage based on context"""

        current_stage = context.conversation_stage
        intents = intent_analysis.get("intents", [])

        # Stage progression logic
        if current_stage == ConversationStage.GREETING:
            if "scheduling" in intents or "meeting" in user_input.lower():
                return ConversationStage.SCHEDULING
            else:
                return ConversationStage.QUALIFICATION

        elif current_stage == ConversationStage.QUALIFICATION:
            if context.qualification_score >= 50:
                if "schedule" in user_input.lower() or "meet" in user_input.lower():
                    return ConversationStage.SCHEDULING
                else:
                    return ConversationStage.DISCOVERY
            else:
                return ConversationStage.QUALIFICATION

        elif current_stage == ConversationStage.DISCOVERY:
            if "schedule" in user_input.lower() or "when can" in user_input.lower():
                return ConversationStage.SCHEDULING
            else:
                return ConversationStage.INFORMATION

        elif current_stage == ConversationStage.SCHEDULING:
            return ConversationStage.CLOSING

        return current_stage

    async def _generate_suggested_actions(self, context: VoiceCallContext, response: str) -> List[str]:
        """Generate suggested follow-up actions based on conversation"""

        actions = []

        # Scheduling actions
        if "schedule" in response.lower() or "meet" in response.lower():
            actions.append("schedule_appointment")
            actions.append("send_calendar_link")

        # Information follow-up
        if "neighborhood" in response.lower() or "area" in response.lower():
            actions.append("send_neighborhood_report")

        # Market analysis
        if "market" in response.lower() or "price" in response.lower():
            actions.append("generate_market_analysis")

        # Qualification follow-up
        if context.qualification_score >= 70:
            actions.append("create_high_priority_lead")
            actions.append("schedule_jorge_callback")

        return actions

    def _predict_next_input(self, context: VoiceCallContext, response: str) -> Optional[str]:
        """Predict what the caller might say next"""

        if "?" in response:
            if "when" in response.lower():
                return "timeline_response"
            elif "where" in response.lower():
                return "location_preference"
            elif "what" in response.lower():
                return "specification_details"

        if "schedule" in response.lower():
            return "availability_confirmation"

        return None

    async def _update_conversation_context(
        self, context: VoiceCallContext, user_input: str, ai_response: VoiceResponse
    ):
        """Update conversation context based on latest exchange"""

        # Extract information from user input
        user_lower = user_input.lower()

        # Extract employer information
        employers = ["amazon", "kaiser", "ups", "fedex", "usps", "dhl", "walmart"]
        for employer in employers:
            if employer in user_lower:
                context.employer = employer.title()
                break

        # Extract timeline information
        timeline_patterns = [
            (r"(\d+)\s*(days?|weeks?|months?)", "timeline"),
            (r"(Union[immediately, asap]|right away)", "urgent"),
            (r"(no Union[rush, just] Union[looking, maybe])", "flexible"),
        ]

        for pattern, category in timeline_patterns:
            match = re.search(pattern, user_lower)
            if match:
                context.timeline = match.group(0)
                break

        # Extract budget information
        budget_match = re.search(r"\$?([0-9,]+)", user_input.replace(",", ""))
        if budget_match and "budget" in user_lower or "price" in user_lower:
            try:
                budget = int(budget_match.group(1).replace(",", ""))
                if budget > 100000:  # Reasonable budget threshold
                    context.budget_range = (budget * 0.9, budget * 1.1)
            except ValueError:
                pass

        # Extract neighborhood preferences
        ie_neighborhoods = [
            "etiwanda",
            "alta loma",
            "central",
            "victoria gardens",
            "terra vista",
            "day creek",
            "upland",
            "fontana",
            "ontario",
        ]
        for neighborhood in ie_neighborhoods:
            if neighborhood in user_lower:
                if neighborhood not in context.neighborhood_preferences:
                    context.neighborhood_preferences.append(neighborhood)

        # Update duration
        context.duration_seconds = int((datetime.now() - context.start_time).total_seconds())

    async def _cache_conversation_state(self, context: VoiceCallContext):
        """Cache conversation state for persistence"""

        cache_key = f"voice_call:{context.call_id}"
        cache_data = {"context": asdict(context), "timestamp": datetime.now().isoformat()}

        # Cache for 1 hour
        await self.cache.set(cache_key, cache_data, ttl=3600)

    async def _check_existing_client(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Check if caller is existing client"""

        cache_key = f"client_phone:{phone_number}"
        existing_data = await self.cache.get(cache_key)

        # In production, this would query CRM/database
        return existing_data

    async def _generate_transfer_response(self, context: VoiceCallContext) -> VoiceResponse:
        """Generate response for transferring to Jorge"""

        transfer_messages = [
            "Let me connect you with Jorge right away. He'll be able to help you personally.",
            "I'm transferring you to Jorge now. He's our Inland Empire specialist and will take excellent care of you.",
            "Jorge is available right now. Let me get him on the line for you.",
            "You'll want to speak directly with Jorge about this. Let me connect you immediately.",
        ]

        import random

        message = random.choice(transfer_messages)

        return VoiceResponse(
            text=message,
            emotion="professional",
            pace="normal",
            confidence=1.0,
            suggested_actions=["transfer_to_jorge", "log_high_priority_lead"],
        )

    async def handle_call_completion(self, call_id: str) -> Dict[str, Any]:
        """Process call completion and generate analytics"""

        if call_id not in self.active_calls:
            return {"error": "Call not found"}

        context = self.active_calls[call_id]

        # Calculate final metrics
        final_analytics = {
            "call_id": call_id,
            "duration": context.duration_seconds,
            "qualification_score": context.qualification_score,
            "conversation_stages": len(set([item.get("stage") for item in context.transcript if item.get("stage")])),
            "transfer_to_jorge": context.should_transfer_to_jorge,
            "automated_actions": len(context.automated_actions_taken),
            "sentiment_score": context.sentiment_score,
            "lead_quality": "high"
            if context.qualification_score >= 70
            else "medium"
            if context.qualification_score >= 40
            else "low",
        }

        # Generate follow-up actions
        follow_up_actions = await self._generate_call_follow_up_actions(context)
        final_analytics["follow_up_actions"] = follow_up_actions

        # Store call record
        await self._store_call_record(context, final_analytics)

        # Clean up active call
        del self.active_calls[call_id]

        logger.info(f"Call {call_id} completed with qualification score: {context.qualification_score}")

        return final_analytics

    async def _generate_call_follow_up_actions(self, context: VoiceCallContext) -> List[Dict[str, Any]]:
        """Generate intelligent follow-up actions based on call outcome"""

        actions = []

        # High-priority lead actions
        if context.qualification_score >= 70:
            actions.extend(
                [
                    {
                        "action": "schedule_jorge_callback",
                        "priority": "urgent",
                        "timeline": "within 1 hour",
                        "description": "High-qualified lead requires personal follow-up",
                    },
                    {
                        "action": "send_market_analysis",
                        "priority": "high",
                        "timeline": "within 2 hours",
                        "description": "Custom IE market analysis for their needs",
                    },
                ]
            )

        # Scheduling actions
        if context.conversation_stage == ConversationStage.SCHEDULING:
            actions.append(
                {
                    "action": "send_calendar_link",
                    "priority": "high",
                    "timeline": "immediately",
                    "description": "Send calendar booking link while interest is high",
                }
            )

        # Information follow-up
        if context.neighborhood_preferences:
            actions.append(
                {
                    "action": "neighborhood_report",
                    "priority": "medium",
                    "timeline": "within 24 hours",
                    "description": f"Detailed report for {', '.join(context.neighborhood_preferences)}",
                }
            )

        # CRM updates
        actions.append(
            {
                "action": "update_crm",
                "priority": "medium",
                "timeline": "within 4 hours",
                "description": "Update lead profile with conversation insights",
            }
        )

        return actions

    async def _store_call_record(self, context: VoiceCallContext, analytics: Dict[str, Any]):
        """Store complete call record for analytics and follow-up"""

        call_record = {
            "call_id": context.call_id,
            "timestamp": context.start_time.isoformat(),
            "phone_number": context.phone_number,
            "duration": context.duration_seconds,
            "transcript": context.transcript,
            "qualification_data": {
                "score": context.qualification_score,
                "employer": context.employer,
                "timeline": context.timeline,
                "budget_range": context.budget_range,
                "neighborhoods": context.neighborhood_preferences,
            },
            "routing_decision": {"transferred": context.should_transfer_to_jorge, "reason": context.transfer_reason},
            "analytics": analytics,
        }

        # Store in cache (in production, would go to database)
        cache_key = f"call_record:{context.call_id}"
        await self.cache.set(cache_key, call_record, ttl=7 * 24 * 3600)  # 7 days

        # Also store in daily analytics
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"daily_calls:{today}"
        daily_calls = await self.cache.get(daily_key) or []
        daily_calls.append(call_record)
        await self.cache.set(daily_key, daily_calls, ttl=30 * 24 * 3600)  # 30 days

    async def get_call_analytics(self, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
        """Get voice AI call analytics"""

        if not date_range:
            # Default to last 7 days
            from datetime import date, timedelta

            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            date_range = (start_date.isoformat(), end_date.isoformat())

        analytics = {
            "total_calls": 0,
            "avg_duration": 0,
            "qualification_distribution": {"high": 0, "medium": 0, "low": 0},
            "transfer_rate": 0,
            "top_industries": {},
            "conversion_metrics": {"appointments_scheduled": 0, "follow_up_actions": 0},
        }

        # Aggregate daily data (simplified - in production would query database)
        total_duration = 0
        transfers = 0

        start_date, end_date = date_range
        current = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()

        while current <= end:
            daily_key = f"daily_calls:{current.isoformat()}"
            daily_calls = await self.cache.get(daily_key) or []

            for call in daily_calls:
                analytics["total_calls"] += 1
                total_duration += call.get("duration", 0)

                if call.get("routing_decision", {}).get("transferred"):
                    transfers += 1

                # Qualification distribution
                score = call.get("qualification_data", {}).get("score", 0)
                if score >= 70:
                    analytics["qualification_distribution"]["high"] += 1
                elif score >= 40:
                    analytics["qualification_distribution"]["medium"] += 1
                else:
                    analytics["qualification_distribution"]["low"] += 1

                # Industry tracking
                employer = call.get("qualification_data", {}).get("employer")
                if employer:
                    analytics["top_industries"][employer] = analytics["top_industries"].get(employer, 0) + 1

            current += timedelta(days=1)

        # Calculate averages
        if analytics["total_calls"] > 0:
            analytics["avg_duration"] = total_duration / analytics["total_calls"]
            analytics["transfer_rate"] = transfers / analytics["total_calls"]

        return analytics


# Singleton instance
_voice_ai_handler = None


def get_voice_ai_handler() -> VoiceAIHandler:
    """Get singleton Voice AI Handler instance"""
    global _voice_ai_handler
    if _voice_ai_handler is None:
        _voice_ai_handler = VoiceAIHandler()
    return _voice_ai_handler
