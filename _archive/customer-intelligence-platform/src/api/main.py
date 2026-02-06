"""
FastAPI main application for Customer Intelligence Platform.

This is the entry point for the API server providing:
- Chat conversation endpoints
- Knowledge base search
- Customer context management
- Lead scoring APIs
"""
from typing import Dict
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import chat
from ..core.tenant_middleware import TenantMiddleware
from ..utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Customer Intelligence Platform API")

    # Initialize any global resources here
    try:
        # Test AI client availability
        from ..core.ai_client import get_ai_client
        ai_client = get_ai_client()
        if ai_client.is_available():
            logger.info("AI client initialized successfully")
        else:
            logger.warning("AI client not available - check API keys")

        # Test knowledge engine
        from ..core.knowledge_engine import KnowledgeEngine
        knowledge_engine = KnowledgeEngine()
        logger.info("Knowledge engine initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Customer Intelligence Platform API")


# Create FastAPI application
app = FastAPI(
    title="Customer Intelligence Platform API",
    description="AI-Powered Customer Intelligence Platform with RAG and Lead Scoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure multi-tenant middleware
app.add_middleware(
    TenantMiddleware,
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
    enable_audit_logging=os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
)

# Include routers
app.include_router(chat.router, prefix="/api/v1")

# Import scoring routes
from .routes import scoring
app.include_router(scoring.router, prefix="/api/v1")

# Import authentication routes
from .routes import auth
app.include_router(auth.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Customer Intelligence Platform API",
        "version": "1.0.0",
        "description": "AI-Powered Customer Intelligence Platform",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with multi-tenant and database status."""
    try:
        # Check AI client
        from ..core.ai_client import get_ai_client
        ai_client = get_ai_client()
        ai_available = ai_client.is_available()

        # Check knowledge engine (basic test)
        from ..core.knowledge_engine import KnowledgeEngine
        knowledge_engine = KnowledgeEngine()

        # Check database service
        from ..utils.database_service import get_database_service
        database_service = get_database_service()
        database_health = await database_service.health_check()

        # Check Redis conversation context
        from ..core.redis_conversation_context import RedisConversationContext
        redis_context = RedisConversationContext()
        redis_health = await redis_context.health_check()

        all_healthy = (
            ai_available and
            database_health.get("status") == "healthy" and
            redis_health.get("status") == "healthy"
        )

        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": {
                "ai_client": "available" if ai_available else "unavailable",
                "knowledge_engine": "available",
                "database": database_health.get("status", "unknown"),
                "redis_context": redis_health.get("status", "unknown"),
                "api": "available"
            },
            "architecture": {
                "multi_tenant": "enabled",
                "rate_limiting": "enabled" if os.getenv("ENABLE_RATE_LIMITING", "true") == "true" else "disabled",
                "audit_logging": "enabled" if os.getenv("ENABLE_AUDIT_LOGGING", "true") == "true" else "disabled"
            },
            "environment": {
                "llm_provider": os.getenv("DEFAULT_LLM_PROVIDER", "claude"),
                "model": os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                "chroma_db": os.getenv("CHROMA_PERSIST_DIRECTORY", "./.chroma_db"),
                "database_type": database_health.get("database_type", "postgresql")
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )


if __name__ == "__main__":
    import uvicorn

    # Configure server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )