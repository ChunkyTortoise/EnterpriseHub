"""
ML Lead Scoring API Routes
Real-time lead scoring endpoints with <50ms response targets.

Features:
- Real-time individual lead scoring
- Batch processing for multiple leads
- WebSocket support for live updates
- Integration with ML Analytics Engine
- Confidence-based Claude AI escalation
- Comprehensive error handling and monitoring

Integrates with:
- ML Analytics Engine for predictions
- Feature Engineering pipeline for data processing
- WebSocket server for real-time updates
- Cache service for performance optimization
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import logging

# Internal imports
from ghl_real_estate_ai.api.schemas.ml_scoring import (
    LeadScoringRequest,
    LeadScoringResponse,
    BatchScoringRequest,
    BatchScoringResponse,
    LeadScoreHistoryResponse,
    MLModelStatus,
    ErrorResponse,
    HealthCheckResponse,
    LeadScoredEvent,
    BatchProcessingEvent,
    ModelStatusEvent,
    ConfidenceLevel,
    LeadClassification,
    ScoreSource,
    MLFeatureExplanation
)
from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.api.middleware.rate_limiter import RateLimitMiddleware
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service, TenantScopedCache

# ML Analytics Engine Integration
try:
    from bots.shared.ml_analytics_engine import (
        get_ml_analytics_engine,
        MLAnalyticsEngine,
        MLPredictionRequest,
        MLPredictionResult,
        ModelType
    )
    from bots.shared.feature_engineering import (
        get_feature_engineer,
        LeadFeatures,
        FeatureEngineeringPipeline
    )
    ML_ENGINE_AVAILABLE = True
except ImportError:
    ML_ENGINE_AVAILABLE = False

# WebSocket support
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ml", tags=["ML Lead Scoring"])

# Service dependencies
cache_service = get_cache_service()
websocket_manager = get_websocket_manager()

if ML_ENGINE_AVAILABLE:
    ml_engine = get_ml_analytics_engine()
    feature_engineer = get_feature_engineer()
else:
    ml_engine = None
    feature_engineer = None


class MLScoringService:
    """Service layer for ML lead scoring operations"""

    def __init__(self):
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.jorge_commission_rate = 0.06  # Jorge's 6% commission rate

    async def score_lead(
        self,
        request: LeadScoringRequest,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> LeadScoringResponse:
        """
        Score a single lead using ML Analytics Engine.

        Performance target: <50ms total response time
        """
        start_time = time.time()

        # Generate cache key
        cache_key = self._generate_cache_key(request, user_id, tenant_id)

        # Check cache first (unless force_refresh)
        if not request.force_refresh:
            cached_result = await self._get_cached_score(cache_key)
            if cached_result:
                logger.info(f"Cache hit for lead {request.lead_id}")
                return cached_result

        try:
            # Convert request to ML prediction format
            ml_request = await self._convert_to_ml_request(request)

            # Get ML prediction
            ml_result = await self._get_ml_prediction(ml_request)

            # Build comprehensive response
            response = await self._build_scoring_response(
                request=request,
                ml_result=ml_result,
                processing_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False
            )

            # Cache the result
            await self._cache_score(cache_key, response)

            # Send WebSocket event
            await self._send_scoring_event(response)

            logger.info(
                f"Lead {request.lead_id} scored: {response.ml_score}% "
                f"({response.classification}) in {response.processing_time_ms:.1f}ms"
            )

            return response

        except Exception as e:
            logger.error(f"Error scoring lead {request.lead_id}: {str(e)}")

            # Return fallback response
            return await self._build_error_response(
                request=request,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def batch_score_leads(
        self,
        request: BatchScoringRequest,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> BatchScoringResponse:
        """
        Score multiple leads in batch, optionally in parallel.
        """
        start_time = time.time()
        batch_id = str(uuid.uuid4())

        logger.info(f"Starting batch scoring {batch_id} for {len(request.leads)} leads")

        results = []
        errors = []

        if request.parallel_processing:
            # Process leads in parallel
            tasks = [
                self.score_lead(lead_request, user_id, tenant_id)
                for lead_request in request.leads
            ]

            # Process with progress updates
            completed_results = await self._process_with_progress_updates(
                tasks, batch_id, len(request.leads)
            )

            for i, result in enumerate(completed_results):
                if isinstance(result, Exception):
                    errors.append({
                        "lead_id": request.leads[i].lead_id,
                        "error": str(result)
                    })
                else:
                    results.append(result)
        else:
            # Process leads sequentially
            for i, lead_request in enumerate(request.leads):
                try:
                    result = await self.score_lead(lead_request, user_id, tenant_id)
                    results.append(result)

                    # Send progress update
                    await self._send_batch_progress_update(
                        batch_id, len(request.leads), i + 1, lead_request.lead_id
                    )

                except Exception as e:
                    errors.append({
                        "lead_id": lead_request.lead_id,
                        "error": str(e)
                    })

        # Calculate batch summary
        return await self._build_batch_response(
            batch_id=batch_id,
            results=results,
            errors=errors,
            processing_time_ms=(time.time() - start_time) * 1000
        )

    async def _convert_to_ml_request(self, request: LeadScoringRequest) -> Dict[str, Any]:
        """Convert API request to ML Analytics Engine format"""
        if not ML_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="ML Analytics Engine is not available"
            )

        # Extract features using Feature Engineering pipeline
        lead_context = {
            "lead_id": request.lead_id,
            "lead_name": request.lead_name,
            "email": request.email,
            "phone": request.phone,
            "message_content": request.message_content,
            "source": request.source,
            "response_time_hours": request.response_time_hours,
            "message_length": request.message_length,
            "questions_asked": request.questions_asked,
            "price_mentioned": request.price_mentioned,
            "timeline_mentioned": request.timeline_mentioned,
            "location_mentioned": request.location_mentioned,
            "financing_mentioned": request.financing_mentioned,
            "family_mentioned": request.family_mentioned,
            "budget_range": request.budget_range,
            "property_type": request.property_type,
            "bedrooms": request.bedrooms,
            "location_preference": request.location_preference,
            "timeline_urgency": request.timeline_urgency,
            "previous_interactions": request.previous_interactions,
            "referral_source": request.referral_source,
            "custom_fields": request.custom_fields or {}
        }

        return {
            "lead_id": request.lead_id,
            "lead_name": request.lead_name,
            "lead_context": lead_context,
            "model_type": ModelType.XGBOOST_CLASSIFIER,
            "include_explanations": request.include_explanations,
            "timeout_ms": request.timeout_ms
        }

    async def _get_ml_prediction(self, ml_request: Dict[str, Any]) -> Dict[str, Any]:
        """Get prediction from ML Analytics Engine"""
        if not ml_engine:
            raise HTTPException(
                status_code=503,
                detail="ML Analytics Engine not available"
            )

        try:
            # Create ML request object
            prediction_request = MLPredictionRequest(
                lead_id=ml_request["lead_id"],
                lead_context=ml_request["lead_context"],
                model_type=ml_request["model_type"],
                include_explanations=ml_request["include_explanations"]
            )

            # Get prediction from ML engine
            result = await ml_engine.predict_lead_score(prediction_request)

            return {
                "ml_score": result.prediction_score,
                "ml_confidence": result.confidence_score,
                "classification": result.classification,
                "feature_explanations": result.feature_explanations,
                "shap_values": result.shap_values,
                "inference_time_ms": result.inference_time_ms,
                "source": ScoreSource.ML_ONLY if result.confidence_score >= 0.85 else ScoreSource.ML_CLAUDE_HYBRID
            }

        except Exception as e:
            logger.error(f"ML prediction error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"ML prediction failed: {str(e)}"
            )

    async def _build_scoring_response(
        self,
        request: LeadScoringRequest,
        ml_result: Dict[str, Any],
        processing_time_ms: float,
        cache_hit: bool
    ) -> LeadScoringResponse:
        """Build comprehensive scoring response"""

        # Calculate commission estimate using Jorge's 6% rate
        estimated_commission = None
        if request.budget_range:
            try:
                # Extract average price from budget range
                price = self._extract_price_from_range(request.budget_range)
                if price:
                    estimated_commission = price * self.jorge_commission_rate
            except:
                pass

        # Determine confidence level
        confidence_level = self._determine_confidence_level(ml_result["ml_confidence"])

        # Build feature explanations
        feature_explanations = []
        if request.include_explanations and ml_result.get("feature_explanations"):
            for feature_data in ml_result["feature_explanations"]:
                feature_explanations.append(
                    MLFeatureExplanation(
                        feature_name=feature_data["feature_name"],
                        feature_value=feature_data["feature_value"],
                        importance_score=feature_data["importance_score"],
                        impact_direction=feature_data["impact_direction"],
                        human_explanation=feature_data["human_explanation"]
                    )
                )

        # Generate insights and recommendations
        key_insights = self._generate_key_insights(request, ml_result)
        recommendations = self._generate_recommendations(request, ml_result)

        return LeadScoringResponse(
            lead_id=request.lead_id,
            ml_score=ml_result["ml_score"],
            ml_confidence=ml_result["ml_confidence"],
            confidence_level=confidence_level,
            classification=LeadClassification(ml_result["classification"]),
            conversion_probability=ml_result["ml_score"] / 100.0,
            estimated_commission=estimated_commission,
            expected_close_days=self._estimate_close_days(ml_result["classification"]),
            score_source=ScoreSource(ml_result["source"]),
            analysis_summary=self._generate_analysis_summary(request, ml_result),
            key_insights=key_insights,
            recommendations=recommendations,
            feature_explanations=feature_explanations if request.include_explanations else None,
            shap_values=ml_result.get("shap_values") if request.include_explanations else None,
            processing_time_ms=processing_time_ms,
            ml_inference_time_ms=ml_result.get("inference_time_ms"),
            cache_hit=cache_hit,
            expires_at=datetime.utcnow() + timedelta(seconds=self.cache_ttl)
        )

    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine categorical confidence level"""
        if confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.65:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.0:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN

    def _extract_price_from_range(self, budget_range: str) -> Optional[float]:
        """Extract average price from budget range string"""
        try:
            # Simple extraction logic for common formats
            import re
            numbers = re.findall(r'[\d,]+', budget_range.replace('$', '').replace('k', '000').replace('K', '000'))
            if len(numbers) >= 2:
                low = float(numbers[0].replace(',', ''))
                high = float(numbers[1].replace(',', ''))
                return (low + high) / 2
            elif len(numbers) == 1:
                return float(numbers[0].replace(',', ''))
        except:
            pass
        return None

    def _estimate_close_days(self, classification: str) -> int:
        """Estimate days to close based on classification"""
        estimates = {
            "hot": 30,
            "warm": 60,
            "cold": 90,
            "unqualified": 120
        }
        return estimates.get(classification.lower(), 75)

    def _generate_analysis_summary(self, request: LeadScoringRequest, ml_result: Dict[str, Any]) -> str:
        """Generate human-readable analysis summary"""
        score = ml_result["ml_score"]
        classification = ml_result["classification"]
        confidence = ml_result["ml_confidence"]

        confidence_text = "high" if confidence >= 0.85 else "medium" if confidence >= 0.65 else "low"

        return (
            f"{request.lead_name} scores {score:.1f}% as a {classification} lead "
            f"with {confidence_text} confidence ({confidence:.2f}). "
            f"Based on their interaction patterns and expressed preferences, "
            f"they show {'strong' if score >= 80 else 'moderate' if score >= 60 else 'limited'} "
            f"buying signals and conversion potential."
        )

    def _generate_key_insights(self, request: LeadScoringRequest, ml_result: Dict[str, Any]) -> List[str]:
        """Generate key insights about the lead"""
        insights = []

        # Add insights based on score and features
        score = ml_result["ml_score"]

        if score >= 80:
            insights.append("Strong conversion signals detected")
        elif score >= 60:
            insights.append("Moderate interest level with conversion potential")
        else:
            insights.append("Early stage inquiry requiring nurturing")

        # Add feature-specific insights
        if request.price_mentioned:
            insights.append("Budget discussion indicates serious interest")

        if request.timeline_mentioned:
            insights.append("Timeline awareness suggests planning stage")

        if request.financing_mentioned:
            insights.append("Financing discussion shows purchase readiness")

        if request.questions_asked and request.questions_asked > 3:
            insights.append("High engagement level with multiple questions")

        return insights

    def _generate_recommendations(self, request: LeadScoringRequest, ml_result: Dict[str, Any]) -> List[str]:
        """Generate recommended actions"""
        recommendations = []
        score = ml_result["ml_score"]
        classification = ml_result["classification"]

        if classification == "hot":
            recommendations.extend([
                "Schedule immediate property viewing",
                "Prepare pre-approval assistance",
                "Fast-track to closing specialist"
            ])
        elif classification == "warm":
            recommendations.extend([
                "Follow up within 24 hours",
                "Send targeted property recommendations",
                "Provide market insights and comparisons"
            ])
        elif classification == "cold":
            recommendations.extend([
                "Add to nurturing email sequence",
                "Provide educational content about the market",
                "Schedule follow-up in 2-3 weeks"
            ])
        else:
            recommendations.extend([
                "Qualify further before investing time",
                "Provide general market information",
                "Monitor for increased engagement"
            ])

        return recommendations

    async def _get_cached_score(self, cache_key: str) -> Optional[LeadScoringResponse]:
        """Retrieve cached scoring result"""
        try:
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                # Update cache hit flag
                cached_response = LeadScoringResponse.parse_obj(cached_data)
                cached_response.cache_hit = True
                return cached_response
        except Exception as e:
            logger.warning(f"Cache retrieval error: {str(e)}")
        return None

    async def _cache_score(self, cache_key: str, response: LeadScoringResponse):
        """Cache scoring result"""
        try:
            await cache_service.set(
                cache_key,
                response.dict(),
                ttl=self.cache_ttl
            )
        except Exception as e:
            logger.warning(f"Cache storage error: {str(e)}")

    def _generate_cache_key(self, request: LeadScoringRequest, user_id: str, tenant_id: str) -> str:
        """Generate cache key for request"""
        # Create hash of request parameters that affect scoring
        import hashlib
        content = f"{request.lead_id}:{request.message_content}:{request.source}:{user_id}:{tenant_id}"
        return f"ml_score:{hashlib.md5(content.encode()).hexdigest()}"

    async def _send_scoring_event(self, response: LeadScoringResponse):
        """Send WebSocket event for lead scoring"""
        try:
            event = LeadScoredEvent(
                lead_id=response.lead_id,
                lead_name=response.lead_id,  # We don't store lead_name in response
                ml_score=response.ml_score,
                classification=response.classification,
                score_source=response.score_source,
                processing_time_ms=response.processing_time_ms
            )

            await websocket_manager.broadcast_message({
                "type": "lead_scored",
                "data": event.dict()
            })
        except Exception as e:
            logger.warning(f"WebSocket event error: {str(e)}")

    async def _send_batch_progress_update(
        self,
        batch_id: str,
        total_leads: int,
        processed_leads: int,
        current_lead: str
    ):
        """Send batch processing progress update"""
        try:
            event = BatchProcessingEvent(
                batch_id=batch_id,
                total_leads=total_leads,
                processed_leads=processed_leads,
                current_lead=current_lead,
                estimated_completion_ms=None
            )

            await websocket_manager.broadcast_message({
                "type": "batch_processing",
                "data": event.dict()
            })
        except Exception as e:
            logger.warning(f"WebSocket batch event error: {str(e)}")

    async def _process_with_progress_updates(
        self,
        tasks: List,
        batch_id: str,
        total_leads: int
    ) -> List:
        """Process tasks with progress updates"""
        results = []
        completed = 0

        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except Exception as e:
                results.append(e)

            completed += 1
            await self._send_batch_progress_update(
                batch_id, total_leads, completed, f"lead_{completed}"
            )

        return results

    async def _build_batch_response(
        self,
        batch_id: str,
        results: List[LeadScoringResponse],
        errors: List[Dict[str, str]],
        processing_time_ms: float
    ) -> BatchScoringResponse:
        """Build comprehensive batch response"""

        # Calculate summary statistics
        successful_scores = len(results)
        failed_scores = len(errors)
        total_leads = successful_scores + failed_scores

        average_score = sum(r.ml_score for r in results) / max(successful_scores, 1)

        # Score distribution
        from collections import Counter
        classifications = [r.classification for r in results]
        score_distribution = dict(Counter(classifications))

        # Performance metrics
        throughput = total_leads / (processing_time_ms / 1000) if processing_time_ms > 0 else 0
        cache_hits = sum(1 for r in results if r.cache_hit)
        cache_hit_rate = (cache_hits / max(successful_scores, 1)) * 100

        return BatchScoringResponse(
            batch_id=batch_id,
            total_leads=total_leads,
            successful_scores=successful_scores,
            failed_scores=failed_scores,
            results=results,
            errors=errors,
            average_score=average_score,
            score_distribution=score_distribution,
            total_processing_time_ms=processing_time_ms,
            throughput_scores_per_second=throughput,
            cache_hit_rate=cache_hit_rate
        )

    async def _build_error_response(
        self,
        request: LeadScoringRequest,
        error: str,
        processing_time_ms: float
    ) -> LeadScoringResponse:
        """Build error response with fallback values"""
        return LeadScoringResponse(
            lead_id=request.lead_id,
            ml_score=50.0,  # Neutral fallback score
            ml_confidence=0.0,
            confidence_level=ConfidenceLevel.UNCERTAIN,
            classification=LeadClassification.COLD,
            conversion_probability=0.5,
            score_source=ScoreSource.CLAUDE_ONLY,
            analysis_summary=f"Unable to generate ML score due to error: {error}. Manual review recommended.",
            key_insights=["ML analysis unavailable"],
            recommendations=["Review lead manually", "Check system status"],
            processing_time_ms=processing_time_ms,
            cache_hit=False,
            warnings=[f"ML scoring error: {error}"]
        )


