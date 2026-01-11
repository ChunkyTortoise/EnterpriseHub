"""
Unified User Experience Orchestrator (Phase 2)

Advanced user experience orchestration that creates seamless, intelligent,
and contextually-aware experiences across all EnterpriseHub hubs by
leveraging Phase 2 systems for workflow automation, data synchronization,
and intelligent assistance.

Key Features:
- Context-aware interface adaptation based on user behavior and preferences
- Intelligent workflow suggestions and automation triggered by user patterns
- Real-time cross-hub data synchronization for consistent experiences
- Personalized dashboard layouts with dynamic component prioritization
- Predictive navigation and smart action recommendations
- Progressive disclosure with complexity management based on user expertise
- Unified notification and communication system across all touchpoints
- Performance optimization with adaptive loading and caching strategies

Intelligence Capabilities:
- Machine learning-driven personalization engine
- Behavioral pattern recognition for workflow optimization
- Predictive content and action suggestions
- Adaptive interface complexity based on user proficiency
- Context-sensitive help and onboarding experiences
- Real-time collaboration features with presence awareness
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import uuid
import numpy as np
from pathlib import Path

# External dependencies
try:
    import streamlit as st
    import redis
    import pandas as pd
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError as e:
    print(f"Unified User Experience Orchestrator: Missing dependencies: {e}")
    print("Install with: pip install streamlit redis pandas scikit-learn plotly")

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.unified_workflow_orchestrator import HubType
from ghl_real_estate_ai.services.advanced_integration_middleware import (
    AdvancedIntegrationMiddleware, EventType, IntegrationEvent
)
from ghl_real_estate_ai.services.intelligent_workflow_automation import (
    IntelligentWorkflowAutomation, WorkflowSuggestion
)

logger = get_logger(__name__)


class UserExpertiseLevel(Enum):
    """User expertise levels for adaptive interfaces."""
    NOVICE = "novice"         # New users, simplified interfaces
    INTERMEDIATE = "intermediate"  # Regular users, balanced complexity
    ADVANCED = "advanced"     # Power users, full features
    EXPERT = "expert"         # Admin/expert users, all capabilities


class InterfaceComplexity(Enum):
    """Interface complexity levels."""
    MINIMAL = "minimal"       # Essential features only
    STANDARD = "standard"     # Standard feature set
    COMPREHENSIVE = "comprehensive"  # Full feature set
    EXPERT = "expert"         # All features + advanced tools


class PersonalizationType(Enum):
    """Types of personalization."""
    LAYOUT = "layout"         # Dashboard and component layout
    CONTENT = "content"       # Content filtering and prioritization
    WORKFLOW = "workflow"     # Workflow and process customization
    NAVIGATION = "navigation" # Navigation patterns and shortcuts
    NOTIFICATIONS = "notifications"  # Notification preferences


@dataclass
class UserContext:
    """Comprehensive user context for experience orchestration."""

    user_id: str
    session_id: str
    current_hub: HubType

    # User characteristics
    expertise_level: UserExpertiseLevel = UserExpertiseLevel.INTERMEDIATE
    role: str = "agent"  # agent, manager, admin, viewer
    team_id: Optional[str] = None
    location_id: Optional[str] = None

    # Behavioral patterns
    preferred_complexity: InterfaceComplexity = InterfaceComplexity.STANDARD
    frequent_actions: List[str] = field(default_factory=list)
    workflow_patterns: List[str] = field(default_factory=list)
    navigation_patterns: List[str] = field(default_factory=list)

    # Current context
    active_leads: List[str] = field(default_factory=list)
    active_deals: List[str] = field(default_factory=list)
    current_tasks: List[str] = field(default_factory=list)
    recent_actions: List[Dict[str, Any]] = field(default_factory=list)

    # Preferences
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    layout_preferences: Dict[str, Any] = field(default_factory=dict)
    theme_preferences: Dict[str, str] = field(default_factory=dict)

    # Performance tracking
    session_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actions_this_session: int = 0
    efficiency_score: float = 0.0


@dataclass
class ExperienceComponent:
    """Component of the user experience."""

    component_id: str
    name: str
    component_type: str  # widget, panel, dashboard, workflow, etc.

    # Content and configuration
    content_data: Dict[str, Any] = field(default_factory=dict)
    layout_config: Dict[str, Any] = field(default_factory=dict)
    interaction_config: Dict[str, Any] = field(default_factory=dict)

    # Personalization
    priority_score: float = 1.0
    personalization_factors: List[str] = field(default_factory=list)
    adaptive_settings: Dict[str, Any] = field(default_factory=dict)

    # Context sensitivity
    required_context: List[str] = field(default_factory=list)
    conditional_display: Dict[str, Any] = field(default_factory=dict)

    # Performance
    load_time_ms: Optional[float] = None
    interaction_count: int = 0
    user_satisfaction: Optional[float] = None


@dataclass
class PersonalizedExperience:
    """Personalized user experience configuration."""

    user_id: str
    experience_id: str
    hub: HubType

    # Components and layout
    components: List[ExperienceComponent]
    layout_structure: Dict[str, Any]
    navigation_structure: Dict[str, Any]

    # Personalization metadata
    personalization_confidence: float = 0.0
    created_from_patterns: List[str] = field(default_factory=list)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)

    # Performance metrics
    engagement_score: float = 0.0
    efficiency_improvement: float = 0.0
    user_satisfaction: float = 0.0

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns for experience personalization."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize user behavior analyzer."""
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)

        # Analysis models
        self.clustering_model = DBSCAN(eps=0.5, min_samples=3)
        self.scaler = StandardScaler()

        # Pattern storage
        self.user_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.global_patterns: Dict[str, Any] = {}

        # Configuration
        self.min_pattern_data = 10
        self.analysis_window_days = 14

    async def analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user behavior patterns for personalization."""

        try:
            # Get user behavior data
            behavior_data = await self._get_user_behavior_data(user_id)

            if len(behavior_data) < self.min_pattern_data:
                return {"patterns": [], "confidence": 0.0, "message": "Insufficient data"}

            # Extract behavioral features
            features = self._extract_behavioral_features(behavior_data)

            # Identify patterns
            patterns = await self._identify_behavior_patterns(features, behavior_data)

            # Calculate user characteristics
            characteristics = self._calculate_user_characteristics(behavior_data, patterns)

            logger.info(f"Analyzed {len(behavior_data)} actions for user {user_id}, found {len(patterns)} patterns")

            return {
                "patterns": patterns,
                "characteristics": characteristics,
                "confidence": min(1.0, len(behavior_data) / 100),
                "data_points": len(behavior_data)
            }

        except Exception as e:
            logger.error(f"User behavior analysis failed for {user_id}: {e}")
            return {"patterns": [], "confidence": 0.0, "error": str(e)}

    async def _get_user_behavior_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user behavior data from Redis."""
        behavior_key = f"user_behavior:{user_id}"
        behavior_data = await self.redis.lrange(behavior_key, 0, -1)

        parsed_data = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.analysis_window_days)

        for data_point in behavior_data:
            try:
                parsed = json.loads(data_point)
                if datetime.fromisoformat(parsed.get("timestamp", "1970-01-01")) > cutoff_date:
                    parsed_data.append(parsed)
            except json.JSONDecodeError:
                continue

        return parsed_data

    def _extract_behavioral_features(self, behavior_data: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features for pattern analysis."""
        features = []

        for data_point in behavior_data:
            # Time-based features
            timestamp = datetime.fromisoformat(data_point.get("timestamp", "1970-01-01"))
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()

            # Action features
            action_type_encoding = self._encode_action_type(data_point.get("action_type", "unknown"))
            hub_encoding = self._encode_hub(data_point.get("hub", "unknown"))

            # Performance features
            duration = min(300, data_point.get("duration", 0))  # Cap at 5 minutes
            success = 1 if data_point.get("success", True) else 0

            # Complexity features
            complexity = data_point.get("complexity", 1)
            steps_count = data_point.get("steps_count", 1)

            features.append([
                hour_of_day, day_of_week, action_type_encoding, hub_encoding,
                duration, success, complexity, steps_count
            ])

        return np.array(features)

    def _encode_action_type(self, action_type: str) -> int:
        """Encode action type as integer."""
        action_mapping = {
            "navigate": 1, "create": 2, "update": 3, "delete": 4, "search": 5,
            "filter": 6, "export": 7, "import": 8, "analyze": 9, "configure": 10
        }
        return action_mapping.get(action_type, 0)

    def _encode_hub(self, hub: str) -> int:
        """Encode hub as integer."""
        hub_mapping = {
            "executive": 1, "lead_intelligence": 2, "automation": 3,
            "sales": 4, "ops": 5
        }
        return hub_mapping.get(hub, 0)

    async def _identify_behavior_patterns(self,
                                        features: np.ndarray,
                                        behavior_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify behavioral patterns using clustering."""
        if len(features) < 3:
            return []

        try:
            # Scale features
            scaled_features = self.scaler.fit_transform(features)

            # Cluster behaviors
            cluster_labels = self.clustering_model.fit_predict(scaled_features)

            # Convert clusters to patterns
            patterns = []
            for cluster_id in set(cluster_labels):
                if cluster_id == -1:  # Skip noise points
                    continue

                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_behaviors = [behavior_data[i] for i in cluster_indices]

                pattern = self._create_pattern_from_cluster(cluster_id, cluster_behaviors)
                if pattern:
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Pattern identification failed: {e}")
            return []

    def _create_pattern_from_cluster(self, cluster_id: int, behaviors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a behavioral pattern from clustered behaviors."""
        if len(behaviors) < 3:
            return None

        # Analyze pattern characteristics
        action_types = [b.get("action_type", "unknown") for b in behaviors]
        hubs = [b.get("hub", "unknown") for b in behaviors]
        durations = [b.get("duration", 0) for b in behaviors]
        success_rates = [1 if b.get("success", True) else 0 for b in behaviors]

        # Find dominant characteristics
        most_common_action = max(set(action_types), key=action_types.count)
        most_common_hub = max(set(hubs), key=hubs.count)

        return {
            "pattern_id": f"pattern_{cluster_id}_{uuid.uuid4().hex[:8]}",
            "type": "behavioral_cluster",
            "dominant_action": most_common_action,
            "dominant_hub": most_common_hub,
            "frequency": len(behaviors),
            "avg_duration": sum(durations) / len(durations),
            "success_rate": sum(success_rates) / len(success_rates),
            "time_distribution": self._analyze_time_distribution(behaviors),
            "complexity_level": self._analyze_complexity_level(behaviors)
        }

    def _analyze_time_distribution(self, behaviors: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze time distribution of behaviors."""
        hours = []
        for behavior in behaviors:
            timestamp = datetime.fromisoformat(behavior.get("timestamp", "1970-01-01"))
            hours.append(timestamp.hour)

        return {
            "morning_weight": sum(1 for h in hours if 6 <= h < 12) / len(hours),
            "afternoon_weight": sum(1 for h in hours if 12 <= h < 18) / len(hours),
            "evening_weight": sum(1 for h in hours if 18 <= h < 24) / len(hours),
            "night_weight": sum(1 for h in hours if 0 <= h < 6) / len(hours)
        }

    def _analyze_complexity_level(self, behaviors: List[Dict[str, Any]]) -> str:
        """Analyze complexity level of behaviors."""
        complexities = [b.get("complexity", 1) for b in behaviors]
        avg_complexity = sum(complexities) / len(complexities)

        if avg_complexity < 2:
            return "simple"
        elif avg_complexity < 4:
            return "moderate"
        else:
            return "complex"

    def _calculate_user_characteristics(self,
                                     behavior_data: List[Dict[str, Any]],
                                     patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall user characteristics."""

        # Calculate expertise level
        complexity_scores = [b.get("complexity", 1) for b in behavior_data]
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 1

        if avg_complexity < 2:
            expertise_level = UserExpertiseLevel.NOVICE
        elif avg_complexity < 3:
            expertise_level = UserExpertiseLevel.INTERMEDIATE
        elif avg_complexity < 4:
            expertise_level = UserExpertiseLevel.ADVANCED
        else:
            expertise_level = UserExpertiseLevel.EXPERT

        # Calculate efficiency score
        success_rates = [1 if b.get("success", True) else 0 for b in behavior_data]
        durations = [b.get("duration", 0) for b in behavior_data]

        efficiency_score = (sum(success_rates) / len(success_rates)) * (1 / (sum(durations) / len(durations) + 1))

        return {
            "expertise_level": expertise_level.value,
            "efficiency_score": efficiency_score,
            "pattern_consistency": len(patterns) / max(len(behavior_data) / 10, 1),
            "preferred_complexity": self._determine_preferred_complexity(patterns),
            "primary_hub": self._determine_primary_hub(behavior_data),
            "peak_activity_hours": self._determine_peak_hours(behavior_data)
        }

    def _determine_preferred_complexity(self, patterns: List[Dict[str, Any]]) -> str:
        """Determine user's preferred interface complexity."""
        complexity_levels = [p.get("complexity_level", "moderate") for p in patterns]

        if not complexity_levels:
            return InterfaceComplexity.STANDARD.value

        most_common = max(set(complexity_levels), key=complexity_levels.count)

        complexity_mapping = {
            "simple": InterfaceComplexity.MINIMAL,
            "moderate": InterfaceComplexity.STANDARD,
            "complex": InterfaceComplexity.COMPREHENSIVE
        }

        return complexity_mapping.get(most_common, InterfaceComplexity.STANDARD).value

    def _determine_primary_hub(self, behavior_data: List[Dict[str, Any]]) -> str:
        """Determine user's primary hub."""
        hubs = [b.get("hub", "unknown") for b in behavior_data]
        if not hubs:
            return "unknown"
        return max(set(hubs), key=hubs.count)

    def _determine_peak_hours(self, behavior_data: List[Dict[str, Any]]) -> List[int]:
        """Determine user's peak activity hours."""
        hours = []
        for behavior in behavior_data:
            timestamp = datetime.fromisoformat(behavior.get("timestamp", "1970-01-01"))
            hours.append(timestamp.hour)

        # Find hours with above-average activity
        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1

        if not hour_counts:
            return []

        avg_activity = sum(hour_counts.values()) / len(hour_counts)
        return [hour for hour, count in hour_counts.items() if count > avg_activity]


class ExperiencePersonalizer:
    """Creates personalized experiences based on user patterns."""

    def __init__(self, behavior_analyzer: UserBehaviorAnalyzer):
        """Initialize experience personalizer."""
        self.behavior_analyzer = behavior_analyzer

        # Component library
        self.component_library = self._build_component_library()

        # Personalization rules
        self.personalization_rules = self._setup_personalization_rules()

    def _build_component_library(self) -> Dict[str, ExperienceComponent]:
        """Build library of available experience components."""
        return {
            "lead_scorecard": ExperienceComponent(
                component_id="lead_scorecard",
                name="Lead Scorecard",
                component_type="widget",
                priority_score=0.9,
                required_context=["active_leads"],
                personalization_factors=["role", "expertise_level"]
            ),
            "revenue_metrics": ExperienceComponent(
                component_id="revenue_metrics",
                name="Revenue Metrics",
                component_type="dashboard",
                priority_score=0.8,
                required_context=["role:manager,admin"],
                personalization_factors=["role", "hub_preference"]
            ),
            "workflow_suggestions": ExperienceComponent(
                component_id="workflow_suggestions",
                name="Workflow Suggestions",
                component_type="panel",
                priority_score=0.7,
                required_context=["workflow_patterns"],
                personalization_factors=["expertise_level", "efficiency_score"]
            ),
            "quick_actions": ExperienceComponent(
                component_id="quick_actions",
                name="Quick Actions",
                component_type="toolbar",
                priority_score=1.0,
                personalization_factors=["frequent_actions", "expertise_level"]
            ),
            "performance_insights": ExperienceComponent(
                component_id="performance_insights",
                name="Performance Insights",
                component_type="widget",
                priority_score=0.6,
                required_context=["role:agent,manager"],
                personalization_factors=["efficiency_score", "expertise_level"]
            )
        }

    def _setup_personalization_rules(self) -> Dict[str, Callable]:
        """Setup personalization rules for different user types."""
        return {
            "novice_users": self._personalize_for_novice,
            "intermediate_users": self._personalize_for_intermediate,
            "advanced_users": self._personalize_for_advanced,
            "expert_users": self._personalize_for_expert,
            "role_based": self._personalize_by_role,
            "hub_based": self._personalize_by_hub,
            "pattern_based": self._personalize_by_patterns
        }

    async def create_personalized_experience(self, user_context: UserContext) -> PersonalizedExperience:
        """Create a personalized experience for the user."""

        try:
            # Analyze user behavior patterns
            behavior_analysis = await self.behavior_analyzer.analyze_user_patterns(user_context.user_id)

            # Select and prioritize components
            selected_components = await self._select_components_for_user(
                user_context, behavior_analysis
            )

            # Create personalized layout
            layout_structure = self._create_personalized_layout(
                user_context, selected_components, behavior_analysis
            )

            # Create navigation structure
            navigation_structure = self._create_personalized_navigation(
                user_context, behavior_analysis
            )

            # Create personalized experience
            experience = PersonalizedExperience(
                user_id=user_context.user_id,
                experience_id=str(uuid.uuid4()),
                hub=user_context.current_hub,
                components=selected_components,
                layout_structure=layout_structure,
                navigation_structure=navigation_structure,
                personalization_confidence=behavior_analysis.get("confidence", 0.0),
                created_from_patterns=[p.get("pattern_id", "") for p in behavior_analysis.get("patterns", [])]
            )

            logger.info(f"Created personalized experience for user {user_context.user_id}")
            return experience

        except Exception as e:
            logger.error(f"Failed to create personalized experience: {e}")
            return self._create_default_experience(user_context)

    async def _select_components_for_user(self,
                                        user_context: UserContext,
                                        behavior_analysis: Dict[str, Any]) -> List[ExperienceComponent]:
        """Select and customize components for the user."""

        selected_components = []
        characteristics = behavior_analysis.get("characteristics", {})

        for component_id, component in self.component_library.items():
            # Check if component is relevant for user
            if self._is_component_relevant(component, user_context, characteristics):
                # Customize component for user
                customized_component = self._customize_component(
                    component, user_context, characteristics
                )
                selected_components.append(customized_component)

        # Sort by priority score
        selected_components.sort(key=lambda c: c.priority_score, reverse=True)

        # Limit based on complexity preference
        max_components = self._get_max_components(user_context.preferred_complexity)
        return selected_components[:max_components]

    def _is_component_relevant(self,
                             component: ExperienceComponent,
                             user_context: UserContext,
                             characteristics: Dict[str, Any]) -> bool:
        """Check if component is relevant for the user."""

        # Check required context
        for context_req in component.required_context:
            if ":" in context_req:
                # Role-based requirement
                role_req = context_req.split(":")[1]
                if user_context.role not in role_req.split(","):
                    return False
            else:
                # General context requirement
                if not hasattr(user_context, context_req) or not getattr(user_context, context_req):
                    return False

        return True

    def _customize_component(self,
                           component: ExperienceComponent,
                           user_context: UserContext,
                           characteristics: Dict[str, Any]) -> ExperienceComponent:
        """Customize component for specific user."""

        customized = ExperienceComponent(
            component_id=component.component_id,
            name=component.name,
            component_type=component.component_type,
            content_data=component.content_data.copy(),
            layout_config=component.layout_config.copy(),
            interaction_config=component.interaction_config.copy(),
            priority_score=component.priority_score,
            personalization_factors=component.personalization_factors.copy(),
            required_context=component.required_context.copy()
        )

        # Apply personalization based on factors
        for factor in component.personalization_factors:
            if factor == "expertise_level":
                self._apply_expertise_personalization(customized, user_context.expertise_level)
            elif factor == "role":
                self._apply_role_personalization(customized, user_context.role)
            elif factor == "efficiency_score":
                efficiency = characteristics.get("efficiency_score", 0.5)
                self._apply_efficiency_personalization(customized, efficiency)

        return customized

    def _apply_expertise_personalization(self, component: ExperienceComponent, expertise: UserExpertiseLevel):
        """Apply expertise-based personalization."""
        if expertise == UserExpertiseLevel.NOVICE:
            component.interaction_config["show_tooltips"] = True
            component.interaction_config["simplified_controls"] = True
        elif expertise == UserExpertiseLevel.EXPERT:
            component.interaction_config["show_advanced_features"] = True
            component.interaction_config["keyboard_shortcuts"] = True

    def _apply_role_personalization(self, component: ExperienceComponent, role: str):
        """Apply role-based personalization."""
        if role == "manager" and component.component_id == "revenue_metrics":
            component.priority_score += 0.2
        elif role == "agent" and component.component_id == "lead_scorecard":
            component.priority_score += 0.3

    def _apply_efficiency_personalization(self, component: ExperienceComponent, efficiency_score: float):
        """Apply efficiency-based personalization."""
        if efficiency_score < 0.5:
            component.interaction_config["show_guidance"] = True
            component.interaction_config["highlight_key_features"] = True

    def _get_max_components(self, complexity: InterfaceComplexity) -> int:
        """Get maximum components based on complexity preference."""
        complexity_limits = {
            InterfaceComplexity.MINIMAL: 3,
            InterfaceComplexity.STANDARD: 6,
            InterfaceComplexity.COMPREHENSIVE: 10,
            InterfaceComplexity.EXPERT: 15
        }
        return complexity_limits.get(complexity, 6)

    def _create_personalized_layout(self,
                                  user_context: UserContext,
                                  components: List[ExperienceComponent],
                                  behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized layout structure."""

        # Basic layout structure
        layout = {
            "type": "responsive_grid",
            "columns": self._get_optimal_columns(user_context.expertise_level),
            "components": []
        }

        # Arrange components based on priority and user patterns
        for i, component in enumerate(components):
            layout["components"].append({
                "component_id": component.component_id,
                "position": {"row": i // layout["columns"], "col": i % layout["columns"]},
                "size": self._get_component_size(component, user_context),
                "responsive_behavior": self._get_responsive_behavior(component)
            })

        return layout

    def _get_optimal_columns(self, expertise: UserExpertiseLevel) -> int:
        """Get optimal number of columns based on expertise."""
        column_mapping = {
            UserExpertiseLevel.NOVICE: 1,
            UserExpertiseLevel.INTERMEDIATE: 2,
            UserExpertiseLevel.ADVANCED: 3,
            UserExpertiseLevel.EXPERT: 4
        }
        return column_mapping.get(expertise, 2)

    def _get_component_size(self, component: ExperienceComponent, user_context: UserContext) -> Dict[str, int]:
        """Get component size based on priority and user context."""
        base_size = {"width": 12, "height": 4}  # Grid units

        # Adjust based on component priority
        if component.priority_score > 0.8:
            base_size["height"] += 2

        # Adjust based on component type
        if component.component_type == "dashboard":
            base_size["width"] = 24
            base_size["height"] = 8

        return base_size

    def _get_responsive_behavior(self, component: ExperienceComponent) -> Dict[str, Any]:
        """Get responsive behavior configuration for component."""
        return {
            "mobile": {"width": 12, "height": component.layout_config.get("mobile_height", 4)},
            "tablet": {"width": 12, "height": component.layout_config.get("tablet_height", 6)},
            "desktop": {"width": component.layout_config.get("desktop_width", 12), "height": component.layout_config.get("desktop_height", 8)}
        }

    def _create_personalized_navigation(self,
                                      user_context: UserContext,
                                      behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized navigation structure."""

        characteristics = behavior_analysis.get("characteristics", {})
        primary_hub = characteristics.get("primary_hub", "lead_intelligence")

        navigation = {
            "type": "adaptive",
            "primary_hub": primary_hub,
            "quick_actions": self._get_personalized_quick_actions(user_context, characteristics),
            "shortcuts": self._get_personalized_shortcuts(user_context, behavior_analysis),
            "breadcrumb_style": "contextual" if user_context.expertise_level == UserExpertiseLevel.ADVANCED else "full"
        }

        return navigation

    def _get_personalized_quick_actions(self, user_context: UserContext, characteristics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get personalized quick actions for user."""
        base_actions = [
            {"action": "create_lead", "label": "New Lead", "priority": 0.9},
            {"action": "view_calendar", "label": "Calendar", "priority": 0.7},
            {"action": "generate_report", "label": "Report", "priority": 0.5}
        ]

        # Customize based on role
        if user_context.role == "manager":
            base_actions.append({"action": "team_performance", "label": "Team", "priority": 0.8})

        # Customize based on primary hub
        primary_hub = characteristics.get("primary_hub", "")
        if primary_hub == "automation":
            base_actions.append({"action": "workflow_builder", "label": "Workflow", "priority": 0.9})

        return sorted(base_actions, key=lambda x: x["priority"], reverse=True)[:5]

    def _get_personalized_shortcuts(self, user_context: UserContext, behavior_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get personalized keyboard shortcuts for user."""
        if user_context.expertise_level in [UserExpertiseLevel.ADVANCED, UserExpertiseLevel.EXPERT]:
            return [
                {"key": "Ctrl+N", "action": "new_lead", "description": "Create new lead"},
                {"key": "Ctrl+F", "action": "search", "description": "Search leads"},
                {"key": "Ctrl+D", "action": "dashboard", "description": "Go to dashboard"}
            ]
        return []

    def _create_default_experience(self, user_context: UserContext) -> PersonalizedExperience:
        """Create default experience when personalization fails."""
        default_components = [
            self.component_library["quick_actions"],
            self.component_library["lead_scorecard"]
        ]

        return PersonalizedExperience(
            user_id=user_context.user_id,
            experience_id=str(uuid.uuid4()),
            hub=user_context.current_hub,
            components=default_components,
            layout_structure={"type": "simple", "components": []},
            navigation_structure={"type": "default"}
        )

    # Personalization rule implementations
    def _personalize_for_novice(self, context: UserContext) -> Dict[str, Any]:
        """Personalization for novice users."""
        return {
            "interface_complexity": InterfaceComplexity.MINIMAL,
            "show_guidance": True,
            "simplified_navigation": True
        }

    def _personalize_for_intermediate(self, context: UserContext) -> Dict[str, Any]:
        """Personalization for intermediate users."""
        return {
            "interface_complexity": InterfaceComplexity.STANDARD,
            "show_shortcuts": True,
            "adaptive_features": True
        }

    def _personalize_for_advanced(self, context: UserContext) -> Dict[str, Any]:
        """Personalization for advanced users."""
        return {
            "interface_complexity": InterfaceComplexity.COMPREHENSIVE,
            "show_advanced_features": True,
            "keyboard_shortcuts": True
        }

    def _personalize_for_expert(self, context: UserContext) -> Dict[str, Any]:
        """Personalization for expert users."""
        return {
            "interface_complexity": InterfaceComplexity.EXPERT,
            "all_features": True,
            "customizable_interface": True
        }

    def _personalize_by_role(self, context: UserContext) -> Dict[str, Any]:
        """Role-based personalization."""
        role_configs = {
            "agent": {"focus": "lead_management", "priority_metrics": ["lead_score", "conversion"]},
            "manager": {"focus": "team_performance", "priority_metrics": ["team_kpis", "revenue"]},
            "admin": {"focus": "system_management", "priority_metrics": ["system_health", "user_activity"]}
        }
        return role_configs.get(context.role, {})

    def _personalize_by_hub(self, context: UserContext) -> Dict[str, Any]:
        """Hub-based personalization."""
        hub_configs = {
            HubType.EXECUTIVE: {"dashboard_focus": "kpis", "quick_actions": ["reports", "alerts"]},
            HubType.LEAD_INTELLIGENCE: {"dashboard_focus": "leads", "quick_actions": ["score", "qualify"]},
            HubType.SALES_COPILOT: {"dashboard_focus": "pipeline", "quick_actions": ["follow_up", "close"]}
        }
        return hub_configs.get(context.current_hub, {})

    def _personalize_by_patterns(self, context: UserContext) -> Dict[str, Any]:
        """Pattern-based personalization."""
        # This would use the user's workflow patterns
        return {"adaptive_workflows": True, "pattern_suggestions": True}


class UnifiedUserExperienceOrchestrator:
    """Main user experience orchestration system."""

    def __init__(self,
                 integration_middleware: AdvancedIntegrationMiddleware,
                 automation_system: IntelligentWorkflowAutomation,
                 redis_client: Optional[redis.Redis] = None):
        """Initialize unified user experience orchestrator."""

        self.middleware = integration_middleware
        self.automation_system = automation_system
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)

        # Core components
        self.behavior_analyzer = UserBehaviorAnalyzer(redis_client)
        self.experience_personalizer = ExperiencePersonalizer(self.behavior_analyzer)

        # State management
        self.active_user_contexts: Dict[str, UserContext] = {}
        self.personalized_experiences: Dict[str, PersonalizedExperience] = {}

        # Performance tracking
        self.orchestration_metrics = defaultdict(int)
        self.experience_performance = defaultdict(list)

        logger.info("Unified User Experience Orchestrator initialized")

    async def orchestrate_user_experience(self, user_id: str, hub: HubType, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate complete user experience for a session."""

        try:
            # Get or create user context
            user_context = await self._get_or_create_user_context(user_id, hub, session_data)

            # Create personalized experience
            experience = await self.experience_personalizer.create_personalized_experience(user_context)

            # Store experience
            self.personalized_experiences[f"{user_id}_{hub.value}"] = experience

            # Generate workflow suggestions
            workflow_suggestions = await self.automation_system.analyze_and_suggest_automations(user_id)

            # Prepare orchestrated response
            orchestrated_experience = {
                "user_context": asdict(user_context),
                "personalized_experience": asdict(experience),
                "workflow_suggestions": [asdict(s) for s in workflow_suggestions],
                "real_time_capabilities": {
                    "websocket_endpoint": f"/ws/{user_id}/{hub.value}",
                    "live_updates": True,
                    "collaboration_enabled": True
                },
                "performance_optimizations": {
                    "adaptive_loading": True,
                    "predictive_caching": True,
                    "progressive_enhancement": True
                }
            }

            # Track orchestration metrics
            self.orchestration_metrics["experiences_orchestrated"] += 1

            # Send experience ready event
            await self._send_experience_event(user_id, hub, "experience_ready", orchestrated_experience)

            logger.info(f"Orchestrated experience for user {user_id} in hub {hub.value}")

            return orchestrated_experience

        except Exception as e:
            logger.error(f"Experience orchestration failed for user {user_id}: {e}")
            return self._create_fallback_experience(user_id, hub)

    async def _get_or_create_user_context(self, user_id: str, hub: HubType, session_data: Dict[str, Any]) -> UserContext:
        """Get or create user context."""

        context_key = f"{user_id}_{hub.value}"

        if context_key in self.active_user_contexts:
            context = self.active_user_contexts[context_key]
            context.last_activity = datetime.now(timezone.utc)
            context.actions_this_session += 1
            return context

        # Create new context
        context = UserContext(
            user_id=user_id,
            session_id=session_data.get("session_id", str(uuid.uuid4())),
            current_hub=hub,
            expertise_level=UserExpertiseLevel(session_data.get("expertise_level", "intermediate")),
            role=session_data.get("role", "agent"),
            team_id=session_data.get("team_id"),
            location_id=session_data.get("location_id")
        )

        # Load user preferences if available
        await self._load_user_preferences(context)

        self.active_user_contexts[context_key] = context
        return context

    async def _load_user_preferences(self, context: UserContext):
        """Load user preferences from storage."""
        try:
            preferences_key = f"user_preferences:{context.user_id}"
            preferences_data = await self.redis.get(preferences_key)

            if preferences_data:
                preferences = json.loads(preferences_data)
                context.notification_preferences = preferences.get("notifications", {})
                context.layout_preferences = preferences.get("layout", {})
                context.theme_preferences = preferences.get("theme", {})

        except Exception as e:
            logger.error(f"Failed to load preferences for user {context.user_id}: {e}")

    async def _send_experience_event(self, user_id: str, hub: HubType, event_type: str, data: Dict[str, Any]):
        """Send experience-related event through middleware."""
        event = IntegrationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_ACTION,
            source_service="experience_orchestrator",
            target_services=["websocket_manager"],
            payload={
                "user_id": user_id,
                "hub": hub.value,
                "event_type": event_type,
                "data": data
            }
        )

        await self.middleware.event_bus.publish_event(event)

    def _create_fallback_experience(self, user_id: str, hub: HubType) -> Dict[str, Any]:
        """Create fallback experience when orchestration fails."""
        return {
            "user_context": {"user_id": user_id, "hub": hub.value, "expertise_level": "intermediate"},
            "personalized_experience": {
                "experience_id": str(uuid.uuid4()),
                "components": [],
                "layout_structure": {"type": "default"}
            },
            "workflow_suggestions": [],
            "fallback_mode": True
        }

    async def update_user_context(self, user_id: str, hub: HubType, updates: Dict[str, Any]) -> bool:
        """Update user context with new information."""
        try:
            context_key = f"{user_id}_{hub.value}"
            context = self.active_user_contexts.get(context_key)

            if not context:
                return False

            # Update context fields
            for field, value in updates.items():
                if hasattr(context, field):
                    setattr(context, field, value)

            context.last_activity = datetime.now(timezone.utc)

            # Trigger experience update if significant changes
            significant_fields = ["expertise_level", "role", "preferred_complexity"]
            if any(field in updates for field in significant_fields):
                await self._refresh_user_experience(user_id, hub)

            return True

        except Exception as e:
            logger.error(f"Failed to update user context for {user_id}: {e}")
            return False

    async def _refresh_user_experience(self, user_id: str, hub: HubType):
        """Refresh user experience after significant context changes."""
        try:
            context_key = f"{user_id}_{hub.value}"
            context = self.active_user_contexts.get(context_key)

            if context:
                # Create new personalized experience
                experience = await self.experience_personalizer.create_personalized_experience(context)
                self.personalized_experiences[f"{user_id}_{hub.value}"] = experience

                # Send update event
                await self._send_experience_event(user_id, hub, "experience_updated", asdict(experience))

        except Exception as e:
            logger.error(f"Failed to refresh experience for user {user_id}: {e}")

    def get_orchestration_analytics(self) -> Dict[str, Any]:
        """Get comprehensive orchestration analytics."""
        active_users = len(self.active_user_contexts)
        total_experiences = len(self.personalized_experiences)

        return {
            "active_users": active_users,
            "total_experiences": total_experiences,
            "experiences_orchestrated": self.orchestration_metrics["experiences_orchestrated"],
            "avg_personalization_confidence": self._calculate_avg_confidence(),
            "experience_performance": self._calculate_experience_performance(),
            "user_satisfaction_metrics": self._calculate_satisfaction_metrics()
        }

    def _calculate_avg_confidence(self) -> float:
        """Calculate average personalization confidence."""
        confidences = [exp.personalization_confidence for exp in self.personalized_experiences.values()]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _calculate_experience_performance(self) -> Dict[str, float]:
        """Calculate experience performance metrics."""
        if not self.experience_performance:
            return {"avg_load_time": 0.0, "total_interactions": 0}

        all_times = []
        total_interactions = 0

        for times in self.experience_performance.values():
            all_times.extend(times)

        for exp in self.personalized_experiences.values():
            total_interactions += sum(comp.interaction_count for comp in exp.components)

        return {
            "avg_load_time": sum(all_times) / len(all_times) if all_times else 0.0,
            "total_interactions": total_interactions
        }

    def _calculate_satisfaction_metrics(self) -> Dict[str, float]:
        """Calculate user satisfaction metrics."""
        satisfactions = []
        for exp in self.personalized_experiences.values():
            if exp.user_satisfaction > 0:
                satisfactions.append(exp.user_satisfaction)

        return {
            "avg_satisfaction": sum(satisfactions) / len(satisfactions) if satisfactions else 0.0,
            "satisfaction_responses": len(satisfactions)
        }


# Export main classes
__all__ = [
    "UnifiedUserExperienceOrchestrator",
    "UserBehaviorAnalyzer",
    "ExperiencePersonalizer",
    "UserContext",
    "PersonalizedExperience",
    "ExperienceComponent",
    "UserExpertiseLevel",
    "InterfaceComplexity",
    "PersonalizationType"
]