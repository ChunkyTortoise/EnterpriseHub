"""
Claude Semantic Property Matcher - Advanced AI-Powered Property Matching
Provides lifestyle-based matching using behavioral psychology and Claude AI.
"""
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import streamlit as st

# Import existing services
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.services.claude_conversation_intelligence import get_conversation_intelligence
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PropertyMatch:
    """Enhanced property match with semantic analysis."""
    property: Dict[str, Any]
    match_score: float  # 0.0-1.0
    lifestyle_fit: float  # 0.0-1.0
    psychological_appeal: str
    reasoning: str
    objection_predictions: List[str]
    presentation_strategy: str
    viewing_probability: float

@dataclass
class LifestyleProfile:
    """Detailed lifestyle profile extracted from lead behavior."""
    personality_type: str  # "analytical", "emotional", "social", "practical"
    life_stage: str  # "young_professional", "growing_family", "empty_nester", "retiree"
    priorities: Dict[str, float]  # {"status": 0.8, "convenience": 0.6, ...}
    hidden_desires: List[str]
    future_planning: Dict[str, Any]
    decision_style: str  # "thorough", "quick", "collaborative", "delegated"

class ClaudeSemanticPropertyMatcher:
    """
    Advanced property matching using Claude AI for behavioral psychology
    and lifestyle analysis.
    """

    def __init__(self):
        self.base_matcher = PropertyMatcher()
        self.conversation_intelligence = get_conversation_intelligence()
        self.lifestyle_cache = {}  # Cache lifestyle profiles
        self.cache_ttl = timedelta(hours=2)  # Cache for 2 hours

        # Initialize Claude client
        try:
            from ghl_real_estate_ai.core.llm_client import LLMClient
            from ghl_real_estate_ai.ghl_utils.config import settings

            self.claude_client = LLMClient(
                provider="claude",
                model=settings.claude_model
            )
            self.enabled = True
            logger.info("ClaudeSemanticPropertyMatcher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            self.claude_client = None
            self.enabled = False

    async def find_lifestyle_matches(self, lead_profile: Dict, properties: List[Dict] = None, limit: int = 5) -> List[PropertyMatch]:
        """
        Claude-powered lifestyle matching beyond basic filters.

        Args:
            lead_profile: Complete lead profile with preferences and behavior
            properties: Available properties (uses cached if None)
            limit: Maximum number of matches to return

        Returns:
            List of PropertyMatch objects with detailed analysis
        """
        if not self.enabled:
            return self._get_fallback_matches(lead_profile, properties, limit)

        try:
            # Get properties from base matcher if not provided
            if properties is None:
                properties = self.base_matcher.listings

            if not properties:
                logger.warning("No properties available for matching")
                return []

            # Extract or retrieve lifestyle profile
            lifestyle_profile = await self._extract_lifestyle_profile(lead_profile)

            # Perform semantic matching for each property
            matches = []
            for property_data in properties:
                match = await self._analyze_property_match(property_data, lead_profile, lifestyle_profile)
                if match and match.match_score >= 0.3:  # Threshold for meaningful matches
                    matches.append(match)

            # Sort by combined score (match + lifestyle + psychology)
            matches.sort(key=lambda m: (m.match_score * 0.4 + m.lifestyle_fit * 0.4 + m.viewing_probability * 0.2), reverse=True)

            logger.info(f"Generated {len(matches)} lifestyle matches for {lead_profile.get('lead_id', 'unknown')}")
            return matches[:limit]

        except Exception as e:
            logger.error(f"Error in lifestyle matching: {e}")
            return self._get_fallback_matches(lead_profile, properties, limit)

    async def generate_personalized_presentation(self, property: Dict, lead: Dict, match_analysis: PropertyMatch = None) -> Dict:
        """
        Create personalized property presentations with Claude.

        Args:
            property: Property details
            lead: Lead profile
            match_analysis: Previous match analysis (optional)

        Returns:
            Personalized presentation strategy
        """
        if not self.enabled:
            return self._get_fallback_presentation(property, lead)

        try:
            presentation_prompt = self._build_presentation_prompt(property, lead, match_analysis)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": presentation_prompt}],
                temperature=0.6  # Balanced creativity and consistency
            )

            presentation = self._parse_presentation_response(response.content)
            logger.info(f"Generated personalized presentation for property {property.get('address', 'unknown')}")

            return presentation

        except Exception as e:
            logger.error(f"Error generating presentation: {e}")
            return self._get_fallback_presentation(property, lead)

    async def predict_viewing_interest(self, lead_behavior: Dict, property: Dict) -> float:
        """
        Predict likelihood of viewing request using behavioral analysis.

        Args:
            lead_behavior: Lead's interaction patterns and behavior
            property: Property details

        Returns:
            Viewing probability (0.0-1.0)
        """
        if not self.enabled:
            return 0.6  # Default moderate interest

        try:
            prediction_prompt = self._build_viewing_prediction_prompt(lead_behavior, property)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": prediction_prompt}],
                temperature=0.3  # Lower temperature for consistent predictions
            )

            prediction = self._parse_viewing_prediction(response.content)
            return max(0.0, min(1.0, prediction))  # Ensure 0-1 range

        except Exception as e:
            logger.error(f"Error predicting viewing interest: {e}")
            return 0.6

    async def _extract_lifestyle_profile(self, lead_profile: Dict) -> LifestyleProfile:
        """Extract detailed lifestyle profile using Claude analysis."""
        lead_id = lead_profile.get('lead_id', 'unknown')

        # Check cache first
        if lead_id in self.lifestyle_cache:
            cached_profile, timestamp = self.lifestyle_cache[lead_id]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_profile

        if not self.enabled:
            return self._get_fallback_lifestyle_profile()

        try:
            lifestyle_prompt = self._build_lifestyle_analysis_prompt(lead_profile)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": lifestyle_prompt}],
                temperature=0.4
            )

            lifestyle_profile = self._parse_lifestyle_profile(response.content)

            # Cache the result
            self.lifestyle_cache[lead_id] = (lifestyle_profile, datetime.now())

            logger.info(f"Extracted lifestyle profile: {lifestyle_profile.personality_type}, {lifestyle_profile.life_stage}")
            return lifestyle_profile

        except Exception as e:
            logger.error(f"Error extracting lifestyle profile: {e}")
            return self._get_fallback_lifestyle_profile()

    async def _analyze_property_match(self, property_data: Dict, lead_profile: Dict, lifestyle_profile: LifestyleProfile) -> PropertyMatch:
        """Analyze individual property match with psychological insights."""
        try:
            match_prompt = self._build_property_match_prompt(property_data, lead_profile, lifestyle_profile)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": match_prompt}],
                temperature=0.5
            )

            match_data = self._parse_property_match_response(response.content)

            return PropertyMatch(
                property=property_data,
                match_score=float(match_data.get('match_score', 0.5)),
                lifestyle_fit=float(match_data.get('lifestyle_fit', 0.5)),
                psychological_appeal=match_data.get('psychological_appeal', 'Standard appeal'),
                reasoning=match_data.get('reasoning', 'Basic feature matching'),
                objection_predictions=match_data.get('objection_predictions', []),
                presentation_strategy=match_data.get('presentation_strategy', 'Standard presentation'),
                viewing_probability=float(match_data.get('viewing_probability', 0.5))
            )

        except Exception as e:
            logger.error(f"Error analyzing property match: {e}")
            return self._get_fallback_property_match(property_data)

    def _build_lifestyle_analysis_prompt(self, lead_profile: Dict) -> str:
        """Build prompt for enhanced 16+ lifestyle dimension analysis."""
        return f"""
As a real estate psychology expert, analyze this lead profile to understand their lifestyle and hidden motivations using our enhanced 16+ dimensional lifestyle framework.

Lead Profile:
{json.dumps(lead_profile, indent=2)}

Extract detailed lifestyle insights in JSON format using our ENHANCED 16+ LIFESTYLE DIMENSIONS model:
{{
    "personality_type": "analytical|emotional|social|practical|hybrid",
    "life_stage": "young_professional|growing_family|established_family|empty_nester|retiree|first_time_buyer|transitioning",
    "enhanced_lifestyle_priorities": {{
        // Core Dimensions (Original 8)
        "status": float (0.0-1.0, importance of status and prestige),
        "convenience": float (0.0-1.0, importance of convenience and accessibility),
        "security": float (0.0-1.0, importance of safety and stability),
        "investment": float (0.0-1.0, importance of financial return),
        "family": float (0.0-1.0, importance of family considerations),
        "career": float (0.0-1.0, importance of career proximity),
        "lifestyle": float (0.0-1.0, importance of lifestyle amenities),
        "privacy": float (0.0-1.0, importance of privacy and space),

        // Enhanced Dimensions (8+ New)
        "social_connectivity": float (0.0-1.0, importance of community and neighbors),
        "cultural_fit": float (0.0-1.0, cultural and demographic alignment),
        "commute_optimization": float (0.0-1.0, transportation and accessibility needs),
        "future_family_planning": float (0.0-1.0, family growth considerations),
        "aging_in_place": float (0.0-1.0, long-term living considerations),
        "investment_mindset": float (0.0-1.0, investment vs personal use focus),
        "environmental_values": float (0.0-1.0, sustainability and green living),
        "technology_integration": float (0.0-1.0, smart home and tech preferences),
        "health_wellness": float (0.0-1.0, health-conscious living priorities),
        "work_life_balance": float (0.0-1.0, home as sanctuary vs productivity),
        "aesthetic_appreciation": float (0.0-1.0, design and beauty importance),
        "community_involvement": float (0.0-1.0, local engagement and activism),
        "educational_priorities": float (0.0-1.0, learning and school district focus),
        "entertainment_hosting": float (0.0-1.0, social gathering and hosting needs),
        "outdoor_recreation": float (0.0-1.0, outdoor activities and nature access),
        "cultural_access": float (0.0-1.0, arts, dining, and cultural amenities)
    }},
    "life_transition_indicators": {{
        "career_stage": "entry|growth|peak|transition|retirement",
        "relationship_status": "single|coupled|married|divorced|widowed",
        "family_dynamics": "planning|expanding|stable|launching|empty",
        "financial_trajectory": "building|accumulating|preserving|distributing",
        "housing_evolution": "upgrading|rightsizing|downsizing|relocating",
        "health_considerations": "none|planning|active|critical"
    }},
    "psychological_motivators": {{
        "primary_driver": "achievement|security|belonging|autonomy|legacy",
        "stress_factors": [list of current life stressors affecting housing decisions],
        "aspiration_themes": [list of future-focused motivations],
        "fear_factors": [list of concerns or anxieties about housing decisions],
        "validation_needs": [what they need to feel confident in their choice]
    }},
    "investment_psychology_profile": {{
        "investment_sophistication": "beginner|intermediate|advanced|expert",
        "risk_appetite": "conservative|balanced|growth|aggressive",
        "time_horizon": "short_term|medium_term|long_term|generational",
        "portfolio_role": "primary_residence|investment_property|mixed_use|diversification",
        "market_timing_beliefs": "timing_important|time_in_market|value_focused|opportunity_driven"
    }},
    "neighborhood_compatibility_factors": {{
        "demographic_preferences": "diverse|similar_age|similar_income|similar_lifestyle",
        "social_interaction_level": "private|selective|social|community_leader",
        "political_alignment": "progressive|moderate|conservative|apolitical",
        "lifestyle_pace": "urban_energy|suburban_balance|rural_tranquility",
        "change_tolerance": "loves_new_development|accepts_growth|prefers_established|resists_change"
    }},
    "hidden_desires": [list of unstated wants and aspirations],
    "future_planning": {{
        "family_growth": "planning|stable|downsizing",
        "career_trajectory": "advancing|stable|retiring",
        "financial_goals": "wealth_building|stability|preservation",
        "lifestyle_evolution": "upgrading|maintaining|simplifying",
        "geographic_flexibility": "location_bound|willing_to_relocate|actively_seeking_change",
        "housing_permanence": "temporary|medium_term|long_term|forever_home"
    }},
    "decision_style": "thorough|quick|collaborative|delegated|consensus_driven",
    "communication_preferences": "data_driven|story_focused|visual|social_proof|experiential",
    "risk_tolerance": "conservative|moderate|aggressive|calculated_risk_taker",
    "timeline_flexibility": "rigid|moderate|flexible|opportunity_driven",
    "budget_sensitivity": "price_focused|value_focused|luxury_focused|investment_focused"
}}

IMPORTANT: Analyze each lifestyle dimension carefully. Look for:
- Explicit preferences and stated needs
- Implicit psychological motivations and life stage indicators
- Hidden needs beyond stated preferences
- Life transition signals and future planning indicators
- Investment vs personal use psychological separation
- Neighborhood and community fit factors
- Long-term lifestyle compatibility considerations
"""

    def _build_property_match_prompt(self, property_data: Dict, lead_profile: Dict, lifestyle_profile: LifestyleProfile) -> str:
        """Build prompt for property-specific match analysis."""
        return f"""
As a real estate psychology expert, analyze how well this property matches the lead's psychological profile.

Property Details:
{json.dumps(property_data, indent=2)}

Lead Profile:
{json.dumps(lead_profile, indent=2)}

Lifestyle Analysis:
- Personality: {lifestyle_profile.personality_type}
- Life Stage: {lifestyle_profile.life_stage}
- Decision Style: {lifestyle_profile.decision_style}
- Key Priorities: {lifestyle_profile.priorities}

Provide detailed matching analysis in JSON format:
{{
    "match_score": float (0.0-1.0, overall compatibility),
    "lifestyle_fit": float (0.0-1.0, how well it fits their lifestyle),
    "psychological_appeal": "Brief description of main psychological appeal",
    "reasoning": "Detailed explanation of why this property matches their psychology",
    "objection_predictions": [list of likely objections they might have],
    "presentation_strategy": "How to present this property to maximize appeal",
    "viewing_probability": float (0.0-1.0, likelihood they'll want to view it),
    "emotional_triggers": [list of emotional factors that will resonate],
    "logical_benefits": [list of rational reasons they'll appreciate],
    "lifestyle_enhancements": [how this property improves their lifestyle],
    "future_suitability": "How this property fits their future plans",
    "competitive_advantages": "What makes this better than alternatives"
}}

Consider:
- Psychological fit with personality type and life stage
- Alignment with stated and unstated priorities
- Potential objections and how to address them
- Emotional and logical appeal factors
- Long-term lifestyle compatibility
"""

    def _build_presentation_prompt(self, property: Dict, lead: Dict, match_analysis: PropertyMatch = None) -> str:
        """Build prompt for personalized presentation strategy."""
        match_context = ""
        if match_analysis:
            match_context = f"""
Previous Match Analysis:
- Match Score: {match_analysis.match_score:.2f}
- Lifestyle Fit: {match_analysis.lifestyle_fit:.2f}
- Psychological Appeal: {match_analysis.psychological_appeal}
- Predicted Objections: {match_analysis.objection_predictions}
"""

        return f"""
Create a personalized property presentation strategy for this lead.

Property:
{json.dumps(property, indent=2)}

Lead Profile:
{json.dumps(lead, indent=2)}
{match_context}

Generate presentation strategy in JSON format:
{{
    "opening_hook": "Compelling opening statement that captures attention",
    "key_selling_points": [ordered list of most relevant benefits],
    "visual_focus_areas": [which aspects to highlight in photos/tours],
    "story_narrative": "Brief story connecting property to their lifestyle",
    "objection_preemption": [how to address potential concerns proactively],
    "logical_arguments": [rational reasons why this property makes sense],
    "emotional_appeals": [emotional benefits that will resonate],
    "comparison_positioning": "How to position vs. alternatives",
    "urgency_factors": [legitimate reasons to act quickly],
    "follow_up_strategy": "How to maintain interest after initial presentation",
    "personalization_elements": [specific details that show you understand them],
    "next_steps": "Natural progression to viewing or next conversation"
}}

Focus on their psychological profile, communication style, and decision-making preferences.
"""

    def _build_viewing_prediction_prompt(self, lead_behavior: Dict, property: Dict) -> str:
        """Build prompt for viewing probability prediction."""
        return f"""
Predict the likelihood this lead will request a property viewing based on their behavior.

Lead Behavior Patterns:
{json.dumps(lead_behavior, indent=2)}

Property Details:
{json.dumps(property, indent=2)}

Analyze viewing probability considering:
- Engagement patterns and response history
- Property alignment with stated preferences
- Timeline urgency and decision-making stage
- Previous viewing requests and patterns
- Current market behavior and competition

Return a single float value between 0.0 and 1.0 representing viewing probability.

Consider factors like:
- How closely the property matches their criteria
- Their current engagement level and responsiveness
- Timeline urgency and decision stage
- Past behavior patterns with similar properties
- Market conditions and competitive pressure

Provide just the probability score (e.g., 0.73) with brief reasoning.
"""

    def _parse_lifestyle_profile(self, response_content: str) -> LifestyleProfile:
        """Parse Claude's lifestyle analysis response."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = self._extract_fallback_lifestyle_data(response_content)

            return LifestyleProfile(
                personality_type=data.get('personality_type', 'analytical'),
                life_stage=data.get('life_stage', 'young_professional'),
                priorities=data.get('priorities', {}),
                hidden_desires=data.get('hidden_desires', []),
                future_planning=data.get('future_planning', {}),
                decision_style=data.get('decision_style', 'thorough')
            )
        except Exception as e:
            logger.error(f"Error parsing lifestyle profile: {e}")
            return self._get_fallback_lifestyle_profile()

    def _parse_property_match_response(self, response_content: str) -> Dict:
        """Parse Claude's property match analysis."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return {
                    "match_score": 0.6,
                    "lifestyle_fit": 0.6,
                    "psychological_appeal": "Good basic fit",
                    "reasoning": "Matches key criteria",
                    "objection_predictions": ["Budget", "Timeline"],
                    "presentation_strategy": "Focus on value and convenience",
                    "viewing_probability": 0.6
                }
        except Exception as e:
            logger.error(f"Error parsing property match: {e}")
            return {"match_score": 0.5, "lifestyle_fit": 0.5, "viewing_probability": 0.5}

    def _parse_presentation_response(self, response_content: str) -> Dict:
        """Parse Claude's presentation strategy response."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "opening_hook": "This property offers excellent value",
                    "key_selling_points": ["Great location", "Updated features"],
                    "story_narrative": "Perfect for your lifestyle",
                    "next_steps": "Schedule a viewing"
                }
        except Exception as e:
            logger.error(f"Error parsing presentation: {e}")
            return self._get_fallback_presentation(None, None)

    def _parse_viewing_prediction(self, response_content: str) -> float:
        """Parse viewing probability from Claude response."""
        try:
            import re
            # Look for float values in the response
            float_match = re.search(r'(0\\.\\d+|1\\.0|0|1)', response_content)
            if float_match:
                return float(float_match.group())
            else:
                return 0.6  # Default moderate probability
        except Exception:
            return 0.6

    def _get_fallback_matches(self, lead_profile: Dict, properties: List[Dict], limit: int) -> List[PropertyMatch]:
        """Get fallback matches when Claude is unavailable."""
        if not properties:
            properties = self.base_matcher.listings

        # Use basic matcher for fallback
        basic_matches = self.base_matcher.find_matches(
            lead_profile.get('extracted_preferences', {}),
            limit=limit
        )

        fallback_matches = []
        for match in basic_matches:
            fallback_matches.append(PropertyMatch(
                property=match,
                match_score=match.get('match_score', 70) / 100.0,
                lifestyle_fit=0.6,
                psychological_appeal="Good basic compatibility",
                reasoning="Matches basic criteria and preferences",
                objection_predictions=["Budget questions", "Timeline concerns"],
                presentation_strategy="Focus on key features and value",
                viewing_probability=0.6
            ))

        return fallback_matches

    def _get_fallback_lifestyle_profile(self) -> LifestyleProfile:
        """Get enhanced fallback lifestyle profile with 16+ dimensions."""
        enhanced_priorities = {
            # Core Dimensions (Original 8)
            "status": 0.4,
            "convenience": 0.7,
            "security": 0.6,
            "investment": 0.5,
            "family": 0.5,
            "career": 0.6,
            "lifestyle": 0.5,
            "privacy": 0.5,

            # Enhanced Dimensions (16+ New)
            "social_connectivity": 0.4,
            "cultural_fit": 0.5,
            "commute_optimization": 0.6,
            "future_family_planning": 0.3,
            "aging_in_place": 0.2,
            "investment_mindset": 0.4,
            "environmental_values": 0.3,
            "technology_integration": 0.5,
            "health_wellness": 0.4,
            "work_life_balance": 0.6,
            "aesthetic_appreciation": 0.4,
            "community_involvement": 0.3,
            "educational_priorities": 0.4,
            "entertainment_hosting": 0.3,
            "outdoor_recreation": 0.4,
            "cultural_access": 0.4
        }

        enhanced_future_planning = {
            "family_growth": "planning",
            "career_trajectory": "advancing",
            "financial_goals": "wealth_building",
            "lifestyle_evolution": "upgrading",
            "geographic_flexibility": "willing_to_relocate",
            "housing_permanence": "medium_term"
        }

        return LifestyleProfile(
            personality_type="analytical",
            life_stage="young_professional",
            priorities=enhanced_priorities,
            hidden_desires=[
                "Status symbol property",
                "Investment growth potential",
                "Professional image enhancement",
                "Future family accommodation",
                "Technology-enabled living"
            ],
            future_planning=enhanced_future_planning,
            decision_style="thorough"
        )

    def _get_fallback_property_match(self, property_data: Dict) -> PropertyMatch:
        """Get fallback property match."""
        return PropertyMatch(
            property=property_data,
            match_score=0.6,
            lifestyle_fit=0.6,
            psychological_appeal="Standard appeal",
            reasoning="Basic feature matching",
            objection_predictions=["Budget", "Location"],
            presentation_strategy="Standard presentation",
            viewing_probability=0.6
        )

    def _get_fallback_presentation(self, property: Dict, lead: Dict) -> Dict:
        """Get fallback presentation strategy."""
        return {
            "opening_hook": "This property offers excellent value for your needs",
            "key_selling_points": ["Great location", "Updated features", "Good value"],
            "story_narrative": "Perfect fit for your lifestyle and budget",
            "logical_arguments": ["Competitive pricing", "Strong neighborhood"],
            "emotional_appeals": ["Comfort", "Security", "Pride of ownership"],
            "next_steps": "Schedule a viewing to see it in person"
        }

    def render_semantic_matching_interface(self, lead_profile: Dict) -> None:
        """
        Render enhanced property matching interface in Streamlit.

        Args:
            lead_profile: Complete lead profile for analysis
        """
        st.markdown("### 🧠 Claude Semantic Property Matching")

        if not lead_profile:
            st.info("Select a lead to see semantic property matching")
            return

        if st.button("🚀 Find Lifestyle Matches", key="semantic_matching"):
            with st.spinner("🔍 Analyzing lifestyle compatibility..."):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Get semantic matches
                matches = loop.run_until_complete(
                    self.find_lifestyle_matches(lead_profile, limit=3)
                )

                if matches:
                    st.success(f"Found {len(matches)} psychologically compatible properties")

                    for i, match in enumerate(matches, 1):
                        with st.expander(f"🏠 Match #{i}: {match.property.get('address', 'Unknown Address')}", expanded=(i == 1)):
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                st.markdown(f"**Price:** ${match.property.get('price', 0):,}")
                                st.markdown(f"**Beds/Baths:** {match.property.get('beds', 0)}BD / {match.property.get('baths', 0)}BA")
                                st.markdown(f"**Sqft:** {match.property.get('sqft', 0):,}")

                            with col2:
                                st.metric("Overall Match", f"{match.match_score:.0%}")
                                st.metric("Lifestyle Fit", f"{match.lifestyle_fit:.0%}")
                                st.metric("Viewing Probability", f"{match.viewing_probability:.0%}")

                            # Psychological insights
                            st.markdown("#### 🎯 Psychological Appeal")
                            st.info(match.psychological_appeal)

                            st.markdown("#### 💭 AI Reasoning")
                            st.write(match.reasoning)

                            if match.objection_predictions:
                                st.markdown("#### ⚠️ Predicted Objections")
                                for objection in match.objection_predictions:
                                    st.markdown(f"- {objection}")

                            st.markdown("#### 📋 Presentation Strategy")
                            st.write(match.presentation_strategy)

                            # Get detailed presentation
                            if st.button(f"📝 Generate Presentation", key=f"presentation_{i}"):
                                with st.spinner("Generating personalized presentation..."):
                                    presentation = loop.run_until_complete(
                                        self.generate_personalized_presentation(
                                            match.property,
                                            lead_profile,
                                            match
                                        )
                                    )

                                    st.markdown("##### 🎣 Opening Hook")
                                    st.success(presentation.get('opening_hook', ''))

                                    st.markdown("##### 🎯 Key Selling Points")
                                    for point in presentation.get('key_selling_points', []):
                                        st.markdown(f"• {point}")

                                    st.markdown("##### 📖 Story Narrative")
                                    st.info(presentation.get('story_narrative', ''))

                else:
                    st.warning("No compatible properties found. Try adjusting search criteria.")

# Global instance for easy access
_semantic_property_matcher = None

def get_semantic_property_matcher() -> ClaudeSemanticPropertyMatcher:
    """Get global semantic property matcher instance."""
    global _semantic_property_matcher
    if _semantic_property_matcher is None:
        _semantic_property_matcher = ClaudeSemanticPropertyMatcher()
    return _semantic_property_matcher