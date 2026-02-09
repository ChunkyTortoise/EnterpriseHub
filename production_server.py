"""
Jorge Ultra-Fast ML Engine Production Server
==========================================

Production-optimized FastAPI server for <25ms ML inference.
Includes health checks, monitoring, and enterprise-grade error handling.

Performance Targets:
- <25ms inference latency
- 10,000+ requests/second throughput
- 99.99% availability
- <0.1% error rate

Author: Jorge Platform Engineering Team
Version: 3.0.0
Date: 2026-01-24
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil
import uvicorn

# FastAPI and async framework
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Monitoring and metrics
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field

# ML Engine and services
from ultra_fast_ml_engine import (
    FeaturePreprocessor,
    UltraFastMLEngine,
    UltraFastPredictionRequest,
    get_ultra_fast_ml_engine,
)

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# METRICS AND MONITORING
# =============================================================================

# Prometheus metrics
REQUEST_COUNT = Counter("jorge_ml_requests_total", "Total ML inference requests", ["endpoint", "status"])
REQUEST_DURATION = Histogram("jorge_ml_request_duration_seconds", "ML request duration", ["endpoint"])
INFERENCE_DURATION = Histogram("jorge_ml_inference_duration_ms", "ML inference duration in milliseconds")
CACHE_HIT_COUNTER = Counter("jorge_ml_cache_hits_total", "Cache hits")
CACHE_MISS_COUNTER = Counter("jorge_ml_cache_misses_total", "Cache misses")
ACTIVE_REQUESTS = Gauge("jorge_ml_active_requests", "Currently active requests")
SYSTEM_CPU = Gauge("jorge_ml_system_cpu_percent", "System CPU usage")
SYSTEM_MEMORY = Gauge("jorge_ml_system_memory_percent", "System memory usage")
GPU_MEMORY = Gauge("jorge_ml_gpu_memory_percent", "GPU memory usage")

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================


class MLPredictionRequest(BaseModel):
    """ML prediction request model"""

    lead_id: str = Field(..., description="Unique lead identifier")
    features: Dict[str, Any] = Field(..., description="Lead features for prediction")
    priority: str = Field("normal", description="Request priority (high, normal, low)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MLPredictionResponse(BaseModel):
    """ML prediction response model"""

    lead_id: str
    score: float = Field(..., ge=0.0, le=1.0, description="Prediction score (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    inference_time_ms: float = Field(..., description="Inference time in milliseconds")
    model_version: str = Field(..., description="Model version used")
    cache_hit: bool = Field(..., description="Whether result came from cache")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchPredictionRequest(BaseModel):
    """Batch prediction request model"""

    requests: List[MLPredictionRequest] = Field(..., description="List of prediction requests")
    batch_id: Optional[str] = Field(None, description="Batch identifier")


class BatchPredictionResponse(BaseModel):
    """Batch prediction response model"""

    batch_id: str
    results: List[MLPredictionResponse]
    total_requests: int
    successful_predictions: int
    failed_predictions: int
    total_inference_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Service version")
    uptime_seconds: int = Field(..., description="Service uptime in seconds")
    inference_health: Dict[str, Any] = Field(..., description="ML inference health metrics")
    system_health: Dict[str, Any] = Field(..., description="System resource health")


class PerformanceStats(BaseModel):
    """Performance statistics response model"""

    avg_inference_time_ms: float
    p95_inference_time_ms: float
    p99_inference_time_ms: float
    cache_hit_rate: float
    total_predictions: int
    target_achievement: bool
    model_version: str
    optimization_status: str


# =============================================================================
# APPLICATION LIFECYCLE MANAGEMENT
# =============================================================================

# Global state
ml_engine: Optional[UltraFastMLEngine] = None
feature_preprocessor: Optional[FeaturePreprocessor] = None
service_start_time: float = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global ml_engine, feature_preprocessor

    logger.info("Starting Jorge Ultra-Fast ML Engine...")

    try:
        # Initialize ML engine
        ml_engine = get_ultra_fast_ml_engine("jorge_production")

        # Initialize feature preprocessor
        feature_preprocessor = FeaturePreprocessor()

        # Load optimized model
        model_path = os.getenv("MODEL_PATH", "/app/models/jorge_ultra_optimized.onnx")
        if os.path.exists(model_path):
            success = await ml_engine.load_optimized_model(model_path)
            if not success:
                raise Exception(f"Failed to load model from {model_path}")
            logger.info(f"Model loaded successfully from {model_path}")
        else:
            logger.error(f"Model file not found: {model_path}")
            raise Exception(f"Model file not found: {model_path}")

        # Start background monitoring
        asyncio.create_task(monitor_system_resources())

        logger.info("Jorge Ultra-Fast ML Engine started successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to start ML engine: {e}")
        sys.exit(1)

    finally:
        logger.info("Shutting down Jorge Ultra-Fast ML Engine...")


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="Jorge Ultra-Fast ML Engine",
    description="Production ML inference service with <25ms latency",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") != "production" else ["https://jorge-platform.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================


async def get_ml_engine() -> UltraFastMLEngine:
    """Get ML engine dependency"""
    if ml_engine is None:
        raise HTTPException(status_code=503, detail="ML engine not initialized")
    return ml_engine


async def get_feature_preprocessor() -> FeaturePreprocessor:
    """Get feature preprocessor dependency"""
    if feature_preprocessor is None:
        raise HTTPException(status_code=503, detail="Feature preprocessor not initialized")
    return feature_preprocessor


# =============================================================================
# BACKGROUND MONITORING
# =============================================================================


async def monitor_system_resources():
    """Background task to monitor system resources"""
    while True:
        try:
            # Update system metrics
            SYSTEM_CPU.set(psutil.cpu_percent(interval=1))
            SYSTEM_MEMORY.set(psutil.virtual_memory().percent)

            # Update GPU metrics (if available)
            try:
                import pynvml

                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_memory_percent = (mem_info.used / mem_info.total) * 100
                GPU_MEMORY.set(gpu_memory_percent)
            except Exception:
                pass  # GPU monitoring not available

            await asyncio.sleep(30)  # Update every 30 seconds

        except Exception as e:
            logger.error(f"Error in system monitoring: {e}")
            await asyncio.sleep(60)


# =============================================================================
# API ENDPOINTS
# =============================================================================


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Request middleware for monitoring and performance tracking"""
    start_time = time.perf_counter()
    ACTIVE_REQUESTS.inc()

    try:
        response = await call_next(request)

        # Record metrics
        duration = time.perf_counter() - start_time
        endpoint = request.url.path
        status = "success" if response.status_code < 400 else "error"

        REQUEST_COUNT.labels(endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)

        return response

    finally:
        ACTIVE_REQUESTS.dec()


