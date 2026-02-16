"""API contracts — shared request/response envelopes."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """A single validation or processing error."""

    code: str
    message: str
    field: str | None = None


class APIError(BaseModel):
    """Standard API error response."""

    error: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    status_code: int = 500


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    total: int
    limit: int
    offset: int = 0

    @property
    def has_more(self) -> bool:
        return self.offset + self.limit < self.total
