"""
Sentiment Analysis API Routes

Exposes multi-channel sentiment analysis, emotion classification,
conversation-level trends, and escalation risk detection.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.sentiment_analysis_engine import (
    get_sentiment_engine,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/sentiment",
    tags=["Sentiment Analysis"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class AnalyzeSentimentRequest(BaseModel):
    contact_id: str = Field(..., description="Contact identifier")
    message: str = Field(..., description="Message to analyze")
    channel: str = Field("sms", description="Channel: sms, voice, email, chat, video")


class SentimentResponse(BaseModel):
    contact_id: str
    polarity: float
    magnitude: float
    emotion: str
    confidence: float
    channel: str
    intent_signals: List[str]
    key_phrases: List[str]


class ConversationSentimentResponse(BaseModel):
    contact_id: str
    message_count: int
    avg_polarity: float
    polarity_variance: float
    dominant_emotion: str
    trend: str
    engagement_score: float
    escalation_risk: float
    emotion_distribution: Dict[str, float]
    sentiment_timeline: List[float]


class BatchSentimentRequest(BaseModel):
    messages: List[AnalyzeSentimentRequest] = Field(..., min_length=1, max_length=200)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: AnalyzeSentimentRequest):
    """Analyze sentiment of a single message."""
    try:
        engine = get_sentiment_engine()
        result = await engine.analyze_message(
            contact_id=request.contact_id,
            message=request.message,
            channel=request.channel,
        )
        return SentimentResponse(
            contact_id=result.contact_id,
            polarity=result.polarity,
            magnitude=result.magnitude,
            emotion=result.emotion.value,
            confidence=result.confidence,
            channel=result.channel.value,
            intent_signals=result.intent_signals,
            key_phrases=result.key_phrases,
        )
    except Exception as e:
        logger.error("Sentiment analysis failed for %s: %s", request.contact_id, e)
        raise HTTPException(500, f"Sentiment analysis error: {e}")


@router.post("/analyze/batch")
async def analyze_sentiment_batch(request: BatchSentimentRequest):
    """Analyze sentiment of multiple messages."""
    try:
        engine = get_sentiment_engine()
        results = []
        for msg in request.messages:
            result = await engine.analyze_message(
                contact_id=msg.contact_id,
                message=msg.message,
                channel=msg.channel,
            )
            results.append(
                {
                    "contact_id": result.contact_id,
                    "polarity": result.polarity,
                    "emotion": result.emotion.value,
                    "intent_signals": result.intent_signals,
                }
            )
        return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error("Batch sentiment analysis failed: %s", e)
        raise HTTPException(500, f"Batch analysis error: {e}")


@router.get(
    "/conversation/{contact_id}",
    response_model=ConversationSentimentResponse,
)
async def get_conversation_sentiment(contact_id: str):
    """Get aggregated sentiment for a contact's full conversation."""
    try:
        engine = get_sentiment_engine()
        result = await engine.get_conversation_sentiment(contact_id)
        return ConversationSentimentResponse(
            contact_id=result.contact_id,
            message_count=result.message_count,
            avg_polarity=result.avg_polarity,
            polarity_variance=result.polarity_variance,
            dominant_emotion=result.dominant_emotion.value,
            trend=result.trend.value,
            engagement_score=result.engagement_score,
            escalation_risk=result.escalation_risk,
            emotion_distribution=result.emotion_distribution,
            sentiment_timeline=result.sentiment_timeline,
        )
    except Exception as e:
        logger.error("Conversation sentiment failed for %s: %s", contact_id, e)
        raise HTTPException(500, f"Conversation sentiment error: {e}")


@router.delete("/history/{contact_id}")
async def clear_sentiment_history(contact_id: str):
    """Clear sentiment history for a contact."""
    engine = get_sentiment_engine()
    engine.clear_history(contact_id)
    return {"status": "cleared", "contact_id": contact_id}


@router.get("/health")
async def sentiment_health():
    """Health check for the sentiment analysis engine."""
    try:
        engine = get_sentiment_engine()
        tracked = len(engine._conversation_history)
        return {
            "status": "healthy",
            "service": "sentiment_analysis_engine",
            "contacts_tracked": tracked,
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
