"""
Voice AI Outbound Service - Bridge to Vapi.ai / Retell
Prepares "Seller Psychology" payloads for outbound Voice AI calls.
"""

import json
from datetime import datetime
from typing import Any, Dict

import httpx

from ghl_real_estate_ai.api.schemas.negotiation import ListingHistory
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType, get_claude_orchestrator
from ghl_real_estate_ai.services.seller_psychology_analyzer import get_seller_psychology_analyzer

logger = get_logger(__name__)


class VoiceOutboundService:
    """
    Orchestrates outbound voice AI calls by preparing psychologically-optimized payloads.
    """

    def __init__(self):
        self.orchestrator = get_claude_orchestrator()
        self.psychology_analyzer = get_seller_psychology_analyzer()

    async def prepare_vapi_payload(
        self, lead_id: str, lead_data: Dict[str, Any], property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare a comprehensive payload for Vapi.ai.
        Includes:
        - Call Script (psychologically optimized)
        - Lead Emotional State
        - Predicted Objections
        - Market Context
        """
        logger.info(f"Preparing Voice AI payload for lead {lead_id}")

        # Ensure listing history is a proper model
        history_data = property_data.get("history", {})
        listing_history = ListingHistory(
            original_list_price=history_data.get("original_list_price", property_data.get("list_price", 0)),
            current_price=history_data.get("current_price", property_data.get("list_price", 0)),
            price_drops=history_data.get("price_drops", []),
            days_on_market=history_data.get("days_on_market", 0),
            listing_views=history_data.get("listing_views"),
            showing_requests=history_data.get("showing_requests"),
            offers_received=history_data.get("offers_received"),
            previous_listing_attempts=history_data.get("previous_listing_attempts"),
        )

        # 1. Analyze seller psychology
        communication_context = {
            "avg_response_time_hours": 24,  # Default
            "communication_tone": "neutral",
            "history": lead_data.get("conversation_history", []),
        }

        psychology = await self.psychology_analyzer.analyze_seller_psychology(
            property_id=property_data.get("id", "unknown"),
            listing_history=listing_history,
            communication_data=communication_context,
        )

        # 2. Generate optimized script and objection handlers using Claude
        prompt = f"""
        As a world-class real estate listing agent, prepare a Voice AI call script payload.
        
        LEAD PROFILE:
        {json.dumps(lead_data, indent=2)}
        
        SELLER PSYCHOLOGY:
        - Motivation: {psychology.motivation_type}
        - Urgency: {psychology.urgency_level}
        - Flexibility: {psychology.flexibility_score}/100
        
        PROPERTY DATA:
        {json.dumps(property_data, indent=2)}
        
        Provide a JSON payload for Vapi.ai containing:
        1. system_prompt: The core persona and instructions for the Voice AI.
        2. first_message: The opening line of the call.
        3. knowledge_base: Key facts about the property and market.
        4. emotional_state: Analysis of lead's current mood/attitude.
        5. predicted_objections: List of likely objections and how to handle them.
        """

        request = ClaudeRequest(
            task_type=ClaudeTaskType.SCRIPT_GENERATION,
            context={"lead_id": lead_id, "mode": "voice_outbound"},
            prompt=prompt,
            temperature=0.5,
        )

        response = await self.orchestrator.process_request(request)

        try:
            # Parse JSON from Claude's response
            import re

            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                payload_data = json.loads(json_match.group())
            else:
                payload_data = {"error": "Could not parse Claude response"}
        except Exception as e:
            logger.error(f"Failed to parse Voice AI payload: {e}")
            payload_data = {"error": str(e)}

        return {
            "lead_id": lead_id,
            "vapi_config": {
                "model": "gpt-4-turbo",  # Vapi default or configured
                "voice": "jorge-custom-voice",
                "system_prompt": payload_data.get(
                    "system_prompt", "You are a professional real estate assistant calling on behalf of Jorge."
                ),
                "first_message": payload_data.get(
                    "first_message",
                    f"Hi {lead_data.get('first_name', '')}, it's Jorge's office calling about your property.",
                ),
            },
            "intelligence": {
                "emotional_state": payload_data.get("emotional_state", "Unknown"),
                "predicted_objections": payload_data.get("predicted_objections", []),
                "psychology": {
                    "motivation": psychology.motivation_type
                    if isinstance(psychology.motivation_type, str)
                    else psychology.motivation_type.value,
                    "urgency": psychology.urgency_level
                    if isinstance(psychology.urgency_level, str)
                    else psychology.urgency_level.value,
                },
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def trigger_vapi_call(self, customer_number: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actually trigger the outbound call via Vapi.ai API.
        """
        if not settings.vapi_api_key:
            logger.warning("Vapi API key not configured. Skipping outbound call.")
            return {"status": "skipped", "reason": "API key missing"}

        url = "https://api.vapi.ai/call/phone"
        headers = {"Authorization": f"Bearer {settings.vapi_api_key}", "Content-Type": "application/json"}

        vapi_payload = {
            "assistantId": settings.vapi_assistant_id,
            "phoneNumberId": settings.vapi_phone_number_id,
            "customer": {"number": customer_number},
            "assistantOverrides": {
                "variableValues": {"first_message": payload["vapi_config"]["first_message"]},
                "serverMessages": [{"role": "system", "content": payload["vapi_config"]["system_prompt"]}],
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=vapi_payload, headers=headers, timeout=10.0)
                response.raise_for_status()
                call_data = response.json()

                logger.info(f"Successfully triggered Vapi call for {customer_number}. Call ID: {call_data.get('id')}")
                return {"status": "success", "call_id": call_data.get("id"), "vapi_response": call_data}
        except Exception as e:
            logger.error(f"Failed to trigger Vapi call: {e}")
            return {"status": "error", "message": str(e)}

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        Fetch the status of a specific Vapi call.
        """
        if not settings.vapi_api_key:
            return {"status": "error", "message": "API key missing"}

        url = f"https://api.vapi.ai/call/{call_id}"
        headers = {"Authorization": f"Bearer {settings.vapi_api_key}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch call status for {call_id}: {e}")
            return {"error": str(e)}


# Singleton instance
_voice_outbound_service = None


def get_voice_outbound_service() -> VoiceOutboundService:
    global _voice_outbound_service
    if _voice_outbound_service is None:
        _voice_outbound_service = VoiceOutboundService()
    return _voice_outbound_service
