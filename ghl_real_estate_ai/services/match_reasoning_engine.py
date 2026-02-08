"""
Match Reasoning Engine for Explainable AI

Generates human-readable explanations for property match scores:
- Natural language reasoning for why properties match
- Comparison narratives vs. past liked properties
- Agent talking points for follow-up conversations
- Lifestyle compatibility explanations
- Market opportunity insights
- Concern identification and mitigation strategies
"""

import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.matching_models import (
    BehavioralProfile,
    MatchReasoning,
    MatchScoreBreakdown,
    PropertyMatch,
)

logger = get_logger(__name__)


class MatchReasoningEngine:
    """
    Engine for generating comprehensive, human-readable match explanations.

    Key Features:
    - Natural language generation for match strengths
    - Intelligent concern identification
    - Agent conversation starters
    - Comparison with past preferences
    - Lifestyle narrative generation
    - Market timing explanations
    """

    def __init__(self):
        """Initialize the match reasoning engine."""
        self._load_reasoning_templates()
        self._load_comparison_data()

    def generate_comprehensive_reasoning(
        self,
        property_data: Dict[str, Any],
        score_breakdown: MatchScoreBreakdown,
        preferences: Dict[str, Any],
        behavioral_profile: Optional[BehavioralProfile] = None,
        past_liked_properties: Optional[List[Dict[str, Any]]] = None,
    ) -> MatchReasoning:
        """
        Generate comprehensive match reasoning with all explanation components.

        Args:
            property_data: Property information
            score_breakdown: Detailed scoring breakdown
            preferences: Lead's stated preferences
            behavioral_profile: Optional behavioral analysis
            past_liked_properties: Optional previously liked properties

        Returns:
            Complete MatchReasoning with all explanation components
        """
        logger.info(f"Generating reasoning for property {property_data.get('id', 'unknown')}")

        # Generate primary strengths
        primary_strengths = self._identify_primary_strengths(property_data, score_breakdown, preferences)

        # Generate secondary benefits
        secondary_benefits = self._identify_secondary_benefits(property_data, score_breakdown)

        # Identify potential concerns
        potential_concerns = self._identify_potential_concerns(property_data, score_breakdown, preferences)

        # Generate agent talking points
        agent_talking_points = self._generate_agent_talking_points(
            property_data, score_breakdown, primary_strengths, potential_concerns
        )

        # Generate comparison to past likes
        comparison_to_past_likes = self._generate_past_comparison(
            property_data, past_liked_properties, behavioral_profile
        )

        # Generate lifestyle fit summary
        lifestyle_fit_summary = self._generate_lifestyle_summary(score_breakdown.lifestyle_scores, preferences)

        # Generate market opportunity summary
        market_opportunity_summary = self._generate_market_summary(score_breakdown.market_timing_score)

        return MatchReasoning(
            primary_strengths=primary_strengths,
            secondary_benefits=secondary_benefits,
            potential_concerns=potential_concerns,
            agent_talking_points=agent_talking_points,
            comparison_to_past_likes=comparison_to_past_likes,
            lifestyle_fit_summary=lifestyle_fit_summary,
            market_opportunity_summary=market_opportunity_summary,
        )

    def generate_quick_explanation(
        self, property_data: Dict[str, Any], score_breakdown: MatchScoreBreakdown, preferences: Dict[str, Any]
    ) -> str:
        """
        Generate a quick, one-sentence explanation for the match.

        For use in SMS, email previews, or quick summaries.
        """
        # Find the top scoring factor
        top_factor, top_reasoning = self._find_top_scoring_factor(score_breakdown)

        property_price = property_data.get("price", 0)
        budget = preferences.get("budget", 0)

        if top_factor == "budget" and budget and property_price <= budget:
            savings = budget - property_price
            if savings > 50000:
                return f"Great find! This home is ${savings // 1000}k under your budget with {top_reasoning.lower()}."
            else:
                return f"Perfect fit within your budget with {top_reasoning.lower()}."

        elif top_factor == "location":
            return f"Excellent location match - {top_reasoning.lower()}."

        elif top_factor == "schools":
            return f"Outstanding schools in this area make it perfect for your family."

        elif top_factor == "market_timing":
            return f"Great timing opportunity - {score_breakdown.market_timing_score.reasoning.lower()}."

        else:
            # Generic strong match
            return f"Strong overall match with {top_reasoning.lower()}."

    def generate_agent_follow_up_script(
        self, property_data: Dict[str, Any], reasoning: MatchReasoning, lead_name: str = "Lead"
    ) -> Dict[str, str]:
        """
        Generate follow-up scripts for different communication channels.

        Returns:
            Dict with scripts for phone, email, and text follow-up
        """
        property_address = self._format_property_address(property_data)
        price = property_data.get("price", 0)

        # Phone script
        phone_script = self._generate_phone_script(lead_name, property_address, price, reasoning)

        # Email script
        email_script = self._generate_email_script(lead_name, property_data, reasoning)

        # Text script
        text_script = self._generate_text_script(property_address, price, reasoning)

        return {"phone": phone_script, "email": email_script, "text": text_script}

    # Primary strength identification

    def _identify_primary_strengths(
        self, property_data: Dict[str, Any], score_breakdown: MatchScoreBreakdown, preferences: Dict[str, Any]
    ) -> List[str]:
        """Identify the top 3-5 reasons why this property matches well."""
        strengths = []

        # Analyze each factor's contribution
        factor_contributions = self._calculate_factor_contributions(score_breakdown)

        # Sort by weighted contribution
        sorted_factors = sorted(factor_contributions.items(), key=lambda x: x[1], reverse=True)

        # Generate strength statements for top factors
        for factor_name, contribution in sorted_factors[:5]:
            if contribution < 0.05:  # Skip factors with minimal contribution
                continue

            strength = self._generate_strength_statement(factor_name, property_data, score_breakdown, preferences)
            if strength:
                strengths.append(strength)

        # Ensure we have at least 2 strengths
        if len(strengths) < 2:
            strengths.extend(self._generate_fallback_strengths(property_data, preferences))

        return strengths[:5]  # Limit to top 5

    def _calculate_factor_contributions(self, score_breakdown: MatchScoreBreakdown) -> Dict[str, float]:
        """Calculate each factor's contribution to the overall score."""
        contributions = {}

        # Traditional factors
        trad = score_breakdown.traditional_scores
        contributions["budget"] = trad.budget.weighted_score
        contributions["location"] = trad.location.weighted_score
        contributions["bedrooms"] = trad.bedrooms.weighted_score
        contributions["bathrooms"] = trad.bathrooms.weighted_score
        contributions["property_type"] = trad.property_type.weighted_score
        contributions["sqft"] = trad.sqft.weighted_score

        # Lifestyle factors (approximate individual contributions)
        lifestyle_total = score_breakdown.lifestyle_scores.overall_score
        contributions["schools"] = lifestyle_total * 0.4  # Schools typically weighted highest
        contributions["commute"] = lifestyle_total * 0.3
        contributions["walkability"] = lifestyle_total * 0.2
        contributions["safety"] = lifestyle_total * 0.1

        # Contextual factors
        contextual_total = score_breakdown.contextual_scores.overall_score
        contributions["hoa_fee"] = contextual_total * 0.3
        contributions["lot_size"] = contextual_total * 0.3
        contributions["home_age"] = contextual_total * 0.2
        contributions["parking"] = contextual_total * 0.1
        contributions["property_condition"] = contextual_total * 0.1

        # Market timing
        timing_weight = score_breakdown.adaptive_weights.market_timing_weight
        contributions["market_timing"] = score_breakdown.market_timing_score.optimal_timing_score * timing_weight

        return contributions

    def _generate_strength_statement(
        self,
        factor_name: str,
        property_data: Dict[str, Any],
        score_breakdown: MatchScoreBreakdown,
        preferences: Dict[str, Any],
    ) -> Optional[str]:
        """Generate a strength statement for a specific factor."""
        if factor_name == "budget":
            return score_breakdown.traditional_scores.budget.reasoning

        elif factor_name == "location":
            return score_breakdown.traditional_scores.location.reasoning

        elif factor_name == "bedrooms":
            bedrooms = property_data.get("bedrooms", 0)
            return f"Has the {bedrooms} bedrooms you need"

        elif factor_name == "schools":
            if hasattr(score_breakdown.lifestyle_scores.schools, "average_rating"):
                rating = score_breakdown.lifestyle_scores.schools.average_rating
                if rating >= 8:
                    return f"Excellent schools (average {rating:.1f}/10 rating)"
                elif rating >= 7:
                    return f"Very good schools in the area"

        elif factor_name == "walkability":
            if hasattr(score_breakdown.lifestyle_scores.walkability, "walk_score"):
                walk_score = score_breakdown.lifestyle_scores.walkability.walk_score
                if walk_score and walk_score >= 70:
                    return f"Very walkable area (Walk Score: {walk_score})"

        elif factor_name == "market_timing":
            timing = score_breakdown.market_timing_score
            if timing.days_on_market_score > 0.7:
                return f"Great negotiation opportunity ({timing.reasoning.split(';')[0]})"

        elif factor_name == "safety":
            neighborhood = property_data.get("address", {}).get("neighborhood", "")
            return f"Safe, family-friendly {neighborhood} neighborhood"

        elif factor_name == "commute":
            return "Convenient commute location"

        return None

    def _generate_fallback_strengths(self, property_data: Dict[str, Any], preferences: Dict[str, Any]) -> List[str]:
        """Generate fallback strengths when scoring factors don't provide enough."""
        fallbacks = []

        # Property condition indicators
        features = property_data.get("features", [])
        year_built = property_data.get("year_built", 0)

        if year_built > 2015:
            fallbacks.append("Recently built with modern amenities")
        elif any("updated" in feature.lower() for feature in features):
            fallbacks.append("Updated and well-maintained")

        # Special features
        special_features = ["pool", "garage", "patio", "deck", "fireplace", "hardwood"]
        found_features = [
            feature for feature in special_features if any(feature in prop_feature.lower() for prop_feature in features)
        ]

        if found_features:
            if len(found_features) == 1:
                fallbacks.append(f"Features {found_features[0]}")
            else:
                fallbacks.append(f"Great features including {', '.join(found_features[:2])}")

        # Lot size
        lot_size = property_data.get("lot_size_sqft", 0)
        if lot_size > 8000:
            fallbacks.append("Large lot with plenty of space")

        return fallbacks

    # Secondary benefits identification

    def _identify_secondary_benefits(
        self, property_data: Dict[str, Any], score_breakdown: MatchScoreBreakdown
    ) -> List[str]:
        """Identify additional benefits beyond primary strengths."""
        benefits = []

        # Property features analysis
        features = property_data.get("features", [])
        highlights = property_data.get("highlights", [])
        all_features = features + highlights

        # Categorize features
        feature_categories = self._categorize_property_features(all_features)

        # Generate benefits from features
        for category, items in feature_categories.items():
            if items:
                benefit = self._feature_category_to_benefit(category, items)
                if benefit:
                    benefits.append(benefit)

        # Energy efficiency benefits
        if any("energy" in feature.lower() for feature in all_features):
            benefits.append("Energy-efficient features help reduce utility costs")

        # Investment potential
        neighborhood = property_data.get("address", {}).get("neighborhood", "")
        if neighborhood.lower() in ["hyde park", "steiner ranch", "west campus"]:
            benefits.append("Strong investment potential in desirable area")

        # Market timing benefits
        dom = property_data.get("days_on_market", 0)
        if dom > 30:
            benefits.append("Seller may be motivated for quick sale")

        return benefits[:4]  # Limit to top 4 benefits

    def _categorize_property_features(self, features: List[str]) -> Dict[str, List[str]]:
        """Categorize property features into benefit groups."""
        categories = {"outdoor_living": [], "modern_updates": [], "storage": [], "entertaining": [], "convenience": []}

        feature_mapping = {
            "outdoor_living": ["patio", "deck", "pool", "backyard", "outdoor", "garden"],
            "modern_updates": ["updated", "renovated", "new", "modern", "upgraded"],
            "storage": ["garage", "storage", "pantry", "closet"],
            "entertaining": ["open concept", "kitchen island", "living room", "dining"],
            "convenience": ["laundry", "parking", "elevator", "smart home"],
        }

        for feature in features:
            feature_lower = feature.lower()
            for category, keywords in feature_mapping.items():
                if any(keyword in feature_lower for keyword in keywords):
                    categories[category].append(feature)
                    break

        return categories

    def _feature_category_to_benefit(self, category: str, items: List[str]) -> Optional[str]:
        """Convert feature category to benefit statement."""
        if not items:
            return None

        benefit_templates = {
            "outdoor_living": "Perfect for outdoor entertaining and relaxation",
            "modern_updates": "Move-in ready with modern updates throughout",
            "storage": "Excellent storage and organization options",
            "entertaining": "Great layout for hosting friends and family",
            "convenience": "Convenient features for everyday living",
        }

        return benefit_templates.get(category)

    # Concerns identification

    def _identify_potential_concerns(
        self, property_data: Dict[str, Any], score_breakdown: MatchScoreBreakdown, preferences: Dict[str, Any]
    ) -> List[str]:
        """Identify potential concerns or drawbacks to address proactively."""
        concerns = []

        # Budget concerns
        budget_score = score_breakdown.traditional_scores.budget
        if budget_score.raw_score < 0.5:
            concerns.append("Price may be above your ideal budget range")

        # Location concerns
        location_score = score_breakdown.traditional_scores.location
        if location_score.raw_score < 0.6:
            concerns.append("Location may not be in your preferred area")

        # Size concerns
        bedrooms_score = score_breakdown.traditional_scores.bedrooms
        if bedrooms_score.raw_score < 0.7:
            concerns.append("Bedroom count may not fully meet your needs")

        # Age concerns
        year_built = property_data.get("year_built", 0)
        current_year = datetime.now().year
        age = current_year - year_built
        if age > 40:
            concerns.append(f"Built in {year_built} - may need updates or maintenance")

        # HOA concerns
        hoa_fee = property_data.get("hoa_fee", 0)
        if hoa_fee > 200:
            concerns.append(f"${hoa_fee}/month HOA fee adds to monthly costs")

        # Market timing concerns
        timing = score_breakdown.market_timing_score
        if timing.competition_level == "high":
            concerns.append("High competition - may need competitive offer")

        # Commute concerns (if applicable)
        lifestyle = score_breakdown.lifestyle_scores
        if hasattr(lifestyle.commute, "to_downtown_minutes"):
            commute_time = lifestyle.commute.to_downtown_minutes
            if commute_time and commute_time > 45:
                concerns.append(f"~{commute_time} minute commute to downtown")

        return concerns[:3]  # Limit to top 3 concerns

    # Agent talking points

    def _generate_agent_talking_points(
        self,
        property_data: Dict[str, Any],
        score_breakdown: MatchScoreBreakdown,
        primary_strengths: List[str],
        potential_concerns: List[str],
    ) -> List[str]:
        """Generate talking points for agent follow-up conversations."""
        talking_points = []

        # Overall match quality
        overall_score = score_breakdown.overall_score
        talking_points.append(f"Overall match score: {overall_score:.0%} compatibility")

        # Key selling point
        if primary_strengths:
            talking_points.append(f"Key highlight: {primary_strengths[0]}")

        # Market position
        timing = score_breakdown.market_timing_score
        if timing.urgency_indicator == "act_fast":
            talking_points.append("Hot property - recommend viewing ASAP")
        elif timing.days_on_market_score > 0.7:
            talking_points.append("Good negotiation opportunity based on market time")

        # Lifestyle fit
        lifestyle_score = score_breakdown.lifestyle_scores.overall_score
        if lifestyle_score > 0.8:
            talking_points.append("Excellent lifestyle fit for your preferences")
        elif lifestyle_score > 0.6:
            talking_points.append("Good lifestyle compatibility")

        # Concern mitigation
        if potential_concerns:
            talking_points.append(f"Address concern: {potential_concerns[0]}")

        # Next steps
        if timing.urgency_indicator == "act_fast":
            talking_points.append("Suggest immediate showing and pre-approval review")
        else:
            talking_points.append("Recommend viewing this week if interested")

        return talking_points

    # Past comparison generation

    def _generate_past_comparison(
        self,
        property_data: Dict[str, Any],
        past_liked_properties: Optional[List[Dict[str, Any]]],
        behavioral_profile: Optional[BehavioralProfile],
    ) -> Optional[str]:
        """Generate comparison to previously liked properties."""
        if not past_liked_properties:
            return None

        current_price = property_data.get("price", 0)
        current_bedrooms = property_data.get("bedrooms", 0)
        current_neighborhood = property_data.get("address", {}).get("neighborhood", "")

        # Find most similar past liked property
        best_match = None
        best_similarity = 0

        for past_prop in past_liked_properties:
            similarity = self._calculate_similarity(property_data, past_prop)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = past_prop

        if not best_match or best_similarity < 0.3:
            return None

        # Generate comparison statement
        past_address = best_match.get("address", {}).get("street", "a previous property")
        past_price = best_match.get("price", 0)
        past_neighborhood = best_match.get("address", {}).get("neighborhood", "")

        if current_price < past_price:
            price_diff = past_price - current_price
            comparison = f"Similar to {past_address} you liked, but ${price_diff:,} less expensive"
        elif abs(current_price - past_price) / past_price < 0.1:  # Within 10%
            comparison = f"Similar price point to {past_address} you saved"
        else:
            comparison = f"Similar style to {past_address} you viewed"

        # Add distinguishing features
        if current_neighborhood != past_neighborhood:
            comparison += f" in {current_neighborhood}"

        return comparison

    def _calculate_similarity(self, prop1: Dict[str, Any], prop2: Dict[str, Any]) -> float:
        """Calculate similarity score between two properties."""
        similarity = 0.0

        # Price similarity (±20%)
        price1, price2 = prop1.get("price", 0), prop2.get("price", 0)
        if price1 and price2:
            price_diff = abs(price1 - price2) / max(price1, price2)
            if price_diff <= 0.2:
                similarity += 0.3

        # Bedroom similarity
        beds1, beds2 = prop1.get("bedrooms", 0), prop2.get("bedrooms", 0)
        if beds1 == beds2:
            similarity += 0.3
        elif abs(beds1 - beds2) == 1:
            similarity += 0.1

        # Property type similarity
        type1 = prop1.get("property_type", "").lower()
        type2 = prop2.get("property_type", "").lower()
        if type1 == type2:
            similarity += 0.2

        # Neighborhood similarity
        neighborhood1 = prop1.get("address", {}).get("neighborhood", "").lower()
        neighborhood2 = prop2.get("address", {}).get("neighborhood", "").lower()
        if neighborhood1 == neighborhood2:
            similarity += 0.2

        return similarity

    # Summary generation

    def _generate_lifestyle_summary(self, lifestyle_scores, preferences: Dict[str, Any]) -> str:
        """Generate lifestyle compatibility summary."""
        overall_score = lifestyle_scores.overall_score

        if overall_score > 0.8:
            summary = "Excellent lifestyle fit"
        elif overall_score > 0.6:
            summary = "Good lifestyle compatibility"
        elif overall_score > 0.4:
            summary = "Moderate lifestyle fit"
        else:
            summary = "Limited lifestyle compatibility"

        # Add specific highlights
        highlights = []
        if hasattr(lifestyle_scores.schools, "average_rating"):
            if lifestyle_scores.schools.average_rating >= 8:
                highlights.append("outstanding schools")

        if hasattr(lifestyle_scores.walkability, "walk_score"):
            if lifestyle_scores.walkability.walk_score and lifestyle_scores.walkability.walk_score >= 80:
                highlights.append("very walkable area")

        if highlights:
            summary += f" with {' and '.join(highlights)}"

        return summary

    def _generate_market_summary(self, market_timing_score) -> str:
        """Generate market opportunity summary."""
        urgency = market_timing_score.urgency_indicator
        timing_score = market_timing_score.optimal_timing_score

        if urgency == "act_fast":
            return "Time-sensitive opportunity - high competition expected"
        elif timing_score > 0.8:
            return "Excellent market opportunity with strong negotiation potential"
        elif timing_score > 0.6:
            return "Good market opportunity for buyers"
        elif urgency == "can_wait":
            return "Buyer-favorable market conditions allow for strategic approach"
        else:
            return "Balanced market conditions"

    # Helper methods

    def _find_top_scoring_factor(self, score_breakdown: MatchScoreBreakdown) -> Tuple[str, str]:
        """Find the highest contributing factor and its reasoning."""
        factor_contributions = self._calculate_factor_contributions(score_breakdown)
        top_factor = max(factor_contributions.items(), key=lambda x: x[1])[0]

        # Get reasoning for top factor
        if top_factor == "budget":
            reasoning = score_breakdown.traditional_scores.budget.reasoning
        elif top_factor == "location":
            reasoning = score_breakdown.traditional_scores.location.reasoning
        elif top_factor == "bedrooms":
            reasoning = score_breakdown.traditional_scores.bedrooms.reasoning
        elif top_factor == "schools":
            reasoning = "excellent schools"
        elif top_factor == "market_timing":
            reasoning = score_breakdown.market_timing_score.reasoning.split(";")[0]
        else:
            reasoning = f"strong {top_factor.replace('_', ' ')} match"

        return top_factor, reasoning

    def _format_property_address(self, property_data: Dict[str, Any]) -> str:
        """Format property address for communication."""
        address = property_data.get("address", {})
        street = address.get("street", "")
        neighborhood = address.get("neighborhood", "")

        if street and neighborhood:
            return f"{street} in {neighborhood}"
        elif street:
            return street
        elif neighborhood:
            return f"Property in {neighborhood}"
        else:
            return "Property"

    # Communication scripts

    def _generate_phone_script(
        self, lead_name: str, property_address: str, price: int, reasoning: MatchReasoning
    ) -> str:
        """Generate phone conversation script."""
        script = f"Hi {lead_name}, I found a property that matches your criteria really well. "

        if reasoning.primary_strengths:
            script += f"{reasoning.primary_strengths[0]}. "

        script += f"It's {property_address} for ${price:,}. "

        if reasoning.market_opportunity_summary:
            if "time-sensitive" in reasoning.market_opportunity_summary.lower():
                script += "This one is getting a lot of interest, so I wanted to call you right away. "

        script += "Would you like me to schedule a showing for you today or tomorrow?"

        return script

    def _generate_email_script(self, lead_name: str, property_data: Dict[str, Any], reasoning: MatchReasoning) -> str:
        """Generate email follow-up script."""
        property_address = self._format_property_address(property_data)
        price = property_data.get("price", 0)

        email = f"Hi {lead_name},\n\n"
        email += f"I found a property that looks like a great match for you!\n\n"
        email += f"📍 {property_address}\n"
        email += f"💰 ${price:,}\n\n"

        if reasoning.primary_strengths:
            email += "Why it's a great fit:\n"
            for strength in reasoning.primary_strengths[:3]:
                email += f"• {strength}\n"
            email += "\n"

        if reasoning.potential_concerns:
            email += "Things to consider:\n"
            for concern in reasoning.potential_concerns[:2]:
                email += f"• {concern}\n"
            email += "\n"

        if "time-sensitive" in reasoning.market_opportunity_summary.lower():
            email += "⏰ This property is getting attention - would you like to see it this week?\n\n"
        else:
            email += "Would you like to schedule a viewing?\n\n"

        email += "Let me know what you think!\n\n"
        email += "Best regards,\n[Agent Name]"

        return email

    def _generate_text_script(self, property_address: str, price: int, reasoning: MatchReasoning) -> str:
        """Generate text message script."""
        text = f"Found a great match for you! {property_address} for ${price:,}. "

        if reasoning.primary_strengths:
            # Use first strength but keep it short
            strength = reasoning.primary_strengths[0]
            if len(strength) > 50:
                strength = strength[:50] + "..."
            text += f"{strength}. "

        if "time-sensitive" in reasoning.market_opportunity_summary.lower():
            text += "Getting interest - want to see it ASAP? "
        else:
            text += "Interested in viewing? "

        text += "Text back YES for details!"

        return text

    # Data loading methods

    def _load_reasoning_templates(self):
        """Load reasoning templates and patterns."""
        # In production, these would come from external files
        self.strength_templates = {
            "budget": [
                "Within your budget with room to spare",
                "Excellent value for the price",
                "Fits comfortably in your price range",
            ],
            "location": [
                "Perfect location in your preferred area",
                "Highly desirable neighborhood",
                "Great location with easy access to amenities",
            ],
            "schools": [
                "Outstanding school district",
                "Top-rated schools nearby",
                "Excellent educational opportunities",
            ],
        }

        self.concern_templates = {
            "budget": [
                "Price is at the top of your range",
                "May need to stretch budget slightly",
                "Worth considering given other benefits",
            ],
            "age": [
                "Older home with character and charm",
                "May need some updating over time",
                "Built in a different era with unique features",
            ],
        }

    def _load_comparison_data(self):
        """Load data for comparison analysis."""
        # Placeholder for comparison patterns and rules
        self.comparison_patterns = {
            "similar_price": "Similar price point to properties you've liked",
            "better_value": "Better value than similar properties",
            "upgrade": "Step up from your previous choices",
        }


