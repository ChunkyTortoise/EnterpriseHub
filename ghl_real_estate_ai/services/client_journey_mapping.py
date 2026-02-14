"""
Client Journey Mapping Service - Phase 1 Foundation Service (Track B)

Maps and optimizes the complete client journey from qualification to advocate:
- Post-qualification journey stage tracking
- Milestone progression monitoring
- Journey optimization recommendations
- Client experience personalization
- Real-time journey health monitoring

Integrates with:
- Event Publisher for real-time journey updates
- Memory Service for client context persistence
- Cache Service for performance optimization
- Enhanced Lead Scoring for qualification handoff
"""

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import TenantScopedCache, get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.memory_service import get_memory_service

logger = get_logger(__name__)


class JourneyStage(Enum):
    """Client journey stages in real estate transaction lifecycle."""

    QUALIFIED = "qualified"
    PROPERTY_SEARCH = "property_search"
    PROPERTY_VIEWING = "property_viewing"
    OFFER_PREPARATION = "offer_preparation"
    NEGOTIATION = "negotiation"
    UNDER_CONTRACT = "under_contract"
    INSPECTION_PERIOD = "inspection_period"
    FINANCING = "financing"
    CLOSING_PREPARATION = "closing_preparation"
    CLOSED = "closed"
    POST_CLOSING = "post_closing"
    ADVOCATE = "advocate"


class MilestoneType(Enum):
    """Types of milestones in client journey."""

    QUALIFICATION = "qualification"
    PROPERTY_MATCH = "property_match"
    VIEWING_SCHEDULED = "viewing_scheduled"
    OFFER_SUBMITTED = "offer_submitted"
    OFFER_ACCEPTED = "offer_accepted"
    INSPECTION_COMPLETED = "inspection_completed"
    FINANCING_APPROVED = "financing_approved"
    CLOSING_SCHEDULED = "closing_scheduled"
    TRANSACTION_CLOSED = "transaction_closed"
    REFERRAL_GENERATED = "referral_generated"
    REVIEW_SUBMITTED = "review_submitted"


class JourneyHealthStatus(Enum):
    """Journey health assessment statuses."""

    EXCELLENT = "excellent"
    GOOD = "good"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    STALLED = "stalled"


@dataclass
class JourneyMilestone:
    """Individual milestone in client journey."""

    milestone_id: str
    client_id: str
    location_id: str
    milestone_type: MilestoneType
    stage: JourneyStage

    # Milestone Details
    title: str
    description: str
    expected_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    completion_status: str = "pending"  # pending, in_progress, completed, skipped, failed

    # Progress Tracking
    progress_percentage: float = 0.0
    blocking_issues: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)

    # Automation & Personalization
    automated_actions_triggered: List[str] = field(default_factory=list)
    personalization_applied: Dict[str, Any] = field(default_factory=dict)
    engagement_score: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    estimated_duration_days: Optional[int] = None
    priority_level: str = "normal"  # low, normal, high, critical


@dataclass
class JourneyHealthMetrics:
    """Client journey health assessment."""

    client_id: str
    location_id: str
    current_stage: JourneyStage
    health_status: JourneyHealthStatus

    # Performance Metrics
    overall_progress_percentage: float
    milestones_completed: int
    milestones_total: int
    milestones_overdue: int

    # Timing Analysis
    journey_duration_days: int
    expected_completion_date: Optional[datetime] = None
    projected_delay_days: int = 0
    velocity_score: float = 0.0  # Progress rate vs. expected

    # Engagement Metrics
    client_engagement_score: float = 0.0
    communication_responsiveness: float = 0.0
    satisfaction_indicators: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)

    # Intervention Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    automation_opportunities: List[str] = field(default_factory=list)
    escalation_needed: bool = False

    # Metadata
    last_assessment: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    assessment_confidence: float = 0.0


