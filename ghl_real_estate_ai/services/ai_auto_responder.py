"""
AI Context-Aware Auto-Responder Service
AI reads messages, understands context, and generates personalized responses

Feature 10: AI Context-Aware Auto-Responder
Intelligent 24/7 response system with context understanding and personality matching.
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ResponseConfidence(Enum):
    """Confidence levels for AI responses"""

    HIGH = "high"  # 90%+ confidence, auto-send safe
    MEDIUM = "medium"  # 70-90%, suggest to agent
    LOW = "low"  # <70%, escalate to human


class MessageIntent(Enum):
    """Detected message intents"""

    PROPERTY_INQUIRY = "property_inquiry"
    PRICING_QUESTION = "pricing_question"
    AVAILABILITY_CHECK = "availability_check"
    APPOINTMENT_REQUEST = "appointment_request"
    OBJECTION = "objection"
    GENERAL_QUESTION = "general_question"
    COMPLAINT = "complaint"
    THANK_YOU = "thank_you"


@dataclass
class ConversationContext:
    """Context for generating responses"""

    lead_id: str
    lead_name: str
    lead_history: List[Dict]
    current_message: str
    properties_viewed: List[Dict]
    lead_score: float
    tags: List[str]
    agent_name: str
    conversation_stage: str


@dataclass
class AIResponse:
    """Generated AI response"""

    response_id: str
    message: str
    confidence: float
    intent_detected: str
    reasoning: str
    suggested_actions: List[str]
    escalate_to_human: bool
    metadata: Dict[str, Any]


class AIAutoResponderService:
    """Service for AI-powered automatic responses"""

    def __init__(self, auto_send_threshold: float = 0.90):
        self.auto_send_threshold = auto_send_threshold
        self.response_templates = self._load_response_patterns()
        self.conversation_memory: Dict[str, List[Dict]] = {}

    def _load_response_patterns(self) -> Dict:
        """Load response patterns and strategies"""
        return {
            "property_inquiry": {
                "patterns": [
                    r"is.*available",
                    r"still.*for sale",
                    r"tell me about",
                    r"interested in.*property",
                ],
                "strategy": "enthusiasm_and_details",
            },
            "pricing_question": {
                "patterns": [r"how much", r"what.*price", r"cost", r"afford"],
                "strategy": "value_and_options",
            },
            "availability_check": {
                "patterns": [
                    r"when.*available",
                    r"can.*see",
                    r"schedule.*viewing",
                    r"visit",
                ],
                "strategy": "urgency_and_booking",
            },
            "objection": {
                "patterns": [
                    r"too expensive",
                    r"need to think",
                    r"not sure",
                    r"working with.*agent",
                ],
                "strategy": "empathy_and_reframe",
            },
        }

    def analyze_message(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze incoming message to understand intent and context"""

        # Detect intent
        intent = self._detect_intent(message)

        # Extract key information
        keywords = self._extract_keywords(message)
        sentiment = self._analyze_sentiment(message)
        urgency = self._detect_urgency(message)

        # Analyze conversation stage
        stage = self._determine_conversation_stage(context)

        return {
            "intent": intent,
            "keywords": keywords,
            "sentiment": sentiment,
            "urgency": urgency,
            "stage": stage,
            "requires_objection_handling": intent == MessageIntent.OBJECTION.value,
        }

    def _detect_intent(self, message: str) -> str:
        """Detect the intent of the message"""
        message_lower = message.lower()

        for intent, config in self.response_templates.items():
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower):
                    return intent

        return "general_question"

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract important keywords from message"""
        # Simple keyword extraction (in production, use NLP)
        keywords = []

        property_types = ["house", "condo", "apartment", "townhouse", "commercial"]
        features = ["bedroom", "bathroom", "garage", "pool", "yard"]
        locations = ["downtown", "suburb", "near", "area"]

        message_lower = message.lower()

        for keyword in property_types + features + locations:
            if keyword in message_lower:
                keywords.append(keyword)

        return keywords

    def _analyze_sentiment(self, message: str) -> str:
        """Analyze message sentiment"""
        message_lower = message.lower()

        positive_words = ["love", "great", "perfect", "interested", "excited"]
        negative_words = ["expensive", "small", "old", "concerned", "worried"]

        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level in message"""
        message_lower = message.lower()

        high_urgency = ["asap", "urgent", "now", "immediately", "today", "quickly"]
        medium_urgency = ["soon", "this week", "next few days"]

        if any(word in message_lower for word in high_urgency):
            return "high"
        elif any(word in message_lower for word in medium_urgency):
            return "medium"
        else:
            return "low"

    def _determine_conversation_stage(self, context: ConversationContext) -> str:
        """Determine what stage of conversation we're in"""
        message_count = len(context.lead_history)

        if message_count == 0:
            return "initial_contact"
        elif message_count <= 3:
            return "qualification"
        elif context.lead_score > 70:
            return "closing"
        else:
            return "nurture"

    def generate_response(self, message: str, context: ConversationContext, safety_mode: bool = True) -> AIResponse:
        """Generate AI response to incoming message"""

        # Analyze the message
        analysis = self.analyze_message(message, context)

        # Generate response based on analysis
        response_text, confidence, reasoning = self._generate_contextual_response(message, context, analysis)

        # Determine if we should escalate
        escalate = confidence < 0.70 or analysis["requires_objection_handling"]

        # Suggest follow-up actions
        suggested_actions = self._suggest_actions(analysis, context)

        response = AIResponse(
            response_id=f"resp_{datetime.utcnow().timestamp()}",
            message=response_text,
            confidence=confidence,
            intent_detected=analysis["intent"],
            reasoning=reasoning,
            suggested_actions=suggested_actions,
            escalate_to_human=escalate,
            metadata={
                "analysis": analysis,
                "safety_mode": safety_mode,
                "auto_send_approved": confidence >= self.auto_send_threshold and not escalate,
            },
        )

        return response

    def _generate_contextual_response(
        self, message: str, context: ConversationContext, analysis: Dict
    ) -> Tuple[str, float, str]:
        """Generate contextual response with confidence score"""

        intent = analysis["intent"]
        stage = analysis["stage"]
        sentiment = analysis["sentiment"]
        urgency = analysis["urgency"]

        # Build personalized response
        if intent == "property_inquiry":
            response = self._respond_to_property_inquiry(context, analysis)
            confidence = 0.92
            reasoning = "Clear property inquiry with sufficient context"

        elif intent == "pricing_question":
            response = self._respond_to_pricing(context, analysis)
            confidence = 0.85
            reasoning = "Pricing question detected, providing value-focused response"

        elif intent == "availability_check":
            response = self._respond_to_availability(context, analysis)
            confidence = 0.95
            reasoning = "Straightforward availability check"

        elif intent == "objection":
            response = self._handle_objection(message, context, analysis)
            confidence = 0.70
            reasoning = "Objection detected, using empathy approach but recommending human review"

        else:
            response = self._respond_general(context, analysis)
            confidence = 0.75
            reasoning = "General inquiry, safe generic response"

        # Adjust response for urgency
        if urgency == "high":
            response = self._add_urgency_acknowledgment(response)
            confidence += 0.05

        # Adjust for sentiment
        if sentiment == "negative":
            response = self._add_empathy(response)

        # Personalize with name
        response = response.replace("{name}", context.lead_name)
        response = response.replace("{agent_name}", context.agent_name)

        return response, min(confidence, 0.99), reasoning

    def _respond_to_property_inquiry(self, context: ConversationContext, analysis: Dict) -> str:
        """Generate response for property inquiries"""

        if context.properties_viewed:
            property_ref = context.properties_viewed[0].get("address", "the property")
            return (
                f"Hi {context.lead_name}! Yes, {property_ref} is still available! "
                f"Based on your interest in {', '.join(analysis['keywords'][:2])}, "
                f"this property is perfect for you. The features include... "
                f"Would you like to schedule a walkthrough this week? "
                f"I have availability Tuesday-Thursday. - {context.agent_name}"
            )
        else:
            return (
                f"Hi {context.lead_name}! Thanks for reaching out! "
                f"I'd love to help you find the perfect property. "
                f"Based on what you mentioned about {', '.join(analysis['keywords'][:2])}, "
                f"I have some great options. Can you tell me a bit more about your ideal home? "
                f"- {context.agent_name}"
            )

    def _respond_to_pricing(self, context: ConversationContext, analysis: Dict) -> str:
        """Generate response for pricing questions"""

        return (
            f"Great question, {context.lead_name}! The property is priced at [PRICE] "
            f"which is actually excellent value considering [FEATURE_1], [FEATURE_2], and the location. "
            f"Many of my clients find the investment pays off quickly because... "
            f"I also have financing options that could make this very affordable. "
            f"Want to discuss numbers in more detail? I'm available for a quick call today. "
            f"- {context.agent_name}"
        )

    def _respond_to_availability(self, context: ConversationContext, analysis: Dict) -> str:
        """Generate response for availability checks"""

        urgency_note = ""
        if analysis["urgency"] == "high":
            urgency_note = "I can prioritize this for you since you mentioned urgency. "

        return (
            f"Hi {context.lead_name}! The property is available for viewing. {urgency_note}"
            f"I have openings this week: Tuesday 2-5 PM, Wednesday 10 AM-1 PM, Thursday 3-6 PM. "
            f"Which time works best for you? I'll send you the address and directions. "
            f"Looking forward to showing you around! - {context.agent_name}"
        )

    def _handle_objection(self, message: str, context: ConversationContext, analysis: Dict) -> str:
        """Handle objections with empathy"""

        return (
            f"I totally understand, {context.lead_name}. Many of my clients had similar concerns initially. "
            f"What I've found is that [REFRAME]. Let me share some examples... "
            f"Would it help if we discussed this over a quick call? No pressure, just want to make sure "
            f"you have all the information to make the best decision. - {context.agent_name}"
        )

    def _respond_general(self, context: ConversationContext, analysis: Dict) -> str:
        """General response for unclear intent"""

        return (
            f"Hi {context.lead_name}! Thanks for your message. "
            f"I want to make sure I give you the best answer. "
            f"Could you tell me a bit more about what you're looking for? "
            f"I'm here to help! - {context.agent_name}"
        )

    def _add_urgency_acknowledgment(self, response: str) -> str:
        """Add urgency acknowledgment to response"""
        return f"⚡ Quick response (I saw you need this soon!): {response}"

    def _add_empathy(self, response: str) -> str:
        """Add empathetic language"""
        empathy_phrases = [
            "I completely understand how you feel. ",
            "That's a valid concern, and I'm glad you brought it up. ",
            "I hear you, and I appreciate your honesty. ",
        ]
        return empathy_phrases[0] + response

    def _suggest_actions(self, analysis: Dict, context: ConversationContext) -> List[str]:
        """Suggest follow-up actions"""

        actions = []

        if analysis["intent"] == "property_inquiry":
            actions.append("Send property details")
            actions.append("Schedule viewing")

        if analysis["urgency"] == "high":
            actions.append("Priority flag - respond within 1 hour")

        if context.lead_score > 70:
            actions.append("Assign to senior agent")
            actions.append("Add to hot leads list")

        if analysis["intent"] == "objection":
            actions.append("Review objection handling guide")
            actions.append("Escalate to sales manager")

        return actions

    def should_auto_send(self, response: AIResponse, safety_mode: bool = True) -> bool:
        """Determine if response should be sent automatically"""

        if safety_mode:
            # In safety mode, only auto-send very high confidence responses
            return (
                response.confidence >= 0.95
                and not response.escalate_to_human
                and response.intent_detected in ["availability_check", "thank_you"]
            )
        else:
            # Normal mode uses confidence threshold
            return response.confidence >= self.auto_send_threshold and not response.escalate_to_human

    def get_conversation_history(self, lead_id: str) -> List[Dict]:
        """Get conversation history for a lead"""
        return self.conversation_memory.get(lead_id, [])

    def add_to_conversation_history(
        self,
        lead_id: str,
        message: str,
        sender: str,
        response: Optional[AIResponse] = None,
    ):
        """Add message to conversation history"""

        if lead_id not in self.conversation_memory:
            self.conversation_memory[lead_id] = []

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "sender": sender,
            "response": (
                {
                    "message": response.message,
                    "confidence": response.confidence,
                    "intent": response.intent_detected,
                }
                if response
                else None
            ),
        }

        self.conversation_memory[lead_id].append(entry)

    def get_response_stats(self) -> Dict[str, Any]:
        """Get statistics on AI responses"""

        total_conversations = len(self.conversation_memory)
        total_messages = sum(len(conv) for conv in self.conversation_memory.values())

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": total_messages / max(total_conversations, 1),
            "auto_send_threshold": self.auto_send_threshold,
        }


