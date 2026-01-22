
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from ghl_real_estate_ai.agents.blackboard import SharedBlackboard
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In a real app, this would be injected or shared
blackboard = SharedBlackboard()

@router.get("/stream-ui-updates")
async def stream_ui_updates(request: Request):
    """
    SSE endpoint to stream real-time UI deltas and agent thinking to the frontend.
    """
    async def event_generator():
        last_history_len = 0
        
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            # Check for new blackboard entries
            history = blackboard.get_history()
            if len(history) > last_history_len:
                new_entries = history[last_history_len:]
                for entry in new_entries:
                    # Filter for UI-relevant events or agent thoughts
                    yield {
                        "event": "update",
                        "id": str(len(history)),
                        "retry": 15000,
                        "data": json.dumps(entry)
                    }
                last_history_len = len(history)
            
            # Keep-alive heartbeat
            await asyncio.sleep(1)
            yield {
                "event": "heartbeat",
                "data": "{}"
            }

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/trigger-ui-swarm")
async def trigger_ui_swarm(objective: str):
    """
    Triggers the Agentic UI Swarm for a specific objective.
    """
    # This would start the swarm in a background task
    # and write progress to the blackboard which SSE picks up.
    from ghl_real_estate_ai.agents.swarm_orchestrator import SwarmOrchestrator
    from pathlib import Path
    
    orchestrator = SwarmOrchestrator(Path("."))
    
    # Run swarm in background
    asyncio.create_task(orchestrator.run_parallel_swarm())
    
    return {"status": "swarm_started", "objective": objective}
