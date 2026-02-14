#!/usr/bin/env python3
"""
🤖 Service 6 Enhanced Lead Recovery & Nurture Engine - Multi-Agent Lead Intelligence Swarm

Advanced agent orchestration system delivering unprecedented lead intelligence through:
- Collaborative multi-agent analysis with specialized expertise
- Real-time consensus building for lead scoring and prioritization
- Autonomous decision-making with human oversight and approval
- Dynamic agent deployment based on lead complexity and value
- Cross-ontario_mills knowledge synthesis for holistic lead understanding
- Continuous learning and adaptation through agent feedback loops

Date: January 17, 2026
Status: Agent-Driven Lead Intelligence System
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple

from ghl_real_estate_ai.services.agent_state_sync import sync_service
from ghl_real_estate_ai.utils.datetime_utils import parse_iso8601

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("lead_intelligence_swarm.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Specialized agent types for lead intelligence"""

    DEMOGRAPHIC_ANALYZER = "demographic_analyzer"
    BEHAVIORAL_PROFILER = "behavioral_profiler"
    INTENT_DETECTOR = "intent_detector"
    FINANCIAL_ASSESSOR = "financial_assessor"
    ENGAGEMENT_SCORER = "engagement_scorer"
    COMMUNICATION_OPTIMIZER = "communication_optimizer"
    COMPETITIVE_ANALYST = "competitive_analyst"
    TIMING_PREDICTOR = "timing_predictor"
    RISK_EVALUATOR = "risk_evaluator"
    OPPORTUNITY_IDENTIFIER = "opportunity_identifier"
    MARKET_ANALYST = "market_analyst"


class AgentStatus(Enum):
    """Agent operational status"""

    IDLE = "idle"
    ANALYZING = "analyzing"
    COLLABORATING = "collaborating"
    REPORTING = "reporting"
    ERROR = "error"
    LEARNING = "learning"


class ConsensusLevel(Enum):
    """Consensus confidence levels"""

    HIGH = "high"  # 80%+ agent agreement
    MEDIUM = "medium"  # 60-79% agreement
    LOW = "low"  # 40-59% agreement
    CONFLICT = "conflict"  # <40% agreement


@dataclass
class AgentInsight:
    """Individual agent insight"""

    agent_type: AgentType
    confidence: float  # 0.0 - 1.0
    primary_finding: str
    supporting_evidence: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    opportunity_score: float  # 0.0 - 100.0
    urgency_level: str  # low, medium, high, critical
    processing_time_ms: float
    data_sources: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmConsensus:
    """Multi-agent consensus result"""

    lead_id: str
    consensus_level: ConsensusLevel
    overall_score: float  # 0.0 - 100.0
    confidence: float  # 0.0 - 1.0
    primary_recommendation: str
    action_priority: str  # immediate, high, medium, low
    agent_insights: List[AgentInsight]
    conflicting_views: List[Tuple[str, str]]  # (agent_type, conflict_description)
    consensus_rationale: str
    processing_time_ms: float
    timestamp: datetime


