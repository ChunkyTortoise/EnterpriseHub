from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .router import router as compliance_router
from .webhooks import router as webhooks_router

app = FastAPI(
    title="Enterprise AI Compliance Platform API",
    description="API for managing AI model compliance, risk assessments, and violations.",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(compliance_router)
app.include_router(webhooks_router)

@app.on_event("startup")
async def startup_event():
    from ..database.database import init_db
    await init_db()

@app.get("/")
async def root():
    return {
        "message": "Enterprise AI Compliance Platform API is running",
        "docs": "/docs",
        "health": "/api/v1/compliance/health"
    }
