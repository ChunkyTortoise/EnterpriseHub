"""
Smart Lead Routing & Assignment
AI automatically assigns leads to best-fit agents

Feature 14: Smart Lead Routing & Assignment
ML-powered lead routing based on expertise, performance, and lead characteristics.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class RoutingStrategy(Enum):
    """Lead routing strategies"""

    PERFORMANCE_BASED = "performance_based"
    EXPERTISE_MATCH = "expertise_match"
    ROUND_ROBIN = "round_robin"
    WORKLOAD_BALANCED = "workload_balanced"
    AI_OPTIMIZED = "ai_optimized"


@dataclass
class Agent:
    """Agent profile"""

    agent_id: str
    name: str
    email: str
    specializations: List[str]
    languages: List[str]
    performance_metrics: Dict[str, float]
    current_workload: int = 0
    max_capacity: int = 20
    availability_hours: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    seniority_level: str = "mid"  # junior, mid, senior


@dataclass
class LeadProfile:
    """Lead profile for routing decisions"""

    lead_id: str
    name: str
    budget_range: str
    property_type: str
    location_preference: str
    urgency: str
    complexity: str
    language: str
    source: str
    lead_score: float


class SmartLeadRoutingService:
    """Service for intelligent lead routing"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.assignments: Dict[str, str] = {}  # lead_id -> agent_id
        self.assignment_history: List[Dict] = []
        self.performance_data: Dict[str, Dict] = {}
        self._initialize_demo_agents()

    def _initialize_demo_agents(self):
        """Initialize demo agents"""

        agents_data = [
            {
                "agent_id": "agent_001",
                "name": "Mike Reynolds",
                "email": "mike@example.com",
                "specializations": ["residential", "first_time_buyers"],
                "languages": ["english"],
                "performance_metrics": {
                    "close_rate": 0.35,
                    "avg_response_time_minutes": 15,
                    "customer_satisfaction": 4.8,
                    "avg_deal_size": 450000,
                },
                "seniority_level": "senior",
            },
            {
                "agent_id": "agent_002",
                "name": "Sarah Chen",
                "email": "sarah@example.com",
                "specializations": ["luxury", "investment"],
                "languages": ["english", "mandarin"],
                "performance_metrics": {
                    "close_rate": 0.42,
                    "avg_response_time_minutes": 10,
                    "customer_satisfaction": 4.9,
                    "avg_deal_size": 850000,
                },
                "seniority_level": "senior",
            },
            {
                "agent_id": "agent_003",
                "name": "Carlos Martinez",
                "email": "carlos@example.com",
                "specializations": ["residential", "commercial"],
                "languages": ["english", "spanish"],
                "performance_metrics": {
                    "close_rate": 0.28,
                    "avg_response_time_minutes": 20,
                    "customer_satisfaction": 4.6,
                    "avg_deal_size": 380000,
                },
                "seniority_level": "mid",
            },
            {
                "agent_id": "agent_004",
                "name": "Emily Taylor",
                "email": "emily@example.com",
                "specializations": ["first_time_buyers", "condos"],
                "languages": ["english"],
                "performance_metrics": {
                    "close_rate": 0.22,
                    "avg_response_time_minutes": 25,
                    "customer_satisfaction": 4.7,
                    "avg_deal_size": 320000,
                },
                "seniority_level": "junior",
            },
        ]

        for data in agents_data:
            agent = Agent(**data)
            self.add_agent(agent)

    def add_agent(self, agent: Agent):
        """Add an agent to the routing pool"""
        self.agents[agent.agent_id] = agent

    def route_lead(
        self, lead: LeadProfile, strategy: str = RoutingStrategy.AI_OPTIMIZED.value
    ) -> Optional[Agent]:
        """Route a lead to the best agent"""

        if strategy == RoutingStrategy.AI_OPTIMIZED.value:
            return self._ai_optimized_routing(lead)
        elif strategy == RoutingStrategy.EXPERTISE_MATCH.value:
            return self._expertise_based_routing(lead)
        elif strategy == RoutingStrategy.PERFORMANCE_BASED.value:
            return self._performance_based_routing(lead)
        elif strategy == RoutingStrategy.WORKLOAD_BALANCED.value:
            return self._workload_balanced_routing(lead)
        elif strategy == RoutingStrategy.ROUND_ROBIN.value:
            return self._round_robin_routing(lead)
        else:
            return None

    def _ai_optimized_routing(self, lead: LeadProfile) -> Optional[Agent]:
        """AI-optimized routing considering multiple factors"""

        available_agents = [
            agent
            for agent in self.agents.values()
            if agent.current_workload < agent.max_capacity
        ]

        if not available_agents:
            return None

        # Score each agent for this lead
        agent_scores = []

        for agent in available_agents:
            score = self._calculate_agent_score(agent, lead)
            agent_scores.append((agent, score))

        # Sort by score and return best match
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        best_agent = agent_scores[0][0]

        # Record assignment
        self._record_assignment(lead, best_agent, agent_scores[0][1])

        return best_agent

    def _calculate_agent_score(self, agent: Agent, lead: LeadProfile) -> float:
        """Calculate how well an agent matches a lead"""

        score = 0.0

        # Factor 1: Expertise match (30%)
        expertise_score = self._score_expertise(agent, lead)
        score += expertise_score * 0.30

        # Factor 2: Performance (25%)
        performance_score = agent.performance_metrics.get("close_rate", 0.2)
        score += performance_score * 0.25

        # Factor 3: Lead complexity vs agent experience (20%)
        complexity_score = self._score_complexity_match(agent, lead)
        score += complexity_score * 0.20

        # Factor 4: Workload balance (15%)
        workload_score = 1 - (agent.current_workload / agent.max_capacity)
        score += workload_score * 0.15

        # Factor 5: Language match (10%)
        language_score = 1.0 if lead.language in agent.languages else 0.5
        score += language_score * 0.10

        return score

    def _score_expertise(self, agent: Agent, lead: LeadProfile) -> float:
        """Score expertise match"""

        # Check property type specialization
        if lead.property_type in agent.specializations:
            return 1.0

        # Check if it's residential and agent has general expertise
        if (
            lead.property_type == "residential"
            and "residential" in agent.specializations
        ):
            return 0.8

        return 0.5

    def _score_complexity_match(self, agent: Agent, lead: LeadProfile) -> float:
        """Match lead complexity to agent experience"""

        complexity_to_score = {
            "simple": {"junior": 1.0, "mid": 0.8, "senior": 0.6},
            "moderate": {"junior": 0.6, "mid": 1.0, "senior": 0.8},
            "complex": {"junior": 0.3, "mid": 0.7, "senior": 1.0},
        }

        return complexity_to_score.get(lead.complexity, {}).get(
            agent.seniority_level, 0.5
        )

    def _expertise_based_routing(self, lead: LeadProfile) -> Optional[Agent]:
        """Route based on expertise match only"""

        matching_agents = [
            agent
            for agent in self.agents.values()
            if lead.property_type in agent.specializations
            and agent.current_workload < agent.max_capacity
        ]

        if not matching_agents:
            return self._round_robin_routing(lead)

        # Return agent with best performance
        matching_agents.sort(
            key=lambda a: a.performance_metrics.get("close_rate", 0), reverse=True
        )
        return matching_agents[0]

    def _performance_based_routing(self, lead: LeadProfile) -> Optional[Agent]:
        """Route to highest performing available agent"""

        available_agents = [
            agent
            for agent in self.agents.values()
            if agent.current_workload < agent.max_capacity
        ]

        if not available_agents:
            return None

        available_agents.sort(
            key=lambda a: a.performance_metrics.get("close_rate", 0), reverse=True
        )
        return available_agents[0]

    def _workload_balanced_routing(self, lead: LeadProfile) -> Optional[Agent]:
        """Route to agent with lowest workload"""

        available_agents = [
            agent
            for agent in self.agents.values()
            if agent.current_workload < agent.max_capacity
        ]

        if not available_agents:
            return None

        available_agents.sort(key=lambda a: a.current_workload)
        return available_agents[0]

    def _round_robin_routing(self, lead: LeadProfile) -> Optional[Agent]:
        """Simple round-robin assignment"""

        available_agents = [
            agent
            for agent in self.agents.values()
            if agent.current_workload < agent.max_capacity
        ]

        if not available_agents:
            return None

        # Get agent with least recent assignment
        agent_last_assigned = {
            agent.agent_id: max(
                [
                    a["timestamp"]
                    for a in self.assignment_history
                    if a["agent_id"] == agent.agent_id
                ],
                default=datetime.min.isoformat(),
            )
            for agent in available_agents
        }

        return min(available_agents, key=lambda a: agent_last_assigned[a.agent_id])

    def _record_assignment(self, lead: LeadProfile, agent: Agent, score: float):
        """Record a lead assignment"""

        self.assignments[lead.lead_id] = agent.agent_id
        agent.current_workload += 1

        assignment = {
            "timestamp": datetime.utcnow().isoformat(),
            "lead_id": lead.lead_id,
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "match_score": score,
            "lead_score": lead.lead_score,
            "property_type": lead.property_type,
        }

        self.assignment_history.append(assignment)

    def get_agent_workload(self, agent_id: str) -> Dict:
        """Get workload info for an agent"""

        agent = self.agents.get(agent_id)
        if not agent:
            return {}

        assigned_leads = [
            lead_id for lead_id, aid in self.assignments.items() if aid == agent_id
        ]

        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "current_workload": agent.current_workload,
            "max_capacity": agent.max_capacity,
            "utilization": f"{(agent.current_workload / agent.max_capacity * 100):.1f}%",
            "assigned_leads": len(assigned_leads),
        }

    def get_routing_analytics(self) -> Dict:
        """Get analytics on routing performance"""

        if not self.assignment_history:
            return {"total_assignments": 0}

        total = len(self.assignment_history)
        avg_score = sum(a["match_score"] for a in self.assignment_history) / total

        # Assignments by agent
        agent_counts = {}
        for assignment in self.assignment_history:
            agent_id = assignment["agent_id"]
            agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1

        return {
            "total_assignments": total,
            "avg_match_score": f"{avg_score:.2f}",
            "assignments_by_agent": agent_counts,
            "most_utilized_agent": max(agent_counts, key=agent_counts.get),
            "least_utilized_agent": min(agent_counts, key=agent_counts.get),
        }

    def predict_best_agent(self, lead: LeadProfile) -> Dict:
        """Predict best agent with explanation"""

        agent = self._ai_optimized_routing(lead)

        if not agent:
            return {"success": False, "reason": "No available agents"}

        score = self._calculate_agent_score(agent, lead)

        # Generate explanation
        reasons = []

        if lead.property_type in agent.specializations:
            reasons.append(f"Specializes in {lead.property_type}")

        if agent.performance_metrics["close_rate"] > 0.35:
            reasons.append(
                f"High close rate ({agent.performance_metrics['close_rate']:.0%})"
            )

        if lead.language in agent.languages:
            reasons.append(f"Speaks {lead.language}")

        if agent.seniority_level == "senior" and lead.complexity == "complex":
            reasons.append("Senior agent for complex lead")

        return {
            "success": True,
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "match_score": f"{score:.2f}",
            "confidence": "high" if score > 0.8 else "medium" if score > 0.6 else "low",
            "reasons": reasons,
            "expected_close_rate": f"{agent.performance_metrics['close_rate']:.0%}",
        }