class LeadIntelligenceAgent:
    """Base class for specialized lead intelligence agents"""

    def __init__(self, agent_type: AgentType, specialization_config: Dict[str, Any]):
        self.agent_type = agent_type
        self.config = specialization_config
        self.status = AgentStatus.IDLE
        self.performance_metrics = {
            "analyses_completed": 0,
            "average_confidence": 0.0,
            "average_processing_time": 0.0,
            "accuracy_score": 1.0,
            "last_learning_update": None,
        }

        # Agent-specific knowledge base
        self.knowledge_base = self._initialize_knowledge_base()
        self.learning_patterns = []

    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize agent-specific knowledge base"""
        base_knowledge = {
            "version": "2.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "expertise_ontario_mills": self.agent_type.value,
            "confidence_thresholds": {"high": 0.85, "medium": 0.65, "low": 0.45},
        }

        # Add specialized knowledge based on agent type
        if self.agent_type == AgentType.DEMOGRAPHIC_ANALYZER:
            base_knowledge.update(
                {
                    "age_segments": {"gen_z": (18, 26), "millennial": (27, 42), "gen_x": (43, 58), "boomer": (59, 77)},
                    "income_indicators": ["job_title", "company_size", "location", "education", "industry"],
                    "lifestyle_markers": ["social_media_activity", "purchase_patterns", "interests"],
                }
            )

        elif self.agent_type == AgentType.BEHAVIORAL_PROFILER:
            base_knowledge.update(
                {
                    "engagement_patterns": [
                        "page_visit_frequency",
                        "session_duration",
                        "content_interaction",
                        "email_open_rates",
                        "response_times",
                        "channel_preferences",
                    ],
                    "behavioral_indicators": {
                        "high_intent": [
                            "multiple_property_views",
                            "mortgage_calculator_use",
                            "contact_form_completion",
                        ],
                        "price_sensitive": ["frequent_filter_use", "price_range_changes", "comparison_shopping"],
                        "location_focused": ["map_interaction", "neighborhood_research", "school_district_searches"],
                    },
                }
            )

        elif self.agent_type == AgentType.INTENT_DETECTOR:
            base_knowledge.update(
                {
                    "purchase_signals": [
                        "timeline_indicators",
                        "financing_inquiries",
                        "viewing_requests",
                        "urgency_language",
                        "decision_maker_involvement",
                    ],
                    "intent_levels": {
                        "immediate": 0.9,  # Ready to buy within 30 days
                        "near_term": 0.75,  # 1-6 months
                        "exploratory": 0.5,  # 6+ months
                        "passive": 0.25,  # No clear timeline
                    },
                }
            )

        elif self.agent_type == AgentType.FINANCIAL_ASSESSOR:
            base_knowledge.update(
                {
                    "qualification_factors": [
                        "credit_indicators",
                        "income_stability",
                        "debt_to_income",
                        "down_payment_readiness",
                        "employment_history",
                    ],
                    "risk_assessment": {"low_risk": 0.9, "moderate_risk": 0.7, "high_risk": 0.4},
                }
            )

        elif self.agent_type == AgentType.MARKET_ANALYST:
            base_knowledge.update(
                {
                    "market_monitoring": {
                        "mls_feed_sync": True,
                        "price_drop_threshold": 0.03,  # 3% drop triggers alert
                        "competitor_analysis": True,
                    },
                    "predator_mode": {"enabled": True, "alert_synergy": True, "defensive_drafting": True},
                }
            )

        return base_knowledge

    async def analyze_lead(self, lead_data: Dict[str, Any]) -> AgentInsight:
        """Perform specialized analysis on lead data"""
        self.status = AgentStatus.ANALYZING
        start_time = asyncio.get_event_loop().time()

        await sync_service.record_agent_thought(
            agent_id=self.agent_type.value,
            thought=f"Starting analysis for lead {lead_data.get('lead_id', 'N/A')}",
            status="Analyzing",
        )

        try:
            # Delegate to specialized analysis method
            insight = await self._perform_specialized_analysis(lead_data)

            # Update performance metrics
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self._update_performance_metrics(insight.confidence, processing_time)

            self.status = AgentStatus.IDLE

            await sync_service.record_agent_thought(
                agent_id=self.agent_type.value,
                thought=f"Completed analysis for lead {lead_data.get('lead_id', 'N/A')}",
                status="Success",
            )
            return insight

        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent {self.agent_type.value} analysis failed: {e}")

            await sync_service.record_agent_thought(
                agent_id=self.agent_type.value,
                thought=f"Analysis failed for lead {lead_data.get('lead_id', 'N/A')}: {str(e)}",
                status="Error",
            )

            # Return error insight
            return AgentInsight(
                agent_type=self.agent_type,
                confidence=0.0,
                primary_finding=f"Analysis failed: {str(e)}",
                supporting_evidence=[],
                recommendations=[],
                risk_factors=["Analysis failure"],
                opportunity_score=0.0,
                urgency_level="low",
                processing_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                data_sources=[],
            )

    async def _perform_specialized_analysis(self, lead_data: Dict[str, Any]) -> AgentInsight:
        """Override this method in specialized agents"""
        # Base implementation - should be overridden
        await asyncio.sleep(0.1)  # Simulate processing

        return AgentInsight(
            agent_type=self.agent_type,
            confidence=0.5,
            primary_finding="Base agent analysis",
            supporting_evidence=["Generic analysis"],
            recommendations=["No specific recommendations"],
            risk_factors=[],
            opportunity_score=50.0,
            urgency_level="medium",
            processing_time_ms=100.0,
            data_sources=["lead_data"],
        )

    def _update_performance_metrics(self, confidence: float, processing_time: float):
        """Update agent performance tracking"""
        self.performance_metrics["analyses_completed"] += 1

        # Update running averages
        count = self.performance_metrics["analyses_completed"]
        self.performance_metrics["average_confidence"] = (
            self.performance_metrics["average_confidence"] * (count - 1) + confidence
        ) / count
        self.performance_metrics["average_processing_time"] = (
            self.performance_metrics["average_processing_time"] * (count - 1) + processing_time
        ) / count

    async def learn_from_outcome(self, insight: AgentInsight, actual_outcome: Dict[str, Any]):
        """Learn from actual outcomes to improve future analysis"""
        self.status = AgentStatus.LEARNING

        # Calculate prediction accuracy
        predicted_score = insight.opportunity_score
        actual_score = actual_outcome.get("conversion_score", 0.0)

        accuracy = 1.0 - abs(predicted_score - actual_score) / 100.0

        # Update accuracy metrics
        self.performance_metrics["accuracy_score"] = (self.performance_metrics["accuracy_score"] * 0.9) + (
            accuracy * 0.1
        )

        # Store learning pattern
        learning_pattern = {
            "timestamp": datetime.utcnow().isoformat(),
            "predicted_score": predicted_score,
            "actual_score": actual_score,
            "accuracy": accuracy,
            "lead_features": actual_outcome.get("lead_features", {}),
            "insight_metadata": insight.metadata,
        }

        self.learning_patterns.append(learning_pattern)

        # Keep only recent learning patterns
        if len(self.learning_patterns) > 1000:
            self.learning_patterns = self.learning_patterns[-1000:]

        self.performance_metrics["last_learning_update"] = datetime.utcnow().isoformat()
        self.status = AgentStatus.IDLE

        logger.info(f"Agent {self.agent_type.value} learned from outcome - accuracy: {accuracy:.3f}")


class DemographicAnalyzerAgent(LeadIntelligenceAgent):
    """Specialized agent for demographic analysis"""

    def __init__(self):
        super().__init__(
            AgentType.DEMOGRAPHIC_ANALYZER,
            {
                "focus_areas": ["age_segmentation", "income_estimation", "lifestyle_analysis"],
                "data_sources": ["contact_info", "social_profiles", "behavioral_data"],
            },
        )

    async def _perform_specialized_analysis(self, lead_data: Dict[str, Any]) -> AgentInsight:
        """Analyze lead demographics and lifestyle indicators"""
        await asyncio.sleep(0.15)  # Simulate complex analysis

        # Extract demographic indicators
        age = lead_data.get("age", 0)
        location = lead_data.get("location", "")
        job_title = lead_data.get("job_title", "")
        education = lead_data.get("education", "")

        # Analyze age segment
        age_segment = self._determine_age_segment(age)

        # Estimate income bracket
        income_estimate = self._estimate_income(job_title, location, education)

        # Assess buying power
        buying_power_score = self._assess_buying_power(income_estimate, age_segment, location)

        # Generate insights
        primary_finding = f"{age_segment.title()} demographic with {income_estimate} income potential"

        supporting_evidence = [
            f"Age segment: {age_segment}",
            f"Estimated income: {income_estimate}",
            f"Location market: {location}",
            f"Professional level: {job_title}",
        ]

        recommendations = []
        if buying_power_score > 75:
            recommendations.append("High-value target - prioritize premium property recommendations")
            recommendations.append("Schedule immediate consultation with senior agent")
        elif buying_power_score > 50:
            recommendations.append("Qualified buyer - focus on mid-range properties")
            recommendations.append("Provide financing assistance information")
        else:
            recommendations.append("Potential first-time buyer - emphasize affordability programs")
            recommendations.append("Long-term nurture strategy recommended")

        risk_factors = []
        if income_estimate == "low":
            risk_factors.append("Potential financing challenges")
        if age_segment == "gen_z":
            risk_factors.append("Limited down payment savings")

        return AgentInsight(
            agent_type=self.agent_type,
            confidence=0.82,
            primary_finding=primary_finding,
            supporting_evidence=supporting_evidence,
            recommendations=recommendations,
            risk_factors=risk_factors,
            opportunity_score=buying_power_score,
            urgency_level="medium" if buying_power_score > 60 else "low",
            processing_time_ms=150.0,
            data_sources=["demographic_data", "market_analysis", "income_models"],
            metadata={
                "age_segment": age_segment,
                "income_estimate": income_estimate,
                "buying_power_score": buying_power_score,
            },
        )

    def _determine_age_segment(self, age: int) -> str:
        """Determine generational segment"""
        age_segments = self.knowledge_base["age_segments"]

        for segment, (min_age, max_age) in age_segments.items():
            if min_age <= age <= max_age:
                return segment

        return "unknown"

    def _estimate_income(self, job_title: str, location: str, education: str) -> str:
        """Estimate income bracket based on available indicators"""
        # Simplified income estimation logic
        # In production, this would use sophisticated ML models

        score = 0

        # Job title indicators
        senior_titles = ["director", "vp", "senior", "lead", "manager", "executive"]
        professional_titles = ["engineer", "analyst", "consultant", "specialist", "developer"]

        if any(title in job_title.lower() for title in senior_titles):
            score += 40
        elif any(title in job_title.lower() for title in professional_titles):
            score += 25
        else:
            score += 10

        # Education indicators
        if "phd" in education.lower() or "doctorate" in education.lower():
            score += 25
        elif "masters" in education.lower() or "mba" in education.lower():
            score += 20
        elif "bachelors" in education.lower():
            score += 15

        # Location adjustments (simplified)
        high_cost_areas = ["san francisco", "new york", "seattle", "boston"]
        if any(area in location.lower() for area in high_cost_areas):
            score += 15

        # Convert score to income bracket
        if score >= 70:
            return "high"
        elif score >= 45:
            return "medium-high"
        elif score >= 25:
            return "medium"
        else:
            return "low"

    def _assess_buying_power(self, income_estimate: str, age_segment: str, location: str) -> float:
        """Calculate overall buying power score"""
        base_scores = {"high": 85, "medium-high": 70, "medium": 55, "low": 30}

        score = base_scores.get(income_estimate, 30)

        # Age adjustments
        if age_segment in ["millennial", "gen_x"]:
            score += 10  # Peak earning years
        elif age_segment == "boomer":
            score += 5  # Established wealth

        # Location adjustments for market conditions
        # This would integrate with real market data
        score += 5  # Default positive market adjustment

        return min(100.0, score)


class BehavioralProfilerAgent(LeadIntelligenceAgent):
    """Specialized agent for behavioral pattern analysis"""

    def __init__(self):
        super().__init__(
            AgentType.BEHAVIORAL_PROFILER,
            {
                "focus_areas": ["engagement_patterns", "decision_style", "communication_preferences"],
                "tracking_windows": ["7d", "30d", "90d"],
            },
        )

    async def _perform_specialized_analysis(self, lead_data: Dict[str, Any]) -> AgentInsight:
        """Analyze behavioral patterns and engagement indicators"""
        await asyncio.sleep(0.12)  # Simulate behavioral analysis

        # Extract behavioral data
        page_visits = lead_data.get("page_visits", [])
        email_interactions = lead_data.get("email_interactions", [])
        search_patterns = lead_data.get("search_patterns", [])
        response_times = lead_data.get("response_times", [])

        # Analyze engagement depth
        engagement_score = self._calculate_engagement_score(page_visits, email_interactions)

        # Determine decision style
        decision_style = self._analyze_decision_style(search_patterns, page_visits)

        # Assess urgency indicators
        urgency_score = self._assess_urgency_indicators(response_times, page_visits)

        # Generate behavioral profile
        profile = self._generate_behavioral_profile(engagement_score, decision_style, urgency_score)

        primary_finding = f"{profile['type']} buyer with {profile['engagement_level']} engagement"

        supporting_evidence = [
            f"Total page visits: {len(page_visits)}",
            f"Email engagement rate: {profile['email_engagement']:.1f}%",
            f"Decision style: {decision_style}",
            f"Response time pattern: {profile['response_pattern']}",
        ]

        recommendations = []
        if profile["type"] == "analytical":
            recommendations.append("Provide detailed market data and property analytics")
            recommendations.append("Schedule virtual tours with comprehensive information")
        elif profile["type"] == "impulsive":
            recommendations.append("Create urgency with limited-time offers")
            recommendations.append("Schedule immediate viewing appointments")
        elif profile["type"] == "cautious":
            recommendations.append("Build trust through testimonials and references")
            recommendations.append("Provide step-by-step buying process guidance")

        risk_factors = []
        if engagement_score < 30:
            risk_factors.append("Low engagement - may lose interest")
        if urgency_score < 20:
            risk_factors.append("No apparent urgency - long sales cycle expected")

        return AgentInsight(
            agent_type=self.agent_type,
            confidence=0.78,
            primary_finding=primary_finding,
            supporting_evidence=supporting_evidence,
            recommendations=recommendations,
            risk_factors=risk_factors,
            opportunity_score=engagement_score,
            urgency_level=profile["urgency_level"],
            processing_time_ms=120.0,
            data_sources=["behavioral_tracking", "engagement_analytics", "decision_models"],
            metadata=profile,
        )

    def _calculate_engagement_score(self, page_visits: List, email_interactions: List) -> float:
        """Calculate overall engagement score"""
        # Simplified engagement calculation
        visit_score = min(len(page_visits) * 2, 40)  # Up to 40 points for visits
        email_score = min(len(email_interactions) * 5, 30)  # Up to 30 points for emails

        # Time-based engagement (recent activity weighted higher)
        recent_visits = [v for v in page_visits if self._is_recent(v.get("timestamp", ""))]
        recency_score = min(len(recent_visits) * 3, 30)  # Up to 30 points for recent activity

        total_score = visit_score + email_score + recency_score
        return min(100.0, total_score)

    def _analyze_decision_style(self, search_patterns: List, page_visits: List) -> str:
        """Determine buyer's decision-making style"""
        if not search_patterns and not page_visits:
            return "unknown"

        # Analyze search depth and breadth
        unique_properties_viewed = len(set([v.get("property_id") for v in page_visits if v.get("property_id")]))

        if unique_properties_viewed > 10:
            return "analytical"  # Views many properties, compares options
        elif unique_properties_viewed < 3:
            return "impulsive"  # Quick decisions, few comparisons
        else:
            return "cautious"  # Moderate research, careful consideration

    def _assess_urgency_indicators(self, response_times: List, page_visits: List) -> float:
        """Assess buyer urgency based on behavioral indicators"""
        if not response_times:
            return 50.0  # Default medium urgency

        # Fast response times indicate higher urgency
        avg_response_hours = sum(response_times) / len(response_times) if response_times else 24

        if avg_response_hours < 2:
            return 90.0  # Very urgent
        elif avg_response_hours < 6:
            return 75.0  # High urgency
        elif avg_response_hours < 24:
            return 55.0  # Medium urgency
        else:
            return 25.0  # Low urgency

    def _generate_behavioral_profile(
        self, engagement_score: float, decision_style: str, urgency_score: float
    ) -> Dict[str, Any]:
        """Generate comprehensive behavioral profile"""
        # Determine engagement level
        if engagement_score >= 75:
            engagement_level = "high"
        elif engagement_score >= 50:
            engagement_level = "medium"
        else:
            engagement_level = "low"

        # Determine urgency level
        if urgency_score >= 80:
            urgency_level = "critical"
        elif urgency_score >= 60:
            urgency_level = "high"
        elif urgency_score >= 40:
            urgency_level = "medium"
        else:
            urgency_level = "low"

        # Response pattern analysis
        if urgency_score >= 75:
            response_pattern = "immediate"
        elif urgency_score >= 50:
            response_pattern = "prompt"
        else:
            response_pattern = "delayed"

        return {
            "type": decision_style,
            "engagement_level": engagement_level,
            "engagement_score": engagement_score,
            "urgency_level": urgency_level,
            "urgency_score": urgency_score,
            "email_engagement": min(engagement_score * 0.7, 100),  # Estimate email engagement
            "response_pattern": response_pattern,
        }

    def _is_recent(self, timestamp_str: str) -> bool:
        """Check if timestamp is within recent period (7 days)"""
        if not timestamp_str:
            return False

        try:
            timestamp = parse_iso8601(timestamp_str)
            return (datetime.utcnow() - timestamp).days <= 7
        except Exception:
            return False


