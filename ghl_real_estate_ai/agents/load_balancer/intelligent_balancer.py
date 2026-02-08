"""
Jorge's Real Estate AI Platform - Intelligent Load Balancer
Optimal client distribution across agent network for maximum efficiency

This module provides:
- Intelligent client-agent matching and assignment
- Dynamic workload balancing across agent network
- Performance-based agent selection optimization
- Real-time capacity management and scaling
- Jorge's commission optimization through optimal assignments
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from ...ghl_utils.jorge_config import JorgeConfig
from ...services.cache_service import CacheService
from ...services.claude_assistant import ClaudeAssistant
from ..multi_agent.agent_coordinator import AgentAssignment, AgentRole, BaseAgent, ClientPriority, ClientRequest

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategy types"""

    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Prioritize success rate
    CAPACITY_OPTIMIZED = "capacity_optimized"  # Maximize agent utilization
    COMMISSION_OPTIMIZED = "commission_optimized"  # Optimize for revenue
    SPEED_OPTIMIZED = "speed_optimized"  # Minimize response time
    SATISFACTION_OPTIMIZED = "satisfaction_optimized"  # Maximize client satisfaction


class AssignmentFactor(Enum):
    """Factors considered in agent assignment"""

    EXPERTISE_MATCH = "expertise_match"  # Skill alignment with needs
    PERFORMANCE_HISTORY = "performance_history"  # Past success rate
    CURRENT_WORKLOAD = "current_workload"  # Capacity utilization
    CLIENT_PREFERENCE = "client_preference"  # Client-agent compatibility
    GEOGRAPHIC_ALIGNMENT = "geographic_alignment"  # Location match
    COMMISSION_POTENTIAL = "commission_potential"  # Revenue optimization
    RESPONSE_TIME = "response_time"  # Speed capability
    SPECIALIZATION_DEPTH = "specialization_depth"  # Deep expertise level


@dataclass
class AgentScore:
    """Agent scoring for assignment optimization"""

    agent_id: str
    total_score: float
    factor_scores: Dict[AssignmentFactor, float]
    confidence: float
    reasoning: str
    estimated_success_probability: float
    estimated_response_time: float
    capacity_impact: float


@dataclass
class LoadBalancingDecision:
    """Load balancing decision with rationale"""

    decision_id: str
    client_request: ClientRequest
    selected_agent: str
    alternative_agents: List[str]
    assignment_reasoning: str
    expected_outcomes: Dict[str, Any]
    risk_factors: List[str]
    success_probability: float
    decision_timestamp: datetime


@dataclass
class CapacityProjection:
    """Agent capacity projection and forecasting"""

    agent_id: str
    current_utilization: float
    projected_utilization: Dict[str, float]  # timeframe -> utilization
    capacity_trends: List[Dict[str, Any]]
    bottleneck_risk: float
    scaling_recommendations: List[str]


@dataclass
class PerformanceMetrics:
    """Agent performance metrics for balancing decisions"""

    agent_id: str
    success_rate: float
    average_response_time: float
    client_satisfaction: float
    commission_per_transaction: float
    transaction_velocity: float  # transactions per time period
    expertise_ratings: Dict[str, float]
    reliability_score: float


