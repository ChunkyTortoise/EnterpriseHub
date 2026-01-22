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
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.core.rag_engine import RAGEngine
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import PredictiveLeadScorerV2
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.analytics_engine import AnalyticsEngine
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.prompts.reengagement_templates import REENGAGEMENT_TEMPLATES
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIResponse:
    """AI-generated response with extracted data."""
    message: str
    extracted_data: Dict[str, Any]
    reasoning: str
    lead_score: int
    predictive_score: Optional[Dict[str, Any]] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class ConversationManager:
    """
    Manages conversation state and AI response generation.

    This class handles:
    - Context retrieval and storage
    - AI response generation via Claude + RAG
    - Data extraction from conversations
    - Lead scoring (Rule-based & Predictive)
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

        # Initialize lead scorers
        self.lead_scorer = LeadScorer()
        self.predictive_scorer = PredictiveLeadScorerV2()

        # Persistent memory service (Dynamically chooses Redis in prod, File in local)
        self.memory_service = MemoryService()

        # Analytics engine for metrics collection
        self.analytics_engine = AnalyticsEngine()
        
        # New Analytics Service for token tracking
        self.analytics = AnalyticsService()

        # Property matcher for listing recommendations
        self.property_matcher = PropertyMatcher()

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
        context = await self.memory_service.get_context(contact_id, location_id=location_id)
        
        # Check for session gap (Smart Resume)
        last_interaction = context.get("last_interaction_at")
        if last_interaction:
            last_dt = datetime.fromisoformat(last_interaction)
            hours_since = (datetime.utcnow() - last_dt).total_seconds() / 3600
            
            if hours_since > settings.previous_context_window_hours:
                # Long gap detected - this is a returning lead session
                context["is_returning_lead"] = True
                context["hours_since_last_interaction"] = hours_since
                logger.info(f"Returning lead detected for {contact_id} ({hours_since:.1f} hours since last interaction)")
        
        return context

    async def update_context(
        self,
        contact_id: str,
        user_message: str,
        ai_response: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None,
        seller_temperature: Optional[str] = None
    ) -> None:
        """
        Update conversation context with new messages and data.

        Args:
            contact_id: GHL contact ID
            user_message: User's message
            ai_response: AI's response
            extracted_data: Newly extracted data from conversation (buyer or seller)
            location_id: Optional location ID for isolation
            seller_temperature: Seller temperature classification (for Jorge's seller bot)
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

        # Update last interaction time
        context["last_interaction_at"] = datetime.utcnow().isoformat()

        # Merge extracted data (new data overrides old)
        if extracted_data:
            # Check if this is seller data (Jorge's seller bot)
            if seller_temperature or any(key in extracted_data for key in ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]):
                # Handle seller data
                if "seller_preferences" not in context:
                    context["seller_preferences"] = {}
                context["seller_preferences"].update(extracted_data)

                # Set seller temperature if provided
                if seller_temperature:
                    context["seller_temperature"] = seller_temperature
            else:
                # Handle buyer data (existing logic)
                context["extracted_preferences"].update(extracted_data)

        # Update last lead score for analytics tracking
        current_score = self.lead_scorer.calculate(context)
        context["last_lead_score"] = current_score

        # Calculate predictive conversion probability
        predictive_result = await self.predictive_scorer.calculate_predictive_score(context, location=location_id)
        # Serialize the dataclass to a dict for storage
        # Filter out fields that might not be serializable if any, but asdict should be fine for JSON types
        # Note: priority_level is an Enum, needs conversion
        predictive_data = asdict(predictive_result)
        predictive_data["priority_level"] = predictive_result.priority_level.value
        context["predictive_score"] = predictive_data

        # Trim conversation history to max length and summarize if needed
        max_length = settings.max_conversation_history_length
        if len(context["conversation_history"]) > max_length:
            # Before trimming, we could theoretically summarize,
            # but for now we'll just keep the preferences updated.
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
        tenant_config: Optional[Dict[str, Any]] = None,
        images: Optional[List[str]] = None
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
            images: Optional list of base64 images for vision analysis

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
- repair_estimate: integer (estimated repair costs if images provided or mentioned)
- pathway: string ("wholesale" or "listing")
- selected_slot: string (if user selected a time for appointment, e.g. "Monday at 10am")

