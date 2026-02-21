"""
PersonalizedNarrativeEngine - Transform property data into compelling lifestyle narratives.

The highest-impact client value feature that transforms generic property listings
into emotional, personalized lifestyle stories that drive buyer engagement.

Architecture:
- Integrates with Claude 3.5 Sonnet for narrative generation
- Redis caching with 24-hour TTL for performance
- Template-based fallbacks when Claude unavailable
- Sophisticated prompt engineering for consistent quality
- Performance optimized for <2 second response time
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.matching_models import LifestyleScores
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class NarrativeStyle(Enum):
    """Different narrative styles for different buyer types."""

    EMOTIONAL = "emotional"  # Family buyers, first-time buyers
    PROFESSIONAL = "professional"  # Executive relocations, professionals
    INVESTMENT = "investment"  # Investors focused on ROI
    LUXURY = "luxury"  # High-end luxury buyers
    LIFESTYLE = "lifestyle"  # Lifestyle-focused buyers


class NarrativeLength(Enum):
    """Narrative length options."""

    SHORT = "short"  # 100-150 words for SMS/quick summaries
    MEDIUM = "medium"  # 200-300 words for emails/detailed cards
    LONG = "long"  # 400-500 words for proposals/presentations


@dataclass
class NarrativeComponent:
    """Individual lifestyle element within the narrative."""

    element_type: str  # "neighborhood", "schools", "commute", "amenities"
    score: float  # 0.0 to 1.0 relevance score
    description: str  # Human-readable description
    emotional_hooks: List[str]  # Key emotional phrases
    data_points: Dict[str, Any]  # Supporting data


@dataclass
class PersonalizedNarrative:
    """Complete personalized narrative for a property-buyer combination."""

    property_id: str
    lead_id: str
    narrative_text: str
    style: NarrativeStyle
    length: NarrativeLength
    components: List[NarrativeComponent] = field(default_factory=list)

    # Metadata
    overall_appeal_score: float = 0.0
    key_selling_points: List[str] = field(default_factory=list)
    emotional_themes: List[str] = field(default_factory=list)
    call_to_action: str = ""

    # Generation details
    generated_at: datetime = field(default_factory=datetime.now)
    generation_time_ms: int = 0
    model_used: str = ""
    cached: bool = False
    fallback_used: bool = False


class PersonalizedNarrativeEngine:
    """
    Core engine for generating personalized property narratives.

    Transforms generic property data into compelling, personalized lifestyle
    stories that resonate with specific buyer psychology and preferences.
    """

    def __init__(self, llm_provider: str = "claude", enable_caching: bool = True):
        """
        Initialize the narrative engine.

        Args:
            llm_provider: LLM provider ("claude" or "gemini")
            enable_caching: Whether to use Redis caching
        """
        self.llm_client = LLMClient(provider=llm_provider)
        self.cache_service = get_cache_service() if enable_caching else None
        self.analytics = AnalyticsService()
        self.enable_caching = enable_caching

        # Performance tracking
        self._generation_count = 0
        self._cache_hits = 0
        self._fallback_count = 0

        logger.info(f"PersonalizedNarrativeEngine initialized with {llm_provider} provider")

    async def generate_personalized_narrative(
        self,
        property_data: Dict[str, Any],
        lead_data: Dict[str, Any],
        lifestyle_scores: Optional[LifestyleScores] = None,
        style: NarrativeStyle = NarrativeStyle.EMOTIONAL,
        length: NarrativeLength = NarrativeLength.MEDIUM,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> PersonalizedNarrative:
        """
        Generate a personalized narrative for a property-buyer combination.

        Args:
            property_data: Property information (address, features, price, etc.)
            lead_data: Lead preferences and profile
            lifestyle_scores: Optional lifestyle compatibility scores
            style: Narrative style preference
            length: Desired narrative length
            conversation_history: Previous interactions for context

        Returns:
            PersonalizedNarrative with compelling lifestyle story
        """
        start_time = time.time()
        property_id = property_data.get("id", "unknown")
        lead_id = lead_data.get("lead_id", "unknown")

        logger.info(f"Generating narrative for property {property_id} and lead {lead_id}")

        try:
            # Check cache first if enabled
            cached_narrative = None
            if self.enable_caching and self.cache_service:
                cached_narrative = await self._get_cached_narrative(
                    property_data, lead_data, lifestyle_scores, style, length
                )

            if cached_narrative:
                self._cache_hits += 1
                logger.info(f"Cache hit for property {property_id}")
                return cached_narrative

            # Generate new narrative
            self._generation_count += 1
            narrative = await self._generate_new_narrative(
                property_data, lead_data, lifestyle_scores, style, length, conversation_history
            )

            # Cache the result if enabled
            if self.enable_caching and self.cache_service and not narrative.fallback_used:
                await self._cache_narrative(property_data, lead_data, lifestyle_scores, style, length, narrative)

            # Track analytics
            await self._track_narrative_generation(narrative, property_data, lead_data)

            generation_time = int((time.time() - start_time) * 1000)
            narrative.generation_time_ms = generation_time

            logger.info(f"Generated narrative in {generation_time}ms for property {property_id}")
            return narrative

        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            # Return fallback narrative on error
            self._fallback_count += 1
            return await self._generate_fallback_narrative(property_data, lead_data, style, length)

    async def generate_batch_narratives(
        self,
        property_lead_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
        style: NarrativeStyle = NarrativeStyle.EMOTIONAL,
        length: NarrativeLength = NarrativeLength.MEDIUM,
        max_concurrent: int = 5,
    ) -> List[PersonalizedNarrative]:
        """
        Generate narratives for multiple property-lead combinations in parallel.

        Optimized for property search results where multiple narratives needed.

        Args:
            property_lead_pairs: List of (property_data, lead_data) tuples
            style: Narrative style for all narratives
            length: Narrative length for all narratives
            max_concurrent: Maximum concurrent generations

        Returns:
            List of PersonalizedNarrative objects
        """
        logger.info(f"Generating batch narratives for {len(property_lead_pairs)} pairs")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(property_data, lead_data):
            async with semaphore:
                return await self.generate_personalized_narrative(property_data, lead_data, None, style, length)

        tasks = [generate_with_semaphore(prop_data, lead_data) for prop_data, lead_data in property_lead_pairs]

        return await asyncio.gather(*tasks, return_exceptions=False)

    async def _generate_new_narrative(
        self,
        property_data: Dict[str, Any],
        lead_data: Dict[str, Any],
        lifestyle_scores: Optional[LifestyleScores],
        style: NarrativeStyle,
        length: NarrativeLength,
        conversation_history: Optional[List[Dict[str, Any]]],
    ) -> PersonalizedNarrative:
        """Generate a new narrative using Claude AI."""

        try:
            # Build enhanced prompt for Claude
            prompt = self._build_narrative_prompt(
                property_data, lead_data, lifestyle_scores, style, length, conversation_history
            )

            # Generate with Claude using appropriate temperature for creativity
            temperature = 0.8  # Higher temperature for creative storytelling
            max_tokens = self._get_max_tokens_for_length(length)

            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt=self._get_system_prompt(style),
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Parse and structure the response
            narrative = self._parse_claude_response(response, property_data, lead_data, style, length)

            return narrative

        except Exception as e:
            logger.warning(f"Claude generation failed: {e}, falling back to template")
            self._fallback_count += 1
            return await self._generate_fallback_narrative(property_data, lead_data, style, length)

    def _build_narrative_prompt(
        self,
        property_data: Dict[str, Any],
        lead_data: Dict[str, Any],
        lifestyle_scores: Optional[LifestyleScores],
        style: NarrativeStyle,
        length: NarrativeLength,
        conversation_history: Optional[List[Dict[str, Any]]],
    ) -> str:
        """Build sophisticated prompt for Claude narrative generation."""

        # Extract key property details
        address = property_data.get("address", "this beautiful property")
        price = property_data.get("price", 0)
        bedrooms = property_data.get("bedrooms", 0)
        bathrooms = property_data.get("bathrooms", 0)
        sqft = property_data.get("sqft", 0)
        neighborhood = property_data.get("neighborhood", "a desirable area")

        # Extract lead preferences and profile
        lead_name = lead_data.get("lead_name", "you")
        family_status = lead_data.get("family_status", "unknown")
        workplace = lead_data.get("workplace", "")
        budget_max = lead_data.get("budget_max", 0)
        lifestyle_priorities = lead_data.get("lifestyle_priorities", [])

        # Build context for lifestyle scores
        lifestyle_context = ""
        if lifestyle_scores:
            lifestyle_context = f"""
