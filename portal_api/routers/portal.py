from fastapi import APIRouter, Depends

from portal_api.dependencies import (
    Services,
    apply_payload_tenant_context,
    get_idempotency_key,
    get_services,
    require_demo_api_key,
    resolve_tenant_context,
)
from portal_api.models import ApiErrorResponse, DeckResponse, Interaction, SwipeResponse, TenantContext

router = APIRouter(prefix="/portal", tags=["portal"])


@router.get("/deck", response_model=DeckResponse)
async def get_smart_deck(
    contact_id: str,
    tenant_context: TenantContext = Depends(resolve_tenant_context),
    services: Services = Depends(get_services),
) -> DeckResponse:
    deck = services.inventory.get_smart_deck(contact_id=contact_id, tenant_id=tenant_context.tenant_id)
    return DeckResponse(deck=deck)


@router.post(
    "/swipe",
    response_model=SwipeResponse,
    dependencies=[Depends(require_demo_api_key), Depends(get_idempotency_key)],
    responses={
        401: {
            "model": ApiErrorResponse,
            "description": "API key missing or invalid",
        },
        409: {
            "model": ApiErrorResponse,
            "description": "Idempotency key conflict",
        },
        500: {
            "model": ApiErrorResponse,
            "description": "Authentication is misconfigured",
        },
    },
)
async def log_swipe(
    interaction: Interaction,
    tenant_context: TenantContext = Depends(resolve_tenant_context),
    services: Services = Depends(get_services),
) -> SwipeResponse:
    effective_tenant = apply_payload_tenant_context(tenant_context, interaction.location_id)
    services.inventory.log_interaction(
        tenant_id=effective_tenant.tenant_id,
        lead_id=interaction.contact_id,
        property_id=interaction.property_id,
        action=interaction.action,
        feedback=interaction.feedback,
        time_on_card=interaction.time_on_card,
    )

    high_intent = False
    trigger_sms = False
    adjustments: list[str] = []

    if interaction.action == "like":
        high_intent = True

        prop_data = services.inventory.get_property(interaction.property_id)
        lead_data = services.inventory.get_lead(interaction.contact_id)

        services.ghl.add_tag_to_contact(
            interaction.contact_id,
            "Property Liked",
            tenant_id=effective_tenant.tenant_id,
        )
        address = prop_data["address"] if prop_data else f"ID: {interaction.property_id}"
        services.ghl.update_contact_field(
            interaction.contact_id,
            services.ghl.field_property_interest,
            address,
            tenant_id=effective_tenant.tenant_id,
        )

        if lead_data and lead_data.get("phone"):
            services.trigger_outbound_call(
                contact_phone=lead_data["phone"],
                contact_name=lead_data["name"],
                property_address=address,
                contact_id=interaction.contact_id,
            )

        match_data = {
            "score": 95,
            "property_id": interaction.property_id,
            "address": address,
            "price": prop_data["price"] if prop_data else "Contact for Price",
            "beds": prop_data["beds"] if prop_data else 0,
            "baths": prop_data["baths"] if prop_data else 0,
            "buyer_name": lead_data["name"] if lead_data else "Valued Client",
        }
        trigger_sms = services.ghl.trigger_match_webhook(
            interaction.contact_id,
            match_data,
            tenant_id=effective_tenant.tenant_id,
        )

    return SwipeResponse(
        status="success",
        high_intent=high_intent,
        trigger_sms=trigger_sms,
        adjustments=adjustments,
    )
