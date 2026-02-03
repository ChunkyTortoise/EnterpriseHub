"""
Lead Intelligence Middleware Endpoints.
Provides advanced behavioral forecasting and agentic re-engagement triggers.
"""
from fastapi import APIRouter, Body, Depends, HTTPException
from typing import Dict, Any, List
from ghl_real_estate_ai.services.predictive_lead_scorer import PredictiveLeadScorer
from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

# Lazy service singletons — defer initialization until first request
_scorer = None
_memory = None
_reengage = None
_intent_decoder = None


def _get_scorer():
    global _scorer
    if _scorer is None:
        _scorer = PredictiveLeadScorer()
    return _scorer


def _get_memory():
    global _memory
    if _memory is None:
        _memory = MemoryService()
    return _memory


def _get_reengage():
    global _reengage
    if _reengage is None:
        _reengage = ReengagementEngine()
    return _reengage


def _get_intent_decoder():
    global _intent_decoder
    if _intent_decoder is None:
        _intent_decoder = LeadIntentDecoder()
    return _intent_decoder

@router.post("/analyze-intent", response_model=LeadIntentProfile)
async def analyze_lead_intent(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user)
):
    """
    2026 Strategic Roadmap: Phase 1
    Detailed Semantic & Psychographic Lead Analysis (FRS & PCS).
    """
    contact_id = payload.get("contact_id")
    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")
    
    # Get history from _get_memory() or payload
    history = payload.get("conversation_history")
    if not history:
        context = await _get_memory().get_context(contact_id)
        history = context.get("conversation_history", [])
        
    if not history:
        # Return empty/neutral profile if no history
        return _get_intent_decoder().analyze_lead(contact_id, [])
        
    profile = _get_intent_decoder().analyze_lead(contact_id, history)
    return profile

@router.post("/score")
async def score_lead_intelligence(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user)
):
    """
    Advanced Behavioral Scoring Endpoint.
    Returns 0-100% conversion probability and strategic recommendations.
    """
    contact_id = payload.get("contact_id")
    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")
        
    # Retrieve context from _get_memory()
    context = await _get_memory().get_context(contact_id)
    if not context.get("conversation_history"):
        # If no history, we can't do predictive scoring yet
        return {
            "success": False,
            "message": "Insufficient conversation history for behavioral forecasting."
        }
        
    # Calculate Predictive Score
    prediction = _get_scorer().predict_conversion(context)
    
    return {
        "success": True,
        "prediction": prediction
    }

@router.post("/trigger-recovery")
async def trigger_agentic_recovery(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user)
):
    """
    Sentiment-Aware Recovery Trigger.
    Generates a personalized re-engagement message for a silent lead.
    """
    contact_id = payload.get("contact_id")
    contact_name = payload.get("contact_name", "there")
    
    context = await _get_memory().get_context(contact_id)
    
    message = await _get_reengage().agentic_reengagement(contact_name, context)
    
    return {
        "success": True,
        "contact_id": contact_id,
        "agentic_message": message
    }
