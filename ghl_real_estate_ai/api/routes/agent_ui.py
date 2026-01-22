from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from pathlib import Path
from ghl_real_estate_ai.agents.blackboard import SharedBlackboard
from ghl_real_estate_ai.agents.ui_agent_swarm import UIAgentSwarm
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In a real app, this would be injected or shared
blackboard = SharedBlackboard()

@router.get("/stream-ui-generation")
async def stream_ui_generation(request: Request, objective: str, location_id: str = "global"):
    """
    SSE endpoint that triggers the UI Agent Swarm and streams events in real-time.
    """
    swarm = UIAgentSwarm(Path("."), location_id=location_id)

    async def event_generator():
        try:
            async for event in swarm.generate_ui_stream(objective):
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                yield f"event: {event['event']}\ndata: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Error in UI stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/stream-ui-updates")
async def stream_ui_updates(request: Request):
    """
    General SSE endpoint to stream blackboard updates to the frontend.
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
                    yield f"event: blackboard_update\ndata: {json.dumps(entry)}\n\n"
                last_history_len = len(history)
            
            # Keep-alive heartbeat
            await asyncio.sleep(1)
            yield f": heartbeat\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/trigger-ui-swarm")
async def trigger_ui_swarm(objective: str, location_id: str = "global"):
    """
    Triggers the Agentic UI Swarm for a specific objective in the background.
    """
    swarm = UIAgentSwarm(Path("."), location_id=location_id)
    
    # Run swarm in background and log to blackboard
    async def run_and_log():
        async for event in swarm.generate_ui_stream(objective):
            blackboard.write(f"ui_event_{datetime.now().timestamp()}", event, "UIAgentSwarm")

    asyncio.create_task(run_and_log())
    
    return {"status": "swarm_started", "objective": objective}