class IntentDetectorAgent(LeadIntelligenceAgent):
    """Specialized agent for purchase intent detection"""

    def __init__(self):
        super().__init__(
            AgentType.INTENT_DETECTOR,
            {
                "intent_signals": ["urgency_language", "timeline_mentions", "financing_inquiries"],
                "classification_model": "purchase_intent_v2.0",
            },
        )

    async def _perform_specialized_analysis(self, lead_data: Dict[str, Any]) -> AgentInsight:
        """Detect and analyze purchase intent signals"""
        await asyncio.sleep(0.18)  # Simulate NLP processing

        # Extract intent signals
        communications = lead_data.get("communications", [])
        form_submissions = lead_data.get("form_submissions", [])
        lead_data.get("search_queries", [])

        # Analyze language patterns
        intent_signals = self._extract_intent_signals(communications)

        # Analyze timeline indicators
        timeline_urgency = self._analyze_timeline_urgency(communications, form_submissions)

        # Assess financing readiness
        financing_readiness = self._assess_financing_readiness(communications, form_submissions)

        # Calculate overall intent score
        intent_score = self._calculate_intent_score(intent_signals, timeline_urgency, financing_readiness)

        # Classify intent level
        intent_level = self._classify_intent_level(intent_score)

        primary_finding = f"{intent_level.title()} purchase intent detected"

        supporting_evidence = [
            f"Intent signals found: {len(intent_signals)}",
            f"Timeline urgency: {timeline_urgency}",
            f"Financing readiness: {financing_readiness}",
            f"Overall intent score: {intent_score:.1f}/100",
        ]

        recommendations = []
        if intent_level == "immediate":
            recommendations.append("Schedule urgent consultation within 24 hours")
            recommendations.append("Prepare pre-approved property recommendations")
            recommendations.append("Coordinate with financing team for rapid pre-qualification")
        elif intent_level == "near_term":
            recommendations.append("Maintain weekly contact with property updates")
            recommendations.append("Provide market insights and timing guidance")
            recommendations.append("Begin pre-qualification process")
        elif intent_level == "exploratory":
            recommendations.append("Monthly market updates and property alerts")
            recommendations.append("Educational content about buying process")
            recommendations.append("Long-term relationship building")
        else:
            recommendations.append("Quarterly check-ins and market reports")
            recommendations.append("Basic property information and resources")

        risk_factors = []
        if intent_score < 25:
            risk_factors.append("Very low purchase intent - may be window shopping")
        if financing_readiness in ("planning", "unknown"):
            risk_factors.append("Financing concerns may delay purchase decision")

        urgency_level = (
            "critical" if intent_level == "immediate" else "high" if intent_level == "near_term" else "medium"
        )

        return AgentInsight(
            agent_type=self.agent_type,
            confidence=0.85,
            primary_finding=primary_finding,
            supporting_evidence=supporting_evidence,
            recommendations=recommendations,
            risk_factors=risk_factors,
            opportunity_score=intent_score,
            urgency_level=urgency_level,
            processing_time_ms=180.0,
            data_sources=["nlp_analysis", "intent_models", "timeline_analysis"],
            metadata={
                "intent_level": intent_level,
                "intent_signals": intent_signals,
                "timeline_urgency": timeline_urgency,
                "financing_readiness": financing_readiness,
            },
        )

    def _extract_intent_signals(self, communications: List) -> List[str]:
        """Extract purchase intent signals from communications"""
        # Simplified NLP-based intent detection
        # In production, this would use sophisticated NLP models

        high_intent_phrases = [
            "ready to buy",
            "looking to purchase",
            "need to move",
            "urgent",
            "pre-approved",
            "cash buyer",
            "closing date",
            "when can we close",
            "make an offer",
            "negotiate price",
            "inspection",
            "mortgage approved",
        ]

        medium_intent_phrases = [
            "seriously considering",
            "planning to buy",
            "in the market",
            "looking for a realtor",
            "mortgage pre-qualification",
            "down payment ready",
            "timeline",
            "budget range",
            "financing options",
        ]

        signals = []
        for comm in communications:
            content = comm.get("content", "").lower()

            for phrase in high_intent_phrases:
                if phrase in content:
                    signals.append(f"HIGH: {phrase}")

            for phrase in medium_intent_phrases:
                if phrase in content:
                    signals.append(f"MEDIUM: {phrase}")

        return signals

    def _analyze_timeline_urgency(self, communications: List, form_submissions: List) -> str:
        """Analyze timeline urgency from communications"""
        timeline_indicators = {
            "immediate": ["asap", "immediately", "this week", "urgent", "right away"],
            "short_term": ["next month", "within 30 days", "by end of month", "soon"],
            "medium_term": ["2-3 months", "this quarter", "spring", "summer", "fall", "winter"],
            "long_term": ["next year", "6 months", "eventually", "someday"],
        }

        all_content = " ".join(
            [comm.get("content", "") for comm in communications]
            + [form.get("message", "") for form in form_submissions]
        ).lower()

        for urgency, indicators in timeline_indicators.items():
            if any(indicator in all_content for indicator in indicators):
                return urgency

        return "unspecified"

    def _assess_financing_readiness(self, communications: List, form_submissions: List) -> str:
        """Assess financing readiness level"""
        financing_indicators = {
            "ready": ["pre-approved", "cash buyer", "financing secured", "mortgage approved"],
            "in_progress": ["applying for mortgage", "pre-qualification", "credit check", "loan application"],
            "planning": ["need financing", "mortgage options", "lender recommendations", "down payment"],
            "unknown": [],
        }

        all_content = " ".join(
            [comm.get("content", "") for comm in communications]
            + [form.get("message", "") for form in form_submissions]
        ).lower()

        for readiness, indicators in financing_indicators.items():
            if any(indicator in all_content for indicator in indicators):
                return readiness

        return "unknown"

    def _calculate_intent_score(
        self, intent_signals: List[str], timeline_urgency: str, financing_readiness: str
    ) -> float:
        """Calculate overall purchase intent score"""
        score = 0.0

        # Intent signals contribution (40% of total)
        high_signals = len([s for s in intent_signals if s.startswith("HIGH")])
        medium_signals = len([s for s in intent_signals if s.startswith("MEDIUM")])

        signal_score = min(40.0, (high_signals * 8) + (medium_signals * 4))
        score += signal_score

        # Timeline urgency contribution (35% of total)
        urgency_scores = {
            "immediate": 35.0,
            "short_term": 28.0,
            "medium_term": 18.0,
            "long_term": 8.0,
            "unspecified": 15.0,  # Medium default
        }
        score += urgency_scores.get(timeline_urgency, 15.0)

        # Financing readiness contribution (25% of total)
        financing_scores = {"ready": 25.0, "in_progress": 20.0, "planning": 12.0, "unknown": 8.0}
        score += financing_scores.get(financing_readiness, 8.0)

        return min(100.0, score)

    def _classify_intent_level(self, intent_score: float) -> str:
        """Classify intent level based on score"""
        self.knowledge_base["intent_levels"]

        if intent_score >= 80:
            return "immediate"
        elif intent_score >= 65:
            return "near_term"
        elif intent_score >= 35:
            return "exploratory"
        else:
            return "passive"


