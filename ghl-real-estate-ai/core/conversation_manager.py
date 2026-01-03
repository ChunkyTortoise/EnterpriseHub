"""
Conversation Manager for GHL Real Estate AI.

Orchestrates conversation flow by:
1. Managing conversation context and history
2. Generating AI responses using Claude + RAG
3. Extracting structured data from conversations
4. Calculating lead scores

This is the core brain of the system.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from core.llm_client import LLMClient
from core.rag_engine import RAGEngine
from services.lead_scorer import LeadScorer
from ghl_utils.config import settings
from ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIResponse:
    """AI-generated response with extracted data."""
    message: str
    extracted_data: Dict[str, Any]
    reasoning: str
    lead_score: int


class ConversationManager:
    """
    Manages conversation state and AI response generation.

    This class handles:
    - Context retrieval and storage
    - AI response generation via Claude + RAG
    - Data extraction from conversations
    - Lead scoring
    """

    def __init__(self):
        """Initialize conversation manager with dependencies."""
        # Initialize LLM client for Claude Sonnet 4.5
        self.llm_client = LLMClient(
            provider="claude",
            model=settings.claude_model
        )

        # Initialize RAG engine for knowledge base queries
        self.rag_engine = RAGEngine(
            collection_name=settings.chroma_collection_name,
            persist_directory=settings.chroma_persist_directory
        )

        # Initialize lead scorer
        self.lead_scorer = LeadScorer()

        # In-memory context store (replace with Redis/PostgreSQL for production)
        self.context_store: Dict[str, Dict[str, Any]] = {}

        logger.info("Conversation manager initialized")

    async def get_context(self, contact_id: str) -> Dict[str, Any]:
        """
        Retrieve conversation context for a contact.

        Args:
            contact_id: GHL contact ID

        Returns:
            Conversation context dict with history and extracted data
        """
        if contact_id in self.context_store:
            return self.context_store[contact_id]

        # Return default context for new conversations
        return {
            "contact_id": contact_id,
            "conversation_history": [],
            "extracted_preferences": {},
            "lead_score": 0,
            "conversation_stage": "initial_contact",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

    async def update_context(
        self,
        contact_id: str,
        user_message: str,
        ai_response: str,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update conversation context with new messages and data.

        Args:
            contact_id: GHL contact ID
            user_message: User's message
            ai_response: AI's response
            extracted_data: Newly extracted data from conversation
        """
        context = await self.get_context(contact_id)

        # Add messages to history
        context["conversation_history"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        context["conversation_history"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Merge extracted data (new data overrides old)
        if extracted_data:
            context["extracted_preferences"].update(extracted_data)

        # Trim conversation history to max length
        max_length = settings.max_conversation_history_length
        if len(context["conversation_history"]) > max_length:
            context["conversation_history"] = context["conversation_history"][-max_length:]

        # Update timestamp
        context["updated_at"] = datetime.utcnow().isoformat()

        # Store context
        self.context_store[contact_id] = context

        logger.info(
            f"Updated context for contact {contact_id}",
            extra={
                "contact_id": contact_id,
                "history_length": len(context["conversation_history"]),
                "preferences": context["extracted_preferences"]
            }
        )

    async def extract_data(
        self,
        user_message: str,
        current_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data from user message.

        Uses Claude to extract:
        - Budget (min/max)
        - Location preferences
        - Bedrooms/bathrooms
        - Timeline
        - Must-have features
        - Financing status

        Args:
            user_message: User's latest message
            current_preferences: Previously extracted preferences

        Returns:
            Dict of extracted preferences
        """
        extraction_prompt = f"""Analyze this real estate conversation and extract structured data.

Previous context: {json.dumps(current_preferences, indent=2)}
New message: {user_message}

Extract the following if mentioned (keep previous values if not updated):
- budget: integer (max budget in dollars)
- budget_min: integer (min budget if range specified)
- location: string or list of locations
- bedrooms: integer
- bathrooms: integer
- timeline: string (user's exact words about when they want to move)
- must_haves: list of strings (non-negotiable features)
- nice_to_haves: list of strings (preferred but optional features)
- financing: string ("pre-approved", "pre-qualified", "cash", "not started", etc.)
- current_situation: string ("renting", "selling current home", "first-time buyer", etc.)

Return ONLY valid JSON with extracted fields. If a field is not mentioned, omit it from the response.

Example output:
{{
  "budget": 400000,
  "location": ["Austin", "Round Rock"],
  "bedrooms": 3,
  "timeline": "June 2025",
  "must_haves": ["good schools", "pool"],
  "financing": "pre-approved"
}}
"""

        try:
            # Use Claude to extract data with low temperature for consistency
            response = await self.llm_client.agenerate(
                prompt=extraction_prompt,
                system_prompt="You are a data extraction specialist. Return only valid JSON.",
                temperature=0,
                max_tokens=500
            )

            extracted = json.loads(response.content)

            logger.info(
                "Extracted data from message",
                extra={"extracted": extracted}
            )

            return extracted

        except (json.JSONDecodeError, Exception) as e:
            logger.error(
                f"Failed to extract data: {str(e)}",
                extra={"error": str(e), "user_message": user_message}
            )
            return {}

    async def generate_response(
        self,
        user_message: str,
        contact_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AIResponse:
        """
        Generate AI response using Claude + RAG.

        Args:
            user_message: User's latest message
            contact_info: Contact information from GHL
            context: Conversation context

        Returns:
            AIResponse with message, extracted data, reasoning, and score
        """
        contact_name = contact_info.get("first_name", "there")

        # 1. Extract structured data from user message
        extracted_data = await self.extract_data(
            user_message,
            context.get("extracted_preferences", {})
        )

        # Merge with existing preferences
        merged_preferences = {**context.get("extracted_preferences", {}), **extracted_data}

        # 2. Retrieve relevant knowledge from RAG
        relevant_docs = await self.rag_engine.search(
            query=user_message,
            top_k=settings.rag_top_k_results
        )

        relevant_knowledge = "\n\n".join([
            f"[{doc.get('metadata', {}).get('category', 'info')}]: {doc.get('document', '')}"
            for doc in relevant_docs
        ]) if relevant_docs else "No specific knowledge base matches."

        # 3. Calculate current lead score
        lead_score = self.lead_scorer.calculate({
            "extracted_preferences": merged_preferences,
            "conversation_history": context.get("conversation_history", []),
            "created_at": context.get("created_at")
        })

        # 4. Build system prompt with context
        system_prompt = BASE_SYSTEM_PROMPT.format(
            contact_name=contact_name,
            conversation_stage=context.get("conversation_stage", "initial_contact"),
            lead_score=lead_score,
            extracted_preferences=json.dumps(merged_preferences, indent=2) if merged_preferences else "None yet",
            relevant_knowledge=relevant_knowledge
        )

        # 5. Generate response using Claude
        try:
            ai_response = await self.llm_client.agenerate(
                prompt=user_message,
                system_prompt=system_prompt,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )

            logger.info(
                "Generated AI response",
                extra={
                    "contact_name": contact_name,
                    "lead_score": lead_score,
                    "message_length": len(ai_response.content)
                }
            )

            return AIResponse(
                message=ai_response.content,
                extracted_data=extracted_data,
                reasoning=f"Lead score: {lead_score}/100",
                lead_score=lead_score
            )

        except Exception as e:
            logger.error(
                f"Failed to generate AI response: {str(e)}",
                extra={"error": str(e)}
            )
            # Fallback response
            return AIResponse(
                message=f"Hey {contact_name}! Thanks for reaching out. I'm having a quick technical issue—give me just a moment and I'll get back to you!",
                extracted_data={},
                reasoning="Error occurred",
                lead_score=0
            )

    async def calculate_lead_score(self, contact_id: str) -> int:
        """
        Calculate lead score for a contact.

        Args:
            contact_id: GHL contact ID

        Returns:
            Lead score (0-100)
        """
        context = await self.get_context(contact_id)
        return self.lead_scorer.calculate(context)
