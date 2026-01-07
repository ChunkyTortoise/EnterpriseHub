#!/usr/bin/env python3
"""
AI Content Personalization Service
Delivers personalized content and property recommendations based on AI analysis
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class AIContentPersonalizationService:
    """
    AI-powered content personalization engine

    Features:
    - Personalized property recommendations
    - Dynamic content adaptation
    - Behavioral learning
    - Multi-channel personalization
    - A/B testing integration
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.personalization_cache = {}

    async def personalize_content(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        content_type: str = "property_recommendations",
    ) -> Dict[str, Any]:
        """
        Generate personalized content for a lead

        Args:
            lead_id: Unique lead identifier
            lead_data: Lead profile and behavior data
            content_type: Type of content to personalize

        Returns:
            Personalized content recommendations
        """
        if content_type == "property_recommendations":
            return await self._property_recommendations(lead_id, lead_data)
        elif content_type == "email_content":
            return await self._email_personalization(lead_id, lead_data)
        elif content_type == "landing_page":
            return await self._landing_page_personalization(lead_id, lead_data)
        elif content_type == "messaging":
            return await self._messaging_personalization(lead_id, lead_data)
        else:
            return await self._auto_personalization(lead_id, lead_data)

    async def _property_recommendations(
        self, lead_id: str, lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized property recommendations"""

        preferences = lead_data.get("preferences", {})
        budget = lead_data.get("budget", 0)
        behavior = lead_data.get("behavior", {})

        # Score properties based on preferences
        recommendations = []

        # High priority matches
        if budget > 800000:
            recommendations.append(
                {
                    "property_id": "prop_luxury_001",
                    "title": "Luxury Waterfront Estate",
                    "price": 1200000,
                    "match_score": 95,
                    "why_recommended": "Matches your luxury preference and waterfront interest",
                    "personalized_message": "This exclusive property offers the premium lifestyle you're seeking",
                    "images": ["img1.jpg", "img2.jpg"],
                    "priority": "high",
                }
            )

        # Budget-appropriate options
        recommendations.append(
            {
                "property_id": "prop_mid_002",
                "title": "Modern Downtown Condo",
                "price": budget * 0.9,  # Slightly under budget
                "match_score": 88,
                "why_recommended": "Perfect fit for your budget and location preferences",
                "personalized_message": f"Great value at ${budget * 0.9:,.0f} - within your ${budget:,.0f} budget",
                "images": ["img3.jpg", "img4.jpg"],
                "priority": "medium",
            }
        )

        # Stretch option
        recommendations.append(
            {
                "property_id": "prop_stretch_003",
                "title": "Premium Family Home",
                "price": budget * 1.1,  # Slightly over budget
                "match_score": 82,
                "why_recommended": "Worth stretching for - exceptional value and features",
                "personalized_message": "This home offers more space and amenities for a modest increase",
                "images": ["img5.jpg", "img6.jpg"],
                "priority": "low",
            }
        )

        return {
            "lead_id": lead_id,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "personalization_factors": [
                "Budget alignment",
                "Location preferences",
                "Property type interest",
                "Browsing history",
                "Engagement patterns",
            ],
            "next_best_action": self._get_next_action(lead_data),
            "timestamp": datetime.now().isoformat(),
        }

    async def _email_personalization(
        self, lead_id: str, lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Personalize email content"""

        name = lead_data.get("name", "Valued Client")
        engagement = lead_data.get("engagement_score", 50)
        last_interaction = lead_data.get("last_interaction", "website visit")

        # Determine email tone and content
        if engagement > 70:
            tone = "enthusiastic"
            subject = f"{name}, Your Dream Properties Are Here! 🏠"
            content = f"Hi {name}! We found amazing properties matching exactly what you're looking for..."
        elif engagement > 40:
            tone = "helpful"
            subject = f"{name}, New Listings You'll Love"
            content = f"Hello {name}, Based on your recent {last_interaction}, we think you'll love these..."
        else:
            tone = "informative"
            subject = f"{name}, Market Update & Property Insights"
            content = f"Hi {name}, Staying informed helps you make the best decision. Here's what's new..."

        return {
            "lead_id": lead_id,
            "email_content": {
                "subject": subject,
                "preview_text": content[:50] + "...",
                "body": content,
                "tone": tone,
                "personalization_tokens": {
                    "first_name": name.split()[0] if name else "Friend",
                    "last_interaction": last_interaction,
                    "recommended_properties": 3,
                },
            },
            "send_time_recommendation": self._optimal_send_time(lead_data),
            "a_b_test_variant": "A" if engagement > 60 else "B",
        }

    async def _landing_page_personalization(
        self, lead_id: str, lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Personalize landing page experience"""

        source = lead_data.get("source", "organic")
        device = lead_data.get("device", "desktop")
        location = lead_data.get("location", "Unknown")

        return {
            "lead_id": lead_id,
            "page_config": {
                "hero_headline": f"Find Your Perfect Home in {location}",
                "hero_subtext": "Personalized property matches based on your preferences",
                "cta_text": (
                    "See My Matches" if source == "paid" else "Explore Properties"
                ),
                "featured_properties": 3,
                "layout": "mobile_optimized" if device == "mobile" else "desktop_full",
                "testimonial_focus": "local" if location != "Unknown" else "general",
            },
            "dynamic_elements": [
                "Location-based property showcase",
                "Personalized search filters",
                "Recent activity highlights",
                "Smart recommendations widget",
            ],
        }

    async def _messaging_personalization(
        self, lead_id: str, lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Personalize chat/SMS messaging"""

        engagement = lead_data.get("engagement_score", 50)
        response_time = lead_data.get("avg_response_time_hours", 24)

        if engagement > 80:
            urgency = "high"
            message = "Quick question - when would you like to schedule a viewing?"
        elif engagement > 50:
            urgency = "medium"
            message = "I have some exciting new listings to share. Interested?"
        else:
            urgency = "low"
            message = (
                "Hope you're doing well! Just checking in to see if you need anything."
            )

        return {
            "lead_id": lead_id,
            "message_template": message,
            "urgency": urgency,
            "channel_preference": "sms" if response_time < 4 else "email",
            "follow_up_timing": f"{response_time} hours",
        }

    async def _auto_personalization(
        self, lead_id: str, lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Automatic multi-channel personalization"""

        property_recs = await self._property_recommendations(lead_id, lead_data)
        email_content = await self._email_personalization(lead_id, lead_data)

        return {
            "lead_id": lead_id,
            "personalization_suite": {
                "properties": property_recs,
                "email": email_content,
                "overall_strategy": self._get_personalization_strategy(lead_data),
            },
        }

    def _get_next_action(self, lead_data: Dict[str, Any]) -> str:
        """Determine next best action for lead"""
        engagement = lead_data.get("engagement_score", 50)
        last_activity = lead_data.get("last_activity_days_ago", 999)

        if engagement > 80 and last_activity < 3:
            return "Schedule immediate phone call"
        elif engagement > 60:
            return "Send personalized property recommendations"
        elif last_activity > 30:
            return "Launch re-engagement campaign"
        else:
            return "Continue nurturing with weekly content"

    def _optimal_send_time(self, lead_data: Dict[str, Any]) -> str:
        """Calculate optimal send time"""
        timezone = lead_data.get("timezone", "EST")
        engagement_history = lead_data.get("engagement_history", {})

        # Simple heuristic - best times are usually morning or lunch
        return "9:00 AM local time"

    def _get_personalization_strategy(self, lead_data: Dict[str, Any]) -> Dict:
        """Define overall personalization strategy"""
        engagement = lead_data.get("engagement_score", 50)

        if engagement > 70:
            strategy = "aggressive_conversion"
            focus = "High-touch, personalized outreach"
        elif engagement > 40:
            strategy = "nurture_and_educate"
            focus = "Value-add content and property matches"
        else:
            strategy = "re_engagement"
            focus = "Win-back campaigns and market updates"

        return {
            "strategy": strategy,
            "focus": focus,
            "channels": ["email", "sms", "retargeting"],
            "frequency": "3x per week" if engagement > 60 else "1x per week",
        }


# Demo/Test function
async def demo_personalization():
    """Demo the personalization service"""
    service = AIContentPersonalizationService()

    sample_lead = {
        "name": "Jane Smith",
        "budget": 650000,
        "engagement_score": 78,
        "last_activity_days_ago": 2,
        "location": "Austin, TX",
        "device": "mobile",
        "source": "paid",
        "preferences": {
            "property_type": "single_family",
            "bedrooms": 3,
            "location": "suburban",
        },
    }

    result = await service.personalize_content(
        lead_id="lead_demo_001",
        lead_data=sample_lead,
        content_type="property_recommendations",
    )

    print("🎨 Content Personalization Results:")
    print(f"Lead: {sample_lead['name']}")
    print(f"Total Recommendations: {result['total_recommendations']}")
    print("\nTop Recommendation:")
    top_rec = result["recommendations"][0]
    print(f"  {top_rec['title']} - ${top_rec['price']:,.0f}")
    print(f"  Match Score: {top_rec['match_score']}/100")
    print(f"  Why: {top_rec['why_recommended']}")

    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_personalization())
