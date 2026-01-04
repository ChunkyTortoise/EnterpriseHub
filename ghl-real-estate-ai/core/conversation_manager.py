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
from services.memory_service import MemoryService
from prompts.system_prompts import BASE_SYSTEM_PROMPT
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

        # Persistent memory service
        self.memory_service = MemoryService(storage_type="file")

        logger.info("Conversation manager initialized")

    async def get_context(self, contact_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve conversation context for a contact.

        Args:
            contact_id: GHL contact ID
            location_id: Optional location ID for isolation

        Returns:
            Conversation context dict with history and extracted data
        """
        return await self.memory_service.get_context(contact_id, location_id=location_id)

    async def update_context(
        self,
        contact_id: str,
        user_message: str,
        ai_response: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None
    ) -> None:
        """
        Update conversation context with new messages and data.

        Args:
            contact_id: GHL contact ID
            user_message: User's message
            ai_response: AI's response
            extracted_data: Newly extracted data from conversation
            location_id: Optional location ID for isolation
        """
        context = await self.get_context(contact_id, location_id=location_id)

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

        # Store context
        await self.memory_service.save_context(contact_id, context, location_id=location_id)

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
        current_preferences: Dict[str, Any],
        tenant_config: Optional[Dict[str, Any]] = None
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
        - Home condition (for sellers)
        - Pathway (wholesale vs listing)

        Args:
            user_message: User's latest message
            current_preferences: Previously extracted preferences
            tenant_config: Optional tenant-specific API keys

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
- home_condition: string ("excellent/move-in ready", "fair/needs work", "poor/fixer-upper")
- pathway: string ("wholesale" or "listing")

Return ONLY valid JSON with extracted fields. If a field is not mentioned, omit it from the response.

Example output:
{{
  "budget": 400000,
  "location": ["Austin", "Round Rock"],
  "bedrooms": 3,
  "timeline": "June 2025",
  "must_haves": ["good schools", "pool"],
  "financing": "pre-approved",
  "home_condition": "excellent",
  "pathway": "listing"
}}
"""

        try:
            # Use tenant-specific LLM client if config provided
            llm_client = self.llm_client
            if tenant_config and tenant_config.get("anthropic_api_key"):
                llm_client = LLMClient(
                    provider="claude",
                    model=settings.claude_model,
                    api_key=tenant_config["anthropic_api_key"]
                )

            # Use Claude to extract data with low temperature for consistency
            response = await llm_client.agenerate(
                prompt=extraction_prompt,
                system_prompt="You are a data extraction specialist. Return only valid JSON.",
                temperature=0,
                max_tokens=500
            )

            extracted = json.loads(response.content)

            # Manual override for pathway detection using keywords (Jorge's rules)
            pathway = self.detect_intent_pathway(user_message)
            if pathway != "unknown":
                extracted["pathway"] = pathway

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

    def detect_intent_pathway(self, message: str) -> str:
        """
        Detect if lead is interested in wholesale or listing based on keywords.
        
        Wholesale indicators:
        - "as-is", "fast sale", "cash offer", "quick", "need to sell fast"
        
        Listing indicators:  
        - "best price", "top dollar", "what's it worth", 
        - "how much can i get", "market value", "list it"
        
        Returns:
            "wholesale", "listing", or "unknown"
        """
        message_lower = message.lower()
        
        # More robust matching for common phrases
        wholesale_patterns = [
            "as-is", "as is", "fast sale", "cash offer", "quick", 
            "need to sell fast", "sell quickly", "don't want to fix"
        ]
        
        listing_patterns = [
            "best price", "top dollar", "what's it worth", "worth",
            "how much can i get", "market value", "list it", "mls"
        ]
        
        if any(pattern in message_lower for pattern in wholesale_patterns):
            return "wholesale"
        # Special check for "worth" to avoid too many false positives, but catch "what is my house worth"
        if any(pattern in message_lower for pattern in listing_patterns):
            # If it's just "worth", check if it's related to the house
            if "worth" in message_lower and not any(p in message_lower for p in ["best price", "top dollar", "market value"]):
                if any(k in message_lower for k in ["house", "home", "property", "place", "it"]):
                    return "listing"
                else:
                    return "unknown"
            return "listing"
            
        return "unknown"

    async def generate_response(
        self,
        user_message: str,
        contact_info: Dict[str, Any],
        context: Dict[str, Any],
        is_buyer: bool = True,
        tenant_config: Optional[Dict[str, Any]] = None,
        ghl_client: Optional[Any] = None
    ) -> AIResponse:
        """
        Generate AI response using Claude + RAG.

        Args:
            user_message: User's latest message
            contact_info: Contact information from GHL
            context: Conversation context
            is_buyer: Whether the contact is a buyer (True) or seller (False)
            tenant_config: Optional tenant-specific API keys
            ghl_client: Optional GHL client to fetch calendar slots

        Returns:
            AIResponse with message, extracted data, reasoning, and score
        """
        contact_name = contact_info.get("first_name", "there")

        # 0. Pre-extract data from first message to avoid redundancy
        # If this is the first interaction (no conversation history yet),
        # extract data BEFORE generating response to prevent asking about info already provided
        if not context.get("conversation_history"):
            pre_extracted = await self.extract_data(
                user_message,
                {},
                tenant_config=tenant_config
            )
            merged_preferences = {**context.get("extracted_preferences", {}), **pre_extracted}
            extracted_data = pre_extracted
        else:
            # 1. Extract structured data from user message
            extracted_data = await self.extract_data(
                user_message,
                context.get("extracted_preferences", {}),
                tenant_config=tenant_config
            )

            # Merge with existing preferences
            merged_preferences = {**context.get("extracted_preferences", {}), **extracted_data}

        # 2. Retrieve relevant knowledge from RAG (pathway-aware)
        location_id = tenant_config.get("location_id") if tenant_config else None

        # Enhance query based on detected pathway
        enhanced_query = user_message
        pathway = merged_preferences.get("pathway")
        home_condition = merged_preferences.get("home_condition", "").lower()

        if pathway == "wholesale" or "poor" in home_condition or "fixer" in home_condition:
            enhanced_query = f"{user_message} wholesale cash offer as-is quick sale"
        elif pathway == "listing":
            enhanced_query = f"{user_message} MLS listing top dollar market value"

        relevant_docs = self.rag_engine.search(
            query=enhanced_query,
            n_results=settings.rag_top_k_results,
            location_id=location_id
        )

        relevant_knowledge = "\n\n".join([
            f"[{doc.metadata.get('category', 'info')}]: {doc.text}"
            for doc in relevant_docs
        ]) if relevant_docs else "No specific knowledge base matches."

        # 3. Calculate current lead score
        lead_score = self.lead_scorer.calculate({
            "extracted_preferences": merged_preferences,
            "conversation_history": context.get("conversation_history", []),
            "created_at": context.get("created_at")
        })

        # 4. Fetch available calendar slots if lead is HOT (Jorge's requirement)
        available_slots_text = ""
        # Get calendar ID from tenant config or global settings
        calendar_id = (tenant_config.get("ghl_calendar_id") if tenant_config else None) or settings.ghl_calendar_id
        
        if lead_score >= 3 and ghl_client and calendar_id:
            try:
                from datetime import datetime, timedelta
                now = datetime.now()
                # Fetch slots for next 3 days for better urgency/directness
                start_date = now.strftime("%Y-%m-%d")
                end_date = (now + timedelta(days=3)).strftime("%Y-%m-%d")

                slots = await ghl_client.get_available_slots(
                    calendar_id=calendar_id,
                    start_date=start_date,
                    end_date=end_date
                )

                if slots:
                    # Professional, direct, and curious tone for appointment setting
                    available_slots_text = "I can get you on the phone with Jorge's team. Would one of these work?\n"
                    # Format first 2 slots for brevity on SMS
                    for slot in slots[:2]:
                        dt = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))
                        available_slots_text += f"- {dt.strftime('%a @ %I:%M %p')}\n"
                    available_slots_text += "Or should I just have them call you when they're free?"
            except Exception as e:
                logger.error(f"Failed to fetch calendar slots: {str(e)}")
        elif lead_score >= 3:
            # Fallback for hot leads when calendar not configured or slots unavailable
            available_slots_text = "I'll have Jorge call you directly. What time works best for you?"

        # 5. Build system prompt with context
        from prompts.system_prompts import build_system_prompt
        
        system_prompt = build_system_prompt(
            contact_name=contact_name,
            conversation_stage=context.get("conversation_stage", "qualifying"),
            lead_score=lead_score,
            extracted_preferences=merged_preferences,
            relevant_knowledge=relevant_knowledge,
            is_buyer=is_buyer,
            available_slots=available_slots_text
        )

        # 6. Generate response using Claude with history
        try:
            # Use tenant-specific LLM client if config provided
            llm_client = self.llm_client
            if tenant_config and tenant_config.get("anthropic_api_key"):
                llm_client = LLMClient(
                    provider="claude",
                    model=settings.claude_model,
                    api_key=tenant_config["anthropic_api_key"]
                )

            # Format history for Claude (only role and content)
            history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in context.get("conversation_history", [])
            ]

            ai_response = await llm_client.agenerate(
                prompt=user_message,
                system_prompt=system_prompt,
                history=history,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )

            # SMS 160-character hard limit enforcement
            if len(ai_response.content) > 160:
                ai_response.content = ai_response.content[:157] + "..."

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

    async def calculate_lead_score(self, contact_id: str, location_id: Optional[str] = None) -> int:
        """
        Calculate lead score for a contact.

        Args:
            contact_id: GHL contact ID
            location_id: Optional location ID for isolation

        Returns:
            Lead score (0-100)
        """
        context = await self.get_context(contact_id, location_id=location_id)
        return self.lead_scorer.calculate(context)
