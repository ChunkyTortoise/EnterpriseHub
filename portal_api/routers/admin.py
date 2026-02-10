from fastapi import APIRouter, Query

from portal_api.dependencies import get_detailed_service_state, get_service_state, reset_services
from portal_api.models import DetailedStateResponse, ResetResponse, StateResponse

router = APIRouter(tags=["admin"])


@router.post("/admin/reset", response_model=ResetResponse)
@router.post("/reset", response_model=ResetResponse)
@router.post("/system/reset", response_model=ResetResponse)
async def reset_demo_state() -> ResetResponse:
    return ResetResponse(status="success", reset=reset_services())


@router.get("/admin/state", response_model=StateResponse)
@router.get("/state", response_model=StateResponse)
@router.get("/system/state", response_model=StateResponse)
async def get_demo_state() -> StateResponse:
    return StateResponse(status="success", state=get_service_state())


@router.get("/admin/state/details", response_model=DetailedStateResponse)
@router.get("/state/details", response_model=DetailedStateResponse)
@router.get("/system/state/details", response_model=DetailedStateResponse)
async def get_demo_state_details(limit: int = Query(default=5, ge=0, le=100)) -> DetailedStateResponse:
    return DetailedStateResponse(status="success", details=get_detailed_service_state(recent_limit=limit))
