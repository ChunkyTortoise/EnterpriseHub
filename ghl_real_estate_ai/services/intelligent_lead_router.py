#!/usr/bin/env python3
"""
🧭 Intelligent Lead Router
==========================

Advanced lead routing system that optimally matches leads with agents
based on multi-criteria optimization including agent performance,
specialization, capacity, and lead characteristics.

Features:
- Multi-criteria agent matching
- Real-time agent capacity monitoring
- Specialization-based routing
- Performance-optimized assignments
- Load balancing algorithms
- SLA-based priority routing
- A/B testing for routing strategies

Optimization Criteria:
- Agent specialization match (market segment, price range)
- Historical performance with similar leads
- Current workload and capacity
- Response time patterns
- Conversion rates
- Client satisfaction scores
- Geographic expertise

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

import asyncio
import json
import math
import random
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class RoutingStrategy(Enum):
    """Routing strategy types"""

    ROUND_ROBIN = "round_robin"
    PERFORMANCE_BASED = "performance_based"
    SPECIALIZATION_MATCH = "specialization_match"
    CAPACITY_OPTIMIZED = "capacity_optimized"
    HYBRID_INTELLIGENT = "hybrid_intelligent"


class AgentStatus(Enum):
    """Agent availability status"""

    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    VACATION = "vacation"
    TRAINING = "training"


class PriorityLevel(Enum):
    """Lead priority levels"""

    CRITICAL = "critical"  # <15 min response
    HIGH = "high"  # <1 hour response
    MEDIUM = "medium"  # <4 hours response
    LOW = "low"  # <24 hours response
    NURTURE = "nurture"  # No SLA


@dataclass
class Agent:
    """Agent profile and performance data"""

    agent_id: str
    name: str
    email: str
    phone: str

    # Status and availability
    status: AgentStatus
    current_capacity: int  # Number of active leads
    max_capacity: int
    last_activity: datetime

    # Specializations
    market_specializations: List[str] = field(default_factory=list)
    price_range_min: int = 0
    price_range_max: int = 10000000
    geographic_areas: List[str] = field(default_factory=list)
    client_types: List[str] = field(default_factory=list)  # first_time, investor, luxury

    # Performance metrics (last 90 days)
    leads_assigned: int = 0
    leads_converted: int = 0
    avg_response_time_minutes: float = 120.0
    client_satisfaction_score: float = 4.0  # 1-5 scale
    avg_days_to_close: int = 45
    total_sales_volume: float = 0.0

    # Availability patterns
    typical_work_hours: Dict[str, List[int]] = field(default_factory=dict)  # day -> [start_hour, end_hour]
    timezone: str = "UTC"
    preferred_communication: List[str] = field(default_factory=lambda: ["email", "phone"])

    # Quality metrics
    follow_up_rate: float = 0.95  # % of leads properly followed up
    lead_qualification_accuracy: float = 0.85
    pipeline_velocity: float = 1.0  # leads/week moved through stages


@dataclass
class RoutingRecommendation:
    """Lead routing recommendation"""

    lead_id: str
    recommended_agent_id: str
    agent_name: str
    routing_strategy: RoutingStrategy
    match_score: float  # 0-100
    confidence: float  # 0-1

    # Reasoning
    primary_reason: str
    match_factors: Dict[str, float]
    expected_response_time_minutes: int
    expected_conversion_probability: float

    # Alternative options
    backup_agents: List[str] = field(default_factory=list)

    # Metadata
    routing_timestamp: datetime = field(default_factory=datetime.now)
    sla_target: str = "24_hours"


class AgentCapacityManager:
    """Manages agent capacity and workload"""

    def __init__(self):
        self.cache = get_cache_service()

    async def get_agent_capacity(self, agent_id: str) -> Dict[str, Any]:
        """Get current agent capacity info"""
        # In production, this would query the CRM system
        cache_key = f"agent_capacity:{agent_id}"
        cached = await self.cache.get(cache_key)

        if cached:
            return cached

        # Mock capacity data - replace with actual CRM integration
        mock_capacity = {
            "current_leads": random.randint(5, 25),
            "max_capacity": 30,
            "availability_percentage": random.uniform(0.4, 1.0),
            "last_lead_assignment": datetime.now() - timedelta(hours=random.randint(1, 12)),
            "response_time_today": random.uniform(15, 180),  # minutes
        }

        await self.cache.set(cache_key, mock_capacity, 300)  # Cache for 5 minutes
        return mock_capacity

    async def update_agent_capacity(self, agent_id: str, new_lead_assigned: bool = True):
        """Update agent capacity after assignment"""
        cache_key = f"agent_capacity:{agent_id}"
        capacity = await self.get_agent_capacity(agent_id)

        if new_lead_assigned:
            capacity["current_leads"] += 1
            capacity["last_lead_assignment"] = datetime.now()

        await self.cache.set(cache_key, capacity, 300)


class PerformanceAnalyzer:
    """Analyzes agent performance for routing decisions"""

    def __init__(self):
        self.cache = get_cache_service()

    async def get_agent_performance(self, agent_id: str) -> Dict[str, float]:
        """Get agent performance metrics"""
        cache_key = f"agent_performance:{agent_id}"
        cached = await self.cache.get(cache_key)

        if cached:
            return cached

        # Mock performance data - replace with actual analytics
        mock_performance = {
            "conversion_rate": random.uniform(0.15, 0.45),
            "avg_response_time": random.uniform(30, 300),  # minutes
            "client_satisfaction": random.uniform(3.5, 5.0),
            "follow_up_rate": random.uniform(0.7, 0.98),
            "deal_velocity": random.uniform(0.5, 2.0),  # deals/month
            "lead_quality_score": random.uniform(0.6, 0.95),
        }

        await self.cache.set(cache_key, mock_performance, 1800)  # Cache for 30 minutes
        return mock_performance

    def calculate_performance_score(self, agent: Agent, lead_characteristics: Dict[str, Any]) -> float:
        """Calculate performance-based match score"""
        score = 0.0

        # Conversion rate (40% weight)
        if agent.leads_assigned > 0:
            conversion_rate = agent.leads_converted / agent.leads_assigned
            score += conversion_rate * 40

        # Response time (25% weight)
        # Normalize response time: <30min=25pts, >4hr=0pts
        response_score = max(0, 25 - (agent.avg_response_time_minutes / 240) * 25)
        score += response_score

        # Client satisfaction (20% weight)
        satisfaction_score = (agent.client_satisfaction_score / 5.0) * 20
        score += satisfaction_score

        # Follow-up consistency (15% weight)
        followup_score = agent.follow_up_rate * 15
        score += followup_score

        return min(score, 100.0)


class SpecializationMatcher:
    """Matches agents based on specialization and expertise"""

    def calculate_specialization_score(
        self, agent: Agent, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate specialization match score with detailed breakdown"""
        factors = {}
        total_score = 0.0

        # Market segment match
        lead_budget = lead_data.get("budget", 0)
        if agent.price_range_min <= lead_budget <= agent.price_range_max:
            factors["price_range_match"] = 20.0
            total_score += 20.0
        else:
            # Partial credit for close ranges
            distance = min(abs(lead_budget - agent.price_range_min), abs(lead_budget - agent.price_range_max))
            range_width = agent.price_range_max - agent.price_range_min
            if range_width > 0:
                proximity = max(0, 1 - (distance / range_width))
                factors["price_range_match"] = proximity * 15.0
                total_score += proximity * 15.0

        # Geographic expertise
        lead_location = lead_data.get("location", "").lower()
        geographic_match = 0.0
        for area in agent.geographic_areas:
            if area.lower() in lead_location or lead_location in area.lower():
                geographic_match = 20.0
                break
        factors["geographic_expertise"] = geographic_match
        total_score += geographic_match

        # Client type specialization
        client_type_score = 0.0
        if behavioral_signals.get("first_time_buyer", 0) > 0.5 and "first_time" in agent.client_types:
            client_type_score += 15.0
        if behavioral_signals.get("investment_mindset", 0) > 0.5 and "investor" in agent.client_types:
            client_type_score += 15.0
        if lead_budget > 1000000 and "luxury" in agent.client_types:
            client_type_score += 15.0

        factors["client_type_specialization"] = client_type_score
        total_score += client_type_score

        # Market segment expertise
        market_match = 0.0
        lead_text = str(lead_data).lower()
        for specialization in agent.market_specializations:
            if specialization.lower() in lead_text:
                market_match = 15.0
                break

        factors["market_specialization"] = market_match
        total_score += market_match

        # Communication preference alignment
        comm_match = 0.0
        if behavioral_signals.get("prefers_text_communication", 0.5) > 0.6:
            if "text" in agent.preferred_communication:
                comm_match = 10.0
        else:
            if "phone" in agent.preferred_communication:
                comm_match = 10.0

        factors["communication_alignment"] = comm_match
        total_score += comm_match

        return min(total_score, 100.0), factors


