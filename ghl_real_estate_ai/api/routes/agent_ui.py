import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Request
from fastapi.responses import StreamingResponse

from ghl_real_estate_ai.agents.blackboard import SharedBlackboard
from ghl_real_estate_ai.agents.ui_agent_swarm import UIAgentSwarm
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.learning.engine import ContentBasedModel
from ghl_real_estate_ai.services.learning.interfaces import FeatureVector

logger = get_logger(__name__)
router = APIRouter()

# Model storage path (shared with simulation skill)
MODEL_PATH = "./data/ml/ui_simulator_v1.json"

# In-memory cache for multi-tenant models
_models: Dict[str, ContentBasedModel] = {}


async def _get_model(location_id: str = "global") -> ContentBasedModel:
    if location_id not in _models:
        model = ContentBasedModel(model_id=f"ui_simulator_{location_id}")
        # Try to load tenant-specific model
        if os.path.exists(MODEL_PATH) or os.path.exists(f"./data/ml/{location_id}_ui_simulator_v1.json"):
            await model.load(MODEL_PATH, tenant_id=location_id)
        _models[location_id] = model
    return _models[location_id]


# Blackboard remains shared for the cockpit
blackboard = SharedBlackboard()


@router.get("/stream-ui-generation")
async def stream_ui_generation(
    request: Request, objective: str = "", location_id: str = "global", voice_transcript: str = None
):
    """
    SSE endpoint that triggers the UI Agent Swarm and streams events in real-time.
    Supports both direct text objective and voice-transcribed intent.
    """
    swarm = UIAgentSwarm(Path("."), location_id=location_id)

    async def event_generator():
        try:
            async for event in swarm.generate_ui_stream(objective, voice_transcript=voice_transcript):
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                yield f"event: {event['event']}\ndata: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Error in UI stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/record-feedback")
async def record_feedback(
    component_id: str = Body(...),
    user_id: str = Body(...),
    rating: float = Body(...),  # 1.0 for like, -1.0 for dislike
    features: Dict[str, float] = Body(...),
    location_id: str = Body("global"),
):
    """
    Records user feedback (like/dislike) for a generated component.
    Updates the Behavioral ML Engine to improve future conversion predictions.
    Now supports Multi-Tenant DNA via location_id.
    """
    logger.info(f"Recording feedback for {component_id} from {user_id} in {location_id}: {rating}")

    model = await _get_model(location_id)

    fv = FeatureVector(
        entity_id=user_id, entity_type="lead_segment", numerical_features=features, feature_names=list(features.keys())
    )

    # Update the ML Engine online
    success = await model.update_online(fv, rating)

    # Persist the updated "Design DNA" specifically for this tenant
    await model.save(MODEL_PATH, tenant_id=location_id)

    # Log to blackboard for transparency
    blackboard.write(
        f"feedback_{datetime.now().timestamp()}",
        {"component_id": component_id, "rating": rating, "user_id": user_id, "location_id": location_id},
        "UserFeedbackLoop",
    )

    return {"status": "success", "updated": success}


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