@dataclass
class JourneyPersonalization:
    """Personalization settings for client journey."""

    client_id: str
    location_id: str

    # Communication Preferences
    preferred_communication_channel: str = "email"  # email, sms, phone, app
    communication_frequency: str = "standard"  # minimal, standard, frequent
    communication_timing: str = "business_hours"  # anytime, business_hours, evenings

    # Content Preferences
    content_detail_level: str = "detailed"  # brief, standard, detailed
    market_update_interest: bool = True
    property_alert_criteria: Dict[str, Any] = field(default_factory=dict)

    # Journey Customization
    milestone_notification_preferences: Dict[str, bool] = field(default_factory=dict)
    automated_check_in_frequency: str = "weekly"  # daily, weekly, biweekly, milestone_based
    priority_focus_areas: List[str] = field(default_factory=list)

    # Experience Optimization
    preferred_agent_characteristics: List[str] = field(default_factory=list)
    stress_level_indicators: List[str] = field(default_factory=list)
    support_intensity_preference: str = "standard"  # minimal, standard, high_touch

    # Learning & Adaptation
    successful_interaction_patterns: List[str] = field(default_factory=list)
    journey_satisfaction_feedback: Dict[str, float] = field(default_factory=dict)
    adaptation_insights: List[str] = field(default_factory=list)


@dataclass
class JourneyOptimizationRecommendation:
    """Journey optimization recommendation."""

    recommendation_id: str
    client_id: str
    location_id: str

    # Recommendation Details
    title: str
    description: str
    category: str  # timing, communication, automation, personalization
    priority: str = "medium"  # low, medium, high, urgent

    # Implementation
    action_items: List[str] = field(default_factory=list)
    estimated_impact: str = ""
    implementation_effort: str = "medium"  # low, medium, high
    timeline: str = "immediate"  # immediate, days, weeks

    # Validation
    expected_outcomes: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    confidence_score: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, accepted, implemented, rejected