class IntelligentLeadRouter:
    """
    Main intelligent lead routing system with multi-criteria optimization
    """

    def __init__(self):
        self.capacity_manager = AgentCapacityManager()
        self.performance_analyzer = PerformanceAnalyzer()
        self.specialization_matcher = SpecializationMatcher()
        self.cache = get_cache_service()

        # Initialize mock agents for demonstration
        self.agents = self._initialize_mock_agents()

        # Routing configuration
        self.default_strategy = RoutingStrategy.HYBRID_INTELLIGENT
        self.max_backup_agents = 3

        logger.info(f"IntelligentLeadRouter initialized with {len(self.agents)} agents")

    async def recommend_routing(
        self,
        lead_id: str,
        lead_score: float,
        behavioral_signals: Dict[str, float],
        lead_data: Dict[str, Any],
        strategy: Optional[RoutingStrategy] = None,
    ) -> Dict[str, Any]:
        """
        Generate intelligent routing recommendation

        Args:
            lead_id: Unique lead identifier
            lead_score: Lead scoring result (0-100)
            behavioral_signals: Behavioral analysis results
            lead_data: Lead information and preferences
            strategy: Routing strategy to use

        Returns:
            Routing recommendation with agent assignment and reasoning
        """
        try:
            routing_strategy = strategy or self.default_strategy

            # Determine priority based on lead score
            priority = self._determine_priority(lead_score, behavioral_signals)

            # Get available agents
            available_agents = await self._get_available_agents(priority)

            if not available_agents:
                return self._create_fallback_recommendation(lead_id, "No agents available")

            # Route based on strategy
            if routing_strategy == RoutingStrategy.HYBRID_INTELLIGENT:
                recommendation = await self._hybrid_intelligent_routing(
                    lead_id, lead_score, behavioral_signals, lead_data, available_agents, priority
                )
            elif routing_strategy == RoutingStrategy.PERFORMANCE_BASED:
                recommendation = await self._performance_based_routing(
                    lead_id, lead_score, behavioral_signals, lead_data, available_agents, priority
                )
            elif routing_strategy == RoutingStrategy.SPECIALIZATION_MATCH:
                recommendation = await self._specialization_routing(
                    lead_id, lead_score, behavioral_signals, lead_data, available_agents, priority
                )
            else:
                recommendation = await self._round_robin_routing(lead_id, available_agents, priority)

            # Update agent capacity
            if recommendation and recommendation.recommended_agent_id != "auto_assign":
                await self.capacity_manager.update_agent_capacity(
                    recommendation.recommended_agent_id, new_lead_assigned=True
                )

            return self._format_routing_response(recommendation)

        except Exception as e:
            logger.error(f"Lead routing failed for {lead_id}: {e}")
            return self._create_fallback_recommendation(lead_id, f"Routing error: {str(e)}")

    async def _hybrid_intelligent_routing(
        self,
        lead_id: str,
        lead_score: float,
        behavioral_signals: Dict[str, float],
        lead_data: Dict[str, Any],
        available_agents: List[Agent],
        priority: PriorityLevel,
    ) -> RoutingRecommendation:
        """Hybrid intelligent routing combining multiple criteria"""

        agent_scores = []

        for agent in available_agents:
            # Calculate component scores
            performance_score = self.performance_analyzer.calculate_performance_score(agent, lead_data)

            specialization_score, spec_factors = self.specialization_matcher.calculate_specialization_score(
                agent, lead_data, behavioral_signals
            )

            # Capacity score (prefer agents with lower current load)
            capacity_info = await self.capacity_manager.get_agent_capacity(agent.agent_id)
            load_ratio = capacity_info["current_leads"] / agent.max_capacity
            capacity_score = (1.0 - load_ratio) * 100

            # Response time prediction based on current load and historical patterns
            base_response = agent.avg_response_time_minutes
            load_multiplier = 1 + (load_ratio * 0.5)  # Up to 50% increase under full load
            predicted_response_time = base_response * load_multiplier

            # Composite scoring with dynamic weights based on priority
            if priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]:
                # Prioritize performance and capacity for urgent leads
                composite_score = performance_score * 0.4 + capacity_score * 0.35 + specialization_score * 0.25
            else:
                # Prioritize specialization for non-urgent leads
                composite_score = specialization_score * 0.4 + performance_score * 0.35 + capacity_score * 0.25

            # Calculate expected conversion probability
            base_conversion = agent.leads_converted / max(agent.leads_assigned, 1)
            # Boost for specialization match
            spec_boost = (specialization_score / 100) * 0.1
            expected_conversion = min(base_conversion + spec_boost, 0.8)

            agent_scores.append(
                {
                    "agent": agent,
                    "composite_score": composite_score,
                    "performance_score": performance_score,
                    "specialization_score": specialization_score,
                    "capacity_score": capacity_score,
                    "predicted_response_time": predicted_response_time,
                    "expected_conversion": expected_conversion,
                    "match_factors": spec_factors,
                }
            )

        # Sort by composite score
        agent_scores.sort(key=lambda x: x["composite_score"], reverse=True)

        # Select best agent
        best_match = agent_scores[0]
        backup_agents = [score["agent"].agent_id for score in agent_scores[1 : self.max_backup_agents + 1]]

        # Determine SLA target based on priority
        sla_targets = {
            PriorityLevel.CRITICAL: "15_minutes",
            PriorityLevel.HIGH: "1_hour",
            PriorityLevel.MEDIUM: "4_hours",
            PriorityLevel.LOW: "24_hours",
            PriorityLevel.NURTURE: "no_sla",
        }

        return RoutingRecommendation(
            lead_id=lead_id,
            recommended_agent_id=best_match["agent"].agent_id,
            agent_name=best_match["agent"].name,
            routing_strategy=RoutingStrategy.HYBRID_INTELLIGENT,
            match_score=best_match["composite_score"],
            confidence=self._calculate_confidence(best_match, agent_scores),
            primary_reason=self._determine_primary_reason(best_match),
            match_factors=best_match["match_factors"],
            expected_response_time_minutes=int(best_match["predicted_response_time"]),
            expected_conversion_probability=best_match["expected_conversion"],
            backup_agents=backup_agents,
            sla_target=sla_targets.get(priority, "24_hours"),
        )

    async def _performance_based_routing(
        self,
        lead_id: str,
        lead_score: float,
        behavioral_signals: Dict[str, float],
        lead_data: Dict[str, Any],
        available_agents: List[Agent],
        priority: PriorityLevel,
    ) -> RoutingRecommendation:
        """Route based purely on agent performance metrics"""

        performance_scores = []
        for agent in available_agents:
            score = self.performance_analyzer.calculate_performance_score(agent, lead_data)
            performance_scores.append((agent, score))

        # Sort by performance score
        performance_scores.sort(key=lambda x: x[1], reverse=True)
        best_agent, best_score = performance_scores[0]

        return RoutingRecommendation(
            lead_id=lead_id,
            recommended_agent_id=best_agent.agent_id,
            agent_name=best_agent.name,
            routing_strategy=RoutingStrategy.PERFORMANCE_BASED,
            match_score=best_score,
            confidence=0.8,
            primary_reason=f"Top performer with {best_agent.leads_converted}/{best_agent.leads_assigned} conversion rate",
            match_factors={"performance_score": best_score},
            expected_response_time_minutes=int(best_agent.avg_response_time_minutes),
            expected_conversion_probability=best_agent.leads_converted / max(best_agent.leads_assigned, 1),
            backup_agents=[agent.agent_id for agent, _ in performance_scores[1:3]],
            sla_target="4_hours",
        )

    async def _specialization_routing(
        self,
        lead_id: str,
        lead_score: float,
        behavioral_signals: Dict[str, float],
        lead_data: Dict[str, Any],
        available_agents: List[Agent],
        priority: PriorityLevel,
    ) -> RoutingRecommendation:
        """Route based on agent specialization match"""

        specialization_scores = []
        for agent in available_agents:
            score, factors = self.specialization_matcher.calculate_specialization_score(
                agent, lead_data, behavioral_signals
            )
            specialization_scores.append((agent, score, factors))

        # Sort by specialization score
        specialization_scores.sort(key=lambda x: x[1], reverse=True)
        best_agent, best_score, best_factors = specialization_scores[0]

        return RoutingRecommendation(
            lead_id=lead_id,
            recommended_agent_id=best_agent.agent_id,
            agent_name=best_agent.name,
            routing_strategy=RoutingStrategy.SPECIALIZATION_MATCH,
            match_score=best_score,
            confidence=0.75,
            primary_reason="Best specialization match for lead characteristics",
            match_factors=best_factors,
            expected_response_time_minutes=int(best_agent.avg_response_time_minutes),
            expected_conversion_probability=best_agent.leads_converted / max(best_agent.leads_assigned, 1),
            backup_agents=[agent.agent_id for agent, _, _ in specialization_scores[1:3]],
            sla_target="2_hours",
        )

    async def _round_robin_routing(
        self, lead_id: str, available_agents: List[Agent], priority: PriorityLevel
    ) -> RoutingRecommendation:
        """Simple round-robin routing"""

        # Select agent with lowest current load
        agent_loads = []
        for agent in available_agents:
            capacity_info = await self.capacity_manager.get_agent_capacity(agent.agent_id)
            load_ratio = capacity_info["current_leads"] / agent.max_capacity
            agent_loads.append((agent, load_ratio))

        agent_loads.sort(key=lambda x: x[1])
        selected_agent = agent_loads[0][0]

        return RoutingRecommendation(
            lead_id=lead_id,
            recommended_agent_id=selected_agent.agent_id,
            agent_name=selected_agent.name,
            routing_strategy=RoutingStrategy.ROUND_ROBIN,
            match_score=50.0,
            confidence=0.6,
            primary_reason="Round-robin assignment to agent with lowest current load",
            match_factors={"load_balancing": 50.0},
            expected_response_time_minutes=int(selected_agent.avg_response_time_minutes),
            expected_conversion_probability=0.25,
            backup_agents=[agent.agent_id for agent, _ in agent_loads[1:3]],
            sla_target="4_hours",
        )

    async def _get_available_agents(self, priority: PriorityLevel) -> List[Agent]:
        """Get list of available agents for assignment"""
        available = []

        for agent in self.agents:
            if agent.status != AgentStatus.AVAILABLE:
                continue

            # Check capacity
            capacity_info = await self.capacity_manager.get_agent_capacity(agent.agent_id)
            if capacity_info["current_leads"] >= agent.max_capacity:
                continue

            # For critical priority, only use agents who are currently online
            if priority == PriorityLevel.CRITICAL:
                time_since_activity = datetime.now() - agent.last_activity
                if time_since_activity.total_seconds() > 1800:  # 30 minutes
                    continue

            available.append(agent)

        return available

    def _determine_priority(self, lead_score: float, behavioral_signals: Dict[str, float]) -> PriorityLevel:
        """Determine lead priority based on score and signals"""

        # Critical priority indicators
        if (
            lead_score >= 90
            or behavioral_signals.get("immediate_timeline", 0) > 0.8
            or behavioral_signals.get("cash_buyer_indicators", 0) > 0.5
        ):
            return PriorityLevel.CRITICAL

        # High priority
        if (
            lead_score >= 75
            or behavioral_signals.get("preapproval_mentions", 0) > 0.5
            or behavioral_signals.get("viewing_urgency", 0) > 0.6
        ):
            return PriorityLevel.HIGH

        # Medium priority
        if lead_score >= 50:
            return PriorityLevel.MEDIUM

        # Low priority
        if lead_score >= 30:
            return PriorityLevel.LOW

        # Nurture
        return PriorityLevel.NURTURE

    def _calculate_confidence(self, best_match: Dict[str, Any], all_matches: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the routing recommendation"""

        if len(all_matches) < 2:
            return 0.7

        # Confidence based on score gap between best and second best
        score_gap = best_match["composite_score"] - all_matches[1]["composite_score"]

        # Normalize gap (0-20 point gap -> 0.7-0.95 confidence)
        confidence = 0.7 + min(score_gap / 20.0 * 0.25, 0.25)

        return confidence

    def _determine_primary_reason(self, best_match: Dict[str, Any]) -> str:
        """Determine primary reason for agent selection"""

        performance = best_match["performance_score"]
        specialization = best_match["specialization_score"]
        capacity = best_match["capacity_score"]

        if specialization > 80:
            return "Excellent specialization match for this lead type"
        elif performance > 85:
            return "Top-performing agent with proven results"
        elif capacity > 80 and performance > 60:
            return "Available agent with strong performance"
        else:
            return "Best overall match based on multiple factors"

    def _create_fallback_recommendation(self, lead_id: str, reason: str) -> Dict[str, Any]:
        """Create fallback recommendation when routing fails"""
        return {
            "recommended_agent": "auto_assign",
            "agent_name": "Auto Assignment",
            "routing_strategy": "fallback",
            "match_score": 0.0,
            "confidence": 0.3,
            "primary_reason": reason,
            "expected_response_time": "4_hours",
            "backup_agents": [],
            "sla_target": "24_hours",
        }

    def _format_routing_response(self, recommendation: RoutingRecommendation) -> Dict[str, Any]:
        """Format routing recommendation as API response"""
        return {
            "recommended_agent": recommendation.recommended_agent_id,
            "agent_name": recommendation.agent_name,
            "routing_strategy": recommendation.routing_strategy.value,
            "match_score": recommendation.match_score,
            "confidence": recommendation.confidence,
            "primary_reason": recommendation.primary_reason,
            "match_factors": recommendation.match_factors,
            "expected_response_time": f"{recommendation.expected_response_time_minutes}_minutes",
            "expected_conversion_probability": recommendation.expected_conversion_probability,
            "backup_agents": recommendation.backup_agents,
            "sla_target": recommendation.sla_target,
            "routing_timestamp": recommendation.routing_timestamp.isoformat(),
        }

    def _initialize_mock_agents(self) -> List[Agent]:
        """Initialize mock agents for demonstration"""
        return [
            Agent(
                agent_id="agent_001",
                name="Sarah Mitchell",
                email="sarah.mitchell@example.com",
                phone="(555) 123-4567",
                status=AgentStatus.AVAILABLE,
                current_capacity=12,
                max_capacity=25,
                last_activity=datetime.now() - timedelta(minutes=15),
                market_specializations=["tech_hub", "luxury"],
                price_range_min=500000,
                price_range_max=2000000,
                geographic_areas=["Austin", "Round Rock", "Cedar Park"],
                client_types=["tech_professional", "luxury"],
                leads_assigned=45,
                leads_converted=18,
                avg_response_time_minutes=25.0,
                client_satisfaction_score=4.8,
                avg_days_to_close=32,
                total_sales_volume=2450000.0,
                preferred_communication=["email", "text"],
            ),
            Agent(
                agent_id="agent_002",
                name="Michael Rodriguez",
                email="michael.rodriguez@example.com",
                phone="(555) 234-5678",
                status=AgentStatus.AVAILABLE,
                current_capacity=8,
                max_capacity=20,
                last_activity=datetime.now() - timedelta(minutes=5),
                market_specializations=["first_time_buyers", "investment"],
                price_range_min=200000,
                price_range_max=800000,
                geographic_areas=["Houston", "Spring", "Woodlands"],
                client_types=["first_time", "investor"],
                leads_assigned=38,
                leads_converted=16,
                avg_response_time_minutes=45.0,
                client_satisfaction_score=4.6,
                avg_days_to_close=28,
                total_sales_volume=1800000.0,
                preferred_communication=["phone", "email"],
            ),
            Agent(
                agent_id="agent_003",
                name="Jennifer Wong",
                email="jennifer.wong@example.com",
                phone="(555) 345-6789",
                status=AgentStatus.AVAILABLE,
                current_capacity=15,
                max_capacity=30,
                last_activity=datetime.now() - timedelta(minutes=2),
                market_specializations=["military", "va_loans"],
                price_range_min=150000,
                price_range_max=600000,
                geographic_areas=["San Antonio", "Killeen", "Fort Hood"],
                client_types=["military", "veteran"],
                leads_assigned=52,
                leads_converted=28,
                avg_response_time_minutes=18.0,
                client_satisfaction_score=4.9,
                avg_days_to_close=21,
                total_sales_volume=1950000.0,
                preferred_communication=["phone", "email", "text"],
            ),
        ]


# Example usage
if __name__ == "__main__":

    async def demo():
        router = IntelligentLeadRouter()

        # Sample lead routing
        recommendation = await router.recommend_routing(
            lead_id="lead_123",
            lead_score=85.0,
            behavioral_signals={
                "immediate_timeline": 0.8,
                "tech_company_association": 0.9,
                "preapproval_mentions": 1.0,
                "digital_engagement": 0.9,
            },
            lead_data={
                "budget": 750000,
                "location": "Austin, TX",
                "messages": [{"text": "Software engineer at Apple, need home ASAP for relocation"}],
            },
        )

        print("Intelligent Lead Routing Recommendation:")
        print(f"Agent: {recommendation['agent_name']}")
        print(f"Match Score: {recommendation['match_score']:.1f}")
        print(f"Confidence: {recommendation['confidence']:.2f}")
        print(f"Reason: {recommendation['primary_reason']}")
        print(f"Expected Response: {recommendation['expected_response_time']}")

    asyncio.run(demo())