@app.get("/health", response_model=HealthResponse)
async def health_check(engine: UltraFastMLEngine = Depends(get_ml_engine)):
    """Health check endpoint with comprehensive system status"""
    try:
        # Test ML engine with dummy prediction
        import numpy as np

        dummy_features = np.random.random(12).astype(np.float32)

        start_time = time.perf_counter()
        request = UltraFastPredictionRequest(
            lead_id="health_check", features=dummy_features, feature_hash="health_check_hash"
        )

        result = await engine.predict_ultra_fast(request)
        inference_time = time.perf_counter() - start_time

        # Determine health status
        if inference_time < 0.025:  # <25ms target
            inference_status = "healthy"
        elif inference_time < 0.050:  # <50ms warning
            inference_status = "warning"
        else:
            inference_status = "critical"

        # System health
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        if cpu_percent > 90 or memory_percent > 90:
            system_status = "critical"
        elif cpu_percent > 70 or memory_percent > 70:
            system_status = "warning"
        else:
            system_status = "healthy"

        # Overall status
        if inference_status == "healthy" and system_status == "healthy":
            overall_status = "healthy"
        elif inference_status == "critical" or system_status == "critical":
            overall_status = "critical"
        else:
            overall_status = "warning"

        return HealthResponse(
            status=overall_status,
            version="3.0.0",
            uptime_seconds=int(time.time() - service_start_time),
            inference_health={
                "status": inference_status,
                "latency_ms": inference_time * 1000,
                "target_met": inference_time < 0.025,
                "model_loaded": engine.model is not None or engine.onnx_session is not None,
            },
            system_health={
                "status": system_status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "active_requests": ACTIVE_REQUESTS._value.get(),
            },
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.get("/ready")
async def readiness_check(engine: UltraFastMLEngine = Depends(get_ml_engine)):
    """Readiness check for Kubernetes"""
    try:
        if engine.model is None and engine.onnx_session is None:
            raise HTTPException(status_code=503, detail="ML model not loaded")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@app.get("/startup")
async def startup_check():
    """Startup check for Kubernetes"""
    global ml_engine
    if ml_engine is None:
        raise HTTPException(status_code=503, detail="Service starting up")
    return {"status": "started"}


@app.post("/predict", response_model=MLPredictionResponse)
async def predict_single(
    request: MLPredictionRequest,
    engine: UltraFastMLEngine = Depends(get_ml_engine),
    preprocessor: FeaturePreprocessor = Depends(get_feature_preprocessor),
):
    """Single ML prediction endpoint with <25ms target"""
    start_time = time.perf_counter()

    try:
        # Preprocess features
        processed_features = preprocessor.transform_fast(request.features)

        # Create feature hash for caching
        import hashlib

        feature_str = json.dumps(request.features, sort_keys=True)
        feature_hash = hashlib.md5(feature_str.encode()).hexdigest()

        # Create ML request
        ml_request = UltraFastPredictionRequest(
            lead_id=request.lead_id, features=processed_features, feature_hash=feature_hash, priority=request.priority
        )

        # Run prediction
        result = await engine.predict_ultra_fast(ml_request)

        # Record metrics
        INFERENCE_DURATION.observe(result.inference_time_ms)
        if result.cache_hit:
            CACHE_HIT_COUNTER.inc()
        else:
            CACHE_MISS_COUNTER.inc()

        # Return response
        response = MLPredictionResponse(
            lead_id=result.lead_id,
            score=result.score,
            confidence=result.confidence,
            inference_time_ms=result.inference_time_ms,
            model_version=result.model_version,
            cache_hit=result.cache_hit,
        )

        total_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Prediction completed: {request.lead_id} - {total_time:.2f}ms total, {result.inference_time_ms:.2f}ms inference"
        )

        return response

    except Exception as e:
        logger.error(f"Prediction failed for {request.lead_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    engine: UltraFastMLEngine = Depends(get_ml_engine),
    preprocessor: FeaturePreprocessor = Depends(get_feature_preprocessor),
):
    """Batch ML prediction endpoint for high throughput"""
    start_time = time.perf_counter()
    batch_id = request.batch_id or f"batch_{int(time.time())}"

    try:
        # Preprocess all features
        ml_requests = []
        for req in request.requests:
            processed_features = preprocessor.transform_fast(req.features)

            import hashlib

            feature_str = json.dumps(req.features, sort_keys=True)
            feature_hash = hashlib.md5(feature_str.encode()).hexdigest()

            ml_request = UltraFastPredictionRequest(
                lead_id=req.lead_id,
                features=processed_features,
                feature_hash=feature_hash,
                priority=req.priority,
                batch_id=batch_id,
            )
            ml_requests.append(ml_request)

        # Run batch prediction
        results = await engine.predict_batch_ultra_fast(ml_requests)

        # Convert to response format
        response_results = []
        successful = 0
        failed = 0

        for result in results:
            try:
                response_result = MLPredictionResponse(
                    lead_id=result.lead_id,
                    score=result.score,
                    confidence=result.confidence,
                    inference_time_ms=result.inference_time_ms,
                    model_version=result.model_version,
                    cache_hit=result.cache_hit,
                )
                response_results.append(response_result)
                successful += 1

                # Record metrics
                INFERENCE_DURATION.observe(result.inference_time_ms)
                if result.cache_hit:
                    CACHE_HIT_COUNTER.inc()
                else:
                    CACHE_MISS_COUNTER.inc()

            except Exception as e:
                logger.error(f"Error processing result for {result.lead_id}: {e}")
                failed += 1

        total_time = (time.perf_counter() - start_time) * 1000

        batch_response = BatchPredictionResponse(
            batch_id=batch_id,
            results=response_results,
            total_requests=len(request.requests),
            successful_predictions=successful,
            failed_predictions=failed,
            total_inference_time_ms=total_time,
        )

        logger.info(
            f"Batch prediction completed: {batch_id} - {successful}/{len(request.requests)} successful in {total_time:.2f}ms"
        )

        return batch_response

    except Exception as e:
        logger.error(f"Batch prediction failed for {batch_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/performance", response_model=PerformanceStats)