# Demo function
def demo_match_reasoning():
    """Demo the match reasoning engine."""
    print("🧠 Match Reasoning Engine Demo\n")

    engine = MatchReasoningEngine()

    # Create sample data for testing
    from ghl_real_estate_ai.models.matching_models import (
        AdaptiveWeights,
        CommuteScore,
        ContextualScores,
        FactorScore,
        LifestyleScores,
        MarketTimingScore,
        MatchScoreBreakdown,
        SafetyScore,
        SchoolScore,
        TraditionalScores,
        WalkabilityScore,
    )

    # Sample property
    test_property = {
        "id": "test_001",
        "address": {"street": "123 Main St", "neighborhood": "Hyde Park", "city": "Austin"},
        "price": 650000,
        "bedrooms": 3,
        "bathrooms": 2,
        "year_built": 2018,
        "features": ["Updated kitchen", "Large backyard", "Garage"],
        "highlights": ["Walkable neighborhood", "Top schools"],
        "days_on_market": 12,
    }

    # Sample preferences
    test_preferences = {"budget": 700000, "location": "Austin", "bedrooms": 3, "property_type": "Single Family"}

    # Create mock score breakdown
    score_breakdown = MatchScoreBreakdown(
        traditional_scores=TraditionalScores(
            budget=FactorScore("budget", 0.9, 0.18, 0.20, 0.95, "Within budget", "high"),
            location=FactorScore("location", 0.8, 0.12, 0.15, 0.90, "Preferred area", "high"),
            bedrooms=FactorScore("bedrooms", 1.0, 0.10, 0.10, 0.95, "Exact match", "high"),
            bathrooms=FactorScore("bathrooms", 0.8, 0.04, 0.05, 0.85, "Good match", "high"),
            property_type=FactorScore("property_type", 1.0, 0.05, 0.05, 0.95, "Exact match", "high"),
            sqft=FactorScore("sqft", 0.7, 0.035, 0.05, 0.80, "Adequate size", "medium"),
        ),
        lifestyle_scores=LifestyleScores(
            schools=SchoolScore(9, 8, 8, 8.3, 0.1, 0.85, "Mathews Elementary", "Excellent schools"),
            commute=CommuteScore(15, None, 0.7, 0.8, 0.75, "Good downtown access"),
            walkability=WalkabilityScore(85, 20, 0.3, 0.8, 0.7, 0.82, "Very walkable area"),
            safety=SafetyScore(12.0, 8.0, 6, 0.85, "Safe neighborhood"),
            amenities_proximity=0.7,
            overall_score=0.79,
        ),
        contextual_scores=ContextualScores(
            hoa_fee_score=FactorScore("hoa_fee", 1.0, 0.03, 0.03, 0.90, "No HOA", "high"),
            lot_size_score=FactorScore("lot_size", 0.8, 0.024, 0.03, 0.85, "Good size", "medium"),
            home_age_score=FactorScore("home_age", 0.9, 0.018, 0.02, 0.90, "Recently built", "high"),
            parking_score=FactorScore("parking", 0.8, 0.016, 0.02, 0.70, "Garage available", "medium"),
            property_condition_score=FactorScore("condition", 0.9, 0.018, 0.02, 0.85, "Excellent condition", "high"),
            overall_score=0.096,
        ),
        market_timing_score=MarketTimingScore(
            0.6, 0.5, 0.7, "medium", 0.59, "good_time", "Normal market time (12 days); moderate competition"
        ),
        adaptive_weights=AdaptiveWeights({}, {}, {}, 0.05, 0.85, 5, datetime.utcnow()),
        overall_score=0.83,
        confidence_level=0.88,
        data_completeness=0.92,
    )

    # Generate reasoning
    reasoning = engine.generate_comprehensive_reasoning(test_property, score_breakdown, test_preferences)

    print("🎯 Primary Strengths:")
    for strength in reasoning.primary_strengths:
        print(f"   • {strength}")

    print(f"\n✨ Secondary Benefits:")
    for benefit in reasoning.secondary_benefits:
        print(f"   • {benefit}")

    print(f"\n⚠️ Potential Concerns:")
    for concern in reasoning.potential_concerns:
        print(f"   • {concern}")

    print(f"\n🏡 Lifestyle Fit: {reasoning.lifestyle_fit_summary}")
    print(f"📈 Market Opportunity: {reasoning.market_opportunity_summary}")

    print(f"\n📞 Agent Talking Points:")
    for point in reasoning.agent_talking_points:
        print(f"   • {point}")

    # Generate quick explanation
    quick_explanation = engine.generate_quick_explanation(test_property, score_breakdown, test_preferences)
    print(f"\n💬 Quick Explanation: {quick_explanation}")

    # Generate follow-up scripts
    scripts = engine.generate_agent_follow_up_script(test_property, reasoning, "Sarah")
    print(f"\n📱 Text Script:\n{scripts['text']}")


if __name__ == "__main__":
    demo_match_reasoning()
