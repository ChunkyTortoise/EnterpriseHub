"""
Chat API endpoints for Customer Intelligence Platform.

Provides REST API for:
- Chat conversations with AI
- Context management
- Knowledge base queries
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...core.conversation_manager import ConversationManager, AIResponse
from ...core.knowledge_engine import KnowledgeEngine, SearchResult
from ...core.auth_system import (
    User, Permission, get_current_active_user, require_permissions
)
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# Pydantic models for request/response
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message")
    customer_id: str = Field(..., description="Unique customer identifier")
    customer_info: Optional[Dict] = Field(default={}, description="Customer information")
    department_id: Optional[str] = Field(None, description="Department context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str = Field(..., description="AI response message")
    customer_id: str = Field(..., description="Customer identifier")
    extracted_data: Dict = Field(..., description="Extracted structured data")
    engagement_score: int = Field(..., description="Customer engagement score (0-100)")
    reasoning: str = Field(..., description="AI reasoning for the response")
    timestamp: str = Field(..., description="Response timestamp")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")


class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge search."""
    query: str = Field(..., description="Search query")
    department_id: Optional[str] = Field(None, description="Department context")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum results to return")


class KnowledgeSearchResponse(BaseModel):
    """Response model for knowledge search."""
    query: str = Field(..., description="Original search query")
    results: List[Dict] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results found")


class ContextRequest(BaseModel):
    """Request model for context retrieval."""
    customer_id: str = Field(..., description="Customer identifier")
    department_id: Optional[str] = Field(None, description="Department context")


class ContextResponse(BaseModel):
    """Response model for context retrieval."""
    customer_id: str = Field(..., description="Customer identifier")
    conversation_history: List[Dict] = Field(..., description="Conversation history")
    extracted_preferences: Dict = Field(..., description="Extracted customer preferences")
    engagement_score: int = Field(..., description="Current engagement score")
    created_at: str = Field(..., description="Context creation timestamp")
    last_interaction_at: Optional[str] = Field(None, description="Last interaction timestamp")


# Dependency to get conversation manager
async def get_conversation_manager() -> ConversationManager:
    """Get conversation manager instance."""
    return ConversationManager()


# Dependency to get knowledge engine
async def get_knowledge_engine() -> KnowledgeEngine:
    """Get knowledge engine instance."""
    return KnowledgeEngine()


@router.post("/message", response_model=ChatResponse, dependencies=[Depends(require_permissions(Permission.START_CONVERSATIONS))])
async def send_message(
    request: ChatRequest,
    user: User = Depends(get_current_active_user),
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Send a message to the AI and get a response.

    Args:
        request: Chat request with message and customer info
        conversation_manager: Conversation manager dependency

    Returns:
        AI response with extracted data and engagement metrics
    """
    try:
        logger.info(f"Processing message from customer {request.customer_id}")

        # Get current context
        context = await conversation_manager.get_context(
            customer_id=request.customer_id,
            department_id=request.department_id
        )

        # Generate AI response
        ai_response: AIResponse = await conversation_manager.generate_response(
            user_message=request.message,
            customer_info=request.customer_info or {"name": request.customer_id},
            context=context,
            department_id=request.department_id
        )

        # Update context with the conversation
        await conversation_manager.update_context(
            customer_id=request.customer_id,
            user_message=request.message,
            ai_response=ai_response.message,
            extracted_data=ai_response.extracted_data,
            department_id=request.department_id
        )

        # Calculate total tokens used
        tokens_used = None
        if ai_response.input_tokens and ai_response.output_tokens:
            tokens_used = ai_response.input_tokens + ai_response.output_tokens

        return ChatResponse(
            message=ai_response.message,
            customer_id=request.customer_id,
            extracted_data=ai_response.extracted_data,
            engagement_score=ai_response.engagement_score,
            reasoning=ai_response.reasoning,
            timestamp=datetime.utcnow().isoformat(),
            tokens_used=tokens_used
        )

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/context/{customer_id}", response_model=ContextResponse, dependencies=[Depends(require_permissions(Permission.VIEW_CUSTOMER_DATA))])
async def get_customer_context(
    customer_id: str,
    department_id: Optional[str] = None,
    user: User = Depends(get_current_active_user),
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Get conversation context for a customer.

    Args:
        customer_id: Customer identifier
        department_id: Optional department context
        conversation_manager: Conversation manager dependency

    Returns:
        Customer conversation context and history
    """
    try:
        context = await conversation_manager.get_context(
            customer_id=customer_id,
            department_id=department_id
        )

        return ContextResponse(
            customer_id=customer_id,
            conversation_history=context.get("conversation_history", []),
            extracted_preferences=context.get("extracted_preferences", {}),
            engagement_score=context.get("engagement_score", 0),
            created_at=context.get("created_at", datetime.utcnow().isoformat()),
            last_interaction_at=context.get("last_interaction_at")
        )

    except Exception as e:
        logger.error(f"Error retrieving context for customer {customer_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve context: {str(e)}")


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse, dependencies=[Depends(require_permissions(Permission.SEARCH_KNOWLEDGE))])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    user: User = Depends(get_current_active_user),
    knowledge_engine: KnowledgeEngine = Depends(get_knowledge_engine)
):
    """
    Search the knowledge base for relevant information.

    Args:
        request: Knowledge search request
        knowledge_engine: Knowledge engine dependency

    Returns:
        Search results from the knowledge base
    """
    try:
        logger.info(f"Searching knowledge base for: {request.query}")

        # Search knowledge base
        search_results: List[SearchResult] = knowledge_engine.search(
            query=request.query,
            n_results=request.max_results,
            department_id=request.department_id
        )

        # Convert SearchResult objects to dict format
        results = []
        for result in search_results:
            results.append({
                "text": result.text,
                "source": result.source,
                "distance": result.distance,
                "metadata": result.metadata
            })

        return KnowledgeSearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )

    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {str(e)}")


@router.post("/context/clear/{customer_id}", dependencies=[Depends(require_permissions(Permission.CLEAR_CUSTOMER_DATA))])
async def clear_customer_context(
    customer_id: str,
    department_id: Optional[str] = None,
    user: User = Depends(get_current_active_user),
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Clear conversation context for a customer.

    Args:
        customer_id: Customer identifier
        department_id: Optional department context
        conversation_manager: Conversation manager dependency

    Returns:
        Success message
    """
    try:
        # Clear context by removing from in-memory storage
        context_key = f"{department_id}:{customer_id}" if department_id else customer_id
        if hasattr(conversation_manager, '_contexts') and context_key in conversation_manager._contexts:
            del conversation_manager._contexts[context_key]

        logger.info(f"Cleared context for customer {customer_id}")

        return {"message": f"Context cleared for customer {customer_id}"}

    except Exception as e:
        logger.error(f"Error clearing context for customer {customer_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear context: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chat-api", "timestamp": datetime.utcnow().isoformat()}