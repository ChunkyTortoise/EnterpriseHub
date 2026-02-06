"""
Scoring API endpoints for Customer Intelligence Platform.

Provides REST API for:
- Lead scoring predictions
- Model training and management
- Engagement predictions
- Churn predictions
- Customer LTV estimates
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ...ml.scoring_pipeline import ScoringPipeline, ModelType, TrainingJob, ModelMetrics
from ...ml.synthetic_data_generator import SyntheticDataGenerator
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/scoring", tags=["scoring"])


# Pydantic models for request/response
class ScoreRequest(BaseModel):
    """Request model for scoring endpoint."""
    customer_features: Dict[str, Any] = Field(..., description="Customer features for scoring")
    model_type: str = Field(default="lead_scoring", description="Type of model to use")
    department_id: Optional[str] = Field(None, description="Department context")


class ScoreResponse(BaseModel):
    """Response model for scoring endpoint."""
    customer_id: Optional[str] = Field(None, description="Customer identifier if provided")
    score: float = Field(..., description="Calculated score (0-1 range)")
    model_type: str = Field(..., description="Model type used")
    model_id: Optional[str] = Field(None, description="Model ID used for prediction")
    confidence: Optional[float] = Field(None, description="Prediction confidence")
    explanation: Optional[Dict] = Field(None, description="Score explanation")
    timestamp: str = Field(..., description="Prediction timestamp")


class TrainModelRequest(BaseModel):
    """Request model for model training."""
    model_type: str = Field(..., description="Type of model to train")
    use_synthetic_data: bool = Field(default=True, description="Use synthetic data for training")
    num_samples: int = Field(default=1000, ge=100, le=10000, description="Number of synthetic samples")
    department_id: Optional[str] = Field(None, description="Department context")
    auto_deploy: bool = Field(default=False, description="Auto-deploy if performance thresholds met")


class TrainingJobResponse(BaseModel):
    """Response model for training job."""
    job_id: str = Field(..., description="Training job ID")
    job_name: str = Field(..., description="Training job name")
    status: str = Field(..., description="Current job status")
    progress_percentage: float = Field(..., description="Training progress (0-100)")
    model_type: str = Field(..., description="Model type being trained")
    started_at: Optional[str] = Field(None, description="Job start timestamp")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    model_id: str = Field(..., description="Model identifier")
    model_name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type")
    version: str = Field(..., description="Model version")
    status: str = Field(..., description="Model status")
    accuracy: float = Field(..., description="Model accuracy")
    precision: float = Field(..., description="Model precision")
    recall: float = Field(..., description="Model recall")
    f1_score: float = Field(..., description="F1 score")
    deployed_at: Optional[str] = Field(None, description="Deployment timestamp")
    training_samples: int = Field(..., description="Number of training samples")


class BatchScoreRequest(BaseModel):
    """Request model for batch scoring."""
    customers: List[Dict[str, Any]] = Field(..., description="List of customer feature sets")
    model_type: str = Field(default="lead_scoring", description="Type of model to use")
    department_id: Optional[str] = Field(None, description="Department context")


class BatchScoreResponse(BaseModel):
    """Response model for batch scoring."""
    results: List[ScoreResponse] = Field(..., description="Scoring results")
    total_processed: int = Field(..., description="Total customers processed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


# Dependency to get scoring pipeline
async def get_scoring_pipeline() -> ScoringPipeline:
    """Get scoring pipeline instance."""
    return ScoringPipeline()


# Dependency to get synthetic data generator
async def get_data_generator() -> SyntheticDataGenerator:
    """Get synthetic data generator instance."""
    return SyntheticDataGenerator()


@router.post("/predict", response_model=ScoreResponse)
async def predict_score(
    request: ScoreRequest,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline)
):
    """
    Predict customer score using trained ML models.

    Args:
        request: Scoring request with customer features
        scoring_pipeline: Scoring pipeline dependency

    Returns:
        Prediction score and metadata
    """
    try:
        logger.info(f"Processing score prediction for model type: {request.model_type}")

        # Validate model type
        try:
            model_type = ModelType(request.model_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type: {request.model_type}. Valid types: {[t.value for t in ModelType]}"
            )

        # Make prediction
        score = await scoring_pipeline.predict(
            model_type=model_type,
            features=request.customer_features,
            department_id=request.department_id
        )

        if score is None:
            raise HTTPException(
                status_code=503,
                detail=f"No trained model available for {request.model_type}"
            )

        # Get model info for response
        model_info = scoring_pipeline.model_registry.get_production_model(model_type)
        model_id = model_info[0] if model_info else None

        return ScoreResponse(
            customer_id=request.customer_features.get("customer_id"),
            score=score,
            model_type=request.model_type,
            model_id=model_id,
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing score prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/batch", response_model=BatchScoreResponse)
async def predict_batch_scores(
    request: BatchScoreRequest,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline)
):
    """
    Predict scores for multiple customers in batch.

    Args:
        request: Batch scoring request
        scoring_pipeline: Scoring pipeline dependency

    Returns:
        Batch prediction results
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Processing batch score prediction for {len(request.customers)} customers")

        # Validate model type
        try:
            model_type = ModelType(request.model_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type: {request.model_type}"
            )

        results = []

        for customer_features in request.customers:
            try:
                score = await scoring_pipeline.predict(
                    model_type=model_type,
                    features=customer_features,
                    department_id=request.department_id
                )

                if score is not None:
                    results.append(ScoreResponse(
                        customer_id=customer_features.get("customer_id"),
                        score=score,
                        model_type=request.model_type,
                        timestamp=datetime.utcnow().isoformat()
                    ))
                else:
                    logger.warning(f"No prediction for customer {customer_features.get('customer_id')}")

            except Exception as e:
                logger.error(f"Error predicting for customer {customer_features.get('customer_id')}: {e}")
                continue

        # Calculate processing time
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return BatchScoreResponse(
            results=results,
            total_processed=len(results),
            processing_time_ms=processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@router.post("/train", response_model=TrainingJobResponse)
async def train_model(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline),
    data_generator: SyntheticDataGenerator = Depends(get_data_generator)
):
    """
    Start training a new ML model.

    Args:
        request: Training request parameters
        background_tasks: FastAPI background tasks
        scoring_pipeline: Scoring pipeline dependency
        data_generator: Data generator dependency

    Returns:
        Training job information
    """
    try:
        logger.info(f"Starting model training for type: {request.model_type}")

        # Validate model type
        try:
            model_type = ModelType(request.model_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type: {request.model_type}"
            )

        # Generate or get training data
        if request.use_synthetic_data:
            training_data = data_generator.generate_customer_dataset(
                num_customers=request.num_samples
            )
        else:
            # In production, would load from database
            raise HTTPException(
                status_code=400,
                detail="Real data training not implemented in demo. Use synthetic data."
            )

        # Configure model for auto-deploy
        custom_config = None
        if request.auto_deploy:
            default_config = scoring_pipeline.default_configs.get(model_type)
            if default_config:
                custom_config = default_config
                custom_config.auto_deploy = True

        # Start training job
        training_job = await scoring_pipeline.train_model(
            model_type=model_type,
            training_data=training_data,
            custom_config=custom_config,
            department_id=request.department_id or ""
        )

        return TrainingJobResponse(
            job_id=training_job.job_id,
            job_name=training_job.job_name,
            status=training_job.status.value,
            progress_percentage=training_job.progress_percentage,
            model_type=request.model_type,
            started_at=training_job.started_at.isoformat() if training_job.started_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting model training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed to start: {str(e)}")


@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job_status(
    job_id: str,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline)
):
    """
    Get the status of a training job.

    Args:
        job_id: Training job identifier
        scoring_pipeline: Scoring pipeline dependency

    Returns:
        Training job status and progress
    """
    try:
        training_job = scoring_pipeline.get_training_job_status(job_id)

        if not training_job:
            raise HTTPException(
                status_code=404,
                detail=f"Training job {job_id} not found"
            )

        return TrainingJobResponse(
            job_id=training_job.job_id,
            job_name=training_job.job_name,
            status=training_job.status.value,
            progress_percentage=training_job.progress_percentage,
            model_type=training_job.model_config.model_type.value,
            started_at=training_job.started_at.isoformat() if training_job.started_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving training job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/models", response_model=List[ModelInfoResponse])
async def list_models(
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline)
):
    """
    List available ML models.

    Args:
        model_type: Filter by model type
        status: Filter by model status
        scoring_pipeline: Scoring pipeline dependency

    Returns:
        List of available models
    """
    try:
        models = []

        for model_id, model_metrics in scoring_pipeline.model_registry.models.items():
            # Apply filters
            if model_type and model_metrics.model_type.value != model_type:
                continue
            if status and model_metrics.status.value != status:
                continue

            models.append(ModelInfoResponse(
                model_id=model_id,
                model_name=model_metrics.model_name,
                model_type=model_metrics.model_type.value,
                version=model_metrics.model_version,
                status=model_metrics.status.value,
                accuracy=model_metrics.accuracy,
                precision=model_metrics.precision,
                recall=model_metrics.recall,
                f1_score=model_metrics.f1_score,
                deployed_at=model_metrics.deployed_at.isoformat() if model_metrics.deployed_at else None,
                training_samples=model_metrics.training_samples
            ))

        return models

    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline)
):
    """
    Deploy a model to production.

    Args:
        model_id: Model identifier to deploy
        scoring_pipeline: Scoring pipeline dependency

    Returns:
        Deployment confirmation
    """
    try:
        success = scoring_pipeline.model_registry.promote_to_production(model_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found or deployment failed"
            )

        return {
            "message": f"Model {model_id} successfully deployed to production",
            "model_id": model_id,
            "deployed_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.get("/health")
async def scoring_health_check():
    """Health check for scoring service."""
    try:
        # Test pipeline initialization
        pipeline = ScoringPipeline()

        return {
            "status": "healthy",
            "service": "scoring-api",
            "models_available": len(pipeline.model_registry.models),
            "production_models": len(pipeline.model_registry.production_models),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Scoring service health check failed: {e}")
        raise HTTPException(status_code=503, detail="Scoring service unhealthy")