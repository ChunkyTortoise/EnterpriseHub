import pytest
pytestmark = pytest.mark.integration

"""Tests for CRM Protocol ABC and CRMContact model."""

from __future__ import annotations

from typing import Any

import pytest

from ghl_real_estate_ai.services.crm.protocol import CRMContact, CRMProtocol

@pytest.mark.unit


class TestCRMContactDefaults:
    """Test CRMContact creation with default values."""

    def test_defaults(self):
        contact = CRMContact()
        assert contact.id is None
        assert contact.first_name == ""
        assert contact.last_name == ""
        assert contact.email is None
        assert contact.phone is None
        assert contact.source == ""
        assert contact.tags == []
        assert contact.metadata == {}


class TestCRMContactFull:
    """Test CRMContact with all fields populated."""

    def test_all_fields(self):
        contact = CRMContact(
            id="c-123",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+15551234567",
            source="website",
            tags=["Hot-Lead", "buyer"],
            metadata={"budget": 500000, "pre_approved": True},
        )
        assert contact.id == "c-123"
        assert contact.first_name == "Jane"
        assert contact.last_name == "Doe"
        assert contact.email == "jane@example.com"
        assert contact.phone == "+15551234567"
        assert contact.source == "website"
        assert contact.tags == ["Hot-Lead", "buyer"]
        assert contact.metadata["budget"] == 500000
        assert contact.metadata["pre_approved"] is True


class TestCRMContactSerialization:
    """Test CRMContact serialization and deserialization."""

    def test_round_trip(self):
        original = CRMContact(
            id="c-456",
            first_name="John",
            last_name="Smith",
            email="john@example.com",
            phone="+15559876543",
            source="referral",
            tags=["Warm-Lead"],
            metadata={"notes": "Interested in 3BR"},
        )
        data = original.model_dump()
        restored = CRMContact.model_validate(data)
        assert restored == original

    def test_json_round_trip(self):
        original = CRMContact(
            id="c-789",
            first_name="Alice",
            last_name="Wonderland",
            tags=["seller"],
        )
        json_str = original.model_dump_json()
        restored = CRMContact.model_validate_json(json_str)
        assert restored == original


class TestCRMProtocolAbstract:
    """Test that CRMProtocol cannot be instantiated directly."""

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError, match="abstract method"):
            CRMProtocol()  # type: ignore[abstract]


class TestCRMProtocolMockAdapter:
    """Test a mock adapter implementing CRMProtocol works correctly."""

    class _InMemoryAdapter(CRMProtocol):
        """Minimal in-memory CRM for testing."""

        def __init__(self) -> None:
            self._store: dict[str, CRMContact] = {}
            self._counter = 0

        async def create_contact(self, contact: CRMContact) -> CRMContact:
            self._counter += 1
            contact = contact.model_copy(update={"id": f"mem-{self._counter}"})
            self._store[contact.id] = contact  # type: ignore[index]
            return contact

        async def update_contact(
            self, contact_id: str, updates: dict[str, Any]
        ) -> CRMContact:
            existing = self._store[contact_id]
            updated = existing.model_copy(update=updates)
            self._store[contact_id] = updated
            return updated

        async def get_contact(self, contact_id: str) -> CRMContact | None:
            return self._store.get(contact_id)

        async def search_contacts(
            self, query: str, limit: int = 10
        ) -> list[CRMContact]:
            results = [
                c
                for c in self._store.values()
                if query.lower() in c.first_name.lower()
                or query.lower() in c.last_name.lower()
            ]
            return results[:limit]

        async def sync_lead(
            self, contact: CRMContact, score: int, temperature: str
        ) -> bool:
            if contact.id and contact.id in self._store:
                existing = self._store[contact.id]
                updated_tags = [*existing.tags, temperature]
                self._store[contact.id] = existing.model_copy(
                    update={"tags": updated_tags}
                )
                return True
            return False

    @pytest.fixture()
    def adapter(self) -> _InMemoryAdapter:
        return self._InMemoryAdapter()

    @pytest.mark.asyncio()
    async def test_create_and_get(self, adapter: _InMemoryAdapter):
        contact = CRMContact(first_name="Bob", last_name="Builder")
        created = await adapter.create_contact(contact)
        assert created.id == "mem-1"

        fetched = await adapter.get_contact("mem-1")
        assert fetched is not None
        assert fetched.first_name == "Bob"

    @pytest.mark.asyncio()
    async def test_update_contact(self, adapter: _InMemoryAdapter):
        contact = CRMContact(first_name="Old", last_name="Name")
        created = await adapter.create_contact(contact)
        updated = await adapter.update_contact(
            created.id, {"first_name": "New"}  # type: ignore[arg-type]
        )
        assert updated.first_name == "New"

    @pytest.mark.asyncio()
    async def test_search_contacts(self, adapter: _InMemoryAdapter):
        await adapter.create_contact(
            CRMContact(first_name="Alice", last_name="A")
        )
        await adapter.create_contact(
            CRMContact(first_name="Bob", last_name="B")
        )
        results = await adapter.search_contacts("alice")
        assert len(results) == 1
        assert results[0].first_name == "Alice"

    @pytest.mark.asyncio()
    async def test_sync_lead_applies_tag(self, adapter: _InMemoryAdapter):
        created = await adapter.create_contact(
            CRMContact(first_name="Lead", last_name="Test")
        )
        success = await adapter.sync_lead(created, score=85, temperature="Hot-Lead")
        assert success is True
        fetched = await adapter.get_contact(created.id)  # type: ignore[arg-type]
        assert fetched is not None
        assert "Hot-Lead" in fetched.tags

    @pytest.mark.asyncio()
    async def test_sync_lead_missing_contact(self, adapter: _InMemoryAdapter):
        ghost = CRMContact(id="nonexistent", first_name="Ghost")
        success = await adapter.sync_lead(ghost, score=10, temperature="Cold-Lead")
        assert success is False