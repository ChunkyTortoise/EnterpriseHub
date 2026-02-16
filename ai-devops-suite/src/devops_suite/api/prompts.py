"""Prompt CRUD with versioning API."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


class PromptCreate(BaseModel):
    name: str
    description: str = ""
    content: str
    model_hint: str | None = None
    tags: list[str] = Field(default_factory=list)


class PromptOut(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    latest_version: int = 1


class PromptVersionOut(BaseModel):
    version: int
    content: str
    variables: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    changelog: str | None = None


class DeployRequest(BaseModel):
    tag: str = "production"


_prompts: dict[UUID, dict] = {}


@router.post("", response_model=PromptOut)
async def create_prompt(prompt: PromptCreate) -> PromptOut:
    out = PromptOut(name=prompt.name, description=prompt.description)
    _prompts[out.id] = {
        "info": out,
        "versions": [
            PromptVersionOut(version=1, content=prompt.content, tags=prompt.tags)
        ],
    }
    return out


@router.get("", response_model=list[PromptOut])
async def list_prompts() -> list[PromptOut]:
    return [p["info"] for p in _prompts.values()]


@router.get("/{prompt_id}", response_model=PromptOut)
async def get_prompt(prompt_id: UUID) -> PromptOut:
    if prompt_id not in _prompts:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return _prompts[prompt_id]["info"]


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionOut])
async def list_versions(prompt_id: UUID) -> list[PromptVersionOut]:
    if prompt_id not in _prompts:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return _prompts[prompt_id]["versions"]


@router.post("/{prompt_id}/deploy")
async def deploy_version(prompt_id: UUID, req: DeployRequest) -> dict:
    if prompt_id not in _prompts:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"deployed": True, "tag": req.tag, "prompt_id": str(prompt_id)}
