#!/usr/bin/env python3
"""
Self-Healing System for AI-Enhanced Operations
Automated incident detection, classification, and resolution with ML-driven workflows.

Performance Targets:
- Automated resolution rate: >80% for common issues
- Mean time to recovery (MTTR): <5 minutes
- Resolution accuracy: >90%
- Escalation precision: >95%
"""

import asyncio
import logging
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np

# ML and Data Processing
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Local imports
from ..base import BaseService
from ..logging_config import get_logger

logger = get_logger(__name__)

class IncidentSeverity(Enum):
    """Incident severity levels for triage and escalation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    """Incident lifecycle status tracking."""
    DETECTED = "detected"
    CLASSIFYING = "classifying"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"

class ResolutionAction(Enum):
    """Available automated resolution actions."""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    APPLY_HOTFIX = "apply_hotfix"
    FAILOVER = "failover"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"
    RESET_CONNECTIONS = "reset_connections"

@dataclass(slots=True)
class IncidentMetrics:
    """System metrics at time of incident detection."""
    cpu_usage: np.float32
    memory_usage: np.float32
    disk_usage: np.float32
    network_io: np.float32
    error_rate: np.float32
    response_time: np.float32
    throughput: np.float32
    active_connections: int
    queue_depth: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass(slots=True)
class IncidentContext:
    """Contextual information about the incident environment."""
    service_name: str
    service_version: str
    environment: str  # dev, staging, production
    recent_deployments: List[str]
    related_alerts: List[str]
    dependency_health: Dict[str, str]
    load_pattern: str  # normal, spike, declining
    time_of_day: str  # peak, off_peak
    day_of_week: str

@dataclass(slots=True)
class Incident:
    """Complete incident representation with all data for ML processing."""
    incident_id: str
    service_name: str
    incident_type: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    metrics: IncidentMetrics
    context: IncidentContext
    detected_at: datetime
    classification_confidence: np.float32 = field(default_factory=lambda: np.float32(0.0))
    resolution_confidence: np.float32 = field(default_factory=lambda: np.float32(0.0))
    recommended_actions: List[ResolutionAction] = field(default_factory=list)
    attempted_actions: List[str] = field(default_factory=list)
    resolution_history: List[Dict[str, Any]] = field(default_factory=list)
    escalation_reason: Optional[str] = None

@dataclass(slots=True)
class ResolutionWorkflow:
    """Self-healing workflow with rollback capabilities."""
    workflow_id: str
    incident_id: str
    actions: List[ResolutionAction]
    current_step: int = 0
    success_probability: np.float32 = field(default_factory=lambda: np.float32(0.0))
    rollback_actions: List[str] = field(default_factory=list)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass(slots=True)
class ResolutionResult:
    """Result of automated resolution attempt."""
    workflow_id: str
    incident_id: str
    success: bool
    actions_executed: List[str]
    resolution_time: timedelta
    confidence_score: np.float32
    impact_assessment: Dict[str, Any]
    lessons_learned: List[str]
    require_human_review: bool

class SelfHealingSystem(BaseService):
    """
    Automated incident detection, classification, and resolution system.

    Uses ML models to classify incidents and recommend resolution actions,
    then executes self-healing workflows with rollback capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize self-healing system with ML models and workflows."""
        super().__init__()
        self.config = config or {}

        # Core components
        self.incident_classifier: Optional[RandomForestClassifier] = None
        self.resolution_recommender: Optional[GradientBoostingClassifier] = None
        self.feature_vectorizer: Optional[TfidfVectorizer] = None
        self.scaler: Optional[StandardScaler] = None

        # System state
        self.active_incidents: Dict[str, Incident] = {}
        self.resolution_workflows: Dict[str, ResolutionWorkflow] = {}
        self.incident_history: List[Incident] = []
        self.resolution_knowledge_base: Dict[str, List[str]] = {}

        # Performance tracking
        self.metrics = {
            'incidents_detected': 0,
            'incidents_resolved_automatically': 0,
            'incidents_escalated': 0,
            'average_resolution_time': 0.0,
            'resolution_success_rate': 0.0,
            'false_positive_rate': 0.0
        }

        # Configuration
        self.max_resolution_attempts = self.config.get('max_resolution_attempts', 3)
        self.escalation_threshold = self.config.get('escalation_threshold', 300)  # 5 minutes
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.auto_resolution_enabled = self.config.get('auto_resolution_enabled', True)

        logger.info("Self-healing system initialized")

    async def initialize_ml_models(self) -> bool:
        """Initialize and train ML models for incident classification and resolution."""
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available - using rule-based fallbacks")
            return False

        try:
            # Initialize incident classifier
            self.incident_classifier = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

            # Initialize resolution recommender
            self.resolution_recommender = GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=10,
                min_samples_split=4,
                min_samples_leaf=2,
                random_state=42
            )

            # Initialize text processing
            self.feature_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )

            self.scaler = StandardScaler()

            # Load or train models with synthetic data
            await self._train_models_with_historical_data()

            logger.info("ML models initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")
            return False

    async def _train_models_with_historical_data(self) -> None:
        """Train ML models using historical incident data or synthetic data for initial training."""
        try:
            # Generate synthetic training data for initial model training
            training_data = self._generate_synthetic_training_data()

            if len(training_data) < 100:
                logger.warning("Insufficient training data - using synthetic data")
                training_data.extend(self._generate_additional_synthetic_data(500))

            # Prepare features for incident classification
            features = []
            labels = []
            resolution_labels = []

            for incident_data in training_data:
                # Extract numerical features
                feature_vector = [
                    incident_data['cpu_usage'],
                    incident_data['memory_usage'],
                    incident_data['disk_usage'],
                    incident_data['error_rate'],
                    incident_data['response_time'],
                    incident_data['throughput'],
                    incident_data['is_peak_hour'],
                    incident_data['recent_deployment'],
                    incident_data['dependency_issues']
                ]

                features.append(feature_vector)
                labels.append(incident_data['incident_type'])
                resolution_labels.append(incident_data['best_resolution'])

            # Scale features
            features_scaled = self.scaler.fit_transform(features)

            # Train incident classifier
            self.incident_classifier.fit(features_scaled, labels)

            # Train resolution recommender
            self.resolution_recommender.fit(features_scaled, resolution_labels)

            # Build knowledge base from training data
            self._build_resolution_knowledge_base(training_data)

            logger.info(f"Models trained with {len(training_data)} historical incidents")

        except Exception as e:
            logger.error(f"Failed to train models: {e}")
            raise

    def _generate_synthetic_training_data(self) -> List[Dict[str, Any]]:
        """Generate synthetic training data for initial model training."""
        training_data = []

        # Common incident patterns for Enhanced ML services
        incident_patterns = [
            # High CPU incidents
            {
                'incident_type': 'high_cpu_utilization',
                'cpu_usage': 0.9, 'memory_usage': 0.6, 'disk_usage': 0.3,
                'error_rate': 0.02, 'response_time': 2000, 'throughput': 50,
                'best_resolution': 'scale_up',
                'is_peak_hour': 1, 'recent_deployment': 0, 'dependency_issues': 0
            },
            # Memory leaks
            {
                'incident_type': 'memory_leak',
                'cpu_usage': 0.5, 'memory_usage': 0.95, 'disk_usage': 0.4,
                'error_rate': 0.05, 'response_time': 3000, 'throughput': 30,
                'best_resolution': 'restart_service',
                'is_peak_hour': 0, 'recent_deployment': 1, 'dependency_issues': 0
            },
            # Database connection issues
            {
                'incident_type': 'database_connection_error',
                'cpu_usage': 0.3, 'memory_usage': 0.4, 'disk_usage': 0.2,
                'error_rate': 0.15, 'response_time': 5000, 'throughput': 10,
                'best_resolution': 'reset_connections',
                'is_peak_hour': 1, 'recent_deployment': 0, 'dependency_issues': 1
            },
            # Cache overflow
            {
                'incident_type': 'cache_overflow',
                'cpu_usage': 0.4, 'memory_usage': 0.8, 'disk_usage': 0.9,
                'error_rate': 0.03, 'response_time': 1500, 'throughput': 70,
                'best_resolution': 'clear_cache',
                'is_peak_hour': 1, 'recent_deployment': 0, 'dependency_issues': 0
            },
            # API rate limiting
            {
                'incident_type': 'api_rate_limit_exceeded',
                'cpu_usage': 0.6, 'memory_usage': 0.4, 'disk_usage': 0.3,
                'error_rate': 0.2, 'response_time': 1000, 'throughput': 200,
                'best_resolution': 'circuit_breaker',
                'is_peak_hour': 1, 'recent_deployment': 0, 'dependency_issues': 0
            }
        ]

        # Generate variations of each pattern
        for pattern in incident_patterns:
            for _ in range(20):  # 20 variations per pattern
                variation = pattern.copy()
                # Add noise to make training more robust
                variation['cpu_usage'] += np.random.normal(0, 0.1)
                variation['memory_usage'] += np.random.normal(0, 0.1)
                variation['disk_usage'] += np.random.normal(0, 0.05)
                variation['error_rate'] += np.random.normal(0, 0.01)
                variation['response_time'] += np.random.normal(0, 200)
                variation['throughput'] += np.random.normal(0, 10)

                # Clip values to valid ranges
                variation['cpu_usage'] = np.clip(variation['cpu_usage'], 0, 1)
                variation['memory_usage'] = np.clip(variation['memory_usage'], 0, 1)
                variation['disk_usage'] = np.clip(variation['disk_usage'], 0, 1)
                variation['error_rate'] = np.clip(variation['error_rate'], 0, 1)
                variation['response_time'] = max(variation['response_time'], 50)
                variation['throughput'] = max(variation['throughput'], 1)

                training_data.append(variation)

        return training_data

    def _generate_additional_synthetic_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate additional synthetic data for robust training."""
        additional_data = []

        for _ in range(count):
            # Random incident scenario
            incident_data = {
                'incident_type': np.random.choice([
                    'high_cpu_utilization', 'memory_leak', 'database_connection_error',
                    'cache_overflow', 'api_rate_limit_exceeded', 'network_timeout',
                    'disk_space_full', 'service_unresponsive'
                ]),
                'cpu_usage': np.random.beta(2, 5),  # Skewed towards lower usage
                'memory_usage': np.random.beta(2, 3),
                'disk_usage': np.random.beta(1.5, 4),
                'error_rate': np.random.exponential(0.02),
                'response_time': np.random.gamma(2, 500),
                'throughput': np.random.gamma(3, 20),
                'is_peak_hour': np.random.choice([0, 1]),
                'recent_deployment': np.random.choice([0, 1], p=[0.8, 0.2]),
                'dependency_issues': np.random.choice([0, 1], p=[0.7, 0.3])
            }

            # Assign resolution based on incident characteristics
            if incident_data['cpu_usage'] > 0.8:
                incident_data['best_resolution'] = 'scale_up'
            elif incident_data['memory_usage'] > 0.9:
                incident_data['best_resolution'] = 'restart_service'
            elif incident_data['error_rate'] > 0.1:
                incident_data['best_resolution'] = 'rollback_deployment'
            elif incident_data['disk_usage'] > 0.9:
                incident_data['best_resolution'] = 'clear_cache'
            else:
                incident_data['best_resolution'] = np.random.choice([
                    'restart_service', 'clear_cache', 'reset_connections'
                ])

            # Clip values
            incident_data['error_rate'] = min(incident_data['error_rate'], 1.0)
            incident_data['response_time'] = min(incident_data['response_time'], 10000)

            additional_data.append(incident_data)

        return additional_data

    def _build_resolution_knowledge_base(self, training_data: List[Dict[str, Any]]) -> None:
        """Build knowledge base of successful resolutions for different incident types."""
        knowledge_base = {}

        for incident in training_data:
            incident_type = incident['incident_type']
            resolution = incident['best_resolution']

            if incident_type not in knowledge_base:
                knowledge_base[incident_type] = []

            if resolution not in knowledge_base[incident_type]:
                knowledge_base[incident_type].append(resolution)

        # Add common resolution sequences
        knowledge_base['escalation_sequence'] = [
            'restart_service', 'clear_cache', 'scale_up', 'rollback_deployment'
        ]

        knowledge_base['critical_incident_sequence'] = [
            'failover', 'scale_up', 'circuit_breaker'
        ]

        self.resolution_knowledge_base = knowledge_base
        logger.info(f"Resolution knowledge base built with {len(knowledge_base)} incident types")

    async def detect_incident(self, service_name: str, metrics: Dict[str, Any],
                            context: Dict[str, Any]) -> Optional[Incident]:
        """Detect and classify incidents from system metrics and context."""
        try:
            # Convert metrics to standardized format
            incident_metrics = IncidentMetrics(
                cpu_usage=np.float32(metrics.get('cpu_usage', 0.0)),
                memory_usage=np.float32(metrics.get('memory_usage', 0.0)),
                disk_usage=np.float32(metrics.get('disk_usage', 0.0)),
                network_io=np.float32(metrics.get('network_io', 0.0)),
                error_rate=np.float32(metrics.get('error_rate', 0.0)),
                response_time=np.float32(metrics.get('response_time', 0.0)),
                throughput=np.float32(metrics.get('throughput', 0.0)),
                active_connections=int(metrics.get('active_connections', 0)),
                queue_depth=int(metrics.get('queue_depth', 0))
            )

            # Convert context to standardized format
            incident_context = IncidentContext(
                service_name=service_name,
                service_version=context.get('service_version', 'unknown'),
                environment=context.get('environment', 'production'),
                recent_deployments=context.get('recent_deployments', []),
                related_alerts=context.get('related_alerts', []),
                dependency_health=context.get('dependency_health', {}),
                load_pattern=context.get('load_pattern', 'normal'),
                time_of_day=context.get('time_of_day', 'unknown'),
                day_of_week=context.get('day_of_week', 'unknown')
            )

            # Check for incident conditions
            incident_detected, incident_type, severity = self._evaluate_incident_conditions(
                incident_metrics, incident_context
            )

            if not incident_detected:
                return None

            # Create incident
            incident_id = self._generate_incident_id(service_name, incident_type)

            incident = Incident(
                incident_id=incident_id,
                service_name=service_name,
                incident_type=incident_type,
                description=f"{incident_type} detected in {service_name}",
                severity=severity,
                status=IncidentStatus.DETECTED,
                metrics=incident_metrics,
                context=incident_context,
                detected_at=datetime.now()
            )

            # Classify incident using ML if available
            if self.incident_classifier is not None:
                confidence = await self._classify_incident_ml(incident)
                incident.classification_confidence = confidence
            else:
                incident.classification_confidence = np.float32(0.8)  # Rule-based confidence

            # Store incident
            self.active_incidents[incident_id] = incident
            self.metrics['incidents_detected'] += 1

            logger.warning(
                f"Incident detected: {incident_id} - {incident_type} "
                f"(severity: {severity.value}, confidence: {incident.classification_confidence:.2f})"
            )

            return incident

        except Exception as e:
            logger.error(f"Error detecting incident: {e}")
            return None

    def _evaluate_incident_conditions(self, metrics: IncidentMetrics,
                                     context: IncidentContext) -> Tuple[bool, str, IncidentSeverity]:
        """Evaluate metrics and context to determine if incident exists."""

        # Critical conditions (immediate incident)
        if metrics.cpu_usage > 0.95:
            return True, "critical_cpu_utilization", IncidentSeverity.CRITICAL

        if metrics.memory_usage > 0.98:
            return True, "critical_memory_usage", IncidentSeverity.CRITICAL

        if metrics.error_rate > 0.5:
            return True, "critical_error_rate", IncidentSeverity.CRITICAL

        if metrics.response_time > 10000:  # 10 seconds
            return True, "critical_response_time", IncidentSeverity.CRITICAL

        # High severity conditions
        if metrics.cpu_usage > 0.85:
            return True, "high_cpu_utilization", IncidentSeverity.HIGH

        if metrics.memory_usage > 0.9:
            return True, "high_memory_usage", IncidentSeverity.HIGH

        if metrics.disk_usage > 0.95:
            return True, "disk_space_critical", IncidentSeverity.HIGH

        if metrics.error_rate > 0.1:
            return True, "high_error_rate", IncidentSeverity.HIGH

        if metrics.response_time > 5000:  # 5 seconds
            return True, "high_response_time", IncidentSeverity.HIGH

        # Medium severity conditions
        if metrics.cpu_usage > 0.8 and metrics.memory_usage > 0.8:
            return True, "resource_contention", IncidentSeverity.MEDIUM

        if metrics.error_rate > 0.05:
            return True, "elevated_error_rate", IncidentSeverity.MEDIUM

        if metrics.throughput < 10 and context.load_pattern == 'spike':
            return True, "throughput_degradation", IncidentSeverity.MEDIUM

        if len(context.related_alerts) > 3:
            return True, "multiple_alerts", IncidentSeverity.MEDIUM

        # Low severity conditions
        if metrics.response_time > 2000:  # 2 seconds
            return True, "slow_response_time", IncidentSeverity.LOW

        if metrics.queue_depth > 100:
            return True, "queue_buildup", IncidentSeverity.LOW

        return False, "", IncidentSeverity.LOW

    async def _classify_incident_ml(self, incident: Incident) -> np.float32:
        """Use ML models to classify incident type and assess confidence."""
        try:
            if self.incident_classifier is None or self.scaler is None:
                return np.float32(0.5)

            # Prepare feature vector
            features = [
                float(incident.metrics.cpu_usage),
                float(incident.metrics.memory_usage),
                float(incident.metrics.disk_usage),
                float(incident.metrics.error_rate),
                float(incident.metrics.response_time),
                float(incident.metrics.throughput),
                1.0 if incident.context.time_of_day == 'peak' else 0.0,
                1.0 if len(incident.context.recent_deployments) > 0 else 0.0,
                float(len([h for h in incident.context.dependency_health.values() if h != 'healthy']) > 0)
            ]

            # Scale features
            features_scaled = self.scaler.transform([features])

            # Get prediction probabilities
            probabilities = self.incident_classifier.predict_proba(features_scaled)[0]
            confidence = np.float32(np.max(probabilities))

            return confidence

        except Exception as e:
            logger.error(f"Error in ML classification: {e}")
            return np.float32(0.5)

    def _generate_incident_id(self, service_name: str, incident_type: str) -> str:
        """Generate unique incident ID."""
        timestamp = datetime.now().isoformat()
        content = f"{service_name}_{incident_type}_{timestamp}"
        return f"inc_{hashlib.md5(content.encode()).hexdigest()[:12]}"

    async def plan_resolution(self, incident: Incident) -> Optional[ResolutionWorkflow]:
        """Plan automated resolution workflow for the incident."""
        try:
            # Get recommended actions
            recommended_actions = await self._recommend_resolution_actions(incident)

            if not recommended_actions:
                logger.warning(f"No resolution actions recommended for incident {incident.incident_id}")
                return None

            # Calculate success probability
            success_probability = await self._estimate_resolution_success(incident, recommended_actions)

            # Create workflow
            workflow_id = f"workflow_{incident.incident_id}_{int(time.time())}"

            workflow = ResolutionWorkflow(
                workflow_id=workflow_id,
                incident_id=incident.incident_id,
                actions=recommended_actions,
                success_probability=success_probability,
                rollback_actions=self._generate_rollback_actions(recommended_actions)
            )

            self.resolution_workflows[workflow_id] = workflow

            logger.info(
                f"Resolution workflow planned for {incident.incident_id}: "
                f"{len(recommended_actions)} actions with {success_probability:.2f} success probability"
            )

            return workflow

        except Exception as e:
            logger.error(f"Error planning resolution for {incident.incident_id}: {e}")
            return None

    async def _recommend_resolution_actions(self, incident: Incident) -> List[ResolutionAction]:
        """Recommend resolution actions based on incident type and ML models."""
        try:
            actions = []

            # Use ML-based recommendation if available
            if self.resolution_recommender is not None and self.scaler is not None:
                actions.extend(await self._get_ml_recommendations(incident))

            # Use knowledge base recommendations
            if incident.incident_type in self.resolution_knowledge_base:
                kb_actions = self.resolution_knowledge_base[incident.incident_type]
                for action_name in kb_actions:
                    try:
                        action = ResolutionAction(action_name)
                        if action not in actions:
                            actions.append(action)
                    except ValueError:
                        continue

            # Use rule-based recommendations as fallback
            if not actions:
                actions = self._get_rule_based_recommendations(incident)

            # Prioritize actions based on severity
            actions = self._prioritize_actions(actions, incident.severity)

            # Limit to reasonable number of actions
            return actions[:self.max_resolution_attempts]

        except Exception as e:
            logger.error(f"Error recommending actions: {e}")
            return self._get_rule_based_recommendations(incident)

    async def _get_ml_recommendations(self, incident: Incident) -> List[ResolutionAction]:
        """Get ML-based resolution recommendations."""
        try:
            # Prepare features (same as classification)
            features = [
                float(incident.metrics.cpu_usage),
                float(incident.metrics.memory_usage),
                float(incident.metrics.disk_usage),
                float(incident.metrics.error_rate),
                float(incident.metrics.response_time),
                float(incident.metrics.throughput),
                1.0 if incident.context.time_of_day == 'peak' else 0.0,
                1.0 if len(incident.context.recent_deployments) > 0 else 0.0,
                float(len([h for h in incident.context.dependency_health.values() if h != 'healthy']) > 0)
            ]

            features_scaled = self.scaler.transform([features])

            # Get prediction probabilities for each action type
            action_probabilities = self.resolution_recommender.predict_proba(features_scaled)[0]
            action_classes = self.resolution_recommender.classes_

            # Sort by probability and select top actions
            action_prob_pairs = list(zip(action_classes, action_probabilities))
            action_prob_pairs.sort(key=lambda x: x[1], reverse=True)

            # Convert to ResolutionAction enum
            recommended_actions = []
            for action_name, probability in action_prob_pairs[:3]:  # Top 3 recommendations
                try:
                    if probability > 0.3:  # Minimum confidence threshold
                        action = ResolutionAction(action_name)
                        recommended_actions.append(action)
                except ValueError:
                    continue

            return recommended_actions

        except Exception as e:
            logger.error(f"Error getting ML recommendations: {e}")
            return []

    def _get_rule_based_recommendations(self, incident: Incident) -> List[ResolutionAction]:
        """Get rule-based resolution recommendations as fallback."""
        actions = []

        # High CPU utilization
        if incident.metrics.cpu_usage > 0.8:
            actions.extend([ResolutionAction.SCALE_UP, ResolutionAction.RESTART_SERVICE])

        # High memory usage
        if incident.metrics.memory_usage > 0.9:
            actions.extend([ResolutionAction.RESTART_SERVICE, ResolutionAction.CLEAR_CACHE])

        # High error rate
        if incident.metrics.error_rate > 0.1:
            if len(incident.context.recent_deployments) > 0:
                actions.append(ResolutionAction.ROLLBACK_DEPLOYMENT)
            else:
                actions.extend([ResolutionAction.RESTART_SERVICE, ResolutionAction.CIRCUIT_BREAKER])

        # Slow response time
        if incident.metrics.response_time > 3000:
            actions.extend([ResolutionAction.CLEAR_CACHE, ResolutionAction.SCALE_UP])

        # Disk space issues
        if incident.metrics.disk_usage > 0.9:
            actions.extend([ResolutionAction.CLEAR_CACHE, ResolutionAction.GRACEFUL_SHUTDOWN])

        # Database connection issues
        if 'database' in incident.incident_type.lower():
            actions.extend([ResolutionAction.RESET_CONNECTIONS, ResolutionAction.RESTART_SERVICE])

        # Network issues
        if 'network' in incident.incident_type.lower() or 'timeout' in incident.incident_type.lower():
            actions.extend([ResolutionAction.RESET_CONNECTIONS, ResolutionAction.FAILOVER])

        # Remove duplicates while preserving order
        unique_actions = []
        for action in actions:
            if action not in unique_actions:
                unique_actions.append(action)

        return unique_actions

    def _prioritize_actions(self, actions: List[ResolutionAction],
                          severity: IncidentSeverity) -> List[ResolutionAction]:
        """Prioritize resolution actions based on incident severity."""

        # Define priority order for different severities
        if severity == IncidentSeverity.CRITICAL:
            priority_order = [
                ResolutionAction.FAILOVER,
                ResolutionAction.CIRCUIT_BREAKER,
                ResolutionAction.SCALE_UP,
                ResolutionAction.RESTART_SERVICE,
                ResolutionAction.ROLLBACK_DEPLOYMENT
            ]
        elif severity == IncidentSeverity.HIGH:
            priority_order = [
                ResolutionAction.SCALE_UP,
                ResolutionAction.RESTART_SERVICE,
                ResolutionAction.ROLLBACK_DEPLOYMENT,
                ResolutionAction.CLEAR_CACHE,
                ResolutionAction.RESET_CONNECTIONS
            ]
        else:
            priority_order = [
                ResolutionAction.CLEAR_CACHE,
                ResolutionAction.RESTART_SERVICE,
                ResolutionAction.RESET_CONNECTIONS,
                ResolutionAction.SCALE_UP,
                ResolutionAction.GRACEFUL_SHUTDOWN
            ]

        # Sort actions based on priority
        prioritized = []

        # First add actions in priority order
        for priority_action in priority_order:
            if priority_action in actions:
                prioritized.append(priority_action)

        # Then add remaining actions
        for action in actions:
            if action not in prioritized:
                prioritized.append(action)

        return prioritized

    async def _estimate_resolution_success(self, incident: Incident,
                                         actions: List[ResolutionAction]) -> np.float32:
        """Estimate probability of successful resolution."""
        try:
            base_probability = 0.5

            # Adjust based on incident severity (easier to fix less severe issues)
            severity_adjustments = {
                IncidentSeverity.LOW: 0.3,
                IncidentSeverity.MEDIUM: 0.1,
                IncidentSeverity.HIGH: -0.1,
                IncidentSeverity.CRITICAL: -0.2
            }

            base_probability += severity_adjustments.get(incident.severity, 0)

            # Adjust based on number of actions (more actions = lower individual success)
            if len(actions) > 2:
                base_probability -= 0.1 * (len(actions) - 2)

            # Adjust based on incident type (some are easier to fix)
            easy_to_fix = ['cache_overflow', 'queue_buildup', 'slow_response_time']
            hard_to_fix = ['memory_leak', 'database_connection_error', 'network_timeout']

            if any(easy_type in incident.incident_type for easy_type in easy_to_fix):
                base_probability += 0.2
            elif any(hard_type in incident.incident_type for hard_type in hard_to_fix):
                base_probability -= 0.15

            # Adjust based on recent deployments (rollback usually works)
            if (len(incident.context.recent_deployments) > 0 and
                ResolutionAction.ROLLBACK_DEPLOYMENT in actions):
                base_probability += 0.2

            # Clip to valid range
            return np.float32(max(0.1, min(0.9, base_probability)))

        except Exception as e:
            logger.error(f"Error estimating success probability: {e}")
            return np.float32(0.5)

    def _generate_rollback_actions(self, actions: List[ResolutionAction]) -> List[str]:
        """Generate rollback actions for the resolution workflow."""
        rollback_actions = []

        for action in actions:
            if action == ResolutionAction.SCALE_UP:
                rollback_actions.append("scale_down_to_original")
            elif action == ResolutionAction.SCALE_DOWN:
                rollback_actions.append("scale_up_to_original")
            elif action == ResolutionAction.RESTART_SERVICE:
                rollback_actions.append("restore_previous_state")
            elif action == ResolutionAction.ROLLBACK_DEPLOYMENT:
                rollback_actions.append("redeploy_to_target_version")
            elif action == ResolutionAction.CLEAR_CACHE:
                rollback_actions.append("restore_cache_if_possible")
            elif action == ResolutionAction.FAILOVER:
                rollback_actions.append("failback_to_primary")
            elif action == ResolutionAction.CIRCUIT_BREAKER:
                rollback_actions.append("close_circuit_breaker")
            else:
                rollback_actions.append(f"undo_{action.value}")

        return rollback_actions

    async def execute_resolution(self, workflow: ResolutionWorkflow) -> ResolutionResult:
        """Execute automated resolution workflow with monitoring and rollback."""
        start_time = datetime.now()
        workflow.started_at = start_time

        try:
            # Check if auto-resolution is enabled
            if not self.auto_resolution_enabled:
                logger.info(f"Auto-resolution disabled - escalating workflow {workflow.workflow_id}")
                return await self._create_escalation_result(workflow, "Auto-resolution disabled")

            # Check confidence threshold
            if workflow.success_probability < self.confidence_threshold:
                logger.info(
                    f"Resolution confidence {workflow.success_probability:.2f} below threshold "
                    f"{self.confidence_threshold} - escalating workflow {workflow.workflow_id}"
                )
                return await self._create_escalation_result(
                    workflow, f"Low confidence: {workflow.success_probability:.2f}"
                )

            logger.info(f"Executing resolution workflow {workflow.workflow_id}")

            actions_executed = []
            success = False

            # Execute each action in sequence
            for i, action in enumerate(workflow.actions):
                workflow.current_step = i

                try:
                    # Execute the action
                    action_result = await self._execute_resolution_action(
                        action, workflow.incident_id
                    )

                    # Log execution
                    execution_log_entry = {
                        'action': action.value,
                        'timestamp': datetime.now().isoformat(),
                        'success': action_result['success'],
                        'details': action_result.get('details', ''),
                        'metrics_before': action_result.get('metrics_before', {}),
                        'metrics_after': action_result.get('metrics_after', {})
                    }

                    workflow.execution_log.append(execution_log_entry)
                    actions_executed.append(action.value)

                    if action_result['success']:
                        logger.info(f"Action {action.value} executed successfully")

                        # Check if incident is resolved
                        if await self._verify_resolution(workflow.incident_id):
                            success = True
                            logger.info(f"Incident {workflow.incident_id} resolved after action {action.value}")
                            break
                        else:
                            logger.info(f"Incident {workflow.incident_id} still active after action {action.value}")
                    else:
                        logger.error(f"Action {action.value} failed: {action_result.get('error', 'Unknown error')}")

                        # Consider rollback if this was a critical failure
                        if action_result.get('critical_failure', False):
                            await self._execute_rollback(workflow, i)
                            break

                except Exception as e:
                    logger.error(f"Error executing action {action.value}: {e}")
                    workflow.execution_log.append({
                        'action': action.value,
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': str(e)
                    })

                # Wait between actions to allow system stabilization
                await asyncio.sleep(2)

            workflow.completed_at = datetime.now()
            resolution_time = workflow.completed_at - workflow.started_at

            # Update incident status
            if workflow.incident_id in self.active_incidents:
                if success:
                    self.active_incidents[workflow.incident_id].status = IncidentStatus.RESOLVED
                    self.metrics['incidents_resolved_automatically'] += 1
                else:
                    self.active_incidents[workflow.incident_id].status = IncidentStatus.FAILED

            # Create result
            result = ResolutionResult(
                workflow_id=workflow.workflow_id,
                incident_id=workflow.incident_id,
                success=success,
                actions_executed=actions_executed,
                resolution_time=resolution_time,
                confidence_score=workflow.success_probability,
                impact_assessment=await self._assess_resolution_impact(workflow),
                lessons_learned=self._extract_lessons_learned(workflow),
                require_human_review=not success or len(actions_executed) > 2
            )

            # Update metrics
            self._update_performance_metrics(result)

            logger.info(
                f"Resolution workflow {workflow.workflow_id} completed: "
                f"success={success}, time={resolution_time}, actions={len(actions_executed)}"
            )

            return result

        except Exception as e:
            logger.error(f"Error executing resolution workflow {workflow.workflow_id}: {e}")
            workflow.completed_at = datetime.now()

            return ResolutionResult(
                workflow_id=workflow.workflow_id,
                incident_id=workflow.incident_id,
                success=False,
                actions_executed=actions_executed,
                resolution_time=datetime.now() - start_time,
                confidence_score=np.float32(0.0),
                impact_assessment={'error': str(e)},
                lessons_learned=[f"Execution failed: {str(e)}"],
                require_human_review=True
            )

    async def _execute_resolution_action(self, action: ResolutionAction,
                                       incident_id: str) -> Dict[str, Any]:
        """Execute a specific resolution action."""
        try:
            # Get incident for context
            incident = self.active_incidents.get(incident_id)
            if not incident:
                return {'success': False, 'error': f'Incident {incident_id} not found'}

            # Capture metrics before action
            metrics_before = await self._capture_current_metrics(incident.service_name)

            # Execute action based on type
            if action == ResolutionAction.RESTART_SERVICE:
                result = await self._restart_service(incident.service_name)
            elif action == ResolutionAction.SCALE_UP:
                result = await self._scale_service(incident.service_name, 'up')
            elif action == ResolutionAction.SCALE_DOWN:
                result = await self._scale_service(incident.service_name, 'down')
            elif action == ResolutionAction.CLEAR_CACHE:
                result = await self._clear_cache(incident.service_name)
            elif action == ResolutionAction.ROLLBACK_DEPLOYMENT:
                result = await self._rollback_deployment(incident.service_name)
            elif action == ResolutionAction.RESET_CONNECTIONS:
                result = await self._reset_connections(incident.service_name)
            elif action == ResolutionAction.CIRCUIT_BREAKER:
                result = await self._activate_circuit_breaker(incident.service_name)
            elif action == ResolutionAction.FAILOVER:
                result = await self._execute_failover(incident.service_name)
            elif action == ResolutionAction.GRACEFUL_SHUTDOWN:
                result = await self._graceful_shutdown(incident.service_name)
            elif action == ResolutionAction.APPLY_HOTFIX:
                result = await self._apply_hotfix(incident.service_name)
            else:
                result = {'success': False, 'error': f'Unknown action: {action.value}'}

            # Wait for system stabilization
            await asyncio.sleep(5)

            # Capture metrics after action
            metrics_after = await self._capture_current_metrics(incident.service_name)

            result.update({
                'metrics_before': metrics_before,
                'metrics_after': metrics_after
            })

            return result

        except Exception as e:
            logger.error(f"Error executing action {action.value}: {e}")
            return {'success': False, 'error': str(e), 'critical_failure': True}

    async def _restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart service (simulation for demo)."""
        logger.info(f"Restarting service: {service_name}")

        # Simulate restart process
        await asyncio.sleep(2)

        # In production, this would interact with container orchestration
        # kubectl restart deployment/{service_name}
        # or docker restart {container_name}

        return {
            'success': True,
            'details': f'Service {service_name} restarted successfully',
            'action_duration': 2.0
        }

    async def _scale_service(self, service_name: str, direction: str) -> Dict[str, Any]:
        """Scale service up or down."""
        logger.info(f"Scaling service {service_name} {direction}")

        # Simulate scaling process
        await asyncio.sleep(3)

        # In production, this would interact with auto-scaling systems
        # kubectl scale deployment {service_name} --replicas={new_count}

        return {
            'success': True,
            'details': f'Service {service_name} scaled {direction} successfully',
            'action_duration': 3.0
        }

    async def _clear_cache(self, service_name: str) -> Dict[str, Any]:
        """Clear service cache."""
        logger.info(f"Clearing cache for service: {service_name}")

        # Simulate cache clearing
        await asyncio.sleep(1)

        # In production, this would clear Redis/Memcached
        # redis-cli FLUSHDB or specific cache invalidation

        return {
            'success': True,
            'details': f'Cache cleared for service {service_name}',
            'action_duration': 1.0
        }

    async def _rollback_deployment(self, service_name: str) -> Dict[str, Any]:
        """Rollback to previous deployment."""
        logger.info(f"Rolling back deployment for service: {service_name}")

        # Simulate rollback process
        await asyncio.sleep(4)

        # In production, this would trigger deployment rollback
        # kubectl rollout undo deployment/{service_name}

        return {
            'success': True,
            'details': f'Deployment rolled back for service {service_name}',
            'action_duration': 4.0
        }

    async def _reset_connections(self, service_name: str) -> Dict[str, Any]:
        """Reset database/network connections."""
        logger.info(f"Resetting connections for service: {service_name}")

        # Simulate connection reset
        await asyncio.sleep(2)

        # In production, this would reset connection pools
        # or restart database connections

        return {
            'success': True,
            'details': f'Connections reset for service {service_name}',
            'action_duration': 2.0
        }

    async def _activate_circuit_breaker(self, service_name: str) -> Dict[str, Any]:
        """Activate circuit breaker pattern."""
        logger.info(f"Activating circuit breaker for service: {service_name}")

        # Simulate circuit breaker activation
        await asyncio.sleep(1)

        # In production, this would configure circuit breaker
        # to prevent cascade failures

        return {
            'success': True,
            'details': f'Circuit breaker activated for service {service_name}',
            'action_duration': 1.0
        }

    async def _execute_failover(self, service_name: str) -> Dict[str, Any]:
        """Execute failover to backup systems."""
        logger.info(f"Executing failover for service: {service_name}")

        # Simulate failover process
        await asyncio.sleep(5)

        # In production, this would switch traffic to backup instances
        # or secondary data centers

        return {
            'success': True,
            'details': f'Failover executed for service {service_name}',
            'action_duration': 5.0
        }

    async def _graceful_shutdown(self, service_name: str) -> Dict[str, Any]:
        """Perform graceful shutdown of service."""
        logger.info(f"Graceful shutdown for service: {service_name}")

        # Simulate graceful shutdown
        await asyncio.sleep(3)

        # In production, this would drain connections and shutdown cleanly

        return {
            'success': True,
            'details': f'Graceful shutdown completed for service {service_name}',
            'action_duration': 3.0
        }

    async def _apply_hotfix(self, service_name: str) -> Dict[str, Any]:
        """Apply automated hotfix for known issues."""
        logger.info(f"Applying hotfix for service: {service_name}")

        # Simulate hotfix deployment
        await asyncio.sleep(6)

        # In production, this would deploy a pre-approved hotfix

        return {
            'success': True,
            'details': f'Hotfix applied for service {service_name}',
            'action_duration': 6.0
        }

    async def _capture_current_metrics(self, service_name: str) -> Dict[str, float]:
        """Capture current system metrics for before/after comparison."""
        # Simulate metric collection
        # In production, this would query monitoring systems

        return {
            'cpu_usage': np.random.uniform(0.1, 0.9),
            'memory_usage': np.random.uniform(0.2, 0.8),
            'error_rate': np.random.uniform(0.0, 0.1),
            'response_time': np.random.uniform(100, 1000),
            'throughput': np.random.uniform(10, 100)
        }

    async def _verify_resolution(self, incident_id: str) -> bool:
        """Verify that the incident has been resolved."""
        try:
            incident = self.active_incidents.get(incident_id)
            if not incident:
                return False

            # Simulate resolution verification
            # In production, this would check if the conditions that triggered
            # the incident are no longer present

            # Get current metrics
            current_metrics = await self._capture_current_metrics(incident.service_name)

            # Check if incident conditions are resolved
            if incident.incident_type == 'high_cpu_utilization':
                return current_metrics['cpu_usage'] < 0.8
            elif incident.incident_type == 'high_memory_usage':
                return current_metrics['memory_usage'] < 0.85
            elif incident.incident_type == 'high_error_rate':
                return current_metrics['error_rate'] < 0.05
            elif incident.incident_type == 'slow_response_time':
                return current_metrics['response_time'] < 2000
            else:
                # For unknown incident types, assume resolution with some probability
                return np.random.random() > 0.3

        except Exception as e:
            logger.error(f"Error verifying resolution for {incident_id}: {e}")
            return False

    async def _execute_rollback(self, workflow: ResolutionWorkflow, failed_step: int) -> None:
        """Execute rollback actions for failed resolution attempts."""
        try:
            logger.warning(f"Executing rollback for workflow {workflow.workflow_id} at step {failed_step}")

            # Execute rollback actions in reverse order
            for i in range(failed_step, -1, -1):
                if i < len(workflow.rollback_actions):
                    rollback_action = workflow.rollback_actions[i]
                    logger.info(f"Executing rollback action: {rollback_action}")

                    # Simulate rollback execution
                    await asyncio.sleep(1)

                    workflow.execution_log.append({
                        'action': f'rollback_{rollback_action}',
                        'timestamp': datetime.now().isoformat(),
                        'success': True,
                        'details': f'Rollback executed: {rollback_action}'
                    })

            logger.info(f"Rollback completed for workflow {workflow.workflow_id}")

        except Exception as e:
            logger.error(f"Error executing rollback: {e}")

    async def _assess_resolution_impact(self, workflow: ResolutionWorkflow) -> Dict[str, Any]:
        """Assess the impact of resolution actions."""
        try:
            impact_assessment = {
                'actions_attempted': len(workflow.actions),
                'actions_successful': len([log for log in workflow.execution_log if log.get('success', False)]),
                'total_downtime': 0.0,
                'performance_impact': 'minimal',
                'cost_impact': 'low',
                'risk_level': 'low'
            }

            # Calculate downtime
            if workflow.started_at and workflow.completed_at:
                downtime_seconds = (workflow.completed_at - workflow.started_at).total_seconds()
                impact_assessment['total_downtime'] = downtime_seconds

            # Assess performance impact
            if len(workflow.actions) > 2:
                impact_assessment['performance_impact'] = 'moderate'
            if any(action in [ResolutionAction.FAILOVER, ResolutionAction.ROLLBACK_DEPLOYMENT]
                   for action in workflow.actions):
                impact_assessment['performance_impact'] = 'significant'

            # Assess cost impact
            if ResolutionAction.SCALE_UP in workflow.actions:
                impact_assessment['cost_impact'] = 'medium'
            if ResolutionAction.FAILOVER in workflow.actions:
                impact_assessment['cost_impact'] = 'high'

            # Assess risk level
            failed_actions = len([log for log in workflow.execution_log if not log.get('success', True)])
            if failed_actions > 0:
                impact_assessment['risk_level'] = 'medium'
            if failed_actions > 1:
                impact_assessment['risk_level'] = 'high'

            return impact_assessment

        except Exception as e:
            logger.error(f"Error assessing resolution impact: {e}")
            return {'error': str(e)}

    def _extract_lessons_learned(self, workflow: ResolutionWorkflow) -> List[str]:
        """Extract lessons learned from resolution execution."""
        lessons = []

        try:
            # Analyze execution log for patterns
            successful_actions = [log for log in workflow.execution_log if log.get('success', False)]
            failed_actions = [log for log in workflow.execution_log if not log.get('success', True)]

            if successful_actions:
                most_effective = successful_actions[0]['action']
                lessons.append(f"Most effective action: {most_effective}")

            if failed_actions:
                lessons.append(f"Failed actions need investigation: {[a['action'] for a in failed_actions]}")

            # Analyze timing
            if workflow.started_at and workflow.completed_at:
                duration = (workflow.completed_at - workflow.started_at).total_seconds()
                if duration < 60:
                    lessons.append("Resolution was completed quickly - good automation")
                elif duration > 300:
                    lessons.append("Resolution took longer than expected - review workflow")

            # Analyze action effectiveness
            if len(workflow.actions) == 1 and len(successful_actions) == 1:
                lessons.append("Single action resolution - excellent targeting")
            elif len(successful_actions) < len(workflow.actions) / 2:
                lessons.append("Low success rate - review action selection logic")

            return lessons

        except Exception as e:
            logger.error(f"Error extracting lessons learned: {e}")
            return [f"Analysis failed: {str(e)}"]

    async def _create_escalation_result(self, workflow: ResolutionWorkflow,
                                      reason: str) -> ResolutionResult:
        """Create result for escalated incidents."""
        return ResolutionResult(
            workflow_id=workflow.workflow_id,
            incident_id=workflow.incident_id,
            success=False,
            actions_executed=[],
            resolution_time=timedelta(seconds=0),
            confidence_score=np.float32(0.0),
            impact_assessment={'escalation_reason': reason},
            lessons_learned=[f"Escalated due to: {reason}"],
            require_human_review=True
        )

    def _update_performance_metrics(self, result: ResolutionResult) -> None:
        """Update system performance metrics based on resolution result."""
        try:
            # Update resolution success rate
            total_resolutions = self.metrics['incidents_resolved_automatically'] + self.metrics['incidents_escalated']
            if total_resolutions > 0:
                self.metrics['resolution_success_rate'] = (
                    self.metrics['incidents_resolved_automatically'] / total_resolutions
                )

            # Update average resolution time
            if result.success:
                current_avg = self.metrics['average_resolution_time']
                new_time = result.resolution_time.total_seconds()
                # Simple moving average
                self.metrics['average_resolution_time'] = (current_avg + new_time) / 2

            # Track escalations
            if result.require_human_review and not result.success:
                self.metrics['incidents_escalated'] += 1

        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    async def escalate_incident(self, incident: Incident, reason: str) -> None:
        """Escalate incident to human operators."""
        try:
            incident.status = IncidentStatus.ESCALATED
            incident.escalation_reason = reason

            # In production, this would:
            # 1. Send alerts to on-call team
            # 2. Create tickets in incident management system
            # 3. Notify stakeholders based on severity

            logger.critical(
                f"Incident {incident.incident_id} escalated: {reason} "
                f"(severity: {incident.severity.value})"
            )

            # Simulate escalation notifications
            await self._send_escalation_notifications(incident, reason)

        except Exception as e:
            logger.error(f"Error escalating incident {incident.incident_id}: {e}")

    async def _send_escalation_notifications(self, incident: Incident, reason: str) -> None:
        """Send escalation notifications to appropriate teams."""
        # Simulate notification sending
        # In production, this would integrate with:
        # - PagerDuty, VictorOps, or other alerting systems
        # - Slack, Teams, or other chat platforms
        # - Email systems
        # - SMS/phone call systems for critical incidents

        notification_channels = []

        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            notification_channels.extend(['pagerduty', 'slack', 'email', 'sms'])
        elif incident.severity == IncidentSeverity.MEDIUM:
            notification_channels.extend(['slack', 'email'])
        else:
            notification_channels.append('email')

        for channel in notification_channels:
            logger.info(f"Sending escalation notification via {channel} for incident {incident.incident_id}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status and health metrics."""
        try:
            active_count = len(self.active_incidents)
            resolved_count = len([i for i in self.incident_history if i.status == IncidentStatus.RESOLVED])

            status = {
                'system_health': 'healthy' if active_count == 0 else 'degraded',
                'active_incidents': active_count,
                'incidents_resolved_today': resolved_count,
                'auto_resolution_enabled': self.auto_resolution_enabled,
                'performance_metrics': self.metrics.copy(),
                'ml_models_status': {
                    'incident_classifier': 'active' if self.incident_classifier is not None else 'unavailable',
                    'resolution_recommender': 'active' if self.resolution_recommender is not None else 'unavailable',
                    'ml_libraries': 'available' if ML_AVAILABLE else 'unavailable'
                },
                'active_workflows': len(self.resolution_workflows),
                'knowledge_base_size': len(self.resolution_knowledge_base),
                'last_updated': datetime.now().isoformat()
            }

            # Add incident summary by severity
            severity_counts = {}
            for incident in self.active_incidents.values():
                severity = incident.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            status['incidents_by_severity'] = severity_counts

            return status

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'system_health': 'unknown',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check of the self-healing system."""
        health_check = {
            'overall_health': 'healthy',
            'checks': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Check ML models
            if ML_AVAILABLE and self.incident_classifier is not None:
                health_check['checks']['ml_models'] = {
                    'status': 'healthy',
                    'incident_classifier': 'active',
                    'resolution_recommender': 'active' if self.resolution_recommender is not None else 'inactive'
                }
            else:
                health_check['checks']['ml_models'] = {
                    'status': 'degraded',
                    'reason': 'ML models not available - using rule-based fallbacks'
                }
                health_check['overall_health'] = 'degraded'

            # Check system resources
            health_check['checks']['system_resources'] = {
                'status': 'healthy',
                'active_incidents': len(self.active_incidents),
                'active_workflows': len(self.resolution_workflows),
                'memory_usage': 'normal'
            }

            # Check configuration
            config_issues = []
            if not self.auto_resolution_enabled:
                config_issues.append('Auto-resolution disabled')
            if self.confidence_threshold > 0.9:
                config_issues.append('Confidence threshold very high')

            health_check['checks']['configuration'] = {
                'status': 'healthy' if not config_issues else 'warning',
                'issues': config_issues
            }

            # Check performance metrics
            if self.metrics['resolution_success_rate'] < 0.7:
                health_check['checks']['performance'] = {
                    'status': 'warning',
                    'reason': f"Low success rate: {self.metrics['resolution_success_rate']:.2f}"
                }
                health_check['overall_health'] = 'degraded'
            else:
                health_check['checks']['performance'] = {
                    'status': 'healthy',
                    'success_rate': self.metrics['resolution_success_rate']
                }

            return health_check

        except Exception as e:
            logger.error(f"Error running health check: {e}")
            health_check['overall_health'] = 'unhealthy'
            health_check['error'] = str(e)
            return health_check

    async def cleanup_completed_workflows(self) -> int:
        """Clean up completed workflows to prevent memory leaks."""
        try:
            cleanup_count = 0
            cutoff_time = datetime.now() - timedelta(hours=24)  # Keep for 24 hours

            workflows_to_remove = []
            for workflow_id, workflow in self.resolution_workflows.items():
                if (workflow.completed_at is not None and
                    workflow.completed_at < cutoff_time):
                    workflows_to_remove.append(workflow_id)

            for workflow_id in workflows_to_remove:
                del self.resolution_workflows[workflow_id]
                cleanup_count += 1

            # Also cleanup old incidents from history
            self.incident_history = [
                incident for incident in self.incident_history
                if incident.detected_at > cutoff_time
            ]

            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} completed workflows")

            return cleanup_count

        except Exception as e:
            logger.error(f"Error cleaning up workflows: {e}")
            return 0


# Monitoring and testing functions
async def simulate_self_healing_test():
    """Simulate self-healing system test with various incident scenarios."""
    try:
        logger.info("🧪 Starting Self-Healing System Simulation")

        # Initialize system
        system = SelfHealingSystem({
            'auto_resolution_enabled': True,
            'confidence_threshold': 0.6,
            'max_resolution_attempts': 3
        })

        # Initialize ML models
        await system.initialize_ml_models()

        # Test scenarios
        test_scenarios = [
            {
                'name': 'High CPU Utilization',
                'service': 'enhanced_ml_personalization_engine',
                'metrics': {
                    'cpu_usage': 0.92, 'memory_usage': 0.6, 'disk_usage': 0.3,
                    'error_rate': 0.02, 'response_time': 2500, 'throughput': 45,
                    'active_connections': 150, 'queue_depth': 25
                },
                'context': {
                    'service_version': 'v2.1.0', 'environment': 'production',
                    'recent_deployments': [], 'related_alerts': ['cpu_alert'],
                    'dependency_health': {'database': 'healthy', 'cache': 'healthy'},
                    'load_pattern': 'spike', 'time_of_day': 'peak', 'day_of_week': 'monday'
                }
            },
            {
                'name': 'Memory Leak Detection',
                'service': 'predictive_churn_prevention',
                'metrics': {
                    'cpu_usage': 0.5, 'memory_usage': 0.96, 'disk_usage': 0.4,
                    'error_rate': 0.08, 'response_time': 3200, 'throughput': 25,
                    'active_connections': 80, 'queue_depth': 45
                },
                'context': {
                    'service_version': 'v1.8.3', 'environment': 'production',
                    'recent_deployments': ['v1.8.3_2024-01-09'], 'related_alerts': ['memory_alert', 'error_alert'],
                    'dependency_health': {'database': 'healthy', 'cache': 'degraded'},
                    'load_pattern': 'normal', 'time_of_day': 'off_peak', 'day_of_week': 'tuesday'
                }
            },
            {
                'name': 'Database Connection Issues',
                'service': 'real_time_model_training',
                'metrics': {
                    'cpu_usage': 0.3, 'memory_usage': 0.4, 'disk_usage': 0.2,
                    'error_rate': 0.18, 'response_time': 5500, 'throughput': 8,
                    'active_connections': 20, 'queue_depth': 80
                },
                'context': {
                    'service_version': 'v3.0.1', 'environment': 'production',
                    'recent_deployments': [], 'related_alerts': ['db_connection_alert', 'timeout_alert'],
                    'dependency_health': {'database': 'unhealthy', 'cache': 'healthy'},
                    'load_pattern': 'normal', 'time_of_day': 'peak', 'day_of_week': 'wednesday'
                }
            }
        ]

        results = []

        for scenario in test_scenarios:
            logger.info(f"\n🎯 Testing Scenario: {scenario['name']}")

            # Detect incident
            incident = await system.detect_incident(
                scenario['service'],
                scenario['metrics'],
                scenario['context']
            )

            if incident:
                logger.info(f"✅ Incident detected: {incident.incident_id} (severity: {incident.severity.value})")

                # Plan resolution
                workflow = await system.plan_resolution(incident)

                if workflow:
                    logger.info(f"📋 Resolution planned: {len(workflow.actions)} actions, {workflow.success_probability:.2f} confidence")

                    # Execute resolution
                    result = await system.execute_resolution(workflow)

                    results.append({
                        'scenario': scenario['name'],
                        'incident_id': incident.incident_id,
                        'severity': incident.severity.value,
                        'actions_planned': len(workflow.actions),
                        'actions_executed': len(result.actions_executed),
                        'success': result.success,
                        'resolution_time': result.resolution_time.total_seconds(),
                        'confidence': float(result.confidence_score),
                        'require_escalation': result.require_human_review
                    })

                    logger.info(f"🏁 Resolution completed: success={result.success}, time={result.resolution_time}")
                else:
                    logger.warning(f"❌ No resolution workflow could be planned")
                    results.append({
                        'scenario': scenario['name'],
                        'incident_id': incident.incident_id,
                        'success': False,
                        'error': 'No workflow planned'
                    })
            else:
                logger.warning(f"❌ No incident detected for scenario: {scenario['name']}")
                results.append({
                    'scenario': scenario['name'],
                    'success': False,
                    'error': 'No incident detected'
                })

            # Wait between scenarios
            await asyncio.sleep(1)

        # Get final system status
        system_status = await system.get_system_status()
        health_check = await system.run_health_check()

        # Summary
        successful_resolutions = len([r for r in results if r.get('success', False)])
        total_scenarios = len(results)

        logger.info(f"\n📊 Self-Healing System Test Summary:")
        logger.info(f"   Total Scenarios: {total_scenarios}")
        logger.info(f"   Successful Resolutions: {successful_resolutions}")
        logger.info(f"   Success Rate: {successful_resolutions/total_scenarios*100:.1f}%")
        logger.info(f"   Average Resolution Time: {np.mean([r.get('resolution_time', 0) for r in results if r.get('success')]):.1f}s")
        logger.info(f"   System Health: {health_check['overall_health']}")

        return {
            'test_results': results,
            'system_status': system_status,
            'health_check': health_check,
            'summary': {
                'total_scenarios': total_scenarios,
                'successful_resolutions': successful_resolutions,
                'success_rate': successful_resolutions / total_scenarios,
                'average_resolution_time': np.mean([r.get('resolution_time', 0) for r in results if r.get('success', False)])
            }
        }

    except Exception as e:
        logger.error(f"Error in self-healing system simulation: {e}")
        raise


if __name__ == "__main__":
    """Run self-healing system simulation for testing."""
    import asyncio

    async def main():
        try:
            # Run simulation
            test_results = await simulate_self_healing_test()

            # Save results
            results_file = Path("scripts/self_healing_test_results.json")
            with open(results_file, 'w') as f:
                json.dump(test_results, f, indent=2, default=str)

            print(f"\n📄 Test results saved to: {results_file}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise

    asyncio.run(main())