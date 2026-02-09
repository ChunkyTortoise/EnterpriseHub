"""
Predictive Analytics API Endpoints for Jorge's Lead Bot.

Provides real-time ML-powered lead scoring, closing probability predictions,
action recommendations, and predictive insights through FastAPI endpoints.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from ghl_real_estate_ai.api.middleware.jwt_auth import verify_jwt_token
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ml.closing_probability_model import ClosingProbabilityModel
from ghl_real_estate_ai.services.action_recommendations import (
    ActionRecommendation,
    ActionRecommendationsEngine,
    ActionType,
)
from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import (
    PredictiveLeadScorerV2,
)

logger = get_logger(__name__)

# Initialize ML services
predictive_scorer = PredictiveLeadScorerV2()
action_engine = ActionRecommendationsEngine()
ml_model = ClosingProbabilityModel()

router = APIRouter(prefix="/api/v1/predictive", tags=["Predictive Analytics"])


# Pydantic models for request/response
class ConversationContextRequest(BaseModel):
    """Request model for conversation context."""

    conversation_history: List[Dict[str, Any]] = Field(description="List of conversation messages")
    extracted_preferences: Dict[str, Any] = Field(default={}, description="Extracted lead preferences")
    created_at: Optional[str] = Field(default=None, description="Conversation start timestamp")
    location: Optional[str] = Field(default=None, description="Target location for market analysis")
    lead_id: Optional[str] = Field(default=None, description="Unique lead identifier")

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, v):
        if v is None:
            return datetime.now().isoformat()
        return v


class PredictiveScoreResponse(BaseModel):
    """Response model for predictive scoring."""

    # Traditional scoring
    qualification_score: int = Field(description="Questions answered (0-7)")
    qualification_percentage: int = Field(description="Qualification percentage (0-100)")

    # ML predictions
    closing_probability: float = Field(description="Closing probability (0-1)")
    closing_confidence_interval: List[float] = Field(description="Confidence interval [lower, upper]")

    # Multi-dimensional scores
    engagement_score: float = Field(description="Engagement score (0-100)")
    urgency_score: float = Field(description="Urgency score (0-100)")
    risk_score: float = Field(description="Risk score (0-100)")

    # Composite scoring
    overall_priority_score: float = Field(description="Overall priority (0-100)")
    priority_level: str = Field(description="Priority level (critical/high/medium/low/cold)")

    # Insights
    risk_factors: List[str] = Field(description="Risk factors reducing closing probability")
    positive_signals: List[str] = Field(description="Positive signals")
    recommended_actions: List[str] = Field(description="Immediate action recommendations")
    optimal_contact_timing: str = Field(description="Optimal timing for contact")

    # ROI predictions
    estimated_revenue_potential: float = Field(description="Estimated commission revenue")
    effort_efficiency_score: float = Field(description="Revenue per hour of effort")
    time_investment_recommendation: str = Field(description="Recommended time investment")

    # Metadata
    model_confidence: float = Field(description="Model confidence (0-1)")
    last_updated: str = Field(description="Last update timestamp")


class ActionRecommendationResponse(BaseModel):
    """Response model for action recommendations."""

    action_type: str = Field(description="Type of action")
    priority_level: int = Field(description="Priority level (1-10)")
    recommended_timing: str = Field(description="When to take action")
    communication_channel: str = Field(description="How to communicate")

    title: str = Field(description="Action title")
    description: str = Field(description="Action description")
    talking_points: List[str] = Field(description="Key talking points")
    questions_to_ask: List[str] = Field(description="Questions to ask")
    materials_to_prepare: List[str] = Field(description="Materials to prepare")

    success_probability: float = Field(description="Expected success probability")
    expected_outcomes: List[str] = Field(description="Expected outcomes")
    potential_objections: List[str] = Field(description="Potential objections")
    objection_responses: Dict[str, str] = Field(description="Objection response scripts")

    estimated_time_investment: int = Field(description="Time investment in minutes")
    effort_level: str = Field(description="Effort level required")
    roi_potential: float = Field(description="ROI potential")


class LeadInsightsResponse(BaseModel):
    """Response model for lead insights."""

    # Behavioral analysis
    response_pattern_analysis: str = Field(description="Response pattern analysis")
    engagement_trend: str = Field(description="Engagement trend")
    conversation_quality_score: float = Field(description="Conversation quality (0-100)")

    # Market context
    market_timing_advantage: str = Field(description="Market timing analysis")
    competitive_pressure_level: str = Field(description="Competitive pressure")
    inventory_availability_impact: str = Field(description="Inventory impact")

    # Action recommendations
    next_best_action: str = Field(description="Next best action")
    optimal_communication_channel: str = Field(description="Optimal communication channel")
    recommended_follow_up_interval: str = Field(description="Follow-up interval")
    pricing_strategy_recommendation: str = Field(description="Pricing strategy")

    # Resource allocation
    estimated_time_to_close: int = Field(description="Estimated days to close")
    recommended_effort_level: str = Field(description="Recommended effort level")
    probability_of_churn: float = Field(description="Probability of churn (0-1)")


class ModelPerformanceResponse(BaseModel):
    """Response model for model performance metrics."""

    accuracy: float = Field(description="Model accuracy")
    precision: float = Field(description="Model precision")
    recall: float = Field(description="Model recall")
    f1_score: float = Field(description="F1 score")
    auc_score: float = Field(description="AUC score")
    feature_importances: Dict[str, float] = Field(description="Feature importances")
    validation_date: str = Field(description="Last validation date")
    needs_retraining: bool = Field(description="Whether model needs retraining")


# API Endpoints


@router.post("/score", response_model=PredictiveScoreResponse)
async def get_predictive_score(request: ConversationContextRequest, current_user: dict = Depends(verify_jwt_token)):
    """
    Get comprehensive predictive score for a lead.

    Returns ML-powered predictions including closing probability,
    multi-dimensional scoring, and actionable insights.
    """
    try:
        logger.info(f"Generating predictive score for lead: {request.lead_id}")

        # Convert request to context dict
        context = {
            "conversation_history": request.conversation_history,
            "extracted_preferences": request.extracted_preferences,
            "created_at": request.created_at,
        }

        # Get predictive score
        score = await predictive_scorer.calculate_predictive_score(context, request.location)

        # Convert to response model
        response = PredictiveScoreResponse(
            qualification_score=score.qualification_score,
            qualification_percentage=score.qualification_percentage,
            closing_probability=score.closing_probability,
            closing_confidence_interval=list(score.closing_confidence_interval),
            engagement_score=score.engagement_score,
            urgency_score=score.urgency_score,
            risk_score=score.risk_score,
            overall_priority_score=score.overall_priority_score,
            priority_level=score.priority_level.value,
            risk_factors=score.risk_factors,
            positive_signals=score.positive_signals,
            recommended_actions=score.recommended_actions,
            optimal_contact_timing=score.optimal_contact_timing,
            estimated_revenue_potential=score.estimated_revenue_potential,
            effort_efficiency_score=score.effort_efficiency_score,
            time_investment_recommendation=score.time_investment_recommendation,
            model_confidence=score.model_confidence,
            last_updated=score.last_updated.isoformat(),
        )

        logger.info(f"Predictive score generated: {score.overall_priority_score:.1f}% priority")
        return response

    except Exception as e:
        logger.error(f"Error generating predictive score: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating predictive score: {str(e)}")


@router.post("/insights", response_model=LeadInsightsResponse)
async def get_lead_insights(request: ConversationContextRequest, current_user: dict = Depends(verify_jwt_token)):
    """
    Get deep insights for lead decision making.

    Returns comprehensive behavioral analysis, market context,
    and strategic recommendations for optimal lead handling.
    """
    try:
        logger.info(f"Generating lead insights for: {request.lead_id}")

        # Convert request to context dict
        context = {
            "conversation_history": request.conversation_history,
            "extracted_preferences": request.extracted_preferences,
            "created_at": request.created_at,
        }

        # Generate insights
        insights = await predictive_scorer.generate_lead_insights(context, request.location)

        # Convert to response model
        response = LeadInsightsResponse(
            response_pattern_analysis=insights.response_pattern_analysis,
            engagement_trend=insights.engagement_trend,
            conversation_quality_score=insights.conversation_quality_score,
            market_timing_advantage=insights.market_timing_advantage,
            competitive_pressure_level=insights.competitive_pressure_level,
            inventory_availability_impact=insights.inventory_availability_impact,
            next_best_action=insights.next_best_action,
            optimal_communication_channel=insights.optimal_communication_channel,
            recommended_follow_up_interval=insights.recommended_follow_up_interval,
            pricing_strategy_recommendation=insights.pricing_strategy_recommendation,
            estimated_time_to_close=insights.estimated_time_to_close,
            recommended_effort_level=insights.recommended_effort_level,
            probability_of_churn=insights.probability_of_churn,
        )

        return response

    except Exception as e:
        logger.error(f"Error generating lead insights: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating lead insights: {str(e)}")


@router.post("/actions", response_model=List[ActionRecommendationResponse])
async def get_action_recommendations(
    request: ConversationContextRequest, limit: Optional[int] = 5, current_user: dict = Depends(verify_jwt_token)
):
    """
    Get prioritized action recommendations for a lead.

    Returns specific, actionable recommendations with detailed guidance
    for optimal lead conversion and time allocation.
    """
    try:
        logger.info(f"Generating action recommendations for: {request.lead_id}")

        # Convert request to context dict
        context = {
            "conversation_history": request.conversation_history,
            "extracted_preferences": request.extracted_preferences,
            "created_at": request.created_at,
        }

        # Generate action recommendations
        recommendations = await action_engine.generate_action_recommendations(context, request.location)

        # Limit results
        if limit:
            recommendations = recommendations[:limit]

        # Convert to response models
        response = []
        for rec in recommendations:
            response.append(
                ActionRecommendationResponse(
                    action_type=rec.action_type.value,
                    priority_level=rec.priority_level,
                    recommended_timing=rec.recommended_timing,
                    communication_channel=rec.communication_channel.value,
                    title=rec.title,
                    description=rec.description,
                    talking_points=rec.talking_points,
                    questions_to_ask=rec.questions_to_ask,
                    materials_to_prepare=rec.materials_to_prepare,
                    success_probability=rec.success_probability,
                    expected_outcomes=rec.expected_outcomes,
                    potential_objections=rec.potential_objections,
                    objection_responses=rec.objection_responses,
                    estimated_time_investment=rec.estimated_time_investment,
                    effort_level=rec.effort_level,
                    roi_potential=rec.roi_potential,
                )
            )

        logger.info(f"Generated {len(response)} action recommendations")
        return response

    except Exception as e:
        logger.error(f"Error generating action recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating action recommendations: {str(e)}")


@router.post("/action-sequence")
async def get_action_sequence(
    request: ConversationContextRequest,
    sequence_type: str = "conversion_focused",
    current_user: dict = Depends(verify_jwt_token),
):
    """
    Get complete action sequence for lead nurturing and conversion.

    Returns time-based action plan with immediate, short-term,
    medium-term, and long-term recommendations.
    """
    try:
        logger.info(f"Generating action sequence ({sequence_type}) for: {request.lead_id}")

        # Convert request to context dict
        context = {
            "conversation_history": request.conversation_history,
            "extracted_preferences": request.extracted_preferences,
            "created_at": request.created_at,
        }

        # Generate action sequence
        sequence = await action_engine.generate_action_sequence(context, request.location, sequence_type)

        # Convert to dict for JSON response
        def action_to_dict(action: ActionRecommendation) -> Dict:
            return {
                "action_type": action.action_type.value,
                "priority_level": action.priority_level,
                "recommended_timing": action.recommended_timing,
                "communication_channel": action.communication_channel.value,
                "title": action.title,
                "description": action.description,
                "talking_points": action.talking_points,
                "questions_to_ask": action.questions_to_ask,
                "materials_to_prepare": action.materials_to_prepare,
                "success_probability": action.success_probability,
                "expected_outcomes": action.expected_outcomes,
                "estimated_time_investment": action.estimated_time_investment,
                "effort_level": action.effort_level,
                "roi_potential": action.roi_potential,
            }

        response = {
            "sequence_name": sequence.sequence_name,
            "total_estimated_duration": sequence.total_estimated_duration,
            "success_probability": sequence.success_probability,
            "estimated_revenue": sequence.estimated_revenue,
            "immediate_actions": [action_to_dict(a) for a in sequence.immediate_actions],
            "short_term_actions": [action_to_dict(a) for a in sequence.short_term_actions],
            "medium_term_actions": [action_to_dict(a) for a in sequence.medium_term_actions],
            "long_term_actions": [action_to_dict(a) for a in sequence.long_term_actions],
        }

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error generating action sequence: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating action sequence: {str(e)}")


@router.post("/timing-optimization")
async def optimize_timing(
    request: ConversationContextRequest, action_type: str, current_user: dict = Depends(verify_jwt_token)
):
    """
    Optimize timing for specific actions based on lead behavior.

    Returns detailed timing recommendations including best call times,
    optimal days, times to avoid, and urgency windows.
    """
    try:
        logger.info(f"Optimizing timing for action '{action_type}' for: {request.lead_id}")

        # Validate action type
        try:
            action_type_enum = ActionType(action_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {action_type}")

        # Convert request to context dict
        context = {
            "conversation_history": request.conversation_history,
            "extracted_preferences": request.extracted_preferences,
            "created_at": request.created_at,
        }

        # Optimize timing
        timing = await action_engine.optimize_timing(context, action_type_enum)

        response = {
            "action_type": action_type,
            "best_call_times": timing.best_call_times,
            "best_days": timing.best_days,
            "avoid_times": timing.avoid_times,
            "urgency_window": timing.urgency_window,
            "competitive_timing": timing.competitive_timing,
        }

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error optimizing timing: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing timing: {str(e)}")


@router.get("/model-performance", response_model=ModelPerformanceResponse)
async def get_model_performance(current_user: dict = Depends(verify_jwt_token)):
    """
    Get current ML model performance metrics.

    Returns accuracy, precision, recall, feature importances,
    and retraining recommendations.
    """
    try:
        logger.info("Retrieving model performance metrics")

        # Get model metrics
        metrics = await ml_model.get_model_performance()

        if metrics is None:
            # Model not trained yet
            return ModelPerformanceResponse(
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                auc_score=0.0,
                feature_importances={},
                validation_date=datetime.now().isoformat(),
                needs_retraining=True,
            )

        # Check if retraining needed
        needs_retraining = await ml_model.needs_retraining()

        response = ModelPerformanceResponse(
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            recall=metrics.recall,
            f1_score=metrics.f1_score,
            auc_score=metrics.auc_score,
            feature_importances=metrics.feature_importances,
            validation_date=metrics.validation_date.isoformat(),
            needs_retraining=needs_retraining,
        )

        return response

    except Exception as e:
        logger.error(f"Error retrieving model performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving model performance: {str(e)}")


@router.post("/train-model")
async def train_model(
    background_tasks: BackgroundTasks, use_synthetic_data: bool = True, current_user: dict = Depends(verify_jwt_token)
):
    """
    Trigger ML model training (admin only).

    Trains the closing probability model using available data.
    For initial deployment, can use synthetic data generation.
    """
    try:
        # Check if user has admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required for model training")

        logger.info("Starting ML model training...")

        # Define background training task
        async def train_model_task():
            try:
                if use_synthetic_data:
                    # Generate synthetic training data
                    training_data = ml_model.generate_synthetic_training_data(num_samples=1000, positive_rate=0.3)
                else:
                    # In production, load real training data
                    # training_data = load_historical_data()
                    raise HTTPException(
                        status_code=400, detail="Real training data not available yet. Use synthetic_data=True"
                    )

                # Train model
                metrics = await ml_model.train_model(training_data)
                logger.info(f"Model training completed. AUC: {metrics.auc_score:.3f}")

            except Exception as e:
                logger.error(f"Model training failed: {e}")

        # Add to background tasks
        background_tasks.add_task(train_model_task)

        return {
            "status": "training_started",
            "message": "Model training initiated in background",
            "use_synthetic_data": use_synthetic_data,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error starting model training: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting model training: {str(e)}")


@router.get("/pipeline-status")
async def get_pipeline_status(current_user: dict = Depends(verify_jwt_token)):
    """
    Get status of the predictive analytics pipeline.

    Returns health status, performance metrics, and system information.
    """
    try:
        # Check model status
        model_metrics = await ml_model.get_model_performance()
        model_trained = model_metrics is not None

        # Check if retraining needed
        needs_retraining = await ml_model.needs_retraining() if model_trained else True

        # System status
        status = {
            "pipeline_health": "healthy" if model_trained else "needs_training",
            "ml_model": {
                "trained": model_trained,
                "needs_retraining": needs_retraining,
                "last_training_date": (
                    ml_model.last_training_date.isoformat() if ml_model.last_training_date else None
                ),
                "performance": {
                    "auc_score": model_metrics.auc_score if model_metrics else 0.0,
                    "accuracy": model_metrics.accuracy if model_metrics else 0.0,
                }
                if model_metrics
                else None,
            },
            "services": {"predictive_scorer": "active", "action_engine": "active", "feature_engineer": "active"},
            "cache": {
                "enabled": True,  # Assume cache is working
                "ttl_minutes": 30,
            },
            "last_updated": datetime.now().isoformat(),
        }

        return JSONResponse(content=status)

    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting pipeline status: {str(e)}")


# Batch operations for processing multiple leads
@router.post("/batch-score")
async def batch_score_leads(leads: List[ConversationContextRequest], current_user: dict = Depends(verify_jwt_token)):
    """
    Process multiple leads for batch scoring.

    Useful for updating scores for multiple leads efficiently
    or for batch processing workflows.
    """
    try:
        logger.info(f"Processing batch scoring for {len(leads)} leads")

        # Limit batch size
        if len(leads) > 50:
            raise HTTPException(status_code=400, detail="Batch size limited to 50 leads per request")

        results = []

        # Process leads concurrently
        async def process_lead(lead_request: ConversationContextRequest):
            try:
                context = {
                    "conversation_history": lead_request.conversation_history,
                    "extracted_preferences": lead_request.extracted_preferences,
                    "created_at": lead_request.created_at,
                }

                score = await predictive_scorer.calculate_predictive_score(context, lead_request.location)

                return {
                    "lead_id": lead_request.lead_id,
                    "status": "success",
                    "score": {
                        "overall_priority_score": score.overall_priority_score,
                        "closing_probability": score.closing_probability,
                        "priority_level": score.priority_level.value,
                        "estimated_revenue_potential": score.estimated_revenue_potential,
                    },
                }

            except Exception as e:
                return {"lead_id": lead_request.lead_id, "status": "error", "error": str(e)}

        # Process all leads concurrently
        results = await asyncio.gather(*[process_lead(lead) for lead in leads])

        # Summary statistics
        successful = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - successful
        avg_score = (
            np.mean([r["score"]["overall_priority_score"] for r in results if r["status"] == "success"])
            if successful > 0
            else 0
        )

        response = {
            "summary": {
                "total_processed": len(leads),
                "successful": successful,
                "failed": failed,
                "average_priority_score": float(avg_score),
            },
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"Error in batch scoring: {e}")
        raise HTTPException(status_code=500, detail=f"Error in batch scoring: {str(e)}")
