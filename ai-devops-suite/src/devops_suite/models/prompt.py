"""Prompt registry models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID

from devops_suite.models.telemetry import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    latest_version = Column(Integer, nullable=False, default=0)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(ARRAY(String), nullable=False, default=list)
    model_hint = Column(String(128), nullable=True)
    tags = Column(ARRAY(String), nullable=False, default=list)
    created_by = Column(String(256), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    parent_version = Column(Integer, nullable=True)
    changelog = Column(Text, nullable=True)


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    prompt_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(256), nullable=False)
    metric = Column(String(64), nullable=False, default="latency")
    status = Column(String(20), nullable=False, default="draft")
    significance_threshold = Column(Float, nullable=False, default=0.95)
    min_samples = Column(Integer, nullable=False, default=100)
    variants = Column(JSON, nullable=False, default=list)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    variant_name = Column(String(64), nullable=False)
    metric_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
