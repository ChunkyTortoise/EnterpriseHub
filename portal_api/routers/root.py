import os

from fastapi import APIRouter

from portal_api.models import RootResponse

router = APIRouter(tags=["root"])


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(
        message="GHL Real Estate AI API is running",
        docs="/docs",
        health="/health",
        reset="/system/reset",
        state="/system/state",
        state_details="/system/state/details",
        environment=os.getenv("ENVIRONMENT", "development"),
    )
