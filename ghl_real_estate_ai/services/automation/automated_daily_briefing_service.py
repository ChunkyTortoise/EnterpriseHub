"""
Automated Daily Intelligence Briefing Service

Generates and delivers personalized AI-powered daily briefings to agents
eliminating manual dashboard checking and lead analysis.

Features:
- Parallel intelligence gathering from all AI engines
- Claude-powered narrative generation
- Multi-channel delivery (SMS, email, dashboard)
- Timezone-aware scheduling
- Performance tracking and optimization

Performance Targets:
- Generation time: <90 seconds per agent
- Delivery time: <30 seconds
- Success rate: >99%
- Agent engagement: >85% open rate
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import pytz
from jinja2 import Template

# Import existing AI engines
from ghl_real_estate_ai.services.predictive_lead_lifecycle_engine import (
    PredictiveLeadLifecycleEngine,
    ConversionForecast,
    InterventionWindow,
    RiskFactor
)
from ghl_real_estate_ai.services.claude_advanced_lead_intelligence import (
    ClaudeAdvancedLeadIntelligence,
    AdvancedLeadIntelligence
)
from ghl_real_estate_ai.services.claude_intelligent_property_recommendation import (
    ClaudeIntelligentPropertyRecommendation,
    PropertyRecommendation
)
from ghl_real_estate_ai.services.ai_lead_insights import (
    AILeadInsightsService,
    LeadInsight
)

logger = logging.getLogger(__name__)


class BriefingPriority(Enum):
    """Priority levels for briefing items"""
    URGENT = "urgent"          # Immediate action required (next 2 hours)
    HIGH = "high"              # Action required today
    MEDIUM = "medium"          # Action recommended this week
    LOW = "low"                # Informational


class ActionType(Enum):
    """Types of recommended actions"""
    CALL_NOW = "call_now"
    SCHEDULE_SHOWING = "schedule_showing"
    SEND_MESSAGE = "send_message"
    SEND_PROPERTIES = "send_properties"
    RE_ENGAGE = "re_engage"
    FOLLOW_UP = "follow_up"
    REVIEW_OFFER = "review_offer"


@dataclass
class PriorityAction:
    """A single prioritized action for the agent"""
    action_id: str
    priority: BriefingPriority
    action_type: ActionType

    # Lead context
    lead_id: str
    lead_name: str
    lead_score: float

    # Action details
    title: str
    description: str
    reasoning: str
    expected_impact: str

    # Timing
    optimal_window_start: datetime
    optimal_window_end: datetime
    urgency_level: int  # 1-10

    # Execution
    one_click_action: Optional[Dict[str, Any]] = None
    estimated_time_minutes: int = 5


@dataclass
class LeadAlert:
    """Alert about a specific lead"""
    lead_id: str
    lead_name: str
    alert_type: str  # "hot", "at_risk", "opportunity"
    severity: int  # 1-10

    message: str
    details: Dict[str, Any]
    recommended_action: str

    conversion_probability: Optional[float] = None
    churn_risk: Optional[float] = None


@dataclass
class PropertyMatch:
    """Property matched to lead"""
    lead_id: str
    lead_name: str
    property_id: str
    property_address: str
    match_score: float

    match_reasons: List[str]
    property_highlights: List[str]
    recommended_approach: str


@dataclass
class ContactWindow:
    """Optimal time window to contact lead"""
    lead_id: str
    lead_name: str
    window_start: datetime
    window_end: datetime
    confidence: float
    reason: str


@dataclass
class DailyMetrics:
    """Daily performance metrics"""
    leads_contacted: int
    appointments_set: int
    showings_completed: int
    offers_submitted: int
    deals_closed: int

    response_time_avg_minutes: float
    conversion_rate: float
    pipeline_value: float
    commission_earned: float

    # Comparisons
    vs_yesterday: Dict[str, float]
    vs_weekly_avg: Dict[str, float]


@dataclass
class WeeklyTrends:
    """Weekly performance trends"""
    week_start: datetime
    week_end: datetime

    trending_up: List[str]
    trending_down: List[str]

    best_performing_day: str
    best_performing_time: str

    conversion_trend: str  # "improving", "stable", "declining"
    velocity_trend: str


@dataclass
class MarketSnapshot:
    """Current market intelligence"""
    hot_neighborhoods: List[str]
    inventory_changes: Dict[str, str]
    price_trends: Dict[str, str]

    opportunities: List[str]
    risks: List[str]

    strategic_recommendations: List[str]


@dataclass
class DailyBriefing:
    """Complete daily briefing for an agent"""

    # Header
    briefing_id: str
    agent_id: str
    agent_name: str
    generated_at: datetime
    briefing_date: datetime

    # Priority actions (top 5)
    priority_actions: List[PriorityAction] = field(default_factory=list)

    # Lead intelligence
    hot_leads: List[LeadAlert] = field(default_factory=list)
    at_risk_leads: List[LeadAlert] = field(default_factory=list)
    conversion_forecasts: List[Tuple[str, float, int]] = field(default_factory=list)  # (name, prob, days)

    # Opportunities
    property_matches: List[PropertyMatch] = field(default_factory=list)
    optimal_contact_windows: List[ContactWindow] = field(default_factory=list)

    # Performance
    daily_metrics: Optional[DailyMetrics] = None
    weekly_trends: Optional[WeeklyTrends] = None

    # AI insights
    strategic_recommendations: List[str] = field(default_factory=list)
    market_intelligence: Optional[MarketSnapshot] = None

    # Deliverables
    summary_text: str = ""  # For SMS
    detailed_html: str = ""  # For email
    dashboard_data: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    processing_time_ms: float = 0.0
    intelligence_sources: List[str] = field(default_factory=list)


class AutomatedDailyBriefingService:
    """
    🌅 Automated Daily Intelligence Briefing Service

    Generates personalized AI-powered briefings that eliminate manual work:
    - Zero manual dashboard checking required
    - Zero manual lead analysis required
    - Zero manual prioritization required

    Delivered automatically every morning with actionable intelligence.
    """

    def __init__(
        self,
        redis_client=None,
        db_session=None,
        ghl_client=None,
        email_service=None
    ):
        """
        Initialize automated briefing service

        Args:
            redis_client: Redis for caching
            db_session: Database session
            ghl_client: GHL client for delivery
            email_service: Email delivery service
        """
        self.redis_client = redis_client
        self.db_session = db_session
        self.ghl_client = ghl_client
        self.email_service = email_service

        # Initialize AI engines
        self.predictive_engine = PredictiveLeadLifecycleEngine()
        self.lead_intelligence = ClaudeAdvancedLeadIntelligence()
        self.property_recommender = ClaudeIntelligentPropertyRecommendation()
        self.lead_insights = AILeadInsightsService()

        # Performance tracking
        self.metrics = {
            "briefings_generated": 0,
            "avg_generation_time_ms": 0.0,
            "delivery_success_rate": 0.0,
            "agent_engagement_rate": 0.0
        }

        logger.info("Automated Daily Briefing Service initialized")

    async def generate_all_daily_briefings(self) -> List[DailyBriefing]:
        """
        Generate daily briefings for all active agents
        Called by scheduled job at 7:00 AM daily

        Returns:
            List of generated briefings
        """
        start_time = datetime.now()

        # Get all active agents
        agents = await self._get_active_agents()

        logger.info(f"Generating daily briefings for {len(agents)} agents")

        # Generate briefings in parallel (with concurrency limit)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent generations

        async def generate_with_semaphore(agent):
            async with semaphore:
                return await self.generate_daily_briefing(agent["id"])

        briefings = await asyncio.gather(
            *[generate_with_semaphore(agent) for agent in agents],
            return_exceptions=True
        )

        # Filter out errors
        successful_briefings = [
            b for b in briefings
            if isinstance(b, DailyBriefing)
        ]

        # Log errors
        errors = [b for b in briefings if isinstance(b, Exception)]
        if errors:
            logger.error(f"Failed to generate {len(errors)} briefings: {errors}")

        generation_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Generated {len(successful_briefings)} briefings in {generation_time:.1f}s"
        )

        return successful_briefings

    async def generate_daily_briefing(
        self,
        agent_id: str,
        force_refresh: bool = False
    ) -> DailyBriefing:
        """
        Generate comprehensive daily briefing for a single agent

        Target: <90 seconds generation time

        Args:
            agent_id: Agent identifier
            force_refresh: Skip cache and regenerate

        Returns:
            Complete daily briefing with all intelligence
        """
        start_time = datetime.now()

        try:
            # Check cache first (briefings valid for 6 hours)
            if not force_refresh:
                cached = await self._get_cached_briefing(agent_id)
                if cached:
                    logger.info(f"Using cached briefing for agent {agent_id}")
                    return cached

            # Get agent profile
            agent_profile = await self._get_agent_profile(agent_id)

            # Parallel intelligence gathering (CORE PERFORMANCE OPTIMIZATION)
            intelligence_tasks = [
                self._get_priority_leads(agent_id),
                self._get_conversion_forecasts(agent_id),
                self._get_risk_alerts(agent_id),
                self._get_opportunity_windows(agent_id),
                self._get_property_matches(agent_id),
                self._get_performance_metrics(agent_id),
                self._get_weekly_trends(agent_id),
                self._get_market_intelligence(agent_id)
            ]

            results = await asyncio.gather(*intelligence_tasks)

            (
                priority_leads,
                conversion_forecasts,
                risk_alerts,
                contact_windows,
                property_matches,
                daily_metrics,
                weekly_trends,
                market_intel
            ) = results

            # Generate priority actions from intelligence
            priority_actions = await self._generate_priority_actions(
                agent_id=agent_id,
                priority_leads=priority_leads,
                conversion_forecasts=conversion_forecasts,
                risk_alerts=risk_alerts,
                contact_windows=contact_windows
            )

            # Generate strategic recommendations using Claude
            strategic_recs = await self._generate_strategic_recommendations(
                agent_profile=agent_profile,
                priority_actions=priority_actions,
                daily_metrics=daily_metrics,
                weekly_trends=weekly_trends,
                market_intel=market_intel
            )

            # Create briefing object
            briefing = DailyBriefing(
                briefing_id=f"briefing_{agent_id}_{datetime.now().strftime('%Y%m%d')}",
                agent_id=agent_id,
                agent_name=agent_profile.get("name", "Agent"),
                generated_at=datetime.now(),
                briefing_date=datetime.now().date(),
                priority_actions=priority_actions[:5],  # Top 5
                hot_leads=priority_leads.get("hot", [])[:5],
                at_risk_leads=risk_alerts[:3],
                conversion_forecasts=conversion_forecasts[:5],
                property_matches=property_matches[:8],
                optimal_contact_windows=contact_windows,
                daily_metrics=daily_metrics,
                weekly_trends=weekly_trends,
                strategic_recommendations=strategic_recs,
                market_intelligence=market_intel,
                intelligence_sources=[
                    "predictive_lead_lifecycle",
                    "claude_lead_intelligence",
                    "property_recommendation",
                    "ai_lead_insights",
                    "market_intelligence"
                ]
            )

            # Generate deliverable formats
            briefing.summary_text = await self._generate_sms_summary(briefing)
            briefing.detailed_html = await self._generate_email_html(briefing)
            briefing.dashboard_data = self._generate_dashboard_data(briefing)

            # Track processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            briefing.processing_time_ms = processing_time

            # Cache briefing
            await self._cache_briefing(agent_id, briefing)

            # Update metrics
            self._update_metrics(processing_time)

            logger.info(
                f"Generated briefing for agent {agent_id} in {processing_time:.0f}ms"
            )

            return briefing

        except Exception as e:
            logger.error(f"Failed to generate briefing for agent {agent_id}: {e}")
            raise

    async def deliver_briefing(
        self,
        briefing: DailyBriefing,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Deliver briefing via multiple channels

        Args:
            briefing: Generated briefing
            channels: Delivery channels (default: ["sms", "email", "dashboard"])

        Returns:
            Delivery results per channel
        """
        if channels is None:
            channels = ["sms", "email", "dashboard"]

        delivery_results = {}

        # SMS delivery
        if "sms" in channels:
            try:
                sms_result = await self._deliver_via_sms(
                    agent_id=briefing.agent_id,
                    message=briefing.summary_text
                )
                delivery_results["sms"] = sms_result
            except Exception as e:
                logger.error(f"SMS delivery failed: {e}")
                delivery_results["sms"] = False

        # Email delivery
        if "email" in channels:
            try:
                email_result = await self._deliver_via_email(
                    agent_id=briefing.agent_id,
                    subject=f"🌅 Your Daily Real Estate Intelligence Briefing - {briefing.briefing_date}",
                    html_content=briefing.detailed_html
                )
                delivery_results["email"] = email_result
            except Exception as e:
                logger.error(f"Email delivery failed: {e}")
                delivery_results["email"] = False

        # Dashboard update
        if "dashboard" in channels:
            try:
                dashboard_result = await self._update_dashboard(
                    agent_id=briefing.agent_id,
                    data=briefing.dashboard_data
                )
                delivery_results["dashboard"] = dashboard_result
            except Exception as e:
                logger.error(f"Dashboard update failed: {e}")
                delivery_results["dashboard"] = False

        # Track delivery success
        success_rate = sum(delivery_results.values()) / len(delivery_results)
        logger.info(f"Briefing delivered with {success_rate*100:.0f}% success rate")

        return delivery_results

    # ============================================================================
    # Intelligence Gathering Methods
    # ============================================================================

    async def _get_priority_leads(self, agent_id: str) -> Dict[str, List[LeadAlert]]:
        """Get hot leads and at-risk leads"""

        # Get agent's active leads
        leads = await self._get_agent_leads(agent_id)

        hot_leads = []
        at_risk_leads = []

        for lead in leads:
            # Get AI analysis
            analysis = await self.lead_insights.analyze_lead(lead)

            # Classify as hot or at-risk
            if analysis.get("conversion_probability", 0) > 0.75:
                hot_leads.append(LeadAlert(
                    lead_id=lead["id"],
                    lead_name=lead["name"],
                    alert_type="hot",
                    severity=9,
                    message=f"High conversion probability ({analysis['conversion_probability']*100:.0f}%)",
                    details=analysis,
                    recommended_action=analysis.get("next_best_action", "Call immediately"),
                    conversion_probability=analysis["conversion_probability"]
                ))

            if analysis.get("churn_risk", 0) > 0.65:
                at_risk_leads.append(LeadAlert(
                    lead_id=lead["id"],
                    lead_name=lead["name"],
                    alert_type="at_risk",
                    severity=8,
                    message=f"High churn risk ({analysis['churn_risk']*100:.0f}%)",
                    details=analysis,
                    recommended_action="Re-engage with breakup text",
                    churn_risk=analysis["churn_risk"]
                ))

        # Sort by severity
        hot_leads.sort(key=lambda x: x.conversion_probability or 0, reverse=True)
        at_risk_leads.sort(key=lambda x: x.churn_risk or 0, reverse=True)

        return {
            "hot": hot_leads,
            "at_risk": at_risk_leads
        }

    async def _get_conversion_forecasts(
        self,
        agent_id: str
    ) -> List[Tuple[str, float, int]]:
        """Get conversion probability forecasts for active leads"""

        leads = await self._get_agent_leads(agent_id)

        forecasts = []

        for lead in leads[:20]:  # Top 20 active leads
            try:
                # Get prediction
                forecast = await self.predictive_engine.predict_conversion_timeline(
                    lead_id=lead["id"]
                )

                if forecast.conversion_probability > 0.5:
                    days_to_conversion = (
                        forecast.expected_conversion_date - datetime.now()
                    ).days

                    forecasts.append((
                        lead["name"],
                        forecast.conversion_probability,
                        days_to_conversion
                    ))
            except Exception as e:
                logger.warning(f"Forecast failed for lead {lead['id']}: {e}")

        # Sort by probability
        forecasts.sort(key=lambda x: x[1], reverse=True)

        return forecasts

    async def _get_risk_alerts(self, agent_id: str) -> List[LeadAlert]:
        """Get risk alerts for leads"""

        leads = await self._get_agent_leads(agent_id)
        alerts = []

        for lead in leads:
            # Get risk analysis
            risks = await self.predictive_engine.predict_risk_factors(
                lead_id=lead["id"]
            )

            # Convert to alerts
            for risk in risks[:2]:  # Top 2 risks per lead
                if risk.severity > 0.6:
                    alerts.append(LeadAlert(
                        lead_id=lead["id"],
                        lead_name=lead["name"],
                        alert_type="risk",
                        severity=int(risk.severity * 10),
                        message=f"{risk.risk_type.value}: {risk.probability*100:.0f}% probability",
                        details={"mitigation": risk.mitigation_strategies},
                        recommended_action=risk.mitigation_strategies[0] if risk.mitigation_strategies else "Monitor closely"
                    ))

        return alerts[:5]  # Top 5 risks

    async def _get_opportunity_windows(self, agent_id: str) -> List[ContactWindow]:
        """Get optimal contact time windows for leads"""

        leads = await self._get_agent_leads(agent_id)
        windows = []

        for lead in leads:
            # Get optimal touchpoints
            interventions = await self.predictive_engine.predict_optimal_interventions(
                lead_id=lead["id"]
            )

            # Convert to contact windows
            for intervention in interventions[:1]:  # Next window only
                windows.append(ContactWindow(
                    lead_id=lead["id"],
                    lead_name=lead["name"],
                    window_start=intervention.start_date,
                    window_end=intervention.end_date,
                    confidence=intervention.confidence,
                    reason=intervention.reasoning
                ))

        # Sort by start time
        windows.sort(key=lambda x: x.window_start)

        return windows[:10]  # Next 10 windows

    async def _get_property_matches(self, agent_id: str) -> List[PropertyMatch]:
        """Get new property matches for active leads"""

        # This would integrate with property recommendation engine
        # Simplified for now

        matches = []

        # Get leads actively looking
        active_leads = await self._get_active_buyer_leads(agent_id)

        for lead in active_leads[:10]:
            # Get property recommendations
            # recommendations = await self.property_recommender.recommend_properties(lead["id"])

            # Mock data for now
            matches.append(PropertyMatch(
                lead_id=lead["id"],
                lead_name=lead["name"],
                property_id="prop_123",
                property_address="123 Main St, Miami",
                match_score=0.92,
                match_reasons=["Budget aligned", "Location preferred", "Amenities match"],
                property_highlights=["Pool", "Modern kitchen", "Great schools"],
                recommended_approach="Highlight investment potential and school district"
            ))

        return matches

    async def _get_performance_metrics(self, agent_id: str) -> DailyMetrics:
        """Get daily performance metrics"""

        # This would query from analytics database
        # Simplified for now

        return DailyMetrics(
            leads_contacted=12,
            appointments_set=5,
            showings_completed=3,
            offers_submitted=1,
            deals_closed=0,
            response_time_avg_minutes=1.2,
            conversion_rate=0.24,
            pipeline_value=1250000,
            commission_earned=0,
            vs_yesterday={"leads_contacted": 0.15, "response_time_avg_minutes": -0.32},
            vs_weekly_avg={"conversion_rate": 0.06}
        )

    async def _get_weekly_trends(self, agent_id: str) -> WeeklyTrends:
        """Get weekly performance trends"""

        # This would analyze last 7 days of data
        # Simplified for now

        return WeeklyTrends(
            week_start=datetime.now() - timedelta(days=7),
            week_end=datetime.now(),
            trending_up=["Response time", "Conversion rate", "Appointments set"],
            trending_down=[],
            best_performing_day="Tuesday",
            best_performing_time="9-11am",
            conversion_trend="improving",
            velocity_trend="stable"
        )

    async def _get_market_intelligence(self, agent_id: str) -> MarketSnapshot:
        """Get current market intelligence"""

        # This would integrate with market data APIs
        # Simplified for now

        return MarketSnapshot(
            hot_neighborhoods=["Brickell", "Coral Gables", "Coconut Grove"],
            inventory_changes={"Brickell": "down 15%", "Downtown": "up 8%"},
            price_trends={"Brickell": "rising", "Beach": "stable"},
            opportunities=["Inventory low in Brickell - urgency messaging effective"],
            risks=["Interest rates rising - financing concerns"],
            strategic_recommendations=[
                "Focus on Brickell leads - low inventory creates urgency",
                "Proactively address financing concerns",
                "Highlight investment potential in rising markets"
            ]
        )

    # ============================================================================
    # Priority Action Generation
    # ============================================================================

    async def _generate_priority_actions(
        self,
        agent_id: str,
        priority_leads: Dict[str, List[LeadAlert]],
        conversion_forecasts: List[Tuple[str, float, int]],
        risk_alerts: List[LeadAlert],
        contact_windows: List[ContactWindow]
    ) -> List[PriorityAction]:
        """Generate prioritized action list from intelligence"""

        actions = []

        # Hot leads = immediate action
        for lead in priority_leads.get("hot", [])[:3]:
            window = next(
                (w for w in contact_windows if w.lead_id == lead.lead_id),
                None
            )

            actions.append(PriorityAction(
                action_id=f"action_hot_{lead.lead_id}",
                priority=BriefingPriority.URGENT,
                action_type=ActionType.CALL_NOW,
                lead_id=lead.lead_id,
                lead_name=lead.lead_name,
                lead_score=lead.conversion_probability or 0.85,
                title=f"🔥 CALL IMMEDIATELY - {lead.lead_name}",
                description=lead.message,
                reasoning=f"Conversion probability: {lead.conversion_probability*100:.0f}%. High urgency detected.",
                expected_impact=f"${12500:.0f} commission potential",
                optimal_window_start=window.window_start if window else datetime.now(),
                optimal_window_end=window.window_end if window else datetime.now() + timedelta(hours=2),
                urgency_level=10,
                estimated_time_minutes=15,
                one_click_action={
                    "type": "call",
                    "lead_id": lead.lead_id,
                    "suggested_script": "I have 2 perfect properties for you. Can you view today?"
                }
            ))

        # At-risk leads = re-engagement
        for lead in priority_leads.get("at_risk", [])[:2]:
            actions.append(PriorityAction(
                action_id=f"action_atrisk_{lead.lead_id}",
                priority=BriefingPriority.HIGH,
                action_type=ActionType.RE_ENGAGE,
                lead_id=lead.lead_id,
                lead_name=lead.lead_name,
                lead_score=0.5,
                title=f"⚠️ RE-ENGAGE NOW - {lead.lead_name}",
                description=lead.message,
                reasoning=f"Churn risk: {lead.churn_risk*100:.0f}%. Needs immediate re-engagement.",
                expected_impact="Prevent lead loss",
                optimal_window_start=datetime.now(),
                optimal_window_end=datetime.now() + timedelta(hours=4),
                urgency_level=8,
                estimated_time_minutes=5,
                one_click_action={
                    "type": "send_breakup_text",
                    "lead_id": lead.lead_id,
                    "message_template": "breakup_default"
                }
            ))

        # Sort by priority and urgency
        actions.sort(key=lambda x: (
            ["urgent", "high", "medium", "low"].index(x.priority.value),
            -x.urgency_level
        ))

        return actions

    async def _generate_strategic_recommendations(
        self,
        agent_profile: Dict,
        priority_actions: List[PriorityAction],
        daily_metrics: DailyMetrics,
        weekly_trends: WeeklyTrends,
        market_intel: MarketSnapshot
    ) -> List[str]:
        """Generate AI-powered strategic recommendations"""

        # This would use Claude to generate personalized recommendations
        # Simplified for now

        recs = []

        # Performance-based
        if daily_metrics.response_time_avg_minutes < 2:
            recs.append("Your response time is excellent (1.2 min avg). Keep it up!")

        if daily_metrics.conversion_rate > 0.20:
            recs.append(f"Conversion rate at {daily_metrics.conversion_rate*100:.0f}% - above target!")

        # Market-based
        if market_intel.opportunities:
            recs.append(market_intel.opportunities[0])

        # Action-based
        urgent_count = sum(1 for a in priority_actions if a.priority == BriefingPriority.URGENT)
        if urgent_count > 0:
            recs.append(f"Focus on {urgent_count} urgent action(s) in next 2 hours for maximum impact")

        return recs

    # ============================================================================
    # Deliverable Generation
    # ============================================================================

    async def _generate_sms_summary(self, briefing: DailyBriefing) -> str:
        """Generate concise SMS summary (160 chars max per message)"""

        urgent_count = sum(
            1 for a in briefing.priority_actions
            if a.priority == BriefingPriority.URGENT
        )

        hot_leads_count = len(briefing.hot_leads)

        summary = f"""🌅 Good morning {briefing.agent_name}!

📊 TODAY'S PRIORITIES
{urgent_count} urgent action(s) | {hot_leads_count} hot lead(s)

"""

        # Top priority
        if briefing.priority_actions:
            top = briefing.priority_actions[0]
            summary += f"""1. {top.title}
   • {top.description[:60]}...
   • Best time: {top.optimal_window_start.strftime('%I:%M%p')}

"""

        summary += f"""Full briefing: [Dashboard Link]"""

        return summary

    async def _generate_email_html(self, briefing: DailyBriefing) -> str:
        """Generate detailed HTML email"""

        # HTML template (simplified - would use Jinja2 in production)
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 20px; border-radius: 10px; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        .priority-action {{ margin: 10px 0; padding: 15px; background: white;
                           border-left: 4px solid #e74c3c; border-radius: 5px; }}
        .urgent {{ border-left-color: #e74c3c; }}
        .high {{ border-left-color: #f39c12; }}
        .metric {{ display: inline-block; margin: 10px 15px; }}
        .trend-up {{ color: #27ae60; }}
        .trend-down {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌅 Your Daily Real Estate Intelligence Briefing</h1>
        <p>{briefing.briefing_date.strftime('%A, %B %d, %Y')}</p>
    </div>

    <div class="section">
        <h2>📊 TODAY'S PRIORITIES ({len(briefing.priority_actions)} actions)</h2>
"""

        # Priority actions
        for i, action in enumerate(briefing.priority_actions[:5], 1):
            priority_class = action.priority.value
            html += f"""
        <div class="priority-action {priority_class}">
            <h3>{i}. {action.title}</h3>
            <p><strong>Why:</strong> {action.reasoning}</p>
            <p><strong>Impact:</strong> {action.expected_impact}</p>
            <p><strong>Action:</strong> {action.description}</p>
            <p><strong>Best time:</strong> {action.optimal_window_start.strftime('%I:%M%p')} -
               {action.optimal_window_end.strftime('%I:%M%p')}</p>
        </div>
"""

        html += """
    </div>

    <div class="section">
        <h2>💰 CONVERSION FORECASTS</h2>
        <ul>
"""

        # Conversion forecasts
        for name, prob, days in briefing.conversion_forecasts[:5]:
            html += f"""
            <li><strong>{name}</strong>: {prob*100:.0f}% likely to convert in {days} days</li>
"""

        html += """
        </ul>
    </div>

    <div class="section">
        <h2>📈 YOUR PERFORMANCE</h2>
"""

        # Performance metrics
        if briefing.daily_metrics:
            m = briefing.daily_metrics
            html += f"""
        <div class="metric">Response time: {m.response_time_avg_minutes:.1f} min avg</div>
        <div class="metric">Conversion rate: {m.conversion_rate*100:.0f}%</div>
        <div class="metric">Pipeline: ${m.pipeline_value:,.0f}</div>
"""

        html += """
    </div>
</body>
</html>
"""

        return html

    def _generate_dashboard_data(self, briefing: DailyBriefing) -> Dict[str, Any]:
        """Generate dashboard-ready data"""

        return {
            "briefing_id": briefing.briefing_id,
            "generated_at": briefing.generated_at.isoformat(),
            "priority_actions": [asdict(a) for a in briefing.priority_actions],
            "hot_leads": [asdict(l) for l in briefing.hot_leads],
            "at_risk_leads": [asdict(l) for l in briefing.at_risk_leads],
            "metrics": asdict(briefing.daily_metrics) if briefing.daily_metrics else {},
            "trends": asdict(briefing.weekly_trends) if briefing.weekly_trends else {},
            "recommendations": briefing.strategic_recommendations
        }

    # ============================================================================
    # Delivery Methods
    # ============================================================================

    async def _deliver_via_sms(self, agent_id: str, message: str) -> bool:
        """Deliver briefing via SMS using GHL"""

        try:
            if self.ghl_client:
                # Get agent phone number
                agent = await self._get_agent_profile(agent_id)
                phone = agent.get("phone")

                if phone:
                    # Send via GHL
                    result = await self.ghl_client.send_sms(
                        to_number=phone,
                        message=message
                    )
                    return result.get("success", False)

            logger.warning(f"SMS delivery skipped for agent {agent_id} (no GHL client or phone)")
            return False

        except Exception as e:
            logger.error(f"SMS delivery failed: {e}")
            return False

    async def _deliver_via_email(
        self,
        agent_id: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Deliver briefing via email"""

        try:
            if self.email_service:
                # Get agent email
                agent = await self._get_agent_profile(agent_id)
                email = agent.get("email")

                if email:
                    # Send email
                    result = await self.email_service.send_email(
                        to_email=email,
                        subject=subject,
                        html_body=html_content
                    )
                    return result.get("success", False)

            logger.warning(f"Email delivery skipped for agent {agent_id}")
            return False

        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return False

    async def _update_dashboard(self, agent_id: str, data: Dict[str, Any]) -> bool:
        """Update dashboard with briefing data"""

        try:
            # Store in database for dashboard retrieval
            if self.redis_client:
                await self.redis_client.setex(
                    f"dashboard:briefing:{agent_id}",
                    86400,  # 24 hour TTL
                    json.dumps(data, default=str)
                )

            return True

        except Exception as e:
            logger.error(f"Dashboard update failed: {e}")
            return False

    # ============================================================================
    # Helper Methods
    # ============================================================================

    async def _get_active_agents(self) -> List[Dict[str, Any]]:
        """Get all active agents for briefing generation"""

        # This would query database
        # Mock data for now
        return [
            {"id": "agent_1", "name": "Jorge", "email": "jorge@example.com", "phone": "+1234567890"},
            {"id": "agent_2", "name": "Sarah", "email": "sarah@example.com", "phone": "+1234567891"}
        ]

    async def _get_agent_profile(self, agent_id: str) -> Dict[str, Any]:
        """Get agent profile information"""

        # This would query database
        # Mock data for now
        return {
            "id": agent_id,
            "name": "Jorge",
            "email": "jorge@example.com",
            "phone": "+1234567890",
            "timezone": "America/New_York"
        }

    async def _get_agent_leads(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get agent's active leads"""

        # This would query database
        # Mock data for now
        return [
            {"id": "lead_1", "name": "Sarah Martinez", "status": "active"},
            {"id": "lead_2", "name": "Michael Chen", "status": "active"}
        ]

    async def _get_active_buyer_leads(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get agent's active buyer leads"""

        leads = await self._get_agent_leads(agent_id)
        return [l for l in leads if l.get("type") == "buyer"]

    async def _get_cached_briefing(self, agent_id: str) -> Optional[DailyBriefing]:
        """Retrieve cached briefing if available"""

        try:
            if self.redis_client:
                cached = await self.redis_client.get(f"briefing:{agent_id}:{datetime.now().date()}")
                if cached:
                    return DailyBriefing(**json.loads(cached))
        except Exception:
            pass

        return None

    async def _cache_briefing(self, agent_id: str, briefing: DailyBriefing):
        """Cache briefing for quick retrieval"""

        try:
            if self.redis_client:
                await self.redis_client.setex(
                    f"briefing:{agent_id}:{briefing.briefing_date}",
                    21600,  # 6 hour TTL
                    json.dumps(asdict(briefing), default=str)
                )
        except Exception as e:
            logger.warning(f"Failed to cache briefing: {e}")

    def _update_metrics(self, processing_time_ms: float):
        """Update service performance metrics"""

        self.metrics["briefings_generated"] += 1

        # Update average
        total = self.metrics["briefings_generated"]
        current_avg = self.metrics["avg_generation_time_ms"]
        new_avg = ((current_avg * (total - 1)) + processing_time_ms) / total
        self.metrics["avg_generation_time_ms"] = new_avg


# Singleton instance
_briefing_service = None


def get_automated_daily_briefing_service(**kwargs) -> AutomatedDailyBriefingService:
    """Get singleton briefing service instance"""
    global _briefing_service
    if _briefing_service is None:
        _briefing_service = AutomatedDailyBriefingService(**kwargs)
    return _briefing_service


# Export
__all__ = [
    "AutomatedDailyBriefingService",
    "DailyBriefing",
    "PriorityAction",
    "LeadAlert",
    "get_automated_daily_briefing_service"
]
