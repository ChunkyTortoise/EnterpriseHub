"""
GHL DNA Synchronization Service (The Bridge)
Maps 25+ Qualification Factors and 16+ Lifestyle Dimensions into GHL Custom Fields.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class GHLSyncService:
    """
    Bridges the gap between Claude's psychological insights and GHL execution.
    Transforms deep intelligence JSON into CRM-actionable data.
    """

    def __init__(self, ghl_client: Optional[GHLClient] = None):
        self.ghl_client = ghl_client or GHLClient()
        
        # Mapping of Platform Keys to GHL Custom Field Keys/IDs
        # In a real scenario, these would be retrieved from GHL account settings
        self.dna_field_mapping = {
            # 25+ Qualification Factors
            "intent_level": "dna_intent_level",
            "financial_readiness": "dna_financial_readiness",
            "timeline_urgency": "dna_timeline_urgency",
            "emotional_investment": "dna_emotional_investment",
            "decision_authority": "dna_decision_authority",
            "market_knowledge": "dna_market_knowledge",
            "property_urgency": "dna_property_urgency",
            "referral_likelihood": "dna_referral_likelihood",
            "communication_preference": "dna_comm_pref",
            "negotiation_style": "dna_neg_style",
            "research_depth": "dna_research_depth",
            "price_anchoring": "dna_price_anchoring",
            "location_flexibility": "dna_loc_flexibility",
            "financing_sophistication": "dna_fin_sophistication",
            "renovation_readiness": "dna_reno_readiness",
            "investment_mindset": "dna_inv_mindset",
            "lifestyle_alignment": "dna_lifestyle_alignment",
            "trust_building": "dna_trust_score",
            "objection_handling": "dna_objection_resilience",
            "follow_through": "dna_reliability_score",
            "competitive_awareness": "dna_comp_awareness",
            "social_influence": "dna_social_influence",
            "stress_tolerance": "dna_stress_tolerance",
            "technology_comfort": "dna_tech_comfort",
            "local_market_fit": "dna_market_fit",

            # 16+ Lifestyle Dimensions
            "status": "life_status_priority",
            "convenience": "life_convenience_priority",
            "security": "life_security_priority",
            "investment": "life_investment_priority",
            "family": "life_family_priority",
            "career": "life_career_priority",
            "lifestyle": "life_lifestyle_priority",
            "privacy": "life_privacy_priority",
            "social_connectivity": "life_social_conn",
            "cultural_fit": "life_cultural_fit",
            "commute_optimization": "life_commute_opt",
            "future_family_planning": "life_fam_planning",
            "aging_in_place": "life_aging_in_place",
            "environmental_values": "life_eco_values",
            "technology_integration": "life_smart_home",
            "health_wellness": "life_health_wellness",
            "work_life_balance": "life_wlb",
            "aesthetic_appreciation": "life_aesthetic",
            "community_involvement": "life_community",
            "educational_priorities": "life_education",
            "entertainment_hosting": "life_hosting",
            "outdoor_recreation": "life_outdoor",
            "cultural_access": "life_culture"
        }

    async def sync_dna_to_ghl(self, contact_id: str, dna_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pushes the entire psychological JSON payload to GHL contact record.
        
        Args:
            contact_id: GHL contact ID
            dna_payload: Combined dictionary of factors and dimensions
            
        Returns:
            Sync status and details
        """
        logger.info(f"Syncing DNA payload to GHL for contact {contact_id}")
        
        custom_fields_to_update = []
        
        # Flatten payload if needed (handles cases where factors and dimensions are in sub-dicts)
        flat_dna = self._flatten_payload(dna_payload)
        
        for platform_key, ghl_key in self.dna_field_mapping.items():
            if platform_key in flat_dna:
                value = flat_dna[platform_key]
                # Format value for GHL (convert floats to percentages or strings as needed)
                formatted_value = self._format_value_for_ghl(value)
                custom_fields_to_update.append({
                    "id": ghl_key,
                    "value": formatted_value
                })

        if not custom_fields_to_update:
            logger.warning(f"No matching DNA fields found in payload for {contact_id}")
            return {"status": "skipped", "message": "No DNA fields matched"}

        try:
            # Update GHL Contact with all custom fields at once
            # We can use update_contact but our GHLClient has update_custom_field which does one by one
            # Let's see if we can optimize by doing a single PUT to /contacts/{id}
            
            # For this implementation, we'll use a batch approach if the client supported it, 
            # or loop through our client's method.
            results = []
            for field in custom_fields_to_update:
                res = await self.ghl_client.update_custom_field(contact_id, field["id"], field["value"])
                results.append(res)
            
            # Also add a "DNA Synced" tag
            await self.ghl_client.add_tags(contact_id, ["DNA_Synced", f"Last_DNA_Update_{datetime.now().strftime('%Y-%m-%d')}"])
            
            # Push raw JSON to a "Master DNA" field if it exists for deep GHL workflows
            import json
            await self.ghl_client.update_custom_field(contact_id, "master_dna_json", json.dumps(dna_payload))

            return {
                "status": "success",
                "fields_updated": len(custom_fields_to_update),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to sync DNA to GHL: {e}")
            return {"status": "error", "message": str(e)}

    def _flatten_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Flattens nested factor/dimension dictionaries into a single level."""
        flat = {}
        
        # Check for common sub-keys
        for key in ["factors", "dimensions", "priorities", "enhanced_lifestyle_priorities", "factor_scores"]:
            if key in payload and isinstance(payload[key], dict):
                flat.update(payload[key])
        
        # Add root level items that aren't the special sub-keys
        for key, value in payload.items():
            if key not in ["factors", "dimensions", "priorities", "enhanced_lifestyle_priorities", "factor_scores"]:
                flat[key] = value
                
        return flat

    def _format_value_for_ghl(self, value: Any) -> str:
        """Formats various data types for GHL custom field compatibility."""
        if isinstance(value, float):
            # Convert 0.85 to "85%"
            return f"{int(value * 100)}%"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, list):
            return ", ".join(map(str, value))
        return str(value)

    async def trigger_high_readiness_handoff(self, contact_id: str, lead_name: str, score: float):
        """Triggers a priority webhook/notification for Jorge when readiness > 85%."""
        if score < 0.85:
            return
            
        logger.info(f"🚀 HIGH READINESS DETECTED ({score:.2%}) for {lead_name}. Triggering handoff.")
        
        # Add 'Priority Handoff' tag
        await self.ghl_client.add_tags(contact_id, ["Priority_Handoff", "Ready_To_Close"])
        
        # Trigger specific Handoff Workflow in GHL
        # workflow_id would be Jorge's specific handoff automation ID
        await self.ghl_client.trigger_workflow(contact_id, "readiness_handoff_workflow_id")
        
        # Send SMS notification directly if needed
        # await self.ghl_client.send_message(
        #     contact_id="Jorge_Admin_ID", 
        #     message=f"🔥 HOT LEAD: {lead_name} has reached {score:.0%} closing readiness. DNA Dossier synced to CRM."
        # )

def get_ghl_sync_service() -> GHLSyncService:
    return GHLSyncService()