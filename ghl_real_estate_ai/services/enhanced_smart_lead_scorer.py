"""
Enhanced Smart Lead Scorer 2.0 for Jorge's Lead Bot

Advanced AI-powered lead scoring with behavioral analysis,
financial readiness assessment, and timeline prediction.

This enhancement provides Jorge with the most sophisticated
lead qualification system in real estate.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

# Mock imports - would be real in production
try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LeadPriority(Enum):
    """Lead priority levels for Jorge's attention."""

    IMMEDIATE = "immediate"  # Call within 5 minutes
    HIGH = "high"  # Call within 1 hour
    MEDIUM = "medium"  # Call within 24 hours
    LOW = "low"  # Nurture sequence
    DISQUALIFIED = "disqualified"  # Archive


class BuyingStage(Enum):
    """Where the lead is in their buying journey."""

    JUST_LOOKING = "just_looking"
    GETTING_SERIOUS = "getting_serious"
    READY_TO_BUY = "ready_to_buy"
    UNDER_CONTRACT = "under_contract"


@dataclass
class LeadScoreBreakdown:
    """Detailed breakdown of lead scoring components."""

    intent_score: float  # 0-100
    financial_readiness: float  # 0-100
    timeline_urgency: float  # 0-100
    engagement_quality: float  # 0-100
    referral_potential: float  # 0-100
    local_connection: float  # 0-100

    overall_score: float  # 0-100
    priority_level: LeadPriority
    buying_stage: BuyingStage

    recommended_actions: List[str]
    jorge_talking_points: List[str]
    risk_factors: List[str]


