"""
Property Routes for GHL Real Estate AI.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

logger = get_logger(__name__)
router = APIRouter(prefix="/properties", tags=["properties"])

# Lazy service singletons — defer initialization until first request
_property_matcher = None
_memory_service = None


def _get_property_matcher():
    global _property_matcher
    if _property_matcher is None:
        _property_matcher = PropertyMatcher()
    return _property_matcher


def _get_memory_service():
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service


@router.get("/match/{location_id}/{contact_id}")
async def match_properties(location_id: str, contact_id: str, limit: int = 3):
    """
    Find matching properties for a specific contact based on their memory.
    """
    logger.info(f"Matching properties for contact {contact_id} in {location_id}")

    # 1. Get contact context from memory
    context = await _get_memory_service().get_context(contact_id, location_id=location_id)
    if not context:
        raise HTTPException(status_code=404, detail="Contact context not found")

    preferences = context.get("extracted_preferences", {})
    if not preferences:
        return {
            "contact_id": contact_id,
            "matches": [],
            "message": "No preferences extracted yet. Continue conversation to get matches.",
        }

    # 2. Find matches
    matches = _get_property_matcher().find_matches(preferences, limit=limit)

    return {
        "contact_id": contact_id,
        "location_id": location_id,
        "preferences": preferences,
        "matches": matches,
        "total_matches": len(matches),
    }


@router.get("/all")
async def list_all_properties():
    """List all available property listings."""
    return {
        "total": len(_get_property_matcher().listings),
        "listings": _get_property_matcher().listings,
    }
