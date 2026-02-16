"""Authentication and authorization schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Permission(str, Enum):
    """Available permissions."""

    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"
    BILLING = "BILLING"


class JWTClaims(BaseModel):
    """Decoded JWT token claims."""

    sub: str
    tenant_id: str
    permissions: list[Permission] = Field(default_factory=list)
    exp: datetime
    iat: datetime | None = None

    @field_validator("exp")
    @classmethod
    def _exp_must_be_future(cls, v: datetime) -> datetime:
        if v <= datetime.utcnow():
            raise ValueError("Token expiration must be in the future")
        return v


class APIKeyConfig(BaseModel):
    """API key configuration."""

    key_id: str
    tenant_id: str
    name: str
    permissions: list[Permission] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    is_active: bool = True