Return ONLY valid JSON with extracted fields. If a field is not mentioned, omit it from the response.
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
                max_tokens=500,
                images=images
            )
            
            # Record usage
            location_id = tenant_config.get("location_id", "unknown") if tenant_config else "unknown"
            provider_val = response.provider.value if hasattr(response.provider, "value") else str(response.provider)
            await self.analytics.track_llm_usage(
                location_id=location_id,
                model=response.model,
                provider=provider_val,
                input_tokens=response.input_tokens or 0,
                output_tokens=response.output_tokens or 0,
                cached=False
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

    async def extract_seller_data(
        self,
        user_message: str,
        current_seller_data: Dict[str, Any],
        tenant_config: Optional[Dict[str, Any]] = None,
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract seller-specific data from user message using Claude.

        Designed for Jorge's 4-question seller qualification process:
        1. Motivation & Relocation destination
        2. Timeline acceptance (30-45 days)
        3. Property condition
        4. Price expectations

        Args:
            user_message: User's latest message
            current_seller_data: Previously extracted seller data
            tenant_config: Optional tenant-specific API keys
            images: Optional list of base64 images for vision analysis

        Returns:
            Dict of extracted seller preferences
        """
        extraction_prompt = f"""Extract seller qualification data from this message: "{user_message}"

Current seller data: {json.dumps(current_seller_data, indent=2)}

Extract the following fields (only if clearly mentioned):

MOTIVATION & RELOCATION:
- motivation: Why they want to sell (relocation, downsizing, financial, divorce, inherited, other)
- relocation_destination: Where they plan to move (city, state, or general area)

TIMELINE:
- timeline_acceptable: Boolean - would 30-45 days be okay? (true/false/null)
- timeline_urgency: "urgent" (30-45 days), "flexible", "long-term", or "unknown"

PROPERTY CONDITION:
- property_condition: "move-in ready", "needs work", "major repairs", or "unknown"
- repair_estimate: Any mentioned or VISUALLY ESTIMATED (from images) repair needs or costs

PRICE EXPECTATIONS:
- price_expectation: Numeric price they mentioned (dollars)
- price_flexibility: "firm", "negotiable", or "unknown"

RESPONSE QUALITY METRICS:
- response_quality: 0.0-1.0 based on completeness and specificity
- responsiveness: 0.0-1.0 based on engagement level

Return ONLY JSON with extracted fields. If no new info, return existing data.
Count questions_answered based on how many of the 4 main categories have data.
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

            # Use Claude to extract seller data
            response = await llm_client.agenerate(
                prompt=extraction_prompt,
                system_prompt="You are a seller data extraction specialist for real estate. Return only valid JSON.",
                temperature=0,
                max_tokens=500,
                images=images
            )

            # Record usage
            location_id = tenant_config.get("location_id", "unknown") if tenant_config else "unknown"
            provider_val = response.provider.value if hasattr(response.provider, "value") else str(response.provider)
            await self.analytics.track_llm_usage(
                location_id=location_id,
                model=response.model,
                provider=provider_val,
                input_tokens=response.input_tokens or 0,
                output_tokens=response.output_tokens or 0,
                cached=False
            )

            extracted_data = json.loads(response.content)

            # Merge with existing seller data
            merged_data = {**current_seller_data, **extracted_data}

            # Ensure questions_answered count is accurate
            question_fields = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]
            questions_answered = sum(1 for field in question_fields if merged_data.get(field) is not None)
            merged_data["questions_answered"] = questions_answered

            # Auto-assess response quality if not provided by Claude
            if "response_quality" not in extracted_data:
                merged_data["response_quality"] = self._assess_seller_response_quality(user_message)

            logger.info(
                "Extracted seller data from message",
                extra={
                    "extracted": merged_data,
                    "questions_answered": questions_answered
                }
            )

            return merged_data

        except (json.JSONDecodeError, Exception) as e:
            logger.error(
                f"Failed to extract seller data: {str(e)}",
                extra={"error": str(e), "user_message": user_message}
            )
            return current_seller_data

    def _assess_seller_response_quality(self, user_message: str) -> float:
        """
        Assess quality of seller response for Jorge's confrontational tone adjustment.

        Args:
            user_message: User's message text

        Returns:
            Quality score (0.0-1.0)
        """
        message = user_message.strip().lower()

        # Very short/evasive responses
        if len(message) < 10:
            return 0.2

        # Vague responses
        vague_indicators = ["maybe", "not sure", "idk", "i don't know", "thinking about it", "unsure"]
        if any(indicator in message for indicator in vague_indicators):
            return 0.4

        # Good quality indicators
        specific_indicators = ["definitely", "yes", "no", "exactly", "specifically", "$", "days", "weeks", "months"]
        if any(indicator in message for indicator in specific_indicators):
            return 0.8

        # Decent responses with some specifics
        if len(message) > 20:
            return 0.7

        # Default quality
        return 0.6

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
        Generate AI response using Claude + RAG with parallel pipeline.

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
        import asyncio
        import time
        
        contact_name = contact_info.get("first_name", "there")
        location_id = tenant_config.get("location_id") if tenant_config else None
        calendar_id = (tenant_config.get("ghl_calendar_id") if tenant_config else None) or settings.ghl_calendar_id

        # 1. Extraction (Still sequential as it's the primary dependency)
        if not context.get("conversation_history"):
            extracted_data = await self.extract_data(
                user_message,
                {},
                tenant_config=tenant_config
            )
        else:
            extracted_data = await self.extract_data(
                user_message,
                context.get("extracted_preferences", {}),
                tenant_config=tenant_config
            )

        merged_preferences = {**context.get("extracted_preferences", {}), **extracted_data}

        # 2. Parallel Pipeline Execution
        # We run RAG, Lead Scoring, and Slots/Matches in parallel
        
        # Prepare RAG query
        pathway = merged_preferences.get("pathway")
        home_condition = merged_preferences.get("home_condition", "").lower()
        enhanced_query = user_message
        if pathway == "wholesale" or "poor" in home_condition or "fixer" in home_condition:
            enhanced_query = f"{user_message} wholesale cash offer as-is quick sale"
        elif pathway == "listing":
            enhanced_query = f"{user_message} MLS listing top dollar market value"

        # Define internal helper for parallel tasks
        async def get_slots_task():
            if ghl_client and calendar_id:
                try:
                    now = datetime.now()
                    start_date = now.strftime("%Y-%m-%d")
                    end_date = (now + timedelta(days=3)).strftime("%Y-%m-%d")
                    return await ghl_client.get_available_slots(calendar_id, start_date, end_date)
                except Exception as e:
                    logger.error(f"Parallel slot fetch failed: {e}")
            return []

        async def get_matches_task():
            if is_buyer:
                matches = await asyncio.to_thread(self.property_matcher.find_matches, merged_preferences, limit=2)
                if matches:
                    # Parallelize explanations for each match
                    explanation_tasks = [
                        self.property_matcher.agentic_explain_match(prop, merged_preferences)
                        for prop in matches
                    ]
                    explanations = await asyncio.gather(*explanation_tasks, return_exceptions=True)
                    
                    results = []
                    for i, prop in enumerate(matches):
                        explanation = explanations[i] if not isinstance(explanations[i], Exception) else "Great match for your needs."
                        results.append((prop, explanation))
                    return results
            return []

        # Execute parallel tasks
        rag_task = self.rag_engine.search_corrective(
            query=enhanced_query,
            n_results=settings.rag_top_k_results,
            location_id=location_id
        )
        
        # Run Lead Score calculation (sync but fast, wrapped for parallel flow consistency)
        score_task = asyncio.to_thread(
            self.lead_scorer.calculate,
            {
                "extracted_preferences": merged_preferences,
                "conversation_history": context.get("conversation_history", []),
                "created_at": context.get("created_at")
            }
        )

        # Launch all parallel tasks
        results = await asyncio.gather(
            rag_task,
            score_task,
            get_slots_task(),
            get_matches_task(),
            return_exceptions=True
        )

        # Unpack results with safety
        relevant_docs = results[0] if not isinstance(results[0], Exception) else []
        lead_score = results[1] if not isinstance(results[1], Exception) else 0
        slots = results[2] if not isinstance(results[2], Exception) else []
        property_matches_data = results[3] if not isinstance(results[3], Exception) else []

        # 3. Process results into formatted strings
        relevant_knowledge = "\n\n".join([
            f"[{doc.metadata.get('category', 'info')}]: {doc.text}"
            for doc in relevant_docs
        ]) if relevant_docs else "No specific knowledge base matches."

        available_slots_text = ""
        if lead_score >= 3 and slots:
            available_slots_text = "I can get you on the phone with Jorge's team. Would one of these work?\n"
            for slot in slots[:2]:
                dt = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))
                available_slots_text += f"- {dt.strftime('%a @ %I:%M %p')}\n"
            available_slots_text += "Or should I just have them call you when they're free?"
        elif lead_score >= 3:
            available_slots_text = "I'll have Jorge call you directly. What time works best for you?"

        property_recommendations = ""
        if lead_score >= 2 and property_matches_data:
            property_recommendations = "I found a couple of strategic property matches for you:\n"
            for prop, explanation in property_matches_data:
                property_recommendations += f"- {self.property_matcher.format_match_for_sms(prop)}\n  {explanation}\n"
            property_recommendations += "Should I send you the full listing details for these?"

        # 4. Appointment Auto-Booking (Sequential but rare)
        appointment_booked_msg = ""
        selected_slot = extracted_data.get("selected_slot")
        if selected_slot and ghl_client and calendar_id:
            # Basic auto-booking logic (simplified for Phase 3)
            try:
                contact_id = contact_info.get("id")
                if contact_id and slots:
                    matched_slot = slots[0]["start_time"]
                    await ghl_client.create_appointment(
                        contact_id=contact_id,
                        calendar_id=calendar_id,
                        start_time=matched_slot,
                        title=f"AI Booking: {contact_info.get('first_name', 'Lead')}"
                    )
                    dt = datetime.fromisoformat(matched_slot.replace("Z", "+00:00"))
                    appointment_booked_msg = f"\n\n[SYSTEM: Confirmed for {dt.strftime('%a @ %I:%M %p')}]"
            except Exception as e:
                logger.error(f"Auto-booking failed: {e}")

        # 5. Build system prompt and Generate response
        from ghl_real_estate_ai.prompts.system_prompts import build_system_prompt
        system_prompt = build_system_prompt(
            contact_name=contact_name,
            conversation_stage=context.get("conversation_stage", "qualifying"),
            lead_score=lead_score,
            extracted_preferences=merged_preferences,
            relevant_knowledge=relevant_knowledge,
            is_buyer=is_buyer,
            available_slots=available_slots_text,
            appointment_status=appointment_booked_msg,
            property_recommendations=property_recommendations,
            is_returning_lead=context.get("is_returning_lead", False),
            hours_since=context.get("hours_since_last_interaction", 0)
        )

        response_start_time = time.time()
        
        # LLM Call (Sequential)
        try:
            llm_client = self.llm_client
            if tenant_config and tenant_config.get("anthropic_api_key"):
                llm_client = LLMClient(
                    provider="claude",
                    model=settings.claude_model,
                    api_key=tenant_config["anthropic_api_key"]
                )

            history = [{"role": msg["role"], "content": msg["content"]} for msg in context.get("conversation_history", [])]

            ai_response = await llm_client.agenerate(
                prompt=user_message,
                system_prompt=system_prompt,
                history=history,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            
            response_time_ms = (time.time() - response_start_time) * 1000

            # SMS limit enforcement
            if len(ai_response.content) > 160:
                ai_response.content = ai_response.content[:157] + "..."

            # 6. Post-Processing (Background Tasks)
            contact_id = contact_info.get("id", "unknown")
            location_id_str = location_id or "default"
            
            # Background task for analytics and predictive scoring
            async def post_processing():
                # Track usage
                await self.analytics.track_llm_usage(
                    location_id=location_id_str,
                    model=ai_response.model,
                    provider=ai_response.provider.value,
                    input_tokens=ai_response.input_tokens or 0,
                    output_tokens=ai_response.output_tokens or 0,
                    cached=False,
                    contact_id=contact_id
                )
                
                # Record event
                appointment_scheduled = any(k in ai_response.content.lower() for k in ["schedule", "appointment", "calendar", "book"])
                await self.analytics_engine.record_event(
                    contact_id=contact_id,
                    location_id=location_id_str,
                    lead_score=lead_score,
                    previous_score=context.get("last_lead_score", 0),
                    message=user_message,
                    response=ai_response.content,
                    response_time_ms=response_time_ms,
                    context=context,
                    appointment_scheduled=appointment_scheduled
                )
                
                # Predictive scoring update in context
                await self.predictive_scorer.calculate_predictive_score({
                    **context,
                    "extracted_preferences": merged_preferences,
                    "last_lead_score": lead_score
                }, location=location_id_str)

            # Fire and forget post-processing
            asyncio.create_task(post_processing())

            return AIResponse(
                message=ai_response.content,
                extracted_data=extracted_data,
                reasoning=f"Lead score: {lead_score}/100",
                lead_score=lead_score,
                predictive_score=None # Will be updated in context via background task
            )

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return AIResponse(
                message=f"Hey {contact_name}! I'm having a quick technical issue—give me just a moment and I'll get back to you!",
                extracted_data={},
                reasoning="Error",
                lead_score=0
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
