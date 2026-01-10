"""
Territory Management Service

Comprehensive territory management system for real estate agents and teams.
Handles territory assignments, performance tracking, optimization recommendations,
and client portfolio management by territory.

Features:
- Agent territory assignment and boundary management
- Territory performance analytics and tracking
- Client portfolio management by territory
- Territory optimization recommendations
- Market coverage analysis
- Performance benchmarking across territories

Created: January 2026
Author: GHL Real Estate AI Platform
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import json

# Import market intelligence service for integration
try:
    from .market_intelligence_service import MarketArea, MarketMetrics, market_intelligence_service
except ImportError:
    # Fallback for testing
    pass

# Configure logging
logger = logging.getLogger(__name__)

class TerritoryStatus(Enum):
    """Territory assignment status."""
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    SHARED = "shared"
    CONTESTED = "contested"
    TRANSITIONING = "transitioning"

class AssignmentType(Enum):
    """Type of territory assignment."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    COLLABORATION = "collaboration"
    TEMPORARY = "temporary"
    BACKUP = "backup"

class PerformanceLevel(Enum):
    """Territory performance levels."""
    EXCELLENT = "excellent"
    ABOVE_AVERAGE = "above_average"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    NEEDS_IMPROVEMENT = "needs_improvement"

class TerritoryType(Enum):
    """Types of territory specialization."""
    RESIDENTIAL = "residential"
    LUXURY = "luxury"
    COMMERCIAL = "commercial"
    INVESTMENT = "investment"
    FIRST_TIME_BUYER = "first_time_buyer"
    MIXED_USE = "mixed_use"

@dataclass
class TerritoryBoundary:
    """Geographic boundary definition for a territory."""
    boundary_id: str
    territory_id: str
    boundary_type: str  # polygon, circle, custom
    coordinates: List[Dict[str, float]]  # lat/lng coordinates
    zip_codes: List[str]
    landmarks: List[str]
    description: str

@dataclass
class TerritoryAssignment:
    """Agent territory assignment record."""
    assignment_id: str
    agent_id: str
    territory_id: str
    assignment_type: AssignmentType
    start_date: datetime
    end_date: Optional[datetime]
    status: TerritoryStatus
    priority_level: int  # 1-5, 5 being highest
    specialization: TerritoryType
    performance_goals: Dict[str, float]
    notes: str = ""

@dataclass
class TerritoryPerformance:
    """Territory performance metrics."""
    territory_id: str
    agent_id: str
    report_period: str  # YYYY-MM format
    total_listings: int
    total_sales: int
    total_volume: float
    avg_sale_price: float
    days_on_market_avg: int
    client_satisfaction: float
    lead_conversion_rate: float
    market_share: float
    revenue_generated: float
    expenses: float
    profit_margin: float
    activity_score: float

    def calculate_performance_level(self) -> PerformanceLevel:
        """Calculate overall performance level."""
        score = 0

        # Market share analysis
        if self.market_share > 20:
            score += 2
        elif self.market_share > 15:
            score += 1
        elif self.market_share < 5:
            score -= 1

        # Conversion rate analysis
        if self.lead_conversion_rate > 25:
            score += 2
        elif self.lead_conversion_rate > 20:
            score += 1
        elif self.lead_conversion_rate < 10:
            score -= 1

        # Client satisfaction analysis
        if self.client_satisfaction > 4.5:
            score += 1
        elif self.client_satisfaction < 3.5:
            score -= 1

        # Profit margin analysis
        if self.profit_margin > 25:
            score += 1
        elif self.profit_margin < 10:
            score -= 1

        # Convert score to performance level
        if score >= 4:
            return PerformanceLevel.EXCELLENT
        elif score >= 2:
            return PerformanceLevel.ABOVE_AVERAGE
        elif score >= 0:
            return PerformanceLevel.AVERAGE
        elif score >= -2:
            return PerformanceLevel.BELOW_AVERAGE
        else:
            return PerformanceLevel.NEEDS_IMPROVEMENT

@dataclass
class Territory:
    """Territory definition and information."""
    territory_id: str
    name: str
    description: str
    territory_type: TerritoryType
    status: TerritoryStatus
    market_areas: List[str]  # MarketArea IDs
    boundaries: List[TerritoryBoundary]
    population: int
    avg_income: float
    property_density: float
    competition_level: str  # low, medium, high
    market_potential: float  # 0-100 score
    created_date: datetime
    last_updated: datetime

