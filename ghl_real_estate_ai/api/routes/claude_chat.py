"""
Claude Chat API - Real-time intelligent chat interface
Handles interactive queries with full context integration
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime

from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeOrchestrator
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.core.service_registry import get_service_registry

router = APIRouter(prefix="/claude", tags=["claude-chat"])


class ChatQueryRequest(BaseModel):
    """Request format for chat queries"""
    message: str
    contact_id: Optional[str] = None
    location_id: Optional[str] = None
    selected_lead_name: Optional[str] = None
    conversation_mode: str = "chat"  # chat, sms, email
    include_context: bool = True
    stream: bool = False


class ChatQueryResponse(BaseModel):
    """Response format for chat queries"""
    success: bool
    message: str
    reasoning: Optional[str] = None
    extracted_data: Dict[str, Any] = {}
    lead_score: Optional[float] = None
    predictive_score: Optional[float] = None
    sources: List[str] = []
    recommended_actions: List[Dict[str, Any]] = []
    response_time_ms: int = 0
    conversation_id: Optional[str] = None


class ConversationHistoryResponse(BaseModel):
    """Response format for conversation history"""
    success: bool
    messages: List[Dict[str, Any]] = []
    conversation_id: str
    lead_context: Dict[str, Any] = {}


@router.post("/query", response_model=ChatQueryResponse)
async def chat_query(
    request: ChatQueryRequest,
    claude: ClaudeOrchestrator = Depends(get_claude_orchestrator)
):
    """
    Process a chat query with full context integration.

    This is the main endpoint for interactive Claude conversations.
    Integrates with memory, lead context, and generates intelligent responses.
    """
    try:
        # Build context
        context = {
            "contact_id": request.contact_id or "demo_user",
            "location_id": request.location_id,
            "selected_lead_name": request.selected_lead_name,
            "conversation_mode": request.conversation_mode,
            "timestamp": datetime.now().isoformat()
        }

        # Add lead options if available (for demo context)
        if request.selected_lead_name:
            context["selected_lead"] = {
                "name": request.selected_lead_name,
                "context": "Available from session state"
            }

        # Process query through Claude orchestrator
        claude_response = await claude.chat_query(
            query=request.message,
            context=context,
            lead_id=request.contact_id
        )

        # Store interaction in memory if contact_id provided
        if request.contact_id and request.include_context:
            try:
                memory_service = MemoryService()
                await memory_service.add_interaction(
                    request.contact_id,
                    request.message,
                    "user",
                    request.location_id
                )
                await memory_service.add_interaction(
                    request.contact_id,
                    claude_response.content,
                    "assistant",
                    request.location_id
                )
            except Exception as e:
                # Don't fail the request if memory storage fails
                print(f"Warning: Failed to store interaction in memory: {e}")

        # Format response
        return ChatQueryResponse(
            success=True,
            message=claude_response.content,
            reasoning=claude_response.reasoning,
            extracted_data=claude_response.metadata,
            sources=claude_response.sources,
            recommended_actions=claude_response.recommended_actions,
            response_time_ms=claude_response.response_time_ms,
            conversation_id=request.contact_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat query: {str(e)}"
        )


@router.post("/query-stream")
async def chat_query_stream(
    request: ChatQueryRequest,
    claude: ClaudeOrchestrator = Depends(get_claude_orchestrator)
):
    """
    Streaming version of chat query for real-time responses.
    Returns Server-Sent Events (SSE) stream.
    """
    async def generate_stream():
        try:
            # Build context (same as non-streaming)
            context = {
                "contact_id": request.contact_id or "demo_user",
                "location_id": request.location_id,
                "selected_lead_name": request.selected_lead_name,
                "conversation_mode": request.conversation_mode,
                "timestamp": datetime.now().isoformat()
            }

            # Process streaming query
            claude_request = claude.ClaudeRequest(
                task_type=claude.ClaudeTaskType.CHAT_QUERY,
                context=context,
                prompt=f"Jorge asks: {request.message}",
                streaming=True
            )

            # Stream response tokens
            response = await claude.process_request(claude_request)

            # For now, send complete response
            # In future, implement actual token-by-token streaming
            yield f"data: {json.dumps({'token': response.content[:50]})}\n\n"
            await asyncio.sleep(0.1)  # Simulate streaming
            yield f"data: {json.dumps({'token': response.content[50:]})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/conversation/{contact_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    contact_id: str,
    location_id: Optional[str] = None,
    limit: int = 50
):
    """
    Retrieve conversation history for a contact.
    """
    try:
        memory_service = MemoryService()
        context = await memory_service.get_context(contact_id, location_id)

        # Format conversation history
        messages = context.get("conversation_history", [])[-limit:]

        # Get lead context for UI
        lead_context = {
            "extracted_preferences": context.get("extracted_preferences", {}),
            "lead_score": context.get("lead_score", 0),
            "conversation_stage": context.get("conversation_stage", "initial"),
            "last_interaction": context.get("last_interaction_at", ""),
        }

        return ConversationHistoryResponse(
            success=True,
            messages=messages,
            conversation_id=contact_id,
            lead_context=lead_context
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@router.post("/lead-analysis/{lead_id}")
async def analyze_lead_comprehensive(
    lead_id: str,
    include_scoring: bool = True,
    include_churn: bool = True,
    claude: ClaudeOrchestrator = Depends(get_claude_orchestrator)
):
    """
    Generate comprehensive Claude-powered lead analysis.
    This endpoint is called by the Lead Intelligence Hub.
    """
    try:
        response = await claude.analyze_lead(
            lead_id=lead_id,
            include_scoring=include_scoring,
            include_churn_analysis=include_churn
        )

        return {
            "success": True,
            "analysis": response.content,
            "reasoning": response.reasoning,
            "recommended_actions": response.recommended_actions,
            "sources": response.sources,
            "response_time_ms": response.response_time_ms
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing lead: {str(e)}"
        )


@router.post("/generate-script")
async def generate_script(
    lead_id: str,
    script_type: str,
    channel: str = "sms",
    variants: int = 1,
    claude: ClaudeOrchestrator = Depends(get_claude_orchestrator)
):
    """
    Generate personalized scripts for lead communication.
    """
    try:
        response = await claude.generate_script(
            lead_id=lead_id,
            script_type=script_type,
            channel=channel,
            variants=variants
        )

        return {
            "success": True,
            "script": response.content,
            "reasoning": response.reasoning,
            "recommended_actions": response.recommended_actions,
            "response_time_ms": response.response_time_ms
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating script: {str(e)}"
        )


@router.post("/synthesize-report")
async def synthesize_report(
    metrics: Dict[str, Any],
    report_type: str = "weekly_summary",
    market_context: Optional[Dict[str, Any]] = None,
    claude: ClaudeOrchestrator = Depends(get_claude_orchestrator)
):
    """
    Generate narrative reports from quantitative metrics.
    """
    try:
        response = await claude.synthesize_report(
            metrics=metrics,
            report_type=report_type,
            market_context=market_context
        )

        return {
            "success": True,
            "report": response.content,
            "reasoning": response.reasoning,
            "recommended_actions": response.recommended_actions,
            "response_time_ms": response.response_time_ms
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error synthesizing report: {str(e)}"
        )


@router.get("/performance-metrics")
async def get_performance_metrics(
    claude: ClaudeOrchestrator = Depends(get_claude_orchestrator)
):
    """
    Get Claude orchestrator performance metrics.
    """
    return {
        "success": True,
        "metrics": claude.get_performance_metrics()
    }