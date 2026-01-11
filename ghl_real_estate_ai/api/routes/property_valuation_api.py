"""
Property Valuation API Routes

FastAPI endpoints for property valuation services.
Provides comprehensive valuations, quick estimates, and performance analytics.

Features:
- Comprehensive property valuations (<500ms)
- Quick property estimates (<200ms)
- CMA report generation
- Performance metrics and health checks
- Error handling with professional fallbacks

Author: EnterpriseHub Development Team
Created: January 10, 2026
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from ...services.property_valuation_engine import PropertyValuationEngine
from ...services.property_valuation_models import (
    ValuationRequest,
    ComprehensiveValuation,
    QuickEstimateRequest,
    QuickEstimateResponse,
    PropertyData,
    PropertyLocation,
    PropertyFeatures,
    PropertyType
)
from ...utils.async_utils import safe_run_async
from ...core.dependencies import get_current_user
from ...core.rate_limiting import RateLimiter
from ...core.monitoring import api_metrics

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/api/v1/valuation",
    tags=["property_valuation"],
    responses={
        404: {"description": "Property not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)

# Initialize valuation engine
valuation_engine = PropertyValuationEngine()

# Rate limiting
rate_limiter = RateLimiter(
    default_limit=100,  # 100 requests per minute
    valuation_limit=30,  # 30 comprehensive valuations per minute
    quick_estimate_limit=60  # 60 quick estimates per minute
)


@router.post(
    "/comprehensive",
    response_model=ComprehensiveValuation,
    status_code=HTTP_200_OK,
    summary="Generate comprehensive property valuation",
    description="Generate detailed property valuation with MLS data, ML predictions, and AI insights"
)
@api_metrics.track("valuation_comprehensive")
@rate_limiter.limit("valuation")
async def generate_comprehensive_valuation(
    request: ValuationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ComprehensiveValuation:
    """
    Generate comprehensive property valuation.

    Performance Target: <500ms
    Accuracy Target: 95%+ within 5% of actual value

    Args:
        request: Valuation request with property data and options
        background_tasks: Background tasks for async processing
        current_user: Authenticated user information

    Returns:
        ComprehensiveValuation with all analysis results

    Raises:
        HTTPException: 400 for invalid input, 500 for processing errors
    """
    start_time = datetime.utcnow()

    try:
        logger.info(
            f"Starting comprehensive valuation for user {current_user.get('id')} "
            f"property {request.property_data.id}"
        )

        # Validate property data
        _validate_property_data(request.property_data)

        # Add request context
        request.requested_by = current_user.get("id")
        request.request_context = {
            "user_role": current_user.get("role"),
            "api_version": "v1",
            "request_timestamp": start_time.isoformat()
        }

        # Generate valuation
        valuation = await safe_run_async(
            valuation_engine.generate_comprehensive_valuation(request)
        )

        # Add background tasks for analytics and caching
        background_tasks.add_task(
            _track_valuation_analytics,
            valuation,
            current_user.get("id"),
            request
        )

        # Log successful completion
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Comprehensive valuation completed for property {request.property_data.id} "
            f"in {processing_time:.0f}ms"
        )

        return valuation

    except ValueError as e:
        logger.warning(f"Invalid valuation request: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid property data: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Comprehensive valuation failed: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Valuation service temporarily unavailable. Please try again."
        )


@router.post(
    "/quick-estimate",
    response_model=QuickEstimateResponse,
    status_code=HTTP_200_OK,
    summary="Generate quick property estimate",
    description="Generate rapid property estimate using cached data and simple models"
)
@api_metrics.track("valuation_quick_estimate")
@rate_limiter.limit("quick_estimate")
async def generate_quick_estimate(
    request: QuickEstimateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> QuickEstimateResponse:
    """
    Generate quick property estimate.

    Performance Target: <200ms

    Args:
        request: Quick estimate request with basic property info
        current_user: Authenticated user information

    Returns:
        QuickEstimateResponse with rapid estimate

    Raises:
        HTTPException: 400 for invalid input, 500 for processing errors
    """
    start_time = datetime.utcnow()

    try:
        logger.info(
            f"Starting quick estimate for user {current_user.get('id')} "
            f"address {request.address}"
        )

        # Validate address data
        _validate_address_data(request)

        # Generate quick estimate
        estimate = await safe_run_async(
            valuation_engine.generate_quick_estimate(request)
        )

        # Log successful completion
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Quick estimate completed for {request.address} "
            f"in {processing_time:.0f}ms"
        )

        return estimate

    except ValueError as e:
        logger.warning(f"Invalid quick estimate request: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid address data: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Quick estimate failed: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quick estimate service temporarily unavailable. Please try again."
        )


@router.get(
    "/property/{property_id}",
    response_model=ComprehensiveValuation,
    summary="Get existing property valuation",
    description="Retrieve previously generated property valuation by ID"
)
@api_metrics.track("valuation_retrieve")
async def get_property_valuation(
    property_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ComprehensiveValuation:
    """
    Retrieve existing property valuation.

    Args:
        property_id: Property identifier
        current_user: Authenticated user information

    Returns:
        Cached ComprehensiveValuation if available

    Raises:
        HTTPException: 404 if valuation not found
    """
    try:
        logger.info(f"Retrieving valuation for property {property_id}")

        # Check cache for existing valuation
        cached_valuation = await safe_run_async(
            valuation_engine._get_cached_valuation(property_id)
        )

        if not cached_valuation:
            raise HTTPException(
                status_code=404,
                detail=f"Valuation not found for property {property_id}"
            )

        # Check if valuation is expired
        if valuation_engine._is_valuation_expired(cached_valuation):
            raise HTTPException(
                status_code=404,
                detail=f"Valuation expired for property {property_id}. Please request a new valuation."
            )

        return cached_valuation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve valuation for property {property_id}: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve property valuation"
        )


@router.post(
    "/batch",
    response_model=Dict[str, ComprehensiveValuation],
    summary="Batch property valuations",
    description="Generate valuations for multiple properties in parallel"
)
@api_metrics.track("valuation_batch")
@rate_limiter.limit("valuation", multiplier=lambda request: len(request))
async def generate_batch_valuations(
    requests: Dict[str, ValuationRequest],
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, ComprehensiveValuation]:
    """
    Generate batch property valuations.

    Args:
        requests: Dictionary of property_id -> ValuationRequest
        background_tasks: Background tasks for async processing
        current_user: Authenticated user information

    Returns:
        Dictionary of property_id -> ComprehensiveValuation

    Raises:
        HTTPException: 400 if too many requests, 500 for processing errors
    """
    start_time = datetime.utcnow()

    try:
        # Limit batch size
        if len(requests) > 10:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Batch size limited to 10 properties. Please split into smaller batches."
            )

        logger.info(
            f"Starting batch valuation for user {current_user.get('id')} "
            f"with {len(requests)} properties"
        )

        # Process valuations in parallel
        valuation_tasks = []
        for property_id, request in requests.items():
            # Add request context
            request.requested_by = current_user.get("id")
            request.request_context = {
                "batch_request": True,
                "batch_size": len(requests),
                "user_role": current_user.get("role")
            }

            task = safe_run_async(
                valuation_engine.generate_comprehensive_valuation(request)
            )
            valuation_tasks.append((property_id, task))

        # Execute all valuations in parallel
        import asyncio
        results = {}

        for property_id, task in valuation_tasks:
            try:
                valuation = await task
                results[property_id] = valuation
            except Exception as e:
                logger.error(f"Batch valuation failed for property {property_id}: {e}")
                # Continue with other properties
                continue

        # Add background analytics tracking
        background_tasks.add_task(
            _track_batch_analytics,
            results,
            current_user.get("id"),
            len(requests)
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Batch valuation completed: {len(results)}/{len(requests)} successful "
            f"in {processing_time:.0f}ms"
        )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch valuation failed: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch valuation service temporarily unavailable"
        )


@router.get(
    "/market-trends/{zip_code}",
    response_model=Dict[str, Any],
    summary="Get market trends for ZIP code",
    description="Retrieve current market trends and statistics for a ZIP code area"
)
@api_metrics.track("market_trends")
async def get_market_trends(
    zip_code: str,
    property_type: Optional[PropertyType] = Query(None, description="Filter by property type"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get market trends for ZIP code area.

    Args:
        zip_code: ZIP code to analyze
        property_type: Optional property type filter
        current_user: Authenticated user information

    Returns:
        Market trends and statistics

    Raises:
        HTTPException: 400 for invalid ZIP, 500 for processing errors
    """
    try:
        logger.info(f"Retrieving market trends for ZIP {zip_code}")

        # Validate ZIP code
        if not zip_code or len(zip_code) < 5:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Invalid ZIP code format"
            )

        # For development, return mock market trends
        # TODO: Implement real market trend analysis
        mock_trends = {
            "zip_code": zip_code,
            "property_type": property_type.value if property_type else "all",
            "market_data": {
                "median_price": 650000,
                "price_per_sqft": 325,
                "days_on_market": 28,
                "price_trend_6m": 0.08,  # 8% increase
                "inventory_level": "low",
                "market_temperature": "hot"
            },
            "comparable_sales": {
                "count_30_days": 15,
                "count_90_days": 42,
                "avg_sale_price": 625000,
                "sale_to_list_ratio": 1.02
            },
            "predictions": {
                "price_trend_next_6m": 0.05,
                "confidence": 0.75
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return mock_trends

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market trends retrieval failed for ZIP {zip_code}: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Market trends service temporarily unavailable"
        )


@router.get(
    "/performance",
    response_model=Dict[str, Any],
    summary="Get valuation service performance metrics",
    description="Retrieve performance statistics for the valuation engine"
)
@api_metrics.track("valuation_performance")
async def get_performance_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get valuation service performance metrics.

    Args:
        current_user: Authenticated user information (admin role required)

    Returns:
        Performance metrics and statistics

    Raises:
        HTTPException: 403 if insufficient permissions
    """
    try:
        # Check admin permissions
        if current_user.get("role") not in ["admin", "agent"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to access performance metrics"
            )

        # Get performance stats from valuation engine
        performance_stats = valuation_engine.get_performance_stats()

        # Add system health indicators
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "mls_integration": "degraded",  # Would check actual service
                "ml_model": "operational",
                "claude_ai": "operational",
                "cache_system": "operational"
            }
        }

        return {
            "performance_metrics": performance_stats,
            "health_status": health_status,
            "targets": {
                "comprehensive_valuation": "< 500ms",
                "quick_estimate": "< 200ms",
                "ml_prediction": "< 100ms",
                "claude_insights": "< 150ms"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performance metrics temporarily unavailable"
        )


@router.get(
    "/health",
    response_model=Dict[str, str],
    summary="Health check endpoint",
    description="Check the health status of the valuation service"
)
async def health_check() -> Dict[str, str]:
    """
    Health check for valuation service.

    Returns:
        Health status information
    """
    try:
        # Perform basic health checks
        # TODO: Add actual service checks (database, cache, external APIs)

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "property_valuation_api"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


# Helper functions

def _validate_property_data(property_data: PropertyData) -> None:
    """Validate property data for comprehensive valuation."""
    if not property_data.location.address:
        raise ValueError("Property address is required")

    if not property_data.location.city:
        raise ValueError("Property city is required")

    if not property_data.location.state:
        raise ValueError("Property state is required")

    if not property_data.location.zip_code:
        raise ValueError("Property ZIP code is required")

    # Validate property features if provided
    if property_data.features:
        if property_data.features.bedrooms is not None and property_data.features.bedrooms < 0:
            raise ValueError("Bedrooms cannot be negative")

        if property_data.features.bathrooms is not None and property_data.features.bathrooms < 0:
            raise ValueError("Bathrooms cannot be negative")

        if property_data.features.square_footage is not None and property_data.features.square_footage <= 0:
            raise ValueError("Square footage must be positive")


def _validate_address_data(request: QuickEstimateRequest) -> None:
    """Validate address data for quick estimate."""
    if not request.address.strip():
        raise ValueError("Address is required")

    if not request.city.strip():
        raise ValueError("City is required")

    if not request.state or len(request.state) != 2:
        raise ValueError("Valid 2-character state code is required")

    if not request.zip_code or len(request.zip_code) < 5:
        raise ValueError("Valid ZIP code is required")


async def _track_valuation_analytics(
    valuation: ComprehensiveValuation,
    user_id: str,
    request: ValuationRequest
) -> None:
    """Track valuation analytics in background."""
    try:
        # TODO: Implement analytics tracking
        analytics_data = {
            "user_id": user_id,
            "property_id": valuation.property_id,
            "valuation_id": valuation.valuation_id,
            "processing_time_ms": valuation.total_processing_time_ms,
            "confidence_score": valuation.confidence_score,
            "data_sources": valuation.data_sources,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Tracked valuation analytics: {analytics_data}")

    except Exception as e:
        logger.error(f"Failed to track valuation analytics: {e}")


async def _track_batch_analytics(
    results: Dict[str, ComprehensiveValuation],
    user_id: str,
    batch_size: int
) -> None:
    """Track batch valuation analytics in background."""
    try:
        # TODO: Implement batch analytics tracking
        batch_analytics = {
            "user_id": user_id,
            "batch_size": batch_size,
            "successful_count": len(results),
            "failure_count": batch_size - len(results),
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Tracked batch analytics: {batch_analytics}")

    except Exception as e:
        logger.error(f"Failed to track batch analytics: {e}")


# Error handlers

@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception in valuation API: {exc}")
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "The valuation service encountered an unexpected error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )