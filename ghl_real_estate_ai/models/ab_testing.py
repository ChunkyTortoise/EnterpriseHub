"""Pydantic models for A/B testing persistence.

Maps to the database schema defined in:
    alembic/versions/2026_02_07_001_add_ab_testing_tables.py

Tables: ab_experiments, ab_variants, ab_assignments, ab_metrics.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExperimentStatusDB(str, Enum):
    """Database experiment status (superset of in-memory ExperimentStatus)."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ABVariantDB(BaseModel):
    """Row from the ab_variants table."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    experiment_id: uuid.UUID
    variant_name: str
    variant_label: Optional[str] = None
    description: Optional[str] = None
    response_template: Optional[str] = None
    system_prompt: Optional[str] = None
    config_overrides: Optional[Dict[str, Any]] = None
    traffic_weight: float = 0.5
    impressions: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    total_value: float = 0.0
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    is_control: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ABExperimentDB(BaseModel):
    """Row from the ab_experiments table with nested variants."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    experiment_name: str
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    target_bot: Optional[str] = None
    metric_type: str = "conversion"
    minimum_sample_size: int = 100
    status: ExperimentStatusDB = ExperimentStatusDB.DRAFT
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    default_traffic_split: Optional[Dict[str, float]] = None
    winner_variant: Optional[str] = None
    statistical_significance: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    variants: List[ABVariantDB] = Field(default_factory=list)


class ABAssignmentDB(BaseModel):
    """Row from the ab_assignments table."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    experiment_id: uuid.UUID
    variant_id: uuid.UUID
    user_id: str
    session_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    bucket_value: Optional[float] = None
    has_converted: bool = False
    converted_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ABMetricEventDB(BaseModel):
    """Row from the ab_metrics table."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    experiment_id: uuid.UUID
    variant_id: uuid.UUID
    assignment_id: uuid.UUID
    event_type: str
    event_value: float = 1.0
    event_data: Optional[Dict[str, Any]] = None
    event_timestamp: Optional[datetime] = None
    source: Optional[str] = None
    session_context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
