from ghl_real_estate_ai.api.routes.webhook import (
    _compute_mode_flags,
    _normalize_tags,
    _select_primary_mode,
    _tag_present,
)
from ghl_real_estate_ai.api.schemas.ghl import GHLWebhookEvent, MessageType


def test_native_flat_payload_propagates_top_level_tags_to_contact() -> None:
    payload = {
        "type": "InboundMessage",
        "locationId": "loc_123",
        "contactId": "contact_123",
        "body": "Hi, I want to sell",
        "messageType": "SMS",
        "tags": ["needs qualifying"],
    }

    event = GHLWebhookEvent(**payload)

    assert event.message.type == MessageType.SMS
    assert event.contact is not None
    assert event.contact.tags == ["needs qualifying"]


def test_normalize_tags_is_case_and_whitespace_insensitive() -> None:
    raw_tags = [" Needs Qualifying ", "seller-lead", "SELLER-LEAD", "", None]
    tags_lower = _normalize_tags(raw_tags)  # type: ignore[arg-type]
    assert tags_lower == {"needs qualifying", "seller-lead"}
    assert _tag_present("Needs Qualifying", tags_lower)
    assert _tag_present("needs qualifying", tags_lower)


def test_mode_priority_prefers_seller_over_other_modes() -> None:
    tags_lower = _normalize_tags(["needs qualifying", "buyer-lead"])
    mode_flags = _compute_mode_flags(
        tags_lower,
        should_deactivate=False,
        seller_mode_enabled=True,
        buyer_mode_enabled=True,
        lead_mode_enabled=True,
        buyer_activation_tag="Buyer-Lead",
        lead_activation_tag="Needs Qualifying",
    )

    assert mode_flags["seller"] is True
    assert mode_flags["buyer"] is True
    assert mode_flags["lead"] is True
    assert _select_primary_mode(mode_flags) == "seller"


def test_mode_flags_support_seller_lead_tag() -> None:
    tags_lower = _normalize_tags(["Seller-Lead"])
    mode_flags = _compute_mode_flags(
        tags_lower,
        should_deactivate=False,
        seller_mode_enabled=True,
        buyer_mode_enabled=True,
        lead_mode_enabled=True,
        buyer_activation_tag="Buyer-Lead",
        lead_activation_tag="Needs Qualifying",
    )
    assert mode_flags["seller"] is True
    assert _select_primary_mode(mode_flags) == "seller"
