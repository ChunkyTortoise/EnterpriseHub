
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
import time

app = FastAPI(title="AI Coaching Server", version="1.0.0")

class CoachingRequest(BaseModel):
    agent_id: str
    conversation_context: Dict[str, Any]
    current_stage: str = "discovery"

class CoachingResponse(BaseModel):
    agent_id: str
    coaching_suggestions: List[str]
    next_questions: List[str]
    confidence_score: float
    processing_time_ms: float

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai_coaching"}

@app.post("/get-coaching", response_model=CoachingResponse)
async def get_coaching(request: CoachingRequest):
    start_time = time.time()

    # Mock coaching suggestions (replace with real AI)
    suggestions = [
        "Ask about their timeline - they seem ready to move quickly",
        "Focus on the school district - they mentioned kids multiple times",
        "Probe deeper on budget - there's flexibility based on their language",
        "Share similar success stories to build confidence"
    ]

    questions = [
        "What's driving your timeline for moving?",
        "How important are the local schools in your decision?",
        "Have you been pre-approved for financing?",
        "What are your must-haves vs nice-to-haves?"
    ]

    processing_time = (time.time() - start_time) * 1000

    return CoachingResponse(
        agent_id=request.agent_id,
        coaching_suggestions=suggestions[:2],
        next_questions=questions[:2],
        confidence_score=0.97,
        processing_time_ms=processing_time
    )

@app.get("/coaching-stats")
async def get_coaching_stats():
    return {
        "total_sessions": 5000,
        "avg_response_time_ms": 85,
        "accuracy_rating": 0.97,
        "agents_helped": 150
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
