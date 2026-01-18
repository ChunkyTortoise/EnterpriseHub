"""
Consulting Delivery Service - Engagement Management System

Manages structured delivery of high-ticket consulting engagements ($25K-$100K).
Provides project management, stakeholder coordination, and success measurement.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class EngagementTier(Enum):
    """High-ticket consulting engagement tiers."""
    ACCELERATOR = "accelerator"      # $25K-$35K
    PLATFORM = "platform"           # $50K-$75K
    INNOVATION = "innovation"        # $75K-$100K


class EngagementStatus(Enum):
    """Consulting engagement status tracking."""
    PROSPECT = "prospect"
    PROPOSAL = "proposal"
    CONTRACTED = "contracted"
    DISCOVERY = "discovery"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    KNOWLEDGE_TRANSFER = "knowledge_transfer"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class DeliverableStatus(Enum):
    """Individual deliverable status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    DEPLOYED = "deployed"


class StakeholderRole(Enum):
    """Client stakeholder roles."""
    EXECUTIVE_SPONSOR = "executive_sponsor"
    PROJECT_MANAGER = "project_manager"
    TECHNICAL_LEAD = "technical_lead"
    END_USER = "end_user"
    DECISION_MAKER = "decision_maker"


@dataclass
class Stakeholder:
    """Client stakeholder information."""
    stakeholder_id: str
    name: str
    email: str
    role: StakeholderRole
    department: str
    influence_level: int  # 1-10 scale
    engagement_preference: str  # email, phone, in-person, slack
    availability: Dict[str, str]  # day -> time range
    decision_authority: List[str]  # areas they can approve
    notes: str = ""


@dataclass
class Deliverable:
    """Consulting engagement deliverable."""
    deliverable_id: str
    name: str
    description: str
    category: str  # technical, strategic, training, documentation
    estimated_hours: int
    actual_hours: int = 0
    status: DeliverableStatus = DeliverableStatus.PLANNED
    assigned_consultant: str = ""
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    client_value: str = ""  # Business value description
    due_date: Optional[str] = None
    completed_date: Optional[str] = None
    client_feedback: Optional[str] = None


@dataclass
class ConsultingEngagement:
    """Complete consulting engagement tracking."""

    # Basic Information
    engagement_id: str
    client_name: str
    client_organization: str
    tier: EngagementTier
    status: EngagementStatus

    # Financial
    contract_value: float
    payment_schedule: List[Dict[str, Any]]

    # Timeline
    start_date: str
    planned_end_date: str
    actual_end_date: Optional[str] = None

    # Team
    lead_consultant: str
    consulting_team: List[str] = field(default_factory=list)
    stakeholders: List[Stakeholder] = field(default_factory=list)

    # Scope & Deliverables
    scope_summary: str = ""
    success_metrics: List[str] = field(default_factory=list)
    deliverables: List[Deliverable] = field(default_factory=list)

    # Progress Tracking
    completion_percentage: float = 0.0
    current_phase: str = ""
    risk_assessment: List[str] = field(default_factory=list)

    # ROI Tracking
    baseline_metrics: Dict[str, float] = field(default_factory=dict)
    current_metrics: Dict[str, float] = field(default_factory=dict)
    projected_roi: float = 0.0

    # Communication
    communication_log: List[Dict[str, Any]] = field(default_factory=list)
    next_milestone: Optional[str] = None

    # Metadata
    created_at: str = ""
    last_updated: str = ""


@dataclass
class ROIMetrics:
    """ROI tracking and measurement."""
    engagement_id: str
    measurement_date: str

    # Revenue Metrics
    monthly_revenue_increase: float = 0.0
    deal_velocity_improvement: float = 0.0  # percentage
    conversion_rate_improvement: float = 0.0  # percentage
    average_deal_size_change: float = 0.0  # percentage

    # Efficiency Metrics
    hours_saved_per_week: float = 0.0
    process_automation_percentage: float = 0.0
    response_time_improvement: float = 0.0  # percentage

    # Quality Metrics
    customer_satisfaction_score: float = 0.0  # 1-10 scale
    lead_quality_improvement: float = 0.0  # percentage
    error_rate_reduction: float = 0.0  # percentage

    # Strategic Metrics
    market_penetration_increase: float = 0.0  # percentage
    competitive_advantage_score: float = 0.0  # 1-10 scale
    innovation_capability_score: float = 0.0  # 1-10 scale

    # Calculated ROI
    total_roi_percentage: float = 0.0
    payback_period_months: float = 0.0
    net_present_value: float = 0.0


class ConsultingDeliveryService:
    """
    Consulting Delivery Service for High-Ticket Engagements.

    Manages end-to-end delivery of $25K-$100K consulting projects with
    structured methodology, stakeholder management, and ROI tracking.
    """

    def __init__(self):
        """Initialize consulting delivery service."""
        self.engagements_dir = Path("data/consulting/engagements")
        self.templates_dir = Path("data/consulting/templates")
        self.metrics_dir = Path("data/consulting/metrics")

        # Create directories
        for directory in [self.engagements_dir, self.templates_dir, self.metrics_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info("Consulting delivery service initialized")
        self._initialize_delivery_templates()

    def _initialize_delivery_templates(self):
        """Initialize consulting delivery templates and methodologies."""

        # Tier-specific deliverable templates
        tier_templates = {
            EngagementTier.ACCELERATOR: [
                {
                    "name": "AI Strategy Assessment",
                    "category": "strategic",
                    "estimated_hours": 16,
                    "description": "Comprehensive analysis of current AI readiness and opportunity identification",
                    "acceptance_criteria": [
                        "Current state analysis completed",
                        "AI opportunity matrix delivered",
                        "ROI projections validated"
                    ],
                    "client_value": "Strategic clarity on $500K+ revenue opportunities"
                },
                {
                    "name": "Multi-Agent Swarm Implementation",
                    "category": "technical",
                    "estimated_hours": 80,
                    "description": "Deploy and configure 10+ specialized AI agents with consensus intelligence",
                    "acceptance_criteria": [
                        "10+ agents deployed and tested",
                        "Consensus scoring above 85% accuracy",
                        "Integration with existing CRM validated"
                    ],
                    "client_value": "85+ hours/month automation with 25% conversion improvement"
                },
                {
                    "name": "Team Training Program",
                    "category": "training",
                    "estimated_hours": 24,
                    "description": "Comprehensive training on AI-assisted workflows",
                    "acceptance_criteria": [
                        "Training materials delivered",
                        "All team members certified",
                        "Performance benchmarks established"
                    ],
                    "client_value": "Team productivity increase of 40%+"
                }
            ],

            EngagementTier.PLATFORM: [
                {
                    "name": "Enterprise AI Architecture Design",
                    "category": "strategic",
                    "estimated_hours": 32,
                    "description": "Complete enterprise AI platform architecture with scalability planning",
                    "acceptance_criteria": [
                        "Enterprise architecture documented",
                        "Scalability roadmap delivered",
                        "Integration strategy validated"
                    ],
                    "client_value": "Foundation for $2M+ revenue scaling"
                },
                {
                    "name": "Predictive Analytics Engine",
                    "category": "technical",
                    "estimated_hours": 120,
                    "description": "Advanced ML models for lead scoring, churn prediction, and revenue forecasting",
                    "acceptance_criteria": [
                        "ML models deployed with 90%+ accuracy",
                        "Real-time prediction dashboard operational",
                        "Historical validation completed"
                    ],
                    "client_value": "40% churn reduction, $1M+ revenue retention"
                },
                {
                    "name": "Executive Intelligence Dashboard",
                    "category": "technical",
                    "estimated_hours": 64,
                    "description": "C-suite dashboard with strategic insights and ROI attribution",
                    "acceptance_criteria": [
                        "Executive dashboard deployed",
                        "Real-time KPI monitoring active",
                        "Mobile optimization completed"
                    ],
                    "client_value": "C-suite decision making acceleration, strategic visibility"
                },
                {
                    "name": "Advanced Team Certification",
                    "category": "training",
                    "estimated_hours": 40,
                    "description": "Advanced AI platform management and optimization training",
                    "acceptance_criteria": [
                        "Advanced certification program completed",
                        "Internal champions identified and trained",
                        "Optimization playbooks delivered"
                    ],
                    "client_value": "Internal capability building, reduced dependency"
                }
            ],

            EngagementTier.INNOVATION: [
                {
                    "name": "Custom AI Model Development",
                    "category": "technical",
                    "estimated_hours": 160,
                    "description": "Proprietary AI models tailored to client's unique competitive advantage",
                    "acceptance_criteria": [
                        "Custom models trained and validated",
                        "Proprietary algorithm documentation delivered",
                        "Competitive differentiation verified"
                    ],
                    "client_value": "Unique competitive advantage, proprietary IP creation"
                },
                {
                    "name": "Innovation Lab Setup",
                    "category": "strategic",
                    "estimated_hours": 48,
                    "description": "Complete innovation lab for ongoing AI experimentation and development",
                    "acceptance_criteria": [
                        "Innovation lab infrastructure deployed",
                        "Experimentation frameworks established",
                        "Success measurement criteria defined"
                    ],
                    "client_value": "Ongoing innovation capability, future-ready organization"
                },
                {
                    "name": "Market Launch Strategy",
                    "category": "strategic",
                    "estimated_hours": 32,
                    "description": "Go-to-market strategy for AI-powered competitive advantage",
                    "acceptance_criteria": [
                        "Market positioning strategy delivered",
                        "Launch plan with success metrics",
                        "Competitive analysis and differentiation strategy"
                    ],
                    "client_value": "Strategic market positioning, revenue growth acceleration"
                },
                {
                    "name": "Executive Advisory Program",
                    "category": "strategic",
                    "estimated_hours": 80,
                    "description": "Ongoing executive advisory and strategic optimization",
                    "acceptance_criteria": [
                        "Advisory framework established",
                        "Monthly strategic reviews scheduled",
                        "Continuous optimization process active"
                    ],
                    "client_value": "Ongoing strategic guidance, performance optimization"
                }
            ]
        }

        # Save templates
        for tier, deliverables in tier_templates.items():
            template_file = self.templates_dir / f"{tier.value}_deliverables.json"
            with open(template_file, 'w') as f:
                json.dump(deliverables, f, indent=2)

    async def create_engagement(
        self,
        client_name: str,
        client_organization: str,
        tier: EngagementTier,
        contract_value: float,
        start_date: str,
        lead_consultant: str
    ) -> str:
        """Create new consulting engagement."""

        try:
            engagement_id = f"eng_{tier.value}_{uuid.uuid4().hex[:8]}"

            # Calculate planned end date based on tier
            start_dt = datetime.fromisoformat(start_date)
            duration_weeks = {
                EngagementTier.ACCELERATOR: 7,  # 6-8 weeks
                EngagementTier.PLATFORM: 11,   # 10-12 weeks
                EngagementTier.INNOVATION: 14  # 12-16 weeks
            }

            end_date = start_dt + timedelta(weeks=duration_weeks[tier])

            # Load deliverable templates for tier
            deliverables = await self._load_tier_deliverables(tier)

            # Create engagement
            engagement = ConsultingEngagement(
                engagement_id=engagement_id,
                client_name=client_name,
                client_organization=client_organization,
                tier=tier,
                status=EngagementStatus.CONTRACTED,
                contract_value=contract_value,
                payment_schedule=self._generate_payment_schedule(contract_value, tier),
                start_date=start_date,
                planned_end_date=end_date.isoformat(),
                lead_consultant=lead_consultant,
                deliverables=deliverables,
                success_metrics=self._get_tier_success_metrics(tier),
                created_at=datetime.utcnow().isoformat(),
                last_updated=datetime.utcnow().isoformat()
            )

            # Save engagement
            await self._save_engagement(engagement)

            logger.info(f"Created {tier.value} engagement {engagement_id} for {client_organization}")
            return engagement_id

        except Exception as e:
            logger.error(f"Failed to create engagement: {e}")
            raise

    async def get_engagement(self, engagement_id: str) -> Optional[ConsultingEngagement]:
        """Retrieve consulting engagement by ID."""

        engagement_file = self.engagements_dir / f"{engagement_id}.json"
        if not engagement_file.exists():
            return None

        try:
            with open(engagement_file, 'r') as f:
                data = json.load(f)

            # Convert enums and nested objects
            data['tier'] = EngagementTier(data['tier'])
            data['status'] = EngagementStatus(data['status'])

            # Convert stakeholders
            if 'stakeholders' in data:
                data['stakeholders'] = [
                    Stakeholder(**s) if isinstance(s, dict) else s
                    for s in data['stakeholders']
                ]

            # Convert deliverables
            if 'deliverables' in data:
                for deliverable_data in data['deliverables']:
                    if isinstance(deliverable_data, dict) and 'status' in deliverable_data:
                        deliverable_data['status'] = DeliverableStatus(deliverable_data['status'])

                data['deliverables'] = [
                    Deliverable(**d) if isinstance(d, dict) else d
                    for d in data['deliverables']
                ]

            return ConsultingEngagement(**data)

        except Exception as e:
            logger.error(f"Failed to load engagement {engagement_id}: {e}")
            return None

    async def update_engagement_status(
        self,
        engagement_id: str,
        status: EngagementStatus,
        notes: str = ""
    ) -> bool:
        """Update engagement status with optional notes."""

        engagement = await self.get_engagement(engagement_id)
        if not engagement:
            return False

        try:
            engagement.status = status
            engagement.last_updated = datetime.utcnow().isoformat()

            # Add communication log entry
            if notes:
                engagement.communication_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "status_update",
                    "message": f"Status updated to {status.value}: {notes}",
                    "author": "system"
                })

            await self._save_engagement(engagement)
            logger.info(f"Updated engagement {engagement_id} status to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update engagement status: {e}")
            return False

    async def add_stakeholder(
        self,
        engagement_id: str,
        stakeholder: Stakeholder
    ) -> bool:
        """Add stakeholder to engagement."""

        engagement = await self.get_engagement(engagement_id)
        if not engagement:
            return False

        try:
            # Check if stakeholder already exists
            existing_ids = [s.stakeholder_id for s in engagement.stakeholders]
            if stakeholder.stakeholder_id in existing_ids:
                return False

            engagement.stakeholders.append(stakeholder)
            engagement.last_updated = datetime.utcnow().isoformat()

            await self._save_engagement(engagement)
            logger.info(f"Added stakeholder {stakeholder.name} to engagement {engagement_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add stakeholder: {e}")
            return False

    async def update_deliverable_status(
        self,
        engagement_id: str,
        deliverable_id: str,
        status: DeliverableStatus,
        actual_hours: Optional[int] = None,
        notes: str = ""
    ) -> bool:
        """Update deliverable status and progress."""

        engagement = await self.get_engagement(engagement_id)
        if not engagement:
            return False

        try:
            # Find and update deliverable
            deliverable_updated = False
            for deliverable in engagement.deliverables:
                if deliverable.deliverable_id == deliverable_id:
                    deliverable.status = status

                    if actual_hours is not None:
                        deliverable.actual_hours = actual_hours

                    if status in [DeliverableStatus.APPROVED, DeliverableStatus.DEPLOYED]:
                        deliverable.completed_date = datetime.utcnow().isoformat()

                    deliverable_updated = True
                    break

            if not deliverable_updated:
                return False

            # Recalculate engagement completion percentage
            engagement.completion_percentage = self._calculate_completion_percentage(engagement)
            engagement.last_updated = datetime.utcnow().isoformat()

            # Add communication log entry
            engagement.communication_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": "deliverable_update",
                "message": f"Deliverable {deliverable_id} updated to {status.value}: {notes}",
                "author": "system"
            })

            await self._save_engagement(engagement)
            logger.info(f"Updated deliverable {deliverable_id} status to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update deliverable: {e}")
            return False

    async def track_roi_metrics(
        self,
        engagement_id: str,
        metrics: ROIMetrics
    ) -> bool:
        """Track ROI metrics for engagement."""

        try:
            metrics_file = self.metrics_dir / f"{engagement_id}_roi.json"

            # Load existing metrics
            metrics_history = []
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics_history = json.load(f)

            # Add new measurement
            metrics_history.append(asdict(metrics))

            # Save updated metrics
            with open(metrics_file, 'w') as f:
                json.dump(metrics_history, f, indent=2)

            # Update engagement with latest metrics
            engagement = await self.get_engagement(engagement_id)
            if engagement:
                engagement.current_metrics = {
                    "monthly_revenue_increase": metrics.monthly_revenue_increase,
                    "hours_saved_per_week": metrics.hours_saved_per_week,
                    "conversion_improvement": metrics.conversion_rate_improvement,
                    "customer_satisfaction": metrics.customer_satisfaction_score
                }
                engagement.projected_roi = metrics.total_roi_percentage
                await self._save_engagement(engagement)

            logger.info(f"Tracked ROI metrics for engagement {engagement_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to track ROI metrics: {e}")
            return False

    async def get_engagement_dashboard(self, engagement_id: str) -> Dict[str, Any]:
        """Get comprehensive engagement dashboard data."""

        engagement = await self.get_engagement(engagement_id)
        if not engagement:
            return {}

        try:
            # Calculate key metrics
            total_deliverables = len(engagement.deliverables)
            completed_deliverables = len([
                d for d in engagement.deliverables
                if d.status in [DeliverableStatus.APPROVED, DeliverableStatus.DEPLOYED]
            ])

            in_progress_deliverables = len([
                d for d in engagement.deliverables
                if d.status == DeliverableStatus.IN_PROGRESS
            ])

            # Financial progress
            paid_milestones = len([
                p for p in engagement.payment_schedule
                if p.get('status') == 'paid'
            ])
            total_milestones = len(engagement.payment_schedule)

            # Risk assessment
            risk_level = "LOW"
            if engagement.completion_percentage < 50 and len(engagement.risk_assessment) > 2:
                risk_level = "HIGH"
            elif len(engagement.risk_assessment) > 0:
                risk_level = "MEDIUM"

            # ROI metrics
            roi_data = await self._get_latest_roi_metrics(engagement_id)

            return {
                "engagement_info": {
                    "id": engagement.engagement_id,
                    "client": engagement.client_organization,
                    "tier": engagement.tier.value,
                    "status": engagement.status.value,
                    "contract_value": engagement.contract_value,
                    "completion_percentage": engagement.completion_percentage
                },
                "progress": {
                    "total_deliverables": total_deliverables,
                    "completed_deliverables": completed_deliverables,
                    "in_progress_deliverables": in_progress_deliverables,
                    "completion_rate": (completed_deliverables / total_deliverables * 100) if total_deliverables > 0 else 0
                },
                "financial": {
                    "contract_value": engagement.contract_value,
                    "paid_milestones": paid_milestones,
                    "total_milestones": total_milestones,
                    "payment_progress": (paid_milestones / total_milestones * 100) if total_milestones > 0 else 0
                },
                "timeline": {
                    "start_date": engagement.start_date,
                    "planned_end_date": engagement.planned_end_date,
                    "actual_end_date": engagement.actual_end_date,
                    "days_remaining": self._calculate_days_remaining(engagement.planned_end_date)
                },
                "team": {
                    "lead_consultant": engagement.lead_consultant,
                    "team_size": len(engagement.consulting_team) + 1,
                    "stakeholders": len(engagement.stakeholders)
                },
                "risk": {
                    "level": risk_level,
                    "issues": engagement.risk_assessment
                },
                "roi": roi_data,
                "recent_activity": engagement.communication_log[-5:] if engagement.communication_log else []
            }

        except Exception as e:
            logger.error(f"Failed to generate dashboard for {engagement_id}: {e}")
            return {}

    async def generate_status_report(self, engagement_id: str) -> Dict[str, Any]:
        """Generate executive status report for client."""

        engagement = await self.get_engagement(engagement_id)
        if not engagement:
            return {}

        try:
            dashboard = await self.get_engagement_dashboard(engagement_id)

            # Executive summary
            status_summary = self._generate_status_summary(engagement, dashboard)

            # Key achievements
            achievements = self._identify_key_achievements(engagement)

            # Upcoming milestones
            upcoming_milestones = self._get_upcoming_milestones(engagement)

            # Risk mitigation
            risk_mitigation = self._assess_risks_and_mitigation(engagement)

            return {
                "report_generated": datetime.utcnow().isoformat(),
                "engagement_id": engagement_id,
                "client": engagement.client_organization,
                "reporting_period": f"Week {self._calculate_project_week(engagement)}",
                "executive_summary": status_summary,
                "key_achievements": achievements,
                "upcoming_milestones": upcoming_milestones,
                "financial_status": {
                    "budget_utilization": dashboard["financial"]["payment_progress"],
                    "projected_roi": engagement.projected_roi,
                    "value_delivered": self._calculate_value_delivered(engagement)
                },
                "risk_assessment": risk_mitigation,
                "next_steps": self._identify_next_steps(engagement),
                "stakeholder_engagement": self._assess_stakeholder_engagement(engagement)
            }

        except Exception as e:
            logger.error(f"Failed to generate status report: {e}")
            return {}

    def _calculate_completion_percentage(self, engagement: ConsultingEngagement) -> float:
        """Calculate engagement completion percentage."""
        if not engagement.deliverables:
            return 0.0

        total_hours = sum(d.estimated_hours for d in engagement.deliverables)
        completed_hours = sum(
            d.estimated_hours for d in engagement.deliverables
            if d.status in [DeliverableStatus.APPROVED, DeliverableStatus.DEPLOYED]
        )

        return (completed_hours / total_hours * 100) if total_hours > 0 else 0.0

    async def _load_tier_deliverables(self, tier: EngagementTier) -> List[Deliverable]:
        """Load deliverable templates for engagement tier."""
        template_file = self.templates_dir / f"{tier.value}_deliverables.json"

        if not template_file.exists():
            return []

        try:
            with open(template_file, 'r') as f:
                templates = json.load(f)

            deliverables = []
            for i, template in enumerate(templates, 1):
                deliverable = Deliverable(
                    deliverable_id=f"del_{tier.value}_{i:02d}",
                    name=template["name"],
                    description=template["description"],
                    category=template["category"],
                    estimated_hours=template["estimated_hours"],
                    acceptance_criteria=template["acceptance_criteria"],
                    client_value=template["client_value"]
                )
                deliverables.append(deliverable)

            return deliverables

        except Exception as e:
            logger.error(f"Failed to load tier deliverables: {e}")
            return []

    def _generate_payment_schedule(self, contract_value: float, tier: EngagementTier) -> List[Dict[str, Any]]:
        """Generate payment schedule based on engagement tier."""

        if tier == EngagementTier.ACCELERATOR:
            return [
                {"milestone": "Contract Signing", "amount": contract_value * 0.30, "status": "pending"},
                {"milestone": "Discovery Complete", "amount": contract_value * 0.30, "status": "pending"},
                {"milestone": "Implementation Complete", "amount": contract_value * 0.40, "status": "pending"}
            ]
        elif tier == EngagementTier.PLATFORM:
            return [
                {"milestone": "Contract Signing", "amount": contract_value * 0.25, "status": "pending"},
                {"milestone": "Architecture Approved", "amount": contract_value * 0.25, "status": "pending"},
                {"milestone": "Platform Deployed", "amount": contract_value * 0.30, "status": "pending"},
                {"milestone": "Training Complete", "amount": contract_value * 0.20, "status": "pending"}
            ]
        else:  # INNOVATION
            return [
                {"milestone": "Contract Signing", "amount": contract_value * 0.20, "status": "pending"},
                {"milestone": "Custom Models Delivered", "amount": contract_value * 0.25, "status": "pending"},
                {"milestone": "Innovation Lab Operational", "amount": contract_value * 0.25, "status": "pending"},
                {"milestone": "Market Launch Support", "amount": contract_value * 0.20, "status": "pending"},
                {"milestone": "Advisory Program Active", "amount": contract_value * 0.10, "status": "pending"}
            ]

    def _get_tier_success_metrics(self, tier: EngagementTier) -> List[str]:
        """Get success metrics for engagement tier."""

        base_metrics = [
            "Client satisfaction score > 9.0",
            "All deliverables approved on time",
            "ROI target achieved within 6 months"
        ]

        if tier == EngagementTier.ACCELERATOR:
            base_metrics.extend([
                "25% conversion rate improvement",
                "85+ hours/month automation achieved",
                "Team adoption rate > 90%"
            ])
        elif tier == EngagementTier.PLATFORM:
            base_metrics.extend([
                "40% churn reduction achieved",
                "$1M+ revenue retention demonstrated",
                "Executive dashboard adoption > 95%",
                "Platform scalability validated"
            ])
        else:  # INNOVATION
            base_metrics.extend([
                "Proprietary competitive advantage established",
                "Innovation lab delivering measurable results",
                "Market leadership position achieved",
                "Ongoing innovation capability established"
            ])

        return base_metrics

    async def _save_engagement(self, engagement: ConsultingEngagement):
        """Save engagement to storage."""
        engagement_file = self.engagements_dir / f"{engagement.engagement_id}.json"

        # Convert to dict and handle enums
        data = asdict(engagement)
        data['tier'] = engagement.tier.value
        data['status'] = engagement.status.value

        # Convert nested objects
        for stakeholder in data['stakeholders']:
            if isinstance(stakeholder, dict) and 'role' in stakeholder:
                stakeholder['role'] = stakeholder['role'].value if hasattr(stakeholder['role'], 'value') else stakeholder['role']

        for deliverable in data['deliverables']:
            if isinstance(deliverable, dict) and 'status' in deliverable:
                deliverable['status'] = deliverable['status'].value if hasattr(deliverable['status'], 'value') else deliverable['status']

        with open(engagement_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def _get_latest_roi_metrics(self, engagement_id: str) -> Dict[str, Any]:
        """Get latest ROI metrics for engagement."""
        metrics_file = self.metrics_dir / f"{engagement_id}_roi.json"

        if not metrics_file.exists():
            return {}

        try:
            with open(metrics_file, 'r') as f:
                metrics_history = json.load(f)

            if not metrics_history:
                return {}

            latest = metrics_history[-1]
            return {
                "measurement_date": latest.get("measurement_date", ""),
                "total_roi": latest.get("total_roi_percentage", 0),
                "payback_months": latest.get("payback_period_months", 0),
                "revenue_increase": latest.get("monthly_revenue_increase", 0),
                "hours_saved": latest.get("hours_saved_per_week", 0)
            }

        except Exception as e:
            logger.error(f"Failed to get ROI metrics: {e}")
            return {}

    def _calculate_days_remaining(self, planned_end_date: str) -> int:
        """Calculate days remaining until planned end date."""
        try:
            end_date = datetime.fromisoformat(planned_end_date.replace('Z', '+00:00'))
            now = datetime.utcnow()
            return (end_date - now).days
        except:
            return 0

    def _generate_status_summary(self, engagement: ConsultingEngagement, dashboard: Dict[str, Any]) -> str:
        """Generate executive status summary."""
        completion = dashboard["progress"]["completion_rate"]
        risk_level = dashboard["risk"]["level"]

        if completion >= 90:
            return f"Engagement is nearing completion with {completion:.0f}% of deliverables approved. Final deployment and knowledge transfer in progress."
        elif completion >= 70:
            return f"Strong progress with {completion:.0f}% completion. Key implementation milestones achieved, moving toward final delivery."
        elif completion >= 40:
            return f"Solid momentum with {completion:.0f}% of deliverables complete. Implementation phase active with {risk_level.lower()} risk level."
        else:
            return f"Engagement in early stages with {completion:.0f}% completion. Discovery and design phases active, establishing foundation for delivery."

    def _identify_key_achievements(self, engagement: ConsultingEngagement) -> List[str]:
        """Identify key achievements from completed deliverables."""
        achievements = []

        for deliverable in engagement.deliverables:
            if deliverable.status in [DeliverableStatus.APPROVED, DeliverableStatus.DEPLOYED]:
                achievements.append(f"✅ {deliverable.name} - {deliverable.client_value}")

        return achievements[:5]  # Top 5 achievements

    def _get_upcoming_milestones(self, engagement: ConsultingEngagement) -> List[str]:
        """Get upcoming milestones and deliverables."""
        upcoming = []

        # Next deliverables
        for deliverable in engagement.deliverables:
            if deliverable.status in [DeliverableStatus.PLANNED, DeliverableStatus.IN_PROGRESS]:
                status_text = "In Progress" if deliverable.status == DeliverableStatus.IN_PROGRESS else "Planned"
                upcoming.append(f"📋 {deliverable.name} - {status_text}")
                if len(upcoming) >= 3:
                    break

        # Payment milestones
        for payment in engagement.payment_schedule:
            if payment["status"] == "pending":
                upcoming.append(f"💰 {payment['milestone']} - ${payment['amount']:,.0f}")
                break

        return upcoming

    def _assess_risks_and_mitigation(self, engagement: ConsultingEngagement) -> List[Dict[str, str]]:
        """Assess current risks and mitigation strategies."""
        risks = []

        for risk in engagement.risk_assessment:
            risks.append({
                "risk": risk,
                "mitigation": "Proactive monitoring and stakeholder communication",
                "status": "Managed"
            })

        # Add standard risk assessment based on progress
        completion = self._calculate_completion_percentage(engagement)
        if completion < 30:
            risks.append({
                "risk": "Early stage execution risk",
                "mitigation": "Weekly stakeholder check-ins and milestone validation",
                "status": "Monitoring"
            })

        return risks

    def _calculate_value_delivered(self, engagement: ConsultingEngagement) -> str:
        """Calculate business value delivered to date."""
        completed_deliverables = [
            d for d in engagement.deliverables
            if d.status in [DeliverableStatus.APPROVED, DeliverableStatus.DEPLOYED]
        ]

        if not completed_deliverables:
            return "Foundation setting and strategic planning"

        value_descriptions = [d.client_value for d in completed_deliverables if d.client_value]
        return "; ".join(value_descriptions[:3])  # Top 3 value items

    def _identify_next_steps(self, engagement: ConsultingEngagement) -> List[str]:
        """Identify immediate next steps."""
        next_steps = []

        # Find next deliverable in progress or planned
        for deliverable in engagement.deliverables:
            if deliverable.status in [DeliverableStatus.PLANNED, DeliverableStatus.IN_PROGRESS]:
                next_steps.append(f"Complete {deliverable.name}")
                break

        # Add strategic next steps
        if engagement.status == EngagementStatus.DISCOVERY:
            next_steps.append("Finalize technical architecture and begin implementation")
        elif engagement.status == EngagementStatus.IMPLEMENTATION:
            next_steps.append("Validate implementation with stakeholder testing")
        elif engagement.status == EngagementStatus.TESTING:
            next_steps.append("Deploy to production and begin user training")

        return next_steps

    def _assess_stakeholder_engagement(self, engagement: ConsultingEngagement) -> Dict[str, Any]:
        """Assess stakeholder engagement levels."""
        if not engagement.stakeholders:
            return {"status": "No stakeholders defined"}

        high_influence = len([s for s in engagement.stakeholders if s.influence_level >= 8])
        total_stakeholders = len(engagement.stakeholders)

        return {
            "total_stakeholders": total_stakeholders,
            "high_influence_engaged": high_influence,
            "engagement_health": "Strong" if high_influence >= 2 else "Needs Attention"
        }

    def _calculate_project_week(self, engagement: ConsultingEngagement) -> int:
        """Calculate current project week."""
        try:
            start_date = datetime.fromisoformat(engagement.start_date)
            now = datetime.utcnow()
            days_elapsed = (now - start_date).days
            return max(1, (days_elapsed // 7) + 1)
        except:
            return 1


# Factory function
def get_consulting_delivery_service() -> ConsultingDeliveryService:
    """Get configured consulting delivery service instance."""
    return ConsultingDeliveryService()