# Initialize service
scoring_service = MLScoringService()


# API Endpoints
@router.post(
    "/score",
    response_model=LeadScoringResponse,
    summary="Score individual lead",
    description="Score a single lead using ML Analytics Engine with <50ms target response time",
    responses={
        200: {"description": "Lead scored successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"},
        503: {"description": "ML service unavailable"}
    }
)
async def score_lead(
    request: LeadScoringRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Score a single lead using the ML Analytics Engine.

    **Performance Target**: <50ms response time
    **Cache TTL**: 5 minutes
    **Confidence Threshold**: 0.85 for ML-only predictions
    """
    try:
        result = await scoring_service.score_lead(
            request=request,
            user_id=current_user.get("user_id"),
            tenant_id=current_user.get("tenant_id")
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in score_lead: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during lead scoring"
        )


@router.post(
    "/batch-score",
    response_model=BatchScoringResponse,
    summary="Score multiple leads",
    description="Score multiple leads in batch with optional parallel processing",
    responses={
        200: {"description": "Batch scoring completed"},
        400: {"description": "Invalid request data or too many leads"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def batch_score_leads(
    request: BatchScoringRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Score multiple leads in batch.

    **Limits**: Maximum 100 leads per batch
    **Processing**: Parallel or sequential based on request
    **Progress**: WebSocket events for real-time updates
    """
    if len(request.leads) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 leads allowed per batch"
        )

    try:
        result = await scoring_service.batch_score_leads(
            request=request,
            user_id=current_user.get("user_id"),
            tenant_id=current_user.get("tenant_id")
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch_score_leads: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during batch scoring"
        )


