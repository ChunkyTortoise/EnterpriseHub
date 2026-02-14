#!/usr/bin/env python3
"""
Script to add buyer persona classification to JorgeBuyerBot.
This script modifies the jorge_buyer_bot.py file to integrate the BuyerPersonaService.
"""

import re

# Read the original file
with open("ghl_real_estate_ai/agents/jorge_buyer_bot.py", "r") as f:
    content = f.read()

# 1. Add import for BuyerPersonaService after the existing imports
import_pattern = r'(from ghl_real_estate_ai\.models\.buyer_bot_state import BuyerBotState)\n'
import_replacement = r'\1\nfrom ghl_real_estate_ai.services.buyer_persona_service import BuyerPersonaService\n'
content = re.sub(import_pattern, import_replacement, content)

# 2. Add buyer persona service initialization in __init__ method
# Find the line with self.ab_testing = ABTestingService()
init_pattern = r'(self\.ab_testing = ABTestingService\(\)\n\s+self\._init_ab_experiments\(\))'
init_replacement = r'\1\n\n        # Phase 1.4: Buyer Persona Classification\n        self.buyer_persona_service = BuyerPersonaService()'
content = re.sub(init_pattern, init_replacement, content)

# 3. Add classify_buyer_persona node to workflow
# Find the line with workflow.add_node("assess_financial_readiness", self.assess_financial_readiness)
node_pattern = r'(workflow\.add_node\("assess_financial_readiness", self\.assess_financial_readiness\))'
node_replacement = r'\1\n\n        # Phase 1.4: Buyer Persona Classification\n        workflow.add_node("classify_buyer_persona", self.classify_buyer_persona)'
content = re.sub(node_pattern, node_replacement, content)

# 4. Update workflow edges to include classify_buyer_persona
# Find the else block for intelligence gathering
edges_pattern = r'(else:\n\s+workflow\.add_edge\("analyze_buyer_intent", "assess_financial_readiness"\))'
edges_replacement = r'else:\n            workflow.add_edge("analyze_buyer_intent", "classify_buyer_persona")\n            workflow.add_edge("classify_buyer_persona", "assess_financial_readiness")'
content = re.sub(edges_pattern, edges_replacement, content)

# Also update the intelligence gathering path
intel_pattern = r'(workflow\.add_edge\("gather_buyer_intelligence", "assess_financial_readiness"\))'
intel_replacement = r'workflow.add_edge("gather_buyer_intelligence", "classify_buyer_persona")\n            workflow.add_edge("classify_buyer_persona", "assess_financial_readiness")'
content = re.sub(intel_pattern, intel_replacement, content)

# 5. Add the classify_buyer_persona method
# Find the analyze_buyer_intent method and add the new method after it
method_pattern = r'(async def analyze_buyer_intent\(self, state: BuyerBotState\) -> Dict:.*?except Exception as e:\s+logger\.error\(f"Error analyzing buyer intent for \{state\.get\('buyer_id'\)\}: \{str\(e\)\}"\)\s+return \{.*?\}\s*\n)'
method_replacement = r'\1\n\n    async def classify_buyer_persona(self, state: BuyerBotState) -> Dict:\n        """Classify buyer persona based on conversation analysis (Phase 1.4)."""\n        try:\n            conversation_history = state.get("conversation_history", [])\n            buyer_id = state.get("buyer_id", "unknown")\n            lead_data = state.get("lead_data", {})\n\n            # Classify buyer persona\n            persona_classification = await self.buyer_persona_service.classify_buyer_type(\n                conversation_history=conversation_history,\n                lead_data=lead_data,\n            )\n\n            # Get persona insights for response tailoring\n            persona_insights = await self.buyer_persona_service.get_persona_insights(\n                persona_classification.persona_type\n            )\n\n            # Sync persona to GHL as tags if confidence is high enough\n            if persona_classification.confidence >= 0.6:\n                await self._sync_buyer_persona_to_ghl(\n                    buyer_id, persona_classification\n                )\n\n            logger.info(\n                f"Buyer persona classified for {buyer_id}: "\n                f"{persona_classification.persona_type.value} "\n                f"(confidence: {persona_classification.confidence:.2f})"\n            )\n\n            return {\n                "buyer_persona": persona_classification.persona_type.value,\n                "buyer_persona_confidence": persona_classification.confidence,\n                "buyer_persona_signals": persona_classification.detected_signals,\n                "buyer_persona_insights": persona_insights.model_dump(),\n            }\n        except Exception as e:\n            logger.error(f"Error classifying buyer persona for {state.get('buyer_id')}: {str(e)}")\n            return {\n                "buyer_persona": "unknown",\n                "buyer_persona_confidence": 0.0,\n                "buyer_persona_signals": [],\n                "buyer_persona_insights": {},\n            }\n\n    async def _sync_buyer_persona_to_ghl(\n        self, buyer_id: str, persona_classification\n    ) -> None:\n        """Sync buyer persona to GHL as tags (Phase 1.4)."""\n        try:\n            persona_tag = f"Buyer-{persona_classification.persona_type.value}"\n            confidence_tag = f"Persona-Conf-{int(persona_classification.confidence * 100)}%"\n\n            # Add tags to contact in GHL\n            await self.ghl_client.add_contact_tags(\n                contact_id=buyer_id,\n                tags=[persona_tag, confidence_tag]\n            )\n\n            logger.info(f"Synced buyer persona tags to GHL for {buyer_id}: {persona_tag}")\n        except Exception as e:\n            logger.warning(f"Failed to sync buyer persona to GHL for {buyer_id}: {str(e)}")\n'
content = re.sub(method_pattern, method_replacement, content, flags=re.DOTALL)

# Write the modified content back
with open("ghl_real_estate_ai/agents/jorge_buyer_bot.py", "w") as f:
    f.write(content)

print("Successfully added buyer persona classification to JorgeBuyerBot")
