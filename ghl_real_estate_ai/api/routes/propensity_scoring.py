"""
XGBoost Propensity Scoring API Routes

Exposes life-event propensity scoring, model training, and feature importance
for lead conversion prediction.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.services.xgboost_propensity_engine import (
    get_propensity_engine,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/propensity",
    tags=["Propensity Scoring"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class ScoreLeadRequest(BaseModel):
    contact_id: str = Field(..., description="Contact identifier")
    address: Optional[str] = Field(None, description="Property address for life-event detection")
    conversation_context: Optional[Dict[str, Any]] = Field(
        None, description="Conversation features (message_count, sentiment, etc.)"
    )
    behavioral_signals: Optional[Dict[str, Any]] = Field(
        None, description="Behavioral signals (commitment_score, hedging_score, etc.)"
    )


class LifeEventResponse(BaseModel):
    event_type: str
    detected: bool
    confidence: float
    source: str
    details: Dict[str, Any]


class PropensityScoreResponse(BaseModel):
    contact_id: str
    conversion_probability: float
    confidence: float
    temperature: str
    primary_event: Optional[str]
    life_events: List[LifeEventResponse]
    feature_importance: Dict[str, float]
    recommended_approach: str
    predicted_timeline: str
    scoring_latency_ms: float


class TrainModelRequest(BaseModel):
    training_data: List[Dict[str, Any]] = Field(
        ..., min_length=10, description="Training feature vectors"
    )
    labels: List[int] = Field(
        ..., min_length=10, description="Binary labels (0=not converted, 1=converted)"
    )
    validation_split: float = Field(0.2, ge=0.1, le=0.5)


class TrainingMetricsResponse(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc_roc: float
    feature_importances: Dict[str, float]
    training_samples: int
    validation_samples: int


class BatchScoreRequest(BaseModel):
    leads: List[ScoreLeadRequest] = Field(..., min_length=1, max_length=50)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/score", response_model=PropensityScoreResponse)
async def score_lead(request: ScoreLeadRequest):
    """Score a lead's conversion propensity using life-event + behavioral signals."""
    try:
        engine = get_propensity_engine()
        result = await engine.score_lead(
            contact_id=request.contact_id,
            address=request.address,
            conversation_context=request.conversation_context,
            behavioral_signals=request.behavioral_signals,
        )
        return PropensityScoreResponse(
            contact_id=result.contact_id,
            conversion_probability=result.conversion_probability,
            confidence=result.confidence,
            temperature=result.temperature,
            primary_event=result.primary_event.value if result.primary_event else None,
            life_events=[
                LifeEventResponse(
                    event_type=e.event_type.value,
                    detected=e.detected,
                    confidence=e.confidence,
                    source=e.source,
                    details=e.details,
                )
                for e in result.life_events
            ],
            feature_importance=result.feature_importance,
            recommended_approach=result.recommended_approach,
            predicted_timeline=result.predicted_timeline,
            scoring_latency_ms=result.scoring_latency_ms,
        )
    except Exception as e:
        logger.error("Propensity scoring failed for %s: %s", request.contact_id, e)
        raise HTTPException(500, f"Propensity scoring error: {e}")


@router.post("/score/batch")
async def score_leads_batch(request: BatchScoreRequest):
    """Score multiple leads in a single request."""
    try:
        engine = get_propensity_engine()
        results = []
        for lead in request.leads:
            result = await engine.score_lead(
                contact_id=lead.contact_id,
                address=lead.address,
                conversation_context=lead.conversation_context,
                behavioral_signals=lead.behavioral_signals,
            )
            results.append({
                "contact_id": result.contact_id,
                "conversion_probability": result.conversion_probability,
                "temperature": result.temperature,
                "primary_event": result.primary_event.value if result.primary_event else None,
                "recommended_approach": result.recommended_approach,
                "predicted_timeline": result.predicted_timeline,
                "scoring_latency_ms": result.scoring_latency_ms,
            })
        return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error("Batch propensity scoring failed: %s", e)
        raise HTTPException(500, f"Batch scoring error: {e}")


@router.post("/train", response_model=TrainingMetricsResponse)
async def train_model(request: TrainModelRequest):
    """Train the XGBoost propensity model on historical lead data."""
    try:
        if len(request.training_data) != len(request.labels):
            raise HTTPException(400, "training_data and labels must have equal length")

        engine = get_propensity_engine()
        metrics = await engine.train(
            training_data=request.training_data,
            labels=request.labels,
            validation_split=request.validation_split,
        )
        return TrainingMetricsResponse(
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            f1=metrics.f1,
            auc_roc=metrics.auc_roc,
            feature_importances=metrics.feature_importances,
            training_samples=metrics.training_samples,
            validation_samples=metrics.validation_samples,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Model training failed: %s", e)
        raise HTTPException(500, f"Training error: {e}")


@router.delete("/cache")
async def clear_propensity_cache():
    """Clear the in-memory propensity score cache."""
    engine = get_propensity_engine()
    engine.clear_cache()
    return {"status": "cleared"}


@router.get("/health")
async def propensity_health():
    """Health check for the propensity scoring engine."""
    try:
        engine = get_propensity_engine()
        return {
            "status": "healthy",
            "service": "xgboost_propensity_engine",
            "model_trained": engine._is_trained,
            "feature_count": len(engine._feature_names),
            "cache_size": len(engine._cache),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
