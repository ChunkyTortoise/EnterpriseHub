"""
Seller Bot Webhook Handlers

Handles GHL webhook events for the Seller Bot:
- ContactCreate with seller tags (seller inquiry)
- OpportunityCreate (listing created)
- ConversationMessageCreate (seller responses)
"""

import logging
from typing import Any, Callable, Dict, Optional

from ghl_real_estate_ai.ghl_utils.ghl_api_client import GHLAPIClient
from ghl_real_estate_ai.services.cache_service import CacheService

logger = logging.getLogger(__name__)

# Handler registry
_handlers: Dict[str, Callable] = {}


def register_handler(event_type: str):
    """Decorator to register a handler"""

    def decorator(func: Callable):
        _handlers[event_type] = func
        return func

    return decorator


def get_handler(event_type: str) -> Optional[Callable]:
    """Get handler for event type"""
    return _handlers.get(event_type)


@register_handler("contact.create")
async def handle_seller_inquiry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ContactCreate with seller tags.

    Trigger CMA generation flow:
    1. Extract property address
    2. Start Q0-Q4 qualification
    3. Generate CMA if address provided
    4. Update GHL with estimated value
    """
    try:
        data = payload.get("data", payload)

        contact_id = data.get("id")
        email = data.get("email")
        name = data.get("name", "").strip()
        tags = data.get("tags", [])

        # Verify seller tag
        seller_tags = ["seller", "listing_inquiry", "home_value", "cma_request"]
        has_seller_tag = any(tag in tags for tag in seller_tags)

        if not has_seller_tag:
            return {
                "success": True,
                "message": "Not a seller inquiry, skipping",
                "tags": tags,
            }

        logger.info(f"Seller inquiry: {contact_id} - {name}")

        # Extract address from custom fields or message
        custom_fields = data.get("customFields", {})
        address = _extract_address(data)

        # Initialize seller state
        seller_state = {
            "contact_id": contact_id,
            "name": name,
            "email": email,
            "address": address,
            "qualification_stage": "Q0",  # Initial inquiry
            "cma_requested": bool(address),
            "cma_generated": False,
        }

        # Store seller state
        await _store_seller_state(contact_id, seller_state)

        # Start qualification if address provided
        if address:
            cma_result = await _generate_cma(address, contact_id)
            seller_state["cma_generated"] = cma_result.get("success", False)
            seller_state["estimated_value"] = cma_result.get("estimated_value")

            # Update GHL with CMA results
            await _update_ghl_seller_fields(contact_id, seller_state)

        # Send initial greeting
        await _send_seller_greeting(contact_id, seller_state)

        # Emit event
        await _emit_seller_event("seller.inquiry.received", seller_state)

        return {
            "success": True,
            "contact_id": contact_id,
            "seller_state": seller_state,
            "action": "Seller inquiry processed",
        }

    except Exception as e:
        logger.error(f"Failed to handle seller inquiry: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


@register_handler("opportunity.create")
async def handle_listing_created(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle OpportunityCreate in listing pipeline.

    Start seller qualification:
    1. Extract opportunity data
    2. Initialize seller conversation state
    3. Send initial greeting
    """
    try:
        data = payload.get("data", payload)

        opportunity_id = data.get("id")
        contact_id = data.get("contactId") or data.get("contact_id")
        pipeline_id = data.get("pipelineId") or data.get("pipeline_id")
        stage_id = data.get("stageId") or data.get("stage_id")

        # Check if this is seller pipeline
        seller_pipeline_ids = _get_seller_pipeline_ids()
        if pipeline_id not in seller_pipeline_ids:
            return {
                "success": True,
                "message": "Not a seller pipeline, skipping",
                "pipeline_id": pipeline_id,
            }

        logger.info(f"Listing opportunity created: {opportunity_id} for contact {contact_id}")

        # Get contact details
        contact = await _get_contact_details(contact_id)

        # Initialize seller state for listing
        seller_state = {
            "contact_id": contact_id,
            "opportunity_id": opportunity_id,
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
            "name": contact.get("name", ""),
            "email": contact.get("email"),
            "qualification_stage": "Q0",
            "listing_created_at": data.get("createdAt"),
        }

        await _store_seller_state(contact_id, seller_state)

        # Send listing confirmation
        await _send_listing_confirmation(contact_id, seller_state)

        # Update GHL
        await _update_ghl_seller_fields(
            contact_id,
            {
                "seller_qualification_stage": "Q0",
            },
        )

        # Emit event
        await _emit_seller_event("seller.listing.created", seller_state)

        return {
            "success": True,
            "contact_id": contact_id,
            "opportunity_id": opportunity_id,
            "seller_state": seller_state,
        }

    except Exception as e:
        logger.error(f"Failed to handle listing creation: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


@register_handler("conversation.message.created")
async def handle_seller_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ConversationMessageCreate from sellers.

    Continue Q0-Q4 qualification flow.
    """
    try:
        data = payload.get("data", payload)

        contact_id = data.get("contactId") or data.get("contact_id")
        message = data.get("message") or data.get("body", "")
        direction = data.get("direction", "inbound")

        if direction != "inbound":
            return {"success": True, "message": "Outbound message, no action needed"}

        logger.info(f"Seller response from {contact_id}: {message[:50]}...")

        # Get current seller state
        seller_state = await _get_seller_state(contact_id)
        if not seller_state:
            logger.warning(f"No seller state found for {contact_id}, initializing")
            seller_state = await _initialize_seller_from_contact(contact_id)

        current_stage = seller_state.get("qualification_stage", "Q0")

        # Process message based on qualification stage
        next_stage, response_message = await _process_qualification_message(
            contact_id, current_stage, message, seller_state
        )

        # Update seller state
        seller_state["qualification_stage"] = next_stage
        seller_state["last_message"] = message
        seller_state["last_response"] = response_message
        await _store_seller_state(contact_id, seller_state)

        # Update GHL custom fields
        await _update_ghl_seller_fields(
            contact_id,
            {
                "seller_qualification_stage": next_stage,
            },
        )

        # Send response
        await _send_seller_message(contact_id, response_message)

        # Check for CMA trigger
        if next_stage == "Q2" and not seller_state.get("cma_generated"):
            if seller_state.get("address"):
                cma_result = await _generate_cma(seller_state["address"], contact_id)
                if cma_result.get("success"):
                    seller_state["cma_generated"] = True
                    seller_state["estimated_value"] = cma_result.get("estimated_value")
                    await _store_seller_state(contact_id, seller_state)
                    await _update_ghl_seller_fields(contact_id, seller_state)

        # Emit event
        await _emit_seller_event(
            "seller.response.processed",
            {
                "contact_id": contact_id,
                "stage": next_stage,
                "message_preview": message[:100],
            },
        )

        return {
            "success": True,
            "contact_id": contact_id,
            "stage": next_stage,
            "response_sent": response_message,
        }

    except Exception as e:
        logger.error(f"Failed to handle seller response: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


# Helper functions


def _extract_address(data: Dict[str, Any]) -> Optional[str]:
    """Extract property address from contact data"""
    # Check custom fields
    custom_fields = data.get("customFields", {})

    address_fields = ["property_address", "home_address", "address", "listing_address"]
    for field in address_fields:
        if field in custom_fields and custom_fields[field]:
            return custom_fields[field]

    # Check message/body
    message = data.get("message", "")
    if message:
        # Simple address extraction (can be enhanced with NLP)
        import re

        # Look for address patterns (street numbers, etc.)
        address_pattern = (
            r"\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Court|Ct)"
        )
        match = re.search(address_pattern, message, re.IGNORECASE)
        if match:
            return match.group(0)

    return None


async def _generate_cma(address: str, contact_id: str) -> Dict[str, Any]:
    """Generate Comparative Market Analysis"""
    try:
        from ...ghl_real_estate_ai.services.cma_service import CMAService

        cma_service = CMAService()
        result = await cma_service.generate_cma(address)

        return {
            "success": True,
            "estimated_value": result.get("estimated_value"),
            "price_range_low": result.get("price_range_low"),
            "price_range_high": result.get("price_range_high"),
            "confidence": result.get("confidence"),
            "comparables": result.get("comparables", []),
        }

    except Exception as e:
        logger.error(f"CMA generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def _send_seller_greeting(contact_id: str, seller_state: Dict[str, Any]):
    """Send initial greeting to seller"""
    try:
        client = GHLAPIClient()

        name = seller_state.get("name", "").split()[0]  # First name
        address = seller_state.get("address")

        if address:
            message = f"Hi {name}! Thanks for your interest in selling at {address}. I'm here to help you understand your home's value and guide you through the selling process. Can you tell me a bit about your timeline for selling?"
        else:
            message = f"Hi {name}! Thanks for reaching out about selling your home. I'm here to help you understand your home's value and guide you through the process. What's the address of the property you're considering selling?"

        await client.send_message(contact_id, message, "SMS")

    except Exception as e:
        logger.error(f"Failed to send greeting: {e}")


async def _send_listing_confirmation(contact_id: str, seller_state: Dict[str, Any]):
    """Send listing confirmation message"""
    try:
        client = GHLAPIClient()

        name = seller_state.get("name", "").split()[0]
        message = f"Hi {name}! I've created a listing opportunity for you in our system. Let's work together to get your home sold quickly and at the best price. I'd like to ask you a few questions to understand your goals better."

        await client.send_message(contact_id, message, "SMS")

    except Exception as e:
        logger.error(f"Failed to send listing confirmation: {e}")


async def _store_seller_state(contact_id: str, state: Dict[str, Any]):
    """Store seller state in cache"""
    try:
        cache = CacheService()
        await cache.set(
            f"seller:state:{contact_id}",
            state,
            ttl=2592000,  # 30 days
        )
    except Exception as e:
        logger.error(f"Failed to store seller state: {e}")


async def _get_seller_state(contact_id: str) -> Optional[Dict[str, Any]]:
    """Get seller state from cache"""
    try:
        cache = CacheService()
        return await cache.get(f"seller:state:{contact_id}")
    except Exception as e:
        logger.error(f"Failed to get seller state: {e}")
        return None


async def _get_contact_details(contact_id: str) -> Dict[str, Any]:
    """Get contact details from GHL"""
    try:
        client = GHLAPIClient()
        result = await client.get_contact(contact_id)
        if result.get("success"):
            return result.get("data", {})
        return {}
    except Exception as e:
        logger.error(f"Failed to get contact details: {e}")
        return {}


async def _initialize_seller_from_contact(contact_id: str) -> Dict[str, Any]:
    """Initialize seller state from contact data"""
    contact = await _get_contact_details(contact_id)

    state = {
        "contact_id": contact_id,
        "name": contact.get("name", ""),
        "email": contact.get("email"),
        "qualification_stage": "Q0",
        "initialized_at": __import__("datetime").datetime.now().isoformat(),
    }

    await _store_seller_state(contact_id, state)
    return state


async def _process_qualification_message(
    contact_id: str, current_stage: str, message: str, seller_state: Dict[str, Any]
) -> tuple:
    """
    Process qualification message and determine next stage.

    Q0: Initial inquiry
    Q1: Timeline established
    Q2: Property details collected (address, condition)
    Q3: Motivation understood
    Q4: Pricing expectations discussed
    QUALIFIED: Ready for listing appointment
    """
    from ...ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

    bot = JorgeSellerBot()

    # Use seller bot to process message
    result = await bot.process_seller_message(
        contact_id=contact_id,
        message=message,
        stage=current_stage,
        context=seller_state,
    )

    next_stage = result.get("next_stage", current_stage)
    response = result.get("response", "Thank you for your message. Let me help you with that.")

    return next_stage, response


async def _send_seller_message(contact_id: str, message: str):
    """Send message to seller via GHL"""
    try:
        client = GHLAPIClient()
        await client.send_message(contact_id, message, "SMS")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")


async def _update_ghl_seller_fields(contact_id: str, seller_data: Dict[str, Any]):
    """Update GHL custom fields for seller"""
    try:
        client = GHLAPIClient()

        custom_fields = {}

        if "estimated_value" in seller_data:
            custom_fields["estimated_property_value"] = seller_data["estimated_value"]
        if "cma_generated" in seller_data:
            custom_fields["cma_generated"] = seller_data["cma_generated"]
        if "qualification_stage" in seller_data:
            custom_fields["seller_qualification_stage"] = seller_data["qualification_stage"]

        if custom_fields:
            await client.update_contact(contact_id, {"customFields": custom_fields})

    except Exception as e:
        logger.error(f"Failed to update GHL fields: {e}")


def _get_seller_pipeline_ids() -> list:
    """Get list of seller pipeline IDs from config"""
    import os

    ids = os.getenv("GHL_SELLER_PIPELINE_IDS", "").split(",")
    return [id.strip() for id in ids if id.strip()]


async def _emit_seller_event(event_type: str, data: Dict[str, Any]):
    """Emit event for dashboard"""
    try:
        from ...ghl_real_estate_ai.services.event_broker import event_broker

        await event_broker.publish(
            {
                "type": event_type,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
                "data": data,
            }
        )
    except Exception as e:
        logger.error(f"Failed to emit event: {e}")
