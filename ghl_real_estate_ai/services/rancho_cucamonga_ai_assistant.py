"""
Rancho Cucamonga AI Assistant - Enhanced Claude integration with Inland Empire market expertise.

Enhances the existing ClaudeAssistant with Rancho Cucamonga/Inland Empire-specific market intelligence,
logistics/healthcare relocation expertise, and neighborhood insights for Jorge's lead bot.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import logging

from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.cache_service import get_cache_service
# from ghl_real_estate_ai.services.property_alerts import get_property_alert_system  # Optional import
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RanchoCucamongaConversationContext:
    """Context for Rancho Cucamonga/Inland Empire-specific conversations."""
    lead_id: str
    employer: Optional[str] = None  # Amazon, Kaiser, UPS, FedEx, etc.
    position_level: Optional[str] = None
    relocation_timeline: Optional[str] = None
    budget_range: Optional[tuple] = None
    preferred_neighborhoods: List[str] = None
    commute_requirements: Optional[str] = None
    lifestyle_preferences: List[str] = None
    family_situation: Optional[str] = None
    current_location: Optional[str] = None
    conversation_stage: str = "discovery"  # discovery, qualification, showing, negotiation
    shift_schedule: Optional[str] = None  # For logistics/healthcare workers
    school_priority: bool = False

    def __post_init__(self):
        if self.preferred_neighborhoods is None:
            self.preferred_neighborhoods = []
        if self.lifestyle_preferences is None:
            self.lifestyle_preferences = []


class RanchoCucamongaAIAssistant(ClaudeAssistant):
    """
    Enhanced Claude Assistant with Rancho Cucamonga/Inland Empire real estate market expertise.

    Provides context-aware responses for logistics/healthcare relocations,
    neighborhood expertise, and market intelligence.
    """

    def __init__(self):
        super().__init__()
        # self.market_service = get_rancho_cucamonga_market_service()  # Optional service
        # self.property_alerts = get_property_alert_system()  # Optional service
        self.cache = get_cache_service()
        self.rc_expertise = self._get_default_rc_expertise()

    def _get_default_rc_expertise(self) -> Dict[str, Any]:
        """Return default RC expertise if file not found."""
        return {
            "neighborhoods": {
                "alta_loma": {
                    "elevator_pitch": "Alta Loma offers luxury living with mountain views and excellent schools.",
                    "key_talking_points": ["Mountain views", "Excellent schools", "Luxury homes", "Family-friendly"],
                    "employer_connections": {
                        "amazon": {
                            "commute": "25-minute drive to fulfillment centers",
                            "appeal": "quiet residential setting perfect for shift workers",
                            "talking_points": ["Peaceful environment for rest between shifts", "Great schools for families"]
                        }
                    }
                },
                "etiwanda": {
                    "elevator_pitch": "Etiwanda provides excellent value with new developments and top-rated schools.",
                    "key_talking_points": ["New construction", "Top schools", "Family neighborhoods", "Value pricing"],
                    "employer_connections": {
                        "amazon": {
                            "commute": "20-minute drive to logistics centers",
                            "appeal": "modern amenities and growing community",
                            "talking_points": ["New homes with modern features", "Growing community of young professionals"]
                        }
                    }
                }
            }
        }

    async def generate_market_response(
        self,
        context: RanchoCucamongaConversationContext,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent response with Rancho Cucamonga market context.

        Args:
            context: Conversation context with lead information
            user_message: Current user message
            conversation_history: Previous conversation history

        Returns:
            Dict containing response and suggested actions
        """
        try:
            # Get market intelligence based on context
            market_data = await self._get_contextual_market_data(context)

            # Build enhanced prompt with IE market expertise
            enhanced_prompt = await self._build_enhanced_prompt(
                context, user_message, market_data, conversation_history
            )

            # Generate Claude response
            response = await self.generate_response(
                enhanced_prompt,
                conversation_history or []
            )

            # Add market-specific suggestions
            suggestions = await self._generate_action_suggestions(context, response)

            return {
                "response": response,
                "suggestions": suggestions,
                "market_data": market_data,
                "context_updates": await self._extract_context_updates(user_message, response)
            }

        except Exception as e:
            logger.error(f"Error generating market response: {str(e)}")
            return {
                "response": "I apologize, but I'm having trouble accessing market data. Let me help you with your Inland Empire real estate needs in another way.",
                "suggestions": [],
                "market_data": {},
                "context_updates": {}
            }

    async def _get_contextual_market_data(self, context: RanchoCucamongaConversationContext) -> Dict[str, Any]:
        """Get relevant market data based on conversation context."""
        market_data = {}

        try:
            # Get general market metrics
            if context.preferred_neighborhoods:
                for neighborhood in context.preferred_neighborhoods[:3]:  # Limit to avoid overload
                    # Mock market data for now - replace with actual service calls when available
                    market_data[f"neighborhood_{neighborhood}"] = {
                        "median_price": 750000,
                        "price_trend": "5.2% YoY",
                        "days_on_market": 18,
                        "inventory_level": "2.1 months"
                    }

            # Get corporate insights if employer known
            if context.employer:
                # Mock corporate insights - replace with actual service when available
                market_data["corporate_insights"] = {
                    "employer": context.employer,
                    "common_commute": "15-25 minutes to logistics centers",
                    "popular_neighborhoods": ["Etiwanda", "Alta Loma", "North RC"],
                    "relocation_support": "Most companies offer assistance"
                }

            # Mock timing advice
            market_data["timing_advice"] = {
                "market_condition": "Strong seller's market",
                "timing_score": 75,
                "recommendations": ["Act quickly on good properties", "Get pre-approved"],
                "urgency_level": "medium"
            }

        except Exception as e:
            logger.warning(f"Error fetching contextual market data: {str(e)}")

        return market_data

    async def _build_enhanced_prompt(
        self,
        context: RanchoCucamongaConversationContext,
        user_message: str,
        market_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Build enhanced prompt with IE market expertise."""

        # Base Jorge persona
        prompt = """
You are Jorge Martinez, a top Inland Empire real estate agent specializing in logistics and healthcare worker relocations to Rancho Cucamonga and surrounding areas. You have deep expertise in:

- Logistics industry needs (Amazon, UPS, FedEx workers)
- Healthcare professional relocations (Kaiser, hospitals)
- Etiwanda and Central Elementary school districts
- Commute optimization to LA/Orange County
- Investment properties in the Inland Empire
"""

        # Add context-specific expertise
        if context.employer:
            if "amazon" in context.employer.lower():
                prompt += "\n\nYou're speaking with an Amazon employee. Focus on proximity to fulfillment centers, shift work considerations, and neighborhoods popular with logistics workers."
            elif "kaiser" in context.employer.lower():
                prompt += "\n\nYou're speaking with a Kaiser Permanente employee. Emphasize healthcare-friendly communities, school quality, and professional neighborhoods."

        # Add market intelligence
        if market_data:
            prompt += f"\n\nCurrent Market Intelligence:\n{json.dumps(market_data, indent=2, default=str)}"

        # Add conversation context
        if context.preferred_neighborhoods:
            prompt += f"\n\nClient has expressed interest in: {', '.join(context.preferred_neighborhoods)}"

        if context.budget_range:
            prompt += f"\n\nBudget range: ${context.budget_range[0]:,} - ${context.budget_range[1]:,}"

        # Add conversation stage guidance
        stage_guidance = {
            "discovery": "Focus on understanding their needs, timeline, and priorities. Ask about work location, family situation, and lifestyle preferences.",
            "qualification": "Dive deeper into budget, financing, and specific requirements. Provide market education and set realistic expectations.",
            "showing": "Use market data to explain property values and neighborhood benefits. Connect features to their specific needs.",
            "negotiation": "Leverage market knowledge to guide strategy. Use timing and competition data to inform decisions."
        }

        prompt += f"\n\nConversation Stage: {context.conversation_stage}"
        prompt += f"\nGuidance: {stage_guidance.get(context.conversation_stage, 'Provide helpful, market-informed responses.')}"

        prompt += f"\n\nUser Message: {user_message}"
        prompt += "\n\nProvide a helpful, market-informed response that demonstrates your Inland Empire expertise:"

        return prompt

    async def _generate_action_suggestions(
        self,
        context: RanchoCucamongaConversationContext,
        response: str
    ) -> List[Dict[str, Any]]:
        """Generate intelligent action suggestions based on context and response."""
        suggestions = []

        try:
            # Property search suggestions
            if any(keyword in response.lower() for keyword in ["show", "properties", "homes", "listings"]):
                suggestions.append({
                    "action": "property_search",
                    "title": "Search Rancho Cucamonga Properties",
                    "description": "Find properties matching client criteria",
                    "priority": "high"
                })

            # Neighborhood analysis
            if any(keyword in response.lower() for keyword in ["neighborhood", "area", "location"]):
                suggestions.append({
                    "action": "neighborhood_analysis",
                    "title": "Neighborhood Intelligence Report",
                    "description": "Generate detailed neighborhood comparison",
                    "priority": "medium"
                })

            # School information
            if context.school_priority or "school" in response.lower():
                suggestions.append({
                    "action": "school_research",
                    "title": "School District Analysis",
                    "description": "Etiwanda vs Central Elementary comparison",
                    "priority": "high"
                })

            # Market timing
            if any(keyword in response.lower() for keyword in ["market", "timing", "buy", "sell"]):
                suggestions.append({
                    "action": "market_timing",
                    "title": "Market Timing Analysis",
                    "description": "Current IE market conditions and timing advice",
                    "priority": "medium"
                })

            # Corporate relocation
            if context.employer and any(keyword in response.lower() for keyword in ["relocation", "move", "company"]):
                suggestions.append({
                    "action": "relocation_package",
                    "title": "Corporate Relocation Guide",
                    "description": f"Specialized guide for {context.employer} employees",
                    "priority": "high"
                })

        except Exception as e:
            logger.warning(f"Error generating action suggestions: {str(e)}")

        return suggestions

    async def _extract_context_updates(self, user_message: str, response: str) -> Dict[str, Any]:
        """Extract context updates from conversation."""
        updates = {}

        try:
            # Extract employer information
            employers = ["amazon", "kaiser", "ups", "fedex", "usps", "dhl"]
            for employer in employers:
                if employer in user_message.lower():
                    updates["employer"] = employer.title()
                    break

            # Extract budget information
            if "$" in user_message and any(word in user_message.lower() for word in ["budget", "price", "afford"]):
                # Simple extraction - in production, use more sophisticated NLP
                import re
                prices = re.findall(r'\$([0-9,]+)', user_message.replace(",", ""))
                if prices:
                    try:
                        price = int(prices[0].replace(",", ""))
                        updates["budget_indication"] = price
                    except ValueError:
                        pass

            # Extract neighborhood preferences
            ie_neighborhoods = ["etiwanda", "alta loma", "central", "victoria gardens", "terra vista", "day creek"]
            mentioned_neighborhoods = [n for n in ie_neighborhoods if n in user_message.lower()]
            if mentioned_neighborhoods:
                updates["mentioned_neighborhoods"] = mentioned_neighborhoods

            # Extract family situation
            family_keywords = ["family", "children", "kids", "school", "spouse", "married"]
            if any(keyword in user_message.lower() for keyword in family_keywords):
                updates["family_indicators"] = True

        except Exception as e:
            logger.warning(f"Error extracting context updates: {str(e)}")

        return updates

    async def explain_ie_market_advantage(
        self,
        comparison_location: str = "Los Angeles",
        buyer_profile: str = "logistics_worker"
    ) -> str:
        """Explain Inland Empire market advantages vs other locations."""

        cache_key = f"ie_advantage:{comparison_location}:{buyer_profile}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        prompt = f"""
As Jorge Martinez, explain why the Inland Empire (specifically Rancho Cucamonga) is a better choice than {comparison_location} for a {buyer_profile.replace('_', ' ')}. Focus on:

1. Cost of living and housing affordability
2. Employment opportunities in logistics/healthcare
3. Quality of life and family amenities
4. Commute considerations and reverse commute advantage
5. Investment potential and market stability

Provide a compelling but factual comparison that addresses common concerns.
"""

        try:
            response = await self.generate_response(prompt, [])
            await self.cache.set(cache_key, response, ttl=3600)  # Cache for 1 hour
            return response
        except Exception as e:
            logger.error(f"Error generating IE advantage explanation: {str(e)}")
            return "The Inland Empire offers exceptional value for logistics and healthcare professionals, with affordable housing, strong employment, and excellent quality of life."


# Singleton instance
_rancho_cucamonga_ai_assistant = None

def get_rancho_cucamonga_ai_assistant() -> RanchoCucamongaAIAssistant:
    """Get singleton instance of Rancho Cucamonga AI Assistant."""
    global _rancho_cucamonga_ai_assistant
    if _rancho_cucamonga_ai_assistant is None:
        _rancho_cucamonga_ai_assistant = RanchoCucamongaAIAssistant()
    return _rancho_cucamonga_ai_assistant

# Backward compatibility - alias the old function to new one
def get_austin_ai_assistant() -> RanchoCucamongaAIAssistant:
    """Backward compatibility alias for Austin AI Assistant."""
    return get_rancho_cucamonga_ai_assistant()