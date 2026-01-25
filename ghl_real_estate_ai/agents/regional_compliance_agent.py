"""
Regional Compliance Agent - Phase 7
Adjusts system behavior based on local real estate laws and data regulations.
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class RegionalComplianceAgent:
    """
    Ensures autonomous agents adhere to regional laws (GDPR, CCPA, Local Disclosure Laws).
    """
    def __init__(self):
        self.rules = {
            "CA": {
                "disclosures": ["Natural Hazard Disclosure", "Agency Disclosure"],
                "data_privacy": "CCPA",
                "sms_consent_required": True
            },
            "CA": {
                "disclosures": ["Information About Brokerage Services (IABS)"],
                "data_privacy": "Standard US",
                "sms_consent_required": True
            },
            "EMEA": {
                "disclosures": ["Standard Privacy Notice"],
                "data_privacy": "GDPR",
                "sms_consent_required": True,
                "opt_out_enforced": True
            }
        }

    def get_compliance_guardrails(self, region: str) -> Dict[str, Any]:
        """Fetch guardrails for a specific region."""
        # Normalize region
        norm_region = region.upper() if len(region) == 2 else region
        return self.rules.get(norm_region, self.rules.get("CA")) # Default to CA rules

    def audit_message(self, message: str, region: str) -> List[str]:
        """Audit an AI-generated message for compliance issues."""
        warnings = []
        guardrails = self.get_compliance_guardrails(region)
        
        if guardrails.get("data_privacy") == "GDPR":
            if "track" in message.lower() or "monitor" in message.lower():
                warnings.append("Message mentions tracking; ensure explicit GDPR consent is logged.")
        
        return warnings

# Global instance
_compliance_agent = None

def get_compliance_agent() -> RegionalComplianceAgent:
    global _compliance_agent
    if _compliance_agent is None:
        _compliance_agent = RegionalComplianceAgent()
    return _compliance_agent