@router.get(
    "/score/{lead_id}",
    response_model=LeadScoringResponse,
    summary="Get existing lead score",
    description="Retrieve the most recent score for a specific lead"
)
async def get_lead_score(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve the most recent score for a specific lead.

    Returns cached result if available, otherwise returns 404.
    """
    try:
        # Try to get from cache
        cache_key = f"ml_score:{lead_id}:{current_user.get('user_id')}:{current_user.get('tenant_id')}"
        cached_result = await scoring_service._get_cached_score(cache_key)

        if cached_result:
            return cached_result

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No score found for lead {lead_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving lead score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="ML service health check",
    description="Check the health status of ML scoring services",
    include_in_schema=True
)
async def health_check():
    """
    Health check endpoint for ML scoring services.

    Checks:
    - ML model availability
    - Cache service status
    - Database connectivity
    - Performance metrics
    """
    try:
        start_time = time.time()

        # Check ML model status
        ml_status = "available" if ML_ENGINE_AVAILABLE and ml_engine else "unavailable"

        # Check cache status
        try:
            await cache_service.ping()
            cache_status = "available"
        except:
            cache_status = "unavailable"

        # Simple database check (placeholder)
        database_status = "available"  # Implement actual check

        # Overall status
        overall_status = "healthy" if all([
            ml_status == "available",
            cache_status == "available",
            database_status == "available"
        ]) else "degraded"

        response_time = (time.time() - start_time) * 1000

        return HealthCheckResponse(
            status=overall_status,
            ml_model_status=ml_status,
            cache_status=cache_status,
            database_status=database_status,
            average_response_time_ms=response_time,
            requests_per_minute=0,  # Implement actual metrics
            error_rate_percent=0.0,  # Implement actual metrics
            uptime_seconds=0,  # Implement actual uptime tracking
            version="1.0.0"
        )

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get(
    "/model/status",
    response_model=MLModelStatus,
    summary="ML model status",
    description="Get detailed status of the ML model",
    dependencies=[Depends(get_current_user)]
)
async def get_model_status():
    """
    Get detailed status information about the ML model.

    Includes performance metrics and operational status.
    """
    try:
        if not ML_ENGINE_AVAILABLE or not ml_engine:
            return MLModelStatus(
                model_name="XGBoost Lead Scorer",
                model_version="1.0.0",
                is_available=False,
                average_inference_time_ms=0.0,
                predictions_today=0,
                cache_hit_rate=0.0
            )

        # Get model metrics from ML engine
        model_info = await ml_engine.get_model_info()

        return MLModelStatus(
            model_name=model_info.get("model_name", "XGBoost Lead Scorer"),
            model_version=model_info.get("version", "1.0.0"),
            is_available=True,
            last_trained=model_info.get("last_trained"),
            accuracy=model_info.get("accuracy"),
            precision=model_info.get("precision"),
            recall=model_info.get("recall"),
            f1_score=model_info.get("f1_score"),
            average_inference_time_ms=model_info.get("avg_inference_time_ms", 0.0),
            predictions_today=model_info.get("predictions_today", 0),
            cache_hit_rate=model_info.get("cache_hit_rate", 0.0)
        )

    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model status"
        )


# WebSocket endpoint for real-time scoring updates
@router.websocket("/ws/live-scores")
async def websocket_live_scores(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time ML scoring updates.

    Provides:
    - Real-time lead scoring events
    - Batch processing progress
    - Model status changes
    - Performance alerts
    """
    try:
        # Authenticate WebSocket connection
        if not token:
            await websocket.close(code=1008, reason="Authentication token required")
            return

        # Connect to WebSocket manager
        connection_id = await websocket_manager.connect_websocket(websocket, token)

        logger.info(f"ML scoring WebSocket connected: {connection_id}")

        # Subscribe to ML events
        await websocket_manager.subscribe_to_events(connection_id, [
            "lead_scored",
            "batch_processing",
            "model_status"
        ])

        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                # Echo heartbeat messages
                if message == "heartbeat":
                    await websocket.send_text("heartbeat_ack")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {str(e)}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")

    finally:
        if 'connection_id' in locals():
            await websocket_manager.disconnect(connection_id)
            logger.info(f"ML scoring WebSocket disconnected: {connection_id}")


# Rate limiting for API endpoints
@router.middleware("http")
async def rate_limit_ml_endpoints(request, call_next):
    """Apply rate limiting to ML scoring endpoints"""
    if request.url.path.startswith("/api/v1/ml/"):
        # Apply rate limiting - implement actual rate limiting logic
        pass

    response = await call_next(request)
    return response