# Demo function
def demo_ai_auto_responder():
    """Demonstrate AI auto-responder capabilities"""
    service = AIAutoResponderService(auto_send_threshold=0.90)

    print("🤖 AI Context-Aware Auto-Responder Demo\n")

    # Create test context
    context = ConversationContext(
        lead_id="lead_123",
        lead_name="Sarah Johnson",
        lead_history=[],
        current_message="Is the 3-bedroom house on Main St still available?",
        properties_viewed=[{"address": "123 Main St", "beds": 3, "price": 450000}],
        lead_score=75.0,
        tags=["first_time_buyer", "qualified"],
        agent_name="Mike Reynolds",
        conversation_stage="qualification",
    )

    # Test different messages
    test_messages = [
        "Is the 3-bedroom house on Main St still available?",
        "How much does it cost?",
        "Can I see it this week?",
        "It seems too expensive for me",
        "Thanks for the info!",
    ]

    for message in test_messages:
        print(f'\n📨 Incoming: "{message}"')

        response = service.generate_response(message, context, safety_mode=False)

        print(f"🎯 Intent: {response.intent_detected}")
        print(f"📊 Confidence: {response.confidence:.0%}")
        print(f"💭 Reasoning: {response.reasoning}")
        print(f"✉️  Response: {response.message[:150]}...")
        print(f"🤔 Escalate: {response.escalate_to_human}")
        print(f"🚀 Auto-send: {service.should_auto_send(response, safety_mode=False)}")

        if response.suggested_actions:
            print(f"📋 Actions: {', '.join(response.suggested_actions)}")

    # Stats
    stats = service.get_response_stats()
    print(f"\n📊 Service Stats:")
    print(f"   Total conversations: {stats['total_conversations']}")
    print(f"   Auto-send threshold: {stats['auto_send_threshold']:.0%}")


if __name__ == "__main__":
    demo_ai_auto_responder()
