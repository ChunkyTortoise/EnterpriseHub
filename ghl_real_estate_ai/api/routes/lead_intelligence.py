"""
Lead Intelligence Middleware Endpoints.
Provides advanced behavioral forecasting and agentic re-engagement triggers.
"""
from fastapi import APIRouter, Body, Depends, HTTPException
from typing import Dict, Any, List
from ghl_real_estate_ai.services.predictive_lead_scorer import PredictiveLeadScorer
from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine
from ghl_real_estate_ai.services.memory_service import MemoryService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

# Initialize Services
scorer = PredictiveLeadScorer()
memory = MemoryService()
reengage = ReengagementEngine()

@router.post("/score")
async def score_lead_intelligence(
    payload: Dict[str, Any] = Body(...)
):
    """
    Advanced Behavioral Scoring Endpoint.
    Returns 0-100% conversion probability and strategic recommendations.
    """
    contact_id = payload.get("contact_id")
    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")
        
    # Retrieve context from memory
    context = await memory.get_context(contact_id)
    if not context.get("conversation_history"):
        # If no history, we can't do predictive scoring yet
        return {
            "success": False,
            "message": "Insufficient conversation history for behavioral forecasting."
        }
        
    # Calculate Predictive Score
    prediction = scorer.predict_conversion(context)
    
    return {
        "success": True,
        "prediction": prediction
    }

@router.post("/trigger-recovery")
async def trigger_agentic_recovery(
    payload: Dict[str, Any] = Body(...)
):
    """
    Sentiment-Aware Recovery Trigger.
    Generates a personalized re-engagement message for a silent lead.
    """
    contact_id = payload.get("contact_id")
    contact_name = payload.get("contact_name", "there")
    
    context = await memory.get_context(contact_id)
    
    message = await reengage.agentic_reengagement(contact_name, context)
    
    return {
        "success": True,
        "contact_id": contact_id,
        "agentic_message": message
    }
