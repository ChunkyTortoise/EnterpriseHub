"""
Enhanced Intelligence Coordinator - Unified Integration Layer
==========================================================

Coordinates all enhanced intelligence capabilities:
- Scenario simulation engine
- Market sentiment radar
- Emergency deal rescue
- Advanced analytics and insights

Provides unified interface for the enhanced features from research recommendations.

Author: Enhanced from research recommendations - January 2026
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service

# Core service imports
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator
from ghl_real_estate_ai.services.emergency_deal_rescue import RescueUrgencyLevel, get_emergency_deal_rescue
from ghl_real_estate_ai.services.ghl_deal_intelligence_service import get_ghl_deal_intelligence_service
from ghl_real_estate_ai.services.market_sentiment_radar import AlertPriority, get_market_sentiment_radar

# Enhanced service imports
from ghl_real_estate_ai.services.scenario_simulation_engine import (
    ScenarioInput,
    ScenarioType,
    get_scenario_simulation_engine,
)

logger = get_logger(__name__)


class IntelligenceLevel(Enum):
    """Levels of intelligence analysis depth."""

    BASIC = "basic"  # Standard analysis
    ENHANCED = "enhanced"  # Include sentiment and scenarios
    COMPREHENSIVE = "comprehensive"  # Full analysis with all features
    EXECUTIVE = "executive"  # Executive summary format


@dataclass
class IntelligenceBriefing:
    """Comprehensive intelligence briefing combining all enhanced capabilities."""

    # Summary metrics
    overall_health_score: float  # 0-100 composite health score
    priority_alerts: List[Dict]  # High-priority items requiring attention
    opportunities: List[Dict]  # Growth and optimization opportunities

    # Market intelligence
    market_sentiment_summary: Optional[Dict] = None
    high_opportunity_areas: List[Dict] = None

    # Deal intelligence
    at_risk_deals: List[Dict] = None
    rescue_recommendations: List[Dict] = None

    # Strategic insights
    scenario_recommendations: List[Dict] = None
    optimization_opportunities: List[Dict] = None

    # Performance metrics
    current_performance: Dict = None
    projected_performance: Dict = None

    # Metadata
    briefing_level: IntelligenceLevel = IntelligenceLevel.ENHANCED
    generated_at: datetime = None
    confidence_score: float = 0.8
    data_freshness: str = "current"


class EnhancedIntelligenceCoordinator:
    """
    Unified coordinator for all enhanced intelligence capabilities.

    Provides:
    - Integrated sentiment and deal intelligence
    - Strategic scenario analysis
    - Executive briefings and alerts
    - Optimization recommendations
    - Performance projections
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.analytics = AnalyticsService()
        self.claude = ClaudeOrchestrator()

        # Enhanced services (lazy-loaded)
        self._scenario_engine = None
        self._sentiment_radar = None
        self._deal_rescue = None

        # Configuration
        self.cache_ttl = 3600  # 1 hour cache
        self.alert_refresh_interval = 900  # 15 minutes for alerts

    async def get_scenario_engine(self):
        """Get scenario simulation engine (lazy loading)."""
        if self._scenario_engine is None:
            self._scenario_engine = await get_scenario_simulation_engine()
        return self._scenario_engine

    async def get_sentiment_radar(self):
        """Get market sentiment radar (lazy loading)."""
        if self._sentiment_radar is None:
            self._sentiment_radar = await get_market_sentiment_radar()
        return self._sentiment_radar

    async def get_deal_rescue(self):
        """Get emergency deal rescue system (lazy loading)."""
        if self._deal_rescue is None:
            self._deal_rescue = await get_emergency_deal_rescue()
        return self._deal_rescue

    async def generate_intelligence_briefing(
        self,
        level: IntelligenceLevel = IntelligenceLevel.ENHANCED,
        focus_areas: Optional[List[str]] = None,
        time_horizon: int = 30,
    ) -> IntelligenceBriefing:
        """
        Generate comprehensive intelligence briefing.

        Args:
            level: Depth of analysis to perform
            focus_areas: Specific areas to focus on (deals, market, growth, etc.)
            time_horizon: Analysis time horizon in days

        Returns:
            Comprehensive intelligence briefing
        """

        # Check cache for recent briefings
        cache_key = f"intelligence_briefing:{level.value}:{time_horizon}:{focus_areas}"
        cached_briefing = await self.cache.get(cache_key)

        if cached_briefing and level != IntelligenceLevel.EXECUTIVE:
            return IntelligenceBriefing(**json.loads(cached_briefing))

        logger.info(f"Generating {level.value} intelligence briefing")

        # Initialize briefing
        briefing = IntelligenceBriefing(
            overall_health_score=0.0,
            priority_alerts=[],
            opportunities=[],
            briefing_level=level,
            generated_at=datetime.now(),
        )

        try:
            # Gather intelligence based on level
            if level in [IntelligenceLevel.ENHANCED, IntelligenceLevel.COMPREHENSIVE, IntelligenceLevel.EXECUTIVE]:
                # Market sentiment analysis
                if not focus_areas or "market" in focus_areas:
                    briefing.market_sentiment_summary = await self._analyze_market_sentiment()
                    briefing.high_opportunity_areas = await self._identify_opportunity_areas()

                # Deal risk analysis
                if not focus_areas or "deals" in focus_areas:
                    briefing.at_risk_deals = await self._analyze_deal_risks()
                    briefing.rescue_recommendations = await self._get_rescue_recommendations()

                # Strategic scenario analysis
                if level == IntelligenceLevel.COMPREHENSIVE or (focus_areas and "growth" in focus_areas):
                    briefing.scenario_recommendations = await self._generate_scenario_recommendations()
                    briefing.optimization_opportunities = await self._identify_optimization_opportunities()

                # Performance analysis
                briefing.current_performance = await self._analyze_current_performance()
                briefing.projected_performance = await self._project_performance(time_horizon)

            # Calculate overall health score
            briefing.overall_health_score = await self._calculate_health_score(briefing)

            # Generate priority alerts
            briefing.priority_alerts = await self._generate_priority_alerts(briefing)

            # Generate opportunities
            briefing.opportunities = await self._generate_opportunities(briefing)

            # Calculate confidence score
            briefing.confidence_score = self._calculate_briefing_confidence(briefing)

        except Exception as e:
            logger.error(f"Error generating intelligence briefing: {e}")
            # Return minimal briefing with error info
            briefing.priority_alerts.append(
                {"type": "system_error", "message": "Intelligence briefing partially unavailable", "priority": "medium"}
            )

        # Cache result (except executive level which should be real-time)
        if level != IntelligenceLevel.EXECUTIVE:
            await self.cache.set(cache_key, json.dumps(asdict(briefing), default=str), expire=self.cache_ttl)

        return briefing

    async def _analyze_market_sentiment(self) -> Dict[str, Any]:
        """Analyze market sentiment across Jorge's territory."""

        try:
            sentiment_radar = await self.get_sentiment_radar()

            # Analyze key areas in Jorge's territory
            territory = ["78731", "78746", "78759", "78704", "78745"]  # Austin ZIP codes

            sentiment_analysis = []
            total_motivation = 0

            for location in territory:
                try:
                    profile = await sentiment_radar.analyze_market_sentiment(location)

                    sentiment_analysis.append(
                        {
                            "location": location,
                            "motivation_index": profile.seller_motivation_index,
                            "trend": profile.trend_direction,
                            "optimal_window": profile.optimal_outreach_window,
                            "confidence": profile.confidence_score,
                        }
                    )

                    total_motivation += profile.seller_motivation_index

                except Exception as e:
                    logger.warning(f"Error analyzing sentiment for {location}: {e}")

            if sentiment_analysis:
                avg_motivation = total_motivation / len(sentiment_analysis)

                # Find top opportunity area
                top_area = max(sentiment_analysis, key=lambda x: x["motivation_index"])

                return {
                    "overall_motivation_index": avg_motivation,
                    "top_opportunity_area": top_area,
                    "areas_analyzed": len(sentiment_analysis),
                    "high_motivation_areas": [area for area in sentiment_analysis if area["motivation_index"] > 60],
                    "immediate_opportunities": [
                        area for area in sentiment_analysis if area["optimal_window"] in ["immediate", "1-week"]
                    ],
                }

        except Exception as e:
            logger.error(f"Error in market sentiment analysis: {e}")

        return {
            "overall_motivation_index": 35.0,
            "areas_analyzed": 0,
            "error": "Market sentiment analysis temporarily unavailable",
        }

    async def _identify_opportunity_areas(self) -> List[Dict[str, Any]]:
        """Identify high-opportunity geographic areas for prospecting."""

        try:
            sentiment_radar = await self.get_sentiment_radar()

            # Get location recommendations
            territory = ["78731", "78746", "78759", "78704", "78745", "78738", "78735"]
            recommendations = await sentiment_radar.get_location_recommendations(territory, max_locations=5)

            # Convert to opportunity format
            opportunities = []
            for rec in recommendations[:3]:  # Top 3 opportunities
                opportunities.append(
                    {
                        "location": rec["location"],
                        "opportunity_score": rec["prospecting_score"],
                        "motivation_index": rec["motivation_index"],
                        "recommended_timing": rec["optimal_window"],
                        "key_triggers": rec["key_triggers"],
                        "confidence": rec["confidence"],
                        "action": f"Focus prospecting efforts in {rec['location']} - {rec['optimal_window']} timing",
                    }
                )

            return opportunities

        except Exception as e:
            logger.error(f"Error identifying opportunity areas: {e}")
            return []

    async def _analyze_deal_risks(self) -> List[Dict[str, Any]]:
        """Analyze current deals for risk factors."""

        try:
            deal_rescue = await self.get_deal_rescue()

            # Get current active deals (mock data - replace with actual CRM integration)
            active_deals = await self._get_active_deals()

            at_risk_deals = []

            for deal in active_deals[:5]:  # Analyze top 5 deals by value
                try:
                    risk_profile = await deal_rescue.assess_deal_risk(deal["deal_id"], deal.get("conversation_context"))

                    if risk_profile.overall_churn_risk > 0.3:  # 30%+ risk
                        at_risk_deals.append(
                            {
                                "deal_id": deal["deal_id"],
                                "deal_value": risk_profile.deal_value,
                                "commission_value": risk_profile.commission_value,
                                "risk_level": risk_profile.overall_churn_risk,
                                "urgency": risk_profile.urgency_level.value,
                                "time_to_loss": risk_profile.time_to_expected_loss,
                                "risk_factors": risk_profile.risk_factors[:3],
                                "days_active": risk_profile.days_since_contract,
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error analyzing deal {deal['deal_id']}: {e}")

            # Sort by risk level and deal value
            at_risk_deals.sort(key=lambda d: d["risk_level"] * (d["deal_value"] / 1000000), reverse=True)

            return at_risk_deals[:3]  # Top 3 at-risk deals

        except Exception as e:
            logger.error(f"Error analyzing deal risks: {e}")
            return []

    async def _get_active_deals(self) -> List[Dict[str, Any]]:
        """Get active deals from GHL CRM."""
        try:
            ghl_service = await get_ghl_deal_intelligence_service()

            # Get high-value active deals (prioritize deals worth monitoring)
            deals = await ghl_service.get_active_deals(
                limit=50,
                min_value=300000,  # $300K minimum for intelligence analysis
            )

            # Convert to format expected by intelligence coordinator
            active_deals = []

            for deal in deals:
                # Prepare conversation context
                conversation_context = {"messages": []}

                # Format recent messages for analysis
                for message in deal.recent_messages[:10]:  # Last 10 messages
                    conversation_context["messages"].append(
                        {
                            "content": message.get("content", ""),
                            "timestamp": message.get("timestamp", ""),
                            "direction": message.get("direction", "unknown"),
                        }
                    )

                # Classify buyer type
                buyer_type = "first_time"
                tags = [tag.lower() for tag in deal.tags]
                if any(tag in tags for tag in ["investor", "investment"]):
                    buyer_type = "investor"
                elif any(tag in tags for tag in ["relocating", "relocation"]):
                    buyer_type = "relocating"
                elif deal.deal_value > 1000000:
                    buyer_type = "luxury"

                deal_dict = {
                    "deal_id": deal.deal_id,
                    "deal_value": deal.deal_value,
                    "commission_value": deal.commission_value,
                    "days_active": deal.days_since_creation,
                    "buyer_type": buyer_type,
                    "property_type": deal.property_type or "single_family",
                    "conversation_context": conversation_context,
                    "deal_stage": deal.deal_stage,
                    "last_contact_date": deal.last_contact_date,
                    "expected_close_date": deal.expected_close_date,
                    "contact_name": deal.contact_name,
                    "contact_id": deal.contact_id,
                    "pipeline_id": deal.pipeline_id,
                    "property_address": deal.property_address,
                    "deal_source": deal.deal_source,
                    "tags": deal.tags,
                }

                active_deals.append(deal_dict)

            logger.info(f"Retrieved {len(active_deals)} active deals from GHL for intelligence analysis")
            return active_deals

        except Exception as e:
            logger.error(f"Error retrieving active deals from GHL: {e}")

            # Fallback to empty list if GHL integration fails
            logger.warning("GHL integration unavailable, using empty deals list")
            return []

    async def _get_rescue_recommendations(self) -> List[Dict[str, Any]]:
        """Get rescue recommendations for at-risk deals."""

        try:
            deal_rescue = await self.get_deal_rescue()

            # Get high-value at-risk deals
            active_deals = await self._get_active_deals()
            high_value_deals = [d for d in active_deals if d["deal_value"] > 500000]

            recommendations = []

            for deal in high_value_deals[:2]:  # Top 2 high-value deals
                try:
                    alert = await deal_rescue.generate_rescue_alert(deal["deal_id"], deal.get("conversation_context"))

                    if alert:
                        recommendations.append(
                            {
                                "deal_id": deal["deal_id"],
                                "deal_value": deal["deal_value"],
                                "urgency": alert.urgency_level.value,
                                "headline": alert.headline,
                                "immediate_actions": alert.immediate_actions[:2],  # Top 2 actions
                                "strategies": [
                                    {
                                        "strategy": rec.strategy.value,
                                        "priority": rec.priority,
                                        "description": rec.description,
                                    }
                                    for rec in alert.recommended_strategies[:2]
                                ],
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error generating rescue recommendation for {deal['deal_id']}: {e}")

            return recommendations

        except Exception as e:
            logger.error(f"Error getting rescue recommendations: {e}")
            return []

    async def _generate_scenario_recommendations(self) -> List[Dict[str, Any]]:
        """Generate strategic scenario recommendations."""

        try:
            scenario_engine = await self.get_scenario_engine()

            # Analyze key strategic scenarios
            scenarios = [
                {
                    "type": ScenarioType.COMMISSION_ADJUSTMENT,
                    "name": "Commission Rate Optimization",
                    "adjustments": {"commission_rate_change": -0.005},  # -0.5%
                    "description": "Reduce buyer agent commission by 0.5%",
                },
                {
                    "type": ScenarioType.QUALIFICATION_THRESHOLD,
                    "name": "Lead Quality Enhancement",
                    "adjustments": {"threshold_change": 10},  # Raise by 10 points
                    "description": "Increase qualification threshold from 50 to 60",
                },
            ]

            recommendations = []

            for scenario_config in scenarios:
                try:
                    scenario_input = ScenarioInput(
                        scenario_type=scenario_config["type"],
                        base_period="12M",
                        adjustments=scenario_config["adjustments"],
                        simulation_runs=1000,  # Lighter simulation for briefing
                        time_horizon_months=12,
                    )

                    results = await scenario_engine.run_scenario_simulation(scenario_input)

                    # Extract key insights
                    revenue_impact = results.baseline_comparison.get("revenue_change", 0)
                    success_probability = results.success_probability

                    recommendations.append(
                        {
                            "scenario_name": scenario_config["name"],
                            "description": scenario_config["description"],
                            "revenue_impact": f"{revenue_impact:+.1f}%",
                            "success_probability": f"{success_probability:.1%}",
                            "key_insights": results.key_insights[:2],
                            "recommendation": results.recommended_actions[0]
                            if results.recommended_actions
                            else "Further analysis recommended",
                        }
                    )

                except Exception as e:
                    logger.warning(f"Error analyzing scenario {scenario_config['name']}: {e}")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating scenario recommendations: {e}")
            return []

    async def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify business optimization opportunities."""

        opportunities = []

        try:
            # Performance optimization analysis
            current_performance = await self._analyze_current_performance()

            # Lead conversion optimization
            conversion_rate = current_performance.get("conversion_rate", 70)
            if conversion_rate < 75:
                opportunities.append(
                    {
                        "category": "Lead Conversion",
                        "current_performance": f"{conversion_rate:.1f}%",
                        "target_performance": "80%+",
                        "potential_impact": "+$240K annual revenue",
                        "effort_level": "Medium",
                        "recommendation": "Enhance qualification criteria and follow-up processes",
                    }
                )

            # Average deal value optimization
            avg_deal_value = current_performance.get("avg_deal_value", 16000)
            if avg_deal_value < 20000:
                opportunities.append(
                    {
                        "category": "Deal Value",
                        "current_performance": f"${avg_deal_value:,.0f}",
                        "target_performance": "$20K+",
                        "potential_impact": "+$600K annual revenue",
                        "effort_level": "High",
                        "recommendation": "Focus on higher-value properties and premium services",
                    }
                )

            # Market share expansion
            market_share = current_performance.get("market_share", 2.8)
            if market_share < 5.0:
                opportunities.append(
                    {
                        "category": "Market Share",
                        "current_performance": f"{market_share:.1f}%",
                        "target_performance": "5.0%+",
                        "potential_impact": "+$1.2M annual revenue",
                        "effort_level": "High",
                        "recommendation": "Geographic expansion and team scaling",
                    }
                )

        except Exception as e:
            logger.error(f"Error identifying optimization opportunities: {e}")

        return opportunities[:3]  # Top 3 opportunities

    async def _analyze_current_performance(self) -> Dict[str, Any]:
        """Analyze current business performance metrics."""

        try:
            # Get performance data from analytics service
            # In production, this would pull real data from CRM/analytics
            return {
                "monthly_revenue": 200000,
                "monthly_deals": 22,
                "conversion_rate": 71.5,
                "avg_deal_value": 16000,
                "market_share": 2.84,
                "client_satisfaction": 4.7,
                "referral_rate": 31.2,
                "time_to_close": 18.5,  # days
                "lead_response_time": 1.2,  # hours
                "ai_automation_efficiency": 42.0,  # percentage
            }

        except Exception as e:
            logger.error(f"Error analyzing current performance: {e}")
            return {}

    async def _project_performance(self, time_horizon_days: int) -> Dict[str, Any]:
        """Project performance for the given time horizon."""

        try:
            current = await self._analyze_current_performance()

            # Simple projection based on current trends and market conditions
            growth_factor = 1.0 + (0.05 * (time_horizon_days / 365))  # 5% annual growth assumption

            return {
                "projected_revenue": current.get("monthly_revenue", 0) * growth_factor * (time_horizon_days / 30),
                "projected_deals": int(current.get("monthly_deals", 0) * growth_factor * (time_horizon_days / 30)),
                "projected_market_share": min(5.0, current.get("market_share", 0) * growth_factor),
                "confidence_level": 0.75,
                "projection_basis": f"{time_horizon_days} days forward projection",
            }

        except Exception as e:
            logger.error(f"Error projecting performance: {e}")
            return {}

    async def _calculate_health_score(self, briefing: IntelligenceBriefing) -> float:
        """Calculate overall business health score (0-100)."""

        try:
            score_components = []

            # Market sentiment component (0-25 points)
            if briefing.market_sentiment_summary:
                motivation_index = briefing.market_sentiment_summary.get("overall_motivation_index", 35)
                market_score = min(25, motivation_index * 0.4)  # Scale to 25 points max
                score_components.append(market_score)

            # Deal risk component (0-25 points)
            if briefing.at_risk_deals is not None:
                num_at_risk = len(briefing.at_risk_deals)
                risk_score = max(0, 25 - (num_at_risk * 8))  # Penalty for at-risk deals
                score_components.append(risk_score)

            # Performance component (0-25 points)
            if briefing.current_performance:
                conversion_rate = briefing.current_performance.get("conversion_rate", 70)
                satisfaction = briefing.current_performance.get("client_satisfaction", 4.0)

                perf_score = (conversion_rate / 100 * 15) + (satisfaction / 5 * 10)
                score_components.append(perf_score)

            # Opportunity component (0-25 points)
            if briefing.opportunities:
                # More opportunities = higher score (up to a point)
                opp_score = min(25, len(briefing.opportunities) * 5)
                score_components.append(opp_score)

            if score_components:
                return sum(score_components) / len(score_components) * 4  # Scale to 100
            else:
                return 65.0  # Default moderate score

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 60.0

    async def _generate_priority_alerts(self, briefing: IntelligenceBriefing) -> List[Dict[str, Any]]:
        """Generate priority alerts from briefing data."""

        alerts = []

        try:
            # Critical deal risk alerts
            if briefing.at_risk_deals:
                for deal in briefing.at_risk_deals:
                    if deal["risk_level"] > 0.7:  # High risk
                        alerts.append(
                            {
                                "type": "deal_risk",
                                "priority": "critical",
                                "title": f"${deal['deal_value']:,.0f} deal at high risk",
                                "message": f"Deal {deal['deal_id']} showing {deal['risk_level']:.0%} churn probability",
                                "action_required": f"Intervention needed within {deal.get('time_to_loss', 24)} hours",
                                "deal_id": deal["deal_id"],
                            }
                        )

            # Market opportunity alerts
            if briefing.market_sentiment_summary:
                immediate_opps = briefing.market_sentiment_summary.get("immediate_opportunities", [])
                for opp in immediate_opps[:2]:  # Top 2 immediate opportunities
                    alerts.append(
                        {
                            "type": "market_opportunity",
                            "priority": "high",
                            "title": f"High motivation in {opp['location']}",
                            "message": f"Seller motivation index: {opp['motivation_index']:.0f}/100",
                            "action_required": f"Begin outreach {opp['optimal_window']}",
                            "location": opp["location"],
                        }
                    )

            # Performance alerts
            if briefing.current_performance:
                conversion_rate = briefing.current_performance.get("conversion_rate", 70)
                if conversion_rate < 65:
                    alerts.append(
                        {
                            "type": "performance",
                            "priority": "medium",
                            "title": "Conversion rate below target",
                            "message": f"Current rate {conversion_rate:.1f}% vs 75% target",
                            "action_required": "Review lead qualification and follow-up processes",
                        }
                    )

            # Sort alerts by priority
            priority_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
            alerts.sort(key=lambda a: priority_order.get(a["priority"], 0), reverse=True)

        except Exception as e:
            logger.error(f"Error generating priority alerts: {e}")

        return alerts[:5]  # Top 5 alerts

    async def _generate_opportunities(self, briefing: IntelligenceBriefing) -> List[Dict[str, Any]]:
        """Generate opportunity recommendations from briefing data."""

        opportunities = []

        try:
            # Market opportunities from sentiment analysis
            if briefing.high_opportunity_areas:
                for area in briefing.high_opportunity_areas[:2]:  # Top 2 areas
                    opportunities.append(
                        {
                            "type": "market_expansion",
                            "category": "Geographic",
                            "title": f"Focus on {area['location']}",
                            "description": f"High seller motivation ({area['motivation_index']:.0f}/100)",
                            "potential_value": "+15-25% deal flow",
                            "effort_required": "Medium",
                            "timeline": area["recommended_timing"],
                        }
                    )

            # Strategic opportunities from scenarios
            if briefing.scenario_recommendations:
                for scenario in briefing.scenario_recommendations[:2]:
                    if "+" in scenario["revenue_impact"]:  # Positive impact
                        opportunities.append(
                            {
                                "type": "strategic_optimization",
                                "category": "Operations",
                                "title": scenario["scenario_name"],
                                "description": scenario["description"],
                                "potential_value": f"{scenario['revenue_impact']} revenue impact",
                                "effort_required": "High",
                                "timeline": "3-6 months",
                            }
                        )

            # Technology and process opportunities
            if briefing.optimization_opportunities:
                for opt in briefing.optimization_opportunities[:2]:
                    opportunities.append(
                        {
                            "type": "process_improvement",
                            "category": opt["category"],
                            "title": f"Optimize {opt['category']}",
                            "description": opt["recommendation"],
                            "potential_value": opt["potential_impact"],
                            "effort_required": opt["effort_level"],
                            "timeline": "2-4 months",
                        }
                    )

        except Exception as e:
            logger.error(f"Error generating opportunities: {e}")

        return opportunities[:6]  # Top 6 opportunities

    def _calculate_briefing_confidence(self, briefing: IntelligenceBriefing) -> float:
        """Calculate confidence score for the briefing."""

        confidence_factors = []

        # Data availability factor
        data_completeness = 0
        total_sections = 6  # market, deals, scenarios, performance, alerts, opportunities

        if briefing.market_sentiment_summary:
            data_completeness += 1
        if briefing.at_risk_deals is not None:
            data_completeness += 1
        if briefing.scenario_recommendations:
            data_completeness += 1
        if briefing.current_performance:
            data_completeness += 1
        if briefing.priority_alerts:
            data_completeness += 1
        if briefing.opportunities:
            data_completeness += 1

        confidence_factors.append(data_completeness / total_sections)

        # Analysis depth factor
        analysis_depth = 0.8 if briefing.briefing_level == IntelligenceLevel.COMPREHENSIVE else 0.7
        confidence_factors.append(analysis_depth)

        # Data freshness factor (assume current data)
        freshness_factor = 0.9
        confidence_factors.append(freshness_factor)

        return sum(confidence_factors) / len(confidence_factors)


# Singleton instance
_intelligence_coordinator = None


async def get_enhanced_intelligence_coordinator() -> EnhancedIntelligenceCoordinator:
    """Get singleton enhanced intelligence coordinator."""
    global _intelligence_coordinator
    if _intelligence_coordinator is None:
        _intelligence_coordinator = EnhancedIntelligenceCoordinator()
    return _intelligence_coordinator
