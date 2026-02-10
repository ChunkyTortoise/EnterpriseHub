"""
Vapi Service - AI Voice Call Orchestration.

Triggers real-time outbound calls to high-intent leads using Vapi.ai.
"""

import json
import os
from typing import Any, Dict, Optional

import httpx

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
        extra_variables: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Triggers an outbound call to a lead with full conversation context.
        """
        if not self.api_key or not self.assistant_id:
            logger.info(f"🚀 [MOCK] Triggering Vapi Call to {lead_name} ({contact_phone})")
            logger.info(f"   Context: {json.dumps(extra_variables, indent=2) if extra_variables else 'None'}")
            return True

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Combine standard variables with extras
        variable_values = {"leadName": lead_name, "propertyAddress": property_address}
        if extra_variables:
            variable_values.update(extra_variables)

        # Vapi Call Payload
        payload = {
            "assistantId": self.assistant_id,
            "customer": {"number": contact_phone, "name": lead_name},
            "assistantOverrides": {"variableValues": variable_values},
        }

        # Persona-based Assistant Mapping
        persona = extra_variables.get("persona") if extra_variables else None
        if persona == "loss_aversion":
            # Specifically trigger the urgency_market_v2 assistant profile
            # In production, this would be an ID from env; here we use the specific name/ID requested
            target_assistant_id = os.getenv("VAPI_ASSISTANT_ID_LOSS_AVERSION", "urgency_market_v2")
            payload["assistantId"] = target_assistant_id
            logger.info(f"⏳ Persona 'loss_aversion' detected: Mapping to assistant profile '{target_assistant_id}'")

        # Deep Persona Handoff: Override system prompt with tone instructions if provided
        if extra_variables and "tone_instruction" in extra_variables:
            payload["assistantOverrides"]["instructions"] = extra_variables["tone_instruction"]
            logger.info(f"🎭 Applying Tone Instruction to Vapi Handoff for {lead_name}")

        # Phase 7: Litigious Seller ROI Defense Override
        if extra_variables and extra_variables.get("persona") == "The Litigious Seller":
            roi_defense_script = (
                "\n\n### ROI DEFENSE SCRIPT (LITIGIOUS SELLER)\n"
                "The lead is extremely defensive and has mentioned legal action regarding their property value. "
                "DO NOT back down on the data. Use actual market metrics to justify the repairs and price gap. "
                "Explain that our valuation is based on verifiable market absorption rates and recent 'Needs Work' comps. "
                "Be professional, firm, and de-escalate by focusing strictly on ROI and financial logic."
            )
            current_instructions = payload.get("assistantOverrides", {}).get("instructions", "")
            payload["assistantOverrides"]["instructions"] = current_instructions + roi_defense_script
            logger.warning(f"⚖️ INJECTING ROI DEFENSE SCRIPT for Litigious Seller: {lead_name}")

        # PRODUCTION HARDENING: Voss 'Drift Scores' and 'Levels' Integration
        if extra_variables and "drift_score" in extra_variables:
            drift_score = extra_variables["drift_score"]
            try:
                from ghl_real_estate_ai.services.negotiation_drift_detector import get_drift_detector

                detector = get_drift_detector()
                recommendation = detector._get_drift_recommendation(drift_score)

                voss_instruction = (
                    f"\n\n### VOSS NEGOTIATION ADAPTATION (Drift Score: {drift_score:.2f})\n"
                    f"Current Lead Flexibility: {recommendation}\n"
                    "Adjust your negotiation level accordingly. "
                )

                if drift_score > 0.7:
                    voss_instruction += (
                        "Use 'The Direct Challenge' - push for immediate commitment as the lead is highly flexible."
                    )
                elif drift_score > 0.4:
                    voss_instruction += "Use 'Labeling' - confirm their internal drift by saying 'It seems like you're considering other options'."
                else:
                    voss_instruction += "Use 'Mirroring' - maintain their firm position and build rapport by repeating their last few words."

                current_instructions = payload.get("assistantOverrides", {}).get("instructions", "")
                # If current_instructions is still empty, get it from assistantOverrides
                if not current_instructions:
                    current_instructions = ""

                payload["assistantOverrides"]["instructions"] = current_instructions + voss_instruction
                logger.info(f"🧠 Voss Drift adaptation applied to Vapi call for {lead_name} (Score: {drift_score:.2f})")
            except Exception as e:
                logger.error(f"Failed to apply Voss Drift adaptation: {e}")

        try:
            url = f"{self.base_url}/call/phone"
            response = httpx.post(url, headers=headers, json=payload)

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