LIFESTYLE COMPATIBILITY ANALYSIS:
- School Quality Score: {lifestyle_scores.schools.overall_score:.1f}/10 ({lifestyle_scores.schools.reasoning})
- Commute Score: {lifestyle_scores.commute.overall_score:.1f}/10 ({lifestyle_scores.commute.reasoning})
- Walkability Score: {lifestyle_scores.walkability.overall_score:.1f}/10 ({lifestyle_scores.walkability.reasoning})
- Safety Score: {lifestyle_scores.safety.overall_score:.1f}/10 ({lifestyle_scores.safety.reasoning})
- Overall Lifestyle Match: {lifestyle_scores.overall_score:.1f}/10
"""

        # Add conversation context
        history_context = ""
        if conversation_history:
            recent_interactions = conversation_history[-3:]  # Last 3 interactions
            history_context = f"""
CONVERSATION CONTEXT:
{chr(10).join([f"- {msg.get('content', '')[:100]}..." for msg in recent_interactions])}
"""

        # Style-specific instructions
        style_instructions = {
            NarrativeStyle.EMOTIONAL: "Focus on emotional connections, family moments, and life experiences. Use vivid imagery and personal touches.",
            NarrativeStyle.PROFESSIONAL: "Emphasize practical benefits, ROI, and strategic advantages. Professional tone with concrete benefits.",
            NarrativeStyle.INVESTMENT: "Highlight investment potential, market appreciation, rental income opportunities, and financial returns.",
            NarrativeStyle.LUXURY: "Showcase premium features, exclusivity, and elevated lifestyle experiences. Sophisticated tone.",
            NarrativeStyle.LIFESTYLE: "Paint a picture of daily life, recreation, and personal fulfillment. Focus on experiences.",
        }

        # Length specifications
        length_specs = {
            NarrativeLength.SHORT: "100-150 words for quick summary or SMS",
            NarrativeLength.MEDIUM: "200-300 words for email or detailed preview",
            NarrativeLength.LONG: "400-500 words for comprehensive presentation",
        }

        return f"""
