import json
from typing import Any, Dict, Optional

import aiohttp

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class RetellClient:
    """
    Client for interacting with Retell AI API.
    Handles voice call initialization, management, and webhook validation.
    """

    BASE_URL = "https://api.retellai.com"

    def __init__(self):
        self.api_key = settings.retell_api_key
        self.agent_id = settings.retell_agent_id

        if not self.api_key:
            logger.warning("Retell API Key not found. Voice features will be disabled or mocked.")

    async def create_call(
        self,
        to_number: str,
        lead_name: str,
        lead_context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        from_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call to a lead.
        """
        if not self.api_key:
            return self._mock_call_response(to_number)

        url = f"{self.BASE_URL}/v2/create-phone-call"

        # Prepare dynamic variables for the Retell agent prompt
        retell_llm_data = {"lead_name": lead_name, "lead_data": lead_context}

        payload = {
            "from_number": from_number or settings.default_agent_phone,
            "to_number": to_number,
            "agent_id": self.agent_id,
            "retell_llm_dynamic_variables": retell_llm_data,
        }

        if metadata:
            payload["metadata"] = metadata

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 201:
                        data = await response.json()
                        logger.info(f"Retell call created: {data.get('call_id')}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create Retell call: {response.status} - {error_text}")
                        raise Exception(f"Retell API Error: {error_text}")
            except Exception as e:
                logger.error(f"Error creating Retell call: {str(e)}")
                raise

    async def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve details of a specific call.
        """
        if not self.api_key:
            return {"status": "completed", "transcript": "Mock transcript"}

        url = f"{self.BASE_URL}/v2/get-call/{call_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get Retell call details: {response.status}")
                    return {}

    def _mock_call_response(self, to_number: str) -> Dict[str, Any]:
        """Return a mock response for development/testing without API keys."""
        import uuid

        return {
            "call_id": f"mock_call_{uuid.uuid4()}",
            "agent_id": self.agent_id or "mock_agent_id",
            "call_status": "registered",
            "to_number": to_number,
            "access_token": "mock_access_token",
        }

    @staticmethod
    def validate_webhook(payload: Dict[str, Any], signature: str) -> bool:
        """
        Validate Retell webhook signature (Placeholder).
        Actual implementation depends on Retell's specific signature scheme.
        """
        # TODO: Implement actual signature verification if Retell provides it.
        # For now, we assume if the secret is present in config, we might check it here.
        return True
