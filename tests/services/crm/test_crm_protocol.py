"""Tests for CRMContact model and CRMProtocol ABC."""

from __future__ import annotations

from typing import Any

import pytest

from ghl_real_estate_ai.services.crm import CRMContact, CRMProtocol


# ---------------------------------------------------------------------------
# CRMContact model tests
# ---------------------------------------------------------------------------


class TestCRMContactDefaults:
    """CRMContact should have sensible defaults for every field."""

    def test_creation_with_defaults(self):
        contact = CRMContact()
        assert contact.id is None
        assert contact.first_name == ""
        assert contact.last_name == ""
        assert contact.email is None
        assert contact.phone is None
        assert contact.source == ""
        assert contact.tags == []
        assert contact.metadata == {}

    def test_tags_default_to_empty_list(self):
        """Each instance should get its own list (no mutable-default sharing)."""
        c1 = CRMContact()
        c2 = CRMContact()
        c1.tags.append("VIP")
        assert c2.tags == []

    def test_metadata_default_to_empty_dict(self):
        """Each instance should get its own dict."""
        c1 = CRMContact()
        c2 = CRMContact()
        c1.metadata["key"] = "value"
        assert c2.metadata == {}


class TestCRMContactPopulated:
    """CRMContact with all fields explicitly set."""

    def test_all_fields_populated(self):
        contact = CRMContact(
            id="abc-123",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+19095551234",
            source="website",
            tags=["Hot-Lead", "VIP"],
            metadata={"campaign": "spring2026"},
        )
        assert contact.id == "abc-123"
        assert contact.first_name == "Jane"
        assert contact.last_name == "Doe"
        assert contact.email == "jane@example.com"
        assert contact.phone == "+19095551234"
        assert contact.source == "website"
        assert contact.tags == ["Hot-Lead", "VIP"]
        assert contact.metadata == {"campaign": "spring2026"}

    def test_optional_fields_can_be_none(self):
        contact = CRMContact(email=None, phone=None)
        assert contact.email is None
        assert contact.phone is None


class TestCRMContactSerialization:
    """JSON round-trip for CRMContact."""

    def test_json_round_trip(self):
        original = CRMContact(
            id="rt-1",
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="+15551234567",
            source="referral",
            tags=["Warm-Lead"],
            metadata={"note": "follow-up"},
        )
        json_str = original.model_dump_json()
        restored = CRMContact.model_validate_json(json_str)
        assert restored == original

    def test_model_dump_keys(self):
        contact = CRMContact(first_name="Bob")
        data = contact.model_dump()
        expected_keys = {
            "id", "first_name", "last_name", "email",
            "phone", "source", "tags", "metadata",
        }
        assert set(data.keys()) == expected_keys


# ---------------------------------------------------------------------------
# CRMProtocol ABC tests
# ---------------------------------------------------------------------------


class TestCRMProtocolABC:
    """CRMProtocol cannot be instantiated directly and enforces interface."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            CRMProtocol()  # type: ignore[abstract]

    def test_partial_implementation_raises(self):
        """A subclass that only implements some methods cannot be instantiated."""

        class PartialAdapter(CRMProtocol):
            async def create_contact(self, contact: CRMContact) -> CRMContact:
                return contact

        with pytest.raises(TypeError):
            PartialAdapter()  # type: ignore[abstract]

    def test_full_implementation_can_be_instantiated(self):
        """A subclass implementing all abstract methods is valid."""

        class StubAdapter(CRMProtocol):
            async def create_contact(self, contact: CRMContact) -> CRMContact:
                return contact

            async def update_contact(
                self, contact_id: str, updates: dict[str, Any]
            ) -> CRMContact:
                return CRMContact(id=contact_id)

            async def get_contact(self, contact_id: str) -> CRMContact | None:
                return None

            async def search_contacts(
                self, query: str, limit: int = 10
            ) -> list[CRMContact]:
                return []

            async def sync_lead(
                self, contact: CRMContact, score: int, temperature: str
            ) -> bool:
                return True

        adapter = StubAdapter()
        assert isinstance(adapter, CRMProtocol)