class EnhancedSmartLeadScorer:
    """
    Advanced lead scoring system that analyzes multiple dimensions
    to provide Jorge with actionable intelligence about each lead.
    """

    def __init__(self, anthropic_client=None):
        self.anthropic_client = anthropic_client
        self.rancho_cucamonga_data = self._load_local_market_data()

    def _load_local_market_data(self) -> Dict[str, Any]:
        """Load Rancho Cucamonga specific market intelligence."""
        return {
            "avg_home_price": 750000,
            "median_income": 85000,
            "price_appreciation_rate": 0.08,
            "days_on_market_avg": 21,
            "inventory_level": "low",
            "best_neighborhoods": ["Alta Loma", "North Rancho Cucamonga", "Victoria Arbors", "Red Hill Country Club"],
            "school_districts": {
                "Chaffey Joint Union": {"rating": 8, "desirability": "high"},
                "Cucamonga Elementary": {"rating": 9, "desirability": "very_high"},
            },
        }

    async def calculate_comprehensive_score(self, lead_data: Dict[str, Any]) -> LeadScoreBreakdown:
        """
        Calculate comprehensive lead score using AI and behavioral analysis.

        Args:
            lead_data: Complete lead information including:
                - contact_info, search_behavior, financial_hints,
                - communication_history, ghl_webhook_data

        Returns:
            LeadScoreBreakdown with detailed scoring and recommendations
        """

        # Analyze each scoring dimension
        intent_score = await self._analyze_intent_signals(lead_data)
        financial_readiness = await self._assess_financial_readiness(lead_data)
        timeline_urgency = await self._predict_purchase_timeline(lead_data)
        engagement_quality = await self._measure_engagement_quality(lead_data)
        referral_potential = await self._evaluate_referral_potential(lead_data)
        local_connection = await self._assess_local_connection(lead_data)

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(
            {
                "intent": intent_score,
                "financial": financial_readiness,
                "timeline": timeline_urgency,
                "engagement": engagement_quality,
                "referral": referral_potential,
                "local": local_connection,
            }
        )

        # Determine priority and stage
        priority_level = self._determine_priority_level(overall_score, lead_data)
        buying_stage = self._identify_buying_stage(lead_data)

        # Generate Jorge-specific recommendations
        recommendations = await self._generate_action_recommendations(lead_data, overall_score, priority_level)
        talking_points = await self._create_jorge_talking_points(lead_data, buying_stage)
        risk_factors = self._identify_risk_factors(lead_data)

        return LeadScoreBreakdown(
            intent_score=intent_score,
            financial_readiness=financial_readiness,
            timeline_urgency=timeline_urgency,
            engagement_quality=engagement_quality,
            referral_potential=referral_potential,
            local_connection=local_connection,
            overall_score=overall_score,
            priority_level=priority_level,
            buying_stage=buying_stage,
            recommended_actions=recommendations,
            jorge_talking_points=talking_points,
            risk_factors=risk_factors,
        )

    async def _analyze_intent_signals(self, lead_data: Dict[str, Any]) -> float:
        """Analyze buying intent from behavior patterns."""

        intent_signals = {
            "search_frequency": lead_data.get("search_frequency", 0),
            "search_specificity": lead_data.get("search_specificity", 0),
            "price_range_consistency": lead_data.get("price_range_consistency", 0),
            "neighborhood_focus": lead_data.get("neighborhood_focus", 0),
            "school_research": lead_data.get("school_research", False),
            "mortgage_calculator_usage": lead_data.get("mortgage_calc_usage", False),
            "property_photos_viewed": lead_data.get("photos_viewed", 0),
            "time_spent_on_listings": lead_data.get("time_on_listings", 0),
        }

        # Scoring logic
        score = 0

        # Search behavior (40 points)
        if intent_signals["search_frequency"] > 5:  # Searching frequently
            score += 15
        if intent_signals["search_specificity"] > 0.7:  # Specific criteria
            score += 15
        if intent_signals["price_range_consistency"]:  # Consistent budget
            score += 10

        # Engagement depth (35 points)
        if intent_signals["time_spent_on_listings"] > 300:  # 5+ min per listing
            score += 15
        if intent_signals["property_photos_viewed"] > 10:
            score += 10
        if intent_signals["school_research"]:
            score += 10

        # Financial preparation (25 points)
        if intent_signals["mortgage_calculator_usage"]:
            score += 15
        if intent_signals["neighborhood_focus"]:  # Focusing on specific area
            score += 10

        return min(score, 100)  # Cap at 100

    async def _assess_financial_readiness(self, lead_data: Dict[str, Any]) -> float:
        """Assess lead's financial readiness to purchase."""

        financial_indicators = {
            "stated_budget": lead_data.get("budget", 0),
            "preapproval_status": lead_data.get("preapproved", False),
            "down_payment_ready": lead_data.get("down_payment_ready", False),
            "employment_status": lead_data.get("employment_status", ""),
            "credit_score_range": lead_data.get("credit_score", ""),
            "debt_to_income": lead_data.get("debt_to_income", 0),
            "first_time_buyer": lead_data.get("first_time_buyer", True),
            "current_home_owner": lead_data.get("owns_home", False),
        }

        score = 0

        # Pre-approval status (30 points)
        if financial_indicators["preapproval_status"]:
            score += 30
        elif financial_indicators["down_payment_ready"]:
            score += 15

        # Budget alignment (25 points)
        budget = financial_indicators["stated_budget"]
        market_avg = self.rancho_cucamonga_data["avg_home_price"]
        if 0.8 <= (budget / market_avg) <= 1.5:  # Realistic budget
            score += 25
        elif budget > 0:
            score += 10

        # Employment stability (20 points)
        employment = financial_indicators["employment_status"].lower()
        if "employed" in employment or "self-employed" in employment:
            score += 20
        elif "contractor" in employment:
            score += 10

        # Credit indicators (15 points)
        credit_score = financial_indicators["credit_score_range"]
        if "excellent" in credit_score.lower() or "800" in credit_score:
            score += 15
        elif "good" in credit_score.lower() or "700" in credit_score:
            score += 10
        elif "fair" in credit_score.lower():
            score += 5

        # Ownership experience (10 points)
        if financial_indicators["current_home_owner"]:
            score += 10  # Has experience with real estate transactions
        elif not financial_indicators["first_time_buyer"]:
            score += 5

        return min(score, 100)

    async def _predict_purchase_timeline(self, lead_data: Dict[str, Any]) -> float:
        """Predict urgency based on timeline indicators."""

        timeline_factors = {
            "stated_timeline": lead_data.get("timeline", ""),
            "lease_expiration": lead_data.get("lease_expires", None),
            "life_events": lead_data.get("life_events", []),
            "current_situation": lead_data.get("current_situation", ""),
            "showing_requests": lead_data.get("showing_requests", 0),
            "follow_up_responsiveness": lead_data.get("response_rate", 0),
        }

        score = 0

        # Stated timeline urgency (40 points)
        timeline = timeline_factors["stated_timeline"].lower()
        if "immediately" in timeline or "asap" in timeline:
            score += 40
        elif "month" in timeline or "30 day" in timeline:
            score += 30
        elif "3 month" in timeline or "90 day" in timeline:
            score += 20
        elif "6 month" in timeline:
            score += 10

        # Life event drivers (25 points)
        life_events = timeline_factors.get("life_events", [])
        urgent_events = ["new_job", "baby_coming", "marriage", "divorce", "retirement"]
        if any(event in life_events for event in urgent_events):
            score += 25

        # Behavioral urgency indicators (25 points)
        if timeline_factors["showing_requests"] > 3:
            score += 15  # Actively scheduling showings
        if timeline_factors["follow_up_responsiveness"] > 0.8:
            score += 10  # Very responsive to outreach

        # External timeline pressure (10 points)
        lease_exp = timeline_factors.get("lease_expiration")
        if lease_exp and self._is_within_days(lease_exp, 90):
            score += 10

        return min(score, 100)

    async def _measure_engagement_quality(self, lead_data: Dict[str, Any]) -> float:
        """Measure the quality and depth of lead engagement."""

        engagement_metrics = {
            "email_opens": lead_data.get("email_opens", 0),
            "email_clicks": lead_data.get("email_clicks", 0),
            "website_sessions": lead_data.get("website_sessions", 0),
            "pages_per_session": lead_data.get("pages_per_session", 0),
            "form_completions": lead_data.get("forms_completed", 0),
            "phone_answered": lead_data.get("phone_answered", False),
            "callback_requests": lead_data.get("callback_requests", 0),
            "social_media_interaction": lead_data.get("social_interaction", 0),
        }

        score = 0

        # Email engagement (25 points)
        if engagement_metrics["email_opens"] > 5:
            score += 10
        if engagement_metrics["email_clicks"] > 2:
            score += 15

        # Website engagement (30 points)
        if engagement_metrics["website_sessions"] > 3:
            score += 15
        if engagement_metrics["pages_per_session"] > 3:
            score += 15

        # Direct communication (30 points)
        if engagement_metrics["phone_answered"]:
            score += 20  # Answered Jorge's call
        if engagement_metrics["callback_requests"] > 0:
            score += 10

        # Form engagement (15 points)
        score += min(engagement_metrics["form_completions"] * 5, 15)

        return min(score, 100)

    async def _evaluate_referral_potential(self, lead_data: Dict[str, Any]) -> float:
        """Evaluate potential for future referrals and network value."""

        referral_indicators = {
            "profession": lead_data.get("profession", ""),
            "company_size": lead_data.get("company_size", ""),
            "social_media_followers": lead_data.get("social_followers", 0),
            "network_activity": lead_data.get("network_activity", 0),
            "community_involvement": lead_data.get("community_involvement", []),
            "previous_moves": lead_data.get("previous_moves", 0),
            "family_size": lead_data.get("family_size", 1),
        }

        score = 0

        # Professional network influence (40 points)
        profession = referral_indicators["profession"].lower()
        high_influence_jobs = [
            "doctor",
            "lawyer",
            "teacher",
            "pastor",
            "coach",
            "manager",
            "director",
            "executive",
            "consultant",
        ]
        if any(job in profession for job in high_influence_jobs):
            score += 25

        company_size = referral_indicators.get("company_size", "")
        if "large" in company_size.lower() or "500+" in company_size:
            score += 15

        # Social influence (25 points)
        followers = referral_indicators["social_media_followers"]
        if followers > 1000:
            score += 15
        elif followers > 500:
            score += 10

        if referral_indicators["network_activity"] > 5:
            score += 10

        # Community connections (20 points)
        community_involvement = referral_indicators.get("community_involvement", [])
        if len(community_involvement) > 2:
            score += 20
        elif len(community_involvement) > 0:
            score += 10

        # Move frequency (15 points)
        moves = referral_indicators["previous_moves"]
        if moves > 2:
            score += 15  # Experienced mover, likely to move again
        elif moves > 0:
            score += 10

        return min(score, 100)

    async def _assess_local_connection(self, lead_data: Dict[str, Any]) -> float:
        """Assess lead's connection to Rancho Cucamonga area."""

        local_factors = {
            "current_location": lead_data.get("current_location", ""),
            "work_location": lead_data.get("work_location", ""),
            "family_in_area": lead_data.get("family_nearby", False),
            "school_preference": lead_data.get("school_preference", ""),
            "local_amenities_interest": lead_data.get("amenities_interest", []),
            "commute_concerns": lead_data.get("commute_concerns", []),
        }

        score = 0

        # Geographic proximity (40 points)
        current_loc = local_factors["current_location"].lower()
        nearby_areas = ["ontario", "upland", "fontana", "claremont", "pomona", "chino"]
        if "rancho cucamonga" in current_loc:
            score += 40  # Already local
        elif any(area in current_loc for area in nearby_areas):
            score += 25  # Nearby, familiar with area
        elif "inland empire" in current_loc or "san bernardino" in current_loc:
            score += 15

        # Local connections (25 points)
        if local_factors["family_in_area"]:
            score += 15

        work_loc = local_factors["work_location"].lower()
        if "rancho cucamonga" in work_loc or any(area in work_loc for area in nearby_areas):
            score += 10

        # Local knowledge/interest (25 points)
        school_pref = local_factors["school_preference"].lower()
        local_schools = ["chaffey", "cucamonga elementary", "etiwanda"]
        if any(school in school_pref for school in local_schools):
            score += 15

        local_amenities = local_factors.get("local_amenities_interest", [])
        if len(local_amenities) > 2:
            score += 10

        # Commute compatibility (10 points)
        commute_concerns = local_factors.get("commute_concerns", [])
        if len(commute_concerns) == 0:  # No commute issues
            score += 10
        elif "short commute" in str(commute_concerns).lower():
            score += 5

        return min(score, 100)

    def _calculate_weighted_score(self, dimension_scores: Dict[str, float]) -> float:
        """Calculate weighted overall score based on Jorge's priorities."""

        weights = {
            "intent": 0.25,  # 25% - Most important for immediate action
            "financial": 0.25,  # 25% - Must be able to buy
            "timeline": 0.20,  # 20% - Urgency drives priority
            "engagement": 0.15,  # 15% - Quality of interaction
            "local": 0.10,  # 10% - Local connection helps
            "referral": 0.05,  # 5% - Future value
        }

        weighted_score = sum(score * weights[dimension] for dimension, score in dimension_scores.items())

        return round(weighted_score, 1)

    def _determine_priority_level(self, overall_score: float, lead_data: Dict[str, Any]) -> LeadPriority:
        """Determine Jorge's action priority for this lead."""

        # Score-based priority
        if overall_score >= 85:
            base_priority = LeadPriority.IMMEDIATE
        elif overall_score >= 70:
            base_priority = LeadPriority.HIGH
        elif overall_score >= 50:
            base_priority = LeadPriority.MEDIUM
        elif overall_score >= 30:
            base_priority = LeadPriority.LOW
        else:
            base_priority = LeadPriority.DISQUALIFIED

        # Urgency modifiers
        urgency_flags = [
            lead_data.get("callback_requested", False),
            lead_data.get("showing_requested", False),
            "urgent" in str(lead_data.get("notes", "")).lower(),
            "immediate" in str(lead_data.get("timeline", "")).lower(),
        ]

        if any(urgency_flags) and base_priority != LeadPriority.DISQUALIFIED:
            if base_priority == LeadPriority.LOW:
                return LeadPriority.MEDIUM
            elif base_priority == LeadPriority.MEDIUM:
                return LeadPriority.HIGH
            elif base_priority == LeadPriority.HIGH:
                return LeadPriority.IMMEDIATE

        return base_priority

    def _identify_buying_stage(self, lead_data: Dict[str, Any]) -> BuyingStage:
        """Identify where the lead is in their buying journey."""

        stage_indicators = {
            "search_specificity": lead_data.get("search_specificity", 0),
            "showing_requests": lead_data.get("showing_requests", 0),
            "financial_prep": lead_data.get("preapproved", False),
            "timeline": lead_data.get("timeline", ""),
            "engagement_depth": lead_data.get("pages_per_session", 0),
        }

        # Decision logic
        if stage_indicators["showing_requests"] > 5 and stage_indicators["financial_prep"]:
            return BuyingStage.READY_TO_BUY
        elif stage_indicators["showing_requests"] > 2 or stage_indicators["financial_prep"]:
            return BuyingStage.GETTING_SERIOUS
        elif stage_indicators["search_specificity"] > 0.5 and stage_indicators["engagement_depth"] > 3:
            return BuyingStage.GETTING_SERIOUS
        else:
            return BuyingStage.JUST_LOOKING

    async def _generate_action_recommendations(
        self, lead_data: Dict[str, Any], overall_score: float, priority_level: LeadPriority
    ) -> List[str]:
        """Generate specific action recommendations for Jorge."""

        recommendations = []

        if priority_level == LeadPriority.IMMEDIATE:
            recommendations.extend(
                [
                    "🚨 CALL IMMEDIATELY - High-value lead ready to buy",
                    "📱 Send pre-approved property matches within 2 hours",
                    "📅 Schedule showing for this week",
                    "💼 Prepare Jorge's success stories for this client type",
                ]
            )
        elif priority_level == LeadPriority.HIGH:
            recommendations.extend(
                [
                    "📞 Call within 1 hour during business hours",
                    "📧 Send personalized follow-up email with market insights",
                    "🏠 Curate 3-5 property matches based on criteria",
                    "📊 Share relevant market data for their area of interest",
                ]
            )
        elif priority_level == LeadPriority.MEDIUM:
            recommendations.extend(
                [
                    "📞 Call within 24 hours",
                    "📧 Add to nurture sequence with weekly valuable content",
                    "🎯 Invite to Jorge's buyer seminar",
                    "📱 Connect on social media for relationship building",
                ]
            )
        elif priority_level == LeadPriority.LOW:
            recommendations.extend(
                [
                    "📧 Add to monthly newsletter",
                    "🎓 Send home buyer's guide and resources",
                    "📊 Share quarterly market reports",
                    "🔄 Re-score in 30 days for status change",
                ]
            )

        # Add specific recommendations based on lead characteristics
        if lead_data.get("first_time_buyer", True):
            recommendations.append("📚 Send first-time home buyer checklist")

        if lead_data.get("investment_interest", False):
            recommendations.append("💰 Share investment property analysis tools")

        if not lead_data.get("preapproved", False):
            recommendations.append("🏦 Recommend trusted lender for pre-approval")

        return recommendations

    async def _create_jorge_talking_points(self, lead_data: Dict[str, Any], buying_stage: BuyingStage) -> List[str]:
        """Create Jorge-specific talking points for this lead."""

        talking_points = []

        # Stage-specific talking points
        if buying_stage == BuyingStage.JUST_LOOKING:
            talking_points.extend(
                [
                    "🏠 'I help people find their perfect home in Rancho Cucamonga'",
                    "📈 Share current market opportunities and timing insights",
                    "🎯 'Let me set you up with auto-notifications for properties that match your criteria'",
                    "📞 'I'm always available for questions - real estate is all about timing'",
                ]
            )
        elif buying_stage == BuyingStage.GETTING_SERIOUS:
            talking_points.extend(
                [
                    "🎯 'Based on your search, I have 3 properties you should see this week'",
                    "💡 'Here's what other buyers like you are doing in this market'",
                    "🏦 'Let me connect you with my preferred lender for pre-approval'",
                    "📊 'I can show you exactly what homes are selling for in your target area'",
                ]
            )
        elif buying_stage == BuyingStage.READY_TO_BUY:
            talking_points.extend(
                [
                    "⚡ 'In this market, we need to act fast on the right property'",
                    "🎯 'I have insider knowledge on homes coming to market soon'",
                    "💪 'My negotiation strategy has saved clients an average of $15K'",
                    "🏆 'Let's schedule a strategy session to position your offer to win'",
                ]
            )

        # Personalized talking points based on lead data
        budget = lead_data.get("budget", 0)
        if budget > 0:
            talking_points.append(f"💰 'With your ${budget:,} budget, you have excellent options in Rancho Cucamonga'")

        if lead_data.get("family_size", 1) > 2:
            talking_points.append("🏫 'I know the best family-friendly neighborhoods with top-rated schools'")

        if lead_data.get("first_time_buyer", True):
            talking_points.append("🌟 'I love helping first-time buyers navigate their journey to homeownership'")

        return talking_points

    def _identify_risk_factors(self, lead_data: Dict[str, Any]) -> List[str]:
        """Identify potential risks or challenges with this lead."""

        risk_factors = []

        # Financial risks
        if not lead_data.get("preapproved", False) and lead_data.get("timeline", "") == "immediate":
            risk_factors.append("⚠️ Urgent timeline but no pre-approval - may face delays")

        if lead_data.get("debt_to_income", 0) > 0.45:
            risk_factors.append("⚠️ High debt-to-income ratio - financing may be challenging")

        # Market risks
        budget = lead_data.get("budget", 0)
        market_avg = self.rancho_cucamonga_data["avg_home_price"]
        if budget < market_avg * 0.7:
            risk_factors.append("⚠️ Budget below market average - limited inventory options")

        # Engagement risks
        if lead_data.get("response_rate", 1) < 0.3:
            risk_factors.append("⚠️ Low response rate to communications")

        # Timeline risks
        if "just looking" in lead_data.get("timeline", "").lower():
            risk_factors.append("⚠️ Extended timeline - may need long-term nurturing")

        return risk_factors

    def _is_within_days(self, date_str: str, days: int) -> bool:
        """Check if a date string is within the specified number of days."""
        try:
            from datetime import datetime

            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            return (target_date - datetime.now()).days <= days
        except (ValueError, TypeError) as e:
            logger.debug(f"Date conversion failed for '{date_str}': {e}")
            return False


