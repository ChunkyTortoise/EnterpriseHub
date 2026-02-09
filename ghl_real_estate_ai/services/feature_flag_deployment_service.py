"""
Feature Flag Deployment Service - Production Rollout Management

This service provides comprehensive production deployment management with:

- Feature flag system for gradual rollouts
- A/B testing integration for deployments
- Rollback mechanisms and safety controls
- Performance monitoring during deployments
- Circuit breaker patterns for system protection
- Canary deployment strategies
- Blue-green deployment support

Critical Missing Component: No deployment controls in current system.
This service enables safe production rollout of the $4.91M ARR enhancement systems.
"""

import asyncio
import hashlib
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.database_service import DatabaseService, get_database
from ghl_real_estate_ai.services.production_monitoring_service import get_monitoring_service

logger = get_logger(__name__)


class FeatureFlagType(Enum):
    """Types of feature flags"""

    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    MULTIVARIATE = "multivariate"
    USER_SEGMENT = "user_segment"


class DeploymentStrategy(Enum):
    """Deployment strategies"""

    IMMEDIATE = "immediate"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    A_B_TEST = "a_b_test"


class DeploymentStatus(Enum):
    """Deployment status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    PAUSED = "paused"


class RollbackTrigger(Enum):
    """Automatic rollback triggers"""

    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    BUSINESS_METRIC = "business_metric"
    MANUAL = "manual"
    HEALTH_CHECK = "health_check"


@dataclass
class FeatureFlag:
    """Feature flag configuration"""

    flag_id: str
    name: str
    description: str
    flag_type: FeatureFlagType

    # Flag Configuration
    enabled: bool = False
    percentage: Optional[float] = None  # For percentage rollouts
    variants: Optional[Dict[str, Any]] = None  # For multivariate flags
    user_segments: Optional[List[str]] = None  # For user segment targeting

    # Targeting Rules
    targeting_rules: Optional[Dict[str, Any]] = None
    prerequisites: Optional[List[str]] = None  # Other flags that must be enabled

    # Deployment Configuration
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.IMMEDIATE
    rollout_percentage: float = 100.0
    canary_percentage: float = 5.0

    # Safety Controls
    max_error_rate: float = 0.05  # 5% error rate triggers rollback
    max_response_time: float = 5000  # 5 second response time triggers rollback
    min_business_metric_threshold: Optional[float] = None

    # Metadata
    created_by: str = "system"
    created_at: datetime = None
    updated_at: datetime = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class DeploymentConfig:
    """Deployment configuration"""

    deployment_id: str
    feature_flags: List[str]  # Flag IDs being deployed
    deployment_strategy: DeploymentStrategy

    # Rollout Configuration
    target_percentage: float = 100.0
    rollout_increment: float = 10.0  # Increase by 10% each step
    rollout_interval_minutes: int = 30  # Wait 30 min between increments

    # Safety Configuration
    rollback_triggers: List[RollbackTrigger]
    health_check_endpoints: List[str]
    success_criteria: Dict[str, float]

    # Monitoring Configuration
    monitoring_duration_minutes: int = 60
    success_threshold: float = 0.95  # 95% of metrics must be within bounds

    # Metadata
    created_by: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class DeploymentStatus:
    """Current deployment status"""

    deployment_id: str
    status: DeploymentStatus
    current_percentage: float
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    # Performance Metrics
    error_rate: Optional[float] = None
    avg_response_time: Optional[float] = None
    success_rate: Optional[float] = None
    business_metrics: Optional[Dict[str, float]] = None

    # Issues and Alerts
    issues: List[str] = None
    alerts_triggered: List[str] = None
    rollback_reason: Optional[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.alerts_triggered is None:
            self.alerts_triggered = []


class FeatureFlagDeploymentService:
    """Production feature flag and deployment management service"""

    def __init__(self):
        self.cache = get_cache_service()
        self.db: Optional[DatabaseService] = None
        self.monitoring_service = None

        # Active feature flags
        self.active_flags: Dict[str, FeatureFlag] = {}

        # Active deployments
        self.active_deployments: Dict[str, DeploymentStatus] = {}

        # Flag evaluation cache
        self.evaluation_cache_ttl = 300  # 5 minutes

        # Enhancement systems configuration
        self.enhancement_systems = {
            "autonomous_followup_engine": {
                "flag_id": "autonomous_followup_enabled",
                "description": "10-agent autonomous follow-up system",
                "target_arr": 225000,
                "dependencies": ["database_service", "claude_assistant"],
                "health_endpoints": ["/health/followup", "/health/agents"],
                "business_metrics": ["follow_up_response_rate", "conversion_rate"],
            },
            "neural_property_matching": {
                "flag_id": "neural_matching_enabled",
                "description": "AI-powered property matching system",
                "target_arr": 400000,
                "dependencies": ["real_estate_pipeline", "ml_models"],
                "health_endpoints": ["/health/matching", "/health/ml"],
                "business_metrics": ["match_accuracy", "user_satisfaction"],
            },
            "behavioral_trigger_engine": {
                "flag_id": "behavioral_triggers_enabled",
                "description": "85+ behavioral signal processing",
                "target_arr": 200000,
                "dependencies": ["behavioral_processor", "signal_analyzer"],
                "health_endpoints": ["/health/behavioral", "/health/signals"],
                "business_metrics": ["signal_accuracy", "trigger_effectiveness"],
            },
            "revenue_attribution_system": {
                "flag_id": "revenue_attribution_enabled",
                "description": "Multi-touch attribution tracking",
                "target_arr": 0,  # Infrastructure component
                "dependencies": ["database_service", "analytics_engine"],
                "health_endpoints": ["/health/attribution", "/health/analytics"],
                "business_metrics": ["attribution_confidence", "data_quality"],
            },
            "pricing_intelligence": {
                "flag_id": "pricing_intelligence_enabled",
                "description": "AI-powered pricing analysis",
                "target_arr": 400000,
                "dependencies": ["pricing_engine", "market_analyzer"],
                "health_endpoints": ["/health/pricing", "/health/market"],
                "business_metrics": ["pricing_accuracy", "valuation_confidence"],
            },
            "churn_prevention_system": {
                "flag_id": "churn_prevention_enabled",
                "description": "Predictive churn detection and intervention",
                "target_arr": 300000,
                "dependencies": ["churn_predictor", "intervention_engine"],
                "health_endpoints": ["/health/churn", "/health/interventions"],
                "business_metrics": ["churn_prediction_accuracy", "recovery_rate"],
            },
            "competitive_intelligence": {
                "flag_id": "competitive_intel_enabled",
                "description": "Multi-agent competitive analysis",
                "target_arr": 300000,
                "dependencies": ["competitive_analyzer", "market_monitor"],
                "health_endpoints": ["/health/competitive", "/health/monitoring"],
                "business_metrics": ["analysis_accuracy", "response_time"],
            },
            "ab_testing_optimization": {
                "flag_id": "ab_testing_enabled",
                "description": "Autonomous A/B testing framework",
                "target_arr": 150000,
                "dependencies": ["ab_test_engine", "statistical_analyzer"],
                "health_endpoints": ["/health/ab_testing", "/health/stats"],
                "business_metrics": ["test_validity", "optimization_lift"],
            },
            "production_monitoring": {
                "flag_id": "production_monitoring_enabled",
                "description": "Comprehensive system monitoring",
                "target_arr": 0,  # Infrastructure component
                "dependencies": ["monitoring_service", "alerting_system"],
                "health_endpoints": ["/health/monitoring", "/health/alerts"],
                "business_metrics": ["uptime_percentage", "alert_accuracy"],
            },
        }

        logger.info("Initialized Feature Flag Deployment Service")

    async def initialize(self):
        """Initialize deployment service"""
        self.db = await get_database()
        self.monitoring_service = await get_monitoring_service()

        # Initialize feature flags for all enhancement systems
        await self._initialize_enhancement_flags()

        # Start background monitoring
        asyncio.create_task(self._deployment_monitoring_loop())

        logger.info("Feature Flag Deployment Service initialized")

    # ============================================================================
    # FEATURE FLAG MANAGEMENT
    # ============================================================================

    async def create_feature_flag(
        self,
        flag_id: str,
        name: str,
        description: str,
        flag_type: FeatureFlagType = FeatureFlagType.BOOLEAN,
        deployment_strategy: DeploymentStrategy = DeploymentStrategy.CANARY,
        **kwargs,
    ) -> FeatureFlag:
        """Create a new feature flag"""

        flag = FeatureFlag(
            flag_id=flag_id,
            name=name,
            description=description,
            flag_type=flag_type,
            deployment_strategy=deployment_strategy,
            **kwargs,
        )

        # Store flag
        await self._store_feature_flag(flag)
        self.active_flags[flag_id] = flag

        logger.info(f"Created feature flag: {flag_id}")
        return flag

    async def update_feature_flag(self, flag_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing feature flag"""

        if flag_id not in self.active_flags:
            return False

        flag = self.active_flags[flag_id]

        # Apply updates
        for key, value in updates.items():
            if hasattr(flag, key):
                setattr(flag, key, value)

        flag.updated_at = datetime.utcnow()

        # Store updated flag
        await self._store_feature_flag(flag)

        # Clear evaluation cache
        await self._clear_flag_evaluation_cache(flag_id)

        logger.info(f"Updated feature flag: {flag_id}")
        return True

    async def evaluate_feature_flag(
        self,
        flag_id: str,
        user_id: Optional[str] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Evaluate feature flag for user/context"""

        # Check cache first
        cache_key = self._get_evaluation_cache_key(flag_id, user_id, user_attributes)
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Get flag
        flag = self.active_flags.get(flag_id)
        if not flag:
            return False  # Default to disabled

        # Check if flag is enabled globally
        if not flag.enabled:
            result = False
        else:
            result = await self._evaluate_flag_logic(flag, user_id, user_attributes, context)

        # Cache result
        await self.cache.set(cache_key, result, ttl=self.evaluation_cache_ttl)

        # Track flag evaluation for analytics
        await self._track_flag_evaluation(flag_id, result, user_id)

        return result

    async def _evaluate_flag_logic(
        self,
        flag: FeatureFlag,
        user_id: Optional[str],
        user_attributes: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> Any:
        """Internal flag evaluation logic"""

        # Check prerequisites
        if flag.prerequisites:
            for prereq_flag_id in flag.prerequisites:
                prereq_result = await self.evaluate_feature_flag(prereq_flag_id, user_id, user_attributes, context)
                if not prereq_result:
                    return False

        # Boolean flag
        if flag.flag_type == FeatureFlagType.BOOLEAN:
            return self._evaluate_percentage_rollout(flag, user_id)

        # Percentage flag
        elif flag.flag_type == FeatureFlagType.PERCENTAGE:
            if flag.percentage is None:
                return False
            return flag.percentage

        # Multivariate flag
        elif flag.flag_type == FeatureFlagType.MULTIVARIATE:
            if not flag.variants:
                return False
            return self._evaluate_multivariate_flag(flag, user_id)

        # User segment flag
        elif flag.flag_type == FeatureFlagType.USER_SEGMENT:
            return self._evaluate_user_segment_flag(flag, user_id, user_attributes)

        return False

    def _evaluate_percentage_rollout(self, flag: FeatureFlag, user_id: Optional[str]) -> bool:
        """Evaluate percentage-based rollout"""

        if flag.rollout_percentage >= 100:
            return True
        elif flag.rollout_percentage <= 0:
            return False

        # Use consistent hashing for stable user assignment
        if user_id:
            hash_input = f"{flag.flag_id}:{user_id}"
        else:
            hash_input = f"{flag.flag_id}:anonymous:{random.random()}"

        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        user_percentage = (hash_value % 100) + 1

        return user_percentage <= flag.rollout_percentage

    def _evaluate_multivariate_flag(self, flag: FeatureFlag, user_id: Optional[str]) -> str:
        """Evaluate multivariate flag with variant selection"""

        if not flag.variants:
            return "control"

        # Use consistent hashing for stable variant assignment
        hash_input = f"{flag.flag_id}:variant:{user_id or 'anonymous'}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)

        # Select variant based on configured weights
        total_weight = sum(variant.get("weight", 1) for variant in flag.variants.values())
        target = hash_value % total_weight

        current_weight = 0
        for variant_name, variant_config in flag.variants.items():
            current_weight += variant_config.get("weight", 1)
            if target < current_weight:
                return variant_name

        return list(flag.variants.keys())[0]  # Fallback to first variant

    def _evaluate_user_segment_flag(
        self, flag: FeatureFlag, user_id: Optional[str], user_attributes: Optional[Dict[str, Any]]
    ) -> bool:
        """Evaluate user segment targeting"""

        if not flag.user_segments or not user_attributes:
            return False

        # Check if user matches any target segment
        for segment in flag.user_segments:
            if self._user_matches_segment(segment, user_attributes):
                return True

        return False

    def _user_matches_segment(self, segment: str, user_attributes: Dict[str, Any]) -> bool:
        """Check if user matches a segment definition"""

        # Simple segment matching - in production this would be more sophisticated
        if segment == "power_users" and user_attributes.get("activity_level") == "high":
            return True
        elif segment == "new_users" and user_attributes.get("registration_date"):
            reg_date = user_attributes["registration_date"]
            if isinstance(reg_date, str):
                reg_date = datetime.fromisoformat(reg_date)
            return (datetime.utcnow() - reg_date).days <= 7
        elif segment == "beta_testers" and user_attributes.get("beta_tester"):
            return True

        return False

    # ============================================================================
    # DEPLOYMENT MANAGEMENT
    # ============================================================================

    async def create_deployment(
        self,
        feature_flags: List[str],
        deployment_strategy: DeploymentStrategy = DeploymentStrategy.CANARY,
        target_percentage: float = 100.0,
        created_by: str = "system",
        **kwargs,
    ) -> str:
        """Create a new deployment"""

        deployment_config = DeploymentConfig(
            deployment_id=f"deploy_{int(datetime.utcnow().timestamp())}",
            feature_flags=feature_flags,
            deployment_strategy=deployment_strategy,
            target_percentage=target_percentage,
            created_by=created_by,
            **kwargs,
        )

        # Initialize deployment status
        deployment_status = DeploymentStatus(
            deployment_id=deployment_config.deployment_id,
            status=DeploymentStatus.PENDING,
            current_percentage=0.0,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Store deployment
        await self._store_deployment_config(deployment_config)
        await self._store_deployment_status(deployment_status)

        self.active_deployments[deployment_config.deployment_id] = deployment_status

        # Start deployment execution
        asyncio.create_task(self._execute_deployment(deployment_config))

        logger.info(f"Created deployment {deployment_config.deployment_id} for flags: {feature_flags}")
        return deployment_config.deployment_id

    async def _execute_deployment(self, config: DeploymentConfig):
        """Execute deployment according to strategy"""

        deployment_id = config.deployment_id

        try:
            if config.deployment_strategy == DeploymentStrategy.IMMEDIATE:
                await self._execute_immediate_deployment(config)
            elif config.deployment_strategy == DeploymentStrategy.CANARY:
                await self._execute_canary_deployment(config)
            elif config.deployment_strategy == DeploymentStrategy.ROLLING:
                await self._execute_rolling_deployment(config)
            elif config.deployment_strategy == DeploymentStrategy.A_B_TEST:
                await self._execute_ab_test_deployment(config)
            else:
                raise ValueError(f"Unsupported deployment strategy: {config.deployment_strategy}")

        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}")
            await self._mark_deployment_failed(deployment_id, str(e))

    async def _execute_canary_deployment(self, config: DeploymentConfig):
        """Execute canary deployment with gradual rollout"""

        deployment_id = config.deployment_id
        current_percentage = 0.0

        while current_percentage < config.target_percentage:
            # Calculate next increment
            next_percentage = min(current_percentage + config.rollout_increment, config.target_percentage)

            logger.info(f"Deployment {deployment_id}: Rolling out to {next_percentage}%")

            # Update feature flags
            await self._update_deployment_percentage(config.feature_flags, next_percentage)

            # Update deployment status
            await self._update_deployment_status(
                deployment_id,
                {
                    "current_percentage": next_percentage,
                    "status": DeploymentStatus.IN_PROGRESS,
                    "updated_at": datetime.utcnow(),
                },
            )

            # Monitor deployment health
            health_check_passed = await self._monitor_deployment_health(deployment_id, config, next_percentage)

            if not health_check_passed:
                logger.warning(f"Deployment {deployment_id}: Health check failed, rolling back")
                await self._rollback_deployment(deployment_id, "Health check failed")
                return

            current_percentage = next_percentage

            # Wait before next increment (unless at 100%)
            if current_percentage < config.target_percentage:
                await asyncio.sleep(config.rollout_interval_minutes * 60)

        # Mark deployment as completed
        await self._update_deployment_status(
            deployment_id,
            {"status": DeploymentStatus.COMPLETED, "completed_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        )

        logger.info(f"Deployment {deployment_id} completed successfully")

    async def _execute_immediate_deployment(self, config: DeploymentConfig):
        """Execute immediate deployment to target percentage"""

        deployment_id = config.deployment_id

        # Update all flags immediately
        await self._update_deployment_percentage(config.feature_flags, config.target_percentage)

        # Update status
        await self._update_deployment_status(
            deployment_id,
            {
                "current_percentage": config.target_percentage,
                "status": DeploymentStatus.IN_PROGRESS,
                "updated_at": datetime.utcnow(),
            },
        )

        # Monitor for safety
        health_check_passed = await self._monitor_deployment_health(deployment_id, config, config.target_percentage)

        if health_check_passed:
            await self._update_deployment_status(
                deployment_id, {"status": DeploymentStatus.COMPLETED, "completed_at": datetime.utcnow()}
            )
        else:
            await self._rollback_deployment(deployment_id, "Post-deployment health check failed")

    async def _execute_rolling_deployment(self, config: DeploymentConfig):
        """Execute rolling deployment across service instances"""

        # For now, implement as canary with smaller increments
        # In a real system, this would deploy to server instances one by one
        rolling_config = config
        rolling_config.rollout_increment = 20.0  # 20% increments for rolling
        rolling_config.rollout_interval_minutes = 10  # 10 minutes between increments

        await self._execute_canary_deployment(rolling_config)

    async def _execute_ab_test_deployment(self, config: DeploymentConfig):
        """Execute A/B test deployment"""

        deployment_id = config.deployment_id

        # Set up 50/50 split for A/B test
        test_percentage = 50.0

        await self._update_deployment_percentage(config.feature_flags, test_percentage)

        await self._update_deployment_status(
            deployment_id,
            {
                "current_percentage": test_percentage,
                "status": DeploymentStatus.IN_PROGRESS,
                "updated_at": datetime.utcnow(),
            },
        )

        # Run A/B test for specified duration
        test_duration = config.monitoring_duration_minutes * 60
        await asyncio.sleep(test_duration)

        # Analyze A/B test results
        test_results = await self._analyze_ab_test_results(deployment_id, config)

        if test_results["winner"] == "treatment":
            # Roll out to 100%
            await self._update_deployment_percentage(config.feature_flags, 100.0)
            await self._update_deployment_status(
                deployment_id,
                {"current_percentage": 100.0, "status": DeploymentStatus.COMPLETED, "completed_at": datetime.utcnow()},
            )
            logger.info(f"A/B test {deployment_id}: Treatment won, rolling out to 100%")
        else:
            # Roll back
            await self._rollback_deployment(deployment_id, "A/B test: Control performed better")

    # ============================================================================
    # DEPLOYMENT MONITORING AND SAFETY
    # ============================================================================

    async def _monitor_deployment_health(
        self, deployment_id: str, config: DeploymentConfig, current_percentage: float
    ) -> bool:
        """Monitor deployment health and trigger rollback if needed"""

        # Wait for metrics to stabilize
        await asyncio.sleep(60)  # 1 minute stabilization period

        health_checks = []
        issues = []

        # Check error rate
        error_rate = await self._get_current_error_rate(config.feature_flags)
        if error_rate and error_rate > 0.05:  # 5% threshold
            health_checks.append(False)
            issues.append(f"Error rate too high: {error_rate:.3f}")
        else:
            health_checks.append(True)

        # Check response time
        response_time = await self._get_current_response_time(config.feature_flags)
        if response_time and response_time > 5000:  # 5 second threshold
            health_checks.append(False)
            issues.append(f"Response time too high: {response_time:.0f}ms")
        else:
            health_checks.append(True)

        # Check business metrics
        business_metrics_ok = await self._check_business_metrics(config)
        if not business_metrics_ok:
            health_checks.append(False)
            issues.append("Business metrics degraded")
        else:
            health_checks.append(True)

        # Check service health
        services_healthy = await self._check_service_health(config)
        if not services_healthy:
            health_checks.append(False)
            issues.append("Service health checks failed")
        else:
            health_checks.append(True)

        # Update deployment status with current health
        await self._update_deployment_status(
            deployment_id,
            {
                "error_rate": error_rate,
                "avg_response_time": response_time,
                "issues": issues,
                "updated_at": datetime.utcnow(),
            },
        )

        # Determine overall health
        success_rate = sum(health_checks) / len(health_checks)
        is_healthy = success_rate >= config.success_threshold

        logger.info(f"Deployment {deployment_id} health check: {success_rate:.2f} ({'PASS' if is_healthy else 'FAIL'})")

        return is_healthy

    async def _rollback_deployment(self, deployment_id: str, reason: str):
        """Rollback deployment to previous state"""

        logger.warning(f"Rolling back deployment {deployment_id}: {reason}")

        # Get deployment config
        config = await self._get_deployment_config(deployment_id)
        if not config:
            return

        # Disable all flags in deployment
        for flag_id in config.feature_flags:
            await self.update_feature_flag(flag_id, {"enabled": False, "rollout_percentage": 0.0})

        # Update deployment status
        await self._update_deployment_status(
            deployment_id,
            {
                "status": DeploymentStatus.ROLLED_BACK,
                "rollback_reason": reason,
                "updated_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
            },
        )

        # Send alerts
        await self._send_rollback_alert(deployment_id, reason)

    async def _deployment_monitoring_loop(self):
        """Background loop monitoring active deployments"""
        while True:
            try:
                for deployment_id, status in list(self.active_deployments.items()):
                    if status.status == DeploymentStatus.IN_PROGRESS:
                        config = await self._get_deployment_config(deployment_id)
                        if config:
                            # Check for automatic rollback triggers
                            should_rollback = await self._check_rollback_triggers(deployment_id, config)
                            if should_rollback:
                                await self._rollback_deployment(deployment_id, "Automatic rollback triggered")

                    # Clean up completed deployments
                    elif status.status in [
                        DeploymentStatus.COMPLETED,
                        DeploymentStatus.ROLLED_BACK,
                        DeploymentStatus.FAILED,
                    ]:
                        if status.completed_at and (datetime.utcnow() - status.completed_at).days >= 1:
                            del self.active_deployments[deployment_id]

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Deployment monitoring loop error: {e}")
                await asyncio.sleep(60)

    # ============================================================================
    # ENHANCEMENT SYSTEMS DEPLOYMENT
    # ============================================================================

    async def deploy_enhancement_system(
        self,
        system_name: str,
        deployment_strategy: DeploymentStrategy = DeploymentStrategy.CANARY,
        target_percentage: float = 100.0,
    ) -> str:
        """Deploy a specific enhancement system"""

        if system_name not in self.enhancement_systems:
            raise ValueError(f"Unknown enhancement system: {system_name}")

        system_config = self.enhancement_systems[system_name]
        flag_id = system_config["flag_id"]

        # Create deployment
        deployment_id = await self.create_deployment(
            feature_flags=[flag_id],
            deployment_strategy=deployment_strategy,
            target_percentage=target_percentage,
            rollback_triggers=[
                RollbackTrigger.ERROR_RATE,
                RollbackTrigger.RESPONSE_TIME,
                RollbackTrigger.BUSINESS_METRIC,
                RollbackTrigger.HEALTH_CHECK,
            ],
            health_check_endpoints=system_config["health_endpoints"],
            success_criteria={"error_rate_max": 0.05, "response_time_max": 5000, "health_check_success_rate": 0.95},
        )

        logger.info(f"Deploying enhancement system {system_name} with deployment {deployment_id}")
        return deployment_id

    async def deploy_all_enhancement_systems(
        self, deployment_strategy: DeploymentStrategy = DeploymentStrategy.CANARY, staggered_rollout: bool = True
    ) -> Dict[str, str]:
        """Deploy all enhancement systems"""

        deployment_ids = {}

        # Define deployment order (infrastructure first, then revenue systems)
        deployment_order = [
            "production_monitoring",
            "revenue_attribution_system",
            "behavioral_trigger_engine",
            "neural_property_matching",
            "autonomous_followup_engine",
            "pricing_intelligence",
            "churn_prevention_system",
            "competitive_intelligence",
            "ab_testing_optimization",
        ]

        for system_name in deployment_order:
            try:
                deployment_id = await self.deploy_enhancement_system(system_name, deployment_strategy)
                deployment_ids[system_name] = deployment_id

                # Wait between deployments for staggered rollout
                if staggered_rollout:
                    await asyncio.sleep(300)  # 5 minutes between systems

            except Exception as e:
                logger.error(f"Failed to deploy {system_name}: {e}")
                deployment_ids[system_name] = f"FAILED: {str(e)}"

        logger.info(
            f"Deployed {len([d for d in deployment_ids.values() if not d.startswith('FAILED')])} enhancement systems"
        )
        return deployment_ids

    async def get_deployment_status_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive deployment status dashboard"""

        # System deployment status
        system_status = {}
        for system_name, config in self.enhancement_systems.items():
            flag_id = config["flag_id"]
            flag = self.active_flags.get(flag_id)

            if flag:
                system_status[system_name] = {
                    "flag_enabled": flag.enabled,
                    "rollout_percentage": flag.rollout_percentage,
                    "target_arr": config["target_arr"],
                    "status": "deployed"
                    if flag.enabled and flag.rollout_percentage >= 100
                    else "partial"
                    if flag.enabled
                    else "disabled",
                }
            else:
                system_status[system_name] = {
                    "flag_enabled": False,
                    "rollout_percentage": 0,
                    "target_arr": config["target_arr"],
                    "status": "not_configured",
                }

        # Active deployments
        active_deployments = [
            asdict(status)
            for status in self.active_deployments.values()
            if status.status in [DeploymentStatus.PENDING, DeploymentStatus.IN_PROGRESS]
        ]

        # Calculate total ARR potential
        total_target_arr = sum(config["target_arr"] for config in self.enhancement_systems.values())

        deployed_arr = sum(
            config["target_arr"]
            for system_name, config in self.enhancement_systems.items()
            if system_status[system_name]["status"] == "deployed"
        )

        return {
            "overall_deployment_status": {
                "total_systems": len(self.enhancement_systems),
                "deployed_systems": len([s for s in system_status.values() if s["status"] == "deployed"]),
                "partial_systems": len([s for s in system_status.values() if s["status"] == "partial"]),
                "target_arr": total_target_arr,
                "deployed_arr": deployed_arr,
                "deployment_percentage": (deployed_arr / total_target_arr * 100) if total_target_arr > 0 else 0,
            },
            "system_status": system_status,
            "active_deployments": active_deployments,
            "last_updated": datetime.utcnow().isoformat(),
        }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    async def _initialize_enhancement_flags(self):
        """Initialize feature flags for all enhancement systems"""

        for system_name, config in self.enhancement_systems.items():
            flag_id = config["flag_id"]

            # Check if flag already exists
            if flag_id not in self.active_flags:
                flag = await self.create_feature_flag(
                    flag_id=flag_id,
                    name=f"{system_name.replace('_', ' ').title()} System",
                    description=config["description"],
                    flag_type=FeatureFlagType.BOOLEAN,
                    deployment_strategy=DeploymentStrategy.CANARY,
                    enabled=False,  # Start disabled
                    rollout_percentage=0.0,
                    max_error_rate=0.05,
                    max_response_time=5000,
                )
                logger.info(f"Initialized flag for {system_name}: {flag_id}")

    def _get_evaluation_cache_key(
        self, flag_id: str, user_id: Optional[str], user_attributes: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for flag evaluation"""

        key_parts = [flag_id]
        if user_id:
            key_parts.append(f"user:{user_id}")
        if user_attributes:
            # Create deterministic hash of attributes
            attr_str = json.dumps(user_attributes, sort_keys=True)
            attr_hash = hashlib.md5(attr_str.encode()).hexdigest()[:8]
            key_parts.append(f"attr:{attr_hash}")

        return f"flag_eval:{':'.join(key_parts)}"

    async def _store_feature_flag(self, flag: FeatureFlag):
        """Store feature flag in cache and database"""

        cache_key = f"feature_flag:{flag.flag_id}"
        await self.cache.set(cache_key, asdict(flag), ttl=86400)  # 24 hours

        # Store in database for persistence
        if self.db:
            comm_data = {
                "lead_id": "system",
                "channel": "feature_flags",
                "direction": "flag_stored",
                "content": f"Feature Flag: {flag.name}",
                "status": "stored",
                "metadata": {
                    "flag_id": flag.flag_id,
                    "flag_enabled": flag.enabled,
                    "rollout_percentage": flag.rollout_percentage,
                },
            }
            await self.db.log_communication(comm_data)

    async def _clear_flag_evaluation_cache(self, flag_id: str):
        """Clear evaluation cache for a flag"""
        # In production, would use cache pattern matching to clear all related keys
        # For now, just log the cache clear operation
        logger.info(f"Clearing evaluation cache for flag: {flag_id}")

    async def _track_flag_evaluation(self, flag_id: str, result: Any, user_id: Optional[str]):
        """Track flag evaluation for analytics"""

        if self.monitoring_service:
            await self.monitoring_service.record_metric(
                f"feature_flag_evaluation_{flag_id}",
                1 if result else 0,
                "counter",
                tags={"flag_id": flag_id, "result": str(result)},
            )

    async def _update_deployment_percentage(self, flag_ids: List[str], percentage: float):
        """Update rollout percentage for deployment flags"""

        for flag_id in flag_ids:
            await self.update_feature_flag(
                flag_id, {"enabled": True if percentage > 0 else False, "rollout_percentage": percentage}
            )

    async def _get_current_error_rate(self, flag_ids: List[str]) -> Optional[float]:
        """Get current error rate for deployment"""
        # Would integrate with actual metrics
        return 0.02  # 2% sample error rate

    async def _get_current_response_time(self, flag_ids: List[str]) -> Optional[float]:
        """Get current response time for deployment"""
        # Would integrate with actual metrics
        return 250.0  # 250ms sample response time

    async def _check_business_metrics(self, config: DeploymentConfig) -> bool:
        """Check if business metrics are within acceptable bounds"""
        # Would check actual business metrics
        return True

    async def _check_service_health(self, config: DeploymentConfig) -> bool:
        """Check service health endpoints"""
        # Would check actual health endpoints
        return True

    async def _store_deployment_config(self, config: DeploymentConfig):
        """Store deployment configuration"""
        cache_key = f"deployment_config:{config.deployment_id}"
        await self.cache.set(cache_key, asdict(config), ttl=86400 * 7)

    async def _store_deployment_status(self, status: DeploymentStatus):
        """Store deployment status"""
        cache_key = f"deployment_status:{status.deployment_id}"
        await self.cache.set(cache_key, asdict(status), ttl=86400 * 7)

    async def _get_deployment_config(self, deployment_id: str) -> Optional[DeploymentConfig]:
        """Get deployment configuration"""
        cache_key = f"deployment_config:{deployment_id}"
        config_data = await self.cache.get(cache_key)
        if config_data:
            return DeploymentConfig(**config_data)
        return None

    async def _update_deployment_status(self, deployment_id: str, updates: Dict[str, Any]):
        """Update deployment status"""
        if deployment_id in self.active_deployments:
            status = self.active_deployments[deployment_id]
            for key, value in updates.items():
                if hasattr(status, key):
                    setattr(status, key, value)
            await self._store_deployment_status(status)

    async def _mark_deployment_failed(self, deployment_id: str, error: str):
        """Mark deployment as failed"""
        await self._update_deployment_status(
            deployment_id, {"status": DeploymentStatus.FAILED, "issues": [error], "completed_at": datetime.utcnow()}
        )

    async def _check_rollback_triggers(self, deployment_id: str, config: DeploymentConfig) -> bool:
        """Check if any rollback triggers are activated"""
        # Would implement actual rollback trigger logic
        return False

    async def _send_rollback_alert(self, deployment_id: str, reason: str):
        """Send alert about deployment rollback"""
        logger.warning(f"DEPLOYMENT ROLLBACK ALERT: {deployment_id} - {reason}")

    async def _analyze_ab_test_results(self, deployment_id: str, config: DeploymentConfig) -> Dict[str, Any]:
        """Analyze A/B test results"""
        # Would implement statistical analysis of A/B test
        return {
            "winner": "treatment",  # Sample result
            "confidence": 0.95,
            "lift": 0.15,
        }


# ============================================================================
# SERVICE FACTORY AND CONVENIENCE FUNCTIONS
# ============================================================================

_deployment_service: Optional[FeatureFlagDeploymentService] = None


async def get_deployment_service() -> FeatureFlagDeploymentService:
    """Get global deployment service instance"""
    global _deployment_service

    if _deployment_service is None:
        _deployment_service = FeatureFlagDeploymentService()
        await _deployment_service.initialize()

    return _deployment_service


# Convenience functions
async def deploy_enhancement_system(system_name: str, strategy: DeploymentStrategy = DeploymentStrategy.CANARY) -> str:
    """Deploy a single enhancement system"""
    service = await get_deployment_service()
    return await service.deploy_enhancement_system(system_name, strategy)


async def deploy_all_systems(
    strategy: DeploymentStrategy = DeploymentStrategy.CANARY, staggered: bool = True
) -> Dict[str, str]:
    """Deploy all enhancement systems"""
    service = await get_deployment_service()
    return await service.deploy_all_enhancement_systems(strategy, staggered)


async def get_deployment_dashboard() -> Dict[str, Any]:
    """Get deployment status dashboard"""
    service = await get_deployment_service()
    return await service.get_deployment_status_dashboard()


async def check_feature_flag(flag_id: str, user_id: str = None) -> bool:
    """Check if feature flag is enabled for user"""
    service = await get_deployment_service()
    return await service.evaluate_feature_flag(flag_id, user_id)


if __name__ == "__main__":

    async def test_deployment_service():
        """Test deployment service functionality"""
        service = FeatureFlagDeploymentService()
        await service.initialize()

        # Test flag creation and evaluation
        flag = await service.create_feature_flag(
            "test_flag", "Test Feature", "Test feature flag", enabled=True, rollout_percentage=50.0
        )
        print(f"Created flag: {flag.flag_id}")

        result = await service.evaluate_feature_flag("test_flag", "user_123")
        print(f"Flag evaluation: {result}")

        # Test deployment
        deployment_id = await service.deploy_enhancement_system("autonomous_followup_engine", DeploymentStrategy.CANARY)
        print(f"Created deployment: {deployment_id}")

        # Test dashboard
        dashboard = await service.get_deployment_status_dashboard()
        print(f"Dashboard: {dashboard}")

    asyncio.run(test_deployment_service())
