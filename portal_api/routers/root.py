import os

from fastapi import APIRouter, status

from portal_api.models import RootResponse

router = APIRouter(tags=["root"])


@router.get("/", response_model=RootResponse, status_code=status.HTTP_200_OK)
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