Create a compelling, personalized property narrative that transforms this listing into an emotional lifestyle story.

PROPERTY DETAILS:
Address: {address}
Price: ${price:,}
{bedrooms} bedrooms, {bathrooms} bathrooms, {sqft:,} sq ft
Neighborhood: {neighborhood}

BUYER PROFILE:
Name: {lead_name}
Family Status: {family_status}
Workplace: {workplace}
Budget: Up to ${budget_max:,}
Priorities: {", ".join(lifestyle_priorities)}

{lifestyle_context}

{history_context}

NARRATIVE REQUIREMENTS:
Style: {style.value} - {style_instructions.get(style, "")}
Length: {length_specs.get(length, "")}

INSTRUCTIONS:
1. Start with an attention-grabbing opening that makes this property feel special
2. Weave in specific lifestyle benefits based on the buyer's profile and priorities
3. Use the lifestyle scores to highlight the strongest compatibility factors
4. Include specific neighborhood details and nearby amenities
5. Paint a picture of daily life in this home
6. End with a compelling call-to-action
7. Use "you" and "your" to make it personal and immediate
8. Include subtle urgency based on market conditions
9. Avoid generic real estate language - be creative and specific

Generate ONLY the narrative text - no headers, bullet points, or additional formatting.
"""

    def _get_system_prompt(self, style: NarrativeStyle) -> str:
        """Get system prompt based on narrative style."""

        base_prompt = """You are an expert real estate storyteller who transforms property listings into compelling lifestyle narratives. You understand buyer psychology and create emotional connections between people and properties."""

        style_additions = {
            NarrativeStyle.EMOTIONAL: " Focus on family moments, emotional connections, and life experiences that resonate deeply.",
            NarrativeStyle.PROFESSIONAL: " Emphasize practical benefits, efficiency, and strategic advantages for busy professionals.",
            NarrativeStyle.INVESTMENT: " Highlight financial opportunities, market trends, and ROI potential for savvy investors.",
            NarrativeStyle.LUXURY: " Showcase premium features, exclusivity, and elevated experiences for discerning buyers.",
            NarrativeStyle.LIFESTYLE: " Paint vivid pictures of daily life, recreation, and personal fulfillment.",
        }

        return base_prompt + style_additions.get(style, "")

    def _get_max_tokens_for_length(self, length: NarrativeLength) -> int:
        """Get appropriate token limit for narrative length."""
        return {NarrativeLength.SHORT: 200, NarrativeLength.MEDIUM: 400, NarrativeLength.LONG: 600}.get(length, 400)

    def _parse_claude_response(
        self,
        response,
        property_data: Dict[str, Any],
        lead_data: Dict[str, Any],
        style: NarrativeStyle,
        length: NarrativeLength,
    ) -> PersonalizedNarrative:
        """Parse Claude's response into structured narrative."""

        narrative_text = response.content.strip()

        # Extract key elements from the narrative (simple keyword analysis)
        emotional_themes = []
        key_selling_points = []

        # Identify emotional themes
        emotion_keywords = {
            "family": ["family", "children", "kids", "home", "memories"],
            "security": ["safe", "secure", "peaceful", "quiet"],
            "luxury": ["luxury", "premium", "elegant", "sophisticated"],
            "convenience": ["convenient", "easy", "accessible", "nearby"],
            "investment": ["appreciate", "value", "investment", "return"],
        }

        text_lower = narrative_text.lower()
        for theme, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                emotional_themes.append(theme)

        # Extract selling points (first sentence often contains key points)
        sentences = narrative_text.split(".")[:3]  # First 3 sentences
        key_selling_points = [s.strip() for s in sentences if len(s.strip()) > 10]

        # Generate call-to-action based on style
        cta_templates = {
            NarrativeStyle.EMOTIONAL: "Schedule a tour today and imagine your family's future here.",
            NarrativeStyle.PROFESSIONAL: "Let's arrange a viewing that fits your schedule.",
            NarrativeStyle.INVESTMENT: "Contact me to discuss the investment potential.",
            NarrativeStyle.LUXURY: "Request a private showing to experience this exceptional property.",
            NarrativeStyle.LIFESTYLE: "Come see how this home can transform your daily life.",
        }

        return PersonalizedNarrative(
            property_id=property_data.get("id", "unknown"),
            lead_id=lead_data.get("lead_id", "unknown"),
            narrative_text=narrative_text,
            style=style,
            length=length,
            overall_appeal_score=0.85,  # Could be calculated from lifestyle scores
            key_selling_points=key_selling_points,
            emotional_themes=emotional_themes,
            call_to_action=cta_templates.get(style, "Let's schedule a tour today."),
            model_used=self.llm_client.model,
            cached=False,
            fallback_used=False,
        )

    async def _generate_fallback_narrative(
        self, property_data: Dict[str, Any], lead_data: Dict[str, Any], style: NarrativeStyle, length: NarrativeLength
    ) -> PersonalizedNarrative:
        """Generate fallback narrative using templates when Claude unavailable."""

        logger.info("Using fallback narrative template")

        # Extract key data
        address = property_data.get("address", "this beautiful property")
        price = property_data.get("price", 0)
        bedrooms = property_data.get("bedrooms", 0)
        bathrooms = property_data.get("bathrooms", 0)
        neighborhood = property_data.get("neighborhood", "a desirable neighborhood")
        lead_data.get("lead_name", "you")

        # Template-based narratives by style
        templates = {
            NarrativeStyle.EMOTIONAL: f"Imagine calling {address} home. This stunning {bedrooms}-bedroom, {bathrooms}-bathroom property in {neighborhood} offers the perfect setting for your family's next chapter. With its thoughtful layout and prime location, this home provides everything you need for comfortable living. From morning coffee in the kitchen to evening gatherings in the living spaces, every moment here feels special. The neighborhood offers excellent schools, parks, and amenities that make daily life easier and more enjoyable. At ${price:,}, this represents an incredible opportunity to create lasting memories. Don't let this special property slip away - schedule your tour today and experience what could be your family's forever home.",
            NarrativeStyle.PROFESSIONAL: f"Located at {address}, this {bedrooms}-bedroom property in {neighborhood} delivers the perfect balance of location, value, and convenience for today's busy professional. Priced at ${price:,}, it offers excellent value in one of the area's most sought-after communities. The efficient floor plan maximizes space while maintaining the quality finishes you expect. Strategic location provides easy access to major employers, highways, and urban amenities. This property represents a smart investment in your lifestyle and financial future. Properties like this in {neighborhood} are moving quickly in today's market. Contact me to arrange a viewing and secure your place in this thriving community.",
            NarrativeStyle.INVESTMENT: f"This {bedrooms}-bedroom property at {address} presents a compelling investment opportunity in the growing {neighborhood} market. At ${price:,}, the numbers work exceptionally well for both appreciation potential and rental income generation. The area has shown consistent growth patterns, with properties appreciating steadily over the past several years. Strong rental demand from local professionals ensures excellent cash flow potential. The property's condition and location position it perfectly for long-term value creation. Market indicators suggest continued growth in this corridor, making this an ideal addition to any real estate portfolio. Schedule your investment analysis today.",
            NarrativeStyle.LUXURY: f"Discover refined living at {address}, where {bedrooms} bedrooms and {bathrooms} bathrooms create an atmosphere of sophisticated comfort in prestigious {neighborhood}. This exceptional property offers the discerning buyer an opportunity to experience elevated living in one of the area's most coveted locations. Every detail reflects quality and attention to design, from the carefully planned layouts to the premium finishes throughout. The neighborhood's reputation for excellence extends to its amenities, schools, and community atmosphere. At ${price:,}, this represents exclusive value in the luxury market. Properties of this caliber are rare opportunities - arrange your private showing today.",
            NarrativeStyle.LIFESTYLE: f"Picture your ideal daily routine unfolding at {address}. This {bedrooms}-bedroom home in vibrant {neighborhood} becomes the backdrop for the lifestyle you've been seeking. Morning walks through tree-lined streets, afternoon trips to nearby cafes and parks, evening gatherings with neighbors who become friends. The home's {bathrooms} bathrooms and thoughtful spaces accommodate both quiet moments and social celebrations. {neighborhood} offers the perfect blend of community feel and urban convenience. Local amenities, restaurants, and recreational opportunities are all within reach. At ${price:,}, this is more than a home purchase - it's an investment in the lifestyle you deserve. Come experience the difference this community can make in your daily life.",
        }

        narrative_text = templates.get(style, templates[NarrativeStyle.EMOTIONAL])

        # Trim for length if needed
        if length == NarrativeLength.SHORT:
            sentences = narrative_text.split(".")[:3]  # First 3 sentences
            narrative_text = ". ".join(sentences) + "."
        elif length == NarrativeLength.LONG:
            # Template is already medium-long, suitable for LONG
            pass

        return PersonalizedNarrative(
            property_id=property_data.get("id", "unknown"),
            lead_id=lead_data.get("lead_id", "unknown"),
            narrative_text=narrative_text,
            style=style,
            length=length,
            overall_appeal_score=0.75,  # Lower score for template
            key_selling_points=[f"{bedrooms} bedrooms", f"{neighborhood} location", f"${price:,} value"],
            emotional_themes=["home", "community", "value"],
            call_to_action="Schedule your tour today and see the difference for yourself.",
            model_used="template",
            cached=False,
            fallback_used=True,
        )

    async def _get_cached_narrative(
        self,
        property_data: Dict[str, Any],
        lead_data: Dict[str, Any],
        lifestyle_scores: Optional[LifestyleScores],
        style: NarrativeStyle,
        length: NarrativeLength,
    ) -> Optional[PersonalizedNarrative]:
        """Check cache for existing narrative."""

        if not self.cache_service:
            return None

        cache_key = self._build_cache_key(property_data, lead_data, lifestyle_scores, style, length)
        cached_data = await self.cache_service.get(cache_key)

        if cached_data:
            logger.debug(f"Cache hit for key: {cache_key}")
            # Deserialize and mark as cached
            narrative = cached_data
            narrative.cached = True
            return narrative

        return None

    async def _cache_narrative(
        self,
        property_data: Dict[str, Any],
        lead_data: Dict[str, Any],
        lifestyle_scores: Optional[LifestyleScores],
        style: NarrativeStyle,
        length: NarrativeLength,
        narrative: PersonalizedNarrative,
    ) -> None:
        """Cache generated narrative with 24-hour TTL."""

        if not self.cache_service:
            return

        cache_key = self._build_cache_key(property_data, lead_data, lifestyle_scores, style, length)
        ttl = 24 * 60 * 60  # 24 hours in seconds

        try:
            await self.cache_service.set(cache_key, narrative, ttl)
            logger.debug(f"Cached narrative with key: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache narrative: {e}")

    def _build_cache_key(
        self,
        property_data: Dict[str, Any],
        lead_data: Dict[str, Any],
        lifestyle_scores: Optional[LifestyleScores],
        style: NarrativeStyle,
        length: NarrativeLength,
    ) -> str:
        """Build cache key from input parameters."""

        # Create hash from key data
        property_id = property_data.get("id", "unknown")
        lead_id = lead_data.get("lead_id", "unknown")

        # Include lifestyle scores hash if available
        lifestyle_hash = ""
        if lifestyle_scores:
            lifestyle_data = f"{lifestyle_scores.overall_score}_{lifestyle_scores.schools.overall_score}_{lifestyle_scores.commute.overall_score}"
            lifestyle_hash = hashlib.md5(lifestyle_data.encode()).hexdigest()[:8]

        # Include key lead preferences
        preferences_data = str(lead_data.get("lifestyle_priorities", []) + [lead_data.get("family_status", "")])
        preferences_hash = hashlib.md5(preferences_data.encode()).hexdigest()[:8]

        cache_key = (
            f"narrative_{property_id}_{lead_id}_{lifestyle_hash}_{preferences_hash}_{style.value}_{length.value}"
        )
        return cache_key

    async def _track_narrative_generation(
        self, narrative: PersonalizedNarrative, property_data: Dict[str, Any], lead_data: Dict[str, Any]
    ) -> None:
        """Track narrative generation for analytics."""

        location_id = lead_data.get("location_id", "demo_location")

        await self.analytics.track_event(
            event_type="narrative_generated",
            location_id=location_id,
            contact_id=narrative.lead_id,
            data={
                "property_id": narrative.property_id,
                "style": narrative.style.value,
                "length": narrative.length.value,
                "generation_time_ms": narrative.generation_time_ms,
                "model_used": narrative.model_used,
                "cached": narrative.cached,
                "fallback_used": narrative.fallback_used,
                "narrative_length": len(narrative.narrative_text),
                "appeal_score": narrative.overall_appeal_score,
                "emotional_themes": narrative.emotional_themes,
            },
        )

        # Track LLM usage if Claude was used
        if not narrative.cached and not narrative.fallback_used:
            # Estimate token usage (rough approximation)
            estimated_input_tokens = (
                len(
                    self._build_narrative_prompt(
                        property_data, lead_data, None, narrative.style, narrative.length, None
                    ).split()
                )
                * 1.3
            )  # Rough token estimation
            estimated_output_tokens = len(narrative.narrative_text.split()) * 1.3

            await self.analytics.track_llm_usage(
                location_id=location_id,
                model=narrative.model_used,
                provider="claude",
                input_tokens=int(estimated_input_tokens),
                output_tokens=int(estimated_output_tokens),
                cached=False,
                contact_id=narrative.lead_id,
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics."""

        cache_hit_rate = (self._cache_hits / max(1, self._generation_count + self._cache_hits)) * 100
        fallback_rate = (self._fallback_count / max(1, self._generation_count)) * 100

        return {
            "total_generations": self._generation_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate_percent": cache_hit_rate,
            "fallback_count": self._fallback_count,
            "fallback_rate_percent": fallback_rate,
            "cache_enabled": self.enable_caching,
        }


# Factory function for easy access
def get_narrative_engine() -> PersonalizedNarrativeEngine:
    """Get a PersonalizedNarrativeEngine instance."""
    return PersonalizedNarrativeEngine()
