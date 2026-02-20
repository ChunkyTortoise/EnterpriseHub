"""Teams API — invite and manage team members."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


class TeamInviteRequest(BaseModel):
    email: str
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class TeamMemberResponse(BaseModel):
    id: str
    email: str
    role: str
    accepted: bool = False
    created_at: str = ""


class TeamListResponse(BaseModel):
    members: list[TeamMemberResponse]
    total: int


@router.post("/invite", response_model=TeamMemberResponse, status_code=201)
async def invite_member(request: Request, body: TeamInviteRequest):
    """Invite a team member to the tenant."""
    tenant_id = request.state.tenant_id
    member_id = str(uuid.uuid4())

    audit_logger = getattr(request.app.state, "audit_logger", None)
    if audit_logger:
        await audit_logger.log(
            tenant_id=tenant_id,
            action="team.invite",
            resource_type="team_member",
            resource_id=member_id,
            metadata={"email": body.email, "role": body.role},
        )

    return TeamMemberResponse(
        id=member_id,
        email=body.email,
        role=body.role,
    )


@router.get("/members", response_model=TeamListResponse)
async def list_members(request: Request):
    """List all team members."""
    return TeamListResponse(members=[], total=0)


@router.delete("/members/{member_id}", status_code=204)
async def remove_member(request: Request, member_id: str):
    """Remove a team member."""
    return None