async def get_performance_stats(engine: UltraFastMLEngine = Depends(get_ml_engine)):
    """Get performance statistics"""
    try:
        stats = engine.get_performance_stats()
        return PerformanceStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance stats")


@app.post("/warm-cache")
async def warm_cache(
    lead_ids: List[str], background_tasks: BackgroundTasks, engine: UltraFastMLEngine = Depends(get_ml_engine)
):
    """Warm cache for specific lead IDs"""
    try:
        # This would typically load lead features from database
        # For now, we'll create dummy features
        lead_features = []
        for lead_id in lead_ids:
            dummy_features = {
                "contact_score": 0.75,
                "engagement_score": 0.80,
                "response_time_avg": 120,
                "property_views": 5,
                "email_opens": 3,
                "call_duration": 180,
                "days_since_inquiry": 2,
                "budget_range": 500000,
                "urgency_score": 0.70,
                "lead_source": "website",
                "property_type": "single_family",
                "market_segment": "residential",
            }
            lead_features.append(dummy_features)

        # Schedule cache warming in background
        background_tasks.add_task(engine.warm_cache_for_leads, lead_ids, lead_features)

        return {"status": "cache warming scheduled", "lead_count": len(lead_ids)}

    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache warming failed: {str(e)}")


# =============================================================================
# ERROR HANDLERS
# =============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled error: {exc} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )


# =============================================================================
# GRACEFUL SHUTDOWN
# =============================================================================


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Production server configuration
    uvicorn.run(
        "production_server:app",
        host="0.0.0.0",
        port=8080,
        workers=1,  # Single worker for GPU affinity
        log_level="info",
        access_log=True,
        loop="uvloop",  # High-performance event loop
        http="httptools",  # Fast HTTP parser
        # Performance optimizations
        backlog=2048,
        limit_concurrency=10000,
        limit_max_requests=100000,
        timeout_keep_alive=5,
    )
