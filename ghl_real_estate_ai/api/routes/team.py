"""
Team API Routes for GHL Real Estate AI.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.team_service import TeamManager

logger = get_logger(__name__)
router = APIRouter(prefix="/team", tags=["team"])


class AgentCreate(BaseModel):
    id: str
    name: str
    email: str
    role: str = "agent"
    specialties: List[str] = []


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


@router.post("/{location_id}/agents")
async def add_agent(location_id: str, agent: AgentCreate):
    """Add a new agent to the team."""
    manager = TeamManager(location_id)
    manager.add_agent(
        agent_id=agent.id,
        name=agent.name,
        email=agent.email,
        role=agent.role,
        specialties=agent.specialties,
    )
    return {"message": "Agent added successfully", "agent_id": agent.id}


@router.get("/{location_id}/agents")
async def list_agents(location_id: str, status: str = "active"):
    """List all agents in a location."""
    manager = TeamManager(location_id)
    return manager.list_agents(status=status)


@router.get("/{location_id}/leaderboard")
async def get_leaderboard(location_id: str):
    """Get the team leaderboard."""
    manager = TeamManager(location_id)
    return manager.get_leaderboard()


@router.post("/{location_id}/assign")
async def assign_lead(location_id: str, contact_id: str):
    """Assign a lead to an agent."""
    manager = TeamManager(location_id)
    agent_id = manager.assign_lead(contact_id)
    if not agent_id:
        raise HTTPException(
            status_code=404, detail="No agents available for assignment"
        )
    return {"contact_id": contact_id, "assigned_to": agent_id}


@router.post("/{location_id}/agents/{agent_id}/performance")
async def update_performance(
    location_id: str,
    agent_id: str,
    conversion: bool = False,
    rating: Optional[float] = None,
):
    """Update agent performance metrics."""
    manager = TeamManager(location_id)
    manager.update_agent_performance(agent_id, conversion=conversion, rating=rating)
    return {"message": "Performance updated"}
