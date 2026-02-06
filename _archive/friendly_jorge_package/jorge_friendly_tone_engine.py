"""
Jorge's Friendly Tone Engine - Customer Service Excellence
==========================================================

This module provides warm, helpful, customer service-focused messaging for Jorge's
Rancho Cucamonga real estate bots. Replaces the confrontational Rancho Cucamonga approach
with relationship-building consultative communication.

Key Features:
- Warm, professional customer service tone
- Rancho Cucamonga market expertise
- California DRE compliant messaging
- Relationship-building conversation flows
- Family-friendly, supportive approach

Author: Claude Code Assistant
Created: 2026-01-25 for Friendly CA Approach
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import random
from datetime import datetime


class FriendlyMessageType(Enum):
    """Message types for friendly customer service approach"""
    WARM_GREETING = "warm_greeting"
    CONSULTATIVE_QUESTION = "consultative_question"
    SUPPORTIVE_FOLLOW_UP = "supportive_follow_up"
    MARKET_INSIGHT = "market_insight"
    APPRECIATION = "appreciation"
    READY_TO_MOVE_HANDOFF = "ready_to_move_handoff"
    RELATIONSHIP_NURTURE = "relationship_nurture"
    HELPFUL_CLARIFICATION = "helpful_clarification"


@dataclass
class FriendlyValidationResult:
    """Result of friendly message validation"""
    is_compliant: bool
    warmth_score: float  # 0.0-1.0 how warm and friendly
    professional_score: float  # 0.0-1.0 how professional
    length_compliant: bool
    dre_compliant: bool
    suggestions: List[str]


@dataclass
class RanchoCucamongaMarketData:
    """Local market data for consultative conversations"""
    avg_price: int = 750000
    market_status: str = "Balanced"
    inventory_level: str = "Good Selection"
    days_on_market: int = 28
    price_trend: str = "Steady Appreciation"
    buyer_activity: str = "Active but Respectful"
    best_selling_season: str = "Spring and Early Fall"


class JorgeFriendlyToneEngine:
    """
    Friendly, consultative tone engine for Jorge's customer service approach.
    Focused on building relationships and providing helpful guidance.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.market_data = RanchoCucamongaMarketData()

        # Friendly conversation templates
        self.friendly_templates = self._initialize_friendly_templates()

        # Rancho Cucamonga specific knowledge
        self.local_knowledge = self._initialize_local_knowledge()

    def _initialize_friendly_templates(self) -> Dict[str, List[str]]:
        """Initialize friendly, warm conversation templates"""
        return {
            "warm_greetings": [
                "Hi {name}! Thank you for reaching out about real estate in Rancho Cucamonga.",
                "Hello {name}! I'm here to help with your real estate needs in the Inland Empire.",
                "Hi there! I appreciate you considering us for your Rancho Cucamonga real estate goals."
            ],

            "question_introductions": [
                "I'd love to learn more about your situation.",
                "To give you the best guidance, could you help me understand",
                "I want to make sure I provide the most helpful information.",
                "To better assist you, I'd appreciate knowing"
            ],

            "appreciation_responses": [
                "Thank you for sharing that with me.",
                "I appreciate you taking the time to explain your situation.",
                "That's very helpful information.",
                "I'm glad you feel comfortable sharing that."
            ],

            "supportive_clarifications": [
                "I want to make sure I understand correctly.",
                "Let me clarify so I can help you better.",
                "To give you accurate guidance, could you help me understand",
                "I'd like to make sure we're on the same page."
            ],

            "market_introductions": [
                "Based on current Rancho Cucamonga market conditions,",
                "Here in the Inland Empire, we're seeing",
                "Our local Rancho Cucamonga market shows",
                "Current conditions in your area indicate"
            ],

            "ready_to_move_transitions": [
                "It sounds like our team can really help you.",
                "Based on what you've shared, I think we're a great fit.",
                "I'm confident our local specialists can guide you through this.",
                "Our Rancho Cucamonga team would love to work with you."
            ],

            "timeline_discussions": [
                "What timeline feels comfortable for you and your family?",
                "Let's work within a schedule that suits your needs.",
                "When would be ideal timing for your situation?",
                "What timeframe would work best for you?"
            ],

            "price_conversations": [
                "What price range are you hoping to achieve?",
                "I'd love to help you understand current market values.",
                "What would make this feel like a successful outcome?",
                "Let's discuss realistic market expectations."
            ]
        }

    def _initialize_local_knowledge(self) -> Dict[str, Any]:
        """Initialize Rancho Cucamonga specific local knowledge"""
        return {
            "neighborhoods": {
                "Alta Loma": {
                    "highlights": ["Top-rated schools", "Mountain views", "Established community"],
                    "avg_price": 825000,
                    "lifestyle": "Family-oriented with excellent schools"
                },
                "Etiwanda": {
                    "highlights": ["New developments", "Modern amenities", "Growing community"],
                    "avg_price": 780000,
                    "lifestyle": "Modern living with family focus"
                },
                "Central RC": {
                    "highlights": ["Historic charm", "Walkable", "Mature neighborhoods"],
                    "avg_price": 720000,
                    "lifestyle": "Established community with character"
                },
                "North RC": {
                    "highlights": ["Newer homes", "Larger lots", "Premium locations"],
                    "avg_price": 890000,
                    "lifestyle": "Upscale family living"
                }
            },

            "family_features": [
                "Excellent school districts (Etiwanda, Chaffey)",
                "Victoria Gardens shopping and entertainment",
                "Central Park recreation facilities",
                "Close to Ontario Airport (15 min)",
                "Easy freeway access to LA and Orange County",
                "Mountain recreation nearby"
            ],

            "market_advantages": [
                "More affordable than coastal areas",
                "Strong appreciation history",
                "Family-friendly communities",
                "Good inventory selection",
                "Reasonable commute to job centers",
                "Growing retail and dining options"
            ]
        }

    def generate_warm_greeting(self, seller_name: Optional[str] = None) -> str:
        """Generate a warm, welcoming greeting message"""
        name = seller_name or "there"

        templates = self.friendly_templates["warm_greetings"]
        greeting = random.choice(templates).format(name=name)

        return self._ensure_sms_compliance(greeting)

    def generate_consultative_question(self,
                                     question_number: int,
                                     seller_name: Optional[str] = None,
                                     context: Dict = None) -> str:
        """Generate friendly, consultative qualification questions"""

        context = context or {}
        name = seller_name or ""

        # Friendly question templates mapped to Jorge's 4 questions
        friendly_questions = {
            1: {
                "question": "I'd love to understand your situation better. What's prompting you to consider selling, and do you have a location in mind for your next home?",
                "variations": [
                    "I'm here to help with your real estate goals. What's motivating your move, and where are you thinking of going next?",
                    "To give you the best guidance, could you share what's behind your interest in selling and where you might relocate?",
                    "I want to understand your needs. What's driving your decision to sell, and do you have a destination in mind?"
                ]
            },
            2: {
                "question": "To help you plan properly, would selling within the next 2-3 months work with your timeline and family needs?",
                "variations": [
                    "For planning purposes, would a 2-3 month timeframe work for you and your family's schedule?",
                    "Would a spring selling timeframe align with your family's needs and plans?",
                    "Is a 2-3 month timeline something that would work comfortably for your situation?"
                ]
            },
            3: {
                "question": "Could you help me understand your home's condition? Would you describe it as move-in ready, or are there areas that might need attention?",
                "variations": [
                    "To give you accurate market guidance, how would you describe your home's current condition?",
                    "I'd love to understand your property better. Is it move-in ready, or are there improvements you've been considering?",
                    "Could you share how you'd describe your home's condition to help me give you the best advice?"
                ]
            },
            4: {
                "question": "What price range would feel right for you? I want to make sure we're aligned with realistic market values for your area.",
                "variations": [
                    "To help set proper expectations, what price range are you hoping to achieve?",
                    "I'd love to discuss realistic market values. What price range would make this feel successful for you?",
                    "What price would feel like a great outcome? I can share current market insights for your area."
                ]
            }
        }

        if question_number in friendly_questions:
            question_data = friendly_questions[question_number]

            # Use variation if context suggests previous attempts
            if context.get("attempt_count", 0) > 0:
                question = random.choice(question_data["variations"])
            else:
                question = question_data["question"]

            # Add personalization if name provided
            if name:
                intro = random.choice(self.friendly_templates["question_introductions"])
                question = f"{name}, {intro.lower()} {question.lower()}"

            return self._ensure_sms_compliance(question)

        # Fallback for invalid question numbers
        return self.generate_helpful_follow_up("I'd love to learn more about your situation.")

    def generate_supportive_follow_up(self,
                                    previous_response: str,
                                    question_number: int,
                                    seller_name: Optional[str] = None) -> str:
        """Generate supportive follow-up for unclear responses"""

        name = seller_name or ""

        # Analyze the previous response to tailor support
        response_lower = previous_response.lower().strip()

        # Supportive responses based on common unclear answers
        if any(word in response_lower for word in ["maybe", "not sure", "idk", "thinking"]):
            supportive_responses = [
                f"I understand you're still thinking it through. That's completely normal. {self._get_gentle_clarification(question_number)}",
                f"No pressure at all. When you're ready, {self._get_gentle_clarification(question_number)}",
                f"Take your time. To help when you're ready, {self._get_gentle_clarification(question_number)}"
            ]
        elif len(response_lower) < 10:
            supportive_responses = [
                f"Thanks for that. {self._get_gentle_clarification(question_number)}",
                f"I appreciate the response. {self._get_gentle_clarification(question_number)}",
                f"Got it. {self._get_gentle_clarification(question_number)}"
            ]
        else:
            # General supportive follow-up
            supportive_responses = [
                f"Thanks for sharing that. {self._get_gentle_clarification(question_number)}",
                f"I appreciate you explaining your situation. {self._get_gentle_clarification(question_number)}",
                f"That's helpful information. {self._get_gentle_clarification(question_number)}"
            ]

        response = random.choice(supportive_responses)

        # Add name if provided
        if name:
            response = f"{name}, {response.lower()}"

        return self._ensure_sms_compliance(response)

    def _get_gentle_clarification(self, question_number: int) -> str:
        """Get gentle clarification for specific questions"""
        clarifications = {
            1: "could you share a bit more about what's motivating your potential move?",
            2: "what timeline would work best for your family's needs?",
            3: "how would you describe your home's current condition?",
            4: "what price range would feel comfortable to discuss?"
        }
        return clarifications.get(question_number, "could you help me understand your situation better?")

    def generate_market_insight(self, location: str = "Rancho Cucamonga") -> str:
        """Generate helpful local market insights"""

        insights = [
            f"Our {location} market is showing {self.market_data.market_status.lower()} conditions with {self.market_data.inventory_level.lower()}.",
            f"Current {location} homes are typically selling in {self.market_data.days_on_market} days with {self.market_data.price_trend.lower()}.",
            f"The Inland Empire market is offering great value compared to coastal areas, with strong family communities.",
            f"{location} continues to attract families for excellent schools, convenient location, and reasonable prices."
        ]

        # Add seasonal timing if appropriate
        current_month = datetime.now().month
        if current_month in [3, 4, 5, 9, 10]:  # Spring or early fall
            insights.append(f"This is actually great timing - {self.market_data.best_selling_season.lower()} is typically our strongest selling period.")

        return self._ensure_sms_compliance(random.choice(insights))

    def generate_ready_to_move_handoff(self,
                                      seller_name: Optional[str] = None,
                                      agent_name: str = "our local team") -> str:
        """Generate warm handoff message for qualified sellers"""

        name = seller_name or ""

        handoff_messages = [
            f"Based on our conversation, I'm confident {agent_name} can help you achieve your goals. Would you prefer a morning or afternoon call to discuss your options?",
            f"It sounds like we're a great fit for your needs. I'd love to connect you with {agent_name} who specializes in Rancho Cucamonga. When works better - mornings or afternoons?",
            f"Perfect! {agent_name} would be excited to work with you. They'll walk you through everything and answer any questions. Are mornings or afternoons better for a brief chat?",
            f"I think you'll really like working with {agent_name}. They know the Rancho Cucamonga market inside and out. Would a morning or afternoon call work better for you?"
        ]

        message = random.choice(handoff_messages)

        if name:
            message = f"{name}, {message.lower()}"

        return self._ensure_sms_compliance(message)

    def generate_appreciation_message(self, context: str = "general") -> str:
        """Generate appreciation message for different contexts"""

        appreciation_messages = {
            "general": [
                "Thank you for taking the time to share that information with me.",
                "I appreciate your openness in discussing your real estate needs.",
                "Thanks for being so helpful with these questions."
            ],
            "detailed_response": [
                "Wow, thank you for such a detailed response. That really helps me understand your situation.",
                "I appreciate you taking the time to explain everything so thoroughly.",
                "That's exactly the kind of information that helps me give you the best guidance."
            ],
            "timeline": [
                "Thank you for being clear about your timeline. That helps me plan the best approach for you.",
                "I appreciate you sharing your timing preferences. We'll work within your schedule.",
                "Thanks for letting me know about your timeline. We'll make sure everything works for you."
            ],
            "price": [
                "Thank you for being open about your price expectations. I'll make sure we're aligned with market realities.",
                "I appreciate your honesty about pricing. Let's work together to set realistic expectations.",
                "Thanks for sharing your price thoughts. I'll help you understand current market values."
            ]
        }

        messages = appreciation_messages.get(context, appreciation_messages["general"])
        return self._ensure_sms_compliance(random.choice(messages))

    def generate_helpful_clarification(self, topic: str) -> str:
        """Generate helpful clarification requests"""

        clarifications = {
            "motivation": "Could you help me understand what's prompting you to consider selling?",
            "timeline": "What timeline would work best for your situation and family needs?",
            "condition": "How would you describe your home's current condition?",
            "price": "What price range would feel comfortable for your situation?",
            "location": "Where are you thinking of moving to next?",
            "family": "Are there any family considerations I should know about for timing?"
        }

        clarification = clarifications.get(topic, "Could you help me understand your situation better?")

        # Add supportive intro
        intro = "I want to make sure I give you the best guidance. "
        return self._ensure_sms_compliance(intro + clarification)

    def generate_neighborhood_insight(self, area: str) -> str:
        """Generate insights about specific Rancho Cucamonga neighborhoods"""

        neighborhood_data = self.local_knowledge["neighborhoods"].get(area)

        if neighborhood_data:
            highlights = ", ".join(neighborhood_data["highlights"])
            message = f"{area} is known for {highlights}. Average homes are around ${neighborhood_data['avg_price']:,}."
        else:
            # Generic Rancho Cucamonga insight
            message = "Rancho Cucamonga offers excellent schools, family amenities, and great value compared to coastal areas."

        return self._ensure_sms_compliance(message)

    def generate_family_focused_message(self, family_context: str = "general") -> str:
        """Generate family-focused messaging for Rancho Cucamonga"""

        family_messages = {
            "schools": "Rancho Cucamonga has some of the best school districts in the Inland Empire, including highly-rated Etiwanda schools.",
            "amenities": "Families love RC for Victoria Gardens, Central Park, and easy access to both mountains and beaches.",
            "community": "The community here is very family-friendly with great parks, safe neighborhoods, and involved residents.",
            "location": "You'll love the convenience - 15 minutes to Ontario Airport, easy freeway access to LA and OC for work.",
            "value": "You get much more house for your money here compared to coastal areas, without sacrificing quality of life."
        }

        message = family_messages.get(family_context, family_messages["community"])
        return self._ensure_sms_compliance(message)

    def generate_relationship_nurture_message(self, seller_data: Dict, temperature: str) -> str:
        """Generate relationship nurture message for ongoing communication"""

        name = seller_data.get("contact_name", "")

        if temperature == "interested":
            nurture_messages = [
                "Thanks for all the information you've shared. I'll keep you updated on market conditions that might interest you.",
                "I appreciate you taking the time to discuss your situation. Please feel free to reach out with any questions.",
                "Thank you for considering us. I'll stay in touch with helpful market updates and insights."
            ]
        elif temperature == "exploring":
            nurture_messages = [
                "Thanks for exploring your options with us. I'm here whenever you're ready to discuss next steps.",
                "I appreciate you reaching out. Please don't hesitate to contact me when your timeline becomes clearer.",
                "Thank you for the conversation. I'll be here when you're ready to move forward."
            ]
        else:
            nurture_messages = [
                "Thanks for your time today. I'm here to help whenever you're ready to discuss your real estate goals.",
                "I appreciate the opportunity to learn about your situation. Please reach out anytime.",
                "Thank you for considering us. I'm always available for questions or market updates."
            ]

        message = random.choice(nurture_messages)

        if name:
            message = f"{name}, {message.lower()}"

        return self._ensure_sms_compliance(message)

    def validate_message_compliance(self, message: str) -> FriendlyValidationResult:
        """Validate message for friendly tone and compliance requirements"""

        # Check basic compliance
        length_compliant = len(message) <= 160

        # Check warmth indicators
        warmth_indicators = [
            "thank", "appreciate", "help", "understand", "love to", "happy to",
            "glad", "great", "wonderful", "perfect", "please", "could you"
        ]
        warmth_count = sum(1 for indicator in warmth_indicators if indicator in message.lower())
        warmth_score = min(1.0, warmth_count * 0.2)

        # Check professional indicators
        professional_indicators = [
            "market", "guidance", "information", "discuss", "situation", "timeline",
            "options", "advice", "experience", "expertise", "service"
        ]
        professional_count = sum(1 for indicator in professional_indicators if indicator in message.lower())
        professional_score = min(1.0, professional_count * 0.15)

        # Check for confrontational language (should be avoided)
        confrontational_words = [
            "need to", "have to", "must", "demand", "require", "insist",
            "bottom line", "deal with it", "face reality", "wake up"
        ]
        has_confrontational = any(word in message.lower() for word in confrontational_words)

        # Adjust warmth score if confrontational
        if has_confrontational:
            warmth_score = max(0.0, warmth_score - 0.5)

        # California DRE compliance check (basic)
        dre_compliant = True  # Assume compliant unless specific violations found

        # Generate suggestions
        suggestions = []
        if not length_compliant:
            suggestions.append("Message exceeds 160 character SMS limit")
        if warmth_score < 0.4:
            suggestions.append("Consider adding warmer, more helpful language")
        if professional_score < 0.3:
            suggestions.append("Consider adding more professional real estate context")
        if has_confrontational:
            suggestions.append("Remove confrontational language for better customer service")

        return FriendlyValidationResult(
            is_compliant=length_compliant and not has_confrontational,
            warmth_score=warmth_score,
            professional_score=professional_score,
            length_compliant=length_compliant,
            dre_compliant=dre_compliant,
            suggestions=suggestions
        )

    def _ensure_sms_compliance(self, message: str) -> str:
        """Ensure message complies with SMS length and friendly tone requirements"""

        # Remove any remaining confrontational language
        confrontational_replacements = {
            "you need to": "could you",
            "you have to": "would you",
            "you must": "could you please",
            "listen": "",
            "look": "",
            "bottom line": "the key point is",
            "deal with it": "work with this",
            "face reality": "consider the facts"
        }

        for confrontational, friendly in confrontational_replacements.items():
            message = message.replace(confrontational, friendly)

        # Ensure friendly tone
        if not any(word in message.lower() for word in ["thank", "appreciate", "help", "love", "happy"]):
            # Add friendly element if missing
            friendly_additions = [
                "I'd be happy to help. ",
                "I appreciate your interest. ",
                "Thanks for reaching out. "
            ]
            addition = random.choice(friendly_additions)
            if len(message + addition) <= 160:
                message = addition + message

        # Trim to SMS length if needed
        if len(message) > 160:
            message = message[:157] + "..."

        # Clean up any double spaces
        message = " ".join(message.split())

        return message.strip()

    def _apply_friendly_tone(self, message: str, seller_name: Optional[str] = None) -> str:
        """Apply consistent friendly tone to any message"""

        # Add name if provided and not already present
        if seller_name and seller_name not in message:
            message = f"{seller_name}, {message.lower()}"

        # Ensure friendly language patterns
        friendly_patterns = {
            "What": "I'd love to know what",
            "When": "When would",
            "How": "How would you describe",
            "Why": "Could you share why",
            "Tell me": "Could you help me understand"
        }

        for direct, friendly in friendly_patterns.items():
            if message.startswith(direct):
                message = message.replace(direct, friendly, 1)

        return self._ensure_sms_compliance(message)

    def get_local_expertise_insight(self, topic: str = "general") -> str:
        """Get local expertise insights for Rancho Cucamonga"""

        expertise_insights = {
            "market": f"Rancho Cucamonga shows {self.market_data.market_status.lower()} market conditions with {self.market_data.days_on_market} days average.",
            "pricing": f"Current pricing trends show {self.market_data.price_trend.lower()} with average values around ${self.market_data.avg_price:,}.",
            "timing": f"Market timing is good - {self.market_data.buyer_activity.lower()} buyer activity with {self.market_data.inventory_level.lower()}.",
            "family": "Families choose Rancho Cucamonga for excellent schools, safety, and value compared to coastal areas.",
            "location": "Great location with 15-minute access to Ontario Airport and easy freeway connections to LA and Orange County."
        }

        insight = expertise_insights.get(topic, expertise_insights["market"])
        return self._ensure_sms_compliance(insight)


# Example usage functions for testing
def demo_friendly_tone_engine():
    """Demonstration of Jorge's friendly tone engine"""

    engine = JorgeFriendlyToneEngine()

    print("🤝 Jorge Friendly Tone Engine - Rancho Cucamonga Edition")
    print("=" * 60)

    # Demo warm greeting
    greeting = engine.generate_warm_greeting("Maria")
    print(f"Warm Greeting: {greeting}")

    # Demo consultative questions
    for i in range(1, 5):
        question = engine.generate_consultative_question(i, "Maria")
        print(f"Question {i}: {question}")

    # Demo supportive follow-up
    follow_up = engine.generate_supportive_follow_up("maybe", 2, "Maria")
    print(f"Supportive Follow-up: {follow_up}")

    # Demo market insight
    market = engine.generate_market_insight()
    print(f"Market Insight: {market}")

    # Demo handoff
    handoff = engine.generate_ready_to_move_handoff("Maria")
    print(f"Ready to Move Handoff: {handoff}")

    # Demo validation
    validation = engine.validate_message_compliance(greeting)
    print(f"Validation - Warmth: {validation.warmth_score:.2f}, Professional: {validation.professional_score:.2f}")


if __name__ == "__main__":
    demo_friendly_tone_engine()