import asyncio
from datetime import datetime
from typing import Any, Dict

import aiohttp

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.circuit_breaker import get_circuit_manager

logger = get_logger(__name__)


class LyrioClient:
    """
    Client for Lyrio.io Headless API Integration.
    EnterpriseHub acts as the 'Intelligence Layer' for Lyrio.
    """

    BASE_URL = "https://api.lyrio.io/v1"

    def __init__(self):
        self.api_key = settings.lyrio_api_key if hasattr(settings, "lyrio_api_key") else "mock_lyrio_key"
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Circuit breaker for fault tolerance
        circuit_manager = get_circuit_manager()
        self.circuit_breaker = circuit_manager.get_or_create_breaker("lyrio")

    async def sync_lead_score(self, contact_id: str, frs_score: float, pcs_score: float, tags: list) -> bool:
        """
        Push FRS/PCS scores and classification tags to Lyrio CRM via circuit breaker.
        """
        logger.info(f"Syncing lead scores to Lyrio for {contact_id}: FRS {frs_score}, PCS {pcs_score}")

        async def _execute_sync():
            """Internal function to execute the sync operation"""
            payload = {
                "custom_field_frs_score": frs_score,
                "custom_field_pcs_score": pcs_score,
                "tags": tags,
                "intelligence_updated_at": datetime.now().isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                # In production, this would be an actual PUT/PATCH request
                # async with session.patch(f"{self.BASE_URL}/contacts/{contact_id}", json=payload, headers=self.headers) as response:
                #     return response.status == 200

                # For now, simulate success
                await asyncio.sleep(0.1)
                return True

        # Execute through circuit breaker
        try:
            return await self.circuit_breaker.call(_execute_sync)
        except Exception as e:
            logger.error(f"Failed to sync lead score to Lyrio through circuit breaker: {e}")
            return False

    async def sync_call_summary(self, contact_id: str, call_id: str, analysis: Dict[str, Any]) -> bool:
        """
        Push call analysis and outcome to Lyrio CRM as a note or activity via circuit breaker.
        """
        logger.info(f"Syncing call summary to Lyrio for contact {contact_id}, call {call_id}")

        async def _execute_sync():
            """Internal function to execute the call summary sync"""
            payload = {
                "contact_id": contact_id,
                "activity_type": "ai_call",
                "call_id": call_id,
                "summary": analysis.get("call_summary"),
                "sentiment": analysis.get("user_sentiment"),
                "objections": analysis.get("custom_analysis_data", {}).get("objections", []),
                "successful": analysis.get("call_successful", False),
            }

            async with aiohttp.ClientSession() as session:
                # async with session.post(f"{self.BASE_URL}/activities", json=payload, headers=self.headers) as response:
                #     return response.status == 201
                await asyncio.sleep(0.1)
                return True

        # Execute through circuit breaker
        try:
            return await self.circuit_breaker.call(_execute_sync)
        except Exception as e:
            logger.error(f"Failed to sync call summary to Lyrio through circuit breaker: {e}")
            return False

    async def get_intelligence_feedback(self, contact_id: str) -> Dict[str, Any]:
        """
        Fetch post-call feedback or manual updates from Lyrio frontend.
        """
        logger.info(f"Fetching intelligence from Lyrio for {contact_id}")

        # Mock response from Lyrio's headless API
        return {
            "contact_id": contact_id,
            "call_outcome": "scheduled",
            "sentiment_end": 85,
            "objections_raised": ["price", "timeline"],
            "next_action": "send_cma_email",
        }

    async def sync_custom_object(self, object_type: str, data: Dict[str, Any]) -> bool:
        """
        Sync Custom Objects (e.g., Property AI Profile) to Lyrio.
        """
        logger.info(f"Syncing {object_type} to Lyrio: {data.get('address', 'Unknown')}")

        try:
            async with aiohttp.ClientSession() as session:
                # async with session.post(f"{self.BASE_URL}/custom-objects/{object_type}", json=data, headers=self.headers) as response:
                #     return response.status == 201
                await asyncio.sleep(0.1)
                return True
        except Exception as e:
            logger.error(f"Failed to sync custom object to Lyrio: {e}")
            return False

    async def sync_digital_twin_url(self, contact_id: str, property_address: str, twin_url: str) -> bool:
        """
        Associate a Three.js Digital Twin URL with a lead in Lyrio.
        """
        logger.info(f"Syncing Digital Twin URL to Lyrio for {contact_id}: {twin_url}")

        payload = {
            "custom_field_digital_twin_url": twin_url,
            "associated_property": property_address,
            "updated_at": datetime.now().isoformat(),
        }

        try:
            async with aiohttp.ClientSession() as session:
                # async with session.patch(f"{self.BASE_URL}/contacts/{contact_id}", json=payload, headers=self.headers) as response:
                #     return response.status == 200
                await asyncio.sleep(0.1)
                return True
        except Exception as e:
            logger.error(f"Failed to sync digital twin URL to Lyrio: {e}")
            return False