def demo_smart_routing():
    """Demonstrate smart lead routing"""
    service = SmartLeadRoutingService()

    print("🎯 Smart Lead Routing & Assignment Demo\n")

    # Create test leads
    test_leads = [
        LeadProfile(
            lead_id="lead_001",
            name="John Smith",
            budget_range="$300K-$500K",
            property_type="residential",
            location_preference="suburbs",
            urgency="high",
            complexity="simple",
            language="english",
            source="website",
            lead_score=75,
        ),
        LeadProfile(
            lead_id="lead_002",
            name="Wei Zhang",
            budget_range="$800K-$1.2M",
            property_type="luxury",
            location_preference="downtown",
            urgency="medium",
            complexity="complex",
            language="mandarin",
            source="referral",
            lead_score=92,
        ),
        LeadProfile(
            lead_id="lead_003",
            name="Maria Garcia",
            budget_range="$250K-$350K",
            property_type="residential",
            location_preference="city",
            urgency="low",
            complexity="moderate",
            language="spanish",
            source="social_media",
            lead_score=58,
        ),
    ]

    # Route each lead
    for lead in test_leads:
        print(f"📋 Lead: {lead.name}")
        print(f"   Type: {lead.property_type} | Budget: {lead.budget_range}")
        print(f"   Score: {lead.lead_score} | Complexity: {lead.complexity}")

        prediction = service.predict_best_agent(lead)

        if prediction["success"]:
            print(f"   ✅ Assigned to: {prediction['agent_name']}")
            print(f"   Match score: {prediction['match_score']}")
            print(f"   Reasons: {', '.join(prediction['reasons'])}")
        print()

    # Show analytics
    analytics = service.get_routing_analytics()
    print(f"📊 Routing Analytics:")
    print(f"   Total assignments: {analytics['total_assignments']}")
    print(f"   Avg match score: {analytics['avg_match_score']}")
    print(f"   Most utilized: {analytics['most_utilized_agent']}")


if __name__ == "__main__":
    demo_smart_routing()
