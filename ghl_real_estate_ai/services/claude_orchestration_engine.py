"""
Multi-Claude Orchestration Engine - Phase 4: Advanced Claude Intelligence

This service coordinates multiple Claude instances for complex real estate workflows,
providing intelligent routing, context management, and workflow optimization.

Key Features:
- Smart Claude Router with automatic service selection
- Multi-Claude coordination for complex workflows
- Cost optimization through intelligent model selection
- Context-aware conversation routing
- Workflow pattern recognition and optimization

Integration with Universal Claude Gateway for seamless orchestration.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
import redis.asyncio as redis

from ..core.service_registry import ServiceRegistry
from ..services.universal_claude_gateway import UniversalClaudeGateway
from ..services.agent_profile_service import AgentProfileService
from ..models.agent_profile_models import AgentProfile, AgentRole, GuidanceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Types of real estate workflows that require orchestration."""
    LEAD_QUALIFICATION = "lead_qualification"
    PROPERTY_SEARCH = "property_search"
    OFFER_NEGOTIATION = "offer_negotiation"
    TRANSACTION_MANAGEMENT = "transaction_management"
    MARKET_ANALYSIS = "market_analysis"
    CLIENT_CONSULTATION = "client_consultation"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    PERFORMANCE_COACHING = "performance_coaching"


class OrchestrationComplexity(str, Enum):
    """Complexity levels for determining orchestration strategy."""
    SIMPLE = "simple"          # Single Claude instance
    MODERATE = "moderate"      # 2-3 coordinated instances
    COMPLEX = "complex"        # 4-6 specialized instances
    ENTERPRISE = "enterprise"  # Full orchestration with learning


class ClaudeInstanceRole(str, Enum):
    """Specialized roles for Claude instances in orchestration."""
    COORDINATOR = "coordinator"           # Main orchestration logic
    LEAD_ANALYZER = "lead_analyzer"       # Lead qualification specialist
    PROPERTY_EXPERT = "property_expert"   # Property matching specialist
    MARKET_ANALYST = "market_analyst"     # Market data analysis
    BEHAVIORAL_COACH = "behavioral_coach" # Agent coaching specialist
    COMPLIANCE_OFFICER = "compliance_officer" # Legal/compliance validation
    PERFORMANCE_OPTIMIZER = "performance_optimizer" # Workflow optimization
    CONTEXT_MANAGER = "context_manager"   # Cross-session context


@dataclass
class ClaudeInstance:
    """Configuration for a specialized Claude instance."""
    role: ClaudeInstanceRole
    agent_context: Optional[AgentProfile] = None
    specialization_prompt: str = ""
    priority_score: float = 1.0
    cost_weight: float = 1.0
    response_time_target: float = 500.0  # milliseconds
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowExecution:
    """Tracks execution of a complex workflow."""
    workflow_id: str
    workflow_type: WorkflowType
    complexity: OrchestrationComplexity
    agent_id: str
    instances: List[ClaudeInstance]
    start_time: datetime
    status: str = "running"
    results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    cost_analysis: Dict[str, float] = field(default_factory=dict)


class OrchestrationRequest(BaseModel):
    """Request for multi-Claude orchestration."""
    workflow_type: WorkflowType
    query: str
    agent_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    complexity_override: Optional[OrchestrationComplexity] = None
    priority: float = Field(default=1.0, ge=0.1, le=10.0)
    cost_limit: Optional[float] = None
    time_limit: Optional[float] = None  # seconds
    enable_learning: bool = True


class OrchestrationResponse(BaseModel):
    """Response from multi-Claude orchestration."""
    workflow_id: str
    workflow_type: WorkflowType
    complexity: OrchestrationComplexity
    primary_response: Dict[str, Any]
    specialized_insights: Dict[ClaudeInstanceRole, Dict[str, Any]]
    coordination_summary: str
    performance_metrics: Dict[str, float]
    cost_analysis: Dict[str, float]
    recommendations: List[str]
    execution_time: float
    success: bool = True
    error_message: Optional[str] = None


