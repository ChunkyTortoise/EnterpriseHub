"""
Intelligent Qualifier Service for Adaptive Lead Qualification.

Implements Jorge's 7 qualifying questions framework with Claude-powered
adaptive questioning that flows naturally in conversation.

Key Features:
- Analyzes qualification gaps using Jorge's methodology
- Prioritizes next questions based on conversation flow
- Uses Claude to craft natural, non-interrogative questions
- Adapts to lead's communication style and behavioral patterns
- Integrates with existing lead scoring system
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

try:
    from ghl_real_estate_ai.core.llm_client import LLMClient
    from ghl_real_estate_ai.ghl_utils.config import settings
    from ghl_real_estate_ai.ghl_utils.logger import get_logger
except ImportError:
    # Fallback for streamlit demo context
    from core.llm_client import LLMClient
    from ghl_utils.config import settings
    from ghl_utils.logger import get_logger

logger = get_logger(__name__)


class CommunicationStyle(Enum):
    """Lead communication style patterns."""
    FORMAL = "formal"
    CASUAL = "casual"
    DIRECT = "direct"
    DETAILED = "detailed"
    QUICK = "quick"


@dataclass
class QualificationGap:
    """Represents a missing qualification question."""
    question_key: str
    question_name: str
    priority: int
    context_relevance: float
    behavioral_readiness: float


@dataclass
class QualificationAnalysis:
    """Complete qualification analysis results."""
    answered_questions: List[str]
    missing_qualifiers: List[QualificationGap]
    next_priority_question: Optional[QualificationGap]
    jorge_methodology_score: int
    confidence_level: float
    communication_style: CommunicationStyle
    conversation_momentum: str  # "high", "medium", "low"


@dataclass
class AdaptiveQuestion:
    """Claude-generated adaptive question."""
    question: str
    targeting: str  # Which qualifier this targets
    style: str  # Communication style used
    reasoning: str  # Why this question was chosen
    backup_options: List[str]  # Alternative phrasings


class IntelligentQualifier:
    """
    Claude-powered lead qualification with adaptive follow-up questions.

    Implements Jorge's 7 qualifying questions with intelligent prioritization
    and natural conversation flow.
    """

    # Jorge's 7 qualifying questions framework
    JORGE_QUALIFICATION_FRAMEWORK = {
        "budget": {
            "name": "Budget/Price Range",
            "description": "Lead's budget or price range for property",
            "buyer_indicators": ["budget", "price", "afford", "financing", "down payment"],
            "seller_indicators": ["asking", "worth", "value", "price", "market"],
            "priority_base": 9  # Highest priority - most important
        },
        "location": {
            "name": "Location Preferences",
            "description": "Where the lead wants to buy/sell",
            "buyer_indicators": ["area", "neighborhood", "location", "city", "school district"],
            "seller_indicators": ["where", "location", "area", "neighborhood"],
            "priority_base": 8
        },
        "timeline": {
            "name": "Timeline for Buying/Selling",
            "description": "When the lead wants to move",
            "buyer_indicators": ["when", "timeline", "move", "soon", "ready"],
            "seller_indicators": ["when", "timeline", "move", "sell", "list"],
            "priority_base": 7
        },
        "requirements": {
            "name": "Property Requirements",
            "description": "Specific property needs (beds/baths/features)",
            "buyer_indicators": ["bedrooms", "bathrooms", "garage", "pool", "features"],
            "seller_indicators": ["bedrooms", "bathrooms", "square feet", "features"],
            "priority_base": 6
        },
        "financing": {
            "name": "Financing Status",
            "description": "Loan pre-approval or cash status",
            "buyer_indicators": ["pre-approved", "pre-qualified", "loan", "mortgage", "cash"],
            "seller_indicators": ["mortgage", "payoff", "equity", "owe"],
            "priority_base": 5
        },
        "motivation": {
            "name": "Motivation for Moving",
            "description": "Why buying/selling now",
            "buyer_indicators": ["why", "moving", "reason", "need", "family"],
            "seller_indicators": ["why", "selling", "reason", "moving", "relocating"],
            "priority_base": 4
        },
        "home_condition": {
            "name": "Home Condition",
            "description": "Condition of seller's current home",
            "buyer_indicators": [],  # Not applicable for buyers
            "seller_indicators": ["condition", "repairs", "updates", "renovations"],
            "priority_base": 3  # Sellers only
        }
    }

    def __init__(self, tenant_id: str, llm_client: Optional[LLMClient] = None):
        """
        Initialize intelligent qualifier.

        Args:
            tenant_id: Tenant identifier for multi-tenant support
            llm_client: Optional LLM client for testing
        """
        self.tenant_id = tenant_id
        self.llm_client = llm_client or LLMClient(
            provider="claude",
            model=settings.claude_model
        )

        logger.info(f"Intelligent qualifier initialized for tenant {tenant_id}")

    async def analyze_qualification_gaps(
        self,
        extracted_preferences: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        contact_info: Optional[Dict[str, Any]] = None,
        is_buyer: bool = True
    ) -> QualificationAnalysis:
        """
        Analyze which of Jorge's 7 qualifying questions are missing and
        prioritize next questions based on conversation flow and behavioral patterns.

        Args:
            extracted_preferences: Current extracted preferences
            conversation_history: Full conversation history
            contact_info: Contact information for context
            is_buyer: Whether this is a buyer or seller lead

        Returns:
            QualificationAnalysis with gaps and recommendations
        """
        # 1. Identify answered questions
        answered_questions = self._identify_answered_questions(
            extracted_preferences, is_buyer
        )

        # 2. Find missing qualifiers
        missing_qualifiers = self._identify_missing_qualifiers(
            answered_questions, is_buyer
        )

        # 3. Analyze conversation context for prioritization
        conversation_context = self._analyze_conversation_context(
            conversation_history, contact_info
        )

        # 4. Calculate priority scores for missing qualifiers
        prioritized_gaps = await self._prioritize_qualification_gaps(
            missing_qualifiers,
            conversation_context,
            extracted_preferences,
            is_buyer
        )

        # 5. Determine next priority question
        next_priority = prioritized_gaps[0] if prioritized_gaps else None

        # 6. Calculate confidence and momentum
        confidence_level = self._calculate_qualification_confidence(answered_questions)

        return QualificationAnalysis(
            answered_questions=answered_questions,
            missing_qualifiers=prioritized_gaps,
            next_priority_question=next_priority,
            jorge_methodology_score=len(answered_questions),
            confidence_level=confidence_level,
            communication_style=conversation_context["communication_style"],
            conversation_momentum=conversation_context["momentum"]
        )

    async def craft_next_question(
        self,
        qualification_analysis: QualificationAnalysis,
        conversation_context: Dict[str, Any],
        extracted_preferences: Dict[str, Any],
        is_buyer: bool = True
    ) -> AdaptiveQuestion:
        """
        Use Claude to craft the most appropriate qualifying question
        based on conversation flow and communication style.

        Args:
            qualification_analysis: Results from gap analysis
            conversation_context: Conversation flow context
            extracted_preferences: Current extracted data
            is_buyer: Whether this is a buyer or seller

        Returns:
            AdaptiveQuestion with natural phrasing
        """
        if not qualification_analysis.next_priority_question:
            # All questions answered or no clear priority
            return AdaptiveQuestion(
                question="Is there anything else I should know to help find you the perfect property?"
                         if is_buyer else "What other details would help me provide the best market analysis?",
                targeting="general_follow_up",
                style="conversational",
                reasoning="All major qualifiers covered, gathering additional context",
                backup_options=[]
            )

        priority_gap = qualification_analysis.next_priority_question

        # Build Claude prompt for natural question crafting
        claude_prompt = await self._build_question_crafting_prompt(
            priority_gap,
            qualification_analysis,
            conversation_context,
            extracted_preferences,
            is_buyer
        )

        try:
            # Use Claude to craft natural question
            response = await self.llm_client.agenerate(
                prompt=claude_prompt,
                system_prompt=self._get_question_crafting_system_prompt(),
                temperature=0.7,  # Allow some creativity for natural flow
                max_tokens=300
            )

            # Parse Claude's response
            question_data = self._parse_claude_question_response(response.content)

            return AdaptiveQuestion(
                question=question_data.get("question", "").strip(),
                targeting=priority_gap.question_key,
                style=qualification_analysis.communication_style.value,
                reasoning=question_data.get("reasoning", ""),
                backup_options=question_data.get("alternatives", [])
            )

        except Exception as e:
            logger.error(f"Failed to craft adaptive question: {str(e)}")

            # Fallback to template-based question
            return self._get_fallback_question(
                priority_gap,
                qualification_analysis.communication_style,
                is_buyer
            )

    async def should_ask_qualifying_question(
        self,
        conversation_context: Dict[str, Any],
        qualification_analysis: QualificationAnalysis,
        recent_messages: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Determine if now is a good time to ask a qualifying question
        based on conversation flow and momentum.

        Args:
            conversation_context: Current conversation state
            qualification_analysis: Qualification gap analysis
            recent_messages: Last 3-5 messages for flow analysis

        Returns:
            Tuple of (should_ask, reasoning)
        """
        # Don't overwhelm with questions if they just answered one
        if len(recent_messages) >= 2:
            last_message = recent_messages[-2].get("content", "").lower()
            if any(indicator in last_message for indicator in
                   ["$", "budget", "location", "when", "bed", "bath", "loan"]):
                return False, "Just provided qualifying info, let them continue"

        # Check conversation momentum
        momentum = qualification_analysis.conversation_momentum

        if momentum == "low":
            return False, "Low engagement, focus on re-engaging first"

        # Good time to ask if momentum is good and we have clear gaps
        if momentum in ["medium", "high"] and qualification_analysis.missing_qualifiers:
            return True, f"Good momentum ({momentum}), can naturally ask for {qualification_analysis.next_priority_question.question_name}"

        return False, "No clear qualification gaps or poor timing"

    def _identify_answered_questions(
        self,
        extracted_preferences: Dict[str, Any],
        is_buyer: bool
    ) -> List[str]:
        """Identify which qualifying questions have been answered."""
        answered = []

        # Budget
        if extracted_preferences.get("budget") or extracted_preferences.get("budget_min"):
            answered.append("budget")

        # Location
        if extracted_preferences.get("location"):
            answered.append("location")

        # Timeline
        if extracted_preferences.get("timeline"):
            answered.append("timeline")

        # Requirements (beds/baths/features)
        if (extracted_preferences.get("bedrooms") or
            extracted_preferences.get("bathrooms") or
            extracted_preferences.get("must_haves")):
            answered.append("requirements")

        # Financing
        if extracted_preferences.get("financing"):
            answered.append("financing")

        # Motivation
        if extracted_preferences.get("motivation"):
            answered.append("motivation")

        # Home condition (sellers only)
        if not is_buyer and extracted_preferences.get("home_condition"):
            answered.append("home_condition")

        return answered

    def _identify_missing_qualifiers(
        self,
        answered_questions: List[str],
        is_buyer: bool
    ) -> List[QualificationGap]:
        """Identify missing qualification questions as gaps."""
        missing_gaps = []

        for key, details in self.JORGE_QUALIFICATION_FRAMEWORK.items():
            # Skip home_condition for buyers
            if is_buyer and key == "home_condition":
                continue

            if key not in answered_questions:
                missing_gaps.append(QualificationGap(
                    question_key=key,
                    question_name=details["name"],
                    priority=details["priority_base"],
                    context_relevance=0.0,  # Will be calculated later
                    behavioral_readiness=0.0  # Will be calculated later
                ))

        return missing_gaps

    def _analyze_conversation_context(
        self,
        conversation_history: List[Dict[str, Any]],
        contact_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze conversation for style and momentum patterns."""
        if not conversation_history:
            return {
                "communication_style": CommunicationStyle.CASUAL,
                "momentum": "medium",
                "message_length_avg": 0,
                "response_pattern": "unknown",
                "engagement_level": "medium"
            }

        # Analyze message patterns
        user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]

        if not user_messages:
            return {
                "communication_style": CommunicationStyle.CASUAL,
                "momentum": "low",
                "message_length_avg": 0,
                "response_pattern": "silent",
                "engagement_level": "low"
            }

        # Calculate average message length
        avg_length = sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)

        # Detect communication style
        style = self._detect_communication_style(user_messages)

        # Calculate momentum based on recent activity
        momentum = self._calculate_conversation_momentum(conversation_history)

        # Determine engagement level
        engagement = self._assess_engagement_level(user_messages)

        return {
            "communication_style": style,
            "momentum": momentum,
            "message_length_avg": avg_length,
            "response_pattern": "active" if len(user_messages) >= 2 else "limited",
            "engagement_level": engagement,
            "total_exchanges": len(user_messages)
        }

    def _detect_communication_style(
        self,
        user_messages: List[Dict[str, Any]]
    ) -> CommunicationStyle:
        """Detect lead's communication style from message patterns."""
        if not user_messages:
            return CommunicationStyle.CASUAL

        # Combine all user messages for analysis
        combined_text = " ".join(msg.get("content", "") for msg in user_messages).lower()

        # Count style indicators
        formal_indicators = len(re.findall(r'\b(please|thank you|appreciate|would like|could you)\b', combined_text))
        casual_indicators = len(re.findall(r'\b(yeah|ok|cool|sure|awesome|great)\b', combined_text))
        direct_indicators = len(re.findall(r'\b(need|want|show me|send me|get me)\b', combined_text))

        # Calculate average message length
        avg_length = sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)

        # Determine style based on patterns
        if formal_indicators > casual_indicators and formal_indicators > 1:
            return CommunicationStyle.FORMAL
        elif direct_indicators > 2 or avg_length < 20:
            return CommunicationStyle.DIRECT if avg_length < 20 else CommunicationStyle.QUICK
        elif avg_length > 60:
            return CommunicationStyle.DETAILED
        else:
            return CommunicationStyle.CASUAL

    def _calculate_conversation_momentum(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Calculate conversation momentum based on recent activity."""
        if len(conversation_history) < 2:
            return "low"

        # Check recent message frequency and engagement
        recent_messages = conversation_history[-4:]  # Last 4 messages
        user_responses = [msg for msg in recent_messages if msg.get("role") == "user"]

        if len(user_responses) >= 2:
            # Good back-and-forth
            return "high"
        elif len(user_responses) == 1 and len(recent_messages) >= 2:
            # Some engagement
            return "medium"
        else:
            return "low"

    def _assess_engagement_level(
        self,
        user_messages: List[Dict[str, Any]]
    ) -> str:
        """Assess overall engagement level of the lead."""
        if not user_messages:
            return "low"

        # Look for engagement signals
        total_content = " ".join(msg.get("content", "") for msg in user_messages).lower()

        # Positive engagement indicators
        positive_signals = len(re.findall(r'\b(yes|interested|love|perfect|great|sounds good)\b', total_content))
        question_signals = total_content.count("?")
        detail_sharing = len(re.findall(r'\b(\d+|bedroom|bathroom|\$|location|area)\b', total_content))

        engagement_score = positive_signals + question_signals + (detail_sharing * 0.5)

        if engagement_score >= 3:
            return "high"
        elif engagement_score >= 1:
            return "medium"
        else:
            return "low"

    async def _prioritize_qualification_gaps(
        self,
        missing_qualifiers: List[QualificationGap],
        conversation_context: Dict[str, Any],
        extracted_preferences: Dict[str, Any],
        is_buyer: bool
    ) -> List[QualificationGap]:
        """
        Use contextual analysis to prioritize which missing qualifier
        to ask about next.
        """
        if not missing_qualifiers:
            return []

        # Calculate context relevance and behavioral readiness for each gap
        for gap in missing_qualifiers:
            gap.context_relevance = self._calculate_context_relevance(
                gap, conversation_context, extracted_preferences, is_buyer
            )
            gap.behavioral_readiness = self._calculate_behavioral_readiness(
                gap, conversation_context
            )

            # Adjust priority based on context
            gap.priority = (
                gap.priority +
                (gap.context_relevance * 3) +
                (gap.behavioral_readiness * 2)
            )

        # Sort by adjusted priority (highest first)
        return sorted(missing_qualifiers, key=lambda x: x.priority, reverse=True)

    def _calculate_context_relevance(
        self,
        gap: QualificationGap,
        conversation_context: Dict[str, Any],
        extracted_preferences: Dict[str, Any],
        is_buyer: bool
    ) -> float:
        """Calculate how relevant this gap is to the current conversation context."""
        framework = self.JORGE_QUALIFICATION_FRAMEWORK[gap.question_key]

        # Get relevant indicators based on buyer/seller
        indicators = framework["buyer_indicators"] if is_buyer else framework["seller_indicators"]

        if not indicators:
            return 0.0

        # Check if conversation has mentioned related topics
        conversation_text = " ".join(
            str(val) for val in extracted_preferences.values() if val
        ).lower()

        relevance_score = sum(
            1 for indicator in indicators
            if indicator in conversation_text
        ) / len(indicators)

        return min(relevance_score, 1.0)

    def _calculate_behavioral_readiness(
        self,
        gap: QualificationGap,
        conversation_context: Dict[str, Any]
    ) -> float:
        """Calculate behavioral readiness to answer this type of question."""
        # Higher readiness for engaged, detailed communicators
        engagement_level = conversation_context["engagement_level"]
        communication_style = conversation_context["communication_style"]

        readiness_score = 0.5  # Base score

        if engagement_level == "high":
            readiness_score += 0.3
        elif engagement_level == "medium":
            readiness_score += 0.1

        if communication_style in [CommunicationStyle.DETAILED, CommunicationStyle.FORMAL]:
            readiness_score += 0.2

        return min(readiness_score, 1.0)

    def _calculate_qualification_confidence(self, answered_questions: List[str]) -> float:
        """Calculate confidence level based on answered questions."""
        total_possible = 7  # Jorge's 7 questions
        answered_count = len(answered_questions)

        # Confidence increases exponentially with more answers
        confidence = (answered_count / total_possible) ** 0.7
        return min(confidence, 1.0)

    async def _build_question_crafting_prompt(
        self,
        priority_gap: QualificationGap,
        qualification_analysis: QualificationAnalysis,
        conversation_context: Dict[str, Any],
        extracted_preferences: Dict[str, Any],
        is_buyer: bool
    ) -> str:
        """Build Claude prompt for crafting natural qualifying questions."""
        # Get conversation summary
        answered_summary = " | ".join(qualification_analysis.answered_questions) if qualification_analysis.answered_questions else "None yet"

        # Get style guidance
        style_guidance = self._get_style_guidance(qualification_analysis.communication_style)

        # Get context about what we know
        known_context = self._summarize_known_context(extracted_preferences, is_buyer)

        return f"""You are crafting the next qualifying question for a real estate lead.

CONTEXT:
- Lead Type: {"Buyer" if is_buyer else "Seller"}
- Communication Style: {qualification_analysis.communication_style.value}
- Conversation Momentum: {qualification_analysis.conversation_momentum}
- Questions Already Answered: {answered_summary}
- What We Know: {known_context}

TARGET QUALIFIER: {priority_gap.question_name}
Description: {self.JORGE_QUALIFICATION_FRAMEWORK[priority_gap.question_key]['description']}

STYLE GUIDANCE: {style_guidance}

REQUIREMENTS:
- Ask about {priority_gap.question_name} naturally
- Don't sound like a form or interrogation
- Flow naturally from the conversation
- Keep it under 160 characters (SMS limit)
- Match their communication style
- Be conversational and helpful

EXAMPLES OF GOOD QUESTIONS:
Budget: "What price range works best for your family?"
Location: "Which neighborhoods are you most interested in?"
Timeline: "When are you hoping to make a move?"

Return ONLY a JSON response with:
{{
  "question": "Your natural question here",
  "reasoning": "Why this phrasing works for this lead",
  "alternatives": ["Alternative phrasing 1", "Alternative phrasing 2"]
}}"""

    def _get_style_guidance(self, communication_style: CommunicationStyle) -> str:
        """Get style-specific guidance for question crafting."""
        style_guides = {
            CommunicationStyle.FORMAL: "Use polite, professional language with 'Would you mind sharing...' or 'Could you help me understand...'",
            CommunicationStyle.CASUAL: "Use friendly, relaxed tone with 'What's...' or 'How about...'",
            CommunicationStyle.DIRECT: "Be straightforward and concise. Get straight to the point.",
            CommunicationStyle.DETAILED: "They like comprehensive info, so you can be slightly more detailed in your ask",
            CommunicationStyle.QUICK: "Keep it very brief and simple. One quick question only."
        }
        return style_guides.get(communication_style, "Use a natural, conversational tone")

    def _summarize_known_context(
        self,
        extracted_preferences: Dict[str, Any],
        is_buyer: bool
    ) -> str:
        """Summarize what we already know about the lead."""
        known_items = []

        if extracted_preferences.get("budget"):
            known_items.append(f"Budget: {extracted_preferences['budget']}")
        if extracted_preferences.get("location"):
            known_items.append(f"Location: {extracted_preferences['location']}")
        if extracted_preferences.get("timeline"):
            known_items.append(f"Timeline: {extracted_preferences['timeline']}")
        if extracted_preferences.get("bedrooms") or extracted_preferences.get("bathrooms"):
            beds = extracted_preferences.get("bedrooms", "")
            baths = extracted_preferences.get("bathrooms", "")
            known_items.append(f"Size: {beds}bed/{baths}bath")

        return "; ".join(known_items) if known_items else "Basic contact info only"

    def _get_question_crafting_system_prompt(self) -> str:
        """System prompt for Claude when crafting questions."""
        return """You are an expert real estate conversation specialist. Your job is to craft qualifying questions that feel natural and conversational, never like an interrogation or form-filling.

Key principles:
1. Questions should flow naturally from the conversation
2. Match the lead's communication style exactly
3. Be helpful, not pushy
4. Keep it under 160 characters for SMS
5. Focus on ONE qualifier at a time
6. Make it sound like you're trying to help them, not collect data

Return only valid JSON as requested."""

    def _parse_claude_question_response(self, response_content: str) -> Dict[str, Any]:
        """Parse Claude's question crafting response."""
        try:
            # Try to extract JSON from response
            json_start = response_content.find("{")
            json_end = response_content.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                return json.loads(json_str)

            # If no JSON found, try to extract just the question
            lines = response_content.strip().split("\n")
            question = lines[0].strip()

            return {
                "question": question,
                "reasoning": "Parsed from plain text response",
                "alternatives": []
            }

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse Claude question response: {str(e)}")
            return {
                "question": "What else would help me find you the perfect property?",
                "reasoning": "Fallback due to parsing error",
                "alternatives": []
            }

    def _get_fallback_question(
        self,
        priority_gap: QualificationGap,
        communication_style: CommunicationStyle,
        is_buyer: bool
    ) -> AdaptiveQuestion:
        """Get fallback template question when Claude fails."""

        # Template questions by qualifier and style
        fallback_templates = {
            "budget": {
                CommunicationStyle.FORMAL: "Could you share what budget range you're comfortable with?",
                CommunicationStyle.CASUAL: "What's your budget looking like?",
                CommunicationStyle.DIRECT: "What's your budget?",
                CommunicationStyle.DETAILED: "What price range works best for your situation?",
                CommunicationStyle.QUICK: "Budget range?"
            },
            "location": {
                CommunicationStyle.FORMAL: "Which areas are you most interested in?",
                CommunicationStyle.CASUAL: "Where are you looking to buy?",
                CommunicationStyle.DIRECT: "Preferred location?",
                CommunicationStyle.DETAILED: "What neighborhoods or areas interest you most?",
                CommunicationStyle.QUICK: "Which area?"
            },
            "timeline": {
                CommunicationStyle.FORMAL: "When would you like to make a move?",
                CommunicationStyle.CASUAL: "What's your timeline like?",
                CommunicationStyle.DIRECT: "When do you want to move?",
                CommunicationStyle.DETAILED: "When are you hoping to complete this move?",
                CommunicationStyle.QUICK: "Timeline?"
            },
            "requirements": {
                CommunicationStyle.FORMAL: "What are your must-have features?",
                CommunicationStyle.CASUAL: "How many bedrooms and baths?",
                CommunicationStyle.DIRECT: "Beds and baths needed?",
                CommunicationStyle.DETAILED: "What are your space requirements and must-have features?",
                CommunicationStyle.QUICK: "Size needed?"
            },
            "financing": {
                CommunicationStyle.FORMAL: "How is your financing situation looking?",
                CommunicationStyle.CASUAL: "Are you pre-approved for a loan?",
                CommunicationStyle.DIRECT: "Financing ready?",
                CommunicationStyle.DETAILED: "What's your financing status - pre-approved, cash, or still exploring?",
                CommunicationStyle.QUICK: "Pre-approved?"
            },
            "motivation": {
                CommunicationStyle.FORMAL: "What's motivating this move for you?",
                CommunicationStyle.CASUAL: "Why are you looking to move?",
                CommunicationStyle.DIRECT: "Why moving?",
                CommunicationStyle.DETAILED: "What's driving this decision to buy/sell right now?",
                CommunicationStyle.QUICK: "Why now?"
            },
            "home_condition": {
                CommunicationStyle.FORMAL: "How would you describe your home's condition?",
                CommunicationStyle.CASUAL: "What shape is your house in?",
                CommunicationStyle.DIRECT: "Home condition?",
                CommunicationStyle.DETAILED: "What's the current condition of your home - move-in ready or needs work?",
                CommunicationStyle.QUICK: "Condition?"
            }
        }

        # Get the appropriate template
        question_templates = fallback_templates.get(priority_gap.question_key, {})
        question = question_templates.get(
            communication_style,
            f"Could you tell me about your {priority_gap.question_name.lower()}?"
        )

        return AdaptiveQuestion(
            question=question,
            targeting=priority_gap.question_key,
            style=communication_style.value,
            reasoning="Fallback template question",
            backup_options=list(question_templates.values())[:2]
        )

    async def get_qualification_summary(
        self,
        extracted_preferences: Dict[str, Any],
        is_buyer: bool = True
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary of qualification status.

        Args:
            extracted_preferences: Current extracted preferences
            is_buyer: Whether this is a buyer lead

        Returns:
            Summary with progress, gaps, and recommendations
        """
        answered_questions = self._identify_answered_questions(extracted_preferences, is_buyer)
        missing_qualifiers = self._identify_missing_qualifiers(answered_questions, is_buyer)

        total_questions = 7 if not is_buyer else 6  # Sellers have home_condition
        progress_percentage = (len(answered_questions) / total_questions) * 100

        # Jorge's classification
        jorge_score = len(answered_questions)
        if jorge_score >= 3:
            classification = "Hot Lead"
            urgency = "Immediate action required"
        elif jorge_score >= 2:
            classification = "Warm Lead"
            urgency = "Follow up within 24 hours"
        else:
            classification = "Cold Lead"
            urgency = "Add to nurture campaign"

        return {
            "qualification_status": {
                "answered_questions": len(answered_questions),
                "total_questions": total_questions,
                "progress_percentage": round(progress_percentage, 1),
                "jorge_score": jorge_score,
                "classification": classification,
                "urgency": urgency
            },
            "answered_details": answered_questions,
            "missing_qualifiers": [gap.question_name for gap in missing_qualifiers],
            "next_priority": missing_qualifiers[0].question_name if missing_qualifiers else None,
            "readiness_for_showing": jorge_score >= 3,
            "recommendations": self._get_qualification_recommendations(jorge_score, missing_qualifiers)
        }

    def _get_qualification_recommendations(
        self,
        jorge_score: int,
        missing_qualifiers: List[QualificationGap]
    ) -> List[str]:
        """Get actionable recommendations based on qualification status."""
        recommendations = []

        if jorge_score >= 3:
            recommendations.extend([
                "Schedule property showing immediately",
                "Notify agent via SMS for direct contact",
                "Send pre-approval checklist if financing not confirmed",
                "Prepare market analysis and comps"
            ])
        elif jorge_score >= 2:
            recommendations.extend([
                "Focus on gathering 1-2 more key qualifiers",
                "Send follow-up within 24 hours",
                "Provide market updates to maintain engagement"
            ])
        else:
            recommendations.extend([
                "Build rapport before additional qualifying",
                "Provide educational content to increase engagement",
                "Focus on 1 qualifier at a time to avoid overwhelm"
            ])

        # Add specific recommendations based on missing qualifiers
        if missing_qualifiers:
            next_gap = missing_qualifiers[0]
            if next_gap.question_key == "budget":
                recommendations.append("Budget is critical - prioritize this qualifier")
            elif next_gap.question_key == "timeline":
                recommendations.append("Timeline helps prioritize urgency level")

        return recommendations