# Example usage for Jorge
async def example_enhanced_scoring():
    """Example of how Jorge would use the enhanced lead scorer."""

    # Sample lead data from GHL webhook
    sample_lead = {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "+1555-123-4567",
        "budget": 800000,
        "timeline": "within 3 months",
        "search_frequency": 8,  # Searches per week
        "search_specificity": 0.8,  # How specific are searches
        "preapproved": True,
        "employment_status": "employed",
        "family_size": 4,
        "first_time_buyer": False,
        "current_location": "Ontario, CA",
        "work_location": "Rancho Cucamonga, CA",
        "school_preference": "Chaffey Joint Union",
        "showing_requests": 3,
        "email_opens": 12,
        "website_sessions": 6,
        "pages_per_session": 4,
        "profession": "teacher",
        "life_events": ["new_job"],
    }

    # Initialize scorer
    scorer = EnhancedSmartLeadScorer()

    # Calculate comprehensive score
    score_breakdown = await scorer.calculate_comprehensive_score(sample_lead)

    # Jorge's dashboard would display this information
    print(f"📊 LEAD SCORE REPORT FOR {sample_lead['name'].upper()}")
    print("=" * 50)
    print(f"🎯 Overall Score: {score_breakdown.overall_score}/100")
    print(f"🚨 Priority: {score_breakdown.priority_level.value.upper()}")
    print(f"🏠 Buying Stage: {score_breakdown.buying_stage.value.replace('_', ' ').title()}")
    print()

    print("📈 SCORE BREAKDOWN:")
    print(f"  Intent Signals: {score_breakdown.intent_score}/100")
    print(f"  Financial Readiness: {score_breakdown.financial_readiness}/100")
    print(f"  Timeline Urgency: {score_breakdown.timeline_urgency}/100")
    print(f"  Engagement Quality: {score_breakdown.engagement_quality}/100")
    print(f"  Referral Potential: {score_breakdown.referral_potential}/100")
    print(f"  Local Connection: {score_breakdown.local_connection}/100")
    print()

    print("🎯 JORGE'S ACTION PLAN:")
    for action in score_breakdown.recommended_actions:
        print(f"  • {action}")
    print()

    print("💬 TALKING POINTS:")
    for point in score_breakdown.jorge_talking_points:
        print(f"  • {point}")
    print()

    if score_breakdown.risk_factors:
        print("⚠️ RISK FACTORS:")
        for risk in score_breakdown.risk_factors:
            print(f"  • {risk}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_enhanced_scoring())
