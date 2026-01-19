"""
Competitive Response System for Jorge's Lead Bot

This module provides Jorge-specific competitive positioning messages,
value proposition reinforcement, and differentiation tactics without
disparaging competitors.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import random

from ghl_real_estate_ai.services.competitor_intelligence import RiskLevel, CompetitorMention


class ResponseType(Enum):
    """Types of competitive responses"""
    POSITIONING = "positioning"
    VALUE_PROP = "value_proposition"
    URGENCY = "urgency"
    DIFFERENTIATION = "differentiation"
    RECOVERY = "recovery"
    NURTURE = "nurture"


class LeadProfile(Enum):
    """Lead profile types for targeted messaging"""
    FIRST_TIME_BUYER = "first_time_buyer"
    INVESTOR = "investor"
    LUXURY_BUYER = "luxury_buyer"
    RELOCATING = "relocating"
    SELLER = "seller"
    DOWNSIZER = "downsizer"


@dataclass
class ResponseTemplate:
    """Template for competitive response messages"""
    message: str
    response_type: ResponseType
    risk_level: RiskLevel
    lead_profile: Optional[LeadProfile]
    urgency_level: int  # 1-5 scale
    follow_up_required: bool
    tags: List[str]
    success_rate: float  # Historical success rate


class CompetitiveResponseSystem:
    """
    Jorge-specific competitive response system

    Features:
    - Professional competitive positioning without disparaging competitors
    - Value proposition reinforcement with Jorge's unique advantages
    - Urgency creation and differentiation tactics
    - Rancho Cucamonga/Inland Empire market-specific positioning
    """

    def __init__(self):
        self.response_templates = self._load_response_templates()
        self.jorge_value_props = self._load_jorge_value_propositions()
        self.rc_advantages = self._load_rc_market_advantages()
        self.success_stories = self._load_success_stories()

    def _load_response_templates(self) -> Dict[RiskLevel, Dict[ResponseType, List[ResponseTemplate]]]:
        """Load competitive response templates organized by risk level and type"""
        return {
            RiskLevel.LOW: {
                ResponseType.POSITIONING: [
                    ResponseTemplate(
                        message="I'd love to understand what you're looking for in an agent to ensure I'm the right fit for your needs. What's most important to you in this process?",
                        response_type=ResponseType.POSITIONING,
                        risk_level=RiskLevel.LOW,
                        lead_profile=None,
                        urgency_level=1,
                        follow_up_required=False,
                        tags=["discovery", "needs_assessment"],
                        success_rate=0.75
                    ),
                    ResponseTemplate(
                        message="Great question! I focus on combining cutting-edge technology with personalized service. Every client gets real-time market insights and my full attention throughout the process.",
                        response_type=ResponseType.POSITIONING,
                        risk_level=RiskLevel.LOW,
                        lead_profile=None,
                        urgency_level=2,
                        follow_up_required=False,
                        tags=["technology", "personalized_service"],
                        success_rate=0.72
                    )
                ],
                ResponseType.VALUE_PROP: [
                    ResponseTemplate(
                        message="What sets me apart is my AI-powered market analysis combined with deep Inland Empire knowledge. I provide insights others simply can't access, helping clients make faster, smarter decisions.",
                        response_type=ResponseType.VALUE_PROP,
                        risk_level=RiskLevel.LOW,
                        lead_profile=None,
                        urgency_level=2,
                        follow_up_required=False,
                        tags=["ai_technology", "market_insights", "rc_expertise"],
                        success_rate=0.78
                    )
                ]
            },

            RiskLevel.MEDIUM: {
                ResponseType.POSITIONING: [
                    ResponseTemplate(
                        message="I completely understand you're exploring your options - that's exactly what smart buyers do! I'd love to show you what makes my approach different and how it could benefit your specific situation.",
                        response_type=ResponseType.POSITIONING,
                        risk_level=RiskLevel.MEDIUM,
                        lead_profile=None,
                        urgency_level=3,
                        follow_up_required=True,
                        tags=["validation", "differentiation"],
                        success_rate=0.65
                    ),
                    ResponseTemplate(
                        message="Smart to shop around! Most agents use the same old playbook. I combine AI technology with 24/7 availability to find opportunities others miss. Want to see how this works?",
                        response_type=ResponseType.POSITIONING,
                        risk_level=RiskLevel.MEDIUM,
                        lead_profile=None,
                        urgency_level=3,
                        follow_up_required=True,
                        tags=["technology_edge", "availability"],
                        success_rate=0.68
                    )
                ],
                ResponseType.DIFFERENTIATION: [
                    ResponseTemplate(
                        message="Here's what's different about working with me: I provide real-time market data, off-market opportunities, and investor-grade analysis for every property. Most agents can't offer this level of insight.",
                        response_type=ResponseType.DIFFERENTIATION,
                        risk_level=RiskLevel.MEDIUM,
                        lead_profile=LeadProfile.INVESTOR,
                        urgency_level=3,
                        follow_up_required=True,
                        tags=["market_data", "off_market", "investor_focus"],
                        success_rate=0.71
                    ),
                    ResponseTemplate(
                        message="What makes me unique in Rancho Cucamonga is my specialization in Amazon logistics and healthcare worker relocations. I understand the timeline pressures and housing preferences better than traditional agents.",
                        response_type=ResponseType.DIFFERENTIATION,
                        risk_level=RiskLevel.MEDIUM,
                        lead_profile=LeadProfile.RELOCATING,
                        urgency_level=4,
                        follow_up_required=True,
                        tags=["amazon_relocations", "healthcare_workers", "timeline_pressure"],
                        success_rate=0.74
                    )
                ],
                ResponseType.URGENCY: [
                    ResponseTemplate(
                        message="Rancho Cucamonga's market is moving incredibly fast right now. The properties I found for clients last week are already under contract. Want me to set up alerts for your criteria so you don't miss opportunities?",
                        response_type=ResponseType.URGENCY,
                        risk_level=RiskLevel.MEDIUM,
                        lead_profile=None,
                        urgency_level=4,
                        follow_up_required=True,
                        tags=["market_speed", "opportunity_alerts"],
                        success_rate=0.69
                    )
                ]
            },

            RiskLevel.HIGH: {
                ResponseType.RECOVERY: [
                    ResponseTemplate(
                        message="I completely respect that you're working with someone else. If for any reason that doesn't work out, I'm here to help. No pressure - just want you to know you have options.",
                        response_type=ResponseType.RECOVERY,
                        risk_level=RiskLevel.HIGH,
                        lead_profile=None,
                        urgency_level=2,
                        follow_up_required=True,
                        tags=["respectful", "backup_option"],
                        success_rate=0.45
                    ),
                    ResponseTemplate(
                        message="Even with an agent, would you like a second opinion on any properties or market analysis? I provide complimentary insights - no strings attached.",
                        response_type=ResponseType.RECOVERY,
                        risk_level=RiskLevel.HIGH,
                        lead_profile=None,
                        urgency_level=3,
                        follow_up_required=True,
                        tags=["second_opinion", "complimentary_service"],
                        success_rate=0.52
                    )
                ],
                ResponseType.VALUE_PROP: [
                    ResponseTemplate(
                        message="No worries about your current agent! I specialize in investor properties and off-market deals that most agents never see. Happy to share these opportunities even if we don't work together directly.",
                        response_type=ResponseType.VALUE_PROP,
                        risk_level=RiskLevel.HIGH,
                        lead_profile=LeadProfile.INVESTOR,
                        urgency_level=3,
                        follow_up_required=True,
                        tags=["investor_specialist", "off_market", "value_add"],
                        success_rate=0.48
                    )
                ],
                ResponseType.NURTURE: [
                    ResponseTemplate(
                        message="I understand you're committed to your current agent. Would it be helpful if I sent you weekly Inland Empire market insights? I share data that benefits all buyers, regardless of who represents them.",
                        response_type=ResponseType.NURTURE,
                        risk_level=RiskLevel.HIGH,
                        lead_profile=None,
                        urgency_level=1,
                        follow_up_required=True,
                        tags=["market_insights", "long_term_nurture"],
                        success_rate=0.35
                    )
                ]
            },

            RiskLevel.CRITICAL: {
                ResponseType.RECOVERY: [
                    ResponseTemplate(
                        message="I completely understand and respect your commitment. I'm here if anything changes or if you need Inland Empire market insights down the road. Wishing you the best with your search!",
                        response_type=ResponseType.RECOVERY,
                        risk_level=RiskLevel.CRITICAL,
                        lead_profile=None,
                        urgency_level=1,
                        follow_up_required=True,
                        tags=["respectful_exit", "door_open"],
                        success_rate=0.25
                    )
                ],
                ResponseType.NURTURE: [
                    ResponseTemplate(
                        message="No problem at all! Would you be open to me staying in touch with quarterly Inland Empire market updates? I share insights that benefit all property owners in the area.",
                        response_type=ResponseType.NURTURE,
                        risk_level=RiskLevel.CRITICAL,
                        lead_profile=None,
                        urgency_level=1,
                        follow_up_required=True,
                        tags=["quarterly_updates", "property_owner_value"],
                        success_rate=0.22
                    )
                ]
            }
        }

    def _load_jorge_value_propositions(self) -> Dict[str, Dict]:
        """Load Jorge's unique value propositions"""
        return {
            "ai_technology": {
                "headline": "AI-Powered Market Intelligence",
                "description": "Real-time analysis that finds opportunities others miss",
                "proof_points": [
                    "Instant property valuation updates",
                    "Predictive market trend analysis",
                    "Off-market opportunity alerts",
                    "Automated comparable analysis"
                ],
                "competitor_advantage": "While others rely on outdated MLS data, I provide live market intelligence"
            },
            "rc_expertise": {
                "headline": "Native Inland Empire Market Knowledge",
                "description": "Born and raised understanding of local markets and trends",
                "proof_points": [
                    "Neighborhood micro-trend analysis",
                    "School district impact predictions",
                    "Development pipeline insights",
                    "Local business impact on values"
                ],
                "competitor_advantage": "Transplant agents learn Inland Empire - I live and breathe it"
            },
            "amazon_specialization": {
                "headline": "Amazon Logistics Specialist",
                "description": "Expert in logistics and healthcare worker relocations",
                "proof_points": [
                    "Amazon fulfillment center proximity analysis",
                    "Shift worker-friendly neighborhoods",
                    "Timeline-compressed searches",
                    "Healthcare benefit timing strategies"
                ],
                "competitor_advantage": "Traditional agents don't understand logistics/healthcare industry nuances"
            },
            "investor_focus": {
                "headline": "Investment Property Expert",
                "description": "ROI-focused approach with data-driven property analysis",
                "proof_points": [
                    "Cash flow projections",
                    "Appreciation potential modeling",
                    "Rental market analysis",
                    "Tax strategy coordination"
                ],
                "competitor_advantage": "Most agents focus on emotions - I focus on numbers"
            },
            "response_speed": {
                "headline": "24/7 Availability & Instant Response",
                "description": "Technology-enabled immediate response in fast-moving markets",
                "proof_points": [
                    "Sub-60-minute property alerts",
                    "Same-day showing coordination",
                    "Real-time offer strategy",
                    "Weekend and evening availability"
                ],
                "competitor_advantage": "Traditional agents work business hours - markets don't"
            }
        }

    def _load_rc_market_advantages(self) -> Dict[str, Any]:
        """Load Rancho Cucamonga/Inland Empire-specific market advantages and positioning"""
        return {
            "market_timing": {
                "current_conditions": "Inventory increasing, buyer opportunity window",
                "jorge_insight": "Perfect time for strategic buyers with proper market analysis",
                "urgency_creator": "Interest rates stabilizing - act before next wave of buyers"
            },
            "neighborhood_expertise": {
                "specialties": [
                    "Alta Loma luxury market",
                    "Etiwanda investment opportunities",
                    "North Rancho Cucamonga family homes",
                    "Town Center area condos",
                    "Victoria Gardens district properties"
                ],
                "unique_knowledge": "Micro-market trends that MLS data doesn't capture"
            },
            "development_pipeline": {
                "insight": "Upcoming development impact on property values",
                "advantage": "Early knowledge of infrastructure changes affecting values",
                "examples": [
                    "Metrolink expansion effects",
                    "New logistics hub announcements",
                    "School district boundary changes"
                ]
            },
            "local_connections": {
                "network": "Direct relationships with investors, developers, and off-market opportunities",
                "access": "Properties that never hit the open market",
                "speed": "24-48 hour advance notice on upcoming listings"
            }
        }

    def _load_success_stories(self) -> Dict[str, List[Dict]]:
        """Load Jorge's success stories for competitive situations"""
        return {
            "competitive_wins": [
                {
                    "situation": "Client was working with Keller Williams agent for 3 months without finding the right property",
                    "jorge_solution": "Used AI analysis to identify off-market opportunity in preferred neighborhood",
                    "outcome": "Closed in 21 days, $15k under ask price",
                    "timeframe": "3 weeks vs 3 months of searching"
                },
                {
                    "situation": "Amazon logistics employee needed to close before benefit enrollment deadline",
                    "jorge_solution": "Leveraged technology for instant property analysis and same-day showings",
                    "outcome": "Found perfect home and closed in 14 days",
                    "timeframe": "2 weeks vs typical 30-45 days"
                },
                {
                    "situation": "Investor was getting generic properties from traditional agent",
                    "jorge_solution": "Provided ROI analysis and cash flow projections for every property",
                    "outcome": "Found property with 12% cap rate in emerging neighborhood",
                    "timeframe": "Data-driven decision in 1 week"
                }
            ],
            "recovery_success": [
                {
                    "situation": "Lead initially chose discount brokerage for lower fees",
                    "jorge_approach": "Demonstrated value through complimentary market analysis",
                    "outcome": "Switched to Jorge after seeing quality difference",
                    "value_created": "Saved $25k through better negotiation and market timing"
                }
            ]
        }

    def get_competitive_response(
        self,
        risk_level: RiskLevel,
        competitor_mentions: List[CompetitorMention],
        lead_profile: Optional[LeadProfile] = None,
        conversation_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate appropriate competitive response based on situation

        Args:
            risk_level: Assessed competitive risk level
            competitor_mentions: List of detected competitor mentions
            lead_profile: Type of lead for targeted messaging
            conversation_context: Additional context for personalization

        Returns:
            Dict containing response message, follow-up actions, and metadata
        """

        # Get appropriate response type based on risk level
        response_type = self._determine_response_type(risk_level, competitor_mentions)

        # Get templates for this risk level and response type
        templates = self.response_templates.get(risk_level, {}).get(response_type, [])

        if not templates:
            return self._get_fallback_response(risk_level)

        # Filter templates by lead profile if specified
        if lead_profile:
            profile_templates = [t for t in templates if t.lead_profile in [None, lead_profile]]
            if profile_templates:
                templates = profile_templates

        # Select best template based on success rate
        template = max(templates, key=lambda t: t.success_rate)

        # Personalize message if context available
        personalized_message = self._personalize_message(template.message, conversation_context)

        # Add value proposition if appropriate
        value_prop = self._get_relevant_value_prop(competitor_mentions, lead_profile)

        # Generate follow-up strategy
        follow_up_strategy = self._generate_follow_up_strategy(template, competitor_mentions)

        return {
            "message": personalized_message,
            "value_proposition": value_prop,
            "response_type": response_type.value,
            "urgency_level": template.urgency_level,
            "follow_up_required": template.follow_up_required,
            "follow_up_strategy": follow_up_strategy,
            "tags": template.tags,
            "success_rate": template.success_rate,
            "escalation_recommended": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            "human_intervention": risk_level == RiskLevel.CRITICAL
        }

    def _determine_response_type(self, risk_level: RiskLevel, competitor_mentions: List[CompetitorMention]) -> ResponseType:
        """Determine the most appropriate response type"""

        if risk_level == RiskLevel.LOW:
            return ResponseType.POSITIONING
        elif risk_level == RiskLevel.MEDIUM:
            # Check for urgency indicators in mentions
            if any(mention.urgency_indicators for mention in competitor_mentions):
                return ResponseType.URGENCY
            return ResponseType.DIFFERENTIATION
        elif risk_level == RiskLevel.HIGH:
            return ResponseType.RECOVERY
        else:  # CRITICAL
            return ResponseType.NURTURE

    def _get_fallback_response(self, risk_level: RiskLevel) -> Dict[str, Any]:
        """Get fallback response when no templates match"""
        fallback_messages = {
            RiskLevel.LOW: "I'd love to learn more about what you're looking for to see how I can best help you.",
            RiskLevel.MEDIUM: "I understand you're exploring options. Let me show you what makes my approach different.",
            RiskLevel.HIGH: "I respect your current relationship. I'm here if anything changes.",
            RiskLevel.CRITICAL: "I understand completely. Wishing you the best with your search!"
        }

        return {
            "message": fallback_messages.get(risk_level, "How can I best help you today?"),
            "value_proposition": None,
            "response_type": "fallback",
            "urgency_level": 1,
            "follow_up_required": False,
            "follow_up_strategy": [],
            "tags": ["fallback"],
            "success_rate": 0.3,
            "escalation_recommended": True,
            "human_intervention": True
        }

    def _personalize_message(self, message: str, context: Optional[Dict]) -> str:
        """Personalize message based on conversation context"""
        if not context:
            return message

        # Add personalization based on lead name, preferences, etc.
        if context.get("lead_name"):
            if not message.startswith(context["lead_name"]):
                message = f"{context['lead_name']}, {message.lower()}"

        # Add specific details if available
        if context.get("property_type"):
            property_type = context["property_type"]
            message = message.replace("properties", f"{property_type} properties")
            message = message.replace("property", f"{property_type} property")

        return message

    def _get_relevant_value_prop(self, competitor_mentions: List[CompetitorMention], lead_profile: Optional[LeadProfile]) -> Optional[Dict]:
        """Get most relevant value proposition based on competitive situation"""

        # Profile-based value props
        if lead_profile == LeadProfile.INVESTOR:
            return self.jorge_value_props["investor_focus"]
        elif lead_profile == LeadProfile.RELOCATING:
            return self.jorge_value_props["amazon_specialization"]

        # Competitor-based value props
        for mention in competitor_mentions:
            if mention.competitor_name in ["keller_williams", "remax", "coldwell_banker"]:
                return self.jorge_value_props["ai_technology"]

        # Default to RC expertise
        return self.jorge_value_props["rc_expertise"]

    def _generate_follow_up_strategy(self, template: ResponseTemplate, competitor_mentions: List[CompetitorMention]) -> List[str]:
        """Generate follow-up strategy based on competitive situation"""
        strategy = []

        if template.follow_up_required:
            if template.risk_level == RiskLevel.LOW:
                strategy.extend([
                    "Send personalized market analysis within 24 hours",
                    "Follow up with relevant property opportunities",
                    "Share success story relevant to their situation"
                ])
            elif template.risk_level == RiskLevel.MEDIUM:
                strategy.extend([
                    "Provide immediate value (market insights, property analysis)",
                    "Schedule consultation to demonstrate technology advantage",
                    "Send case study showing competitive wins"
                ])
            elif template.risk_level == RiskLevel.HIGH:
                strategy.extend([
                    "Add to long-term nurture campaign",
                    "Send monthly market updates",
                    "Alert to off-market opportunities",
                    "Check in quarterly with market insights"
                ])
            else:  # CRITICAL
                strategy.extend([
                    "Add to quarterly touch-base campaign",
                    "Send bi-annual market reports",
                    "Monitor for future opportunities"
                ])

        return strategy

    def get_success_story(self, situation_type: str, competitor_name: Optional[str] = None) -> Optional[Dict]:
        """Get relevant success story for competitive positioning"""

        if situation_type == "competitive_win":
            stories = self.success_stories["competitive_wins"]

            # Filter by competitor if specified
            if competitor_name:
                relevant_stories = [s for s in stories if competitor_name.lower() in s["situation"].lower()]
                if relevant_stories:
                    return random.choice(relevant_stories)

            return random.choice(stories)

        elif situation_type == "recovery":
            return random.choice(self.success_stories["recovery_success"])

        return None

    def get_urgency_creator(self, market_context: str = "general") -> Dict[str, str]:
        """Get market-based urgency creators"""
        rc_urgency = self.rc_advantages["market_timing"]

        urgency_messages = {
            "inventory": f"Rancho Cucamonga inventory is {rc_urgency['current_conditions']}. This is {rc_urgency['jorge_insight']}.",
            "rates": rc_urgency['urgency_creator'],
            "competition": "Three other buyers are looking at similar properties in this price range this week.",
            "seasonal": "Spring buying season is starting - best selection is available now before the rush."
        }

        return urgency_messages.get(market_context, urgency_messages["inventory"])

    def get_differentiation_points(self, competitor_name: Optional[str] = None) -> List[str]:
        """Get key differentiation points vs specific competitor or general market"""

        base_differentiators = [
            "AI-powered market analysis provides insights others can't access",
            "24/7 availability in fast-moving Inland Empire market",
            "Specialization in logistics/healthcare worker and investor needs",
            "Real-time off-market opportunity access",
            "Native Inland Empire knowledge with data-driven approach"
        ]

        if competitor_name:
            # Add competitor-specific differentiators based on known weaknesses
            competitor_weaknesses = {
                "keller_williams": "Unlike high-volume brokerages, you get personal attention and customized service",
                "remax": "While franchises follow corporate playbooks, I adapt to your specific needs",
                "coldwell_banker": "I combine traditional service with modern technology for best of both worlds"
            }

            if competitor_name in competitor_weaknesses:
                base_differentiators.insert(0, competitor_weaknesses[competitor_name])

        return base_differentiators


# Singleton instance
_competitive_response_system = None

def get_competitive_response_system() -> CompetitiveResponseSystem:
    """Get singleton competitive response system"""
    global _competitive_response_system
    if _competitive_response_system is None:
        _competitive_response_system = CompetitiveResponseSystem()
    return _competitive_response_system