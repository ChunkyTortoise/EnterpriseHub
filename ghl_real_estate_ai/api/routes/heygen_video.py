"""
HeyGen Personalized Video API Routes

Exposes video generation, delivery tracking, cost management, and
engagement analytics for HeyGen avatar videos.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.heygen_video_service import (
    get_heygen_service,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/video",
    tags=["HeyGen Video"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class CreateVideoRequest(BaseModel):
    lead_id: str = Field(..., description="Lead identifier")
    lead_name: str = Field(..., description="Lead's first name")
    lead_profile: Dict[str, Any] = Field(
        default_factory=dict,
        description="Lead psychographics (temperature, interests, persona)",
    )
    template: str = Field("buyer_welcome", description="Video template name")
    variables: Optional[Dict[str, str]] = Field(None, description="Additional template variables")
    avatar_style: str = Field("professional", description="Avatar style")


class VideoResultResponse(BaseModel):
    request_id: str
    lead_id: str
    video_url: str
    thumbnail_url: str
    duration_sec: int
    status: str
    cost: float
    created_at: float
    delivered_at: Optional[float] = None
    view_count: int = 0
    engagement_score: float = 0.0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/create", response_model=VideoResultResponse)
async def create_personalized_video(request: CreateVideoRequest):
    """Generate a personalized HeyGen video for a lead."""
    try:
        service = get_heygen_service()
        result = await service.create_personalized_video(
            lead_id=request.lead_id,
            lead_name=request.lead_name,
            lead_profile=request.lead_profile,
            template=request.template,
            variables=request.variables,
            avatar_style=request.avatar_style,
        )
        return VideoResultResponse(
            request_id=result.request_id,
            lead_id=result.lead_id,
            video_url=result.video_url,
            thumbnail_url=result.thumbnail_url,
            duration_sec=result.duration_sec,
            status=result.status.value,
            cost=result.cost,
            created_at=result.created_at,
            delivered_at=result.delivered_at,
            view_count=result.view_count,
            engagement_score=result.engagement_score,
        )
    except Exception as e:
        logger.error("Video creation failed for lead %s: %s", request.lead_id, e)
        raise HTTPException(500, f"Video creation error: {e}")


@router.get("/status/{request_id}")
async def get_video_status(request_id: str):
    """Check the status of a video generation request."""
    service = get_heygen_service()
    result = await service.get_video_status(request_id)
    if not result:
        raise HTTPException(404, f"Video request {request_id} not found")
    return VideoResultResponse(
        request_id=result.request_id,
        lead_id=result.lead_id,
        video_url=result.video_url,
        thumbnail_url=result.thumbnail_url,
        duration_sec=result.duration_sec,
        status=result.status.value,
        cost=result.cost,
        created_at=result.created_at,
        delivered_at=result.delivered_at,
        view_count=result.view_count,
        engagement_score=result.engagement_score,
    )


@router.post("/delivered/{request_id}")
async def mark_video_delivered(request_id: str):
    """Mark a video as delivered to the lead."""
    service = get_heygen_service()
    success = await service.mark_delivered(request_id)
    if not success:
        raise HTTPException(404, f"Video request {request_id} not found")
    return {"status": "delivered", "request_id": request_id}


@router.post("/view/{request_id}")
async def record_video_view(request_id: str):
    """Record a video view event."""
    service = get_heygen_service()
    success = await service.record_view(request_id)
    if not success:
        raise HTTPException(404, f"Video request {request_id} not found")
    return {"status": "view_recorded", "request_id": request_id}


@router.get("/lead/{lead_id}")
async def get_lead_videos(lead_id: str):
    """Get all videos generated for a specific lead."""
    service = get_heygen_service()
    videos = service.get_lead_videos(lead_id)
    return {
        "lead_id": lead_id,
        "videos": [
            {
                "request_id": v.request_id,
                "video_url": v.video_url,
                "status": v.status.value,
                "duration_sec": v.duration_sec,
                "view_count": v.view_count,
                "engagement_score": v.engagement_score,
                "created_at": v.created_at,
            }
            for v in videos
        ],
        "total": len(videos),
    }


@router.get("/costs")
async def get_cost_summary():
    """Get video generation cost tracking summary."""
    service = get_heygen_service()
    return service.get_cost_summary()


@router.get("/health")
async def video_health():
    """Health check for the HeyGen video service."""
    try:
        service = get_heygen_service()
        return {
            "status": "healthy",
            "service": "heygen_video_service",
            "api_configured": service.api_key is not None,
            "costs": service.get_cost_summary(),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