class IntelligentLoadBalancer:
    """
    Intelligent load balancer for Jorge's agent empire
    Optimizes client distribution for maximum success and efficiency
    """

    def __init__(self):
        self.config = JorgeConfig()
        self.claude = ClaudeAssistant()
        self.cache = CacheService()

        # Load balancing configuration
        self.balancing_strategy = LoadBalancingStrategy.COMMISSION_OPTIMIZED
        self.assignment_factors = self._initialize_assignment_factors()
        self.performance_weights = self._initialize_performance_weights()

        # Agent tracking and metrics
        self.agent_performance: Dict[str, PerformanceMetrics] = {}
        self.capacity_projections: Dict[str, CapacityProjection] = {}
        self.assignment_history: List[LoadBalancingDecision] = []

        # Optimization parameters
        self.rebalancing_threshold = 0.15  # 15% capacity imbalance triggers rebalancing
        self.performance_learning_window = timedelta(days=30)  # 30-day learning window
        self.prediction_horizon = timedelta(hours=24)  # 24-hour capacity prediction

        # Jorge-specific optimization
        self.jorge_optimization_criteria = {
            "min_success_rate": 0.95,  # 95% minimum success rate
            "commission_weight": 0.30,  # 30% weight on commission potential
            "speed_weight": 0.25,  # 25% weight on response speed
            "satisfaction_weight": 0.25,  # 25% weight on client satisfaction
            "expertise_weight": 0.20,  # 20% weight on expertise match
        }

    async def initialize(self):
        """Initialize intelligent load balancer"""
        try:
            logger.info("Initializing Intelligent Load Balancer")

            # Load historical performance data
            await self._load_performance_history()

            # Initialize capacity projections
            await self._initialize_capacity_projections()

            # Start performance monitoring
            asyncio.create_task(self._performance_monitoring_loop())

            # Start capacity forecasting
            asyncio.create_task(self._capacity_forecasting_loop())

            logger.info("Intelligent Load Balancer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Intelligent Load Balancer: {str(e)}")
            raise

    async def assign_optimal_agent(
        self,
        client_request: ClientRequest,
        available_agents: List[BaseAgent],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> LoadBalancingDecision:
        """
        Assign optimal agent using intelligent balancing algorithms

        Args:
            client_request: Client service request
            available_agents: List of available agents
            constraints: Optional assignment constraints

        Returns:
            LoadBalancingDecision: Optimal assignment decision with rationale
        """
        try:
            logger.info(f"Assigning optimal agent for request: {client_request.request_id}")

            # Score all available agents
            agent_scores = await self._score_agents_for_request(client_request, available_agents)

            # Apply constraints if specified
            if constraints:
                agent_scores = await self._apply_assignment_constraints(agent_scores, constraints)

            if not agent_scores:
                raise ValueError("No suitable agents available after applying constraints")

            # Select optimal agent
            optimal_assignment = await self._select_optimal_assignment(client_request, agent_scores)

            # Create load balancing decision
            decision = LoadBalancingDecision(
                decision_id=f"balance_{client_request.request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                client_request=client_request,
                selected_agent=optimal_assignment["agent_id"],
                alternative_agents=optimal_assignment.get("alternatives", []),
                assignment_reasoning=optimal_assignment["reasoning"],
                expected_outcomes=optimal_assignment["expected_outcomes"],
                risk_factors=optimal_assignment.get("risk_factors", []),
                success_probability=optimal_assignment["success_probability"],
                decision_timestamp=datetime.now(),
            )

            # Update capacity projections
            await self._update_capacity_projections(decision)

            # Store decision for learning
            self.assignment_history.append(decision)

            # Learn from assignment patterns
            await self._learn_from_assignment_decision(decision)

            logger.info(f"Optimal assignment decision made: {decision.decision_id}")
            return decision

        except Exception as e:
            logger.error(f"Optimal agent assignment failed: {str(e)}")
            raise

    async def rebalance_workload(
        self, performance_data: Dict[str, Any], rebalancing_strategy: Optional[LoadBalancingStrategy] = None
    ) -> Dict[str, Any]:
        """
        Dynamically rebalance workload across agent network

        Args:
            performance_data: Current performance metrics
            rebalancing_strategy: Optional strategy override

        Returns:
            Dict containing rebalancing results and actions
        """
        try:
            logger.info("Starting intelligent workload rebalancing")

            strategy = rebalancing_strategy or self.balancing_strategy

            rebalancing_result = {
                "strategy": strategy.value,
                "analysis": {},
                "rebalancing_actions": [],
                "expected_improvements": {},
                "implementation_timeline": {},
                "success": True,
            }

            # Analyze current workload distribution
            workload_analysis = await self._analyze_workload_distribution(performance_data)
            rebalancing_result["analysis"] = workload_analysis

            # Identify rebalancing opportunities
            if workload_analysis["imbalance_score"] > self.rebalancing_threshold:
                rebalancing_opportunities = await self._identify_rebalancing_opportunities(workload_analysis, strategy)

                # Generate rebalancing actions
                for opportunity in rebalancing_opportunities:
                    actions = await self._generate_rebalancing_actions(opportunity)
                    rebalancing_result["rebalancing_actions"].extend(actions)

                # Calculate expected improvements
                rebalancing_result["expected_improvements"] = await self._calculate_rebalancing_impact(
                    rebalancing_result["rebalancing_actions"]
                )

                # Create implementation timeline
                rebalancing_result["implementation_timeline"] = await self._create_rebalancing_timeline(
                    rebalancing_result["rebalancing_actions"]
                )

                # Execute rebalancing actions
                execution_results = await self._execute_rebalancing_actions(rebalancing_result["rebalancing_actions"])
                rebalancing_result["execution_results"] = execution_results

            else:
                logger.info("No rebalancing required - workload distribution is optimal")
                rebalancing_result["rebalancing_actions"] = []
                rebalancing_result["message"] = "Workload distribution is already optimal"

            logger.info(f"Workload rebalancing completed - {len(rebalancing_result['rebalancing_actions'])} actions")
            return rebalancing_result

        except Exception as e:
            logger.error(f"Workload rebalancing failed: {str(e)}")
            raise

    async def predict_capacity_needs(
        self, forecast_horizon: timedelta, scenario_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict future capacity needs using predictive analytics

        Args:
            forecast_horizon: Time horizon for prediction
            scenario_data: Optional scenario data for what-if analysis

        Returns:
            Dict containing capacity predictions and recommendations
        """
        try:
            logger.info(f"Predicting capacity needs for {forecast_horizon}")

            capacity_prediction = {
                "forecast_horizon": forecast_horizon.total_seconds(),
                "predictions": {},
                "bottleneck_risks": [],
                "scaling_recommendations": [],
                "confidence_interval": {},
            }

            # Analyze historical capacity patterns
            historical_patterns = await self._analyze_historical_capacity_patterns()

            # Generate capacity predictions for each agent
            for agent_id in self.agent_performance.keys():
                agent_prediction = await self._predict_agent_capacity(
                    agent_id, forecast_horizon, historical_patterns, scenario_data
                )
                capacity_prediction["predictions"][agent_id] = agent_prediction

                # Identify potential bottlenecks
                if agent_prediction["predicted_utilization"] > 0.90:
                    bottleneck_risk = {
                        "agent_id": agent_id,
                        "risk_level": "high" if agent_prediction["predicted_utilization"] > 0.95 else "medium",
                        "predicted_utilization": agent_prediction["predicted_utilization"],
                        "time_to_bottleneck": agent_prediction.get("time_to_bottleneck"),
                        "impact_assessment": agent_prediction.get("impact_assessment", {}),
                    }
                    capacity_prediction["bottleneck_risks"].append(bottleneck_risk)

            # Generate scaling recommendations
            capacity_prediction["scaling_recommendations"] = await self._generate_scaling_recommendations(
                capacity_prediction["predictions"], capacity_prediction["bottleneck_risks"]
            )

            # Calculate confidence intervals
            capacity_prediction["confidence_interval"] = await self._calculate_prediction_confidence(
                capacity_prediction["predictions"]
            )

            logger.info(
                f"Capacity prediction completed - {len(capacity_prediction['bottleneck_risks'])} risks identified"
            )
            return capacity_prediction

        except Exception as e:
            logger.error(f"Capacity prediction failed: {str(e)}")
            raise

    async def optimize_for_jorge_metrics(self, optimization_goals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize load balancing specifically for Jorge's business metrics

        Args:
            optimization_goals: Jorge-specific optimization targets

        Returns:
            Dict containing optimization results and recommendations
        """
        try:
            logger.info("Optimizing load balancing for Jorge's metrics")

            optimization_result = {
                "optimization_id": f"jorge_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "goals": optimization_goals,
                "current_performance": {},
                "optimization_opportunities": [],
                "recommended_adjustments": [],
                "expected_roi": 0.0,
                "implementation_plan": {},
            }

            # Analyze current performance against Jorge's metrics
            current_performance = await self._analyze_jorge_performance_metrics()
            optimization_result["current_performance"] = current_performance

            # Identify optimization opportunities
            opportunities = await self._identify_jorge_optimization_opportunities(
                current_performance, optimization_goals
            )
            optimization_result["optimization_opportunities"] = opportunities

            # Generate specific recommendations
            for opportunity in opportunities:
                recommendations = await self._generate_jorge_recommendations(opportunity)
                optimization_result["recommended_adjustments"].extend(recommendations)

            # Calculate expected ROI
            optimization_result["expected_roi"] = await self._calculate_jorge_optimization_roi(
                optimization_result["recommended_adjustments"]
            )

            # Create implementation plan
            optimization_result["implementation_plan"] = await self._create_jorge_implementation_plan(
                optimization_result["recommended_adjustments"]
            )

            logger.info(f"Jorge optimization completed - Expected ROI: {optimization_result['expected_roi']:.2f}%")
            return optimization_result

        except Exception as e:
            logger.error(f"Jorge metrics optimization failed: {str(e)}")
            raise

    async def _score_agents_for_request(self, request: ClientRequest, agents: List[BaseAgent]) -> List[AgentScore]:
        """Score agents for optimal assignment to request"""
        try:
            agent_scores = []

            for agent in agents:
                # Calculate factor scores
                factor_scores = {}

                # Expertise match (specialized knowledge alignment)
                factor_scores[AssignmentFactor.EXPERTISE_MATCH] = await self._calculate_expertise_match(agent, request)

                # Performance history (success rate and quality)
                factor_scores[AssignmentFactor.PERFORMANCE_HISTORY] = await self._calculate_performance_score(
                    agent, request
                )

                # Current workload (capacity availability)
                factor_scores[AssignmentFactor.CURRENT_WORKLOAD] = await self._calculate_workload_score(agent, request)

                # Client preference (compatibility factors)
                factor_scores[AssignmentFactor.CLIENT_PREFERENCE] = await self._calculate_preference_score(
                    agent, request
                )

                # Geographic alignment (location/market match)
                factor_scores[AssignmentFactor.GEOGRAPHIC_ALIGNMENT] = await self._calculate_geographic_score(
                    agent, request
                )

                # Commission potential (revenue optimization)
                factor_scores[AssignmentFactor.COMMISSION_POTENTIAL] = await self._calculate_commission_score(
                    agent, request
                )

                # Calculate weighted total score
                total_score = await self._calculate_weighted_total_score(factor_scores)

                # Generate assignment reasoning
                reasoning = await self._generate_assignment_reasoning(agent, request, factor_scores)

                # Estimate success probability
                success_probability = await self._estimate_success_probability(agent, request, factor_scores)

                agent_score = AgentScore(
                    agent_id=agent.agent_id,
                    total_score=total_score,
                    factor_scores=factor_scores,
                    confidence=min(total_score / 100, 1.0),
                    reasoning=reasoning,
                    estimated_success_probability=success_probability,
                    estimated_response_time=await self._estimate_response_time(agent, request),
                    capacity_impact=await self._estimate_capacity_impact(agent, request),
                )

                agent_scores.append(agent_score)

            # Sort by total score
            agent_scores.sort(key=lambda x: x.total_score, reverse=True)

            return agent_scores

        except Exception as e:
            logger.error(f"Agent scoring failed: {str(e)}")
            raise

    async def _calculate_weighted_total_score(self, factor_scores: Dict[AssignmentFactor, float]) -> float:
        """Calculate weighted total score based on Jorge's optimization criteria"""
        try:
            # Jorge's factor weights based on business priorities
            weights = {
                AssignmentFactor.EXPERTISE_MATCH: self.jorge_optimization_criteria["expertise_weight"],
                AssignmentFactor.PERFORMANCE_HISTORY: self.jorge_optimization_criteria["expertise_weight"],
                AssignmentFactor.CURRENT_WORKLOAD: 0.15,
                AssignmentFactor.CLIENT_PREFERENCE: self.jorge_optimization_criteria["satisfaction_weight"],
                AssignmentFactor.GEOGRAPHIC_ALIGNMENT: 0.10,
                AssignmentFactor.COMMISSION_POTENTIAL: self.jorge_optimization_criteria["commission_weight"],
                AssignmentFactor.RESPONSE_TIME: self.jorge_optimization_criteria["speed_weight"],
                AssignmentFactor.SPECIALIZATION_DEPTH: 0.15,
            }

            total_score = 0.0
            total_weight = 0.0

            for factor, score in factor_scores.items():
                weight = weights.get(factor, 0.1)
                total_score += score * weight
                total_weight += weight

            # Normalize score
            if total_weight > 0:
                return min(total_score / total_weight, 100.0)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Weighted score calculation failed: {str(e)}")
            return 0.0

    async def _performance_monitoring_loop(self):
        """Background performance monitoring for load balancing optimization"""
        try:
            while True:
                # Wait 10 minutes between monitoring cycles
                await asyncio.sleep(600)

                try:
                    # Update performance metrics
                    await self._update_performance_metrics()

                    # Check for rebalancing needs
                    await self._check_rebalancing_needs()

                except Exception as e:
                    logger.error(f"Performance monitoring error: {str(e)}")

        except asyncio.CancelledError:
            logger.info("Performance monitoring loop cancelled")

    async def _capacity_forecasting_loop(self):
        """Background capacity forecasting for proactive scaling"""
        try:
            while True:
                # Wait 30 minutes between forecasting cycles
                await asyncio.sleep(1800)

                try:
                    # Update capacity projections
                    await self._update_all_capacity_projections()

                    # Check for scaling needs
                    await self._check_scaling_needs()

                except Exception as e:
                    logger.error(f"Capacity forecasting error: {str(e)}")

        except asyncio.CancelledError:
            logger.info("Capacity forecasting loop cancelled")

    def _initialize_assignment_factors(self) -> Dict[AssignmentFactor, float]:
        """Initialize assignment factor weights"""
        return {
            AssignmentFactor.EXPERTISE_MATCH: 0.25,
            AssignmentFactor.PERFORMANCE_HISTORY: 0.20,
            AssignmentFactor.CURRENT_WORKLOAD: 0.15,
            AssignmentFactor.CLIENT_PREFERENCE: 0.15,
            AssignmentFactor.GEOGRAPHIC_ALIGNMENT: 0.10,
            AssignmentFactor.COMMISSION_POTENTIAL: 0.10,
            AssignmentFactor.RESPONSE_TIME: 0.05,
        }

    def _initialize_performance_weights(self) -> Dict[str, float]:
        """Initialize performance metric weights"""
        return {"success_rate": 0.35, "response_time": 0.25, "client_satisfaction": 0.20, "commission_rate": 0.20}

    async def cleanup(self):
        """Clean up load balancer resources"""
        try:
            # Save performance data and learning models
            await self._save_performance_data()

            logger.info("Intelligent Load Balancer cleanup completed")

        except Exception as e:
            logger.error(f"Load Balancer cleanup failed: {str(e)}")

    # Additional helper methods would be implemented here...
