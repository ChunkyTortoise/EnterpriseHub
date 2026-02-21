"""CRM Protocol ABC -- vendor-agnostic interface for CRM adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class CRMContact(BaseModel):
    """Vendor-agnostic contact representation."""

    id: str | None = None
    first_name: str = ""
    last_name: str = ""
    email: str | None = None
    phone: str | None = None
    source: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CRMProtocol(ABC):
    """Abstract base class for CRM adapters."""

    @abstractmethod
    async def create_contact(self, contact: CRMContact) -> CRMContact:
        """Create a new contact in the CRM."""

    @abstractmethod
    async def update_contact(self, contact_id: str, updates: dict[str, Any]) -> CRMContact:
        """Update an existing contact."""

    @abstractmethod
    async def get_contact(self, contact_id: str) -> CRMContact | None:
        """Retrieve a contact by ID."""

    @abstractmethod
    async def search_contacts(self, query: str, limit: int = 10) -> list[CRMContact]:
        """Search contacts by query string."""

    @abstractmethod
    async def sync_lead(self, contact: CRMContact, score: int, temperature: str) -> bool:
        """Sync lead data with temperature scoring."""