class MarketAnalystAgent(LeadIntelligenceAgent):
    """
    Specialized agent for real-time market monitoring and "Predator Mode".

    Features:
    - External MLS/Listing feed monitoring
    - "Alert Synergy": Price drop detection for swiped properties
    - Automatic defensive comparison drafting
    """

    def __init__(self):
        super().__init__(AgentType.MARKET_ANALYST, {"monitoring_active": True, "predator_mode": True})

    async def _perform_specialized_analysis(self, lead_data: Dict[str, Any]) -> AgentInsight:
        """Monitor market changes relative to lead's swiped list"""
        await asyncio.sleep(0.2)  # Simulate external feed check

        swiped_list = lead_data.get("swiped_list", [])
        market_changes = await self._check_mls_for_changes(swiped_list)

        alerts = []
        recommendations = []
        defensive_drafts = []
        opportunity_score = 50.0

        for change in market_changes:
            if change["type"] == "price_drop":
                alert_msg = f"PREDATOR ALERT: Property {change['property_id']} dropped in price by {change['amount']}%"
                alerts.append(alert_msg)

                # Push to Redis for real-time WebSocket stream
                await self._push_to_websocket_stream(change, lead_data)

                # Implement Alert Synergy
                draft = await self._draft_defensive_comparison(change, lead_data)
                defensive_drafts.append(draft)
                recommendations.append(f"Send defensive comparison for {change['property_id']}")
                opportunity_score = max(opportunity_score, 85.0)

        primary_finding = (
            f"Market Analyst: Found {len(alerts)} critical price updates for lead's interest list"
            if alerts
            else "No critical market changes detected for lead's interest list"
        )

        return AgentInsight(
            agent_type=self.agent_type,
            confidence=0.92,
            primary_finding=primary_finding,
            supporting_evidence=alerts,
            recommendations=recommendations,
            risk_factors=["Competitive market pressure" if alerts else "None"],
            opportunity_score=opportunity_score,
            urgency_level="high" if alerts else "low",
            processing_time_ms=200.0,
            data_sources=["mls_feed", "swiped_list", "market_analytics"],
            metadata={"market_alerts": alerts, "defensive_drafts": defensive_drafts},
        )

    async def _check_mls_for_changes(self, swiped_list: List[str]) -> List[Dict[str, Any]]:
        """Check for MLS changes using the simulated feed."""
        from ghl_real_estate_ai.services.simulated_mls_feed import get_simulated_mls

        mls = get_simulated_mls()
        return await mls.get_recent_changes(swiped_list)

    async def _push_to_websocket_stream(self, change: Dict[str, Any], lead_data: Dict[str, Any]):
        """Pushes a Predator Alert to the Redis-backed websocket gateway."""
        try:
            from ghl_real_estate_ai.services.realtime_config import get_aioredis_client

            redis = await get_aioredis_client()

            if redis:
                tenant_id = lead_data.get("tenant_id", "default_tenant")
                alert_payload = {
                    "type": "predator_alert",
                    "tenant_id": tenant_id,
                    "lead_id": lead_data.get("lead_id"),
                    "lead_name": f"{lead_data.get('first_name', '')} {lead_data.get('last_name', '')}".strip(),
                    "property_id": change["property_id"],
                    "old_price": change["old_price"],
                    "new_price": change["new_price"],
                    "drop_amount": change["amount"],
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Publish to tenant-specific and global alert channels
                channel = f"alerts:{tenant_id}:predator"
                await redis.publish(channel, json.dumps(alert_payload))
                await redis.publish("alerts:global:predator", json.dumps(alert_payload))

                logger.info(f"Published Predator Alert to WebSocket gateway: {channel}")
        except Exception as e:
            logger.error(f"Failed to push alert to WebSocket gateway: {e}")

    async def _draft_defensive_comparison(self, change: Dict[str, Any], lead_data: Dict[str, Any]) -> str:
        """Draft a defensive comparison message for the human agent to send"""
        # Use Claude via Orchestrator if possible, otherwise mock
        from ghl_real_estate_ai.services.claude_orchestrator import (
            ClaudeRequest,
            ClaudeTaskType,
            get_claude_orchestrator,
        )

        orchestrator = get_claude_orchestrator()

        prompt = f"""
        PREDATOR MODE: DEFENSIVE COMPARISON DRAFT
        
        Property {change["property_id"]} just dropped in price from ${change["old_price"]} to ${change["new_price"]}.
        This property is in the lead's "Swiped List" (highly interested).
        
        Lead Name: {lead_data.get("first_name", "Client")}
        
        Draft a "Defensive Comparison" SMS/Email for the human agent to send.
        Goal: Acknowledge the price drop, but highlight WHY our recommended properties are still a better value, 
        or explain how this price drop creates a negotiation opening for US.
        
        Tone: Professional, expert, strategic.
        """

        try:
            request = ClaudeRequest(
                task_type=ClaudeTaskType.SCRIPT_GENERATION, context={"task": "defensive_draft"}, prompt=prompt
            )
            response = await orchestrator.process_request(request)
            return response.content
        except Exception:
            return f"Hi {lead_data.get('first_name', 'there')}, I noticed a price drop on {change['property_id']}. Let's discuss how this affects our strategy."


class NegotiationStrategistAgent(LeadIntelligenceAgent):
    """Specialized agent for negotiation strategy and tactical behavioral response"""

    def __init__(self):
        super().__init__(
            AgentType.COMMUNICATION_OPTIMIZER,
            {
                "focus_areas": ["negotiation_drift", "persona_adaptation", "tactical_triggers"],
                "strategies": ["voss_labeling", "price_anchor_defense", "micro_commitment"],
            },
        )
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine

        self.tone_engine = JorgeToneEngine()
        from ghl_real_estate_ai.agents.voss_negotiation_agent import get_voss_negotiation_agent

        self.voss_agent = get_voss_negotiation_agent()

    async def _perform_specialized_analysis(self, lead_data: Dict[str, Any]) -> AgentInsight:
        """Analyze negotiation stance and tactical opportunities"""
        await asyncio.sleep(0.1)

        history = lead_data.get("conversation_history", [])
        drift = self.tone_engine.detect_negotiation_drift(history)

        persona = lead_data.get("persona", "unknown")

        recommendations = []
        voss_response = None

        if drift.is_softening:
            recommendations.append("Trigger ROI Proforma - flexibility detected")

            # Phase 3: Voss-Powered Closure Execution
            voss_result = await self.voss_agent.run_negotiation(
                lead_id=lead_data.get("lead_id", "N/A"),
                lead_name=lead_data.get("first_name", "there"),
                address=lead_data.get("property_address", "your property"),
                history=history,
            )
            voss_response = voss_result.get("generated_response")
            recommendations.append(f"Voss Closure: {voss_response}")

        if persona == "loss_aversion":
            recommendations.append("Switch to 'Cost of Waiting' qualification branching")
        elif persona == "investor":
            recommendations.append("Switch to 'ROI/Cap Rate' qualification branching")

        return AgentInsight(
            agent_type=self.agent_type,
            confidence=0.9,
            primary_finding=f"Negotiation stance: {'Softening' if drift.is_softening else 'Firm'}. Persona: {persona}",
            supporting_evidence=[f"Drift score: {drift.sentiment_shift}", f"Hedging count: {drift.hedging_count}"],
            recommendations=recommendations,
            risk_factors=["Price anchor mismatch"] if not drift.is_softening else [],
            opportunity_score=80.0 if drift.is_softening else 40.0,
            urgency_level="high" if drift.is_softening else "medium",
            processing_time_ms=100.0,
            data_sources=["conversation_history", "tone_engine"],
            metadata={"drift": drift.__dict__},
        )


class LeadIntelligenceSwarm:
    """Multi-agent orchestration system for comprehensive lead intelligence"""

    def __init__(self):
        self.agents: Dict[AgentType, LeadIntelligenceAgent] = {}
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.consensus_history: List[SwarmConsensus] = []

        # Performance tracking
        self.swarm_metrics = {
            "analyses_completed": 0,
            "average_consensus_confidence": 0.0,
            "average_processing_time": 0.0,
            "agent_agreement_rate": 0.0,
        }

        # Initialize specialized agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all specialized agents"""
        self.agents[AgentType.DEMOGRAPHIC_ANALYZER] = DemographicAnalyzerAgent()
        self.agents[AgentType.BEHAVIORAL_PROFILER] = BehavioralProfilerAgent()
        self.agents[AgentType.INTENT_DETECTOR] = IntentDetectorAgent()
        self.agents[AgentType.MARKET_ANALYST] = MarketAnalystAgent()
        self.agents[AgentType.COMMUNICATION_OPTIMIZER] = NegotiationStrategistAgent()

        # Additional agents would be initialized here:
        # self.agents[AgentType.FINANCIAL_ASSESSOR] = FinancialAssessorAgent()
        # self.agents[AgentType.ENGAGEMENT_SCORER] = EngagementScorerAgent()
        # self.agents[AgentType.COMMUNICATION_OPTIMIZER] = CommunicationOptimizerAgent()
        # self.agents[AgentType.TIMING_PREDICTOR] = TimingPredictorAgent()
        # self.agents[AgentType.RISK_EVALUATOR] = RiskEvaluatorAgent()
        # self.agents[AgentType.OPPORTUNITY_IDENTIFIER] = OpportunityIdentifierAgent()

        logger.info(f"Initialized {len(self.agents)} specialized intelligence agents")

    async def analyze_lead_comprehensive(self, lead_id: str, lead_data: Dict[str, Any]) -> SwarmConsensus:
        """Perform comprehensive multi-agent analysis of a lead"""
        start_time = asyncio.get_event_loop().time()

        logger.info(f"🤖 Starting comprehensive swarm analysis for lead {lead_id}")

        # Track active analysis
        self.active_analyses[lead_id] = {
            "start_time": datetime.utcnow(),
            "status": "analyzing",
            "agents_deployed": list(self.agents.keys()),
        }

        try:
            # Deploy all agents in parallel for maximum efficiency
            agent_tasks = []
            for agent_type, agent in self.agents.items():
                task = asyncio.create_task(agent.analyze_lead(lead_data), name=f"{agent_type.value}_analysis")
                agent_tasks.append(task)

            # Wait for all agents to complete analysis
            agent_insights = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # Filter out failed analyses
            valid_insights = []
            for insight in agent_insights:
                if isinstance(insight, AgentInsight):
                    valid_insights.append(insight)
                else:
                    logger.warning(f"Agent analysis failed: {insight}")

            # Build consensus from agent insights
            consensus = await self._build_consensus(lead_id, valid_insights)

            # Update tracking
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            consensus.processing_time_ms = processing_time

            self._update_swarm_metrics(consensus)
            self.consensus_history.append(consensus)

            # Clean up active analysis tracking
            self.active_analyses.pop(lead_id, None)

            logger.info(
                f"🎯 Swarm analysis complete for lead {lead_id} - "
                f"Consensus: {consensus.consensus_level.value}, "
                f"Score: {consensus.overall_score:.1f}, "
                f"Time: {processing_time:.1f}ms"
            )

            return consensus

        except Exception as e:
            logger.error(f"Swarm analysis failed for lead {lead_id}: {e}")
            self.active_analyses.pop(lead_id, None)
            raise

    async def _build_consensus(self, lead_id: str, insights: List[AgentInsight]) -> SwarmConsensus:
        """Build consensus from multiple agent insights"""
        if not insights:
            raise ValueError("No valid agent insights to build consensus from")

        # Calculate weighted scores based on agent confidence
        weighted_scores = []
        total_confidence = 0.0

        for insight in insights:
            weight = insight.confidence
            weighted_scores.append(insight.opportunity_score * weight)
            total_confidence += weight

        # Calculate consensus score
        overall_score = sum(weighted_scores) / total_confidence if total_confidence > 0 else 0.0

        # Determine consensus level based on agent agreement
        consensus_level = self._calculate_consensus_level(insights)

        # Calculate overall confidence
        avg_confidence = sum(insight.confidence for insight in insights) / len(insights)

        # Determine primary recommendation through voting
        [insight.primary_finding for insight in insights]
        primary_recommendation = self._select_primary_recommendation(insights)

        # Determine action priority
        action_priority = self._determine_action_priority(insights)

        # Identify conflicting views
        conflicting_views = self._identify_conflicts(insights)

        # Generate consensus rationale
        consensus_rationale = self._generate_consensus_rationale(insights, consensus_level)

        return SwarmConsensus(
            lead_id=lead_id,
            consensus_level=consensus_level,
            overall_score=overall_score,
            confidence=avg_confidence,
            primary_recommendation=primary_recommendation,
            action_priority=action_priority,
            agent_insights=insights,
            conflicting_views=conflicting_views,
            consensus_rationale=consensus_rationale,
            processing_time_ms=0.0,  # Set by caller
            timestamp=datetime.utcnow(),
        )

    def _calculate_consensus_level(self, insights: List[AgentInsight]) -> ConsensusLevel:
        """Calculate consensus level based on agent agreement"""
        if len(insights) < 2:
            return ConsensusLevel.HIGH

        scores = [insight.opportunity_score for insight in insights]
        avg_score = sum(scores) / len(scores)

        # Calculate variance in scores
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        std_deviation = variance**0.5

        # Calculate agreement percentage based on standard deviation
        if std_deviation <= 10:
            return ConsensusLevel.HIGH  # Scores within 10 points
        elif std_deviation <= 20:
            return ConsensusLevel.MEDIUM  # Scores within 20 points
        elif std_deviation <= 30:
            return ConsensusLevel.LOW  # Scores within 30 points
        else:
            return ConsensusLevel.CONFLICT  # High disagreement

    def _select_primary_recommendation(self, insights: List[AgentInsight]) -> str:
        """Select primary recommendation based on highest confidence agent"""
        if not insights:
            return "No recommendation available"

        # Find insight with highest confidence
        highest_confidence_insight = max(insights, key=lambda x: x.confidence)

        return highest_confidence_insight.primary_finding

    def _determine_action_priority(self, insights: List[AgentInsight]) -> str:
        """Determine action priority based on agent urgency levels"""
        urgency_levels = [insight.urgency_level for insight in insights]

        # Priority mapping
        if "critical" in urgency_levels:
            return "immediate"
        elif "high" in urgency_levels:
            return "high"
        elif "medium" in urgency_levels:
            return "medium"
        else:
            return "low"

    def _identify_conflicts(self, insights: List[AgentInsight]) -> List[Tuple[str, str]]:
        """Identify conflicting agent views"""
        conflicts = []

        # Compare opportunity scores for significant disagreements
        for i, insight1 in enumerate(insights):
            for j, insight2 in enumerate(insights[i + 1 :], i + 1):
                score_diff = abs(insight1.opportunity_score - insight2.opportunity_score)

                if score_diff > 30:  # Significant disagreement threshold
                    conflict = (
                        insight1.agent_type.value,
                        f"Score disagreement: {insight1.opportunity_score:.1f} vs {insight2.opportunity_score:.1f}",
                    )
                    conflicts.append(conflict)

        return conflicts

    def _generate_consensus_rationale(self, insights: List[AgentInsight], consensus_level: ConsensusLevel) -> str:
        """Generate explanation for consensus decision"""
        if consensus_level == ConsensusLevel.HIGH:
            return f"Strong agreement across {len(insights)} agents with consistent scoring and recommendations"
        elif consensus_level == ConsensusLevel.MEDIUM:
            return f"Moderate agreement with some variance in scoring but aligned on overall assessment"
        elif consensus_level == ConsensusLevel.LOW:
            return f"Limited agreement with noticeable differences in agent assessments"
        else:
            return f"Significant disagreement between agents - manual review recommended"

    def _update_swarm_metrics(self, consensus: SwarmConsensus):
        """Update swarm performance metrics"""
        self.swarm_metrics["analyses_completed"] += 1
        count = self.swarm_metrics["analyses_completed"]

        # Update running averages
        self.swarm_metrics["average_consensus_confidence"] = (
            self.swarm_metrics["average_consensus_confidence"] * (count - 1) + consensus.confidence
        ) / count

        self.swarm_metrics["average_processing_time"] = (
            self.swarm_metrics["average_processing_time"] * (count - 1) + consensus.processing_time_ms
        ) / count

        # Calculate agreement rate (high consensus percentage)
        high_consensus_count = sum(1 for c in self.consensus_history if c.consensus_level == ConsensusLevel.HIGH)
        self.swarm_metrics["agent_agreement_rate"] = (high_consensus_count / count) * 100

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get current swarm operational status"""
        agent_status = {}
        for agent_type, agent in self.agents.items():
            agent_status[agent_type.value] = {"status": agent.status.value, "performance": agent.performance_metrics}

        return {
            "swarm_metrics": self.swarm_metrics,
            "active_analyses": len(self.active_analyses),
            "agent_status": agent_status,
            "consensus_history_count": len(self.consensus_history),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def learn_from_outcomes(self, lead_id: str, actual_outcome: Dict[str, Any]):
        """Update all agents with actual outcome for learning"""
        # Find the consensus for this lead
        lead_consensus = None
        for consensus in self.consensus_history:
            if consensus.lead_id == lead_id:
                lead_consensus = consensus
                break

        if not lead_consensus:
            logger.warning(f"No consensus found for lead {lead_id} - cannot learn from outcome")
            return

        # Update each agent with the outcome
        learning_tasks = []
        for insight in lead_consensus.agent_insights:
            agent = self.agents.get(insight.agent_type)
            if agent:
                task = agent.learn_from_outcome(insight, actual_outcome)
                learning_tasks.append(task)

        await asyncio.gather(*learning_tasks, return_exceptions=True)

        # Phase 6: Dojo Learning - Record Winning Tactics
        if actual_outcome.get("is_conversion"):
            await self.record_winning_tactics(lead_id, lead_consensus, actual_outcome)

        logger.info(f"Swarm learned from outcome for lead {lead_id}")

    async def record_winning_tactics(self, lead_id: str, consensus: SwarmConsensus, outcome: Dict[str, Any]):
        """
        Phase 6: The Dojo.
        Reverse-analyzes a closed deal to identify exactly which agent insights
        and tactical triggers drove the 'Win'.
        """
        logger.info(f"🏆 Dojo: Recording winning tactics for deal {lead_id}")

        winning_triggers = []
        for insight in consensus.agent_insights:
            if insight.confidence > 0.8 and insight.opportunity_score > 70:
                winning_triggers.append(
                    {"agent": insight.agent_type.value, "finding": insight.primary_finding, "recommendation_used": True}
                )

        # Send to Collective Learning Engine (Mock for Phase 6)
        try:
            from ghl_real_estate_ai.intelligence.collective_learning_engine import CollectiveLearningEngine

            # In production, we'd use the DI container to get the instance
            logger.info(f"🚀 Sharing {len(winning_triggers)} winning patterns with Collective Intelligence")
        except ImportError:
            pass

    async def adjust_agent_weights(self, agent_ratings: Dict[str, float]):
        """
        Phase 6: Jorge's Dojo (RLHF).
        Allows human feedback to manually boost or nerf specific agent influence.
        Example: Jorge marks a 'Behavioral' insight as 'Weak', lowering its weight.
        """
        for agent_id, rating in agent_ratings.items():
            try:
                # Find agent by string ID
                agent_type = next((t for t in AgentType if t.value == agent_id), None)
                if agent_type and agent_type in self.agents:
                    agent = self.agents[agent_type]
                    # Adjust accuracy based on human rating (0.0 to 1.0)
                    old_accuracy = agent.performance_metrics["accuracy_score"]
                    new_accuracy = (old_accuracy * 0.7) + (rating * 0.3)
                    agent.performance_metrics["accuracy_score"] = new_accuracy
                    logger.info(
                        f"🥋 Dojo RLHF: Adjusted {agent_id} weight. Accuracy: {old_accuracy:.2f} -> {new_accuracy:.2f}"
                    )
            except Exception as e:
                logger.error(f"Failed to adjust agent weight: {e}")


# Lazy initialization to avoid circular dependencies
_lead_intelligence_swarm_instance = None


def get_lead_intelligence_swarm() -> LeadIntelligenceSwarm:
    """Get the global lead intelligence swarm instance with lazy initialization."""
    global _lead_intelligence_swarm_instance
    if _lead_intelligence_swarm_instance is None:
        _lead_intelligence_swarm_instance = LeadIntelligenceSwarm()
    return _lead_intelligence_swarm_instance


# For backwards compatibility - use the factory function
class _SwarmProxy:
    """Proxy object that delegates calls to the lazily initialized swarm."""

    def __getattr__(self, name):
        return getattr(get_lead_intelligence_swarm(), name)


lead_intelligence_swarm = _SwarmProxy()


async def main():
    """Demonstration of multi-agent lead intelligence swarm"""
    # Sample lead data for testing
    sample_lead = {
        "lead_id": "LEAD_12345",
        "age": 32,
        "location": "San Francisco, CA",
        "job_title": "Senior Software Engineer",
        "education": "Masters in Computer Science",
        "page_visits": [
            {"timestamp": "2026-01-17T10:00:00Z", "property_id": "PROP_001"},
            {"timestamp": "2026-01-17T10:15:00Z", "property_id": "PROP_002"},
            {"timestamp": "2026-01-17T10:30:00Z", "property_id": "PROP_001"},
        ],
        "email_interactions": [
            {"timestamp": "2026-01-16T15:00:00Z", "type": "opened"},
            {"timestamp": "2026-01-16T15:05:00Z", "type": "clicked"},
        ],
        "communications": [
            {"content": "I'm looking to buy a house in the next 2-3 months. I'm pre-approved for a mortgage."},
            {"content": "Can you send me information about properties in good school districts?"},
        ],
        "form_submissions": [{"message": "Interested in scheduling a viewing", "timestamp": "2026-01-17T09:00:00Z"}],
        "search_patterns": ["3 bedroom", "good schools", "commute to central_rc"],
        "response_times": [2, 4, 1.5],  # hours
    }

    try:
        logger.info("🚀 Starting Lead Intelligence Swarm Demonstration")

        # Analyze lead with multi-agent swarm
        consensus = await lead_intelligence_swarm.analyze_lead_comprehensive(sample_lead["lead_id"], sample_lead)

        # Display results
        logger.info(f"🎯 SWARM ANALYSIS RESULTS:")
        logger.info(f"   Lead ID: {consensus.lead_id}")
        logger.info(f"   Overall Score: {consensus.overall_score:.1f}/100")
        logger.info(f"   Consensus Level: {consensus.consensus_level.value}")
        logger.info(f"   Confidence: {consensus.confidence:.2f}")
        logger.info(f"   Action Priority: {consensus.action_priority}")
        logger.info(f"   Primary Recommendation: {consensus.primary_recommendation}")
        logger.info(f"   Processing Time: {consensus.processing_time_ms:.1f}ms")

        logger.info(f"\n📊 AGENT INSIGHTS:")
        for insight in consensus.agent_insights:
            logger.info(f"   {insight.agent_type.value}:")
            logger.info(f"     Score: {insight.opportunity_score:.1f}")
            logger.info(f"     Confidence: {insight.confidence:.2f}")
            logger.info(f"     Finding: {insight.primary_finding}")
            logger.info(f"     Urgency: {insight.urgency_level}")

        if consensus.conflicting_views:
            logger.info(f"\n⚠️  CONFLICTS DETECTED:")
            for agent_type, conflict in consensus.conflicting_views:
                logger.info(f"   {agent_type}: {conflict}")

        # Get swarm status
        status = await lead_intelligence_swarm.get_swarm_status()
        logger.info(f"\n📈 SWARM METRICS:")
        logger.info(f"   Analyses Completed: {status['swarm_metrics']['analyses_completed']}")
        logger.info(f"   Average Confidence: {status['swarm_metrics']['average_consensus_confidence']:.2f}")
        logger.info(f"   Average Processing Time: {status['swarm_metrics']['average_processing_time']:.1f}ms")
        logger.info(f"   Agent Agreement Rate: {status['swarm_metrics']['agent_agreement_rate']:.1f}%")

    except Exception as e:
        logger.error(f"Swarm demonstration failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
