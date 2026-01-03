"""
Claude AI service for Real Estate qualification conversations.

Handles AI conversation logic for qualifying real estate leads including:
- Generating initial qualification messages
- Processing responses and extracting preferences
- Determining conversation flow and completion
- Maintaining conversation context

Uses Anthropic's Claude API with real estate-specific prompts.
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from anthropic import AsyncAnthropic
from core.config import settings
from core.prompts import SYSTEM_PROMPTS, QUALIFICATION_QUESTIONS


class ClaudeService:
    """
    Service for handling AI-powered real estate qualification conversations.

    Manages conversation flow, preference extraction, and qualification completion logic.
    """

    def __init__(self):
        """Initialize Claude service with API key and model configuration."""
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens

        # Conversation state tracking
        self.active_conversations: Dict[str, Dict] = {}

    async def generate_initial_message(self, contact_data: Dict[str, Any]) -> str:
        """
        Generate personalized initial qualification message.

        Args:
            contact_data: Contact information from GHL

        Returns:
            Initial message to send to contact
        """
        contact_name = contact_data.get("firstName", "there")
        contact_phone = contact_data.get("phone", "")
        contact_email = contact_data.get("email", "")

        # Build context about the contact
        context = f"""
        Contact Information:
        - Name: {contact_name}
        - Phone: {contact_phone}
        - Email: {contact_email}
        - Source: Real estate lead requiring qualification
        """

        system_prompt = SYSTEM_PROMPTS["initial_contact"].format(
            agent_name=settings.default_agent_name,
            agent_phone=settings.default_agent_phone,
            contact_name=contact_name
        )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate an initial qualification message for this contact: {context}"
                    }
                ]
            )

            initial_message = response.content[0].text

            # Initialize conversation tracking
            self.active_conversations[contact_data["id"]] = {
                "started_at": datetime.now(),
                "messages": [],
                "extracted_preferences": {},
                "current_question": "initial",
                "questions_asked": [],
                "responses_received": 0
            }

            return initial_message

        except Exception as e:
            print(f"Error generating initial message: {str(e)}")
            return f"Hi {contact_name}! I'm {settings.default_agent_name} from {settings.app_name}. I'd love to help you find your perfect home. What type of property are you looking for?"

    async def process_message(
        self,
        message_text: str,
        contact_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process incoming message and generate appropriate response.

        Args:
            message_text: Message from contact
            contact_data: Contact information
            conversation_history: Previous conversation messages

        Returns:
            Dict containing response message, qualification status, and extracted preferences
        """
        contact_id = contact_data["id"]

        # Get or initialize conversation state
        if contact_id not in self.active_conversations:
            self.active_conversations[contact_id] = {
                "started_at": datetime.now(),
                "messages": [],
                "extracted_preferences": {},
                "current_question": "budget",
                "questions_asked": [],
                "responses_received": 0
            }

        conversation_state = self.active_conversations[contact_id]

        # Add message to conversation
        conversation_state["messages"].append({
            "timestamp": datetime.now(),
            "sender": "contact",
            "text": message_text
        })
        conversation_state["responses_received"] += 1

        # Extract preferences from message
        extracted_prefs = await self.extract_preferences(message_text, conversation_state["extracted_preferences"])
        conversation_state["extracted_preferences"].update(extracted_prefs)

        # Determine next question/response
        next_question = self.get_next_question(conversation_state)

        # Generate response
        response_message = await self.generate_response(
            message_text=message_text,
            contact_data=contact_data,
            conversation_state=conversation_state,
            next_question=next_question
        )

        # Check if qualification is complete
        qualification_complete = self.is_qualification_complete(conversation_state)

        # Add AI response to conversation
        conversation_state["messages"].append({
            "timestamp": datetime.now(),
            "sender": "ai",
            "text": response_message
        })

        return {
            "response_message": response_message,
            "qualification_complete": qualification_complete,
            "extracted_preferences": conversation_state["extracted_preferences"],
            "context": {
                "extracted_preferences": conversation_state["extracted_preferences"],
                "conversation_history": conversation_state["messages"],
                "created_at": conversation_state["started_at"]
            },
            "conversation_state": conversation_state
        }

    async def extract_preferences(self, message: str, existing_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract real estate preferences from contact message.

        Args:
            message: Contact's message
            existing_prefs: Previously extracted preferences

        Returns:
            Dictionary of extracted preferences
        """
        extraction_prompt = SYSTEM_PROMPTS["preference_extraction"]

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.1,  # Lower temperature for extraction
                system=extraction_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Extract preferences from this message: "{message}"

                        Existing preferences: {json.dumps(existing_prefs)}

                        Return only new/updated preferences as JSON.
                        """
                    }
                ]
            )

            # Parse JSON response
            preferences_text = response.content[0].text

            # Try to extract JSON from response
            try:
                # Look for JSON content between braces
                json_match = re.search(r'\{.*\}', preferences_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

            # Fallback: manual extraction
            return self.extract_preferences_fallback(message)

        except Exception as e:
            print(f"Error extracting preferences: {str(e)}")
            return self.extract_preferences_fallback(message)

    def extract_preferences_fallback(self, message: str) -> Dict[str, Any]:
        """
        Fallback method for preference extraction using regex patterns.

        Args:
            message: Contact's message

        Returns:
            Dictionary of extracted preferences
        """
        preferences = {}
        message_lower = message.lower()

        # Budget extraction
        budget_patterns = [
            r'\$(\d+,?\d*)\s*k?\s*(?:-|to)\s*\$?(\d+,?\d*)\s*k?',
            r'budget.*?\$?(\d+,?\d*)k?',
            r'(\d+,?\d*)\s*(?:k|thousand)',
            r'\$(\d+,?\d*)'
        ]

        for pattern in budget_patterns:
            match = re.search(pattern, message_lower)
            if match:
                preferences["budget"] = match.group()
                break

        # Timeline extraction
        timeline_keywords = ["asap", "immediately", "next month", "this month", "6 months", "year", "timeline"]
        for keyword in timeline_keywords:
            if keyword in message_lower:
                preferences["timeline"] = message
                break

        # Location extraction
        location_patterns = [
            r'in\s+([a-zA-Z\s]+)',
            r'near\s+([a-zA-Z\s]+)',
            r'around\s+([a-zA-Z\s]+)'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                preferences["location"] = match.group(1).strip()
                break

        # Bedrooms/Bathrooms
        bedroom_match = re.search(r'(\d+)\s*(?:bed|br)', message_lower)
        if bedroom_match:
            preferences["bedrooms"] = int(bedroom_match.group(1))

        bathroom_match = re.search(r'(\d+)\s*(?:bath|ba)', message_lower)
        if bathroom_match:
            preferences["bathrooms"] = int(bathroom_match.group(1))

        # Property type
        property_types = ["house", "condo", "apartment", "townhouse", "single family"]
        for prop_type in property_types:
            if prop_type in message_lower:
                preferences["property_type"] = prop_type
                break

        return preferences

    def get_next_question(self, conversation_state: Dict[str, Any]) -> Optional[str]:
        """
        Determine next qualification question to ask.

        Args:
            conversation_state: Current conversation state

        Returns:
            Next question key or None if qualification complete
        """
        extracted_prefs = conversation_state["extracted_preferences"]
        questions_asked = conversation_state["questions_asked"]

        # Required information for qualification
        required_info = ["budget", "timeline", "location", "property_type"]

        for info_type in required_info:
            if info_type not in extracted_prefs and info_type not in questions_asked:
                conversation_state["questions_asked"].append(info_type)
                conversation_state["current_question"] = info_type
                return info_type

        # All basic info collected, ask follow-up if needed
        if len(conversation_state["messages"]) < 6:  # Continue for engagement
            return "additional_requirements"

        return None  # Qualification complete

    async def generate_response(
        self,
        message_text: str,
        contact_data: Dict[str, Any],
        conversation_state: Dict[str, Any],
        next_question: Optional[str]
    ) -> str:
        """
        Generate contextual response message.

        Args:
            message_text: Contact's message
            contact_data: Contact information
            conversation_state: Current conversation state
            next_question: Next question to ask (if any)

        Returns:
            Response message to send
        """
        contact_name = contact_data.get("firstName", "")
        extracted_prefs = conversation_state["extracted_preferences"]

        # Build context for response
        context = f"""
        Contact: {contact_name}
        Message: {message_text}
        Extracted Preferences: {json.dumps(extracted_prefs)}
        Conversation Length: {len(conversation_state["messages"])}
        Next Question Topic: {next_question}
        """

        # Choose appropriate system prompt
        if next_question:
            system_prompt = SYSTEM_PROMPTS["continuation"].format(
                agent_name=settings.default_agent_name,
                next_question=QUALIFICATION_QUESTIONS.get(next_question, "")
            )
        else:
            system_prompt = SYSTEM_PROMPTS["completion"].format(
                agent_name=settings.default_agent_name
            )

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate response for: {context}"
                    }
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Error generating response: {str(e)}")

            # Fallback responses
            if next_question:
                return QUALIFICATION_QUESTIONS.get(next_question, "Tell me more about what you're looking for.")
            else:
                return f"Thank you {contact_name}! I have everything I need. One of our agents will be in touch soon."

    def is_qualification_complete(self, conversation_state: Dict[str, Any]) -> bool:
        """
        Check if lead qualification is complete.

        Args:
            conversation_state: Current conversation state

        Returns:
            True if qualification is complete
        """
        extracted_prefs = conversation_state["extracted_preferences"]
        responses_received = conversation_state["responses_received"]

        # Minimum information required
        required_fields = ["budget", "timeline"]
        has_required_info = all(field in extracted_prefs for field in required_fields)

        # Minimum engagement threshold
        min_responses = 3

        # Complete if we have required info and minimum engagement
        return has_required_info and responses_received >= min_responses

    def cleanup_conversation(self, contact_id: str) -> None:
        """
        Clean up conversation state after completion.

        Args:
            contact_id: Contact ID to clean up
        """
        if contact_id in self.active_conversations:
            del self.active_conversations[contact_id]