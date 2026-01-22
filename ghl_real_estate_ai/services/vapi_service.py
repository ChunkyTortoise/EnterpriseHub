"""
Vapi Service - AI Voice Call Orchestration.

Triggers real-time outbound calls to high-intent leads using Vapi.ai.
"""
import os
import requests
import json
from typing import Dict, Any, Optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class VapiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VAPI_API_KEY")
        self.assistant_id = os.getenv("VAPI_ASSISTANT_ID")
        self.base_url = "https://api.vapi.ai"
        
        if not self.api_key:
            logger.warning("VAPI_API_KEY not found. Voice calls will be disabled.")

    def trigger_outbound_call(
        self, 
        contact_phone: str, 
        lead_name: str, 
        property_address: str,
        extra_variables: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Triggers an outbound call to a lead with full conversation context.
        """
        if not self.api_key or not self.assistant_id:
            logger.info(f"🚀 [MOCK] Triggering Vapi Call to {lead_name} ({contact_phone})")
            logger.info(f"   Context: {json.dumps(extra_variables, indent=2) if extra_variables else 'None'}")
            return True

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Combine standard variables with extras
        variable_values = {
            "leadName": lead_name,
            "propertyAddress": property_address
        }
        if extra_variables:
            variable_values.update(extra_variables)

        # Vapi Call Payload
        payload = {
            "assistantId": self.assistant_id,
            "customer": {
                "number": contact_phone,
                "name": lead_name
            },
            "assistantOverrides": {
                "variableValues": variable_values
            }
        }

        try:
            url = f"{self.base_url}/call/phone"
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                logger.info(f"✅ Vapi Call Triggered Successfully for {lead_name}")
                return True
            else:
                logger.error(f"❌ Vapi Call Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Vapi Exception: {e}")
            return False

if __name__ == "__main__":
    # Test/Demo
    vapi = VapiService()
    vapi.trigger_outbound_call("+15125551234", "John Doe", "123 Maple Street")
