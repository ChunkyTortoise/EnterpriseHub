"""CRUD API for voice agent personas."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentPersonaCreate(BaseModel):
    name: str
    bot_type: str  # "lead" | "buyer" | "seller"
    voice_id: str | None = None
    language: str = "en"
    system_prompt_override: str | None = None
    greeting_message: str | None = None
    transfer_number: str | None = None
    settings: dict = Field(default_factory=dict)


class AgentPersonaResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    bot_type: str
    voice_id: str | None
    language: str
    system_prompt_override: str | None
    greeting_message: str | None
    transfer_number: str | None
    settings: dict
    is_active: bool
    created_at: str | None


class AgentPersonaUpdate(BaseModel):
    name: str | None = None
    voice_id: str | None = None
    language: str | None = None
    system_prompt_override: str | None = None
    greeting_message: str | None = None
    transfer_number: str | None = None
    settings: dict | None = None
    is_active: bool | None = None


@router.post("", response_model=AgentPersonaResponse, status_code=201)
async def create_agent(body: AgentPersonaCreate, request: Request) -> dict[str, Any]:
    """Create a new voice agent persona."""
    if body.bot_type not in ("lead", "buyer", "seller"):
        raise HTTPException(status_code=400, detail="bot_type must be lead, buyer, or seller")

    persona_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())  # From auth in production

    return {
        "id": persona_id,
        "tenant_id": tenant_id,
        "name": body.name,
        "bot_type": body.bot_type,
        "voice_id": body.voice_id,
        "language": body.language,
        "system_prompt_override": body.system_prompt_override,
        "greeting_message": body.greeting_message,
        "transfer_number": body.transfer_number,
        "settings": body.settings,
        "is_active": True,
        "created_at": None,
    }


@router.get("", response_model=list[AgentPersonaResponse])
async def list_agents(request: Request) -> list[dict[str, Any]]:
    """List all agent personas for the tenant."""
    return []


@router.put("/{agent_id}", response_model=AgentPersonaResponse)
async def update_agent(agent_id: str, body: AgentPersonaUpdate, request: Request) -> dict[str, Any]:
    """Update an agent persona."""
    raise HTTPException(status_code=404, detail="Agent not found")


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, request: Request) -> None:
    """Delete an agent persona."""
    raise HTTPException(status_code=404, detail="Agent not found")
