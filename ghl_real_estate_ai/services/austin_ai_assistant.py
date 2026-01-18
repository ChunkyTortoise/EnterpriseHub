"""
Austin AI Assistant - Enhanced Claude integration with Austin market expertise.

Enhances the existing ClaudeAssistant with Austin-specific market intelligence,
corporate relocation expertise, and neighborhood insights for Jorge's lead bot.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging

from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.austin_market_service import get_austin_market_service, PropertyType
from ghl_real_estate_ai.services.property_alerts import get_property_alert_system
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AustinConversationContext:
    """Context for Austin-specific conversations."""
    lead_id: str
    employer: Optional[str] = None
    position_level: Optional[str] = None
    relocation_timeline: Optional[str] = None
    budget_range: Optional[tuple] = None
    preferred_neighborhoods: List[str] = None
    commute_requirements: Optional[str] = None
    lifestyle_preferences: List[str] = None
    family_situation: Optional[str] = None
    current_location: Optional[str] = None
    conversation_stage: str = "discovery"  # discovery, qualification, showing, negotiation

    def __post_init__(self):
        if self.preferred_neighborhoods is None:
            self.preferred_neighborhoods = []
        if self.lifestyle_preferences is None:
            self.lifestyle_preferences = []


class AustinAIAssistant(ClaudeAssistant):
    """
    Enhanced Claude Assistant with Austin real estate market expertise.

    Provides context-aware responses for corporate relocations,
    neighborhood recommendations, and market intelligence.
    """

    def __init__(self, context_type: str = "austin_real_estate"):
        super().__init__(context_type)
        self.market_service = get_austin_market_service()
        self.alert_system = get_property_alert_system()
        self.cache = get_cache_service()
        self.austin_expertise = self._load_austin_expertise()

    def _load_austin_expertise(self) -> Dict[str, Any]:
        """Load Austin expertise knowledge base."""
        try:
            with open("/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/data/knowledge_base/austin_expertise.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Austin expertise: {e}")
            return {}

    async def analyze_lead_with_austin_context(
        self,
        lead_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze lead with Austin market context and corporate expertise.

        Provides comprehensive analysis including:
        - Corporate relocation insights
        - Neighborhood matching based on employer and lifestyle
        - Market timing recommendations
        - Personalized talking points
        """
        try:
            # Extract lead information
            lead_id = lead_data.get("lead_id", "")
            lead_name = lead_data.get("name", "Client")

            # Build Austin context
            austin_context = await self._build_austin_context(lead_data, conversation_history)

            # Generate market insights
            market_insights = await self._generate_market_insights(austin_context)

            # Get neighborhood recommendations
            neighborhood_recs = await self._get_neighborhood_recommendations(austin_context)

            # Generate talking points
            talking_points = await self._generate_talking_points(austin_context, market_insights)

            # Get corporate insights if applicable
            corporate_insights = {}
            if austin_context.employer:
                corporate_insights = await self.market_service.get_corporate_relocation_insights(
                    austin_context.employer, austin_context.position_level
                )

            analysis = {
                "lead_id": lead_id,
                "lead_name": lead_name,
                "austin_context": austin_context.__dict__,
                "market_insights": market_insights,
                "neighborhood_recommendations": neighborhood_recs,
                "corporate_insights": corporate_insights,
                "talking_points": talking_points,
                "next_best_actions": self._generate_next_actions(austin_context, market_insights),
                "conversation_starters": self._get_conversation_starters(austin_context),
                "objection_responses": self._get_objection_responses(austin_context),
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Cache analysis
            cache_key = f"austin_analysis:{lead_id}"
            await self.cache.set(cache_key, analysis, ttl=3600)  # 1 hour TTL

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing lead with Austin context: {e}")
            return {"error": str(e)}

    async def generate_austin_response(
        self,
        query: str,
        lead_context: AustinConversationContext,
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate Austin market-aware response to lead queries.

        Incorporates market data, neighborhood insights, and corporate expertise.
        """
        try:
            # Analyze query intent
            query_intent = self._analyze_query_intent(query)

            # Get relevant market data
            market_data = await self._get_relevant_market_data(query_intent, lead_context)

            # Generate context-aware response
            response = await self._generate_contextual_response(
                query, query_intent, lead_context, market_data, conversation_history
            )

            return {
                "response": response,
                "query_intent": query_intent,
                "market_data_used": list(market_data.keys()),
                "confidence_score": self._calculate_response_confidence(response, market_data),
                "suggested_follow_ups": self._get_suggested_follow_ups(query_intent, lead_context),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating Austin response: {e}")
            return {"error": str(e)}

    async def get_neighborhood_match_explanation(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        Generate strategic narrative explaining why a property/neighborhood matches lead needs.
        Provides psychological insights, not just raw stats.
        """
        try:
            neighborhood = property_data.get("neighborhood", "Austin")
            price = property_data.get("price", 0)

            # Get neighborhood analysis
            neighborhood_analysis = await self.market_service.get_neighborhood_analysis(neighborhood)
            if not neighborhood_analysis:
                return f"This property in {neighborhood} offers excellent value in Austin's competitive market."

            # Build explanation based on lead preferences
            explanation_parts = []

            # Employer-based insights
            employer = lead_preferences.get("employer", "").lower()
            if employer in ["apple", "google", "meta", "tesla", "dell"]:
                corp_match = self._get_corporate_neighborhood_match(employer, neighborhood)
                if corp_match:
                    explanation_parts.append(corp_match)

            # Lifestyle alignment
            lifestyle_match = self._get_lifestyle_match(neighborhood_analysis, lead_preferences)
            if lifestyle_match:
                explanation_parts.append(lifestyle_match)

            # Market positioning
            market_position = self._get_market_positioning(property_data, neighborhood_analysis)
            explanation_parts.append(market_position)

            # Investment perspective
            investment_angle = self._get_investment_perspective(neighborhood_analysis, price)
            explanation_parts.append(investment_angle)

            # Combine into narrative
            explanation = " ".join(explanation_parts)

            return explanation

        except Exception as e:
            logger.error(f"Error generating neighborhood match explanation: {e}")
            return "This property offers excellent potential in Austin's dynamic market."

    async def generate_market_timing_advice(
        self,
        lead_context: AustinConversationContext,
        transaction_type: str = "buy"
    ) -> Dict[str, Any]:
        """Generate personalized market timing advice for Austin market."""
        try:
            # Get market timing from service
            property_types = [PropertyType.SINGLE_FAMILY]  # Default
            preferred_neighborhood = None

            if lead_context.preferred_neighborhoods:
                preferred_neighborhood = lead_context.preferred_neighborhoods[0]

            timing_advice = await self.market_service.get_market_timing_advice(
                transaction_type, property_types[0], preferred_neighborhood
            )

            # Enhance with corporate context
            if lead_context.employer:
                corporate_timing = self._get_corporate_timing_context(
                    lead_context.employer, lead_context.relocation_timeline
                )
                timing_advice["corporate_context"] = corporate_timing

            # Add personalized recommendations
            personalized_recs = self._personalize_timing_advice(timing_advice, lead_context)
            timing_advice["personalized_recommendations"] = personalized_recs

            return timing_advice

        except Exception as e:
            logger.error(f"Error generating timing advice: {e}")
            return {"error": str(e)}

    async def setup_lead_alerts(self, lead_context: AustinConversationContext) -> bool:
        """Set up intelligent property alerts for the lead."""
        try:
            from ghl_real_estate_ai.services.property_alerts import AlertCriteria

            # Convert context to alert criteria
            criteria = AlertCriteria(
                lead_id=lead_context.lead_id,
                neighborhoods=lead_context.preferred_neighborhoods,
                work_location=lead_context.employer,
                lifestyle_preferences=lead_context.lifestyle_preferences
            )

            # Add budget if available
            if lead_context.budget_range:
                criteria.min_price = lead_context.budget_range[0]
                criteria.max_price = lead_context.budget_range[1]

            # Set commute requirements
            if lead_context.commute_requirements:
                if "30" in lead_context.commute_requirements or "short" in lead_context.commute_requirements.lower():
                    criteria.max_commute_time = 30
                elif "45" in lead_context.commute_requirements:
                    criteria.max_commute_time = 45

            return await self.alert_system.setup_lead_alerts(criteria)

        except Exception as e:
            logger.error(f"Error setting up lead alerts: {e}")
            return False

    # Private helper methods

    async def _build_austin_context(
        self,
        lead_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> AustinConversationContext:
        """Build Austin-specific conversation context from lead data."""

        # Extract employer information
        employer = self._extract_employer(lead_data, conversation_history)

        # Extract preferences
        neighborhoods = self._extract_neighborhoods(lead_data, conversation_history)
        lifestyle_prefs = self._extract_lifestyle_preferences(lead_data, conversation_history)

        # Determine conversation stage
        stage = self._determine_conversation_stage(conversation_history)

        return AustinConversationContext(
            lead_id=lead_data.get("lead_id", ""),
            employer=employer,
            position_level=lead_data.get("position", ""),
            budget_range=self._extract_budget_range(lead_data),
            preferred_neighborhoods=neighborhoods,
            lifestyle_preferences=lifestyle_prefs,
            family_situation=lead_data.get("family_status", ""),
            current_location=lead_data.get("current_city", ""),
            conversation_stage=stage
        )

    def _extract_employer(self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Optional[str]:
        """Extract employer from lead data or conversation."""
        # Check direct field
        if lead_data.get("employer"):
            return lead_data["employer"]

        # Check conversation history for mentions
        if conversation_history:
            text_content = " ".join([
                msg.get("content", "") for msg in conversation_history
                if isinstance(msg.get("content"), str)
            ]).lower()

            for company in ["apple", "google", "meta", "tesla", "dell", "ibm"]:
                if company in text_content:
                    return company.title()

        return None

    def _extract_neighborhoods(self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Extract preferred neighborhoods from lead data or conversation."""
        neighborhoods = []

        # Check direct preferences
        if lead_data.get("preferred_neighborhoods"):
            neighborhoods.extend(lead_data["preferred_neighborhoods"])

        # Extract from conversation
        if conversation_history:
            text_content = " ".join([
                msg.get("content", "") for msg in conversation_history
                if isinstance(msg.get("content"), str)
            ]).lower()

            austin_neighborhoods = [
                "round rock", "domain", "south lamar", "downtown", "mueller",
                "east austin", "cedar park", "westlake", "north austin"
            ]

            for neighborhood in austin_neighborhoods:
                if neighborhood in text_content and neighborhood.title() not in neighborhoods:
                    neighborhoods.append(neighborhood.title().replace(" ", "_"))

        return neighborhoods

    def _extract_budget_range(self, lead_data: Dict[str, Any]) -> Optional[tuple]:
        """Extract budget range from lead data."""
        min_budget = lead_data.get("min_budget")
        max_budget = lead_data.get("max_budget")

        if min_budget and max_budget:
            return (min_budget, max_budget)
        elif max_budget:
            return (max_budget * 0.8, max_budget)  # Assume 80% of max as minimum

        return None

    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent behind a lead's query."""
        query_lower = query.lower()

        intent = {
            "type": "general",
            "topics": [],
            "urgency": "medium",
            "requires_data": False
        }

        # Neighborhood inquiry
        if any(word in query_lower for word in ["neighborhood", "area", "where", "location"]):
            intent["type"] = "neighborhood_inquiry"
            intent["topics"].append("neighborhoods")
            intent["requires_data"] = True

        # Market conditions
        elif any(word in query_lower for word in ["market", "prices", "trends", "inventory"]):
            intent["type"] = "market_inquiry"
            intent["topics"].append("market_data")
            intent["requires_data"] = True

        # Commute concerns
        elif any(word in query_lower for word in ["commute", "drive", "traffic", "work"]):
            intent["type"] = "commute_inquiry"
            intent["topics"].append("commute")
            intent["requires_data"] = True

        # Schools
        elif any(word in query_lower for word in ["school", "education", "kids", "children"]):
            intent["type"] = "school_inquiry"
            intent["topics"].append("schools")
            intent["requires_data"] = True

        # Timing
        elif any(word in query_lower for word in ["when", "timing", "should i", "good time"]):
            intent["type"] = "timing_inquiry"
            intent["topics"].append("timing")
            intent["urgency"] = "high"
            intent["requires_data"] = True

        # Property specific
        elif any(word in query_lower for word in ["property", "house", "home", "listing"]):
            intent["type"] = "property_inquiry"
            intent["topics"].append("properties")
            intent["requires_data"] = True

        return intent

    async def _get_relevant_market_data(
        self,
        query_intent: Dict[str, Any],
        lead_context: AustinConversationContext
    ) -> Dict[str, Any]:
        """Get relevant market data based on query intent."""
        market_data = {}

        try:
            if "market_data" in query_intent["topics"]:
                # Get overall market metrics
                market_data["metrics"] = await self.market_service.get_market_metrics()

            if "neighborhoods" in query_intent["topics"] and lead_context.preferred_neighborhoods:
                # Get neighborhood data
                neighborhood_data = {}
                for neighborhood in lead_context.preferred_neighborhoods[:3]:  # Limit to 3
                    data = await self.market_service.get_neighborhood_analysis(neighborhood)
                    if data:
                        neighborhood_data[neighborhood] = data.__dict__
                market_data["neighborhoods"] = neighborhood_data

            if "commute" in query_intent["topics"] and lead_context.employer:
                # Get corporate insights
                market_data["corporate"] = await self.market_service.get_corporate_relocation_insights(
                    lead_context.employer, lead_context.position_level
                )

            if "schools" in query_intent["topics"]:
                # Get school district data
                school_data = {}
                for neighborhood in lead_context.preferred_neighborhoods[:2]:
                    # Map neighborhoods to school districts
                    district_name = self._get_school_district_for_neighborhood(neighborhood)
                    if district_name:
                        school_data[district_name] = await self.market_service.get_school_district_info(district_name)
                market_data["schools"] = school_data

            if "timing" in query_intent["topics"]:
                # Get timing advice
                neighborhood = lead_context.preferred_neighborhoods[0] if lead_context.preferred_neighborhoods else None
                market_data["timing"] = await self.market_service.get_market_timing_advice(
                    "buy", PropertyType.SINGLE_FAMILY, neighborhood
                )

        except Exception as e:
            logger.error(f"Error getting market data: {e}")

        return market_data

    async def _generate_contextual_response(
        self,
        query: str,
        query_intent: Dict[str, Any],
        lead_context: AustinConversationContext,
        market_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """Generate contextual response using Austin expertise."""

        # Get base expertise
        expertise = self.austin_expertise.get("neighborhoods", {})
        conversation_starters = self.austin_expertise.get("conversation_starters", {})

        response_parts = []

        # Handle different query types
        if query_intent["type"] == "neighborhood_inquiry":
            response_parts.append(self._generate_neighborhood_response(lead_context, market_data, expertise))

        elif query_intent["type"] == "market_inquiry":
            response_parts.append(self._generate_market_response(market_data, lead_context))

        elif query_intent["type"] == "commute_inquiry":
            response_parts.append(self._generate_commute_response(lead_context, market_data))

        elif query_intent["type"] == "school_inquiry":
            response_parts.append(self._generate_school_response(market_data, lead_context))

        elif query_intent["type"] == "timing_inquiry":
            response_parts.append(self._generate_timing_response(market_data, lead_context))

        else:
            # General response
            response_parts.append(self._generate_general_response(lead_context, conversation_starters))

        # Add Austin-specific insights
        if lead_context.employer and lead_context.employer.lower() in ["apple", "google", "meta", "tesla"]:
            response_parts.append(self._add_corporate_context(lead_context.employer))

        return " ".join(response_parts)

    def _generate_neighborhood_response(
        self,
        lead_context: AustinConversationContext,
        market_data: Dict[str, Any],
        expertise: Dict[str, Any]
    ) -> str:
        """Generate neighborhood-specific response."""

        if not lead_context.preferred_neighborhoods:
            return "I'd be happy to recommend neighborhoods based on your work location and lifestyle preferences. Where will you be working in Austin?"

        neighborhood = lead_context.preferred_neighborhoods[0].lower().replace("_", " ")
        neighborhood_data = expertise.get(neighborhood.replace(" ", "_"), {})

        if not neighborhood_data:
            return f"Let me get you detailed information about {neighborhood.title()} and how it fits with your Austin move."

        elevator_pitch = neighborhood_data.get("elevator_pitch", "")
        key_points = neighborhood_data.get("key_talking_points", [])

        response = f"{elevator_pitch}"

        if key_points:
            response += f" Here are the key advantages: {', '.join(key_points[:3])}."

        # Add employer-specific context
        if lead_context.employer:
            employer_connections = neighborhood_data.get("employer_connections", {})
            employer_data = employer_connections.get(lead_context.employer.lower(), {})
            if employer_data:
                commute = employer_data.get("commute", "")
                appeal = employer_data.get("appeal", "")
                response += f" For {lead_context.employer} employees, {neighborhood.title()} offers {commute} commute and {appeal}."

        return response

    def _generate_market_response(self, market_data: Dict[str, Any], lead_context: AustinConversationContext) -> str:
        """Generate market conditions response."""
        metrics = market_data.get("metrics")
        if not metrics:
            return "Austin's market remains strong with continued growth driven by tech expansion. I can provide specific data for neighborhoods you're considering."

        condition = metrics.market_condition.value.replace("_", " ").title()
        median_price = metrics.median_price
        days_on_market = metrics.average_days_on_market

        response = f"Austin's current market is a {condition} with a median home price of ${median_price:,}. "
        response += f"Properties are averaging {days_on_market} days on market. "

        if metrics.months_supply < 2:
            response += "Inventory is tight, so I recommend being prepared to move quickly on properties that fit your criteria."
        else:
            response += "Inventory levels provide good selection for qualified buyers."

        return response

    def _generate_commute_response(self, lead_context: AustinConversationContext, market_data: Dict[str, Any]) -> str:
        """Generate commute-focused response."""
        if not lead_context.employer:
            return "I can help you find neighborhoods with great commutes once I know where you'll be working in Austin."

        corporate_data = market_data.get("corporate", {})
        if corporate_data:
            recommended_neighborhoods = corporate_data.get("recommended_neighborhoods", [])
            if recommended_neighborhoods:
                response = f"For {lead_context.employer} employees, I typically recommend: "
                recs = [f"{n['name']} ({n['commute']} - {n['appeal']})" for n in recommended_neighborhoods[:3]]
                response += ", ".join(recs) + "."
                return response

        return f"I have extensive experience helping {lead_context.employer} employees find homes with optimal commutes. Let me show you the neighborhoods where your colleagues are choosing to live."

    def _generate_school_response(self, market_data: Dict[str, Any], lead_context: AustinConversationContext) -> str:
        """Generate school district response."""
        school_data = market_data.get("schools", {})

        if not school_data:
            return "Austin area has several excellent school districts. Round Rock ISD, Westlake, and Cedar Park all rank in the top tier. I can provide detailed ratings and boundaries for specific neighborhoods."

        top_districts = []
        for district_name, data in school_data.items():
            if data and data.get("rating", 0) > 8:
                top_districts.append(f"{data['name']} (rated {data['rating']}/10)")

        if top_districts:
            response = f"The top school districts for your consideration are: {', '.join(top_districts)}. "
            response += "These districts consistently rank among Texas's best for academic performance and college readiness."
            return response

        return "I can provide detailed school district information for any neighborhoods you're considering."

    def _generate_timing_response(self, market_data: Dict[str, Any], lead_context: AustinConversationContext) -> str:
        """Generate market timing response."""
        timing_data = market_data.get("timing", {})

        if not timing_data:
            return "Austin's market timing depends on several factors including your employer's relocation timeline and seasonal patterns. I can provide specific timing guidance based on your situation."

        timing_score = timing_data.get("timing_score", 50)
        recommendations = timing_data.get("recommendations", [])
        urgency = timing_data.get("urgency_level", "medium")

        response = f"Based on current market conditions, this is "

        if timing_score > 75:
            response += "an excellent time to buy. "
        elif timing_score > 50:
            response += "a good time to buy. "
        else:
            response += "a challenging time to buy, but opportunities exist. "

        response += f"Urgency level is {urgency}. "

        if recommendations:
            response += f"Key recommendations: {recommendations[0]}."

        return response

    def _generate_general_response(self, lead_context: AustinConversationContext, conversation_starters: Dict[str, Any]) -> str:
        """Generate general helpful response."""
        discovery_questions = conversation_starters.get("discovery_questions", [])
        value_props = conversation_starters.get("value_propositions", [])

        if lead_context.conversation_stage == "discovery":
            if discovery_questions:
                return f"I'd be happy to help! {discovery_questions[0]}"
            return "I specialize in helping tech professionals relocating to Austin. What's most important to you in your new neighborhood?"

        if value_props:
            return value_props[0]

        return "I'm here to help you navigate Austin's market with insights from helping hundreds of tech professionals find their perfect home."

    def _get_corporate_neighborhood_match(self, employer: str, neighborhood: str) -> Optional[str]:
        """Get corporate-specific neighborhood matching insight."""
        expertise = self.austin_expertise.get("neighborhoods", {})
        neighborhood_key = neighborhood.lower().replace(" ", "_")
        neighborhood_data = expertise.get(neighborhood_key, {})

        if not neighborhood_data:
            return None

        employer_connections = neighborhood_data.get("employer_connections", {})
        employer_data = employer_connections.get(employer.lower(), {})

        if employer_data:
            talking_points = employer_data.get("talking_points", [])
            if talking_points:
                return talking_points[0]

        return None

    def _get_lifestyle_match(self, neighborhood_analysis, lead_preferences: Dict[str, Any]) -> Optional[str]:
        """Get lifestyle-based matching insight."""
        lifestyle_highlights = neighborhood_analysis.amenities

        if not lifestyle_highlights:
            return None

        # Match preferences to highlights
        preferences = lead_preferences.get("lifestyle_preferences", [])
        if not preferences:
            return f"The neighborhood offers {', '.join(lifestyle_highlights[:3])}."

        matches = []
        for pref in preferences:
            for highlight in lifestyle_highlights:
                if pref.lower() in highlight.lower():
                    matches.append(highlight)

        if matches:
            return f"This aligns perfectly with your {', '.join(matches[:2])} preferences."

        return None

    def _get_market_positioning(self, property_data: Dict[str, Any], neighborhood_analysis) -> str:
        """Get market positioning insight."""
        property_price = property_data.get("price", 0)
        neighborhood_median = neighborhood_analysis.median_price

        if property_price < neighborhood_median * 0.95:
            return "This property is priced below neighborhood median, offering excellent value."
        elif property_price > neighborhood_median * 1.1:
            return "While premium-priced, this property offers exceptional features for the neighborhood."
        else:
            return "The pricing is well-positioned within the neighborhood range."

    def _get_investment_perspective(self, neighborhood_analysis, price: float) -> str:
        """Get investment perspective on the property."""
        if neighborhood_analysis.price_trend_3m > 5:
            return "The neighborhood shows strong appreciation trends, supporting long-term value growth."
        elif neighborhood_analysis.tech_worker_appeal > 85:
            return "High tech worker appeal ensures strong resale demand and rental potential."
        else:
            return "This represents a solid investment in Austin's growing market."

    def _get_corporate_timing_context(self, employer: str, timeline: str) -> Dict[str, Any]:
        """Get corporate-specific timing context."""
        corporate_data = self.austin_expertise.get("corporate_relocations", {})
        employer_data = corporate_data.get(employer.lower(), {})

        if not employer_data:
            return {}

        timeline_insights = employer_data.get("timeline_insights", [])

        return {
            "employer": employer,
            "peak_periods": timeline_insights,
            "recommendation": f"Based on {employer}'s typical relocation patterns, timing your purchase around their peak hiring periods can provide the best market access and company support."
        }

    def _personalize_timing_advice(self, timing_advice: Dict[str, Any], lead_context: AustinConversationContext) -> List[str]:
        """Personalize timing advice based on lead context."""
        recommendations = []

        # Corporate timeline alignment
        if lead_context.employer and lead_context.relocation_timeline:
            if "60 days" in lead_context.relocation_timeline or "2 months" in lead_context.relocation_timeline:
                recommendations.append("With your 60-day timeline, start house hunting immediately for optimal selection.")
            elif "30 days" in lead_context.relocation_timeline:
                recommendations.append("Your 30-day timeline requires immediate action - I recommend focusing on move-in ready properties.")

        # Family considerations
        if "family" in lead_context.family_situation.lower() if lead_context.family_situation else False:
            recommendations.append("For families, timing the move before the school year provides the smoothest transition.")

        # Budget considerations
        if lead_context.budget_range and lead_context.budget_range[1] > 800000:
            recommendations.append("In the luxury segment, timing is less critical due to lower competition levels.")

        return recommendations

    def _get_school_district_for_neighborhood(self, neighborhood: str) -> Optional[str]:
        """Map neighborhood to school district."""
        district_mapping = {
            "round_rock": "round rock isd",
            "cedar_park": "leander isd",
            "westlake": "eanes isd",
            "mueller": "austin isd",
            "downtown": "austin isd",
            "south_lamar": "austin isd",
            "east_austin": "austin isd",
            "domain": "round rock isd"
        }

        return district_mapping.get(neighborhood.lower().replace(" ", "_"))

    def _determine_conversation_stage(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Determine conversation stage from history."""
        if not conversation_history:
            return "discovery"

        # Analyze conversation for stage indicators
        text_content = " ".join([
            msg.get("content", "") for msg in conversation_history[-5:]  # Last 5 messages
            if isinstance(msg.get("content"), str)
        ]).lower()

        if any(word in text_content for word in ["showing", "tour", "visit", "see the house"]):
            return "showing"
        elif any(word in text_content for word in ["offer", "negotiate", "price", "counter"]):
            return "negotiation"
        elif any(word in text_content for word in ["qualified", "preapproval", "budget", "loan"]):
            return "qualification"
        else:
            return "discovery"

    def _extract_lifestyle_preferences(self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Extract lifestyle preferences from conversation."""
        preferences = []

        # Check direct field
        if lead_data.get("lifestyle_preferences"):
            preferences.extend(lead_data["lifestyle_preferences"])

        # Extract from conversation
        if conversation_history:
            text_content = " ".join([
                msg.get("content", "") for msg in conversation_history
                if isinstance(msg.get("content"), str)
            ]).lower()

            lifestyle_keywords = {
                "walkable": ["walk", "walkable", "pedestrian", "walkability"],
                "nightlife": ["nightlife", "bars", "entertainment", "dining"],
                "family-friendly": ["family", "kids", "children", "schools", "parks"],
                "quiet": ["quiet", "peaceful", "calm", "residential"],
                "urban": ["urban", "city", "downtown", "high-rise"],
                "suburban": ["suburban", "suburbs", "yard", "space"]
            }

            for pref, keywords in lifestyle_keywords.items():
                if any(keyword in text_content for keyword in keywords) and pref not in preferences:
                    preferences.append(pref)

        return preferences

    def _generate_next_actions(self, austin_context: AustinConversationContext, market_insights: Dict[str, Any]) -> List[str]:
        """Generate next best actions for the lead."""
        actions = []

        # Stage-specific actions
        if austin_context.conversation_stage == "discovery":
            actions.append("Complete needs assessment questionnaire")
            actions.append("Schedule neighborhood tour based on work location")
            if austin_context.employer:
                actions.append(f"Provide {austin_context.employer}-specific relocation guide")

        elif austin_context.conversation_stage == "qualification":
            actions.append("Connect with preferred lender for pre-approval")
            actions.append("Set up property alerts based on criteria")
            actions.append("Schedule home search strategy call")

        elif austin_context.conversation_stage == "showing":
            actions.append("Book property showings for this weekend")
            actions.append("Prepare market analysis for target properties")
            actions.append("Research neighborhood comparables")

        # Market-driven actions
        market_condition = market_insights.get("market_condition", "")
        if "strong_sellers" in market_condition:
            actions.append("Prepare competitive offer strategy")
            actions.append("Secure financing pre-approval letter")

        # Corporate-specific actions
        if austin_context.employer:
            actions.append(f"Review {austin_context.employer} relocation benefits")
            actions.append("Connect with corporate relocation coordinator")

        return actions[:5]  # Limit to top 5

    def _get_conversation_starters(self, austin_context: AustinConversationContext) -> List[str]:
        """Get conversation starters based on context."""
        starters = self.austin_expertise.get("conversation_starters", {}).get("discovery_questions", [])

        # Customize based on context
        customized = []

        if austin_context.employer:
            customized.append(f"How is {austin_context.employer} supporting your relocation to Austin?")
            customized.append("Have you had a chance to visit Austin yet, or will this be your first time?")

        if austin_context.family_situation and "family" in austin_context.family_situation.lower():
            customized.append("What's most important for your family in choosing a neighborhood - schools, activities, or community?")

        # Add generic starters
        customized.extend(starters[:3])

        return customized[:5]

    def _get_objection_responses(self, austin_context: AustinConversationContext) -> Dict[str, str]:
        """Get objection responses relevant to the lead's context."""
        objections = self.austin_expertise.get("objection_handling", {})

        relevant_objections = {}

        # Always include common objections
        if "price_concerns" in objections:
            relevant_objections["price"] = objections["price_concerns"]["response"]

        if "commute_concerns" in objections:
            relevant_objections["commute"] = objections["commute_concerns"]["response"]

        # Add context-specific objections
        if austin_context.family_situation and "family" in austin_context.family_situation.lower():
            if "school_concerns" in objections:
                relevant_objections["schools"] = objections["school_concerns"]["response"]

        if austin_context.current_location and any(city in austin_context.current_location.lower()
            for city in ["san francisco", "seattle", "new york", "california"]):
            if "culture_concerns" in objections:
                relevant_objections["culture"] = objections["culture_concerns"]["response"]

        return relevant_objections

    def _calculate_response_confidence(self, response: str, market_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the response."""
        confidence = 70  # Base confidence

        # Increase confidence based on data availability
        if market_data.get("metrics"):
            confidence += 10
        if market_data.get("neighborhoods"):
            confidence += 10
        if market_data.get("corporate"):
            confidence += 5

        # Decrease confidence for generic responses
        if len(response) < 100:
            confidence -= 15

        # Response quality indicators
        if any(term in response.lower() for term in ["specifically", "exactly", "precisely"]):
            confidence += 5

        return min(95, max(30, confidence))

    def _get_suggested_follow_ups(self, query_intent: Dict[str, Any], lead_context: AustinConversationContext) -> List[str]:
        """Get suggested follow-up questions."""
        follow_ups = []

        if query_intent["type"] == "neighborhood_inquiry":
            follow_ups.extend([
                "Would you like to see current inventory in this neighborhood?",
                "Should I set up property alerts for this area?",
                "Would you like to schedule a neighborhood tour?"
            ])

        elif query_intent["type"] == "market_inquiry":
            follow_ups.extend([
                "Would you like a detailed market report for your target areas?",
                "Should I show you how this compares to your current market?",
                "Would you like pricing trends for specific neighborhoods?"
            ])

        elif query_intent["type"] == "commute_inquiry":
            follow_ups.extend([
                "Would you like me to map optimal commute neighborhoods?",
                "Should I check for corporate shuttle routes?",
                "Would you like to see where your colleagues are living?"
            ])

        # Add general follow-ups
        if lead_context.conversation_stage == "discovery":
            follow_ups.append("What other questions do you have about Austin?")

        return follow_ups[:3]

    def _add_corporate_context(self, employer: str) -> str:
        """Add corporate-specific context to responses."""
        corporate_advantages = self.austin_expertise.get("competitive_advantages", {}).get("austin_advantages", [])

        context_map = {
            "apple": f"Many Apple employees particularly value Austin's no state income tax, which effectively increases your take-home pay significantly.",
            "google": f"Google employees often appreciate Austin's creative culture and the city's commitment to innovation and sustainability.",
            "meta": f"Austin's tech community provides excellent networking opportunities for Meta professionals, with regular industry meetups and events.",
            "tesla": f"Tesla employees love Austin's commitment to sustainability and the city's support for electric vehicle infrastructure."
        }

        return context_map.get(employer.lower(), f"Austin's business-friendly environment and quality of life make it ideal for {employer} professionals.")


# Global service instance
_austin_ai_assistant = None

def get_austin_ai_assistant() -> AustinAIAssistant:
    """Get singleton instance of Austin AI Assistant."""
    global _austin_ai_assistant
    if _austin_ai_assistant is None:
        _austin_ai_assistant = AustinAIAssistant()
    return _austin_ai_assistant