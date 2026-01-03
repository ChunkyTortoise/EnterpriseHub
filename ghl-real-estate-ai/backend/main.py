from fastapi import FastAPI
from core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Backend API for GHL Real Estate AI Qualification Assistant"
)

@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "online",
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
