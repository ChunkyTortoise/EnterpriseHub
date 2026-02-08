"""
Enterprise Compliance Platform - Risk Assessment Models

Specialized models for risk categorization, indicators, matrices, and mitigation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RiskCategory(str, Enum):
    """Risk categories aligned with EU AI Act and enterprise standards"""

    # Technical risks
    ALGORITHMIC_BIAS = "algorithmic_bias"
    MODEL_DRIFT = "model_drift"
    DATA_QUALITY = "data_quality"
    SECURITY_VULNERABILITY = "security_vulnerability"
    SYSTEM_RELIABILITY = "system_reliability"

    # Ethical risks
    FAIRNESS = "fairness"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    HUMAN_OVERSIGHT = "human_oversight"
    EXPLAINABILITY = "explainability"

    # Legal/compliance risks
    REGULATORY_VIOLATION = "regulatory_violation"
    DATA_PROTECTION = "data_protection"
    CONSENT_MANAGEMENT = "consent_management"
    CROSS_BORDER_TRANSFER = "cross_border_transfer"
    DOCUMENTATION_GAP = "documentation_gap"

    # Operational risks
    VENDOR_DEPENDENCY = "vendor_dependency"
    SKILLS_GAP = "skills_gap"
    PROCESS_FAILURE = "process_failure"
    INCIDENT_RESPONSE = "incident_response"
    CHANGE_MANAGEMENT = "change_management"

    # Business risks
    REPUTATIONAL = "reputational"
    FINANCIAL = "financial"
    COMPETITIVE = "competitive"
    STAKEHOLDER_TRUST = "stakeholder_trust"


class RiskIndicator(BaseModel):
    """Individual risk indicator with measurement"""

    indicator_id: str = Field(default_factory=lambda: str(uuid4()))

    # Classification
    category: RiskCategory
    name: str
    description: str

    # Measurement
    value: float = Field(..., ge=0, le=100)
    threshold_warning: float = Field(default=60.0)
    threshold_critical: float = Field(default=80.0)
    unit: str = Field(default="percentage")

    # Status
    status: str = Field(default="normal")  # normal, warning, critical
    trend: str = Field(default="stable")  # improving, stable, declining
    trend_percentage: float = Field(default=0.0)

    # Source
    data_source: str = Field(default="automated_scan")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    measurement_frequency: str = Field(default="daily")

    # Context
    applicable_models: List[str] = Field(default_factory=list)
    applicable_regulations: List[str] = Field(default_factory=list)

    # Evidence
    evidence_summary: Optional[str] = None
    evidence_details: Dict[str, Any] = Field(default_factory=dict)

    def calculate_status(self) -> str:
        """Determine status based on thresholds"""
        if self.value >= self.threshold_critical:
            return "critical"
        elif self.value >= self.threshold_warning:
            return "warning"
        return "normal"

    def to_dashboard_widget(self) -> Dict[str, Any]:
        """Format for dashboard display"""
        return {
            "name": self.name,
            "value": self.value,
            "status": self.calculate_status(),
            "trend": self.trend,
            "trend_pct": self.trend_percentage,
            "category": self.category.value,
        }


class RiskMatrix(BaseModel):
    """Risk matrix for impact vs likelihood assessment"""

    matrix_id: str = Field(default_factory=lambda: str(uuid4()))

    # Matrix definition
    name: str
    description: str

    # Dimensions
    likelihood_levels: List[str] = Field(default=["rare", "unlikely", "possible", "likely", "almost_certain"])
    impact_levels: List[str] = Field(default=["negligible", "minor", "moderate", "major", "catastrophic"])

    # Risk scoring matrix (likelihood x impact -> risk level)
    # 5x5 matrix stored as dict for flexibility
    risk_scores: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    # Thresholds for risk levels
    risk_level_definitions: Dict[str, Dict[str, Any]] = Field(
        default={
            "critical": {"min_score": 20, "color": "#EF4444", "action": "immediate"},
            "high": {"min_score": 15, "color": "#F59E0B", "action": "urgent"},
            "medium": {"min_score": 10, "color": "#FBBF24", "action": "planned"},
            "low": {"min_score": 5, "color": "#10B981", "action": "monitor"},
            "minimal": {"min_score": 0, "color": "#6B7280", "action": "accept"},
        }
    )

    # Assessment context
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(default="compliance_engine")
    version: str = Field(default="1.0")

    def calculate_risk_score(self, likelihood: str, impact: str) -> int:
        """Calculate numeric risk score"""
        likelihood_values = {level: i + 1 for i, level in enumerate(self.likelihood_levels)}
        impact_values = {level: i + 1 for i, level in enumerate(self.impact_levels)}

        l_score = likelihood_values.get(likelihood, 3)
        i_score = impact_values.get(impact, 3)

        return l_score * i_score

    def get_risk_level(self, likelihood: str, impact: str) -> str:
        """Determine risk level from likelihood and impact"""
        score = self.calculate_risk_score(likelihood, impact)

        for level, definition in sorted(
            self.risk_level_definitions.items(), key=lambda x: x[1]["min_score"], reverse=True
        ):
            if score >= definition["min_score"]:
                return level
        return "minimal"


class RiskTrend(BaseModel):
    """Historical risk trend data"""

    trend_id: str = Field(default_factory=lambda: str(uuid4()))

    # Identification
    entity_type: str  # model, category, regulation, organization
    entity_id: str
    entity_name: str

    # Time series data
    period: str  # daily, weekly, monthly
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    # Each point: {"timestamp": datetime, "score": float, "status": str}

    # Analysis
    trend_direction: str = Field(default="stable")  # improving, stable, declining
    average_score: float = Field(default=0.0)
    min_score: float = Field(default=0.0)
    max_score: float = Field(default=0.0)
    volatility: float = Field(default=0.0)  # Standard deviation

    # Forecasting
    predicted_30_day: Optional[float] = None
    predicted_90_day: Optional[float] = None
    confidence_interval: Optional[tuple] = None

    # Context
    notable_events: List[Dict[str, Any]] = Field(default_factory=list)
    analysis_notes: Optional[str] = None

    # Metadata
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_start: Optional[datetime] = None
    data_end: Optional[datetime] = None

    def add_data_point(self, score: float, status: str, timestamp: Optional[datetime] = None):
        """Add a new data point to the trend"""
        self.data_points.append(
            {
                "timestamp": timestamp or datetime.now(timezone.utc),
                "score": score,
                "status": status,
            }
        )
        self._recalculate_statistics()

    def _recalculate_statistics(self):
        """Recalculate trend statistics"""
        if not self.data_points:
            return

        scores = [dp["score"] for dp in self.data_points]
        self.average_score = sum(scores) / len(scores)
        self.min_score = min(scores)
        self.max_score = max(scores)

        # Calculate volatility (standard deviation)
        if len(scores) > 1:
            mean = self.average_score
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            self.volatility = variance**0.5

        # Determine trend direction
        if len(scores) >= 3:
            recent = scores[-3:]
            older = scores[-6:-3] if len(scores) >= 6 else scores[:3]
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)

            diff_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0

            if diff_pct > 5:
                self.trend_direction = "declining"  # Higher score = worse
            elif diff_pct < -5:
                self.trend_direction = "improving"  # Lower score = better
            else:
                self.trend_direction = "stable"


class RiskMitigation(BaseModel):
    """Risk mitigation strategy and controls"""

    mitigation_id: str = Field(default_factory=lambda: str(uuid4()))

    # Target risk
    risk_category: RiskCategory
    risk_indicator_id: Optional[str] = None
    target_models: List[str] = Field(default_factory=list)

    # Strategy
    strategy_name: str
    strategy_type: str  # avoid, transfer, mitigate, accept
    description: str

    # Controls
    controls: List[Dict[str, Any]] = Field(default_factory=list)
    # Each control: {"name": str, "type": str, "status": str, "effectiveness": float}

    # Effectiveness
    expected_risk_reduction: float = Field(default=0.0, ge=0, le=100)
    actual_risk_reduction: Optional[float] = None
    effectiveness_rating: str = Field(default="unverified")  # unverified, effective, partially_effective, ineffective

    # Implementation
    status: str = Field(default="planned")  # planned, implementing, implemented, verified
    implementation_start: Optional[datetime] = None
    implementation_end: Optional[datetime] = None
    responsible_party: Optional[str] = None

    # Resources
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    cost_currency: str = Field(default="USD")
    required_resources: List[str] = Field(default_factory=list)

    # Review
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None
    review_frequency: str = Field(default="quarterly")

    # Evidence
    evidence_of_effectiveness: List[str] = Field(default_factory=list)
    audit_references: List[str] = Field(default_factory=list)

    def calculate_residual_risk(self, initial_risk_score: float) -> float:
        """Calculate residual risk after mitigation"""
        reduction = self.actual_risk_reduction or self.expected_risk_reduction
        return initial_risk_score * (1 - reduction / 100)


class RiskAppetite(BaseModel):
    """Organization's risk appetite configuration"""

    config_id: str = Field(default_factory=lambda: str(uuid4()))

    # Organization
    organization_id: str
    organization_name: str

    # Risk tolerance by category
    category_tolerances: Dict[str, Dict[str, float]] = Field(
        default={
            "regulatory_violation": {"acceptable": 10, "tolerable": 25, "unacceptable": 50},
            "data_protection": {"acceptable": 15, "tolerable": 30, "unacceptable": 50},
            "algorithmic_bias": {"acceptable": 20, "tolerable": 40, "unacceptable": 60},
            "reputational": {"acceptable": 15, "tolerable": 35, "unacceptable": 55},
            "financial": {"acceptable": 20, "tolerable": 40, "unacceptable": 60},
        }
    )

    # Aggregate risk tolerance
    overall_risk_tolerance: float = Field(default=30.0)
    risk_capacity: float = Field(default=50.0)  # Maximum risk organization can absorb

    # Escalation thresholds
    board_notification_threshold: float = Field(default=70.0)
    regulatory_notification_threshold: float = Field(default=80.0)

    # Review
    approved_by: str
    approved_at: datetime
    effective_from: datetime
    effective_until: Optional[datetime] = None
    version: str = Field(default="1.0")

    # Governance
    review_frequency: str = Field(default="annual")
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None

    def is_within_appetite(self, category: str, risk_score: float) -> str:
        """Check if risk is within appetite"""
        tolerance = self.category_tolerances.get(category, {"acceptable": 20, "tolerable": 40, "unacceptable": 60})

        if risk_score <= tolerance["acceptable"]:
            return "acceptable"
        elif risk_score <= tolerance["tolerable"]:
            return "tolerable"
        elif risk_score <= tolerance["unacceptable"]:
            return "unacceptable"
        return "critical"