class ClientJourneyMappingService:
    """
    Client Journey Mapping and Optimization Service.

    Provides comprehensive client journey intelligence:
    - Real-time journey stage tracking
    - Milestone progression monitoring
    - Journey health assessment
    - Personalization and optimization
    - Predictive journey analytics
    """

    def __init__(self):
        """Initialize the client journey mapping service."""
        self.cache = get_cache_service()
        self.event_publisher = get_event_publisher()
        self.memory_service = get_memory_service()

        # Journey stage progression rules
        self.stage_progression = {
            JourneyStage.QUALIFIED: [JourneyStage.PROPERTY_SEARCH],
            JourneyStage.PROPERTY_SEARCH: [JourneyStage.PROPERTY_VIEWING],
            JourneyStage.PROPERTY_VIEWING: [JourneyStage.OFFER_PREPARATION, JourneyStage.PROPERTY_SEARCH],
            JourneyStage.OFFER_PREPARATION: [JourneyStage.NEGOTIATION],
            JourneyStage.NEGOTIATION: [JourneyStage.UNDER_CONTRACT, JourneyStage.PROPERTY_SEARCH],
            JourneyStage.UNDER_CONTRACT: [JourneyStage.INSPECTION_PERIOD],
            JourneyStage.INSPECTION_PERIOD: [JourneyStage.FINANCING, JourneyStage.PROPERTY_SEARCH],
            JourneyStage.FINANCING: [JourneyStage.CLOSING_PREPARATION],
            JourneyStage.CLOSING_PREPARATION: [JourneyStage.CLOSED],
            JourneyStage.CLOSED: [JourneyStage.POST_CLOSING],
            JourneyStage.POST_CLOSING: [JourneyStage.ADVOCATE],
        }

        # Expected durations for stages (in days)
        self.stage_durations = {
            JourneyStage.QUALIFIED: 3,
            JourneyStage.PROPERTY_SEARCH: 21,
            JourneyStage.PROPERTY_VIEWING: 14,
            JourneyStage.OFFER_PREPARATION: 3,
            JourneyStage.NEGOTIATION: 7,
            JourneyStage.UNDER_CONTRACT: 1,
            JourneyStage.INSPECTION_PERIOD: 10,
            JourneyStage.FINANCING: 21,
            JourneyStage.CLOSING_PREPARATION: 7,
            JourneyStage.CLOSED: 1,
            JourneyStage.POST_CLOSING: 30,
            JourneyStage.ADVOCATE: 365,  # Ongoing
        }

        # Milestone templates for each stage
        self.milestone_templates = self._initialize_milestone_templates()

    async def track_client_journey(
        self,
        client_id: str,
        location_id: str,
        current_stage: JourneyStage,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> JourneyHealthMetrics:
        """
        Track and assess client journey progress.

        Args:
            client_id: Unique client identifier
            location_id: Tenant identifier for isolation
            current_stage: Current journey stage
            context_data: Additional context for journey assessment

        Returns:
            JourneyHealthMetrics with comprehensive assessment
        """
        start_time = time.perf_counter()

        tenant_cache = TenantScopedCache(location_id, self.cache)

        try:
            # 1. Get or Initialize Journey Data
            journey_data = await self._get_journey_data(client_id, location_id, tenant_cache)

            # 2. Update Current Stage if Changed
            if journey_data["current_stage"] != current_stage:
                await self._progress_journey_stage(client_id, location_id, current_stage, journey_data, tenant_cache)

            # 3. Assess Journey Health
            health_metrics = await self._assess_journey_health(client_id, location_id, journey_data)

            # 4. Update Milestones
            await self._update_milestone_progress(client_id, location_id, journey_data, health_metrics, tenant_cache)

            # 5. Apply Personalization
            personalization = await self._get_journey_personalization(client_id, location_id, tenant_cache)
            await self._apply_personalization(client_id, location_id, health_metrics, personalization)

            # 6. Generate Optimization Recommendations
            await self._generate_optimization_recommendations(
                client_id, location_id, health_metrics, journey_data
            )

            processing_time = (time.perf_counter() - start_time) * 1000

            # 7. Cache Updated Data
            await self._cache_journey_data(client_id, location_id, journey_data, health_metrics, tenant_cache)

            # 8. Publish Real-time Events
            await self._publish_journey_events(client_id, location_id, health_metrics, processing_time)

            # 9. Update Memory Service
            await self._update_client_memory(client_id, location_id, health_metrics, journey_data)

            logger.info(
                f"Journey tracking complete for {client_id}: Stage {current_stage.value}, "
                f"Health {health_metrics.health_status.value}, "
                f"{health_metrics.milestones_completed}/{health_metrics.milestones_total} milestones "
                f"[{processing_time:.2f}ms]"
            )

            return health_metrics

        except Exception as e:
            logger.error(f"Journey tracking failed for {client_id}: {e}")
            return self._create_fallback_health_metrics(client_id, location_id, current_stage)

    async def progress_milestone(
        self,
        client_id: str,
        location_id: str,
        milestone_type: MilestoneType,
        completion_data: Optional[Dict[str, Any]] = None,
    ) -> JourneyMilestone:
        """
        Progress a specific milestone in the client journey.

        Args:
            client_id: Client identifier
            location_id: Tenant identifier
            milestone_type: Type of milestone being completed
            completion_data: Additional completion data

        Returns:
            Updated JourneyMilestone
        """
        tenant_cache = TenantScopedCache(location_id, self.cache)

        try:
            # Get current journey data
            journey_data = await self._get_journey_data(client_id, location_id, tenant_cache)
            milestones = journey_data.get("milestones", {})

            # Find and update the milestone
            milestone_id = f"{client_id}_{milestone_type.value}"
            if milestone_id in milestones:
                milestone = milestones[milestone_id]
                milestone["completion_status"] = "completed"
                milestone["actual_completion"] = datetime.now(timezone.utc)
                milestone["progress_percentage"] = 100.0
                milestone["updated_at"] = datetime.now(timezone.utc)

                if completion_data:
                    milestone["completion_data"] = completion_data

                # Update journey data
                journey_data["milestones"] = milestones
                await tenant_cache.set(f"journey_data:{client_id}", journey_data, ttl=3600)

                # Publish milestone completion event
                await self._publish_milestone_event(client_id, location_id, milestone_type, milestone)

                # Check for stage progression
                await self._check_stage_progression(client_id, location_id, journey_data)

                logger.info(f"Milestone completed: {milestone_type.value} for client {client_id}")

                return JourneyMilestone(**milestone)
            else:
                # Create new milestone if not exists
                return await self._create_milestone(client_id, location_id, milestone_type, tenant_cache)

        except Exception as e:
            logger.error(f"Milestone progression failed for {client_id}: {e}")
            raise

    async def personalize_journey(
        self, client_id: str, location_id: str, preferences: Dict[str, Any]
    ) -> JourneyPersonalization:
        """
        Update client journey personalization settings.

        Args:
            client_id: Client identifier
            location_id: Tenant identifier
            preferences: Personalization preferences

        Returns:
            Updated JourneyPersonalization
        """
        tenant_cache = TenantScopedCache(location_id, self.cache)

        try:
            # Get existing personalization or create new
            personalization_data = await tenant_cache.get(f"journey_personalization:{client_id}") or {}

            # Update with new preferences
            personalization_data.update(preferences)
            personalization_data["client_id"] = client_id
            personalization_data["location_id"] = location_id

            personalization = JourneyPersonalization(**personalization_data)

            # Cache updated personalization
            await tenant_cache.set(f"journey_personalization:{client_id}", asdict(personalization), ttl=7200)

            # Apply immediate personalization changes
            await self._apply_immediate_personalization_changes(client_id, location_id, personalization)

            logger.info(f"Journey personalization updated for client {client_id}")

            return personalization

        except Exception as e:
            logger.error(f"Journey personalization failed for {client_id}: {e}")
            raise

    async def get_journey_insights(self, client_id: str, location_id: str) -> Dict[str, Any]:
        """
        Get comprehensive journey insights and analytics.

        Args:
            client_id: Client identifier
            location_id: Tenant identifier

        Returns:
            Journey insights and analytics
        """
        tenant_cache = TenantScopedCache(location_id, self.cache)

        try:
            # Get journey data
            journey_data = await self._get_journey_data(client_id, location_id, tenant_cache)
            health_metrics = await self._assess_journey_health(client_id, location_id, journey_data)

            # Calculate journey analytics
            analytics = await self._calculate_journey_analytics(client_id, location_id, journey_data, health_metrics)

            # Generate insights
            insights = {
                "client_id": client_id,
                "location_id": location_id,
                "current_stage": journey_data["current_stage"],
                "health_status": health_metrics.health_status.value,
                "progress_summary": {
                    "overall_progress": health_metrics.overall_progress_percentage,
                    "milestones_completed": health_metrics.milestones_completed,
                    "milestones_total": health_metrics.milestones_total,
                    "velocity_score": health_metrics.velocity_score,
                },
                "timing_analysis": analytics["timing_analysis"],
                "engagement_metrics": analytics["engagement_metrics"],
                "optimization_opportunities": analytics["optimization_opportunities"],
                "risk_assessment": analytics["risk_assessment"],
                "predictions": analytics["predictions"],
            }

            return insights

        except Exception as e:
            logger.error(f"Journey insights generation failed for {client_id}: {e}")
            return {"error": str(e)}

    async def _get_journey_data(
        self, client_id: str, location_id: str, tenant_cache: TenantScopedCache
    ) -> Dict[str, Any]:
        """Get or initialize client journey data."""

        journey_data = await tenant_cache.get(f"journey_data:{client_id}")

        if not journey_data:
            # Initialize new journey
            journey_data = {
                "client_id": client_id,
                "location_id": location_id,
                "current_stage": JourneyStage.QUALIFIED.value,
                "journey_start_date": datetime.now(timezone.utc).isoformat(),
                "milestones": {},
                "stage_history": [
                    {
                        "stage": JourneyStage.QUALIFIED.value,
                        "entered_at": datetime.now(timezone.utc).isoformat(),
                        "duration_days": 0,
                    }
                ],
                "engagement_events": [],
            }

            # Create initial milestones
            await self._initialize_journey_milestones(client_id, location_id, journey_data, tenant_cache)

        return journey_data

    async def _initialize_journey_milestones(
        self, client_id: str, location_id: str, journey_data: Dict[str, Any], tenant_cache: TenantScopedCache
    ):
        """Initialize milestones for the journey."""

        current_stage = JourneyStage(journey_data["current_stage"])
        milestones = {}

        # Create milestones for current and next stages
        stages_to_process = [current_stage]
        if current_stage in self.stage_progression:
            stages_to_process.extend(self.stage_progression[current_stage])

        for stage in stages_to_process:
            if stage in self.milestone_templates:
                for milestone_type, template in self.milestone_templates[stage].items():
                    milestone_id = f"{client_id}_{milestone_type.value}"
                    milestone = JourneyMilestone(
                        milestone_id=milestone_id,
                        client_id=client_id,
                        location_id=location_id,
                        milestone_type=milestone_type,
                        stage=stage,
                        **template,
                    )
                    milestones[milestone_id] = asdict(milestone)

        journey_data["milestones"] = milestones
        await tenant_cache.set(f"journey_data:{client_id}", journey_data, ttl=3600)

    async def _progress_journey_stage(
        self,
        client_id: str,
        location_id: str,
        new_stage: JourneyStage,
        journey_data: Dict[str, Any],
        tenant_cache: TenantScopedCache,
    ):
        """Progress client to a new journey stage."""

        old_stage = JourneyStage(journey_data["current_stage"])

        # Update stage history
        stage_history = journey_data.get("stage_history", [])
        if stage_history:
            # Update duration for previous stage
            previous_entry = stage_history[-1]
            entered_at = datetime.fromisoformat(previous_entry["entered_at"])
            duration = (datetime.now(timezone.utc) - entered_at).days
            previous_entry["duration_days"] = duration

        # Add new stage entry
        stage_history.append(
            {"stage": new_stage.value, "entered_at": datetime.now(timezone.utc).isoformat(), "duration_days": 0}
        )

        journey_data["current_stage"] = new_stage.value
        journey_data["stage_history"] = stage_history

        # Create milestones for new stage
        await self._create_stage_milestones(client_id, location_id, new_stage, journey_data)

        # Update cache
        await tenant_cache.set(f"journey_data:{client_id}", journey_data, ttl=3600)

        # Publish stage progression event
        await self._publish_stage_progression_event(client_id, location_id, old_stage, new_stage)

        logger.info(f"Client {client_id} progressed: {old_stage.value} → {new_stage.value}")

    async def _assess_journey_health(
        self, client_id: str, location_id: str, journey_data: Dict[str, Any]
    ) -> JourneyHealthMetrics:
        """Assess overall journey health."""

        milestones = journey_data.get("milestones", {})
        current_stage = JourneyStage(journey_data["current_stage"])

        # Calculate milestone statistics
        total_milestones = len(milestones)
        completed_milestones = sum(1 for m in milestones.values() if m["completion_status"] == "completed")
        overdue_milestones = self._count_overdue_milestones(milestones)

        # Calculate overall progress
        overall_progress = (completed_milestones / max(1, total_milestones)) * 100

        # Calculate journey duration
        journey_start = datetime.fromisoformat(journey_data["journey_start_date"])
        journey_duration = (datetime.now(timezone.utc) - journey_start).days

        # Calculate velocity score
        expected_duration = sum(
            self.stage_durations[stage] for stage in self.stage_durations if stage.value <= current_stage.value
        )
        velocity_score = max(0, min(100, (expected_duration / max(1, journey_duration)) * 100))

        # Determine health status
        health_status = self._determine_health_status(
            overall_progress, overdue_milestones, velocity_score, journey_duration
        )

        # Generate recommendations and risk factors
        risk_factors = self._identify_risk_factors(milestones, journey_duration, velocity_score)
        recommended_actions = self._generate_health_recommendations(health_status, risk_factors)

        return JourneyHealthMetrics(
            client_id=client_id,
            location_id=location_id,
            current_stage=current_stage,
            health_status=health_status,
            overall_progress_percentage=round(overall_progress, 1),
            milestones_completed=completed_milestones,
            milestones_total=total_milestones,
            milestones_overdue=overdue_milestones,
            journey_duration_days=journey_duration,
            velocity_score=round(velocity_score, 1),
            risk_factors=risk_factors,
            recommended_actions=recommended_actions,
            assessment_confidence=self._calculate_assessment_confidence(total_milestones, journey_duration),
        )

    def _initialize_milestone_templates(self) -> Dict[JourneyStage, Dict[MilestoneType, Dict[str, Any]]]:
        """Initialize milestone templates for each stage."""

        return {
            JourneyStage.QUALIFIED: {
                MilestoneType.QUALIFICATION: {
                    "title": "Client Qualification Complete",
                    "description": "Client has been qualified and onboarded",
                    "estimated_duration_days": 1,
                    "priority_level": "high",
                }
            },
            JourneyStage.PROPERTY_SEARCH: {
                MilestoneType.PROPERTY_MATCH: {
                    "title": "Initial Property Matches Identified",
                    "description": "Property matches based on client criteria",
                    "estimated_duration_days": 7,
                    "priority_level": "high",
                }
            },
            JourneyStage.PROPERTY_VIEWING: {
                MilestoneType.VIEWING_SCHEDULED: {
                    "title": "Property Viewings Scheduled",
                    "description": "In-person or virtual property viewings arranged",
                    "estimated_duration_days": 3,
                    "priority_level": "high",
                }
            },
            JourneyStage.OFFER_PREPARATION: {
                MilestoneType.OFFER_SUBMITTED: {
                    "title": "Offer Submitted",
                    "description": "Purchase offer submitted to seller",
                    "estimated_duration_days": 2,
                    "priority_level": "critical",
                }
            },
            JourneyStage.NEGOTIATION: {
                MilestoneType.OFFER_ACCEPTED: {
                    "title": "Offer Accepted",
                    "description": "Purchase offer accepted by seller",
                    "estimated_duration_days": 5,
                    "priority_level": "critical",
                }
            },
            JourneyStage.INSPECTION_PERIOD: {
                MilestoneType.INSPECTION_COMPLETED: {
                    "title": "Property Inspection Complete",
                    "description": "Professional property inspection completed",
                    "estimated_duration_days": 7,
                    "priority_level": "high",
                }
            },
            JourneyStage.FINANCING: {
                MilestoneType.FINANCING_APPROVED: {
                    "title": "Financing Approved",
                    "description": "Mortgage financing approved by lender",
                    "estimated_duration_days": 14,
                    "priority_level": "critical",
                }
            },
            JourneyStage.CLOSING_PREPARATION: {
                MilestoneType.CLOSING_SCHEDULED: {
                    "title": "Closing Scheduled",
                    "description": "Final closing meeting scheduled",
                    "estimated_duration_days": 3,
                    "priority_level": "critical",
                }
            },
            JourneyStage.CLOSED: {
                MilestoneType.TRANSACTION_CLOSED: {
                    "title": "Transaction Closed",
                    "description": "Property purchase transaction completed",
                    "estimated_duration_days": 1,
                    "priority_level": "critical",
                }
            },
            JourneyStage.POST_CLOSING: {
                MilestoneType.REFERRAL_GENERATED: {
                    "title": "Client Referral Generated",
                    "description": "Satisfied client provides referral",
                    "estimated_duration_days": 21,
                    "priority_level": "medium",
                },
                MilestoneType.REVIEW_SUBMITTED: {
                    "title": "Review Submitted",
                    "description": "Client submits positive review",
                    "estimated_duration_days": 14,
                    "priority_level": "medium",
                },
            },
        }

    def _count_overdue_milestones(self, milestones: Dict[str, Any]) -> int:
        """Count overdue milestones."""

        overdue_count = 0
        now = datetime.now(timezone.utc)

        for milestone in milestones.values():
            if (
                milestone["completion_status"] != "completed"
                and milestone.get("expected_completion")
                and datetime.fromisoformat(milestone["expected_completion"]) < now
            ):
                overdue_count += 1

        return overdue_count

    def _determine_health_status(
        self, progress: float, overdue_count: int, velocity_score: float, duration_days: int
    ) -> JourneyHealthStatus:
        """Determine overall journey health status."""

        # Calculate health score
        health_score = 0

        # Progress contribution (40%)
        if progress >= 80:
            health_score += 40
        elif progress >= 60:
            health_score += 32
        elif progress >= 40:
            health_score += 24
        elif progress >= 20:
            health_score += 16
        else:
            health_score += 8

        # Overdue penalties (30%)
        if overdue_count == 0:
            health_score += 30
        elif overdue_count == 1:
            health_score += 24
        elif overdue_count == 2:
            health_score += 18
        else:
            health_score += 10  # 3+ overdue

        # Velocity contribution (30%)
        if velocity_score >= 90:
            health_score += 30
        elif velocity_score >= 70:
            health_score += 24
        elif velocity_score >= 50:
            health_score += 18
        else:
            health_score += 12

        # Map to health status
        if health_score >= 90:
            return JourneyHealthStatus.EXCELLENT
        elif health_score >= 75:
            return JourneyHealthStatus.GOOD
        elif health_score >= 60:
            return JourneyHealthStatus.AT_RISK
        elif health_score >= 40:
            return JourneyHealthStatus.CRITICAL
        else:
            return JourneyHealthStatus.STALLED

    def _identify_risk_factors(
        self, milestones: Dict[str, Any], duration_days: int, velocity_score: float
    ) -> List[str]:
        """Identify journey risk factors."""

        risk_factors = []

        # Overdue milestones
        overdue_count = self._count_overdue_milestones(milestones)
        if overdue_count > 0:
            risk_factors.append(f"{overdue_count} overdue milestone(s)")

        # Velocity issues
        if velocity_score < 50:
            risk_factors.append("Below-average progress velocity")

        # Extended duration
        if duration_days > 120:  # 4 months
            risk_factors.append("Extended journey duration")

        # Stalled milestones
        stalled_count = sum(
            1 for m in milestones.values() if m["completion_status"] == "in_progress" and m["progress_percentage"] < 50
        )
        if stalled_count > 1:
            risk_factors.append(f"{stalled_count} stalled milestone(s)")

        return risk_factors

    def _generate_health_recommendations(
        self, health_status: JourneyHealthStatus, risk_factors: List[str]
    ) -> List[str]:
        """Generate health-based recommendations."""

        recommendations = []

        if health_status == JourneyHealthStatus.CRITICAL:
            recommendations.extend(
                [
                    "🚨 Urgent: Schedule immediate client check-in",
                    "📞 Escalate to senior agent or manager",
                    "🔄 Review and adjust journey timeline",
                    "🎯 Focus on removing blocking issues",
                ]
            )
        elif health_status == JourneyHealthStatus.AT_RISK:
            recommendations.extend(
                [
                    "⚠️ Increase communication frequency",
                    "📅 Proactive milestone planning session",
                    "🤝 Provide additional support resources",
                    "📊 Weekly progress monitoring",
                ]
            )
        elif health_status == JourneyHealthStatus.STALLED:
            recommendations.extend(
                [
                    "🔄 Complete journey assessment and reset",
                    "🎯 Identify and remove blockers",
                    "📞 Re-engage client with value-add approach",
                    "⏰ Set aggressive but achievable milestones",
                ]
            )

        # Risk-specific recommendations
        if "overdue" in " ".join(risk_factors):
            recommendations.append("⏰ Prioritize overdue milestone completion")

        if "velocity" in " ".join(risk_factors):
            recommendations.append("🚀 Implement journey acceleration tactics")

        return recommendations[:5]  # Limit to top 5

    def _calculate_assessment_confidence(self, total_milestones: int, journey_duration: int) -> float:
        """Calculate confidence level in the assessment."""

        # More milestones and longer duration = higher confidence
        milestone_score = min(1.0, total_milestones / 10)  # Max at 10 milestones
        duration_score = min(1.0, journey_duration / 30)  # Max at 30 days

        return round((milestone_score * 0.6 + duration_score * 0.4), 3)

    async def _publish_journey_events(
        self, client_id: str, location_id: str, health_metrics: JourneyHealthMetrics, processing_time: float
    ):
        """Publish journey-related events."""

        try:
            # Publish journey health update event
            await self.event_publisher.publish_client_health_update(
                client_id=client_id,
                health_status=health_metrics.health_status.value,
                progress_percentage=health_metrics.overall_progress_percentage,
                risk_factors=health_metrics.risk_factors,
                location_id=location_id,
            )

        except Exception as e:
            logger.warning(f"Failed to publish journey events: {e}")

    async def _update_client_memory(
        self, client_id: str, location_id: str, health_metrics: JourneyHealthMetrics, journey_data: Dict[str, Any]
    ):
        """Update client memory with journey information."""

        try:
            journey_context = {
                "current_stage": health_metrics.current_stage.value,
                "health_status": health_metrics.health_status.value,
                "progress_percentage": health_metrics.overall_progress_percentage,
                "milestones_completed": health_metrics.milestones_completed,
                "velocity_score": health_metrics.velocity_score,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            await self.memory_service.store_journey_context(client_id, location_id, journey_context)

        except Exception as e:
            logger.warning(f"Failed to update client memory: {e}")

    def _create_fallback_health_metrics(
        self, client_id: str, location_id: str, current_stage: JourneyStage
    ) -> JourneyHealthMetrics:
        """Create fallback health metrics when assessment fails."""

        return JourneyHealthMetrics(
            client_id=client_id,
            location_id=location_id,
            current_stage=current_stage,
            health_status=JourneyHealthStatus.AT_RISK,
            overall_progress_percentage=0.0,
            milestones_completed=0,
            milestones_total=1,
            milestones_overdue=0,
            journey_duration_days=0,
            velocity_score=0.0,
            recommended_actions=["Manual review required - assessment failed"],
            assessment_confidence=0.1,
        )


# Singleton accessor following established pattern
_client_journey_mapping_service = None


def get_client_journey_mapping() -> ClientJourneyMappingService:
    """Get singleton client journey mapping service instance."""
    global _client_journey_mapping_service
    if _client_journey_mapping_service is None:
        _client_journey_mapping_service = ClientJourneyMappingService()
    return _client_journey_mapping_service


# Convenience functions for common operations
async def track_journey_progress(
    client_id: str, location_id: str, current_stage: JourneyStage, **kwargs
) -> JourneyHealthMetrics:
    """Convenience function for journey progress tracking."""
    service = get_client_journey_mapping()
    return await service.track_client_journey(client_id, location_id, current_stage, **kwargs)


async def complete_milestone(
    client_id: str, location_id: str, milestone_type: MilestoneType, **kwargs
) -> JourneyMilestone:
    """Convenience function for milestone completion."""
    service = get_client_journey_mapping()
    return await service.progress_milestone(client_id, location_id, milestone_type, **kwargs)
