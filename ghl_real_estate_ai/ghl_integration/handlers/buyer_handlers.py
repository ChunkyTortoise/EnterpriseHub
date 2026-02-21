"""
Buyer Bot Webhook Handlers

Handles GHL webhook events for the Buyer Bot:
- ContactCreate with buyer tags (buyer inquiry)
- ConversationMessageCreate (buyer responses)
- PipelineStageChange (pipeline updates)
"""

import logging
from typing import Any, Callable, Dict, List, Optional

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
async def handle_buyer_inquiry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ContactCreate with buyer tags.

    Start buyer qualification:
    1. Initialize buyer preferences
    2. Start Q0-Q4 qualification
    3. Extract budget/preferences from message
    """
    try:
        data = payload.get("data", payload)

        contact_id = data.get("id")
        email = data.get("email")
        name = data.get("name", "").strip()
        tags = data.get("tags", [])

        # Verify buyer tag
        buyer_tags = ["buyer", "home_buyer", "buyer_lead", "first_time_buyer", "investor"]
        has_buyer_tag = any(tag in tags for tag in buyer_tags)

        if not has_buyer_tag:
            return {
                "success": True,
                "message": "Not a buyer inquiry, skipping",
                "tags": tags,
            }

        logger.info(f"Buyer inquiry: {contact_id} - {name}")

        # Extract initial preferences from custom fields
        custom_fields = data.get("customFields", {})
        initial_preferences = _extract_buyer_preferences(data)

        # Initialize buyer state
        buyer_state = {
            "contact_id": contact_id,
            "name": name,
            "email": email,
            "qualification_stage": "Q0",
            "preferences": initial_preferences,
            "buyer_score": 0,
            "properties_matched": 0,
            "created_at": __import__("datetime").datetime.now().isoformat(),
        }

        # Store buyer state
        await _store_buyer_state(contact_id, buyer_state)

        # Analyze initial intent
        if data.get("message"):
            intent_analysis = await _analyze_buyer_intent(data.get("message"))
            buyer_state["initial_intent"] = intent_analysis

            # Update preferences from intent analysis
            if intent_analysis.get("budget"):
                buyer_state["preferences"]["budget"] = intent_analysis["budget"]
            if intent_analysis.get("timeline"):
                buyer_state["preferences"]["timeline"] = intent_analysis["timeline"]

        # Send initial greeting
        await _send_buyer_greeting(contact_id, buyer_state)

        # Update GHL
        await _update_ghl_buyer_fields(contact_id, buyer_state)

        # Emit event
        await _emit_buyer_event("buyer.inquiry.received", buyer_state)

        return {
            "success": True,
            "contact_id": contact_id,
            "buyer_state": buyer_state,
            "action": "Buyer inquiry processed",
        }

    except Exception as e:
        logger.error(f"Failed to handle buyer inquiry: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


@register_handler("conversation.message.created")
async def handle_buyer_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ConversationMessageCreate from buyers.

    Continue qualification and property matching.
    """
    try:
        data = payload.get("data", payload)

        contact_id = data.get("contactId") or data.get("contact_id")
        message = data.get("message") or data.get("body", "")
        direction = data.get("direction", "inbound")

        if direction != "inbound":
            return {"success": True, "message": "Outbound message, no action needed"}

        logger.info(f"Buyer response from {contact_id}: {message[:50]}...")

        # Get current buyer state
        buyer_state = await _get_buyer_state(contact_id)
        if not buyer_state:
            logger.warning(f"No buyer state found for {contact_id}, initializing")
            buyer_state = await _initialize_buyer_from_contact(contact_id)

        current_stage = buyer_state.get("qualification_stage", "Q0")

        # Process message based on qualification stage
        next_stage, response_message, updates = await _process_buyer_message(
            contact_id, current_stage, message, buyer_state
        )

        # Update buyer state
        buyer_state["qualification_stage"] = next_stage
        buyer_state["last_message"] = message
        buyer_state["last_response"] = response_message

        # Merge any updates
        if updates:
            buyer_state.update(updates)

        # Calculate buyer score
        buyer_state["buyer_score"] = _calculate_buyer_score(buyer_state)

        await _store_buyer_state(contact_id, buyer_state)

        # Update GHL
        await _update_ghl_buyer_fields(contact_id, buyer_state)

        # Send response
        await _send_buyer_message(contact_id, response_message)

        # Check if qualified for property matching
        if next_stage == "Q4" or buyer_state["buyer_score"] >= 70:
            properties = await _match_properties(buyer_state)
            if properties:
                await _send_property_recommendations(contact_id, properties, buyer_state)
                buyer_state["properties_matched"] = len(properties)
                await _store_buyer_state(contact_id, buyer_state)

        # Emit event
        await _emit_buyer_event(
            "buyer.response.processed",
            {
                "contact_id": contact_id,
                "stage": next_stage,
                "buyer_score": buyer_state["buyer_score"],
                "message_preview": message[:100],
            },
        )

        return {
            "success": True,
            "contact_id": contact_id,
            "stage": next_stage,
            "buyer_score": buyer_state["buyer_score"],
            "response_sent": response_message,
        }

    except Exception as e:
        logger.error(f"Failed to handle buyer response: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


@register_handler("pipeline.stage.changed")
async def handle_pipeline_change(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PipelineStageChange for buyer pipeline.

    Sync stage changes to bot state.
    """
    try:
        data = payload.get("data", payload)

        contact_id = data.get("contactId") or data.get("contact_id")
        pipeline_id = data.get("pipelineId") or data.get("pipeline_id")
        new_stage_id = data.get("newStageId") or data.get("new_stage_id")
        old_stage_id = data.get("oldStageId") or data.get("old_stage_id")

        # Check if this is buyer pipeline
        buyer_pipeline_ids = _get_buyer_pipeline_ids()
        if pipeline_id not in buyer_pipeline_ids:
            return {
                "success": True,
                "message": "Not a buyer pipeline, skipping",
                "pipeline_id": pipeline_id,
            }

        logger.info(f"Buyer pipeline change for {contact_id}: {old_stage_id} -> {new_stage_id}")

        # Map stage to qualification stage
        stage_mapping = _get_stage_qualification_mapping()
        qualification_stage = stage_mapping.get(new_stage_id)

        # Update buyer state
        buyer_state = await _get_buyer_state(contact_id)
        if buyer_state:
            buyer_state["pipeline_stage_id"] = new_stage_id
            if qualification_stage:
                buyer_state["qualification_stage"] = qualification_stage
            buyer_state["last_pipeline_change"] = __import__("datetime").datetime.now().isoformat()

            await _store_buyer_state(contact_id, buyer_state)

            # Update GHL
            await _update_ghl_buyer_fields(contact_id, buyer_state)

        # Emit event
        await _emit_buyer_event(
            "buyer.pipeline.changed",
            {
                "contact_id": contact_id,
                "old_stage": old_stage_id,
                "new_stage": new_stage_id,
                "qualification_stage": qualification_stage,
            },
        )

        return {
            "success": True,
            "contact_id": contact_id,
            "pipeline_stage": new_stage_id,
            "qualification_stage": qualification_stage,
        }

    except Exception as e:
        logger.error(f"Failed to handle pipeline change: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


# Helper functions


def _extract_buyer_preferences(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract buyer preferences from contact data"""
    preferences = {
        "budget_min": None,
        "budget_max": None,
        "bedrooms": None,
        "bathrooms": None,
        "location_preferences": [],
        "property_types": [],
        "timeline": None,
    }

    # Extract from custom fields
    custom_fields = data.get("customFields", {})

    if "budget_min" in custom_fields:
        preferences["budget_min"] = _parse_budget(custom_fields["budget_min"])
    if "budget_max" in custom_fields:
        preferences["budget_max"] = _parse_budget(custom_fields["budget_max"])
    if "bedrooms" in custom_fields:
        preferences["bedrooms"] = custom_fields["bedrooms"]
    if "bathrooms" in custom_fields:
        preferences["bathrooms"] = custom_fields["bathrooms"]

    # Extract from message if present
    message = data.get("message", "")
    if message:
        extracted = _extract_preferences_from_message(message)
        for key, value in extracted.items():
            if value and not preferences.get(key):
                preferences[key] = value

    return preferences


def _parse_budget(value) -> Optional[float]:
    """Parse budget value from various formats"""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove non-numeric characters except decimal
        import re

        numeric = re.sub(r"[^\d.]", "", value)
        try:
            return float(numeric) if numeric else None
        except ValueError:
            return None
    return None


def _extract_preferences_from_message(message: str) -> Dict[str, Any]:
    """Extract buyer preferences from message text"""
    extracted = {}
    message_lower = message.lower()

    # Budget extraction
    import re

    budget_patterns = [
        r"(?:budget|looking for|up to|around|about)\s*[\$]?\s*(\d[\d,\.]+\s*[kmb]?)",
        r"\$\s*(\d[\d,\.]+\s*[kmb]?)",
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, message_lower)
        if match:
            budget_str = match.group(1).replace(",", "")
            # Handle K/M/B suffixes
            multiplier = 1
            if budget_str.endswith("k"):
                multiplier = 1000
                budget_str = budget_str[:-1]
            elif budget_str.endswith("m"):
                multiplier = 1000000
                budget_str = budget_str[:-1]
            try:
                extracted["budget_max"] = float(budget_str) * multiplier
            except ValueError:
                pass
            break

    # Bedrooms/bathrooms
    bed_match = re.search(r"(\d+)\s*bed", message_lower)
    if bed_match:
        extracted["bedrooms"] = int(bed_match.group(1))

    bath_match = re.search(r"(\d+(?:\.5)?)\s*bath", message_lower)
    if bath_match:
        extracted["bathrooms"] = float(bath_match.group(1))

    # Location (simple city name extraction)
    location_keywords = [
        "rancho cucamonga",
        "ontario",
        "fontana",
        "upland",
        "claremont",
        "la verne",
        "san dimas",
        "glendora",
        "covina",
        "west covina",
        "walnut",
        "diamond bar",
        "pomona",
        "chino",
        "chino hills",
        "eastvale",
        "mira loma",
        "riverside",
    ]
    found_locations = [loc for loc in location_keywords if loc in message_lower]
    if found_locations:
        extracted["location_preferences"] = found_locations

    # Timeline
    timeline_keywords = {
        "asap": "ASAP",
        "immediately": "ASAP",
        "right away": "ASAP",
        "this month": "30_days",
        "next month": "30_days",
        "30 days": "30_days",
        "60 days": "60_days",
        "90 days": "90_days",
        "6 months": "180_days",
        "just looking": "exploring",
        "browsing": "exploring",
    }
    for keyword, timeline in timeline_keywords.items():
        if keyword in message_lower:
            extracted["timeline"] = timeline
            break

    return extracted


async def _analyze_buyer_intent(message: str) -> Dict[str, Any]:
    """Analyze buyer intent from initial message"""
    message_lower = message.lower()

    intents = []

    # Intent detection
    if any(w in message_lower for w in ["first time", "first-time", "starter home"]):
        intents.append("first_time_buyer")
    if any(w in message_lower for w in ["investment", "rental", "cash flow", "cap rate"]):
        intents.append("investor")
    if any(w in message_lower for w in ["upgrade", "bigger home", "more space", "growing family"]):
        intents.append("move_up_buyer")
    if any(w in message_lower for w in ["downsize", "smaller home", "retire", "retirement", "empty nest"]):
        intents.append("downsizer")
    if any(w in message_lower for w in ["pre-approved", "preapproved", "pre approval", "financing ready"]):
        intents.append("pre_approved")

    # Extract preferences
    preferences = _extract_preferences_from_message(message)

    return {
        "intents": intents,
        "budget": preferences.get("budget_max"),
        "timeline": preferences.get("timeline"),
        "buyer_type": intents[0] if intents else "general_buyer",
    }


async def _process_buyer_message(
    contact_id: str, current_stage: str, message: str, buyer_state: Dict[str, Any]
) -> tuple:
    """
    Process buyer qualification message.

    Returns: (next_stage, response_message, updates)
    """
    from ...ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

    bot = JorgeBuyerBot()

    # Use buyer bot to process message
    result = await bot.process_buyer_conversation(
        contact_id=contact_id,
        message=message,
        stage=current_stage,
        preferences=buyer_state.get("preferences", {}),
        context=buyer_state,
    )

    next_stage = result.get("next_stage", current_stage)
    response = result.get("response", "Thank you for your message. Let me help you find the perfect home.")

    updates = {}
    if result.get("preferences_updated"):
        updates["preferences"] = result.get("preferences_updated")
    if result.get("financial_readiness"):
        updates["financial_readiness"] = result.get("financial_readiness")

    return next_stage, response, updates


def _calculate_buyer_score(buyer_state: Dict[str, Any]) -> int:
    """Calculate buyer qualification score (0-100)"""
    score = 0

    # Stage contribution
    stage_scores = {
        "Q0": 10,
        "Q1": 25,
        "Q2": 40,
        "Q3": 60,
        "Q4": 80,
        "QUALIFIED": 90,
    }
    score += stage_scores.get(buyer_state.get("qualification_stage"), 0)

    # Budget clarity
    prefs = buyer_state.get("preferences", {})
    if prefs.get("budget_min") and prefs.get("budget_max"):
        score += 10
    elif prefs.get("budget_max"):
        score += 5

    # Location preference
    if prefs.get("location_preferences"):
        score += 5

    # Timeline
    if prefs.get("timeline"):
        score += 5

    return min(score, 100)


async def _match_properties(buyer_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Match properties based on buyer preferences"""
    try:
        from ...ghl_real_estate_ai.services.property_matcher import PropertyMatcher

        matcher = PropertyMatcher()
        preferences = buyer_state.get("preferences", {})

        matches = await matcher.find_matches(
            budget_min=preferences.get("budget_min"),
            budget_max=preferences.get("budget_max"),
            bedrooms=preferences.get("bedrooms"),
            bathrooms=preferences.get("bathrooms"),
            locations=preferences.get("location_preferences", []),
            limit=5,
        )

        return matches

    except Exception as e:
        logger.error(f"Property matching failed: {e}")
        return []


async def _send_buyer_greeting(contact_id: str, buyer_state: Dict[str, Any]):
    """Send initial greeting to buyer"""
    try:
        client = GHLAPIClient()

        name = buyer_state.get("name", "").split()[0]

        # Personalize based on initial intent
        initial_intent = buyer_state.get("initial_intent", {})
        buyer_type = initial_intent.get("buyer_type", "home buyer")

        if buyer_type == "first_time_buyer":
            message = f"Hi {name}! Congratulations on starting your home buying journey! I'm here to guide you through every step. Let's start by understanding what you're looking for - what's your ideal location and budget range?"
        elif buyer_type == "investor":
            message = f"Hi {name}! I see you're interested in investment properties. I can help you find properties with great cash flow potential in the Inland Empire. What type of investment are you looking for (single-family, multi-family, etc.)?"
        else:
            message = f"Hi {name}! Thanks for reaching out about buying a home. I'm excited to help you find the perfect property! Can you tell me a bit about what you're looking for - location, budget, and must-haves?"

        await client.send_message(contact_id, message, "SMS")

    except Exception as e:
        logger.error(f"Failed to send greeting: {e}")


async def _send_property_recommendations(
    contact_id: str, properties: List[Dict[str, Any]], buyer_state: Dict[str, Any]
):
    """Send property recommendations to buyer"""
    try:
        client = GHLAPIClient()

        name = buyer_state.get("name", "").split()[0]

        # Send intro message
        intro = f"Hi {name}! Based on what you've shared, I found some properties that might interest you:"
        await client.send_message(contact_id, intro, "SMS")

        # Send top 3 properties
        for i, prop in enumerate(properties[:3], 1):
            address = prop.get("address", "")
            price = prop.get("price", 0)
            beds = prop.get("bedrooms", "N/A")
            baths = prop.get("bathrooms", "N/A")
            sqft = prop.get("square_feet", "N/A")

            prop_message = f"{i}. {address}\n${price:,.0f} | {beds}bd/{baths}ba | {sqft} sqft"
            await client.send_message(contact_id, prop_message, "SMS")

        # Follow up
        follow_up = "Would you like to schedule a showing for any of these? Or I can send you more options!"
        await client.send_message(contact_id, follow_up, "SMS")

    except Exception as e:
        logger.error(f"Failed to send property recommendations: {e}")


async def _store_buyer_state(contact_id: str, state: Dict[str, Any]):
    """Store buyer state in cache"""
    try:
        cache = CacheService()
        await cache.set(
            f"buyer:state:{contact_id}",
            state,
            ttl=2592000,  # 30 days
        )
    except Exception as e:
        logger.error(f"Failed to store buyer state: {e}")


async def _get_buyer_state(contact_id: str) -> Optional[Dict[str, Any]]:
    """Get buyer state from cache"""
    try:
        cache = CacheService()
        return await cache.get(f"buyer:state:{contact_id}")
    except Exception as e:
        logger.error(f"Failed to get buyer state: {e}")
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


async def _initialize_buyer_from_contact(contact_id: str) -> Dict[str, Any]:
    """Initialize buyer state from contact data"""
    contact = await _get_contact_details(contact_id)

    state = {
        "contact_id": contact_id,
        "name": contact.get("name", ""),
        "email": contact.get("email"),
        "qualification_stage": "Q0",
        "preferences": _extract_buyer_preferences(contact),
        "initialized_at": __import__("datetime").datetime.now().isoformat(),
    }

    await _store_buyer_state(contact_id, state)
    return state


async def _send_buyer_message(contact_id: str, message: str):
    """Send message to buyer via GHL"""
    try:
        client = GHLAPIClient()
        await client.send_message(contact_id, message, "SMS")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")


async def _update_ghl_buyer_fields(contact_id: str, buyer_data: Dict[str, Any]):
    """Update GHL custom fields for buyer"""
    try:
        client = GHLAPIClient()

        custom_fields = {}

        if "buyer_score" in buyer_data:
            custom_fields["buyer_score"] = buyer_data["buyer_score"]
        if "qualification_stage" in buyer_data:
            custom_fields["buyer_qualification_stage"] = buyer_data["qualification_stage"]
        if "properties_matched" in buyer_data:
            custom_fields["properties_matched"] = buyer_data["properties_matched"]

        prefs = buyer_data.get("preferences", {})
        if prefs.get("timeline"):
            custom_fields["buyer_timeline_days"] = _timeline_to_days(prefs["timeline"])

        if custom_fields:
            await client.update_contact(contact_id, {"customFields": custom_fields})

    except Exception as e:
        logger.error(f"Failed to update GHL fields: {e}")


def _timeline_to_days(timeline: str) -> Optional[int]:
    """Convert timeline string to days"""
    mapping = {
        "ASAP": 7,
        "30_days": 30,
        "60_days": 60,
        "90_days": 90,
        "180_days": 180,
    }
    return mapping.get(timeline)


def _get_buyer_pipeline_ids() -> List[str]:
    """Get list of buyer pipeline IDs from config"""
    import os

    ids = os.getenv("GHL_BUYER_PIPELINE_IDS", "").split(",")
    return [id.strip() for id in ids if id.strip()]


def _get_stage_qualification_mapping() -> Dict[str, str]:
    """Map pipeline stage IDs to qualification stages"""
    # This should be configured based on actual GHL pipeline stages
    return {
        "stage_new_lead": "Q0",
        "stage_contacted": "Q1",
        "stage_qualified": "Q2",
        "stage_showing": "Q3",
        "stage_offer_pending": "Q4",
    }


async def _emit_buyer_event(event_type: str, data: Dict[str, Any]):
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


from datetime import datetime
