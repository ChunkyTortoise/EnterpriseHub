from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service
from ghl_real_estate_ai.services.agent_state_sync import sync_service

router = APIRouter(prefix="/agent-sync", tags=["Agent Sync"])


@router.get("/state")
async def get_current_state(current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user)):
    """Returns the full authoritative AI state"""
    return sync_service.get_state()


@router.get("/delta")
async def get_state_delta(current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user)):
    """Returns incremental changes since the last update (AG-UI Protocol)"""
    return {"type": "STATE_DELTA", "delta": sync_service.get_delta()}


@router.post("/mock-update")
async def mock_agent_update(
    path: str, value: Any, current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user)
):
    """Debug endpoint to trigger a state change and see it reflect in the UI"""
    sync_service.update_state(path, value)
    return {"status": "updated", "path": path, "new_value": value}


@router.post("/thought")
async def record_thought(
    agent_id: str,
    thought: str,
    status: str = "Success",
    current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user),
):
    """Trigger an agent 'thought' event"""
    sync_service.record_agent_thought(agent_id, thought, status)
    return {"status": "recorded"}
