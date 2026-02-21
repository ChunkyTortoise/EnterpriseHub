"""Authentication and authorization schemas."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    BILLING = "billing"


class APIKeySchema(BaseModel):
    """API key configuration stored in database."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    key_prefix: str = Field(
        ..., min_length=8, max_length=8, description="First 8 chars for identification"
    )
    hashed_key: str
    name: str = Field(..., min_length=1, max_length=128)
    scopes: list[str] = Field(default_factory=lambda: ["read", "write"])
    rate_limit: int = Field(default=100, ge=1, description="Requests per minute")
    is_active: bool = True


class JWTPayload(BaseModel):
    """JWT token payload for API authentication."""

    sub: str  # user_id
    tenant_id: str
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    exp: int


class JWTClaims(BaseModel):
    """Extended JWT claims with permissions."""

    sub: str
    tenant_id: str
    permissions: list[Permission] = Field(default_factory=lambda: [Permission.READ])
    exp: int
    iat: int | None = None
    iss: str | None = None
