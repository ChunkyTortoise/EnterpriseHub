"""
Property Recommendation Engine with Claude Explanations and Behavioral Learning.

Enhances the basic PropertyMatcher with:
- Claude-powered explanations for property recommendations
- Behavioral learning from property interactions
- Adaptive scoring based on lead preferences and behavior
- Property interaction tracking for personalized recommendations
- Integration with multi-tenant memory system
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

try:
    from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
    from ghl_real_estate_ai.core.llm_client import LLMClient
    from ghl_real_estate_ai.ghl_utils.config import settings
    from ghl_real_estate_ai.ghl_utils.logger import get_logger
except ImportError:
    # Fallback for streamlit demo context
    from services.property_matcher import PropertyMatcher
    from core.llm_client import LLMClient
    from ghl_utils.config import settings
    from ghl_utils.logger import get_logger

logger = get_logger(__name__)


class InteractionType(Enum):
    """Types of property interactions for behavioral learning."""
    VIEW = "view"
    LIKE = "like"
    DISLIKE = "dislike"
    SAVE = "save"
    SHARE = "share"
    BOOK_SHOWING = "book_showing"
    DISMISS = "dismiss"
    DETAILED_VIEW = "detailed_view"


@dataclass
class PropertyInteraction:
    """Represents a property interaction for behavioral learning."""
    property_id: str
    interaction_type: InteractionType
    timestamp: datetime
    duration_seconds: Optional[int] = None
    feedback_text: Optional[str] = None
    property_features: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None


@dataclass
class BehavioralPreference:
    """Learned behavioral preferences from property interactions."""
    preference_type: str  # "price_sensitivity", "location_preference", etc.
    preference_value: Any
    confidence_score: float  # 0.0 to 1.0
    learned_from: List[str]  # Interaction types that contributed
    last_updated: datetime
    weight_multiplier: float = 1.0  # How much to weight this preference


@dataclass
class PropertyMatch:
    """Enhanced property match with Claude explanations."""
    property: Dict[str, Any]
    base_score: float
    behavioral_score: float
    final_score: float
    claude_explanation: str
    reasoning_breakdown: Dict[str, Any]
    behavioral_insights: List[BehavioralPreference]
    recommendation_confidence: float


@dataclass
class PersonalizedRecommendations:
    """Complete personalized property recommendations."""
    recommendations: List[PropertyMatch]
    behavioral_profile: Dict[str, Any]
    learning_metadata: Dict[str, Any]
    explanation_summary: str
    next_learning_opportunities: List[str]


class PropertyRecommendationEngine:
    """
    Claude-enhanced property recommendations with behavioral learning.

    Extends PropertyMatcher with sophisticated AI explanations and
    adaptive scoring based on user behavior patterns.
    """

    def __init__(
        self,
        tenant_id: str,
        property_matcher: Optional[PropertyMatcher] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize property recommendation engine.

        Args:
            tenant_id: Tenant identifier for multi-tenant support
            property_matcher: Optional property matcher instance
            llm_client: Optional LLM client for testing
        """
        self.tenant_id = tenant_id
        self.property_matcher = property_matcher or PropertyMatcher()
        self.llm_client = llm_client or LLMClient(
            provider="claude",
            model=settings.claude_model
        )

        # In-memory storage for behavioral learning (would be database in production)
        self.property_interactions: Dict[str, List[PropertyInteraction]] = {}
        self.behavioral_preferences: Dict[str, List[BehavioralPreference]] = {}

        logger.info(f"Property recommendation engine initialized for tenant {tenant_id}")

    async def generate_personalized_recommendations(
        self,
        contact_id: str,
        extracted_preferences: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]] = None,
        limit: int = 3,
        min_score: float = 0.4
    ) -> PersonalizedRecommendations:
        """
        Generate personalized property recommendations with Claude explanations.

        Args:
            contact_id: Contact identifier for behavioral tracking
            extracted_preferences: Lead's stated preferences
            conversation_context: Optional conversation context
            limit: Maximum number of recommendations
            min_score: Minimum final score threshold

        Returns:
            PersonalizedRecommendations with enhanced matches
        """
        try:
            # 1. Get behavioral profile for this contact
            behavioral_profile = await self._build_behavioral_profile(contact_id)

            # 2. Get base matches from existing property matcher
            base_matches = self.property_matcher.find_matches(
                extracted_preferences,
                limit=limit * 2,  # Get more to apply behavioral filtering
                min_score=0.3  # Lower threshold, we'll filter with behavioral scoring
            )

            if not base_matches:
                return self._empty_recommendations_response()

            # 3. Apply behavioral scoring and filtering
            enhanced_matches = await self._apply_behavioral_scoring(
                base_matches,
                behavioral_profile,
                extracted_preferences
            )

            # 4. Filter by final score and limit
            qualified_matches = [
                match for match in enhanced_matches
                if match.final_score >= min_score
            ][:limit]

            # 5. Generate Claude explanations for top matches
            explained_matches = await self._generate_claude_explanations(
                qualified_matches,
                behavioral_profile,
                extracted_preferences,
                conversation_context
            )

            # 6. Generate overall explanation summary
            explanation_summary = await self._generate_explanation_summary(
                explained_matches,
                behavioral_profile,
                extracted_preferences
            )

            # 7. Identify next learning opportunities
            learning_opportunities = self._identify_learning_opportunities(
                behavioral_profile,
                explained_matches
            )

            return PersonalizedRecommendations(
                recommendations=explained_matches,
                behavioral_profile=behavioral_profile,
                learning_metadata={
                    "total_interactions": len(self.property_interactions.get(contact_id, [])),
                    "behavioral_preferences_count": len(self.behavioral_preferences.get(contact_id, [])),
                    "confidence_level": self._calculate_profile_confidence(behavioral_profile),
                    "recommendation_method": "behavioral_enhanced"
                },
                explanation_summary=explanation_summary,
                next_learning_opportunities=learning_opportunities
            )

        except Exception as e:
            logger.error(f"Failed to generate personalized recommendations: {str(e)}")
            # Fallback to basic recommendations
            return await self._fallback_recommendations(
                extracted_preferences,
                limit
            )

    async def track_property_interaction(
        self,
        contact_id: str,
        property_id: str,
        interaction_type: InteractionType,
        duration_seconds: Optional[int] = None,
        feedback_text: Optional[str] = None,
        property_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track property interaction for behavioral learning.

        Args:
            contact_id: Contact identifier
            property_id: Property identifier
            interaction_type: Type of interaction
            duration_seconds: How long they engaged
            feedback_text: Optional feedback text
            property_data: Property features and details
        """
        interaction = PropertyInteraction(
            property_id=property_id,
            interaction_type=interaction_type,
            timestamp=datetime.utcnow(),
            duration_seconds=duration_seconds,
            feedback_text=feedback_text,
            property_features=property_data,
            user_context={
                "interaction_sequence": len(self.property_interactions.get(contact_id, [])),
                "tenant_id": self.tenant_id
            }
        )

        # Store interaction
        if contact_id not in self.property_interactions:
            self.property_interactions[contact_id] = []
        self.property_interactions[contact_id].append(interaction)

        # Update behavioral preferences
        await self._update_behavioral_preferences(contact_id, interaction)

        logger.info(
            f"Tracked {interaction_type.value} interaction for {contact_id}",
            extra={
                "property_id": property_id,
                "duration": duration_seconds,
                "total_interactions": len(self.property_interactions[contact_id])
            }
        )

    async def _build_behavioral_profile(self, contact_id: str) -> Dict[str, Any]:
        """Build behavioral profile from interaction history."""
        interactions = self.property_interactions.get(contact_id, [])
        preferences = self.behavioral_preferences.get(contact_id, [])

        if not interactions:
            return self._default_behavioral_profile()

        # Analyze interaction patterns
        profile = {
            "total_interactions": len(interactions),
            "interaction_types": self._analyze_interaction_types(interactions),
            "engagement_patterns": self._analyze_engagement_patterns(interactions),
            "preference_patterns": self._analyze_preference_patterns(interactions),
            "learned_preferences": {pref.preference_type: pref for pref in preferences},
            "confidence_level": self._calculate_profile_confidence({"interactions": interactions}),
            "last_activity": interactions[-1].timestamp if interactions else None
        }

        return profile

    def _analyze_interaction_types(self, interactions: List[PropertyInteraction]) -> Dict[str, Any]:
        """Analyze patterns in interaction types."""
        type_counts = {}
        for interaction in interactions:
            type_name = interaction.interaction_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        total = len(interactions)
        return {
            "counts": type_counts,
            "ratios": {k: v / total for k, v in type_counts.items()},
            "dominant_behavior": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "none"
        }

    def _analyze_engagement_patterns(self, interactions: List[PropertyInteraction]) -> Dict[str, Any]:
        """Analyze engagement patterns from interactions."""
        durations = [i.duration_seconds for i in interactions if i.duration_seconds]

        if not durations:
            return {"avg_duration": None, "engagement_level": "unknown"}

        avg_duration = sum(durations) / len(durations)

        # Categorize engagement level
        if avg_duration > 120:  # 2+ minutes
            engagement_level = "high"
        elif avg_duration > 30:  # 30+ seconds
            engagement_level = "medium"
        else:
            engagement_level = "low"

        return {
            "avg_duration": avg_duration,
            "engagement_level": engagement_level,
            "total_time_spent": sum(durations),
            "engagement_consistency": self._calculate_engagement_consistency(durations)
        }

    def _analyze_preference_patterns(self, interactions: List[PropertyInteraction]) -> Dict[str, Any]:
        """Analyze preference patterns from property features."""
        all_features = {}
        liked_features = {}
        disliked_features = {}

        for interaction in interactions:
            if not interaction.property_features:
                continue

            features = interaction.property_features

            # Track all features seen
            for feature, value in features.items():
                if feature not in all_features:
                    all_features[feature] = []
                all_features[feature].append(value)

            # Track liked/disliked based on interaction type
            if interaction.interaction_type in [InteractionType.LIKE, InteractionType.SAVE, InteractionType.BOOK_SHOWING]:
                for feature, value in features.items():
                    if feature not in liked_features:
                        liked_features[feature] = []
                    liked_features[feature].append(value)
            elif interaction.interaction_type in [InteractionType.DISLIKE, InteractionType.DISMISS]:
                for feature, value in features.items():
                    if feature not in disliked_features:
                        disliked_features[feature] = []
                    disliked_features[feature].append(value)

        return {
            "all_features": all_features,
            "liked_features": liked_features,
            "disliked_features": disliked_features,
            "preference_strength": self._calculate_preference_strength(liked_features, disliked_features)
        }

    async def _apply_behavioral_scoring(
        self,
        base_matches: List[Dict[str, Any]],
        behavioral_profile: Dict[str, Any],
        extracted_preferences: Dict[str, Any]
    ) -> List[PropertyMatch]:
        """Apply behavioral scoring to base matches."""
        enhanced_matches = []

        for property_data in base_matches:
            # Get base score from property matcher
            base_score = property_data.get("match_score", 0.5)

            # Calculate behavioral adjustment
            behavioral_score = await self._calculate_behavioral_score(
                property_data,
                behavioral_profile,
                extracted_preferences
            )

            # Combine scores (weighted average)
            confidence = behavioral_profile.get("confidence_level", 0.3)
            final_score = (base_score * (1 - confidence * 0.5)) + (behavioral_score * confidence * 0.5)

            # Get reasoning breakdown
            reasoning = self._build_reasoning_breakdown(
                property_data,
                base_score,
                behavioral_score,
                behavioral_profile
            )

            enhanced_match = PropertyMatch(
                property=property_data,
                base_score=base_score,
                behavioral_score=behavioral_score,
                final_score=final_score,
                claude_explanation="",  # Will be filled later
                reasoning_breakdown=reasoning,
                behavioral_insights=list(behavioral_profile.get("learned_preferences", {}).values()),
                recommendation_confidence=confidence
            )

            enhanced_matches.append(enhanced_match)

        # Sort by final score
        enhanced_matches.sort(key=lambda x: x.final_score, reverse=True)
        return enhanced_matches

    async def _calculate_behavioral_score(
        self,
        property_data: Dict[str, Any],
        behavioral_profile: Dict[str, Any],
        extracted_preferences: Dict[str, Any]
    ) -> float:
        """Calculate behavioral score for a property based on learned preferences."""
        if behavioral_profile.get("total_interactions", 0) < 3:
            return 0.5  # Neutral score for insufficient data

        score = 0.5  # Start with neutral

        # Apply learned preferences
        learned_prefs = behavioral_profile.get("learned_preferences", {})

        for pref_type, preference in learned_prefs.items():
            if isinstance(preference, dict):
                pref_value = preference.get("preference_value")
                confidence = preference.get("confidence_score", 0.5)
                weight = preference.get("weight_multiplier", 1.0)

                # Apply preference-specific scoring
                pref_score = self._score_property_for_preference(
                    property_data,
                    pref_type,
                    pref_value,
                    confidence
                )

                score += (pref_score - 0.5) * weight * 0.2  # Max 20% adjustment per preference

        # Apply engagement patterns
        engagement_level = behavioral_profile.get("engagement_patterns", {}).get("engagement_level", "medium")
        if engagement_level == "high":
            score += 0.1  # Boost for high-engagement users
        elif engagement_level == "low":
            score -= 0.05  # Slight penalty for low-engagement

        return max(0.0, min(1.0, score))

    def _score_property_for_preference(
        self,
        property_data: Dict[str, Any],
        preference_type: str,
        preference_value: Any,
        confidence: float
    ) -> float:
        """Score a property for a specific learned preference."""
        property_value = property_data.get(preference_type)

        if property_value is None:
            return 0.5  # Neutral if property doesn't have this feature

        # Preference-specific scoring logic
        if preference_type == "price":
            if isinstance(preference_value, (int, float)) and isinstance(property_value, (int, float)):
                # Preference for prices in certain range
                if abs(property_value - preference_value) / preference_value < 0.1:  # Within 10%
                    return 0.8
                elif abs(property_value - preference_value) / preference_value < 0.2:  # Within 20%
                    return 0.7
                else:
                    return 0.3
        elif preference_type in ["bedrooms", "bathrooms"]:
            if property_value == preference_value:
                return 0.8
            elif abs(property_value - preference_value) <= 1:
                return 0.6
            else:
                return 0.4
        elif preference_type == "property_type":
            if property_value.lower() == str(preference_value).lower():
                return 0.9
            else:
                return 0.3
        else:
            # Generic string matching for other preferences
            if str(preference_value).lower() in str(property_value).lower():
                return 0.8
            else:
                return 0.4

        return 0.5

    async def _generate_claude_explanations(
        self,
        property_matches: List[PropertyMatch],
        behavioral_profile: Dict[str, Any],
        extracted_preferences: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]]
    ) -> List[PropertyMatch]:
        """Generate Claude explanations for property matches."""
        for match in property_matches:
            try:
                explanation = await self._generate_single_claude_explanation(
                    match,
                    behavioral_profile,
                    extracted_preferences,
                    conversation_context
                )
                match.claude_explanation = explanation
            except Exception as e:
                logger.error(f"Failed to generate Claude explanation: {str(e)}")
                match.claude_explanation = self._generate_fallback_explanation(match)

        return property_matches

    async def _generate_single_claude_explanation(
        self,
        property_match: PropertyMatch,
        behavioral_profile: Dict[str, Any],
        extracted_preferences: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate Claude explanation for a single property match."""
        # Build context for Claude
        property_data = property_match.property
        reasoning = property_match.reasoning_breakdown

        # Summarize behavioral insights
        behavioral_summary = self._summarize_behavioral_insights(behavioral_profile)

        claude_prompt = f"""You're helping a real estate lead understand why a property is a great match for them.

LEAD'S STATED PREFERENCES:
{json.dumps(extracted_preferences, indent=2)}

BEHAVIORAL INSIGHTS:
{behavioral_summary}

PROPERTY DETAILS:
- Address: {property_data.get('address', {}).get('full_address', 'N/A')}
- Price: ${property_data.get('price', 0):,}
- Bedrooms: {property_data.get('bedrooms', 'N/A')}
- Bathrooms: {property_data.get('bathrooms', 'N/A')}
- Property Type: {property_data.get('property_type', 'N/A')}
- Special Features: {', '.join(property_data.get('features', []))}

MATCH ANALYSIS:
- Base Score: {property_match.base_score:.2f}
- Behavioral Score: {property_match.behavioral_score:.2f}
- Final Score: {property_match.final_score:.2f}
- Recommendation Confidence: {property_match.recommendation_confidence:.2f}

Create a compelling, personalized explanation (2-3 sentences) for why this property is perfect for them. Focus on:
1. How it meets their specific stated needs
2. Why it aligns with their behavioral patterns (if confidence > 0.5)
3. What makes it stand out from other options

Keep it conversational, enthusiastic, and under 200 characters for SMS compatibility."""

        try:
            response = await self.llm_client.agenerate(
                prompt=claude_prompt,
                system_prompt="You are an expert real estate agent explaining property matches. Be enthusiastic but authentic, personalized but concise.",
                temperature=0.7,
                max_tokens=200
            )

            explanation = response.content.strip()

            # Ensure SMS length limit
            if len(explanation) > 200:
                explanation = explanation[:197] + "..."

            return explanation

        except Exception as e:
            logger.error(f"Claude explanation generation failed: {str(e)}")
            return self._generate_fallback_explanation(property_match)

    def _generate_fallback_explanation(self, property_match: PropertyMatch) -> str:
        """Generate fallback explanation when Claude fails."""
        property_data = property_match.property
        score = property_match.final_score

        price = property_data.get('price', 0)
        location = property_data.get('address', {}).get('city', 'great location')
        beds = property_data.get('bedrooms', 0)

        if score > 0.8:
            return f"This ${price:,} home in {location} is an excellent match with {beds} bedrooms - it checks all your boxes!"
        elif score > 0.6:
            return f"This ${price:,} property in {location} is a strong contender that meets most of your key criteria."
        else:
            return f"This ${price:,} home in {location} could work well for your needs with some trade-offs to consider."

    async def _generate_explanation_summary(
        self,
        property_matches: List[PropertyMatch],
        behavioral_profile: Dict[str, Any],
        extracted_preferences: Dict[str, Any]
    ) -> str:
        """Generate overall summary explanation for the recommendations."""
        if not property_matches:
            return "No properties found matching your criteria. Let's adjust the search parameters."

        total_interactions = behavioral_profile.get("total_interactions", 0)
        confidence = behavioral_profile.get("confidence_level", 0.0)

        if total_interactions >= 5 and confidence > 0.6:
            return f"Based on your preferences and how you've interacted with {total_interactions} properties, here are my top personalized picks:"
        elif total_interactions >= 2:
            return f"Here are properties matching your criteria, with insights from your recent property views:"
        else:
            return "Here are properties that match your stated preferences:"

    def _summarize_behavioral_insights(self, behavioral_profile: Dict[str, Any]) -> str:
        """Summarize behavioral insights for Claude context."""
        total_interactions = behavioral_profile.get("total_interactions", 0)

        if total_interactions < 2:
            return "Limited behavioral data available."

        insights = []

        # Interaction patterns
        interaction_types = behavioral_profile.get("interaction_types", {})
        dominant_behavior = interaction_types.get("dominant_behavior", "none")
        if dominant_behavior != "none":
            insights.append(f"Most common interaction: {dominant_behavior}")

        # Engagement level
        engagement = behavioral_profile.get("engagement_patterns", {})
        engagement_level = engagement.get("engagement_level", "unknown")
        if engagement_level != "unknown":
            insights.append(f"Engagement level: {engagement_level}")

        # Learned preferences
        learned_prefs = behavioral_profile.get("learned_preferences", {})
        if learned_prefs:
            pref_count = len(learned_prefs)
            insights.append(f"Learned {pref_count} behavioral preferences")

        return "; ".join(insights) if insights else "Analyzing interaction patterns"

    async def _update_behavioral_preferences(
        self,
        contact_id: str,
        interaction: PropertyInteraction
    ) -> None:
        """Update behavioral preferences based on new interaction."""
        if not interaction.property_features:
            return

        # Initialize if needed
        if contact_id not in self.behavioral_preferences:
            self.behavioral_preferences[contact_id] = []

        # Extract preferences from interaction
        for feature, value in interaction.property_features.items():
            await self._update_single_preference(
                contact_id,
                feature,
                value,
                interaction.interaction_type,
                interaction.timestamp
            )

    async def _update_single_preference(
        self,
        contact_id: str,
        preference_type: str,
        preference_value: Any,
        interaction_type: InteractionType,
        timestamp: datetime
    ) -> None:
        """Update a single behavioral preference."""
        preferences = self.behavioral_preferences[contact_id]

        # Find existing preference
        existing_pref = None
        for pref in preferences:
            if pref.preference_type == preference_type:
                existing_pref = pref
                break

        # Determine preference strength from interaction type
        if interaction_type in [InteractionType.LIKE, InteractionType.SAVE, InteractionType.BOOK_SHOWING]:
            strength = 0.8
        elif interaction_type in [InteractionType.VIEW, InteractionType.DETAILED_VIEW]:
            strength = 0.6
        elif interaction_type in [InteractionType.SHARE]:
            strength = 0.7
        else:
            strength = 0.3  # Negative interactions

        if existing_pref:
            # Update existing preference
            existing_pref.confidence_score = (existing_pref.confidence_score + strength) / 2
            existing_pref.learned_from.append(interaction_type.value)
            existing_pref.last_updated = timestamp
            existing_pref.weight_multiplier = min(2.0, existing_pref.weight_multiplier + 0.1)
        else:
            # Create new preference
            new_pref = BehavioralPreference(
                preference_type=preference_type,
                preference_value=preference_value,
                confidence_score=strength,
                learned_from=[interaction_type.value],
                last_updated=timestamp,
                weight_multiplier=1.0
            )
            preferences.append(new_pref)

    def _default_behavioral_profile(self) -> Dict[str, Any]:
        """Return default behavioral profile for new contacts."""
        return {
            "total_interactions": 0,
            "interaction_types": {"counts": {}, "ratios": {}, "dominant_behavior": "none"},
            "engagement_patterns": {"avg_duration": None, "engagement_level": "unknown"},
            "preference_patterns": {"all_features": {}, "liked_features": {}, "disliked_features": {}},
            "learned_preferences": {},
            "confidence_level": 0.0,
            "last_activity": None
        }

    def _calculate_profile_confidence(self, behavioral_profile: Dict[str, Any]) -> float:
        """Calculate confidence level in behavioral profile."""
        interactions = behavioral_profile.get("interactions", [])
        total_interactions = len(interactions) if isinstance(interactions, list) else behavioral_profile.get("total_interactions", 0)

        if total_interactions == 0:
            return 0.0
        elif total_interactions < 3:
            return 0.3
        elif total_interactions < 7:
            return 0.6
        elif total_interactions < 15:
            return 0.8
        else:
            return 1.0

    def _calculate_engagement_consistency(self, durations: List[float]) -> float:
        """Calculate consistency of engagement durations."""
        if len(durations) < 2:
            return 0.5

        avg_duration = sum(durations) / len(durations)
        variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5

        # Lower standard deviation = higher consistency
        if avg_duration > 0:
            consistency = max(0.0, 1.0 - (std_dev / avg_duration))
        else:
            consistency = 0.5

        return consistency

    def _calculate_preference_strength(
        self,
        liked_features: Dict[str, List],
        disliked_features: Dict[str, List]
    ) -> Dict[str, float]:
        """Calculate preference strength for each feature."""
        strengths = {}

        all_features = set(list(liked_features.keys()) + list(disliked_features.keys()))

        for feature in all_features:
            likes = len(liked_features.get(feature, []))
            dislikes = len(disliked_features.get(feature, []))
            total = likes + dislikes

            if total > 0:
                strength = (likes - dislikes) / total
                strengths[feature] = strength
            else:
                strengths[feature] = 0.0

        return strengths

    def _build_reasoning_breakdown(
        self,
        property_data: Dict[str, Any],
        base_score: float,
        behavioral_score: float,
        behavioral_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build detailed reasoning breakdown for the recommendation."""
        return {
            "base_match_factors": {
                "budget_match": self._analyze_budget_match(property_data),
                "location_match": self._analyze_location_match(property_data),
                "size_requirements": self._analyze_size_match(property_data)
            },
            "behavioral_factors": {
                "interaction_patterns": behavioral_profile.get("interaction_types", {}),
                "engagement_level": behavioral_profile.get("engagement_patterns", {}).get("engagement_level", "unknown"),
                "learned_preferences": len(behavioral_profile.get("learned_preferences", {}))
            },
            "score_components": {
                "base_score": base_score,
                "behavioral_adjustment": behavioral_score - 0.5,
                "confidence_weight": behavioral_profile.get("confidence_level", 0.0)
            }
        }

    def _analyze_budget_match(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well property matches budget."""
        # This would integrate with extracted_preferences in full implementation
        return {"analysis": "budget_analysis_placeholder"}

    def _analyze_location_match(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze location match quality."""
        return {"analysis": "location_analysis_placeholder"}

    def _analyze_size_match(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze size and feature matching."""
        return {"analysis": "size_analysis_placeholder"}

    def _identify_learning_opportunities(
        self,
        behavioral_profile: Dict[str, Any],
        property_matches: List[PropertyMatch]
    ) -> List[str]:
        """Identify opportunities to learn more about user preferences."""
        opportunities = []

        total_interactions = behavioral_profile.get("total_interactions", 0)
        confidence = behavioral_profile.get("confidence_level", 0.0)

        if total_interactions < 5:
            opportunities.append("Encourage more property interactions to improve recommendations")

        if confidence < 0.5:
            opportunities.append("Ask for feedback on recommended properties to learn preferences")

        learned_prefs = behavioral_profile.get("learned_preferences", {})
        if "price" not in learned_prefs:
            opportunities.append("Learn price sensitivity from property interactions")

        if "location" not in learned_prefs:
            opportunities.append("Identify preferred neighborhoods from viewing patterns")

        return opportunities

    def _empty_recommendations_response(self) -> PersonalizedRecommendations:
        """Return empty recommendations response."""
        return PersonalizedRecommendations(
            recommendations=[],
            behavioral_profile=self._default_behavioral_profile(),
            learning_metadata={"total_interactions": 0, "recommendation_method": "no_matches"},
            explanation_summary="No properties found matching your criteria. Let's broaden the search or adjust preferences.",
            next_learning_opportunities=["Provide more details about your preferences", "Expand search criteria"]
        )

    async def _fallback_recommendations(
        self,
        extracted_preferences: Dict[str, Any],
        limit: int
    ) -> PersonalizedRecommendations:
        """Generate fallback recommendations when full process fails."""
        try:
            basic_matches = self.property_matcher.find_matches(extracted_preferences, limit=limit)

            simple_recommendations = []
            for prop in basic_matches:
                simple_match = PropertyMatch(
                    property=prop,
                    base_score=prop.get("match_score", 0.5),
                    behavioral_score=0.5,
                    final_score=prop.get("match_score", 0.5),
                    claude_explanation=self.property_matcher.generate_match_reasoning(prop, extracted_preferences),
                    reasoning_breakdown={"fallback": True},
                    behavioral_insights=[],
                    recommendation_confidence=0.3
                )
                simple_recommendations.append(simple_match)

            return PersonalizedRecommendations(
                recommendations=simple_recommendations,
                behavioral_profile=self._default_behavioral_profile(),
                learning_metadata={"recommendation_method": "fallback_basic"},
                explanation_summary="Here are properties matching your basic criteria:",
                next_learning_opportunities=["Interact with properties to improve future recommendations"]
            )

        except Exception as e:
            logger.error(f"Fallback recommendations failed: {str(e)}")
            return self._empty_recommendations_response()

    async def get_recommendation_explanation(
        self,
        contact_id: str,
        property_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed explanation for why a specific property was recommended.

        Args:
            contact_id: Contact identifier
            property_id: Property identifier

        Returns:
            Detailed explanation with behavioral insights
        """
        behavioral_profile = await self._build_behavioral_profile(contact_id)

        # This would fetch the specific property and generate explanation
        # Placeholder implementation
        return {
            "property_id": property_id,
            "explanation": "Detailed explanation would be generated here",
            "behavioral_factors": behavioral_profile,
            "confidence": behavioral_profile.get("confidence_level", 0.0)
        }