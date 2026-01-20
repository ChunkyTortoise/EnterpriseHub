"""
Conversation Manager for Customer Intelligence Platform.

Orchestrates conversation flow by:
1. Managing conversation context and history
2. Generating AI responses using LLM + RAG
3. Extracting structured data from conversations
4. Calculating customer engagement scores

This is the core brain of the system.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

from .ai_client import AIClient
from .knowledge_engine import KnowledgeEngine
from .redis_conversation_context import RedisConversationContext
from .event_bus import EventBus, EventType, create_event_bus
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIResponse:
    """AI-generated response with extracted data."""
    message: str
    extracted_data: Dict[str, Any]
    reasoning: str
    engagement_score: int
    confidence_score: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class ConversationManager:
    """
    Manages conversation state and AI response generation.

    This class handles:
    - Context retrieval and storage
    - AI response generation via LLM + RAG
    - Data extraction from conversations
    - Customer engagement scoring
    """

    def __init__(self, collection_name: str = "business_knowledge", tenant_id: Optional[str] = None):
        """Initialize conversation manager with dependencies."""
        self.tenant_id = tenant_id or "default"

        # Initialize AI client for Claude
        self.ai_client = AIClient(
            provider=os.getenv("DEFAULT_LLM_PROVIDER", "claude"),
            model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        )

        # Initialize knowledge engine for RAG queries
        self.knowledge_engine = KnowledgeEngine(
            collection_name=collection_name,
            persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY", "./.chroma_db")
        )

        # Initialize Redis-backed context storage (with fallback to in-memory)
        try:
            self.context_manager = RedisConversationContext(
                tenant_id=self.tenant_id,
                max_history_length=int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
            )
            logger.info("Conversation manager initialized with Redis context storage")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis context storage: {e}")
            logger.info("Falling back to in-memory context storage")
            # Fallback to in-memory storage for development
            self._contexts = {}
            self.context_manager = None

        # Initialize event bus for real-time analytics and integration
        try:
            asyncio.create_task(self._init_event_bus())
            logger.info("Event bus initialization scheduled")
        except Exception as e:
            logger.warning(f"Failed to initialize event bus: {e}")
            self.event_bus = None

        logger.info("Conversation manager initialized")

    async def _init_event_bus(self):
        """Initialize event bus asynchronously."""
        try:
            self.event_bus = await create_event_bus(
                tenant_id=self.tenant_id,
                service_name="conversation_manager"
            )
            logger.info("Event bus initialized for conversation manager")
        except Exception as e:
            logger.error(f"Failed to initialize event bus: {e}")
            self.event_bus = None

    async def get_context(self, customer_id: str, department_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve conversation context for a customer.

        Args:
            customer_id: Unique customer identifier
            department_id: Optional department ID for context isolation

        Returns:
            Conversation context dict with history and extracted data
        """
        # Use Redis context manager if available, otherwise fallback to in-memory
        if self.context_manager:
            return await self.context_manager.get_context(customer_id, department_id)
        else:
            # Fallback to in-memory storage for development
            context_key = f"{department_id}:{customer_id}" if department_id else customer_id

            if context_key not in self._contexts:
                self._contexts[context_key] = {
                    "customer_id": customer_id,
                    "department_id": department_id,
                    "conversation_history": [],
                    "extracted_preferences": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "last_interaction_at": None,
                    "engagement_score": 0
                }

            context = self._contexts[context_key]

            # Check for session gap (Smart Resume)
            last_interaction = context.get("last_interaction_at")
            if last_interaction:
                last_dt = datetime.fromisoformat(last_interaction)
                hours_since = (datetime.utcnow() - last_dt).total_seconds() / 3600

                if hours_since > 24:  # 24 hour window for returning customers
                    context["is_returning_customer"] = True
                    context["hours_since_last_interaction"] = hours_since
                    logger.info(f"Returning customer detected for {customer_id} ({hours_since:.1f} hours since last interaction)")

            return context

    async def update_context(
        self,
        customer_id: str,
        user_message: str,
        ai_response: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        department_id: Optional[str] = None
    ) -> None:
        """
        Update conversation context with new messages and data.

        Args:
            customer_id: Unique customer identifier
            user_message: User's message
            ai_response: AI's response
            extracted_data: Newly extracted data from conversation
            department_id: Optional department ID for context isolation
        """
        # Use Redis context manager if available, otherwise fallback to in-memory
        if self.context_manager:
            # Get current context to calculate engagement score
            context = await self.context_manager.get_context(customer_id, department_id)

            # Calculate engagement score for the updated context
            temp_context = {
                "extracted_preferences": {**context.get("extracted_preferences", {}), **(extracted_data or {})},
                "conversation_history": context.get("conversation_history", []) + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": ai_response}
                ],
                "created_at": context.get("created_at")
            }
            engagement_score = self._calculate_engagement_score(temp_context)

            # Update using Redis context manager
            await self.context_manager.update_context(
                customer_id=customer_id,
                user_message=user_message,
                ai_response=ai_response,
                extracted_data=extracted_data,
                department_id=department_id,
                engagement_score=engagement_score
            )

            # Publish conversation events for real-time analytics
            await self._publish_conversation_events(
                customer_id=customer_id,
                user_message=user_message,
                ai_response=ai_response,
                extracted_data=extracted_data,
                engagement_score=engagement_score,
                department_id=department_id
            )
        else:
            # Fallback to in-memory storage for development
            context = await self.get_context(customer_id, department_id=department_id)

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

            # Update last interaction time
            context["last_interaction_at"] = datetime.utcnow().isoformat()

            # Merge extracted data (new data overrides old)
            if extracted_data:
                context["extracted_preferences"].update(extracted_data)

            # Calculate engagement score based on conversation length and data extracted
            context["engagement_score"] = self._calculate_engagement_score(context)

            # Trim conversation history to max length
            max_length = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
            if len(context["conversation_history"]) > max_length:
                context["conversation_history"] = context["conversation_history"][-max_length:]

            context_key = f"{department_id}:{customer_id}" if department_id else customer_id
            self._contexts[context_key] = context

            logger.info(
                f"Updated context for customer {customer_id}",
                extra={
                    "customer_id": customer_id,
                    "history_length": len(context["conversation_history"]),
                    "preferences": context["extracted_preferences"]
                }
            )

    def _calculate_engagement_score(self, context: Dict[str, Any]) -> int:
        """Calculate customer engagement score (0-100)."""
        score = 0

        # Message count factor (up to 30 points)
        message_count = len(context["conversation_history"])
        score += min(30, message_count * 3)

        # Data extraction factor (up to 40 points)
        extracted_data = context["extracted_preferences"]
        score += min(40, len(extracted_data) * 8)

        # Session consistency factor (up to 30 points)
        if context.get("last_interaction_at"):
            hours_since = 0
            if context.get("hours_since_last_interaction"):
                hours_since = context["hours_since_last_interaction"]

            # Higher score for recent interactions
            if hours_since < 1:
                score += 30
            elif hours_since < 24:
                score += 20
            elif hours_since < 72:
                score += 10

        return min(100, score)

    async def extract_data(
        self,
        user_message: str,
        current_preferences: Dict[str, Any],
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from user message.

        Uses AI to extract:
        - Budget/pricing information
        - Service preferences
        - Timeline requirements
        - Contact preferences
        - Industry/company information
        - Specific needs or requirements

        Args:
            user_message: User's latest message
            current_preferences: Previously extracted preferences
            department_id: Optional department context

        Returns:
            Dict of extracted preferences
        """
        extraction_prompt = f"""Analyze this business conversation and extract structured data.

Previous context: {json.dumps(current_preferences, indent=2)}
New message: {user_message}

Extract the following if mentioned (keep previous values if not updated):
- budget: integer (budget in dollars if mentioned)
- budget_range: object with "min" and "max" if range specified
- industry: string (customer's industry or business type)
- company_size: string ("startup", "small", "medium", "enterprise")
- timeline: string (when they need the service/product)
- service_interest: list of strings (services they're interested in)
- contact_preference: string ("email", "phone", "chat", "in-person")
- priority_level: string ("low", "medium", "high", "urgent")
- department: string (which department this relates to)
- requirements: list of strings (specific needs or requirements mentioned)
- pain_points: list of strings (problems they're trying to solve)

Return ONLY valid JSON with extracted fields. If a field is not mentioned, omit it from the response.

Example output:
{{
  "budget": 50000,
  "industry": "healthcare",
  "company_size": "medium",
  "timeline": "Q2 2025",
  "service_interest": ["consulting", "implementation"],
  "contact_preference": "email",
  "priority_level": "high",
  "requirements": ["HIPAA compliance", "24/7 support"],
  "pain_points": ["slow processes", "manual workflows"]
}}
"""

        try:
            # Use AI to extract data with low temperature for consistency
            response = await self.ai_client.agenerate(
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
        customer_info: Dict[str, Any],
        context: Dict[str, Any],
        department_id: Optional[str] = None
    ) -> AIResponse:
        """
        Generate AI response using LLM + RAG.

        Args:
            user_message: User's latest message
            customer_info: Customer information
            context: Conversation context
            department_id: Optional department context

        Returns:
            AIResponse with message, extracted data, reasoning, and score
        """
        customer_name = customer_info.get("name", "there")

        # 1. Extract structured data from user message
        if not context.get("conversation_history"):
            # First interaction - extract data before generating response
            pre_extracted = await self.extract_data(
                user_message,
                {},
                department_id=department_id
            )
            merged_preferences = {**context.get("extracted_preferences", {}), **pre_extracted}
            extracted_data = pre_extracted
        else:
            extracted_data = await self.extract_data(
                user_message,
                context.get("extracted_preferences", {}),
                department_id=department_id
            )
            merged_preferences = {**context.get("extracted_preferences", {}), **extracted_data}

        # 2. Retrieve relevant knowledge from RAG
        relevant_docs = self.knowledge_engine.search(
            query=user_message,
            n_results=4,
            department_id=department_id
        )

        relevant_knowledge = "\\n\\n".join([
            f"[{doc.metadata.get('category', 'info')}]: {doc.text}"
            for doc in relevant_docs
        ]) if relevant_docs else "No specific knowledge base matches."

        # 3. Calculate current engagement score
        engagement_score = self._calculate_engagement_score({
            "extracted_preferences": merged_preferences,
            "conversation_history": context.get("conversation_history", []),
            "created_at": context.get("created_at")
        })

        # 4. Build system prompt with context
        system_prompt = self._build_system_prompt(
            customer_name=customer_name,
            engagement_score=engagement_score,
            extracted_preferences=merged_preferences,
            relevant_knowledge=relevant_knowledge,
            department_id=department_id,
            is_returning_customer=context.get("is_returning_customer", False)
        )

        # 5. Generate response using AI with history
        try:
            # Format history for AI (only role and content)
            history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in context.get("conversation_history", [])
            ]

            ai_response = await self.ai_client.agenerate(
                prompt=user_message,
                system_prompt=system_prompt,
                history=history,
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("MAX_TOKENS", "1000"))
            )

            logger.info(
                "Generated AI response",
                extra={
                    "customer_name": customer_name,
                    "engagement_score": engagement_score,
                    "message_length": len(ai_response.content)
                }
            )

            return AIResponse(
                message=ai_response.content,
                extracted_data=extracted_data,
                reasoning=f"Engagement score: {engagement_score}/100",
                engagement_score=engagement_score,
                input_tokens=ai_response.input_tokens,
                output_tokens=ai_response.output_tokens
            )

        except Exception as e:
            logger.error(
                f"Failed to generate AI response: {str(e)}",
                extra={"error": str(e)}
            )
            # Fallback response
            return AIResponse(
                message=f"Hi {customer_name}! Thanks for reaching out. I'm having a technical issue right now, but I'll get back to you shortly!",
                extracted_data={},
                reasoning="Error occurred",
                engagement_score=0
            )

    def _build_system_prompt(
        self,
        customer_name: str,
        engagement_score: int,
        extracted_preferences: Dict[str, Any],
        relevant_knowledge: str,
        department_id: Optional[str] = None,
        is_returning_customer: bool = False
    ) -> str:
        """Build system prompt with customer context."""

        context_info = ""
        if extracted_preferences:
            context_info = f"\\n\\nCustomer Profile:\\n{json.dumps(extracted_preferences, indent=2)}"

        returning_context = ""
        if is_returning_customer:
            returning_context = "\\nNote: This is a returning customer who has been away for a while. Acknowledge their return warmly."

        knowledge_context = ""
        if relevant_knowledge and relevant_knowledge != "No specific knowledge base matches.":
            knowledge_context = f"\\n\\nRelevant Knowledge Base Information:\\n{relevant_knowledge}"

        return f"""You are an intelligent customer service AI assistant for a business platform.

Customer: {customer_name}
Department: {department_id or 'General'}
Engagement Level: {engagement_score}/100
{returning_context}

Instructions:
1. Be helpful, professional, and conversational
2. Use the customer's name naturally in conversation
3. Reference their previous preferences and needs when relevant
4. Ask clarifying questions to better understand their requirements
5. Provide specific, actionable information based on available knowledge
6. Keep responses concise but informative
7. If you don't have specific information, be honest and offer to connect them with the right person

{context_info}
{knowledge_context}

Always aim to move the conversation forward productively while building rapport."""

    async def calculate_engagement_score(self, customer_id: str, department_id: Optional[str] = None) -> int:
        """
        Calculate engagement score for a customer.

        Args:
            customer_id: Unique customer identifier
            department_id: Optional department context

        Returns:
            Engagement score (0-100)
        """
        context = await self.get_context(customer_id, department_id=department_id)
        return self._calculate_engagement_score(context)

    async def _publish_conversation_events(
        self,
        customer_id: str,
        user_message: str,
        ai_response: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        engagement_score: Optional[int] = None,
        department_id: Optional[str] = None
    ) -> None:
        """Publish conversation events to the event bus for real-time analytics."""
        if not hasattr(self, 'event_bus') or not self.event_bus:
            return  # Event bus not available

        try:
            correlation_id = f"conv_{customer_id}_{int(datetime.utcnow().timestamp())}"

            # Publish conversation message event
            await self.event_bus.publish(
                EventType.CONVERSATION_MESSAGE_SENT,
                {
                    "customer_id": customer_id,
                    "department_id": department_id,
                    "message_type": "user_ai_exchange",
                    "user_message_length": len(user_message),
                    "ai_response_length": len(ai_response),
                    "engagement_score": engagement_score,
                    "extracted_data": extracted_data or {},
                    "has_extracted_data": bool(extracted_data)
                },
                correlation_id=correlation_id
            )

            # Publish context update event
            await self.event_bus.publish(
                EventType.CONTEXT_UPDATED,
                {
                    "customer_id": customer_id,
                    "department_id": department_id,
                    "engagement_score": engagement_score,
                    "preferences_extracted": len(extracted_data or {}),
                    "timestamp": datetime.utcnow().isoformat()
                },
                correlation_id=correlation_id
            )

            # Publish lead scoring event if engagement is high
            if engagement_score and engagement_score > 70:
                await self.event_bus.publish(
                    EventType.LEAD_SCORED,
                    {
                        "customer_id": customer_id,
                        "score_type": "engagement",
                        "score": engagement_score / 100.0,  # Normalize to 0-1
                        "source": "conversation_engagement",
                        "department_id": department_id
                    },
                    correlation_id=correlation_id
                )

            # Publish AI memory update event if significant data was extracted
            if extracted_data and len(extracted_data) > 2:
                await self.event_bus.publish(
                    EventType.AI_MEMORY_UPDATED,
                    {
                        "customer_id": customer_id,
                        "memory_changes": extracted_data,
                        "significant_change": True,
                        "department_id": department_id
                    },
                    correlation_id=correlation_id
                )

            logger.debug(
                f"Published conversation events for customer {customer_id}",
                extra={"correlation_id": correlation_id}
            )

        except Exception as e:
            logger.error(f"Failed to publish conversation events: {e}")

    async def start_conversation(self, customer_id: str, department_id: Optional[str] = None) -> str:
        """
        Start a new conversation session for a customer.

        Args:
            customer_id: Customer identifier
            department_id: Optional department context

        Returns:
            Conversation ID
        """
        conversation_id = f"conv_{customer_id}_{int(datetime.utcnow().timestamp())}"

        # Publish conversation start event
        if hasattr(self, 'event_bus') and self.event_bus:
            try:
                await self.event_bus.publish(
                    EventType.CONVERSATION_STARTED,
                    {
                        "customer_id": customer_id,
                        "conversation_id": conversation_id,
                        "department_id": department_id,
                        "started_at": datetime.utcnow().isoformat()
                    },
                    correlation_id=conversation_id
                )
            except Exception as e:
                logger.error(f"Failed to publish conversation start event: {e}")

        return conversation_id

    async def get_event_bus_stats(self) -> Dict[str, Any]:
        """Get event bus statistics for monitoring."""
        if hasattr(self, 'event_bus') and self.event_bus:
            return await self.event_bus.get_stats()
        return {"error": "Event bus not available"}