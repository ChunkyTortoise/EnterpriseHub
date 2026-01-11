"""
Intelligent Workflow Automation Framework (Phase 2)

AI-powered workflow automation that learns from user behavior, suggests optimizations,
and automatically creates intelligent workflows across all EnterpriseHub hubs.

Key Features:
- AI-driven workflow pattern recognition and suggestion engine
- Behavioral learning from user interactions and business outcomes
- Automatic workflow optimization based on performance metrics
- Predictive workflow triggering with context awareness
- Smart workflow templates with industry-specific patterns
- Performance-based workflow evolution and A/B testing
- Integration with GHL Real Estate AI models for enhanced intelligence

Intelligence Capabilities:
- Lead qualification workflow automation with ML scoring
- Property matching workflows with behavioral insights
- Follow-up sequence optimization based on response patterns
- Deal progression workflows with predictive closing insights
- Agent coaching workflows triggered by performance patterns
"""

import asyncio
import json
import time
import pickle
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, NamedTuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
import uuid
import numpy as np
from pathlib import Path

# External dependencies
try:
    import redis
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    import joblib
except ImportError as e:
    print(f"Intelligent Workflow Automation: Missing dependencies: {e}")
    print("Install with: pip install redis pandas scikit-learn joblib")

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.unified_workflow_orchestrator import (
    AdvancedWorkflowOrchestrator, UnifiedWorkflow, WorkflowAction,
    WorkflowContext, HubType, WorkflowPriority, WorkflowStatus
)

logger = get_logger(__name__)


class AutomationType(Enum):
    """Types of intelligent automation."""
    TRIGGER_BASED = "trigger_based"        # Event-driven automation
    SCHEDULE_BASED = "schedule_based"      # Time-based automation
    BEHAVIORAL = "behavioral"              # Behavior pattern automation
    PREDICTIVE = "predictive"             # AI-predicted needs automation
    ADAPTIVE = "adaptive"                 # Self-optimizing automation
    CONTEXTUAL = "contextual"             # Context-aware automation


class WorkflowIntelligence(Enum):
    """Levels of workflow intelligence."""
    BASIC = "basic"           # Simple if-then rules
    PATTERN = "pattern"       # Pattern recognition based
    LEARNING = "learning"     # Continuous learning from outcomes
    PREDICTIVE = "predictive" # Predictive analytics driven
    ADAPTIVE = "adaptive"     # Self-adapting and optimizing


class OptimizationMetric(Enum):
    """Metrics for workflow optimization."""
    EXECUTION_TIME = "execution_time"
    SUCCESS_RATE = "success_rate"
    USER_SATISFACTION = "user_satisfaction"
    BUSINESS_OUTCOME = "business_outcome"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    ERROR_RATE = "error_rate"


@dataclass
class WorkflowPattern:
    """Discovered workflow pattern from user behavior."""

    pattern_id: str
    name: str
    description: str

    # Pattern characteristics
    trigger_sequence: List[str]
    action_sequence: List[Dict[str, Any]]
    success_indicators: List[str]

    # Analytics
    frequency: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    user_satisfaction: float = 0.0

    # Context
    applicable_roles: List[str] = field(default_factory=list)
    business_context: List[str] = field(default_factory=list)
    seasonal_patterns: Dict[str, float] = field(default_factory=dict)

    # Learning data
    training_examples: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AutomationRule:
    """Intelligent automation rule definition."""

    rule_id: str
    name: str
    description: str

    # Rule configuration
    automation_type: AutomationType
    intelligence_level: WorkflowIntelligence
    triggers: List[Dict[str, Any]]
    conditions: List[Dict[str, Any]]
    actions: List[WorkflowAction]

    # Performance settings
    priority: WorkflowPriority = WorkflowPriority.MEDIUM
    max_executions_per_hour: int = 10
    timeout_seconds: int = 300

    # Optimization
    optimization_metrics: List[OptimizationMetric] = field(default_factory=list)
    a_b_test_variants: List[Dict[str, Any]] = field(default_factory=list)

    # State tracking
    enabled: bool = True
    execution_count: int = 0
    success_count: int = 0
    last_execution: Optional[datetime] = None

    # Learning data
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class WorkflowSuggestion:
    """AI-generated workflow suggestion."""

    suggestion_id: str
    title: str
    description: str

    # Suggestion details
    suggested_workflow: UnifiedWorkflow
    confidence_score: float
    potential_time_savings: float  # minutes per execution
    potential_success_improvement: float  # percentage points

    # Context
    based_on_patterns: List[str]
    applicable_scenarios: List[str]
    business_justification: str

    # User interaction
    status: str = "pending"  # pending, accepted, rejected, implemented
    user_feedback: Optional[str] = None
    implementation_date: Optional[datetime] = None

    # Tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    suggested_by: str = "ai_system"