class ClaudeOrchestrationEngine:
    """Advanced orchestration engine for multi-Claude workflows."""

    def __init__(
        self,
        service_registry: ServiceRegistry,
        redis_client: Optional[redis.Redis] = None
    ):
        self.service_registry = service_registry
        self.redis_client = redis_client or redis.from_url("redis://localhost:6379/0")
        self.gateway = UniversalClaudeGateway(service_registry, redis_client)
        self.agent_service = AgentProfileService(service_registry, redis_client)

        # Orchestration state
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_patterns: Dict[WorkflowType, Dict[str, Any]] = {}
        self.performance_history: List[Dict[str, Any]] = []

        # Configuration
        self.max_concurrent_workflows = 50
        self.default_timeout = 30.0  # seconds
        self.cost_optimization_threshold = 0.8

        # Initialize workflow patterns
        self._initialize_workflow_patterns()

    def _initialize_workflow_patterns(self) -> None:
        """Initialize pre-defined workflow patterns for different real estate scenarios."""
        self.workflow_patterns = {
            WorkflowType.LEAD_QUALIFICATION: {
                "instances": [
                    {"role": ClaudeInstanceRole.COORDINATOR, "priority": 1.0},
                    {"role": ClaudeInstanceRole.LEAD_ANALYZER, "priority": 0.9},
                    {"role": ClaudeInstanceRole.BEHAVIORAL_COACH, "priority": 0.7}
                ],
                "complexity_threshold": OrchestrationComplexity.MODERATE,
                "expected_duration": 15.0  # seconds
            },
            WorkflowType.PROPERTY_SEARCH: {
                "instances": [
                    {"role": ClaudeInstanceRole.COORDINATOR, "priority": 1.0},
                    {"role": ClaudeInstanceRole.PROPERTY_EXPERT, "priority": 0.9},
                    {"role": ClaudeInstanceRole.MARKET_ANALYST, "priority": 0.8},
                    {"role": ClaudeInstanceRole.BEHAVIORAL_COACH, "priority": 0.6}
                ],
                "complexity_threshold": OrchestrationComplexity.COMPLEX,
                "expected_duration": 25.0
            },
            WorkflowType.TRANSACTION_MANAGEMENT: {
                "instances": [
                    {"role": ClaudeInstanceRole.COORDINATOR, "priority": 1.0},
                    {"role": ClaudeInstanceRole.COMPLIANCE_OFFICER, "priority": 0.95},
                    {"role": ClaudeInstanceRole.PERFORMANCE_OPTIMIZER, "priority": 0.8},
                    {"role": ClaudeInstanceRole.CONTEXT_MANAGER, "priority": 0.7}
                ],
                "complexity_threshold": OrchestrationComplexity.ENTERPRISE,
                "expected_duration": 40.0
            }
        }

    async def orchestrate_workflow(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """
        Orchestrate a complex real estate workflow using multiple Claude instances.

        Args:
            request: Orchestration request with workflow details

        Returns:
            Comprehensive response from coordinated Claude instances
        """
        workflow_id = f"{request.workflow_type.value}_{int(time.time() * 1000)}"
        start_time = datetime.now()

        try:
            # Get agent profile for context
            agent_profile = await self.agent_service.get_agent_profile(request.agent_id)
            if not agent_profile:
                return self._create_error_response(
                    workflow_id, request, "Agent profile not found", start_time
                )

            # Determine complexity and required instances
            complexity = self._determine_complexity(request, agent_profile)
            required_instances = self._plan_instances(request.workflow_type, complexity, agent_profile)

            # Create workflow execution tracker
            workflow = WorkflowExecution(
                workflow_id=workflow_id,
                workflow_type=request.workflow_type,
                complexity=complexity,
                agent_id=request.agent_id,
                instances=required_instances,
                start_time=start_time
            )

            self.active_workflows[workflow_id] = workflow

            # Execute orchestrated workflow
            if complexity == OrchestrationComplexity.SIMPLE:
                response = await self._execute_simple_workflow(workflow, request)
            elif complexity == OrchestrationComplexity.MODERATE:
                response = await self._execute_moderate_workflow(workflow, request)
            elif complexity == OrchestrationComplexity.COMPLEX:
                response = await self._execute_complex_workflow(workflow, request)
            else:  # ENTERPRISE
                response = await self._execute_enterprise_workflow(workflow, request)

            # Record performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._record_performance_metrics(workflow, execution_time, response)

            # Clean up
            del self.active_workflows[workflow_id]

            return response

        except Exception as e:
            logger.error(f"Orchestration failed for workflow {workflow_id}: {str(e)}")
            return self._create_error_response(workflow_id, request, str(e), start_time)

    def _determine_complexity(
        self, request: OrchestrationRequest, agent_profile: AgentProfile
    ) -> OrchestrationComplexity:
        """Determine workflow complexity based on request and agent context."""
        if request.complexity_override:
            return request.complexity_override

        # Base complexity from workflow type
        base_complexity = self.workflow_patterns.get(
            request.workflow_type, {}
        ).get("complexity_threshold", OrchestrationComplexity.MODERATE)

        # Adjust based on agent experience and specialization
        complexity_score = 0.5  # Base score

        if agent_profile.years_experience < 2:
            complexity_score += 0.3  # New agents need more guidance
        elif agent_profile.years_experience > 10:
            complexity_score -= 0.2  # Experienced agents need less

        if len(agent_profile.specializations) > 2:
            complexity_score += 0.2  # More specializations = more complex guidance

        # Query complexity analysis
        query_indicators = {
            "multiple": 0.2, "complex": 0.3, "analyze": 0.2, "compare": 0.3,
            "negotiate": 0.4, "compliance": 0.5, "legal": 0.5
        }

        for indicator, weight in query_indicators.items():
            if indicator.lower() in request.query.lower():
                complexity_score += weight

        # Map score to complexity
        if complexity_score <= 0.4:
            return OrchestrationComplexity.SIMPLE
        elif complexity_score <= 0.7:
            return OrchestrationComplexity.MODERATE
        elif complexity_score <= 1.0:
            return OrchestrationComplexity.COMPLEX
        else:
            return OrchestrationComplexity.ENTERPRISE

    def _plan_instances(
        self, workflow_type: WorkflowType, complexity: OrchestrationComplexity,
        agent_profile: AgentProfile
    ) -> List[ClaudeInstance]:
        """Plan required Claude instances based on workflow and complexity."""
        pattern = self.workflow_patterns.get(workflow_type, {})
        base_instances = pattern.get("instances", [])

        instances = []
        for instance_config in base_instances:
            instance = ClaudeInstance(
                role=instance_config["role"],
                agent_context=agent_profile,
                priority_score=instance_config["priority"],
                specialization_prompt=self._get_specialization_prompt(
                    instance_config["role"], workflow_type, agent_profile
                )
            )
            instances.append(instance)

        # Adjust instances based on complexity
        if complexity == OrchestrationComplexity.SIMPLE:
            # Keep only coordinator
            instances = [i for i in instances if i.role == ClaudeInstanceRole.COORDINATOR]
        elif complexity == OrchestrationComplexity.ENTERPRISE:
            # Add additional specialized instances
            additional_roles = [
                ClaudeInstanceRole.PERFORMANCE_OPTIMIZER,
                ClaudeInstanceRole.CONTEXT_MANAGER
            ]
            for role in additional_roles:
                if not any(i.role == role for i in instances):
                    instance = ClaudeInstance(
                        role=role,
                        agent_context=agent_profile,
                        priority_score=0.6,
                        specialization_prompt=self._get_specialization_prompt(
                            role, workflow_type, agent_profile
                        )
                    )
                    instances.append(instance)

        return instances

    def _get_specialization_prompt(
        self, role: ClaudeInstanceRole, workflow_type: WorkflowType,
        agent_profile: AgentProfile
    ) -> str:
        """Generate specialized prompt for Claude instance based on role and context."""
        base_prompts = {
            ClaudeInstanceRole.COORDINATOR: f"""
You are a real estate workflow coordinator specializing in {workflow_type.value}.
Agent Context: {agent_profile.primary_role.value} with {agent_profile.years_experience} years experience.
Specializations: {', '.join(agent_profile.specializations)}

Your role is to coordinate multiple Claude specialists and synthesize their insights into
actionable guidance for the agent. Focus on workflow efficiency and outcome optimization.
""",
            ClaudeInstanceRole.LEAD_ANALYZER: f"""
You are a lead qualification specialist for real estate agents.
Agent Context: Working with {agent_profile.primary_role.value} agents.

Analyze leads for qualification score, buying/selling motivation, budget alignment,
timeline urgency, and conversion probability. Provide specific next-step recommendations.
""",
            ClaudeInstanceRole.PROPERTY_EXPERT: f"""
You are a property matching and valuation expert.
Agent Focus: {agent_profile.primary_role.value} specializing in {', '.join(agent_profile.specializations)}.

Analyze property characteristics, market positioning, pricing strategy, and match
quality for specific client needs. Consider local market conditions and trends.
""",
            ClaudeInstanceRole.MARKET_ANALYST: f"""
You are a real estate market analysis specialist.
Agent Specializations: {', '.join(agent_profile.specializations)}.

Provide market insights, pricing trends, competitive analysis, and investment
recommendations based on current market conditions and historical data.
""",
            ClaudeInstanceRole.BEHAVIORAL_COACH: f"""
You are an agent coaching specialist focusing on behavioral optimization.
Agent Profile: {agent_profile.primary_role.value}, {agent_profile.years_experience} years experience.

Analyze agent-client interactions and provide coaching on communication style,
negotiation tactics, relationship building, and performance improvement.
""",
            ClaudeInstanceRole.COMPLIANCE_OFFICER: f"""
You are a real estate compliance and legal specialist.
Jurisdiction: Based on agent location and specializations.

Review transactions, contracts, and processes for legal compliance, risk assessment,
and regulatory adherence. Flag potential issues and recommend mitigations.
""",
            ClaudeInstanceRole.PERFORMANCE_OPTIMIZER: f"""
You are a workflow and performance optimization specialist.
Agent Experience Level: {agent_profile.years_experience} years.

Analyze workflows for efficiency improvements, automation opportunities,
and performance optimization. Focus on time management and productivity gains.
""",
            ClaudeInstanceRole.CONTEXT_MANAGER: f"""
You are a context and knowledge management specialist.
Agent Role: {agent_profile.primary_role.value}.

Manage cross-session context, conversation continuity, and knowledge capture.
Ensure consistent service quality and continuous learning from interactions.
"""
        }

        return base_prompts.get(role, "You are a real estate AI specialist.")

    async def _execute_simple_workflow(
        self, workflow: WorkflowExecution, request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """Execute simple workflow with single Claude instance."""
        coordinator = next(
            (i for i in workflow.instances if i.role == ClaudeInstanceRole.COORDINATOR),
            workflow.instances[0]
        )

        # Use Universal Claude Gateway for single instance
        from ..services.universal_claude_gateway import UniversalQueryRequest

        gateway_request = UniversalQueryRequest(
            query=request.query,
            agent_id=request.agent_id,
            guidance_types=[GuidanceType.RESPONSE_SUGGESTIONS, GuidanceType.STRATEGY_COACHING],
            context=request.context,
            enable_caching=True
        )

        gateway_response = await self.gateway.process_universal_query(gateway_request)

        return OrchestrationResponse(
            workflow_id=workflow.workflow_id,
            workflow_type=workflow.workflow_type,
            complexity=workflow.complexity,
            primary_response=gateway_response.responses,
            specialized_insights={coordinator.role: gateway_response.responses},
            coordination_summary="Single instance execution completed successfully.",
            performance_metrics={
                "response_time": gateway_response.metadata.get("response_time", 0),
                "token_usage": gateway_response.metadata.get("token_usage", 0)
            },
            cost_analysis={
                "total_cost": gateway_response.metadata.get("estimated_cost", 0),
                "cost_per_token": gateway_response.metadata.get("cost_per_token", 0)
            },
            recommendations=["Consider workflow optimization for future similar requests."],
            execution_time=gateway_response.metadata.get("response_time", 0) / 1000
        )

    async def _execute_moderate_workflow(
        self, workflow: WorkflowExecution, request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """Execute moderate complexity workflow with 2-3 coordinated instances."""
        start_time = time.time()

        # Execute specialized instances in parallel
        specialist_tasks = []
        coordinator_instance = None

        for instance in workflow.instances:
            if instance.role == ClaudeInstanceRole.COORDINATOR:
                coordinator_instance = instance
                continue

            # Create specialized query for this instance
            specialized_query = self._create_specialized_query(
                request.query, instance.role, request.context
            )

            task = self._execute_specialized_instance(
                instance, specialized_query, request.agent_id
            )
            specialist_tasks.append(task)

        # Execute specialists in parallel
        specialist_results = await asyncio.gather(*specialist_tasks, return_exceptions=True)

        # Filter successful results
        successful_results = {}
        for i, result in enumerate(specialist_results):
            if not isinstance(result, Exception):
                instance = [inst for inst in workflow.instances
                           if inst.role != ClaudeInstanceRole.COORDINATOR][i]
                successful_results[instance.role] = result

        # Execute coordinator with specialist insights
        coordinator_context = {
            **request.context,
            "specialist_insights": successful_results,
            "workflow_type": request.workflow_type.value
        }

        coordinator_query = f"""
Original Query: {request.query}

Specialist Insights Available:
{json.dumps({role.value: insights for role, insights in successful_results.items()}, indent=2)}

Please coordinate these insights and provide a comprehensive response with:
1. Synthesized analysis combining specialist perspectives
2. Prioritized action recommendations
3. Risk assessment and mitigation strategies
4. Next steps for the agent
"""

        coordinator_response = await self._execute_specialized_instance(
            coordinator_instance, coordinator_query, request.agent_id
        )

        execution_time = time.time() - start_time

        # Calculate performance metrics
        total_tokens = sum(r.get("token_usage", 0) for r in successful_results.values())
        total_tokens += coordinator_response.get("token_usage", 0)

        total_cost = sum(r.get("estimated_cost", 0) for r in successful_results.values())
        total_cost += coordinator_response.get("estimated_cost", 0)

        return OrchestrationResponse(
            workflow_id=workflow.workflow_id,
            workflow_type=workflow.workflow_type,
            complexity=workflow.complexity,
            primary_response=coordinator_response,
            specialized_insights=successful_results,
            coordination_summary=coordinator_response.get("analysis", "Coordination completed."),
            performance_metrics={
                "response_time": execution_time * 1000,
                "token_usage": total_tokens,
                "parallel_efficiency": len(successful_results) / len(specialist_tasks) if specialist_tasks else 1.0
            },
            cost_analysis={
                "total_cost": total_cost,
                "specialist_costs": {role.value: r.get("estimated_cost", 0) for role, r in successful_results.items()},
                "coordinator_cost": coordinator_response.get("estimated_cost", 0)
            },
            recommendations=[
                f"Executed {len(successful_results)} specialist instances successfully.",
                "Consider caching specialist results for similar queries.",
                f"Workflow completed in {execution_time:.2f}s with {len(successful_results)} coordinated insights."
            ],
            execution_time=execution_time
        )

    async def _execute_complex_workflow(
        self, workflow: WorkflowExecution, request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """Execute complex workflow with 4-6 specialized instances."""
        start_time = time.time()

        # Phase 1: Execute high-priority specialists
        high_priority_instances = [
            i for i in workflow.instances
            if i.role != ClaudeInstanceRole.COORDINATOR and i.priority_score >= 0.8
        ]

        high_priority_tasks = []
        for instance in high_priority_instances:
            specialized_query = self._create_specialized_query(
                request.query, instance.role, request.context
            )
            task = self._execute_specialized_instance(
                instance, specialized_query, request.agent_id
            )
            high_priority_tasks.append(task)

        high_priority_results = await asyncio.gather(*high_priority_tasks, return_exceptions=True)

        # Phase 2: Execute lower-priority specialists with high-priority context
        low_priority_instances = [
            i for i in workflow.instances
            if i.role != ClaudeInstanceRole.COORDINATOR and i.priority_score < 0.8
        ]

        # Build enhanced context from high-priority results
        enhanced_context = {**request.context}
        high_priority_insights = {}

        for i, result in enumerate(high_priority_results):
            if not isinstance(result, Exception):
                instance = high_priority_instances[i]
                high_priority_insights[instance.role] = result
                enhanced_context[f"{instance.role.value}_insights"] = result

        # Execute low-priority specialists with enhanced context
        low_priority_tasks = []
        for instance in low_priority_instances:
            specialized_query = self._create_specialized_query(
                request.query, instance.role, enhanced_context
            )
            task = self._execute_specialized_instance(
                instance, specialized_query, request.agent_id
            )
            low_priority_tasks.append(task)

        low_priority_results = await asyncio.gather(*low_priority_tasks, return_exceptions=True)

        # Combine all specialist results
        all_specialist_results = {}
        all_specialist_results.update(high_priority_insights)

        for i, result in enumerate(low_priority_results):
            if not isinstance(result, Exception):
                instance = low_priority_instances[i]
                all_specialist_results[instance.role] = result

        # Phase 3: Coordinator synthesis
        coordinator_instance = next(
            (i for i in workflow.instances if i.role == ClaudeInstanceRole.COORDINATOR),
            None
        )

        if coordinator_instance:
            coordinator_context = {
                **enhanced_context,
                "all_specialist_insights": all_specialist_results,
                "workflow_complexity": "complex",
                "execution_phases": ["high_priority", "low_priority", "coordination"]
            }

            coordinator_query = f"""
Complex Real Estate Workflow Analysis:

Original Query: {request.query}
Workflow Type: {request.workflow_type.value}

High-Priority Specialist Insights:
{json.dumps({role.value: insights for role, insights in high_priority_insights.items()}, indent=2)}

Additional Specialist Insights:
{json.dumps({role.value: insights for role, insights in all_specialist_results.items() if role not in high_priority_insights}, indent=2)}

Please provide a comprehensive coordination response that:
1. Synthesizes all specialist perspectives into actionable guidance
2. Identifies critical dependencies and potential conflicts
3. Prioritizes recommendations based on agent role and experience
4. Provides implementation timeline and success metrics
5. Highlights risk factors and mitigation strategies
"""

            coordinator_response = await self._execute_specialized_instance(
                coordinator_instance, coordinator_query, request.agent_id
            )
        else:
            coordinator_response = {
                "analysis": "Complex workflow completed without coordinator",
                "recommendations": ["Review specialist insights for comprehensive guidance"]
            }

        execution_time = time.time() - start_time

        # Advanced performance metrics for complex workflows
        total_tokens = sum(r.get("token_usage", 0) for r in all_specialist_results.values())
        total_tokens += coordinator_response.get("token_usage", 0)

        total_cost = sum(r.get("estimated_cost", 0) for r in all_specialist_results.values())
        total_cost += coordinator_response.get("estimated_cost", 0)

        parallel_efficiency = (
            len(high_priority_results) + len(low_priority_results)
        ) / (len(high_priority_instances) + len(low_priority_instances)) if (high_priority_instances or low_priority_instances) else 1.0

        return OrchestrationResponse(
            workflow_id=workflow.workflow_id,
            workflow_type=workflow.workflow_type,
            complexity=workflow.complexity,
            primary_response=coordinator_response,
            specialized_insights=all_specialist_results,
            coordination_summary=coordinator_response.get("analysis", "Complex workflow coordination completed."),
            performance_metrics={
                "response_time": execution_time * 1000,
                "token_usage": total_tokens,
                "parallel_efficiency": parallel_efficiency,
                "phase_1_specialists": len(high_priority_instances),
                "phase_2_specialists": len(low_priority_instances),
                "successful_specialists": len(all_specialist_results)
            },
            cost_analysis={
                "total_cost": total_cost,
                "high_priority_cost": sum(r.get("estimated_cost", 0) for r in high_priority_insights.values()),
                "low_priority_cost": total_cost - sum(r.get("estimated_cost", 0) for r in high_priority_insights.values()) - coordinator_response.get("estimated_cost", 0),
                "coordinator_cost": coordinator_response.get("estimated_cost", 0),
                "cost_per_specialist": total_cost / len(all_specialist_results) if all_specialist_results else 0
            },
            recommendations=[
                f"Complex workflow executed with {len(all_specialist_results)} coordinated specialists.",
                f"Phased execution optimized for {parallel_efficiency:.1%} efficiency.",
                "Consider workflow pattern caching for similar complex requests.",
                f"Execution time: {execution_time:.2f}s with comprehensive multi-phase analysis."
            ],
            execution_time=execution_time
        )

    async def _execute_enterprise_workflow(
        self, workflow: WorkflowExecution, request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """Execute enterprise-level workflow with full orchestration and learning."""
        start_time = time.time()

        # Enterprise workflows include advanced features:
        # - Adaptive execution based on real-time performance
        # - Continuous learning and optimization
        # - Advanced error handling and recovery
        # - Cross-workflow context sharing

        # Phase 1: Workflow Planning and Optimization
        workflow_context = {
            **request.context,
            "enterprise_mode": True,
            "learning_enabled": request.enable_learning,
            "historical_patterns": await self._get_historical_patterns(request.workflow_type)
        }

        # Phase 2: Adaptive Specialist Execution
        all_specialist_results = {}
        execution_phases = []

        # Execute specialists in adaptive phases
        for phase_name, instances in self._plan_enterprise_phases(workflow.instances):
            phase_start = time.time()

            phase_tasks = []
            for instance in instances:
                specialized_query = self._create_specialized_query(
                    request.query, instance.role, workflow_context
                )
                task = self._execute_specialized_instance(
                    instance, specialized_query, request.agent_id
                )
                phase_tasks.append(task)

            phase_results = await asyncio.gather(*phase_tasks, return_exceptions=True)

            # Process phase results and update context
            phase_insights = {}
            for i, result in enumerate(phase_results):
                if not isinstance(result, Exception):
                    instance = instances[i]
                    phase_insights[instance.role] = result
                    all_specialist_results[instance.role] = result
                    workflow_context[f"{instance.role.value}_insights"] = result

            execution_phases.append({
                "name": phase_name,
                "duration": time.time() - phase_start,
                "specialists": len(instances),
                "successful": len(phase_insights),
                "insights": phase_insights
            })

        # Phase 3: Advanced Coordinator Synthesis
        coordinator_instance = next(
            (i for i in workflow.instances if i.role == ClaudeInstanceRole.COORDINATOR),
            None
        )

        if coordinator_instance:
            coordinator_query = f"""
Enterprise Real Estate Workflow Analysis:

Original Query: {request.query}
Workflow Type: {request.workflow_type.value}
Agent Context: {workflow.agent_id}

Execution Summary:
{json.dumps(execution_phases, indent=2)}

Complete Specialist Insights:
{json.dumps({role.value: insights for role, insights in all_specialist_results.items()}, indent=2)}

Historical Patterns:
{json.dumps(workflow_context.get("historical_patterns", {}), indent=2)}

Please provide an enterprise-level coordination response that includes:

1. Executive Summary with key findings and recommendations
2. Strategic Analysis combining all specialist perspectives
3. Implementation Roadmap with specific timelines and milestones
4. Risk Assessment with comprehensive mitigation strategies
5. Success Metrics and KPIs for measuring outcomes
6. Continuous Improvement recommendations for future workflows
7. Agent-specific coaching based on performance patterns
8. Resource optimization opportunities identified
9. Compliance and regulatory considerations
10. Long-term strategic implications and opportunities

Focus on delivering actionable intelligence that drives measurable business results.
"""

            coordinator_response = await self._execute_specialized_instance(
                coordinator_instance, coordinator_query, request.agent_id
            )
        else:
            coordinator_response = {
                "analysis": "Enterprise workflow completed without coordinator",
                "recommendations": ["Review detailed specialist insights for comprehensive guidance"]
            }

        execution_time = time.time() - start_time

        # Enterprise-level performance analytics
        total_tokens = sum(r.get("token_usage", 0) for r in all_specialist_results.values())
        total_tokens += coordinator_response.get("token_usage", 0)

        total_cost = sum(r.get("estimated_cost", 0) for r in all_specialist_results.values())
        total_cost += coordinator_response.get("estimated_cost", 0)

        # Advanced metrics
        phase_efficiency = sum(p["successful"] / p["specialists"] for p in execution_phases) / len(execution_phases) if execution_phases else 1.0
        average_phase_time = sum(p["duration"] for p in execution_phases) / len(execution_phases) if execution_phases else 0

        # Store learning data for future optimization
        if request.enable_learning:
            await self._store_enterprise_learning_data(workflow, execution_phases, coordinator_response)

        return OrchestrationResponse(
            workflow_id=workflow.workflow_id,
            workflow_type=workflow.workflow_type,
            complexity=workflow.complexity,
            primary_response=coordinator_response,
            specialized_insights=all_specialist_results,
            coordination_summary=coordinator_response.get("analysis", "Enterprise workflow coordination completed with advanced analytics."),
            performance_metrics={
                "response_time": execution_time * 1000,
                "token_usage": total_tokens,
                "phase_efficiency": phase_efficiency,
                "average_phase_time": average_phase_time,
                "total_phases": len(execution_phases),
                "successful_specialists": len(all_specialist_results),
                "enterprise_features_enabled": True
            },
            cost_analysis={
                "total_cost": total_cost,
                "phase_breakdown": {p["name"]: sum(
                    all_specialist_results.get(inst.role, {}).get("estimated_cost", 0)
                    for inst in workflow.instances if inst.role in [r.role for r in p.get("insights", {}).keys()]
                ) for p in execution_phases},
                "coordinator_cost": coordinator_response.get("estimated_cost", 0),
                "cost_efficiency": total_cost / execution_time if execution_time > 0 else 0,
                "cost_per_insight": total_cost / len(all_specialist_results) if all_specialist_results else 0
            },
            recommendations=[
                f"Enterprise workflow executed with {len(all_specialist_results)} coordinated specialists across {len(execution_phases)} phases.",
                f"Achieved {phase_efficiency:.1%} phase efficiency with comprehensive analysis.",
                "Learning data captured for continuous workflow optimization.",
                f"Total execution time: {execution_time:.2f}s with enterprise-level insights.",
                "Consider establishing this pattern for similar high-value workflows."
            ],
            execution_time=execution_time
        )

    def _plan_enterprise_phases(self, instances: List[ClaudeInstance]) -> List[Tuple[str, List[ClaudeInstance]]]:
        """Plan execution phases for enterprise workflows."""
        phases = []

        # Phase 1: Foundation Analysis (highest priority)
        foundation_instances = [
            i for i in instances
            if i.role in [ClaudeInstanceRole.LEAD_ANALYZER, ClaudeInstanceRole.PROPERTY_EXPERT]
            and i.priority_score >= 0.9
        ]
        if foundation_instances:
            phases.append(("foundation_analysis", foundation_instances))

        # Phase 2: Market and Compliance Analysis
        market_compliance_instances = [
            i for i in instances
            if i.role in [ClaudeInstanceRole.MARKET_ANALYST, ClaudeInstanceRole.COMPLIANCE_OFFICER]
        ]
        if market_compliance_instances:
            phases.append(("market_compliance", market_compliance_instances))

        # Phase 3: Optimization and Coaching
        optimization_instances = [
            i for i in instances
            if i.role in [ClaudeInstanceRole.PERFORMANCE_OPTIMIZER, ClaudeInstanceRole.BEHAVIORAL_COACH]
        ]
        if optimization_instances:
            phases.append(("optimization_coaching", optimization_instances))

        # Phase 4: Context and Integration
        context_instances = [
            i for i in instances
            if i.role == ClaudeInstanceRole.CONTEXT_MANAGER
        ]
        if context_instances:
            phases.append(("context_integration", context_instances))

        # Add any remaining instances to appropriate phases
        remaining_instances = [
            i for i in instances
            if i.role != ClaudeInstanceRole.COORDINATOR and
            not any(i in phase_instances for _, phase_instances in phases)
        ]

        if remaining_instances:
            phases.append(("additional_analysis", remaining_instances))

        return phases

    def _create_specialized_query(
        self, original_query: str, role: ClaudeInstanceRole, context: Dict[str, Any]
    ) -> str:
        """Create specialized query for specific Claude instance role."""
        role_focuses = {
            ClaudeInstanceRole.LEAD_ANALYZER: "lead qualification, scoring, and conversion probability",
            ClaudeInstanceRole.PROPERTY_EXPERT: "property analysis, matching, and valuation",
            ClaudeInstanceRole.MARKET_ANALYST: "market trends, pricing analysis, and competitive positioning",
            ClaudeInstanceRole.BEHAVIORAL_COACH: "agent coaching, communication optimization, and performance improvement",
            ClaudeInstanceRole.COMPLIANCE_OFFICER: "legal compliance, risk assessment, and regulatory requirements",
            ClaudeInstanceRole.PERFORMANCE_OPTIMIZER: "workflow optimization, efficiency improvements, and automation opportunities",
            ClaudeInstanceRole.CONTEXT_MANAGER: "context preservation, knowledge management, and cross-session continuity"
        }

        focus = role_focuses.get(role, "general real estate analysis")

        specialized_query = f"""
Role: {role.value.replace('_', ' ').title()} Specialist

Focus Area: {focus}

Original Request: {original_query}

Context Information:
{json.dumps(context, indent=2)}

Please provide specialized analysis and recommendations specific to your expertise area.
Include specific, actionable insights that complement other specialists' perspectives.
"""
        return specialized_query

    async def _execute_specialized_instance(
        self, instance: ClaudeInstance, query: str, agent_id: str
    ) -> Dict[str, Any]:
        """Execute a single specialized Claude instance."""
        try:
            # Use Universal Claude Gateway with specialized context
            from ..services.universal_claude_gateway import UniversalQueryRequest

            gateway_request = UniversalQueryRequest(
                query=f"{instance.specialization_prompt}\n\n{query}",
                agent_id=agent_id,
                guidance_types=[GuidanceType.RESPONSE_SUGGESTIONS, GuidanceType.STRATEGY_COACHING],
                context={"specialist_role": instance.role.value},
                enable_caching=True
            )

            response = await self.gateway.process_universal_query(gateway_request)

            # Add specialist-specific metadata
            result = {
                "specialist_role": instance.role.value,
                "analysis": response.responses.get("analysis", ""),
                "recommendations": response.responses.get("recommendations", []),
                "insights": response.responses.get("insights", {}),
                "token_usage": response.metadata.get("token_usage", 0),
                "estimated_cost": response.metadata.get("estimated_cost", 0),
                "response_time": response.metadata.get("response_time", 0),
                "confidence_score": response.metadata.get("confidence_score", 0.8)
            }

            return result

        except Exception as e:
            logger.error(f"Specialized instance execution failed for {instance.role}: {str(e)}")
            return {
                "specialist_role": instance.role.value,
                "error": str(e),
                "analysis": f"Specialist analysis unavailable due to error: {str(e)}",
                "recommendations": ["Review error and retry if necessary"],
                "token_usage": 0,
                "estimated_cost": 0,
                "response_time": 0,
                "confidence_score": 0.0
            }

    async def _get_historical_patterns(self, workflow_type: WorkflowType) -> Dict[str, Any]:
        """Get historical workflow patterns for optimization."""
        try:
            cache_key = f"workflow_patterns:{workflow_type.value}"
            cached_patterns = await self.redis_client.get(cache_key)

            if cached_patterns:
                return json.loads(cached_patterns)

            # Generate patterns from performance history
            relevant_history = [
                h for h in self.performance_history
                if h.get("workflow_type") == workflow_type.value
            ]

            if not relevant_history:
                return {"message": "No historical patterns available"}

            patterns = {
                "average_execution_time": sum(h.get("execution_time", 0) for h in relevant_history) / len(relevant_history),
                "success_rate": sum(1 for h in relevant_history if h.get("success", False)) / len(relevant_history),
                "common_specialists": {},
                "optimization_opportunities": []
            }

            # Cache patterns for 1 hour
            await self.redis_client.setex(
                cache_key,
                3600,
                json.dumps(patterns)
            )

            return patterns

        except Exception as e:
            logger.error(f"Error getting historical patterns: {str(e)}")
            return {"error": str(e)}

    async def _store_enterprise_learning_data(
        self, workflow: WorkflowExecution, execution_phases: List[Dict],
        coordinator_response: Dict[str, Any]
    ) -> None:
        """Store learning data for enterprise workflow optimization."""
        try:
            learning_data = {
                "workflow_id": workflow.workflow_id,
                "workflow_type": workflow.workflow_type.value,
                "complexity": workflow.complexity.value,
                "agent_id": workflow.agent_id,
                "execution_phases": execution_phases,
                "coordinator_insights": coordinator_response,
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "total_specialists": len(workflow.instances),
                    "successful_phases": len(execution_phases),
                    "total_execution_time": sum(p["duration"] for p in execution_phases)
                }
            }

            # Store in Redis with 30-day TTL
            cache_key = f"enterprise_learning:{workflow.workflow_id}"
            await self.redis_client.setex(
                cache_key,
                30 * 24 * 3600,  # 30 days
                json.dumps(learning_data)
            )

            # Add to performance history
            self.performance_history.append(learning_data)

            # Keep only last 100 entries in memory
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]

        except Exception as e:
            logger.error(f"Error storing enterprise learning data: {str(e)}")

    async def _record_performance_metrics(
        self, workflow: WorkflowExecution, execution_time: float,
        response: OrchestrationResponse
    ) -> None:
        """Record performance metrics for workflow optimization."""
        try:
            metrics = {
                "workflow_id": workflow.workflow_id,
                "workflow_type": workflow.workflow_type.value,
                "complexity": workflow.complexity.value,
                "execution_time": execution_time,
                "success": response.success,
                "specialist_count": len(workflow.instances),
                "total_cost": response.cost_analysis.get("total_cost", 0),
                "token_usage": response.performance_metrics.get("token_usage", 0),
                "timestamp": datetime.now().isoformat()
            }

            # Store metrics
            cache_key = f"workflow_metrics:{workflow.workflow_id}"
            await self.redis_client.setex(
                cache_key,
                7 * 24 * 3600,  # 7 days
                json.dumps(metrics)
            )

        except Exception as e:
            logger.error(f"Error recording performance metrics: {str(e)}")

    def _create_error_response(
        self, workflow_id: str, request: OrchestrationRequest,
        error_message: str, start_time: datetime
    ) -> OrchestrationResponse:
        """Create error response for failed orchestration."""
        execution_time = (datetime.now() - start_time).total_seconds()

        return OrchestrationResponse(
            workflow_id=workflow_id,
            workflow_type=request.workflow_type,
            complexity=OrchestrationComplexity.SIMPLE,
            primary_response={"error": error_message},
            specialized_insights={},
            coordination_summary=f"Orchestration failed: {error_message}",
            performance_metrics={
                "response_time": execution_time * 1000,
                "token_usage": 0,
                "success_rate": 0.0
            },
            cost_analysis={
                "total_cost": 0,
                "error_cost": 0
            },
            recommendations=[
                "Review error message and retry with adjusted parameters",
                "Consider reducing workflow complexity if issues persist"
            ],
            execution_time=execution_time,
            success=False,
            error_message=error_message
        )

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active or completed workflow."""
        try:
            # Check active workflows
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                return {
                    "workflow_id": workflow_id,
                    "status": "active",
                    "workflow_type": workflow.workflow_type.value,
                    "complexity": workflow.complexity.value,
                    "start_time": workflow.start_time.isoformat(),
                    "specialist_count": len(workflow.instances),
                    "agent_id": workflow.agent_id
                }

            # Check completed workflows in Redis
            cache_key = f"workflow_metrics:{workflow_id}"
            cached_metrics = await self.redis_client.get(cache_key)

            if cached_metrics:
                metrics = json.loads(cached_metrics)
                metrics["status"] = "completed"
                return metrics

            return None

        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return None

    async def get_orchestration_analytics(
        self, time_period: int = 24
    ) -> Dict[str, Any]:
        """Get orchestration analytics for the specified time period (hours)."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_period)

            # Gather metrics from recent workflows
            recent_workflows = []
            workflow_keys = await self.redis_client.keys("workflow_metrics:*")

            for key in workflow_keys:
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        workflow_data = json.loads(data)
                        workflow_time = datetime.fromisoformat(workflow_data.get("timestamp", "1970-01-01"))

                        if workflow_time > cutoff_time:
                            recent_workflows.append(workflow_data)
                except Exception:
                    continue

            if not recent_workflows:
                return {
                    "message": f"No workflow data available for the last {time_period} hours",
                    "time_period": time_period
                }

            # Calculate analytics
            total_workflows = len(recent_workflows)
            successful_workflows = sum(1 for w in recent_workflows if w.get("success", False))

            analytics = {
                "time_period_hours": time_period,
                "total_workflows": total_workflows,
                "successful_workflows": successful_workflows,
                "success_rate": successful_workflows / total_workflows if total_workflows > 0 else 0,
                "average_execution_time": sum(w.get("execution_time", 0) for w in recent_workflows) / total_workflows if total_workflows > 0 else 0,
                "total_cost": sum(w.get("total_cost", 0) for w in recent_workflows),
                "average_cost_per_workflow": sum(w.get("total_cost", 0) for w in recent_workflows) / total_workflows if total_workflows > 0 else 0,
                "total_token_usage": sum(w.get("token_usage", 0) for w in recent_workflows),
                "workflow_type_distribution": {},
                "complexity_distribution": {},
                "performance_trends": {
                    "fastest_workflow": min(recent_workflows, key=lambda x: x.get("execution_time", float('inf')), default={}).get("execution_time", 0),
                    "slowest_workflow": max(recent_workflows, key=lambda x: x.get("execution_time", 0), default={}).get("execution_time", 0),
                    "most_expensive": max(recent_workflows, key=lambda x: x.get("total_cost", 0), default={}).get("total_cost", 0),
                    "least_expensive": min(recent_workflows, key=lambda x: x.get("total_cost", float('inf')), default={}).get("total_cost", 0)
                }
            }

            # Workflow type distribution
            for workflow in recent_workflows:
                workflow_type = workflow.get("workflow_type", "unknown")
                analytics["workflow_type_distribution"][workflow_type] = analytics["workflow_type_distribution"].get(workflow_type, 0) + 1

            # Complexity distribution
            for workflow in recent_workflows:
                complexity = workflow.get("complexity", "unknown")
                analytics["complexity_distribution"][complexity] = analytics["complexity_distribution"].get(complexity, 0) + 1

            return analytics

        except Exception as e:
            logger.error(f"Error getting orchestration analytics: {str(e)}")
            return {"error": str(e)}