"""
AI Response Generator for Real Estate Lead Qualification
Based on Jorge Sales' proven conversational patterns

Generates Claude AI responses that match successful agent communication style.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import anthropic


logger = logging.getLogger(__name__)


class RealEstateAIResponseGenerator:
    """
    Generates AI responses for real estate lead qualification.

    Trained on Jorge Sales' successful conversation patterns:
    - Professional but friendly tone
    - Direct and curious approach
    - SMS-optimized length (under 160 chars)
    - Natural qualification flow
    """

    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.response_cache = {}  # Cache for common responses

    async def generate_qualification_response(
        self,
        contact_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        question_type: str,
        lead_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response for lead qualification.

        Args:
            contact_data: Contact information from GHL
            conversation_history: Previous messages in conversation
            question_type: Type of qualification question to ask
            lead_context: Additional context about lead behavior

        Returns:
            Generated response string optimized for SMS
        """

        # Check cache first for common patterns
        cache_key = f"{question_type}_{hash(str(conversation_history[-3:]))}"
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            logger.debug(f"Using cached response for {question_type}")
            return self._personalize_cached_response(cached_response, contact_data)

        try:
            response = await self._generate_claude_response(
                contact_data=contact_data,
                conversation_history=conversation_history,
                question_type=question_type,
                lead_context=lead_context
            )

            # Cache successful responses
            self.response_cache[cache_key] = response
            return response

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            # Fallback to template responses
            return self._get_fallback_response(question_type, contact_data)

    async def _generate_claude_response(
        self,
        contact_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        question_type: str,
        lead_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate response using Claude API."""

        system_prompt = self._build_system_prompt()
        messages = self._build_conversation_context(
            conversation_history, question_type, contact_data, lead_context
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,  # Keep responses concise
            temperature=0.7,  # Balance creativity with consistency
            system=system_prompt,
            messages=messages
        )

        generated_text = response.content[0].text.strip()

        # Validate response meets criteria
        validated_response = self._validate_and_clean_response(generated_text)
        return validated_response

    def _build_system_prompt(self) -> str:
        """Build system prompt based on Jorge's communication style."""
        return """You are an AI assistant for Jorge Sales, a professional real estate agent in Austin, Texas.

Your communication style must match Jorge's proven approach:

TONE & PERSONALITY:
- Professional but friendly and approachable
- Direct and to-the-point (no fluff)
- Genuinely curious and interested in helping
- Confident without being pushy
- Never robotic or overly formal

MESSAGE FORMAT:
- SMS-optimized: ALWAYS under 160 characters
- Use natural, conversational language
- No corporate speak or jargon
- Start with a brief acknowledgment when appropriate

EXAMPLES OF JORGE'S ACTUAL MESSAGES:
- "Hey, are you actually still looking to sell or should we close your file?"
- "Hey [name] just checking in, is it still a priority of yours to buy or have you given up?"
- "Quick question - what's your budget range looking like?"
- "Got it. Which neighborhoods are you eyeing?"
- "When are you hoping to make a move?"

QUALIFICATION APPROACH:
- Ask ONE question at a time
- Build on previous answers naturally
- Show that you're listening and processing their responses
- Use their name occasionally but not excessively
- Create urgency without being aggressive

NEVER:
- Ask multiple questions in one message
- Use exclamation points excessively
- Sound like a chatbot or customer service script
- Be pushy about scheduling calls
- Ignore what they just told you"""

    def _build_conversation_context(
        self,
        conversation_history: List[Dict[str, str]],
        question_type: str,
        contact_data: Dict[str, Any],
        lead_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Build conversation context for Claude."""

        messages = []

        # Add recent conversation history (last 6 messages for context)
        recent_history = conversation_history[-6:] if conversation_history else []

        for msg in recent_history:
            role = "assistant" if msg.get("from") == "agent" else "user"
            messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

        # Add current qualification request
        qualification_context = self._get_question_context(question_type, contact_data, lead_context)

        messages.append({
            "role": "user",
            "content": f"Generate the next message to ask about: {qualification_context}. "
                      f"Remember: under 160 characters, natural conversation flow, Jorge's direct style."
        })

        return messages

    def _get_question_context(
        self,
        question_type: str,
        contact_data: Dict[str, Any],
        lead_context: Optional[Dict[str, Any]]
    ) -> str:
        """Get context for specific qualification question."""

        contact_name = contact_data.get("name", "").split()[0] if contact_data.get("name") else ""

        contexts = {
            "budget": f"their budget range for buying property. Be direct but not invasive.",

            "location": f"which neighborhoods or areas they're interested in. "
                       f"This is Austin market focused.",

            "bedrooms": f"how many bedrooms they need. This affects property type and price range.",

            "timeline": f"when they're hoping to buy or sell. This determines urgency and priority.",

            "preapproval": f"their financing situation - are they pre-approved? "
                          f"This is crucial for serious buyers.",

            "motivation": f"what's driving their decision to buy/sell right now. "
                         f"Understanding motivation helps with urgency and objections.",

            "seller_condition": f"the current condition of their home (for sellers). "
                               f"This affects pricing strategy and timeline.",

            "follow_up": f"general follow-up to keep the conversation moving. "
                        f"They may have gone quiet - re-engage naturally.",

            "closing": f"wrapping up the qualification and setting next steps. "
                     f"They've answered questions, time to transition to action."
        }

        context = contexts.get(question_type, "continuing the qualification conversation")

        # Add personalization if name available
        if contact_name:
            context = f"{context} (their name is {contact_name}, use naturally but don't overdo it)"

        # Add behavioral context if available
        if lead_context:
            engagement = lead_context.get("engagement_level", 0)
            if engagement > 0.7:
                context += " (they're highly engaged - keep momentum going)"
            elif engagement < 0.3:
                context += " (they seem less engaged - try to re-spark interest)"

        return context

    def _validate_and_clean_response(self, response: str) -> str:
        """Validate and clean generated response."""

        # Remove any quotes or formatting artifacts
        response = response.strip().strip('"').strip("'")

        # Ensure under 160 characters
        if len(response) > 160:
            # Truncate at last complete word before 160 chars
            truncated = response[:157]
            last_space = truncated.rfind(' ')
            if last_space > 100:  # Ensure we don't truncate too much
                response = truncated[:last_space] + "..."
            else:
                response = truncated + "..."

        # Remove any placeholder brackets that might remain
        response = response.replace("[name]", "").replace("[Name]", "")

        # Clean up double spaces
        response = ' '.join(response.split())

        return response

    def _get_fallback_response(self, question_type: str, contact_data: Dict[str, Any]) -> str:
        """Get fallback response when AI generation fails."""

        contact_name = contact_data.get("name", "").split()[0] if contact_data.get("name") else ""
        name_prefix = f"{contact_name}, " if contact_name else ""

        fallback_responses = {
            "budget": f"{name_prefix}quick question - what's your budget range looking like?",
            "location": f"{name_prefix}which neighborhoods are you eyeing?",
            "bedrooms": f"{name_prefix}how many bedrooms do you need?",
            "timeline": f"{name_prefix}when are you hoping to make a move?",
            "preapproval": f"{name_prefix}are you pre-approved or do you need a lender recommendation?",
            "motivation": f"{name_prefix}what's driving the decision right now?",
            "seller_condition": "What's the current condition of your home?",
            "follow_up": f"{name_prefix}still interested in finding the right property?",
            "closing": "Thanks for the info! A team member will reach out soon."
        }

        response = fallback_responses.get(question_type, "Thanks for the information!")

        # Ensure fallback also meets length requirements
        if len(response) > 160:
            response = response[:157] + "..."

        return response

    def _personalize_cached_response(self, cached_response: str, contact_data: Dict[str, Any]) -> str:
        """Add personalization to cached response."""

        contact_name = contact_data.get("name", "").split()[0] if contact_data.get("name") else ""

        # Only add name if response is short enough and doesn't already have personalization
        if contact_name and len(cached_response) < 140 and not any(
            indicator in cached_response.lower()
            for indicator in ["hey", "hi", contact_name.lower()]
        ):
            return f"{contact_name}, {cached_response.lower()}"

        return cached_response

    def generate_handoff_message(
        self,
        contact_data: Dict[str, Any],
        qualification_summary: Dict[str, Any]
    ) -> str:
        """Generate message for handing off to human agent."""

        contact_name = contact_data.get("name", "").split()[0] if contact_data.get("name") else ""
        name_part = f"{contact_name}, t" if contact_name else "T"

        score = qualification_summary.get("score", 0)

        if score >= 3:
            return f"{name_part}hanks for all the info! A team member will reach out shortly to help you. 🎉"
        else:
            return f"{name_part}hanks for the information! We'll be in touch soon with some options."

    async def generate_batch_responses(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate multiple responses efficiently."""

        tasks = [
            self.generate_qualification_response(**request)
            for request in requests
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in batch
        clean_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch response {i} failed: {response}")
                # Use fallback for failed responses
                fallback = self._get_fallback_response(
                    requests[i].get("question_type", "follow_up"),
                    requests[i].get("contact_data", {})
                )
                clean_responses.append(fallback)
            else:
                clean_responses.append(response)

        return clean_responses


# Response quality metrics for monitoring
class ResponseQualityTracker:
    """Track response quality metrics for optimization."""

    def __init__(self):
        self.response_metrics = []

    def track_response(
        self,
        response: str,
        question_type: str,
        response_time_ms: int,
        was_fallback: bool = False,
        lead_replied: bool = False,
        reply_time_seconds: Optional[int] = None
    ):
        """Track metrics for response optimization."""

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "response_length": len(response),
            "question_type": question_type,
            "response_time_ms": response_time_ms,
            "was_fallback": was_fallback,
            "lead_replied": lead_replied,
            "reply_time_seconds": reply_time_seconds,
            "character_efficiency": len(response) / 160  # How much of SMS limit used
        }

        self.response_metrics.append(metrics)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for optimization."""
        if not self.response_metrics:
            return {}

        total_responses = len(self.response_metrics)
        fallback_rate = sum(1 for m in self.response_metrics if m["was_fallback"]) / total_responses
        avg_length = sum(m["response_length"] for m in self.response_metrics) / total_responses
        reply_rate = sum(1 for m in self.response_metrics if m["lead_replied"]) / total_responses

        return {
            "total_responses": total_responses,
            "fallback_rate": round(fallback_rate, 3),
            "average_length": round(avg_length, 1),
            "reply_rate": round(reply_rate, 3),
            "avg_char_efficiency": round(avg_length / 160, 3)
        }


# Usage patterns from production system
"""
# Initialize response generator
generator = RealEstateAIResponseGenerator(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Generate qualification response
response = await generator.generate_qualification_response(
    contact_data={"name": "John Smith", "phone": "+1234567890"},
    conversation_history=[
        {"content": "Looking for a 3-bedroom house", "from": "contact"},
        {"content": "Great! What's your budget range?", "from": "agent"},
        {"content": "Around 500k", "from": "contact"}
    ],
    question_type="location",
    lead_context={"engagement_level": 0.8, "score": 2}
)

# Track response quality
tracker = ResponseQualityTracker()
tracker.track_response(
    response=response,
    question_type="location",
    response_time_ms=250,
    was_fallback=False
)
"""