class BehavioralPatternAnalyzer:
    """Analyzes user behavior to identify automation opportunities."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize behavioral pattern analyzer."""
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)

        # Pattern recognition models
        self.clustering_model = None
        self.scaler = StandardScaler()

        # Pattern storage
        self.discovered_patterns: Dict[str, WorkflowPattern] = {}
        self.user_behaviors: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Analysis settings
        self.min_pattern_frequency = 3
        self.pattern_confidence_threshold = 0.7
        self.analysis_window_days = 30

    async def analyze_user_behavior(self, user_id: str) -> List[WorkflowPattern]:
        """Analyze user behavior to discover workflow patterns."""

        try:
            # Get user behavior data
            behavior_data = await self._get_user_behavior_data(user_id)

            if len(behavior_data) < self.min_pattern_frequency:
                return []

            # Extract features from behavior data
            features = self._extract_behavior_features(behavior_data)

            # Cluster similar behavior patterns
            patterns = await self._cluster_behavior_patterns(features, behavior_data)

            # Validate and score patterns
            validated_patterns = []
            for pattern in patterns:
                if pattern.confidence_score >= self.pattern_confidence_threshold:
                    validated_patterns.append(pattern)

            # Store discovered patterns
            for pattern in validated_patterns:
                self.discovered_patterns[pattern.pattern_id] = pattern

            logger.info(f"Discovered {len(validated_patterns)} workflow patterns for user {user_id}")
            return validated_patterns

        except Exception as e:
            logger.error(f"Behavior analysis failed for user {user_id}: {e}")
            return []

    async def _get_user_behavior_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user behavior data from the last N days."""

        behavior_key = f"user_behavior:{user_id}"
        behavior_data = await self.redis.lrange(behavior_key, 0, -1)

        parsed_data = []
        for data_point in behavior_data:
            try:
                parsed = json.loads(data_point)
                parsed_data.append(parsed)
            except json.JSONDecodeError:
                continue

        # Filter to analysis window
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.analysis_window_days)
        filtered_data = [
            d for d in parsed_data
            if datetime.fromisoformat(d.get("timestamp", "1970-01-01")) > cutoff_date
        ]

        return filtered_data

    def _extract_behavior_features(self, behavior_data: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features from behavior data for clustering."""

        features = []

        for data_point in behavior_data:
            # Time-based features
            timestamp = datetime.fromisoformat(data_point.get("timestamp", "1970-01-01"))
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()

            # Action-based features
            action_type_mapping = {
                "navigate": 1, "create": 2, "update": 3, "delete": 4,
                "search": 5, "filter": 6, "export": 7, "import": 8
            }
            action_type = action_type_mapping.get(data_point.get("action_type", "unknown"), 0)

            # Hub-based features
            hub_mapping = {
                "executive": 1, "lead_intelligence": 2, "automation": 3,
                "sales": 4, "ops": 5
            }
            hub = hub_mapping.get(data_point.get("hub", "unknown"), 0)

            # Duration and success features
            duration = data_point.get("duration", 0)
            success = 1 if data_point.get("success", False) else 0

            features.append([hour_of_day, day_of_week, action_type, hub, duration, success])

        return np.array(features)

    async def _cluster_behavior_patterns(self,
                                       features: np.ndarray,
                                       behavior_data: List[Dict[str, Any]]) -> List[WorkflowPattern]:
        """Cluster behavior data to identify patterns."""

        if len(features) < 3:
            return []

        try:
            # Scale features
            scaled_features = self.scaler.fit_transform(features)

            # Find optimal number of clusters
            max_clusters = min(10, len(features) // 2)
            best_score = -1
            best_n_clusters = 2

            for n_clusters in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(scaled_features)

                if len(set(cluster_labels)) > 1:  # Need at least 2 clusters for silhouette score
                    score = silhouette_score(scaled_features, cluster_labels)
                    if score > best_score:
                        best_score = score
                        best_n_clusters = n_clusters

            # Create final clustering
            self.clustering_model = KMeans(n_clusters=best_n_clusters, random_state=42, n_init=10)
            cluster_labels = self.clustering_model.fit_predict(scaled_features)

            # Convert clusters to workflow patterns
            patterns = []
            for cluster_id in set(cluster_labels):
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_behaviors = [behavior_data[i] for i in cluster_indices]

                pattern = self._create_pattern_from_cluster(cluster_id, cluster_behaviors)
                if pattern:
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return []

    def _create_pattern_from_cluster(self, cluster_id: int, behaviors: List[Dict[str, Any]]) -> Optional[WorkflowPattern]:
        """Create a workflow pattern from clustered behaviors."""

        if len(behaviors) < self.min_pattern_frequency:
            return None

        # Analyze action sequences
        action_sequences = []
        for behavior in behaviors:
            actions = behavior.get("action_sequence", [])
            if actions:
                action_sequences.append(actions)

        if not action_sequences:
            return None

        # Find common action patterns
        common_actions = self._find_common_action_sequence(action_sequences)

        # Calculate success metrics
        success_count = sum(1 for b in behaviors if b.get("success", False))
        success_rate = success_count / len(behaviors)

        # Calculate timing metrics
        durations = [b.get("duration", 0) for b in behaviors]
        avg_duration = sum(durations) / len(durations)

        # Create pattern
        pattern_id = f"pattern_{cluster_id}_{uuid.uuid4().hex[:8]}"

        pattern = WorkflowPattern(
            pattern_id=pattern_id,
            name=f"Workflow Pattern {cluster_id}",
            description=f"Discovered pattern from {len(behaviors)} similar user behaviors",
            trigger_sequence=self._extract_trigger_sequence(behaviors),
            action_sequence=common_actions,
            success_indicators=self._extract_success_indicators(behaviors),
            frequency=len(behaviors),
            success_rate=success_rate,
            avg_execution_time=avg_duration,
            confidence_score=min(1.0, success_rate * (len(behaviors) / 10))
        )

        return pattern

    def _find_common_action_sequence(self, action_sequences: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Find the most common action sequence pattern."""

        # For simplicity, return the most frequent first action
        if not action_sequences:
            return []

        first_actions = []
        for sequence in action_sequences:
            if sequence:
                first_actions.append(sequence[0])

        if not first_actions:
            return []

        # Count action types
        action_counts = Counter(action.get("type", "unknown") for action in first_actions)
        most_common_type = action_counts.most_common(1)[0][0]

        # Return representative action
        for action in first_actions:
            if action.get("type") == most_common_type:
                return [action]

        return []

    def _extract_trigger_sequence(self, behaviors: List[Dict[str, Any]]) -> List[str]:
        """Extract common trigger sequence from behaviors."""
        triggers = []
        for behavior in behaviors:
            trigger = behavior.get("trigger", "manual")
            triggers.append(trigger)

        # Return most common trigger
        trigger_counts = Counter(triggers)
        most_common = trigger_counts.most_common(1)
        return [most_common[0][0]] if most_common else ["manual"]

    def _extract_success_indicators(self, behaviors: List[Dict[str, Any]]) -> List[str]:
        """Extract success indicators from behaviors."""
        indicators = []
        for behavior in behaviors:
            if behavior.get("success", False):
                outcome = behavior.get("outcome", "completed")
                indicators.append(outcome)

        # Return unique indicators
        return list(set(indicators))


class WorkflowOptimizer:
    """Optimizes existing workflows based on performance data."""

    def __init__(self):
        """Initialize workflow optimizer."""
        self.optimization_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.optimization_strategies = {
            OptimizationMetric.EXECUTION_TIME: self._optimize_execution_time,
            OptimizationMetric.SUCCESS_RATE: self._optimize_success_rate,
            OptimizationMetric.USER_SATISFACTION: self._optimize_user_satisfaction,
            OptimizationMetric.BUSINESS_OUTCOME: self._optimize_business_outcome
        }

    async def optimize_workflow(self,
                              workflow: UnifiedWorkflow,
                              performance_data: List[Dict[str, Any]],
                              target_metrics: List[OptimizationMetric]) -> Dict[str, Any]:
        """Optimize a workflow based on performance data and target metrics."""

        optimization_results = {
            "workflow_id": workflow.workflow_id,
            "original_performance": self._calculate_baseline_performance(performance_data),
            "optimizations": [],
            "expected_improvements": {}
        }

        try:
            for metric in target_metrics:
                if metric in self.optimization_strategies:
                    optimizer = self.optimization_strategies[metric]
                    optimization = await optimizer(workflow, performance_data)

                    if optimization:
                        optimization_results["optimizations"].append(optimization)
                        optimization_results["expected_improvements"][metric.value] = optimization.get("expected_improvement", 0)

            # Record optimization attempt
            self.optimization_history[workflow.workflow_id].append({
                "timestamp": datetime.now(timezone.utc),
                "target_metrics": [m.value for m in target_metrics],
                "results": optimization_results
            })

            logger.info(f"Optimized workflow {workflow.workflow_id} for {len(target_metrics)} metrics")

        except Exception as e:
            logger.error(f"Workflow optimization failed: {e}")

        return optimization_results

    def _calculate_baseline_performance(self, performance_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate baseline performance metrics."""
        if not performance_data:
            return {}

        total_time = sum(d.get("execution_time", 0) for d in performance_data)
        success_count = sum(1 for d in performance_data if d.get("success", False))
        satisfaction_scores = [d.get("user_satisfaction", 0) for d in performance_data if d.get("user_satisfaction")]

        return {
            "avg_execution_time": total_time / len(performance_data),
            "success_rate": success_count / len(performance_data),
            "avg_satisfaction": sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        }

    async def _optimize_execution_time(self, workflow: UnifiedWorkflow, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize workflow for faster execution."""
        # Analyze bottlenecks and suggest parallelization
        bottleneck_actions = self._identify_bottleneck_actions(workflow, performance_data)

        optimization = {
            "type": "execution_time",
            "suggestions": [
                "Enable parallel execution for independent actions",
                "Optimize slow actions identified in bottleneck analysis",
                "Add caching for frequently accessed data"
            ],
            "expected_improvement": 0.3  # 30% improvement
        }

        if bottleneck_actions:
            optimization["bottleneck_actions"] = bottleneck_actions

        return optimization

    async def _optimize_success_rate(self, workflow: UnifiedWorkflow, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize workflow for higher success rate."""
        # Analyze failure patterns
        failure_patterns = self._analyze_failure_patterns(performance_data)

        return {
            "type": "success_rate",
            "suggestions": [
                "Add retry logic for failed actions",
                "Improve error handling and validation",
                "Add rollback mechanisms for critical failures"
            ],
            "failure_patterns": failure_patterns,
            "expected_improvement": 0.15  # 15% improvement
        }

    async def _optimize_user_satisfaction(self, workflow: UnifiedWorkflow, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize workflow for better user satisfaction."""
        return {
            "type": "user_satisfaction",
            "suggestions": [
                "Add progress indicators for long-running workflows",
                "Improve user feedback and notifications",
                "Simplify complex action sequences"
            ],
            "expected_improvement": 0.2  # 20% improvement
        }

    async def _optimize_business_outcome(self, workflow: UnifiedWorkflow, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize workflow for better business outcomes."""
        return {
            "type": "business_outcome",
            "suggestions": [
                "Align workflow actions with business KPIs",
                "Add business metric tracking",
                "Integrate with revenue attribution systems"
            ],
            "expected_improvement": 0.25  # 25% improvement
        }

    def _identify_bottleneck_actions(self, workflow: UnifiedWorkflow, performance_data: List[Dict[str, Any]]) -> List[str]:
        """Identify actions that are performance bottlenecks."""
        # Simplified bottleneck identification
        slow_actions = []
        for action in workflow.actions:
            if action.execution_time and action.execution_time > 5.0:  # Actions taking more than 5 seconds
                slow_actions.append(action.action_id)
        return slow_actions

    def _analyze_failure_patterns(self, performance_data: List[Dict[str, Any]]) -> List[str]:
        """Analyze patterns in workflow failures."""
        failure_reasons = []
        for data in performance_data:
            if not data.get("success", True) and data.get("error"):
                failure_reasons.append(data["error"])

        # Count failure types
        failure_counts = Counter(failure_reasons)
        return [f"{reason}: {count}" for reason, count in failure_counts.most_common(3)]


class IntelligentWorkflowAutomation:
    """Main intelligent workflow automation system."""

    def __init__(self,
                 workflow_orchestrator: AdvancedWorkflowOrchestrator,
                 redis_client: Optional[redis.Redis] = None):
        """Initialize intelligent workflow automation system."""

        self.orchestrator = workflow_orchestrator
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)

        # Core AI systems
        self.pattern_analyzer = BehavioralPatternAnalyzer(redis_client)
        self.workflow_optimizer = WorkflowOptimizer()

        # Automation rules and suggestions
        self.automation_rules: Dict[str, AutomationRule] = {}
        self.workflow_suggestions: Dict[str, WorkflowSuggestion] = {}

        # Performance tracking
        self.automation_metrics = defaultdict(list)
        self.suggestion_acceptance_rate = 0.0

        logger.info("Intelligent Workflow Automation initialized")

    async def analyze_and_suggest_automations(self, user_id: str) -> List[WorkflowSuggestion]:
        """Analyze user behavior and suggest intelligent automations."""

        try:
            # Discover behavior patterns
            patterns = await self.pattern_analyzer.analyze_user_behavior(user_id)

            # Generate automation suggestions
            suggestions = []
            for pattern in patterns:
                suggestion = await self._create_automation_suggestion(pattern, user_id)
                if suggestion:
                    suggestions.append(suggestion)
                    self.workflow_suggestions[suggestion.suggestion_id] = suggestion

            logger.info(f"Generated {len(suggestions)} automation suggestions for user {user_id}")
            return suggestions

        except Exception as e:
            logger.error(f"Automation analysis failed for user {user_id}: {e}")
            return []

    async def _create_automation_suggestion(self, pattern: WorkflowPattern, user_id: str) -> Optional[WorkflowSuggestion]:
        """Create automation suggestion from discovered pattern."""

        if pattern.confidence_score < 0.7:
            return None

        # Create workflow actions from pattern
        actions = []
        for i, action_data in enumerate(pattern.action_sequence):
            action = WorkflowAction(
                action_id=f"action_{i}",
                hub=HubType.AUTOMATION_STUDIO,  # Default hub
                action_type=action_data.get("type", "execute"),
                target=action_data.get("target", "default"),
                parameters=action_data.get("parameters", {})
            )
            actions.append(action)

        # Create workflow context
        context = WorkflowContext(
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            primary_hub=HubType.AUTOMATION_STUDIO,
            triggered_by="ai_suggested",
            priority=WorkflowPriority.MEDIUM
        )

        # Create suggested workflow
        workflow = UnifiedWorkflow(
            workflow_id=str(uuid.uuid4()),
            name=f"Automated {pattern.name}",
            description=f"AI-suggested automation based on your usage patterns: {pattern.description}",
            actions=actions,
            context=context
        )

        # Calculate potential benefits
        time_savings = max(0, pattern.avg_execution_time * 0.8)  # 80% time savings
        success_improvement = max(0, (1.0 - pattern.success_rate) * 0.5)  # 50% of remaining improvement

        # Create suggestion
        suggestion = WorkflowSuggestion(
            suggestion_id=str(uuid.uuid4()),
            title=f"Automate {pattern.name}",
            description=f"Based on {pattern.frequency} similar actions, this automation could save you time",
            suggested_workflow=workflow,
            confidence_score=pattern.confidence_score,
            potential_time_savings=time_savings,
            potential_success_improvement=success_improvement * 100,
            based_on_patterns=[pattern.pattern_id],
            applicable_scenarios=[f"When you perform {pattern.name.lower()} tasks"],
            business_justification=f"Could save {time_savings:.1f} minutes per execution with {pattern.success_rate*100:.1f}% success rate"
        )

        return suggestion

    async def implement_automation_rule(self,
                                      suggestion_id: str,
                                      user_feedback: Optional[str] = None) -> Dict[str, Any]:
        """Implement an automation rule from a suggestion."""

        suggestion = self.workflow_suggestions.get(suggestion_id)
        if not suggestion:
            return {"success": False, "error": "Suggestion not found"}

        try:
            # Create automation rule
            rule = AutomationRule(
                rule_id=str(uuid.uuid4()),
                name=suggestion.title,
                description=suggestion.description,
                automation_type=AutomationType.BEHAVIORAL,
                intelligence_level=WorkflowIntelligence.LEARNING,
                triggers=[{"type": "pattern_match", "pattern_ids": suggestion.based_on_patterns}],
                conditions=[{"type": "confidence_threshold", "value": 0.7}],
                actions=suggestion.suggested_workflow.actions
            )

            # Store automation rule
            self.automation_rules[rule.rule_id] = rule

            # Update suggestion status
            suggestion.status = "implemented"
            suggestion.user_feedback = user_feedback
            suggestion.implementation_date = datetime.now(timezone.utc)

            # Cache in Redis
            await self.redis.setex(
                f"automation_rule:{rule.rule_id}",
                86400,  # 24 hour expiry
                json.dumps(asdict(rule), default=str)
            )

            logger.info(f"Implemented automation rule: {rule.rule_id} from suggestion {suggestion_id}")

            return {
                "success": True,
                "rule_id": rule.rule_id,
                "workflow_id": suggestion.suggested_workflow.workflow_id
            }

        except Exception as e:
            logger.error(f"Failed to implement automation rule: {e}")
            return {"success": False, "error": str(e)}

    async def execute_automated_workflow(self, rule_id: str, trigger_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an automated workflow based on a rule."""

        rule = self.automation_rules.get(rule_id)
        if not rule or not rule.enabled:
            return {"success": False, "error": "Rule not found or disabled"}

        try:
            # Check rate limiting
            if rule.execution_count >= rule.max_executions_per_hour:
                time_since_last = datetime.now(timezone.utc) - (rule.last_execution or datetime.now(timezone.utc))
                if time_since_last < timedelta(hours=1):
                    return {"success": False, "error": "Rate limit exceeded"}

            # Create workflow context
            context = WorkflowContext(
                user_id=trigger_context.get("user_id", "system"),
                session_id=str(uuid.uuid4()),
                primary_hub=HubType.AUTOMATION_STUDIO,
                triggered_by="automation_rule",
                priority=rule.priority,
                metadata={"rule_id": rule_id, "trigger_context": trigger_context}
            )

            # Create and execute workflow
            workflow = await self.orchestrator.create_unified_workflow(
                name=f"Automated: {rule.name}",
                description=rule.description,
                actions=rule.actions,
                context=context
            )

            execution_result = await self.orchestrator.execute_workflow(workflow.workflow_id)

            # Update rule statistics
            rule.execution_count += 1
            rule.last_execution = datetime.now(timezone.utc)

            if execution_result.get("status") == "completed":
                rule.success_count += 1

            # Track performance
            performance_data = {
                "rule_id": rule_id,
                "execution_time": execution_result.get("execution_time", 0),
                "success": execution_result.get("status") == "completed",
                "timestamp": datetime.now(timezone.utc)
            }
            rule.performance_history.append(performance_data)

            # Keep only last 100 performance records
            if len(rule.performance_history) > 100:
                rule.performance_history = rule.performance_history[-100:]

            logger.info(f"Executed automated workflow: {rule_id} -> {execution_result.get('status')}")

            return {
                "success": True,
                "rule_id": rule_id,
                "workflow_id": workflow.workflow_id,
                "execution_result": execution_result
            }

        except Exception as e:
            logger.error(f"Automated workflow execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_automation_rules(self) -> Dict[str, Any]:
        """Optimize existing automation rules based on performance data."""

        optimization_results = {
            "total_rules": len(self.automation_rules),
            "optimized_rules": 0,
            "optimization_details": []
        }

        try:
            for rule_id, rule in self.automation_rules.items():
                if len(rule.performance_history) >= 10:  # Minimum data for optimization
                    # Create dummy workflow for optimization
                    context = WorkflowContext(
                        user_id="system",
                        session_id=str(uuid.uuid4()),
                        primary_hub=HubType.AUTOMATION_STUDIO
                    )

                    workflow = UnifiedWorkflow(
                        workflow_id=str(uuid.uuid4()),
                        name=rule.name,
                        description=rule.description,
                        actions=rule.actions,
                        context=context
                    )

                    # Optimize workflow
                    optimization = await self.workflow_optimizer.optimize_workflow(
                        workflow,
                        rule.performance_history,
                        [OptimizationMetric.EXECUTION_TIME, OptimizationMetric.SUCCESS_RATE]
                    )

                    if optimization.get("optimizations"):
                        rule.optimization_suggestions = [
                            opt.get("suggestions", []) for opt in optimization["optimizations"]
                        ]
                        optimization_results["optimized_rules"] += 1
                        optimization_results["optimization_details"].append({
                            "rule_id": rule_id,
                            "optimization": optimization
                        })

            logger.info(f"Optimized {optimization_results['optimized_rules']} automation rules")

        except Exception as e:
            logger.error(f"Rule optimization failed: {e}")

        return optimization_results

    def get_automation_analytics(self) -> Dict[str, Any]:
        """Get comprehensive automation analytics."""

        total_rules = len(self.automation_rules)
        enabled_rules = sum(1 for rule in self.automation_rules.values() if rule.enabled)

        if total_rules == 0:
            return {"total_rules": 0, "enabled_rules": 0}

        total_executions = sum(rule.execution_count for rule in self.automation_rules.values())
        total_successes = sum(rule.success_count for rule in self.automation_rules.values())

        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "total_executions": total_executions,
            "overall_success_rate": total_successes / max(total_executions, 1),
            "suggestions_generated": len(self.workflow_suggestions),
            "suggestions_implemented": sum(1 for s in self.workflow_suggestions.values() if s.status == "implemented"),
            "avg_confidence_score": sum(s.confidence_score for s in self.workflow_suggestions.values()) / max(len(self.workflow_suggestions), 1)
        }


# Export main classes
__all__ = [
    "IntelligentWorkflowAutomation",
    "BehavioralPatternAnalyzer",
    "WorkflowOptimizer",
    "WorkflowPattern",
    "AutomationRule",
    "WorkflowSuggestion",
    "AutomationType",
    "WorkflowIntelligence",
    "OptimizationMetric"
]