"""
Lead Bot Webhook Handlers

Handles GHL webhook events for the Lead Bot:
- ContactCreate (new lead)
- ConversationMessageCreate (lead responses)
- ContactUpdate (lead data changes)
"""

import logging
from typing import Any, Callable, Dict, Optional

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
async def handle_new_lead(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process ContactCreate webhook from GHL.
    
    Flow:
    1. Extract contact information
    2. Analyze lead (temperature scoring)
    3. Create/update lead in database
    4. Trigger appropriate workflow
    5. Update GHL custom fields
    """
    try:
        data = payload.get("data", payload)
        
        contact_id = data.get("id")
        email = data.get("email")
        phone = data.get("phone")
        name = data.get("name", "").strip()
        
        logger.info(f"Processing new lead: {contact_id} - {name}")
        
        # Extract custom fields if present
        custom_fields = data.get("customFields", {})
        
        # Perform lead analysis
        analysis_result = await _analyze_lead(data)
        
        # Update GHL with analysis results
        await _update_ghl_lead_fields(contact_id, analysis_result)
        
        # Emit event for dashboard
        await _emit_lead_event("lead.created", {
            "contact_id": contact_id,
            "name": name,
            "temperature": analysis_result.get("temperature"),
            "score": analysis_result.get("score"),
        })
        
        return {
            "success": True,
            "contact_id": contact_id,
            "analysis": analysis_result,
            "action": "Lead processed successfully",
        }
        
    except Exception as e:
        logger.error(f"Failed to process new lead: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


@register_handler("conversation.message.created")
async def handle_lead_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ConversationMessageCreate from leads.
    
    When lead replies via SMS/email:
    1. Parse message content
    2. Re-analyze lead (temperature may change)
    3. Trigger follow-up if needed
    4. Update GHL custom fields
    """
    try:
        data = payload.get("data", payload)
        
        contact_id = data.get("contactId") or data.get("contact_id")
        message = data.get("message") or data.get("body", "")
        direction = data.get("direction", "inbound")
        
        if direction != "inbound":
            return {"success": True, "message": "Outbound message, no action needed"}
        
        logger.info(f"Lead response from {contact_id}: {message[:50]}...")
        
        # Get conversation history for context
        conversation_history = await _get_conversation_history(contact_id)
        
        # Analyze response intent
        intent_analysis = await _analyze_response_intent(message, conversation_history)
        
        # Update lead temperature if changed
        if intent_analysis.get("temperature_change"):
            await _update_lead_temperature(contact_id, intent_analysis["temperature"])
        
        # Trigger appropriate follow-up
        follow_up_action = await _determine_follow_up(contact_id, intent_analysis)
        
        # Emit event
        await _emit_lead_event("lead.response.received", {
            "contact_id": contact_id,
            "intent": intent_analysis.get("intent"),
            "temperature": intent_analysis.get("temperature"),
            "follow_up": follow_up_action,
        })
        
        return {
            "success": True,
            "contact_id": contact_id,
            "intent_analysis": intent_analysis,
            "follow_up": follow_up_action,
        }
        
    except Exception as e:
        logger.error(f"Failed to handle lead response: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


@register_handler("contact.update")
async def handle_lead_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ContactUpdate webhook.
    
    Sync GHL contact changes to bot database.
    """
    try:
        data = payload.get("data", payload)
        
        contact_id = data.get("id")
        changes = data.get("changes", {})
        
        logger.info(f"Lead update for {contact_id}: {list(changes.keys())}")
        
        # Update local database
        await _sync_contact_to_local(contact_id, changes)
        
        # Check for significant changes that need re-analysis
        significant_fields = ["email", "phone", "customFields", "tags"]
        needs_reanalysis = any(f in changes for f in significant_fields)
        
        if needs_reanalysis:
            logger.info(f"Significant changes detected, re-analyzing lead {contact_id}")
            await _trigger_reanalysis(contact_id)
        
        return {
            "success": True,
            "contact_id": contact_id,
            "changes_synced": list(changes.keys()),
            "reanalysis_triggered": needs_reanalysis,
        }
        
    except Exception as e:
        logger.error(f"Failed to handle lead update: {e}")
        return {
            "success": False,
            "error": str(e),
            "retry_eligible": True,
        }


# Helper functions

async def _analyze_lead(contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform AI analysis on lead data"""
    try:
        # Use existing analysis service
        from ...ghl_real_estate_ai.agents.jorge_lead_bot import LeadBotWorkflow
        
        workflow = LeadBotWorkflow()
        
        # Build conversation context
        message = contact_data.get("message", "")
        if not message and contact_data.get("email"):
            message = f"New lead from {contact_data.get('email')}"
        
        result = await workflow.process_lead_conversation(
            lead_id=contact_data.get("id"),
            message=message,
            context={
                "source": contact_data.get("source", "ghl_webhook"),
                "contact_data": contact_data,
            }
        )
        
        return {
            "temperature": result.get("temperature", "warm"),
            "score": result.get("lead_score", 50),
            "qualified": result.get("qualified", False),
            "urgency": result.get("urgency", "medium"),
            "budget_range": result.get("budget_range"),
        }
        
    except Exception as e:
        logger.error(f"Lead analysis failed: {e}")
        return {
            "temperature": "warm",
            "score": 50,
            "qualified": False,
        }


async def _update_ghl_lead_fields(contact_id: str, analysis: Dict[str, Any]):
    """Update GHL custom fields with analysis results"""
    try:
        client = GHLAPIClient()
        
        # Map to custom field values
        custom_fields = {
            "ai_lead_score": analysis.get("score", 50),
            "lead_temperature": analysis.get("temperature", "warm"),
            "ai_analysis_date": datetime.now().isoformat(),
            "budget_qualified": analysis.get("budget_range") is not None,
        }
        
        await client.update_contact(contact_id, {"customFields": custom_fields})
        
    except Exception as e:
        logger.error(f"Failed to update GHL fields: {e}")


async def _get_conversation_history(contact_id: str, limit: int = 10) -> list:
    """Get recent conversation history"""
    try:
        from ...database.repository import get_conversation_history
        return await get_conversation_history(contact_id, limit=limit)
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        return []


async def _analyze_response_intent(message: str, history: list) -> Dict[str, Any]:
    """Analyze the intent of a lead response"""
    try:
        # Simple keyword-based analysis (can be enhanced with AI)
        message_lower = message.lower()
        
        # Intent detection
        intents = []
        if any(w in message_lower for w in ["buy", "purchase", "looking for"]):
            intents.append("purchase_interest")
        if any(w in message_lower for w in ["sell", "selling", "list", "value", "worth", "cma"]):
            intents.append("selling_interest")
        if any(w in message_lower for w in ["budget", "price", "afford", "pre-approved", "preapproved"]):
            intents.append("budget_discussion")
        if any(w in message_lower for w in ["schedule", "tour", "see", "viewing", "showing", "visit"]):
            intents.append("scheduling_interest")
        if any(w in message_lower for w in ["not interested", "stop", "unsubscribe", "remove"]):
            intents.append("opt_out")
        
        # Temperature scoring
        temperature = "warm"
        if "opt_out" in intents:
            temperature = "cold"
        elif "scheduling_interest" in intents or ("purchase_interest" in intents and "budget_discussion" in intents):
            temperature = "hot"
        elif len(intents) >= 2:
            temperature = "warm"
        
        return {
            "intent": intents[0] if intents else "general_inquiry",
            "intents": intents,
            "temperature": temperature,
            "temperature_change": True,  # Signal to update
            "urgency": "high" if "hot" == temperature else "medium",
        }
        
    except Exception as e:
        logger.error(f"Intent analysis failed: {e}")
        return {"intent": "unknown", "temperature": "warm"}


async def _update_lead_temperature(contact_id: str, temperature: str):
    """Update lead temperature in GHL"""
    try:
        client = GHLAPIClient()
        await client.update_contact(contact_id, {
            "customFields": {"lead_temperature": temperature}
        })
    except Exception as e:
        logger.error(f"Failed to update temperature: {e}")


async def _determine_follow_up(contact_id: str, analysis: Dict[str, Any]) -> str:
    """Determine appropriate follow-up action"""
    intent = analysis.get("intent")
    temperature = analysis.get("temperature")
    
    if intent == "opt_out":
        return "unsubscribe_workflow"
    elif intent == "scheduling_interest":
        return "immediate_scheduling"
    elif temperature == "hot":
        return "priority_follow_up"
    elif intent == "selling_interest":
        return "handoff_to_seller_bot"
    else:
        return "standard_nurture"


async def _sync_contact_to_local(contact_id: str, changes: Dict[str, Any]):
    """Sync GHL contact changes to local database"""
    try:
        from ...database.repository import update_contact_fields
        await update_contact_fields(contact_id, changes)
    except Exception as e:
        logger.error(f"Failed to sync contact: {e}")


async def _trigger_reanalysis(contact_id: str):
    """Trigger re-analysis of lead"""
    try:
        # Fetch full contact data
        client = GHLAPIClient()
        contact = await client.get_contact(contact_id)
        
        if contact.get("success"):
            await _analyze_lead(contact.get("data", {}))
    except Exception as e:
        logger.error(f"Reanalysis failed: {e}")


async def _emit_lead_event(event_type: str, data: Dict[str, Any]):
    """Emit event for dashboard/real-time updates"""
    try:
        from ...ghl_real_estate_ai.services.event_broker import event_broker
        
        await event_broker.publish({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        })
    except Exception as e:
        logger.error(f"Failed to emit event: {e}")


from datetime import datetime