@dataclass
class ClientPortfolioMetrics:
    """Client portfolio metrics for a territory."""
    territory_id: str
    agent_id: str
    total_clients: int
    active_clients: int
    new_clients_30d: int
    repeat_clients: int
    referral_clients: int
    avg_client_value: float
    client_retention_rate: float
    client_acquisition_cost: float
    lifetime_value: float

@dataclass
class TerritoryOptimization:
    """Territory optimization recommendation."""
    recommendation_id: str
    territory_id: str
    agent_id: str
    optimization_type: str  # expansion, reduction, reallocation, specialization
    description: str
    expected_benefit: str
    implementation_effort: str  # low, medium, high
    confidence_score: float
    supporting_metrics: Dict[str, Any]
    recommended_actions: List[str]
    created_date: datetime

class TerritoryManagementService:
    """
    Comprehensive territory management service for real estate agents.

    Manages territory assignments, tracks performance, optimizes coverage,
    and provides insights for territory-based client portfolio management.
    """

    def __init__(self):
        self.territories: Dict[str, Territory] = {}
        self.assignments: Dict[str, TerritoryAssignment] = {}
        self.performance_data: Dict[str, List[TerritoryPerformance]] = {}
        self.boundaries: Dict[str, TerritoryBoundary] = {}
        self.client_portfolios: Dict[str, ClientPortfolioMetrics] = {}
        self.optimizations: Dict[str, TerritoryOptimization] = {}

        # Initialize with demo data
        asyncio.create_task(self._initialize_demo_data())

    async def _initialize_demo_data(self) -> None:
        """Initialize service with demo territory management data."""
        try:
            await self._create_demo_territories()
            await self._create_demo_assignments()
            await self._create_demo_performance_data()
            await self._create_demo_client_portfolios()
            await self._create_demo_optimizations()

            logger.info("Territory management service initialized with demo data")

        except Exception as e:
            logger.error(f"Error initializing demo data: {e}")

    async def _create_demo_territories(self) -> None:
        """Create demo territories."""
        demo_territories = [
            {
                "territory_id": "territory_001",
                "name": "Downtown Core",
                "description": "High-density urban area with condos and luxury properties",
                "territory_type": TerritoryType.RESIDENTIAL,
                "status": TerritoryStatus.ASSIGNED,
                "market_areas": ["area_downtown", "area_luxury"],
                "population": 85000,
                "avg_income": 125000,
                "property_density": 85.5,
                "competition_level": "high",
                "market_potential": 82.5
            },
            {
                "territory_id": "territory_002",
                "name": "Suburban Family District",
                "description": "Family-oriented suburbs with single-family homes",
                "territory_type": TerritoryType.RESIDENTIAL,
                "status": TerritoryStatus.ASSIGNED,
                "market_areas": ["area_suburbs"],
                "population": 78000,
                "avg_income": 95000,
                "property_density": 45.2,
                "competition_level": "medium",
                "market_potential": 75.8
            },
            {
                "territory_id": "territory_003",
                "name": "Luxury Hills",
                "description": "High-end luxury properties and estates",
                "territory_type": TerritoryType.LUXURY,
                "status": TerritoryStatus.ASSIGNED,
                "market_areas": ["area_luxury"],
                "population": 25000,
                "avg_income": 285000,
                "property_density": 12.8,
                "competition_level": "high",
                "market_potential": 88.3
            },
            {
                "territory_id": "territory_004",
                "name": "Emerging Markets",
                "description": "Growing neighborhoods with investment opportunities",
                "territory_type": TerritoryType.INVESTMENT,
                "status": TerritoryStatus.SHARED,
                "market_areas": ["area_emerging"],
                "population": 35000,
                "avg_income": 65000,
                "property_density": 38.7,
                "competition_level": "low",
                "market_potential": 92.1
            }
        ]

        for territory_data in demo_territories:
            # Create boundaries for each territory
            boundaries = [
                TerritoryBoundary(
                    boundary_id=f"boundary_{territory_data['territory_id']}_001",
                    territory_id=territory_data["territory_id"],
                    boundary_type="polygon",
                    coordinates=[
                        {"lat": 34.0 + i * 0.01, "lng": -118.0 - i * 0.01}
                        for i in range(4)
                    ],
                    zip_codes=["90210", "90211"],
                    landmarks=["Main Street", "City Center"],
                    description=f"Primary boundary for {territory_data['name']}"
                )
            ]

            territory = Territory(
                **territory_data,
                boundaries=boundaries,
                created_date=datetime.now() - timedelta(days=90),
                last_updated=datetime.now() - timedelta(days=5)
            )

            self.territories[territory.territory_id] = territory
            self.boundaries[boundaries[0].boundary_id] = boundaries[0]

    async def _create_demo_assignments(self) -> None:
        """Create demo territory assignments."""
        demo_assignments = [
            {
                "assignment_id": "assign_001",
                "agent_id": "agent_001",
                "territory_id": "territory_001",
                "assignment_type": AssignmentType.PRIMARY,
                "status": TerritoryStatus.ASSIGNED,
                "priority_level": 5,
                "specialization": TerritoryType.RESIDENTIAL,
                "performance_goals": {
                    "monthly_sales": 8,
                    "quarterly_revenue": 2500000,
                    "client_satisfaction": 4.5,
                    "market_share": 15.0
                }
            },
            {
                "assignment_id": "assign_002",
                "agent_id": "agent_002",
                "territory_id": "territory_002",
                "assignment_type": AssignmentType.PRIMARY,
                "status": TerritoryStatus.ASSIGNED,
                "priority_level": 4,
                "specialization": TerritoryType.RESIDENTIAL,
                "performance_goals": {
                    "monthly_sales": 12,
                    "quarterly_revenue": 3200000,
                    "client_satisfaction": 4.7,
                    "market_share": 20.0
                }
            },
            {
                "assignment_id": "assign_003",
                "agent_id": "agent_003",
                "territory_id": "territory_003",
                "assignment_type": AssignmentType.PRIMARY,
                "status": TerritoryStatus.ASSIGNED,
                "priority_level": 5,
                "specialization": TerritoryType.LUXURY,
                "performance_goals": {
                    "monthly_sales": 4,
                    "quarterly_revenue": 8500000,
                    "client_satisfaction": 4.8,
                    "market_share": 25.0
                }
            },
            {
                "assignment_id": "assign_004",
                "agent_id": "agent_001",
                "territory_id": "territory_004",
                "assignment_type": AssignmentType.SECONDARY,
                "status": TerritoryStatus.SHARED,
                "priority_level": 3,
                "specialization": TerritoryType.INVESTMENT,
                "performance_goals": {
                    "monthly_sales": 3,
                    "quarterly_revenue": 950000,
                    "client_satisfaction": 4.4,
                    "market_share": 8.0
                }
            }
        ]

        for assignment_data in demo_assignments:
            assignment = TerritoryAssignment(
                **assignment_data,
                start_date=datetime.now() - timedelta(days=60),
                end_date=None,
                notes="Demo territory assignment"
            )
            self.assignments[assignment.assignment_id] = assignment

    async def _create_demo_performance_data(self) -> None:
        """Create demo performance data for territories."""
        import random

        # Generate 6 months of performance data for each assignment
        for assignment in self.assignments.values():
            performance_list = []

            for month_offset in range(6):
                report_date = datetime.now() - timedelta(days=30 * month_offset)
                report_period = report_date.strftime("%Y-%m")

                # Generate realistic performance data based on territory type
                base_values = self._get_base_performance_values(assignment.specialization)
                variation = random.uniform(0.8, 1.2)

                performance = TerritoryPerformance(
                    territory_id=assignment.territory_id,
                    agent_id=assignment.agent_id,
                    report_period=report_period,
                    total_listings=int(base_values["listings"] * variation),
                    total_sales=int(base_values["sales"] * variation),
                    total_volume=base_values["volume"] * variation,
                    avg_sale_price=base_values["avg_price"] * variation,
                    days_on_market_avg=int(base_values["dom"] * variation),
                    client_satisfaction=min(5.0, base_values["satisfaction"] * random.uniform(0.95, 1.05)),
                    lead_conversion_rate=base_values["conversion"] * random.uniform(0.9, 1.1),
                    market_share=base_values["market_share"] * random.uniform(0.85, 1.15),
                    revenue_generated=base_values["revenue"] * variation,
                    expenses=base_values["expenses"] * random.uniform(0.9, 1.1),
                    profit_margin=base_values["profit_margin"] * random.uniform(0.9, 1.1),
                    activity_score=random.uniform(70, 95)
                )

                performance_list.append(performance)

            self.performance_data[f"{assignment.agent_id}_{assignment.territory_id}"] = performance_list

    def _get_base_performance_values(self, territory_type: TerritoryType) -> Dict[str, float]:
        """Get base performance values for different territory types."""
        base_values = {
            TerritoryType.RESIDENTIAL: {
                "listings": 15,
                "sales": 8,
                "volume": 6500000,
                "avg_price": 812500,
                "dom": 32,
                "satisfaction": 4.4,
                "conversion": 22.5,
                "market_share": 12.5,
                "revenue": 195000,
                "expenses": 45000,
                "profit_margin": 23.5
            },
            TerritoryType.LUXURY: {
                "listings": 8,
                "sales": 4,
                "volume": 14500000,
                "avg_price": 3625000,
                "dom": 68,
                "satisfaction": 4.7,
                "conversion": 28.5,
                "market_share": 18.2,
                "revenue": 435000,
                "expenses": 85000,
                "profit_margin": 28.5
            },
            TerritoryType.INVESTMENT: {
                "listings": 12,
                "sales": 6,
                "volume": 3900000,
                "avg_price": 650000,
                "dom": 25,
                "satisfaction": 4.2,
                "conversion": 19.5,
                "market_share": 8.5,
                "revenue": 117000,
                "expenses": 32000,
                "profit_margin": 21.2
            }
        }

        return base_values.get(territory_type, base_values[TerritoryType.RESIDENTIAL])

    async def _create_demo_client_portfolios(self) -> None:
        """Create demo client portfolio metrics."""
        for assignment in self.assignments.values():
            key = f"{assignment.agent_id}_{assignment.territory_id}"

            portfolio = ClientPortfolioMetrics(
                territory_id=assignment.territory_id,
                agent_id=assignment.agent_id,
                total_clients=random.randint(45, 85),
                active_clients=random.randint(15, 25),
                new_clients_30d=random.randint(3, 8),
                repeat_clients=random.randint(8, 15),
                referral_clients=random.randint(5, 12),
                avg_client_value=random.uniform(35000, 95000),
                client_retention_rate=random.uniform(75.0, 92.5),
                client_acquisition_cost=random.uniform(450, 1200),
                lifetime_value=random.uniform(85000, 245000)
            )

            self.client_portfolios[key] = portfolio

    async def _create_demo_optimizations(self) -> None:
        """Create demo territory optimization recommendations."""
        demo_optimizations = [
            {
                "recommendation_id": "opt_001",
                "territory_id": "territory_004",
                "agent_id": "agent_001",
                "optimization_type": "expansion",
                "description": "Expand territory coverage to include adjacent emerging neighborhoods",
                "expected_benefit": "25% increase in lead generation potential",
                "implementation_effort": "medium",
                "confidence_score": 0.82,
                "supporting_metrics": {
                    "market_growth_rate": 15.2,
                    "competition_density": "low",
                    "agent_capacity": "available"
                },
                "recommended_actions": [
                    "Survey additional neighborhoods for market potential",
                    "Assess agent capacity for expanded coverage",
                    "Develop marketing strategy for new areas"
                ]
            },
            {
                "recommendation_id": "opt_002",
                "territory_id": "territory_002",
                "agent_id": "agent_002",
                "optimization_type": "specialization",
                "description": "Focus on first-time buyer specialization in family districts",
                "expected_benefit": "18% increase in conversion rates",
                "implementation_effort": "low",
                "confidence_score": 0.75,
                "supporting_metrics": {
                    "first_time_buyer_percentage": 42.5,
                    "agent_skill_match": "high",
                    "market_demand": "strong"
                },
                "recommended_actions": [
                    "Develop first-time buyer educational content",
                    "Partner with mortgage brokers",
                    "Create specialized marketing campaigns"
                ]
            }
        ]

        for opt_data in demo_optimizations:
            optimization = TerritoryOptimization(
                **opt_data,
                created_date=datetime.now() - timedelta(days=random.randint(1, 14))
            )
            self.optimizations[optimization.recommendation_id] = optimization

    # Core Territory Management Methods

    async def assign_territory(
        self,
        agent_id: str,
        territory_id: str,
        assignment_type: AssignmentType = AssignmentType.PRIMARY,
        specialization: TerritoryType = TerritoryType.RESIDENTIAL,
        performance_goals: Optional[Dict[str, float]] = None,
        notes: str = ""
    ) -> TerritoryAssignment:
        """Assign a territory to an agent."""
        if territory_id not in self.territories:
            raise ValueError(f"Territory {territory_id} not found")

        assignment_id = f"assign_{len(self.assignments) + 1:03d}"

        assignment = TerritoryAssignment(
            assignment_id=assignment_id,
            agent_id=agent_id,
            territory_id=territory_id,
            assignment_type=assignment_type,
            start_date=datetime.now(),
            end_date=None,
            status=TerritoryStatus.ASSIGNED,
            priority_level=5 if assignment_type == AssignmentType.PRIMARY else 3,
            specialization=specialization,
            performance_goals=performance_goals or {},
            notes=notes
        )

        self.assignments[assignment_id] = assignment

        # Update territory status
        territory = self.territories[territory_id]
        if assignment_type == AssignmentType.PRIMARY:
            territory.status = TerritoryStatus.ASSIGNED
        else:
            territory.status = TerritoryStatus.SHARED

        territory.last_updated = datetime.now()

        logger.info(f"Assigned territory {territory_id} to agent {agent_id}")
        return assignment

    async def get_agent_territories(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all territories assigned to an agent."""
        agent_assignments = [
            a for a in self.assignments.values()
            if a.agent_id == agent_id and a.status == TerritoryStatus.ASSIGNED
        ]

        territories_data = []
        for assignment in agent_assignments:
            territory = self.territories.get(assignment.territory_id)
            if territory:
                territory_data = {
                    "assignment_id": assignment.assignment_id,
                    "territory_id": territory.territory_id,
                    "name": territory.name,
                    "description": territory.description,
                    "assignment_type": assignment.assignment_type.value,
                    "specialization": assignment.specialization.value,
                    "priority_level": assignment.priority_level,
                    "market_potential": territory.market_potential,
                    "population": territory.population,
                    "competition_level": territory.competition_level,
                    "performance_goals": assignment.performance_goals,
                    "start_date": assignment.start_date.isoformat()
                }
                territories_data.append(territory_data)

        return sorted(territories_data, key=lambda x: x["priority_level"], reverse=True)

    async def get_territory_performance(
        self,
        agent_id: str,
        territory_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """Get performance analytics for a specific territory assignment."""
        key = f"{agent_id}_{territory_id}"

        if key not in self.performance_data:
            return {"error": "No performance data found"}

        performance_history = self.performance_data[key][:months]
        territory = self.territories.get(territory_id)
        assignment = next(
            (a for a in self.assignments.values()
             if a.agent_id == agent_id and a.territory_id == territory_id),
            None
        )

        if not performance_history or not territory or not assignment:
            return {"error": "Incomplete data for analysis"}

        # Calculate trends and analytics
        recent_performance = performance_history[0]
        performance_level = recent_performance.calculate_performance_level()

        # Calculate trends
        revenue_trend = self._calculate_trend([p.revenue_generated for p in performance_history])
        sales_trend = self._calculate_trend([p.total_sales for p in performance_history])
        satisfaction_trend = self._calculate_trend([p.client_satisfaction for p in performance_history])

        # Goal achievement analysis
        goal_achievement = {}
        goals = assignment.performance_goals

        if "monthly_sales" in goals:
            goal_achievement["sales"] = {
                "goal": goals["monthly_sales"],
                "actual": recent_performance.total_sales,
                "achievement": (recent_performance.total_sales / goals["monthly_sales"]) * 100
            }

        if "client_satisfaction" in goals:
            goal_achievement["satisfaction"] = {
                "goal": goals["client_satisfaction"],
                "actual": recent_performance.client_satisfaction,
                "achievement": (recent_performance.client_satisfaction / goals["client_satisfaction"]) * 100
            }

        performance_analysis = {
            "territory_id": territory_id,
            "territory_name": territory.name,
            "agent_id": agent_id,
            "analysis_period": f"{months} months",
            "performance_level": performance_level.value,
            "current_metrics": {
                "total_sales": recent_performance.total_sales,
                "revenue_generated": recent_performance.revenue_generated,
                "market_share": recent_performance.market_share,
                "client_satisfaction": recent_performance.client_satisfaction,
                "conversion_rate": recent_performance.lead_conversion_rate,
                "profit_margin": recent_performance.profit_margin
            },
            "trends": {
                "revenue": revenue_trend,
                "sales": sales_trend,
                "satisfaction": satisfaction_trend
            },
            "goal_achievement": goal_achievement,
            "historical_data": [
                {
                    "period": p.report_period,
                    "sales": p.total_sales,
                    "revenue": p.revenue_generated,
                    "satisfaction": p.client_satisfaction
                }
                for p in performance_history
            ],
            "recommendations": self._generate_performance_recommendations(
                recent_performance, performance_level, revenue_trend
            )
        }

        return performance_analysis

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "insufficient_data"

        recent_avg = sum(values[:3]) / min(3, len(values))
        older_avg = sum(values[3:]) / max(1, len(values) - 3)

        if recent_avg > older_avg * 1.1:
            return "strong_upward"
        elif recent_avg > older_avg * 1.05:
            return "upward"
        elif recent_avg < older_avg * 0.9:
            return "strong_downward"
        elif recent_avg < older_avg * 0.95:
            return "downward"
        else:
            return "stable"

    def _generate_performance_recommendations(
        self,
        performance: TerritoryPerformance,
        level: PerformanceLevel,
        revenue_trend: str
    ) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if level in [PerformanceLevel.BELOW_AVERAGE, PerformanceLevel.NEEDS_IMPROVEMENT]:
            recommendations.append("Focus on lead generation and conversion optimization")

            if performance.client_satisfaction < 4.0:
                recommendations.append("Implement client satisfaction improvement program")

            if performance.market_share < 10:
                recommendations.append("Develop market share growth strategy")

        if revenue_trend in ["downward", "strong_downward"]:
            recommendations.append("Review pricing strategy and value proposition")
            recommendations.append("Increase marketing activities and networking")

        if performance.conversion_rate < 20:
            recommendations.append("Improve lead qualification and follow-up processes")

        if performance.days_on_market_avg > 45:
            recommendations.append("Review property pricing and marketing strategies")

        return recommendations

    async def get_territory_coverage_analysis(self) -> Dict[str, Any]:
        """Analyze overall territory coverage and gaps."""
        coverage_analysis = {
            "total_territories": len(self.territories),
            "assigned_territories": 0,
            "unassigned_territories": 0,
            "shared_territories": 0,
            "coverage_gaps": [],
            "optimization_opportunities": [],
            "agent_workload": {}
        }

        # Analyze territory status
        for territory in self.territories.values():
            if territory.status == TerritoryStatus.ASSIGNED:
                coverage_analysis["assigned_territories"] += 1
            elif territory.status == TerritoryStatus.UNASSIGNED:
                coverage_analysis["unassigned_territories"] += 1
            elif territory.status == TerritoryStatus.SHARED:
                coverage_analysis["shared_territories"] += 1

        # Analyze agent workload
        agent_territories = {}
        for assignment in self.assignments.values():
            if assignment.status == TerritoryStatus.ASSIGNED:
                agent_id = assignment.agent_id
                if agent_id not in agent_territories:
                    agent_territories[agent_id] = []
                agent_territories[agent_id].append(assignment)

        for agent_id, assignments in agent_territories.items():
            total_market_potential = sum(
                self.territories[a.territory_id].market_potential for a in assignments
            )
            primary_territories = len([a for a in assignments if a.assignment_type == AssignmentType.PRIMARY])

            coverage_analysis["agent_workload"][agent_id] = {
                "total_territories": len(assignments),
                "primary_territories": primary_territories,
                "total_market_potential": total_market_potential,
                "workload_level": self._assess_workload_level(len(assignments), total_market_potential)
            }

        # Identify coverage gaps
        unassigned_territories = [
            t for t in self.territories.values()
            if t.status == TerritoryStatus.UNASSIGNED
        ]

        for territory in unassigned_territories:
            gap = {
                "territory_id": territory.territory_id,
                "name": territory.name,
                "market_potential": territory.market_potential,
                "reason": "No assigned agent"
            }
            coverage_analysis["coverage_gaps"].append(gap)

        # Identify optimization opportunities
        optimizations = list(self.optimizations.values())
        coverage_analysis["optimization_opportunities"] = [
            {
                "territory_id": opt.territory_id,
                "type": opt.optimization_type,
                "description": opt.description,
                "confidence": opt.confidence_score
            }
            for opt in sorted(optimizations, key=lambda x: x.confidence_score, reverse=True)[:5]
        ]

        return coverage_analysis

    def _assess_workload_level(self, territory_count: int, market_potential: float) -> str:
        """Assess agent workload level based on territories and potential."""
        if territory_count > 4 or market_potential > 350:
            return "high"
        elif territory_count > 2 or market_potential > 200:
            return "medium"
        else:
            return "low"

    async def get_client_portfolio_analysis(self, agent_id: str, territory_id: str) -> Dict[str, Any]:
        """Get client portfolio analysis for a specific territory."""
        key = f"{agent_id}_{territory_id}"

        if key not in self.client_portfolios:
            return {"error": "No client portfolio data found"}

        portfolio = self.client_portfolios[key]
        territory = self.territories.get(territory_id)

        if not territory:
            return {"error": "Territory not found"}

        # Calculate portfolio metrics
        acquisition_efficiency = portfolio.avg_client_value / portfolio.client_acquisition_cost
        referral_rate = (portfolio.referral_clients / portfolio.total_clients) * 100
        repeat_rate = (portfolio.repeat_clients / portfolio.total_clients) * 100

        portfolio_analysis = {
            "territory_id": territory_id,
            "territory_name": territory.name,
            "agent_id": agent_id,
            "portfolio_metrics": {
                "total_clients": portfolio.total_clients,
                "active_clients": portfolio.active_clients,
                "new_clients_this_month": portfolio.new_clients_30d,
                "client_retention_rate": portfolio.client_retention_rate,
                "avg_client_value": portfolio.avg_client_value,
                "lifetime_value": portfolio.lifetime_value
            },
            "client_dynamics": {
                "referral_rate": referral_rate,
                "repeat_client_rate": repeat_rate,
                "acquisition_efficiency": acquisition_efficiency,
                "portfolio_health_score": self._calculate_portfolio_health_score(portfolio)
            },
            "recommendations": self._generate_portfolio_recommendations(portfolio, referral_rate, repeat_rate)
        }

        return portfolio_analysis

    def _calculate_portfolio_health_score(self, portfolio: ClientPortfolioMetrics) -> float:
        """Calculate overall portfolio health score."""
        score = 0

        # Retention rate scoring
        if portfolio.client_retention_rate > 85:
            score += 25
        elif portfolio.client_retention_rate > 75:
            score += 20
        elif portfolio.client_retention_rate > 65:
            score += 15
        else:
            score += 10

        # Acquisition efficiency scoring
        efficiency = portfolio.avg_client_value / portfolio.client_acquisition_cost
        if efficiency > 80:
            score += 25
        elif efficiency > 60:
            score += 20
        elif efficiency > 40:
            score += 15
        else:
            score += 10

        # Portfolio growth scoring
        growth_rate = (portfolio.new_clients_30d / portfolio.total_clients) * 100
        if growth_rate > 8:
            score += 25
        elif growth_rate > 5:
            score += 20
        elif growth_rate > 3:
            score += 15
        else:
            score += 10

        # Lifetime value scoring
        if portfolio.lifetime_value > 150000:
            score += 25
        elif portfolio.lifetime_value > 100000:
            score += 20
        elif portfolio.lifetime_value > 75000:
            score += 15
        else:
            score += 10

        return score  # Score out of 100

    def _generate_portfolio_recommendations(
        self,
        portfolio: ClientPortfolioMetrics,
        referral_rate: float,
        repeat_rate: float
    ) -> List[str]:
        """Generate client portfolio optimization recommendations."""
        recommendations = []

        if portfolio.client_retention_rate < 80:
            recommendations.append("Implement client retention program with regular follow-ups")

        if referral_rate < 15:
            recommendations.append("Develop referral incentive program to increase word-of-mouth marketing")

        if repeat_rate < 25:
            recommendations.append("Create long-term relationship strategy for repeat business opportunities")

        if portfolio.client_acquisition_cost > 1000:
            recommendations.append("Optimize marketing spend and lead generation efficiency")

        if portfolio.new_clients_30d < 3:
            recommendations.append("Increase prospecting activities and market presence")

        return recommendations

    # Query and Analytics Methods

    async def get_territory_comparison(self, territory_ids: List[str]) -> Dict[str, Any]:
        """Compare performance across multiple territories."""
        comparison = {
            "territories": [],
            "comparative_analysis": {},
            "recommendations": []
        }

        territories_data = []
        for territory_id in territory_ids:
            if territory_id in self.territories:
                territory = self.territories[territory_id]

                # Get current performance data
                current_performance = None
                for key, performance_list in self.performance_data.items():
                    if territory_id in key and performance_list:
                        current_performance = performance_list[0]
                        break

                if current_performance:
                    territory_data = {
                        "territory_id": territory_id,
                        "name": territory.name,
                        "type": territory.territory_type.value,
                        "market_potential": territory.market_potential,
                        "performance_metrics": {
                            "revenue": current_performance.revenue_generated,
                            "sales": current_performance.total_sales,
                            "market_share": current_performance.market_share,
                            "satisfaction": current_performance.client_satisfaction,
                            "profit_margin": current_performance.profit_margin
                        }
                    }
                    territories_data.append(territory_data)

        comparison["territories"] = territories_data

        if territories_data:
            # Comparative analysis
            revenues = [t["performance_metrics"]["revenue"] for t in territories_data]
            market_shares = [t["performance_metrics"]["market_share"] for t in territories_data]

            comparison["comparative_analysis"] = {
                "top_revenue_territory": max(territories_data, key=lambda x: x["performance_metrics"]["revenue"])["name"],
                "highest_market_share": max(territories_data, key=lambda x: x["performance_metrics"]["market_share"])["name"],
                "revenue_variance": max(revenues) - min(revenues),
                "market_share_variance": max(market_shares) - min(market_shares),
                "avg_satisfaction": sum(t["performance_metrics"]["satisfaction"] for t in territories_data) / len(territories_data)
            }

        return comparison

    async def generate_territory_optimizations(self, agent_id: str) -> List[TerritoryOptimization]:
        """Generate territory optimization recommendations for an agent."""
        agent_territories = await self.get_agent_territories(agent_id)
        optimizations = []

        for territory_data in agent_territories:
            territory_id = territory_data["territory_id"]

            # Check for existing optimizations
            existing_opts = [
                opt for opt in self.optimizations.values()
                if opt.agent_id == agent_id and opt.territory_id == territory_id
            ]

            if existing_opts:
                optimizations.extend(existing_opts)
                continue

            # Generate new optimization recommendations
            territory = self.territories[territory_id]

            # Check for expansion opportunities
            if territory.market_potential > 80 and territory.competition_level == "low":
                opt = TerritoryOptimization(
                    recommendation_id=f"opt_{len(self.optimizations) + 1:03d}",
                    territory_id=territory_id,
                    agent_id=agent_id,
                    optimization_type="expansion",
                    description=f"Expand coverage in {territory.name} due to high market potential",
                    expected_benefit="20-30% increase in lead generation",
                    implementation_effort="medium",
                    confidence_score=0.78,
                    supporting_metrics={
                        "market_potential": territory.market_potential,
                        "competition_level": territory.competition_level
                    },
                    recommended_actions=[
                        "Increase marketing activities in the area",
                        "Develop local partnerships",
                        "Enhance market presence"
                    ],
                    created_date=datetime.now()
                )
                optimizations.append(opt)
                self.optimizations[opt.recommendation_id] = opt

        return sorted(optimizations, key=lambda x: x.confidence_score, reverse=True)

    async def get_all_territories(self) -> List[Territory]:
        """Get all available territories."""
        return list(self.territories.values())

    async def get_territory_details(self, territory_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific territory."""
        if territory_id not in self.territories:
            return None

        territory = self.territories[territory_id]

        # Get current assignment
        current_assignment = next(
            (a for a in self.assignments.values()
             if a.territory_id == territory_id and a.status == TerritoryStatus.ASSIGNED),
            None
        )

        territory_details = {
            "territory_id": territory.territory_id,
            "name": territory.name,
            "description": territory.description,
            "territory_type": territory.territory_type.value,
            "status": territory.status.value,
            "market_areas": territory.market_areas,
            "population": territory.population,
            "avg_income": territory.avg_income,
            "property_density": territory.property_density,
            "competition_level": territory.competition_level,
            "market_potential": territory.market_potential,
            "created_date": territory.created_date.isoformat(),
            "last_updated": territory.last_updated.isoformat(),
            "current_assignment": {
                "agent_id": current_assignment.agent_id,
                "assignment_type": current_assignment.assignment_type.value,
                "start_date": current_assignment.start_date.isoformat()
            } if current_assignment else None,
            "boundaries": [
                {
                    "boundary_id": b.boundary_id,
                    "boundary_type": b.boundary_type,
                    "zip_codes": b.zip_codes,
                    "description": b.description
                }
                for b in territory.boundaries
            ]
        }

        return territory_details

# Global service instance
territory_management_service = TerritoryManagementService()

# Helper functions for easy access
async def get_agent_territories(agent_id: str) -> List[Dict[str, Any]]:
    """Helper function to get agent territories."""
    return await territory_management_service.get_agent_territories(agent_id)

async def get_territory_performance(agent_id: str, territory_id: str) -> Dict[str, Any]:
    """Helper function to get territory performance."""
    return await territory_management_service.get_territory_performance(agent_id, territory_id)

async def get_territory_coverage_analysis() -> Dict[str, Any]:
    """Helper function to get coverage analysis."""
    return await territory_management_service.get_territory_coverage_analysis()

async def generate_territory_optimizations(agent_id: str) -> List[TerritoryOptimization]:
    """Helper function to generate optimizations."""
    return await territory_management_service.generate_territory_optimizations(agent_id)

if __name__ == "__main__":
    # Test the service
    async def test_service():
        service = TerritoryManagementService()
        await asyncio.sleep(1)  # Wait for demo data

        # Test territory retrieval
        territories = await service.get_agent_territories("agent_001")
        print(f"Agent 001 Territories: {len(territories)}")

        # Test performance analysis
        performance = await service.get_territory_performance("agent_001", "territory_001")
        print(f"Performance Level: {performance.get('performance_level', 'Unknown')}")

        # Test coverage analysis
        coverage = await service.get_territory_coverage_analysis()
        print(f"Coverage Analysis: {coverage['assigned_territories']} assigned territories")

    asyncio.run(test_service())