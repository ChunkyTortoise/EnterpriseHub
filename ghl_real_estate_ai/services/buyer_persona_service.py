"""
Buyer Persona Service

Analyzes buyer conversation patterns to classify buyer personas and provide
personalized communication recommendations.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, TaskComplexity
from ghl_real_estate_ai.models.buyer_persona import (
    BuyerPersonaClassification,
    BuyerPersonaInsights,
    BuyerPersonaType,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class BuyerPersonaService:
    """
    Classifies buyers into persona categories based on conversation analysis
    and provides tailored communication recommendations.
    """

    # Keyword patterns for each persona type
    KEYWORD_PATTERNS: Dict[BuyerPersonaType, List[str]] = {
        BuyerPersonaType.FIRST_TIME: [
            "first home",
            "new to buying",
            "never owned",
            "what do i need",
            "how does buying work",
            "excited but nervous",
            "first time buyer",
            "never bought before",
            "don't know where to start",
            "first purchase",
            "buying my first",
        ],
        BuyerPersonaType.UPSIZER: [
            "more space",
            "growing family",
            "outgrown",
            "bigger",
            "additional bedroom",
            "need room",
            "upsizing",
            "need more space",
            "running out of room",
            "family is growing",
            "need a bigger house",
            "expanding",
        ],
        BuyerPersonaType.DOWNSIZER: [
            "too much space",
            "maintenance",
            "downsize",
            "simpler",
            "empty nest",
            "less cleaning",
            "too big",
            "too much house",
            "simplify",
            "retiring",
            "kids moved out",
            "smaller home",
        ],
        BuyerPersonaType.INVESTOR: [
            "rental",
            "rental income",
            "roi",
            "return on investment",
            "cash flow",
            "tenant",
            "deal",
            "investment property",
            "renting out",
            "flip",
            "multi-family",
            "duplex",
            "investment",
            "cashflow",
        ],
        BuyerPersonaType.RELOCATOR: [
            "relocating",
            "moving to",
            "new job",
            "transfer",
            "area",
            "different city",
            "moving from",
            "relocation",
            "transferring",
            "new area",
            "unfamiliar with",
            "moving for work",
        ],
        BuyerPersonaType.LUXURY: [
            "high-end",
            "premium",
            "amenities",
            "view",
            "custom",
            "executive",
            "luxury",
            "exclusive",
            "gated",
            "estate",
            "premium features",
            "high quality",
            "upscale",
        ],
    }

    # Behavioral weights for signal scoring
    BEHAVIORAL_WEIGHTS: Dict[str, float] = {
        "question_pattern": 0.3,
        "response_length": 0.2,
        "timeline_urgency": 0.2,
        "budget_openness": 0.15,
        "feature_priority": 0.15,
    }

    # Persona insights for communication recommendations
    PERSONA_INSIGHTS: Dict[BuyerPersonaType, BuyerPersonaInsights] = {
        BuyerPersonaType.FIRST_TIME: BuyerPersonaInsights(
            tone="Encouraging, supportive",
            content_focus="Educational, step-by-step",
            urgency_level="Moderate",
            key_messages=[
                "Here's how it works",
                "Validation of concerns",
                "You're not alone in this process",
                "Let me guide you through each step",
            ],
            recommended_questions=[
                "What's your biggest concern about buying?",
                "Have you thought about your timeline?",
                "What's most important to you in a home?",
            ],
        ),
        BuyerPersonaType.UPSIZER: BuyerPersonaInsights(
            tone="Efficient, family-focused",
            content_focus="Space solutions, equity info",
            urgency_level="High",
            key_messages=[
                "Maximize your investment",
                "Room for growth",
                "Leverage your current equity",
                "Find the perfect space for your family",
            ],
            recommended_questions=[
                "How many bedrooms do you need?",
                "What's driving your need for more space?",
                "What's your ideal timeline for moving?",
            ],
        ),
        BuyerPersonaType.DOWNSIZER: BuyerPersonaInsights(
            tone="Empathetic, simplifying",
            content_focus="Maintenance reduction, equity",
            urgency_level="Moderate",
            key_messages=[
                "Simplify your life",
                "Access your equity",
                "Less maintenance, more freedom",
                "Right-size your home for your lifestyle",
            ],
            recommended_questions=[
                "What's motivating your downsizing decision?",
                "How much space do you realistically need?",
                "What features are must-haves vs. nice-to-haves?",
            ],
        ),
        BuyerPersonaType.INVESTOR: BuyerPersonaInsights(
            tone="Professional, data-driven",
            content_focus="ROI analysis, cash flow",
            urgency_level="Low-Medium",
            key_messages=[
                "Numbers breakdown",
                "Deal analysis",
                "ROI projections",
                "Market data and trends",
            ],
            recommended_questions=[
                "What's your target ROI?",
                "Are you looking for cash flow or appreciation?",
                "What's your investment budget?",
            ],
        ),
        BuyerPersonaType.RELOCATOR: BuyerPersonaInsights(
            tone="Direct, informative",
            content_focus="Area info, timeline",
            urgency_level="High",
            key_messages=[
                "Area insights",
                "Smooth transition",
                "Local market knowledge",
                "Timeline management",
            ],
            recommended_questions=[
                "When do you need to be moved in?",
                "What's bringing you to this area?",
                "What do you know about the neighborhoods here?",
            ],
        ),
        BuyerPersonaType.LUXURY: BuyerPersonaInsights(
            tone="Sophisticated, exclusive",
            content_focus="Amenities, lifestyle",
            urgency_level="Low",
            key_messages=[
                "Premium experience",
                "Exclusive properties",
                "Lifestyle amenities",
                "Exceptional quality",
            ],
            recommended_questions=[
                "What amenities are non-negotiable?",
                "What's your ideal lifestyle vision?",
                "What features define luxury for you?",
            ],
        ),
        BuyerPersonaType.UNKNOWN: BuyerPersonaInsights(
            tone="Friendly, inquisitive",
            content_focus="General information gathering",
            urgency_level="Low",
            key_messages=[
                "Let me help you find what you're looking for",
                "Tell me more about your needs",
                "I'm here to assist you",
            ],
            recommended_questions=[
                "What brings you to the market today?",
                "What are you looking for in a property?",
                "What's your ideal timeline?",
            ],
        ),
    }

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.cache_service = get_cache_service()
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)

    async def classify_buyer_type(
        self,
        conversation_history: List[Dict[str, Any]],
        lead_data: Optional[Dict[str, Any]] = None,
    ) -> BuyerPersonaClassification:
        """
        Classify buyer into persona category based on conversation analysis.

        Args:
            conversation_history: List of conversation messages
            lead_data: Optional lead data from GHL

        Returns:
            BuyerPersonaClassification with persona type, confidence, and signals
        """
        # Check cache first
        cache_key = f"buyer_persona:{self._get_cache_key(conversation_history)}"
        cached_result = await self.cache_service.get(cache_key)

        if cached_result:
            logger.info("Returning cached buyer persona classification")
            return BuyerPersonaClassification.model_validate(cached_result)

        logger.info("Classifying buyer persona from conversation using LLM")

        # Primary Strategy: LLM Semantic Analysis
        llm_result = await self._classify_persona_llm(conversation_history, lead_data)
        
        if llm_result and llm_result.persona_type != BuyerPersonaType.UNKNOWN and llm_result.confidence > 0.6:
            classification = llm_result
        else:
            # Fallback Strategy: Keyword and Behavioral Analysis
            logger.info("LLM classification low confidence or failed, falling back to heuristics")
            persona_scores = self._analyze_persona_signals(conversation_history)

            # Determine primary persona
            primary_persona = max(persona_scores, key=persona_scores.get)
            confidence = persona_scores[primary_persona]

            # Get detected signals
            detected_signals = self._get_detected_signals(
                conversation_history, primary_persona
            )

            # Analyze behavioral signals
            behavioral_signals = self._analyze_behavioral_signals(conversation_history)

            # Classify indicators
            primary_indicators, secondary_indicators = self._classify_indicators(
                detected_signals, behavioral_signals
            )

            # Build classification result
            classification = BuyerPersonaClassification(
                persona_type=primary_persona,
                confidence=confidence,
                detected_signals=detected_signals,
                behavioral_signals=behavioral_signals,
                primary_indicators=primary_indicators,
                secondary_indicators=secondary_indicators,
            )

        # Cache result for 1 hour (personas can change as conversation progresses)
        await self.cache_service.set(cache_key, classification.model_dump(), ttl=3600)

        logger.info(
            f"Buyer persona classified: {classification.persona_type.value} (confidence: {classification.confidence:.2f})"
        )

        return classification

    async def _classify_persona_llm(
        self,
        conversation_history: List[Dict[str, Any]],
        lead_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[BuyerPersonaClassification]:
        """
        Use LLM for semantic persona classification.
        """
        prompt = f"""
        Analyze the following real estate conversation and lead data to classify the buyer persona.
        
        CONVERSATION:
        {json.dumps(conversation_history, indent=2)}
        
        LEAD DATA:
        {json.dumps(lead_data, indent=2)}
        
        PERSONA DEFINITIONS:
        - first_time: Never owned property, needs education, cautious, validation-seeking.
        - upsizer: Moving to larger property, growing family, space needs, equity leverage.
        - downsizer: Reducing living space, empty nest, maintenance reduction, equity access.
        - investor: Purchasing for ROI, cash flow focus, numbers-driven, deal-focused.
        - relocator: Job/region change, time pressure, area unfamiliarity.
        - luxury: High-end purchase, amenity focus, lifestyle vision, premium features.
        
        Return ONLY a JSON object:
        {{
            "persona": "one of the above keys",
            "confidence": 0.0 to 1.0,
            "signals": ["detected keyword or signal 1", "signal 2"],
            "behavioral_insights": {{
                "urgency": 0.0 to 1.0,
                "data_focus": 0.0 to 1.0,
                "emotional_engagement": 0.0 to 1.0
            }},
            "reasoning": "Brief explanation of the classification"
        }}
        """

        try:
            response = await self.llm.agenerate(
                prompt=prompt,
                system_prompt="You are an expert Real Estate Behavioral Analyst specializing in buyer segmentation.",
                complexity=TaskComplexity.COMPLEX,
                max_tokens=500,
                temperature=0.0,
            )

            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            persona_map = {
                "first_time": BuyerPersonaType.FIRST_TIME,
                "upsizer": BuyerPersonaType.UPSIZER,
                "downsizer": BuyerPersonaType.DOWNSIZER,
                "investor": BuyerPersonaType.INVESTOR,
                "relocator": BuyerPersonaType.RELOCATOR,
                "luxury": BuyerPersonaType.LUXURY,
            }
            
            persona_type = persona_map.get(data.get("persona"), BuyerPersonaType.UNKNOWN)
            
            return BuyerPersonaClassification(
                persona_type=persona_type,
                confidence=data.get("confidence", 0.0),
                detected_signals=data.get("signals", []),
                behavioral_signals={
                    "urgency": data.get("behavioral_insights", {}).get("urgency", 0.0),
                    "data_focus": data.get("behavioral_insights", {}).get("data_focus", 0.0),
                    "emotional_engagement": data.get("behavioral_insights", {}).get("emotional_engagement", 0.0),
                },
                primary_indicators=data.get("signals", [])[:3],
                secondary_indicators=[f"Reasoning: {data.get('reasoning', '')}"]
            )
        except Exception as e:
            logger.error(f"Error in LLM persona classification: {e}")
            return None


        # Cache result for 1 hour (personas can change as conversation progresses)
        await self.cache_service.set(cache_key, classification.model_dump(), ttl=3600)

        logger.info(
            f"Buyer persona classified: {primary_persona.value} (confidence: {confidence:.2f})"
        )

        return classification

    def _analyze_persona_signals(
        self, conversation_history: List[Dict[str, Any]]
    ) -> Dict[BuyerPersonaType, float]:
        """
        Analyze conversation for persona signals and score each persona type.

        Returns:
            Dictionary mapping persona types to confidence scores (0.0-1.0)
        """
        scores = {persona: 0.0 for persona in BuyerPersonaType}

        # Combine all user messages for analysis
        user_messages = [
            msg.get("content", "").lower()
            for msg in conversation_history
            if msg.get("role") == "user"
        ]
        combined_text = " ".join(user_messages)

        # Score each persona based on keyword matches
        for persona, keywords in self.KEYWORD_PATTERNS.items():
            matches = 0
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    matches += 1

            # Calculate confidence based on match count
            if matches > 0:
                # Base score from keyword matches (max 0.7)
                base_score = min(matches * 0.15, 0.7)
                scores[persona] = base_score

        # If no strong signals, default to unknown
        if all(score < 0.3 for score in scores.values()):
            scores[BuyerPersonaType.UNKNOWN] = 0.5

        return scores

    def _get_detected_signals(
        self,
        conversation_history: List[Dict[str, Any]],
        persona: BuyerPersonaType,
    ) -> List[str]:
        """
        Get detected keyword signals for the classified persona.

        Args:
            conversation_history: List of conversation messages
            persona: Classified persona type

        Returns:
            List of detected keyword signals
        """
        detected = []

        # Combine all user messages
        user_messages = [
            msg.get("content", "").lower()
            for msg in conversation_history
            if msg.get("role") == "user"
        ]
        combined_text = " ".join(user_messages)

        # Check for keywords matching the persona
        keywords = self.KEYWORD_PATTERNS.get(persona, [])
        for keyword in keywords:
            if keyword.lower() in combined_text:
                detected.append(keyword)

        return detected

    def _analyze_behavioral_signals(
        self, conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Analyze behavioral signals from conversation patterns.

        Returns:
            Dictionary of behavioral signal scores
        """
        signals = {
            "question_pattern": 0.0,
            "response_length": 0.0,
            "timeline_urgency": 0.0,
            "budget_openness": 0.0,
            "feature_priority": 0.0,
        }

        user_messages = [
            msg.get("content", "")
            for msg in conversation_history
            if msg.get("role") == "user"
        ]

        if not user_messages:
            return signals

        # Question pattern: count questions
        question_count = sum(1 for msg in user_messages if "?" in msg)
        signals["question_pattern"] = min(question_count / len(user_messages), 1.0)

        # Response length: average message length
        avg_length = sum(len(msg) for msg in user_messages) / len(user_messages)
        signals["response_length"] = min(avg_length / 200, 1.0)

        # Timeline urgency: look for urgency keywords
        urgency_keywords = ["asap", "soon", "urgent", "quickly", "immediately", "need to move"]
        urgency_count = sum(
            1
            for msg in user_messages
            for keyword in urgency_keywords
            if keyword in msg.lower()
        )
        signals["timeline_urgency"] = min(urgency_count / len(user_messages), 1.0)

        # Budget openness: look for budget-related keywords
        budget_keywords = ["budget", "price", "afford", "can afford", "spend", "looking to spend"]
        budget_count = sum(
            1
            for msg in user_messages
            for keyword in budget_keywords
            if keyword in msg.lower()
        )
        signals["budget_openness"] = min(budget_count / len(user_messages), 1.0)

        # Feature priority: look for feature-specific keywords
        feature_keywords = ["bedroom", "bathroom", "yard", "garage", "pool", "kitchen"]
        feature_count = sum(
            1
            for msg in user_messages
            for keyword in feature_keywords
            if keyword in msg.lower()
        )
        signals["feature_priority"] = min(feature_count / len(user_messages), 1.0)

        return signals

    def _classify_indicators(
        self, detected_signals: List[str], behavioral_signals: Dict[str, float]
    ) -> tuple[List[str], List[str]]:
        """
        Classify detected signals into primary and secondary indicators.

        Returns:
            Tuple of (primary_indicators, secondary_indicators)
        """
        primary = []
        secondary = []

        # Primary indicators: direct keyword matches
        primary.extend(detected_signals[:3])  # Top 3 detected signals

        # Secondary indicators: behavioral signals with high scores
        for signal, score in behavioral_signals.items():
            if score >= 0.5:
                secondary.append(f"{signal.replace('_', ' ')} (score: {score:.2f})")

        return primary, secondary

    def _get_cache_key(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate a cache key from conversation history.

        Args:
            conversation_history: List of conversation messages

        Returns:
            Cache key string
        """
        # Use last 3 user messages for cache key
        user_messages = [
            msg.get("content", "")[:50]
            for msg in conversation_history[-6:]
            if msg.get("role") == "user"
        ]
        return "|".join(user_messages)

    async def get_persona_insights(
        self, persona: BuyerPersonaType
    ) -> BuyerPersonaInsights:
        """
        Get communication recommendations for a specific persona.

        Args:
            persona: Buyer persona type

        Returns:
            BuyerPersonaInsights with communication recommendations
        """
        return self.PERSONA_INSIGHTS.get(persona, self.PERSONA_INSIGHTS[BuyerPersonaType.UNKNOWN])

    async def update_persona(
        self,
        lead_id: str,
        new_conversation: List[Dict[str, Any]],
        lead_data: Optional[Dict[str, Any]] = None,
    ) -> BuyerPersonaClassification:
        """
        Re-classify buyer persona with new conversation data.

        Args:
            lead_id: Lead/contact ID
            new_conversation: New conversation messages
            lead_data: Optional lead data from GHL

        Returns:
            Updated BuyerPersonaClassification
        """
        logger.info(f"Updating buyer persona for lead {lead_id}")

        # Clear cache for this lead
        cache_key = f"buyer_persona:{self._get_cache_key(new_conversation)}"
        await self.cache_service.delete(cache_key)

        # Re-classify with new data
        return await self.classify_buyer_type(new_conversation, lead_data)
